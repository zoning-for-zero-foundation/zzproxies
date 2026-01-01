# zzproxies

**The Epistemological Bridge between Urban Planning and Climate Impact Research.**

`zzproxies` is a Python engine that bridges the gap between Normative **Urban Planning** (policy intent) and the latest research on **Climate Impacts** of land-use (empirical reality). It provides a unified, modular pipeline for discovering, developing, and modelling the climate impacts of urban plans.


---

## The Core Philosophy: Discovery-to-Verification

`zzproxies` treats the urban environment as an auditable data product engineered by urban planning blueprints as a public policy. Applying climate impact findings of particular activity - construction, business or lifestyle types - to the blueprint land-use data that facilitates them, we can discover & verify the systemic impacts of urban planning data based. The discovery can be used to define such blueprints which align with climate policy.

1.  **Discovery (The Blueprint):** Self-contained classes in `blueprints.py` fetch raw spatial data (Overture, OSM, National Cadastres etc.) and reclassify it into "Meaningful Zoning" designations.
2.  **Verification (The Proxy):** Mathematical functions in `models.py` calculate climate impacts using either established methods (e.g., GWP, PCF) or experimental methods developed by contributors (e.g., 'SLF' - Situated Lifestyle Carbon).
3.  **Policy (The Coverage):** Development of proxies and their blueprint requirements, using real-world data from selected geographic regions, defines the coverage in which their scientific calibration is valid. To mitigate impacts measured by a specific proxy, planners and consultants operating within the defined coverage region can apply the blueprint as a land-use plan to achieve a lower Global Warming Potential Level (GWPL) of urban development.



---

## Installation

`zzproxies` is designed to be lightweight. Choose the installation tier that matches your environment:

| Tier | Command | Best For |
| :--- | :--- | :--- |
| **Core** | `pip install zzproxies` | Production APIs and Microservices. |
| **Data** | `pip install "zzproxies[data]"` | Libraries to fetch raw data for **Blueprint** development (DuckDB/S3/requests..). |
| **Science** | `pip install "zzproxies[data,science]"` | City Science for Proxy Development in the **Datalab** (Pandas/GeoPandas/Momepy..). |

---

## Quick Start

```python
from zzproxies import registry, UrbanImpactReport
from zzproxies import compare_reports

# 1. Define your intent (BBOX and ISO Country Code)
bbox = [24.93, 60.16, 24.95, 60.18] # Helsinki Center
country_code = "FI"

# 2. Execute the Pipeline (Blueprint -> Proxy)
# The engine handles fetching, reclassification, and math in one go.
results = registry.execute_pipeline(
    proxy_name="my_proxy_name",
    bbox=bbox, 
    country_code=country_code
)

# 3. Generate a Policy-Ready Report
report = UrbanImpactReport("Helsinki_my_proxy", results)
print(report.summary)

# 4. Compare plans/locations by their impact
comparison_df = compare_reports([report_plan_a, report_plan_b])

```

  
## Project Structure
- src/zzproxies/core.py: The Registry and Orchestration engine.
- src/zzproxies/blueprints.py: Encapsulated Discovery (Data Fetching + Zoning Logic).
- src/zzproxies/models.py: Scientific Verification (Climate Impact Math).
- src/zzproxies/reports.py: Aggregation and Comparison functions.
- docs/: Scientific methodology and blueprint requirements of proxies as .md files.

