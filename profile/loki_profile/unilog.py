#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
# Author: Ke Jie <jinxi.kj@taobao.com>
# Copyright (C) taobao.com 2011

''' Singleton Logger for Python
'''

import os
import sys
import logging
import logging.handlers

class _UniLogger(logging.getLoggerClass()):
    @classmethod
    def instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls("")
        return cls._instance

unilogger = _UniLogger.instance()

def setup_rotating_log(logname):
    rotating_file_handler = logging.handlers.RotatingFileHandler(logname, "a", 134217728, 7)
    fmt = logging.Formatter("%(asctime)s %(filename)s(%(lineno)s): %(levelname)-5s %(message)s", "%x %X")
    rotating_file_handler.setFormatter(fmt)
    unilogger.addHandler(rotating_file_handler)

def setup_console_log():
    console = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s %(filename)s(%(lineno)s): %(levelname)-5s %(message)s", "%x %X")
    console.setFormatter(fmt)
    unilogger.addHandler(console)

def rotating_sample(logname):
    rotating_file_handler = logging.handlers.RotatingFileHandler(logname, "a", 134217728, 7)
    fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
    rotating_file_handler.setFormatter(fmt)
    unilogger.addHandler(rotating_file_handler)

def console_sample():
    console = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
    console.setFormatter(fmt)
    unilogger.addHandler(console)

def main():
    ''' main function
    '''
    unilogger.setLevel(logging.DEBUG)

    rotating_sample('test.log')
    unilogger.info('rotating handler')

    console_sample()
    unilogger.info('both rotating and console handler')
    print 'Done'

if __name__ == '__main__':
    main()
