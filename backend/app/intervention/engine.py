"""
Reality Sculptor — Intervention Engine
=======================================

Generates, scores, composes, and optimizes intervention plans using
the Minimal Force Principle: find the smallest effective intervention
set that meets the user's target.

Architecture:
    InterventionLibrary → CandidateGenerator → Composer → Scorer →
    MinimalForceOptimizer → ConsequenceAnalyzer → CriticAgent → RankedPlans

Every intervention carries: requirements, cost_model, time_model,
maintenance_model, reversibility, side_effects, simulation_handler,
confidence, data_requirements.
"""

from __future__ import annotations

import itertools
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

import numpy as np
from loguru import logger


# ===================================================================
# Intervention Categories & Types
# ===================================================================

class InterventionCategory(str, Enum):
    """Top-level intervention categories."""
    HYDROLOGY = "hydrology"
    HEAT = "heat"
    TRAFFIC = "traffic"
    INFRASTRUCTURE = "infrastructure"
    EMERGENCY = "emergency"
    VEGETATION = "vegetation"


class InterventionType(str, Enum):
    """Specific intervention types within categories."""
    # Hydrology
    DRAIN_CLEANING = "drain_cleaning"
    DRAIN_OPENING = "drain_opening"
    DRAIN_EXPANSION = "drain_expansion"
    WATER_DIVERSION = "water_diversion"
    RETENTION_BASIN = "retention_basin"
    DETENTION_POND = "detention_pond"
    BIOSWALE = "bioswale"
    PERMEABLE_SURFACE = "permeable_surface"
    CULVERT_UPGRADE = "culvert_upgrade"

    # Heat
    TREE_PLANTING = "tree_planting"
    SHADE_STRUCTURE = "shade_structure"
    COOL_ROOF = "cool_roof"
    REFLECTIVE_SURFACE = "reflective_surface"
    GREEN_ROOF = "green_roof"
    VEGETATION_CORRIDOR = "vegetation_corridor"

    # Traffic
    ROUTE_DIVERSION = "route_diversion"
    LANE_CHANGE = "lane_change"
    TEMPORARY_CLOSURE = "temporary_closure"
    EMERGENCY_CORRIDOR = "emergency_corridor"

    # Infrastructure
    FLOOD_BARRIER = "flood_barrier"
    ROAD_ELEVATION = "road_elevation"
    DRAINAGE_REDESIGN = "drainage_redesign"
    SEWER_UPGRADE = "sewer_upgrade"

    # Emergency
    EVACUATION_ROUTE = "evacuation_route"
    SHELTER_ACTIVATION = "shelter_activation"
    RESOURCE_RELOCATION = "resource_relocation"


# ===================================================================
# Cost & Time Models
# ===================================================================

@dataclass
class CostModel:
    """Cost estimation for an intervention."""
    capital_cost_usd: float
    annual_maintenance_usd: float
    implementation_time_days: float
    labor_hours: float
    confidence: float  # 0.0 to 1.0
    source: str = "ESTIMATED"

    @property
    def total_5yr_cost(self) -> float:
        return self.capital_cost_usd + (self.annual_maintenance_usd * 5)


@dataclass
class TimeModel:
    """Temporal effects of an intervention."""
    immediate_effect_pct: float      # % of full effect at t=0
    short_term_days: float           # Days to reach 50% effect
    full_effect_days: float          # Days to reach 100% effect
    degradation_rate_per_year: float # Annual effectiveness loss
    lifespan_years: float

    def effectiveness_at(self, days: float) -> float:
        """Calculate effectiveness fraction at a given time point."""
        if days <= 0:
            return self.immediate_effect_pct / 100.0
        if days >= self.full_effect_days:
            years = (days - self.full_effect_days) / 365.0
            return max(0.0, 1.0 - self.degradation_rate_per_year * years)
        # Sigmoid ramp-up
        midpoint = self.short_term_days
        k = 4.0 / self.full_effect_days  # steepness
        return 1.0 / (1.0 + np.exp(-k * (days - midpoint)))


# ===================================================================
# Intervention Definition
# ===================================================================

@dataclass
class InterventionSpec:
    """
    Complete specification for a single intervention type.

    Each intervention in the library is a template; concrete interventions
    are instantiated with specific location and parameters.
    """
    intervention_type: InterventionType
    category: InterventionCategory
    name: str
    description: str

    # Models
    cost_model: CostModel
    time_model: TimeModel

    # Metadata
    reversibility: float  # 0.0 (irreversible) to 1.0 (fully reversible)
    maintenance_complexity: float  # 0.0 to 1.0
    environmental_impact: float   # -1.0 (harmful) to 1.0 (beneficial)

    # Requirements
    data_requirements: list[str] = field(default_factory=list)
    physical_requirements: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)

    # Side effects (predicted)
    known_side_effects: list[str] = field(default_factory=list)

    # Affected state variables
    primary_variables: list[str] = field(default_factory=list)
    secondary_variables: list[str] = field(default_factory=list)

    # Simulation handler name
    simulation_handler: str = ""


@dataclass
class ConcreteIntervention:
    """An intervention applied to a specific location with specific parameters."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    spec: InterventionSpec = field(default_factory=lambda: None)  # type: ignore
    location_id: str = ""
    location_geometry: Any = None  # GeoJSON or Shapely
    parameters: dict[str, Any] = field(default_factory=dict)

    # Scored results (filled by scorer)
    predicted_risk_reduction: float = 0.0
    predicted_cost: float = 0.0
    robustness_score: float = 0.0
    confidence: float = 0.0


# ===================================================================
# Intervention Plan
# ===================================================================

@dataclass
class ConsequenceProfile:
    """Full consequence analysis for a plan."""
    direct_effects: list[dict[str, Any]] = field(default_factory=list)
    secondary_effects: list[dict[str, Any]] = field(default_factory=list)
    tertiary_effects: list[dict[str, Any]] = field(default_factory=list)
    cascade_effects: list[dict[str, Any]] = field(default_factory=list)
    trade_offs: list[dict[str, Any]] = field(default_factory=list)
    failure_modes: list[dict[str, Any]] = field(default_factory=list)
    long_term_effects: list[dict[str, Any]] = field(default_factory=list)
    reversibility_score: float = 0.0


@dataclass
class InterventionPlan:
    """
    A composed set of interventions forming a complete plan.

    Plans are scored, stress-tested, critiqued, and ranked.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    interventions: list[ConcreteIntervention] = field(default_factory=list)

    # Aggregate scores
    total_risk_reduction: float = 0.0
    total_cost: float = 0.0
    total_complexity: float = 0.0
    total_disruption: float = 0.0
    total_maintenance: float = 0.0
    robustness_profile: dict[str, float] = field(default_factory=dict)

    # Consequence analysis
    consequences: ConsequenceProfile = field(default_factory=ConsequenceProfile)

    # Optimization metadata
    meets_target: bool = False
    is_pareto_efficient: bool = False
    critic_passed: bool = False
    critic_notes: list[str] = field(default_factory=list)

    # User approval
    approved: bool = False
    installed: bool = False

    @property
    def intervention_count(self) -> int:
        return len(self.interventions)

    @property
    def composite_score(self) -> float:
        """Lower is better: weighted sum of cost, complexity, disruption."""
        if not self.meets_target:
            return float("inf")
        return (
            0.4 * self.total_cost / max(self.total_cost, 1.0)
            + 0.2 * self.total_complexity
            + 0.2 * self.total_disruption
            + 0.2 * self.total_maintenance
        )


# ===================================================================
# Intervention Library
# ===================================================================

class InterventionLibrary:
    """
    Structured library of all available intervention types.

    Each type has a complete specification including cost, time,
    reversibility, and simulation handler.
    """

    def __init__(self) -> None:
        self._specs: dict[InterventionType, InterventionSpec] = {}
        self._build_default_library()

    def _build_default_library(self) -> None:
        """Populate with default intervention specifications."""

        # --- HYDROLOGY ---
        self.register(InterventionSpec(
            intervention_type=InterventionType.DRAIN_CLEANING,
            category=InterventionCategory.HYDROLOGY,
            name="Drain Cleaning",
            description="Remove debris/sediment from existing drain to restore capacity.",
            cost_model=CostModel(500, 200, 1, 4, 0.85, "ESTIMATED"),
            time_model=TimeModel(80, 0.5, 1, 0.15, 1),
            reversibility=1.0,
            maintenance_complexity=0.2,
            environmental_impact=0.1,
            data_requirements=["drain_location", "drain_id"],
            physical_requirements=["access_to_drain"],
            primary_variables=["drain_capacity", "drain_load"],
            secondary_variables=["water_depth", "road_accessibility"],
            simulation_handler="apply_drain_cleaning",
        ))

        self.register(InterventionSpec(
            intervention_type=InterventionType.DRAIN_EXPANSION,
            category=InterventionCategory.HYDROLOGY,
            name="Drain Expansion",
            description="Increase drain pipe diameter or add parallel capacity.",
            cost_model=CostModel(15000, 500, 30, 200, 0.7, "ESTIMATED"),
            time_model=TimeModel(0, 15, 30, 0.02, 30),
            reversibility=0.3,
            maintenance_complexity=0.3,
            environmental_impact=0.0,
            data_requirements=["drain_location", "drain_capacity", "downstream_connectivity"],
            physical_requirements=["excavation_access", "road_closure_permit"],
            primary_variables=["drain_capacity"],
            secondary_variables=["water_depth", "surface_runoff"],
            simulation_handler="apply_drain_expansion",
        ))

        self.register(InterventionSpec(
            intervention_type=InterventionType.RETENTION_BASIN,
            category=InterventionCategory.HYDROLOGY,
            name="Retention Basin",
            description="Construct water retention area to buffer peak runoff.",
            cost_model=CostModel(50000, 2000, 90, 500, 0.6, "ESTIMATED"),
            time_model=TimeModel(0, 45, 90, 0.03, 50),
            reversibility=0.4,
            maintenance_complexity=0.4,
            environmental_impact=0.5,
            data_requirements=["available_land", "terrain_elevation", "soil_type"],
            physical_requirements=["land_area_min_500sqm"],
            primary_variables=["water_depth", "surface_runoff"],
            secondary_variables=["drain_load", "road_accessibility"],
            simulation_handler="apply_retention_basin",
        ))

        self.register(InterventionSpec(
            intervention_type=InterventionType.BIOSWALE,
            category=InterventionCategory.HYDROLOGY,
            name="Bioswale",
            description="Vegetated channel for stormwater filtration and flow reduction.",
            cost_model=CostModel(8000, 800, 21, 80, 0.7, "ESTIMATED"),
            time_model=TimeModel(20, 30, 180, 0.05, 20),
            reversibility=0.7,
            maintenance_complexity=0.5,
            environmental_impact=0.8,
            data_requirements=["terrain_slope", "soil_permeability"],
            primary_variables=["surface_runoff", "water_depth"],
            secondary_variables=["vegetation_canopy", "heat_flux"],
            simulation_handler="apply_bioswale",
        ))

        self.register(InterventionSpec(
            intervention_type=InterventionType.PERMEABLE_SURFACE,
            category=InterventionCategory.HYDROLOGY,
            name="Permeable Surface",
            description="Replace impervious road/pavement with permeable material.",
            cost_model=CostModel(25000, 1000, 14, 100, 0.65, "ESTIMATED"),
            time_model=TimeModel(70, 3, 14, 0.04, 15),
            reversibility=0.5,
            maintenance_complexity=0.4,
            environmental_impact=0.6,
            data_requirements=["road_segment", "traffic_load", "soil_type"],
            primary_variables=["surface_runoff", "soil_saturation"],
            secondary_variables=["water_depth", "heat_flux"],
            simulation_handler="apply_permeable_surface",
        ))

        # --- HEAT ---
        self.register(InterventionSpec(
            intervention_type=InterventionType.TREE_PLANTING,
            category=InterventionCategory.HEAT,
            name="Tree Planting",
            description="Plant shade-providing trees to reduce surface temperature.",
            cost_model=CostModel(2000, 300, 3, 16, 0.8, "ESTIMATED"),
            time_model=TimeModel(5, 365, 1825, 0.0, 50),  # Full effect in ~5 years
            reversibility=0.9,
            maintenance_complexity=0.3,
            environmental_impact=1.0,
            data_requirements=["available_land", "soil_suitability"],
            primary_variables=["vegetation_canopy", "surface_temperature"],
            secondary_variables=["heat_flux", "surface_runoff"],
            simulation_handler="apply_tree_planting",
        ))

        self.register(InterventionSpec(
            intervention_type=InterventionType.COOL_ROOF,
            category=InterventionCategory.HEAT,
            name="Cool Roof",
            description="Apply high-albedo coating to building rooftops.",
            cost_model=CostModel(5000, 500, 7, 40, 0.75, "ESTIMATED"),
            time_model=TimeModel(90, 1, 7, 0.08, 10),
            reversibility=0.8,
            maintenance_complexity=0.2,
            environmental_impact=0.3,
            data_requirements=["building_id", "roof_area", "roof_material"],
            primary_variables=["surface_temperature", "heat_flux"],
            simulation_handler="apply_cool_roof",
        ))

        self.register(InterventionSpec(
            intervention_type=InterventionType.SHADE_STRUCTURE,
            category=InterventionCategory.HEAT,
            name="Shade Structure",
            description="Install artificial shade over walkways or public spaces.",
            cost_model=CostModel(12000, 600, 14, 60, 0.7, "ESTIMATED"),
            time_model=TimeModel(95, 1, 14, 0.03, 20),
            reversibility=0.9,
            maintenance_complexity=0.3,
            environmental_impact=0.1,
            data_requirements=["location", "area_coverage"],
            primary_variables=["surface_temperature"],
            secondary_variables=["heat_flux"],
            simulation_handler="apply_shade_structure",
        ))

        # --- TRAFFIC ---
        self.register(InterventionSpec(
            intervention_type=InterventionType.ROUTE_DIVERSION,
            category=InterventionCategory.TRAFFIC,
            name="Route Diversion",
            description="Redirect traffic away from flooded or dangerous roads.",
            cost_model=CostModel(200, 50, 0.1, 2, 0.9, "ESTIMATED"),
            time_model=TimeModel(100, 0, 0.1, 0, 0.01),
            reversibility=1.0,
            maintenance_complexity=0.1,
            environmental_impact=0.0,
            primary_variables=["traffic_density", "road_accessibility"],
            secondary_variables=["emergency_access"],
            simulation_handler="apply_route_diversion",
        ))

        self.register(InterventionSpec(
            intervention_type=InterventionType.EMERGENCY_CORRIDOR,
            category=InterventionCategory.TRAFFIC,
            name="Emergency Corridor",
            description="Designate and protect priority routes for emergency vehicles.",
            cost_model=CostModel(1000, 100, 1, 8, 0.8, "ESTIMATED"),
            time_model=TimeModel(100, 0, 1, 0, 0.01),
            reversibility=1.0,
            maintenance_complexity=0.1,
            environmental_impact=0.0,
            primary_variables=["emergency_access"],
            secondary_variables=["traffic_density"],
            simulation_handler="apply_emergency_corridor",
        ))

        # --- INFRASTRUCTURE ---
        self.register(InterventionSpec(
            intervention_type=InterventionType.FLOOD_BARRIER,
            category=InterventionCategory.INFRASTRUCTURE,
            name="Flood Barrier",
            description="Construct temporary or permanent flood barrier.",
            cost_model=CostModel(30000, 1500, 21, 150, 0.6, "ESTIMATED"),
            time_model=TimeModel(50, 5, 21, 0.05, 25),
            reversibility=0.6,
            maintenance_complexity=0.4,
            environmental_impact=-0.2,
            data_requirements=["terrain_elevation", "flood_extent"],
            primary_variables=["water_depth"],
            secondary_variables=["road_accessibility", "traffic_density"],
            simulation_handler="apply_flood_barrier",
        ))

        self.register(InterventionSpec(
            intervention_type=InterventionType.SEWER_UPGRADE,
            category=InterventionCategory.INFRASTRUCTURE,
            name="Sewer Upgrade",
            description="Increase sewer pipe capacity or repair structural issues.",
            cost_model=CostModel(40000, 1000, 45, 400, 0.55, "ESTIMATED"),
            time_model=TimeModel(0, 20, 45, 0.02, 40),
            reversibility=0.2,
            maintenance_complexity=0.4,
            environmental_impact=0.1,
            data_requirements=["sewer_network", "pipe_condition", "capacity"],
            primary_variables=["drain_capacity", "drain_load"],
            secondary_variables=["water_depth", "surface_runoff"],
            simulation_handler="apply_sewer_upgrade",
        ))

    def register(self, spec: InterventionSpec) -> None:
        """Register an intervention specification."""
        self._specs[spec.intervention_type] = spec
        logger.debug(f"Registered intervention: {spec.name}")

    def get(self, itype: InterventionType) -> InterventionSpec:
        """Get intervention specification by type."""
        return self._specs[itype]

    def get_by_category(self, category: InterventionCategory) -> list[InterventionSpec]:
        """Get all interventions in a category."""
        return [s for s in self._specs.values() if s.category == category]

    def get_all(self) -> list[InterventionSpec]:
        """Get all registered intervention specifications."""
        return list(self._specs.values())

    def get_for_variables(self, variables: list[str]) -> list[InterventionSpec]:
        """Find interventions that affect any of the given state variables."""
        results = []
        for spec in self._specs.values():
            affected = set(spec.primary_variables) | set(spec.secondary_variables)
            if affected & set(variables):
                results.append(spec)
        return results


# ===================================================================
# Minimal Force Optimizer
# ===================================================================

class MinimalForceOptimizer:
    """
    Searches for the smallest effective intervention set meeting
    the user's target.

    Mathematical formulation:
        MINIMIZE: Cost(I) + Complexity(I) + Disruption(I) + Maintenance(I)
        SUBJECT TO: Risk(State after I) ≤ Target
                    AND all constraints satisfied

    Search strategy: progressive expansion
        1 action → 2 actions → 3 actions → ...
        until target is reached.
    """

    def __init__(
        self,
        library: InterventionLibrary,
        max_plan_size: int = 6,
        max_candidates_per_size: int = 50,
    ) -> None:
        self.library = library
        self.max_plan_size = max_plan_size
        self.max_candidates_per_size = max_candidates_per_size

    def optimize(
        self,
        target_variable: str,
        target_reduction_pct: float,
        current_risk: float,
        available_locations: list[dict[str, Any]],
        constraints: dict[str, Any] | None = None,
        simulate_fn: Callable[[list[ConcreteIntervention]], dict[str, float]] | None = None,
    ) -> list[InterventionPlan]:
        """
        Find minimal-force intervention plans.

        Args:
            target_variable: State variable to reduce (e.g., "water_depth")
            target_reduction_pct: Target reduction percentage (e.g., 40.0)
            current_risk: Current risk/exposure value
            available_locations: List of locations where interventions can be placed
            constraints: Budget, time, environmental constraints
            simulate_fn: Function to simulate a set of interventions and return
                         new state metrics. If None, uses estimated scores.

        Returns:
            List of plans sorted by composite score (best first),
            including Pareto-efficient plans.
        """
        constraints = constraints or {}
        budget = constraints.get("budget_usd", float("inf"))
        max_time_days = constraints.get("max_time_days", float("inf"))

        target_value = current_risk * (1.0 - target_reduction_pct / 100.0)

        # Find relevant interventions
        relevant_specs = self.library.get_for_variables([target_variable])
        if not relevant_specs:
            logger.warning(f"No interventions found for variable: {target_variable}")
            return []

        # Generate concrete intervention candidates
        candidates = self._generate_candidates(
            relevant_specs, available_locations
        )

        # Progressive search: 1 action, then 2, then 3...
        all_plans: list[InterventionPlan] = []

        for size in range(1, self.max_plan_size + 1):
            logger.info(f"Searching intervention sets of size {size}...")

            combos = list(itertools.combinations(candidates, size))
            if len(combos) > self.max_candidates_per_size:
                # Prioritize by estimated individual effectiveness
                combos = sorted(
                    combos,
                    key=lambda c: sum(i.predicted_risk_reduction for i in c),
                    reverse=True,
                )[:self.max_candidates_per_size]

            for combo in combos:
                interventions = list(combo)

                # Check budget constraint
                total_cost = sum(
                    i.spec.cost_model.capital_cost_usd for i in interventions
                )
                if total_cost > budget:
                    continue

                # Check time constraint
                max_impl_time = max(
                    i.spec.cost_model.implementation_time_days
                    for i in interventions
                )
                if max_impl_time > max_time_days:
                    continue

                # Simulate or estimate
                if simulate_fn:
                    result = simulate_fn(interventions)
                    new_risk = result.get(target_variable, current_risk)
                else:
                    # Estimate: non-linear combination (diminishing returns)
                    combined_reduction = self._estimate_combined_reduction(
                        interventions, target_variable
                    )
                    new_risk = current_risk * (1.0 - combined_reduction)

                plan = InterventionPlan(
                    name=f"Plan-{size}-{len(all_plans)}",
                    interventions=interventions,
                    total_risk_reduction=(current_risk - new_risk) / current_risk * 100,
                    total_cost=total_cost,
                    total_complexity=size / self.max_plan_size,
                    total_disruption=sum(
                        1.0 - i.spec.reversibility for i in interventions
                    ) / max(size, 1),
                    total_maintenance=sum(
                        i.spec.maintenance_complexity for i in interventions
                    ) / max(size, 1),
                    meets_target=new_risk <= target_value,
                )
                all_plans.append(plan)

            # Check if we found meeting plans at this size
            meeting_plans = [p for p in all_plans if p.meets_target]
            if meeting_plans and size >= 2:
                # We've found solutions — continue one more size for comparison
                logger.info(
                    f"Found {len(meeting_plans)} meeting plans at size ≤{size}"
                )
                if size >= 3:
                    break  # Sufficient search depth

        # Mark Pareto-efficient plans
        self._mark_pareto_efficient(all_plans)

        # Sort: meeting plans first, then by composite score
        all_plans.sort(key=lambda p: (not p.meets_target, p.composite_score))

        logger.info(
            f"Optimization complete: {len(all_plans)} plans generated, "
            f"{sum(1 for p in all_plans if p.meets_target)} meet target, "
            f"{sum(1 for p in all_plans if p.is_pareto_efficient)} Pareto-efficient"
        )

        return all_plans

    def _generate_candidates(
        self,
        specs: list[InterventionSpec],
        locations: list[dict[str, Any]],
    ) -> list[ConcreteIntervention]:
        """Generate concrete intervention candidates from specs × locations."""
        candidates = []
        for spec in specs:
            for loc in locations:
                ci = ConcreteIntervention(
                    spec=spec,
                    location_id=loc.get("id", "unknown"),
                    location_geometry=loc.get("geometry"),
                    parameters=loc.get("parameters", {}),
                    predicted_risk_reduction=self._estimate_individual_reduction(
                        spec, loc
                    ),
                    predicted_cost=spec.cost_model.capital_cost_usd,
                    confidence=spec.cost_model.confidence,
                )
                candidates.append(ci)
        return candidates

    def _estimate_individual_reduction(
        self, spec: InterventionSpec, location: dict[str, Any]
    ) -> float:
        """
        Estimate risk reduction for a single intervention at a location.

        This is a simplified estimation. In production, the full simulation
        engine provides the actual reduction.
        """
        # Base reduction by type (heuristic, to be replaced by simulation)
        base_reductions: dict[InterventionType, float] = {
            InterventionType.DRAIN_CLEANING: 0.15,
            InterventionType.DRAIN_EXPANSION: 0.25,
            InterventionType.RETENTION_BASIN: 0.30,
            InterventionType.BIOSWALE: 0.10,
            InterventionType.PERMEABLE_SURFACE: 0.12,
            InterventionType.TREE_PLANTING: 0.08,
            InterventionType.COOL_ROOF: 0.15,
            InterventionType.SHADE_STRUCTURE: 0.12,
            InterventionType.FLOOD_BARRIER: 0.20,
            InterventionType.SEWER_UPGRADE: 0.22,
            InterventionType.ROUTE_DIVERSION: 0.05,
            InterventionType.EMERGENCY_CORRIDOR: 0.03,
        }
        base = base_reductions.get(spec.intervention_type, 0.10)

        # Scale by location vulnerability
        vulnerability = location.get("vulnerability", 0.5)
        return min(base * (0.5 + vulnerability), 0.5)

    def _estimate_combined_reduction(
        self,
        interventions: list[ConcreteIntervention],
        target_variable: str,
    ) -> float:
        """
        Estimate combined reduction with diminishing returns.

        DO NOT simply add individual scores — use multiplicative
        (1 - reduction) model for non-linear combination.
        """
        remaining = 1.0
        for intervention in interventions:
            remaining *= (1.0 - intervention.predicted_risk_reduction)
        return 1.0 - remaining

    def _mark_pareto_efficient(self, plans: list[InterventionPlan]) -> None:
        """
        Mark Pareto-efficient plans.

        A plan is Pareto-efficient if no other plan is strictly better
        on all objectives (risk_reduction, cost, complexity).
        """
        for i, plan_a in enumerate(plans):
            plan_a.is_pareto_efficient = True
            for j, plan_b in enumerate(plans):
                if i == j:
                    continue
                # plan_b dominates plan_a if better/equal on all, strictly better on at least one
                if (
                    plan_b.total_risk_reduction >= plan_a.total_risk_reduction
                    and plan_b.total_cost <= plan_a.total_cost
                    and plan_b.total_complexity <= plan_a.total_complexity
                    and (
                        plan_b.total_risk_reduction > plan_a.total_risk_reduction
                        or plan_b.total_cost < plan_a.total_cost
                        or plan_b.total_complexity < plan_a.total_complexity
                    )
                ):
                    plan_a.is_pareto_efficient = False
                    break


# ===================================================================
# Adversarial Critic Agent
# ===================================================================

class CriticAgent:
    """
    Attempts to break proposed intervention plans by testing
    adverse conditions, assumption failures, and edge cases.

    Asks:
    - What if rainfall is 30% higher?
    - What if downstream drain is blocked?
    - What if maintenance fails?
    - What if traffic doubles?
    - What if one intervention fails?
    """

    def __init__(self) -> None:
        self.stress_scenarios: list[dict[str, Any]] = [
            {"name": "rainfall_30pct_higher", "variable": "rainfall", "multiplier": 1.3},
            {"name": "rainfall_50pct_higher", "variable": "rainfall", "multiplier": 1.5},
            {"name": "extreme_rainfall", "variable": "rainfall", "multiplier": 2.0},
            {"name": "drain_blocked", "variable": "drain_capacity", "multiplier": 0.3},
            {"name": "reduced_maintenance", "variable": "drain_capacity", "multiplier": 0.7},
            {"name": "higher_temperature", "variable": "temperature", "multiplier": 1.15},
            {"name": "traffic_doubled", "variable": "traffic_density", "multiplier": 2.0},
            {"name": "partial_failure", "remove_intervention_pct": 0.3},
        ]

    def critique(
        self,
        plan: InterventionPlan,
        simulate_fn: Callable | None = None,
    ) -> tuple[bool, list[str]]:
        """
        Stress-test a plan against adverse scenarios.

        Returns:
            (passed, notes): Whether the plan survived criticism and reviewer notes.
        """
        notes: list[str] = []
        failures = 0

        for scenario in self.stress_scenarios:
            scenario_name = scenario.get("name", "unknown")

            if "remove_intervention_pct" in scenario:
                # Test partial intervention failure
                n_remove = max(
                    1,
                    int(len(plan.interventions) * scenario["remove_intervention_pct"]),
                )
                if n_remove >= len(plan.interventions):
                    notes.append(
                        f"⚠ {scenario_name}: Single-intervention plan has "
                        f"no redundancy."
                    )
                    failures += 1
                else:
                    notes.append(
                        f"✓ {scenario_name}: Plan has redundancy with "
                        f"{len(plan.interventions) - n_remove} remaining interventions."
                    )
            else:
                variable = scenario.get("variable", "")
                multiplier = scenario.get("multiplier", 1.0)

                # Estimate degraded effectiveness
                if multiplier > 1.0:
                    degradation = (multiplier - 1.0) * 0.8  # rough estimate
                    adjusted_reduction = plan.total_risk_reduction * (1.0 - degradation)
                    if adjusted_reduction < plan.total_risk_reduction * 0.5:
                        notes.append(
                            f"⚠ {scenario_name}: Plan effectiveness drops to "
                            f"{adjusted_reduction:.1f}% (from {plan.total_risk_reduction:.1f}%). "
                            f"Plan is FRAGILE under this scenario."
                        )
                        failures += 1
                    else:
                        notes.append(
                            f"✓ {scenario_name}: Plan maintains "
                            f"{adjusted_reduction:.1f}% reduction."
                        )
                elif multiplier < 1.0:
                    notes.append(
                        f"⚠ {scenario_name}: {variable} reduced to "
                        f"{multiplier * 100:.0f}% — downstream effects need evaluation."
                    )

        passed = failures <= len(self.stress_scenarios) // 3  # Allow some failures
        plan.critic_passed = passed
        plan.critic_notes = notes
        plan.robustness_profile = {
            "total_scenarios": len(self.stress_scenarios),
            "failures": failures,
            "robustness_score": 1.0 - failures / len(self.stress_scenarios),
        }

        return passed, notes


# ===================================================================
# Multi-Future Simulator
# ===================================================================

class MultiFutureSimulator:
    """
    Tests plans against multiple plausible future scenarios.

    Scenarios include:
    - Normal conditions
    - Heavy rainfall
    - Extreme rainfall
    - Blocked drainage
    - Reduced maintenance
    - Higher temperature
    - Higher traffic
    - Intervention degradation
    """

    def __init__(self) -> None:
        self.futures: list[dict[str, Any]] = [
            {"name": "Normal", "rainfall_mult": 1.0, "temp_mult": 1.0, "maintenance": 1.0},
            {"name": "Heavy Rain", "rainfall_mult": 1.5, "temp_mult": 1.0, "maintenance": 1.0},
            {"name": "Extreme Rain", "rainfall_mult": 2.5, "temp_mult": 1.0, "maintenance": 1.0},
            {"name": "Drain Failure", "rainfall_mult": 1.0, "drain_capacity_mult": 0.4, "maintenance": 1.0},
            {"name": "Low Maintenance", "rainfall_mult": 1.2, "maintenance": 0.6},
            {"name": "Heat Wave", "rainfall_mult": 0.3, "temp_mult": 1.3, "maintenance": 1.0},
            {"name": "Rush Hour + Rain", "rainfall_mult": 1.3, "traffic_mult": 2.0, "maintenance": 1.0},
            {"name": "Worst Case", "rainfall_mult": 2.0, "temp_mult": 1.2, "drain_capacity_mult": 0.5, "traffic_mult": 1.5, "maintenance": 0.5},
        ]

    def simulate_futures(
        self,
        plan: InterventionPlan,
        base_state: dict[str, float],
        simulate_fn: Callable | None = None,
    ) -> dict[str, dict[str, float]]:
        """
        Run plan through all future scenarios.

        Returns:
            dict mapping future_name → resulting metrics
        """
        results: dict[str, dict[str, float]] = {}

        for future in self.futures:
            name = future["name"]
            # Apply future modifiers to base state
            modified_state = dict(base_state)
            if "rainfall_mult" in future:
                modified_state["rainfall"] = base_state.get("rainfall", 0) * future["rainfall_mult"]
            if "temp_mult" in future:
                modified_state["temperature"] = base_state.get("temperature", 0) * future["temp_mult"]
            if "drain_capacity_mult" in future:
                modified_state["drain_capacity"] = base_state.get("drain_capacity", 0) * future["drain_capacity_mult"]
            if "traffic_mult" in future:
                modified_state["traffic_density"] = base_state.get("traffic_density", 0) * future["traffic_mult"]

            # Degrade interventions by maintenance factor
            maintenance = future.get("maintenance", 1.0)
            effective_reduction = plan.total_risk_reduction * maintenance

            results[name] = {
                "risk_reduction_pct": effective_reduction,
                "meets_target": effective_reduction >= plan.total_risk_reduction * 0.7,
                "conditions": future,
            }

        return results
