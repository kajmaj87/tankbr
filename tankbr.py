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
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

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

    def process(self):
        for ent, (move, position) in self.world.get_components(Move, PositionBox):
            # TODO Movement must take rotation into account
            position.x += move.x
            position.y += move.y
            self.world.remove_component(ent, Move)

class RotationProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        for ent, (rotate, position) in self.world.get_components(Rotate, PositionBox):
            position.rotation += rotate.angle
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
        # This will iterate over every Entity that has this Component, and blit it:
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
    player = world.create_entity()
    bodyImage = pygame.image.load("assets/tank_body.png")
    gunImage = pygame.image.load("assets/tank_gun.png")
    

    world.add_component(player, Renderable(image=bodyImage))
    world.add_component(player, PositionBox(x=STARTING_POSITION_X, y=STARTING_POSITION_Y, w=bodyImage.get_width(), h=bodyImage.get_height()))

    gun = world.create_entity()
    world.add_component(gun, Renderable(image=gunImage))
    world.add_component(gun, PositionBox(x=STARTING_POSITION_X, y=STARTING_POSITION_Y+10, w=gunImage.get_width(), h=gunImage.get_height(), pivoty=gunImage.get_height()*4/5))

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
                    world.add_component(player, Rotate(angle=-3))
                elif event.key == pygame.K_d:
                    world.add_component(player, Rotate(angle=3))
                elif event.key == pygame.K_w:
                    world.add_component(player, Move(x=0, y=-6))
                    world.add_component(gun, Move(x=0, y=-6))
                elif event.key == pygame.K_s:
                    world.add_component(player, Move(x=0, y=6))
                    world.add_component(gun, Move(x=0, y=6))
                elif event.key == pygame.K_l:
                    world.add_component(gun, Rotate(angle=-5))
                elif event.key == pygame.K_j:
                    world.add_component(gun, Rotate(angle=5))
                elif event.key == pygame.K_ESCAPE:
                    running = False

        # A single call to world.process() will update all Processors:
        world.process()

        clock.tick(FPS)


if __name__ == "__main__":
    run()
    pygame.quit()
