from grid_coordinate import GridCoordinate
from survery_solver import SurveySolver


class IronNestBallisticCalc():
    AngleCoefficientTable = {1:12, 2:6, 3:4, 4:3, 5:2.4, 6:2}
    
    def __init__(self) -> None:
        pass
    
    def setpos(self, position: GridCoordinate) -> None:
        self.ironnest:GridCoordinate = position

    @classmethod
    def distance_charge_to_elevangle(cls, distance, charge):
        baseangle = cls.AngleCoefficientTable.get(charge)
        return distance * baseangle
    
    @classmethod
    def distance_to_elevangle_charge(cls, distance):
        for charge, agl in cls.AngleCoefficientTable.items():
            angle = distance * agl
            if angle < 60:
                return angle, charge
        return 0, 0
    
    @classmethod
    def two_point_to_azimuth_elevation(
        cls,
        point_from: GridCoordinate,
        point_to: GridCoordinate,
    ) -> tuple[float, float, int]:
        azimuth, distance = SurveySolver.to_angle_distance(point_from, point_to)
        elevation, charge = cls.distance_to_elevangle_charge(distance)

        return azimuth, elevation, charge
    
    def fire(
        self,
        point_to: GridCoordinate,
    ) -> tuple[float, float, int]:
        azimuth, elevation, charge = self.two_point_to_azimuth_elevation(self.ironnest, point_to)

        return azimuth, elevation, charge

