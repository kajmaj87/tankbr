import math
import random

import pygame

from argparser import config
from gamecomponents import (
    RotationSteering,
    FiringSteering,
    MovementSteering,
    Solid,
    PositionBox,
    Renderable,
    Velocity,
    Owner,
    Explosive,
    Agent,
    Rotate,
    RangeFinder,
    Gun,
    AI,
    Child,
    TTL,
)


def bullet(world, ownerId, position):
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


def tank(world, startx, starty, playerInfo, bodyRotation=0.0, gunRotation=0.0):
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


def tanks(world, players):
    for p in players:
        if p.ai is None:
            tank(world=world, startx=0, starty=0, bodyRotation=0, gunRotation=0, playerInfo=p)
        else:
            tank(
                world=world,
                startx=random.randint(-config.game_spawn_range, config.game_spawn_range),
                starty=random.randint(-config.game_spawn_range, config.game_spawn_range),
                bodyRotation=random.randint(0, 359),
                gunRotation=random.randint(0, 359),
                playerInfo=p,
            )
