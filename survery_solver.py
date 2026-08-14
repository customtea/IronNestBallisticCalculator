from math import sin, cos, radians, sqrt, atan2, degrees, hypot
from grid_coordinate import GridCoordinate


class SurveySolver:
    """Grid Survery Calcuration"""

    METER_PER_KM = 1000

    @classmethod
    def from_angle_distance(
        cls,
        point: GridCoordinate,
        angle_deg: float,
        distance_km: float,
    ) -> GridCoordinate:
        """Calcurate Position from Angle and Distance of Position1

        :param point: Reference Position
        :type point: GridCoordinate
        :param angle_deg: Angle of Reference Position
        :type angle_deg: float
        :param distance_km: Distance of Reference Position
        :type distance_km: float
        :return: Calurated Positon
        :rtype: GridCoordinate
        """


        x, y = point.to_xy()

        length = distance_km * cls.METER_PER_KM
        theta = radians(angle_deg)

        x += length * sin(theta)
        y += length * cos(theta)

        return GridCoordinate.from_xy(x, y)


    @classmethod
    def from_two_angles(
        cls,
        point_a: GridCoordinate,
        angle_a: float,
        point_b: GridCoordinate,
        angle_b: float,
    ) -> GridCoordinate:
        """Calcurate Position from Two Angles

        :param point_a: Reference Point A
        :type point_a: GridCoordinate
        :param angle_a: Angle of Point A
        :type angle_a: float
        :param point_b: Reference Point B
        :type point_b: GridCoordinate
        :param angle_b: Angle of Point B
        :type angle_b: float
        :raises ValueError: Parallel Angle
        :return: Calurated Positon
        :rtype: GridCoordinate
        """

        xa, ya = point_a.to_xy()
        xb, yb = point_b.to_xy()

        sa = sin(radians(angle_a))
        ca = cos(radians(angle_a))

        sb = sin(radians(angle_b))
        cb = cos(radians(angle_b))

        denom = sa * cb - ca * sb

        if abs(denom) < 1e-10:
            raise ValueError("Two Angle is Parallel")

        t = (
            (xb - xa) * cb -
            (yb - ya) * sb
        ) / denom

        x = xa + t * sa
        y = ya + t * ca

        return GridCoordinate.from_xy(x, y)


    @classmethod
    def from_two_distances(
        cls,
        point_a: GridCoordinate,
        distance_a_km: float,
        point_b: GridCoordinate,
        distance_b_km: float,
    ) -> list[GridCoordinate]:
        """Calcurate Position from Two Distances

        :param point_a: Reference Position A
        :type point_a: GridCoordinate
        :param distance_a_km: Distance of Position A
        :type distance_a_km: float
        :param point_b: Reference Position B
        :type point_b: GridCoordinate
        :param distance_b_km: Distance of Position B
        :type distance_b_km: float
        :raises ValueError: Same Refernce Position
        :return: Calurated Positon
        :rtype: list[GridCoordinate]
        """


        xa, ya = point_a.to_xy()
        xb, yb = point_b.to_xy()

        r0 = distance_a_km * cls.METER_PER_KM
        r1 = distance_b_km * cls.METER_PER_KM

        dx = xb - xa
        dy = yb - ya

        d = sqrt(dx * dx + dy * dy)

        if d == 0:
            raise ValueError("Same Refernce Position")

        if d > r0 + r1:
            return []

        if d < abs(r0 - r1):
            return []

        a = (r0 * r0 - r1 * r1 + d * d) / (2 * d)

        h2 = r0 * r0 - a * a

        if h2 < 0:
            h2 = 0

        h = sqrt(h2)

        xc = xa + a * dx / d
        yc = ya + a * dy / d

        rx = -dy * h / d
        ry = dx * h / d

        result = [
            GridCoordinate.from_xy(
                xc + rx,
                yc + ry,
            )
        ]

        if h > 1e-10:
            result.append(
                GridCoordinate.from_xy(
                    xc - rx,
                    yc - ry,
                )
            )

        return result


    @classmethod
    def from_angle_and_distance(
        cls,
        point_a: GridCoordinate,
        angle_a: float,
        point_b: GridCoordinate,
        distance_b_km: float,
    ) -> list[GridCoordinate]:
        """Calcurate Position from One Angle One Distance

        :param point_a: Refernce Position A
        :type point_a: GridCoordinate
        :param angle_a: Angle of Position A
        :type angle_a: float
        :param point_b: Refernce Position B
        :type point_b: GridCoordinate
        :param distance_b_km: Distance of Position B
        :type distance_b_km: float
        :return: List of Calurated Position
        :rtype: list[GridCoordinate]
        """

        xa, ya = point_b.to_xy()
        xb, yb = point_a.to_xy()

        radius = distance_b_km * cls.METER_PER_KM

        s = sin(radians(angle_a))
        c = cos(radians(angle_a))

        dx = xb - xa
        dy = yb - ya

        A = dx * s + dy * c
        B = dx * dx + dy * dy - radius * radius

        D = A * A - B

        if D < 0:
            return []

        root = sqrt(max(D, 0))

        result = []

        t = -A + root

        result.append(
            GridCoordinate.from_xy(
                xb + t * s,
                yb + t * c,
            )
        )

        if root > 1e-10:

            t = -A - root

            result.append(
                GridCoordinate.from_xy(
                    xb + t * s,
                    yb + t * c,
                )
            )

        return result


    @classmethod
    def to_angle_distance(
        cls,
        point_from: GridCoordinate,
        point_to: GridCoordinate,
    ) -> tuple[float, float]:
        """Calcurate Angle and Distance from Two Position

        :param point_from: Source Position
        :type point_from: GridCoordinate
        :param point_to: Destination Position
        :type point_to: GridCoordinate
        :return: angle, distance
        :rtype: tuple[float, float]
        """

        angle = cls.to_angle(point_from, point_to)
        distance_km = cls.to_distance(point_from, point_to)

        return angle, distance_km


    @classmethod
    def to_distance(
        cls,
        point_from: GridCoordinate,
        point_to: GridCoordinate,
    ) -> float:
        """Calcurate Distance from Two Position

        :param point_from: Source Position
        :type point_from: GridCoordinate
        :param point_to: Destination Position
        :type point_to: GridCoordinate
        :return: Distance
        :rtype: float
        """

        x1, y1 = point_from.to_xy()
        x2, y2 = point_to.to_xy()

        dx = x2 - x1
        dy = y2 - y1

        distance_grid = hypot(dx, dy)
        distance_km = distance_grid / cls.METER_PER_KM

        return distance_km


    @classmethod
    def to_angle(
        cls,
        point_from: GridCoordinate,
        point_to: GridCoordinate,
    ) -> float:
        """Calurate Angle from Two Position

        :param point_from: Source Position
        :type point_from: GridCoordinate
        :param point_to: Destination Position
        :type point_to: GridCoordinate
        :return: Angle
        :rtype: float
        """

        x1, y1 = point_from.to_xy()
        x2, y2 = point_to.to_xy()

        dx = x2 - x1
        dy = y2 - y1

        angle = degrees(atan2(dx, dy))

        if angle < 0:
            angle += 360

        return angle % 360
