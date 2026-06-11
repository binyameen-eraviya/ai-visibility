"""Application services that sit between interactors and external systems.

Each service hides an implementation detail behind a small interface so it can
be swapped later (e.g. local disk storage -> S3) without touching callers.
"""
