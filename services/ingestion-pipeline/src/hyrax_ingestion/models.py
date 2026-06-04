"""Pydantic v2 data models for the ingestion pipeline.

The models form a small ETL contract:

    RawMaterial      -> what a fetcher/extractor pulls off a supplier page
    PbrTexture       -> a single classified PBR map within a material
    NormalizedMaterial -> the cleaned, deduplicated catalog record
    IngestionResult  -> the run summary emitted by the pipeline
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class MapType(str, Enum):
    """Canonical PBR texture map channels.

    Supplier pages label these inconsistently (e.g. "diffuse", "base color",
    "BaseColor", "col"); normalization collapses those aliases onto these
    canonical members.
    """

    ALBEDO = "albedo"
    NORMAL = "normal"
    ROUGHNESS = "roughness"
    METALLIC = "metallic"
    AO = "ao"
    UNKNOWN = "unknown"


class RawTextureLink(BaseModel):
    """An un-normalized texture link as scraped from a page."""

    model_config = ConfigDict(frozen=True)

    label: str = Field(description="Raw label/anchor text from the page.")
    url: str = Field(description="Raw href to the texture asset.")


class RawMaterial(BaseModel):
    """A material record as extracted directly from a supplier page.

    Values are intentionally messy: units may be in cm or mm, resolutions are
    free-text, and texture labels use vendor-specific naming. Normalization is
    responsible for cleaning these up.
    """

    model_config = ConfigDict(frozen=True)

    supplier: str
    source_url: str
    name: str
    category: str | None = None
    resolution_raw: str | None = Field(
        default=None, description="Free-text resolution, e.g. '4096x4096' or '2K'."
    )
    physical_size_raw: str | None = Field(
        default=None, description="Free-text tileable size, e.g. '200 cm' or '1.5m'."
    )
    tags: tuple[str, ...] = Field(default_factory=tuple)
    texture_links: tuple[RawTextureLink, ...] = Field(default_factory=tuple)


class PbrTexture(BaseModel):
    """A single classified PBR map belonging to a normalized material."""

    model_config = ConfigDict(frozen=True)

    map_type: MapType
    url: str
    original_label: str

    @field_validator("url")
    @classmethod
    def _url_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("texture url must not be blank")
        return v.strip()


class NormalizedMaterial(BaseModel):
    """A cleaned, catalog-ready material with classified PBR maps."""

    model_config = ConfigDict(frozen=True)

    material_id: str = Field(description="Stable content hash used for dedup.")
    supplier: str
    source_url: str
    name: str
    slug: str
    category: str | None = None
    resolution_px: int | None = Field(
        default=None, description="Square resolution in pixels (e.g. 4096)."
    )
    physical_size_cm: float | None = Field(
        default=None, description="Tileable physical size normalized to centimeters."
    )
    tags: tuple[str, ...] = Field(default_factory=tuple)
    textures: tuple[PbrTexture, ...] = Field(default_factory=tuple)

    @property
    def map_types(self) -> tuple[MapType, ...]:
        return tuple(t.map_type for t in self.textures)


class IngestionResult(BaseModel):
    """Summary emitted by a pipeline run."""

    model_config = ConfigDict(frozen=True)

    sources_fetched: int = 0
    raw_materials: int = 0
    normalized_materials: int = 0
    duplicates_dropped: int = 0
    errors: tuple[str, ...] = Field(default_factory=tuple)
    catalog_path: str | None = None

    def as_summary(self) -> str:
        return (
            f"fetched={self.sources_fetched} "
            f"raw={self.raw_materials} "
            f"normalized={self.normalized_materials} "
            f"duplicates_dropped={self.duplicates_dropped} "
            f"errors={len(self.errors)}"
        )
