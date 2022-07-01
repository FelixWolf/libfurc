#!/usr/bin/env python3 
import asyncio
from . import base
from .furcbuffer import FurcBuffer
from .account import Character
from .colors import Colors
from .particles import Particles
import datetime
import time
import math
import logging

LIVE_SERVER = ("lightbringer.furcadia.com", 6500)

#Incoming message definitions
class DefaultPacketHandler:
    async def message_unhandled(self, opcode, data):
        logging.error("Unhandled {}".format(opcode), data)

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
    async def message_0(self, opcode, data):
        msg = FurcBuffer(data)
        fuid = msg.read220(4)
        await self.fire("RemoveAvatarID", fuid)
    
    #"!" - Sound
    async def message_1(self, opcode, data):
        msg = FurcBuffer(data)
        soundID = msg.read95(2)
        await self.fire("Sound", soundID)
    
    #"%" - Standing on object
    async def message_5(self, opcode, data):
        msg = FurcBuffer(data)
        itemID = msg.read95(2)
        await self.fire("ButlerFeet", itemID)
    
    #"&" - Login success
    async def message_6(self, opcode, data):
        await self.fire("Login", True)
    
    #"(" - Text message
    async def message_8(self, opcode, data):
        await self.fire("Message", data)
    
    #")" - Remove avatar
    async def message_9(self, opcode, data):
        msg = FurcBuffer(data)
        fuid = msg.read220(4)
        await self.fire("RemoveAvatar", fuid)
    
    #"/" - Animate avatar
    async def message_15(self, opcode, data):
        msg = FurcBuffer(data)
        fuid = msg.read220(4)
        x = msg.read220(2)
        y = msg.read220(2)
        direction = msg.read220(1)
        shape = msg.read220(1)
        await self.fire("AnimateAvatar", fuid, (x,y), direction, shape)
    
    #"0" - Sync dream variables
    async def message_16(self, opcode, data):
        msg = FurcBuffer(data)
        variables = {}
        while msg.remaining >= 2:
            offset = msg.read95(2)
            while msg.remaining >= 6:
                val = msg.read95(3)
                if val != 0x4000:
                    variables[offset] = val
                    offset += 3
                else:
                    repeats = msg.read95(3) + 1
                    val = msg.read95(3)
                    for i in range(repeats):
                        variables[offset] = val
                        offset += 3
        await self.fire("UpdateVariables", variables)
    
    #"1" - Set floors
    async def message_17(self, opcode, data):
        msg = FurcBuffer(data)
        result = []
        while msg.remaining >= 6:
            x = msg.read220(2)
            y = msg.read220(2)
            floorID = msg.read220(2)
            
            #Decode repeats
            repeats = 48 * math.floor(x / 1000) + math.floor(y / 1000)
            x = x % 1000
            y = y % 1000
            
            result.append({
                "pos": (x, y),
                "floor": floorID,
                "repeats": repeats
            })
        
        await self.fire("SetFloor", result)
    
    #"2" - Set walls
    async def message_18(self, opcode, data):
        msg = FurcBuffer(data)
        result = []
        while msg.remaining >= 6:
            x = msg.read220(2)
            y = msg.read220(2)
            wallID = msg.read220(2)
            
            #Decode repeats
            repeats = 48 * math.floor(x / 1000) + math.floor(y / 1000)
            x = x % 1000
            y = y % 1000
            
            result.append({
                "pos": (x, y),
                "wall": wallID,
                "repeats": repeats
            })
        await self.fire("SetWall", result)
    
    #"3" - Set all DS variables
    async def message_19(self, opcode, data):
        msg = FurcBuffer(data)
        vals = []
        while msg.remaining >= 3:
            var = msg.read95(3)
            vals.append(var)
        await self.fire("SetVariables", vals)
    
    #"4" - Set region
    async def message_20(self, opcode, data):
        msg = FurcBuffer(data)
        result = []
        while msg.remaining >= 6:
            x = msg.read220(2)
            y = msg.read220(2)
            regionID = msg.read220(2)
            result.append({
                "pos": (x, y),
                "region": regionID
            })
        await self.fire("SetRegion", result)
    
    #"5" - Set effect
    async def message_21(self, opcode, data):
        msg = FurcBuffer(data)
        result = []
        while msg.remaining >= 6:
            x = msg.read220(2)
            y = msg.read220(2)
            effectID = msg.read220(2)
            
            #Decode repeats
            repeats = 48 * math.floor(x / 1000) + math.floor(y / 1000)
            x = x % 1000
            y = y % 1000
            
            result.append({
                "pos": (x, y),
                "id": effectID,
                "repeats": repeats
            })
        await self.fire("SetEffect", result)
    
    #"6" - DS event triggered by player
    async def message_22(self, opcode, data):
        msg = FurcBuffer(data)
        from_x = msg.read95(2)
        from_y = msg.read95(2)
        to_x = msg.read95(2)
        to_y = msg.read95(2)
        while msg.remaining >= 6:
            line = msg.read95(2)
            if line > 8000:
                line = line - 8000 + (msg.read95(2) * 1000)
            
            extra_x = msg.read95(2)
            extra_y = msg.read95(2)
            
            result = {
                "from": (from_x, from_y),
                "to": (to_x, to_y),
                "extra": (extra_x, extra_y),
                "line": line
            }
            await self.fire("DSEvent", True, result)
    
    #"7" - DS event triggered by other
    async def message_23(self, opcode, data):
        msg = FurcBuffer(data)
        from_x = msg.read95(2)
        from_y = msg.read95(2)
        to_x = msg.read95(2)
        to_y = msg.read95(2)
        while msg.remaining >= 8:
            line = msg.read95(2)
            if line > 8000:
                line = line - 8000 + (msg.read95(2) * 1000)
            
            extra_x = msg.read95(2)
            extra_y = msg.read95(2)
        
            result = {
                "from": (from_x, from_y),
                "to": (to_x, to_y),
                "extra": (extra_x, extra_y),
                "line": line
            }
            await self.fire("DSEvent", False, result)
    
    #"8" - DS event addon
    async def message_24(self, opcode, data):
        msg = FurcBuffer(data)
        moveFlag = msg.read95(1)
        randSeed = msg.read95(5)
        try:
            saidNum = msg.read95(3)
        except ValueError:
            #TEMPORARY: Fix for server sending non-base95 numbers
            saidNum = 0
        facingDir = msg.read95(1)
        entryCode = msg.read95(3)
        objPaws =  msg.read95(3)
        furreCount = msg.read95(2)
        userID = msg.read95(6)
        DSBtn = msg.read95(2)
        dreamCookies = msg.read95(3)
        triggererCookies = msg.read95(2)
        portalOpen = (msg.read95(2), msg.read95(2))
        second = msg.read95(1)
        minute = msg.read95(1)
        hour = msg.read95(1)
        day = msg.read95(1)
        month = msg.read95(1)
        year = msg.read95(2)
        portalClose = (msg.read95(2), msg.read95(2))
        await self.fire("DSEventAddon", {
            "moveFlag": moveFlag,
            "randSeed": randSeed,
            "saidNum": saidNum,
            "facingDir": facingDir,
            "entryCode": entryCode,
            "objPaws": objPaws,
            "furreCount": furreCount,
            "userID": userID,
            "DSBtn": DSBtn,
            "dreamCookies": dreamCookies,
            "triggererCookies": triggererCookies,
            "portalOpen": portalOpen,
            "second": second,
            "minute": minute,
            "hour": hour,
            "day": day,
            "month": month,
            "year": year,
            "portalClose": portalClose
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
        await self.fire("LoadMap", data.decode())
    
    #"<" - Spawn avatar
    async def message_28(self, opcode, data):
        msg = FurcBuffer(data)
        fuid = msg.read220(4)
        x = msg.read220(2)
        y = msg.read220(2)
        direction = msg.read220(1)
        shape = msg.read220(1)
        nameLength = msg.read220(1)
        name = msg.read(nameLength)
        colors = Colors.fromStream(msg, False)
        flags = msg.read220(1)
        afkTime = msg.read220(4)
        scale = msg.read220(1)
        await self.fire("SpawnAvatar", fuid, (x,y), direction, shape, name, colors, flags, afkTime, scale)
    
    #"=" - Resume drawing
    async def message_29(self, opcode, data):
        await self.fire("Suspend", False)
    
    #">" - Spawn object
    async def message_30(self, opcode, data):
        msg = FurcBuffer(data)
        result = []
        while msg.remaining >= 6:
            x = msg.read220(2)
            y = msg.read220(2)
            objectID = msg.read220(2)
            
            #Decode repeats
            repeats = 48 * math.floor(x / 1000) + math.floor(y / 1000)
            x = x % 1000
            y = y % 1000
            
            result.append({
                "pos": (x, y),
                "id": objectID,
                "repeats": repeats
            })
        
        await self.fire("SetObject", result)
    
    #"@" - Move camera
    async def message_32(self, opcode, data):
        msg = FurcBuffer(data)
        x = msg.read95(2)
        y = msg.read95(2)
        result = {
            "to": (x, y)
        }
        if msg.remaining >= 4:
            x = msg.read95(2)
            y = msg.read95(2)
            result["from"] = (x, y)
        await self.fire("MoveCamera", result)
    
    #"A" - Move avatars
    async def message_33(self, opcode, data):
        msg = FurcBuffer(data)
        fuid = msg.read220(4)
        x = msg.read220(2)
        y = msg.read220(2)
        direction = msg.read220(1)
        shape = msg.read220(1)
        await self.fire("MoveAvatar", fuid, (x,y), direction, shape)
    
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
    
    #"D" - Announce furre presence
    async def message_36(self, opcode, data):
        msg = FurcBuffer(data)
        fuid = msg.read220(4)
        if fuid == 0: #Server side bug fix
            return
        x = msg.read220(2)
        y = msg.read220(2)
        direction = msg.read220(1)
        shape = msg.read220(1)
        unk1 = msg.read220(4)
        unk2 = msg.read220(4)
        unk3 = msg.read220(2)
        unk4 = msg.read220(2)
        await self.fire("FurreArrive", fuid, (x, y), direction, shape, unk1, unk2, unk3, unk4)
    
    #"E" - Spawn SFX
    async def message_37(self, opcode, data):
        msg = FurcBuffer(data)
        result = []
        while msg.remaining >= 6:
            x = msg.read220(2)
            y = msg.read220(2)
            fxID = msg.read220(2)
            
            #Decode repeats
            repeats = 48 * math.floor(x / 1000) + math.floor(y / 1000)
            x = x % 1000
            y = y % 1000
            
            result.append({
                "pos": (x, y),
                "id": fxID,
                "repeats": repeats
            })
        
        await self.fire("SetSFX", result)
    
    #"F" - Spawn Ambient
    async def message_38(self, opcode, data):
        msg = FurcBuffer(data)
        result = []
        while msg.remaining >= 6:
            x = msg.read220(2)
            y = msg.read220(2)
            ambientID = msg.read220(2)
            
            #Decode repeats
            repeats = 48 * math.floor(x / 1000) + math.floor(y / 1000)
            x = x % 1000
            y = y % 1000
            
            result.append({
                "pos": (x, y),
                "id": ambientID,
                "repeats": repeats
            })
        
        await self.fire("SetAmbient", result)
    
    #"[" - Disconnected (Reconnect allowed)
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
        logging.error("Unhandled 61:{}".format(opcode), data)
    
    #"]!" - Adult warning
    async def message_61_1(self, opcode, data):
        maturity = data.decode()
        parental = False
        if maturity.startswith("+"):
            parental = True
            maturity = maturity[1:]
        
        await self.fire("MaturityWarning", parental, maturity)
    
    #"]#" - Dialog
    async def message_61_3(self, opcode, data):
        msg = FurcBuffer(data)
        dialogID = msg.readUntil().decode()
        
        if dialogID == "xxxx":
            dialogID = -1
        else:
            dialogID = int(dialogID)
        
        dialogType = int(msg.readUntil())
        dialogMessage = msg.read()
        await self.fire("Dialog", dialogID, dialogType, dialogMessage)
    
    #"]$" - Open URL
    async def message_61_4(self, opcode, data):
        msg = FurcBuffer(data)
        url = msg.readUntil()
        await self.fire("OpenURL", False, url)
    
    #"]%" - Online reply
    async def message_61_5(self, opcode, data):
        msg = FurcBuffer(data)
        online = bool(int(msg.read(1)))
        name = msg.read()
        await self.fire("OnlineStatus", online, name)
    
    #"]&" - Set portrait
    async def message_61_6(self, opcode, data):
        msg = FurcBuffer(data)
        pid = int(msg.readUntil().decode())
        name = msg.read() #Portrait name, not furre name!
        await self.fire("Portrait", pid, name)
    
    #"]*" - Show URL
    async def message_61_10(self, opcode, data):
        await self.fire("OpenURL", True, data)
    
    #"]+" - Set last profile ID (DEPRECATED)
    async def message_61_11(self, opcode, data):
        msg = FurcBuffer(data)
        pid = int(msg.readUntil().decode())
        #For use with:
        #http://www.furcadia.com/services/profile/profile.php4?cmd=view&p=<PID>
        await self.fire("LastProfileID", pid)
    
    #"]-" - Prefix text, used by say command (Can be overridden by 61_48)
    async def message_61_13(self, opcode, data):
        await self.fire("PrefixBadge", data)
    
    #"]3" - Show user list
    async def message_61_19(self, opcode, data):
        msg = FurcBuffer(data)
        #0 = Show usercount + list, 1 = Only count
        enabled = not bool(int(msg.read(1)))
        await self.fire("EnableUserList", enabled)
    
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
    
    
    #"]A" - Download guild tag command (DEPRECATED?)
    async def message_61_33(self, opcode, data):
        msg = FurcBuffer(data)
        checksum = int(msg.readUntil()) #Download it from file server using gt%i
        name = msg.readUntil()
        await self.fire("GuildTagDownload", checksum, name)
    
    #"]B" - Set user ID
    async def message_61_34(self, opcode, data):
        msg = FurcBuffer(data)
        fuid = int(msg.readUntil())
        username = msg.readUntil()
        await self.fire("SetUserID", fuid, username)
    
    #"]C" - Bookmark Dream
    async def message_61_35(self, opcode, data):
        msg = FurcBuffer(data)
        msg = FurcBuffer(data)
        temporary = not bool(int(msg.read(1)))
        fdl = msg.read()
        await self.fire("Bookmark", temporary, fdl)
    
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
        #0 = Enable, 1 = Disable
        msg = FurcBuffer(data)
        disabled = not bool(int(msg.read(1)))
        await self.fire("DisableTab", disabled)
    
    #"]H" - Offset avatar
    async def message_61_40(self, opcode, data):
        msg = FurcBuffer(data)
        fuid = msg.read220(4)
        x = msg.read220(2) - 256
        y = msg.read220(2) - 256
        await self.fire("OffsetAvatar", fuid, (x, y))
    
    #"]I" - Particle Effect
    async def message_61_41(self, opcode, data):
        msg = FurcBuffer(data)
        x = msg.read220(2)
        y = msg.read220(2)
        offset_x = msg.read220(2)
        offset_y = msg.read220(2)
        particles = Particles.loadsMessage(data[8:])
        await self.fire("Particles", (x, y), (offset_x, offset_y), particles)
    
    #"]J" - Web map
    async def message_61_42(self, opcode, data):
        await self.fire("WebMap", data)
    
    #"]K" - Focus DSBtn? Return if visible?
    async def message_61_43(self, opcode, data):
        pass
    
    #"]M" - Dynamic Avatars Info
    async def message_61_45(self, opcode, data):
        avatars = {}
        msg = FurcBuffer(data)
        dataVersion = msg.read220(1)
        if data == 2:
            while msg.remaining >= 8:
                avatarVersion = msg.read220(1)
                
                flags = msg.read220(1)
                
                idP1 = msg.read220(1)
                idP2 = msg.read220(1)
                avatarId = idP1 + 220 * (idP2 >> 1)
                
                updated = msg.read220(4)
                
                avatars[avatarId] = {
                    "version": avatarVersion,
                    "flags": flags,
                    "updated": updated
                }
        
        await self.fire("DynamicAvatars", avatars)
    
    #"]N" - Show pounce channel list
    async def message_61_46(self, opcode, data):
        msg = FurcBuffer(data)
        showPounceChannels = bool(int(msg.read(1)))
        await self.fire("ShowPounceChannels", showPounceChannels)
    
    #"]O" - Gloam
    async def message_61_47(self, opcode, data):
        msg = FurcBuffer(data)
        result = {}
        
        while msg.remaining >= 12:
            fuid = msg.read220(4)
            
            color = 0
            
            for i in range(6):
                #I still don't fully understand this but this seems to work
                color = color << 4
                fragment = msg.read(1)[0]
                if fragment >= 48 and fragment <= 57:
                    color = color | (fragment & 15)
                elif fragment >= 65 and fragment <= 70:
                    color = color | (fragment - 75)
            
            intensity = msg.read220(2)
            
            result[fuid] = {
                "color": color,
                "intensity": intensity
            }
        
        await self.fire("Gloam", result)
    
    #"]P" - Prefix next line (Can be overridden by 61_13)
    async def message_61_48(self, opcode, data):
        await self.fire("PrefixLine", data)
    
    #"]S" - Connection security info
    async def message_61_51(self, opcode, data):
        msg = FurcBuffer(data)
        #0 = insecure, 1 = unk, 2 = unused, 3 = secure
        flag = int(msg.read(1))
        await self.fire("ConnectionSecurity", flag)
    
    #"]W" - Region settings
    #FIXME: Resolve unknown variables
    async def message_61_55(self, opcode, data):
        msg = FurcBuffer(data)
        result = {
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
            "unk1": msg.read220(2),
            "walls": {
                "bottom": msg.read220(1),
                "top": msg.read220(1),
            },
            "unk2": msg.read220(2),
            "unk3": msg.read220(2),
            "unk4": msg.read220(2),
            "unk5": msg.read220(2),
            "unk6": []
        }
        
        while msg.remaining >= 4:
            l = msg.read220(1)
            for i in range(l):
                result["unk6"].append((
                    msg.read220(2),
                    msg.read220(1),
                ))
        
        await self.fire("RegionSettings", result)
    
    #"]Z" - Art party(?)
    #TODO: Implement
    async def message_61_58(self, opcode, data):
        """
            Format:
                char[1] opcode # 0 - 7
                
            if opcode == 0: #End
                #No params
            
            if opcode == 2: #Draw
                #Probably base220 byte array
            
            if opcode == 3: #UNKNOWN
                #unknown
            
            if opcode == 4: #Set shape
                base220(4) shape
                
            if opcode == 5:
                #unknown
            
            if opcode == 6: #Request data?
                #no op
            
            if opcode == 7:
                char(*) filename
        """
        pass
    
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
    
    #"]`" - Load remote config
    async def message_61_64(self, opcode, data):
        msg = FurcBuffer(data)
        subop = msg.read(1)
        if subop == b"e":
            subop = int(msg.read(1))
            if subop == 1:
                afkTime = int(msg.readUntil())
                disconnectTime = int(msg.readUntil())
                await self.fire("RemoteConfig", "Timers", afkTime, disconnectTime)
            
            else:
                #afkconfig <int> <str>
                await self.fire("RemoteConfig", "RequestSend")
        
        elif subop == b"r":
            message = msg.read()
            await self.fire("RemoteConfig", "AutoWhisper", message)
        
        elif subop == b"m":
            message = msg.read()
            await self.fire("RemoteConfig", "AFKWhisper", message)
    
    #"]a" - Upload dream request (DEPRECATED)
    async def message_61_65(self, opcode, data):
        logging.warn("Received deprecated 61:65 (Upload dream request) from server!")
    
    #"]b" - Resize map
    async def message_61_64(self, opcode, data):
        msg = FurcBuffer(data)
        x = msg.read95(2)
        y = msg.read95(2)
        await self.fire("DreamResize", (x, y))
    
    #"]c" - Set marbled
    async def message_61_67(self, opcode, data):
        #This has a "c" prefixed to it
        msg = FurcBuffer(data)
        
        #t is Type
        #type 0 and 1 are unknown
        #type 2 is normal mode
        t = msg.read(1)[0]
        if t > 96 and t < 123:
            t = t - 97
        else:
            t = 0
        
        background = msg.readUntil()
        
        await self.fire("Marbled", t, background)
    
    #"]d" - Something something stickers prototype (DEPRECATED)
    async def message_61_68(self, opcode, data):
        logging.warn("Received deprecated 61:68 (Unknown) from server!")
    
    #"]e" - Something something stickers prototype (DEPRECATED)
    async def message_61_69(self, opcode, data):
        logging.warn("Received deprecated 61:69 (Unknown) from server!")
    
    #"]f" - Look
    async def message_61_70(self, opcode, data):
        msg = FurcBuffer(data)
        colors = Colors.fromStream(msg, False)
        name = msg.read().decode()
        await self.fire("Look", colors, name)
    
    #"]g" - Execute binary (lmao) (DEPRECATED)
    async def message_61_71(self, opcode, data):
        msg = FurcBuffer(data)
        command = msg.read()
        await self.fire("Execute", command, False)
    
    #"]h" - Execute binary and close (lmao)
    async def message_61_72(self, opcode, data):
        msg = FurcBuffer(data)
        command = msg.read()
        await self.fire("Execute", command, True)
    
    #"]i" - Create a file with path name (DEPRECATED)
    async def message_61_73(self, opcode, data):
        """
            Format:
                char(1) bool # 1 = write, anything else is NOP
                char(*) path #?
        """
        logging.warn("Received deprecated 61:73 (Create file) from server!")
    
    #"]j" - Music
    async def message_61_74(self, opcode, data):
        msg = FurcBuffer(data)
        musicID = msg.read95(2)
        await self.fire("Music", musicID)
    
    #"]k" - Set file server
    async def message_61_75(self, opcode, data):
        msg = FurcBuffer(data)
        serverID = msg.read95(1)
        await self.fire("SetFileServer", serverID)
    
    #"]m" - Marco
    async def message_61_77(self, opcode, data):
        msg = FurcBuffer(data)
        msg.readUntil() #Skip space
        polon = msg.read()
        await self.fire("Marco", polon)
    
    #"]n" - Channel info(?)
    async def message_61_78(self, opcode, data):
        msg = FurcBuffer(data)
        version = msg.read220(1)
        channelUpdateType = msg.read220(1)
        unk1 = msg.read220(1)
        while msg.remaining >= 9:
            nameLength = msg.read220(1)
            name = msg.read(nameLength)
            bitpack = msg.read220(4)
            canJoin = bitpack >> 7 & 1
            maturity = (bitpack >> 8 & 0xf) * 100
            peopleCount = bitpack >> 25 & 0x1f
            canTell = bitpack & 0x4000
            canListen = bitpack & 0x20000
            canBroadcast = bitpack & 0x40000
            channelImage = msg.read220(4)
            await self.fire("ChannelInfo", channelUpdateType == "@", name, maturity, peopleCount, canTell, canListen, canBroadcast, channelImage)
    
    #"]o" - Dream owner name
    async def message_61_79(self, opcode, data):
        msg = FurcBuffer(data)
        owner = msg.read()
        await self.fire("DreamOwner", owner.decode())
    
    #"]q" - Load dream with custom patches
    async def message_61_81(self, opcode, data):
        msg = FurcBuffer(data)
        patchName = msg.readUntil()
        crc32 = msg.readUntil()
        unk1 = msg.readUntil()
        unk2 = msg.readUntil()
        modern = msg.readUntil()
        if modern == "modern":
            modern = True
        else:
            modern = False
        await self.fire("Dream", True, patchName, crc32, modern)
    
    #"]r" - Load dream with default patches
    async def message_61_82(self, opcode, data):
        msg = FurcBuffer(data)
        patchName = msg.readUntil()
        crc32 = msg.readUntil()
        unk1 = msg.readUntil()
        unk2 = msg.readUntil()
        modern = msg.readUntil()
        if modern == "modern":
            modern = True
        else:
            modern = False
        await self.fire("Dream", False, patchName, crc32, modern)
    
    #"]s" - Place text at location
    async def message_61_83(self, opcode, data):
        msg = FurcBuffer(data)
        x = msg.read95(2)
        y = msg.read95(2)
        textType = int(msg.readUntil()) #Text type: 0 = None, 1 = Normal, 2 = Lower
        name = msg.readUntil()
        title = msg.readUntil()
        maturity = int(msg.readUntil())
        gateType = int(msg.readUntil()) #Gate type: 0 = Normal, 1 = SS, 2 = Guild
        await self.fire("Text", (x, y), textType, name, title, maturity, gateType)
    
    #"]t" - Clear text at location
    async def message_61_84(self, opcode, data):
        msg = FurcBuffer(data)
        x = msg.read95(2)
        y = msg.read95(2)
        await self.fire("ClearText", (x, y))
    
    #"]u" - Waiting for dream
    #FIXME: Has a string parameter like 0_11, find out what this does
    async def message_61_85(self, opcode, data):
        await self.fire("UploadReady")
    
    #"]v" - Effect
    async def message_61_86(self, opcode, data):
        msg = FurcBuffer(data)
        #Known types:
        #a = breath
        #b = flame
        #c = glamour
        #d = splash
        effectType = msg.read(1)
        x = msg.read95(2)
        y = msg.read95(2)
        await self.fire("Effect",
            effectType.decode(), #Type
            (x, y) #Location
        )
    
    #"]w" - Version request
    async def message_61_87(self, opcode, data):
        await self.fire("VersionReq")
    
    #"]x" - Client should update
    async def message_61_88(self, opcode, data):
        await self.fire("Update")
    
    #"]y" - Changing IP/port
    async def message_61_89(self, opcode, data):
        await self.fire("Update", data)
    
    #"]z" - UID response
    async def message_61_90(self, opcode, data):
        msg = FurcBuffer(data)
        fuid = int(msg.readUntil())
        await self.fire("UID", fuid)
    
    #"]{" - Session ID
    async def message_61_91(self, opcode, data):
        msg = FurcBuffer(data)
        sessionID = int(msg.readUntil())
        await self.fire("SessionID", sessionID)
    
    #"]|" - Flip screen
    async def message_61_92(self, opcode, data):
        msg = FurcBuffer(data)
        flip = msg.read(1) == 49
        await self.fire("FlipScreen", flip)
    
    #"]}" - Set own colors
    async def message_61_93(self, opcode, data):
        msg = FurcBuffer(data)
        colors = Colors.fromStream(msg)
        await self.fire("SetColors", colors)
    
    #"^" - Item in hand
    async def message_62(self, opcode, data):
        msg = FurcBuffer(data)
        item = msg.read95(2)
        await self.fire("ButlerPaws", item)
    
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
    
    def hook(self, name, func):
        if name not in self.listeners:
            self.listeners[name] = []
        self.listeners[name].append(func)
    
    def off(self, name, func):
        if name not in self.listeners:
            return
        self.listeners[name].remove(func)
    
    async def handlePacket(self, data):
        await self.fire("Raw", data)
        await getattr(
            self,
            "message_" + str(data[0]-32),
            self.message_unhandled
        )(data[0]-32, data[1:])

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
    
    def handlePacket(self, data):
        pass
    
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
            
            await self.handlePacket(data)
        
        #We are out of the loop! Presume Disconnected!
        self.reader = None
        self.writer = None
