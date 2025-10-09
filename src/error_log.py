# -*- coding: utf-8 -*-
"""エラー出力関連のライブラリ

"""

# 外部ライブラリ
import os
import datetime

# 内部ライブラリ
import cam_generic_lib as glib 
import cam_global as gdata

def output_log(error_str):
    """指定の文字列をERROR_LOG_FILENAMEで指定されるファイルに出力する。

    エラーメッセージに加え、発生時刻も追加してファイルに出力する。

    Args:
        error_str (str): エラーメッセージ
    """
    cur_dir =  glib.get_curdir()
    file_name = "%s\\%s"%(cur_dir, gdata.ERROR_LOG_FILENAME)
    dt_now = datetime.datetime.now()
    time_str = dt_now.strftime('%Y/%m/%d %H:%M:%S')
    
    f = open(file_name,'a', encoding='shift-jis')
    f.write("Time: %s\n"%time_str)
    f.write(error_str)
    f.write("\n")
    f.close()