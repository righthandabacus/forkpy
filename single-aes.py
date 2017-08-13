#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os

import pyaes # https://github.com/ricmoo/pyaes

# Alt: key_256 = os.urandom(32) # 32*8 = 256 bits
KEY_256 = "TodayMeColdNightSeeSnowFlyAcross" # 今天我寒夜裡看雪飄過 32 bytes key
IV_128 = "SeaWide&SkyEmpty" # 海闊天空 16 bytes IV

if __name__=='__main__':
    # argparse
    parser = argparse.ArgumentParser(description='Slow encrypter')
    parser.add_argument("-i", "--infile", help="Path to input", required=True)
    parser.add_argument("-o", "--outfile", help="Path to output", default='/dev/null')
    parser.add_argument("-d", "--decrypt", action='store_true', default=False, help="Decrypt instead of encrypt")
    args = parser.parse_args()
    # invoke
    aes = pyaes.AESModeOfOperationCBC(KEY_256, iv=IV_128)
    infile = file(args.infile)
    outfile = file(args.outfile, 'wb')
    if not args.decrypt:
        pyaes.encrypt_stream(aes, infile, outfile)
    else:
        pyaes.decrypt_stream(aes, infile, outfile)
    infile.close()
    outfile.close()
