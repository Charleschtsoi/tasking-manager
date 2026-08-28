"""Unit tests for sandbox PBF export path helpers (no DuckDB/S3 required)."""

import os
import sys
from types import SimpleNamespace

import pytest

# Allow importing the Windmill script as a module from repo root / tests.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXPORT_DIR = os.path.join(REPO_ROOT, "scripts", "export")
if EXPORT_DIR not in sys.path:
    sys.path.insert(0, EXPORT_DIR)

from pbf_data_export import (  # noqa: E402
    Extractor,
    build_object_key,
    category_slug,
)


@pytest.mark.parametrize(
    "name,expected",
    [
        ("Roads", "roads"),
        ("BUILDINGS", "buildings"),
        ("Landuse", "landuse"),
        (" waterways ", "waterways"),
    ],
)
def test_category_slug_lowercases(name, expected):
    assert category_slug(name) == expected


@pytest.mark.parametrize(
    "rel_key,prefix,expected",
    [
        (
            "TM/hotosm_project_1/roads/lines/hotosm_project_1_roads_lines_geojson.zip",
            "",
            "TM/hotosm_project_1/roads/lines/hotosm_project_1_roads_lines_geojson.zip",
        ),
        (
            os.path.join(
                "TM",
                "hotosm_project_1",
                "buildings",
                "polygons",
                "hotosm_project_1_buildings_polygons_shp.zip",
            ),
            "",
            "TM/hotosm_project_1/buildings/polygons/hotosm_project_1_buildings_polygons_shp.zip",
        ),
        (
            "TM/hotosm_project_1/roads/lines/x.zip",
            "sandbox",
            "sandbox/TM/hotosm_project_1/roads/lines/x.zip",
        ),
        (
            "/TM/hotosm_project_1/roads/lines/x.zip",
            "/sandbox/",
            "sandbox/TM/hotosm_project_1/roads/lines/x.zip",
        ),
    ],
)
def test_build_object_key(rel_key, prefix, expected):
    assert build_object_key(rel_key, prefix) == expected


def test_frontend_download_path_contract_example():
    """Mirror DownloadOsmData URL segments for a sample sandbox project."""
    project_id = 42
    category = category_slug("Buildings")
    geom_type = "polygons"
    fmt = "geojson"
    prefix = f"hotosm_project_{project_id}"
    rel = os.path.join(
        "TM",
        prefix,
        category,
        geom_type,
        f"{prefix}_{category}_{geom_type}_{fmt}.zip",
    )
    assert (
        build_object_key(rel)
        == "TM/hotosm_project_42/buildings/polygons/hotosm_project_42_buildings_polygons_geojson.zip"
    )


def test_export_project_propagates_gdal_copy_failure(tmp_path):
    class CopyError(Exception):
        pass

    class FakeConnection:
        def execute(self, query):
            if query.startswith("SELECT count(*)"):
                return self
            if query.startswith("COPY "):
                raise CopyError("GDAL driver unavailable")
            return self

        def fetchone(self):
            return (1,)

    extractor = Extractor.__new__(Extractor)
    extractor.work_dir = str(tmp_path)
    extractor.map_returns_list = False
    extractor.con = FakeConnection()
    extractor._duckdb = SimpleNamespace(Error=CopyError)

    categories = [
        {
            "Buildings": {
                "types": ["polygons"],
                "select": ["building"],
                "where": "tags['building'] IS NOT NULL",
                "formats": ["geojson"],
            }
        }
    ]

    with pytest.raises(RuntimeError, match="GDAL driver unavailable"):
        extractor.export_project(
            42,
            '{"type":"Polygon","coordinates":[]}',
            {"dataset_folder": "TM"},
            categories,
        )
