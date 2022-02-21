#!/usr/bin/env python3
from .character import Character
from .character import Costume
from .colors import Colors
import datetime
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET

class LoginError(Exception):
    pass

class Account:
    loginServer = "https://charon.furcadia.com/accounts/clogin.php"
    def __init__(self, id, email = None):
        self.id = id
        self.email = email
        self.characters = []
        pass
    
    def addCharacter(self, char):
        self.characters.append(char)
    
    def findCharacter(self, charname):
        for character in self.characters:
            if character.name == charname: #TODO: Compare by shortname
                return character
        return None
    
    @classmethod
    def login(cls, username, password, loginServer = None):
        data = urllib.parse.urlencode({
            "u": username,
            "p": password,
            "k": "ZAWJuuaTpRrG-Furcadia-KFzsVWwpPM9t",
            "v": "libfurc"
        })
        
        #TODO: Make this async
        req = urllib.request.Request(
            loginServer or cls.loginServer,
            data = data.encode(),
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            method = "POST"
        )
        
        with urllib.request.urlopen(req) as res:
            root = ET.fromstring(res.read())
            account = None
            #Find the account entry (Future proofing)
            for child in root:
                if child.tag == "account":
                    account = child
                    break
            
            if account == None:
                raise LoginError("No account element located!")
            
            self = cls(int(account.attrib["id"]), account.attrib.get("email", None))
            
            for character in account:
                char = Character(
                    id = character.attrib["id"],
                    name = character.attrib["name"],
                    species = character.attrib["species"],
                    colors = Colors.fromCode(character.attrib["colors"]),
                    flags = int(character.attrib["flags"]),
                    created = datetime.datetime.strptime(character.attrib["created"], "%Y-%m-%d %H:%M:%S"),
                    lastLogin = datetime.datetime.strptime(character.attrib["lastlogin"], "%Y-%m-%d %H:%M:%S"),
                    lastItem = int(character.attrib["lastitem"]),
                    lastPort = int(character.attrib["lastport"]),
                    lastScale = int(character.attrib["lastscale"]),
                    lastGloam = int(character.attrib["lastgloam"]),
                    lastSpeci = int(character.attrib["lastspeci"]),
                    messages = int(character.attrib["messages"]),
                    logins = int(character.attrib["logins"]),
                    time = int(character.attrib["time"]),
                    owner = self
                )
                
                for costume in character:
                    if costume.tag == "costume":
                        char.addCostume(Costume(
                            character = char,
                            id = int(costume.attrib["id"]),
                            name = costume.attrib["name"],
                            ordinal = int(costume.attrib["ordinal"]),
                            colors = Colors.fromCode(costume.attrib["colors"]),
                            lastPortrait = int(costume.attrib["last_portrait"]),
                            lastScale = int(costume.attrib["last_scale"]),
                            lastGloam = int(costume.attrib["last_gloam"]),
                            lastSpecitag = int(costume.attrib["last_specitag"]),
                            standard = int(costume.attrib["standard"]),
                            desc = costume.text
                        ))
                    elif costume.tag == "desc":
                        char.desc = costume.text
                
                self.addCharacter(char)
            
        return self