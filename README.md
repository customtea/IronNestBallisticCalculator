# IronNest Ballistic Calclator

## Usage
- StartShell
  - `py main.py`

```
py main.py
Welcome to the IronNest Ballistic Calculator Shell.
Version 0.1.0.
Type help or ? to list commands.

(IronNest) version
IronNest Ballistic Calculator ver:0.1.0 Created By customtea (https://github.com/customtea/)
(IronNest) help
mypos set    mypos get    fire    dfire    afire    pos add    pos get    pos del    pos rename    pos list    task list    task flag    task uflag    two a    two d    two ad    one    save    load    map   
(IronNest) help --all
mypos set        <GridCordinate>                                    Set Own IronNest Position
mypos get                                                           Get Own IronNest Position
fire             <PointName>                                        Calculate Aziuth, Elevation, Charge to PointName
dfire            <PointName1> <PointName2>                          Calculate Aziuth, Elevation, Charge to Two PointName. For Double Cannon
afire                                                               Calculate Aziuth, Elevation, Charge for Registerd All Position
pos add          <PointName> <GridCordinate>                        Registry GridCordinate for PointName
pos get          <PointName>                                        Get GridCordinate from PointName
pos del          <PointName>                                        Delete GridCordinate from PointName
pos rename       <BeforeName> <AfterName>                           Rename BeforeName to AfterName
pos list                                                            Registerd Postion List
task list                                                           Task(position) List
task flag        <PointName>                                        Flagged Task(Position) Item
task uflag       <PointName>                                        UnFlagged Task(Position) Item
two a            <PointName1> <Angle1> <PointName2> <Angle2>        Calculate Position from Two Position and Angle
two d            <PointName1> <Distance1> <PointName2> <Distance2>  Calculate Position from Two Position and Distance
two ad           <PointName1> <Angle1> <PointName2> <Distance2>     Calculate Position from Two Positon and Angle, Distance
one              <PointName> <Angle> <Distance>                     Calculate Position from One Position and Angle, Distance
save             [<FilaName>]                                       Save to file Position List Data
load             [<FileName>]                                       Load Position List Data from file
map                                                                 Mapping Position Data in Terminal
(IronNest)
```
