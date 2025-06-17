from geometry.primitives import Point, Rectangle, line_intersects


def test_horizontal_vertical_pass():
    """Пряма через центр – має перетинати прямокутник."""
    r = Rectangle(
        id=1,
        corners=[
            Point(0, 0), Point(2, 0),
            Point(2, 1), Point(0, 1),
        ],
    )
    # y = 0.5  (a = 0, k = 0.5)
    assert line_intersects(r, a=0, k=0.5)


def test_far_line():
    """Далека горизонтальна пряма не перетинає."""
    r = Rectangle(
        id=2,
        corners=[
            Point(0, 0), Point(2, 0),
            Point(2, 1), Point(0, 1),
        ],
    )
    # y = 10
    assert not line_intersects(r, a=0, k=10)