"""
src/zzproxies/core.py
The Orchestration Engine for Impact-Verified Zoning.
Handles Proxy Registration, Coverage Validation, and Pipeline Execution.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, Any, List, Optional, Type


# --- 1. Regional Constants (Standard ISO Alpha-2) ---

REGIONS = {
    "NORDICS": ["FI", "SE", "NO", "DK", "IS"],
    "EU": [
        "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", 
        "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", 
        "NL", "PL", "PT", "RO", "SE", "SI", "SK"
    ],
    "GLOBAL": ["GLOBAL"]
}


# --- 2. Data Structures for Governance ---

@dataclass
class CoverageLimit:
    """Geographic safety guard for proxy applicability."""
    allowed_regions: List[str]  # List of ISO Alpha-2 codes or ["GLOBAL"]
    data_source: str
    validation_note: str

    def is_allowed(self, country_code: str) -> bool:
        """Verifies if the location matches the proxy's scientific calibration."""
        if "GLOBAL" in self.allowed_regions:
            return True
        return country_code.upper() in self.allowed_regions


@dataclass
class ProxyStatus:
    """Metadata for scientific and operational status."""
    name: str
    version: str
    state: str  # "experimental", "beta", "production"
    description: str
    coverage: CoverageLimit


# --- 3. The Registry (The Orchestrator) ---

class ProxyRegistry:
    """
    Central Registry linking Impact Proxies to Discovery Blueprints.
    """
    def __init__(self):
        # Maps proxy_name -> function
        self._proxies: Dict[str, Callable] = {}
        # Maps proxy_name -> metadata (including required_blueprint)
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, required_blueprint: str, status: ProxyStatus):
        """
        Decorator to link an Impact Proxy to a specific Blueprint Class.
        """
        def decorator(func: Callable):
            self._proxies[name] = func
            self._metadata[name] = {
                "blueprint_name": required_blueprint,
                "status": status
            }
            return func
        return decorator

    def get_metadata(self, name: str) -> Dict[str, Any]:
        if name not in self._metadata:
            raise KeyError(f"Proxy '{name}' is not registered.")
        return self._metadata[name]

    def execute_pipeline(self, proxy_name: str, bbox: List[float], country_code: str) -> List[Dict[str, Any]]:
        """
        The Core Execution Loop:
        1. Context Check (Coverage)
        2. Discovery (Blueprint Run)
        3. Verification (Proxy Run)
        """
        from . import blueprints  # Local import to avoid circular dependencies
        meta = self.get_metadata(proxy_name)
        status: ProxyStatus = meta["status"]
        blueprint_class_name = meta["blueprint_name"]

        # 1. Coverage Pre-flight Check
        if not status.coverage.is_allowed(country_code):
            raise PermissionError(
                f"Geographic Check Failed: Proxy '{proxy_name}' is not validated for {country_code}. "
                f"Scientific Requirement: {status.coverage.allowed_regions}. "
                f"Note: {status.coverage.validation_note}"
            )

        # 2. Instantiate and Run Blueprint (The Discovery Phase)
        # We fetch the class from blueprints.py and initialize it
        if not hasattr(blueprints, blueprint_class_name):
            raise ImportError(f"Blueprint class '{blueprint_class_name}' not found in blueprints.py")
        
        blueprint_cls: Type = getattr(blueprints, blueprint_class_name)
        blueprint_instance = blueprint_cls(bbox=bbox, country_code=country_code)
        
        # This triggers integrated fetch + reclassification + possible imputation
        upd_data = blueprint_instance.run()

        # 3. Run Proxy (The Verification Phase)
        # Pass the UPD data into the mathematical model
        impact_results = self._proxies[proxy_name](upd_data)

        return impact_results


# Initialize the global registry singleton
registry = ProxyRegistry()