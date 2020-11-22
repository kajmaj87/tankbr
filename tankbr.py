#!/usr/bin/env python
# -*- coding: utf-8 -*-

# RoadMap:
# - [ ] v0.x
#   - [ ] Multihostprocessing
# - [ ] v0.7
#   - [ ] Multiprocessing
#   - [ ] Optimization round
# - [ ] v0.6
#   - [ ] Genetic mutations for NN Ai
#   - [ ] Simple NeuralNet AI
# - [ ] v0.5
#   - [ ] Tournaments
#   - [ ] Seeding and game end checksums (replay functionality)
# - [ ] v0.4
#   - [ ] Headless simulations
#   - [ ] More different AIs
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

import pygame
import esper
import math
import random
from gamecomponents import (
    Name,
    Move,
    Score,
    TotalScore,
    Velocity,
    Rotate,
    RotateGun,
    MovementSteering,
    RotationSteering,
    FiringSteering,
    AI,
    Agent,
    Decision,
    PositionBox,
    Solid,
    Explosive,
    Gun,
    RangeFinder,
    FireGun,
    Child,
    Owner,
    InputEvents,
    Renderable,
)
from enum import Enum


################################
#  Define some Processors:
################################
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

    def isGameRunning(self):
        return self.gameEndReason is None

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
        for ent, inputEvents in self.world.get_component(InputEvents):
            for event in inputEvents.events:
                if event.type == pygame.QUIT:
                    self.gameEndReason = self.GameEndReason.MANUAL
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.gameEndReason = self.GameEndReason.MANUAL


class InputEventProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def registerKeyActions(self, entity, key, actionKeyDown=None, actionKeyUp=None):
        for ent, inputEvents in self.world.get_component(InputEvents):
            for event in inputEvents.events:
                if event.type == pygame.KEYDOWN and event.key == key and actionKeyDown is not None:
                    actionKeyDown(entity)
                elif event.type == pygame.KEYUP and event.key == key and actionKeyUp is not None:
                    actionKeyUp(entity)

    def steerRotation(self, entity, rotationSteering):
        def setAngularSpeed(ent, speed):
            self.world.component_for_entity(ent, Velocity).angularSpeed = speed

        def reset(ent):
            setAngularSpeed(ent, 0)

        def left(ent):
            setAngularSpeed(ent, ROTATION_SPEED)

        def right(ent):
            setAngularSpeed(ent, -ROTATION_SPEED)

        self.registerKeyActions(entity, rotationSteering.rotateLeftKey, left, reset)
        self.registerKeyActions(entity, rotationSteering.rotateRightKey, right, reset)

    def steerMovement(self, entity, movementSteering):
        def setSpeed(ent, speed):
            self.world.component_for_entity(ent, Velocity).speed = speed

        def reset(ent):
            setSpeed(ent, 0)

        def forward(ent):
            setSpeed(ent, MOVEMENT_SPEED)

        def backwards(ent):
            setSpeed(ent, -MOVEMENT_SPEED)

        self.registerKeyActions(entity, movementSteering.moveForwardKey, forward, reset)
        self.registerKeyActions(entity, movementSteering.moveBackwardsKey, backwards, reset)

    def fireGun(self, entity, firingSteering):
        self.registerKeyActions(
            entity,
            firingSteering.fireGunKey,
            lambda ent: self.world.add_component(ent, FireGun()),
        )

    def doMouseActions(self):
        global OFFSET_X, OFFSET_Y
        # button events must go first so the screen does not jump when motion comes first
        for ent, inputEvents in self.world.get_component(InputEvents):
            for event in inputEvents.events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    leftMouseButtonPressed, _, _ = pygame.mouse.get_pressed(3)
                    if leftMouseButtonPressed:
                        # get_rel needs to be reset to avoid screen jumps when dragging
                        pygame.mouse.get_rel()
        for ent, inputEvents in self.world.get_component(InputEvents):
            for event in inputEvents.events:
                if event.type == pygame.MOUSEWHEEL:
                    if event.y > 0:
                        increaseZoom()
                    if event.y < 0:
                        decreaseZoom()
                if event.type == pygame.MOUSEMOTION:
                    leftMouseButtonPressed, _, _ = pygame.mouse.get_pressed(3)
                    if leftMouseButtonPressed:
                        x, y = pygame.mouse.get_rel()
                        OFFSET_X += x
                        OFFSET_Y += y

    def process(self):
        for ent, (_, movementSteering) in self.world.get_components(Velocity, MovementSteering):
            self.steerMovement(ent, movementSteering)
        for ent, (_, rotationSteering) in self.world.get_components(Velocity, RotationSteering):
            self.steerRotation(ent, rotationSteering)
        for ent, (_, firingSteering) in self.world.get_components(Gun, FiringSteering):
            self.fireGun(ent, firingSteering)
        self.doMouseActions()


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
                gun.reloadTimeLeft = GUN_LOADING_TIME
            elif not gun.isLoaded and gun.reloadTimeLeft > 0:
                gun.reloadTimeLeft -= 1
                if gun.reloadTimeLeft == 0:
                    gun.isLoaded = True


class RangeFindingProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        def dist_square(x1, y1, x2, y2):
            return math.pow(x1 - x2, 2) + math.pow(y1 - y2, 2)

        for ent, (position, finder) in self.world.get_components(PositionBox, RangeFinder):
            targets = []
            for target, (targetPosition, solid) in self.world.get_components(PositionBox, Solid):
                if position.x == targetPosition.x and position.y == targetPosition.y:
                    continue
                # nice calculation at:
                #   https://mathworld.wolfram.com/Circle-LineIntersection.html#:~:text=In%20geometry%2C%20a%20line%20meeting,429).
                x1, y1 = position.x, position.y
                x2 = x1 + finder.maxRange * math.cos(math.radians(finder.angleOffset + position.rotation))
                y2 = y1 + finder.maxRange * math.sin(math.radians(finder.angleOffset + position.rotation))
                maxRangeSqr = math.pow(finder.maxRange, 2)
                maxRangeWithCollision = finder.maxRange + solid.collisionRadius
                # range between and of laser and target is not bigger than max laser range
                targetInFront = dist_square(targetPosition.x, targetPosition.y, x2, y2) < maxRangeSqr
                targetInRange = (
                    math.sqrt(dist_square(position.x, position.y, targetPosition.x, targetPosition.y))
                    < maxRangeWithCollision
                )
                x1, y1, x2, y2 = (
                    x1 - targetPosition.x,
                    y1 - targetPosition.y,
                    x2 - targetPosition.x,
                    y2 - targetPosition.y,
                )
                dr_square = dist_square(x1, y1, x2, y2)
                D = x1 * y2 - x2 * y1
                delta = math.pow(solid.collisionRadius, 2) * dr_square - math.pow(D, 2)
                # we have direct hit and it is in range of finder and in front of the finder
                if delta > 0 and targetInFront and targetInRange:
                    targets.append(targetPosition)
            finder.foundTargets = targets
            if len(targets) > 0:
                finder.closestTarget = min(
                    targets,
                    key=lambda targetPosition: math.pow(position.x - targetPosition.x, 2)
                    + math.pow(position.y - targetPosition.y, 2),
                )
            else:
                finder.closestTarget = None


class CollisionProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def circlesCollide(self, x0, y0, r0, x1, y1, r1):
        pointDifference = math.pow(x0 - x1, 2) + math.pow(y0 - y1, 2)
        return math.pow(r0 - r1, 2) <= pointDifference and pointDifference <= math.pow(r0 + r1, 2)

    def deleteWithChildren(self, entity):
        for child in self.world.try_component(entity, Child):
            self.world.delete_entity(child.childId)
        self.world.delete_entity(entity)

    def revertMoveOnCollision(self, entity):
        for move in self.world.try_component(entity, Move):
            move.distance *= -1

    def process(self):
        for entityA, (positionA, solidA) in self.world.get_components(PositionBox, Solid):
            for entityB, (positionB, solidB) in self.world.get_components(PositionBox, Solid):
                if (entityA != entityB) and self.circlesCollide(
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
                                self.world.create_entity(Score(owner.ownerId, FRAG_SCORE))
                    else:
                        self.revertMoveOnCollision(entityA)


class AIProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        for ent, (ai, position, gun) in self.world.get_components(AI, PositionBox, Gun):
            if not self.world.has_component(ent, Decision):
                # move around
                if random.random() > 0.9:
                    self.world.add_component(
                        ent,
                        Decision(
                            commands=[
                                Move(random.randint(-2, 3)),
                                Rotate(random.randint(-3, 3)),
                            ],
                            timeout=30,
                        ),
                    )
                # search for targets
                else:
                    target = self.world.component_for_entity(gun.gunEntity, RangeFinder).closestTarget
                    if target is not None:
                        self.world.add_component(ent, Decision(commands=[FireGun()], timeout=10))
                    else:
                        self.world.add_component(ent, Decision(commands=[RotateGun(3)], timeout=1))


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


class InputEventCollector(esper.Processor):
    def __init__(self, eventsEntity):
        super().__init__()
        self.eventsEntity = eventsEntity

    def process(self):
        # FIXME Can be used to decouple further processors from
        # pygame by mapping those events to other objects
        self.world.component_for_entity(self.eventsEntity, InputEvents).events = pygame.event.get()


class TotalScoreProcessor(esper.Processor):
    def __init__(self, gameEndProcessor, survivorScore, lastManStandingScore):
        super().__init__()
        self.gameEndProcessor = gameEndProcessor
        self.survivorScore = survivorScore
        self.lastManStandingScore = lastManStandingScore

    def process(self):
        for ent, score in self.world.get_component(Score):
            self.world.component_for_entity(score.ownerId, TotalScore).points += score.points
            self.world.delete_entity(ent)
        if not self.gameEndProcessor.isGameRunning():
            agentsLeft = self.world.get_components(Agent, TotalScore)
            for ent, (agent, totalScore) in agentsLeft:
                totalScore.points += self.survivorScore
                if len(agentsLeft) <= 1:
                    totalScore.points += self.lastManStandingScore


class RenderProcessor(esper.Processor):

    FRAME_AVG_SIZE = 100

    def __init__(self, window, clock, clear_color=(0, 0, 0)):
        super().__init__()
        self.window = window
        self.clock = clock
        self.clear_color = clear_color
        self.currentFrame = 0
        self.lastFrameTimes = [0] * self.FRAME_AVG_SIZE

    def blitRotate(self, surf, image, pos, originPos, angle, imageRotation):
        # calcaulate the axis aligned bounding box of the rotated image
        w, h = image.get_size()
        box = [pygame.math.Vector2(p) for p in [(0, 0), (w, 0), (w, h), (0, h)]]
        box_rotate = [p.rotate(angle) for p in box]
        min_x, max_y = min(box_rotate, key=lambda p: p[0])[0], max(box_rotate, key=lambda p: p[1])[1]
        # sin_a, cos_a = math.sin(math.radians(angle)), math.cos(math.radians(angle))
        # min_x, min_y = min([0, sin_a * h, cos_a * w, sin_a * h + cos_a * w]), max(
        #     [0, sin_a * w, -cos_a * h, sin_a * w - cos_a * h]
        # )
        # calculate the translation of the pivot
        pivot = pygame.math.Vector2(originPos[0], originPos[1])
        pivot_rotate = pivot.rotate(angle)
        pivot_move = pivot_rotate - pivot
        # calculate the upper left origin of the rotated image
        x, y = pos[0] - originPos[0] + min_x - pivot_move[0], pos[1] - originPos[1] + max_y - pivot_move[1]

        # get a rotated image
        rotated_image = pygame.transform.rotozoom(image, angle + imageRotation, ZOOM)
        # rotate and blit the image
        surf.blit(rotated_image, self.transformCoordinates(x, y))

    def addRawTime(self, time):
        self.lastFrameTimes[self.currentFrame % self.FRAME_AVG_SIZE] = time

    def getRawTimeAvg(self):
        return sum(self.lastFrameTimes) / self.FRAME_AVG_SIZE

    def transformCoordinates(self, x, y):
        return ZOOM * x + RESOLUTION[0] / 2 + OFFSET_X, -ZOOM * y + RESOLUTION[1] / 2 + OFFSET_Y

    def drawTank(self):
        for ent, (rend, position) in self.world.get_components(Renderable, PositionBox):
            pivot = pygame.math.Vector2(position.pivotx, position.pivoty)
            originalPosition = pygame.math.Vector2(position.x, position.y)
            self.blitRotate(self.window, rend.image, originalPosition, pivot, position.rotation, rend.rotation)

    def drawLaser(self):
        for ent, (gun, position) in self.world.get_components(Gun, PositionBox):
            gunPosition = self.world.component_for_entity(gun.gunEntity, PositionBox)
            sin_a, cos_a = math.sin(math.radians(gunPosition.rotation)), math.cos(math.radians(gunPosition.rotation))
            x, y = self.transformCoordinates(gunPosition.x, gunPosition.y)
            lx, ly = self.transformCoordinates(gunPosition.x + LASER_RANGE * cos_a, gunPosition.y + LASER_RANGE * sin_a)
            pygame.draw.line(self.window, pygame.Color(255, 0, 0), (x, y), (lx, ly), 2)

    def drawNamesAndScores(self):
        font = pygame.font.Font(None, 16)
        for ent, (name, score, position) in self.world.get_components(Name, TotalScore, PositionBox):
            text = "{} +{}".format(name.name, score.points)
            label = font.render(
                text,
                True,
                pygame.Color("yellow"),
            )
            tx, ty = font.size(text)
            x, y = self.transformCoordinates(position.x, position.y + 0.7 * position.h)
            self.window.blit(label, (x - tx / 2, y - ty))

    def drawUI(self):
        font = pygame.font.Font(None, 20)
        fps = font.render(
            "FPS: {} (update took: {:.1f} ms (avg from {} FPS))".format(
                int(self.clock.get_fps()), self.getRawTimeAvg(), self.FRAME_AVG_SIZE
            ),
            True,
            pygame.Color("white"),
        )
        self.window.blit(fps, (10, 10))

    def process(self):
        # Clear the window:
        self.window.fill(self.clear_color)

        self.drawTank()
        self.drawLaser()
        self.drawNamesAndScores()
        self.drawUI()

        # Flip the framebuffers
        pygame.display.flip()
        self.addRawTime(self.clock.get_rawtime())
        self.currentFrame += 1
        self.clock.tick(FPS)


FPS = 30
RESOLUTION = 720, 480
# To decouple screen from game coordinates
ZOOM = 1
ZOOM_CHANGE_FACTOR = 0.1

FRAG_SCORE = 2
LAST_MAN_STANDING_SCORE = 10
SURVIVED_SCORE = 10

OFFSET_X = 0
OFFSET_Y = 0

RANDOM_TANKS = 1
SPAWN_RANGE = 300
ENEMYS_HAVE_AI = True

MOVEMENT_SPEED = 6
ROTATION_SPEED = 3

GUN_LOADING_TIME = 30
AMMO = 3
BULLET_SPEED = 20
BULLET_POSITION_OFFSET = 36

LASER_RANGE = 1600

MAX_SIMULATION_TURNS = 30 * 60
NO_AMMO_GAME_TIMEOUT = 30 * 3


def increaseZoom():
    global ZOOM
    ZOOM *= 1 + ZOOM_CHANGE_FACTOR


def decreaseZoom():
    global ZOOM
    ZOOM *= 1 - ZOOM_CHANGE_FACTOR


def createBullet(world, ownerId, position):
    bullet = world.create_entity()
    bulletImage = pygame.image.load("assets/bullet.png")
    world.add_component(bullet, Solid(collisionRadius=10))
    # Bullet needs to be offset not to kill own tank
    dx, dy = (
        BULLET_POSITION_OFFSET * math.cos(math.radians(position.rotation)),
        BULLET_POSITION_OFFSET * math.sin(math.radians(position.rotation)),
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
    world.add_component(bullet, Velocity(speed=BULLET_SPEED, angularSpeed=0))
    world.add_component(bullet, Owner(ownerId))
    world.add_component(bullet, Explosive())


def createTank(world, startx, starty, name, bodyRotation=0.0, gunRotation=0.0, isPlayer=False):
    bodyImage = pygame.image.load("assets/tankBase.png")
    gunImage = pygame.image.load("assets/tankTurret.png")
    bw, bh = bodyImage.get_width(), bodyImage.get_height()

    body = world.create_entity()
    world.add_component(body, Renderable(image=bodyImage, rotation=-90))
    world.add_component(
        body, Solid(collisionRadius=math.sqrt(bw * bw + bh * bh) / 2 * 0.7)
    )  # may overlap a little sometimes
    world.add_component(body, Name(name))
    world.add_component(body, Agent())
    world.add_component(body, TotalScore(points=0))
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
    world.add_component(gun, RangeFinder(maxRange=300, angleOffset=0))
    world.add_component(body, Gun(gun, ammo=AMMO))

    if isPlayer:
        world.add_component(
            body,
            MovementSteering(moveForwardKey=pygame.K_w, moveBackwardsKey=pygame.K_s),
        )
        world.add_component(body, RotationSteering(rotateLeftKey=pygame.K_a, rotateRightKey=pygame.K_d))
        world.add_component(body, FiringSteering(fireGunKey=pygame.K_SPACE))
        world.add_component(gun, RotationSteering(rotateLeftKey=pygame.K_j, rotateRightKey=pygame.K_l))
    elif ENEMYS_HAVE_AI:
        world.add_component(body, AI())

    world.add_component(body, Child(gun))


def run():
    # Initialize Pygame stuff
    pygame.init()
    window = pygame.display.set_mode(RESOLUTION)
    pygame.display.set_caption("Tankbr")
    clock = pygame.time.Clock()
    pygame.key.set_repeat(1, 1)

    # Initialize Esper world, and create a "player" Entity with a few Components.
    world = esper.World()
    events = world.create_entity()
    world.add_component(events, InputEvents())

    createTank(world=world, startx=0, starty=0, bodyRotation=0, gunRotation=0, isPlayer=True, name="<<Player>>")

    for i in range(RANDOM_TANKS):
        createTank(
            world=world,
            startx=random.randint(-SPAWN_RANGE, SPAWN_RANGE),
            starty=random.randint(-SPAWN_RANGE, SPAWN_RANGE),
            bodyRotation=random.randint(0, 359),
            gunRotation=random.randint(0, 359),
            name="Tank-{}".format(i),
        )

    # createTank(world=world, startx=100, starty=-100, bodyRotation=0, gunRotation=90)
    # createTank(world=world, startx=-100, starty=200, bodyRotation=0, gunRotation=0)

    gameEndProcessor = GameEndProcessor(turnsLeft=MAX_SIMULATION_TURNS, ammoTimeout=NO_AMMO_GAME_TIMEOUT)
    world.add_processor(InputEventCollector(events))
    world.add_processor(InputEventProcessor())
    world.add_processor(AIProcessor())
    world.add_processor(DecisionProcessor())
    world.add_processor(gameEndProcessor)
    world.add_processor(CollisionProcessor())
    world.add_processor(
        TotalScoreProcessor(
            gameEndProcessor=gameEndProcessor,
            survivorScore=SURVIVED_SCORE,
            lastManStandingScore=LAST_MAN_STANDING_SCORE,
        )
    )
    world.add_processor(MovementProcessor())
    world.add_processor(RotationProcessor())
    world.add_processor(RangeFindingProcessor())
    world.add_processor(VelocityProcessor())
    world.add_processor(FiringGunProcessor())
    world.add_processor(GunReloadProcessor())
    world.add_processor(RenderProcessor(window=window, clock=clock))

    while gameEndProcessor.isGameRunning():
        # A single call to world.process() will update all Processors:
        world.process()


if __name__ == "__main__":
    run()
    pygame.quit()
