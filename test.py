#!/usr/bin/env
import libfurc
import argparse
import asyncio

parser = argparse.ArgumentParser(description="Simple client test")
parser.add_argument("account", help="Account name (Typically email address)")
parser.add_argument("password", help="Account password")
parser.add_argument("character", nargs="?", help="Character name (Leave blank for listing)")
args = parser.parse_args()

account = libfurc.Account.login(args.account, args.password)
if not args.character:
    print("Characters on {} (#{}):".format(account.email, account.id))
    for character in account.characters:
        print("  {}".format(character.name))
    exit()

character = account.findCharacter(args.character)

if not character:
    print("Can't find that character!")
    exit()

client = libfurc.Client()
@client.on("MOTD")
async def motd(data):
    print(data)
    await client.login(character)

@client.on("Login")
async def login(success):
    if success:
        print("Logged in!")
    else:
        print("Connection failed!")

@client.on("Message")
async def message(msg):
    print(msg)

asyncio.run(client.connect())