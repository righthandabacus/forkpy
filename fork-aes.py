#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import logging
import time
import traceback

from fork import timed_exec, JobQueue, JobThread
import pyaes

# Alt: key_256 = os.urandom(32) # 32*8 = 256 bits
KEY_256 = "TodayMeColdNightSeeSnowFlyAcross" # 今天我寒夜裡看雪飄過 32 bytes key
IV_128 = "SeaWide&SkyEmpty" # 海闊天空 16 bytes IV

PROCESS_COUNT = 4
JOB_TIMEOUT = 30

def worker_main(filepath):
    """
    Real worker: doing all CPU intensive thing
    """
    aes = pyaes.AESModeOfOperationCBC(KEY_256, iv=IV_128)
    infile = file(filepath)
    outfile = file('/dev/null', 'wb')
    pyaes.encrypt_stream(aes, infile, outfile)

def foreman(filename):
    '''
    Worker function. It calls timed_exec() to spawn a new process instead of running as a thread
    '''
    cmdline = [os.path.realpath(__file__), '-f', filename] # command line to call
    logging.info("Running "+str(cmdline))
    return (timed_exec(cmdline, JOB_TIMEOUT) >= 0)

def master_main(indir):
    '''
    Clone several threads to synchronize the local workspace cache. Run this for a few seconds then die.
    '''
    # create thread objects, with function specified as worker
    jobqueue = JobQueue()
    jobthreads = [JobThread(jobqueue, foreman) for _ in range(PROCESS_COUNT)]

    # Scan dirs for files and populate 
    work_count = 0
    for path, dirs, files in os.walk(indir):
        for basename in files:
            filepath = os.path.join(path, basename)
            jobqueue.put(filepath)
            work_count += 1

    # start all threads
    for t in jobthreads:
        t.start()

    # run for some time, then terminate all threads
    BUDGET = 30
    RECHECK_TIMEOUT = 1
    try:
        logging.info('Total wall-clock time budget of %d seconds' % BUDGET)
        starttime = nowtime = time.time()
        endtime = starttime + BUDGET
        while True: # Make sure there is progress
            time.sleep(min(endtime-nowtime, RECHECK_TIMEOUT))
            nowtime = time.time()
            if nowtime >= endtime or jobqueue.is_empty():
                break
            elif jobqueue.lastdone and not jobqueue.is_empty() and (nowtime-jobqueue.lastdone) > JOB_TIMEOUT:
                raise RuntimeError('Stalled progress?')
            elif not all(t.is_alive() for t in jobthreads):
                raise RuntimeError('Some thread dead?')
        logging.info('Done')
    except KeyboardInterrupt, e:
        logging.error('Interrupted by user')
        logging.error(e)
        logging.error(traceback.format_exc())
    except Exception, e:
        logging.error('Interrupted by exception')
        logging.error(e)
        logging.error(traceback.format_exc())
    finally:
        logging.info('Terminating all threads...')
        for t in jobthreads:
            t.done()
        for t in jobthreads:
            t.join()
        logging.info('all done')


if __name__ == '__main__':
    #logging.basicConfig(level=logging.DEBUG)
    # argparse
    parser = argparse.ArgumentParser(description='Slow encrypter in multithread')
    parser.add_argument("-i", "--indir", help="Directory of input files")
    parser.add_argument("-f", "--filename", help="Path to one input file")
    args = parser.parse_args()
    # invoke
    if args.indir:
        master_main(args.indir)
    else:
        worker_main(args.filename)
