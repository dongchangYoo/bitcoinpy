from utils.varint import read_varint, encode_varint
from base.opcodes import OP_CODE_NAMES
from io import BytesIO


class Script:
    def __init__(self, cmds=None):
        if cmds is None:
            self.cmds = []
        else:
            self.cmds = cmds

    def __repr__(self):
        result = []
        for cmd in self.cmds:
            if type(cmd) == int:
                if OP_CODE_NAMES.get(cmd):
                    name = OP_CODE_NAMES.get(cmd)
                else:
                    name = 'OP_[{}]'.format(cmd)
                result.append(name)
            else:
                result.append(cmd.hex())
        return ' '.join(result)

    def __add__(self, other):
        return Script(self.cmds + other.cmds)

    @classmethod
    def parse(cls, s):
        length = read_varint(s)
        cmds = []
        count = 0
        while count < length:
            current = s.read(1)
            count += 1
            current_byte = current[0]
            if current_byte >= 1 and current_byte <= 75:
                n = current_byte
                cmds.append(s.read(n))
                count += n
            elif current_byte == 76:
                data_length = int.from_bytes(s.read(1), 'little')
                cmds.append(s.read(data_length))
                count += data_length + 1
            elif current_byte == 77:
                data_length = int.from_bytes(s.read(2), 'little')
                cmds.append(s.read(data_length))
                count += data_length + 2
            else:
                op_code = current_byte
                cmds.append(op_code)
        if count != length:
            raise SyntaxError('parsing script failed')
        return cls(cmds)

    @classmethod
    def parse_coinbase(cls, s: BytesIO):
        length = read_varint(s)
        cmd = s.read(length)
        return cls([-1, cmd])

    def raw_serialize(self):
        if self.cmds[0] == -1:
            raise Exception("This is coinbase input. use \"raw_coinbase_serialize()\"")

        result = b''
        for cmd in self.cmds:
            if type(cmd) == int:
                result += cmd.to_bytes(1, 'little')
            else:
                length = len(cmd)
                if length <= 75:
                    result += length.to_bytes(1, 'little')
                elif length > 75 and length < 0x100:
                    result += int(76).to_bytes(1, 'little')
                    result += length.to_bytes(1, 'little')
                elif length >= 0x100 and length <= 520:
                    result += int(77).to_bytes(1, 'little')
                    result += length.to_bytes(2, 'little')
                else:
                    print(cmd)
                    raise ValueError('too long an cmd')
                result += cmd
        return result

    def raw_coinbase_serialize(self):
        if self.cmds[0] != -1:
            raise Exception("This is not coinbase input. use \"raw_serialize()\"")
        return self.cmds[1]

    def serialize(self):
        if len(self.cmds) == 0:
            return b'\x00'

        if self.cmds[0] == -1:
            result = self.raw_coinbase_serialize()
        else:
            result = self.raw_serialize()
        total = len(result)
        return encode_varint(total) + result
