#!/usr/bin/env python3

class Color:
    def __init__(self, id, type, rgb):
        pass

class Colors:
    def __init__(self):
        pass
    
    @classmethod
    def fromCode(cls, data):
        self = cls()
        
        return self
    
    @classmethod
    def fromStream(cls, data):
        version = data.read(1)[0]
        self = cls()
        if version == 116:
            code = data.read(10)
            if len(code) != 10:
                raise ValueError("Invalid color code!")
        else:
            raise ValueError("Invalid color code!")
        return self
