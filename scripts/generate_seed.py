"""Generate the deterministic synthetic parcel/case world from a measured HAND raster."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import random
import uuid

import numpy as np
import rasterio
from pyproj import Transformer
from scipy.ndimage import distance_transform_edt
from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.ops import transform as transform_geometry
from sklearn.cluster import KMeans

from pipeline.parcel_prep import minimum_width_m

EVENT_ID = "MH-2024-07-PUNE"
EVENT_UUID = uuid.UUID("be23db6b-7ef6-4bd4-a31c-5ef5108e8c3e")
SEED = 42
CASE_COUNT = 300
CONTROL_COUNT = 150


def _rect(center_x: float, center_y: float, width: float, height: float, angle: float) -> Polygon:
    return affinity.rotate(
        box(center_x - width / 2, center_y - height / 2,
            center_x + width / 2, center_y + height / 2),
        angle, origin=(center_x, center_y), use_radians=False,
    )


def _orientation(
    grad_row: np.ndarray, grad_col: np.ndarray, row: int, col: int,
    transform: rasterio.Affine,
) -> float:
    """Approximate local drainage direction as tangent to the HAND gradient."""
    dx = float(grad_col[row, col]) / transform.a
    dy = float(grad_row[row, col]) / transform.e
    return float(np.degrees(np.arctan2(dx, -dy))) if abs(dx) + abs(dy) > 1e-8 else 0.0


def _candidate_geometry(
    transform: rasterio.Affine,
    grad_row: np.ndarray,
    grad_col: np.ndarray,
    row: int,
    col: int,
    kind: str,
    rng: np.random.Generator,
) -> Polygon:
    x, y = transform * (col + 0.5, row + 0.5)
    theta = (
        _orientation(grad_row, grad_col, row, col, transform)
        if kind == "strip"
        else float(rng.uniform(0, 180))
    )
    if kind == "strip":
        width = float(rng.uniform(20, 35))
        length = float(rng.uniform(250, 450))
        return _rect(x, y, width, length, theta)
    if kind == "regular":
        width = float(rng.uniform(80, 140))
        height = float(rng.uniform(max(60, 8000 / width), min(150, 30000 / width)))
        return _rect(x, y, width, height, theta)
    width = float(rng.uniform(80, 120))
    height = float(rng.uniform(80, 120))
    return _rect(x, y, width, height, theta)


def _sample_cells(
    hand: np.ndarray, low: float, high: float | None, rng: np.random.Generator,
    *, limit: int = 50000,
) -> np.ndarray:
    mask = np.isfinite(hand) & (hand >= low)
    if high is not None:
        mask &= hand <= high
    flat = np.flatnonzero(mask)
    if flat.size > limit:
        flat = rng.choice(flat, size=limit, replace=False)
    return np.column_stack(np.unravel_index(flat, hand.shape))


def generate_seed(hand: np.ndarray, transform: rasterio.Affine, *, seed: int = SEED) -> list[dict]:
    """Create 300 case and 150 control parcels; all locations come from measured HAND."""
    hand = np.asarray(hand, dtype=np.float32)
    if hand.ndim != 2 or min(hand.shape) < 2:
        raise ValueError("HAND must be a 2D raster with at least two cells per dimension")
    if abs(transform.a) < 1e-8 or abs(transform.e) < 1e-8:
        raise ValueError("HAND raster transform must have non-zero pixel sizes")
    rng = np.random.default_rng(seed)
    if not np.any(np.isfinite(hand)):
        raise ValueError("HAND raster contains no finite elevations")
    missing = ~np.isfinite(hand)
    nearest = distance_transform_edt(
        missing, return_distances=False, return_indices=True
    )
    gradient_hand = hand.copy()
    gradient_hand[missing] = gradient_hand[tuple(nearest[:, missing])]
    grad_row, grad_col = np.gradient(gradient_hand)
    categories = [
        ("strip", 80, _sample_cells(hand, 0, 3, rng), "case"),
        ("floodplain", 120, _sample_cells(hand, 0, 6, rng), "case"),
        ("midslope", 100, _sample_cells(hand, 6.01, 30, rng), "case"),
        ("control", CONTROL_COUNT, _sample_cells(hand, 8, None, rng), "control"),
    ]
    if any(len(rows) == 0 for _, _, rows, _ in categories):
        raise ValueError("HAND raster has no eligible cells for one or more parcel classes")
    accepted: list[dict] = []
    geometries: list[Polygon] = []
    for kind, target, cells, role in categories:
        order = rng.permutation(len(cells))
        count = 0
        for index in order:
            row, col = (int(v) for v in cells[index])
            shape_kind = "strip" if kind == "strip" else "control"
            if kind in {"floodplain", "midslope"}:
                shape_kind = "regular"
            geom = _candidate_geometry(
                transform, grad_row, grad_col, row, col, shape_kind, rng
            )
            # Preserve full parcel footprints inside the measured HAND raster.
            inverse = ~transform
            pixels = [inverse * point for point in (geom.bounds[:2], geom.bounds[2:])]
            if (
                min(p[0] for p in pixels) < 0
                or min(p[1] for p in pixels) < 0
                or max(p[0] for p in pixels) >= hand.shape[1]
                or max(p[1] for p in pixels) >= hand.shape[0]
            ):
                continue
            if any(geom.intersects(existing) for existing in geometries):
                continue
            if role == "case" and kind == "floodplain":
                if float(hand[row, col]) > 6:
                    continue
            if role == "case" and kind == "midslope":
                if float(hand[row, col]) <= 6:
                    continue
            if role == "control" and float(hand[row, col]) < 8:
                continue
            geometries.append(geom)
            accepted.append({
                "geometry": geom,
                "role": role,
                "kind": kind,
                "hand_m": float(hand[row, col]),
                "center": (geom.centroid.x, geom.centroid.y),
            })
            count += 1
            if count == target:
                break
        if count < target:
            raise ValueError(
                f"HAND raster only supported {count}/{target} non-overlapping {kind} parcels; "
                "provide a wider verified AOI"
            )

    case_items = [item for item in accepted if item["role"] == "case"]
    centers = np.array([item["center"] for item in accepted])
    village_count = min(12, len(centers))
    village_labels = KMeans(
        n_clusters=village_count, random_state=seed, n_init=10
    ).fit_predict(centers)
    rng_py = random.Random(seed)
    crops = ["soybean", "sugarcane", "bajra", "tur", None]
    case_crops = (["soybean"] * 150 + ["sugarcane"] * 36 + ["bajra"] * 24
                  + ["tur"] * 15 + [None] * 75)
    rng_py.shuffle(case_crops)
    case_crop_index = 0
    taluka_midpoint = float(np.median([item["center"][0] for item in accepted]))
    to_wgs84 = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)
    parcels: list[dict] = []
    for idx, item in enumerate(accepted):
        role = item["role"]
        number = idx + 1
        code = "HAV" if item["center"][0] <= taluka_midpoint else "DAU"
        survey_no = f"PUN-{code}-{number:04d}"
        parcel_id = str(uuid.uuid5(EVENT_UUID, f"parcel:{survey_no}"))
        case_id = str(uuid.uuid5(EVENT_UUID, f"case:{survey_no}")) if role == "case" else None
        village = f"Synthetic-V{int(village_labels[idx]) + 1:02d}"
        if role == "control":
            crop = rng_py.choices(crops[:-1], weights=[0.50, 0.12, 0.08, 0.05])[0]
        else:
            crop = case_crops[case_crop_index]
            case_crop_index += 1
        sowing = None
        if crop is not None:
            sowing = date(2024, 6, 15).toordinal() + rng_py.randint(0, 20)
            sowing = date.fromordinal(sowing).isoformat()
        if item["hand_m"] <= 6:
            soil = "alluvial"
        elif rng_py.random() < 0.72:
            soil = "vertisol"
        else:
            soil = "murrum"
        geom_wgs = transform_geometry(to_wgs84.transform, item["geometry"])
        parcels.append({
            **item,
            "parcel_id": parcel_id,
            "case_id": case_id,
            "survey_no": survey_no,
            "village": village,
            "taluka": "Haveli" if code == "HAV" else "Daund",
            "district": "Pune",
            "crop": crop,
            "sowing_date": sowing,
            "soil_class": soil,
            "area_ha": item["geometry"].area / 10000.0,
            "min_width_m": minimum_width_m(item["geometry"]),
            "geom_wgs84": geom_wgs,
        })
    control_count = sum(item["role"] == "control" for item in accepted)
    if len(case_items) != CASE_COUNT or control_count != CONTROL_COUNT:
        raise RuntimeError("generated world does not match the 300 case / 150 control contract")
    return parcels


def _sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def render_seed_sql(parcels: list[dict]) -> str:
    lines = [
        "-- Generated deterministic fixture. All parcel geometry and records are synthetic.",
        "BEGIN;",
        "INSERT INTO events (event_id, name, start_date, peak_date, end_date, notes) VALUES ",
        f"({_sql_text(EVENT_ID)}, 'Pune July 2024 synthetic benchmark', "
        "'2024-07-24', '2024-07-25', '2024-07-26', "
        "'Synthetic parcels and claims on real imagery; not field validation') ",
        "ON CONFLICT (event_id) DO NOTHING;",
    ]
    for item in parcels:
        geom_utm = item["geometry"].wkt
        geom_wgs = item["geom_wgs84"].wkt
        crop = "NULL" if item["crop"] is None else _sql_text(item["crop"])
        sowing = "NULL" if item["sowing_date"] is None else _sql_text(item["sowing_date"])
        lines.append(
            "INSERT INTO parcels (parcel_id, survey_no, village, taluka, district, area_ha, "
            "min_width_m, geom, geom_utm, crop, sowing_date, soil_class, is_synthetic, role) "
            f"VALUES ('{item['parcel_id']}', {_sql_text(item['survey_no'])}, "
            f"{_sql_text(item['village'])}, {_sql_text(item['taluka'])}, 'Pune', "
            f"{item['area_ha']:.4f}, {item['min_width_m']:.2f}, "
            f"ST_GeomFromText({_sql_text(geom_wgs)}, 4326), "
            f"ST_GeomFromText({_sql_text(geom_utm)}, 32643), {crop}, {sowing}, "
            f"{_sql_text(item['soil_class'])}, TRUE, {_sql_text(item['role'])}) "
            "ON CONFLICT (parcel_id) DO NOTHING;"
        )
        if item["case_id"]:
            farmer = f"FRM-{int(item['survey_no'].split('-')[-1]):06d}"
            lines.append(
                "INSERT INTO cases (case_id, event_id, parcel_id, farmer_ref) VALUES "
                f"('{item['case_id']}', {_sql_text(EVENT_ID)}, '{item['parcel_id']}', "
                f"{_sql_text(farmer)}) ON CONFLICT (event_id, parcel_id) DO NOTHING;"
            )
    lines.extend(["COMMIT;", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--hand", type=Path,
        default=Path("data/rasters/terrain_hand_twi_32643.tif"),
    )
    parser.add_argument("--manifest", type=Path, default=Path("data/rasters/manifest.json"))
    parser.add_argument("--output", type=Path, default=Path("sql/04_seed_pune_july2024.sql"))
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    if not args.hand.is_file():
        parser.error(f"measured HAND raster not found: {args.hand}; see data/rasters/SCENES.md")
    if not args.manifest.is_file():
        parser.error(f"raster provenance manifest not found: {args.manifest}")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    terrain = next(
        (asset for asset in manifest.get("assets", [])
         if asset.get("id") == "terrain_hand_twi_32643"),
        None,
    )
    source = (terrain or {}).get("source", {})
    if (
        manifest.get("status") != "VERIFIED"
        or terrain is None
        or terrain.get("status") != "VERIFIED"
        or not source.get("product_id")
        or source.get("provenance_status") != "VERIFIED"
        or source.get("license_status") != "APPROVED"
        or not source.get("license_or_attribution")
    ):
        parser.error("HAND raster and its source/license provenance must be VERIFIED and APPROVED")
    manifest_hand = Path(terrain["path"])
    if not manifest_hand.is_absolute():
        manifest_hand = args.manifest.parent.parent / manifest_hand
    if manifest_hand.resolve() != args.hand.resolve():
        parser.error("--hand must match the verified HAND path recorded in the raster manifest")
    with rasterio.open(args.hand) as dataset:
        if dataset.crs is None or dataset.crs.to_epsg() != 32643:
            parser.error("HAND raster must use EPSG:32643")
        if (
            not np.isclose(abs(dataset.transform.a), 10)
            or not np.isclose(abs(dataset.transform.e), 10)
        ):
            parser.error("HAND raster must use the aligned 10 m target grid")
        hand = dataset.read(1, masked=True).astype("float32").filled(np.nan)
        parcels = generate_seed(hand, dataset.transform, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_seed_sql(parcels), encoding="utf-8")
    print(json.dumps({"event_id": EVENT_ID, "seed": args.seed,
                      "case_parcels": sum(item["role"] == "case" for item in parcels),
                      "controls": sum(item["role"] == "control" for item in parcels),
                      "is_synthetic": True, "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
