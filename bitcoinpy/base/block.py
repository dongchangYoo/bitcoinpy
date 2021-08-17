from typing import Union

from bitcoinpy.base.bytes import BTCBytes
from header import Header
from merkle_tree import BTCMerkleTree

# import for test below
import os
import json
from unittest import TestCase


class Block(Header):
    def __init__(self, tx_ids: list, version: bytes, prev_hash: bytes, merkle_root: bytes, _time: bytes, bits: bytes, nonce: bytes, height: int = 0):
        """ all delivered bytes have big endian form """
        super().__init__(version, prev_hash, merkle_root, _time, bits, nonce, height)
        self.tx_ids = [BTCBytes.from_big_hex(tx) for tx in tx_ids]
        self.merkle_prover = BTCMerkleTree.from_big_endian_hex_list(tx_ids)

        if super().merkle_root != self.merkle_prover.root:
            raise Exception("Invalid merkle root")

    @classmethod
    def from_dict(cls, block_dict):
        tx_ids = block_dict["tx"]
        version = bytes.fromhex(block_dict["versionHex"])
        prev_hash = bytes.fromhex(block_dict["previousblockhash"])
        mr = bytes.fromhex(block_dict["merkleroot"])
        timestamp = block_dict["time"].to_bytes(4, "big")
        bits = bytes.fromhex(block_dict["bits"])
        nonce = block_dict["nonce"].to_bytes(4, "big")
        height = int(block_dict["height"])
        return cls(tx_ids, version, prev_hash, mr, timestamp, bits, nonce, height)

    @property
    def txs(self):
        return self.tx_ids

    def get_tx_by_index(self, index: int) -> BTCBytes:
        return self.tx_ids[index]

    def get_multi_merkle_proof_by_leaves(self, leaves_as_be: Union[BTCBytes, list]):
        if not isinstance(leaves_as_be[0], BTCBytes):
            raise Exception("Invalid input type: expected {}, but {}".format(type(BTCBytes), type(leaves_as_be[0])))

        indices = list()
        for leaf in leaves_as_be:
            index = self.merkle_prover.get_index_of_leaf(leaf)
            indices.append(index)
        return self.merkle_prover.gen_multi_proof_and_flags(indices)

    def get_multi_merkle_proof_by_indices(self, indices: list):
        return self.merkle_prover.gen_multi_proof_and_flags(indices)

    @classmethod
    def verify_multi_proof(cls, root: BTCBytes, target_leaves: list, proof: list, flags: list) -> bool:
        return BTCMerkleTree.verify_multi_proof(root, target_leaves, proof, flags)


class BitcoinBlockTest(TestCase):
    def test_block_constructor(self):
        block_path = "../test_data/blocks/mainnet_684032.json"
        with open(block_path) as json_data:
            block_dict = json.load(json_data)
            block = Block.from_dict(block_dict)
            block_hash = block.hash.hex_as_be
            self.assertEqual(block_hash, "0x0000000000000000000b346d014b3cb3e80d06a13b52e44f1beb0a98374c4b76")

    def test_merkle_proof(self):
        block_path = "../test_data/blocks/mainnet_684032.json"
        with open(block_path) as json_data:
            block_dict = json.load(json_data)
            block = Block.from_dict(block_dict)

            indices = [1]
            proof, flags = block.get_multi_merkle_proof_by_indices(indices)

            leaves = [block.get_tx_by_index(index) for index in indices]
            result = Block.verify_multi_proof(block.merkle_root, leaves, proof, flags)
            self.assertTrue(result)

