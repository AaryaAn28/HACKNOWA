import numpy as np
import heapq

class TerrainAnalyzer:
    """
    A class for terrain analysis operations required for flood simulation.
    """

    @staticmethod
    def compute_slope(elevation: np.ndarray, cell_size: float) -> np.ndarray:
        """
        Compute terrain slope in degrees using finite differences.
        """
        dzdy, dzdx = np.gradient(elevation, cell_size, cell_size)
        slope = np.sqrt(dzdx**2 + dzdy**2)
        return np.degrees(np.arctan(slope))

    @staticmethod
    def compute_aspect(elevation: np.ndarray, cell_size: float) -> np.ndarray:
        """
        Compute terrain aspect in compass degrees (0-360).
        0 is North, 90 is East.
        """
        dzdy, dzdx = np.gradient(elevation, cell_size, cell_size)
        aspect = np.degrees(np.arctan2(-dzdy, dzdx))
        # Convert to 0-360 compass bearing
        compass = (90.0 - aspect) % 360.0
        return compass

    @staticmethod
    def compute_curvature(elevation: np.ndarray, cell_size: float) -> np.ndarray:
        """
        Compute profile curvature using second derivatives.
        """
        dzdy, dzdx = np.gradient(elevation, cell_size, cell_size)
        d2zdy2, d2zdydx = np.gradient(dzdy, cell_size, cell_size)
        d2zdxdy, d2zdx2 = np.gradient(dzdx, cell_size, cell_size)
        
        p = dzdx**2 + dzdy**2
        p = np.where(p < 1e-8, 1e-8, p)
        
        prof = (dzdx**2 * d2zdx2 + 2 * dzdx * dzdy * d2zdydx + dzdy**2 * d2zdy2) / (p * np.sqrt(1 + p))
        return prof

    @staticmethod
    def compute_flow_direction_d8(elevation: np.ndarray) -> np.ndarray:
        """
        Compute D8 flow direction.
        Directions: 1=E, 2=SE, 4=S, 8=SW, 16=W, 32=NW, 64=N, 128=NE
        """
        rows, cols = elevation.shape
        
        dr = [-1, -1, -1,  0, 0,  1, 1, 1]
        dc = [-1,  0,  1, -1, 1, -1, 0, 1]
        dir_codes = [32, 64, 128, 16, 1, 8, 4, 2]
        
        steepest_drop = np.zeros_like(elevation)
        steepest_dir = np.zeros_like(elevation, dtype=np.uint8)
        
        for i in range(8):
            r_shift = dr[i]
            c_shift = dc[i]
            
            dist = 1.41421356 if (r_shift != 0 and c_shift != 0) else 1.0
            
            shifted_elev = np.full_like(elevation, np.inf)
            r_start, r_end = max(0, r_shift), min(rows, rows + r_shift)
            c_start, c_end = max(0, c_shift), min(cols, cols + c_shift)
            
            sr_start, sr_end = max(0, -r_shift), min(rows, rows - r_shift)
            sc_start, sc_end = max(0, -c_shift), min(cols, cols - c_shift)
            
            shifted_elev[sr_start:sr_end, sc_start:sc_end] = elevation[r_start:r_end, c_start:c_end]
            
            drop = (elevation - shifted_elev) / dist
            mask = drop > steepest_drop
            steepest_drop[mask] = drop[mask]
            steepest_dir[mask] = dir_codes[i]
            
        return steepest_dir

    @staticmethod
    def compute_flow_accumulation(flow_direction: np.ndarray) -> np.ndarray:
        """
        Compute flow accumulation using a topological sort approach.
        """
        rows, cols = flow_direction.shape
        accumulation = np.ones((rows, cols), dtype=np.float32)
        
        in_degree = np.zeros((rows, cols), dtype=int)
        
        dir_map = {
            1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1),
            16: (0, -1), 32: (-1, -1), 64: (-1, 0), 128: (-1, 1)
        }
        
        for r in range(rows):
            for c in range(cols):
                fd = flow_direction[r, c]
                if fd in dir_map:
                    dr, dc = dir_map[fd]
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        in_degree[nr, nc] += 1
                        
        queue = []
        for r in range(rows):
            for c in range(cols):
                if in_degree[r, c] == 0:
                    queue.append((r, c))
                    
        while queue:
            r, c = queue.pop(0)
            fd = flow_direction[r, c]
            if fd in dir_map:
                dr, dc = dir_map[fd]
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    accumulation[nr, nc] += accumulation[r, c]
                    in_degree[nr, nc] -= 1
                    if in_degree[nr, nc] == 0:
                        queue.append((nr, nc))
                        
        return accumulation

    @staticmethod
    def fill_depressions(elevation: np.ndarray) -> np.ndarray:
        """
        Fill depressions in elevation using Priority-Flood algorithm.
        """
        rows, cols = elevation.shape
        filled = np.full((rows, cols), np.inf, dtype=elevation.dtype)
        pq = []
        
        for r in range(rows):
            for c in [0, cols - 1]:
                heapq.heappush(pq, (elevation[r, c], r, c))
                filled[r, c] = elevation[r, c]
                
        for c in range(1, cols - 1):
            for r in [0, rows - 1]:
                heapq.heappush(pq, (elevation[r, c], r, c))
                filled[r, c] = elevation[r, c]
                
        dr = [-1, 1, 0, 0]
        dc = [0, 0, -1, 1]
        
        while pq:
            elev, r, c = heapq.heappop(pq)
            
            for i in range(4):
                nr, nc = r + dr[i], c + dc[i]
                if 0 <= nr < rows and 0 <= nc < cols:
                    if filled[nr, nc] == np.inf:
                        new_elev = max(elevation[nr, nc], elev)
                        filled[nr, nc] = new_elev
                        heapq.heappush(pq, (new_elev, nr, nc))
                        
        return filled

    @staticmethod
    def delineate_basins(flow_direction: np.ndarray) -> np.ndarray:
        """
        Delineate basins by tracing upstream from outlets.
        """
        rows, cols = flow_direction.shape
        basins = np.zeros((rows, cols), dtype=np.int32)
        
        dir_map = {
            1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1),
            16: (0, -1), 32: (-1, -1), 64: (-1, 0), 128: (-1, 1)
        }
        
        outlets = []
        for r in range(rows):
            for c in range(cols):
                fd = flow_direction[r, c]
                if fd == 0:
                    outlets.append((r, c))
                elif fd in dir_map:
                    dr, dc = dir_map[fd]
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < rows and 0 <= nc < cols):
                        outlets.append((r, c))
                        
        rev_map = {
            1: 16, 2: 32, 4: 64, 8: 128,
            16: 1, 32: 2, 64: 4, 128: 8
        }
        
        current_basin = 1
        for r_out, c_out in outlets:
            if basins[r_out, c_out] != 0:
                continue
                
            queue = [(r_out, c_out)]
            basins[r_out, c_out] = current_basin
            
            while queue:
                r, c = queue.pop(0)
                
                for fd, (dr, dc) in dir_map.items():
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if flow_direction[nr, nc] == rev_map[fd] and basins[nr, nc] == 0:
                            basins[nr, nc] = current_basin
                            queue.append((nr, nc))
            
            current_basin += 1
            
        return basins

    @staticmethod
    def compute_twi(slope: np.ndarray, flow_accumulation: np.ndarray, cell_size: float) -> np.ndarray:
        """
        Compute Topographic Wetness Index (TWI).
        """
        a = flow_accumulation * cell_size
        
        slope_rad = np.radians(slope)
        slope_rad = np.where(slope_rad < 0.001, 0.001, slope_rad)
        
        tan_beta = np.tan(slope_rad)
        tan_beta = np.where(tan_beta < 0.001, 0.001, tan_beta)
        
        twi = np.log(a / tan_beta)
        return twi
