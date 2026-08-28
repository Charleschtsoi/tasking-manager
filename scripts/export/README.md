# Sandbox / OSM PBF data export (Windmill)

Self-contained script that clips a dated `.osm.pbf` to active Tasking Manager
project boundaries and uploads GeoJSON / SHP / KML zips for the project detail
**Download OSM Data** UI.

Based on [hotosm/tasking-manager#7275](https://github.com/hotosm/tasking-manager/pull/7275),
with fixes so object keys match the existing frontend contract.

## Frontend path contract

`frontend/src/components/projectDetail/downloadOsmData.js` requests:

```text
{EXPORT_TOOL_S3_URL}/TM/hotosm_project_{id}/{category}/{geom_type}/
  hotosm_project_{id}_{category}_{geom_type}_{format}.zip
```

Examples:

```text
TM/hotosm_project_42/buildings/polygons/hotosm_project_42_buildings_polygons_geojson.zip
TM/hotosm_project_42/roads/lines/hotosm_project_42_roads_lines_shp.zip
```

`category` is always lowercase (`roads`, `buildings`, `waterways`, `landuse`).

This script lowercases category path segments and, by default, writes keys with
**no** extra top-level prefix so the current UI works without frontend changes
once objects are in the bucket behind `EXPORT_TOOL_S3_URL`.

## Windmill usage

1. Create a Python script in Windmill and paste `pbf_data_export.py`.
2. Ensure worker packages: `duckdb>=1.1.0`, `boto3`, `requests` (and
   optionally `quackosm` if `engine="quackosm"`).
3. Schedule `main(...)` with at least:

| Arg | Typical sandbox value |
|---|---|
| `pbf_bucket` | Bucket that receives daily sandbox OSM dumps |
| `pbf_filename` | e.g. `sandbox-export.pbf` under `exports/<date>/` |
| `tm_api_base_url` | e.g. `https://tasks.hotosm.org/api/v2` |
| `sandbox` | `true` (uses `/projects/queries/active/?sandbox=true`) |
| `output_bucket` | Same bucket (or CDN origin) as `EXPORT_TOOL_S3_URL` |
| `sandbox_prefix` | Leave empty for UI-compatible keys |

4. Confirm dated PBFs exist at `s3://{pbf_bucket}/exports/{YYYY-MM-DD}/{pbf_filename}`
   before the job runs (`pbf_date_offset_days=1` targets yesterday by default).

## Local dry-run

```bash
# After installing duckdb/boto3/requests, invoke main with output_local_dir set
# and boundary_source="static" plus a small FeatureCollection to avoid S3 uploads.
python -c "from scripts.export.pbf_data_export import category_slug, build_object_key; \
print(category_slug('Roads')); print(build_object_key('TM/hotosm_project_1/roads/lines/x.zip'))"
```

## Relationship to TM-Extractor

Production (non-sandbox) projects still use
[hotosm/tm-extractor](https://github.com/hotosm/tm-extractor) + raw-data-api.
Sandbox projects are excluded from that feed (`sandbox=false` by default on
`/projects/queries/active/`). This script is the sandbox counterpart: it reads
sandbox PBFs and the `sandbox=true` active-projects list.
