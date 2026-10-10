from dataclasses import dataclass
import math
from typing import Dict, Any, List

@dataclass
class VegetationSpec:
    species: str
    growth_rate_m_per_year: float
    max_canopy_radius_m: float
    max_height_m: float
    water_requirement_mm: float
    shade_factor: float
    root_depth_m: float
    maintenance_cost: float

class VegetationInstance:
    def __init__(self, spec: VegetationSpec, initial_age_years: float = 0.0):
        self.spec = spec
        self.age_years = initial_age_years
        
    def get_height(self) -> float:
        # Logistic growth curve
        k = 2.0 * self.spec.growth_rate_m_per_year / self.spec.max_height_m
        t_mid = self.spec.max_height_m / (2.0 * self.spec.growth_rate_m_per_year)
        
        return self.spec.max_height_m / (1 + math.exp(-k * (self.age_years - t_mid)))
        
    def get_canopy_radius(self) -> float:
        height = self.get_height()
        return self.spec.max_canopy_radius_m * (height / self.spec.max_height_m) ** 0.7
        
    def get_shade_effect(self) -> Dict[str, float]:
        canopy_radius = self.get_canopy_radius()
        shade_area = math.pi * (canopy_radius ** 2)
        temp_reduction = self.spec.shade_factor * shade_area
        return {
            "shade_area": shade_area,
            "temperature_reduction": temp_reduction
        }
        
    def get_infiltration_boost(self) -> float:
        return self.spec.root_depth_m * 0.1
        
    def step(self, dt_years: float):
        self.age_years += dt_years

class VegetationEngine:
    def __init__(self):
        self.plants: List[VegetationInstance] = []
        
    def add_plant(self, plant: VegetationInstance):
        self.plants.append(plant)
        
    def step(self, dt_years: float):
        for plant in self.plants:
            plant.step(dt_years)
            
    def compute_temporal_snapshots(self) -> Dict[str, Dict[str, float]]:
        snapshots = {}
        timepoints = {
            "Day0": 0.0,
            "Month1": 1/12,
            "Month6": 0.5,
            "Year1": 1.0,
            "Year3": 3.0,
            "Year5": 5.0
        }
        
        # Save current state
        original_ages = [p.age_years for p in self.plants]
        
        for label, t in timepoints.items():
            for i, p in enumerate(self.plants):
                p.age_years = original_ages[i] + t
            
            total_shade = sum(p.get_shade_effect()["shade_area"] for p in self.plants)
            avg_height = sum(p.get_height() for p in self.plants) / len(self.plants) if self.plants else 0
            
            snapshots[label] = {
                "total_shade_area": total_shade,
                "average_height": avg_height
            }
            
        # Restore state
        for i, p in enumerate(self.plants):
            p.age_years = original_ages[i]
            
        return snapshots
