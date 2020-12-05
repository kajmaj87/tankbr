import sys
import random
from random import randint

from tensorflow.keras import layers, initializers
from tensorflow.python.keras.models import Sequential
import keras

from argparser import config
from gamecomponents import FireGun, Move, RotateGun, Rotate, Decision

keras.backend.set_learning_phase(0)

def createModel(stddev, seed):
    random.seed(seed)

    model = Sequential()
    model.add(
        layers.Dense(12, input_dim=2, activation="relu",
                     kernel_initializer=initializers.RandomNormal(stddev=stddev, seed=randint(0, sys.maxsize - 1))))
    model.add(layers.Dense(8, activation="relu", kernel_initializer=initializers.RandomNormal(stddev=stddev,
                                                                                              seed=randint(0,
                                                                                                           sys.maxsize - 1))))
    model.add(layers.Dense(7, activation="sigmoid", kernel_initializer=initializers.RandomNormal(stddev=stddev,
                                                                                                 seed=randint(0,
                                                                                                              sys.maxsize - 1))))

    # print(model.summary())
    # print(model.get_weights())
    # print(model.predict([[1, 0], [1,1], [0,1], [0,0]]))
    return model


ACTIVATION_THRESHOLD = 0.5


def neuralAI(seed):
    model = createModel(3, seed)

    def decide(perception, memory):
        if perception.target is not None:
            found = 1
        else:
            found = 0
        result = model.predict([[random.random(), found]], batch_size=1)[0]
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
