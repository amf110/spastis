#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@package main_functions.py
Created on Thu May 23 14:45:38 2019

Documentacion extras
"""

import re
import os
import time
import subprocess
from datetime import datetime
from pykml import parser
import log_function as log

# import checks_function as check

MSG_BAR = "\n############################################################\n"

XML_BEGINNING = '''<graph id="Graph">
  <version>1.0</version>
  '''

XML_END = '''</graph>'''

FILE_PROCCESS_NUM = 0

PIXEL_STANDARD = '0,0,0,0'

WGS84_TEXT = '''GEOGCS[&quot;WGS84(DD)&quot;,
  DATUM[&quot;WGS84&quot;,
    SPHEROID[&quot;WGS84&quot;, 6378137.0, 298.257223563]],
  PRIMEM[&quot;Greenwich&quot;, 0.0],
  UNIT[&quot;degree&quot;, 0.017453292519943295],
  AXIS[&quot;Geodetic longitude&quot;, EAST],
  AXIS[&quot;Geodetic latitude&quot;, NORTH]]'''

UTM_TEXT = '''PROJCS[&quot;UTM Zone 31 / World Geodetic System 1984&quot;,
  GEOGCS[&quot;World Geodetic System 1984&quot;,
    DATUM[&quot;World Geodetic System 1984&quot;,
      SPHEROID[&quot;WGS 84&quot;, 6378137.0, 298.257223563, AUTHORITY[&quot;EPSG&quot;,&quot;7030&quot;]],
      AUTHORITY[&quot;EPSG&quot;,&quot;6326&quot;]],
    PRIMEM[&quot;Greenwich&quot;, 0.0, AUTHORITY[&quot;EPSG&quot;,&quot;8901&quot;]],
    UNIT[&quot;degree&quot;, 0.017453292519943295],
    AXIS[&quot;Geodetic longitude&quot;, EAST],
    AXIS[&quot;Geodetic latitude&quot;, NORTH]],
  PROJECTION[&quot;Transverse_Mercator&quot;],
  PARAMETER[&quot;central_meridian&quot;, 3.0],
  PARAMETER[&quot;latitude_of_origin&quot;, 0.0],
  PARAMETER[&quot;scale_factor&quot;, 0.9996],
  PARAMETER[&quot;false_easting&quot;, 500000.0],
  PARAMETER[&quot;false_northing&quot;, 0.0],
  UNIT[&quot;m&quot;, 1.0],
  AXIS[&quot;Easting&quot;, EAST],
  AXIS[&quot;Northing&quot;, NORTH]]'''


def clean_par_file(input_list):
    '''This function clean parameters.par files.
    1. We delete Newline [\n] control caracte
    2. We delete content from [#] character. This content is comments.
    3. We delete empty items at list
	Return parameter.par file clean.
    '''
    intermediate_list1 = []
    for item in input_list:
        strip_new_line = item.rstrip('\n')
        intermediate_list1.append(strip_new_line)

    intermediate_list2 = []
    for item in intermediate_list1:
        intermediate_list2.append(item.partition('#')[0].strip())

    output_list = []
    output_list = list(filter(None, intermediate_list2))

    return output_list


def get_steps(config_file):
    '''
    Read steps with a '1' at config file and create a ordered Top-Down list with steps to do.
    Return list with steps.
    Write Warning error log in case:
        - A step is not correctly separatec by '='
    '''
    step_to_do = []
    recording = 0
    for line in config_file:
        if re.match("~STEPS~", line) is not None:
            recording = 1
            i = 0  # We use this to not include 'STEPS' line
        elif re.match("~END_STEPS~", line) is not None:
            recording = 0

        if (recording == 1) and (i > 0):
            try:
                if line.split('=')[1].strip() == '1':
                    step_to_do.append(line.split('=')[0].strip())
            except IndexError:
                msg_err_get_step = "WARNING: Processes to do should be separated " \
                                   "by a '='. This process '" + line + "' is not properly introduced."
                log.write_error(msg_err_get_step)
        elif recording == 1:
            i += 1  # We use this to not include 'STEPS' line
    return step_to_do


def set_all_parameters(xml_file, key_list, value_list):
    #   Set all parameters that found at parameters.par into xml file.
    #   Return xml file with parameter setted.
    xml_file_out = xml_file
#    print(key_list)
    for i, key in enumerate(key_list):
        xml_file_out = re.sub(key, value_list[i], xml_file_out)
    if '~COORDINATES_FORMAT' in key_list:
        index = key_list.index('~COORDINATES_FORMAT')
        value = value_list[index]
        if value == 'Pixel':
            polygon_pixel = set_coordinates_pixel(key_list, value_list)
            xml_file_out = re.sub('~PIXEL_COORD', polygon_pixel, xml_file_out)
            xml_file_out = xml_file_out.replace('<geoRegion>~POyLYGON</geoRegion>', '<geoRegion/>')
        if value == 'Geographics':
            polygon_geo = polygon_geographics(key_list, value_list)
            xml_file_out = re.sub('~POyLYGON', polygon_geo, xml_file_out)
            xml_file_out = re.sub('~PIXEL_COORD', PIXEL_STANDARD, xml_file_out)
        if value == 'FileXML':
            path_kml = value_list[key_list.index('~KML_FILE_ROUTE')]
            polygon_kml = get_polygon_from_kml(path_kml)
            xml_file_out = re.sub('~POyLYGON', polygon_kml, xml_file_out)
            xml_file_out = re.sub('~PIXEL_COORD', PIXEL_STANDARD, xml_file_out)
    if '~MAP_PROJECTION' in key_list:
        index = key_list.index('~MAP_PROJECTION')
        value = value_list[index]
        if value == 'WGS84':
            xml_file_out = re.sub('~MAP_PROJ_TEXT', WGS84_TEXT, xml_file_out)
        if value == 'UTM':
            xml_file_out = re.sub('~MAP_PROJ_TEXT', UTM_TEXT, xml_file_out)
    return xml_file_out


def polygon_geographics(key_list, value_list):
    '''
	Generate polygon with defined geographic coordinates at configuration file.
	Return string with subset polygon format.
	'''
    lon_min = value_list[key_list.index('~LONMIN')]
    lat_min = value_list[key_list.index('~LATMIN')]
    lon_max = value_list[key_list.index('~LONMAX')]
    lat_max = value_list[key_list.index('~LATMAX')]

    polygon = 'POLYGON ((' + lon_min + ' ' + lat_min + ',' + lon_max + ' ' \
              + lat_min + ',' + lon_max + ' ' + lat_max + ',' + lon_min + ' ' + lat_max \
              + ',' + lon_min + ' ' + lat_min + '))'
    return polygon


def set_coordinates_pixel(key_list, value_list):
    '''
	Generate polygon with defined pixel coordinates at configuration file.
	Return string with subset polygon format.
	'''''
    parameters_pixel = ['~PIXEL_X', '~PIXEL_Y', '~PIXEL_WIDTH', '~PIXEL_HEIGHT']
    pixel_coord = []
    for i in parameters_pixel:
        value = value_list[key_list.index(i)]
        pixel_coord.append(value)
    result_value = ','.join(pixel_coord)

    return result_value


def get_polygon_from_kml(path_kml_file):
    '''
	Generate polygon from kml file at configuration file.
	Return string with subset polygon format.
    Write Error error log in case:
        - The kml document does not exist at setted path.
	'''
    try:
        polygon = ''
        with open(path_kml_file, 'rt', encoding="utf-8") as file:
            doc = parser.parse(file).getroot()
        file.close()

        coordinates = doc.Document.Placemark.Polygon.outerBoundaryIs.LinearRing.coordinates.text
        coordinates = coordinates.replace(',0', '')
        coordinates = coordinates.replace(' ', ',')
        coordinates = re.sub(r'\s+', '', coordinates)
        coordinates = coordinates.split(',')
        coordinates = list(filter(None, coordinates))
        len_coordinates = len(coordinates)

        longitud = []
        for i in range(0, len_coordinates, 2):
            longitud.append(float(coordinates[i]))

        longitud_max = str(max(longitud))
        longitud_min = str(min(longitud))

        latitud = []

        for i in range(1, len_coordinates, 2):
            latitud.append(float(coordinates[i]))
        latitud_max = str(max(latitud))
        latitud_min = str(min(latitud))

        # Create polygon in SNAP format
        polygon = 'POLYGON ((' + longitud_min + ' ' + latitud_max + ', ' \
                  + longitud_max + ' ' + latitud_max + ', ' + longitud_max + ' ' \
                  + latitud_min + ', ' + longitud_min + ' ' + latitud_min + ', ' \
                  + longitud_min + ' ' + latitud_max + ', ' + longitud_min + ' ' + latitud_max + '))'
        return polygon

    except FileNotFoundError:
        msg_err_file = "ERROR: The .kml file doesn't exist\n"
        print(msg_err_file)
        log.write_error(msg_err_file)


def get_parameters(config_file):
    '''
	Read content at configuration file 'parameter.par' and extract parameters.
	Extract parameter onto a pair '~PARAMETER = VALUE' and return diferents list.
    Return a pair of list (key, value).
        - key: It is a list with parameter name.
        - value: It is a list with parameter value.
        Both list has items ordered, so key[i] has the value of value[i] and so on.
	Write Error error log in case:
        - A key-value is not correctly separatec by '='
	'''
    parameters = []
    keys = []
    values = []
    recording = 0
    for line in config_file:
        if re.match("~PARAMETERS~", line) is not None:
            recording = 1
            i = 0  # We use this to not include 'STEPS' line
        elif re.match("~END_PARAMETERS~", line) is not None:
            recording = 0

        if (recording == 1) and (i > 0):
            parameters.append(line)
            try:
                values.append(line.split('=')[1].strip())
                keys.append(line.split('=')[0].strip())
            except IndexError:
                log.write_error("ERROR: Parameters should be separated by a '='. " \
                                "This pair key = value: '" \
                                + line + "' is not properly introduced.")
        elif recording == 1:
            i += 1  # We use this to not include 'STEPS' line
        if len(keys) != len(values):
            msg_err_leng = "ERROR: Parameters key and value list has differents lengs."
            log.write_error(msg_err_leng)
    return keys, values


def get_files(path):
    '''
    Get files at specified path and all her branches.
    Return a list of founded files.
    '''
    # create a list of file and sub directories
    # names in the given directory
    list_files = os.listdir(path)
    all_files = list()
    # Iterate over all the entries
    for entry in list_files:
        # Create full path
        full_path = os.path.join(path, entry)
        # If entry is a directory then get the list of files in this directory
        if os.path.isdir(full_path):
            all_files = all_files + get_files(full_path)
        else:
            all_files.append(full_path)

    return all_files


def launch_proccess(args, num_proc):
    '''
	Launch with bulk processing SNAP tool (GPT) via Linux CLI the process.
    Generate output messages and write error if happen during execution.
    This function return feedback of execution.
    '''
    procc_name = str(num_proc)
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    time_started = time.time()
    write_out_def_1 = MSG_BAR + 'Proccess [' + procc_name + '] ' \
                                                            'launched:\nARG: ' + str(args)
    # We print to have feedback at Terminal
    print(write_out_def_1)
    stdout = process.communicate()[0]
    stdout = stdout.decode("utf-8")
    write_out_def_2 = '\n\nOutput:\n {}'.format(stdout)
    time_delta = "{:.1f}".format(time.time() - time_started)
    msg_out_end = '\n\n[' + procc_name + '] Finished process in ' \
                  + str(time_delta) + ' seconds.'
    print(msg_out_end)
    if process.returncode != 0:
        message = '\nError at process [' + procc_name + ']'
    else:
        message = '\nProcess [' + procc_name + '] successfully completed.'
    print(message)
    msg_return = write_out_def_1 + write_out_def_2 + msg_out_end + message

    return msg_return


def clean_files_start(all_files):
    '''
    Remove files that not finish with images specific formats '.dim' '.safe' and '.zip
    Return a pair (path_img, name_img).
        - path_img: It is a list with absolute path.
        - name_img: It is a list with Sentinel-1 naming convention without product extension.
        https://sentinel.esa.int/web/sentinel/user-guides/sentinel-1-sar/naming-conventions
        Both list has items ordered, so path_img[i] has her name at name_img[i] and so on.
    '''
    path_img = []
    name_img = []
    for file in all_files:
        if file.endswith('.safe'):
            path_img.append(file)
            name_img.append(os.path.basename(file[:-14])[:-5])
        elif file.endswith('.zip'):
            path_img.append(file)
            name_img.append(os.path.basename(file)[:-4])

    return path_img, name_img


def clean_files_processed(all_files):
    '''
    Remove files that not finish with images specific formats '.dim' '.safe' and '.zip
    Return a pair (path_img, name_img).
        - path_img: It is a list with absolute path.
        - name_img: It is a list with Sentinel-1 naming convention without product extension.
        https://sentinel.esa.int/web/sentinel/user-guides/sentinel-1-sar/naming-conventions
        Both list has items ordered, so path_img[i] has her name at name_img[i] and so on.
    '''
    path_img = []
    name_img = []
    for file in all_files:
        if file.endswith('.dim'):
            path_img.append(file)
            name_img.append(os.path.basename(file)[:-4])
        elif file.endswith('.tif'):
            path_img.append(file)
            name_img.append(os.path.basename(file)[:-4])

    return path_img, name_img


def check_images(path_img, name_img):
    '''
    Check if we have two images with same image name. Remove one of these duplicated.
    Check if a image is not from Sentinel-1 mission. Remove from list and print a Warning error log.
    This function maintain order, so path_img[i] has her name at name_img[i] and so on.
    Return a pair (path_img, name_img).
    '''
    name_img_out = name_img
    path_img_out = path_img
    # Check for duplicates images
    name_img_uniq = list(dict.fromkeys(name_img))
    if not len(name_img_uniq) == len(path_img):
        msg_err_len = "WARNING: We found two images with same name."
        log.write_error(msg_err_len)
        for i, image in enumerate(name_img):
            for i_2, image_2 in enumerate(name_img):
                if (i != i_2) and (image == image_2):
                    del name_img_out[i_2]
                    del path_img_out[i_2]
    # Delete files who doesn't start with 'S1'
    to_del_name = list()
    to_del_path = list()
    n_pos = 0
    for i in name_img_out:
        if name_img_out[n_pos][:2] != 'S1':
            msg_err_mission = "WARNING: File is not a Sentinel-1 image. File: '" + i \
                              + "'. This image are not going to be processed."
            log.write_error(msg_err_mission)
            print(msg_err_mission)
            to_del_name.append(name_img_out[n_pos])
            to_del_path.append(path_img_out[n_pos])
        n_pos += 1
    for i in to_del_name:
        name_img_out.remove(i)
    for i in to_del_path:
        path_img_out.remove(i)

    return path_img_out, name_img_out


def set_images_list(img_txt, path_img, name_img):
    '''
    Complementing 'set_images' function. In case of set images by list, return
    images that are at list.
    Set images to process in case:
        - Name conform with Sentinel-1 name convention without product extension.
        - Name conform with product unique ID.

    This function maintain order, so path_img[i] has her name at name_img[i] and so on.
    Return a pair (path_img, name_img)

    Write Warning error log in case:
        - Image list value doesn't match with any image at images folder.
        - Image list values doesn't conform with name format.
    '''
    input_list = list()
    recording = 0
    path_img_out = list()
    name_img_out = list()
    for line in img_txt:
        if re.match("~LIST~", line) is not None:
            recording = 1
            i = 0
        elif re.match("~END~", line) is not None:
            recording = 0
        if (recording == 1) and (i > 0):
            input_list.append(line.strip())
        elif recording == 1:
            i += 1
    img_code = list()
    path_code = list()
    date_code = list()
    # Checks input list are dates
    input_list_date = list()
    for i in input_list:
        if len(i) == 8:
            try:
                datetime.strptime(i, '%Y%m%d')
                input_list_date.append(i)
            except ValueError:
                msg_err_list_format = "WARNING: At images date list, line content '" + i + "' is not with correct date format 'YYYYMMDD'. This date will not be processed."
                log.write_error(msg_err_list_format)
        else:
            msg_err_list_leng = "WARNING: At images date list, line content '" + i + "' is not with correct date format 'YYYYMMDD'. This date will not be processed."
            log.write_error(msg_err_list_leng)

#    for num, img in enumerate(name_img):
    num = 0
    for img in name_img:
        try:
            datetime.strptime(img, '%Y%m%d')
            date_code.append(img)
            img_code.append(name_img[num])
            path_code.append(path_img[num])
        except ValueError:
            pass
        try:
            datetime.strptime(img[17:25], '%Y%m%d')
            date_code.append(img[17:25])
            img_code.append(name_img[num])
            path_code.append(path_img[num])
        except ValueError:
            pass
        num += 1
    # We search array with dates list and if match
    for i in input_list_date:
        flagg = 0
        pos_img = 0
        for w in date_code:
            if i == w:
                flagg = 1
                path_img_out.append(path_img[pos_img])
                name_img_out.append(name_img[pos_img])
            pos_img += 1   
        if flagg == 0:
            msg_err = "WARNING: Images list value '" + i + "' couldn't " \
            "find at images directory. This image will be not processed."
            log.write_error(msg_err)

    return path_img_out, name_img_out


def set_images_date(start_date, end_date, path_img, name_img):
    '''
    Complementing 'set_images' function. In case of set images by date, return
    images within configured dates.
    Set images to process in case that date is equal or between specified dates.

    This function maintain order, so path_img[i] has her name at name_img[i] and so on.
    Return a pair (path_img, name_img)

    Write Error error log in case:
        - Date format doesn't conform format YYYYMMDD
        - Date has not introduced at configuration file.
    '''
    path_img_out = list()
    name_img_out = list()
    try:
        start_date_ = datetime.strptime(start_date, '%Y%m%d')
        end_date_ = datetime.strptime(end_date, '%Y%m%d')
    except ValueError:
        msg_err_date = "ERROR: Date format at images file is wrong"
        log.write_error(msg_err_date)
    except AttributeError:
        msg_err_date = "ERROR: Dates are not introduced at images file."
        log.write_error(msg_err_date)
    for i, img in enumerate(name_img):
        try:
            img_date = datetime.strptime(img[17:25], '%Y%m%d')
        except ValueError:
            pass
        try:
            img_date = datetime.strptime(img, '%Y%m%d')
        except ValueError:
            pass
        if start_date_ <= img_date <= end_date_:
            path_img_out.append(path_img[i])
            name_img_out.append(name_img[i])

    return path_img_out, name_img_out


def set_images(path_img_txt, path_img, name_img):
    '''
    Read images document and set images within configured parameters.
    This function is complemented by 'set_images_date' and 'set_images_list'.

    This function maintain order, so path_img[i] has her name at name_img[i] and so on.
    Return a pair (path_img, name_img)

    Write Error error log in case:
        - Type parameter is wrong. Should be 'LIST' or 'DATE'.
    '''
    with open(path_img_txt, 'r') as file:
        img_txt = clean_par_file(file.readlines())
    file.close()
    path_img_out = list()
    name_img_out = list()
    for line in img_txt:
        if 'TYPE' in line:
            type_restriction = line.split('=')[1].strip()
        if 'START_DATE' in line:
            start_date = line.split('=')[1].strip()
        if 'END_DATE' in line:
            end_date = line.split('=')[1].strip()
    if type_restriction == 'DATE':
        path_img_out, name_img_out = set_images_date(start_date, end_date, path_img, name_img)
    elif type_restriction == 'LIST':
        path_img_out, name_img_out = set_images_list(img_txt, path_img, name_img)
    else:
        msg_err_type = "ERROR: At images text file parameter TYPE it is wrong. " \
                       "Should be 'LIST' or 'DATE'. All images at setted folder will be processed"
        log.write_error(msg_err_type)
        path_img_out = path_img
        name_img_out = name_img
    return path_img_out, name_img_out


def get_parents_files(path_img, name_img):
    '''
    Clasifica las imagenes en función de si tienen fechas coincidentes o no
    Return: img_par_out, path_par_out, par_out_join, img_uni_out, path_uni_out
    Donde:
           - img_par_out = Name images with same date
           - path_par_out = Path images with same date
           - par_out_join = Route to two images same date, Assembly format

           - img_uni_out = Name iamges with unique date
           - path_uni_out = Path images with unique date
   '''
    dates = []
    img_par_out = []  # Name images with same data
    path_par_out = []  # Path images with same data
    par_out_join = []  # Route to two images same data, Assembly format

    img_uni_out = name_img.copy()  # Name iamges with unique data
    path_uni_out = path_img.copy()  # Path images with unique data

    for image in name_img:
        # Mofification, now we check if image has between 17:25 a date, if not, we maintain full name
        string_date = image[17:25]
        if string_date == '':
            try:
                datetime.strptime(image, '%Y%m%d')
                dates.append(image)
            except ValueError:
                dates.append(image)
                msg_err_par_files = "This image: '" + image + "' doesn't conform date format. Will be saved with full name"
                log.write_error(msg_err_par_files)
        else:
            try:
                datetime.strptime(image[17:25], '%Y%m%d')
                dates.append(image[17:25])
            except ValueError:
                dates.append(image)
                msg_err_par_files = "This image: '" + image + "' doesn't conform date format. Will be saved with full name"
                log.write_error(msg_err_par_files)

    #        dates.append(image[17:25])

    for xpos, _ in enumerate(dates):
        for wpos, _ in enumerate(dates):
            if xpos != wpos:
                if wpos > xpos:
                    if dates[xpos] == dates[wpos]:
                        par_out_join.append(path_img[xpos] + ',' + path_img[wpos])
                        path_par_out.append(path_img[xpos])
                        path_par_out.append(path_img[wpos])
                        img_par_out.append(name_img[xpos])
                        img_par_out.append(name_img[wpos])
                        path_uni_out.remove(path_img[xpos])
                        img_uni_out.remove(name_img[xpos])
                        path_uni_out.remove(path_img[wpos])
                        img_uni_out.remove(name_img[wpos])

    return img_par_out, path_par_out, par_out_join, img_uni_out, path_uni_out


def graph_skeleton(steps_todo, path_graph):
    '''
    Create a basic graph with specified steps.
    Return xml basic skeleton.
    '''
    xml_data = previous_step = ""  # Initialize variable
    for i in steps_todo:
        with open(path_graph + '/' + i + '.xml', 'r') as file:
            xml_data += file.read()
            xml_data = re.sub('~PREVIOUS', previous_step, xml_data)
        previous_step = i
    xml_data = XML_BEGINNING + xml_data + XML_END
    return xml_data
