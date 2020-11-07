#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
import esper
import math


FPS = 30
RESOLUTION = 720, 480


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

class Child:
    def __init__(self, childId):
        self.childId = childId

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

class RenderProcessor(esper.Processor):
    def __init__(self, window, clear_color=(0, 0, 0)):
        super().__init__()
        self.window = window
        self.clear_color = clear_color

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

    def process(self):
        # Clear the window:
        self.window.fill(self.clear_color)
        for ent, (rend, position) in self.world.get_components(Renderable, PositionBox):
            pivot = pygame.math.Vector2(position.pivotx, position.pivoty)
            originalPosition = pygame.math.Vector2(position.x, position.y)
            self.blitRotate(self.window, rend.image, originalPosition, pivot, position.rotation)

        # Flip the framebuffers
        pygame.display.flip()

STARTING_POSITION_X = 200
STARTING_POSITION_Y = 200

def run():
    # Initialize Pygame stuff
    pygame.init()
    window = pygame.display.set_mode(RESOLUTION)
    pygame.display.set_caption("Tankbr")
    clock = pygame.time.Clock()
    pygame.key.set_repeat(1, 1)

    # Initialize Esper world, and create a "player" Entity with a few Components.
    world = esper.World()
    bodyImage = pygame.image.load("assets/tank_body.png")
    gunImage = pygame.image.load("assets/tank_gun.png")
    

    player = world.create_entity()
    world.add_component(player, Renderable(image=bodyImage))
    world.add_component(player, PositionBox(x=STARTING_POSITION_X, y=STARTING_POSITION_Y, w=bodyImage.get_width(), h=bodyImage.get_height()))
    world.add_component(player, Velocity(speed=0, angularSpeed=0))
    
    # TODO Ordering of rendering should be processed separetely, now it is based on declaration order
    # Idea is to use a PreRenderingProcessor that would add Rendarable elements to components based on their zlevel that would run once
    gun = world.create_entity()
    world.add_component(gun, Renderable(image=gunImage))
    # FIXME For now the gun and body must have the same center or they will diverge during rotation/moving
    world.add_component(gun, PositionBox(x=STARTING_POSITION_X, y=STARTING_POSITION_Y, w=gunImage.get_width(), h=gunImage.get_height()))
    world.add_component(gun, Velocity(speed=0, angularSpeed=0))
   
    world.add_component(player, Child(gun))

    world.add_processor(VelocityProcessor())
    world.add_processor(MovementProcessor())
    world.add_processor(RotationProcessor())
    world.add_processor(RenderProcessor(window=window))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    world.component_for_entity(player, Velocity).angularSpeed = 3
                elif event.key == pygame.K_d:
                    world.component_for_entity(player, Velocity).angularSpeed = -3
                elif event.key == pygame.K_w:
                    world.component_for_entity(player, Velocity).speed = -6
                elif event.key == pygame.K_s:
                    world.component_for_entity(player, Velocity).speed = 6
                elif event.key == pygame.K_j:
                    world.component_for_entity(gun, Velocity).angularSpeed = 5
                elif event.key == pygame.K_l:
                    world.component_for_entity(gun, Velocity).angularSpeed = -5
                elif event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_w or event.key == pygame.K_s:
                    world.component_for_entity(player, Velocity).speed = 0
                elif event.key == pygame.K_d or event.key == pygame.K_a:
                    world.component_for_entity(player, Velocity).angularSpeed = 0
                elif event.key == pygame.K_j or event.key == pygame.K_l:
                    world.component_for_entity(gun, Velocity).angularSpeed = 0

        # A single call to world.process() will update all Processors:
        world.process()

        clock.tick(FPS)


if __name__ == "__main__":
    run()
    pygame.quit()
