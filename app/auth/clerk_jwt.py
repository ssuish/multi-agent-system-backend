from jwt import PyJWKClient
from jwt import decode as jwt_decode


def verify_clerk_jwt(
    token: str, *, clerk_jwks_url: str, clerk_issuer: str, clerk_audience: str | None
) -> str:
    jwks_client = PyJWKClient(clerk_jwks_url)
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    options = {"require": ["exp", "iat", "sub", "iss"]}
    decode_kwargs: dict = {
        "algorithms": ["RS256"],
        "issuer": clerk_issuer,
        "options": options,
    }

    if clerk_audience:
        decode_kwargs["audience"] = clerk_audience
        payload = jwt_decode(
            token,
            signing_key.key,
            **decode_kwargs,
        )

    sub = payload.get("sub")

    if not isinstance(sub, str) or not sub:
        raise ValueError("Invalid token: missing sub")
    return sub
