from bitcoinpy.utils.varint import read_varint, encode_varint
from bitcoinpy.base.script import Script
from io import BytesIO
from typing import Union
import os
import json
import hashlib

from unittest import TestCase


class Transaction:
    def __init__(self, tx_ins: list, tx_outs: list, version: int = 0, lock_time: int = 0):
        self.version = version
        self.tx_ins = tx_ins
        self.tx_outs = tx_outs
        self.lock_time = lock_time

    def __repr__(self):
        tx_ins = ''
        for tx_in in self.tx_ins:
            tx_ins += tx_in.__repr__() + '\n'
        tx_outs = ''
        for tx_out in self.tx_outs:
            tx_outs += tx_out.__repr__() + '\n'
        return 'tx: {}\nversion: {}\ntx_ins:\n{}tx_outs:\n{}locktime: {}'.format(
            self.tx_id,
            self.version,
            tx_ins,
            tx_outs,
            self.lock_time,
        )

    @classmethod
    def parse_from_dict(cls, tx: dict):
        tx_hex = tx["hex"]
        tx_io = BytesIO(bytes.fromhex(tx_hex))
        return Transaction.parse_from_bytes_io(tx_io)

    @classmethod
    def parse_from_hex(cls, tx_str: str):
        if tx_str.startswith("0x"):
            tx_str = tx_str[2:]
        tx_io = BytesIO(bytes.fromhex(tx_str))
        return cls.parse_from_bytes_io(tx_io)

    @classmethod
    def parse_from_bytes_io(cls, s: BytesIO):
        version: int = int.from_bytes(s.read(4), 'little')
        if s.read(2) == b"\x00\x01":
            is_segwit: bool = True
        else:
            is_segwit: bool = False
            s.seek(-2, os.SEEK_CUR)

        num_inputs: int = read_varint(s)
        inputs = list()
        for _ in range(num_inputs):
            inputs.append(TxIn.parse(s))

        num_outputs: int = read_varint(s)
        outputs = []
        for _ in range(num_outputs):
            outputs.append(TxOut.parse(s))

        if is_segwit:
            for tx_in in inputs:
                num_items: int = read_varint(s)
                items: list = list()

                for _ in range(num_items):
                    len: int = read_varint(s)
                    if len == 0:
                        items.append(0)
                    else:
                        items.append(s.read(len))
                tx_in.witness = items
        lock_time: int = int.from_bytes(s.read(4), 'little')
        return cls(inputs, outputs, version, lock_time)

    def serialize_legacy(self) -> bytes:
        result = self.version.to_bytes(4, 'little')
        result += encode_varint(len(self.tx_ins))
        for tx_in in self.tx_ins:
            result += tx_in.serialize()
        result += encode_varint(len(self.tx_outs))
        for tx_out in self.tx_outs:
            result += tx_out.serialize()
        result += self.lock_time.to_bytes(4, 'little')
        return result

    @property
    def tx_id(self):
        result = self.serialize_legacy()
        return hashlib.sha256(hashlib.sha256(result).digest()).digest()[::-1]

    @property
    def height(self) -> Union[int, None]:
        return self.tx_ins[0].height

    def is_coinbase(self):
        return self.tx_ins[0].is_coinbase()


class TxIn:
    def __init__(self, prev_tx: bytes, prev_index: int, script_sig: Script = None, sequence=0xffffffff):
        self.prev_tx = prev_tx
        self.prev_index = prev_index
        self.script_sig = script_sig
        if script_sig is None:
            self.script_sig = Script()
        self.sequence = sequence

    def __repr__(self):
        return '{}:{}'.format(
            self.prev_tx.hex(),
            self.prev_index,
        )

    @classmethod
    def parse(cls, s):
        prev_tx = s.read(32)[::-1]  # previous tx id
        prev_index = int.from_bytes(s.read(4), 'little')  # the tx id above
        if prev_tx.hex() == "00" * 32 and prev_index == 0xffffffff:
            script_sig = Script.parse_coinbase(s)
        else:
            script_sig = Script.parse(s)  # scriptSig
        sequence = int.from_bytes(s.read(4), 'little')  # sequence
        return cls(prev_tx, prev_index, script_sig, sequence)

    def serialize(self):
        result = self.prev_tx[::-1]
        result += self.prev_index.to_bytes(4, 'little')
        result += self.script_sig.serialize()
        result += self.sequence.to_bytes(4, 'little')
        return result

    def is_coinbase(self) -> bool:
        # TxIn().prev_tx
        if self.prev_tx == b'\x00' * 32 and self.prev_index == 0xffffffff:
            return True
        return False

    @property
    def height(self) -> Union[int, None]:
        if not self.is_coinbase():
            return None
        s = BytesIO(self.script_sig.cmds[1])
        length = read_varint(s)
        height_little = s.read(length)

        return int.from_bytes(height_little, byteorder="little")


class TxOut:
    def __init__(self, amount: int, script_pubkey: Script):
        self.amount: int = amount
        self.script_pubkey = script_pubkey

    def __repr__(self):
        return '{}:{}'.format(self.amount, self.script_pubkey)

    @classmethod
    def parse(cls, s):
        amount = int.from_bytes(s.read(8), 'little')  # amount
        script_pubkey = Script.parse(s)  # scriptPubkey
        return cls(amount, script_pubkey)

    def serialize(self):
        result = self.amount.to_bytes(8, 'little')
        result += self.script_pubkey.serialize()
        return result


class BTCTransaction(TestCase):
    test_data_dir = os.path.dirname(os.path.abspath(__file__)) + "/test_data/transactions"
    test_file_names = ["mainnet_687454_0.json", "mainnet_688536_0.json", "mainnet_688536_1.json"]

    def setUp(self):
        data_dir = BTCTransaction.test_data_dir
        data_file_names = BTCTransaction.test_file_names
        self.data_height = [int(name.split("_")[1]) for name in data_file_names]

        self.test_data = list()
        for name in data_file_names:
            with open(data_dir + "/" + name, "r") as json_data:
                data = json.load(json_data)
                self.test_data.append(data)

    def test_transaction_height(self):
        expected_data = self.test_data[0]
        expected_height = self.data_height
        tx_obj = Transaction.parse_from_hex(expected_data["hex"])
        # check transaction height
        self.assertEqual(tx_obj.height, expected_height[0])

    def test_transaction_parsing(self):
        for i, expected_data in enumerate(self.test_data):
            tx_obj = Transaction.parse_from_hex(expected_data["hex"])

            expected_ins = expected_data["vin"]
            if tx_obj.is_coinbase() and len(tx_obj.tx_ins) != 1:
                self.assertTrue(False, "tx is coinbase, but has input more than 1")

            if tx_obj.is_coinbase():
                self.assertEqual("00" * 32, tx_obj.tx_ins[0].prev_tx.hex())
                self.assertEqual(4294967295, tx_obj.tx_ins[0].prev_index)
                self.assertEqual(expected_ins[0]["coinbase"], tx_obj.tx_ins[0].script_sig.serialize().hex()[2:])
                self.assertEqual(expected_ins[0]["sequence"], tx_obj.tx_ins[0].sequence)
            else:
                for j, tx_in in enumerate(tx_obj.tx_ins):
                    self.assertEqual(expected_ins[j]["txid"], tx_in.prev_tx.hex())
                    self.assertEqual(expected_ins[j]["vout"], tx_in.prev_index)
                    self.assertEqual(expected_ins[j]["scriptSig"]["asm"], str(tx_in.script_sig))
                    self.assertEqual(expected_ins[j]["sequence"], tx_in.sequence)

            expected_outs = expected_data["vout"]
            for j, tx_out in enumerate(tx_obj.tx_outs):
                self.assertEqual(expected_outs[j]["value"], tx_out.amount / 10**8)
                self.assertEqual(expected_outs[j]["scriptPubKey"]["hex"], tx_out.script_pubkey.serialize().hex()[2:])

            legacy_serialized: bytes = tx_obj.serialize_legacy()
            actual_tx_id = hashlib.sha256(hashlib.sha256(legacy_serialized).digest()).digest()[::-1]
            self.assertEqual(expected_data["txid"], actual_tx_id.hex())