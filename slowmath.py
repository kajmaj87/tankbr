def square(a):
    return a * a


def circlesCollide(x0, y0, r0, x1, y1, r1):
    a = (x0 - x1) ** 2
    b = (y0 - y1) ** 2
    r_low = (r0 - r1) ** 2
    r_high = (r0 + r1) ** 2
    pointDifference = a + b
    return r_low <= pointDifference and pointDifference <= r_high


def dist_square(x1, y1, x2, y2):
    dx, dy = x1 - x2, y1 - y2
    return dx * dx + dy * dy


# nice calculation at:
#   https://mathworld.wolfram.com/Circle-LineIntersection.html#:~:text=In%20geometry%2C%20a%20line%20meeting,429).
def segmentAndCircleIntersect(
    sourceStartX,
    sourceStartY,
    sourceEndX,
    sourceEndY,
    startEndDist,
    targetX,
    targetY,
    targetRange,
):
    """Check if a line coming from (sourceX, sourceY) ending at (sourceEndX, sourceEndY) intersects
    a circle of range targetRange centered at (targetX, targetY)
    You have to provide distansce between sourceStart and sourceEnd as startEndDist"""
    maxRangeSqr = square(startEndDist)
    maxRangeWithCollision = startEndDist + targetRange
    # range between and of laser and target is not bigger than max laser range
    targetInFront = dist_square(targetX, targetY, sourceEndX, sourceEndY) < maxRangeSqr
    targetInRange = dist_square(sourceStartX, sourceStartY, targetX, targetY) < square(maxRangeWithCollision)
    x1, y1, x2, y2 = (
        sourceStartX - targetX,
        sourceStartY - targetY,
        sourceEndX - targetX,
        sourceEndY - targetY,
    )
    dr_square = dist_square(x1, y1, x2, y2)
    D = x1 * y2 - x2 * y1
    delta = square(targetRange) * dr_square - square(D)
    return delta > 0 and targetInFront and targetInRange
