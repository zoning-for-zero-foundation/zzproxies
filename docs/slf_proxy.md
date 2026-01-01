# Lifestyle Carbon

This is the most advanced proxy in the package, bridging urban morphology with human consumption behavior. It identifies the "Rebound Effect" where dense urban environments accelerate the pace of consumption.

### Methodology
The calculation is based on the **Situated Lifestyle Carbon Footprint (SLCF) theory**, utilizing a dynamic interaction model. It assumes that a building's **Morphological Archetype** sets a baseline consumption pace, which is then accelerated or decelerated by the **Kinetic Intensity** of nearby consumer amenities (Retail & Food) and Leisure travel. The proxy uses the `pace_factor` to adjust the baseline 2.5t CO2e per capita according to the manifested spatial reality defined by urban plans.

### Blueprint schema
The blueprint requires that each building has building type and Gross Floor Area (GFA) as well as distribution of Net Floor Area (NFA) by industry category defined as dict. The proxy applies the operational intensity on those industries, transforming economic activity into quantified Global Warming Potential Level (GWPL).

```python
# Example of required fields in the schema of the input data:
{
    "building_type": "apartment-condo", # string , one of:
    #["apartment-condo","multi-family-house","one-family-house","commercial","public","industrial"]
    "GFA": 7500.0, # float
    "NFA_by_industry": { # dict
                "Retail & Food": 400,
                "Accommodation": 0,
                "Health & Education": 0,
                "Leisure & Culture": 1300,
                "Industry & Services": 0,
                "Transport": 0,
                "Other": 5400
                } 
}

```

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