import base64
import os

import cryptography.hazmat.primitives.asymmetric.padding as __cryptography_padding
import cryptography.hazmat.primitives.asymmetric.rsa as __cryptography_rsa
import cryptography.hazmat.primitives.hashes as __cryptography_hashes
import cryptography.hazmat.primitives.serialization as __cryptography_serialization

from core import tp

TRSAPrivateKey: tp.TypeAlias = __cryptography_rsa.RSAPrivateKey

__PROTO_V1_PADDING = __cryptography_padding.OAEP(
    mgf=__cryptography_padding.MGF1(algorithm=__cryptography_hashes.SHA256()),
    algorithm=__cryptography_hashes.SHA256(),
    label=None,
)


def rsa_load_pem_from_bytes(
    data: bytes,
) -> TRSAPrivateKey:
    key = __cryptography_serialization.load_pem_private_key(data=data, password=None)

    if not isinstance(key, TRSAPrivateKey):
        raise tp.WDException("Unsupported key type")

    return key


def rsa_decrypt_proto_v1(key: TRSAPrivateKey, ciphertext: bytes) -> bytes:
    return key.decrypt(ciphertext, __PROTO_V1_PADDING)


def decrypt_api_secret_v1(private_key: TRSAPrivateKey, encrypted_secret: str) -> str:
    if not encrypted_secret.startswith("enc_proto_v1."):
        raise tp.WDException("Unknown encryption protocol")

    _, _, key_b64 = encrypted_secret.split(".")
    api_secret = rsa_decrypt_proto_v1(private_key, base64.b64decode(key_b64))

    return bytes(api_secret).decode()


def decrypt_api_secret_v2(encrypted_secret: str) -> str:
    if not encrypted_secret.startswith("enc_proto_v2."):
        raise tp.WDException("Unknown encryption protocol")

    _, private_key_ref, key_b64 = encrypted_secret.split(".")

    private_key_label = f"ENC_PROTO_V2_PRIVATE_KEY_B64_{private_key_ref}"
    private_key_b64 = os.environ.get(private_key_label)

    if private_key_b64 is None:
        raise tp.WDException(f"Private key not set: {private_key_label}")

    private_key = rsa_load_pem_from_bytes(base64.b64decode(private_key_b64))
    api_secret = rsa_decrypt_proto_v1(private_key, base64.b64decode(key_b64))

    return bytes(api_secret).decode()
