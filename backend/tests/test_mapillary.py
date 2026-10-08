import json
from pathlib import Path

import httpx
import pytest

from app.mapillary import MapillaryClient, MapillaryError, parse_images, spatial_sample


def test_parse_images_preserves_metadata() -> None:
    images = parse_images(
        {
            "data": [
                {
                    "id": "abc",
                    "computed_geometry": {"coordinates": [73.82, 18.51]},
                    "captured_at": 1700000000000,
                    "thumb_1024_url": "https://example.test/image.jpg",
                    "creator": {"username": "walker"},
                }
            ]
        }
    )

    assert images[0].id == "abc"
    assert images[0].latitude == 18.51
    assert images[0].attribution == "Mapillary / walker"


def test_spatial_sample_reduces_dense_points() -> None:
    payload = [
        {
            "id": str(index),
            "longitude": 73.82 + index * 0.000001,
            "latitude": 18.51,
            "captured_at": None,
            "thumb_1024_url": None,
            "creator_username": None,
            "attribution": "Mapillary",
        }
        for index in range(5)
    ]
    from app.mapillary import MapillaryImage

    assert len(spatial_sample([MapillaryImage(**item) for item in payload], 20)) == 1


def test_search_handles_pagination_and_caches(tmp_path: Path) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if len(calls) == 1:
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": "one",
                            "computed_geometry": {"coordinates": [73.82, 18.51]},
                        }
                    ],
                    "paging": {"next": "https://graph.mapillary.com/images?page=2"},
                },
            )
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "two",
                        "computed_geometry": {"coordinates": [73.821, 18.511]},
                    }
                ]
            },
        )

    client = MapillaryClient("token", tmp_path, transport=httpx.MockTransport(handler))
    images = client.search((73.8, 18.5, 73.9, 18.6), limit=2, minimum_distance_m=1)

    assert [image.id for image in images] == ["one", "two"]
    assert len(calls) == 2
    assert json.loads(next(tmp_path.glob("*.json")).read_text())[0]["id"] == "one"


def test_search_reports_api_failure(tmp_path: Path) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="rate limited")

    client = MapillaryClient("token", tmp_path, transport=httpx.MockTransport(handler))

    with pytest.raises(MapillaryError, match="Mapillary request failed"):
        client.search((73.8, 18.5, 73.9, 18.6))
