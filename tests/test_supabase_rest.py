import json

import httpx
import pytest

from xscanner.server.supabase_rest import SupabaseRestClient, SupabaseRestConfig


@pytest.mark.asyncio
async def test_supabase_storage_upload_and_insert_are_called_with_expected_headers_and_paths():
    seen: list[tuple[str, str, dict[str, str], bytes]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(
            (
                request.method,
                str(request.url),
                dict(request.headers),
                request.content or b"",
            )
        )

        if request.url.path.startswith("/storage/v1/object/extractions/"):
            return httpx.Response(200, json={"Key": request.url.path})

        if request.url.path == "/rest/v1/extraction":
            payload = json.loads(request.content.decode("utf-8"))
            assert payload["storage_path"].startswith("some/")
            return httpx.Response(
                201,
                json=[{"id": payload["id"], "storage_path": payload["storage_path"]}],
            )

        return httpx.Response(404, json={"error": "not found"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        client = SupabaseRestClient(
            SupabaseRestConfig(
                url="https://example.supabase.co",
                service_role_key="svc",
                storage_bucket="extractions",
            ),
            http_client=http,
        )

        await client.upload_object(path="some/file.jpg", content=b"abc", content_type="image/jpeg")
        await client.insert_row(
            table="extraction",
            payload={"id": "1", "original_id": "1", "storage_path": "some/file.jpg"},
        )

    assert len(seen) == 2

    upload = seen[0]
    assert upload[0] == "POST"
    assert "/storage/v1/object/extractions/some/file.jpg" in upload[1]
    assert upload[3] == b"abc"
    assert upload[2]["apikey"] == "svc"
    assert upload[2]["authorization"].startswith("Bearer ")

    insert = seen[1]
    assert insert[0] == "POST"
    assert insert[1].endswith("/rest/v1/extraction")
    assert insert[2]["prefer"] == "return=representation"
    assert insert[2]["content-type"].startswith("application/json")
