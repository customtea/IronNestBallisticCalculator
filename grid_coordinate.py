from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN



L_GRIDALP = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",]
D_GRIDALP = {"A":0, "B":1, "C":2, "D":3, "E":4, "F":5, "G":6, "H":7, "I":8, "J":9, "K":10, "L":11, "M":12, "N":13, "O":14, "P":15, "Q":16, "R":17, "S":18, "T":19}

my_round = lambda x: Decimal(str(x)).quantize(Decimal("0"), ROUND_HALF_UP)

class GridCoordinate:
    METER_PER_KM = 1000
    GRID_PER_KM = 100

    def __init__(self) -> None:
        self.posx: float
        self.posy: float
    
    def __str__(self) -> str:
        return self.to_grid()
    
    def __repr__(self) -> str:
        return self.to_grid()
    
    def to_xy(self):
        return (self.posx, self.posy)
    
    def to_grid(self):
        ax = int(my_round(self.posx) // self.METER_PER_KM)
        ay = int(my_round(self.posy) // self.METER_PER_KM)
        sx = int((my_round(self.posx) % self.METER_PER_KM) // self.GRID_PER_KM)
        sy = int((my_round(self.posy) % self.METER_PER_KM) // self.GRID_PER_KM)
        ax_alp = L_GRIDALP[ax]
        s = f"{ax_alp}{ay} {sx}:{sy}"
        return s

    def to_areapos(self):
        ax = int(my_round(self.posx) // self.METER_PER_KM)
        ay = int(my_round(self.posy) // self.METER_PER_KM)
        return ax, ay
    
    def is_valid(self):
        return 0 <= self.posx <= 20*self.METER_PER_KM and 0 <= self.posy <= 10*self.METER_PER_KM
    
    @classmethod
    def from_xy(cls, x, y):
        c = cls()
        c.posx = x
        c.posy = y
        return c

    @classmethod
    def from_grid(cls, s):
        c = cls()
        sp = s.split(" ")
        area = sp[0]
        subarea = sp[1]
        galp = area[0].upper()
        t = D_GRIDALP.get(galp)
        if t is None:
            raise IndexError
        ax = int(t)
        ay = int(area[1])
        sx = int(subarea[0])
        sy = int(subarea[2])
        c.posx = ax*cls.METER_PER_KM + sx*cls.GRID_PER_KM + 50
        c.posy = ay*cls.METER_PER_KM + sy*cls.GRID_PER_KM + 50
        return c
