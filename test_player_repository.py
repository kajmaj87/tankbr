import pytest

from PlayerRepository import PlayerRepository
from gamecomponents import PlayerInfo

repo = None
p1, p2 = None, None


@pytest.fixture(autouse=True)
def initPlayers():
    global repo, p1, p2
    p1, p2 = PlayerInfo("1"), PlayerInfo("2")
    p1.sigma = 3
    p2.sigma = 5
    repo = PlayerRepository()
    repo.setPlayers([p1, p2])


def test_remove_worst_players_too_low_sigma():
    removed = repo.removeWorstPlayers(quantile=1, minSigma=2)

    assert len(removed) == 0
    assert len(repo.fetchPlayers()) == 2


def test_remove_worst_players_too_middle_sigma():
    removed = repo.removeWorstPlayers(quantile=1, minSigma=4)

    assert len(removed) == 1
    assert len(repo.fetchPlayers()) == 1


def test_remove_worst_players_too_big_sigma():
    removed = repo.removeWorstPlayers(quantile=1, minSigma=6)

    assert len(removed) == 2
    assert len(repo.fetchPlayers()) == 0


def test_remove_worst_players_too_big_sigma_but_limited_amount_should_remove_worst_player():
    p1.rank = 30
    p2.rank = 40
    removed = repo.removeWorstPlayers(quantile=0.5, minSigma=6)

    assert len(removed) == 1
    assert len(repo.fetchPlayers()) == 1
    assert repo.fetchPlayers() == [p2]
