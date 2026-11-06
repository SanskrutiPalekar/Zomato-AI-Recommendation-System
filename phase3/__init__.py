"""
Phase 3: Integrate.
Integrates the Step 1 data knowledge base with Step 2 user inputs, producing
ranked candidate pools and token-efficient RAG context payloads for Step 4.
"""

from phase3.context_fusion import ContextFusionEngine
from phase3.filter_engine import FilterEngine
from phase3.integrator import IntegrationPipeline
from phase3.models import CandidateRestaurant, IntegrationContextPayload

__all__ = [
    "CandidateRestaurant",
    "IntegrationContextPayload",
    "FilterEngine",
    "ContextFusionEngine",
    "IntegrationPipeline",
]

