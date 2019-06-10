import json
from jwcrypto import jwt, jwk, jwe

class DataEncryptor:
    """
        DataEncryptor

        A simple wrapper around the jwcrpto JOSE library
    """
    @staticmethod
    def encrypt(data=None, key=None):
        if key is None:
            raise Exception("A key is needed to encrypt data")

        if data is None:
            raise Exception("Data of null value can not be encrypted")

        key = jwk.JWK(k=key, kty="oct")
        etoken = jwt.JWT(header={"alg": "A256KW", "enc": "A256CBC-HS512"}, claims=data)
        etoken.make_encrypted_token(key)

        return etoken.serialize()

    @staticmethod
    def decrypt(cipher_text=None, key=None):

        if cipher_text is None:
            raise Exception("Token with value not None is needed.")

        if key is None:
            raise Exception("Decryption key is required. None given")

        key = jwk.JWK(k=key, kty="oct")

        try:
            decoded_token = jwt.JWT(key=key, jwt=cipher_text)
        except (jwe.InvalidJWEData, ValueError):
            return False

        return json.loads(decoded_token.claims)

