# Lifestyle Carbon: Pace of Life (SLF) (GWPL)

This is the most advanced proxy in the package, bridging urban morphology with human consumption behavior. It identifies the "Rebound Effect" where dense urban environments accelerate the pace of consumption.

### Methodology
The calculation is based on the **Situate Lifestyle Footprint (SLF) theory**, utilizing a dynamic interaction model. It assumes that a building's **Morphological Archetype** sets a baseline consumption pace, which is then accelerated or decelerated by the **Kinetic Intensity** of nearby consumer amenities (Retail & Food and Leisure travel).


### Epistemological Bridge
- **Normative Intent:** Zoning for "15-minute cities."
- **Empirical Reality:** High density + High accessibility = High-velocity consumption.
- **Verification:** This proxy uses the `pace_factor` to adjust the baseline 2.5t CO2e per capita (2025 targets) according to the manifested spatial reality.

### Dynamic GWPL Interaction (Interaction Matrix)
The GWPL is determined dynamically by the **Retail & Food NFA** count:

| Level | Threshold (NFA) | Description |
| :--- | :--- | :--- |
| **L4** | > 10,000 m² | **Critical Rebound**: Hyper-consumption urban hubs. |
| **L3** | > 5,000 m² | **High Pace**: Intensive urban consumption districts. |
| **L2** | > 2,000 m² | **Moderate Pace**: Standard mixed-use neighborhoods. |
| **L1** | > 100 m² | **Sufficiency**: Baseline low-consumption zones. |
| **L0** | < 100 m² | **Low Impact**: Accessible residential zones. |


### Citations
- SSRN 5290807: "Impact of Land-Use Planning on Lifestyle Carbon Footprints."
- IPCC AR6 Chapter 5: "Demand, services and social aspects of mitigation."