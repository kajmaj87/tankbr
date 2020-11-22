from gamecomponents import Decision, FireGun, RotateGun, Memory, Move, Rotate
import random


def rotatorAI(perception, memory):
    if perception.target is not None:
        return Decision(commands=[FireGun()]), None
    else:
        return Decision(commands=[RotateGun(3)]), None


def fastAndSlowRotatorAI(perception, memory):
    FAST_ROTATE_SPEED = 3
    SLOW_ROTATE_SPEED = 1
    if memory is None:
        memory = Memory()
        memory.rotateFast = True
        # one full circle
        memory.timeToChange = 360 / FAST_ROTATE_SPEED
    else:
        memory.timeToChange -= 1

    if memory.timeToChange == 0 and memory.rotateFast:
        memory.rotateFast = False
        memory.timeToChange = 360 / FAST_ROTATE_SPEED
    elif memory.timeToChange == 0 and not memory.rotateFast:
        memory.rotateFast = True
        memory.timeToChange = 360 / SLOW_ROTATE_SPEED

    if perception.target is not None:
        return Decision(commands=[FireGun()]), None
    else:
        if memory.rotateFast:
            return Decision(commands=[RotateGun(FAST_ROTATE_SPEED)]), memory
        else:
            return Decision(commands=[RotateGun(-SLOW_ROTATE_SPEED)]), memory


def monkeyAI(perception, memory):
    if memory is not None and memory.ttl > 0:
        memory.ttl -= 1
        # repeat last decision until its outdated
        return memory.lastDecision, memory
    else:
        memory = Memory()
    if random.random() > 0.9:
        memory.ttl = 30
        memory.lastDecision = Decision(
            commands=[
                Move(random.randint(-2, 3)),
                Rotate(random.randint(-3, 3)),
            ]
        )
        return memory.lastDecision, memory
    # search for targets
    else:
        if perception.target is not None:
            memory.ttl = 10
            memory.lastDecision = Decision(commands=[FireGun()])
            return memory.lastDecision, memory
        else:
            return Decision(commands=[RotateGun(3)]), None
