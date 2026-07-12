import os
import subprocess
import sys


def _alembic(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        check=False,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )


def test_migration_upgrade_downgrade_is_repeatable() -> None:
    first_down = _alembic("downgrade", "base")
    first_up = _alembic("upgrade", "head")
    second_down = _alembic("downgrade", "base")
    second_up = _alembic("upgrade", "head")

    assert first_down.returncode == 0, first_down.stderr
    assert first_up.returncode == 0, first_up.stderr
    assert second_down.returncode == 0, second_down.stderr
    assert second_up.returncode == 0, second_up.stderr
