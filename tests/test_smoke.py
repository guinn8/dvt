from importlib import metadata
def test_import():
    assert metadata.version("dvt")  # package metadata resolves
