"""Strict RSA PKCS#1 v1.5 SHA-256 verification for the pinned update key.

Only SubjectPublicKeyInfo rsaEncryption keys are accepted. No signing or key
generation is implemented here. Python's integer exponentiation handles public
values; the entire expected encoded message is compared, not a suffix.
"""
import base64
import hashlib
import hmac

RSA_OID = bytes.fromhex('06092a864886f70d010101')
SHA256_INFO = bytes.fromhex('3031300d060960864801650304020105000420')


def element(data, offset, tag):
    if offset + 2 > len(data) or data[offset] != tag:
        raise ValueError('Invalid DER key')
    size = data[offset + 1]
    offset += 2
    if size & 128:
        count = size & 127
        if count < 1 or count > 4 or offset + count > len(data) or data[offset] == 0:
            raise ValueError('Invalid DER length')
        size = int.from_bytes(data[offset:offset + count], 'big')
        if size < 128:
            raise ValueError('Noncanonical DER length')
        offset += count
    end = offset + size
    if end > len(data):
        raise ValueError('Truncated DER key')
    return data[offset:end], end


def integer(data, offset):
    value, end = element(data, offset, 2)
    if not value or value[0] & 128 or (len(value) > 1 and value[0] == 0 and not value[1] & 128):
        raise ValueError('Invalid RSA integer')
    return int.from_bytes(value, 'big'), end


def public_numbers(der):
    if not 1 <= len(der) <= 4096:
        raise ValueError('Invalid RSA key size')
    spki, end = element(der, 0, 0x30)
    if end != len(der):
        raise ValueError('Trailing key data')
    algorithm, offset = element(spki, 0, 0x30)
    if algorithm != RSA_OID + b'\x05\x00':
        raise ValueError('Unsupported key algorithm')
    bits, end = element(spki, offset, 3)
    if end != len(spki) or not bits or bits[0] != 0:
        raise ValueError('Invalid RSA bit string')
    key, end = element(bits[1:], 0, 0x30)
    if end != len(bits) - 1:
        raise ValueError('Trailing RSA data')
    modulus, offset = integer(key, 0)
    exponent, end = integer(key, offset)
    if end != len(key) or not 2048 <= modulus.bit_length() <= 8192 or modulus % 2 != 1:
        raise ValueError('Invalid RSA modulus')
    if exponent < 3 or exponent % 2 != 1 or exponent.bit_length() > 32:
        raise ValueError('Invalid RSA exponent')
    return modulus, exponent


def verify(data, encoded, der):
    try:
        signature = base64.b64decode(encoded, validate=True)
        modulus, exponent = public_numbers(der)
        length = (modulus.bit_length() + 7) // 8
        number = int.from_bytes(signature, 'big')
        if len(signature) != length or number >= modulus:
            raise ValueError('Invalid signature length or range')
        actual = pow(number, exponent, modulus).to_bytes(length, 'big')
        digest = SHA256_INFO + hashlib.sha256(data).digest()
        padding = length - len(digest) - 3
        if padding < 8:
            raise ValueError('Invalid signature padding')
        expected = b'\x00\x01' + b'\xff' * padding + b'\x00' + digest
        if not hmac.compare_digest(actual, expected):
            raise ValueError('Signature mismatch')
    except (ValueError, TypeError, OverflowError) as error:
        raise ValueError('Update signature is invalid') from error
