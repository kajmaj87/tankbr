import math

import esper
import pygame
from argparser import config
from gamecomponents import (
    Renderable,
    PositionBox,
    Gun,
    PlayerInfo,
    InputEvents,
    Velocity,
    FireGun,
    MovementSteering,
    RotationSteering,
    FiringSteering,
)


class RenderProcessor(esper.Processor):
    FRAME_AVG_SIZE = 100

    def __init__(self):
        super().__init__()
        self.window = pygame.display.set_mode(config.gui_resolution)
        self.clock = pygame.time.Clock()
        self.clear_color = (0, 0, 0)
        self.currentFrame = 0
        self.lastFrameTimes = [0] * self.FRAME_AVG_SIZE
        # Initialize Pygame stuff
        if not pygame.get_init():
            pygame.init()
            pygame.display.set_caption("Tankbr")
            pygame.key.set_repeat(1, 1)

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
        rotated_image = pygame.transform.rotozoom(image, angle + imageRotation, config.gui_zoom)
        # rotate and blit the image
        surf.blit(rotated_image, self.transformCoordinates(x, y))

    def addRawTime(self, time):
        self.lastFrameTimes[self.currentFrame % self.FRAME_AVG_SIZE] = time

    def getRawTimeAvg(self):
        return sum(self.lastFrameTimes) / self.FRAME_AVG_SIZE

    def transformCoordinates(self, x, y):
        return (
            config.gui_zoom * x + config.gui_resolution[0] / 2 + config.gui_offset_x,
            -config.gui_zoom * y + config.gui_resolution[1] / 2 + config.gui_offset_y,
        )

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
            lx, ly = self.transformCoordinates(
                gunPosition.x + config.game_laser_range * cos_a, gunPosition.y + config.game_laser_range * sin_a
            )
            pygame.draw.line(self.window, pygame.Color(255, 0, 0), (x, y), (lx, ly), 2)

    def drawNamesAndScores(self):
        font = pygame.font.Font(None, 16)
        for ent, (info, position) in self.world.get_components(PlayerInfo, PositionBox):
            text = "{} +{:.1f}".format(info.name, info.score)
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
        self.clock.tick(config.gui_max_fps)


class InputEventProcessor(esper.Processor):
    def __init__(self, gameEndProcessor):
        super().__init__()
        self.gameEndProcessor = gameEndProcessor

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
            setAngularSpeed(ent, config.game_rotation_speed)

        def right(ent):
            setAngularSpeed(ent, -config.game_rotation_speed)

        self.registerKeyActions(entity, rotationSteering.rotateLeftKey, left, reset)
        self.registerKeyActions(entity, rotationSteering.rotateRightKey, right, reset)

    def steerMovement(self, entity, movementSteering):
        def setSpeed(ent, speed):
            self.world.component_for_entity(ent, Velocity).speed = speed

        def reset(ent):
            setSpeed(ent, 0)

        def forward(ent):
            setSpeed(ent, config.game_movement_speed)

        def backwards(ent):
            setSpeed(ent, -config.game_movement_speed)

        self.registerKeyActions(entity, movementSteering.moveForwardKey, forward, reset)
        self.registerKeyActions(entity, movementSteering.moveBackwardsKey, backwards, reset)

    def fireGun(self, entity, firingSteering):
        self.registerKeyActions(
            entity,
            firingSteering.fireGunKey,
            lambda ent: self.world.add_component(ent, FireGun()),
        )

    def doMouseActions(self):
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
                        config.gui_offset_x += x
                        config.gui_offset_y += y

    def checkForQuit(self):
        for ent, inputEvents in self.world.get_component(InputEvents):
            for event in inputEvents.events:
                if event.type == pygame.QUIT:
                    self.gameEndReason = self.gameEndProcessor.GameEndReason.MANUAL
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.gameEndReason = self.gameEndProcessor.GameEndReason.MANUAL

    def process(self):
        for ent, (_, movementSteering) in self.world.get_components(Velocity, MovementSteering):
            self.steerMovement(ent, movementSteering)
        for ent, (_, rotationSteering) in self.world.get_components(Velocity, RotationSteering):
            self.steerRotation(ent, rotationSteering)
        for ent, (_, firingSteering) in self.world.get_components(Gun, FiringSteering):
            self.fireGun(ent, firingSteering)
        self.doMouseActions()
        self.checkForQuit()


class InputEventCollector(esper.Processor):
    def __init__(self, eventsEntity):
        super().__init__()
        self.eventsEntity = eventsEntity

    def process(self):
        # FIXME Can be used to decouple further processors from
        # pygame by mapping those events to other objects
        self.world.component_for_entity(self.eventsEntity, InputEvents).events = pygame.event.get()


def increaseZoom():
    config.gui_zoom *= 1 + config.gui_zoom_change_factor


def decreaseZoom():
    config.gui_zoom *= 1 - config.gui_zoom_change_factor
