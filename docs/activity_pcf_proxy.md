# Activity-Side PCF Impact (GWPL)

This proxy treats urban amenities as "Planning Products," quantifying the annual carbon footprint of the services and activities facilitated by specific zoning designations.

### Methodology
The calculation is grounded in **ISO 14067:2018** (Product Carbon Footprint - PCF). It uses **Area-Based Allocation** to distribute the carbon intensity of various industry sectors (Retail, Accommodation, Industry) across the Net Floor Area (NFA) manifested by the blueprint.

### Epistemological Bridge
- **Discovery:** The blueprint performs a spatial join between building footprints and amenity "Places," creating an internal distribution of NFA by industry category.
- **Verification:** This proxy verifies the operational intensity of those industries, transforming economic activity into a scientifically quantified GWP value.

### GWPL Scaling
| Level | Range (t CO2e/yr) | Description |
| :--- | :--- | :--- |
| **L3** | > 100 | **High Activity Intensity**: Massive commercial/service hubs. |
| **L2** | 20 - 100 | **Moderate Activity Intensity**: Standard mixed-use or active urban zones. |
| **L1** | < 20 | **Low Activity Intensity**: Passive residential or low-impact services. |

### Citations
- ISO 14067:2018 Greenhouse gases — Carbon footprint of products.
- GPC (Global Protocol for Community-Scale GHG Inventories).