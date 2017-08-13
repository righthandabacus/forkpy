#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Queue
import argparse
import os
import threading

import pyaes

# Alt: key_256 = os.urandom(32) # 32*8 = 256 bits
KEY_256 = "TodayMeColdNightSeeSnowFlyAcross" # 今天我寒夜裡看雪飄過 32 bytes key
IV_128 = "SeaWide&SkyEmpty" # 海闊天空 16 bytes IV

class WorkerThread(threading.Thread):
    """
    A worker thread that takes filenames from a queue, work on each of them and
    reports the result.

    Ask the thread to stop by calling its join() method.
    """
    def __init__(self, file_q, result_q):
        super(WorkerThread, self).__init__()
        self.file_q = file_q
        self.result_q = result_q
        self.stoprequest = threading.Event()

    def run(self):
        # As long as we weren't asked to stop, try to take new tasks from the
        # queue. The tasks are taken with a blocking 'get', so no CPU
        # cycles are wasted while waiting.
        # Also, 'get' is given a timeout, so stoprequest is always checked,
        # even if there's nothing in the queue.
        while not self.stoprequest.isSet():
            try:
                filepath = self.file_q.get(True, 0.05)
                aes = pyaes.AESModeOfOperationCBC(KEY_256, iv=IV_128)
                infile = file(filepath)
                outfile = file('/dev/null', 'wb')
                pyaes.encrypt_stream(aes, infile, outfile)
                self.result_q.put((self.name, filepath))
            except Queue.Empty:
                continue

    def join(self, timeout=None):
        self.stoprequest.set()
        super(WorkerThread, self).join(timeout)

def main(indir):
    # Create a single input and a single output queue for all threads.
    file_q = Queue.Queue()
    result_q = Queue.Queue()

    # Scan dirs for files and populate file_q
    work_count = 0
    for path, dirs, files in os.walk(indir):
        for basename in files:
            filepath = os.path.join(path, basename)
            file_q.put(filepath)
            work_count += 1

    # Create the "thread pool" of 4
    pool = [WorkerThread(file_q=file_q, result_q=result_q) for _ in range(4)]

    # Start all threads
    for thread in pool:
        thread.start()

    print 'Assigned %s jobs to workers' % work_count

    # Now get all the results
    while work_count > 0:
        # Blocking 'get' from a Queue.
        result = result_q.get()
        print 'From thread %s: AES(%s)' % (result[0], result[1])
        work_count -= 1

    # Ask threads to die and wait for them to do it
    for thread in pool:
        thread.join()

if __name__ == '__main__':
    # argparse
    parser = argparse.ArgumentParser(description='Slow encrypter in multithread')
    parser.add_argument("-i", "--indir", help="Directory of input files", required=True)
    args = parser.parse_args()
    # invoke
    main(args.indir)
