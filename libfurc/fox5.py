#!/usr/bin/env python3
try:
    from PIL import Image, ImageDraw, ImageOps
except ModuleNotFoundError:
    pass

try:
    from libfurc.crypto.fox5 import Fox5Cipher
    haveCrypto = True
except ModuleNotFoundError:
    haveCrypto = False

import io
import lzma
import struct
import random

sUInt64 = struct.Struct("<Q")
def Compress(data):
    compressed = lzma.compress(data, format=lzma.FORMAT_ALONE)
        
    compressed = compressed[:5] + sUInt64.pack(len(data)) + compressed[13:]
    return compressed

def Decompress(data):
    return lzma.decompress(data, format=lzma.FORMAT_ALONE)
    
class Fox5Error(Exception):
    pass

class Fox5Image:
    def __init__(self, width = 0, height = 0, format = 0, data = None, compressed = False):
        self.width = width
        self.height = height
        self.format = format
        self.__data__ = data
        self.compressed = compressed
    
    def __repr__(self):
        return "<{} Width={}; Height={}; Format={}>".format(self.__class__.__name__, self.width, self.height, self.format)
    
    def __len__(self):
        return len(self.__data__)
    
    @property
    def data(self):
        return self.__data__
    
    @data.setter
    def data(self, value):
        self.__data__ = value
        self.compressed = False
    
    def compress(self):
        if not self.compressed:
            self.data = Compress(self.data)
            self.compressed = True
        return self.data
    
    def decompress(self):
        if self.compressed:
            self.data = Decompress(self.data)
            self.compressed = False
        return self.data
    
    @classmethod
    def fromPIL(cls, im):
        data = b""
        for pixel in im.getdata():
            data += bytes((pixel[3], pixel[0], pixel[1], pixel[2]))
        
        return cls(im.width, im.height, 1, data, False)
    
    def toPIL(self):
        self.decompress()
        if self.format == 1:
            return Image.frombytes('RGBA', (self.width, self.height), self.data, "raw", "ARGB")
        elif self.format == 2:
            return Image.frombytes('L', (self.width, self.height), self.data)

sList = struct.Struct(">BI")
sUInt8 = struct.Struct(">B")
sUInt16 = struct.Struct(">H")
sInt16 = struct.Struct(">h")
sUInt32 = struct.Struct(">I")
sInt32 = struct.Struct(">i")
sImageList = struct.Struct(">IHHB")

class Fox5List(object):
    __properties__ = ()
    __childtype__ = None
    properties = {}
    def __init__(self, parent = None):
        self.properties = {}
        for prop in self.__properties__:
            self.properties[prop] = None
        
        self.children = []
        self.childrenLevel = 0
        self.parent = parent
    
    def toDict(self):
        return {
            **self.properties,
            "children": [child.toDict() for child in self.children]
        }
    
    def __getitem__(self, name):
        if type(name) == int:
            return self.children[name]
        elif type(name) == str and name in self.__properties__:
            return self.properties[name]
        else:
            raise Fox5Error("Unknown key {}".format(name))
    
    def __setitem__(self, name, value):
        if type(name) == int:
            self.children[name] = value
        
        elif type(name) == str and name in self.__properties__:
            self.properties[name] = value
        
        else:
            raise Fox5Error("Unknown key {}".format(name))
    
    def __delitem__(self, name):
        if type(name) == int:
            del self.children[name]
        
        elif type(name) == str and name in self.__properties__:
            self.properties.pop(name)
        
        else:
            raise Fox5Error("Unknown key {}".format(name))
    
    def append(self, value):
        self.children.append(value)
    
    def decodeProperty(self, char, handle):
        return False
    
    def encodeProperty(self, prop):
        return False
    
    @classmethod
    def fromStream(cls, handle, *args, **kwargs):
        self = cls(*args, **kwargs)
        char = True
        while True:
            char = handle.read(1)
            if not char:
                break
            
            if char == b"<":
                break
            
            elif char == b"L":
                if self.__childtype__ == None:
                    raise Fox5Error("Unexpected list!")
                
                level, count = sList.unpack(handle.read(sList.size))
                
                if level != self.__childtype__.__level__:
                    raise Fox5Error("Invalid level encountered!")
                
                for i in range(count):
                    self.children.append(self.__childtype__.fromStream(handle, self))
                
                if i+1 != count:
                    raise Fox5Error("Unexpected end of list!")
                
            elif not self.decodeProperty(char, handle):
                    raise Fox5Error("Unhandled attribute {}".format(char))
        return self
    
    def __bytes__(self):
        data = b""
        for prop in self.__properties__:
            if prop in self.properties and self.properties[prop] != None:
                encoded = self.encodeProperty(prop)
                if type(encoded) != bytes:
                    raise Fox5Error("Unhandled attribute {}".format(prop))
                data += encoded
        
        if self.__childtype__ != None:
            data += b"L" + sList.pack(self.__childtype__.__level__, len(self.children))
            for child in self.children:
                data += bytes(child)
                data += b"<"
        return data
        
    
class Fox5Sprite(Fox5List):
    __level__ = 4
    __properties__ = ("Purpose", "Image", "Offset")
    __childtype__ = None
    
    def encodeProperty(self, prop):
        data = b""
        if prop == "Purpose":
            data += b"C" + sUInt16.pack(self["Purpose"])
            return data
        
        if prop == "Image":
            data += b"c" + sUInt16.pack(self["Image"])
            return data
        
        if prop =="Offset":
            data += b"O" + sUInt16.pack(self["Offset"][0]) + sUInt16.pack(self["Offset"][1])
            return data
    
    def decodeProperty(self, char, handle):
        if char == b"C":
            self["Purpose"], = sUInt16.unpack(handle.read(sUInt16.size))
            return True
        
        if char == b"c":
            self["Image"], = sUInt16.unpack(handle.read(sUInt16.size))
            return True
        
        if char == b"O":
            self["Offset"] = [
                sUInt16.unpack(handle.read(sUInt16.size))[0],
                sUInt16.unpack(handle.read(sUInt16.size))[0]
            ]
            return True

class Fox5Frame(Fox5List):
    __level__ = 3
    __properties__ = ("FrameOffset", "FurreOffset")
    __childtype__ = Fox5Sprite
    
    def encodeProperty(self, prop):
        data = b""
        if prop == "FrameOffset":
            data += b"o" + sInt16.pack(self["FrameOffset"][0]) + sInt16.pack(self["FrameOffset"][1])
            return data
        
        if prop == "FurreOffset":
            data += b"f" + sInt16.pack(self["FurreOffset"][0]) + sInt16.pack(self["FurreOffset"][1])
            return data
    
    def decodeProperty(self, char, handle):
        if char == b"o":
            self["FrameOffset"] = [
                sInt16.unpack(handle.read(sInt16.size))[0],
                sInt16.unpack(handle.read(sInt16.size))[0]
            ]
            return True
        
        if char == b"f":
            self["FurreOffset"] = [
                sInt16.unpack(handle.read(sInt16.size))[0],
                sInt16.unpack(handle.read(sInt16.size))[0]
            ]
            return True
            

class Fox5Shape(Fox5List):
    __level__ = 2
    __properties__ = ("Purpose", "Direction", "State", "Ratio",
                      "KitterSpeak")
    __childtype__ = Fox5Frame
    
    def encodeProperty(self, prop):
        data = b""
        if prop == "Purpose":
            data += b"p" + sUInt8.pack(self["Purpose"])
            return data
        
        if prop == "State":
            data += b"s" + sUInt8.pack(self["State"])
            return data
        
        if prop == "Direction":
            data += b"D" + sUInt8.pack(self["Direction"])
            return data
        
        if prop == "Ratio":
            data += b"R" + sUInt8.pack(self["Ratio"][0]) + sUInt8.pack(self["Ratio"][1])
            return data
        
        if prop == "KitterSpeak":
            data += b"K" + sUInt16.pack(len(self["KitterSpeak"]))
            for kline in self["KitterSpeak"]:
                kline = (list(kline) + [0,0,0])[0:3]
                data += sUInt16.pack(kline[0]) + sInt16.pack(kline[1]) + sInt16.pack(kline[2])
            return data
    
    def decodeProperty(self, char, handle):
        if char == b"p":
            self["Purpose"], = sUInt8.unpack(handle.read(sUInt8.size))
            return True
        
        if char == b"s":
            self["State"], = sUInt8.unpack(handle.read(sUInt8.size))
            return True
        
        if char == b"D":
            self["Direction"], = sUInt8.unpack(handle.read(sUInt8.size))
            return True
        
        if char == b"R":
            self["Ratio"] = [
                sUInt8.unpack(handle.read(sUInt8.size))[0],
                sUInt8.unpack(handle.read(sUInt8.size))[0]
            ]
            return True
        
        if char == b"K":
            self["KitterSpeak"] = []
            count, = sUInt16.unpack(handle.read(sUInt16.size))
            for i in range(count):
                self["KitterSpeak"].append([
                    sUInt16.unpack(handle.read(sUInt16.size))[0],
                    sInt16.unpack(handle.read(sInt16.size))[0],
                    sInt16.unpack(handle.read(sInt16.size))[0],
                ])
            return True

class Fox5Object(Fox5List):
    __level__ = 1
    __properties__ = ("ID", "Name", "Description", "Authors", "Revisions",
                      "Keywords", "License", "Portal", "EditType", "Flags",
                      "MoreFlags", "FxFilter")
    __childtype__ = Fox5Shape
    
    def encodeProperty(self, prop):
        data = b""
        if prop == "Revisions":
            data += b"r" + sUInt16.pack(self["Revisions"])
            return data
        
        if prop == "Authors":
            data += b"a" + sUInt16.pack(len(self["Authors"]))
            for i in range(len(self["Authors"])):
                name = self["Authors"][i].encode()
                data += sUInt16.pack(len(name)) + name
            return data
        
        if prop == "License":
            data += b"l" + sUInt8.pack(self["License"])
            return data
        
        if prop == "Keywords":
            data += b"k" + sUInt16.pack(len(self["Keywords"]))
            for i in range(len(self["Keywords"])):
                name = self["Keywords"][i].encode()
                data += sUInt16.pack(len(name)) + name
            return data
        
        if prop == "Name":
            name = self["Name"].encode()
            data += b"n" + sUInt16.pack(len(name)) + name   
            return data
        
        if prop == "Description":
            name = self["Description"].encode()
            data += b"d" + sUInt16.pack(len(name)) + name
            return data
        
        if prop == "Flags":
            data += b"!" + sUInt8.pack(self["Flags"])
            return data
        
        if prop == "Portal":
            name = self["Portal"].encode("iso-8859-1")
            data += b"P" + sUInt16.pack(len(name)) + name
            return data

        if prop == "MoreFlags":
            data += b"?" + sUInt32.pack(self["MoreFlags"])
            return data
        
        if prop == "ID":
            data += b"i" + sInt32.pack(self["ID"])
            return data
        
        if prop == "EditType":
            data += b"t" + sUInt8.pack(self["EditType"])
            return data
        
        if prop == "FxFilter":
            data += b"F" + sUInt8.pack(self["FxFilter"]["Layer"]) + sUInt8.pack(self["FxFilter"]["Mode"])
            return data
    
    def decodeProperty(self, char, handle):
        if char == b"r":
            self["Revisions"], = sUInt16.unpack(handle.read(sUInt16.size))
            return True
        
        if char == b"a":
            self["Authors"] = []
            count, = sUInt16.unpack(handle.read(sUInt16.size))
            for i in range(count):
                l, = sUInt16.unpack(handle.read(sUInt16.size))
                self["Authors"].append(handle.read(l).decode())
            return True
        
        if char == b"l":
            self["License"], = sUInt8.unpack(handle.read(sUInt8.size))
            return True
        
        if char == b"k":
            self["Keywords"] = []
            count, = sUInt16.unpack(handle.read(sUInt16.size))
            for i in range(count):
                l, = sUInt16.unpack(handle.read(sUInt16.size))
                self["Keywords"].append(handle.read(l).decode())
            return True
        
        if char == b"n":
            l, = sUInt16.unpack(handle.read(sUInt16.size))
            self["Name"] = handle.read(l).decode()
            return True
        
        if char == b"d":
            l, = sUInt16.unpack(handle.read(sUInt16.size))
            self["Description"] = handle.read(l).decode()
            return True
        
        if char == b"!":
            self["Flags"], = sUInt8.unpack(handle.read(sUInt8.size))
            return True
        
        if char == b"P":
            l, = sUInt16.unpack(handle.read(sUInt16.size))
            self["Portal"] = handle.read(l).decode("iso-8859-1")
            return True

        if char == b"?":
            self["MoreFlags"], = sUInt32.unpack(handle.read(sUInt32.size))
            return True
        
        if char == b"i":
            self["ID"], = sInt32.unpack(handle.read(sInt32.size))
            return True
        
        if char == b"t":
            self["EditType"], = sUInt8.unpack(handle.read(sUInt8.size))
            return True
        
        if char == b"F":
            self["FxFilter"] = {
                "Layer": sUInt8.unpack(handle.read(sUInt8.size))[0],
                "Mode": sUInt8.unpack(handle.read(sUInt8.size))[0]
            }
            return True

class Fox5Body(Fox5List):
    __level__ = 0
    __properties__ = ("ImageList", "Generator")
    __childtype__ = Fox5Object
    
    def encodeProperty(self, prop):
        data = b""

        if prop == "Generator":
            data += b"g" + sUInt8.pack(self["Generator"])
            return data

        if prop == "ImageList":
            data += b"S" + sUInt32.pack(len(self["ImageList"]))
            for image in self["ImageList"]:
                data += sImageList.pack(len(image.compress()), image.width, image.height, image.format)
                #Encryption is handled in Fox5File
            return data
        
    def decodeProperty(self, char, handle):
        if char == b"g":
            self["Generator"], = sUInt8.unpack(handle.read(sUInt8.size))
            return True

        if char == b"S":
            self["ImageList"] = []
            
            foxhandle = self.parent.parent
            
            count, = sUInt32.unpack(handle.read(sUInt32.size))
            for count in range(count):
                compressedSize, width, height, fmt = sImageList.unpack(handle.read(sImageList.size))
                data = foxhandle.read(compressedSize)
                
                #Decrypt if needed
                if self.parent.encryption == 1:
                    uncompressedSize = width * height * (4 if fmt == 1 else 1)
                    data = Fox5Cipher(data, uncompressedSize, self.parent.seed)
                
                im = Fox5Image(width, height, fmt, data, True)
                self["ImageList"].append(im)
            return True

sFox5Footer = struct.Struct(">BBxxII8s")
class Fox5File(Fox5List):
    __level__ = -1
    __childtype__ = Fox5Body
    
    def __init__(self, *args, compression = 2, encryption = 0, seed = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.compression = compression
        self.encryption = encryption
        self.seed = seed
    
    @property
    def body(self):
        return self.children[0]
    
    @classmethod
    def fromStream(cls, handle):
        handle.seek(-8, 2)
        if handle.read(4) != b"FOX5":
            raise Fox5Error("Not a Fox5 File!")
        
        if handle.read(4) != b".1.1":
            raise Fox5Error("Fox5 file, but no idea what version it is!")
        
        handle.seek(-20, 2)
        compression, encryption, dataCompressedSize, \
            dataUncompressedSize, magic = sFox5Footer.unpack(handle.read(sFox5Footer.size))
        
        if encryption == 1:
            if haveCrypto == False:
                #Only need to check for this once, it won't magically appear.
                raise Fox5Error("Can't decrypt without libfurc.crypto!")
            handle.seek(-36, 2)
            seed = handle.read(16)
        else:
            seed = None
        
        handle.seek(0)
        data = handle.read(dataCompressedSize)
        
        if encryption == 1:
            data = Fox5Cipher(data, dataUncompressedSize, seed)
        
        data = Decompress(data)
        
        if len(data) != dataUncompressedSize:
            raise Fox5Error("Uncompressed size does not equal decompressed size!")
        
        data = io.BytesIO(data)
        if data.read(4) != b"\0\0\0\0":
            raise Fox5Error("Data header is incorrect!")
        
        #This is actually calling the Fox5List
        self = super(Fox5File, cls).fromStream(data, handle, compression = compression, encryption = encryption, seed = seed)
        return self
    
    def __bytes__(self):
        if self.encryption == 1:
            if haveCrypto == False:
                #Only need to check for this once, it won't magically appear.
                raise Fox5Error("Can't encrypt without libfurc.crypto!")
            if self.seed == None:
                seed = random.randbytes(16)
        
        data = b"\0\0\0\0" + super().__bytes__()
        uncompressedSize = len(data)
        data = Compress(data)
        compressedSize = len(data)
        
        if self.encryption == 1:
            data = Fox5Cipher(data, uncompressedSize, self.seed)
        
        for image in self.body["ImageList"]:
            if self.encryption == 1:
                data += Fox5Cipher(image.compress(), len(image), self.seed)
                
            else:
                data += image.compress()
        
        if self.encryption == 1:
            data += self.seed
        
        data += sFox5Footer.pack(self.compression, self.encryption, compressedSize, uncompressedSize, b"FOX5.1.1")
        return data

def load(path):
    with open(path, "rb") as f:
        return Fox5File.fromStream(f)

def loads(data):
    return Fox5File.fromStream(io.BytesIO(data))

def dump(fox, path):
    with open(path, "wb") as f:
        return f.write(bytes(fox))

def dumps(fox):
    return bytes(fox)
