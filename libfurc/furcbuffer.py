#!/usr/bin/env python3 
from . import base

class FurcBuffer:
    def __init__(self, buffer):
        self.buffer = buffer
        self.offset = 0

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
    
    def readBuffer(self, l = 1):
        return FurcBuffer(self.read(l))
    
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
    
    def read220(self, l = 1):
        try:
            return base.b220decode(self.read(l))
        except ValueError as e:
            raise ValueError("Failed to decode message {} at {}".format(self.buffer, self.offset - l))
    
    def read95Bytes(self, l = 1):
        try:
            return self.read(base.b95decode(self.read(l)))
        except ValueError as e:
            raise ValueError("Failed to decode message {} at {}".format(self.buffer, self.offset - l))
    
    def read95String(self, l = 1):
        return self.read95Bytes(l).decode()
    
    def read220Bytes(self, l = 1):
        try:
            return self.read(base.b220decode(self.read(l)))
        except ValueError as e:
            raise ValueError("Failed to decode message {} at {}".format(self.buffer, self.offset - l))
    
    def read220ByteArray(self, l = 1):
        result = []
        for i in range(l):
            v = self.read220(self.read(2))
            if v > 255: #No need to check for underflow, base220 is unsigned.
                raise ValueError("Base 220 byte array in message {} at {} is out of range!".format(self.buffer, self.offset - 2))
            result.append(v)
        
        return bytes(result)
    
    def read220String(self, l = 1):
        return self.read220Bytes(l).decode()