import time

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.auth import clerk_jwt as m


def test_verify_clerk_jwt_success(monkeypatch: pytest.MonkeyPatch) -> None:
    issuer = "https://example.clerk.accounts.dev"
    audience = "my-audience"
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    pub = key.public_key()
    now = int(time.time())
    payload = {
        "iss": issuer,
        "sub": "user_abc",
        "iat": now,
        "exp": now + 3600,
        "aud": audience,
    }

    token = jwt.encode(payload, priv_pem, algorithm="RS256")

    class FakeSigningKey:
        def __init__(self, key: object) -> None:
            self.key = key

    monkeypatch.setattr(
        m.PyJWKClient,
        "get_signing_key_from_jwt",
        lambda self, tok: FakeSigningKey(pub),
    )

    sub = m.verify_clerk_jwt(
        token,
        clerk_jwks_url="https://example.clerk.accounts.dev/.well-known/jwks.json",
        clerk_issuer=issuer,
        clerk_audience=audience,
    )
    assert sub == "user_abc"
