These are the code samples for HKPyUG meeting on 2017-08-14.

# Single thread

```
$ time for x in _Tolo_1/* ; do python single-md5.py -f "$x" ; done

real	0m0.247s
user	0m0.144s
sys	0m0.076s

$ time for x in _Tolo_1/* ; do python single-aes.py -i "$x" ; done

real	0m31.259s
user	0m31.116s
sys	0m0.104s
```

# Multithread

```
$ time python mt-aes.py -i _Tolo_1/
Assigned 6 jobs to workers
From thread Thread-1: AES(_Tolo_1/Tolo-Morning-01.jpg)
From thread Thread-3: AES(_Tolo_1/Tolo-Morning-03.jpg)
From thread Thread-4: AES(_Tolo_1/Tolo-Morning-04.jpg)
From thread Thread-2: AES(_Tolo_1/Tolo-Morning-02.jpg)
From thread Thread-3: AES(_Tolo_1/Tolo-Morning-06.jpg)
From thread Thread-1: AES(_Tolo_1/Tolo-Morning-05.jpg)

real	0m48.253s
user	0m40.309s
sys	0m24.649s
```

Note that Queue implemnted locking semantics

# Module multiprocessing

Using Pool:

```
$ time python mp-pool-aes.py -i _Tolo_1/
Completed 6 jobs

real	0m10.978s
user	0m32.521s
sys	0m0.192s
```

Using Process:

```
$ time python mp-process-aes.py -i _Tolo_1/
Assigned 6 jobs to workers
From process 3: AES(_Tolo_1/Tolo-Morning-03.jpg)
From process 1: AES(_Tolo_1/Tolo-Morning-01.jpg)
From process 4: AES(_Tolo_1/Tolo-Morning-04.jpg)
From process 2: AES(_Tolo_1/Tolo-Morning-02.jpg)
From process 1: AES(_Tolo_1/Tolo-Morning-06.jpg)
From process 3: AES(_Tolo_1/Tolo-Morning-05.jpg)

real	0m11.204s
user	0m33.348s
sys	0m0.179s
```

Note that Queue implemented using pipe, locks, and semaphores

# Timed fork execute

```
$ time python fork-aes.py -i _Tolo_1/

real	0m12.306s
user	0m33.217s
sys	0m0.233s

```
