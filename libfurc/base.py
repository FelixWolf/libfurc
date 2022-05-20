#!/usr/bin/env python3

def b95encode(i, size = None):
    out = b""
    while i > 0:
        out = bytes([i % 95 + 32]) + out
        i = i // 95
    
    #Pad if needed
    if size:
        out = out[:size]
        if len(out) < size:
            out = b" "*(size - len(out)) + out
    
    return out

def b95decode(data):
    out = 0
    for c in data:
        if c >= 32 and c < 127:
            out = (out * 95) + (c - 32)
        else:
            raise ValueError("Invalid base95 character!")
    return out

def b220encode(i, size = None):
    out = b""
    while i > 0:
        out = out + bytes([i % 220 + 35])
        i = i // 220
    
    #Pad if needed
    if size:
        out = out[:size]
        if len(out) < size:
            out = out + b"#"*(size - len(out))
    
    return out

def b220decode(data):
    out = 0
    i = 1
    for c in data:
        if c >= 35 and c < 255:
            out = out + ((c - 35) * i)
            i *= 220
        else:
            raise ValueError("Invalid base220 character!")
    return out

def unitTests():
    b95Tests = [
        ((0, None), b''),
        ((94, None), b'~'),
        ((95, None), b'! '),
        ((43, None), b'K'),
        ((583, None), b'&-'),
        ((2299, None), b'83'),
        ((0, 2), b'  '),
        ((94, 2), b' ~'),
        ((95, 2), b'! '),
        ((43, 2), b' K'),
        ((583, 2), b'&-'),
        ((2299, 2), b'83'),
    ]
    for test in b95Tests:
        assert b95encode(*test[0]) == test[1], "Base95 encode for {} (Padding: {}) failed!".format(*test[0])

    for test in b95Tests:
        assert b95decode(test[1]) == test[0][0], "Base95 decode for {} (Padding: {}) failed!".format(*test[0])

    b220Tests = [
        ((0, None), b''),
        ((219, None), b'\xfe'),
        ((220, None), b'#$'),
        ((43, None), b'N'),
        ((583, None), b'\xb2%'),
        ((2299, None), b'\x86-'),
        ((0, 2), b'##'),
        ((219, 2), b'\xfe#'),
        ((220, 2), b'#$'),
        ((43, 2), b'N#'),
        ((583, 2), b'\xb2%'),
        ((2299, 2), b'\x86-'),
    ]
    for test in b220Tests:
        assert b220encode(*test[0]) == test[1], "Base220 encode for {} (Padding: {}) failed!".format(*test[0])

    for test in b220Tests:
        assert b220decode(test[1]) == test[0][0], "Base220 decode for {} (Padding: {}) failed!".format(*test[0])


if __name__ == "__main__":
    unitTests()