import pytest

from fenix_retrieval.rrf import rrf_fuse


def test_consensus_wins() -> None:
    fused = rrf_fuse([[1, 2, 3], [2, 1, 4], [2, 5, 1]])
    assert fused[0][0] == 2


def test_single_ranking_preserves_order() -> None:
    fused = rrf_fuse([[7, 3, 9]])
    assert [item_id for item_id, _ in fused] == [7, 3, 9]

    fused_scores = dict(fused)
    assert fused_scores[7] == pytest.approx(1 / 61)
    assert fused_scores[3] == pytest.approx(1 / 62)


def test_absent_ids_do_not_score() -> None:
    fused = dict(rrf_fuse([[1], [2]]))
    assert fused[1] == fused[2] == pytest.approx(1 / 61)


def test_ties_break_by_id() -> None:
    fused = rrf_fuse([[4], [2]])
    assert [item_id for item_id, _ in fused] == [2, 4]


def test_empty_rankings() -> None:
    assert rrf_fuse([]) == []
    assert rrf_fuse([[], []]) == []


def test_invalid_k() -> None:
    with pytest.raises(ValueError):
        rrf_fuse([[1]], k=0)
