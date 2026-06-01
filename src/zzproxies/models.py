"""
src/zzproxies/models.py
Verification Models: Impact calculation for Impact-Verified Zoning.
Linked to OvertureMapBuildingsWithPlaces blueprint.
"""

from .core import registry, ProxyStatus, CoverageLimit, REGIONS
from typing import List, Dict, Any

# --- 2025 EU Sustainability Benchmarks ----
# Sourced from Delegated Act C/2025/8723 and ISO 14067 defaults
GWP_BENCHMARKS = {
    "SUPPLY_SIDE": {  # kg CO2e / m2 (Upfront Embodied)
        "one-family-house": 650.0,
        "multi-family-house": 720.0,
        "apartment-condo": 780.0,
        "commercial": 850.0,
        "public": 800.0,
        "industrial": 1100.0,
    },
    "ACTIVITY_SIDE": {  # kg CO2e / m2 / yr (Annual Activity)
        "Retail & Food": 150.5,
        "Accommodation": 85.2,
        "Health & Education": 45.0,
        "Leisure & Culture": 30.0,
        "Industry & Services": 320.0,
        "Transport": 12.0,
    }
}

# --- 1. Upfront GWP (Supply-Side) ---

@registry.register(
    name="upfront_gwp_supply",
    required_blueprint="OvertureMapBuildingsWithPlaces",
    status=ProxyStatus(
        name="Supply-Side Embodied GWP",
        version="1.0.0",
        state="production",
        description="Calculates upfront CO2e from estimated building materials (A1-A3).",
        coverage=CoverageLimit(
            allowed_regions=REGIONS["EU"],
            data_source="Overture Buildings",
            validation_note="Calibrated for EU material intensity standards."
        )
    )
)
def supply_gwp_proxy(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Verifies 'Carbon Debt' of the urban fabric.
    Inputs: UPD schema (GFA, building_type).
    """
    for record in data:
        # 1. Force GFA to float and handle 'null' or None
        raw_gfa = record.get("GFA")
        gfa = float(raw_gfa) if (raw_gfa is not None and str(raw_gfa).lower() != "null") else 0.0
        # 2. Handle building type 'null' or None
        raw_type = record.get("building_type")
        b_type = str(raw_type) if (raw_type is not None and str(raw_type).lower() != "null") else "other"
        
        factor = GWP_BENCHMARKS["SUPPLY_SIDE"].get(b_type, 700.0)
        gwp_t = round((gfa * factor) / 1000, -1)
        
        if gwp_t > 1000:
            gwpl = "L4: Critical Carbon Debt"
        elif gwp_t > 500:
            gwpl = "L3: High Carbon Debt"
        elif gwp_t > 200:
            gwpl = "L2: Moderate Carbon Debt"
        elif gwp_t > 100:
            gwpl = "L1: Baseline"
        else:
            gwpl = "L0: Low Carbon Debt"

        record.update({
            "proxy_value": gwp_t,
            "proxy_unit": "t_CO2e_upfront",
            "GWPL": gwpl
        })
    return data


# --- 2. Activity-Side PCF (Product Impact) ---

@registry.register(
    name="activity_gwp_pcf",
    required_blueprint="OvertureMapBuildingsWithPlaces_vDEC2025",
    status=ProxyStatus(
        name="Activity-Side PCF Impact",
        version="0.9.0",
        state="experimental",
        description="Estimates annual GWP of services (PCF) based on ISO 14067.",
        coverage=CoverageLimit(
            allowed_regions=["GLOBAL"],
            data_source="Overture Buildings and Places",
            validation_note="Uses global average industry PCF intensities."
        )
    )
)
def activity_pcf_proxy(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    The Blueprint data must provide NFA_by_industry with correct categories.
    """
    for record in data:
        # CHECK NFA Dictionary: Ensure it is a valid dict and not a 'null' string
        raw_nfa = record.get("NFA_by_industry")
        if isinstance(raw_nfa, dict):
            nfas = raw_nfa
        elif isinstance(raw_nfa, str) and raw_nfa.lower() != "null":
            # Handle cases where dict might be a JSON string
            import json
            try:
                nfas = json.loads(raw_nfa)
            except:
                nfas = {}
        else:
            nfas = {}

        total_pcf_kg = 0.0
        
        # Mapping categories directly to Activity Benchmarks
        for category, area in nfas.items():
            factor = GWP_BENCHMARKS["ACTIVITY_SIDE"].get(category, 25.0)
            total_pcf_kg += (area * factor)
            
        pcf_t = round(total_pcf_kg / 1000, -1)
        
        if pcf_t > 500:
            gwpl = "L4: Critically High Consumer Activity Intensity"
        elif pcf_t > 100:
            gwpl = "L3: High Consumer Activity Intensity"
        elif pcf_t > 20:
            gwpl = "L2: Moderate Consumer Activity Intensity"
        elif pcf_t > 10:
            gwpl = "L1: Baseline Consumer Activity Intensity"
        else:
            gwpl = "L0: Low Consumer Activity Intensity"
        record.update({
            "proxy_value": pcf_t,
            "proxy_unit": "t_CO2e_pcf_annual",
            "GWPL": gwpl
        })
    return data


# --- 3. Lifestyle Carbon (experimental) ---

@registry.register(
    name="slf_proxy",
    required_blueprint="OvertureMapBuildingsWithPlaces",
    status=ProxyStatus(
        name="Situated Lifestyle Footprint",
        version="0.9.0",
        state="experimental",
        description="Measures lifestyle GWP using the Situated Lifestyle Footprint (SLF) factor.",
        coverage=CoverageLimit(
            allowed_regions=REGIONS["NORDICS"],
            data_source="Overture Buildings and Places",
            validation_note="Statistically found rebound factors based on SSRN 5290807."
        )
    )
)
def slf_proxy(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Dynamically maps GWPL based on consumption intensity of NFA_by_industry 
    and morphological archetype.
    """
    # 1. Configuration: Morphological Base Multipliers
    ARCHETYPE_FACTORS = {
        'apartment-condo': 1.20,
        'multi-family-house': 1.00,
        'one-family-house': 0.75,
        'default': 1.00
    }

    # 2. Configuration: Intensity Thresholds for Pace Up-scaling
    # Maps Retail & Food NFA to GWPL Levels and Boost Factors in unit (building or plot)
    INTENSITY_MAP = [
        (2000, "L4: Critical Consumption Rebound", 1.45),
        (1000,  "L3: High Consumption Pace", 1.30),
        (500,  "L2: Moderate Consumption Pace", 1.15),
        (100,   "L1: Sufficiency baseline", 1.05),
        (0,     "L0: Below baseline", 1.00)
    ]

    for record in data:
        # 1. Force GFA to float and handle 'null' or None
        raw_gfa = record.get("GFA")
        gfa = float(raw_gfa) if (raw_gfa is not None and str(raw_gfa).lower() != "null") else 0.0
        # 2. Handle building type 'null' or None
        raw_type = record.get("building_type")
        b_type = str(raw_type) if (raw_type is not None and str(raw_type).lower() != "null") else "other"
        # 3. CHECK NFA Dictionary: Ensure it is a valid dict and not a 'null' string
        raw_nfa = record.get("NFA_by_industry")
        if isinstance(raw_nfa, dict):
            nfa_dist = raw_nfa
        elif isinstance(raw_nfa, str) and raw_nfa.lower() != "null":
            # Handle cases where dict might be a JSON string
            import json
            try:
                nfa_dist = json.loads(raw_nfa)
            except:
                nfa_dist = {}
        else:
            nfa_dist = {}
        
        # Extract Consumption Intensity
        retail_food_nfa = nfa_dist.get("Retail & Food", 0.0)

        # 3. Dynamic Mapping
        # Find the first threshold that the NFA exceeds (highest to lowest)
        gwpl, intensity_boost = next(
            (label, boost) for threshold, label, boost in INTENSITY_MAP 
            if retail_food_nfa >= threshold
        )

        # Calculate final Pace Factor: Archetype Base * Intensity Boost
        # e.g., building type with retail NFA becomes mixed.
        base_factor = ARCHETYPE_FACTORS.get(b_type, ARCHETYPE_FACTORS['default'])
        final_pace_factor = base_factor * intensity_boost

        # 4. Impact Calculation (t CO2e annual)
        # Base: 2.5t per capita / 45m2 per capita
        total_lifestyle_t = (gfa / 45.0) * 2.5 * final_pace_factor

        record.update({
            "proxy_value": round(total_lifestyle_t, -1),
            "proxy_unit": "t_CO2e_lifestyle_annual",
            "GWPL": gwpl
        })

    return data