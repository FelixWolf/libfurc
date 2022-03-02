#!/usr/bin/env
import libfurc
import argparse
import getpass
import asyncio

client = libfurc.Client()
@client.on("Login")
async def login(success):
    if success:
        print("Logged in!")
    else:
        print("Connection failed!")

@client.on("Message")
async def message(msg):
    print(msg)

@client.on("*")
async def t(name, *args, **kwargs):
    print(name, *args)

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