from tankbr import GameEndProcessor, Agent, Gun
import esper


def createAgent(world, ammo=1):
    agent = world.create_entity()
    world.add_component(agent, Agent())
    world.add_component(agent, Gun(gunEntity=agent, ammo=ammo))
    return agent


def test_shouldEndGameWhenTimeIsOut():
    world = esper.World()
    createAgent(world)
    createAgent(world)
    gameEndProcessor = GameEndProcessor(turnsLeft=2, ammoTimeout=1)
    world.add_processor(gameEndProcessor)
    world.process()

    assert gameEndProcessor.isGameRunning()

    world.process()

    assert not gameEndProcessor.isGameRunning()
    assert gameEndProcessor.gameEndReason == GameEndProcessor.GameEndReason.OUT_OF_TIME


def test_shouldEndGameWhenOnlyOneAgentLeft():
    world = esper.World()
    createAgent(world)
    agentToKill = createAgent(world)
    gameEndProcessor = GameEndProcessor(turnsLeft=5, ammoTimeout=1)
    world.add_processor(gameEndProcessor)
    world.process()

    assert gameEndProcessor.isGameRunning()

    world.delete_entity(agentToKill)

    world.process()

    assert not gameEndProcessor.isGameRunning()
    assert gameEndProcessor.gameEndReason == GameEndProcessor.GameEndReason.LAST_MAN_STANDING


def test_shouldEndGameAfterSomeTimeWhenNoAmmoLeft():
    world = esper.World()
    createAgent(world=world, ammo=0)
    createAgent(world=world, ammo=0)
    gameEndProcessor = GameEndProcessor(turnsLeft=5, ammoTimeout=1)
    world.add_processor(gameEndProcessor)
    world.process()

    assert gameEndProcessor.isGameRunning()

    world.process()

    assert not gameEndProcessor.isGameRunning()
    assert gameEndProcessor.gameEndReason == GameEndProcessor.GameEndReason.OUT_OF_AMMO
