from io import BytesIO
from unittest import TestCase
import json
import hashlib

from bitcoinpy.base.bytes import BTCBytes


class Header:
    def __init__(self, version: bytes, prev_hash: bytes, merkle_root: bytes, _time: bytes, bits: bytes, nonce: bytes, height: int = 0):
        """ all delivered bytes have big endian form """
        self.__version: BTCBytes = BTCBytes(version)
        self.__prev_hash: BTCBytes = BTCBytes(prev_hash)
        self.__merkle_root: BTCBytes = BTCBytes(merkle_root)
        self.__bits: BTCBytes = BTCBytes(bits)
        self.__nonce: BTCBytes = BTCBytes(nonce)
        self.__time: BTCBytes = BTCBytes(_time)
        self.__height: int = height

    def __repr__(self):
        ret = self.to_dict()
        return json.dumps(ret, indent=4)

    @classmethod
    def from_raw_str(cls, header_str: str):
        s = BytesIO(bytes.fromhex(header_str))
        version = s.read(4)
        prev_hash = s.read(32)
        mr = s.read(32)
        timestamp = s.read(4)
        bits = s.read(4)
        nonce = s.read(4)
        return cls(version[::-1], prev_hash[::-1], mr[::-1], timestamp[::-1], bits[::-1], nonce[::-1])

    @classmethod
    def from_dict(cls, header_dict: dict):
        version_hex = bytes.fromhex(header_dict["versionHex"])
        prev_hash = bytes.fromhex(header_dict["previousblockhash"])
        mr = bytes.fromhex(header_dict["merkleroot"])
        timestamp = header_dict["time"].to_bytes(4, "big")
        bits = bytes.fromhex(header_dict["bits"])
        nonce = header_dict["nonce"].to_bytes(4, "big")
        height = int(header_dict["height"])
        return cls(version_hex, prev_hash, mr, timestamp, bits, nonce, height)

    def serialize(self) -> bytes:
        result = self.__version.bytes_as_le
        result += self.__prev_hash.bytes_as_le
        result += self.__merkle_root.bytes_as_le
        result += self.__time.bytes_as_le
        result += self.__bits.bytes_as_le
        result += self.__nonce.bytes_as_le
        return result

    @property
    def version(self) -> BTCBytes:
        return self.__version

    @property
    def prev_hash(self) -> BTCBytes:
        return self.__prev_hash

    @property
    def merkle_root(self) -> BTCBytes:
        return self.__merkle_root

    @property
    def time(self) -> int:
        return self.__time.int

    @property
    def bits(self) -> int:
        return self.__bits.int

    @property
    def hash(self) -> BTCBytes:
        # after converting each element to little-endian bytes
        header_bytes = self.serialize()
        hash_ = hashlib.sha256(hashlib.sha256(header_bytes).digest()).digest()
        return BTCBytes.from_little_bytes(hash_)

    @property
    def nonce(self) -> int:
        return self.__nonce.int

    @property
    def height(self) -> int:
        return self.__height

    @property
    def target(self) -> int:
        exp = (self.bits & 0xff000000) >> 24
        coef = self.bits & 0x00ffffff
        return coef * 256 ** (exp - 3)

    @version.setter
    def version(self, value: int):
        if not isinstance(value, int):
            raise Exception("Expected type: {}, but {}".format("int", type(value)))
        self.__version = BTCBytes(value.to_bytes(4, byteorder="big"))

    @prev_hash.setter
    def prev_hash(self, value_big_hex: str):
        self.__prev_hash = BTCBytes.from_big_hex(value_big_hex)

    @merkle_root.setter
    def merkle_root(self, value_big_hex: str):
        self.__merkle_root = BTCBytes.from_big_hex(value_big_hex)

    @time.setter
    def time(self, value: int):
        if not isinstance(value, int):
            raise Exception("Expected type: {}, but {}".format("int", type(value)))
        self.__time = BTCBytes(value.to_bytes(4, byteorder="big"))

    @bits.setter
    def bits(self, value: int):
        if not isinstance(value, int):
            raise Exception("Expected type: {}, but {}".format("int", type(value)))
        self.__bits = BTCBytes(value.to_bytes(4, byteorder="big"))

    @nonce.setter
    def nonce(self, value: int):
        if not isinstance(value, int):
            raise Exception("Expected type: {}, but {}".format("int", type(value)))
        self.__nonce = BTCBytes(value.to_bytes(4, byteorder="big"))

    @height.setter
    def height(self, value: int):
        if not isinstance(value, int):
            raise Exception("Expected type: {}, but {}".format("int", type(value)))
        self.__height = value

    def raw_header_str(self) -> str:
        return self.serialize().hex()

    def to_dict(self) -> dict:
        ret = dict()
        ret["versionHex"] = self.__version.hex_as_be
        ret["previousblockhash"] = self.__prev_hash.hex_as_be
        ret["merkleroot"] = self.__merkle_root.hex_as_be
        ret["time"] = self.__time.int
        ret["bits"] = self.__bits.int
        ret["nonce"] = self.__nonce.int
        ret["height"] = self.height
        return ret

    def get_word_of_single_word(self, who: int) -> bytes:
        raw_header = self.serialize()
        return raw_header[who * 16: (who + 1) * 16]


class HeaderTest(TestCase):
    block645120_str = "00e0ff2fd98ebb2a6aba647793c8851db51c9e79712332ca669a04000000000000000000a3e1762af56223c68eab02df4f65c6e982118f1a4aed87393ad553a221738a2d8b7b435fea071017acc0cd5c"
    block645120_dict = {
        'versionHex': '2fffe000',
        'previousblockhash': '000000000000000000049a66ca322371799e1cb51d85c8937764ba6a2abb8ed9',
        'merkleroot': '2d8a7321a253d53a3987ed4a1a8f1182e9c6654fdf02ab8ec62362f52a76e1a3',
        'time': 1598258059,
        'bits': '171007ea',
        'nonce': 1556988076,
        'height': 0
    }

    def test_header_parsing_from_str(self):
        header = Header.from_raw_str(HeaderTest.block645120_str)
        self.assertEqual(header.version.hex_as_be, "0x" + HeaderTest.block645120_dict["versionHex"])
        self.assertEqual(header.prev_hash.hex_as_be, "0x000000000000000000049a66ca322371799e1cb51d85c8937764ba6a2abb8ed9")
        self.assertEqual(header.merkle_root.hex_as_be, "0x2d8a7321a253d53a3987ed4a1a8f1182e9c6654fdf02ab8ec62362f52a76e1a3")
        self.assertEqual(header.time, HeaderTest.block645120_dict["time"])
        self.assertEqual(header.bits, int(HeaderTest.block645120_dict["bits"], 16))
        self.assertEqual(header.nonce, HeaderTest.block645120_dict["nonce"])

    def test_header_parsing_from_dict(self):
        header = Header.from_dict(HeaderTest.block645120_dict)
        self.assertEqual(header.raw_header_str(), HeaderTest.block645120_str)
