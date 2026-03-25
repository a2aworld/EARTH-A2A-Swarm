import json
import math
import re
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, LinearRing
from shapely.ops import unary_union
from shapely.validation import make_valid
from lxml import etree
import fiona
from config import KML_PATH, DATA_DIR, FIGURE_PARTS_PATH, FIGURES_PATH, STYLE_CATALOG_PATH, LEGEND_INDEX_PATH

# ----------------------------
# Config
# ----------------------------
CUT_LON = 180.0  # always split at +180
DEFAULT_ZOOM = 9
USE_UNDERSCORES = False  # kebab-case as requested

# ----------------------------
# Helpers: IDs / names
# ----------------------------
def slugify(s: str) -> str:
    s = (s or "").strip().lower()
    # Find the first alphanumeric character to start the slug
    match = re.search(r"[a-z0-9]", s)
    if match:
        s = s[match.start():]
    s = re.sub(r"[^a-z0-9 _-]+", "", s)
    s = re.sub(r"[\s_-]+", "-" if not USE_UNDERSCORES else "_", s)
    return s.strip("_-") or "unnamed"

def split_name(name: str):
    """Split at first ' - ' into figure_name and part_name."""
    if not name:
        return ("", None)
    if " - " in name:
        a, b = name.split(" - ", 1)
        return (a.strip(), b.strip() if b.strip() else None)
    return (name.strip(), None)

def json_dumps_compact(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))

# ----------------------------
# Antimeridian handling
# ----------------------------
def wrap_lon(lon: float) -> float:
    return ((lon + 180.0) % 360.0) - 180.0

def unwrap_ring(coords):
    if len(coords) < 2:
        return [[float(x), float(y)] for (x, y) in coords]
    out = [[float(coords[0][0]), float(coords[0][1])]]
    prev = out[0][0]
    for lon, lat in coords[1:]:
        lon2 = float(lon)
        while lon2 - prev > 180.0: lon2 -= 360.0
        while lon2 - prev < -180.0: lon2 += 360.0
        out.append([lon2, float(lat)])
        prev = lon2
    return out

def close_ring(coords):
    if not coords: return coords
    if coords[0] != coords[-1]: coords = coords + [coords[0]]
    return coords

def _segment_crosses_cut(x1, x2, cut=CUT_LON):
    return (x1 < cut and x2 > cut) or (x2 < cut and x1 > cut)

def _interp_at_cut(p1, p2, cut=CUT_LON):
    x1, y1 = p1
    x2, y2 = p2
    t = (cut - x1) / (x2 - x1)
    y = y1 + t * (y2 - y1)
    return [cut, float(y)]

def split_ring_at_antimeridian(coords_unwrapped_closed, cut=CUT_LON):
    coords = coords_unwrapped_closed
    if len(coords) < 4: return [coords]
    pieces = []
    current = [coords[0]]
    for i in range(1, len(coords)):
        p_prev = coords[i - 1]
        p = coords[i]
        if _segment_crosses_cut(p_prev[0], p[0], cut=cut):
            ip = _interp_at_cut(p_prev, p, cut=cut)
            current.append(ip)
            current = close_ring(current)
            if len(current) >= 4: pieces.append(current)
            current = [ip, p]
        else:
            current.append(p)
    if current:
        current = close_ring(current)
        if len(current) >= 4: pieces.append(current)
    cleaned = []
    for ring in pieces:
        rr = [ring[0]]
        for pt in ring[1:]:
            if pt != rr[-1]: rr.append(pt)
        rr = close_ring(rr)
        if len(rr) >= 4:
            try:
                lr = LinearRing(rr)
                if lr.is_valid and lr.length > 0: cleaned.append(rr)
            except: pass
    return cleaned if cleaned else [coords]

def ring_to_polygon_parts(exterior, holes=None):
    holes = holes or []
    ext_u = close_ring(unwrap_ring(exterior))
    holes_u = [close_ring(unwrap_ring(h)) for h in holes if h and len(h) >= 4]
    ext_pieces_u = split_ring_at_antimeridian(ext_u, cut=CUT_LON)
    if len(ext_pieces_u) == 1:
        ext_w = [(wrap_lon(x), y) for x, y in ext_u]
        holes_w = [[(wrap_lon(x), y) for x, y in h] for h in holes_u]
        return make_valid(Polygon(ext_w, holes_w))
    flat_polys = []
    for ring_u in ext_pieces_u:
        ring_w = [(wrap_lon(x), y) for x, y in ring_u]
        try:
            p = make_valid(Polygon(ring_w))
            if not p.is_empty and p.area > 0:
                if isinstance(p, Polygon): flat_polys.append(p)
                elif isinstance(p, MultiPolygon): flat_polys.extend(list(p.geoms))
        except: continue
    if not flat_polys: return make_valid(Polygon([(wrap_lon(x), y) for x, y in ext_u]))
    holes_for_poly = [[] for _ in flat_polys]
    for h_u in holes_u:
        h_w = [(wrap_lon(x), y) for x, y in h_u]
        try:
            h_poly = Polygon(h_w)
            rep = h_poly.representative_point()
            for i, p in enumerate(flat_polys):
                if p.contains(rep):
                    holes_for_poly[i].append(h_w)
                    break
        except: continue
    final_polys = []
    for p, hs in zip(flat_polys, holes_for_poly):
        try:
            newp = make_valid(Polygon(list(p.exterior.coords), hs))
            if not newp.is_empty and newp.area > 0:
                if isinstance(newp, Polygon): final_polys.append(newp)
                elif isinstance(newp, MultiPolygon): final_polys.extend(list(newp.geoms))
        except: continue
    return MultiPolygon(final_polys) if len(final_polys) > 1 else (final_polys[0] if final_polys else None)

def fix_antimeridian(geom):
    if geom is None or geom.is_empty: return geom
    geom = make_valid(geom)
    if isinstance(geom, Polygon):
        return ring_to_polygon_parts(list(geom.exterior.coords), [list(r.coords) for r in geom.interiors])
    if isinstance(geom, MultiPolygon):
        parts = []
        for g in geom.geoms:
            gg = fix_antimeridian(g)
            if gg and not gg.is_empty:
                if isinstance(gg, Polygon): parts.append(gg)
                elif isinstance(gg, MultiPolygon): parts.extend(list(gg.geoms))
        return MultiPolygon(parts) if len(parts) > 1 else (parts[0] if parts else None)
    return geom

# ----------------------------
# KML & Main logic
# ----------------------------
def parse_kml_styles(kml_path: Path):
    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    try:
        tree = etree.parse(str(kml_path))
        root = tree.getroot()
        styles = {el.get("id"): {"type": "Style", "id": el.get("id"), "xml": etree.tostring(el, encoding="unicode")} for el in root.findall(".//kml:Style", namespaces=ns) if el.get("id")}
        return {"styles": styles}
    except: return {"styles": {}}

def main():
    if not KML_PATH.exists(): raise FileNotFoundError(f"Missing {KML_PATH}")
    for p in [FIGURE_PARTS_PATH, FIGURES_PATH, STYLE_CATALOG_PATH, LEGEND_INDEX_PATH]: p.parent.mkdir(parents=True, exist_ok=True)
    STYLE_CATALOG_PATH.write_text(json.dumps(parse_kml_styles(KML_PATH), indent=2))

    layers = fiona.listlayers(str(KML_PATH))
    gdfs = [gpd.read_file(str(KML_PATH), layer=lyr).assign(source_layer=lyr) for lyr in layers]
    gdf = pd.concat(gdfs, ignore_index=True).to_crs("EPSG:4326")

    records = []
    for idx, row in gdf.iterrows():
        if row.geometry is None or row.geometry.is_empty: continue
        geom = make_valid(row.geometry)
        if geom.geom_type not in ("Polygon", "MultiPolygon"): continue

        fname, pname = split_name(str(row.get("Name", "")))
        fid = slugify(fname)

        surl = row.get("styleUrl")
        sid = surl[1:] if surl and surl.startswith("#") else surl

        fixed = fix_antimeridian(geom)
        if fixed:
            records.append({
                "figure_id": fid, "figure_name": fname, "part_id": slugify(pname) if pname else None,
                "part_name": pname, "style_id": sid, "geometry": fixed
            })

    parts_gdf = gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")
    parts_gdf.to_file(FIGURE_PARTS_PATH, driver="FlatGeobuf")

    # style_ids used per figure
    styles_by_id = (
        parts_gdf.groupby("figure_id")["style_id"]
        .apply(lambda s: sorted({x for x in s.dropna().astype(str).tolist()}))
        .reset_index()
        .rename(columns={"style_id": "style_id_list"})
    )

    figs = parts_gdf.dissolve(by="figure_id", as_index=False)
    figs = figs.merge(styles_by_id, on="figure_id", how="left")
    figs["style_ids_json"] = figs["style_id_list"].apply(lambda x: json_dumps_compact(x if isinstance(x, list) else []))
    figs.drop(columns=["style_id", "style_id_list"], inplace=True)

    figs["geometry"] = figs["geometry"].apply(fix_antimeridian)

    legend = []
    for _, r in figs.iterrows():
        rep = r.geometry.representative_point()
        legend.append({
            "figure_id": r["figure_id"], "figure_name": r["figure_name"],
            "center_lat": rep.y, "center_lon": rep.x, "default_zoom": DEFAULT_ZOOM,
            "style_ids": json.loads(r["style_ids_json"])
        })

    figs.to_file(FIGURES_PATH, driver="FlatGeobuf")
    LEGEND_INDEX_PATH.write_text(json.dumps(legend, indent=2))
    print(f"✅ Pipeline Complete. Artifacts in {DATA_DIR}")

if __name__ == "__main__":
    main()
