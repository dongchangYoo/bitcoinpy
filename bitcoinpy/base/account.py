from bitcoinpy.crypto.secp256k1 import G, BitcoinPoint
from bitcoinpy.crypto.hashes import hash160
from bitcoinpy.utils.bech32 import bech32_decode, bech32_encode
from bitcoinpy.utils.base58 import decode_base58_checksum, encode_base58_checksum

from unittest import TestCase
from enum import Enum


class NetType(Enum):
    MAIN_NET = 1
    TEST_NET = 2
    REG_TEST = 3


class AddrType(Enum):
    LEGACY = "legacy"
    BECH32 = "bech32"
    P2SH_SEGWIT = "p2sh-segwit"


# TODO move constant to constant.py
DEFAULT_ADDRESS_TYPE = AddrType.BECH32
DEFAULT_NETWORK_TYPE = NetType.MAIN_NET


class BTCAccount:
    def __init__(
            self,
            secret: int = None,
            hash160: bytes = None,
            public_key_sec: bytes = None,
            address: str = None,
            addr_type: AddrType = DEFAULT_ADDRESS_TYPE,
            network_type: NetType = DEFAULT_NETWORK_TYPE):

        self._secret: int = secret
        self._hash160: bytes = hash160
        self._public_key_sec: bytes = public_key_sec
        self._address: str = address
        self.addr_type: AddrType = addr_type
        self.network_type: NetType = network_type

    def __repr__(self):
        return "Address(addr={})".format(self.address)

    @classmethod
    def from_secret(cls, secret: int, addr_type: AddrType = None, network_type: NetType = None):
        """ Initiate Account Object by Secret Key (256-bit random Integer) """
        if secret.bit_length() > 256:
            raise Exception("Too big secret: {}".format(secret.bit_length()))
        if addr_type is None:
            addr_type = DEFAULT_ADDRESS_TYPE
        if network_type is None:
            network_type = DEFAULT_NETWORK_TYPE
        point: BitcoinPoint = secret * G
        return cls(secret=secret, public_key_sec=point.sec(True), addr_type=addr_type, network_type=network_type)

    @classmethod
    def from_wif_key(cls, encoded_private_key: str, address_type: AddrType = None):
        # decode wif key
        # TODO validates base58 functions
        key: bytes = decode_base58_checksum(encoded_private_key)  # decoded without checksum
        # key: bytes = base58.b58decode_check(encoded_private_key)  # decoded without checksum

        if key[0] == 0x80:
            network_type = NetType.MAIN_NET
        elif key[0] == 0xef:
            network_type = NetType.TEST_NET
        else:
            raise Exception("Invalid WIF")

        if address_type is None:
            address_type = DEFAULT_ADDRESS_TYPE

        if len(key) == 34 and key[-1] == 0x01:
            key = key[1:-1]  # remove prefix 1 byte and suffix 1 byte
        if len(key) == 33:
            key = key[1:]  # remove prefix 1 byte

        secret = int.from_bytes(key, byteorder="big")
        point: BitcoinPoint = secret * G
        return cls(secret=secret, public_key_sec=point.sec(True), addr_type=address_type, network_type=network_type)

    @classmethod
    def from_h160(cls, h160: bytes, addr_type: AddrType = None, network_type: NetType = None):
        if addr_type is None:
            addr_type = DEFAULT_ADDRESS_TYPE
        if network_type is None:
            network_type = DEFAULT_NETWORK_TYPE
        return cls(hash160=h160, addr_type=addr_type, network_type=network_type)

    @classmethod
    def from_public_key_sec(cls, public_key_sec: bytes, addr_type: AddrType = None, network_type: NetType = None):
        if addr_type is None:
            addr_type = DEFAULT_ADDRESS_TYPE
        if network_type is None:
            network_type = DEFAULT_NETWORK_TYPE
        return cls(public_key_sec=public_key_sec,addr_type=addr_type, network_type=network_type)

    @classmethod
    def from_address(cls, address: str):
        if address[0] == "1":
            addr_type = AddrType.LEGACY
            network = NetType.MAIN_NET
        elif address[0] == "n" or address[0] == "m":
            addr_type = AddrType.LEGACY
            network = NetType.TEST_NET
        elif address[:2] == "bc" and address[:4] != "bcrt":
            addr_type = AddrType.BECH32
            network = NetType.MAIN_NET
        elif address[:2] == "tb":
            addr_type = AddrType.BECH32
            network = NetType.TEST_NET
        elif address[:4] == "bcrt":
            addr_type = AddrType.BECH32
            network = NetType.REG_TEST
        else:
            raise Exception("Invalid or not supported address")

        if addr_type == AddrType.LEGACY:
            h160 = decode_base58_checksum(address)[1:]
            # h160 = b58decode_check(address)[1:]
        elif addr_type == AddrType.BECH32:
            if network == NetType.REG_TEST: hrp = "bcrt"
            elif network == NetType.TEST_NET: hrp = "tb"
            elif network == NetType.MAIN_NET: hrp = "bc"
            else: raise Exception("Invalid address")
            _, witprog = bech32_decode(hrp, address)
            h160 = bytes(witprog)
        else:
            raise Exception("Not supported addr type")

        return cls(hash160=h160, addr_type=addr_type, network_type=network)

    @property
    def secret(self) -> int:
        return self._secret

    @property
    def wif(self, compressed: bool = True) -> str:
        secret_bytes = self._secret.to_bytes(32, 'big')
        if self.network_type == NetType.MAIN_NET:
            prefix = b'\x80'
        else:
            prefix = b'\xef'

        # append b'\x01' if compressed
        if compressed:  # TODO is it necessary?
            suffix = b'\x01'
        else:
            suffix = b''

        return encode_base58_checksum(prefix + secret_bytes + suffix)
        # return b58encode_check(prefix + secret_bytes + suffix).decode()

    @property
    def hash(self) -> bytes:
        if self._hash160 is not None:
            return self._hash160
        if self._public_key_sec is not None:
            self._hash160 = hash160(self._public_key_sec)
            return self._hash160
        raise Exception("No hash160 and pubkey_sec")

    @property
    def address(self) -> str:
        if self._address is not None:
            return self._address

        if self.addr_type == AddrType.LEGACY:
            if self.network_type == NetType.MAIN_NET: version: bytes = b'\x00'
            elif self.network_type == NetType.TEST_NET: version: bytes = b'\x6F'
            elif self.network_type == NetType.REG_TEST: version: bytes = b'\x6F'
            else: raise Exception("Invalid or not supproted address type")

            self._address = encode_base58_checksum(version + self.hash)
            # self._address = base58.b58encode_check(version + self.hash).decode()
            return self._address

        if self.addr_type == AddrType.BECH32:
            # determine hrp
            if self.network_type == NetType.MAIN_NET: hrp = "bc"
            elif self.network_type == NetType.TEST_NET: hrp = "tb"
            else: hrp = "bcrt"
            # bech32 encode
            wit_prog = [int(item) for item in self.hash]
            self._address = bech32_encode(hrp, 0, wit_prog)
            return self._address

    @property
    def pubkey_sec(self) -> bytes:
        return self._public_key_sec


class BitcoinAddressTest(TestCase):
    def test_regtest_account(self):
        regtest_legacy_wif = "cPJvsCQVicdvwCCmSnYtZzGkzGrXZCWAR94ezWeSZAJPQhVYucgg"
        regtest_legacy_addr = "n2NiuUFWdxV2rB72Ky7UkCKepBziKXJrmZ"

        acc1 = BTCAccount.from_wif_key(regtest_legacy_wif, AddrType.LEGACY, NetType.REG_TEST)
        acc2 = BTCAccount.from_address(regtest_legacy_addr)
        self.assertEqual(acc1.address, acc2.address)
        self.assertEqual(acc1.hash, acc2.hash)

        regtest_bech32_wif = "cTcvSXfhdTkt2rAeSf5EuFfWp4V3P2yWWw3qLRChMMwRianeegKb"
        regtest_bech32_addr = "bcrt1qsn9rrqturgndtprum52j40qjqq2rjtex8quamf"

        acc3 = BTCAccount.from_wif_key(regtest_bech32_wif, AddrType.BECH32, NetType.REG_TEST)
        acc4 = BTCAccount.from_address(regtest_bech32_addr)
        self.assertEqual(acc3.address, acc4.address)
        self.assertEqual(acc3.hash, acc4.hash)

    def test_mainnet_account(self):
        # bitcoin main-net supports only bech32 addr
        main_bech32_wif = "L1JCsPq7T1eoGtfxuDrwgrV8hxEFGTdKhRtux96h4KtAYNXX7kQF"
        main_bech32_addr = "bc1q0uy8v35g5789y3v846g55uqjdq9u359udq0gc0"

        acc3 = BTCAccount.from_wif_key(main_bech32_wif, AddrType.BECH32)
        acc4 = BTCAccount.from_address(main_bech32_addr)
        self.assertEqual(acc3.address, acc4.address)
        self.assertEqual(acc3.hash, acc4.hash)

    def test_mainnet_account2(self):
        main_legacy_addr = "13LbwCGmxvRrWwFBZGRHBkwF3o7ug8WBcT"
        acc = BTCAccount.from_address(main_legacy_addr)
        print(acc.address)
        # self.assertEqual(acc3.address, acc4.address)
        # self.assertEqual(acc3.hash, acc4.hash)

    def test_testnet_account(self):
        # bitcoin test-net supports only bech32 addr
        test_bech32_wif = "cPncuZqx1xm98CnFrjvrvV4XZ2kWELczGWiT9zSC4CwP8WsSaYcn"
        test_bech32_addr = "tb1qqelnteqqdg5jz8p76srdg3tluqmzx7hw6h6hpa"

        acc3 = BTCAccount.from_wif_key(test_bech32_wif, AddrType.BECH32)
        acc4 = BTCAccount.from_address(test_bech32_addr)
        self.assertEqual(acc3.address, acc4.address)
        self.assertEqual(acc3.hash, acc4.hash)
