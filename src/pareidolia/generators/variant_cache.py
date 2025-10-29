"""Variant cache for storing generated variant content."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CachedVariant:
    """Represents a cached variant with metadata.

    Attributes:
        variant_name: The name of the variant (e.g., 'update', 'refine')
        action_name: The name of the action this variant is based on
        persona_name: The name of the persona this variant uses
        content: The generated variant content
        generated_at: Timestamp when the variant was generated
        metadata: Additional metadata associated with the variant
    """

    variant_name: str
    action_name: str
    persona_name: str
    content: str
    generated_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


class VariantCache:
    """Singleton cache for storing generated variants during a session.

    This class implements a singleton pattern to ensure all parts of the
    application share the same cache instance. It stores CachedVariant objects
    and provides methods to query and manage the cache.
    """

    _instance: "VariantCache | None" = None
    _variants: list[CachedVariant]

    def __new__(cls) -> "VariantCache":
        """Create or return the singleton instance.

        Returns:
            The singleton VariantCache instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._variants = []
        return cls._instance

    def add(self, variant: CachedVariant) -> None:
        """Add a variant to the cache.

        Args:
            variant: The CachedVariant to add to the cache.
        """
        self._variants.append(variant)

    def get_all(self) -> list[CachedVariant]:
        """Get all cached variants.

        Returns:
            List of all cached variants.
        """
        return self._variants.copy()

    def get_by_action(self, action_name: str) -> list[CachedVariant]:
        """Get all variants for a specific action.

        Args:
            action_name: The action name to filter by.

        Returns:
            List of variants matching the action name.
        """
        return [v for v in self._variants if v.action_name == action_name]

    def get_by_variant(self, variant_name: str) -> list[CachedVariant]:
        """Get all cached entries for a specific variant type.

        Args:
            variant_name: The variant name to filter by (e.g., 'update', 'refine').

        Returns:
            List of cached variants matching the variant name.
        """
        return [v for v in self._variants if v.variant_name == variant_name]

    def clear(self) -> None:
        """Clear all variants from the cache."""
        self._variants.clear()

    def has_variants(self) -> bool:
        """Check if the cache contains any variants.

        Returns:
            True if cache contains variants, False otherwise.
        """
        return len(self._variants) > 0

    def count(self) -> int:
        """Get the number of variants in the cache.

        Returns:
            The number of cached variants.
        """
        return len(self._variants)
