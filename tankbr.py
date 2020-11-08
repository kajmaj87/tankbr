#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
import esper
import math
import random

##################################
#  Define some Components:
##################################
class Move:
    def __init__(self, distance=0.0):
        self.distance = distance

class Velocity:
    def __init__(self, speed=0.0, angularSpeed=0.0):
        self.speed = speed
        self.angularSpeed = angularSpeed

class Rotate:
    def __init__(self, angle=0.0):
        self.angle = angle

class MovementSteering:
    def __init__(self, moveForwardKey, moveBackwardsKey):
        self.moveForwardKey = moveForwardKey
        self.moveBackwardsKey = moveBackwardsKey

class RotationSteering:
    def __init__(self, rotateLeftKey, rotateRightKey):
        self.rotateLeftKey = rotateLeftKey
        self.rotateRightKey = rotateRightKey

class PositionBox:
    def __init__(self, x=0.0, y=0.0, w=0.0, h=0.0, rotation=0.0, pivotx=None, pivoty=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.rotation = rotation
        if pivotx is None:
            self.pivotx = w/2
        else:
            self.pivotx = pivotx
        if pivoty is None:
            self.pivoty = h/2
        else:
            self.pivoty = pivoty

    def getCenter(self):
        return (self.x - self.w)/2, (self.y - self.h)/2

class Solid:
    def __init__(self, collisionRadius):
        self.collisionRadius = collisionRadius

class Child:
    def __init__(self, childId):
        self.childId = childId

class KeyboardEvents:
    def __init__(self, events = None):
        self.events = events

class Renderable:
    def __init__(self, image):
        self.image = image
        self.w = image.get_width()
        self.h = image.get_height()


################################
#  Define some Processors:
################################
class MovementProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def move(self, move, position, rotation):
        position.x += move.distance * math.sin(math.radians(rotation))
        position.y += move.distance * math.cos(math.radians(rotation))

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
            self.world.add_component(ent,Move(velocity.speed))
            self.world.add_component(ent,Rotate(velocity.angularSpeed))

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
            
class GameEndProcessor(esper.Processor):
    def __init__(self):
        super().__init__()
        self.running = True

    def isGameRunning(self):
        return self.running

    def process(self):
        for ent, keyboardEvents in self.world.get_component(KeyboardEvents):
            for event in keyboardEvents.events:
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        self.running = False

class SteeringProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def steerRotation(self, entity, rotationSteering):
        for ent, keyboardEvents in self.world.get_component(KeyboardEvents):
            for event in keyboardEvents.events:
                if event.type == pygame.KEYDOWN:
                    if event.key == rotationSteering.rotateLeftKey:
                        self.world.component_for_entity(entity, Velocity).angularSpeed = ROTATION_SPEED
                    elif event.key == rotationSteering.rotateRightKey:
                        self.world.component_for_entity(entity, Velocity).angularSpeed = -ROTATION_SPEED
                elif event.type == pygame.KEYUP and (event.key == rotationSteering.rotateLeftKey or event.key == rotationSteering.rotateRightKey):
                        self.world.component_for_entity(entity, Velocity).angularSpeed = 0

    def steerMovement(self, entity, movementSteering):
        for ent, keyboardEvents in self.world.get_component(KeyboardEvents):
            for event in keyboardEvents.events:
                if event.type == pygame.KEYDOWN:
                    if event.key == movementSteering.moveForwardKey:
                        self.world.component_for_entity(entity, Velocity).speed = -MOVEMENT_SPEED
                    elif event.key == movementSteering.moveBackwardsKey:
                        self.world.component_for_entity(entity, Velocity).speed = MOVEMENT_SPEED
                elif event.type == pygame.KEYUP and (event.key == movementSteering.moveForwardKey or event.key == movementSteering.moveBackwardsKey):
                    self.world.component_for_entity(entity, Velocity).speed = 0

    def process(self):
        for ent, (_, movementSteering) in self.world.get_components(Velocity, MovementSteering):
            self.steerMovement(ent, movementSteering)
        for ent, (_, rotationSteering) in self.world.get_components(Velocity, RotationSteering):
            self.steerRotation(ent, rotationSteering)

class CollisionProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def circlesCollide(self, x0, y0, r0, x1, y1, r1):
        pointDifference = math.pow(x0 - x1, 2) + math.pow(y0 - y1, 2)
        return math.pow(r0-r1, 2) <= pointDifference and pointDifference <= math.pow(r0+r1, 2)

    def process(self):
        for entityA, (positionA, solidA) in self.world.get_components(PositionBox, Solid):
            for entityB, (positionB, solidB) in self.world.get_components(PositionBox, Solid):
                if (entityA != entityB) and self.circlesCollide(positionA.x, positionA.y, solidA.collisionRadius,
                                       positionB.x, positionB.y, solidB.collisionRadius):
                    self.world.delete_entity(entityA)
                    self.world.delete_entity(entityB)
            
class KeyboardEventProcessor(esper.Processor):
    def __init__(self, eventsEntity):
        super().__init__()
        self.eventsEntity = eventsEntity

    def process(self):
        # FIXME Can be used to decouple further processors from pygame by mapping those events to other objects
        self.world.component_for_entity(self.eventsEntity, KeyboardEvents).events = pygame.event.get()



class RenderProcessor(esper.Processor):

    FRAME_AVG_SIZE = 100
    
    def __init__(self, window, clock, clear_color=(0, 0, 0)):
        super().__init__()
        self.window = window
        self.clock = clock
        self.clear_color = clear_color
        self.currentFrame = 0
        self.lastFrameTimes = [0] * self.FRAME_AVG_SIZE

    def blitRotate(self, surf, image, pos, originPos, angle):
        # calcaulate the axis aligned bounding box of the rotated image
        w, h         = image.get_size()
        sin_a, cos_a = math.sin(math.radians(angle)), math.cos(math.radians(angle))
        min_x, min_y = min([0, sin_a*h, cos_a*w, sin_a*h + cos_a*w]), max([0, sin_a*w, -cos_a*h, sin_a*w - cos_a*h])
        # calculate the translation of the pivot
        pivot        = pygame.math.Vector2(originPos[0], -originPos[1])
        pivot_rotate = pivot.rotate(angle)
        pivot_move   = pivot_rotate - pivot
        # calculate the upper left origin of the rotated image
        origin = (pos[0] - originPos[0] + min_x - pivot_move[0], pos[1] - originPos[1] - min_y + pivot_move[1])
        # get a rotated image
        rotated_image = pygame.transform.rotate(image, angle)
        # rotate and blit the image
        surf.blit(rotated_image, origin)

    def addRawTime(self, time):
        self.lastFrameTimes[self.currentFrame % self.FRAME_AVG_SIZE] = time

    def getRawTimeAvg(self):
        return sum(self.lastFrameTimes)/self.FRAME_AVG_SIZE

    def process(self):
        # Clear the window:
        self.window.fill(self.clear_color)
        for ent, (rend, position) in self.world.get_components(Renderable, PositionBox):
            pivot = pygame.math.Vector2(position.pivotx, position.pivoty)
            originalPosition = pygame.math.Vector2(position.x, position.y)
            self.blitRotate(self.window, rend.image, originalPosition, pivot, position.rotation)


        font = pygame.font.Font(None, 20)
        fps = font.render("FPS: {} (update took: {:.1f} ms (avg from {} FPS))".format(int(self.clock.get_fps()), self.getRawTimeAvg(), self.FRAME_AVG_SIZE), True, pygame.Color('white'))
        self.window.blit(fps, (10, 10))
        # Flip the framebuffers
        pygame.display.flip()
        self.addRawTime(self.clock.get_rawtime())
        self.currentFrame += 1
        self.clock.tick(FPS)

FPS = 30
RESOLUTION = 720, 480

MOVEMENT_SPEED = 6
ROTATION_SPEED = 3

def createTank(world, startx, starty, bodyRotation=0.0, gunRotation=0.0, isPlayer=False):
    bodyImage = pygame.image.load("assets/tank_body.png")
    gunImage = pygame.image.load("assets/tank_gun.png")
    bw, bh = bodyImage.get_width(), bodyImage.get_height()

    body = world.create_entity()
    world.add_component(body, Renderable(image=bodyImage))
    world.add_component(body, Solid(collisionRadius=math.sqrt(bw*bw + bh*bh)/2 * 0.7)) # may overlap a little sometimes
    world.add_component(body, PositionBox(x=startx, y=starty, w=bw, h=bh))
    world.add_component(body, Velocity(speed=0, angularSpeed=0))
    world.add_component(body, Rotate(bodyRotation))
    
    # TODO Ordering of rendering should be processed separetely, now it is based on declaration order
    # Idea is to use a PreRenderingProcessor that would add Rendarable elements to components based on their zlevel that would run once
    gun = world.create_entity()
    world.add_component(gun, Renderable(image=gunImage))
    # FIXME For now the gun and body must have the same center or they will diverge during rotation/moving
    world.add_component(gun, PositionBox(x=startx, y=starty, w=gunImage.get_width(), h=gunImage.get_height()))
    world.add_component(gun, Velocity(speed=0, angularSpeed=0))
    world.add_component(gun, Rotate(gunRotation))

    if isPlayer:
        world.add_component(body, MovementSteering(moveForwardKey=pygame.K_w, moveBackwardsKey=pygame.K_s))
        world.add_component(body, RotationSteering(rotateLeftKey=pygame.K_a, rotateRightKey=pygame.K_d))
        world.add_component(gun, RotationSteering(rotateLeftKey=pygame.K_j, rotateRightKey=pygame.K_l))
   
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
    world.add_component(events, KeyboardEvents())

    createTank(world=world, startx=400, starty=100, bodyRotation=random.randint(0,359), gunRotation=random.randint(0,359), isPlayer = False)
    createTank(world=world, startx=600, starty=400, bodyRotation=random.randint(0,359), gunRotation=random.randint(0,359), isPlayer = False)

    createTank(world=world, startx=200, starty=200, bodyRotation=-90, gunRotation=0, isPlayer = True)

    gameEndProcessor = GameEndProcessor()
    world.add_processor(KeyboardEventProcessor(events))
    world.add_processor(SteeringProcessor())
    world.add_processor(gameEndProcessor)
    world.add_processor(CollisionProcessor())
    world.add_processor(MovementProcessor())
    world.add_processor(RotationProcessor())
    world.add_processor(VelocityProcessor())
    world.add_processor(RenderProcessor(window=window, clock=clock))

    while gameEndProcessor.isGameRunning():
        # A single call to world.process() will update all Processors:
        world.process()


if __name__ == "__main__":
    run()
    pygame.quit()
