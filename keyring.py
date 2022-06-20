import Draft
import numpy as np
import Part
import ProfileLib.RegularPolygon
from FreeCAD import Base
from PIL import Image

def test(image, outputprefix, drillA=True):
    rheight = 80
    rwidth = 30
    thick = 2

    x0 = 2
    y0 = 12
    x1 = rwidth - 2
    y1 = rheight - 2

    h1 = y1 - y0
    w1 = x1 - x0

    hole = 0.17
    scale = 2.0

    height = int((y1 - y0)*scale)
    width = int((x1 - x0)*scale)

    img = Image.open(image)
    img = img.convert('L')
    arr = np.array(img) > 0
    arr = np.swapaxes(arr, 0, 1)

    iwidth = (width // 2) + 1
    iheight = (height // 2) + 1
    print(f"Please use image of size - {iwidth}x{iheight}")

    np.random.seed(1)
    arr2 = np.random.randint(2, size=(iheight, iwidth)) > 0

    doc = FreeCAD.newDocument()
    myPart = doc.addObject("Part::Feature","myPartName")

    A = np.full((2, 2), False, dtype=bool)
    A[0][0] = True
    A[1][1] = True

    B = np.full((2, 2), False, dtype=bool)
    B[0][1] = True
    B[1][0] = True

    cube = FreeCAD.ActiveDocument.addObject("Part::Feature", "myCube")
    cube.Shape = Part.makeBox(rheight, rwidth, thick)

    chmfr = FreeCAD.ActiveDocument.addObject("Part::Fillet", "myChamfer")
    chmfr.Base = FreeCAD.ActiveDocument.myCube
    myEdges = []

    for i in range(1, 12+1):
        myEdges.append((i, 0.35, 0.325)) # (edge number, chamfer start length, chamfer end length)

    chmfr.Edges = myEdges
    FreeCADGui.ActiveDocument.myCube.Visibility = False
    FreeCAD.ActiveDocument.recompute()

    doc.addObject('PartDesign::Body','Body001')
    SocketSketch = doc.Body001.newObject('Sketcher::SketchObject','SketchHole0')
    SocketSketch.Support = (chmfr,["Face14"])
    SocketSketch.MapMode = 'FlatFace'
    doc.recompute()

    for y in range(0, height+1):
        for x in range(0, width+1):
            color = arr[y//2][x//2]
            choice = arr2[y//2][x//2]
            x_ = x % 2
            y_ = y % 2

            if choice:
                drill = A[y_][x_]
            else:
                drill = B[y_][x_]

            if not color:
                drilla = drill
                drillb = not drill
            else:
                drilla = drill
                drillb = drill

            if (drillA and drilla) or ((not drillA) and drillb):
                y_ = y0 + ((y/height)*h1)
                x_ = x0 + ((x/width)*w1)
                SocketSketch.addGeometry(Part.Circle(App.Vector(y_, x_, 0), App.Vector(0,0,1), hole), False)

    SocketSketch.addGeometry(Part.Circle(App.Vector(4, rwidth / 2, 0), App.Vector(0,0,1), 1.5),False)

    pocket = doc.Body001.newObject("PartDesign::Pocket","Pocket0")
    pocket.Profile = SocketSketch
    pocket.Length = 5.0
    Gui.activeDocument().hide("SketchHole0")
    doc.recompute()

    Gui.activeDocument().hide("SketchHole")
    Gui.activeDocument().hide("myPartName")
    Gui.activeDocument().hide("myChamfer")
    doc.recompute()

    state = "A" if drillA else "B"
    doc.saveAs(f"{outputprefix}-{state}.FCStd")

test("imgs/test.png", "key", drillA=True)
test("imgs/test.png", "key", drillA=False)