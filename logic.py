import math
from enum import Enum

import esper

import create
from argparser import config
from gamecomponents import (
    PlayerInfo,
    Move,
    Score,
    Velocity,
    Rotate,
    RotateGun,
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
)
from mymath import segmentAndCircleIntersect, circlesCollide, square


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
                # print("Game ended because no one had bullets left")
                self.gameEndReason = self.GameEndReason.OUT_OF_AMMO
        if all(g.ammo == 0 for e, g in self.world.get_component(Gun)) and not self.noAmmoCountdown:
            # print("No bullets countdown started")
            self.noAmmoCountdown = True
            self.noAmmoTurnsLeft = self.ammoTimeout
        if self.turnsLeft <= 0:
            # print("Game ended because time run out")
            self.gameEndReason = self.GameEndReason.OUT_OF_TIME
        if len(self.world.get_component(Agent)) <= 1:
            # print("Game ended because there were no players to kill left")
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
                create.bullet(
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
