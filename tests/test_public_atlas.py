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
                "fields": 180,
                "gas_pipelines": 24,
                "oil_pipelines": 15,
                "lng_terminals": 24,
                "power_plants": 193,
                "refineries": 4,
                "protected_areas": 1005,
                "demand_centers": 28,
                "roads": 5124,
                "railways": 1381,
                "rail_stations": 141,
                "power_grid": 931,
                "substations": 390,
                "ports": 25,
                "minigrids": 66,
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

    def test_benchmark_matches_processed_assets(self):
        benchmark = json.loads(
            (ROOT / "outputs/maps/public_asset_benchmark_summary.json").read_text()
        )
        counts = benchmark["asset_counts"]
        self.assertEqual(counts["power_plants"], 193)
        self.assertEqual(counts["substations"], 390)
        self.assertEqual(counts["demand_centres"], 28)
        self.assertEqual(counts["mini_grids"], 66)

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
        self.assertEqual(national["mapped_records"], 9531)
        self.assertEqual(national["counts"]["power_plants"], 193)
        self.assertEqual(national["counts"]["substations"], 390)
        self.assertEqual(national["counts"]["minigrids"], 66)
        self.assertAlmostEqual(national["capacity"]["minigrid_kw"], 3016.0)

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


if __name__ == "__main__":
    unittest.main()
