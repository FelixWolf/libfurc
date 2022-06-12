#!/usr/bin/env python3

class Colors:
    def __init__(self, version = 116):
        self.version = version
        self.fur = 0
        self.markings = 0
        self.hair = 0
        self.eye = 0
        self.badge = 0
        self.vest = 0
        self.bracer = 0
        self.cape = 0
        self.boot = 0
        self.trousers = 0
        self.wings = 0
        self.accent = 0
        self.gender = None
        self.species = None
        self.avatar = None
    
    def __repr__(self):
        values = ("F: {}; M: {}; E: {}; Ba: {}; V: {}; " \
               + "Br: {}; C: {}; B: {}; T: {}; W: {}; " \
               + "Ac: {}").format(
                   self.fur, self.markings, self.hair, self.hair, self.eye,
                   self.badge, self.vest, self.bracer, self.cape, self.boot,
                   self.trousers, self.wings, self.accent
                )
        if self.gender:
            values += "; G: {}".format(self.gender)
        if self.species:
            values += "; S: {}".format(self.species)
        if self.avatar:
            values += "; Av: {}".format(self.avatar)
        
        return "<Colors({}) {}>".format(self.version, values)
    
    @classmethod
    def fromCode(cls, data):
        self = cls()
        
        return self
    
    @classmethod
    def fromStream(cls, data, readAvatar = True):
        version = data.read(1)[0]
        self = cls(version)
        if version == 116: #t
            if data.remaining < 10:
                raise ValueError("Invalid color code length!")
            
            self.fur = data.read220()
            self.markings = data.read220()
            self.hair = data.read220()
            self.eye = data.read220()
            self.badge = data.read220()
            self.vest = data.read220()
            self.bracer = data.read220()
            self.cape = data.read220()
            self.boot = data.read220()
            self.trousers = data.read220()
            
            if data.remaining >= 1:
                self.gender = data.read220()
            
            if data.remaining >= 1:
                self.species = data.read220()
            
            if data.remaining >= 1:
                self.avatar = data.read220()
            
        elif version == 117: #u
            #TODO: Implement this
            #http://dev.furcadia.com/docs/new_color_code_format.pdf
            if data.remaining < 2:
                raise ValueError("Invalid color code length!")
            
            bitmask = (data.read220()&63) | (data.read220() << 6)
            
            for i in range(0, 10):
                if bitmask >> i & 1:
                    data.read(3)
                else:
                    data.read(1)
            
            if data.remaining >= 1:
                self.gender = data.read220()
            
            if data.remaining >= 1:
                self.species = data.read220()
            
            if data.remaining >= 1:
                self.avatar = data.read220()
        
        elif version == 118: #v
            #TODO: Implement this
            #http://dev.furcadia.com/docs/new_color_code_format.pdf
            if data.remaining < 27:
                raise ValueError("Invalid color code length!")
            
            data.read(27) # 9 * 3
            
            if data.remaining >= 1:
                self.gender = data.read220()
            
            if data.remaining >= 1:
                self.species = data.read220()
            
            if data.remaining >= 1:
                self.avatar = data.read220()
        
        elif version == 119: #w
            if data.remaining < 12:
                raise ValueError("Invalid color code length!")
            
            self.fur = data.read220()
            self.markings = data.read220()
            self.hair = data.read220()
            self.eye = data.read220()
            self.badge = data.read220()
            self.vest = data.read220()
            self.bracer = data.read220()
            self.cape = data.read220()
            self.boot = data.read220()
            self.trousers = data.read220()
            self.wings = data.read220()
            self.accent = data.read220()
            
            if data.remaining >= 1:
                self.gender = data.read220()
            
            if data.remaining >= 1:
                self.species = data.read220()
            
            if data.remaining >= 2 and readAvatar:
                self.avatar = data.read220(2)
            
        else:
            raise ValueError("Invalid color code version {}!".format(version))
        return self
