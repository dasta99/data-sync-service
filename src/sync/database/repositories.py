"""Data repositories — backward compat redirect.

Use shared.repositories instead.
"""
from shared.repositories import SchemaManager, TableConfigRepository, WatermarkRepository

__all__ = ["SchemaManager", "TableConfigRepository", "WatermarkRepository"]
