def test_package_import_exposes_core_api():
    import zzproxies

    assert zzproxies.registry is not None
    assert callable(zzproxies.compare_reports)
