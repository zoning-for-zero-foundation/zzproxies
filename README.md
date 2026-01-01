# 🏙️ zzproxies

**The Epistemological Bridge for Urban Climate Policy.**

`zzproxies` is a high-performance Python engine that bridges the gap between **Normative Urban Planning** (policy intent) and **Spatial Ground Truth** (empirical reality). It provides a unified, modular pipeline to discover, manifest, and verify the climate impacts of urban zoning designations.


---

## 🚀 The Core Philosophy: Discovery-to-Verification

Unlike traditional GIS tools that merely describe spatial data, `zzproxies` treats the urban environment as an auditable data product. 

1.  **Discovery (The Blueprint):** Self-contained classes in `blueprints.py` fetch raw spatial data (Overture, OSM, National Cadastres etc.) and reclassify it into "Meaningful Zoning" designations.
2.  **Verification (The Proxy):** Mathematical functions in `models.py` calculate the climate impacts using established methods (e.g., GWP, PCF) as well as experimental ones developed by contributors (e.g., 'SLF' - Situated Lifestyle Carbon) of those designations.
3.  **Context (The Coverage):** Geographic safety guards ensure that proxies are only applied in regions where their scientific calibration is valid.



---

## 🛠️ Installation

`zzproxies` is designed to be lightweight. Choose the installation tier that matches your environment:

| Tier | Command | Best For |
| :--- | :--- | :--- |
| **Core** | `pip install zzproxies` | Production APIs and Microservices. |
| **Data** | `pip install "zzproxies[data]"` | Libraries to fetch raw data for **Blueprint** development (DuckDB/S3/requests..). |
| **Science** | `pip install "zzproxies[data,science]"` | City Science for Proxy Development in the **Datalab** (Pandas/GeoPandas/Momepy..). |

---

## 📖 Quick Start

```python
from zzproxies import registry, UrbanImpactReport

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
```
  

## 🧪 The Transdisciplinary Workflow

**For Climate Research**
Use the datalab environment to perform Exploratory Data Analysis (EDA). Once you discover a new way to classify urban fabric (e.g., "Heat-Island Zones"), wrap your logic into a new Blueprint Class and link it to your Impact Proxy function!

**For Policy Development**
Compare different districts or "What If" scenarios of selected proxy using the reports module.  

```python
from zzproxies import compare_reports
comparison = compare_reports([report_plan_a, report_plan_b])
```
  
## 🏛️ Project Structure
- src/zzproxies/core.py: The Registry and Orchestration engine.
- src/zzproxies/blueprints.py: Encapsulated Discovery (Data Fetching + Zoning Logic).
- src/zzproxies/models.py: Scientific Verification (Climate Impact Math).
- src/zzproxies/reports.py: Aggregation and Comparison logic.
- docs/: Scientific methodology and ISO/EN standard citations.

## 🤝 Contributing
We welcome contributions for:
- **New Blueprints:** Manifest new zoning designations from novel data sources.
- **New Proxies:** Verify impacts using regional or industry-specific benchmarks.  
_Read more in datalab 👉 [CONTRIBUTE.md](https://github.com/zoning-for-zero-foundation/datalab/CONTRIBUTE.md)_