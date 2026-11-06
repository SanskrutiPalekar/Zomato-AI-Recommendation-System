"""
Phase 5: Display to the User & Full System Integration.
Integrates all 5 layers (Data -> Input -> Integrate -> Recommend -> Display)
with extensible Display Adapters (CLI & JSON).
"""

from phase5.display_adapter import CLIDisplayAdapter, DisplayAdapter, JSONDisplayAdapter
from phase5.service import ZomatoAIService

__all__ = [
    "DisplayAdapter",
    "CLIDisplayAdapter",
    "JSONDisplayAdapter",
    "ZomatoAIService",
]

