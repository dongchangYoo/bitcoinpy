from typing import Union

from bitcoinpy.crypto.hashes import hash256
from bitcoinpy.base.bytes import BTCBytes

# import for test below
import random
import os
from unittest import TestCase
import json


class MerkleTree:
    def __init__(self, leaves: list):
        if not isinstance(leaves[0], BTCBytes):
            raise Exception("Invalid leaf type: expected BTCBytes, but {}".format(type(leaves[0])))

        leaf_len: int = len(leaves)
        if leaf_len < 1:
            self.depth: int = 0
        else:
            self.depth = len(bin(len(leaves) - 1)[2:])  # num of layer:= (bit_len of n-1) + 1

        self.layers: list = list()
        # build tree
        zero_layer: list = [leaf for leaf in leaves]
        self.layers.append(zero_layer)
        for _ in range(self.depth):
            prev_layer = self.layers[-1]
            next_layer = list()
            for i in range(0, len(prev_layer), 2):
                left: BTCBytes = prev_layer[i]
                if i + 1 == len(prev_layer):
                    right: BTCBytes = left  # TODO is deep copied?
                else:
                    right: BTCBytes = prev_layer[i+1]
                data = BTCMerkleTree.hash_func(left, right)
                next_layer.append(data)
            self.layers.append(next_layer)

    @classmethod
    def from_big_endian_hex_list(cls, leaves: list):
        little_leaves = list()
        for leaf in leaves:
            little_leaves.append(BTCBytes.from_big_hex(leaf))
        return cls(little_leaves)

    @staticmethod
    def hash_func(left: BTCBytes, right: BTCBytes) -> BTCBytes:
        return BTCBytes.from_little_bytes(hash256(left.bytes_as_le + right.bytes_as_le))

    @property
    def root(self) -> BTCBytes:
        if len(self.layers[-1]) == 0:
            return BTCBytes.from_big_hex("0000000000000000000000000000000000000000000000000000000000000000")
        return self.layers[-1][0]

    def get_index_of_leaf(self, leaf: BTCBytes) -> int:
        return self.layers[0].index(leaf.bytes_as_le)


class NodeIndicator:
    def __init__(self, height: int, idx: int):
        self._height = height
        self._idx = idx

    def __eq__(self, other):
        return self.height == other.height and self.idx == other.idx

    @property
    def height(self):
        return self._height

    @property
    def idx(self):
        return self._idx

    @property
    def parent_ind(self):
        return NodeIndicator(self._height + 1, self._idx // 2)


class IndicatorQueue:
    def __init__(self, indicators: list):
        self.queue = indicators
        self.cursor = 0

    def pop(self) -> Union[NodeIndicator, None]:
        if len(self.queue) < 1:  # in empty
            return None
        ret: NodeIndicator = self.queue[self.cursor]
        self.cursor += 1
        return ret

    def enq(self, ind: NodeIndicator):
        # ?????? ?????????
        if not self.included(ind):
            self.queue.append(ind)

    def included(self, ind: NodeIndicator) -> bool:
        return ind in self.queue

    def is_empty(self) -> bool:
        return len(self.queue) == self.cursor

    @property
    def array(self):
        return self.queue


class BTCMerkleTree(MerkleTree):
    def __init__(self, leaves: list):
        super().__init__(leaves)

    @classmethod
    def from_big_hex_list(cls, big_hex_leaves: list):
        return super().from_big_endian_hex_list(big_hex_leaves)

    def gen_multi_proof_and_flags(self, indices: list):
        # generate multi_proof
        proof = self._gen_multi_proof(indices)

        # generate flags
        proof_ind: list = [self.get_indicator_by_node(item) for item in proof]
        flags = self._get_proof_flags(indices, proof_ind)
        return proof, flags

    def _gen_multi_proof(self, indices: list):
        hashes_queue = IndicatorQueue([NodeIndicator(0, idx) for idx in indices])
        proof: list = list()
        while True:
            ind: NodeIndicator = hashes_queue.pop()

            pair_node: BTCBytes = self.get_pair_by_indicator(ind)
            if pair_node is not None:
                proof.append(pair_node)

            if ind.parent_ind.height == self.depth:
                break

            hashes_queue.enq(ind.parent_ind)

        # proof - hashes
        ret_proof: list = list()
        for item in proof:
            ind = self.get_indicator_by_node(item)
            if not hashes_queue.included(ind):
                ret_proof.append(item)
        return ret_proof

    def _get_proof_flags(self, target_indices: list, proofs_ind: list):
        ret_flags: list = list()
        target_ind: list = [NodeIndicator(0, idx) for idx in target_indices]
        hashes_ind: IndicatorQueue = IndicatorQueue(target_ind)
        proof_ind: IndicatorQueue = IndicatorQueue(proofs_ind)

        while True:
            test = hashes_ind.pop()
            if test.height == self.depth:
                break

            is_hash_left: bool = test.idx % 2 == 0
            pair_idx: int = test.idx + 1 if is_hash_left else test.idx - 1
            pair_ind = NodeIndicator(test.height, pair_idx)
            if proof_ind.included(pair_ind):
                is_pair_hash: bool = False
                proof_ind.pop()
            elif hashes_ind.included(pair_ind):
                is_pair_hash: bool = True
                hashes_ind.pop()
            else:  # i'm last one in the layer
                is_hash_left = False
                is_pair_hash = True
            next_hash_ind = NodeIndicator(test.height + 1, test.idx // 2)
            hashes_ind.enq(next_hash_ind)
            flag = BTCMerkleTree._determine_flag(is_hash_left, is_pair_hash)
            ret_flags.append(flag)

        return ret_flags

    @staticmethod
    def verify_multi_proof(root: BTCBytes, target_leaves: list, proof: list, flags: list):
        if not isinstance(target_leaves[0], BTCBytes):
            raise Exception("Invalid target_leaves type: expected {}, but {}".format(type(BTCBytes), type(target_leaves[0])))

        if not isinstance(proof[0], BTCBytes):
            raise Exception("Invalid proof type: expected {}, but {}".format(type(BTCBytes), type(proof[0])))

        total_hashes: int = len(flags)

        hashes_pos: int = 0
        proof_pos: int = 0
        hashes: list = target_leaves[:]

        for i in range(total_hashes):
            if flags[i] == 0:  # hash alone
                left: BTCBytes = hashes[hashes_pos]
                hashes_pos += 1
                right: BTCBytes = left
            elif flags[i] == 1:  # proof || hash
                left: BTCBytes = proof[proof_pos]
                proof_pos += 1
                right: BTCBytes = hashes[hashes_pos]
                hashes_pos += 1
            elif flags[i] == 2:  # hash || proof
                left: BTCBytes = hashes[hashes_pos]
                hashes_pos += 1
                right: BTCBytes = proof[proof_pos]
                proof_pos += 1
            elif flags[i] == 3:  # hash || hash
                left: BTCBytes = hashes[hashes_pos]
                hashes_pos += 1
                right: BTCBytes = hashes[hashes_pos]
                hashes_pos += 1
            else:
                return Exception("wrong flags in verify")

            next_hash: BTCBytes = BTCMerkleTree.hash_func(left, right)
            hashes.append(next_hash)

        return root == hashes[-1]  # root

    @staticmethod
    def _determine_flag(is_hash_left: bool, is_pair_hash: bool) -> int:
        if is_hash_left and is_pair_hash:  # hash || hash
            return 3
        if is_hash_left and not is_pair_hash:  # hash || proof
            return 2
        if not is_hash_left and not is_pair_hash:  # proof || hash
            return 1
        else:
            return 0  # has no pair..

    def get_indicator_by_node(self, leaf: str) -> Union[NodeIndicator, None]:
        for height, layer in enumerate(self.layers):
            if leaf in layer:
                idx = layer.index(leaf)
                return NodeIndicator(height, idx)
        return None

    def get_node(self, height: int, idx: int) -> BTCBytes:
        return self.layers[height][idx]

    def get_node_by_indicator(self, ind: NodeIndicator) -> BTCBytes:
        return self.get_node(ind.height, ind.idx)

    def get_pair_by_indicator(self, ind: NodeIndicator) -> Union[BTCBytes, None]:
        target_layer: list = self.layers[ind.height]
        pair_idx = ind.idx + 1 if ind.idx % 2 == 0 else ind.idx - 1
        if pair_idx < len(target_layer):
            return target_layer[pair_idx]
        else:
            return None

    # @staticmethod
    # def hash_func(left: BTCBytes, right: BTCBytes) -> BTCBytes:
    #     return BTCBytes(hash256(left.bytes_as_le + right.bytes_as_le))

    @property
    def root(self) -> BTCBytes:
        return self.layers[-1][0]


class MerkleProofFuzzTest(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        test_file_names = os.listdir("../test_data/blocks/")
        if "__init__.py" in test_file_names:
            test_file_names.remove("__init__.py")

        self.expected_roots: list = list()
        self.provers: list = list()
        for name in test_file_names:
            with open("../test_data/blocks/" + name) as json_data:
                test_dict = json.load(json_data)
                tx_ids: list = test_dict["tx"]

                self.expected_roots.append("0x" + test_dict["merkleroot"])
                # initiate manager included building tree
                prover = BTCMerkleTree.from_big_hex_list(tx_ids)
                self.provers.append(prover)

    def test_merkle_root_generate(self):
        for i in range(len(self.expected_roots)):
            actual_root: str = self.provers[i].root.hex_as_be
            self.assertEqual(actual_root, self.expected_roots[i])

    def test_merkle_single_proof_fuzz(self):
        for i in range(len(self.provers)):
            prover = self.provers[i]

            # randomly select index of target leaf
            index_max: int = len(prover.layers)
            target_indices = [random.randrange(index_max)]

            # testing
            self.multi_prove_and_verify(prover, target_indices)

    def test_merkle_multi_proof_fuzz(self):
        prover = self.provers[0]

        for i in range(1):
            # randomly select index of target leaf
            index_max: int = len(prover.layers[0])
            target_indices: list = MerkleProofFuzzTest.get_random_indices(index_max)

            # testing
            result = self.multi_prove_and_verify(prover, target_indices)
            self.assertTrue(result)

    @staticmethod
    def multi_prove_and_verify(prover: BTCMerkleTree, target_indices: list) -> bool:
        proof: list = prover._gen_multi_proof(target_indices)

        # generate flag
        proof_ind: list = [prover.get_indicator_by_node(item) for item in proof]
        flags: list = prover._get_proof_flags(target_indices, proof_ind)

        # verify proof
        target_leaves = [prover.get_node(0, idx) for idx in target_indices]
        expected_root: BTCBytes = BTCBytes.from_big_hex(prover.root.hex_as_be)
        result = BTCMerkleTree.verify_multi_proof(expected_root, target_leaves, proof, flags)
        return result

    @staticmethod
    def get_random_indices(index_max: int) -> list:
        len_indices: int = 5

        indices = [random.randrange(index_max) for _ in range(len_indices)]
        indices.sort()

        ret_indices: list = list()
        for idx, item in enumerate(indices):
            if indices.index(item) == idx:
                ret_indices.append(item)
        return ret_indices


class BitcoinBlockTest(TestCase):

    def test_merkle_root_new(self):
        data_path = "../test_data/blocks/mainnet_684032.json"
        with open(data_path) as json_data:
            test_dict = json.load(json_data)
            tx_ids: list = test_dict["tx"]
            expected_merkle_root: BTCBytes = BTCBytes.from_big_hex(test_dict["merkleroot"])

            tree = MerkleTree.from_big_endian_hex_list(tx_ids)
            self.assertEqual(expected_merkle_root, tree.root)
