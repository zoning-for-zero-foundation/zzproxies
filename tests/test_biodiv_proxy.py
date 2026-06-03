import sys

import pytest

sys.path.insert(0, "/workspaces/zzproxies/src")

from zzproxies.models import biodiv_proxy


def test_biodiv_proxy_aggregates_landcover_rows_into_gwpl():
    sample = [
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

    result = biodiv_proxy(sample)

    assert len(result) == 1
    assert result[0]["proxy_unit"] == "ecological_area_sqm"
    assert result[0]["proxy_value"] == 95.0
    assert result[0]["biodiversity_index"] == pytest.approx(0.475, rel=1e-3)
    assert result[0]["GWPL"].startswith("L2")


def test_biodiv_proxy_accepts_composition_mapping():
    sample = [
        {
            "id": "parcel-b",
            "landcover_composition": {
                "Vegetation_High": 120.0,
                "Sealed_Yard": 30.0,
            },
        }
    ]

    result = biodiv_proxy(sample)

    assert len(result) == 1
    assert result[0]["landcover_composition"]["Vegetation_High"] == 120.0
    assert result[0]["GWPL"].startswith("L1") or result[0]["GWPL"].startswith("L0")
