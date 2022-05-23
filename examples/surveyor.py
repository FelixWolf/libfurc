#!/usr/bin/env
import libfurc
import argparse
import getpass
import asyncio
import time

class DreamVisit:
    def __init__(self, owner = None, name = None, parent = None, gomap = None):
        self.owner = owner
        self.name = name
        self.parent = parent
        self.gomap = gomap
        self.available = False
        self.entryText = None
        self.standard = None
        self.patch = None
        self.checksum = None
    
    def __str__(self):
        return "furc://{}{}/ gomap {} standard {}".format(self.owner, ":"+self.name if self.name != "|" and self.name != None else "", self.gomap, self.standard)

data = {}
visited = []
toVisit = [DreamVisit(gomap = i) for i in range(95)]
currentDream = None
timeSinceLast = time.time()

async def timer():
    global currentDream, timeSinceLast
    while True:
        if timeSinceLast + 5 < time.time():
            await visitNext()
        await asyncio.sleep(1)

async def visitNext():
    global currentDream, timeSinceLast
    step = time.time() - timeSinceLast
    if step < 2:
        await asyncio.sleep(2)
    
    if len(toVisit) <= 0:
        print("Should disconnect now!")
        return
    
    print("Discovered "+str(currentDream))
    currentDream = toVisit.pop(0)
    timeSinceLast = time.time()
    
    if currentDream.gomap != None:
        await client.command("gomap {}".format(chr(32+currentDream.gomap)))
    elif currentDream.name != None:
        await client.command("fdl furc://{}:{}/".format(currentDream.owner, currentDream.name))
    elif currentDream.owner != None:
        await client.command("fdl furc://{}/".format(currentDream.owner))
    else:
        print("Encountered empty dream visit!")
        await visitNext()
    

client = libfurc.Client()
@client.on("Login")
async def login(success):
    global currentDream, timeSinceLast
    if success:
        print("Logged in!")
    else:
        print("Connection failed!")
    
    timeSinceLast = time.time()
    await visitNext()
    asyncio.ensure_future(timer())


@client.on("Message")
async def message(msg):
    global currentDream
    if currentDream.entryText == None and \
        msg.startswith(b"<font color='emit'><img src='fsh://system.fsh:91' alt='@emit' /><channel name='@emit' />"):
        currentDream.entryText = msg
        await visitNext()
    if msg.startswith(b"<img src='fsh://system.fsh:86' /> Dream Standard: <a href='http://www.furcadia.com/standards/'>"):
        currentDream.standard = msg.split(b"<a href='http://www.furcadia.com/standards/'>")[1].split(b"</a>")[0].decode()
    #print(msg)

@client.on("Dream")
async def dream(patched, package, checksum, modern):
    global currentDream, timeSinceLast
    timeSinceLast = time.time()
    if currentDream == None:
        await visitNext()
    else:
        visited.append(currentDream)
        currentDream.patch = package
        currentDream.checksum = checksum
        await client.vascodagama()
        await client.command("dreambookmark 0")
        currentDream.available = True

@client.on("Bookmark")
async def bookmark(user, fdl):
    global currentDream
    d = fdl.split("furc://",1)[-1].split("/")[0].split(":")
    if len(d) == 1:
        currentDream.owner = d[0]
        currentDream.name = "|"
    elif len(d) == 2:
        currentDream.owner = d[0]
        currentDream.name = d[1]

@client.on("Text")
async def text(pos, t, owner, name, maturity, gateType):
    visit = DreamVisit(owner.decode(), name.decode(), parent = currentDream)
    print("Added {} to visit list".format(str(visit)))
    toVisit.append(visit)
    
#@client.on("*")
#async def t(name, *args, **kwargs):
#    print(name, *args)

async def main():
    parser = argparse.ArgumentParser(description="Simple client test")
    parser.add_argument("-a", "--account", default=None, help="Account name (Typically email address)")
    parser.add_argument("-p", "--password", default=None, help="Account password")
    parser.add_argument("-c", "--character", default=None, help="Character name (Leave blank for listing)")
    args = parser.parse_args()
    if not args.account:
        args.account = input("Username / email: ")
    
    if not args.password:
        args.password = getpass.getpass()
    
    try:
        account = libfurc.Account.login(args.account, args.password)
    except libfurc.exceptions.LoginError as e:
        print(e)
    
    character = None
    if not args.character or not character:
        while True:
            print("Characters on {} (#{}):".format(account.email, account.id))
            for i, character in enumerate(account.characters):
                print(" {}. {}".format(i+1, character.name))
            cn = input("Character name or ID: ")
            try:
                character = account.characters[int(cn)-1]
            except ValueError:
                character = account.findCharacter(cn)
            if character:
                break
            else:
                print("Can't find that character")

    if not character:
        print("Can't find that character!")
        exit()
    motd = await client.connect()
    if not motd:
        print("Failed to connect. Is the address correct?")
        return
    print(motd)
    await client.login(character)
    await client.run()

asyncio.run(main())