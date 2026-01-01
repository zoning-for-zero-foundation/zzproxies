# Activity-Side PCF Impact

This proxy treats urban amenities as "Planning Products," quantifying the annual carbon footprint of the services and activities facilitated by specific zoning designations.

### Methodology
The calculation is grounded in **ISO 14067:2018** (Product Carbon Footprint - PCF). It uses **Area-Based Allocation** to distribute the carbon intensity of various industry sectors (Retail, Accommodation, Industry) across the Net Floor Area (NFA) manifested by the blueprint.

### Blueprint schema
The blueprint requires that each building has distribution of Net Floor Area (NFA) by industry category defined as dict. The proxy applies the operational intensity on those industries, transforming economic activity into quantified Global Warming Potential Level (GWPL).
  
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

### GWPL Scaling
| Level | Range (t CO2e/yr) | Description |
| :--- | :--- | :--- |
| **L4** | > 500 | **Critically High Consumer Activity Intensity**: Massive commercial/service hubs. |
| **L3** | 100 - 500 | **High Activity Intensity**: Active urban zones. |
| **L2** | 20 - 100 | **Moderate Activity Intensity**: Standard mixed-use zones. |
| **L1** | < 20 | **Baseline Activity Intensity**: Passive residential or low-impact services. |
| **L0** | < 20 | **Low Activity Intensity**: Passive residential zones etc. |
