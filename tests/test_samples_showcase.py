"""Integration test verifying the runnable samples showcase."""

from __future__ import annotations

import pytest

from samples.main import run_showcase


def test_samples_showcase_runs_end_to_end(capsys: pytest.CaptureFixture[str]) -> None:
    run_showcase()
    captured = capsys.readouterr().out
    assert "RQL LIBRARY — END-TO-END SHOWCASE" in captured
    assert "Matched Issue Keys : ['CRM-101']" in captured
    assert "SQL Search Total   : 2" in captured
