class BTCBytes:
    def __init__(self, big_bytes: bytes):
        if not isinstance(big_bytes, bytes):
            raise Exception("Wrong input format. expected: {}, acture: {}".format("bytes", type(big_bytes)))
        self._big_bytes = big_bytes  # store as big endian

    def __repr__(self):
        return "be({})".format(self. _big_bytes.hex())

    def __add__(self, other):
        if not BTCBytes.type_check(other):
            raise Exception("other type is not BTCBytes")
        return BTCBytes(self.bytes_as_be + other.bytes_as_be)

    def __eq__(self, other):
        if not BTCBytes.type_check(other):
            raise Exception("other type is not BTCBytes")
        return self.bytes_as_be == other.bytes_as_be

    def __ne__(self, other):
        if not BTCBytes.type_check(other):
            raise Exception("other type is not BTCBytes")
        return not self == other

    @classmethod
    def from_little_bytes(cls, little_bytes: bytes):
        return cls(little_bytes[::-1])

    @classmethod
    def from_big_hex(cls, big_hex: str):
        if big_hex.startswith("0x"):
            big_hex = big_hex[2:]
        data = bytes.fromhex(big_hex)
        return cls(data)

    @classmethod
    def from_little_hex(cls, little_hex: str):
        if little_hex.startswith("0x"):
            little_hex = little_hex[2:]
        data = bytes.fromhex(little_hex)[::-1]
        return cls(data)

    @property
    def bytes_as_be(self) -> bytes:
        """ return big endian bytes """
        return self._big_bytes

    @property
    def bytes_as_le(self) -> bytes:
        """ return little endian bytes"""
        return self._big_bytes[::-1]

    @property
    def hex_as_be(self):
        """ return big endian hex """
        return "0x" + self.bytes_as_be.hex()

    @property
    def hex_as_le(self):
        """ return little endian hex """
        return "0x" + self.bytes_as_le.hex()

    @property
    def int(self):
        return int.from_bytes(self.bytes_as_be, 'big')

    @staticmethod
    def type_check(other):
        return True if isinstance(other, BTCBytes) else False
