# Supply-Side Embodied GWP (GWPL)

This proxy verifies the "Carbon Debt" of the physical urban fabric, focusing on the upfront greenhouse gas emissions associated with building materials.

### Methodology
The calculation follows the **EN 15978:2011** standard for the assessment of environmental performance of buildings, specifically focusing on the **Life Cycle Stages A1-A3** (Product Stage: Raw material supply, transport, and manufacturing).

### Epistemological Bridge
- **Discovery:** The `blueprints.py` layer manifests the urban environment by extracting building footprints and Gross Floor Area (GFA) from "Ground Truth" spatial data (Overture/Cadastres).
- **Verification:** This proxy applies regional EU 2025 benchmarks to that GFA to determine the total upfront carbon investment required for the manifested zoning.

### GWPL Scaling (Global Warming Potential Level)
| Level | Range (t CO2e) | Description |
| :--- | :--- | :--- |
| **L4** | > 1000 | **Critical Carbon Debt**: High-intensity material use (e.g., massive industrial/commercial). |
| **L3** | 500 - 1000 | **High Carbon Debt**: Standard high-density urban construction. |
| **L2** | < 500 | **Moderate Carbon Debt**: Standard mid-to-low density urban fabric. |

### Citations
- EU Delegated Act C/2025/8723 on Life-Cycle GWP of Buildings.
- ISO 14040/44: Environmental management — Life cycle assessment.