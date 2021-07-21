class BTCBytes:
    def __init__(self, little_bytes: bytes):
        if not isinstance(little_bytes, bytes):
            raise Exception("Wrong input format. expected: {}, acture: {}".format("bytes", type(little_bytes)))
        self._little_bytes = little_bytes  # store as little endian

    def __repr__(self):
        return "le({})".format(self._little_bytes.hex())

    def __add__(self, other):
        return BTCBytes(self.little_bytes + other.little_bytes)

    def __eq__(self, other):
        return self.little_bytes == other.little_bytes

    def __ne__(self, other):
        return self.little_bytes != other.little_bytes

    @classmethod
    def from_big_hex(cls, big_hex: str):
        data = bytes.fromhex(big_hex)[::-1]
        return cls(data)

    @property
    def big_bytes(self) -> bytes:
        return self._little_bytes[::-1]

    @property
    def little_bytes(self) -> bytes:
        return self._little_bytes

    @property
    def big_hex(self):
        return "0x" + self._little_bytes[::-1].hex()

    @property
    def little_hex(self):
        return "0x" + self._little_bytes.hex()

    @property
    def int(self):
        return int.from_bytes(self._little_bytes, 'little')