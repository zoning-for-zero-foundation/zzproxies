# Biodiversity Support Proxy

This proxy translates Overture landcover output into a biodiversity support score that can be compared with the rest of the `zzproxies` outcome pipeline through the shared `GWPL` field.

### Blueprint schema

The proxy is designed to consume the output of `OvertureMapLandcoverForBiodiversity` from `src/zzproxies/blueprints.py`. The blueprint emits rows with fields such as:

- `id`
- `landcover_class`
- `area_sqm`
- `ecological_area_sqm`
- `wkt`

The proxy also accepts an aggregated `landcover_composition` dictionary where keys are landcover classes and values are areas.

### Methodology

The proxy computes a weighted ecological area from the landcover mix. Permeable and biologically active surfaces contribute more strongly than sealed or built surfaces. The resulting `proxy_value` is the total ecological area in square metres, while `biodiversity_index` is the normalized ecological support ratio in the $0$ to $1$ range.

The ordinal `GWPL` label is reused as the common outcome scale across the library:

| Level | Interpretation |
| :--- | :--- |
| `L0` | High Biodiversity Support |
| `L1` | Strong Urban Habitat |
| `L2` | Transitional Habitat |
| `L3` | Fragmented Habitat |
| `L4` | Critical Biodiversity Pressure |

### Example

```python
from zzproxies.models import biodiv_proxy

data = [
    {
        "id": "parcel-a",
        "landcover_class": "Managed_Yard",
        "area_sqm": 100.0,
        "ecological_area_sqm": 60.0,
    },
    {
        "id": "parcel-a",
        "landcover_class": "Bare_Soil",
        "area_sqm": 100.0,
        "ecological_area_sqm": 35.0,
    },
]

result = biodiv_proxy(data)
```

This produces one aggregated record for `parcel-a` with a biodiversity index and a `GWPL` label.
