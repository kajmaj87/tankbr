cpdef double square(double a):
    return a*a

def circlesCollide(double x0, double y0, double r0, double x1, double y1, double r1):
    cdef float a = (x0 - x1)**2
    cdef float b = (y0 - y1)**2
    cdef float r_low = (r0 - r1)**2
    cdef float r_high = (r0 + r1)**2
    cdef float pointDifference = a + b
    return r_low <= pointDifference and pointDifference <= r_high


cdef double dist_square(double x1, double y1, double x2, double y2):
    dx, dy = x1 - x2, y1 - y2
    return dx * dx + dy * dy

def segmentAndCircleIntersect(double sourceStartX, double sourceStartY, double sourceEndX, double sourceEndY, double startEndDist, double targetX, double targetY, double targetRange):
    """Check if a line coming from (sourceX, sourceY) ending at (sourceEndX, sourceEndY) intersects
       a circle of range targetRange centered at (targetX, targetY)
       You have to provide distansce between sourceStart and sourceEnd as startEndDist"""
    cdef double maxRangeSqr = square(startEndDist)
    cdef double maxRangeWithCollision = startEndDist + targetRange
    # range between and of laser and target is not bigger than max laser range
    cdef bint targetInFront = dist_square(targetX, targetY, sourceEndX, sourceEndY) < maxRangeSqr
    cdef bint targetInRange = (
            dist_square(sourceStartX, sourceStartY, targetX, targetY)
            < square(maxRangeWithCollision)
    )
    x1, y1, x2, y2 = (
        sourceStartX - targetX,
        sourceStartY - targetY,
        sourceEndX - targetX,
        sourceEndY - targetY,
    )
    dr_square = dist_square(x1, y1, x2, y2)
    D = x1 * y2 - x2 * y1
    delta = square(targetRange) * dr_square - square(D)
    return delta>0 and targetInFront and targetInRange

