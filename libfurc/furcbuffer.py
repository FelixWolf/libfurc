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
    
    def readUntil(self, seperator = b" "):
        data = b""
        while not self.eof:
            c = self.read(1)
            if c == seperator:
                return data
            data += c
        return data
    
    def read95(self, l = 1):
        return base.b95decode(self.read(l))
    
    def read220(self, l = 1):
        return base.b220decode(self.read(l))
    
    def read95Bytes(self, l = 1):
        return self.read(base.b95decode(self.read(l)))
    
    def read95String(self, l = 1):
        return self.read95Bytes(l).decode()
    
    def read220Bytes(self, l = 1):
        return self.read(base.b220decode(self.read(l)))
    
    def read220String(self, l = 1):
        return self.read220Bytes(l).decode()