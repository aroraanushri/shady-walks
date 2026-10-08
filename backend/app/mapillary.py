from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import httpx

MAPILLARY_API = "https://graph.mapillary.com/images"
DEFAULT_LIMIT = 10
MAX_LIMIT = 50


@dataclass(frozen=True)
class MapillaryImage:
    id: str
    longitude: float
    latitude: float
    captured_at: int | None
    thumb_1024_url: str | None
    creator_username: str | None
    attribution: str


class MapillaryError(RuntimeError):
    """Raised when Mapillary cannot provide a valid response."""


def _coordinate(item: dict[str, Any]) -> tuple[float, float] | None:
    geometry = item.get("computed_geometry") or {}
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) != 2:
        return None
    try:
        return float(coordinates[0]), float(coordinates[1])
    except (TypeError, ValueError):
        return None


def parse_images(payload: dict[str, Any]) -> list[MapillaryImage]:
    parsed: list[MapillaryImage] = []
    for item in payload.get("data", []):
        if not isinstance(item, dict) or not item.get("id"):
            continue
        coordinate = _coordinate(item)
        if coordinate is None:
            continue
        creator = item.get("creator") or {}
        username = creator.get("username") if isinstance(creator, dict) else None
        parsed.append(
            MapillaryImage(
                id=str(item["id"]),
                longitude=coordinate[0],
                latitude=coordinate[1],
                captured_at=item.get("captured_at"),
                thumb_1024_url=item.get("thumb_1024_url"),
                creator_username=username,
                attribution=f"Mapillary{f' / {username}' if username else ''}",
            )
        )
    return parsed


def spatial_sample(
    images: list[MapillaryImage], minimum_distance_m: float = 20
) -> list[MapillaryImage]:
    """Keep points separated by an approximate ground distance."""
    if minimum_distance_m <= 0:
        return list(dict.fromkeys(images))
    sampled: list[MapillaryImage] = []
    for image in images:
        is_distant = all(
            (
                ((image.latitude - previous.latitude) * 111_000) ** 2
                + (
                    (image.longitude - previous.longitude)
                    * 111_000
                    * 0.65
                )
                ** 2
            )
            ** 0.5
            >= minimum_distance_m
            for previous in sampled
        )
        if is_distant:
            sampled.append(image)
    return sampled


class MapillaryClient:
    def __init__(
        self,
        token: str | None,
        cache_dir: Path,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 20,
    ) -> None:
        self.token = token
        self.cache_dir = cache_dir
        self.transport = transport
        self.timeout = timeout

    def search(
        self,
        bbox: tuple[float, float, float, float],
        limit: int = DEFAULT_LIMIT,
        minimum_distance_m: float = 20,
    ) -> list[MapillaryImage]:
        if not self.token:
            raise MapillaryError("MAPILLARY_TOKEN is not configured on the backend.")
        if len(bbox) != 4 or bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
            raise MapillaryError("bbox must be west,south,east,north.")
        limit = min(max(1, limit), MAX_LIMIT)
        cache_key = hashlib.sha256(
            f"{','.join(map(str, bbox))}:{limit}:{minimum_distance_m}".encode()
        ).hexdigest()
        cache_path = self.cache_dir / f"{cache_key}.json"
        if cache_path.exists() and time.time() - cache_path.stat().st_mtime < 3600:
            return [MapillaryImage(**item) for item in json.loads(cache_path.read_text())]

        fields = "id,computed_geometry,captured_at,thumb_1024_url,creator"
        params: dict[str, str | int] = {
            "access_token": self.token,
            "bbox": ",".join(map(str, bbox)),
            "fields": fields,
            "limit": limit,
        }
        results: list[MapillaryImage] = []
        next_url: str | None = MAPILLARY_API
        try:
            with httpx.Client(
                timeout=self.timeout, transport=self.transport, follow_redirects=True
            ) as client:
                while next_url and len(results) < limit:
                    response = client.get(
                        next_url, params=params if next_url == MAPILLARY_API else None
                    )
                    response.raise_for_status()
                    page = response.json()
                    results.extend(parse_images(page))
                    next_url = (page.get("paging") or {}).get("next")
                    params = {}
        except (httpx.HTTPError, ValueError) as exc:
            raise MapillaryError(f"Mapillary request failed: {exc}") from exc

        sampled = spatial_sample(results[:limit], minimum_distance_m)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps([asdict(item) for item in sampled]))
        return sampled
