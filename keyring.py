import math
import random
import sys

import importDXF
import numpy as np
import FreeCAD
import FreeCAD as App
import FreeCADGui as Gui
import Part
from PIL import Image, ImageOps


def readbits(file, count):
    with open(file, "rb") as f:
        bits = []
        data = f.read(math.ceil(count / 8))
        for b in data:
            for i in range(8):
                bits += [b & 1]
                b >>= 1
                if len(bits) == count:
                    break
        return bits


def test(image, outputprefix, keyfile=None, drillA=True):
    img = Image.open(image)
    img = img.convert('L')
    img = ImageOps.flip(img)
    img = np.array(img) > 0
    img = np.swapaxes(img, 0, 1)

    hole = 0.3  # Radius of hole
    gap = 0.5   # Gap between holes
    yborder = 4
    xborder = 2
    h = img.shape[0]
    w = img.shape[1]
    rheight = h * 2 * ((hole*2)+gap)
    rwidth = w * 2 * ((hole*2)+gap)
    thick = 1

    if keyfile is None:
        random.seed(1)
    else:
        randbits = np.reshape(readbits(keyfile, h * w), (h, w))

    doc = FreeCAD.newDocument()
    # patterns = [(0, 0, 1, 1), (1, 1, 0, 0), (1, 0, 1, 0), (0, 1, 0, 1), (1, 0, 0, 1), (0, 1, 1, 0)]
    patterns = [(1, 0, 0, 1), (0, 1, 1, 0)]
    kheight = rheight + yborder + (xborder / 2)
    kwidth = rwidth + xborder

    print(f"{kheight},{kwidth}")
    cube = doc.addObject("Part::Feature", "myCube")
    cube.Shape = Part.makeBox(kheight, kwidth, thick)

    chmfr = doc.addObject("Part::Fillet", "myChamfer")
    chmfr.Base = doc.myCube
    myEdges = []
    for i in range(1, 12+1):
        myEdges.append((i, 0.35, 0.325))  # (edge number, chamfer start length, chamfer end length)

    chmfr.Edges = myEdges
    doc.myCube.Visibility = False
    doc.recompute()

    SocketSketch = doc.addObject('Sketcher::SketchObject', 'SketchHole0')
    SocketSketch.Support = (chmfr, ["Face14"])
    SocketSketch.MapMode = 'FlatFace'
    doc.recompute()

    for y in range(0, h):
        for x in range(0, w):
            color = img[y][x]
            if keyfile is None:
                val = np.reshape(random.choice(patterns), (2, 2)) > 0
            else:
                val = np.reshape(patterns[randbits[y][x]], (2, 2)) > 0
            if not drillA and not color:
                val = np.invert(val)
            for y_1 in range(2):
                for x_1 in range(2):
                    y_ = ((((y*2) + y_1 + 0.5) / (h*2)) * rheight) + yborder
                    x_ = ((((x*2) + x_1 + 0.5) / (w*2)) * rwidth) + (xborder/2)
                    drillit = val[y_1][x_1]
                    if drillit:
                        SocketSketch.addGeometry(Part.Circle(App.Vector(y_, x_, 0), App.Vector(0, 0, 1), hole), False)

    SocketSketch.addGeometry(Part.Circle(App.Vector(yborder / 2, kwidth / 2, 0), App.Vector(0, 0, 1), 1.3), False)
    pocket = doc.addObject("PartDesign::Pocket", "Pocket0")
    pocket.Profile = SocketSketch
    pocket.Length = 10

    Gui.activeDocument().hide("SketchHole0")
    Gui.activeDocument().hide("myChamfer")
    doc.recompute()

    state = "A" if drillA else "B"
    doc.saveAs(f"{outputprefix}-{state}.FCStd")

    # Following is used to simplify outline of keyring
    # so where to laser cut edge is more clear
    wires=list()
    shape = pocket.Shape
    for i in shape.slice(App.Vector(0,0,1),0.5):
        wires.append(i)
    comp=Part.Compound(wires)
    sliceit=doc.addObject("Part::Feature","Pocket0_cs")
    sliceit.Shape=comp
    sliceit.purgeTouched()

    importDXF.export([sliceit], f"{outputprefix}-{state}.dxf")
    pocket.Shape.exportStl(f"{outputprefix}-{state}.stl")
    Gui.activeDocument().activeView().setCameraOrientation(App.Rotation(90, 0, 0))
    Gui.activeDocument().activeView().fitAll()


if len(sys.argv) == 4 or len(sys.argv) == 5:
    image = sys.argv[2]
    output = sys.argv[3]
    keyfile = None
    if len(sys.argv) == 5:
        keyfile = sys.argv[4]
    print(f"""Using image "{image}" and output prefix "{output}".""")
    test(image, output, keyfile=keyfile, drillA=True)
    test(image, output, keyfile=keyfile, drillA=False)
else:
    print("Please use: freecad keyring.py image_path output_prefix")
    print("Or        : freecad keyring.py image_path output_prefix key_file")
