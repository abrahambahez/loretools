import asyncio

import httpx


async def get(
    client: httpx.AsyncClient,
    url: str,
    *,
    params=None,
    attempts: int = 3,
    delay: float = 5.0,
) -> httpx.Response:
    for i in range(attempts):
        r = await client.get(url, params=params)
        if r.is_success:
            return r
        if i < attempts - 1 and r.status_code in (429, 500, 502, 503, 504):
            await asyncio.sleep(delay)
            continue
        r.raise_for_status()
    return r  # unreachable
