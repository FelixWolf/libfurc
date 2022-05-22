#!/usr/bin/env python3 
import asyncio
from . import base
from .furcbuffer import FurcBuffer
from .account import Character
from .colors import Colors

LIVE_SERVER = ("lightbringer.furcadia.com", 6500)

#Incoming message definitions
class DefaultPacketHandler:
    async def message_unhandled(self, opcode, data):
        print("Unhandled {}".format(opcode+32), data)

class PacketHooks(DefaultPacketHandler):
    def __init__(self, useLookups = False):
        self.listeners = {
            "*": []
        }
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
    
    #Messages
    #" " - Remove avatar by ID
    #FIXME: Unconfirmed
    async def message_1(self, opcode, data):
        avatars = []
        msg = FurcBuffer(data)
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
    
    #")" - Remove avatar
    async def message_9(self, opcode, data):
        avatars = []
        msg = FurcBuffer(data)
        msg.read220(4)
        await self.fire("RemoveAvatar", avatars)
    
    #"/" - Animate avatar
    #FIXME: New format
    async def message_15(self, opcode, data):
        avatars = {}
        msg = FurcBuffer(data)
        """New format:
            Base220(4) unk
            Base220(2) unk
            Base220(2) unk
            Base220(1) unk
            Base220(1) unk
        """
        while msg.remaining >= 16:
            avatars[msg.read220(4)] = {
                "pos": (msg.read220(4), msg.read220(4)),
                "patch": msg.read220(4)
            }
        await self.fire("AnimateAvatar", avatars)
    
    #"0" - Sync dream variables
    async def message_16(self, opcode, data):
        msg = FurcBuffer(data)
        variables = {}
        while msg.remaining >= 2:
            offset = msg.read95(2)
            while msg.remaining >= 6:
                val = msg.read95(3)
                if x != 0x4000:
                    variables[offset] = val
                    offset += 3
                else:
                    repeats = msg.read95(3) + 1
                    for i in range(repeats):
                        variables[offset] = v
                        offset += 3
        await self.fire("UpdateVariables", variables, remaining)
    
    #"1" - Set floors
    async def message_17(self, opcode, data):
        msg = FurcBuffer(data)
        result = []
        while msg.remaining >= 6:
            result.append({
                "pos": (msg.read220(2), msg.read220(2)),
                "id": msg.read220(2)
            })
        await self.fire("SetFloor", result)
    
    #"2" - Set floors
    async def message_18(self, opcode, data):
        msg = FurcBuffer(data)
        result = []
        while msg.remaining >= 6:
            result.append({
                "pos": (msg.read220(2), msg.read220(2)),
                "id": msg.read220(2)
            })
        await self.fire("SetWall", result)
    
    #"3" - Set all DS variables
    async def message_19(self, opcode, data):
        msg = FurcBuffer(data)
        vals = []
        while msg.remaining >= 3:
            vals.append(msg.read95(3))
        await self.fire("SetVariables", vals)
    
    #"4" - Set region
    async def message_20(self, opcode, data):
        msg = FurcBuffer(data)
        result = []
        while msg.remaining >= 6:
            result.append({
                "pos": (msg.read220(2), msg.read220(2)),
                "id": msg.read220(2)
            })
        await self.fire("SetRegion", result)
    
    #"5" - Set effect
    async def message_21(self, opcode, data):
        msg = FurcBuffer(data)
        result = []
        while msg.remaining >= 6:
            result.append({
                "pos": (msg.read220(2), msg.read220(2)),
                "id": msg.read220(2)
            })
        await self.fire("SetEffect", result)
    
    #"6" - DS event triggered by player
    #FIXME: Verify
    async def message_22(self, opcode, data):
        msg = FurcBuffer(data)
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
        await self.fire("DSEvent", True, result)
    
    #"7" - DS event triggered by other
    #FIXME: Verify
    async def message_23(self, opcode, data):
        msg = FurcBuffer(data)
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
        await self.fire("DSEvent", False, result)
    
    #"8" - DS event addon
    async def message_24(self, opcode, data):
        msg = FurcBuffer(data)
        await self.fire("DSEventAddon", {
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
        msg = FurcBuffer(data)
        regions = {}
        while msg.remaining >= 8:
            index = msg.read220(3)
            flag = msg.read220(3)
            count = msg.read220(2)
            for i in range(count):
                regions[0xFFFF & i] = flag
                
        await self.fire("RegionFlags", regions)
    
    #";" - Load map
    async def message_27(self, opcode, data):
        await self.fire("DSEventAddon", data.decode())
    
    #"<" - Spawn avatar
    #FIXME: New format
    async def message_28(self, opcode, data):
        msg = FurcBuffer(data)
        result = []
        """New format:
            Base220(4)
            Base220(2)
            Base220(1)
            Base220(1)
            Base220(1)
            ColorCode
            Base220(1)
            Base220(4)
            Base220(1)
        """
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
        await self.fire("SpawnAvatar", result)
    
    #"=" - Resume drawing
    async def message_29(self, opcode, data):
        await self.fire("Suspend", False)
    
    #">" - Spawn object
    async def message_30(self, opcode, data):
        msg = FurcBuffer(data)
        result = []
        while msg.remaining >= 6:
            result.append({
                "pos": (msg.read220(2), msg.read220(2)),
                "id": msg.read220(2)
            })
        await self.fire("SetObject", result)
    
    #"@" - Move camera
    #FIXME: Looks like "from" might be encoded some way
    async def message_32(self, opcode, data):
        msg = FurcBuffer(data)
        result = {
            "to": (msg.read95(2), msg.read95(2))
        }
        if msg.remaining >= 4:
            result["from"] = (msg.read95(2), msg.read95(2))
        await self.fire("MoveCamera", result)
    
    #"A" - Move avatars
    async def message_33(self, opcode, data):
        msg = FurcBuffer(data)
        furre = msg.read220(4)
        pos = (msg.read220(2), msg.read220(2)),
        unk1 = msg.read220(1)
        unk2 = msg.read220(1)
        await self.fire("MoveAvatar", furre, pos)
    
    #"B" - Set avatar colors
    async def message_34(self, opcode, data):
        msg = FurcBuffer(data)
        furre = msg.read220(4)
        direction = msg.read220(1)
        unk1 = msg.read220(1)
        colors = Colors.fromStream(msg)
        await self.fire("SetAvatarColors", furre, direction, unk1, colors)
    
    #"C" - Hide avatar at position
    async def message_35(self, opcode, data):
        msg = FurcBuffer(data)
        furre = msg.read220(4)
        pos = (msg.read220(2), msg.read220(2))
        await self.fire("HideAvatar", furre, pos)
    
    #"D" - Set triggering furre
    #WARNING: Probably deprecated
    async def message_36(self, opcode, data):
        msg = FurcBuffer(data)
        await self.fire("DSTriggerer", msg.read220(4))
    
    #"[" - Server authenticate
    async def message_59(self, opcode, data):
        await self.fire("Disconnect", data.decode())
    
    #"\" - Server authenticate
    async def message_60(self, opcode, data):
        await self.fire("Authenticate", data.decode())
    
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
        msg = FurcBuffer(data)
        diagID = msg.readUntil().decode()
        if diagID == "xxxx":
            diagID = -1
        else:
            diagID = int(diagID)
        await self.fire("Dialog",
            diagID, #Dialog ID
            int(msg.readUntil().decode()), #Dialog Type
            msg.read().decode()
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
        msg = FurcBuffer(data)
        await self.fire("Portrait",
            int(msg.readUntil().decode()), #Portrait ID
            msg.read().decode() #Portrait name
        )
    
    #"]*" - Show URL
    async def message_61_10(self, opcode, data):
        await self.fire("OpenURL", True, data)
    
    #"]-" - Prefix text
    async def message_61_13(self, opcode, data):
        await self.fire("Prefix", data)
    
    #"]3" - Show user list
    async def message_61_19(self, opcode, data):
        await self.fire("EnableUserList",
            data[0] == 48 #0 = Show usercount + list, 1 = Only count
        )
    
    #"]A" - Guild tag related?
    #FIXME: Figure out how this works
    async def message_61_33(self, opcode, data):
        await self.fire("GuildTagA", data)
    
    #"]?" - Unknown, something related to pounce
    #FIXME: Figure out wtf this is
    async def message_61_31(self, opcode, data):
        """Seen values:
            char[1] "I" - Clear(?) and jump to func1
            char[1] "A" - jump to func1
            char[1] "S" - jump to func2
            char[1] "o" - jump to func3
            
            func1:
                Base220(4) unk1
                Base220(4) unk2
                char[1] unk3 #flag?
                Base220(4) unk4 #Time?
                Base220(4) unk5 #Time?
                Base220(4) unk6 #Time?
                Base220(1) unk7
                Base220(1) unk8
            
            func2:
                while(remaining > 3)
                    Base220(4) unk1
                    Base220(4) unk2
                    char[1] unk3
                    Base220(4) unk4
                    Base220(4) unk5
            
            func3:
                Base220(4) unk1
                char[1] flag - "+" or "-"
        """
        #await self.fire("SetUserID", int(data.decode()))
    
    #"]B" - Set user ID
    #FIXME: This might be incorrect
    async def message_61_34(self, opcode, data):
        await self.fire("SetUserID", int(data.decode()))
    
    #"]C" - Bookmark Dream
    async def message_61_35(self, opcode, data):
        msg = FurcBuffer(data)
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
        msg = FurcBuffer(data)
        fuid = msg.read220(4)
        pos = (msg.read220(2) - 256, msg.read220(2) - 256)
        await self.fire("OffsetAvatar", fuid, pos)
    
    #"]I" - Particle Effect
    #TODO: Implement
    async def message_61_41(self, opcode, data):
        """Format:
            Base220(2) unk1
            Base220(2) unk2
            Base220(2) unk3
            Base220(2) unk4
            
            char(6) "VXNASC"
            Base220(1) version
            Base220(4) flags
            while(remaining > 5)
                char[2] "m!" #Static string? Same in VXN file particles
                Base220(4) unk5
                Base220(1) unk6 #Looks like always 1
                if(unk6 == 1)
                    length = 800
                elif(unk6 == 2)
                    length = 656
                Base220(length) particleData #This is a byte array
            
            VXN format is similar: (Little endian!)
                char(4) "FvXn"
                uint8 version
                uint32 flags
                while(remaining > 5)
                    char[2] "m!" #Static string? Same in streamed particles
                    uint32 unk1
                    uint8 subversion (? Looks like 1)
                    if(unk1 == 1)
                        length = 400
                    elseif(unk1 == 2)
                        length = 328
                    char[length] particleData
        """
        await self.fire("Particles", data)
    
    #"]J" - Web map
    async def message_61_42(self, opcode, data):
        await self.fire("WebMap", data)
    
    #"]M" - Dynamic Avatars Info
    #TODO: Implement
    async def message_61_45(self, opcode, data):
        """Format:
            while(remaining > 8)
                Base220(1) version
                Base220(1) unk1
                Base220(1) unk2
                Base220(1) unk3
                Base220(4) unk4
        """
        await self.fire("DynamicAvatars", data)
    
    #"]N" - Unknown
    #TODO: Implement
    async def message_61_45(self, opcode, data):
        pass
    
    #"]O" - Gloam
    async def message_61_47(self, opcode, data):
        """Format:
            while(remaining)
                Base220(4) UID
                Base220(2) Gloam data
        """
        await self.fire("Gloam", data)
    
    #"]P" - Guild tag related?
    #FIXME: Figure out how this works
    async def message_61_48(self, opcode, data):
        await self.fire("GuildTagB", data)
    
    #"]W" - Region settings
    #FIXME: This has changed!
    async def message_61_55(self, opcode, data):
        msg = FurcBuffer(data)
        """
        New format:
            Base220(2) unk
            Base220(2) unk
            Base220(2) unk
            Base220(2) unk
            Base220(2) unk
            Base220(2) unk
            Base220(2) unk
            Base220(2) unk
            Base220(2) unk
            Base220(1) bool1
            Base220(1) bool2
            Base220(2) unk
            Base220(2) unk
            Base220(2) unk
            Base220(2) unk
            if(remaining > 3)
                Base220(1) length
                for(i = 0; i < length; i++)
                    Base220(2) unk
                    Base220(1) unk
        """
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
    async def message_61_63(self, opcode, data):
        msg = FurcBuffer(data)
        avatars = {}
        while msg.remaining >= 5:
            avatars[msg.read220(4)] = msg.read220(1)
        await self.fire("KitterDust", avatars)
    
    #"]a" - Waiting for dream
    #FIXME: Confirm this is correct
    async def message_61_65(self, opcode, data):
        await self.fire("UploadReady")
    
    #"]c" - Set marbled
    async def message_61_67(self, opcode, data):
        #This has a "c" prefixed to it
        await self.fire("Marbled", data[1:].decode())
    
    #"]f" - Look
    #FIXME: this might be incorrect
    async def message_61_70(self, opcode, data):
        msg = FurcBuffer(data)
        await self.fire("Look", Colors.fromStream(msg), msg.read().decode())
    
    #"]h" - Execute binary (lmao)
    async def message_61_72(self, opcode, data):
        msg = FurcBuffer(data)
        await self.fire("Execute", data.decode())
    
    #"]j" - Music
    async def message_61_74(self, opcode, data):
        await self.fire("Music", base.b95decode(data[0:2]))
    
    #"]k" - Unknown
    #FIXME: Implement this
    async def message_61_75(self, opcode, data):
        pass
    
    #"]m" - Marco
    async def message_61_77(self, opcode, data):
        msg = FurcBuffer(data)
        msg.readUntil()
        await self.fire("Marco", msg.read())
    
    #"]n" - Channel info(?)
    #FIXME: Implement this
    async def message_61_78(self, opcode, data):
        pass
    
    #"]o" - Dream owner name
    async def message_61_79(self, opcode, data):
        msg = FurcBuffer(data)
        await self.fire("DreamOwner", msg.read().decode())
    
    #"]q" - Load dream with custom patches
    #FIXME: This can end with the string "modern"
    async def message_61_81(self, opcode, data):
        msg = FurcBuffer(data)
        msg.readUntil()
        await self.fire("Dream", True, msg.readUntil(), msg.readUntil())
    
    #"]r" - Load dream with default patches
    #FIXME: This can end with the string "modern"
    async def message_61_82(self, opcode, data):
        msg = FurcBuffer(data)
        msg.readUntil()
        await self.fire("Dream", False, msg.readUntil(), msg.readUntil())
    
    #"]s" - Place text at location
    #FIXME: This is probably incorrect
    async def message_61_83(self, opcode, data):
        msg = FurcBuffer(data)
        await self.fire("Text",
            (msg.read95(2), msg.read95(2)),
            int(msg.readUntil()), #Type?
            msg.readUntil(), #Name
            msg.readUntil(), #Title
            int(msg.readUntil()), #Maturity?
        )
    
    #"]t" - Clear text at location
    async def message_61_84(self, opcode, data):
        msg = FurcBuffer(data)
        await self.fire("ClearText", (msg.read95(2), msg.read95(2)))
    
    #"]u" - Waiting for dream
    #FIXME: Confirm this is correct
    async def message_61_85(self, opcode, data):
        await self.fire("UploadReady")
    
    #"]v" - Effect
    async def message_61_86(self, opcode, data):
        msg = FurcBuffer(data)
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
        msg = FurcBuffer(data)
        await self.fire("SetColors", Colors.fromStream(msg))
    
    #"^" - Item in hand
    async def message_62(self, opcode, data):
        await self.fire("ButlerPaws", base.b95decode(data[0:2]))
    
    #"e" - Unknown
    #FIXME: Implement
    async def message_69(self, opcode, data):
        pass
    
    #"f" - Unknown
    #FIXME: Implement
    async def message_70(self, opcode, data):
        pass
    
    #"~" - Suspend drawing
    async def message_94(self, opcode, data):
        await self.fire("Suspend", True)
    
    #Hook definitions
    async def fire(self, name, *args, **kwargs):
        if name in self.listeners:
            for callback in self.listeners[name]:
                await callback(*args, **kwargs)
        
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
            return self.command("account {} {} {}".format(
                character.account.username,
                character.name,
                character.account.password
            ))
    
    def move(self, direction):
        return self.command("m {}".format(direction))
    
    def rotate(self, direction):
        if direction == 1:
            return self.command(">")
        elif direction == -1:
            return self.command("<")
    
    def vascodagama(self):
        return self.command("vascodagama")
    
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
    async def connect(self, server = None, loop = None, timeout = 5):
        if self.connected:
            await self.disconnect()
        
        if not server:
            server = self.server
        
        self.reader, self.writer = await asyncio.open_connection(
            server[0], server[1])
        
        motd = ""
        while self.connected:
            try:
                data = await asyncio.wait_for(self.reader.readline(), timeout)
            except asyncio.TimeoutError:
                data = None
                pass
            
            if not data: #None = Disconnected
                break
            
            if data[-1] != 10: #No EOL means incomplete stream + disconnected
                break
            
            if data == b"Dragonroar\n":
                return motd
            else:
                motd += data.decode()
        
        return None
    
    async def disconnect(self):
        writer.close()
        await writer.wait_closed()
        self.reader = None
        self.writer = None
    
    async def send(self, data):
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
    async def run(self):
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