#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@package main.py
spastisX(Sofware de Procesado Automático de Series Temporales de Imágenes Sentinel-1)
Created by Alejandro Martínez Flor
Final master degree project:  Automatic chain processing of Sentinel-1 time series images
Contact: amf110@alu.ua.es
Date: July 2018
Code comments could be not properly setted.
"""

import os
import sys
import time
import re
import shutil
import multiprocessing
from datetime import datetime
import main_functions as func
import checks_function as check
import log_function as log

START_TIME = time.time()
MSG_BAR = "\n############################################################\n"
#Set flags
flag_not_img_txt = 0
flag_delete_stack = 0
flag_delete_tmp = 0
flag_assembly = 0
flag_stack = 0
flag_only_stack = 0
flag_separate_bands = 0
#We initialize number of porcess variable
procc_num = 0
#Define .par file path via same directory that program is or first argument at CLI.
try:
    sys_arg1 = sys.argv[1]
    if len(sys.argv) > 2:
        print("Only one argument that should be the .par file")
        sys.exit(1)
    PATH_CONFIG_FILE = sys_arg1
except IndexError:
    PATH_CONFIG_FILE = str(os.path.dirname(os.path.realpath(__file__))) + '/parameters.par'
#Define directories
PATH_BIN_FLR = os.path.dirname(os.path.realpath(__file__))
PATH_MAIN_FLR = (PATH_BIN_FLR)[:-4]
#Create logs
PATH_LOG_FLR = PATH_MAIN_FLR + '/logs'
log.create(PATH_LOG_FLR)
#Start message
msg_init = "Execution launched: " + str(time.strftime('%c')) + "."
log.write_output(msg_init)
#Read parameter.par file
try:
    with open(PATH_CONFIG_FILE, 'r') as file:
        file_parameters = func.clean_par_file(file.readlines())
    file.close()
except FileNotFoundError:
    msg_err_fnf = "ERROR: File .par could not be founded at path: " + PATH_CONFIG_FILE
    log.write_error(msg_err_fnf)
#Set configuration parameters at parameter.par
for x in file_parameters:
    if "dir_slc" in x:
        path_img_flr = x.split('=')[1].strip()
        if path_img_flr != '':
            PATH_IMG_FLR = path_img_flr
        else:
            PATH_IMG_FLR = PATH_MAIN_FLR + '/images'
        msg_path_img = "Images directory is setted to: " + PATH_IMG_FLR
        if not os.path.exists(PATH_IMG_FLR):
            os.makedirs(PATH_IMG_FLR)
        if not os.listdir(PATH_IMG_FLR):
            msg_err_img = "WARNING: Images folder is empty"
            log.write_error(msg_err_img)
    if "dir_out" in x:
        path_res_flr = x.split('=')[1].strip()
        if path_res_flr != '':
            PATH_RES_FLR = path_res_flr
        else:
            PATH_RES_FLR = PATH_MAIN_FLR + '/results/' + str(time.strftime('%Y%m%d_%H%M%S'))
        if not os.path.exists(PATH_RES_FLR):
            os.makedirs(PATH_RES_FLR)
        PATH_XML_FLR = PATH_RES_FLR + '/xml'
        if not os.path.exists(PATH_RES_FLR + '/xml'):
            os.makedirs(PATH_RES_FLR + '/xml')
        msg_path_res = "Result directory is setted to: " + PATH_RES_FLR + \
        "\nXML files will be stored at: " + PATH_RES_FLR + "/xml"
    if "file_images" in x:
        path_img_file = x.split('=')[1].strip()
        if path_img_file != '':
            PATH_IMG_FILE = path_img_file
            if not os.path.isfile(PATH_IMG_FILE):
                msg_err_imgfile = "WARNING: Images text file does not exist at path: " \
                + PATH_IMG_FILE + ". All images at images folder will be processes."
                log.write_error(msg_err_imgfile)
                flag_not_img_txt = 1
        else:
            flag_not_img_txt = 1
            msg_err_imgfile = "INFO: All images at images folder will be processes."
            log.write_output(msg_err_imgfile)
    if "dir_tmp" in x:
        path_tmp_flr = x.split('=')[1].strip()
        if path_tmp_flr != '':
            PATH_TMP_FLR = path_tmp_flr
            msg_path_tmp = "Images directory is setted to different folder than " \
            "output. Path: " + path_tmp_flr
        else:
            PATH_TMP_FLR = PATH_RES_FLR
            msg_path_tmp = "Images directory is setted together with output file"
        if not os.path.exists(PATH_TMP_FLR):
            os.makedirs(PATH_TMP_FLR)
    if "GPTBIN_PATH" in x:
        GPT = x.split('=')[1].strip()
        if os.path.isfile(GPT):
            msg_GPT = "GPT directory is setted to: " + GPT
        else:
            msg_err_gpt = "ERROR: The route to GPT is incorrect. Path: " + GPT
            msg_GPT = ''
            log.write_error(msg_err_gpt)
    if "CPU" in x:
        CPU = x.split('=')[1].strip()
        try:
            int(CPU)
        except ValueError:
            msg_err_cpu = "ERROR: CPU value should be a integrer. Current value: " + CPU
            log.write_error(msg_err_cpu)
    if "CACHE" in x:
        CACHE = x.split('=')[1].strip()
        if not CACHE[-1:] == 'G':
            msg_err_ram = "ERROR: Cache value should be a integrer followed by a G"\
            " Ex: '6G' '64G'. Current value: " + CACHE
            log.write_error(msg_err_ram)
        else:
            try:
                int(CACHE[:-1])
            except ValueError:
                msg_err_ram = "ERROR: Cache value should be a integrer followed by a G"\
                " Example: '6G' '64G'. Current value: " + CACHE
                log.write_error(msg_err_ram)
    if "DELETE_TMP_FILES" in x:
        delete_tmp = x.split('=')[1].strip()
        if delete_tmp == '1':
            flag_delete_tmp = 1
            msg_del_tmp = "Files used at intermediate processes will be DELETED."
        else:
            msg_del_tmp = "Files used at intermediate processes will NOT be DELETED."
    if "DELETE_STACK_FILES" in x:
        delete_stack = x.split('=')[1].strip()
        if delete_stack == '1':
            flag_delete_stack = 1
            msg_del_stack = "Files used to generate stack will be DELETED."
        else:
            msg_del_stack = "Files used to generate stack will NOT be DELETED."
    if "PARALLEL_PROCESSES" in x:
        NUM_PROC = x.split('=')[1].strip()
        try:
            NUM_PROC = int(NUM_PROC)
        except ValueError:
            NUM_PROC = 1
            msg_err_cpu = "WARNING: Number of processes value should be a integrer." \
            " Current value: " + NUM_PROC + "Not using multiprocessing."
            log.write_error(msg_err_cpu)
#Write log output with setted configuration.
log.write_output(MSG_BAR + "\nParameter file '.par':\n")
for i in file_parameters:
    log.write_output(i)
log.write_output(MSG_BAR)
log.write_output(msg_path_img)
log.write_output(msg_path_res)
log.write_output(msg_path_tmp)
log.write_output(msg_GPT)
log.write_output(msg_del_tmp)
log.write_output(msg_del_stack)
log.write_output(MSG_BAR)
path_graphs = PATH_MAIN_FLR + '/graphs'
#Read steps to do and check
steps_todo = func.get_steps(file_parameters)
check.check_steps(steps_todo)
if not steps_todo:
    log.write_error("ERROR: Steps to do is empty.")
    log.close()
    sys.exit(1)
else:
    log.write_output("Steps to do:\n" + str(steps_todo))
log.write_output(MSG_BAR)
steps_todo_original = steps_todo.copy()
#Source Bands
BANDS_ALL = '~SOURCE_BANDS = Amplitude_VH,Intensity_VH,Amplitude_VV,Intensity_VV'
BANDS_INTENSITY = '~SOURCE_BANDS = Intensity_VH,Intensity_VV'
#Set flags value
for i in steps_todo:
    if "Assembly_Orbit" in i:
        flag_assembly = 1
    if "CreateStack" in i:
        flag_stack = 1
        steps_todo.remove('CreateStack')
    #If we want to execute Subset, depending position of ThermalNoiseRemoval
    #We need to put different value of Source Bands
    if "Subset" in i:
        try:
            pos_subset = steps_todo.index('Subset')
            pos_therma = steps_todo.index('ThermalNoiseRemoval')
            #We insert at penultimate position, last position is ~END_PARAMETERS~
            insert_bands = len(file_parameters)-1
            if pos_subset > pos_therma:
                file_parameters.insert(insert_bands, BANDS_INTENSITY)
            else:
                file_parameters.insert(insert_bands, BANDS_ALL)
        except ValueError:
            insert_bands = len(file_parameters)-1
            file_parameters.insert(insert_bands, BANDS_ALL)
#Read parameters key = value and do checks
key_list, value_list = func.get_parameters(file_parameters)
check.check_parameter_key(key_list)
check.check_parameter_value(steps_todo, key_list, value_list)

pos_save_bands = key_list.index('~SAVE_BANDS_SEPARATE')
if value_list[pos_save_bands] == 'yes':
    flag_separate_bands = 1

ONLY_STACK = ['Read', 'CreateStack', 'Write']
if steps_todo_original == ONLY_STACK:
    flag_only_stack = 1
if flag_only_stack == 1:
    msg_only_stack = "INFO: Execution do only Stack step at files with '.tif' or" \
    " '.dim' extension on folder and subfolders with parent path settle at images directory"
    log.write_output(msg_only_stack)
#Launch only stack process.
    #Get files at resources path
    if flag_separate_bands == 1:
        list_files = os.listdir(PATH_IMG_FLR)
        print(list_files)
        path_list_files = list()
        path_img, name_img = func.clean_files_processed(list_files)
        for i in name_img:
            path_list_files.append(PATH_IMG_FLR + '/' + i)
        print(path_list_files)
        with open(path_graphs + '/Band_Math.xml', 'r') as file:
            xml_skelet = file.read()
        xml_skelet = func.set_all_parameters(xml_skelet, key_list, value_list)
        xml_skel_vh = re.sub('~INPUT_BAND', 'Sigma0_VH_db', xml_skelet)
        xml_skel_vh = re.sub('~OUTPUT_NAME', 'VH', xml_skel_vh)
        xml_skel_vv = re.sub('~INPUT_BAND', 'Sigma0_VV_db', xml_skelet)
        xml_skel_vv = re.sub('~OUTPUT_NAME', 'VV', xml_skel_vv)
#        list_files = os.listdir(PATH_IMG_FLR)
        path_xml_vv = PATH_XML_FLR + '/stack_VV/'
        path_xml_vh = PATH_XML_FLR + '/stack_VH/'
        if not os.path.exists(path_xml_vv):
            os.makedirs(path_xml_vv)
        if not os.path.exists(path_xml_vh):
            os.makedirs(path_xml_vh)
        exist_file = os.path.isfile(PATH_IMG_FLR + '/' + name_img[0] + '.dim')
        if exist_file:
            format_file = '.dim'
        exist_file = os.path.isfile(PATH_IMG_FLR + '/' + name_img[0] + '.tif')
        if exist_file:
            format_file = '.tif'
        path_to_xmls = list()
        for i in name_img:
            xml_vv = xml_skel_vv
            xml_vh = xml_skel_vh
            path_input_file = PATH_IMG_FLR + '/' + i + format_file
            out_path_vv = PATH_RES_FLR + '/result_stack/VV/' + i
            out_path_vh = PATH_RES_FLR + '/result_stack/VH/' + i
            xml_vv = re.sub('~INPUTFILE', path_input_file, xml_vv)
            xml_vv = re.sub('~OUTPUTFILE', out_path_vv, xml_vv)
            xml_vh = re.sub('~INPUTFILE', path_input_file, xml_vh)
            xml_vh = re.sub('~OUTPUTFILE', out_path_vh, xml_vh)
            route_xml_file_vv = path_xml_vv + i + '.xml'
            route_xml_file_vh = path_xml_vh + i + '.xml'
            xml_file = open(route_xml_file_vv, 'w')
            xml_file.write(xml_vv)
            xml_file.close()
            xml_file2 = open(route_xml_file_vh, 'w')
            xml_file2.write(xml_vh)
            xml_file2.close()
            path_to_xmls.append(route_xml_file_vv)
            path_to_xmls.append(route_xml_file_vh)
        #Launch processes
        #Create list with args
        args_list = list()
        for i in path_to_xmls:
            args = [GPT, i, '-c', CACHE, '-q', CPU]
            args_list.append(args)
        #Multiprocessing
        multi_list = list()
        pool = multiprocessing.Pool(processes=NUM_PROC)
        for i in args_list:
            procc_num += 1
            y = pool.apply_async(func.launch_proccess, args=(i, procc_num))
            multi_list.append(y)
        pool.close()
        pool.join()
        for i in multi_list:
            msg_out = i.get()
            pos_err = msg_out.find('Error at process [')
            if pos_err != -1:
                log.write_error(msg_out[pos_err:pos_err+20])
            log.write_output(msg_out)
     ####################   #################### ####################
        list_files = os.listdir(PATH_RES_FLR + '/result_stack/VV/')
        path_list_files = list()
        for i in list_files:
            path_list_files.append(PATH_RES_FLR + '/result_stack/VV/' + i)
        #Clean to admited formats
        path_img_stack, name_img_stack = func.clean_files_processed(path_list_files)
        list_images_stack = list()
        list_path_stack = list()
        for num, name in enumerate(name_img_stack):
            try:
                datetime.strptime(name, '%Y%m%d')
                list_images_stack.append(name_img_stack[num])
                list_path_stack.append(path_img_stack[num])
            except ValueError:
                pass
        if flag_not_img_txt == 0:
            log.write_output("INFO: Images to process are setted up via images text file\n")
            list_path_stack, list_images_stack = func.set_images(PATH_IMG_FILE, list_path_stack, list_images_stack)
        #Check if is empty
        if not list_images_stack:
            msg_err_empty_stack = "ERROR: Resources to do stack are empty. This process will not be executed"
            log.write_error(msg_err_empty_stack)
        elif len(list_images_stack) == 1:
            msg_err_empty_stack = "ERROR: Only one resource to do stack. This process will not be executed"
            log.write_error(msg_err_empty_stack)
        else:
            msg_str_stack = MSG_BAR + "##### STACK IMAGES VV #####\nImages to process: " \
            + str(len(list_images_stack)) + " images.\nImages result: " + str(len(list_images_stack)) \
            + " images.\nImages input list to do stack:"
            log.write_output(msg_str_stack)
            for i in list_images_stack:
                log.write_output(" · " + i)
        #   Generate input format
            input_string = ",".join(list_path_stack)
        #   Set xml
            path_xml = PATH_XML_FLR
            xml_stack = func.graph_skeleton(['CreateStack'], path_graphs)
            try:
                xml_stack_parameters = func.set_all_parameters(xml_stack, key_list, value_list)
            except:
                log.close()
                sys.exit(1)
            xml = re.sub('~INPUTFILE', input_string, xml_stack_parameters)
            path_out_stack = PATH_RES_FLR + '/result_stack/stack_vv'
            xml = re.sub('~OUTPUTFILE', path_out_stack, xml)
        #   Replace stack number files
            xml = re.sub('~NUM_STACK', str(len(list_images_stack)), xml)
            route_xml_file = path_xml + '/stack_vv.xml'
    #        route_xml_file = path_xml + '\\stack.xml'
            xml_file = open(route_xml_file, 'a')
            xml_file.write(xml)
            xml_file.close()
        #   Launch process
            args = [GPT, route_xml_file, '-c', CACHE, '-q', CPU]
            procc_num += 1
            feedback = func.launch_proccess(args, procc_num)
            log.write_output(feedback)

            if flag_delete_stack == 1:
                for i in list_path_stack:
                    os.remove(i)
####################   #################### ####################
        list_files = os.listdir(PATH_RES_FLR + '/result_stack/VH/')
        path_list_files = list()
        date_list = list()
        for i in list_files:
            path_list_files.append(PATH_RES_FLR + '/result_stack/VH/' + i)
        #Clean to admited formats
        path_img_stack, name_img_stack = func.clean_files_processed(path_list_files)
        date_as_num = list()
        for i in name_img_stack:
            date_as_num.append(int(i))
        list_images_stack = list()
        list_path_stack = list()
        for num, name in enumerate(name_img_stack):
            try:
                datetime.strptime(name, '%Y%m%d')
                list_images_stack.append(name_img_stack[num])
                list_path_stack.append(path_img_stack[num])
            except ValueError:
                pass
        if flag_not_img_txt == 0:
            log.write_output("INFO: Images to process are setted up via images text file\n")
            list_path_stack, list_images_stack = func.set_images(PATH_IMG_FILE, list_path_stack, list_images_stack)
        #Check if is empty
        if not list_images_stack:
            msg_err_empty_stack = "ERROR: Resources to do stack are empty. This process will not be executed"
            log.write_error(msg_err_empty_stack)
        elif len(list_images_stack) == 1:
            msg_err_empty_stack = "ERROR: Only one resource to do stack. This process will not be executed"
            log.write_error(msg_err_empty_stack)
        else:
            msg_str_stack = MSG_BAR + "##### STACK IMAGES VH #####\nImages to process: " \
            + str(len(list_images_stack)) + " images.\nImages result: " + str(len(list_images_stack)) \
            + " images.\nImages input list to do stack:"
            log.write_output(msg_str_stack)
            for i in list_images_stack:
                log.write_output(" · " + i)
        #   Generate input format
            input_string = ",".join(list_path_stack)
        #   Set xml
            path_xml = PATH_XML_FLR
            xml_stack = func.graph_skeleton(['CreateStack'], path_graphs)
            try:
                xml_stack_parameters = func.set_all_parameters(xml_stack, key_list, value_list)
            except:
                log.close()
                sys.exit(1)
            xml = re.sub('~INPUTFILE', input_string, xml_stack_parameters)
            path_out_stack = PATH_RES_FLR + '/result_stack/stack_vh'
    #        path_out_stack = PATH_RES_FLR + '\\result_stack\\stack'
            xml = re.sub('~OUTPUTFILE', path_out_stack, xml)
        #   Replace stack number files
            xml = re.sub('~NUM_STACK', str(len(list_images_stack)), xml)
            route_xml_file = path_xml + '/stack_vh.xml'
    #        route_xml_file = path_xml + '\\stack.xml'
            xml_file = open(route_xml_file, 'a')
            xml_file.write(xml)
            xml_file.close()
        #   Launch process
            args = [GPT, route_xml_file, '-c', CACHE, '-q', CPU]
            procc_num += 1
            feedback = func.launch_proccess(args, procc_num)
            log.write_output(feedback)
            if flag_delete_stack == 1:
                for i in list_path_stack:
                    os.remove(i)
    else:
        list_files = os.listdir(PATH_IMG_FLR)
        path_list_files = list()
        for i in list_files:
            path_list_files.append(PATH_IMG_FLR + '/' + i)
        #Clean to admited formats
        path_img_stack, name_img_stack = func.clean_files_processed(path_list_files)
        list_images_stack = list()
        list_path_stack = list()
        for num, name in enumerate(name_img_stack):
            try:
                datetime.strptime(name, '%Y%m%d')
                list_images_stack.append(name_img_stack[num])
                list_path_stack.append(path_img_stack[num])
            except ValueError:
                pass
        if flag_not_img_txt == 0:
            log.write_output("INFO: Images to process are setted up via images text file\n")
            list_path_stack, list_images_stack = func.set_images(PATH_IMG_FILE, list_path_stack, list_images_stack)
        #Check if is empty
        if not list_images_stack:
            msg_err_empty_stack = "ERROR: Resources to do stack are empty. This process will not be executed"
            log.write_error(msg_err_empty_stack)
        elif len(list_images_stack) == 1:
            msg_err_empty_stack = "ERROR: Only one resource to do stack. This process will not be executed"
            log.write_error(msg_err_empty_stack)
        else:
            msg_str_stack = MSG_BAR + "##### STACK IMAGES #####\nImages to process: " \
            + str(len(list_images_stack)) + " images.\nImages result: " + str(len(list_images_stack)) \
            + " images.\nImages input list to do stack:"
            log.write_output(msg_str_stack)
    #        print(list_images_stack)
            for i in list_images_stack:
                log.write_output(" · " + i)
        #   Generate input format
            input_string = ",".join(list_path_stack)
        #   Set xml
            path_xml = PATH_XML_FLR
            xml_stack = func.graph_skeleton(['CreateStack'], path_graphs)
            try:
                xml_stack_parameters = func.set_all_parameters(xml_stack, key_list, value_list)
            except:
                log.close()
                sys.exit(1)
            xml = re.sub('~INPUTFILE', input_string, xml_stack_parameters)
            path_out_stack = PATH_RES_FLR + '/result_stack/stack'
    #        path_out_stack = PATH_RES_FLR + '\\result_stack\\stack'
            xml = re.sub('~OUTPUTFILE', path_out_stack, xml)
        #   Replace stack number files
            xml = re.sub('~NUM_STACK', str(len(list_images_stack)), xml)
            route_xml_file = path_xml + '/stack.xml'
    #        route_xml_file = path_xml + '\\stack.xml'
            xml_file = open(route_xml_file, 'a')
            xml_file.write(xml)
            xml_file.close()
        #   Launch process
            args = [GPT, route_xml_file, '-c', CACHE, '-q', CPU]
            procc_num += 1
            feedback = func.launch_proccess(args, procc_num)
            log.write_output(feedback)
            if flag_delete_stack == 1:
                for i in list_path_stack:
                    os.remove(i)
else:
    #Get images from folder and do checks.
    files_img_flr = func.get_files(PATH_IMG_FLR)
    path_img, name_img = func.clean_files_start(files_img_flr)
    path_img, name_img = func.check_images(path_img, name_img)
    if flag_not_img_txt == 0:
        path_img, name_img = func.set_images(PATH_IMG_FILE, path_img, name_img)
        log.write_output("INFO: Images to process are setted up via images text file\n")
###############################################################################
#This flag indicates if we need to do Assembly_Orbit step.
#If not we go directly to, aprox line 500  ---  'if flag_assembly == 0:'
    if flag_assembly == 1:
#    From images to process, we separate into images with a date pair and without.
#    Phase Zero, process images without pair date.
#    Phases 1 to 3 process pair images:
#        - 1: Steps before Assembly_Orbit
#        - 2: Assembly_Orbit
#        - 3: Steps after Assembly_Orbit
    #Get separated images
        img_par_out, path_par_out, par_out_join, img_uni_out, path_uni_out = func.get_parents_files(path_img, name_img)
    ############ 0 phase ############
    #We execute all processes to images without parent
        #Print images to process at phase 0
        msg_out_nopair = MSG_BAR + "##### START PROCESSING IMAGES WITHOUT DATE COUPLE" \
        " #####\nImages to process: " + str(len(img_uni_out)) + " images.\nImages result: " \
        + str(len(img_uni_out)) + " images.\nImages input list:"
        log.write_output(msg_out_nopair)
        for i, img in enumerate(img_uni_out):
            log.write_output(" · " + img)
        path_xmls_0 = list()
        #Zero phase. Set steps to do. All steps to do extracting Assembly_Orbit
        steps_todo_0 = steps_todo.copy()
        steps_todo_0.remove('Assembly_Orbit')
        #Set xml model
        xml_basic_0 = func.graph_skeleton(steps_todo_0, path_graphs)
        try:
            xml_parameters_0 = func.set_all_parameters(xml_basic_0, key_list, value_list)
        except:
            log.close()
            sys.exit(1)
        #Set phase zero folders
        if flag_delete_stack == 1:
            path_out_0 = PATH_RES_FLR + '/to_delete'
        else:
            path_out_0 = PATH_RES_FLR + '/result'
#        path_out_0 = PATH_RES_FLR + '/result'
        path_xml_0 = PATH_XML_FLR + '/step0'
        if not os.path.exists(path_xml_0):
            os.makedirs(path_xml_0)
        #Generate zero phase xmls.
        for i, img in enumerate(img_uni_out):
            xml_i = re.sub('~INPUTFILE', path_uni_out[i], xml_parameters_0)
            path_out_0_i = path_out_0 + '/' + img[17:25]
            xml_i = re.sub('~OUTPUTFILE', path_out_0_i, xml_i)
            route_xml_file_0 = path_xml_0 + '/' + img[17:25] + '.xml'
            xml_file_0 = open(route_xml_file_0, 'a')
            xml_file_0.write(xml_i)
            xml_file_0.close()
            path_xmls_0.append(route_xml_file_0)
        #Launch processes
        #Create list with args
        args_list = list()
        for i in path_xmls_0:
            args = [GPT, i, '-c', CACHE, '-q', CPU]
            args_list.append(args)
        #Multiprocessing
        multi_list = list()
        pool = multiprocessing.Pool(processes=NUM_PROC)
        for i in args_list:
            procc_num += 1
            y = pool.apply_async(func.launch_proccess, args=(i, procc_num))
            multi_list.append(y)
        pool.close()
        pool.join()
        for i in multi_list:
            msg_out = i.get()
            pos_err = msg_out.find('Error at process [')
            if pos_err != -1:
                log.write_error(msg_out[pos_err:pos_err+20])
            log.write_output(msg_out)
    #Print images to process at phase 1 to 3
        msg_out_pair = MSG_BAR + "##### START PROCESSING IMAGES WITH DATE COUPLE #####" \
        "\nImages to process: " + str(len(img_par_out)) + " images.\nImages result: " \
        + str(int(len(img_par_out)/2)) + " images.\nImages input list:"
        log.write_output(msg_out_pair)
        for i, img in enumerate(img_par_out):
            log.write_output(" · " + img)
    ############ 1º phase ############
    #We execute steps before Assembly
        msg_out_1 = MSG_BAR + "##### Start first phase #####"
        log.write_output(msg_out_1)
        path_xmls_1 = list()
        #1º phase. Set steps to do. From first step to 'Assembly_Orbit' + Write
        steps_todo_1 = steps_todo[:steps_todo.index('Assembly_Orbit')]
        steps_todo_1.append('Write')
        #Set xml model
        xml_basic_1 = func.graph_skeleton(steps_todo_1, path_graphs)
        xml_basic_1 = re.sub('~WRITE_FORMAT', 'BEAM-DIMAP', xml_basic_1)
        xml_parameters_1 = func.set_all_parameters(xml_basic_1, key_list, value_list)
        #Set 1º phase folders
        path_out_1 = PATH_TMP_FLR + '/tmp/step1'
        path_xml_1 = PATH_XML_FLR + '/step1'
        if not os.path.exists(path_xml_1):
            os.makedirs(path_xml_1)
        if not os.path.exists(path_out_1):
            os.makedirs(path_out_1)
        #Generate 1º phase xmls. We use pair images setted previously.
        for i, img in enumerate(img_par_out):
            xml_i = re.sub('~INPUTFILE', path_par_out[i], xml_parameters_1)
            path_out_1_i = path_out_1 + '/' + img
            xml_i = re.sub('~OUTPUTFILE', path_out_1_i, xml_i)
            route_xml_file_1 = path_xml_1 + '/' + img + '.xml'
            xml_file_1 = open(route_xml_file_1, 'a')
            xml_file_1.write(xml_i)
            xml_file_1.close()
            path_xmls_1.append(route_xml_file_1)
        #Launch 1º phase processes
        #Create list with args
        args_list = list()
        for i in path_xmls_1:
            args = [GPT, i, '-c', CACHE, '-q', CPU]
            args_list.append(args)
        #Multiprocessing
        multi_list = list()
        pool = multiprocessing.Pool(processes=NUM_PROC)
        for i in args_list:
            procc_num += 1
            y = pool.apply_async(func.launch_proccess, args=(i, procc_num))
            multi_list.append(y)
        pool.close()
        pool.join()
        for i in multi_list:
            msg_out = i.get()
            pos_err = msg_out.find('Error at process [')
            if pos_err != -1:
                log.write_error(msg_out[pos_err:pos_err+20])
            log.write_output(msg_out)
    ############ 2º phase ############
    #We execute two images Assembly
        msg_out_2 = MSG_BAR + "##### Start second phase #####"
        log.write_output(msg_out_2)
        path_xmls_2 = list()
        #2º phase. Set steps to do. Assembly_Orbit graph include Read and Write functions.
        steps_todo_2 = ['Assembly_Orbit']
        #Set xml model
        xml_basic_2 = func.graph_skeleton(steps_todo_2, path_graphs)
        xml_basic_2 = re.sub('~WRITE_FORMAT', 'BEAM-DIMAP', xml_basic_2)
        xml_parameters_2 = func.set_all_parameters(xml_basic_2, key_list, value_list)
        #Set 2º phase folders
        path_out_2 = PATH_TMP_FLR + '/tmp/step2'
        path_xml_2 = PATH_XML_FLR + '/step2'
        if not os.path.exists(path_xml_2):
            os.makedirs(path_xml_2)
        if not os.path.exists(path_out_2):
            os.makedirs(path_out_2)
        #Get files that has been properly processed at 1º phase
        files_img_flr_1 = func.get_files(path_out_1)
        path_img_1, name_img_1 = func.clean_files_processed(files_img_flr_1)
        path_img_1, name_img_1 = func.check_images(path_img_1, name_img_1)
        #Set images with same date
        img_par_out_1, path_par_out_1, par_out_join_1, img_uni_out_1, path_uni_out_1 = func.get_parents_files(path_img_1, name_img_1)
        #Generate 2º phase xmls.
        for i, img in enumerate(par_out_join_1):
            xml_i = re.sub('~INPUTFILE', par_out_join_1[i], xml_parameters_2)
            path_out_2_i = path_out_2 + '/' + img_par_out_1[i*2][17:25]
            xml_i = re.sub('~OUTPUTFILE', path_out_2_i, xml_i)
            route_xml_file_2 = path_xml_2 + '/' + img_par_out_1[i*2][17:25] + '.xml'
            xml_file_2 = open(route_xml_file_2, 'a')
            xml_file_2.write(xml_i)
            xml_file_2.close()
            path_xmls_2.append(route_xml_file_2)
        #Launch 2º phase processes
        #Create list with args
        args_list = list()
        for i in path_xmls_2:
            args = [GPT, i, '-c', CACHE, '-q', CPU]
            args_list.append(args)
        #Multiprocessing
        multi_list = list()
        pool = multiprocessing.Pool(processes=NUM_PROC)
        for i in args_list:
            procc_num += 1
            y = pool.apply_async(func.launch_proccess, args=(i, procc_num))
            multi_list.append(y)
        pool.close()
        pool.join()
        for i in multi_list:
            msg_out = i.get()
            pos_err = msg_out.find('Error at process [')
            if pos_err != -1:
                log.write_error(msg_out[pos_err:pos_err+20])
            log.write_output(msg_out)
    ############ 3º phase ############
    #We execute processes after Assembly Orbit
        msg_out_3 = MSG_BAR + "##### Start third phase #####"
        log.write_output(msg_out_3)
        path_xmls_3 = list()
        #3º phase. Set steps to do. Read + from step after Assembly_Orbit to last one.
        steps_todo_3 = steps_todo[steps_todo.index('Assembly_Orbit'):]
        steps_todo_3.pop(0)
        steps_todo_3.insert(0, 'Read')
        #Set xml model
        xml_basic_3 = func.graph_skeleton(steps_todo_3, path_graphs)
        xml_parameters_3 = func.set_all_parameters(xml_basic_3, key_list, value_list)
        #Set 3º phase folders
        if flag_delete_stack == 1:
            path_out_3 = PATH_RES_FLR + '/to_delete'
        else:
            path_out_3 = PATH_RES_FLR + '/result'
        path_xml_3 = PATH_XML_FLR + '/step3'
        if not os.path.exists(path_xml_3):
            os.makedirs(path_xml_3)
        #Get files that has been properly processed at 2º phase
        files_img_flr_2 = func.get_files(path_out_2)
        path_img_2, name_img_2 = func.clean_files_processed(files_img_flr_2)
        #Generate 3º phase xmls
        for i, img in enumerate(name_img_2):
            xml_i = re.sub('~INPUTFILE', path_img_2[i], xml_parameters_3)
            path_out_3_i = path_out_3 + '/' + img
            xml_i = re.sub('~OUTPUTFILE', path_out_3_i, xml_i)
            route_xml_file_3 = path_xml_3 + '/' + img + '.xml'
            xml_file_3 = open(route_xml_file_3, 'a')
            xml_file_3.write(xml_i)
            xml_file_3.close()
            path_xmls_3.append(route_xml_file_3)
        #Launch 3º phase processes
        #Create list with args
        args_list = list()
        for i in path_xmls_3:
            args = [GPT, i, '-c', CACHE, '-q', CPU]
            args_list.append(args)
        #Multiprocessing
        multi_list = list()
        pool = multiprocessing.Pool(processes=NUM_PROC)
        for i in args_list:
            procc_num += 1
            y = pool.apply_async(func.launch_proccess, args=(i, procc_num))
            multi_list.append(y)
        pool.close()
        pool.join()
        for i in multi_list:
            msg_out = i.get()
            pos_err = msg_out.find('Error at process [')
            if pos_err != -1:
                log.write_error(msg_out[pos_err:pos_err+20])
            log.write_output(msg_out)
    ###############################################################################
    #Delete 'tmp' folder
        if flag_delete_tmp == 1:
            shutil.rmtree(PATH_TMP_FLR + '/tmp', ignore_errors=True)
    ############ EXECUTION WITHOUT ASSEMBLY ############
    #Execute normal process when we don't need to do assembly.
    #We do in a single process by image
    #No necessary to chop in three steps

    if flag_assembly == 0:
        #Print files to process
        log.write_output(MSG_BAR + "##### START PROCESSING IMAGES #####\nImages to process: " \
                         + str(len(name_img)) + " images.\nImages result: " + str(len(name_img)) \
                         + " images.\nImages input list:")
        for i, img in enumerate(name_img):
            log.write_output(" - " + img)
        path_xmls = list()
        #Set xml model
        xml_basic = func.graph_skeleton(steps_todo, path_graphs)
        try:
            xml_parameters = func.set_all_parameters(xml_basic, key_list, value_list)
        except:
            log.close()
            sys.exit(1)
        #Set folders
        if flag_delete_stack == 1:
            path_out = PATH_RES_FLR + '/to_delete'
        else:
            path_out = PATH_RES_FLR + '/result'
#        path_out = PATH_RES_FLR + '/result'
        path_xml = PATH_XML_FLR
        if not os.path.exists(path_xml):
            os.makedirs(path_xml)
        #Generate xmls.
        for i, img in enumerate(name_img):
            xml_i = re.sub('~INPUTFILE', path_img[i], xml_parameters)
            path_out_i = path_out + '/' + img[17:25]
            xml_i = re.sub('~OUTPUTFILE', path_out_i, xml_i)
            route_xml_file = path_xml + '/' + img[17:25] + '.xml'
            xml_file_0 = open(route_xml_file, 'a')
            xml_file_0.write(xml_i)
            xml_file_0.close()
            path_xmls.append(route_xml_file)
        #Launch processes
        #Create list with args
        args_list = list()
        for i in path_xmls:
            args = [GPT, i, '-c', CACHE, '-q', CPU]
            args_list.append(args)
        #Multiprocessing
        multi_list = list()
        pool = multiprocessing.Pool(processes=NUM_PROC)
        for i in args_list:
            procc_num += 1
            y = pool.apply_async(func.launch_proccess, args=(i, procc_num))
            multi_list.append(y)
        pool.close()
        pool.join()
        for i in multi_list:
            msg_out = i.get()
            pos_err = msg_out.find('Error at process [')
            if pos_err != -1:
                log.write_error(msg_out[pos_err:pos_err+20])
            log.write_output(msg_out)

    #Launch stack process in case.
    if flag_stack == 1:
        if flag_delete_stack == 1:
            path_images_stack = PATH_RES_FLR + '/to_delete'
        else:
            path_images_stack = PATH_RES_FLR + '/result'
        path_list_files = list()
        list_files = os.listdir(path_images_stack)
        for i in list_files:
            path_list_files.append(path_images_stack +'/' + i)
        path_img, name_img = func.clean_files_processed(path_list_files)
        if flag_separate_bands == 1:
            exist_file = os.path.isfile(path_images_stack + '/' + name_img[0] + '.dim')
            if exist_file:
                format_file = '.dim'
            exist_file = os.path.isfile(path_images_stack + '/' + name_img[0] + '.tif')
            if exist_file:
                format_file = '.tif'
            with open(path_graphs + '/Band_Math.xml', 'r') as file:
                xml_skelet = file.read()
            xml_skelet = func.set_all_parameters(xml_skelet, key_list, value_list)
            xml_skel_vh = re.sub('~INPUT_BAND', 'Sigma0_VH_db', xml_skelet)
            xml_skel_vh = re.sub('~OUTPUT_NAME', 'VH', xml_skel_vh)
            xml_skel_vv = re.sub('~INPUT_BAND', 'Sigma0_VV_db', xml_skelet)
            xml_skel_vv = re.sub('~OUTPUT_NAME', 'VV', xml_skel_vv)
#        list_files = os.listdir(PATH_IMG_FLR)
            path_xml_vv = PATH_XML_FLR + '/stack_VV/'
            path_xml_vh = PATH_XML_FLR + '/stack_VH/'
            if not os.path.exists(path_xml_vv):
                os.makedirs(path_xml_vv)
            if not os.path.exists(path_xml_vh):
                os.makedirs(path_xml_vh)
            path_to_xmls = list()
            for i in name_img:
                xml_vv = xml_skel_vv
                xml_vh = xml_skel_vh
                path_input_file = path_images_stack + '/' + i + format_file
                out_path_vv = PATH_RES_FLR + '/result_stack/VV/' + i
                out_path_vh = PATH_RES_FLR + '/result_stack/VH/' + i
                xml_vv = re.sub('~INPUTFILE', path_input_file, xml_vv)
                xml_vv = re.sub('~OUTPUTFILE', out_path_vv, xml_vv)
                xml_vh = re.sub('~INPUTFILE', path_input_file, xml_vh)
                xml_vh = re.sub('~OUTPUTFILE', out_path_vh, xml_vh)
                route_xml_file_vv = path_xml_vv + i + '.xml'
                route_xml_file_vh = path_xml_vh + i + '.xml'
                xml_file = open(route_xml_file_vv, 'w')
                xml_file.write(xml_vv)
                xml_file.close()
                xml_file2 = open(route_xml_file_vh, 'w')
                xml_file2.write(xml_vh)
                xml_file2.close()
                path_to_xmls.append(route_xml_file_vv)
                path_to_xmls.append(route_xml_file_vh)
            #Launch processes
            #Create list with args
            args_list = list()
            for i in path_to_xmls:
                args = [GPT, i, '-c', CACHE, '-q', CPU]
                args_list.append(args)
            #Multiprocessing
            multi_list = list()
            pool = multiprocessing.Pool(processes=NUM_PROC)
            for i in args_list:
                procc_num += 1
                y = pool.apply_async(func.launch_proccess, args=(i, procc_num))
                multi_list.append(y)
            pool.close()
            pool.join()
            for i in multi_list:
                msg_out = i.get()
                pos_err = msg_out.find('Error at process [')
                if pos_err != -1:
                    log.write_error(msg_out[pos_err:pos_err+20])
                log.write_output(msg_out)

#################### STACK VV
            list_files = os.listdir(PATH_RES_FLR + '/result_stack/VV/')
            path_list_files = list()
            for i in list_files:
                path_list_files.append(PATH_RES_FLR + '/result_stack/VV/' + i)
            #Clean to admited formats
            path_img_stack, name_img_stack = func.clean_files_processed(path_list_files)
            list_images_stack = list()
            list_path_stack = list()
            for num, name in enumerate(name_img_stack):
                try:
                    datetime.strptime(name, '%Y%m%d')
                    list_images_stack.append(name_img_stack[num])
                    list_path_stack.append(path_img_stack[num])
                except ValueError:
                    pass
            if flag_not_img_txt == 0:
                log.write_output("INFO: Images to process are setted up via images text file\n")
                list_path_stack, list_images_stack = func.set_images(PATH_IMG_FILE, list_path_stack, list_images_stack)
            #Check if is empty
            if not list_images_stack:
                msg_err_empty_stack = "ERROR: Resources to do stack are empty. This process will not be executed"
                log.write_error(msg_err_empty_stack)
            elif len(list_images_stack) == 1:
                msg_err_empty_stack = "ERROR: Only one resource to do stack. This process will not be executed"
                log.write_error(msg_err_empty_stack)
            else:
                msg_str_stack = MSG_BAR + "##### STACK IMAGES VV #####\nImages to process: " \
                + str(len(list_images_stack)) + " images.\nImages result: " + str(len(list_images_stack)) \
                + " images.\nImages input list to do stack:"
                log.write_output(msg_str_stack)
                for i in list_images_stack:
                    log.write_output(" · " + i)
            #   Generate input format
                input_string = ",".join(list_path_stack)
            #   Set xml
                path_xml = PATH_XML_FLR
                xml_stack = func.graph_skeleton(['CreateStack'], path_graphs)
                try:
                    xml_stack_parameters = func.set_all_parameters(xml_stack, key_list, value_list)
                except:
                    log.close()
                    sys.exit(1)
                xml = re.sub('~INPUTFILE', input_string, xml_stack_parameters)
                path_out_stack = PATH_RES_FLR + '/result_stack/stack_vv'
                xml = re.sub('~OUTPUTFILE', path_out_stack, xml)
            #   Replace stack number files
                xml = re.sub('~NUM_STACK', str(len(list_images_stack)), xml)
                route_xml_file = path_xml + '/stack_vv.xml'
                xml_file = open(route_xml_file, 'a')
                xml_file.write(xml)
                xml_file.close()
            #   Launch process
                args = [GPT, route_xml_file, '-c', CACHE, '-q', CPU]
                procc_num += 1
                feedback = func.launch_proccess(args, procc_num)
                log.write_output(feedback)

                if flag_delete_stack == 1:
                    for i in list_path_stack:
                        os.remove(i)

#################### STACK VH
            list_files = os.listdir(PATH_RES_FLR + '/result_stack/VH/')
            path_list_files = list()
            date_list = list()
            for i in list_files:
                path_list_files.append(PATH_RES_FLR + '/result_stack/VH/' + i)
            #Clean to admited formats
            path_img_stack, name_img_stack = func.clean_files_processed(path_list_files)
            date_as_num = list()
            for i in name_img_stack:
                date_as_num.append(int(i))
            list_images_stack = list()
            list_path_stack = list()
            for num, name in enumerate(name_img_stack):
                try:
                    datetime.strptime(name, '%Y%m%d')
                    list_images_stack.append(name_img_stack[num])
                    list_path_stack.append(path_img_stack[num])
                except ValueError:
                    pass
            if flag_not_img_txt == 0:
                log.write_output("INFO: Images to process are setted up via images text file\n")
                list_path_stack, list_images_stack = func.set_images(PATH_IMG_FILE, list_path_stack, list_images_stack)
#Check if is empty
            if not list_images_stack:
                msg_err_empty_stack = "ERROR: Resources to do stack are empty. This process will not be executed"
                log.write_error(msg_err_empty_stack)
            elif len(list_images_stack) == 1:
                msg_err_empty_stack = "ERROR: Only one resource to do stack. This process will not be executed"
                log.write_error(msg_err_empty_stack)
            else:
                msg_str_stack = MSG_BAR + "##### STACK IMAGES VH #####\nImages to process: " \
                + str(len(list_images_stack)) + " images.\nImages result: " + str(len(list_images_stack)) \
                + " images.\nImages input list to do stack:"
                log.write_output(msg_str_stack)
#        print(list_images_stack)
                for i in list_images_stack:
                    log.write_output(" · " + i)
#   Generate input format
                input_string = ",".join(list_path_stack)
#   Set xml
                path_xml = PATH_XML_FLR
                xml_stack = func.graph_skeleton(['CreateStack'], path_graphs)
                try:
                    xml_stack_parameters = func.set_all_parameters(xml_stack, key_list, value_list)
                except:
                    log.close()
                    sys.exit(1)
                xml = re.sub('~INPUTFILE', input_string, xml_stack_parameters)
                path_out_stack = PATH_RES_FLR + '/result_stack/stack_vh'
#        path_out_stack = PATH_RES_FLR + '\\result_stack\\stack'
                xml = re.sub('~OUTPUTFILE', path_out_stack, xml)
#   Replace stack number files
                xml = re.sub('~NUM_STACK', str(len(list_images_stack)), xml)
                route_xml_file = path_xml + '/stack_vh.xml'
#        route_xml_file = path_xml + '\\stack.xml'
                xml_file = open(route_xml_file, 'a')
                xml_file.write(xml)
                xml_file.close()
#   Launch process
                args = [GPT, route_xml_file, '-c', CACHE, '-q', CPU]
                procc_num += 1
                feedback = func.launch_proccess(args, procc_num)
                log.write_output(feedback)

                if flag_delete_stack == 1:
                    for i in list_path_stack:
                        os.remove(i)
        else:
            list_images_stack = list()
            list_path_stack = list()
            for num, name in enumerate(name_img):
                try:
                    datetime.strptime(name, '%Y%m%d')
                    list_images_stack.append(name_img[num])
                    list_path_stack.append(path_img[num])
                except ValueError:
                    pass
            if flag_not_img_txt == 0:
                log.write_output("INFO: Images to process are setted up via images text file\n")
                list_path_stack, list_images_stack = func.set_images(PATH_IMG_FILE, list_path_stack, list_images_stack)
            #Check if is empty
            if not list_images_stack:
                msg_err_empty_stack = "ERROR: Resources to do stack are empty. This process will not be executed"
                log.write_error(msg_err_empty_stack)
            elif len(list_images_stack) == 1:
                msg_err_empty_stack = "ERROR: Only one resource to do stack. This process will not be executed"
                log.write_error(msg_err_empty_stack)
            else:
                msg_str_stack = MSG_BAR + "##### STACK IMAGES #####\nImages to process: " \
                + str(len(list_images_stack)) + " images.\nImages result: " + str(len(list_images_stack)) \
                + " images.\nImages input list to do stack:"
                log.write_output(msg_str_stack)
                for i in list_images_stack:
                    log.write_output(" · " + i)
            #   Generate input format
                input_string = ",".join(list_path_stack)
            #   Set xml
                path_xml = PATH_XML_FLR
                xml_stack = func.graph_skeleton(['CreateStack'], path_graphs)
                try:
                    xml_stack_parameters = func.set_all_parameters(xml_stack, key_list, value_list)
                except:
                    log.close()
                    sys.exit(1)
                xml = re.sub('~INPUTFILE', input_string, xml_stack_parameters)
                path_out_stack = PATH_RES_FLR + '/result_stack/stack'
        #        path_out_stack = PATH_RES_FLR + '\\result_stack\\stack'
                xml = re.sub('~OUTPUTFILE', path_out_stack, xml)
            #   Replace stack number files
                xml = re.sub('~NUM_STACK', str(len(list_images_stack)), xml)
                route_xml_file = path_xml + '/stack.xml'
        #        route_xml_file = path_xml + '\\stack.xml'
                xml_file = open(route_xml_file, 'a')
                xml_file.write(xml)
                xml_file.close()
            #   Launch process
                args = [GPT, route_xml_file, '-c', CACHE, '-q', CPU]
                procc_num += 1
                feedback = func.launch_proccess(args, procc_num)
                log.write_output(feedback)

                if flag_delete_stack == 1:
                    for i in list_path_stack:
                        os.remove(i)
    ###############################################################################
    #Delete images.
if flag_delete_stack == 1:
    path_del = PATH_RES_FLR + '/to_delete'
    shutil.rmtree(path_del, ignore_errors=True)
#Finish program.
END_TIME = time.time()
TIME_EXECUTION = "{:.1f}".format(END_TIME - START_TIME)
msg_out_end = "####### The execution needed " + str(TIME_EXECUTION) + " seconds. #######"+ MSG_BAR
log.write_output(msg_out_end)
log.close()
