"""Validated, bounded public API contracts. All coordinates use original image pixels."""
from datetime import date as Date
from typing import Literal
from pydantic import BaseModel, Field, field_validator
from shapely.geometry import Polygon
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

class Region(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    kind: Literal['roof', 'vegetation', 'obstacle'] = 'roof'
    polygon: list[tuple[float, float]] = Field(min_length=3, max_length=150)
    height: float = Field(default=8, ge=0, le=150)
    tilt: float = Field(default=10, ge=0, le=80)
    azimuth: float = Field(default=180, ge=0, le=360)
    confidence: float | None = Field(default=None, ge=0, le=1)
    source: str = Field(default='manual', max_length=120)

    @field_validator('polygon')
    def valid_polygon(cls, value):
        import math
        if not all(math.isfinite(x) and math.isfinite(y) and 0 <= x <= 20000 and 0 <= y <= 20000 for x,y in value):
            raise ValueError('Coordinates must be finite image pixels from 0 to 20000.')
        p = Polygon(value)
        if not p.is_valid or p.area < 1:
            raise ValueError('Polygon must have area and must not cross itself.')
        return value

class Settings(BaseModel):
    latitude: float = Field(default=38.546, ge=-89, le=89)
    longitude: float = Field(default=-121.744, ge=-180, le=180)
    timezone: str = 'America/Los_Angeles'
    date: Date = Date(2026, 6, 21)
    meters_per_pixel: float = Field(default=0.2, ge=0.01, le=10)
    north_angle: float = Field(default=0, ge=-360, le=360)
    coverage: float = Field(default=0.65, ge=0.05, le=0.95)
    efficiency: float = Field(default=0.22, ge=0.1, le=0.3)
    performance_ratio: float = Field(default=0.8, ge=0.4, le=1)
    panel_area: float = Field(default=2, ge=0.5, le=4)
    turbidity: float = Field(default=3, ge=1, le=10)

    @field_validator('timezone')
    def valid_timezone(cls, value):
        try: ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError): raise ValueError('Use an IANA timezone, e.g. Europe/Rome.')
        return value

class SimulationRequest(BaseModel):
    regions: list[Region] = Field(min_length=1, max_length=100)
    settings: Settings

    @field_validator('regions')
    def unique_ids(cls, value):
        if len({r.id for r in value}) != len(value): raise ValueError('Region identifiers must be unique.')
        return value
