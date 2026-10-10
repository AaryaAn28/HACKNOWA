import math
import numpy as np
from datetime import datetime
from typing import List, Tuple

class Building:
    def __init__(self, id: str, height: float, footprint: List[Tuple[float, float]]):
        self.id = id
        self.height = height
        self.footprint = footprint
        
class Tree:
    def __init__(self, x: float, y: float, canopy_radius: float):
        self.x = x
        self.y = y
        self.canopy_radius = canopy_radius

class SolarShadowEngine:
    def calculate_sun_position(self, lat: float, lon: float, dt: datetime) -> Tuple[float, float]:
        """Returns (altitude, azimuth) in radians."""
        # Simplified solar position algorithm
        day_of_year = dt.timetuple().tm_yday
        fractional_year = (2 * math.pi / 365) * (day_of_year - 1 + (dt.hour - 12) / 24)
        
        eq_time = 229.18 * (0.000075 + 0.001868 * math.cos(fractional_year) - 0.032077 * math.sin(fractional_year) \
                  - 0.014615 * math.cos(2 * fractional_year) - 0.040849 * math.sin(2 * fractional_year))
                  
        declination = 0.006918 - 0.399912 * math.cos(fractional_year) + 0.070257 * math.sin(fractional_year) \
                      - 0.006758 * math.cos(2 * fractional_year) + 0.000907 * math.sin(2 * fractional_year) \
                      - 0.002697 * math.cos(3 * fractional_year) + 0.00148 * math.sin(3 * fractional_year)
                      
        time_offset = eq_time + 4 * lon
        tst = dt.hour * 60 + dt.minute + time_offset
        ha = (tst / 4) - 180
        ha_rad = math.radians(ha)
        
        lat_rad = math.radians(lat)
        
        zenith = math.acos(math.sin(lat_rad) * math.sin(declination) + math.cos(lat_rad) * math.cos(declination) * math.cos(ha_rad))
        altitude = (math.pi / 2) - zenith
        
        azimuth = math.acos((math.sin(lat_rad) * math.cos(zenith) - math.sin(declination)) / (math.cos(lat_rad) * math.sin(zenith)))
        if ha > 0:
            azimuth = 2 * math.pi - azimuth
            
        return altitude, azimuth

    def compute_shadows(self, grid_shape: Tuple[int, int], cell_size: float, 
                        buildings: List[Building], trees: List[Tree], 
                        lat: float, lon: float, dt: datetime) -> np.ndarray:
        
        altitude, azimuth = self.calculate_sun_position(lat, lon, dt)
        
        shadow_grid = np.zeros(grid_shape)
        
        if altitude <= 0:
            return np.ones(grid_shape) # Night time, full shadow
            
        shadow_direction_rad = azimuth + math.pi
        dx = math.sin(shadow_direction_rad)
        dy = math.cos(shadow_direction_rad)
        
        # Buildings
        for b in buildings:
            shadow_length = b.height / math.tan(altitude)
            # Simplified projection: ray casting on grid
            for px, py in b.footprint:
                grid_x = int(px / cell_size)
                grid_y = int(py / cell_size)
                
                length_cells = int(shadow_length / cell_size)
                for step in range(length_cells):
                    sx = grid_x + int(step * dx)
                    sy = grid_y + int(step * dy)
                    if 0 <= sx < grid_shape[0] and 0 <= sy < grid_shape[1]:
                        shadow_grid[sx, sy] = 1.0

        # Trees
        for t in trees:
            shadow_offset = (t.canopy_radius) / math.tan(altitude) if altitude > 0.1 else t.canopy_radius * 2
            center_x = t.x + shadow_offset * dx
            center_y = t.y + shadow_offset * dy
            
            cx_grid = int(center_x / cell_size)
            cy_grid = int(center_y / cell_size)
            rad_grid = int(t.canopy_radius / cell_size)
            
            for i in range(max(0, cx_grid - rad_grid), min(grid_shape[0], cx_grid + rad_grid + 1)):
                for j in range(max(0, cy_grid - rad_grid), min(grid_shape[1], cy_grid + rad_grid + 1)):
                    dist = math.sqrt((i - cx_grid)**2 + (j - cy_grid)**2)
                    if dist <= rad_grid:
                        # Partial shade from trees
                        shadow_grid[i, j] = max(shadow_grid[i, j], 0.8)

        return shadow_grid

# Backwards compatible class alias
HeatSimulationEngine = SolarShadowEngine
