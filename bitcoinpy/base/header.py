from io import BytesIO
from unittest import TestCase
import json
import hashlib


class Header:
    def __init__(self, version: bytes, prev_hash: bytes, merkle_root: bytes, _time: bytes, bits: bytes, nonce: bytes, height: int = 0):
        """ store elements in big endian bytes"""
        self.__version: bytes = version
        self.__prev_hash: bytes = prev_hash
        self.__merkle_root: bytes = merkle_root
        self.__bits: bytes = bits
        self.__nonce: bytes = nonce
        self.__time: bytes = _time
        self._height: int = height

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
        result = self.__version[::-1]
        result += self.__prev_hash[::-1]
        result += self.__merkle_root[::-1]
        result += self.__time[::-1]
        result += self.__bits[::-1]
        result += self.__nonce[::-1]
        return result

    @property
    def version(self) -> int:
        return int.from_bytes(self.__version, "big")

    @property
    def prev_hash(self) -> str:
        return self.__prev_hash.hex()

    @property
    def merkle_root(self) -> str:
        return self.__merkle_root.hex()

    @property
    def time(self) -> int:
        return int.from_bytes(self.__time, "big")

    @property
    def bits(self) -> int:
        return int.from_bytes(self.__bits, "big")

    @property
    def hash(self) -> bytes:
        # after converting each element to little-endian bytes
        header_bytes = self.serialize()
        # calc hash, and return big-endian hash
        return hashlib.sha256(hashlib.sha256(header_bytes).digest()).digest()[::-1]

    @property
    def nonce(self):
        return int.from_bytes(self.__nonce, "big")

    @property
    def height(self) -> int:
        return self._height

    @property
    def target(self) -> int:
        exp = (self.bits & 0xff000000) >> 24
        coef = self.bits & 0x00ffffff
        return coef * 256 ** (exp - 3)

    @version.setter
    def version(self, value: int):
        if isinstance(value, int):
            raise Exception("Expected type: {}, but {}".format("int", type(value)))
        self.__version = value.to_bytes(4, byteorder="big")

    @prev_hash.setter
    def prev_hash(self, value_big_hex: str):
        if value_big_hex.startswith("0x"):
            self.__prev_hash = bytes.fromhex(value_big_hex[2:])
        else:
            self.__prev_hash = bytes.fromhex(value_big_hex)

    @merkle_root.setter
    def merkle_root(self, value_big_hex: str):
        if value_big_hex.startswith("0x"):
            self.__merkle_root = bytes.fromhex(value_big_hex[2:])
        else:
            self.__merkle_root = bytes.fromhex(value_big_hex)

    @time.setter
    def time(self, value: int):
        if isinstance(value, int):
            raise Exception("Expected type: {}, but {}".format("int", type(value)))
        self.__time = value.to_bytes(4, byteorder="big")

    @bits.setter
    def bits(self, value: int):
        if isinstance(value, int):
            raise Exception("Expected type: {}, but {}".format("int", type(value)))
        self.__bits = value.to_bytes(4, byteorder="big")

    @nonce.setter
    def nonce(self, value: int):
        if isinstance(value, int):
            raise Exception("Expected type: {}, but {}".format("int", type(value)))
        self.__nonce = value.to_bytes(4, "big")

    def raw_header_str(self) -> str:
        return self.serialize().hex()

    def to_dict(self) -> dict:
        ret = dict()
        ret["versionHex"] = self.__version.hex()
        ret["previousblockhash"] = self.__prev_hash.hex()
        ret["merkleroot"] = self.__merkle_root.hex()
        ret["time"] = int.from_bytes(self.__time, "big")
        ret["bits"] = self.__bits.hex()
        ret["nonce"] = int.from_bytes(self.__nonce, "big")
        ret["height"] = self.height
        return ret

    def raw_parse_by_element_name(self, element_name: str) -> bytes:
        if element_name == "version":
            return self.__version[::-1]
        elif element_name == "prev_hash":
            return self.__prev_hash[::-1]
        elif element_name == "merkle_root":
            return self.__merkle_root[::-1]
        elif element_name == "time":
            return self.__time[::-1]
        elif element_name == "bits":
            return self.__bits[::-1]
        elif element_name == "nonce":
            return self.__nonce[::-1]
        raise Exception("Unknown element")

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
        self.assertEqual(hex(header.version), "0x" + HeaderTest.block645120_dict["versionHex"])
        self.assertEqual(header.prev_hash, "000000000000000000049a66ca322371799e1cb51d85c8937764ba6a2abb8ed9")
        self.assertEqual(header.merkle_root, "2d8a7321a253d53a3987ed4a1a8f1182e9c6654fdf02ab8ec62362f52a76e1a3")
        self.assertEqual(header.time, HeaderTest.block645120_dict["time"])
        self.assertEqual(hex(header.bits), "0x" + HeaderTest.block645120_dict["bits"])
        self.assertEqual(header.nonce, HeaderTest.block645120_dict["nonce"])

    def test_header_parsing_from_dict(self):
        header = Header.from_dict(HeaderTest.block645120_dict)
        self.assertEqual(header.raw_header_str(), HeaderTest.block645120_str)
