from io import BytesIO
from backend.btc_module.base.bytes import BTCBytes


def read_varint(s: BytesIO) -> int:
    '''read_varint reads a variable integer from bytes'''

    i = s.read(1)[0]
    if i == 0xfd:
        # 0xfd means the next two bytes are the number
        return BTCBytes(s.read(2)).int
    elif i == 0xfe:
        # 0xfe means the next four bytes are the number
        return BTCBytes(s.read(4)).int
    elif i == 0xff:
        # 0xff means the next eight bytes are the number
        return BTCBytes(s.read(8)).int
    else:
        # anything else is just the integer
        return i


def encode_varint(i: int) -> bytes:
    '''encodes an integer as a varint'''
    if i < 0xfd:
        return bytes([i])
    elif i < 0x10000:
        return b'\xfd' + i.to_bytes(2, 'little')
    elif i < 0x100000000:
        return b'\xfe' + i.to_bytes(4, 'little')
    elif i < 0x10000000000000000:
        return b'\xff' + i.to_bytes(8, 'little')
    else:
        raise ValueError('integer too large: {}'.format(i))

