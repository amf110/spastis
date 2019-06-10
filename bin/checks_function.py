#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
@package check_function.py
Created on Wed May 15 00:05:16 2019

Documentacion extras
This document needs
"""

import os
import log_function as log

def check_value_from_list(value_to_check, list_to_check, key_list, value_list):
    '''
    Checks values from a list of correct values and in case that a value is wrong write error logs.
    This function does not specify a return value. Return value always will be None.
    '''
    try:
        index = key_list.index(value_to_check)
        val = value_list[index]
        try:
            list_to_check.index(val)
        except ValueError:
            msg_err = "ERROR: Parameter '" + value_to_check \
            + "'. It has a wrong value: " + val
            log.write_error(msg_err)
    except ValueError:
        msg_err = "ERROR: Parameter needed '" + value_to_check \
        + "'. It is not defined on parameter list."
        log.write_error(msg_err)


def check_numerical_value(value_to_check, key_list, value_list):
    '''
    Check if value of a parameter is numeric.
    If not write at error log.
    If value to check does not find on key list, write at error log.
    This function does not specify a return value. Return value always will be None.
    '''
    try:
        index_tc = key_list.index(value_to_check)
        val_tc = value_list[index_tc]
        try:
            float(val_tc)
        except ValueError:
            msg_err_num = "ERROR: Parameter '" + value_to_check \
            + "' should has a numeric value. It has a wrong value: " + val_tc
            log.write_error(msg_err_num)
    except ValueError:
        msg_err_num = "ERROR: Parameter '" + value_to_check \
        +"' it is not defined on parameter list."
        log.write_error(msg_err_num)



def check_parameter_value(steps_todo, key_list, value_list):
    '''
    Check each step setted at steps to do.
    Call specifics check functions for each step.
    This function does not specify a return value. Return value always will be None.
    '''
    check_write(key_list, value_list)
    if 'Subset' in steps_todo:
        check_subset(key_list, value_list)

    if 'Speckle-Filter' in steps_todo:
        check_speckle(key_list, value_list)

    if 'Terrain-Correction' in steps_todo:
        check_terrain_correction(key_list, value_list)

    if 'CreateStack' in steps_todo:
        check_create_stack(key_list, value_list)



def check_subset(key_list, value_list):
    '''
    Verification values that are necessary to do Subset process.
    We check that all necessary values are on .par file.
    Also we check that the values are properly setted.
    This function does not specify a return value. Return value always will be None.

    Write Error error log in case:
        - Parameter has a wrong value. Feedback about parameter and current value.
        - A necessary parameter is missing.
        - Coordinates format has a incorrect value.
    '''
    index = key_list.index('~COORDINATES_FORMAT')
    values_coord_format = ['FileXML', 'Geographics', 'Pixel']
    value = value_list[index]
    if value == 'Pixel':
        correct_pixel = ['~PIXEL_X', '~PIXEL_Y', '~PIXEL_WIDTH', '~PIXEL_HEIGHT']
        for i in correct_pixel:
            check_numerical_value(i, key_list, value_list)
    if value == 'Geographics':
        correct_geo = ['~LATMAX', '~LONMAX', '~LATMIN', '~LONMIN']
        for i in correct_geo:
            check_numerical_value(i, key_list, value_list)
    if value == 'FileXML':
        index_path = key_list.index('~KML_FILE_ROUTE')
        path_file = value_list[index_path]
        if not os.path.isfile(path_file):
            msg_err_xmlfile = "ERROR: XML file does not exist at path: " + path_file + "."
            log.write_error(msg_err_xmlfile)
    if not value in values_coord_format:
        msg_err_cf = "ERROR: Value of parameter '~COORDINATES_FORMAT' is wrong. "\
        "Should be  'FileXML', 'Geographics', 'Pixel'. Current value: " + value
        log.write_error(msg_err_cf)



def check_speckle(key_list, value_list):
    '''
    Verification values that are necessary to do Speckle-Filter process.
    We check that all necessary values are on .par file.
    Also we check that the values are properly setted.
    This function does not specify a return value. Return value always will be None.

    Write Error error log in case:
        - Parameter has a wrong value. Feedback about parameter and current value.
        - A necessary parameter is missing.
    '''
    speckle_values = ['IDAN', 'Boxcar']
    check_value_from_list('~TYPE_OF_FILTER', speckle_values, key_list, value_list)
    check_numerical_value('~FILTER_SIZE', key_list, value_list)


def check_terrain_correction(key_list, value_list):
    '''
    Verification values that are necessary to do Terrain-Correction process.
    We check that all necessary values are on .par file.
    Also we check that the values are properly setted.
    This function does not specify a return value. Return value always will be None.

    Write Error error log in case:
        - Parameter has a wrong value. Feedback about parameter and current value.
        - A necessary parameter is missing.
    '''
    dem_res_method_values = ['BILINEAR_INTERPOLATION', '~BICUBIC_INTERPOLATION']
    img_res_method_values = ['BILINEAR_INTERPOLATION', '~BICUBIC_INTERPOLATION']
    dem_model_values = ['SRTM 3Sec', 'SRTM 1Sec HGT']
    map_projec_values = ['WGS84', 'UTM']
    ######################################
    check_value_from_list('~DEM_RESAMPLING_METHOD', dem_res_method_values, key_list, value_list)
    check_value_from_list('~IMG_RESAMPLING_METHOD', img_res_method_values, key_list, value_list)
    check_value_from_list('~DEM_MODEL', dem_model_values, key_list, value_list)
    check_value_from_list('~MAP_PROJECTION', map_projec_values, key_list, value_list)
    check_numerical_value('~PIXEL_SPACING_METERS', key_list, value_list)
    check_numerical_value('~PIXEL_SPACING_DEGREE', key_list, value_list)



def check_write(key_list, value_list):
    '''
    Verification output values.
    We check that all necessary values are on .par file.
    Also we check that the values are properly setted.
    This function does not specify a return value. Return value always will be None.

    Write Error error log in case:
        - Parameter has a wrong value. Feedback about parameter and current value.
        - A necessary parameter is missing.
    '''
    write_forma_values = ['BEAM-DIMAP', 'GeoTIFF']
    check_value_from_list('~WRITE_FORMAT', write_forma_values, key_list, value_list)



def check_parameter_key(key_list):
    '''
    Check that parameters key name start with '~'.
    This function does not specify a return value. Return value always will be None.

    Write Error error log in case:
        - A parameter do not start with proper symbol.
    '''
    for i, _ in enumerate(key_list):
        first_character = key_list[i][:1]
        if first_character != '~':
            msg_err_key = "ERROR: Introduced parameter name is wrong. The parameter '"\
            + key_list[i] \
            + "' has incorrect key name. All parameters keys should start with '~' symbol."
            log.write_error(msg_err_key)


def check_create_stack(key_list, value_list):
    '''
    Verification values that are necessary to create a stack.
    We check that all necessary values are on .par file.
    Also we check that the values are properly setted.
    This function does not specify a return value. Return value always will be None.

    Write Error error log in case:
        - Parameter has a wrong value. Feedback about parameter and current value.
        - A necessary parameter is missing.
    '''
    resamp_type_values = ['BILINEAR_INTERPOLATION', 'CUBIC_CONVOLUTION', 'NONE',\
                          'NEAREST_NEIGHBOUR']
    extent_values = ['Master', 'Maximum', 'Minimum']
    initial_ofset_method_values = ['Orbit', 'Product Geolocation']
    check_write(key_list, value_list)
    check_value_from_list('~RESAMPLING_TYPE', resamp_type_values, key_list, value_list)
    check_value_from_list('~EXTENT', extent_values, key_list, value_list)
    check_value_from_list('~INITIAL_OFFSET_METHOD', initial_ofset_method_values,\
                          key_list, value_list)



def check_steps(steps):
    '''
    Verification at step to do values.
    We check that values  on .par file are properly setted.
    This function does not specify a return value. Return value always will be None.

    Write Warning error log in case:
        - Steps to do has duplicates values.
        - Step to do has a incorrect value.
    '''
    correct_values = ['Read', 'Apply-Orbit-File', 'Assembly_Orbit', 'Subset', \
                      'ThermalNoiseRemoval', 'Calibration', 'Speckle-Filter', \
                      'LinearToFromdB', 'Terrain-Correction', 'CreateStack', 'Write']
    if len(steps) != len(set(steps)):
        log.write_error('WARNING: Steps to do has duplicates values.')
    for step in steps:
        flag = 0
        for value in correct_values:
            if value == step:
                flag += 1
        if flag == 0:
            msg_err_inc_val = "WARNING: Step to do has a incorrect value. Value: '" + step + "'."
            log.write_error(msg_err_inc_val)
