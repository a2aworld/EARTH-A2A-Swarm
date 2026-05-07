import numpy as np
from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString
from shapely.ops import split, unary_union
import shapely.affinity

def unwrap_longitude(lons):
    """Removes >180 jumps in longitude array."""
    unwrapped = np.copy(lons)
    for i in range(1, len(unwrapped)):
        diff = unwrapped[i] - unwrapped[i-1]
        if diff > 180:
            unwrapped[i:] -= 360
        elif diff < -180:
            unwrapped[i:] += 360
    return unwrapped

def wrap_longitude(lons):
    """Wraps longitudes back to [-180, 180)."""
    return (lons + 180) % 360 - 180

def split_at_antimeridian(geom):
    """
    Splits a geometry at the +180/-180 meridian.
    """
    if geom.is_empty:
        return geom

    antimeridian = LineString([(180, -90), (180, 90)])

    try:
        split_geom = split(geom, antimeridian)
        parts = []
        for g in getattr(split_geom, 'geoms', [split_geom]):
            wrapped_g = wrap_geometry_coords(g)
            parts.append(wrapped_g)

        return MultiPolygon(parts) if all(isinstance(p, Polygon) for p in parts) else unary_union(parts)
    except Exception as e:
        return wrap_geometry_coords(geom)

def wrap_geometry_coords(geom):
    if geom.is_empty:
        return geom

    def _wrap_coords(coords):
        coords_arr = np.array(coords)
        coords_arr[:, 0] = wrap_longitude(coords_arr[:, 0])
        return tuple(map(tuple, coords_arr))

    if isinstance(geom, Polygon):
        shell = _wrap_coords(geom.exterior.coords)
        holes = [_wrap_coords(h.coords) for h in geom.interiors]
        return Polygon(shell, holes)
    elif isinstance(geom, MultiPolygon):
        return MultiPolygon([wrap_geometry_coords(p) for p in geom.geoms])
    return geom

def normalize_geometry(geom):
    """Full Diamond Standard Normalization."""
    if not geom.is_valid:
        geom = geom.buffer(0)

    geom = split_at_antimeridian(geom)

    if not geom.is_valid:
        geom = geom.buffer(0)

    return geom
