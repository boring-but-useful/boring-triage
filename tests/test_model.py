from __future__ import annotations

from pathlib import Path

import pytest

from boring_triage.errors import ModelProviderError
from boring_triage.model import OpenAIModelAdapter


def test_live_adapter_fails_cleanly_without_api_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ModelProviderError, match="OPENAI_API_KEY is missing"):
        OpenAIModelAdapter(env_file=tmp_path / ".env.local")
