#!/usr/bin/env
import libfurc
import argparse
import getpass
import asyncio
import time
import json
import hashlib

class DreamVisit:
    def __init__(self, owner = None, name = None, parent = None, gomap = None):
        self.owner = owner
        self.ownerraw = None
        self.name = name
        self.parent = parent
        self.gomap = gomap
        self.available = False
        self.entryText = None
        self.standard = None
        self.patch = None
        self.checksum = None
        self.mapfile = None
    
    def toDict(self):
        return {
            "id": self.getHash(),
            "parent": "00"*16 if self.parent == None else self.parent.getHash(),
            "owner": self.owner,
            "name": self.name,
            "gomap": self.gomap,
            "available": self.available,
            "entryText": self.entryText,
            "standard": self.standard,
            "patch": self.patch,
            "checksum": self.checksum
        }
    
    def getHash(self):
        hashtable = []
        if self.mapfile and self.mapfile != "default.map":
            hashtable.append(self.mapfile)
        
        if self.ownerraw:
            hashtable.append(self.ownerraw)
        
        if self.checksum:
            hashtable.append(self.checksum)
        
        if self.standard:
            hashtable.append(self.standard)
        
        if self.owner:
            hashtable.append(self.owner)
        
        if self.name:
            hashtable.append(self.name)
        
        return hashlib.md5("".join(hashtable).encode()).hexdigest()
    
    def __str__(self):
        return "furc://{}{}/ gomap {} standard {}".format(self.owner, ":"+self.name if self.name != "|" and self.name != None else "", self.gomap, self.standard)

class Bot:
    def __init__(self, name, data = None, visited = None, toVisit = None, onVisit = None):
        self.name = name
        self.data = data or {}
        self.visited = visited or []
        self.toVisit = toVisit or []
        self.client = libfurc.Client()
        self.currentDream = None
        self.timeSinceLast = time.time()
        self.onVisit = onVisit
        self.mapfile = None
        self.dreamowner = None
        if self.onVisit == None:
            def _(dream):
                pass
            self.onVisit = _
        self.client.hook("Login", self.Login)
        self.client.hook("Message", self.Message)
        self.client.hook("Dream", self.Dream)
        self.client.hook("Bookmark", self.Bookmark)
        self.client.hook("Text", self.Text)
        self.client.hook("DreamOwner", self.DreamOwner)
        self.client.hook("LoadMap", self.LoadMap)

    async def timer(self):
        while self.client.connected:
            if self.timeSinceLast + 5 < time.time():
                await self.visitNext()
            await asyncio.sleep(1)

    async def visitNext(self):
        step = time.time() - self.timeSinceLast
        if step < 2:
            await asyncio.sleep(2)
        
        if len(self.toVisit) <= 0:
            self.client.disconnect()
            return
        
        print(self.name, "Discovered", str(self.currentDream))
        self.onVisit(self.currentDream)
        self.currentDream = self.toVisit.pop(0)
        self.timeSinceLast = time.time()
        
        if self.currentDream.gomap != None:
            print("Visit gomap {} on {}".format(self.currentDream.gomap, self.name))
            await self.client.command("gomap {}".format(chr(32+self.currentDream.gomap)))
        elif self.currentDream.name != None:
            print("Visit gomap furc://{}:{}/ on {}".format(self.currentDream.owner, self.currentDream.name, self.name))
            await self.client.command("fdl furc://{}:{}/".format(self.currentDream.owner, self.currentDream.name))
        elif self.currentDream.owner != None:
            print("Visit gomap furc://{}:{}/ on {}".format(self.currentDream.owner, self.name))
            await self.client.command("fdl furc://{}/".format(self.currentDream.owner))
        else:
            print("Encountered empty dream visit!")
            await self.visitNext()
    
    async def Login(self, success):
        if success:
            print(self.name, "Logged in!")
        else:
            print(self.name, "Connection failed!")
        
        self.timeSinceLast = time.time()
        await self.visitNext()
        asyncio.ensure_future(self.timer())

    async def Message(self, msg):
        if msg.startswith(b"<font color='emit'><img src='fsh://system.fsh:91' alt='@emit' /><channel name='@emit' />"):
            self.currentDream.entryText = msg.decode()
            await self.visitNext()
        if msg.startswith(b"<img src='fsh://system.fsh:86' /> Dream Standard: <a href='http://www.furcadia.com/standards/'>"):
            self.currentDream.standard = msg.split(b"<a href='http://www.furcadia.com/standards/'>")[1].split(b"</a>")[0].decode()

    async def DreamOwner(self, name):
        self.timeSinceLast = time.time()
        self.dreamowner = name
    
    async def LoadMap(self, name):
        self.timeSinceLast = time.time()
        self.mapfile = name
    
    async def Dream(self, patched, package, checksum, modern):
        self.timeSinceLast = time.time()
        if self.currentDream == None:
            await self.visitNext()
        else:
            self.visited.append(self.currentDream)
            self.currentDream.patch = package.decode()
            self.currentDream.checksum = checksum.decode()
            self.currentDream.ownerraw = self.dreamowner
            self.currentDream.mapfile = self.mapfile
            await self.client.vascodagama()
            await self.client.command("dreambookmark 0")
            self.currentDream.available = True
            self.dreamowner = None
            self.mapfile = None

    async def Bookmark(self, user, fdl):
        fdl = fdl.decode()
        d = fdl.split("furc://",1)[-1].split("/")[0].split(":")
        if len(d) == 1:
            self.currentDream.owner = d[0]
            self.currentDream.name = "|"
        elif len(d) == 2:
            self.currentDream.owner = d[0]
            self.currentDream.name = d[1]

    async def Text(self, pos, t, owner, name, maturity, gateType):
        visit = DreamVisit(owner.decode(), name.decode(), parent = self.currentDream)
        test = visit.getHash()
        for dream in self.visited:
            if dream.getHash() == test:
                return
        for dream in self.toVisit:
            if dream.getHash() == test:
                return
        print("Added {} to visit list".format(str(visit)))
        self.toVisit.append(visit)
    

async def main():
    parser = argparse.ArgumentParser(description="Simple client test")
    parser.add_argument("-a", "--account", nargs="+", default=None, action='append', help="[<<username> <password> <character> [<character>...]>...]")
    args = parser.parse_args()
    if not args.account:
        print("Need account list!")
        exit()
    
    characters = []
    for account in args.account:
        try:
            chars = account[2:]
            acc = libfurc.Account.login(account[0], account[1])
            if len(chars) == 0:
                print("Using all characters on account {}".format(acc.email))
                for character in acc.characters:
                    characters.append(character)
            else:
                for c in chars:
                    found = False
                    for character in acc.characters:
                        if character.name == c:
                            found = True
                            characters.append(character)
                        
                    if not found:
                        print("Couldn't find character {} in account {}".format(c, acc.email))
                        exit()
        except libfurc.exceptions.LoginError as e:
            print(e)
            return
    
    data = {}
    visited = []
    toVisit = [DreamVisit(gomap = i) for i in range(95)]
    clients = []
    with open("dreams.jsons", "w") as f:
        def onVisit(dream):
            if dream:
                f.write(json.dumps(dream.toDict())+"\n")
        for character in characters:
            print("Logging into {}".format(character.name))
            client = Bot(character.name, data, visited, toVisit, onVisit).client
            motd = await client.connect()
            if not motd:
                print("Failed to connect to {}".format(character.name))
                continue
            await client.login(character)
            clients.append(client)
        
        await asyncio.gather(*[client.run() for client in clients])

asyncio.run(main())