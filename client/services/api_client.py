"""Тонка обгортка над httpx для запитів до backend. Розширюється в FE-3…FE-9."""
from typing import Any, Optional

import httpx

from config import API_BASE_URL
from state.auth_state import auth_state


class ApiError(Exception):
    def __init__(self, message: str, status: Optional[int] = None) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


class ApiClient:
    def __init__(self, base_url: str = API_BASE_URL, timeout: float = 10.0) -> None:
        self.base_url = base_url
        self.timeout = timeout

    async def request(self, method: str, path: str, *, json: Any = None,
                      params: Optional[dict] = None) -> Any:
        headers = {}
        if auth_state.token:
            headers["Authorization"] = f"Bearer {auth_state.token}"
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.request(method, path, json=json, params=params, headers=headers)
        except httpx.HTTPError:
            raise ApiError("Не вдалося звʼязатися із сервером") from None

        if response.status_code >= 400:
            message = "Сталася помилка"
            try:
                body = response.json()
                message = body.get("detail") or body.get("message") or message
            except ValueError:
                pass
            raise ApiError(str(message), response.status_code)
        return response.json() if response.content else None

    async def get(self, path: str, **kw: Any) -> Any:
        return await self.request("GET", path, **kw)

    async def post(self, path: str, **kw: Any) -> Any:
        return await self.request("POST", path, **kw)

    async def patch(self, path: str, **kw: Any) -> Any:
        return await self.request("PATCH", path, **kw)

    async def delete(self, path: str, **kw: Any) -> Any:
        return await self.request("DELETE", path, **kw)


api = ApiClient()
