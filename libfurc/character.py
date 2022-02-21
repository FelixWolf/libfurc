#!/usr/bin/env python3

class Costume:
    def __init__(self, character, id, name, ordinal = None, colors = None,
                 lastPortrait = 0, lastScale = 100, lastGloam = 0,
                 lastSpecitag = 0, standard = 200, desc = ""):
        self.character = character
        self.id = id
        self.name = name
        self.ordinal = ordinal
        self.colors = colors
        self.lastPortrait = lastPortrait
        self.lastScale = lastScale
        self.lastGloam = lastGloam
        self.lastSpecitag = lastSpecitag
        self.standard = standard
        self.desc = desc

class Character:
    def __init__(self, id, name, species = "", colors = "", flags = 0,
                 created = None, lastLogin = None, lastItem = None,
                 lastPort = 0, lastScale = 100, lastGloam = 0, lastSpeci = 0,
                 messages = 0, logins = 0, time = 0, owner = None, desc = ""):
        self.id = id
        self.name = name
        self.species = species
        self.colors = colors
        self.flags = flags
        self.created = created
        self.lastLogin = lastLogin
        self.lastItem = lastItem
        self.lastPort = lastPort
        self.lastScale = lastScale
        self.lastGloam = lastGloam
        self.lastSpeci = lastSpeci
        self.messages = messages
        self.logins = logins
        self.time = time
        self.owner = owner
        self.desc = desc
        self.costumes = []
    
    def addCostume(self, costume):
        self.costumes.append(costume)
    
