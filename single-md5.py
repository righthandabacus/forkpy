#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import hashlib

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='MD5 hasher')
    parser.add_argument("-f", "--filename", required=True)
    args = parser.parse_args()

    md5 = hashlib.md5() # or sha512, etc.
    md5.update(open(args.filename).read())
