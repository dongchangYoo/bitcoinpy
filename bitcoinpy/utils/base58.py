from bitcoinpy.crypto import hash256
import base58
BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def encode_base58(s: bytes) -> str:
    # determine how many 0s in front of input
    if not isinstance(s, bytes):
        raise Exception("input must be bytes type")
    count = 0
    for c in s:
        if c == 0:
            count += 1
        else:
            break
    # convert to big endian integer
    num = int.from_bytes(s, 'big')
    prefix = '1' * count
    result = ''
    while num > 0:
        num, mod = divmod(num, 58)
        result = BASE58_ALPHABET[mod] + result
    return prefix + result


def decode_base58(s: str) -> bytes:
    num = 0
    for c in s:
        num *= 58
        num += BASE58_ALPHABET.index(c)

    return num.to_bytes((num.bit_length() + 7) // 8, byteorder='big')


def encode_base58_checksum(s: bytes) -> str:
    """ return encoded data whit checksum """
    if not isinstance(s, bytes):
        raise Exception("input must be bytes type")

    check_sum = hash256(s)[:4]
    return encode_base58(s + check_sum)


def decode_base58_checksum(s: str) -> bytes:
    """
    base58 decoded string with checksum
    :param s: encoded data with checksum
    :return: decoded data
    """

    # combined = decode_base58(s)
    combined = base58.b58decode(s)

    checksum = combined[-4:]

    if hash256(combined[:-4])[:4] != checksum:
        raise ValueError('bad address: {} {}'.format(checksum.hex(), hash256(combined[:-4])[:4].hex()))
    return combined[:-4]
