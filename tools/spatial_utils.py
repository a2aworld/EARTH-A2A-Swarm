import numpy as np
from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString
from shapely.ops import split, unary_union
import shapely.affinity

def unwrap_longitude(lons):
    unwrapped = np.copy(lons)
    for i in range(1, len(unwrapped)):
        diff = unwrapped[i] - unwrapped[i-1]
        if diff > 180: unwrapped[i:] -= 360
        elif diff < -180: unwrapped[i:] += 360
    return unwrapped

def wrap_longitude(lons):
    return (lons + 180) % 360 - 180

def wrap_geometry_coords(geom):
    if geom is None or geom.is_empty: return geom
    def _wrap(coords):
        arr = np.array(coords)
        arr[:, 0] = wrap_longitude(arr[:, 0])
        return tuple(map(tuple, arr))
    if isinstance(geom, Polygon):
        shell = _wrap(geom.exterior.coords)
        holes = [_wrap(h.coords) for h in geom.interiors]
        return Polygon(shell, holes)
    elif isinstance(geom, MultiPolygon):
        return MultiPolygon([wrap_geometry_coords(p) for p in geom.geoms])
    return geom

def split_at_antimeridian(geom):
    if geom is None or geom.is_empty: return geom
    antimeridian = LineString([(180, -90), (180, 90)])
    try:
        split_geom = split(geom, antimeridian)
        parts = []
        for g in getattr(split_geom, 'geoms', [split_geom]):
            parts.append(wrap_geometry_coords(g))
        return unary_union(parts)
    except: return wrap_geometry_coords(geom)

def normalize_geometry(geom):
    if geom is None or geom.is_empty: return geom
    if not geom.is_valid: geom = geom.buffer(0)
    try:
        geom = split_at_antimeridian(geom)
    except: geom = wrap_geometry_coords(geom)
    if not geom.is_valid: geom = geom.buffer(0)
    if geom.geom_type == 'GeometryCollection':
        parts = [g for g in geom.geoms if isinstance(g, (Polygon, MultiPolygon))]
        geom = unary_union(parts) if parts else geom
    return geom
