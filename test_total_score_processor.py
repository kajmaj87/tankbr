from hypothesis import given
import hypothesis.strategies as st
import esper

from gamecomponents import Agent, PlayerInfo, Score
from logic import TotalScoreProcessor, GameEndProcessor

SURVIVOR_SCORE_PER_TURN = 0.02
LAST_MAN_STANDING_SCORE = 3


def createAgent(world, totalScore=0):
    agent = world.create_entity()
    world.add_component(agent, Agent())
    world.add_component(agent, PlayerInfo(name="test_agent", score=totalScore))
    return agent


@given(startingScore=st.integers(), pointsGained=st.integers())
def test_shouldAddScore(startingScore, pointsGained):
    world = esper.World()
    agent = createAgent(world, startingScore)
    world.add_processor(
        TotalScoreProcessor(
            GameEndProcessor(turnsLeft=10, ammoTimeout=10), SURVIVOR_SCORE_PER_TURN, LAST_MAN_STANDING_SCORE
        )
    )
    world.create_entity(Score(agent, pointsGained))
    world.process()

    assert world.component_for_entity(agent, PlayerInfo).score == startingScore + pointsGained + SURVIVOR_SCORE_PER_TURN


def test_shouldAddScoreAfterGameEndIfMoreThenOnePlayer():
    world = esper.World()
    agent1 = createAgent(world)
    agent2 = createAgent(world)
    gameEndProcessor = GameEndProcessor(turnsLeft=1, ammoTimeout=10)
    world.add_processor(gameEndProcessor)
    world.add_processor(TotalScoreProcessor(gameEndProcessor, SURVIVOR_SCORE_PER_TURN, LAST_MAN_STANDING_SCORE))
    world.process()

    assert world.component_for_entity(agent1, PlayerInfo).score == SURVIVOR_SCORE_PER_TURN
    assert world.component_for_entity(agent2, PlayerInfo).score == SURVIVOR_SCORE_PER_TURN


def test_shouldAddScoreAfterGameEndIfTheOnlyVictor():
    world = esper.World()
    agent = createAgent(world)
    gameEndProcessor = GameEndProcessor(turnsLeft=10, ammoTimeout=10)
    world.add_processor(gameEndProcessor)
    world.add_processor(TotalScoreProcessor(gameEndProcessor, SURVIVOR_SCORE_PER_TURN, LAST_MAN_STANDING_SCORE))
    world.process()

    assert world.component_for_entity(agent, PlayerInfo).score == SURVIVOR_SCORE_PER_TURN + LAST_MAN_STANDING_SCORE
