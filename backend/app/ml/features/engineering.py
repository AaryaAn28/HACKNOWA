import numpy as np
import scipy.ndimage
from typing import Dict, Any, Tuple, Optional

def compute_slope(elevation: np.ndarray, cell_size: float) -> np.ndarray:
    """Computes slope from elevation data using numpy gradient."""
    dy, dx = np.gradient(elevation, cell_size, cell_size)
    slope = np.arctan(np.sqrt(dx**2 + dy**2))
    return np.degrees(slope)

def compute_aspect(elevation: np.ndarray, cell_size: float) -> np.ndarray:
    """Computes aspect from elevation data."""
    dy, dx = np.gradient(elevation, cell_size, cell_size)
    aspect = np.degrees(np.arctan2(-dy, dx))
    return np.mod(90.0 - aspect, 360.0)

def compute_curvature(elevation: np.ndarray, cell_size: float) -> np.ndarray:
    """Computes second derivatives for curvature."""
    dy, dx = np.gradient(elevation, cell_size, cell_size)
    dyy, dyx = np.gradient(dy, cell_size, cell_size)
    dxy, dxx = np.gradient(dx, cell_size, cell_size)
    curvature = (dxx * dy**2 + dyy * dx**2 - 2 * dx * dy * dxy) / ((dx**2 + dy**2)**1.5 + 1e-8)
    return curvature

def compute_twi(slope: np.ndarray, flow_acc: np.ndarray, cell_size: float) -> np.ndarray:
    """Computes Topographic Wetness Index (TWI)."""
    slope_rad = np.radians(np.maximum(slope, 0.1)) # Prevent div by 0
    specific_catchment_area = (flow_acc + 1) * (cell_size ** 2)
    twi = np.log(specific_catchment_area / np.tan(slope_rad))
    return twi

def compute_distance_to_nearest(grid: np.ndarray, target_mask: np.ndarray) -> np.ndarray:
    """Computes Euclidean distance to nearest target."""
    return scipy.ndimage.distance_transform_edt(~target_mask)

def compute_density(points: np.ndarray, grid_shape: Tuple[int, int], radius: float) -> np.ndarray:
    """Computes kernel density estimation."""
    grid = np.zeros(grid_shape)
    for y, x in points:
        if 0 <= y < grid_shape[0] and 0 <= x < grid_shape[1]:
            grid[int(y), int(x)] += 1
    return scipy.ndimage.gaussian_filter(grid, sigma=radius)

def compute_vegetation_fraction(ndvi: np.ndarray) -> np.ndarray:
    """Computes vegetation fraction from NDVI."""
    return (ndvi > 0.3).astype(float)

def compute_imperviousness(land_cover: np.ndarray) -> np.ndarray:
    """Computes imperviousness based on land cover classification."""
    # Lookup table: 1: Urban (90%), 2: Forest (5%), 3: Water (0%)
    lut = {1: 0.9, 2: 0.05, 3: 0.0}
    impervious = np.zeros_like(land_cover, dtype=float)
    for lc, imp in lut.items():
        impervious[land_cover == lc] = imp
    return impervious

def compute_drainage_density(drain_network: np.ndarray, grid_shape: Tuple[int, int], cell_size: float) -> float:
    """Computes total drain length per unit area."""
    total_length = np.sum(drain_network > 0) * cell_size
    total_area = grid_shape[0] * grid_shape[1] * (cell_size ** 2)
    return total_length / total_area if total_area > 0 else 0.0

def compute_terrain_roughness(elevation: np.ndarray, window_size: int = 3) -> np.ndarray:
    """Computes standard deviation in moving window for terrain roughness."""
    c1 = scipy.ndimage.uniform_filter(elevation, window_size, mode='reflect')
    c2 = scipy.ndimage.uniform_filter(elevation*elevation, window_size, mode='reflect')
    roughness = np.sqrt(np.maximum(c2 - c1*c1, 0))
    return roughness

class FeatureStore:
    """Caches computed features and tracks stale features."""
    def __init__(self):
        self.cache: Dict[str, Any] = {}
        self.stale: Dict[str, bool] = {}

    def get(self, name: str) -> Optional[Any]:
        if name in self.cache and not self.stale.get(name, True):
            return self.cache[name]
        return None

    def put(self, name: str, value: Any):
        self.cache[name] = value
        self.stale[name] = False

    def mark_stale(self, name: str):
        if name in self.stale:
            self.stale[name] = True
