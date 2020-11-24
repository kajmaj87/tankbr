class PlayerInfo:
    def __init__(self, name, score=0):
        self.name = name
        self.score = score
        # will be set by rating component
        self.rating = None
        self.ranking = None
        self.mu = None
        self.sigma = None


class Move:
    def __init__(self, distance=0.0):
        self.distance = distance


class Score:
    """Define points for some entity. One enity can have many scores"""

    def __init__(self, ownerId, points=0):
        self.ownerId = ownerId
        self.points = points


class Velocity:
    def __init__(self, speed=0.0, angularSpeed=0.0):
        self.speed = speed
        self.angularSpeed = angularSpeed


class Rotate:
    def __init__(self, angle=0.0):
        self.angle = angle


class RotateGun:
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


class FiringSteering:
    def __init__(self, fireGunKey):
        self.fireGunKey = fireGunKey


class Perception:
    """Special dynamic object used in AI context. You can pass anything to it and use in AI decisionFunction"""

    pass


class Memory:
    """Special dynamic object used in AI context. You can pass anything to it and use in AI decisionFunction"""

    pass


class AI:
    def __init__(self, decisionFunction, memory=None):
        self.decisionFunction = decisionFunction
        self.memory = memory

    def decide(self, perception, memory):
        return self.decisionFunction(perception, memory)


class Agent:
    """Marker component for players/AIs that are taking part in the game actively"""

    pass


class Decision:
    def __init__(self, commands, timeout=1):
        self.commands = commands
        self.timeout = timeout


class PositionBox:
    def __init__(self, x=0.0, y=0.0, w=0.0, h=0.0, rotation=0.0, pivotx=None, pivoty=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.rotation = rotation
        if pivotx is None:
            self.pivotx = w / 2
        else:
            self.pivotx = pivotx
        if pivoty is None:
            self.pivoty = h / 2
        else:
            self.pivoty = pivoty

    def getCenter(self):
        return (self.x - self.w) / 2, (self.y - self.h) / 2


class Solid:
    def __init__(self, collisionRadius):
        self.collisionRadius = collisionRadius


class Explosive:
    pass


class Gun:
    def __init__(self, gunEntity, ammo):
        self.gunEntity = gunEntity
        self.ammo = ammo
        self.reloadTimeLeft = 0
        self.isLoaded = True


class RangeFinder:
    def __init__(self, maxRange, angleOffset):
        self.maxRange = maxRange
        self.angleOffset = angleOffset
        self.closestTarget = None


class FireGun:
    pass


class Child:
    def __init__(self, childId):
        self.childId = childId


class Owner:
    def __init__(self, ownerId):
        self.ownerId = ownerId


class InputEvents:
    def __init__(self, events=None):
        self.events = events


class Renderable:
    def __init__(self, image, rotation=0):
        self.image = image
        self.w = image.get_width()
        self.h = image.get_height()
        self.rotation = rotation
