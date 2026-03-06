import sys
from pathlib import Path
import pytest

# Ensure project root is importable when running pytest from various working directories.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.store.memory import store


@pytest.fixture(autouse=True)
def _isolate_in_memory_store():
    """
    The app uses a module-level singleton store. Clear it between tests so
    tests don't implicitly depend on execution order.
    """
    with store._lock:
        store._docs.clear()
    yield
    with store._lock:
        store._docs.clear()
