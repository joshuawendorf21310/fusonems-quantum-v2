import asyncio
import json as json_module
import os
import sys
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlsplit

backend_root = Path(__file__).resolve().parents[1]
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

os.environ["ENV"] = "test"
TEST_DB_URL = "postgresql://postgres:postgres@localhost:5432/fusonems_test"
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["TELEHEALTH_DATABASE_URL"] = TEST_DB_URL
os.environ["FIRE_DATABASE_URL"] = TEST_DB_URL
os.environ["HEMS_DATABASE_URL"] = TEST_DB_URL
os.environ["JWT_SECRET_KEY"] = "test-secret"

from sqlalchemy import text

from core.database import Base, FireBase, HemsBase, TelehealthBase, get_engine, get_hems_engine
from models.user import User
from models.organization import Organization
from main import app


def _normalize_path(path: str) -> tuple[str, str]:
    parsed = urlsplit(path)
    return parsed.path or "/", parsed.query or ""


class SimpleResponse:
    def __init__(self, status_code: int, headers: list[tuple[str, str]], body: bytes):
        self.status_code = status_code
        self.headers = {name.lower(): value for name, value in headers}
        self._body = body

    @property
    def text(self) -> str:
        return self._body.decode("utf-8", "ignore")

    def json(self) -> Any:
        if not self._body:
            return {}
        return json_module.loads(self._body)

    @property
    def cookies(self) -> dict[str, str]:
        cookies_data: dict[str, str] = {}
        raw_cookie = self.headers.get("set-cookie")
        if not raw_cookie:
            return cookies_data
        for line in raw_cookie.split("\n"):
            parsed_cookie = SimpleCookie()
            parsed_cookie.load(line)
            for name, morsel in parsed_cookie.items():
                cookies_data[name] = morsel.value
        return cookies_data


class SimpleSyncClient:
    def __init__(self, app):
        self._app = app
        self.cookies: dict[str, str] = {}

    def _build_cookie_header(self) -> str | None:
        if not self.cookies:
            return None
        return "; ".join(f"{name}={value}" for name, value in self.cookies.items())

    def _store_cookies(self, response: SimpleResponse) -> None:
        for name, value in response.cookies.items():
            self.cookies[name] = value

    def _prepare_headers(self, headers: dict[str, str], include_cookie: bool) -> list[tuple[bytes, bytes]]:
        header_list: list[tuple[bytes, bytes]] = []
        for key, value in headers.items():
            header_list.append((key.lower().encode(), value.encode()))
        if include_cookie:
            cookie_header = self._build_cookie_header()
            if cookie_header:
                header_list.append((b"cookie", cookie_header.encode()))
        return header_list

    def _encode_body(
        self,
        json_payload: Any,
        data: Any,
        headers: dict[str, str],
    ) -> tuple[bytes, dict[str, str]]:
        body = b""
        if json_payload is not None:
            body = json_module.dumps(json_payload).encode("utf-8")
            headers.setdefault("content-type", "application/json")
        elif data is not None:
            if isinstance(data, dict):
                body = urlencode(data).encode("utf-8")
            elif isinstance(data, str):
                body = data.encode("utf-8")
            else:
                body = bytes(data)
            headers.setdefault("content-type", "application/x-www-form-urlencoded")
        return body, headers

    def _build_scope(
        self,
        method: str,
        path: str,
        headers: list[tuple[bytes, bytes]],
        query_string: str,
    ) -> dict[str, Any]:
        target_path, existing_qs = _normalize_path(path)
        parts: list[str] = []
        if query_string:
            parts.append(query_string)
        if existing_qs:
            parts.append(existing_qs)
        final_qs = "&".join(parts) if parts else ""
        return {
            "type": "http",
            "http_version": "1.1",
            "method": method.upper(),
            "scheme": "http",
            "path": target_path,
            "raw_path": target_path.encode("utf-8"),
            "query_string": final_qs.encode("utf-8"),
            "headers": headers,
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
            "root_path": "",
            "extensions": {},
        }

    def _send(self, scope: dict[str, Any], body: bytes) -> SimpleResponse:
        request_sent = False
        response_status = 500
        response_headers: list[tuple[str, str]] = []
        body_chunks: list[bytes] = []

        async def receive() -> dict[str, Any]:
            nonlocal request_sent
            if not request_sent:
                request_sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.disconnect"}

        async def send(message: dict[str, Any]) -> None:
            nonlocal response_status, response_headers
            if message["type"] == "http.response.start":
                print("send start", message, flush=True)
                response_status = message["status"]
                response_headers = [
                    (key.decode(), value.decode()) for key, value in message.get("headers", [])
                ]
            elif message["type"] == "http.response.body":
                print("send body", message, flush=True)
                chunk = message.get("body", b"")
                if chunk:
                    body_chunks.append(chunk)

        asyncio.run(self._app(scope, receive, send))
        response = SimpleResponse(response_status, response_headers, b"".join(body_chunks))
        self._store_cookies(response)
        return response

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
        params: dict[str, Any] | None = None,
    ) -> SimpleResponse:
        req_headers = dict(headers or {})
        body, req_headers = self._encode_body(json, data, req_headers)
        query_string = ""
        if params:
            query_string = urlencode(params, doseq=True)
        header_list = self._prepare_headers(req_headers, include_cookie=True)
        scope = self._build_scope(method, path, header_list, query_string)
        return self._send(scope, body)

    def get(self, path: str, *, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None) -> SimpleResponse:
        return self.request("GET", path, headers=headers, params=params)

    def post(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
        params: dict[str, Any] | None = None,
    ) -> SimpleResponse:
        return self.request("POST", path, headers=headers, json=json, data=data, params=params)

    def put(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
    ) -> SimpleResponse:
        return self.request("PUT", path, headers=headers, json=json, data=data)

    def patch(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
    ) -> SimpleResponse:
        return self.request("PATCH", path, headers=headers, json=json, data=data)

    def delete(self, path: str, *, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None) -> SimpleResponse:
        return self.request("DELETE", path, headers=headers, params=params)


def _reset_schema():
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    FireBase.metadata.drop_all(bind=engine)
    TelehealthBase.metadata.drop_all(bind=engine)
    hems_engine = get_hems_engine()
    HemsBase.metadata.drop_all(bind=hems_engine)


def _prepare_schema():
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    # Ensure HEMS schema exists before creating tables that reference it
    hems_engine = get_hems_engine()
    with hems_engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS hems"))
    # ensure org/user tables exist before dependent schemas
    Organization.__table__.create(bind=engine, checkfirst=True)
    User.__table__.create(bind=engine, checkfirst=True)
    TelehealthBase.metadata.create_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    FireBase.metadata.create_all(bind=engine)
    HemsBase.metadata.create_all(bind=hems_engine)


def create_test_client():
    print("TESTCLIENT: resetting schema", flush=True)
    _reset_schema()
    print("TESTCLIENT: preparing schema", flush=True)
    _prepare_schema()
    print("TESTCLIENT: schema ready", flush=True)
    return SimpleSyncClient(app)


def drop_test_db():
    _reset_schema()


import pytest


@pytest.fixture()
def client():
    client = create_test_client()
    try:
        yield client
    finally:
        drop_test_db()
