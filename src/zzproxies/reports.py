
"""
src/zzproxies/reports.py
Universal GWPL Aggregator.
"""
from typing import List, Dict, Any
from collections import Counter

class UrbanImpactReport:
    def __init__(self, name: str, results: List[Dict[str, Any]]):
        self.name = name
        self.results = results
        self.summary = self._generate_summary()

    def _generate_summary(self) -> Dict[str, Any]:
        if not self.results:
            return {"district": self.name, "status": "Empty"}
            
        # Detect Metadata
        unit = self.results[0].get('proxy_unit', 'units')
        
        # Aggregations
        total_val = sum(r.get('proxy_value', 0) for r in self.results)
        
        # GWPL Level Distribution
        # Extracts 'L0', 'L1', etc. from the mitigation_insight string
        gwpl_counts = Counter(
            r.get('GWPL', 'L2').split(':')[0] 
            for r in self.results
        )
        
        return {
            "district_name": self.name,
            "total_impact": round(total_val, 2),
            "unit": unit,
            "gwpl_distribution": dict(gwpl_counts),
            "critical_assets_L4": gwpl_counts.get("L4", 0),
            "high_risk_assets_L3": gwpl_counts.get("L3", 0),
            "primary_methodology": self.results[0].get('methodology', 'N/A')
        }

def compare_reports(reports: List[UrbanImpactReport]) -> List[Dict[str, Any]]:
    """Compares side-by-side regardless of the underlying proxy math."""
    return [r.summary for r in reports]

