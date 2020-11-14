from tankbr import RangeFindingProcessor, RangeFinder, PositionBox, Solid
import esper
import math
from hypothesis import given
import hypothesis.strategies as st


# We check for translation invariant here also
@given(xt=st.floats(max_value=1000, min_value=-1000), yt=st.floats(max_value=1000, min_value=-1000))
def test_shouldFindTargetOnRight(xt, yt):
    world = esper.World()
    finderEntity = world.create_entity()
    target = world.create_entity()
    finder = RangeFinder(maxRange=100, angleOffset=0)
    world.add_component(finderEntity, finder)
    world.add_component(finderEntity, PositionBox(x=xt, y=yt))
    world.add_component(target, Solid(collisionRadius=1))
    targetPosition = PositionBox(x=xt + 50, y=yt)
    world.add_component(target, targetPosition)
    world.add_processor(RangeFindingProcessor())
    world.process()

    assert finder.closestTarget == targetPosition
    assert finder.foundTargets == [targetPosition]


@given(angle=st.floats(min_value=0, max_value=360))
def test_shouldFindTargetOnEachAngle(angle):
    world = esper.World()
    finderEntity = world.create_entity()
    target = world.create_entity()
    finder = RangeFinder(maxRange=100, angleOffset=0)
    world.add_component(finderEntity, finder)
    world.add_component(finderEntity, PositionBox(rotation=angle))
    world.add_component(target, Solid(collisionRadius=2))
    targetPosition = PositionBox(x=100 * math.cos(math.radians(angle)), y=100 * math.sin(math.radians(angle)))
    world.add_component(target, targetPosition)
    world.add_processor(RangeFindingProcessor())
    world.process()

    assert finder.closestTarget == targetPosition
    assert finder.foundTargets == [targetPosition]


def test_shouldNotFindTargetBackwards():
    world = esper.World()
    finderEntity = world.create_entity()
    target = world.create_entity()
    finder = RangeFinder(maxRange=100, angleOffset=0)
    world.add_component(finderEntity, finder)
    world.add_component(finderEntity, PositionBox(rotation=0))
    world.add_component(target, Solid(collisionRadius=1))
    targetPosition = PositionBox(x=-10, y=0)
    world.add_component(target, targetPosition)
    world.add_processor(RangeFindingProcessor())
    world.process()

    assert finder.closestTarget is None
    assert finder.foundTargets == []


def test_shouldNotFindTargetOutOfRange():
    world = esper.World()
    finderEntity = world.create_entity()
    target = world.create_entity()
    finder = RangeFinder(maxRange=100, angleOffset=0)
    world.add_component(finderEntity, finder)
    world.add_component(finderEntity, PositionBox(rotation=0))
    world.add_component(target, Solid(collisionRadius=1))
    targetPosition = PositionBox(x=102, y=0)
    world.add_component(target, targetPosition)
    world.add_processor(RangeFindingProcessor())
    world.process()

    assert finder.closestTarget is None
    assert finder.foundTargets == []
