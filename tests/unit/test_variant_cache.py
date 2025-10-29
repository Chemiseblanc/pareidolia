"""Unit tests for variant cache."""

from datetime import datetime

import pytest

from pareidolia.generators.variant_cache import CachedVariant, VariantCache


class TestCachedVariant:
    """Tests for CachedVariant dataclass."""

    def test_create_cached_variant_with_all_fields(self) -> None:
        """Test creating a cached variant with all fields."""
        now = datetime.now()
        metadata = {"tool": "claude", "version": "1.0"}
        variant = CachedVariant(
            variant_name="update",
            action_name="research",
            persona_name="researcher",
            content="Generated content",
            generated_at=now,
            metadata=metadata,
        )

        assert variant.variant_name == "update"
        assert variant.action_name == "research"
        assert variant.persona_name == "researcher"
        assert variant.content == "Generated content"
        assert variant.generated_at == now
        assert variant.metadata == metadata

    def test_cached_variant_is_frozen(self) -> None:
        """Test that CachedVariant is immutable."""
        variant = CachedVariant(
            variant_name="update",
            action_name="research",
            persona_name="researcher",
            content="content",
            generated_at=datetime.now(),
        )

        with pytest.raises(AttributeError):
            variant.variant_name = "refine"  # type: ignore

    def test_cached_variant_default_metadata(self) -> None:
        """Test that metadata defaults to empty dict."""
        variant = CachedVariant(
            variant_name="update",
            action_name="research",
            persona_name="researcher",
            content="content",
            generated_at=datetime.now(),
        )

        assert variant.metadata == {}
        assert isinstance(variant.metadata, dict)

    def test_cached_variant_metadata_does_not_share_default(self) -> None:
        """Test that metadata default factory creates separate dicts."""
        variant1 = CachedVariant(
            variant_name="update",
            action_name="research",
            persona_name="researcher",
            content="content1",
            generated_at=datetime.now(),
        )
        variant2 = CachedVariant(
            variant_name="refine",
            action_name="analyze",
            persona_name="analyst",
            content="content2",
            generated_at=datetime.now(),
        )

        # Verify they have different dict instances
        assert variant1.metadata is not variant2.metadata
        assert variant1.metadata == variant2.metadata == {}


class TestVariantCache:
    """Tests for VariantCache singleton."""

    def test_variant_cache_singleton_returns_same_instance(self) -> None:
        """Test that VariantCache returns the same instance."""
        cache1 = VariantCache()
        cache2 = VariantCache()

        assert cache1 is cache2

    def test_add_single_variant(self) -> None:
        """Test adding a single variant to the cache."""
        cache = VariantCache()
        cache.clear()  # Ensure clean state

        variant = CachedVariant(
            variant_name="update",
            action_name="research",
            persona_name="researcher",
            content="content",
            generated_at=datetime.now(),
        )
        cache.add(variant)

        assert cache.count() == 1
        assert variant in cache.get_all()

    def test_add_multiple_variants(self) -> None:
        """Test adding multiple variants to the cache."""
        cache = VariantCache()
        cache.clear()

        variants = [
            CachedVariant(
                variant_name="update",
                action_name="research",
                persona_name="researcher",
                content="content1",
                generated_at=datetime.now(),
            ),
            CachedVariant(
                variant_name="refine",
                action_name="research",
                persona_name="researcher",
                content="content2",
                generated_at=datetime.now(),
            ),
            CachedVariant(
                variant_name="summarize",
                action_name="analyze",
                persona_name="analyst",
                content="content3",
                generated_at=datetime.now(),
            ),
        ]

        for variant in variants:
            cache.add(variant)

        assert cache.count() == 3
        assert all(v in cache.get_all() for v in variants)

    def test_get_all_returns_all_variants(self) -> None:
        """Test that get_all returns all cached variants."""
        cache = VariantCache()
        cache.clear()

        variants = [
            CachedVariant(
                variant_name="update",
                action_name="research",
                persona_name="researcher",
                content="content1",
                generated_at=datetime.now(),
            ),
            CachedVariant(
                variant_name="refine",
                action_name="analyze",
                persona_name="analyst",
                content="content2",
                generated_at=datetime.now(),
            ),
        ]

        for variant in variants:
            cache.add(variant)

        all_variants = cache.get_all()
        assert len(all_variants) == 2
        assert all(v in all_variants for v in variants)

    def test_get_all_returns_copy(self) -> None:
        """Test that get_all returns a copy, not the original list."""
        cache = VariantCache()
        cache.clear()

        variant = CachedVariant(
            variant_name="update",
            action_name="research",
            persona_name="researcher",
            content="content",
            generated_at=datetime.now(),
        )
        cache.add(variant)

        variants1 = cache.get_all()
        variants2 = cache.get_all()

        # Different list objects
        assert variants1 is not variants2
        # But same content
        assert variants1 == variants2

    def test_get_by_action_filters_correctly(self) -> None:
        """Test that get_by_action filters variants by action name."""
        cache = VariantCache()
        cache.clear()

        research_variants = [
            CachedVariant(
                variant_name="update",
                action_name="research",
                persona_name="researcher",
                content="content1",
                generated_at=datetime.now(),
            ),
            CachedVariant(
                variant_name="refine",
                action_name="research",
                persona_name="researcher",
                content="content2",
                generated_at=datetime.now(),
            ),
        ]

        analyze_variant = CachedVariant(
            variant_name="update",
            action_name="analyze",
            persona_name="analyst",
            content="content3",
            generated_at=datetime.now(),
        )

        for variant in research_variants + [analyze_variant]:
            cache.add(variant)

        filtered = cache.get_by_action("research")
        assert len(filtered) == 2
        assert all(v.action_name == "research" for v in filtered)
        assert all(v in filtered for v in research_variants)
        assert analyze_variant not in filtered

    def test_get_by_action_returns_empty_list_when_no_match(self) -> None:
        """Test that get_by_action returns empty list when no matches."""
        cache = VariantCache()
        cache.clear()

        variant = CachedVariant(
            variant_name="update",
            action_name="research",
            persona_name="researcher",
            content="content",
            generated_at=datetime.now(),
        )
        cache.add(variant)

        filtered = cache.get_by_action("nonexistent")
        assert filtered == []

    def test_get_by_variant_filters_correctly(self) -> None:
        """Test that get_by_variant filters variants by variant name."""
        cache = VariantCache()
        cache.clear()

        update_variants = [
            CachedVariant(
                variant_name="update",
                action_name="research",
                persona_name="researcher",
                content="content1",
                generated_at=datetime.now(),
            ),
            CachedVariant(
                variant_name="update",
                action_name="analyze",
                persona_name="analyst",
                content="content2",
                generated_at=datetime.now(),
            ),
        ]

        refine_variant = CachedVariant(
            variant_name="refine",
            action_name="research",
            persona_name="researcher",
            content="content3",
            generated_at=datetime.now(),
        )

        for variant in update_variants + [refine_variant]:
            cache.add(variant)

        filtered = cache.get_by_variant("update")
        assert len(filtered) == 2
        assert all(v.variant_name == "update" for v in filtered)
        assert all(v in filtered for v in update_variants)
        assert refine_variant not in filtered

    def test_get_by_variant_returns_empty_list_when_no_match(self) -> None:
        """Test that get_by_variant returns empty list when no matches."""
        cache = VariantCache()
        cache.clear()

        variant = CachedVariant(
            variant_name="update",
            action_name="research",
            persona_name="researcher",
            content="content",
            generated_at=datetime.now(),
        )
        cache.add(variant)

        filtered = cache.get_by_variant("nonexistent")
        assert filtered == []

    def test_clear_empties_cache(self) -> None:
        """Test that clear removes all variants from cache."""
        cache = VariantCache()
        cache.clear()

        variants = [
            CachedVariant(
                variant_name="update",
                action_name="research",
                persona_name="researcher",
                content="content1",
                generated_at=datetime.now(),
            ),
            CachedVariant(
                variant_name="refine",
                action_name="analyze",
                persona_name="analyst",
                content="content2",
                generated_at=datetime.now(),
            ),
        ]

        for variant in variants:
            cache.add(variant)

        assert cache.count() == 2

        cache.clear()

        assert cache.count() == 0
        assert cache.get_all() == []

    def test_has_variants_returns_true_when_variants_exist(self) -> None:
        """Test that has_variants returns True when cache has variants."""
        cache = VariantCache()
        cache.clear()

        variant = CachedVariant(
            variant_name="update",
            action_name="research",
            persona_name="researcher",
            content="content",
            generated_at=datetime.now(),
        )
        cache.add(variant)

        assert cache.has_variants() is True

    def test_has_variants_returns_false_when_empty(self) -> None:
        """Test that has_variants returns False when cache is empty."""
        cache = VariantCache()
        cache.clear()

        assert cache.has_variants() is False

    def test_count_returns_correct_number(self) -> None:
        """Test that count returns the correct number of variants."""
        cache = VariantCache()
        cache.clear()

        assert cache.count() == 0

        for i in range(5):
            variant = CachedVariant(
                variant_name=f"variant{i}",
                action_name="research",
                persona_name="researcher",
                content=f"content{i}",
                generated_at=datetime.now(),
            )
            cache.add(variant)
            assert cache.count() == i + 1

    def test_empty_cache_edge_case(self) -> None:
        """Test operations on empty cache."""
        cache = VariantCache()
        cache.clear()

        assert cache.get_all() == []
        assert cache.get_by_action("research") == []
        assert cache.get_by_variant("update") == []
        assert cache.count() == 0
        assert cache.has_variants() is False

    def test_duplicate_adds_are_allowed(self) -> None:
        """Test that adding duplicate variants is allowed."""
        cache = VariantCache()
        cache.clear()

        variant1 = CachedVariant(
            variant_name="update",
            action_name="research",
            persona_name="researcher",
            content="content",
            generated_at=datetime.now(),
        )
        variant2 = CachedVariant(
            variant_name="update",
            action_name="research",
            persona_name="researcher",
            content="content",
            generated_at=datetime.now(),
        )

        cache.add(variant1)
        cache.add(variant2)

        # Both should be in cache (they are different instances)
        assert cache.count() == 2

    def test_singleton_persists_across_instances(self) -> None:
        """Test that singleton state persists across multiple instance creations."""
        cache1 = VariantCache()
        cache1.clear()

        variant = CachedVariant(
            variant_name="update",
            action_name="research",
            persona_name="researcher",
            content="content",
            generated_at=datetime.now(),
        )
        cache1.add(variant)

        cache2 = VariantCache()

        # Same state should be visible
        assert cache2.count() == 1
        assert variant in cache2.get_all()
