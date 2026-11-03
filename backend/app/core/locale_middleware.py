"""响应本地化中间件：仅在显式请求 `?locale=zh-Hant|en` 时改写 JSON 文案。

纯 ASGI 中间件，而不是 `BaseHTTPMiddleware`，为的是一条硬要求：**默认路径必须逐字节透传**。
`zh-Hans`（缺省）与任何未知 locale 直接 `await self.app(...)`，不缓冲、不重排、不改头，
现有 HTTP golden 与前端夹具录到的真响应因此不可能被这层动到。只有落到 `ACTIVE_LOCALES`
才缓冲整段 JSON、走 `core.locale_i18n.localize` 精确查表、再重发。

挂载点在 `main.py`，装在 CORS 之内（先解 CORS，后本地化）。
"""

from __future__ import annotations

import json
from urllib.parse import parse_qs

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.locale_i18n import ACTIVE_LOCALES, localize, resolve_locale

Headers = list[tuple[bytes, bytes]]

#: 回显用户自撰文本的路径永不做叶子翻译——姓名分析把用户输入的每个汉字原样
#: 作为 `NameChar.char` 叶值返回，若走全局整串查表，会把人名里的「金」「木」
#: 「心」等误翻成五行/牌名。这类路径恒透传（前端 chrome 客户端自译，后端数据不该动）。
_PATH_EXEMPT: tuple[str, ...] = ("/api/v1/name",)


class LocaleMiddleware:
    """按 `?locale=` 本地化 JSON 响应体；默认 locale 原样透传。"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not self._active(scope):
            await self.app(scope, receive, send)
            return

        start: Message | None = None
        chunks: list[bytes] = []
        complete = False

        async def capture(message: Message) -> None:
            nonlocal start, complete
            if message["type"] == "http.response.start":
                start = message
            elif message["type"] == "http.response.body":
                chunks.append(message.get("body", b""))
                complete = not message.get("more_body", False)
            # `http.response.action` / disconnect 之类原样忽略：我们代发最终响应。

        # 下游只看见 capture，攒够再决定是否改写。
        await self.app(scope, receive, capture)

        if start is None or not complete:
            # 未收到 start（异常路径）或响应未收尾（流式未支持）：交回原样，不猜测。
            if start is not None:
                await send(start)
            await send({"type": "http.response.body", "body": b"".join(chunks), "more_body": False})
            return

        localized = self._maybe_localize(start, b"".join(chunks), resolve_locale(self._locale_raw(scope)))
        if localized is None:
            await send(start)
            await send({"type": "http.response.body", "body": b"".join(chunks), "more_body": False})
            return

        body, headers = localized
        await send({"type": "http.response.start", "status": start["status"], "headers": headers})
        await send({"type": "http.response.body", "body": body, "more_body": False})

    @staticmethod
    def _maybe_localize(start: Message, body: bytes, locale: str) -> tuple[bytes, Headers] | None:
        """命中 JSON 且真能本地化时返回 `(新 body, 新 headers)`，否则 None（走透传）。"""
        headers: Headers = list(start.get("headers", []))
        if not _is_json(headers) or _has_content_encoding(headers):
            return None
        try:
            data = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        localized = json.dumps(
            localize(data, locale), ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")
        if localized == body:
            # 全表未命中，字节不变——干脆透传，连 content-length 都不重算。
            return None
        new_headers: Headers = [
            (k, v) for k, v in headers if k.lower() not in (b"content-length", b"content-type")
        ]
        new_headers.append((b"content-length", str(len(localized)).encode("latin-1")))
        new_headers.append((b"content-type", b"application/json"))
        return localized, new_headers

    @staticmethod
    def _active(scope: Scope) -> bool:
        if scope.get("path", "").startswith(_PATH_EXEMPT):
            return False
        return resolve_locale(LocaleMiddleware._locale_raw(scope)) in ACTIVE_LOCALES

    @staticmethod
    def _locale_raw(scope: Scope) -> str | None:
        query: str = scope.get("query_string", b"").decode("latin-1")
        values = parse_qs(query).get("locale")
        return values[0] if values else None


def _header(headers: Headers, name: bytes) -> str | None:
    lowered = name.lower()
    for key, value in headers:
        if key.lower() == lowered:
            return value.decode("latin-1")
    return None


def _is_json(headers: Headers) -> bool:
    content_type = _header(headers, b"content-type") or ""
    return "application/json" in content_type.lower()


def _has_content_encoding(headers: Headers) -> bool:
    return _header(headers, b"content-encoding") is not None
