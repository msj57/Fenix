import pytest

from fenix_retrieval.metrics import hit_at_k, mean, reciprocal_rank

RELEVANT = {"runbooks/rb-001.md", "postmortems/pm-2026-02.md"}


def test_hit_at_k_found_within_k() -> None:
    retrieved = ["tickets/tk-1.md", "runbooks/rb-001.md", "runbooks/rb-9.md"]
    assert hit_at_k(retrieved, RELEVANT, k=3) == 1.0


def test_hit_at_k_outside_k_is_miss() -> None:
    retrieved = ["tickets/tk-1.md", "runbooks/rb-9.md", "runbooks/rb-001.md"]
    assert hit_at_k(retrieved, RELEVANT, k=2) == 0.0


def test_hit_at_k_none_relevant() -> None:
    assert hit_at_k(["x.md", "y.md"], RELEVANT, k=5) == 0.0


def test_reciprocal_rank_first_position() -> None:
    assert reciprocal_rank(["runbooks/rb-001.md", "x.md"], RELEVANT) == pytest.approx(1.0)


def test_reciprocal_rank_third_position() -> None:
    retrieved = ["x.md", "y.md", "postmortems/pm-2026-02.md"]
    assert reciprocal_rank(retrieved, RELEVANT) == pytest.approx(1 / 3)


def test_reciprocal_rank_dedupes_repeated_docs() -> None:
    # dos chunks del mismo doc irrelevante no deben penalizar el rango del relevante
    retrieved = ["x.md", "x.md", "runbooks/rb-001.md"]
    assert reciprocal_rank(retrieved, RELEVANT) == pytest.approx(1 / 2)


def test_reciprocal_rank_no_match() -> None:
    assert reciprocal_rank(["a.md", "b.md"], RELEVANT) == 0.0


def test_mean_empty_is_zero() -> None:
    assert mean([]) == 0.0


def test_mean_basic() -> None:
    assert mean([1.0, 0.0, 0.5]) == pytest.approx(0.5)
