#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
@package log_function.py
log_operation.py module handle execution report.
Create two differents reports:
        - error log
        - output log

For proper execution, at main module firstly call create function.
To include content at report use write functions.
Include close function to generate reports.

Error log are not printed during execution. If you want to print, uncomment \
'print' line at write_error function.
"""
import os
import time

TIME_START = str(time.strftime("%Y%m%d_%H%M%S"))
PATH_ERROR_FILE = str()
PATH_OUTPUT_FILE = str()


def create(path_to):
    '''
	Put logs into a directory 'logs' at path.
    Generate a Output log & Error log file with starting running time with format "%Y%m%d_%H_%M"
	'''
    if not os.path.exists(path_to):
        os.makedirs(path_to)
    path_log_folder = path_to
    global PATH_ERROR_FILE
    global ERROR_FILE
    global OUTPUT_FILE
    global PATH_OUTPUT_FILE

    PATH_ERROR_FILE = path_log_folder +'/error_' + TIME_START + '.log'
    ERROR_FILE = open(PATH_ERROR_FILE, 'a')
    PATH_OUTPUT_FILE = path_log_folder +'/output_' + TIME_START + '.log'
    OUTPUT_FILE = open(PATH_OUTPUT_FILE, 'a')

def write_error(text):
    '''Write the input at Error File
	This logs are not printed during execution. To print, uncomment print line at this function.'''
    ERROR_FILE.write(text)
    print(text)
    ERROR_FILE.write('\n')

def write_output(text):
    '''Write the input at Output File
	Print during execution this logs'''
    OUTPUT_FILE.write(text)
    print(text)
    OUTPUT_FILE.write('\n')

def close():
    '''Close files and remove log file if is empty'''
    OUTPUT_FILE.close()
    ERROR_FILE.close()
    with open(PATH_ERROR_FILE) as file:
        if not file.read(1):
            os.remove(PATH_ERROR_FILE)
    file.close()
    with open(PATH_OUTPUT_FILE) as file_read:
        if not file_read.read(1):
            os.remove(PATH_OUTPUT_FILE)
    file_read.close()
    