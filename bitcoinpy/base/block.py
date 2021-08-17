from header import Header
from merkle_tree import MerkleTree

# import for test below
import os
import json
from unittest import TestCase


class BTCBlock:
    def __init__(self, tx_ids: list, version_hex: str, prev_hash: str, bits: str, nonce: int, time: int):
        self.tx_ids = tx_ids
        prover = MerkleTree.from_big_hex_list(tx_ids)
        self._header = Header.new_by_elements(version_hex, prev_hash, prover.root.big_hex, bits, nonce, time)

    @classmethod
    def from_dict(cls, block_dict):
        tx_ids = block_dict["tx"]
        version_hex = block_dict["versionHex"]
        prev_hash = block_dict["previousblockhash"]
        bits = block_dict["bits"]
        nonce = block_dict["nonce"]
        time = block_dict["time"]
        return cls(tx_ids, version_hex, prev_hash, bits, nonce, time)

    def __repr__(self):
        return 'header: \n{}\ntx: {}'.format(
            self._header,
            self.tx_ids
        )

    @property
    def hash(self):
        return self._header.hash

    @property
    def prev_hash(self):
        return self._header.prev_hash

    @property
    def merkle_root(self):
        return self._header.merkle_root

    @property
    def height(self):
        return int("0x" + self._header.time.hex(), 16)

    @property
    def txs(self):
        return self.tx_ids

    @property
    def header(self):
        return self._header

    @property
    def raw_header_str(self):
        return self._header.serialize().hex()


class BitcoinBlockTest(TestCase):
    my_abspath = os.path.dirname(os.path.abspath(__file__))

    def test_block_constructor(self):
        test_file_path = BitcoinBlockTest.my_abspath + "/test_data/blocks/"
        test_file_names = os.listdir(test_file_path)
        if "__init__.py" in test_file_names:
            test_file_names.remove("__init__.py")

        for path in test_file_names:
            with open(test_file_path + path) as json_data:
                test_dict = json.load(json_data)

                # for merkle tree
                tx_ids: list = test_dict["tx"]

                # for header
                version_hex: str = test_dict["versionHex"]
                prev_hash: str = test_dict["previousblockhash"]
                bits_hex: str = test_dict["bits"]
                nonce: int = test_dict["nonce"]
                _time: int = test_dict["time"]
                expected_hash: str = test_dict["hash"]

                block = Block(tx_ids, version_hex, prev_hash, bits_hex, nonce, _time)
                block_hash = block.hash.hex()

                self.assertEqual(expected_hash, block_hash)
