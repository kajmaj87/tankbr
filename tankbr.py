#!/usr/bin/env python
# -*- coding: utf-8 -*-

# RoadMap:
# - [ ] v0.x
#   - [ ] Multihostprocessing
# - [ ] v0.7
#   - [ ] Multiprocessing
# - [ ] v0.6
#   - [ ] Genetic mutations for NN Ai
#   - [ ] Simple NeuralNet AI
# - [X] v0.5
#   - [X] Tournaments
#   - [X] Seeding and game end checksums (replay functionality)
#   - [X] Optimization round
#   - [-] Code cleanup
# - [X] v0.4
#   - [X] Headless simulations
#   - [X] More different AIs
#   - [?] More rangefinders as input for AI (include constant input and random input also?)
# - [X] v0.3.1
#   - [X] Game End adds points depending on conditions (+tests)
# - [X] v0.3
#   - [X] Names
#   - [X] Zooming & Screen dragging
#   - [X] Scoring
#   - [X] Game End conditions
# Refactors & Ideas:
# - [ ] Separate Gun and change child to Mount (mount just moves around with parent)
# - [ ] Change all Move, Rotate etc to Commands
# Quality of life and bugs:
# - [ ] Player in different color
# - [ ] Countdown on start
# - [ ] Generating stating positions without overlap


import pygame
import esper
import math
import random
from PlayerRepository import PlayerRepository
from gui import InputEventProcessor, RenderProcessor, InputEventCollector
from ranking import processRanks
from mymath import square, circlesCollide, segmentAndCircleIntersect
from argparser import config
from gamecomponents import (
    PlayerInfo,
    Move,
    Score,
    Velocity,
    Rotate,
    RotateGun,
    MovementSteering,
    RotationSteering,
    FiringSteering,
    Perception,
    AI,
    Agent,
    Decision,
    PositionBox,
    Solid,
    Explosive,
    TTL,
    Gun,
    RangeFinder,
    FireGun,
    Child,
    Owner,
    InputEvents,
    Renderable,
)
from enum import Enum


class MovementProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def move(self, move, position, rotation):
        position.x += move.distance * math.cos(math.radians(rotation))
        position.y += move.distance * math.sin(math.radians(rotation))

    def process(self):
        for ent, (move, position) in self.world.get_components(Move, PositionBox):
            self.move(move, position, position.rotation)
            for child in self.world.try_component(ent, Child):
                for child_position in self.world.try_component(child.childId, PositionBox):
                    self.move(move, child_position, position.rotation)
            self.world.remove_component(ent, Move)


# Velocity processor genarates move and rotate components
class VelocityProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        for ent, velocity in self.world.get_component(Velocity):
            if velocity.speed != 0:
                self.world.add_component(ent, Move(velocity.speed))
            if velocity.angularSpeed != 0:
                self.world.add_component(ent, Rotate(velocity.angularSpeed))


class RotationProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        for ent, (rotate, position) in self.world.get_components(Rotate, PositionBox):
            position.rotation += rotate.angle
            for child in self.world.try_component(ent, Child):
                for child_position in self.world.try_component(child.childId, PositionBox):
                    child_position.rotation += rotate.angle
            self.world.remove_component(ent, Rotate)
        for ent, (rotateGun, gun) in self.world.get_components(RotateGun, Gun):
            self.world.component_for_entity(gun.gunEntity, PositionBox).rotation += rotateGun.angle
            self.world.remove_component(ent, RotateGun)


class GameEndProcessor(esper.Processor):
    class GameEndReason(Enum):
        MANUAL = 0
        OUT_OF_AMMO = 1
        OUT_OF_TIME = 2
        LAST_MAN_STANDING = 3

    def __init__(self, turnsLeft, ammoTimeout):
        super().__init__()
        self.turnsLeft = turnsLeft
        self.gameEndReason = None
        self.noAmmoCountdown = False
        self.ammoTimeout = ammoTimeout
        self.gameEndCallbacks = []

    def isGameRunning(self):
        return self.gameEndReason is None

    def callAtGameEnd(self, callback):
        self.gameEndCallbacks.append(callback)

    def process(self):
        self.turnsLeft -= 1
        if self.noAmmoCountdown:
            self.noAmmoTurnsLeft -= 1
            if self.noAmmoTurnsLeft <= 0:
                print("Game ended because no one had bullets left")
                self.gameEndReason = self.GameEndReason.OUT_OF_AMMO
        if all(g.ammo == 0 for e, g in self.world.get_component(Gun)) and not self.noAmmoCountdown:
            print("No bullets countdown started")
            self.noAmmoCountdown = True
            self.noAmmoTurnsLeft = self.ammoTimeout
        if self.turnsLeft <= 0:
            print("Game ended because time run out")
            self.gameEndReason = self.GameEndReason.OUT_OF_TIME
        if len(self.world.get_component(Agent)) <= 1:
            print("Game ended because there were no players to kill left")
            self.gameEndReason = self.GameEndReason.LAST_MAN_STANDING
        if not self.isGameRunning():
            for callback in self.gameEndCallbacks:
                callback()

class FiringGunProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        for ent, (gun, fireGun, position) in self.world.get_components(Gun, FireGun, PositionBox):
            if gun.isLoaded:
                createBullet(
                    world=self.world,
                    ownerId=ent,
                    position=self.world.component_for_entity(gun.gunEntity, PositionBox),
                )
                gun.isLoaded = False
            self.world.remove_component(ent, FireGun)


class GunReloadProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        for ent, gun in self.world.get_component(Gun):
            # start loading gun if its not already loaded and has ammo left
            if gun.ammo > 0 and not gun.isLoaded and gun.reloadTimeLeft == 0:
                self.world.component_for_entity(ent, Gun).ammo = gun.ammo - 1
                gun.reloadTimeLeft = config.game_gun_load_time
            elif not gun.isLoaded and gun.reloadTimeLeft > 0:
                gun.reloadTimeLeft -= 1
                if gun.reloadTimeLeft == 0:
                    gun.isLoaded = True


class RangeFindingProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):

        finders = self.world.get_components(PositionBox, RangeFinder)
        targets = self.world.get_components(PositionBox, Solid)
        for ent, (position, finder) in finders:
            fx = finder.maxRange * math.cos(math.radians(finder.angleOffset + position.rotation))
            fy = finder.maxRange * math.sin(math.radians(finder.angleOffset + position.rotation))
            endX, endY = position.x + fx, position.y + fy
            foundTargets = []
            for target, (targetPosition, solid) in targets:
                if position.x == targetPosition.x and position.y == targetPosition.y:
                    continue
                # we have direct hit and it is in range of finder and in front of the finder
                if segmentAndCircleIntersect(
                    position.x,
                    position.y,
                    endX,
                    endY,
                    finder.maxRange,
                    targetPosition.x,
                    targetPosition.y,
                    solid.collisionRadius,
                ):
                    foundTargets.append(targetPosition)
            finder.foundTargets = foundTargets
            if len(foundTargets) > 0:
                finder.closestTarget = min(
                    foundTargets,
                    key=lambda targetPosition: square(position.x - targetPosition.x)
                    + square(position.y - targetPosition.y),
                )
            else:
                finder.closestTarget = None


class CollisionProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def deleteWithChildren(self, entity):
        for info in self.world.try_component(entity, PlayerInfo):
            # keep the scoring information when player dies
            self.world.create_entity(info)
        for child in self.world.try_component(entity, Child):
            self.world.delete_entity(child.childId)
        self.world.delete_entity(entity)

    def revertMoveOnCollision(self, entity):
        for move in self.world.try_component(entity, Move):
            move.distance *= -1

    def process(self):
        solids = self.world.get_components(PositionBox, Solid)
        for entityA, (positionA, solidA) in solids:
            for entityB, (positionB, solidB) in solids:
                if (entityA != entityB) and circlesCollide(
                    positionA.x,
                    positionA.y,
                    solidA.collisionRadius,
                    positionB.x,
                    positionB.y,
                    solidB.collisionRadius,
                ):
                    if self.world.has_component(entityA, Explosive) or self.world.has_component(entityB, Explosive):
                        self.deleteWithChildren(entityA)
                        # Add points for someone that caused explosion
                        for owner in self.world.try_component(entityA, Owner):
                            # owner of the bullet may already be dead
                            if self.world.entity_exists(owner.ownerId):
                                self.world.create_entity(Score(owner.ownerId, config.game_frag_score))
                    else:
                        self.revertMoveOnCollision(entityA)


class AIProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        for ent, (ai, position, gun) in self.world.get_components(AI, PositionBox, Gun):
            perception = Perception()
            perception.target = self.world.component_for_entity(gun.gunEntity, RangeFinder).closestTarget
            decision, ai.memory = ai.decide(perception, ai.memory)
            if decision is not None:
                self.world.add_component(ent, decision)


class DecisionProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        for ent, (position, decisions) in self.world.get_components(PositionBox, Decision):
            for command in decisions.commands:
                self.world.add_component(ent, command)
            decisions.timeout -= 1
            if decisions.timeout <= 0:
                self.world.remove_component(ent, Decision)


class CleanupProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        for ent, ttl in self.world.get_component(TTL):
            if ttl.turns <= 0:
                self.world.delete_entity(ent)
            else:
                ttl.turns -= 1


class TotalScoreProcessor(esper.Processor):
    def __init__(self, gameEndProcessor, survivorScore, lastManStandingScore):
        super().__init__()
        self.gameEndProcessor = gameEndProcessor
        self.survivorScore = survivorScore
        self.lastManStandingScore = lastManStandingScore

    def process(self):

        for ent, score in self.world.get_component(Score):
            self.world.component_for_entity(score.ownerId, PlayerInfo).score += score.points
            self.world.delete_entity(ent)

        for ent, (agent, playerInfo) in self.world.get_components(Agent, PlayerInfo):
            playerInfo.score += self.survivorScore

        if not self.gameEndProcessor.isGameRunning():
            agentsLeft = self.world.get_components(Agent, PlayerInfo)
            for ent, (agent, totalScore) in agentsLeft:
                if len(agentsLeft) <= 1:
                    totalScore.score += self.lastManStandingScore




def createBullet(world, ownerId, position):
    bullet = world.create_entity()
    bulletImage = pygame.image.load("assets/bullet.png")
    world.add_component(bullet, Solid(collisionRadius=10))
    # Bullet needs to be offset not to kill own tank
    dx, dy = (
        config.game_bullet_position_offset * math.cos(math.radians(position.rotation)),
        config.game_bullet_position_offset * math.sin(math.radians(position.rotation)),
    )
    world.add_component(
        bullet,
        PositionBox(
            x=position.x + dx,
            y=position.y + dy,
            w=bulletImage.get_width(),
            h=bulletImage.get_height(),
            rotation=position.rotation,
        ),
    )
    world.add_component(bullet, Renderable(image=bulletImage))
    world.add_component(bullet, Velocity(speed=config.game_bullet_speed, angularSpeed=0))
    world.add_component(bullet, Owner(ownerId))
    world.add_component(bullet, Explosive())
    world.add_component(bullet, TTL(config.game_bullet_ttl))


def createTank(world, startx, starty, playerInfo, bodyRotation=0.0, gunRotation=0.0):
    bodyImage = pygame.image.load("assets/tankBase.png")
    gunImage = pygame.image.load("assets/tankTurret.png")
    bw, bh = bodyImage.get_width(), bodyImage.get_height()

    body = world.create_entity()
    world.add_component(body, Renderable(image=bodyImage, rotation=-90))
    world.add_component(
        body, Solid(collisionRadius=math.sqrt(bw * bw + bh * bh) / 2 * 0.7)
    )  # may overlap a little sometimes
    world.add_component(body, Agent())
    world.add_component(body, PositionBox(x=startx, y=starty, w=bw, h=bh))
    world.add_component(body, Velocity(speed=0, angularSpeed=0))
    world.add_component(body, Rotate(bodyRotation))

    # TODO Ordering of rendering should be processed separetely, now it is based on
    # declaration order. Idea is to use a PreRenderingProcessor that would add elements
    # to components based on their zlevel that would run once
    gun = world.create_entity()
    world.add_component(gun, Renderable(image=gunImage, rotation=-90))
    world.component_for_entity(gun, Renderable)
    # FIXME For now the gun and body must have the same center or they will diverge
    # during rotation/moving
    world.add_component(
        gun,
        PositionBox(x=startx, y=starty, w=gunImage.get_width(), h=gunImage.get_height()),
    )
    world.add_component(gun, Velocity(speed=0, angularSpeed=0))
    world.add_component(gun, Rotate(gunRotation))
    world.add_component(gun, RangeFinder(maxRange=config.game_laser_range, angleOffset=0))
    world.add_component(body, Gun(gun, ammo=config.game_ammo))

    if playerInfo.ai is None:
        world.add_component(
            body,
            MovementSteering(moveForwardKey=pygame.K_w, moveBackwardsKey=pygame.K_s),
        )
        world.add_component(body, RotationSteering(rotateLeftKey=pygame.K_a, rotateRightKey=pygame.K_d))
        world.add_component(body, FiringSteering(fireGunKey=pygame.K_SPACE))
        world.add_component(gun, RotationSteering(rotateLeftKey=pygame.K_j, rotateRightKey=pygame.K_l))
        world.add_component(body, playerInfo)
    else:
        world.add_component(body, playerInfo)
        world.add_component(body, AI(playerInfo.ai))

    world.add_component(body, Child(gun))


def printScoresAndRankings(players):
    formatHeaders = "{:>25} | {:>3} | {:>6} | {:>5} | {:>4} | {:>4} | {:>5} |"
    formatScores = "{:>25} | {:>3} | {:>6} | {:>5.1f} | {:>4.1f} | {:>4.1f} | {:>5.2f} |"
    print(formatHeaders.format("Name", "#", "#Games", "Score", "Rank", "Mu", "Sigma"))
    for place, p in enumerate(sorted(players, key=lambda x: 50 if x.rank is None else -x.rank)):
        rank = -50 if p.rank is None else p.rank
        mu = -50 if p.mu is None else p.mu
        sigma = -50 if p.sigma is None else p.sigma
        print(formatScores.format(p.name, place, p.totalGames, p.score, rank, mu, sigma))


def initWorld():
    world = esper.World()
    events = world.create_entity()
    world.add_component(events, InputEvents())
    return world, events


def createTanks(world, players):
    for p in players:
        if p.ai is None:
            createTank(world=world, startx=0, starty=0, bodyRotation=0, gunRotation=0, playerInfo=p)
        else:
            createTank(
                world=world,
                startx=random.randint(-config.game_spawn_range, config.game_spawn_range),
                starty=random.randint(-config.game_spawn_range, config.game_spawn_range),
                bodyRotation=random.randint(0, 359),
                gunRotation=random.randint(0, 359),
                playerInfo=p,
            )


def prepareProcessors(world, events, drawUI=True):
    gameEndProcessor = GameEndProcessor(turnsLeft=config.game_max_match_turns, ammoTimeout=config.game_bullet_ttl)
    world.add_processor(AIProcessor())
    world.add_processor(DecisionProcessor())
    world.add_processor(gameEndProcessor)
    world.add_processor(CollisionProcessor())
    world.add_processor(
        TotalScoreProcessor(
            gameEndProcessor=gameEndProcessor,
            survivorScore=config.game_survived_score / config.game_max_match_turns,
            lastManStandingScore=config.game_last_man_score,
        )
    )
    world.add_processor(MovementProcessor())
    world.add_processor(RotationProcessor())
    world.add_processor(RangeFindingProcessor())
    world.add_processor(VelocityProcessor())
    world.add_processor(FiringGunProcessor())
    world.add_processor(CleanupProcessor())
    world.add_processor(GunReloadProcessor())
    if drawUI:
        world.add_processor(RenderProcessor())
        world.add_processor(InputEventCollector(events))
        world.add_processor(InputEventProcessor(gameEndProcessor))
    return gameEndProcessor


def simulateGame(players):
    world, events = initWorld()
    createTanks(world, players)
    gameEndProcessor = prepareProcessors(world, events, drawUI=config.gui_draw)

    while gameEndProcessor.isGameRunning():
        # A single call to world.process() will update all Processors:
        world.process()
    # rankedPlayers = processRanks([p[1] for p in world.get_component(PlayerInfo)])
    rankedPlayers = processRanks(players)
    for p in rankedPlayers:
        p.totalGames += 1
    return rankedPlayers


def run():
    if config.random_seed is not None and config.random_seed != "disabled":
        random.seed(config.random_seed)

    playerRepository = PlayerRepository()
    players = playerRepository.generatePlayers(number=config.players, includeHumanPlayer=config.include_human_player)
    playerRepository.setPlayers(players)
    randomize = False
    for i in range(config.rounds):
        players = playerRepository.fetchPlayers()
        for j in range(config.players // config.match_size):
            if randomize:
                nextMatchPlayers = random.sample(players, config.match_size)
            else:
                nextMatchPlayers = players[j * config.match_size : (j + 1) * config.match_size]
            print("Starting match from round {} for group {}".format(i, j))

            simulateGame(nextMatchPlayers)
            for p in players:
                p.score = 0
        print("Rankings after {} round:".format(i))
        printScoresAndRankings(players)

    printScoresAndRankings(players)


if __name__ == "__main__":
    run()
    pygame.quit()