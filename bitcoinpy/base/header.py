from io import BytesIO
import time
import hashlib

# import for test below
from unittest import TestCase
import os
import json


class BTCHeader:
    def __init__(self, version: bytes, prev_hash: bytes, merkle_root: bytes, _time: bytes, bits: bytes, nonce: bytes, height: int = 0):
        """ store element by big endian bytes"""
        self.version = version
        self.__prev_hash = prev_hash
        self.merkle_root = merkle_root
        self.__bits = bits
        self.__nonce = nonce
        self.__time = _time
        self._height = height

    def __repr__(self):
        ret = "version: {}\nprev_hash: {}\nmerkle_root: {}\ntime: {}\nbits: {}\nnonce: {}\nheight: {}".format(
            self.version.hex(), self.__prev_hash.hex(), self.merkle_root.hex(), self.__time.hex(), self.__bits.hex(),
            self.__nonce.hex(), self.height
        )

        return ret

    def serialize(self) -> bytes:
        result = self.version[::-1]
        result += self.__prev_hash[::-1]
        result += self.merkle_root[::-1]
        result += self.__time[::-1]
        result += self.__bits[::-1]
        result += self.__nonce[::-1]
        return result

    @classmethod
    def parse_from_str(cls, header_str: str):
        s = BytesIO(bytes.fromhex(header_str))
        version = s.read(4)
        prev_hash = s.read(32)
        mr = s.read(32)
        timestamp = s.read(4)
        bits = s.read(4)
        nonce = s.read(4)
        return cls(version[::-1], prev_hash[::-1], mr[::-1], timestamp[::-1], bits[::-1], nonce[::-1])

    @classmethod
    def parse_from_dict(cls, header_dict: dict):
        version_hex = bytes.fromhex(header_dict["versionHex"])
        prev_hash = bytes.fromhex(header_dict["previousblockhash"])
        mr = bytes.fromhex(header_dict["merkleroot"])
        timestamp = header_dict["time"].to_bytes(4, "big")
        bits = bytes.fromhex(header_dict["bits"])
        nonce = header_dict["nonce"].to_bytes(4, "big")
        height = int(header_dict["height"])
        return cls(version_hex, prev_hash, mr, timestamp, bits, nonce, height)

    @classmethod
    def new_by_elements(cls, version_hex: str, prev_hash: str, merkle_root: str, bits: str, nonce: int = 0, _time: int = None, height: int = 0):
        """ store element by big endian bytes"""
        version_hex = bytes.fromhex(version_hex)
        prev_hash = bytes.fromhex(prev_hash)
        mr = bytes.fromhex(merkle_root[2:] if merkle_root.startswith("0x") else merkle_root)
        if _time is None:
            timestamp = int(time.time()).to_bytes(4, "big")
        else:
            timestamp = _time.to_bytes(4, "big")
        bits = bytes.fromhex(bits)
        nonce = nonce.to_bytes(4, "big")
        return cls(version_hex, prev_hash, mr, timestamp, bits, nonce, height)

    @property
    def hash(self) -> bytes:
        # after converting each element to little-endian bytes
        header_bytes = self.serialize()
        # calc hash, and return big-endian hash
        return hashlib.sha256(hashlib.sha256(header_bytes).digest()).digest()[::-1]

    @property
    def bits(self) -> int:
        return int.from_bytes(self.__bits, "big")

    @bits.setter
    def bits(self, bits: int):
        self.__bits = bits.to_bytes(4, byteorder="big")

    @property
    def nonce(self):
        return int.from_bytes(self.__nonce, "big")

    @nonce.setter
    def nonce(self, nonce: int):
        self.__nonce = nonce.to_bytes(4, "big")

    @property
    def prev_hash(self) -> str:
        return self.__prev_hash.hex()

    @prev_hash.setter
    def prev_hash(self, prev_hash_big_hex: str):
        if prev_hash_big_hex.startswith("0x"):
            self.__prev_hash = bytes.fromhex(prev_hash_big_hex[2:])
        else:
            self.__prev_hash = bytes.fromhex(prev_hash_big_hex)

    @property
    def time(self) -> int:
        return int.from_bytes(self.__time, "big")

    @time.setter
    def time(self, time: int):
        self.__time = time.to_bytes(4, byteorder="big")

    @property
    def height(self) -> int:
        return self._height

    @property
    def raw_header_str(self) -> str:
        return self.serialize().hex()

    def to_dict(self) -> dict:
        ret = dict()
        ret["versionHex"] = self.version.hex()
        ret["previousblockhash"] = self.__prev_hash.hex()
        ret["merkleroot"] = self.merkle_root.hex()
        ret["time"] = int.from_bytes(self.__time, "big")
        ret["bits"] = self.__bits.hex()
        ret["nonce"] = int.from_bytes(self.__nonce, "big")
        ret["height"] = self.height
        return ret


class BitcoinHeaderTest(TestCase):
    my_abspath = os.path.dirname(os.path.abspath(__file__))

    def test_header_constructor1(self):
        test_jsons = BitcoinHeaderTest.get_test_json("test_data/blocks")

        for test_dict in test_jsons:
            version: str = test_dict["versionHex"]
            prev_hash: str = test_dict["previousblockhash"]
            merkle_root: str = test_dict["merkleroot"]
            bits: str = test_dict["bits"]
            nonce: int = test_dict["nonce"]
            _time: int = test_dict["time"]

            expected_hash: str = test_dict["hash"]

            header = Header.new_by_elements(version, prev_hash, merkle_root, bits, nonce, _time)
            header_hash = header.hash.hex()
            self.assertEqual(expected_hash, header_hash)

    def test_header_constructor2(self):
        expected_hash = list()
        test_jsons = BitcoinHeaderTest.get_test_json("test_data/blocks")
        for test_dict in test_jsons:
            expected_hash.append(test_dict["hash"])

        test_jsons = BitcoinHeaderTest.get_test_json("test_data/headers")
        for test_dict in test_jsons:
            header_str: str = test_dict["result"]
            header = Header.parse_from_str(header_str)
            header_hash = header.hash.hex()

            self.assertTrue(header_hash in expected_hash)

    @staticmethod
    def get_test_json(test_dir_name: str) -> list:
        test_file_path = BitcoinHeaderTest.my_abspath + "/" + test_dir_name + "/"
        test_file_names = os.listdir(test_file_path)
        if "__init__.py" in test_file_names:
            test_file_names.remove("__init__.py")

        ret = list()
        for path in test_file_names:
            with open(test_file_path + path) as json_data:
                ret.append(json.load(json_data))
        return ret
