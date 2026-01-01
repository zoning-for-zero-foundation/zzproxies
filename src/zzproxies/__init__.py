"""
zzproxies: The Epistemological Bridge between Climate Science and Urban Planning.
An all-in-one package for Discovery-to-Verification Urban Research for Land-use Zoning development.
"""

from .core import registry, ProxyStatus, CoverageLimit, REGIONS
from . import blueprints, models, reports
from .reports import UrbanImpactReport, compare_reports

__all__ = [
    "registry",
    "ProxyStatus",
    "CoverageLimit",
    "REGIONS",
    "blueprints",
    "models",
    "reports",
    "UrbanImpactReport",
    "compare_reports"
]
 
__version__ = "0.9.0"
__author__ = "Zoning For Zero Foundation"