#!/usr/bin/env python3
import struct

class TileAccessor:
    def __init__(self, dream, target, walls = False):
        self.dream = dream
        self.target = target
    
    def __getitem__(self, key):
        if type(key) == int:
            return getattr(self.dream, self.target)[key]
        elif type(key) == tuple and len(key) == 2:
            return getattr(self.dream, self.target)[self.dream.coordinateToIndex(key[0], key[1])]
        else:
            raise ValueError("Unsupported accessor")

    def __setitem__(self, key, value):
        if type(key) == int:
            getattr(self.dream, self.target)[key] = value
        elif type(key) == tuple and len(key) == 2:
            getattr(self.dream, self.target)[self.dream.coordinateToIndex(key[0], key[1])] = value
        else:
            raise ValueError("Unsupported accessor")

class NullAccessor:
    def __init__(self, dream, target, walls = False):
        self.dream = dream
        self.target = target
    
    def __getitem__(self, key):
        return 0

    def __setitem__(self, key, value):
        return 0



sUInt16 = struct.Struct("<H")
sUInt8 = struct.Struct("<B")

DreamTypeCast = {
    'width': int,
    'height': int,
    'revision': int,
    'encoded': bool,
    'patcht': bool,
    'sfxlayermode': str,
    'sfxopacity': int,
    'name': str,
    'patchs': str,
    'noload': bool,
    'allowjs': bool,
    'allowlf': bool,
    'allowfurl': bool,
    'allowshouts': bool,
    'allowlarge': bool,
    'swearfilter': bool,
    'nowho': bool,
    'forcesittable': bool,
    'notab': bool,
    'nonovelty': bool,
    'rating': str,
    'allow32bitart': bool,
    'ismodern': bool,
    'parentalcontrols': bool
}

class Dream:
    def __init__(self, version = 1.5, **parameters):
        self.properties = {}
        for parameter in parameters:
            if parameter.lower() not in DreamTypeCast:
                raise ValueError("Unknown parameter {}".format(parameter))
            self.properties[parameter.lower()] = DreamTypeCast[parameter.lower()](parameters[parameter])
        
        #Version 100 only supports a static size
        if version == 1.0:
            self.width = 52
            self.height = 100
        
        cells = self.width * self.height
        self._floors = [0] * cells
        self._items = [0] * cells
        self._walls = [0] * cells * 2
        
        self.floors = TileAccessor(self, "_floors")
        self.items = TileAccessor(self, "_items")
        self.walls = TileAccessor(self, "_walls", True)
        
        self._regions = None
        self._effects = None
        
        if version > 1.30:
            self._regions = [0] * cells
            self._effects = [0] * cells
            self.regions = TileAccessor(self, "_regions")
            self.effects = TileAccessor(self, "_effects")
        
        self._lighting = None
        self._ambient = None
        
        if version > 1.50:
            self._lighting = [0] * cells
            self._ambient = [0] * cells
            self._lighting = TileAccessor(self, "_lighting")
            self._ambient = TileAccessor(self, "_ambient")
    
    def coordinateToIndex(self, x, y):
        return (self.height * x) + y
    
    def __getitem__(self, key):
        self.properties[key]

    def __setitem__(self, key, value):
        if parameter.lower() not in DreamTypeCast:
            print("[WARN] Unknown dream parameter {}".format(parameter))
        self.properties[key] = value
    
    @property
    def width(self):
        return self.properties["width"]
    
    @width.setter
    def width(self, value):
        self.properties["width"] = value
    
    @property
    def height(self):
        return self.properties["height"]
    
    @height.setter
    def height(self, value):
        self.properties["height"] = value
    
    @classmethod
    def fromStream(cls, handle):
        header = b""
        while True:
            b = handle.read(1)
            if b == b"\n":
                break
            header += b
        
        if header[0:5] != b"MAP V":
            raise ValueError("Not a map file!")
        
        if header[-9:] != b" Furcadia":
            raise ValueError("Not a map file!")
        
        version = float(header[5:-9])
        
        parameters = {}
        while True:
            param = b""
            while True:
                b = handle.read(1)
                if b == b"\n":
                    break
                param += b
            
            if param == B"BODY":
                break
            
            key, value = param.decode().split("=", 1)
            parameters[key] = value
        
        width, height = int(parameters["width"]), int(parameters["height"])
        
        dream = cls(**parameters, version = version)
        for i in range(0, width*height):
            dream._floors[i], = sUInt16.unpack(handle.read(2))
        
        for i in range(0, width*height):
            dream._items[i], = sUInt16.unpack(handle.read(2))
        
        for i in range(0, width*height*2):
            dream._walls[i], = sUInt8.unpack(handle.read(1))
        
        if version > 1.30:
            for i in range(0, width*height):
                dream._regions[i], = sUInt16.unpack(handle.read(2))
            for i in range(0, width*height):
                dream._effects[i], = sUInt16.unpack(handle.read(2))
        
        if version > 1.50:
            for i in range(0, width*height):
                dream._lighting[i], = sUInt16.unpack(handle.read(2))
            for i in range(0, width*height):
                dream._ambient[i], = sUInt16.unpack(handle.read(2))
        
        return dream

def load(path):
    with open(path, "rb") as f:
        return Dream.fromStream(f)

def loads(data):
    return Dream.fromStream(io.BytesIO(data))

def dump(dream, path):
    with open(path, "wb") as f:
        return f.write(bytes(dream))

def dumps(dream):
    return bytes(dream)

