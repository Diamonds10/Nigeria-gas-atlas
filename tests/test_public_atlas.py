"""Release-gate checks for processed data and the public atlas bundle."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT / "docs" / "assets" / "atlas_data.json"
BUILDER_PATH = ROOT / "scripts" / "build_public_atlas_data.py"
API_DIR = ROOT / "docs" / "api" / "v1"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_public_atlas_data", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PublicAtlasTests(unittest.TestCase):
    def test_committed_bundle_is_reproducible(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as directory:
            rebuilt_path = Path(directory) / "atlas_data.json"
            builder.write_bundle(builder.build_bundle(), rebuilt_path)
            self.assertEqual(
                BUNDLE_PATH.read_bytes(),
                rebuilt_path.read_bytes(),
                "Run: python scripts/build_public_atlas_data.py",
            )

    def test_public_layer_counts(self):
        bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
        layers = bundle["layers"]
        counts = {
            sublayer: len(definition["data"]["features"])
            for layer in layers.values()
            for sublayer, definition in layer["sublayers"].items()
        }
        self.assertEqual(
            counts,
            {
                "fields_oil": 33,
                "fields_gas": 2,
                "fields_mixed": 145,
                "field_polygons_gas": 62,
                "field_polygons_mixed": 62,
                "gas_pipelines": 24,
                "oil_pipelines": 15,
                "lng_terminals": 24,
                "power_plants": 193,
                "refineries": 4,
                "gas_infrastructure": 98,
                "protected_areas": 1005,
                "demand_centers": 28,
                "roads": 5124,
                "railways": 1381,
                "rail_stations": 141,
                "power_grid": 931,
                "substations": 390,
                "ports": 25,
                "minigrids": 80,
                "population_access": 1278,
                "settlements": 1480,
            },
        )

    def test_coordinates_and_required_processed_columns(self):
        checks = {
            "data/processed/01_resource/goget_fields_nigeria_2023-08.csv": {
                "project", "lat", "lng",
            },
            "data/processed/04_demand/demand_centers_nigeria.csv": {
                "demand_center", "lat", "lon",
            },
            "data/processed/07_renewables/renewable_offgrid_minigrid_nigeria.csv": {
                "asset_name", "latitude", "longitude", "status",
            },
            "data/processed/08_context/population_access_grid_nigeria.csv": {
                "cell_id", "grid_lat", "grid_lon", "population_estimate",
                "nightlight_population_share_pct",
            },
            "data/processed/08_context/state_population_access_summary_nigeria.csv": {
                "state", "worldpop_population_2025", "settlement_count",
            },
        }
        for relative_path, required in checks.items():
            frame = pd.read_csv(ROOT / relative_path)
            self.assertTrue(required.issubset(frame.columns))

        minigrids = pd.read_csv(
            ROOT / "data/processed/07_renewables/renewable_offgrid_minigrid_nigeria.csv"
        )
        self.assertTrue(minigrids["longitude"].between(2.5, 14.8).all())
        self.assertTrue(minigrids["latitude"].between(3.9, 14.0).all())
        self.assertTrue(minigrids["asset_id"].is_unique)
        self.assertEqual(len(minigrids), 80)
        self.assertEqual(
            minigrids["record_origin"].value_counts().to_dict(),
            {"nigeria_se4all": 66, "official_supplement": 14},
        )
        kano = minigrids[minigrids["state"] == "Kano"]
        self.assertEqual(len(kano), 2)
        self.assertTrue(
            kano["asset_name"].str.contains("Bayero University").all()
        )

        audit = pd.read_csv(
            ROOT / "data/processed/07_renewables/minigrid_state_coverage_audit.csv"
        )
        self.assertEqual(len(audit), 37)
        self.assertTrue(audit["state"].is_unique)
        self.assertEqual(
            set(audit.loc[audit["catalogued_record_count"].eq(0), "state"]),
            {"Abia", "Borno", "Ekiti", "Enugu", "Imo", "Zamfara"},
        )
        self.assertTrue(
            audit.loc[
                audit["catalogued_record_count"].eq(0), "coverage_interpretation"
            ].str.contains("must not be interpreted as zero assets").all()
        )

        context = pd.read_csv(
            ROOT / "data/processed/08_context/state_population_access_summary_nigeria.csv"
        )
        self.assertEqual(len(context), 37)
        self.assertTrue(context["state"].is_unique)
        self.assertFalse(context["worldpop_population_2025"].isna().any())
        self.assertFalse(context["settlement_count"].isna().any())
        self.assertTrue(context["nightlight_population_share_pct"].between(0, 100).all())

    def test_benchmark_matches_processed_assets(self):
        benchmark = json.loads(
            (ROOT / "outputs/maps/public_asset_benchmark_summary.json").read_text()
        )
        counts = benchmark["asset_counts"]
        self.assertEqual(counts["power_plants"], 193)
        self.assertEqual(counts["substations"], 390)
        self.assertEqual(counts["demand_centres"], 28)
        self.assertEqual(counts["mini_grids"], 80)

    def test_state_profiles_are_complete_and_consistent(self):
        bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
        profiles = bundle["state_profiles"]
        state_names = {
            feature["properties"]["name"]
            for feature in bundle["states"]["features"]
        }
        self.assertEqual(set(profiles), state_names | {"Nigeria"})
        self.assertEqual(len(profiles), 38)

        national = profiles["Nigeria"]
        self.assertEqual(national["mapped_records"], 12525)
        self.assertEqual(national["counts"]["power_plants"], 193)
        self.assertEqual(national["counts"]["substations"], 390)
        self.assertEqual(national["counts"]["minigrids"], 80)
        self.assertAlmostEqual(national["capacity"]["minigrid_kw"], 33680.4)
        self.assertEqual(national["people_access"]["settlement_count"], 154319)
        self.assertAlmostEqual(
            national["people_access"]["worldpop_population_2025"],
            237527782.002,
        )
        for profile in profiles.values():
            self.assertIn("people_access", profile)
            self.assertIn("minigrid_coverage", profile)

        for layer in bundle["layers"].values():
            for definition in layer["sublayers"].values():
                for feature in definition["data"]["features"]:
                    memberships = feature["properties"]["_states"]
                    self.assertTrue(set(memberships).issubset(state_names))

    def test_catalogue_covers_every_public_sublayer(self):
        bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
        catalogue = {item["key"]: item for item in bundle["catalogue"]}
        sublayers = {
            key: definition
            for layer in bundle["layers"].values()
            for key, definition in layer["sublayers"].items()
        }
        self.assertEqual(set(catalogue), set(sublayers))
        for key, definition in sublayers.items():
            metadata = catalogue[key]
            self.assertEqual(metadata, definition["metadata"])
            self.assertEqual(
                metadata["record_count"],
                len(definition["data"]["features"]),
            )
            self.assertIn(metadata["quality"], {"A", "B", "C"})
            self.assertTrue(metadata["download_url"].startswith("https://"))
            self.assertTrue((ROOT / metadata["path"]).exists())

    def test_status_and_temporal_filter_metadata(self):
        bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
        filters = bundle["filters"]
        self.assertEqual(sum(filters["status_groups"].values()), 12525)
        self.assertEqual(
            filters["temporal"]["dated_records"]
            + filters["temporal"]["undated_records"],
            12525,
        )
        self.assertEqual(filters["temporal"]["minimum_year"], 1912)
        self.assertEqual(filters["temporal"]["maximum_year"], 2026)

        valid_statuses = set(filters["status_groups"])
        for layer in bundle["layers"].values():
            for definition in layer["sublayers"].values():
                for feature in definition["data"]["features"]:
                    props = feature["properties"]
                    self.assertIn(props["_status_group"], valid_statuses)
                    if "_year" in props:
                        self.assertGreaterEqual(props["_year"], 1912)
                        self.assertLessEqual(props["_year"], 2026)
                        self.assertTrue(props["_year_label"])

    def test_static_api_is_reproducible_and_complete(self):
        builder = load_builder()
        bundle = builder.build_bundle()
        with tempfile.TemporaryDirectory() as directory:
            rebuilt_api = Path(directory) / "v1"
            builder.write_api_outputs(bundle, rebuilt_api)
            expected_files = {
                path.relative_to(rebuilt_api)
                for path in rebuilt_api.rglob("*")
                if path.is_file()
            }
            committed_files = {
                path.relative_to(API_DIR)
                for path in API_DIR.rglob("*")
                if path.is_file() and path.name != "README.md"
            }
            self.assertEqual(committed_files, expected_files)
            for relative_path in expected_files:
                self.assertEqual(
                    (API_DIR / relative_path).read_bytes(),
                    (rebuilt_api / relative_path).read_bytes(),
                    f"API artifact differs: {relative_path}",
                )

        manifest = json.loads((API_DIR / "manifest.json").read_text())
        self.assertEqual(manifest["api_version"], "v1")
        self.assertEqual(manifest["atlas_release"]["version"], "0.4.1")
        self.assertEqual(len(manifest["layers"]), 22)
        for layer in manifest["layers"]:
            endpoint = API_DIR / layer["endpoint"]
            payload = json.loads(endpoint.read_text())
            self.assertEqual(len(payload["features"]), layer["record_count"])


if __name__ == "__main__":
    unittest.main()
