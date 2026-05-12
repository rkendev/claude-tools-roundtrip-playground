"""CLI plumbing tests for ``python -m claude_tools_roundtrip_playground``.

Mocks ``run_roundtrip`` at the ``__main__`` import boundary so no
Anthropic API call is made --- the goal is covering argparse, env-var
validation, and the dispatch into ``run_roundtrip`` in ``__main__.py``.
Mirrors Artifact C's ``tests/unit/test_cli.py`` pattern.
"""

from __future__ import annotations

from typing import Any

import pytest

from claude_tools_roundtrip_playground import __main__ as cli_module
from claude_tools_roundtrip_playground.__main__ import main
from claude_tools_roundtrip_playground.playground import MODEL_DEFAULT


class TestMain:
    def test_no_args_exits_2(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with pytest.raises(SystemExit) as excinfo:
            main([])
        assert excinfo.value.code == 2
        err = capsys.readouterr().err
        assert "usage:" in err
        assert "question" in err

    def test_missing_api_key_returns_1(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        rc = main(["test question"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "ANTHROPIC_API_KEY" in err
        assert "not set" in err

    def test_default_model_dispatch(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "stub")
        calls: list[dict[str, Any]] = []

        def _stub(question: str, *, model: str, **_: Any) -> str:
            calls.append({"question": question, "model": model})
            return "stub-final-text"

        monkeypatch.setattr(cli_module, "run_roundtrip", _stub)
        rc = main(["test question"])
        assert rc == 0
        assert len(calls) == 1
        assert calls[0]["question"] == "test question"
        assert calls[0]["model"] == MODEL_DEFAULT

    def test_model_override(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "stub")
        calls: list[dict[str, Any]] = []

        def _stub(question: str, *, model: str, **_: Any) -> str:
            calls.append({"question": question, "model": model})
            return "stub-final-text"

        monkeypatch.setattr(cli_module, "run_roundtrip", _stub)
        rc = main(["test question", "--model", "claude-sonnet-4-6"])
        assert rc == 0
        assert calls == [
            {"question": "test question", "model": "claude-sonnet-4-6"},
        ]
