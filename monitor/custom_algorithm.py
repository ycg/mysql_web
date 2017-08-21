# -*- coding: utf-8 -*-

def encrypt(key, value):
    b = bytearray(str(value).encode("utf8"))
    n = len(b)
    c = bytearray(n * 2)
    j = 0
    for i in range(0, n):
        b1 = b[i]
        b2 = b1 ^ key
        c1 = b2 % 16
        c2 = b2 // 16
        c1 += 65
        c2 += 65
        c[j] = c1
        c[j + 1] = c2
        j += 2
    return c.decode("utf8")


def decrypt(key, value):
    c = bytearray(str(value).encode("utf8"))
    n = len(c)
    if n % 2 != 0:
        return ""
    n //= 2
    b = bytearray(n)
    j = 0
    for i in range(0, n):
        c1 = c[j]
        c2 = c[j + 1]
        j += 2
        c1 -= 65
        c2 -= 65
        b2 = c2 * 16 + c1
        b1 = b2 ^ key
        b[i] = b1
    return b.decode("utf8")


if (__name__ == "__main__"):
    key = 20
    s1 = encrypt(key, "yangcaogui123!.+")
    s2 = decrypt(key, s1)
    print s1, '\n', s2
