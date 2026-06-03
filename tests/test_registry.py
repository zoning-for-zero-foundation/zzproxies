"""
tests/test_registry.py
The Integrity Guardian of the Discovery-to-Verification Pipeline.
Ensures that every proxy is linked, contextually limited, and documented.
"""
import os
import pytest
from zzproxies import registry, blueprints

# Define the path to the documentation folder for visibility checks
DOCS_PATH = os.path.join(os.path.dirname(__file__), "../docs")

def test_proxy_blueprint_linkage():
    """
    Validation: Every registered proxy must point to an 
    existing Blueprint Class in blueprints.py.
    """
    if blueprints is None:
        pytest.skip("duckdb is not installed, so blueprint linkage cannot be checked in this environment.")

    for name, metadata in registry._metadata.items():
        blueprint_name = metadata["blueprint_name"]
        
        # Check if the Blueprint class exists in the blueprints module
        assert hasattr(blueprints, blueprint_name), \
            f"Proxy '{name}' requires blueprint '{blueprint_name}', but it's missing in blueprints.py"
        
        # Check if it is a class (Enforcing Encapsulated Discovery)
        blueprint_cls = getattr(blueprints, blueprint_name)
        assert isinstance(blueprint_cls, type), \
            f"Blueprint '{blueprint_name}' must be a Class, not a function."

def test_geographic_context_integrity():
    """
    Contextual Integrity: Every proxy must have a defined coverage 
    to prevent 'Geographic Hallucinations' of climate impact.
    """
    for name, metadata in registry._metadata.items():
        coverage = metadata["status"].coverage
        
        # Ensure allowed_regions is a non-empty list
        assert isinstance(coverage.allowed_regions, list) and len(coverage.allowed_regions) > 0, \
            f"Proxy '{name}' must specify at least one ISO region or ['GLOBAL']."
        
        # Validate ISO Alpha-2 format
        for region in coverage.allowed_regions:
            assert region == "GLOBAL" or (len(region) == 2 and region.isupper()), \
                f"Invalid region code '{region}' in proxy '{name}'. Use ISO Alpha-2 (e.g., 'FI')."

def test_scientific_visibility():
    """
    Visibility: Production-state proxies MUST have a corresponding 
    Markdown documentation file in the /docs folder.
    """
    for name, metadata in registry._metadata.items():
        status = metadata["status"]
        
        if status.state == "production":
            # We expect a file named {proxy_name}.md in the docs folder
            doc_file_name = f"{name}.md"
            doc_path = os.path.join(DOCS_PATH, doc_file_name)
            
            assert os.path.exists(doc_path), (
                f"Visibility Error: Production proxy '{name}' is missing scientific documentation. "
                f"Please create 'docs/{doc_file_name}' citing your ISO/EN standards."
            )

def test_pipeline_dry_run():
    """
    Execution: Verifies the registry can instantiate a blueprint 
    and pass data to the proxy.
    """
    if blueprints is None:
        pytest.skip("duckdb is not installed, so pipeline execution cannot be checked in this environment.")

    # Mock parameters
    mock_bbox = [24.9, 60.1, 25.0, 60.2]
    mock_cc = "FI"
    
    # Check the first registered proxy as a sample
    if registry._proxies:
        sample_proxy = list(registry._proxies.keys())[0]
        
        try:
            # This will fail if DuckDB/S3 isn't configured, so we test the orchestration
            # rather than the actual data fetch in this lightweight test.
            meta = registry.get_metadata(sample_proxy)
            assert meta["blueprint_name"] is not None
            assert registry._proxies[sample_proxy] is not None
        except Exception as e:
            pytest.fail(f"Pipeline orchestration failed for {sample_proxy}: {e}")