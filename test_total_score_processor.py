from tankbr import TotalScoreProcessor, Score, TotalScore, Agent, GameEndProcessor
from hypothesis import given
import hypothesis.strategies as st
import esper

SURVIVOR_SCORE = 2
LAST_MAN_STANDING_SCORE = 3


def createAgent(world, totalScore=0):
    agent = world.create_entity()
    world.add_component(agent, Agent())
    world.add_component(agent, TotalScore(points=totalScore))
    return agent


@given(startingScore=st.integers(), pointsGained=st.integers())
def test_shouldAddScore(startingScore, pointsGained):
    world = esper.World()
    agent = createAgent(world, startingScore)
    world.add_processor(
        TotalScoreProcessor(GameEndProcessor(turnsLeft=10, ammoTimeout=10), SURVIVOR_SCORE, LAST_MAN_STANDING_SCORE)
    )
    world.create_entity(Score(agent, pointsGained))
    world.process()

    assert world.component_for_entity(agent, TotalScore).points == startingScore + pointsGained


def test_shouldAddScoreAfterGameEndIfMoreThenOnePlayer():
    world = esper.World()
    agent1 = createAgent(world)
    agent2 = createAgent(world)
    gameEndProcessor = GameEndProcessor(turnsLeft=1, ammoTimeout=10)
    world.add_processor(gameEndProcessor)
    world.add_processor(TotalScoreProcessor(gameEndProcessor, SURVIVOR_SCORE, LAST_MAN_STANDING_SCORE))
    world.process()

    assert world.component_for_entity(agent1, TotalScore).points == SURVIVOR_SCORE
    assert world.component_for_entity(agent2, TotalScore).points == SURVIVOR_SCORE


def test_shouldAddScoreAfterGameEndIfTheOnlyVictor():
    world = esper.World()
    agent = createAgent(world)
    gameEndProcessor = GameEndProcessor(turnsLeft=10, ammoTimeout=10)
    world.add_processor(gameEndProcessor)
    world.add_processor(TotalScoreProcessor(gameEndProcessor, SURVIVOR_SCORE, LAST_MAN_STANDING_SCORE))
    world.process()

    assert world.component_for_entity(agent, TotalScore).points == SURVIVOR_SCORE + LAST_MAN_STANDING_SCORE
