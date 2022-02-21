#!/usr/bin/env python3 
import asyncio

LIVE_SERVER = ("lightbringer.furcadia.com", 6500)

#Incoming message definitions
class DefaultPacketHandler:
    async def message_unhandled(self, *args, **kwargs):
        pass

class PacketHooks(DefaultPacketHandler):
    def __init__(self):
        self.listeners = {}
    
    #Message "]" - Protocol extension
    async def message_61(self, data):
        if len(data) < 2:
            return
        await getattr(
            self,
            "message_61_" + str(data[1]-32),
            self.message_unhandled
        )(data)
    
    #Hook definitions
    async def fire(self, name, *args, **kwargs):
        if name not in self.listeners:
            return False
        
        for callback in self.listeners[name]:
            await callback(*args, **kwargs)
        
        return True
    
    def on(self, func):
        def _(name, *args, **kwargs):
            if name not in self.listeners:
                self.listeners[name] = []
            self.listeners[name].append(name)
            return func
        return _
    
    def off(self, name, func):
        if name not in self.listeners:
            return
        self.listeners[name].remove(name)

#Outgoing message definitions
class Commands:
    async def login(self):
        pass
    
    async def move(self, direction):
        pass
    
    async def rotate(self, direction):
        pass
    
    async def say(self, message):
        pass

class Client(PacketHooks, Commands):
    def __init__(self, server = None):
        super().__init__()
        self.reader = None
        self.writer = None
        self.server = server or LIVE_SERVER
    
    #Basic networking stuff
    async def connect(self, server = None):
        if self.connected():
            await self.disconnect()
        if not server:
            server = self.server
        
        self.reader, self.writer = await asyncio.open_connection(
            server[0], server[1])
        
        eventLoop = loop.create_task(self.readLoop())
        return eventLoop
    
    async def disconnect(self):
        writer.close()
        await writer.wait_closed()
    
    async def send(self, data):
        if self.connected():
            await writer.write(data+b"\n")
            await writer.drain()
            return True
        return False
    
    @property
    def connected(self):
        if self.reader == None or self.writer == None:
            return False
        return True
    
    #Actual read loop, it is designed to be it's own task
    async def readLoop():
        while True:
            if not self.reader:
                break
            
            data = self.reader.readline()
            if not data:
                break
            
            if data[-1] != b"\n":
                break
            
            data = data[:-1]
            
            if len(data) == 0:
                continue
            
            await getattr(
                self,
                "message_" + str(data[0]-32),
                self.message_unhandled
            )(data)
            
        self.reader = None
        self.writer = None