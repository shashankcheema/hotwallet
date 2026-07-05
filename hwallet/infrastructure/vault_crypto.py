import base64
import hashlib
import json
import secrets
from typing import Any

from Crypto.Cipher import AES


SALT_BYTES = 16
IV_BYTES = 12
KEY_BYTES = 32
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1


def _b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _b64decode(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


def _zeroize(buffer: bytearray) -> None:
    for index in range(len(buffer)):
        buffer[index] = 0


def _derive_key(password: str, salt: bytes) -> bytearray:
    password_bytes = bytearray(password.encode("utf-8"))
    try:
        return bytearray(
            hashlib.scrypt(
                password=password_bytes,
                salt=salt,
                n=SCRYPT_N,
                r=SCRYPT_R,
                p=SCRYPT_P,
                dklen=KEY_BYTES,
            )
        )
    finally:
        _zeroize(password_bytes)


def encryptWallet(seed_phrase: str, password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    iv = secrets.token_bytes(IV_BYTES)
    key = _derive_key(password, salt)

    seed_bytes = bytearray(seed_phrase.encode("utf-8"))
    try:
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        ciphertext, auth_tag = cipher.encrypt_and_digest(seed_bytes)
    finally:
        _zeroize(seed_bytes)
        _zeroize(key)

    payload = {
        "version": 1,
        "kdf": {
            "name": "scrypt",
            "n": SCRYPT_N,
            "r": SCRYPT_R,
            "p": SCRYPT_P,
            "key_bytes": KEY_BYTES,
        },
        "cipher": {
            "name": "AES-256-GCM",
            "salt": _b64encode(salt),
            "iv": _b64encode(iv),
            "ciphertext": _b64encode(ciphertext),
            "auth_tag": _b64encode(auth_tag),
        },
    }
    return json.dumps(payload, separators=(",", ":"))


def decryptWalletBytes(payload: str | dict[str, Any], password: str) -> bytearray:
    data = json.loads(payload) if isinstance(payload, str) else payload
    cipher_data = data["cipher"]

    salt = _b64decode(cipher_data["salt"])
    iv = _b64decode(cipher_data["iv"])
    ciphertext = _b64decode(cipher_data["ciphertext"])
    auth_tag = _b64decode(cipher_data["auth_tag"])

    key = _derive_key(password, salt)
    plaintext = bytearray()
    try:
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        plaintext.extend(cipher.decrypt_and_verify(ciphertext, auth_tag))
        return plaintext
    finally:
        _zeroize(key)


def decryptWallet(payload: str | dict[str, Any], password: str) -> str:
    plaintext = decryptWalletBytes(payload, password)
    try:
        return plaintext.decode("utf-8")
    finally:
        _zeroize(plaintext)

