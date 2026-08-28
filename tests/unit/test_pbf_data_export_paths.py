"""Unit tests for sandbox PBF export path helpers (no DuckDB/S3 required)."""

import os
import sys

import pytest

# Allow importing the Windmill script as a module from repo root / tests.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXPORT_DIR = os.path.join(REPO_ROOT, "scripts", "export")
if EXPORT_DIR not in sys.path:
    sys.path.insert(0, EXPORT_DIR)

from pbf_data_export import (  # noqa: E402
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
