#!/usr/bin/env python3
import struct
from . import base

sInt32 = struct.Struct("<i")
sUInt32 = struct.Struct("<I")
sFloat64 = struct.Struct("<d")

class ParticleSource:
    TYPE_UNSIGNED_INT = 0
    TYPE_SIGNED_INT = 1
    TYPE_FLOAT = 2

    version = None
    type = None

    attributes = (
    )

    def __init__(self, version = 1):
        self.version = version
        self.particleVarianceStart = 0
        self.endTimeMinRaw = 0
        self.particleVarianceEnd = 0
        self.endTimeMaxRaw = 0
        self.particleCount = 0
        self.unused1 = 0
        self.centerPosX = 0
        self.centerPosY = 0
        self.effectLength = 0
        self.centerRadiusMin = 0
        self.centerRadiusMax = 0
        self.colorAMinB = 0
        self.colorAMinG = 0
        self.colorAMinR = 0
        self.colorAMaxB = 0
        self.colorAMaxG = 0
        self.colorAMaxR = 0
        self.colorBMinB = 0
        self.colorBMinG = 0
        self.colorBMinR = 0
        self.colorBMaxB = 0
        self.colorBMaxG = 0
        self.colorBMaxR = 0
        self.colorCMinB = 0
        self.colorCMinG = 0
        self.colorCMinR = 0
        self.colorCMaxB = 0
        self.colorCMaxG = 0
        self.colorCMaxR = 0
        self.translucencyMinA = 0
        self.translucencyMinB = 0
        self.translucencyMinC = 0
        self.translucencyMaxA = 0
        self.translucencyMaxB = 0
        self.translucencyMaxC = 0
        self.motionBlurStepsMin = 0
        self.motionBlurStepsMax = 0
        self.motionBlurLengthMin = 0
        self.motionBlurLengthMax = 0
        self.shape = 0
        self.unused2 = 0

        self._attributeIndex = []
        for attribute, t in self:
            self._attributeIndex.append(attribute)
    
    def __iter__(self):
        for attribute in self.attributes:
            yield attribute
    
    def __getitem__(self, key):
        if type(key) == int:
            return getattr(self, self._attributeIndex[key])
        elif type(key) == str:
            if key not in self._attributeIndex:
                raise KeyError("Unknown attribute {}!".format(key))
            return getattr(self, key)
        else:
            raise KeyError("Invalid key type {}!".format(type(key)))
    
    def __setitem__(self, key, value):
        if type(key) == int:
            return setattr(self, self._attributeIndex[key], value)
        elif type(key) == str:
            if key not in self._attributeIndex:
                raise KeyError("Unknown attribute {}!".format(key))
            return setattr(self, key, value)
        else:
            raise KeyError("Invalid key type {}!".format(type(key)))
    

class ParticleBezier(ParticleSource):
    version = 1
    type = 1
    attributes = (
        ("particleVarianceStart", ParticleSource.TYPE_UNSIGNED_INT),
        ("endTimeMinRaw", ParticleSource.TYPE_UNSIGNED_INT),
        ("particleVarianceEnd", ParticleSource.TYPE_UNSIGNED_INT),
        ("endTimeMaxRaw", ParticleSource.TYPE_UNSIGNED_INT),
        ("particleCount", ParticleSource.TYPE_SIGNED_INT),
        ("unused1", ParticleSource.TYPE_SIGNED_INT),
        ("centerPosX", ParticleSource.TYPE_FLOAT),
        ("centerPosY", ParticleSource.TYPE_FLOAT),
        ("effectLength", ParticleSource.TYPE_FLOAT),
        ("centerRadiusMin", ParticleSource.TYPE_FLOAT),
        ("centerRadiusMax", ParticleSource.TYPE_FLOAT),
        #
        ("direction", ParticleSource.TYPE_SIGNED_INT),
        ("unknown3", ParticleSource.TYPE_SIGNED_INT),
        ("abMinWidth", ParticleSource.TYPE_FLOAT),
        ("abMinHeight", ParticleSource.TYPE_FLOAT),
        ("abMinUnused", ParticleSource.TYPE_FLOAT),
        ("abMaxWidth", ParticleSource.TYPE_FLOAT),
        ("abMaxHeight", ParticleSource.TYPE_FLOAT),
        ("abMaxUnused", ParticleSource.TYPE_FLOAT),
        ("bcMinWidth", ParticleSource.TYPE_FLOAT),
        ("bcMinHeight", ParticleSource.TYPE_FLOAT),
        ("bcMinUnused", ParticleSource.TYPE_FLOAT),
        ("bcMaxWidth", ParticleSource.TYPE_FLOAT),
        ("bcMaxHeight", ParticleSource.TYPE_FLOAT),
        ("bcMaxUnused", ParticleSource.TYPE_FLOAT),
        #
        ("colorAMinB", ParticleSource.TYPE_FLOAT),
        ("colorAMinG", ParticleSource.TYPE_FLOAT),
        ("colorAMinR", ParticleSource.TYPE_FLOAT),
        ("colorAMaxB", ParticleSource.TYPE_FLOAT),
        ("colorAMaxG", ParticleSource.TYPE_FLOAT),
        ("colorAMaxR", ParticleSource.TYPE_FLOAT),
        ("colorBMinB", ParticleSource.TYPE_FLOAT),
        ("colorBMinG", ParticleSource.TYPE_FLOAT),
        ("colorBMinR", ParticleSource.TYPE_FLOAT),
        ("colorBMaxB", ParticleSource.TYPE_FLOAT),
        ("colorBMaxG", ParticleSource.TYPE_FLOAT),
        ("colorBMaxR", ParticleSource.TYPE_FLOAT),
        ("colorCMinB", ParticleSource.TYPE_FLOAT),
        ("colorCMinG", ParticleSource.TYPE_FLOAT),
        ("colorCMinR", ParticleSource.TYPE_FLOAT),
        ("colorCMaxB", ParticleSource.TYPE_FLOAT),
        ("colorCMaxG", ParticleSource.TYPE_FLOAT),
        ("colorCMaxR", ParticleSource.TYPE_FLOAT),
        ("translucencyMinA", ParticleSource.TYPE_FLOAT),
        ("translucencyMinB", ParticleSource.TYPE_FLOAT),
        ("translucencyMinC", ParticleSource.TYPE_FLOAT),
        ("translucencyMaxA", ParticleSource.TYPE_FLOAT),
        ("translucencyMaxB", ParticleSource.TYPE_FLOAT),
        ("translucencyMaxC", ParticleSource.TYPE_FLOAT),
        ("motionBlurStepsMin", ParticleSource.TYPE_FLOAT),
        ("motionBlurStepsMax", ParticleSource.TYPE_FLOAT),
        ("motionBlurLengthMin", ParticleSource.TYPE_FLOAT),
        ("motionBlurLengthMax", ParticleSource.TYPE_FLOAT),
        ("shape", ParticleSource.TYPE_SIGNED_INT),
        ("unused2", ParticleSource.TYPE_SIGNED_INT)
    )

    def __init__(self, version):
        super().__init__(version)
        self.direction = 0
        self.abMinWidth = 0
        self.abMinHeight = 0
        self.abMinUnused = 0
        self.abMaxWidth = 0
        self.abMaxHeight = 0
        self.abMaxUnused = 0
        self.bcMinWidth = 0
        self.bcMinHeight = 0
        self.bcMinUnused = 0
        self.bcMaxWidth = 0
        self.bcMaxHeight = 0
        self.bcMaxUnused = 0

class ParticleRay(ParticleSource):
    version = 1
    type = 2
    attributes = (
        ("particleVarianceStart", ParticleSource.TYPE_UNSIGNED_INT),
        ("endTimeMinRaw", ParticleSource.TYPE_UNSIGNED_INT),
        ("particleVarianceEnd", ParticleSource.TYPE_UNSIGNED_INT),
        ("endTimeMaxRaw", ParticleSource.TYPE_UNSIGNED_INT),
        ("particleCount", ParticleSource.TYPE_SIGNED_INT),
        ("unused1", ParticleSource.TYPE_SIGNED_INT),
        ("centerPosX", ParticleSource.TYPE_FLOAT),
        ("centerPosY", ParticleSource.TYPE_FLOAT),
        ("effectLength", ParticleSource.TYPE_FLOAT),
        ("centerRadiusMin", ParticleSource.TYPE_FLOAT),
        ("centerRadiusMax", ParticleSource.TYPE_FLOAT),
        #
        ("rayAngleMin", ParticleSource.TYPE_FLOAT),
        ("rayAngleMax", ParticleSource.TYPE_FLOAT),
        ("rayLengthMin", ParticleSource.TYPE_FLOAT),
        ("rayLengthMax", ParticleSource.TYPE_FLOAT),
        #
        ("colorAMinB", ParticleSource.TYPE_FLOAT),
        ("colorAMinG", ParticleSource.TYPE_FLOAT),
        ("colorAMinR", ParticleSource.TYPE_FLOAT),
        ("colorAMaxB", ParticleSource.TYPE_FLOAT),
        ("colorAMaxG", ParticleSource.TYPE_FLOAT),
        ("colorAMaxR", ParticleSource.TYPE_FLOAT),
        ("colorBMinB", ParticleSource.TYPE_FLOAT),
        ("colorBMinG", ParticleSource.TYPE_FLOAT),
        ("colorBMinR", ParticleSource.TYPE_FLOAT),
        ("colorBMaxB", ParticleSource.TYPE_FLOAT),
        ("colorBMaxG", ParticleSource.TYPE_FLOAT),
        ("colorBMaxR", ParticleSource.TYPE_FLOAT),
        ("colorCMinB", ParticleSource.TYPE_FLOAT),
        ("colorCMinG", ParticleSource.TYPE_FLOAT),
        ("colorCMinR", ParticleSource.TYPE_FLOAT),
        ("colorCMaxB", ParticleSource.TYPE_FLOAT),
        ("colorCMaxG", ParticleSource.TYPE_FLOAT),
        ("colorCMaxR", ParticleSource.TYPE_FLOAT),
        ("translucencyMinA", ParticleSource.TYPE_FLOAT),
        ("translucencyMinB", ParticleSource.TYPE_FLOAT),
        ("translucencyMinC", ParticleSource.TYPE_FLOAT),
        ("translucencyMaxA", ParticleSource.TYPE_FLOAT),
        ("translucencyMaxB", ParticleSource.TYPE_FLOAT),
        ("translucencyMaxC", ParticleSource.TYPE_FLOAT),
        ("motionBlurStepsMin", ParticleSource.TYPE_FLOAT),
        ("motionBlurStepsMax", ParticleSource.TYPE_FLOAT),
        ("motionBlurLengthMin", ParticleSource.TYPE_FLOAT),
        ("motionBlurLengthMax", ParticleSource.TYPE_FLOAT),
        ("shape", ParticleSource.TYPE_SIGNED_INT),
        ("unused2", ParticleSource.TYPE_SIGNED_INT)
    )

    def __init__(self, version):
        super().__init__(version)
        self.rayAngleMin = 0
        self.rayAngleMax = 0
        self.rayLengthMin = 0
        self.rayLengthMax = 0

class Particles:
    def __init__(self, version, flags):
        self.version = version
        self.flags = flags
        self.sources = []
    
    def addSource(self, source):
        self.sources.append(source)
    
    def __repr__(self):
        return "<Particles {} flags=0x{:x} sources={}>".format(self.version, self.flags, len(self.sources))
    
    @classmethod
    def loadsVXT(cls, data):
        if isinstance(data, (bytes, bytearray)):
            data = data.decode()

        lines = data.splitlines()
        if len(lines) == 0 or lines[0].strip() != "HORUS VXN TEXT":
            raise ValueError("Invalid VXN text file!")
        
        i = 1
        loaded = {}
        stack = [loaded]
        while i < len(lines):
            #Remove comments, starting and ending spaces, newlines, etc
            raw = lines[i].split("#", 1)[0].strip()
            line = raw.split()
            
            #Skip if empty
            if len(line) == 0:
                i += 1
                continue
            
            if line[0].lower() == "start":
                if len(line) == 2:
                    if line[1] in stack[-1]:
                        raise ValueError("Key {} already exists!".format(line[1]))
                    
                    d = {}
                    stack[-1][line[1]] = d
                    stack.append(line[1])
                    stack.append(d)
                
                elif len(line) == 3:
                    if line[1] not in stack[-1]:
                        stack[-1][line[1]] = []
                    
                    if type(stack[-1][line[1]]) != list:
                        raise ValueError("Key {} already exists!".format(line[1]))
                    
                    #Resize as nessassery
                    count = int(line[2])
                    while len(stack[-1][line[1]]) <= count:
                        stack[-1][line[1]].append(None)
                    
                    d = {}
                    stack[-1][line[1]][count] = d
                    stack.append(line[1])
                    stack.append(d)
                
            elif line[0].lower() == "end":
                d = stack.pop()
                name = stack.pop()
                if name != line[1]:
                    raise ValueError("Expected end to {}, got {}!".format(name, line[1]))
            
            else:
                if line[0] in stack[-1]:
                    raise ValueError("Key {} already exists!".format(line[0]))
                stack[-1][line[0]] = line[1]
            
            i += 1
        
        if "version" not in loaded:
            raise ValueError("Missing attribute version!")
        
        if "flags" not in loaded:
            raise ValueError("Missing attribute flags!")
        
        if loaded["flags"].startswith("0b"):
            loaded["flags"] = int(loaded["flags"], 2)
        
        result = cls(int(loaded["version"]), int(loaded["flags"]))
        
        if "sources" not in loaded:
            return result

        source_container = loaded["sources"]
        if "source" not in source_container:
            return result

        raw_sources = source_container["source"]
        if type(raw_sources) != list:
            raw_sources = [raw_sources]

        for source in raw_sources:
            if type(source) != dict:
                raise ValueError("Invalid source block in text file!")

            if "version" not in source:
                raise ValueError("Missing attribute source.version!")
            
            if "type" not in source:
                raise ValueError("Missing attribute source.type!")
            
            source_type = int(source["type"], 0)
            source_version = int(source["version"], 0)

            if source_type == 1:
                pSource = ParticleBezier(source_version)
            elif source_type == 2:
                pSource = ParticleRay(source_version)
            else:
                raise ValueError("Unknown source.type {}!".format(source_type))

            attr_data = source.get("attributes", {})
            if type(attr_data) != dict:
                raise ValueError("Invalid source.attributes block!")

            for idx, (name, t) in enumerate(pSource):
                if name in attr_data:
                    raw_value = attr_data[name]
                else:
                    continue

                if t in (ParticleSource.TYPE_UNSIGNED_INT, ParticleSource.TYPE_SIGNED_INT):
                    pSource[name] = int(raw_value, 0)
                elif t == ParticleSource.TYPE_FLOAT:
                    pSource[name] = float(raw_value)
                else:
                    raise ValueError("Unknown attribute type {}!".format(t))
            
            result.sources.append(pSource)
        
        return result
    
    @classmethod
    def loadsVXN(cls, data):
        magic, version, flags = struct.unpack_from("<4sBI", data)
        if magic != b"FvXn":
            raise ValueError("Invalid VXN file!")
        
        if version != 1:
            raise ValueError("Only know version 1")
        
        offset = 9
        
        result = cls(version, flags)
        while offset < len(data):
            magic, pType, version = struct.unpack_from("<2sIB", data, offset)
            if magic != b"m!":
                raise ValueError("Unexpected data in particle stream!")
            
            offset += 7

            if pType == 1:
                source = ParticleBezier(version)
                sourceDataLen = 400
            elif pType == 2:
                source = ParticleRay(version)
                sourceDataLen = 328
            else:
                raise ValueError("Unknown particle type {}".format(pType))

            if offset + sourceDataLen > len(data):
                raise ValueError("Truncated particle source data!")

            sourceData = data[offset:offset+sourceDataLen]
            sourceOffset = 0

            for attribute, t in source:
                if t == ParticleSource.TYPE_UNSIGNED_INT:
                    source[attribute] = sUInt32.unpack_from(sourceData, sourceOffset)[0]
                    sourceOffset += 4
                elif t == ParticleSource.TYPE_SIGNED_INT:
                    source[attribute] = sInt32.unpack_from(sourceData, sourceOffset)[0]
                    sourceOffset += 4
                elif t == ParticleSource.TYPE_FLOAT:
                    source[attribute] = sFloat64.unpack_from(sourceData, sourceOffset)[0]
                    sourceOffset += 8
                else:
                    raise ValueError("Unknown attribute type {}!".format(t))

            offset += sourceDataLen
            
            result.sources.append(source)
            
        return result
    
    @classmethod
    def loadsVXA(cls, data):
        offset = 0
        if data[:6] == b"VXNASC":
            offset = 6 #Raw, no offsets
        else:
            raise ValueError("Invalid VXN ASCII stream!")
        
        version = base.b220decode(data[offset:offset+1])
        offset += 1
        
        flags = base.b220decode(data[offset:offset+4])
        offset += 4
        
        result = cls(version, flags)
        while offset < len(data):
            if data[offset:offset+2] != b"m!":
                raise ValueError("Unexpected data in particle stream!")
            
            offset += 2
            
            pType = base.b220decode(data[offset:offset+4])
            offset += 4
            
            version = base.b220decode(data[offset:offset+1])
            offset += 1
            
            if pType == 1:
                sourceDataLen = 400
            elif pType == 2:
                sourceDataLen = 328
            else:
                raise ValueError("Unknown source data type!")
            
            sourceData = []
            for i in range(0, sourceDataLen, 1):
                sourceData.append(base.b220decode(data[offset:offset+2]))
                offset += 2
            
            sourceData = bytes(sourceData)
            
            if pType == 1:
                source = ParticleBezier(version)
            elif pType == 2:
                source = ParticleRay(version)
            
            sourceOffset = 0

            for attribute, t in source:
                if t == ParticleSource.TYPE_UNSIGNED_INT:
                    source[attribute] = sUInt32.unpack_from(sourceData, sourceOffset)[0]
                    sourceOffset += 4
                elif t == ParticleSource.TYPE_SIGNED_INT:
                    source[attribute] = sInt32.unpack_from(sourceData, sourceOffset)[0]
                    sourceOffset += 4
                elif t == ParticleSource.TYPE_FLOAT:
                    source[attribute] = sFloat64.unpack_from(sourceData, sourceOffset)[0]
                    sourceOffset += 8
                else:
                    raise ValueError("Unknown attribute type {}!".format(t))
            result.sources.append(source)
        
        return result
    
    def dumpsVXN(self):
        data = b""
        data += struct.pack("<4sBI", b"FvXn", self.version, self.flags)
        
        for source in self.sources:
            data += struct.pack("<2sIB", b"m!", source.type, source.version)

            sourceData = bytearray()
            for attribute, t in source:
                value = source[attribute]
                if t == ParticleSource.TYPE_UNSIGNED_INT:
                    sourceData += sUInt32.pack(value)
                elif t == ParticleSource.TYPE_SIGNED_INT:
                    sourceData += sInt32.pack(value)
                elif t == ParticleSource.TYPE_FLOAT:
                    sourceData += sFloat64.pack(value)
                else:
                    raise ValueError("Unknown attribute type {}!".format(t))

            if source.type == 1:
                expected_len = 400
            elif source.type == 2:
                expected_len = 328
            else:
                raise ValueError("Unknown source type {}!".format(source.type))

            if len(sourceData) != expected_len:
                raise ValueError(
                    "Unexpected serialized source length {} for type {} (expected {})".format(
                        len(sourceData), source.type, expected_len
                    )
                )

            data += bytes(sourceData)
            
        return data
    
    def dumpsVXT(self):
        data = "HORUS VXN TEXT\n"
        data += "version {}\n".format(self.version)
        data += "flags 0b{:0>32b}\n".format(self.flags)
        data += "start sources\n"
        for source in self.sources:
            data += "    start source\n"
            data += "        version {}\n".format(source.version)
            data += "        type {}\n".format(source.type)
            data += "        start attributes\n"
            for attribute, t in source:
                value = source[attribute]

                if t in (ParticleSource.TYPE_UNSIGNED_INT, ParticleSource.TYPE_SIGNED_INT):
                    data += "            {} {}\n".format(attribute, int(value))
                elif t == ParticleSource.TYPE_FLOAT:
                    data += "            {} {}\n".format(attribute, float(value))
                else:
                    raise ValueError("Unknown attribute type {}!".format(t))
            
            data += "        end attributes\n"
            data += "    end source\n"
        data += "end sources\n"
        
        return data.strip().encode()
    
    def dumpsVXA(self):
        data = b"VXNASC" 
        
        data += base.b220encode(self.version, 1)
        data += base.b220encode(self.flags, 4)
        
        for source in self.sources:
            data += b"m!"
            
            data += base.b220encode(source.type, 4)
            data += base.b220encode(source.version, 1)
            
            sourceData = bytearray()
            for attribute, t in source:
                value = source[attribute]
                if t == ParticleSource.TYPE_UNSIGNED_INT:
                    sourceData += sUInt32.pack(value)
                elif t == ParticleSource.TYPE_SIGNED_INT:
                    sourceData += sInt32.pack(value)
                elif t == ParticleSource.TYPE_FLOAT:
                    sourceData += sFloat64.pack(value)
                else:
                    raise ValueError("Unknown attribute type {}!".format(t))

            if source.type == 1:
                expected_len = 400
            elif source.type == 2:
                expected_len = 328
            else:
                raise ValueError("Unknown source type {}!".format(source.type))

            if len(sourceData) != expected_len:
                raise ValueError(
                    "Unexpected serialized source length {} for type {} (expected {})".format(
                        len(sourceData), source.type, expected_len
                    )
                )

            for byte in sourceData:
                data += base.b220encode(byte, 2)
        
        return data
