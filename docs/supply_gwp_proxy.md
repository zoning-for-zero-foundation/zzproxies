# Embodied Global Warming Potential

This proxy verifies the "Carbon Debt" of the physical urban fabric, focusing on the upfront greenhouse gas emissions associated with building materials.

### Methodology
The calculation follows the **EN 15978:2011** standard for the assessment of environmental performance of buildings, specifically focusing on the **Life Cycle Stages A1-A3** (Product Stage: Raw material supply, transport, and manufacturing). Global Warming Potential (GWP) as a unit applies EU Delegated Act C/2025/8723 on Life-Cycle GWP of Buildings to determine the total upfront carbon investment required for the manifested zoning.

### Blueprint schema
The blueprint requires that each building has building type and Gross Floor Area (GFA).

```python
# Example of required fields in the schema of the input data:
{
    "building_type": "apartment-condo", # string , one of:
    #["apartment-condo","multi-family-house","one-family-house","commercial","public","industrial"]
    "GFA": 7500.0, # float
}

```

### GWPL Scaling (Global Warming Potential Level)
| Level | Range (t CO2e) | Description |
| :--- | :--- | :--- |
| **L4** | > 1000 | **Critical Carbon Debt**: High-intensity material use (e.g., massive industrial/commercial). |
| **L3** | 500 - 1000 | **High Carbon Debt**: Standard high-density urban construction. |
| **L2** | > 500 | **Moderate Carbon Debt**: Standard mid-density urban fabric. |
| **L1** | > 100 | **Baseline Carbon Debt**: Standard mid-to-low density urban fabric. |
| **L0** | < 100 | **Low Carbon Debt**: low density urban fabric. |