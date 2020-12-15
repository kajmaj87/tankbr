import math

from gamecomponents import PlayerInfo
from ai import monkeyAI, dummyAI, dummyRotatorAI, rotatorAI, fastAndSlowRotatorAI

import random

from networks import neuralAI


class PlayerRepository:
    def __init__(self):
        self.players = []
        self.generatedPlayers = 0

    def generateHumanPlayer(self):
        return [PlayerInfo(name="<<Player>>")]

    def genarateAIPlayers(self):
        nonNNAis = {
            "monkey": monkeyAI,
            "dummy": dummyAI,
            "dummyRotator": dummyRotatorAI,
            "rotator": rotatorAI,
            "fastRotator": fastAndSlowRotatorAI,
        }
        return [PlayerInfo(name="Tank-{}".format(aiName), ai=aiBrain) for aiName, aiBrain in nonNNAis.items()]

    def generateRandomNNAIPlayers(self, number):
        uptoNumber = self.generatedPlayers + number
        nnAis = {i: neuralAI(i) for i in range(self.generatedPlayers, uptoNumber)}
        self.generatedPlayers = uptoNumber
        return [
            PlayerInfo(name="Tank-0:{}".format(aiName), ai=aiBrain, neural_net=neural_net)
            for aiName, (aiBrain, neural_net) in nnAis.items()
        ]

    def generateNNAIPlayer(self, neural_net_model):
        self.generatedPlayers += 1
        aiBrain, neural_net = neuralAI(neural_net_model=neural_net_model)
        return PlayerInfo(
            name="Tank-{}:{}".format(neural_net.generation, self.generatedPlayers),
            ai=aiBrain,
            neural_net=neural_net_model,
        )

    def generatePlayers(self, number, includeAIs=True, includeHumanPlayer=False):
        result = []
        if includeHumanPlayer:
            result = result + self.generateHumanPlayer()
        if includeAIs:
            result = result + self.genarateAIPlayers()
        self.generatedPlayers += len(result)
        if len(result) < number:
            result = result + self.generateRandomNNAIPlayers(number - len(result))
        return result

    def setPlayers(self, players):
        self.players = players

    def removeWorstPlayers(self, minSigma, quantile=0.1):
        possiblePlayersToRemove = math.floor(len(self.players) * quantile)
        if possiblePlayersToRemove > 0:
            eligiblePlayers = self.sortPlayers(self.players)[-possiblePlayersToRemove:]
        else:
            return 0
        playersToRemove = self.sortPlayers([p for p in eligiblePlayers if p.sigma is not None and p.sigma < minSigma])
        self.players = [p for p in self.players if p not in playersToRemove]
        return playersToRemove

    def fetchPlayers(self, sort=False, filter=lambda x: True):
        if sort:
            return [p for p in self.sortPlayers(self.players) if filter(p)]
        else:
            return [p for p in self.players if filter(p)]

    def sortPlayers(self, players):
        return sorted(players, key=lambda p: 50 if p.rank is None else -p.rank)
