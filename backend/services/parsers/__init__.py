"""Parser building blocks (Milestone 3).

Pure, dependency-light modules that turn a raw scrape answer into structured
signals: brand mentions, sentiment, and cited sources. The orchestration and
DB writes live in backend/services/parser_service.py; these modules stay
testable in isolation (no DB, LLM calls expressed as prompt fragments the
orchestrator batches into a single request).
"""
