"""
Configuration settings for Phase 4: Groq AI Recommendation Engine.
"""

import os

# Default Groq models (active on Groq Cloud)
# openai/gpt-oss-120b provides high reasoning; openai/gpt-oss-20b and qwen/qwen3.8-27b provide high speed
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
FAST_GROQ_MODEL = "openai/gpt-oss-20b"

# Generation settings
DEFAULT_TEMPERATURE = 0.2  # Low temperature for grounded recommendations
DEFAULT_MAX_TOKENS = 2500

# Environment variable name for Groq API key
GROQ_API_KEY_ENV = "GROQ_API_KEY"

# Candidate pool sizes
DEFAULT_FINAL_RECS_COUNT = 6  # Default top recommendations
MAX_FINAL_RECS_COUNT = 20

# Re-ranking composite weights (from Architecture.md)
WEIGHT_RATING = 0.45
WEIGHT_VOTES = 0.25
WEIGHT_BUDGET = 0.30

