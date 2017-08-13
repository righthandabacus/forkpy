#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import multiprocessing

import pyaes

# Alt: key_256 = os.urandom(32) # 32*8 = 256 bits
KEY_256 = "TodayMeColdNightSeeSnowFlyAcross" # 今天我寒夜裡看雪飄過 32 bytes key
IV_128 = "SeaWide&SkyEmpty" # 海闊天空 16 bytes IV

def aes_a_file(filepath):
    aes = pyaes.AESModeOfOperationCBC(KEY_256, iv=IV_128)
    infile = file(filepath)
    outfile = file('/dev/null', 'wb')
    pyaes.encrypt_stream(aes, infile, outfile)

def main(indir):
    # Scan dirs for files and populate a list
    filepaths = []
    for path, dirs, files in os.walk(indir):
        for basename in files:
            filepath = os.path.join(path, basename)
            filepaths.append(filepath)
    work_count = len(filepaths)

    # Create the "process pool" of 4
    pool = multiprocessing.Pool(4)
    pool.map(aes_a_file, filepaths)

    print 'Completed %s jobs' % work_count

if __name__ == '__main__':
    # argparse
    parser = argparse.ArgumentParser(description='Slow encrypter in multiprocessing')
    parser.add_argument("-i", "--indir", help="Directory of input files", required=True)
    args = parser.parse_args()
    # invoke
    main(args.indir)
