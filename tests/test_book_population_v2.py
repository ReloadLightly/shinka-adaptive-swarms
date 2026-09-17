"""One 401-query integration fixture for corrected geometry and accounting."""
from adaptive_swarms import book_population_v2


def test_corrected_engine_geometry_budget_and_roles(monkeypatch):
    calls = []
    predicate = book_population_v2.enclosing_ball_converged

    def observe(positions, radius):
        points = list(positions)
        assert 2 <= len(points) <= 8
        assert all(len(point) == 5 for point in points)
        calls.append(len(points))
        return predicate(points, radius)

    monkeypatch.setattr(book_population_v2, "enclosing_ball_converged", observe)
    result = book_population_v2.run_case(
        {"budget": 401, "period": 31, "trace_interval": 1, "npeaks": 200}, lambda _: 7)
    print("BOOK_POPULATION_V2_SMALL_FIXTURE_OBJECTIVE_QUERIES=401")
    assert result["engine_version"] == "book_mpso_population_v2_enclosing_ball"
    assert result["evaluations"] == sum(result["evaluation_counts"].values()) == 401
    assert calls and set(calls) <= {5, 6, 7}
    assert max(calls) > 5
    assert result["permanent_quantum"] == 1
    assert result["population_stats"]["additions"] > 0
    assert result["population_stats"]["removals"] == 0
    for row in result["response_log"]:
        assert row["neutral_count_after"] - row["neutral_count_before"] in (0, 1)
        assert row["decision"]["temporary_quantum_count"] == row["neutral_count_after"]
    assert "population_initialization" not in result["evaluation_counts"]
