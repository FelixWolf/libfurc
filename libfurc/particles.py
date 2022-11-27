#!/usr/bin/env python3
import struct
from . import base

particleAttributeMetadata = {
    1: {
        "size": 52,
        "names": {
            0: "delay",
            2: "stime",
            3: "ptime",
            4: "count"
        }
    },
    2: {
        "size": 45,
        "names": {
            0: "delay",
            2: "stime",
            3: "ptime",
            4: "count"
        }
    }
}
        
class ParticleSource:
    def __init__(self, version, pType):
        self.version = version
        self.type = pType
        self.attributes = []

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
    def loadsTxt(cls, data):
        lines = data.splitlines()
        if lines[0] != "HORUS VXN TEXT":
            raise ValueError("Invalid VXN text file!")
        
        i = 1
        loaded = {}
        stack = [loaded]
        while i < len(lines):
            #Remove comments, starting and ending spaces, newlines, etc
            line = [x.lower() for x in lines[i].split("#")[0].strip().split(" ")]
            
            #Skip if empty
            if len(line) == 0:
                i += 1
                continue
            
            if line[0] == "start":
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
                
            elif line[0] == "end":
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
            loaded["flags"] = int(loaded["flags"], 16)
        
        result = cls(int(loaded["version"]), int(loaded["flags"]))
        
        for source in loaded["sources"]["source"]:
            if "version" not in source:
                raise ValueError("Missing attribute source.version!")
            
            if "type" not in source:
                raise ValueError("Missing attribute source.type!")
            
            source["type"] = int(source["type"])
            
            pSource = ParticleSource(int(source["version"]), source["type"])
            
            #Prefill
            pSource.attributes = [0] * particleAttributeMetadata[source["type"]]["size"]
            
            for i in range(len(pSource.attributes)):
                name = "attr{}".format(i)
                
                #Resolve name if we have it
                if i in particleAttributeMetadata[source["type"]]["names"]:
                    tname = particleAttributeMetadata[source["type"]]["names"][i]
                    if tname in source["attributes"]:
                        name = tname
                        
                #Type cast
                if "." in source["attributes"][name]:
                    pSource.attributes[i] = float(source["attributes"][name])
                else:
                    pSource.attributes[i] = int(source["attributes"][name])
            
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
            source = ParticleSource(version, pType)
            
            sdata = offset
            
            for p in struct.unpack_from("<4Iii5d", data, offset):
                source.attributes.append(p)
            
            offset += 64
            
            if pType == 1:
                for p in struct.unpack_from("<i12d", data, offset):
                    source.attributes.append(p)
                offset += 100
            elif pType == 2:
                for p in struct.unpack_from("<4d", data, offset):
                    source.attributes.append(p)
                offset += 32
            else:
                raise ValueError("Unknown particle type {}".format(pType))
            
            for p in struct.unpack_from("<28dii", data, offset):
                source.attributes.append(p)
            
            offset += 232
            
            result.sources.append(source)
            
        return result
    
    @classmethod
    def loadsMessage(cls, data):
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
            
            source = ParticleSource(version, pType)
            
            sourceOffset = 0
            
            for p in struct.unpack_from("<4Iii5d", sourceData, sourceOffset):
                source.attributes.append(p)
            
            sourceOffset += 64
            
            if pType == 1:
                for p in struct.unpack_from("<i12d", sourceData, sourceOffset):
                    source.attributes.append(p)
                sourceOffset += 100
            elif pType == 2:
                for p in struct.unpack_from("<4d", sourceData, sourceOffset):
                    source.attributes.append(p)
                sourceOffset += 32
            else:
                raise ValueError("Unknown particle type {}".format(pType))
            
            for p in struct.unpack_from("<28dii", sourceData, sourceOffset):
                source.attributes.append(p)
            
            result.sources.append(source)
        
        return result
    
    def dumpsVXN(self):
        data = b""
        data += struct.pack("<4sBI", b"FvXn", self.version, self.flags)
        
        for source in self.sources:
            data += struct.pack("<2sIB", b"m!", source.type, source.version)
            data += struct.pack("<4Iii5d", *source.attributes[:11])
            offset = 11
            
            if source.type == 1:
                data += struct.pack("<i12d", *source.attributes[offset:offset+13])
                offset += 13
            
            elif source.type == 2:
                data += struct.pack("<4d", *source.attributes[offset:offset+4])
                offset += 4
            
            data += struct.pack("<28dii", *source.attributes[offset:offset+30])
            
        return data
    
    def dumpsTxt(self):
        data = "HORUS VXN TEXT\n"
        data += "version {}\n".format(self.version)
        data += "flags 0b{:0>32b}\n".format(self.flags)
        data += "start sources\n"
        i = 0
        for source in self.sources:
            data += "    start source {}\n".format(i)
            data += "        version {}\n".format(source.version)
            data += "        type {}\n".format(source.type)
            data += "        start attributes\n"
            ii = 0
            for attribute in source.attributes:
                attrName = "attr{}".format(ii)
                
                #Resolve the name if we have it
                if ii in particleAttributeMetadata[source.type]["names"]:
                    attrName = particleAttributeMetadata[source.type]["names"][ii]
                
                if type(attribute) == int:
                    data += "            {} {}\n".format(attrName, attribute)
                elif type(attribute) == float:
                    data += "            {} {}\n".format(attrName, attribute)
                else:
                    print("Invalid attribute value!")
                    return None
                
                ii += 1
            
            data += "        end attributes\n"
            data += "    end source\n"
            i += 1
        data += "end sources\n"
        
        return data.strip().encode()
    
    def dumpsMessage(self):
        data = b"VXNASC" 
        
        data += base.b220encode(self.version, 1)
        data += base.b220encode(self.flags, 4)
        
        for source in self.sources:
            data += b"m!"
            
            data += base.b220encode(source.type, 4)
            data += base.b220encode(source.version, 1)
            
            sourceData = list(struct.pack("<4Iii5d", *source.attributes[:11]))
            offset = 11
            
            if source.type == 1:
                sourceData += list(struct.pack("<i12d", *source.attributes[offset:offset+13]))
                offset += 13
            
            elif source.type == 2:
                sourceData += list(struct.pack("<4d", *source.attributes[offset:offset+4]))
                offset += 4
            
            sourceData += list(struct.pack("<28dii", *source.attributes[offset:offset+30]))
            for byte in sourceData:
                data += base.b220encode(byte, 2)
        
        return data
