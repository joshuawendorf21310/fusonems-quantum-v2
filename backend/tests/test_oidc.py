from types import SimpleNamespace

import pytest

from services.auth import oidc_router
from core.config import settings


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_oidc_login_disabled(client):
    original = settings.OIDC_ENABLED
    settings.OIDC_ENABLED = False
    response = client.get("/api/auth/oidc/login")
    settings.OIDC_ENABLED = original
    assert response.status_code == 403


def test_oidc_callback_flow(monkeypatch, client):
    original_enabled = settings.OIDC_ENABLED
    settings.OIDC_ENABLED = True
    settings.OIDC_ISSUER_URL = "https://issuer.test"
    settings.OIDC_CLIENT_ID = "client"
    settings.OIDC_REDIRECT_URI = "https://backend.test/api/auth/oidc/callback"

    monkeypatch.setattr(oidc_router, "_get_oidc_config", lambda: {
        "authorization_endpoint": "https://issuer.test/auth",
        "token_endpoint": "https://issuer.test/token",
        "jwks_uri": "https://issuer.test/jwks",
    })
    monkeypatch.setattr(oidc_router, "_get_jwks", lambda: {})
    monkeypatch.setattr(
        oidc_router,
        "requests",
        SimpleNamespace(post=lambda *args, **kwargs: DummyResponse({"id_token": "token"})),
    )

    def fake_decode(token, *args, **kwargs):
        if token == "state-token":
            return {"nonce": "abc", "verifier": "ver", "redirect": "/dashboard"}
        return {"email": "user@example.com", "name": "Test User", "sub": "sub", "nonce": "abc", "amr": ["mfa"]}

    monkeypatch.setattr(oidc_router, "jwt", SimpleNamespace(decode=fake_decode, encode=lambda *a, **k: "state-token"))

    response = client.get(
        "/api/auth/oidc/callback?code=code&state=state-token",
        cookies={"oidc_state": "state-token"},
        follow_redirects=False,
    )
    settings.OIDC_ENABLED = original_enabled
    assert response.status_code == 307
