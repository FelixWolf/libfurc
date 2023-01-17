#!/usr/bin/env python3 
from . import base

#TODO: Convert to bytesIO?
class FurcBuffer:
    def __init__(self, buffer = None):
        if buffer == None:
            buffer = b""
        self.buffer = buffer
        self.offset = 0
    
    def __bytes__(self):
        return self.buffer
    
    @property
    def eof(self):
        return self.offset >= len(self.buffer)
    
    @property
    def remaining(self):
        return len(self.buffer) - self.offset
    
    
    
    def read(self, l = None):
        if l == None:
            v = self.buffer[self.offset:]
            self.offset = len(self.buffer)
        else:
            v = self.buffer[self.offset:self.offset+l]
            self.offset += l
        return v
    
    def write(self, data):
        self.buffer = self.buffer[:self.offset] + data + self.buffer[self.offset + len(data):]
        self.offset += len(data)
    
    
    def readBuffer(self, l = 1):
        return FurcBuffer(self.read(l))
    
    def writeBuffer(self, v):
        self.write(v.buffer)
    
    
    def readUntil(self, seperator = b" "):
        data = b""
        while not self.eof:
            c = self.read(1)
            if c == seperator:
                return data
            data += c
        return data
    
    
    
    def read95(self, l = 1):
        try:
            return base.b95decode(self.read(l))
        except ValueError as e:
            raise ValueError("Failed to decode message {} at {}".format(self.buffer, self.offset - l))
    
    def write95(self, v, l = 1):
        self.write(base.b95encode(v, l))
    
    
    def read95Bytes(self, l = 1):
        try:
            return self.read(base.b95decode(self.read(l)))
        except ValueError as e:
            raise ValueError("Failed to decode message {} at {}".format(self.buffer, self.offset - l))
    
    def write95Bytes(self, data, l = 1):
        if len(data)/95 > l:
            raise ValueError("Can't pack data size of {} is greater than b95 size of {}".format(len(data)/95, l))
        
        self.write(base.b95encode(len(data), l))
        self.write(data)
    
    
    def read95String(self, l = 1):
        return self.read95Bytes(l).decode()
    
    def write95String(self, v, l = 1):
        return self.write95Bytes(v.encode(), l)
    
    
    
    def read220(self, l = 1):
        try:
            return base.b220decode(self.read(l))
        except ValueError as e:
            raise ValueError("Failed to decode message {} at {}".format(self.buffer, self.offset - l))
    
    def write220(self, v, l = 1):
        self.write(base.b220encode(v, l))
    
    
    def read220Bytes(self, l = 1):
        try:
            return self.read(base.b220decode(self.read(l)))
        except ValueError as e:
            raise ValueError("Failed to decode message {} at {}".format(self.buffer, self.offset - l))
    
    def write220Bytes(self, data, l = 1):
        if len(data)/220 > l:
            raise ValueError("Can't pack data size of {} is greater than b220 size of {}".format(len(data)/220, l))
        
        self.write(base.b220encode(len(data), l))
        self.write(data)
    
    
    def read220ByteArray(self, l = 1):
        result = []
        for i in range(l):
            v = self.read220(self.read(2))
            if v > 255: #No need to check for underflow, base220 is unsigned.
                raise ValueError("Base 220 byte array in message {} at {} is out of range!".format(self.buffer, self.offset - 2))
            result.append(v)
        
        return bytes(result)
    
    def write220ByteArray(self, v, l = 1):
        if len(v) / 220 > l:
            raise ValueError("Can't pack data size of {} is greater than b220 size of {}".format(len(data)/220, l))
        
        self.write220(len(v), l)
        for i in v:
            self.write220(v, 2)
    
    
    def read220String(self, l = 1):
        return self.read220Bytes(l).decode()
    
    def write220String(self, v, l = 1):
        return self.write220Bytes(v.encode(), l)