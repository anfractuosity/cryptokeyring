import Draft
import numpy as np
import Part
import ProfileLib.RegularPolygon
from FreeCAD import Base
from PIL import Image

def test(image, outputprefix, drillA=True):
    img = Image.open(image)
    img = img.convert('L')
    image = np.array(img) > 0
    image = np.swapaxes(image, 0, 1)

    doc = FreeCAD.newDocument()
    myPart = doc.addObject("Part::Feature","myPartName")
    off = 2
    dim = 1

    rheight = 80
    rwidth = 30
    scale = 1.5
    height = int((rheight) * scale)
    width = int((rwidth) * scale)

    arr = np.full((height, width), False, dtype=bool)
    for y in range(height):
        arr[y][width // 2] = True
    arr = image

    np.random.seed(1)
    arr2 = np.random.randint(2, size=(height, width)) > 0

    A = np.full((2, 2), False, dtype=bool)
    A[0][0] = True
    A[1][1] = True

    B = np.full((2, 2), False, dtype=bool)
    B[0][1] = True
    B[1][0] = True

    thick = 2
    off = 0 #0.15 + 3
    cube = FreeCAD.ActiveDocument.addObject("Part::Feature", "myCube")
    cube.Shape = Part.makeBox(rheight - (2*(((1/(height)) * rheight))) + (off), rwidth - (2*(((1/(width)) * rwidth))) + (off), thick)

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

    for y in range(0,height,1):
        for x in range(0,width,1):

            if x < 3 or x >= width - 3 - 1:
                continue

            if y < 12 or y >= height - 3 - 1:
                continue

            color = arr[y][x]
            choice = arr2[y][x]
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
                SocketSketch.addGeometry(Part.Circle(App.Vector(((y/(height)) * rheight) + (off/2), ((x/(width)) * rwidth) + (off/2), 0), App.Vector(0,0,1), 0.2),False)

    SocketSketch.addGeometry(Part.Circle(App.Vector(4, (rwidth - (2*(((1/(width)) * rwidth))) + (off)) / 2, 0), App.Vector(0,0,1), 1.5),False)

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