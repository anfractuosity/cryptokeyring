import argparse
import sys

import importDXF
import numpy as np
import Part
import ProfileLib.RegularPolygon
from FreeCAD import Base
from PIL import Image, ImageOps


def test(image, outputprefix, drillA=True):
    img = Image.open(image)
    img = img.convert('L')
    img = ImageOps.flip(img)

    arr = np.array(img) > 0
    arr = np.swapaxes(arr, 0, 1)

    hole = 0.3 # Radius of hole
    gap = 0.5  # Gap between holes
    yborder = 4
    xborder = 2

    rheight = (arr.shape[0] * 2 * ((hole*2)+gap))
    rwidth = (arr.shape[1] * 2 * ((hole*2)+gap))
    thick = 1

    height = arr.shape[0] * 2
    width = arr.shape[1] * 2

    np.random.seed(1)
    arr2 = np.random.randint(2, size=(height, width)) > 0

    doc = FreeCAD.newDocument()
    myPart = doc.addObject("Part::Feature","myPartName")

    A = np.full((2, 2), False, dtype=bool)
    A[0][0] = True
    A[1][1] = True

    B = np.full((2, 2), False, dtype=bool)
    B[0][1] = True
    B[1][0] = True

    kheight = rheight + yborder + (xborder/2)
    kwidth = rwidth + xborder
    print(f"{kheight},{kwidth}")
    cube = doc.addObject("Part::Feature", "myCube")
    cube.Shape = Part.makeBox(kheight, kwidth, thick)

    chmfr = doc.addObject("Part::Fillet", "myChamfer")
    chmfr.Base = doc.myCube
    myEdges = []
    for i in range(1, 12+1):
        myEdges.append((i, 0.35, 0.325)) # (edge number, chamfer start length, chamfer end length)

    chmfr.Edges = myEdges
    doc.myCube.Visibility = False
    doc.recompute()

    SocketSketch = doc.addObject('Sketcher::SketchObject','SketchHole0')
    SocketSketch.Support = (chmfr, ["Face14"])
    SocketSketch.MapMode = 'FlatFace'
    doc.recompute()

    for y in range(0, height):
        for x in range(0, width):
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
                y_ = hole + ((y/height) * rheight) + yborder
                x_ = (((x+0.5)/width) * rwidth) + (xborder/2)
                SocketSketch.addGeometry(Part.Circle(App.Vector(y_, x_, 0), App.Vector(0,0,1), hole), False)
    SocketSketch.addGeometry(Part.Circle(App.Vector(yborder / 2, kwidth / 2, 0), App.Vector(0,0,1), 1.3),False)
    pocket = doc.addObject("PartDesign::Pocket","Pocket0")
    pocket.Profile = SocketSketch
    pocket.Length = 10

    Gui.activeDocument().hide("SketchHole0")
    Gui.activeDocument().hide("myPartName")
    Gui.activeDocument().hide("myChamfer")
    doc.recompute()

    state = "A" if drillA else "B"
    doc.saveAs(f"{outputprefix}-{state}.FCStd")
    importDXF.export([pocket], f"{outputprefix}-{state}.dxf")
    Gui.activeDocument().activeView().setCameraOrientation(App.Rotation(90, 0, 0))
    Gui.activeDocument().activeView().fitAll()

if len(sys.argv) == 4:
    image = sys.argv[2]
    output = sys.argv[3]
    print(f"""Using image "{image}" and output prefix "{output}".""")
    test(image, output, drillA=True)
    test(image, output, drillA=False)
else:
    print("Please use: freecad keyring.py image_path output_prefix")
