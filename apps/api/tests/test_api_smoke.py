from fenix_api import __version__


def test_package_imports() -> None:
    assert isinstance(__version__, str)
