# -*- coding: utf-8 -*-
"""
Created on Tue Aug 12 11:23:06 2025

@author: hirar
"""

# 外部ライブラリ
import os
import datetime

# 内部ライブラリ
from cam_generic_lib import *
from cam_global import *

def output_log(error_str):
    cur_dir =  get_curdir()
    file_name = "%s\%s"%(cur_dir, ERROR_LOG_FILENAME)
    dt_now = datetime.datetime.now()
    time_str = dt_now.strftime('%Y/%m/%d %H:%M:%S')
    
    f = open(file_name,'a')
    f.write("Time: %s\n"%time_str)
    f.write(error_str)
    f.write("\n")
    f.close()