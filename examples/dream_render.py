#!/usr/bin/env python3
import os
import libfurc.dream
import libfurc.fox5
from PIL import Image
from PIL import ImageShow
from PIL import ImageDraw

ImageShow.register(ImageShow.DisplayViewer, 0)

patchIndices = {
    "items": [
        ("items.fox", 0, 1799),
        ("portals.fox", 1800, 1999),
        ("portalse.fox", 2000, 2399),
        ("iteme.fox", 2400, 3399)
    ],
    "floors": [
        ("floors.fox", 0, 499),
        ("floore.fox", 500, 999)
    ],
    "walls": [
        ("wall.fox", 0, 23),
        ("wall_3.fox", 24, 35),
        ("wall_4.fox", 36, 47),
        ("wall_5.fox", 48, 59),
        ("wall_6.fox", 60, 71),
        ("wall_7.fox", 72, 83),
        ("wall_8.fox", 84, 95),
        ("wall_9.fox", 96, 107),
        ("wall_10.fox", 108, 119),
        ("wall_11.fox", 120, 131),
        ("wall_12.fox", 132, 143),
        ("wall_13.fox", 144, 155),
        ("wall_14.fox", 156, 167),
        ("wall_15.fox", 168, 179)
    ],
    "effects": [
        ("effects.fox", 0, 199),
        ("effectse.fox", 200, 999)
    ],
    "regions": [
        ("regions.fox", 0, 200),
    ],
    "ambience": [
        ("ambience.fox", 0, 199),
        ("ambiencee.fox", 200, 299)
    ],
    "lighting": [
        ("lighting.fox", 0, 199),
        ("lightinge.fox", 200, 299)
    ],
    "junctions": [
        ("junction.fox", 0, 31)
    ]
}

#This expression is complicated, but all it does is:
#for entry in patchIndices[*][i]: yield entry[0]
#renderables = list(set([a for b in [[i[0] for i in v] for k,v in patchIndices.items()] for a in b]))

#FIXME: This only renders the first frame. Should parse the kitterspeak
def getPatch(patches, t, i, direction = None):
    im = Image.new("RGBA", (32,32), color=(0,0,0,0))
    if t in patches and i in patches[t]:
        obj = patches[t][i]
        for shape in obj.children:
            #Default, Floor, Item, Portals
            if shape["Purpose"] in [0, 21, 22, 29]:
                for frame in shape.children:
                    for sprite in frame.children:
                        if sprite["Image"] and sprite["Image"] != 0:
                            im = obj.parent.properties["ImageList"][sprite["Image"] - 1].toPIL()
                            pos = frame["FrameOffset"] or (0,0)
                            pos2 = sprite["Offset"] or (0,0)
                            return im, (pos[0] + pos2[0], pos[1] + pos2[1])
            
            #Walls
            elif shape["Purpose"] == 23:
                if direction != None and shape["Direction"] != direction:
                    continue
                for frame in shape.children:
                    for sprite in frame.children:
                        if sprite["Image"] and sprite["Image"] != 0:
                            im = obj.parent.properties["ImageList"][sprite["Image"] - 1].toPIL()
                            pos = frame["FrameOffset"] or (0,0)
                            pos2 = sprite["Offset"] or (0,0)
                            return im, (pos[0] + pos2[0], pos[1] + pos2[1])
            
            #Skipping regions(24), effects(25)
    
    return None, (0,0)

def loadPatch(patchName, folders, startId = 0):
    result = {}
    for folder in folders:
        path = os.path.join(folder, patchName)
        if os.path.isfile(path):
            print("Loading", path)
            fox = libfurc.fox5.load(path)
            lastObjectId = 0
            lastImageId = 0
            for obj in fox.body.children:
                oid = obj["ID"]
                if not oid or oid == -1:
                    oid = lastObjectId + 1
                
                for shape in obj.children:
                    for frame in shape.children:
                        for sprite in frame.children:
                            if sprite["Image"] == None:
                                sprite["Image"] = lastImageId + 1
                            
                            lastImageId = sprite["Image"]
                result[startId + oid] = obj
                lastObjectId = oid
    return result

TILE_WIDTH = 62
TILE_HEIGHT = 32
def renderDream(dream, patches, pos, size = None):
    #testTile = Image.open("testtile.png")
    if size == None:
        size = (448, 256)
    
    im = Image.new("RGB", size)
    
    #Try divide render size by tile size
    renderOffset = (
        int(size[0] / TILE_WIDTH / 2 - 0.5),
        int(size[1] / TILE_HEIGHT / 2) + 3
    )
    
    
    #if not tile: #Debugger
    #    tile = testTile.copy()
    #    draw = ImageDraw.Draw(tile)
    #    draw.text((10, 10), "{},{}={}".format(*tilePos,dream.floors[tilePos]), fill=(0,0,0,255))
    for y in range(-1, int(size[1] + 1)):
        for x in range(-1, int((size[0]/TILE_WIDTH) + 1)):
            #TODO: Additive offset
            tilePos = pos[0]-renderOffset[0]+x, pos[1]-renderOffset[1]+y
            if not 0 < tilePos[0] < dream.width:
                continue
            if not 0 < tilePos[1] < dream.height:
                continue
            #Floors
            tid = dream.floors[tilePos]
            if tid == 0:
                tid = 1
            tile, offset2 = getPatch(patches, "floors", tid)
            
            if tile:
                offset = [0,0]
                if (y & 1) == 0:
                    offset[0] += TILE_WIDTH/2
                    offset[0] += 1
                
                offset[0] += (x * (TILE_WIDTH + 2))
                offset[1] += (y * (TILE_HEIGHT / 2))
                im.paste(tile, [int(offset[0]), int(offset[1])], tile)
        
            #Render walls
            for i in range(2):
                wallPos = (
                    ((pos[0]-renderOffset[0]+x)) * 2 + i,
                    pos[1]-renderOffset[1]+y
                )
                
                tile, offset2 = None, None
                
                #this is horrible
                tid = dream.walls[wallPos]
                if tid == 1 or tid == 3:
                    tile, offset2 = getPatch(patches, "junctions", 10 if i == 0 else 7)
                elif tid == 2:
                    tile, offset2 = getPatch(patches, "junctions", 9 if i == 0 else 5)
                elif tid == 13 or tid == 15:
                    tile, offset2 = getPatch(patches, "junctions", 25 if i == 0 else 22)
                elif tid == 14:
                    tile, offset2 = getPatch(patches, "junctions", 24 if i == 0 else 20)
                elif tid > 0:
                    if tid > 3:
                        tid -= 4
                    if tid > 15:
                        tid -= 3
                    tile, offset2 = getPatch(patches, "walls", tid, 9 if i == 0 else 7)
                if tile:
                    offset = [offset2[0], offset2[1] - (TILE_HEIGHT * 2)]
                    if (y & 1) == 0:
                        offset[0] += TILE_WIDTH/2
                        offset[0] += 1
                    
                    if i == 1:
                        offset[0] += TILE_WIDTH/4
                        offset[1] -= TILE_HEIGHT/4
                    else:
                        offset[0] -= TILE_WIDTH/4
                        offset[1] -= TILE_HEIGHT/4
                    
                    offset[0] += (x * (TILE_WIDTH + 2))
                    offset[1] += (y * (TILE_HEIGHT / 2))
                    im.paste(tile, [int(offset[0]), int(offset[1])], tile)
            
            #Render objects
            tile, offset2 = getPatch(patches, "items", dream.items[tilePos])
            
            if tile:
                offset = [offset2[0], offset2[1] - (TILE_HEIGHT * 2)]
                if (y & 1) == 0:
                    offset[0] += TILE_WIDTH/2
                    offset[0] += 1
                
                offset[0] += (x * (TILE_WIDTH + 2))
                offset[1] += (y * (TILE_HEIGHT / 2))
                im.paste(tile, [int(offset[0]), int(offset[1])], tile)
    
    #im.resize((size[0]*3, size[1]*3), resample=0).show()
    im.show()


if __name__ == "__main__":
    dream = libfurc.dream.load("default.map")
    patchFolders = [
        "/home/felix/.wine/drive_c/Program Files/Furcadia/patches/default/",
        os.getcwd()
    ]
    
    patches = {
        "floors": {},
        "items": {},
        "walls": {},
        "effects": {},
        "regions": {},
        "ambience": {},
        "lighting": {},
        "junctions": {}
    }
    for patch in patchIndices:
        for file, start, end in patchIndices[patch]:
            patches[patch].update(loadPatch(file, patchFolders, start))
    renderDream(dream, patches, (10,21))

