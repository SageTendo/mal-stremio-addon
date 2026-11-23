from app.services.cinemeta_service import (
    compute_per_season_counts,
    place_episode,
    unplace_episode,
)


# ----- compute_per_season_counts -----


def test_compute_per_season_counts_scopes_to_season_range():
    videos = [
        {"season": 1, "episode": 1},
        {"season": 1, "episode": 2},
        {"season": 2, "episode": 1},
        {"season": 3, "episode": 1},  # belongs to the next entry, must be excluded
    ]
    counts = compute_per_season_counts(
        videos=videos, from_season=1, from_episode=1, next_from_season=3
    )
    assert counts == [2, 1]


def test_compute_per_season_counts_excludes_episodes_before_starting_point():
    videos = [
        {"season": 1, "episode": 1},
        {"season": 1, "episode": 2},
        {"season": 1, "episode": 3},
    ]
    counts = compute_per_season_counts(videos=videos, from_season=1, from_episode=2)
    assert counts == [2]


def test_compute_per_season_counts_uses_number_field_fallback():
    videos = [{"season": 1, "number": 1}, {"season": 1, "number": 2}]
    counts = compute_per_season_counts(videos=videos, from_season=1, from_episode=1)
    assert counts == [2]


# ----- place_episode -----


def test_place_episode_single_season():
    assert place_episode(
        from_season=1,
        from_episode=1,
        per_season_counts=[12],
        non_imdb_episodes=frozenset(),
        absolute_episode=5,
    ) == (1, 5)


def test_place_episode_crosses_season_boundary():
    counts = [12, 13]
    assert place_episode(
        from_season=1,
        from_episode=1,
        per_season_counts=counts,
        non_imdb_episodes=frozenset(),
        absolute_episode=13,
    ) == (2, 1)
    assert place_episode(
        from_season=1,
        from_episode=1,
        per_season_counts=counts,
        non_imdb_episodes=frozenset(),
        absolute_episode=25,
    ) == (2, 13)


def test_place_episode_skips_non_imdb_episode():
    assert (
        place_episode(
            from_season=1,
            from_episode=1,
            per_season_counts=[10],
            non_imdb_episodes=frozenset({5}),
            absolute_episode=5,
        )
        is None
    )


def test_place_episode_shifts_after_skipped_episode():
    assert place_episode(
        from_season=1,
        from_episode=1,
        per_season_counts=[10],
        non_imdb_episodes=frozenset({5}),
        absolute_episode=6,
    ) == (1, 5)


def test_place_episode_beyond_known_coverage_returns_none():
    assert (
        place_episode(
            from_season=1,
            from_episode=1,
            per_season_counts=[12, 13],
            non_imdb_episodes=frozenset(),
            absolute_episode=26,
        )
        is None
    )


def test_place_episode_no_counts_returns_none():
    assert (
        place_episode(
            from_season=1,
            from_episode=1,
            per_season_counts=[],
            non_imdb_episodes=frozenset(),
            absolute_episode=1,
        )
        is None
    )


# ----- unplace_episode (inverse of place_episode) -----


def test_unplace_episode_single_season():
    assert (
        unplace_episode(
            from_season=1,
            from_episode=1,
            per_season_counts=[12],
            non_imdb_episodes=frozenset(),
            season=1,
            episode=5,
        )
        == 5
    )


def test_unplace_episode_crosses_season_boundary():
    counts = [12, 13]
    assert (
        unplace_episode(
            from_season=1,
            from_episode=1,
            per_season_counts=counts,
            non_imdb_episodes=frozenset(),
            season=2,
            episode=1,
        )
        == 13
    )


def test_unplace_episode_inverts_skip_offset():
    assert (
        unplace_episode(
            from_season=1,
            from_episode=1,
            per_season_counts=[10],
            non_imdb_episodes=frozenset({5}),
            season=1,
            episode=5,
        )
        == 6
    )


def test_unplace_episode_no_counts_returns_none():
    assert (
        unplace_episode(
            from_season=1,
            from_episode=1,
            per_season_counts=[],
            non_imdb_episodes=frozenset(),
            season=1,
            episode=1,
        )
        is None
    )


def test_unplace_episode_season_out_of_range_returns_none():
    assert (
        unplace_episode(
            from_season=1,
            from_episode=1,
            per_season_counts=[12, 13],
            non_imdb_episodes=frozenset(),
            season=5,
            episode=1,
        )
        is None
    )


def test_place_and_unplace_round_trip():
    counts = [12, 13]
    non_imdb_episodes = frozenset()
    for absolute_episode in range(1, 26):
        season, episode = place_episode(
            from_season=1,
            from_episode=1,
            per_season_counts=counts,
            non_imdb_episodes=non_imdb_episodes,
            absolute_episode=absolute_episode,
        )
        recovered = unplace_episode(
            from_season=1,
            from_episode=1,
            per_season_counts=counts,
            non_imdb_episodes=non_imdb_episodes,
            season=season,
            episode=episode,
        )
        assert recovered == absolute_episode
