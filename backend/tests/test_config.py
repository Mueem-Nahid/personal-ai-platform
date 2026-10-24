from pathlib import Path

import pytest

from core.config import Settings


@pytest.fixture(autouse=True)
def clear_groq_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)


@pytest.mark.parametrize("name", ["GROQ_API_KEY", "APP_GROQ_API_KEY"])
def test_groq_key_from_dotenv(tmp_path: Path, name: str) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(f"{name}=test-key\n", encoding="utf-8")

    assert Settings(_env_file=env_file).groq_api_key == "test-key"


def test_backend_dotenv_overrides_root(tmp_path: Path) -> None:
    root_env = tmp_path / ".env"
    backend_env = tmp_path / "backend.env"
    root_env.write_text("APP_GROQ_API_KEY=root-key\n", encoding="utf-8")
    backend_env.write_text("APP_GROQ_API_KEY=backend-key\n", encoding="utf-8")

    assert Settings(_env_file=(root_env, backend_env)).groq_api_key == "backend-key"


def test_environment_overrides_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("GROQ_API_KEY=file-key\n", encoding="utf-8")
    monkeypatch.setenv("APP_GROQ_API_KEY", "environment-key")

    assert Settings(_env_file=env_file).groq_api_key == "environment-key"


def test_default_dotenv_paths_are_independent_of_working_directory() -> None:
    backend = Path(__file__).resolve().parents[1]

    assert Settings.model_config["env_file"] == (backend.parent / ".env", backend / ".env")
