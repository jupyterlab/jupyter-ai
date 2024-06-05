from pathlib import Path

import pytest

pytest_plugins = ("jupyter_server.pytest_plugin",)


@pytest.fixture
def jp_server_config(jp_server_config):
    return {"ServerApp": {"jpserver_extensions": {"jupyter_ai": True}}}


@pytest.fixture(scope="session")
def static_test_files_dir() -> Path:
    return (
        Path(__file__).parent.resolve()
        / "packages"
        / "jupyter-ai"
        / "jupyter_ai"
        / "tests"
        / "static"
    )


@pytest.fixture
def jp_ai_staging_dir(jp_data_dir: Path) -> Path:
    staging_area = jp_data_dir / "scheduler_staging_area"
    staging_area.mkdir()
    return staging_area
