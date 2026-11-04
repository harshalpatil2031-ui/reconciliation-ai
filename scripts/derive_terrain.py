"""Derive HAND and topographic wetness from Copernicus GLO-30 tiles.

The output grid is 10 m EPSG:32643 to match the project contract. Source
information content remains the Copernicus DEM's approximately 30 m spacing.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import tempfile

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.merge import merge
from rasterio.transform import from_origin
from rasterio.warp import reproject, transform_bounds
from scipy.ndimage import distance_transform_edt

# pysheds 0.5 still calls NumPy's removed `in1d`; `isin` has the same default
# behavior and keeps this one-shot hydrology command working on NumPy 2.5.
if not hasattr(np, "in1d"):
    np.in1d = np.isin  # type: ignore[attr-defined]

from pysheds.grid import Grid

SOURCE_CRS = "EPSG:4326"
TARGET_CRS = "EPSG:32643"
SOURCE_RES = 1 / 3600
NODATA = -9999.0


def _ceil_to(value: float, step: float) -> float:
    return math.ceil(value / step) * step


def _floor_to(value: float, step: float) -> float:
    return math.floor(value / step) * step


def derive(
    tiles: list[Path],
    output: Path,
    *,
    bounds: tuple[float, float, float, float],
    stream_area_km2: float = 3.0,
    buffer_degrees: float = 0.05,
) -> dict[str, float | int | str]:
    """Create a two-band HAND/TWI GeoTIFF over the requested lon/lat bounds."""
    if len(tiles) < 2 or any(not path.is_file() for path in tiles):
        raise ValueError("provide the verified Copernicus GLO-30 tiles covering the AOI")
    west, south, east, north = bounds
    if not (west < east and south < north and stream_area_km2 > 0 and buffer_degrees > 0):
        raise ValueError("AOI bounds, stream area, and hydrology buffer must be positive")
    processing_bounds = (
        west - buffer_degrees, south - buffer_degrees,
        east + buffer_degrees, north + buffer_degrees,
    )

    sources = [rasterio.open(path) for path in tiles]
    try:
        if any(source.crs.to_string() != SOURCE_CRS for source in sources):
            raise ValueError("Copernicus source tiles must use EPSG:4326")
        dem_geo, transform_geo = merge(
            sources,
            bounds=processing_bounds,
            res=(SOURCE_RES, SOURCE_RES),
            nodata=NODATA,
            dtype="float32",
            method="first",
        )
    finally:
        for source in sources:
            source.close()

    left, bottom, right, top = transform_bounds(
        SOURCE_CRS, TARGET_CRS, *processing_bounds, densify_pts=21
    )
    left, top = _floor_to(left, 30), _ceil_to(top, 30)
    width = math.ceil((right - left) / 30)
    height = math.ceil((top - bottom) / 30)
    transform_30 = from_origin(left, top, 30, 30)
    dem_30 = np.full((height, width), NODATA, dtype=np.float32)
    reproject(
        source=dem_geo[0], destination=dem_30,
        src_transform=transform_geo, src_crs=SOURCE_CRS, src_nodata=NODATA,
        dst_transform=transform_30, dst_crs=TARGET_CRS, dst_nodata=NODATA,
        resampling=Resampling.bilinear,
    )
    valid = np.isfinite(dem_30) & (dem_30 != NODATA)
    if valid.mean() < 0.98:
        raise ValueError("DEM processing extent contains nodata; check the selected source tiles")
    # Projected rectangular bounds include corner cells outside the curved
    # reprojected lon/lat rectangle. Extend only those outer cells from their
    # nearest source value; the requested AOI is buffered 5 km from this edge.
    if not valid.all():
        missing_rows, missing_cols = np.nonzero(~valid)
        missing_x = left + (missing_cols + 0.5) * 30
        missing_y = top - (missing_rows + 0.5) * 30
        missing_lon, missing_lat = rasterio.warp.transform(
            TARGET_CRS, SOURCE_CRS, missing_x.tolist(), missing_y.tolist()
        )
        in_aoi = (
            (np.asarray(missing_lon) >= west) & (np.asarray(missing_lon) <= east)
            & (np.asarray(missing_lat) >= south) & (np.asarray(missing_lat) <= north)
        )
        if np.any(in_aoi):
            raise ValueError("source DEM has nodata inside the requested AOI")
        nearest = distance_transform_edt(~valid, return_distances=False, return_indices=True)
        dem_30[~valid] = dem_30[tuple(nearest[:, ~valid])]
        valid = np.ones_like(valid, dtype=bool)

    temp_root = Path(__file__).resolve().parents[1] / "data/processed"
    temp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pccoe-terrain-", dir=temp_root) as temp_dir:
        dem_path = Path(temp_dir) / "dem_utm_30m.tif"
        with rasterio.open(
            dem_path, "w", driver="GTiff", height=height, width=width, count=1,
            dtype="float32", crs=TARGET_CRS, transform=transform_30,
            nodata=NODATA, compress="deflate", predictor=3,
        ) as dataset:
            dataset.write(dem_30, 1)
        grid = Grid.from_raster(str(dem_path))
        dem = grid.read_raster(str(dem_path))
        filled = grid.fill_pits(dem)
        filled = grid.fill_depressions(filled)
        conditioned = grid.resolve_flats(filled)
        dirmap = (64, 128, 1, 2, 4, 8, 16, 32)
        flow_direction = grid.flowdir(conditioned, dirmap=dirmap)
        accumulation = grid.accumulation(flow_direction, dirmap=dirmap)
        stream_cells = max(1, math.ceil(stream_area_km2 * 1_000_000 / 900))
        streams_array = np.asarray(accumulation) >= stream_cells
        if int(streams_array.sum()) == 0:
            raise ValueError("selected drainage-initiation threshold produced no stream cells")
        streams_path = Path(temp_dir) / "streams.tif"
        with rasterio.open(
            streams_path, "w", driver="GTiff", height=height, width=width, count=1,
            dtype="uint8", crs=TARGET_CRS, transform=transform_30,
            nodata=0, compress="deflate",
        ) as dataset:
            dataset.write(streams_array.astype(np.uint8), 1)
        streams = grid.read_raster(str(streams_path))
        hand = np.asarray(
            grid.compute_hand(flow_direction, conditioned, streams, dirmap=dirmap),
            dtype=np.float32,
        )
        dem_values = np.asarray(conditioned, dtype=np.float32)
        dem_values[~valid] = np.nan
        dy, dx = np.gradient(dem_values, 30.0, -30.0)
        slope_tangent = np.hypot(dx, dy)
        specific_area_m = (np.asarray(accumulation, dtype=np.float32) + 1) * 30.0
        twi = np.log(specific_area_m / np.maximum(slope_tangent, 0.001)).astype(np.float32)
        hand[~valid] = np.nan
        twi[~valid] = np.nan

        hand_tmp = Path(temp_dir) / "hand.tif"
        with rasterio.open(
            hand_tmp, "w", driver="GTiff", height=height, width=width, count=2,
            dtype="float32", crs=TARGET_CRS, transform=transform_30,
            nodata=NODATA, compress="deflate", predictor=3,
        ) as dataset:
            dataset.write(np.where(np.isfinite(hand), hand, NODATA).astype(np.float32), 1)
            dataset.write(np.where(np.isfinite(twi), twi, NODATA).astype(np.float32), 2)

        aoi_bounds = transform_bounds(SOURCE_CRS, TARGET_CRS, west, south, east, north)
        out_left, out_bottom, out_right, out_top = aoi_bounds
        out_left, out_bottom = _floor_to(out_left, 10), _floor_to(out_bottom, 10)
        out_right, out_top = _ceil_to(out_right, 10), _ceil_to(out_top, 10)
        out_width = math.ceil((out_right - out_left) / 10)
        out_height = math.ceil((out_top - out_bottom) / 10)
        out_transform = from_origin(out_left, out_top, 10, 10)
        output.parent.mkdir(parents=True, exist_ok=True)
        profile = {
            "driver": "GTiff", "height": out_height, "width": out_width,
            "count": 2, "dtype": "float32", "crs": TARGET_CRS,
            "transform": out_transform, "nodata": NODATA,
            "compress": "deflate", "predictor": 3, "tiled": True,
            "blockxsize": 256, "blockysize": 256,
        }
        with rasterio.open(hand_tmp) as source, rasterio.open(output, "w+", **profile) as target:
            for band in (1, 2):
                reproject(
                    source=rasterio.band(source, band), destination=rasterio.band(target, band),
                    src_transform=transform_30, src_crs=TARGET_CRS, src_nodata=NODATA,
                    dst_transform=out_transform, dst_crs=TARGET_CRS, dst_nodata=NODATA,
                    resampling=Resampling.bilinear,
                )
            target.set_band_description(1, "HAND_m")
            target.set_band_description(2, "TWI")
            hand_out = target.read(1)
            no_flow = ~np.isfinite(hand_out) | (hand_out == NODATA)
            no_flow_pixels = int(no_flow.sum())
            max_fill_distance = 0.0
            if no_flow_pixels:
                if no_flow_pixels / hand_out.size > 0.001:
                    raise ValueError("too many output cells have no D8 drainage assignment")
                distances, nearest = distance_transform_edt(
                    no_flow, return_distances=True, return_indices=True
                )
                max_fill_distance = float(distances.max())
                if max_fill_distance > 15:
                    raise ValueError("no-flow cells are too far from a valid HAND cell to fill")
                hand_out[no_flow] = hand_out[tuple(nearest[:, no_flow])]
                target.write(hand_out, 1)
            target.update_tags(
                source="Copernicus DEM GLO-30 DSM",
                source_resolution_m="approximately 30",
                aoi_lonlat=",".join(map(str, bounds)),
                buffer_degrees=str(buffer_degrees),
                stream_initiation_area_km2=str(stream_area_km2),
                stream_initiation_cells=str(stream_cells),
                flow_routing="D8; pysheds 0.5",
                twi="ln((upstream_cells+1)*30m / tan(slope)); slope floor 0.001",
                output_resolution_m="10; resampled from approximately 30m source",
                no_flow_cells_filled=str(no_flow_pixels),
                maximum_no_flow_fill_distance_cells=str(max_fill_distance),
            )

    with rasterio.open(output) as result:
        values = result.read(masked=True)
        hand_valid = values[0].compressed()
        twi_valid = values[1].compressed()
        if not hand_valid.size or not twi_valid.size:
            raise ValueError("derived terrain output contains no valid pixels")
        if np.any(hand_valid < -0.05) or not np.isfinite(twi_valid).all():
            raise ValueError("derived HAND/TWI failed physical or finite-value checks")
        return {
            "output": str(output), "width": result.width, "height": result.height,
            "resolution_m": 10, "hand_min_m": float(hand_valid.min()),
            "hand_max_m": float(hand_valid.max()), "twi_min": float(twi_valid.min()),
            "twi_max": float(twi_valid.max()), "valid_pixels": int(hand_valid.size),
            "stream_initiation_area_km2": stream_area_km2,
            "stream_initiation_cells": stream_cells,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tiles", nargs="+", type=Path, help="Copernicus GLO-30 COG source tiles")
    parser.add_argument("--output", type=Path, default=Path("data/rasters/terrain_hand_twi_32643.tif"))
    parser.add_argument("--bounds", type=float, nargs=4, default=(73.81, 18.32, 74.19, 18.68),
                        metavar=("WEST", "SOUTH", "EAST", "NORTH"))
    parser.add_argument("--stream-area-km2", type=float, default=3.0)
    args = parser.parse_args()
    try:
        summary = derive(args.tiles, args.output, bounds=tuple(args.bounds),
                         stream_area_km2=args.stream_area_km2)
    except (ValueError, OSError, rasterio.errors.RasterioError) as exc:
        parser.error(str(exc))
    import json
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
