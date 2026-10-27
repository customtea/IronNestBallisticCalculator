import cmd
import shlex
import json
from dataclasses import dataclass, field
from typing import IO, Any, Callable
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from typing import NamedTuple

from grid_coordinate import GridCoordinate
from survery_solver import SurveySolver
from ironnest_ballistic import IronNestBallisticCalc

__author__ = 'customtea (https://github.com/customtea/)'
__semver__ = '0.1.0'
__program__ = 'IronNest Ballistic Calculator'
__version__ = f'{__program__} ver:{__semver__} Created By {__author__}'

Handler = Callable[..., None]

@dataclass(slots=True)
class CommandNode:
    # name: str
    handler: Handler | None = None
    helptext: str = ""
    argshelptext:str = ""
    children: dict[str, "CommandNode"] = field(default_factory=dict)

class CommandRegistry:
    def __init__(self):
        self.root = CommandNode()
        self.__commands_list = []
        self.__commands_help_list = []

    def command(self, path: str, argshelp:str="" , helptext=""):
        """
        @registry.command("user add")
        @registry.command("config get value")
        """

        parts = path.split()

        if not parts:
            raise ValueError("Command path must not be empty.")

        def decorator(func: Handler):
            node = self.root

            for part in parts:
                node = node.children.setdefault(part, CommandNode())

            # if node.handler is not None:
            #     raise ValueError(f'Command "{path}" is already registered.')

            node.handler = func
            node.helptext = helptext
            node.argshelptext = argshelp
            self.__commands_list.append(f"{path}")
            self.__commands_help_list.append(f"{path:16} {argshelp:50} {helptext}")
            return func

        return decorator

    def resolve(self, argv: list[str]):
        """
        Resolve Command Tree, Return Handler

        Returns:
            (handler, remaining_args)
        """

        node = self.root
        index = 0

        while index < len(argv):
            child = node.children.get(argv[index])
            if child is None:
                break

            node = child
            index += 1

        return node.handler, argv[index:]
    
    def complete(self, argv: list[str], partial: str) -> list[str]:
        node = self.root

        for part in argv:
            child = node.children.get(part)
            if child is None:
                return []

            node = child

        return sorted(
            name
            for name in node.children
            if name.startswith(partial)
        )


    def print_help(self, argv: list[str]):
        if argv != []:
            if argv[0] == "--all":
                for c in self.__commands_help_list:
                    print(c)
                return
            node = self.root
            index = 0

            while index < len(argv):
                child = node.children.get(argv[index])
                if child is None:
                    break

                node = child
                index += 1

            path = " ".join(argv)
            print(f"{path}  {node.argshelptext}")
            print(node.helptext)
            return

        print("    ".join(self.__commands_list))


@dataclass
class PointDatum:
    pos: GridCoordinate
    is_cmpl: bool


class Context:
    def __init__(self):
        self.ironnest = IronNestBallisticCalc()
        self.ironnest.setpos(GridCoordinate.from_xy(0,0))
        self.pointdata: dict[str, PointDatum] = {}


registry = CommandRegistry()


class IronNestShell(cmd.Cmd):
    intro = f'Welcome to the IronNest Ballistic Calculator Shell.\nVersion {__semver__}.\nType help or ? to list commands.\n'
    prompt = '(IronNest) '
    def __init__(self, completekey: str = "tab", stdin: IO[str] | None = None, stdout: IO[str] | None = None) -> None:
        self.context = Context()
        super().__init__(completekey, stdin, stdout)

    
    def emptyline(self):
        return False

    # def precmd(self, line):
    #     line = line.lower()
    #     return line

    def default(self, line: str):
        argv = shlex.split(line)

        if not argv:
            return

        handler, args = registry.resolve(argv)

        if handler is None:
            print("Unknown command")
            return

        return handler(self, args)

    # def complete(self, text, line, begidx, endidx):
    #     parents = shlex.split(line[:begidx])
    #     return registry.complete(parents, text)
    def complete(self, text, state):
        pass
    def completedefault(self, *ignored: Any) -> list[str]:
        return super().completedefault(*ignored)


    def do_exit(self, arg):
        dat = self.context.pointdata
        with open("point.dat", "w") as fw:
            json.dump(dat, fw, default=support_myclass_default, indent=4, ensure_ascii=False)
        return True

    def do_version(self, arg):
        print(__version__)


    def do_help(self, arg):
        argv = shlex.split(arg)
        registry.print_help(argv)



@registry.command("mypos set", "<GridCordinate>", "Set Own IronNest Position")
def mypos_set(shell: IronNestShell, argv:list[str]):
    if len(argv) < 2:
        print("Not Enough arguments")
        return
    s1 = argv[0]
    s2 = argv[1]
    pos = GridCoordinate.from_grid(f"{s1} {s2}")
    shell.context.ironnest.setpos(pos)
    pdat = PointDatum(pos, False)
    shell.context.pointdata["@ironnest"] = pdat
    print(f"IronNest : {pos}")

@registry.command("mypos get", "", "Get Own IronNest Position")
def mypos_get(shell: IronNestShell, argv:list[str]):
    pos = shell.context.ironnest.ironnest
    print(f"IronNest : {pos}")


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
    # print(f"<DISTANCE> {distance}")
    # print(f"<AZIMUTH > {azimuth}")
    # print(f"<CHARGE  > {charge}")
    # print(f"<ANGLE   > {angle}")
    print(f"Target:{name:<5}    POINT:{pos.to_grid()}    DISTANCE:{p_distance:05.2f}    Charge:{charge}    ElevAngle:{p_angle:05.2f}    Azimuth:{p_azimuth:05.1f}")


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
    print(f"LEFT  CANNON:    Target:{name1:<5}    POINT:{pos.to_grid()}    DISTANCE:{p_distance:05.2f}    Charge:{charge}    ElevAngle:{p_angle:05.2f}    Azimuth:{p_azimuth:04.1f}")

    pos = pdat2.pos
    _, distance = SurveySolver.to_angle_distance(shell.context.ironnest.ironnest, pos)
    azimuth, angle, charge = shell.context.ironnest.fire(pos)
    p_distance = Decimal(str(distance)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    p_angle = Decimal(str(angle)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    p_azimuth = Decimal(str(azimuth)).quantize(Decimal("0.1"), ROUND_HALF_UP)
    print(f"RIGHT CANNON:    Target:{name2:<5}    POINT:{pos.to_grid()}    DISTANCE:{p_distance:05.2f}    Charge:{charge}    ElevAngle:{p_angle:05.2f}    Azimuth:{p_azimuth:04.1f}")

@registry.command("afire", "", "Calculate Aziuth, Elevation, Charge for Registerd All Position")
def fire_list(shell: IronNestShell, argv:list[str]):
    class fpos(NamedTuple):
        name : str
        pos : str
        distance: Decimal
        charge : int
        angle: Decimal
        azimuth: Decimal
    tl = []
    for name, pdat in shell.context.pointdata.items():
        if name.startswith("@"):
            continue
        if not name.startswith("a"):
            continue
        if pdat.is_cmpl:
            continue
        pos = pdat.pos
        _, distance = SurveySolver.to_angle_distance(shell.context.ironnest.ironnest, pos)
        azimuth, angle, charge = shell.context.ironnest.fire(pos)
        p_distance = Decimal(str(distance)).quantize(Decimal("0.01"), ROUND_HALF_UP)
        p_angle = Decimal(str(angle)).quantize(Decimal("0.01"), ROUND_HALF_UP)
        p_azimuth = Decimal(str(azimuth)).quantize(Decimal("0.1"), ROUND_HALF_UP)
        tl.append(fpos(name, pos.to_grid(), p_distance, charge, p_angle, p_azimuth))
    tl.sort(key=lambda x:x.azimuth)
    for t in tl:
        print(f"Target:{t.name:<5}    DISTANCE:{t.distance:05.2f}    Charge:{t.charge}    ElevAngle:{t.angle:05.2f}    Azimuth:{t.azimuth:04.1f}")




@registry.command("pos add", "<PointName> <GridCordinate>", "Registry GridCordinate for PointName")
def pos_add(shell: IronNestShell, argv:list[str]):
    if len(argv) < 3:
        print("Not Enough arguments")
        return
    name = argv[0]
    a1 = argv[1]
    a2 = argv[2]
    pos = f"{a1} {a2}"
    r = GridCoordinate.from_grid(pos)
    pdat = PointDatum(r, False)
    shell.context.pointdata[name] = pdat
    print(f"SaveAs {name} : {r.to_grid()}")

@registry.command("pos get", "<PointName>", "Get GridCordinate from PointName")
def pos_get(shell: IronNestShell, argv:list[str]):
    if len(argv) < 1:
        print("Not Enough arguments")
        return
    name = argv[0]
    r = shell.context.pointdata.get(name)
    if r is None:
        print(f"Not Found {name}")
        return
    print(f"{name} : {r.pos.to_grid()}")

@registry.command("pos del", "<PointName>", "Delete GridCordinate from PointName")
def pos_del(shell: IronNestShell, argv:list[str]):
    if len(argv) < 1:
        print("Not Enough arguments")
        return
    name = argv[0]
    if name in shell.context.pointdata:
        r = shell.context.pointdata.pop(name)
        print(f"Delete {name} : {r.pos.to_grid()}")
    else:
        print(f"Not Found {name}")


@registry.command("pos rename", "<BeforeName> <AfterName>", "Rename BeforeName to AfterName")
def pos_rename(shell: IronNestShell, argv:list[str]):
    if len(argv) < 2:
        print("Not Enough arguments")
        return
    name = argv[0]
    name2 = argv[1]
    if name in shell.context.pointdata:
        r = shell.context.pointdata.pop(name)
        shell.context.pointdata[name2] = r
        print(f"ReName from {name} to {name2}: {r.pos.to_grid()}")
    else:
        print(f"Not Found {name}")

@registry.command("pos list", "", "Registerd Postion List")
def pos_list(shell: IronNestShell, argv:list[str]):
    for name,r in shell.context.pointdata.items():
        if name.startswith("@"):
            continue
        color = "\033[37m"
        if name.startswith("s"):
            color = "\033[34m"
        if name.startswith(("a", "ac")):
            color = "\033[31m"
        if name.startswith(("r", "alpha", "bravo", "charile", "delta", "echo")):
            color = "\033[32m"
        text = f"{name:<5} : {r.pos.to_grid()}"
        s = f"{color}{text}\033[0m"
        print(s)


@registry.command("task list", "", "Task(position) List")
def task_list(shell: IronNestShell, argv:list[str]):
    for name,r in shell.context.pointdata.items():
        if not name.startswith("a"):
            continue
        # color = "\033[31m"
        if r.is_cmpl:
            color = "\033[32m"
            check = "X"
        else:
            color = "\033[31m"
            check = " "
        # check = "X" if r.is_cmpl else " "
        text = f"[{check}] {name:<5} : {r.pos.to_grid()}"
        s = f"{color}{text}\033[0m"
        print(s)

@registry.command("task flag", "<PointName>", "Flagged Task(Position) Item")
def task_check(shell: IronNestShell, argv:list[str]):
    if len(argv) < 1:
        print("Not Enough arguments")
        return
    name = argv[0]
    r = shell.context.pointdata.get(name)
    if r is None:
        print(f"Not Found {name}")
        return
    r.is_cmpl = True
    print(f"Flagged {name}")


@registry.command("task uflag", "<PointName>", "UnFlagged Task(Position) Item")
def task_uncheck(shell: IronNestShell, argv:list[str]):
    if len(argv) < 1:
        print("Not Enough arguments")
        return
    name = argv[0]
    r = shell.context.pointdata.get(name)
    if r is None:
        print(f"Not Found {name}")
        return
    r.is_cmpl = False
    print(f"Unflagged {name}")



@registry.command("two a", "<NewPointName> <PointName1> <Angle1> <PointName2> <Angle2>", "Calculate Position from Two Position and Angle")
def two_angles(shell: IronNestShell, argv:list[str]):
    if len(argv) < 5:
        print("Not Enough arguments")
        return
    name = argv[0]
    pname1 = argv[1]
    angle1 = float(argv[2])
    pname2 = argv[3]
    angle2 = float(argv[4])

    p1 = shell.context.pointdata.get(pname1)
    p2 = shell.context.pointdata.get(pname2)
    if p1 is None:
        print(f"Not Found {pname1}")
        return
    if p2 is None:
        print(f"Not Found {pname2}")
        return
    r = SurveySolver.from_two_angles(p1.pos, angle1, p2.pos, angle2)
    shell.context.pointdata[name] = PointDatum(r, False)
    print(f"{name} : {r.to_grid()}")

@registry.command("two d", "<NewPointName> <PointName1> <Distance1> <PointName2> <Distance2>", "Calculate Position from Two Position and Distance")
def two_distances(shell: IronNestShell, argv:list[str]):
    if len(argv) < 5:
        print("Not Enough arguments")
        return
    name = argv[0]
    pname1 = argv[1]
    distance1 = float(argv[2])
    pname2 = argv[3]
    distance2 = float(argv[4])

    p1 = shell.context.pointdata.get(pname1)
    p2 = shell.context.pointdata.get(pname2)
    if p1 is None:
        print(f"Not Found {pname1}")
        return
    if p2 is None:
        print(f"Not Found {pname2}")
        return

    r = SurveySolver.from_two_distances(p1.pos, distance1, p2.pos, distance2)
    for i,t in enumerate(r):
        if not t.is_valid():
            continue
        shell.context.pointdata[f"{name}-{i+1}"] = PointDatum(t, False)
        print(f"{name}-{i+1} : {t.to_grid()}")

@registry.command("two ad", "<NewPointName> <PointName1> <Angle1> <PointName2> <Distance2>", "Calculate Position from Two Positon and Angle, Distance")
def two_angle_distance(shell: IronNestShell, argv:list[str]):
    if len(argv) < 5:
        print("Not Enough arguments")
        return
    name = argv[0]
    pname1 = argv[1]
    angle1 = float(argv[2])
    pname2 = argv[3]
    distance2 = float(argv[4])

    p1 = shell.context.pointdata.get(pname1)
    p2 = shell.context.pointdata.get(pname2)
    if p1 is None:
        print(f"Not Found {pname1}")
        return
    if p2 is None:
        print(f"Not Found {pname2}")
        return

    r = SurveySolver.from_angle_and_distance(p1.pos, angle1, p2.pos, distance2)
    for i,t in enumerate(r):
        if not t.is_valid():
            continue
        shell.context.pointdata[f"{name}-{i+1}"] = PointDatum(t, False)
        print(f"{name}-{i+1} : {t.to_grid()}")

@registry.command("one", "<NewPointName> <PointName> <Angle> <Distance>", "Calculate Position from One Position and Angle, Distance")
def one_angle_distance(shell: IronNestShell, argv:list[str]):
    if len(argv) < 4:
        print("Not Enough arguments")
        return
    name = argv[0]
    pname1 = argv[1]
    angle1 = float(argv[2])
    distance2 = float(argv[3])

    p1 = shell.context.pointdata.get(pname1)
    if p1 is None:
        print(f"Not Found {pname1}")
        return

    r = SurveySolver.from_angle_distance(p1.pos, angle1, distance2)
    shell.context.pointdata[name] = PointDatum(r, False)
    print(f"{name} : {r.to_grid()}")

@registry.command("save", "[<FilaName>]", "Save to file Position List Data")
def savedata(shell: IronNestShell, argv:list[str]):
    print(argv)
    if len(argv) == 1:
        filename = argv[0]
    else:
        filename = "point.dat"
    with open(filename, "w") as fw:
        print(f"Save {filename} ...")
        dat = shell.context.pointdata
        json.dump(dat, fw, default=support_myclass_default, indent=4, ensure_ascii=False)
    print("Save")


@registry.command("load", "[<FileName>]", "Load Position List Data from file")
def loaddata(shell: IronNestShell, argv:list[str]):
    if len(argv) == 1:
        filename = argv[0]
    else:
        filename = "point.dat"
    p_file = Path(filename)
    if not p_file.exists():
        print(f"Not Found {filename}. Load File Abort")
        return
    with p_file.open("r") as f:
        print(f"Load {filename} ...")
        table = json.load(f)
        pos = table.get("@ironnest")
        if pos is not None:
            if isinstance(pos, dict):
                shell.context.ironnest.setpos(GridCoordinate.from_xy(pos["x"], pos["y"]))
            elif isinstance(pos, str):
                shell.context.ironnest.setpos(GridCoordinate.from_grid(pos))
            
        for name, pos in table.items():
            if isinstance(pos, dict):
                shell.context.pointdata[name] = PointDatum(GridCoordinate.from_xy(pos["x"], pos["y"]), pos["is_cmpl"])
            elif isinstance(pos, str):
                shell.context.pointdata[name] = PointDatum(GridCoordinate.from_grid(pos),False)
            else:
                print(f"Invalid Format {name}")
    print("Load Complete")



@registry.command("map", "", "Mapping Position Data in Terminal")
def maprender(shell: IronNestShell, argv:list[str]):
    @dataclass
    class Cell:
        char: str = " "
        color: str = ""
    
    # pos_list(shell, [])

    WIDTH = 20
    HEIGHT = 10
    CELL_WIDTH = 7

    grid = [[Cell() for _ in range(WIDTH)] for _ in range(HEIGHT)]

    for name, pdat in shell.context.pointdata.items():
        x, y = pdat.pos.to_areapos()
        color = "\033[37m"
        if name.startswith("@"):
            color = "\033[33m"
        if name.startswith("s"):
            color = "\033[34m"
        if name.startswith(("a", "ac")):
            color = "\033[31m"
        if name.startswith(("r", "alpha", "bravo", "charile", "delta", "echo")):
            color = "\033[32m"
        if pdat.is_cmpl:
            continue
        grid[y][x] = Cell(name[:5], color)
                #  30	黒色
                #  31	赤色
                #  32	緑色
                #  33	黄色
                #  34	青色
                #  35	マゼンタ
                #  36	シアン
                #  37	白色
    
    grid.reverse()

    border = "+" + "+".join("-" * CELL_WIDTH for _ in range(WIDTH+1)) + "+"
    grid_header = []
    for i in range(1, WIDTH+1):
        grid_header.append(Cell(chr(65+i-1)))
    grid.insert(0, grid_header)
    for row in range(HEIGHT+1):
        if row == 0:
            grid[row].insert(0, Cell("#"))
            continue
        grid[row].insert(0, Cell(str(HEIGHT-row)))

    lines = []
    for row in grid:
        body = "|"
        for cell in row:
            text = cell.char.center(CELL_WIDTH)
            if cell.color:
                text = f"{cell.color}{text}\033[0m"
            body += text + "|"
        lines.append(body)
        lines.append(border)

    print("\n".join(lines))



def support_myclass_default(o):
    if isinstance(o, GridCoordinate):
        x,y = o.to_xy()
        return {"x":x, "y":y}
    if isinstance(o, PointDatum):
        return {"is_cmpl": o.is_cmpl, "x":o.pos.posx, "y":o.pos.posy}
    raise TypeError(repr(o) + " is not JSON serializable")


if __name__ == '__main__':
    import traceback
    ironnestshell = IronNestShell()
    # ironnestshell.cmdqueue.append("load")
    # ironnestshell.cmdqueue.append("map")
    try:
        ironnestshell.cmdloop()
    except KeyboardInterrupt:
        print("Exiting ...")
        pass
    except Exception as e:
        print(e)
        print(traceback.format_exc())
    finally:
        dat = ironnestshell.context.pointdata
        with open("point.dat", "w") as fw:
            json.dump(dat, fw, default=support_myclass_default, indent=4, ensure_ascii=False)
        print("Save File Complete")

