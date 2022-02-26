#!/usr/bin/env python3 
import asyncio
from . import base
from .account import Character
from .colors import Colors

LIVE_SERVER = ("lightbringer.furcadia.com", 6500)

class FurcMessageReader:
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
        return data
    
    def read95(self, l):
        return base.b95decode(self.read(l))
    
    def read220(self, l):
        return base.b220decode(self.read(l))
    
    def read95Bytes(self, l=1):
        return self.read(base.b95decode(self.read(l)))
    
    def read95String(self, l=1):
        return self.read95Bytes(l).decode()
    
    def read220Bytes(self, l=1):
        return self.read(base.b220decode(self.read(l)))
    
    def read220String(self, l=1):
        return self.read220Bytes(l).decode()

#Incoming message definitions
class DefaultPacketHandler:
    async def message_unhandled(self, opcode, data):
        print("Unhandled {}".format(opcode+32), data)

class PacketHooks(DefaultPacketHandler):
    def __init__(self, useLookups = False):
        self.listeners = {}
        self.lookup = None
        if useLookups:
            self.generateLookups()
    
    def generateLookups(self):
        self.lookup = {}
        for entry in dir(self):
            if entry.startswith("message_"):
                try:
                    n = entry.split("_")[1:]
                    if len(n) == 1:
                        n = int(n[0])
                    else:
                        n = (int(n[0]), int(n[1]))
                    self.lookup[n] = getattr(self, entry)
                except ValueError:
                    pass
    
    #Meta messages
    async def message_motd(self, message):
        await self.fire("MOTD", message)
    
    #Messages
    #" " - Remove avatar by ID
    async def message_1(self, opcode, data):
        avatars = []
        msg = FurcMessageReader(data)
        while msg.remaining >= 4:
            avatars.append(msg.read220(4))
        await self.fire("RemoveAvatarID", avatars)
    
    #"!" - Sound
    async def message_1(self, opcode, data):
        await self.fire("Sound", base.b95decode(data[0:2]))
    
    #"%" - Standing on object
    async def message_5(self, opcode, data):
        await self.fire("ButlerFeet", base.b95decode(data[0:2]))
    
    #"&" - Login success
    async def message_6(self, opcode, data):
        await self.fire("Login", True)
    
    #"(" - Text message
    async def message_8(self, opcode, data):
        await self.fire("Message", data)
    
    #")" - Remove avatar at location
    async def message_9(self, opcode, data):
        avatars = []
        msg = FurcMessageReader(data)
        while msg.remaining >= 8:
            avatars.append((msg.read220(4), msg.read220(4)))
        await self.fire("RemoveAvatarLocation", avatars)
    
    #"/" - Animate avatar
    async def message_15(self, opcode, data):
        avatars = {}
        msg = FurcMessageReader(data)
        while msg.remaining >= 16:
            avatars[msg.read220(4)] = {
                "pos": (msg.read220(4), msg.read220(4)),
                "patch": msg.read220(4)
            }
        await self.fire("AnimateAvatar", avatars)
    
    #"0" - Sync dream variables
    async def message_16(self, opcode, data):
        msg = FurcMessageReader(data)
        start = msg.read95(2)
        offset = 0
        variables = {}
        remaining = 0
        while msg.remaining >= 6:
            x, y = msg.read95(3), msg.read95(3)
            if x == 0x4000:
                remaining = y
            else:
                variables[start+offset] = (x, y)
            offset += 1
        await self.fire("UpdateVariables", variables, remaining)
    
    #"1" - Set floors
    async def message_17(self, opcode, data):
        msg = FurcMessageReader(data)
        result = []
        while msg.remaining >= 20:
            result.append({
                "pos": (msg.read95(2), msg.read95(2)),
                "id": msg.read95(2)
            })
        self.fire("SetFloor", result)
    
    #"2" - Set floors
    async def message_18(self, opcode, data):
        msg = FurcMessageReader(data)
        result = []
        while msg.remaining >= 20:
            result.append({
                "pos": (msg.read95(2), msg.read95(2)),
                "id": msg.read95(2)
            })
        self.fire("SetWall", result)
    
    #"3" - Set all DS variables
    async def message_19(self, opcode, data):
        msg = FurcMessageReader(data)
        vals = []
        while msg.remaining >= 3:
            vals.append(msg.read95(3))
        self.fire("SetVariables", result)
    
    #"4" - Set region
    async def message_20(self, opcode, data):
        msg = FurcMessageReader(data)
        result = []
        while msg.remaining >= 20:
            result.append({
                "pos": (msg.read95(2), msg.read95(2)),
                "id": msg.read95(2)
            })
        self.fire("SetRegion", result)
    
    #"5" - Set effect
    async def message_21(self, opcode, data):
        msg = FurcMessageReader(data)
        result = []
        while msg.remaining >= 20:
            result.append({
                "pos": (msg.read95(2), msg.read95(2)),
                "id": msg.read95(2)
            })
        self.fire("SetEffect", result)
    
    #"6" - DS event triggered by player
    async def message_22(self, opcode, data):
        msg = FurcMessageReader(data)
        from_x = msg.read95(2)
        from_y = msg.read95(2)
        to_x = msg.read95(2)
        to_y = msg.read95(2)
        line = msg.read95(2)
        if line > 8000:
            line = line - 8000 + (msg.read95(2) * 1000)
        trig_x = msg.read95(2)
        trig_y = msg.read95(2)
        result = {
            "from": (from_x, from_y),
            "to": (to_x, to_y),
            "line": line,
            "triggerer": (trig_x, trig_y)
        }
        self.fire("DSEvent", True, result)
    
    #"7" - DS event triggered by other
    async def message_23(self, opcode, data):
        msg = FurcMessageReader(data)
        from_x = msg.read95(2)
        from_y = msg.read95(2)
        to_x = msg.read95(2)
        to_y = msg.read95(2)
        line = msg.read95(2)
        if line > 8000:
            line = line - 8000 + (msg.read95(2) * 1000)
        trig_x = msg.read95(2)
        trig_y = msg.read95(2)
        result = {
            "from": (from_x, from_y),
            "to": (to_x, to_y),
            "line": line,
            "triggerer": (trig_x, trig_y)
        }
        self.fire("DSEvent", False, result)
    
    #"8" - DS event addon
    async def message_24(self, opcode, data):
        msg = FurcMessageReader(data)
        self.fire("DSEventAddon", {
            "moveFlag": msg.read95(1),
            "randSeed": msg.read95(5),
            "saidNum": msg.read95(3),
            "facingDir": msg.read95(1),
            "entryCode": msg.read95(3),
            "objPaws": msg.read95(3),
            "furreCount": msg.read95(2),
            "userID": msg.read95(6),
            "DSBtn": msg.read95(2),
            "dreamCookies": msg.read95(3),
            "triggererCookies": msg.read95(2),
            "portalOpen": (msg.read95(2), msg.read95(2)),
            "second": msg.read95(1),
            "minute": msg.read95(1),
            "hour": msg.read95(1),
            "day": msg.read95(1),
            "month": msg.read95(1),
            "year": msg.read95(2),
            "portalClose": (msg.read95(2), msg.read95(2))
        })
    
    #"9" - Region flags
    async def message_25(self, opcode, data):
        msg = FurcMessageReader(data)
        regions = {}
        while msg.remaining >= 8:
            index = msg.read95(3)
            flag = msg.read95(3)
            count = msg.read95(2)
            for i in range(count):
                regions[0xFFFF & i] = flag
                
        self.fire("RegionFlags", regions)
    
    #";" - Load map
    async def message_27(self, opcode, data):
        self.fire("DSEventAddon", data.decode())
    
    #"<" - Spawn avatar
    async def message_28(self, opcode, data):
        msg = FurcMessageReader(data)
        result = []
        while msg.remaining >= 20:
            result.append({
                "userID": msg.read220(4),
                "pos": (msg.read220(2), msg.read220(2)),
                "patch": msg.read220(2),
                "name": msg.read220String(),
                "color": Colors.fromStream(msg),
                "flags": msg.read220(2),
                "afk": msg.read220(2),
                "scale": msg.read220(2)
            })
        self.fire("SpawnAvatar", result)
    
    #"=" - Resume drawing
    async def message_29(self, opcode, data):
        self.fire("Suspend", False)
    
    #">" - Spawn object
    async def message_30(self, opcode, data):
        msg = FurcMessageReader(data)
        result = []
        while msg.remaining >= 20:
            result.append({
                "pos": (msg.read95(2), msg.read95(2)),
                "id": msg.read95(2)
            })
        self.fire("SetObject", result)
    
    #"@" - Move camera
    async def message_32(self, opcode, data):
        msg = FurcMessageReader(data)
        result = {
            "to": (msg.read95(2), msg.read95(2))
        }
        while msg.remaining >= 2:
            result["from"] = (msg.read95(2), msg.read95(2))
        self.fire("MoveCamera", result)
    
    #"A" - Move avatars
    async def message_33(self, opcode, data):
        msg = FurcMessageReader(data)
        avatars = {}
        while msg.remaining >= 10:
            avatars[msg.read220(4)] = {
                "pos": (msg.read220(4), msg.read220(4)),
                "patch": msg.read220(4)
            }
        self.fire("MoveAvatar", avatars)
    
    #"B" - Set avatar colors
    async def message_34(self, opcode, data):
        msg = FurcMessageReader(data)
        avatars = {}
        while msg.remaining >= 16:
            avatars[msg.read220(4)] = {
                "patch": msg.read220(4),
                "colors":   Colors.fromStream(msg),
            }
        self.fire("SetAvatarColors", avatars)
    
    #"C" - Hide avatar at position
    async def message_35(self, opcode, data):
        msg = FurcMessageReader(data)
        avatars = {}
        while msg.remaining >= 8:
            avatars[msg.read220(4)] = {
                "pos": (msg.read220(4), msg.read220(4)),
                "patch": msg.read220(4)
            }
        self.fire("HideAvatar", avatars)
    
    #"D" - Set triggering furre
    #WARNING: Probably deprecated
    async def message_36(self, opcode, data):
        msg = FurcMessageReader(data)
        self.fire("DSTriggerer", msg.read220(4))
    
    #"[" - Server authenticate
    async def message_59(self, opcode, data):
        self.fire("Disconnect", data.decode())
    
    #"\" - Server authenticate
    async def message_60(self, opcode, data):
        self.fire("Authenticate", data.decode())
    
    #"]" - Protocol extension
    async def message_61(self, opcode, data):
        if len(data) < 2:
            return
        await getattr(
            self,
            "message_61_" + str(data[0]-32),
            self.message_61_unhandled
        )(data[0]-32, data[1:])
    
    #Default handler
    async def message_61_unhandled(self, opcode, data):
        print("Unhandled 61:{}".format(opcode), data)
    
    #"]!" - Adult warning
    async def message_61_1(self, opcode, data):
        await self.fire("AdultWarning")
    
    #"]#" - Dialog
    async def message_61_3(self, opcode, data):
        msg = FurcMessageReader(data)
        await self.fire("Dialog",
            int(msg.readUntil().decode()), #Dialog ID
            int(msg.readUntil().decode()), #Dialog Type
            msg.read()
        )
    
    #"]$" - Open URL
    async def message_61_4(self, opcode, data):
        await self.fire("OpenURL", False, data)
    
    #"]%" - Online reply
    async def message_61_5(self, opcode, data):
        await self.fire("OnlineStatus",
            data[0] == 49, #Status bool
            data[1:]
        )
    
    #"]&" - Set portrait
    async def message_61_6(self, opcode, data):
        msg = FurcMessageReader(data)
        await self.fire("Portrait",
            int(msg.readUntil().decode()), #Portrait ID
            msg.read() #Portrait name
        )
    
    #"]*" - Show URL
    async def message_61_4(self, opcode, data):
        await self.fire("OpenURL", True, data)
    
    #"]-" - Prefix text
    async def message_61_13(self, opcode, data):
        await self.fire("Prefix", data)
    
    #"]3" - Show user list
    async def message_61_19(self, opcode, data):
        await self.fire("UserList",
            data[0] == 49 #0 = Show usercount + list, 1 = Only count
        )
    
    #"]A" - Guild tag related?
    #FIXME: Figure out how this works
    async def message_61_34(self, opcode, data):
        await self.fire("GuildTagA", data)
    
    #"]B" - Set user ID
    async def message_61_34(self, opcode, data):
        await self.fire("SetUserID", int(data.decode()))
    
    #"]C" - Bookmark Dream
    async def message_61_35(self, opcode, data):
        msg = FurcMessageReader(data)
        await self.fire("Bookmark",
            data[0] == 49, #0 = Temporary, 1 = User request
            data[1:].decode() #FDL
        )
    
    #"]D" - Begin share edit
    async def message_61_36(self, opcode, data):
        #Activate, Is Owner
        await self.fire("LiveEdit", True, False)
    
    #"]E" - Begin share edit
    async def message_61_37(self, opcode, data):
        #Activate, Is Owner
        await self.fire("LiveEdit", True, True)
    
    #"]F" - Begin share edit
    async def message_61_38(self, opcode, data):
        #Activate, Is Owner
        await self.fire("LiveEdit", False, False)
    
    #"]G" - Disable tab key
    async def message_61_39(self, opcode, data):
        await self.fire("DisableTab",
            data[0] == 49 #0 = Enable, 1 = Disable
        )
    
    #"]H" - Offset avatar
    async def message_61_39(self, opcode, data):
        msg = FurcMessageReader(data)
        avatars = {}
        while msg.remaining >= 8:
            avatars[msg.read220(4)] = {
                "userID": msg.read220(4),
                "pos": (msg.read220(4), msg.read220(4)),
            }
        self.fire("OffsetAvatar", avatars)
    
    #"]I" - Particle Effect
    async def message_61_41(self, opcode, data):
        await self.fire("Particles", data)
    
    #"]J" - Particle Effect
    async def message_61_42(self, opcode, data):
        await self.fire("WebMap", data)
    
    #"]M" - Dynamic Avatars Info
    async def message_61_45(self, opcode, data):
        #TODO: Decode this
        #Should be:
        #(
        #    base220 syntax,
        #   [
        #       (
        #           base220 avatarVersion,
        #           base220 gender,
        #           base220 special
        #       ),
        #   ...
        #   ]
        #)
        #But probably has changed since the new fox format was introduced
        await self.fire("DynamicAvatars", data)
    
    #"]P" - Guild tag related?
    #FIXME: Figure out how this works
    async def message_61_34(self, opcode, data):
        await self.fire("GuildTagB", data)
    
    #"]W" - Region settings
    #FIXME: This has changed!
    async def message_61_55(self, opcode, data):
        msg = FurcMessageReader(data)
        await self.fire("RegionSettings", {
            "outdoor": {
                "object": msg.read220(2),
                "wall": msg.read220(2),
                "floor": msg.read220(2),
                "effect": msg.read220(2),
            },
            "indoor": {
                "object": msg.read220(2),
                "wall": msg.read220(2),
                "floor": msg.read220(2),
                "effect": msg.read220(2),
            },
            "unk": msg.read220(2),
            "walls": {
                "bottom": msg.read220(1),
                "top": msg.read220(1),
            }
        })
    
    #"]]" - Login failure
    async def message_61_61(self, opcode, data):
        await self.fire("Login", False)
    
    #"]_" - Kitterdust
    async def message_61_39(self, opcode, data):
        msg = FurcMessageReader(data)
        avatars = {}
        while msg.remaining >= 5:
            avatars[msg.read220(4)] = msg.read220(1)
        self.fire("KitterDust", avatars)
    
    #"]a" - Waiting for dream
    #FIXME: Confirm this is correct
    async def message_61_65(self, opcode, data):
        await self.fire("UploadReady")
    
    #"]c" - Set marbled
    async def message_61_67(self, opcode, data):
        #This has a "c" prefixed to it
        await self.fire("Marbled", data[1:].decode())
    
    #"]f" - Look
    async def message_61_70(self, opcode, data):
        msg = FurcMessageReader(data)
        await self.fire("Look", Colors.fromStream(msg), msg.read().decode())
    
    #"]j" - Look
    async def message_61_74(self, opcode, data):
        await self.fire("Music", base.b95decode(data[0:2]))
    
    #"]m" - Marco
    async def message_61_77(self, opcode, data):
        msg = FurcMessageReader(data)
        msg.readUntil()
        await self.fire("Marco", msg.read())
    
    #"]o" - Dream owner name
    async def message_61_79(self, opcode, data):
        msg = FurcMessageReader(data)
        await self.fire("DreamOwner", msg.read())
    
    #"]q" - Load dream with custom patches
    async def message_61_81(self, opcode, data):
        msg = FurcMessageReader(data)
        msg.readUntil()
        await self.fire("Dream", True, msg.readUntil(), msg.readUntil())
    
    #"]r" - Load dream with default patches
    async def message_61_82(self, opcode, data):
        msg = FurcMessageReader(data)
        msg.readUntil()
        await self.fire("Dream", False, msg.readUntil(), msg.readUntil())
    
    #"]s" - Place text at location
    async def message_61_83(self, opcode, data):
        msg = FurcMessageReader(data)
        await self.fire("Text",
            (msg.read95(2), msg.read95(2)),
            int(msg.readUntil()), #Type?
            msg.readUntil(), #Name
            msg.readUntil(), #Title
            int(msg.readUntil()), #Maturity?
        )
    
    #"]t" - Clear text at location
    async def message_61_84(self, opcode, data):
        msg = FurcMessageReader(data)
        await self.fire("ClearText", (msg.read95(2), msg.read95(2)))
    
    #"]u" - Waiting for dream
    #FIXME: Confirm this is correct
    async def message_61_85(self, opcode, data):
        await self.fire("UploadReady")
    
    #"]v" - Effect
    async def message_61_86(self, opcode, data):
        msg = FurcMessageReader(data)
        await self.fire("Effect",
            msg.read(1).decode(), #Type
            (msg.read95(2),msg.read95(2)) #Location
        )
    
    #"]w" - Version request
    async def message_61_87(self, opcode, data):
        await self.fire("VersionReq")
    
    #"]x" - Client should update
    async def message_61_88(self, opcode, data):
        await self.fire("Update")
    
    #"]z" - UID response
    async def message_61_88(self, opcode, data):
        await self.fire("UID", int(data.decode()))
    
    #"]{" - Session ID
    async def message_61_91(self, opcode, data):
        await self.fire("SessionID", int(data.decode()))
    
    #"]|" - Flip screen
    async def message_61_92(self, opcode, data):
        await self.fire("FlipScreen", data[0] == 49)
    
    #"]}" - Set own colors
    async def message_61_93(self, opcode, data):
        msg = FurcMessageReader(data)
        await self.fire("SetColors", Colors.fromStream(msg))
    
    #"^" - Item in hand
    async def message_62(self, opcode, data):
        self.fire("ButlerPaws", base.b95decode(data[0:2]))
    
    #"~" - Suspend drawing
    async def message_94(self, opcode, data):
        self.fire("Suspend", True)
    
    #Hook definitions
    async def fire(self, name, *args, **kwargs):
        if name not in self.listeners:
            return False
        
        for callback in self.listeners[name]:
            await callback(*args, **kwargs)
        
        if "*" in self.listeners:
            for callback in self.listeners["*"]:
                await callback(name, *args, **kwargs)
        
        return True
    
    def on(self, name, *args, **kwargs):
        def _(func):
            if name not in self.listeners:
                self.listeners[name] = []
            self.listeners[name].append(func)
            return func
        return _
    
    def off(self, name, func):
        if name not in self.listeners:
            return
        self.listeners[name].remove(name)

#Outgoing message definitions
class Commands:
    def login(self, character):
        if character.type == character.TYPE_INI:
            return self.command("connect {} {}".format(
                character.name,
                character.password
            ))
        elif character.type == character.TYPE_ACCOUNT:
            return self.command("account {} {} {} {}".format(
                character.account.username,
                character.name,
                character.account.password,
                "" #TODO: Machine ID goes here
            ))
    
    def move(self, direction):
        return self.command("m {}".format(direction))
    
    def rotate(self, direction):
        if direction == 1:
            return self.command(">")
        elif direction == -1:
            return self.command("<")
    
    def say(self, message):
        return self.command("\"" + message)
    
    def gomap(self, mapid):
        return self.command("gomap " + encoding.b95encode(mapid))
    
    def fdl(self, url):
        return self.command("fdl "+url)
    
    def goToDream(self, furrename, dreamname = None):
        #TODO: URL Escape the names, could probably just shortname them
        url = "furc://" + furrename
        if dreamname:
            url += ":" + dreamname
        return self.fdl(url)

class Client(PacketHooks, Commands):
    def __init__(self, server = None):
        super().__init__()
        self.reader = None
        self.writer = None
        self.server = server or LIVE_SERVER
    
    #Basic networking stuff
    async def connect(self, server = None, loop = None):
        if self.connected:
            await self.disconnect()
        
        if not server:
            server = self.server
        
        self.reader, self.writer = await asyncio.open_connection(
            server[0], server[1])
        
        await self.readLoop()
    
    async def disconnect(self):
        writer.close()
        await writer.wait_closed()
        self.reader = None
        self.writer = None
    
    async def send(self, data):
        print("<", data)
        if self.connected:
            self.writer.write(data)
            await self.writer.drain()
            return True
        return False
    
    def command(self, data):
        if type(data) == str:
            data = data.encode()
        return self.send(data + b"\n")
    
    @property
    def connected(self):
        if self.reader == None or self.writer == None:
            return False
        return True
    
    #Actual read loop, it is designed to be it's own task
    async def readLoop(self):
        motd = ""
        #Wait for MOTD
        #TODO: Add timeout
        #TODO: Move this to connect() and return MOTD from there
        while self.connected:
            data = await self.reader.readline()
            
            if not data: #None = Disconnected
                break
            
            if data[-1] != 10: #No EOL means incomplete stream + disconnected
                break
            
            if data == b"Dragonroar\n":
                await getattr(
                    self,
                    "message_motd",
                    self.message_unhandled
                )(motd)
                motd = None
                break
            else:
                motd += data.decode()
        
        #Connected loop
        while self.connected:
            data = await self.reader.readline()
            
            if not data: #None = Disconnected
                break
            
            if data[-1] != 10: #No EOL means incomplete stream + disconnected
                break
            
            data = data[:-1] #Strip EOL
            
            if len(data) == 0: #If empty, ignore
                continue
            
            await getattr(
                self,
                "message_" + str(data[0]-32),
                self.message_unhandled
            )(data[0]-32, data[1:])
        
        #We are out of the loop! Presume Disconnected!
        self.reader = None
        self.writer = None