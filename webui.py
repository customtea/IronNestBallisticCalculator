from main import IronNestShell, registry

from decimal import Decimal, ROUND_HALF_UP

from grid_coordinate import GridCoordinate
from survery_solver import SurveySolver
from ironnest_ballistic import IronNestBallisticCalc

@registry.command("fire", "<PointName>", "Calculate Aziuth, Elevation, Charge to PointName")
def do_fire(shell: IronNestShell, argv:list[str]):
    if len(argv) < 1:
        print("Not Enough arguments")
        return
    name = argv[0]
    pdat = shell.context.pointdata.get(name)
    if pdat is None:
        print(f"Not Found {name}")
        return 
    pos = pdat.pos
    # s1 = args[0]
    # s2 = args[1]
    # pos = GridCoordinate.from_grid(f"{s1} {s2}")
    _, distance = SurveySolver.to_angle_distance(shell.context.ironnest.ironnest, pos)
    azimuth, angle, charge = shell.context.ironnest.fire(pos)

    p_distance = Decimal(str(distance)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    p_angle = Decimal(str(angle)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    p_azimuth = Decimal(str(azimuth)).quantize(Decimal("0.1"), ROUND_HALF_UP)
    print(f"Target:{name:<5}\nPOINT:{pos.to_grid()}\nDISTANCE:{p_distance:05.2f}\nCharge:{charge}\nElevAngle:{p_angle:05.2f}\nAzimuth:{p_azimuth:05.1f}")


@registry.command("dfire", "<PointName1> <PointName2>", "Calculate Aziuth, Elevation, Charge to Two PointName. For Double Cannon")
def double_fire(shell: IronNestShell, argv:list[str]):
    if len(argv) < 2:
        print("Not Enough arguments")
        return
    name1 = argv[0]
    name2 = argv[1]
    pdat1 = shell.context.pointdata.get(name1)
    if pdat1 is None:
        print(f"Not Found {name1}")
        return 
    pdat2 = shell.context.pointdata.get(name2)
    if pdat2 is None:
        print(f"Not Found {name2}")
        return 
    pos = pdat1.pos
    _, distance = SurveySolver.to_angle_distance(shell.context.ironnest.ironnest, pos)
    azimuth, angle, charge = shell.context.ironnest.fire(pos)
    p_distance = Decimal(str(distance)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    p_angle = Decimal(str(angle)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    p_azimuth = Decimal(str(azimuth)).quantize(Decimal("0.1"), ROUND_HALF_UP)
    print(f"LEFT  CANNON: {name1:<5}\nPOINT:{pos.to_grid()} DIST:{p_distance:05.2f}\nCharge:{charge}\nElevAngle:{p_angle:05.2f}\nAzimuth:{p_azimuth:04.1f}")
    print()

    pos = pdat2.pos
    _, distance = SurveySolver.to_angle_distance(shell.context.ironnest.ironnest, pos)
    azimuth, angle, charge = shell.context.ironnest.fire(pos)
    p_distance = Decimal(str(distance)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    p_angle = Decimal(str(angle)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    p_azimuth = Decimal(str(azimuth)).quantize(Decimal("0.1"), ROUND_HALF_UP)
    print(f"RIGHT CANNON: {name2:<5}\nPOINT:{pos.to_grid()} DIST:{p_distance:05.2f}\nCharge:{charge}\nElevAngle:{p_angle:05.2f}\nAzimuth:{p_azimuth:04.1f}")




