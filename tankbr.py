#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
import esper


FPS = 30
RESOLUTION = 720, 480


##################################
#  Define some Components:
##################################
class Movement:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

class Position:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y


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
        for ent, (move, position) in self.world.get_components(Movement, Position):
            position.x += move.x
            position.y += move.y
            self.world.remove_component(ent, Movement)


class RenderProcessor(esper.Processor):
    def __init__(self, window, clear_color=(0, 0, 0)):
        super().__init__()
        self.window = window
        self.clear_color = clear_color

    def process(self):
        # Clear the window:
        self.window.fill(self.clear_color)
        # This will iterate over every Entity that has this Component, and blit it:
        for ent, (rend, position) in self.world.get_components(Renderable, Position):
            self.window.blit(rend.image, (position.x, position.y))
        # Flip the framebuffers
        pygame.display.flip()

STARTING_POSITION_X = 200
STARTING_POSITION_Y = 200

def run():
    # Initialize Pygame stuff
    pygame.init()
    window = pygame.display.set_mode(RESOLUTION)
    pygame.display.set_caption("Esper Pygame example")
    clock = pygame.time.Clock()
    pygame.key.set_repeat(1, 1)

    # Initialize Esper world, and create a "player" Entity with a few Components.
    world = esper.World()
    player = world.create_entity()
    bodyImage = pygame.image.load("assets/tank_body.png")
    gunImage = pygame.image.load("assets/tank_gun.png")
    

    world.add_component(player, Renderable(image=bodyImage))
    world.add_component(player, Position(x=STARTING_POSITION_X, y=STARTING_POSITION_Y))

    gun = world.create_entity()
    world.add_component(gun, Renderable(image=gunImage))
    world.add_component(gun, Position(x=STARTING_POSITION_X + bodyImage.get_width()/2 - gunImage.get_width()/2, y=STARTING_POSITION_Y))

    # Create some Processor instances, and asign them to be processed.
    render_processor = RenderProcessor(window=window)
    movement_processor = MovementProcessor()
    world.add_processor(render_processor)
    world.add_processor(movement_processor)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    world.add_component(player, Movement(x=-6, y=0))
                elif event.key == pygame.K_RIGHT:
                    world.add_component(player, Movement(x=6, y=0))
                elif event.key == pygame.K_UP:
                    world.add_component(player, Movement(x=0, y=-6))
                elif event.key == pygame.K_DOWN:
                    world.add_component(player, Movement(x=0, y=6))
                elif event.key == pygame.K_ESCAPE:
                    running = False

        # A single call to world.process() will update all Processors:
        world.process()

        clock.tick(FPS)


if __name__ == "__main__":
    run()
    pygame.quit()
