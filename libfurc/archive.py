#!/usr/bin/env python3
import struct
import io
import time
import bz2
import binascii
import os
#from . import lzw

#Filename, version, timestamp, filesize, crc32, compressionType
sRCHBlock = struct.Struct("<40sIIIII")

class RCHBlock:
    def __init__(self, parent, filename, version = 1, timestamp = 0, filesize = 0,
                 crc32 = None, compressionType = 2, offset = -1):
        self.parent = parent
        self.name = filename
        self.version = version
        self.timestamp = timestamp
        self.filesize = filesize
        self.crc32 = crc32
        self.compressionType = compressionType
        self.offset = offset
    
    def read(self, uncompressed = False):
        #Seek to location and past header
        self.parent.handle.seek(self.offset + sRCHBlock.size + 2)
        data = self.parent.handle.read(self.filesize)
        if uncompressed:
            return data
        
        if self.compressionType == 0:
            data = bytearray(data)
            for i in range(len(data)):
                data[i] = data[i] ^ 255
            raise NotImplementedError("LZW is not implemented at the moment!")
            decomp = lzw.LzwDecompressor()
            data = decomp.decompress(data)
        elif self.compressionType == 1:
            data = bytearray(data)
            for i in range(len(data)):
                data[i] = data[i] ^ 255
            data = bytes(data)
        elif self.compressionType == 2:
            data = bz2.decompress(data)
        else:
            raise ValueError("Invalid compression type {}".format(self.compressionType))
        return data
    
    def test(self):
        #For some reason, bzip checksum is the uncompressed data
        #all others is the checksum of the compressed data
        if self.compressionType == 2:
            return self.crc32 == binascii.crc32(self.read())
        
        elif self.compressionType == 0 or self.compressionType == 1:
            return self.crc32 == binascii.crc32(self.read(uncompressed=True))
    
#Version, creation time, 4 unsigned ints of reserved
sRCHHeader = struct.Struct("<II16x")

class RCHFile:
    def __init__(self, handle, compressionlevel = 9):
        self.handle = handle
        self.compressionlevel = compressionlevel
        self.files = []
    
    def load(self):
        self.handle.seek(0)
        """Load a metadata into memory"""
        magic = self.handle.read(4)
        
        if len(magic) == 0: #Create data
            return
        elif magic == b"FR01": #Load existing data
            version, timestamp = sRCHHeader.unpack(self.handle.read(sRCHHeader.size))
            #Disabled this check because it'll always be the same thing
            #but the installer has different values.
            #if version != 1:
            #    raise ValueError("Don't know how to read RCH version {}".format(version))
        else:
            raise ValueError("Not a valid RCH archive!")
        
        self.files = []
        
        while True:
            offset = self.handle.tell()
            magic = self.handle.read(2)
            if len(magic) == 0:
                #End of file
                break
            
            if magic != b"FZ":
                raise ValueError("Corrupted RCH file!")
            
            else:
                filename, version, timestamp, filesize, crc32, \
                    compressionType = sRCHBlock.unpack(self.handle.read(sRCHBlock.size))
                
                if version != 1:
                    raise ValueError("Don't know how to read RCH block version {}".format(version))
                
                filename = filename.rstrip(b"\0").decode()
                
                self.files.append(RCHBlock(self, filename, version, timestamp, \
                    filesize, crc32, compressionType, offset))
                self.handle.seek(filesize, 1) #Seek past the data
    
    def getFile(self, name):
        for file in self.files:
            if file.name == name:
                return file
        return None
    
    def add(self, name, data):
        self.handle.seek(0, 2)
        self.handle.write(b"FZ")
        test = bz2.compress(data)
        crc32 = 0
        compression = 1
        if len(data) > len(test):
            #Yes this is correct, before we compress
            crc32 = binascii.crc32(data)
            data = test
            compression = 2
            del test
        else:
            del test
            data = bytearray(data)
            for i in range(len(data)):
                data[i] = data[i] ^ 255
            data = bytes(data)
            #Yes this is correct, after we "compress"
            crc32 = binascii.crc32(data)
        
        self.handle.write(sRCHBlock.pack(name.encode(), 1, 0, len(data), crc32, compression))
        self.handle.write(data)
    
    def write(self):
        self.handle.seek(0)
        self.handle.truncate()
        self.handle.write(b"FR01")
        #Version 1, no timestamp
        self.handle.write(sRCHHeader.pack(1, 0))
        
        chunks = {}
        for file in self.files:
            if file.filesize > 0:
                chunks[file.name] = file.read()
        
        for chunk in chunks:
            self.handle.write(b"FZ")
            data = chunks[chunk]
            test = bz2.compress(data)
            crc32 = 0
            compression = 1
            if len(data) > len(test):
                #Yes this is correct, before we compress
                crc32 = binascii.crc32(data)
                data = test
                compression = 2
                del test
            else:
                del test
                data = bytearray(data)
                for i in range(len(data)):
                    data[i] = data[i] ^ 255
                data = bytes(data)
                #Yes this is correct, after we "compress"
                crc32 = binascii.crc32(data)
            
            self.handle.write(sRCHBlock.pack(chunk.encode(), 1, 0, len(data), crc32, compression))
            self.handle.write(data)
        
        self.handle.truncate()
    
    @classmethod
    def open(cls, filename, mode = "rb"):
        handle = None
        
        if type(filename) == str:
            handle = open(filename, mode)
        elif isinstance(filename, io.IOBase):
            handle = filename
        
        self = cls(handle)
        self.load()
        return self

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Handle RCH files')
    parser.add_argument('command', choices=("a", "d", "e", "l", "t"),
                        help='Command to use. (a = add; d = delete; e = extract')
    parser.add_argument('archive')
    parser.add_argument('filenames', nargs="*")

    args = parser.parse_args()
    
    mode = None
    if args.command in ["a", "d"]:
        mode = "a+b"
    elif args.command in ["e", "l", "t"]:
        mode = "rb"
    
    handle = open(args.archive, mode)
    
    archive = RCHFile.open(handle)
    
    if args.command == "l":
        for file in archive.files:
            print(file.name)
    
    elif args.command == "t":
        for file in archive.files:
            print("[{}] {}".format("PASS" if file.test() else "FAIL", file.name))
    
    elif args.command == "e":
        if not args.filenames:
            args.filenames = [i.name for i in archive.files]
        
        for file in args.filenames:
            data = archive.getFile(file)
            if not data:
                print("Couldn't find file \"{}\" in archive!".format(file))
            with open(file, "wb") as f:
                f.write(data.read())
        
    elif args.command == "d":
        for file in args.filenames:
            data = archive.getFile(file)
            if not data:
                print("Couldn't find file \"{}\" in archive!".format(file))
            data.filesize = -1
        archive.write()
    
    elif args.command == "a":
        for file in args.filenames:
            with open(file, "rb") as f:
                archive.add(os.path.basename(file), f.read())
    

if __name__ == "__main__":
    main()
