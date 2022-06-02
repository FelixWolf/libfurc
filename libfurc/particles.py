#!/usr/bin/env python3
import struct
from . import base

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
            
            sourceData += list(struct.pack("<28di", *source.attributes[offset:offset+30]))
            
            for byte in sourceData:
                data += base.b220encode(byte, 2)
        
        return data
