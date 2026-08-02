class Track:
    def __init__(self, corners):
        self.corners = corners

    @property
    def length(self):
        return sum(l for l, _ in self.corners)

    def v_limit(self, s):
        s_mod = s % self.length
        limit = 100.0
        for l, v_corner in self.corners:
            if s_mod < l:
                return min(limit, v_corner if s_mod >= l - 60.0 else limit)
            s_mod -= l
        return limit

    def corner_at(self, s):
        s_mod = s % self.length
        for l, v_corner in self.corners:
            if s_mod < l:
                return l - 60.0, v_corner
            s_mod -= l
        return self.length, 100.0


def monza():
    corners = [
        (500.0, 62.0),
        (420.0, 72.0),
        (360.0, 58.0),
        (450.0, 80.0),
        (900.0, 55.0),
        (700.0, 70.0),
        (650.0, 95.0),
    ]
    return Track(corners)


def spa():
    corners = [
        (700.0, 80.0),
        (300.0, 55.0),
        (900.0, 45.0),
        (600.0, 65.0),
        (500.0, 75.0),
        (400.0, 50.0),
        (750.0, 90.0),
    ]
    return Track(corners)
