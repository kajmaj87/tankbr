from tankbr import RangeFindingProcessor, RangeFinder, PositionBox, Solid
import esper
from hypothesis import given
import hypothesis.strategies as st


# We check for translation invariant here also
@given(
    xt=st.floats(max_value=1000, min_value=-1000),
    yt=st.floats(max_value=1000, min_value=-1000),
)
def test_shouldFindTargetOnRight(xt, yt):
    world = esper.World()
    finderEntity = world.create_entity()
    target = world.create_entity()
    finder = RangeFinder(maxRange=100, angleOffset=0)
    world.add_component(finderEntity, finder)
    world.add_component(finderEntity, PositionBox(x=xt, y=yt))
    world.add_component(target, Solid(collisionRadius=10))
    targetPosition = PositionBox(x=xt + 50, y=yt)
    world.add_component(target, targetPosition)
    world.add_processor(RangeFindingProcessor())
    world.process()

    assert finder.closestTarget == targetPosition
    assert finder.foundTargets == [targetPosition]
