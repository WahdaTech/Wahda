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
