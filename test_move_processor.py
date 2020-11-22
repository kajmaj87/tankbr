from tankbr import MovementProcessor, Move, PositionBox
import esper
import math
from hypothesis import given
import hypothesis.strategies as st
import pytest

smallFloatStrategy = st.floats(min_value=-100, max_value=100)
angleStrategy = st.floats(min_value=-720, max_value=720)


def setupWorld(x=0, y=0, r=0, d=0):
    world = esper.World()
    entityToMove = world.create_entity()
    world.add_component(entityToMove, Move(d))
    world.add_component(entityToMove, PositionBox(x=x, y=y, rotation=r))
    world.add_processor(MovementProcessor())
    world.process()
    return world, entityToMove


# We check for translation invariant here also
@given(xt=smallFloatStrategy, yt=smallFloatStrategy, rt=angleStrategy, dt=smallFloatStrategy)
def test_movingAlwaysChangesDistanceRegardlessOfRotationAndPosition(xt, yt, rt, dt):
    world, ent = setupWorld(xt, yt, rt, dt)
    for e, pos in world.get_component(PositionBox):
        d = math.pow(pos.x - xt, 2) + math.pow(pos.y - yt, 2)
        assert dt * dt == pytest.approx(d)


@given(xt=smallFloatStrategy, yt=smallFloatStrategy, rt=angleStrategy, dt=smallFloatStrategy)
def test_movingForwardAndBackGoesToStart(xt, yt, rt, dt):
    world, entityToMove = setupWorld(xt, yt, rt, dt)
    world.add_component(entityToMove, Move(-dt))
    world.process()
    for e, pos in world.get_component(PositionBox):
        d = math.pow(pos.x - xt, 2) + math.pow(pos.y - yt, 2)
        assert 0 == pytest.approx(d)


def test_movingInAngleZeroMovesRight():
    world, ent = setupWorld(r=0, d=1)
    for e, pos in world.get_component(PositionBox):
        assert (1, 0) == pytest.approx((pos.x, pos.y))


def test_movingBackInAngle90MovesDown():
    world, ent = setupWorld(r=90, d=-1)
    for e, pos in world.get_component(PositionBox):
        assert (0, -1) == pytest.approx((pos.x, pos.y))
