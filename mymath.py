try:
    from fastmath import square, circlesCollide, segmentAndCircleIntersect
except:
    print("Fast math libraries not found, compile fastmath.pyx with Cython to have better performance")
    from slowmath import square, circlesCollide, segmentAndCircleIntersect
