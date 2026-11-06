"""
Uvicorn server launcher for Phase 6 API.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main():
    import uvicorn

    # Initialize the data store at startup
    from phase6.dependencies import initialize_store

    print("[*] Initializing restaurant data store...")
    store = initialize_store()
    print(f"[✓] Store ready — {store.count()} restaurants, {len(store.get_distinct_cities())} cities")
    print("[*] Starting Zomato AI Recommendation API on http://127.0.0.1:8000")
    print("[*] API docs at http://127.0.0.1:8000/docs")

    uvicorn.run(
        "phase6.api:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()

