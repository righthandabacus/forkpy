#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Queue
import argparse
import os
import sys
import time
import multiprocessing

import pyaes

# Alt: key_256 = os.urandom(32) # 32*8 = 256 bits
KEY_256 = "TodayMeColdNightSeeSnowFlyAcross" # 今天我寒夜裡看雪飄過 32 bytes key
IV_128 = "SeaWide&SkyEmpty" # 海闊天空 16 bytes IV

def aes_files(my_id, file_q, result_q):
    aes = pyaes.AESModeOfOperationCBC(KEY_256, iv=IV_128)
    while True:
        try:
            filepath = file_q.get_nowait() # no wait as the queue is pre-populated
        except Queue.Empty:
            return # if can't get from file queue, we're done
        infile = file(filepath)
        outfile = file('/dev/null', 'wb')
        pyaes.encrypt_stream(aes, infile, outfile)
        result_q.put((my_id, filepath))

def main(indir):
    # Create a single input and single output queue for all processes
    file_q = multiprocessing.Queue()
    result_q = multiprocessing.Queue()

    # Scan dirs for files and populate file_q
    work_count = 0
    for path, dirs, files in os.walk(indir):
        for basename in files:
            filepath = os.path.join(path, basename)
            file_q.put(filepath)
            work_count += 1

    # Create the "process pool" of 4
    pool = [multiprocessing.Process(target=aes_files, args=(i+1, file_q, result_q)) for i in range(4)]
    for process in pool:
        process.start()

    print 'Assigned %s jobs to workers' % work_count

    # Now get all the results
    while work_count > 0:
        # Blocking 'get' from a Queue.
        result = result_q.get()
        print 'From process %s: AES(%s)' % (result[0], result[1])
        work_count -= 1

    # Ask threads to die and wait for them to do it
    for process in pool:
        process.join()

if __name__ == '__main__':
    # argparse
    parser = argparse.ArgumentParser(description='Slow encrypter in multiprocessing')
    parser.add_argument("-i", "--indir", help="Directory of input files", required=True)
    args = parser.parse_args()
    # invoke
    main(args.indir)
