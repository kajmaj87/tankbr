import sys
import random
from random import randint

from argparser import config
from gamecomponents import FireGun, Move, RotateGun, Rotate, Decision

from fann2 import libfann

def createModel(randomRange, seed):
    random.seed(seed)

    model = libfann.neural_net()

    model.create_standard_array([2,12,8,7])
    model.randomize_weights(-randomRange,randomRange)

    return model


ACTIVATION_THRESHOLD = 0.5
RANDOM_RANGE = 3


def neuralAI(seed):
    model = createModel(RANDOM_RANGE, seed)

    def decide(perception, memory):
        if perception.target is not None:
            found = 1
        else:
            found = 0
        result = model.run([random.random(), found])
        commands = []
        if result[0] > ACTIVATION_THRESHOLD:
            commands.append(FireGun())
        if result[1] > ACTIVATION_THRESHOLD or result[2] > ACTIVATION_THRESHOLD:
            if result[1] > result[2]:
                commands.append(Move(config.game_movement_speed))
            else:
                commands.append(Move(-config.game_movement_speed))
        if result[3] > ACTIVATION_THRESHOLD or result[4] > ACTIVATION_THRESHOLD:
            if result[3] > result[4]:
                commands.append(Rotate(config.game_rotation_speed))
            else:
                commands.append(Rotate(-config.game_rotation_speed))
        if result[5] > ACTIVATION_THRESHOLD or result[6] > ACTIVATION_THRESHOLD:
            if result[5] > result[6]:
                commands.append(RotateGun(config.game_rotation_speed))
            else:
                commands.append(RotateGun(-config.game_rotation_speed))
        return Decision(commands), None

    return decide
