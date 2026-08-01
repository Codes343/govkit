import httpx
import pytest
import respx

from govkit.http import GovKitClient, UpstreamError

URL = "https://example.gov/api"


@respx.mock
async def test_retries_on_5xx_then_succeeds():
    route = respx.get(URL).mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(503),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    async with GovKitClient("test", max_retries=3, min_interval=0) as client:
        assert await client.get_json(URL) == {"ok": True}
    assert route.call_count == 3


@respx.mock
async def test_does_not_retry_on_4xx_client_errors():
    route = respx.get(URL).mock(return_value=httpx.Response(400))
    async with GovKitClient("test", max_retries=3, min_interval=0) as client:
        with pytest.raises(UpstreamError) as exc:
            await client.get_json(URL)
    assert exc.value.status == 400
    assert route.call_count == 1  # a bad request will never become a good one


@respx.mock
async def test_gives_up_after_max_retries_with_a_readable_error():
    respx.get(URL).mock(return_value=httpx.Response(500))
    async with GovKitClient("grants.gov", max_retries=2, min_interval=0) as client:
        with pytest.raises(UpstreamError, match=r"grants\.gov.*giving up after 3"):
            await client.get_json(URL)


@respx.mock
async def test_honours_retry_after_header(monkeypatch):
    slept: list[float] = []

    async def fake_sleep(delay: float) -> None:
        slept.append(delay)

    monkeypatch.setattr("govkit.http.asyncio.sleep", fake_sleep)
    respx.get(URL).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "7"}),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    async with GovKitClient("test", max_retries=2, min_interval=0) as client:
        await client.get_json(URL)

    assert 7.0 in slept


@respx.mock
async def test_non_json_body_raises_upstream_error_not_a_json_traceback():
    respx.get(URL).mock(return_value=httpx.Response(200, text="<html>maintenance"))
    async with GovKitClient("test", max_retries=0, min_interval=0) as client:
        with pytest.raises(UpstreamError, match="non-JSON"):
            await client.get_json(URL)


@respx.mock
async def test_get_json_drops_none_params():
    route = respx.get(URL).mock(return_value=httpx.Response(200, json={}))
    async with GovKitClient("test", min_interval=0) as client:
        await client.get_json(URL, keyword="ai", agency=None)
    assert route.calls[0].request.url.params["keyword"] == "ai"
    assert "agency" not in route.calls[0].request.url.params
