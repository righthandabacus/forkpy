import Queue
import logging
import os
import select
import subprocess
import sys
import threading
import time

def status_code(status):
    '''
    Decode child process exit code.
    status is the exist status indication from os.waitpid(pid,0)[1]
    '''
    if os.WIFSIGNALED(status): # process exited due to a signal
        # get the signal which caused the process to exit: make it negative to
        # distinguish from exit(2) call
        return -os.WTERMSIG(status)
    elif os.WIFEXITED(status): # process exited using exit(2) system call
        # get the integer parameter to exit(2) call
        return os.WEXITSTATUS(status)
    elif os.WIFSTOPPED(status) or os.WIFCONTINUED(status):
        raise RuntimeError("Child stopped or continued?")
    elif os.WCOREDUMP(status):
        raise RuntimeError("Child core dump!")
    else:
        raise RuntimeError("Unknown child return status!")

TIMEOUT_RETCODE = -24

def timed_exec(commandline, timeout):
    '''
    Run a command in a new process for up to `timeout` seconds. Usage:

        mypath = os.path.dirname(os.path.realpath(__file__))
        timed_exec([os.path.join(mypath,"foo.py"), arg1, arg2], 10e3)

    Note: (1) child process maintains its stdin open for parent process to
    detect it is alive. The command to run must not do os.close(sys.stdin.fileno());
    (2) return code -24 is reserved to mean child process killed due to time
    out, otherwise the return code from child process is passed through;
    '''
    if 'poll' in dir(select):
        # Method for Linux: Using poll
        popenobj = subprocess.Popen(commandline, stdin=subprocess.PIPE)
        pollobj = select.poll()
        pollobj.register(popenobj.stdin, select.POLLHUP)
        if len(pollobj.poll(timeout * 1e3)) == 0: # timeout in seconds -> milliseconds
            if sys.version_info >= (2,6):
                popenobj.kill() # Python 2.6+
            else:
                os.kill(popenobj.pid, 9) # Python <=2.5 only
            return TIMEOUT_RETCODE
        else:
            popenobj.wait()
            return popenobj.returncode
    else:
        # Alternative method: using thread
        popenobj = subprocess.Popen(commandline)
        timer = threading.Timer(timeout, popenobj.kill) # popenobj.kill needs Python 2.6+
        timer.start()
        popenobj.communicate() # block until subprocess terminated
        if timer.is_alive():
            timer.cancel() # timer didn't fire before subprocess terminate
            return popenobj.poll() # return the subprocess' retcode
        else:
            logging.info("Killed %s" % commandline)
            return TIMEOUT_RETCODE

def timed_fork(functor, timeout):
    '''
    Run the functor in a new process for up to `timeout` milliseconds. Usage:

        timed_fork(myfunction, 10e3)

    Note: (1) child process maintains its stdin open for parent process to
    detect it is alive. The function to run must not do
    os.close(sys.stdin.fileno()); (2) return code -24 is reserved to mean child
    process killed due to time out, otherwise the return code from child process
    is passed through; (3) Using the multiprocessing module might be a better
    solution in Python 2.6+
    '''
    r, w = os.pipe()
    pid = os.fork()
    if not pid: # child
        os.close(r)
        try:
            functor()
        except:
            os.close(w)
            os._exit(2)
        finally:
            os.close(w)
            os._exit(0)
    else:       # parent
        try:
            os.close(w)
            p = select.poll()
            p.register(r, select.POLLHUP)
            if len(p.poll(timeout)) == 0:
                os.kill(pid, 9)
                return TIMEOUT_RETCODE
        finally:
            rcode = status_code(os.waitpid(pid,0)[1])
            os.close(r)
            return rcode

class JobThread(threading.Thread):
    '''
    A thread to consume the JobQueue and call the workhorse
    '''
    def __init__(self, jobqueue, jobfunc):
        self.__queue   = jobqueue   # JobQueue object to hold deal tuples
        self.__done    = False      # If True, this thread terminates
        self.__worker  = jobfunc    # func takes job as argument and fork out
        threading.Thread.__init__(self)

    def done(self):
        self.__done = True
        self.__queue.destroy()

    def run(self):
        while not self.__done:
            try:
                logging.info("Try getting job from queue")
                job = self.__queue.get()
            except Queue.Empty:
                if not self.__queue.is_done():
                    time.sleep(0.25) # sleep for a short while to prevent CPU overheat
                    continue
                else:
                    break
            if job is None:
                time.sleep(0.25) # queue depleted but not sure if working job can finish
                continue
            success = self.__worker(job)
            self.__queue.completed(job)
            if not success: # job isn't success, try again
                logging.info("To retry: %s" % job)
                self.__queue.put(job)
        logging.info("Work thread terminated")

class JobQueue(object):
    '''
    A job queue architecture with thread-safe locks. Remembers jobs in queue
    and jobs in progress such that we can re-enqueue a halted working job.
    Interface function destroy() is provided to signal for graceful termination.

    Job is any object that equality comparison is defined to indicate jobs are
    identical. The queue behaviour satisfies the following:
       - no two identical job can be in the queue
       - each job in the queue is in waiting, blocked, or working state
       - when a new job is enqueued by put(job), it is in waiting state
       - get() call returns a job and transit the job from waiting to working state
       - get() may return None if no job is in waiting state
       - complete(job) call removes a job from queue if it is in working state
    '''
    def __init__(self):
        self.__lock = threading.Lock()
        self.__queue = []
        self.__working = []
        self.__done = False
        self.lastdone = None


    def is_done(self):
        return self.__done

    def is_empty(self):
        "Empty job queue only if nothing in queue and working on nothing"
        return not self.__queue and not self.__working

    def destroy(self):
        self.__done = True
        logging.info("JobQueue marked done")

    def completed(self, job):
        '''
        Remove a job from the working set
        '''
        with self.__lock:
            self.__working = [w for w in self.__working if w != job]
            self.lastdone = time.time()
            logging.info("Completed job: %s" % job)

    def get(self):
        '''
        Get the first job from self.__queue
        '''
        with self.__lock:
            if not self.__working and not self.__queue and self.__done:
                raise Queue.Empty   # raise if nothing in the queue and JobQueue marked done
            if not self.__queue:
                return None
            job = self.__queue[0]
            self.__working.append(job)
            self.__queue = self.__queue[1:]
            logging.info("Dispatch job: %s" % job)
            return job

    def put(self, job):
        '''
        Append a tuple into self.__queue, unless it already exists
        '''
        with self.__lock:
            if [w for w in self.__queue if w==job]:
                logging.info("Ignore in-queue job: %s" % job)
                return
            if [w for w in self.__working if w==job]:
                logging.info("Ignore working job: %s" % job)
                return
            self.__queue.append(job)
