# -*- coding: utf-8 -*-
"""
Created on Sat Jun 27 13:29:53 2020

@author: Naoto
"""
#======================================================================================================================================
#            改訂履歴
#======================================================================================================================================
#   日付         バージョン  改訂内容
#   2020.7.12    ver1.0   新規作成
#   2020.10.11   ver2.0   Gコード修正/ 加工面のオフセット機能追加
#   2020.10.13   ver2.1   加工面オフセットを両端で別値とできるように変更

#======================================================================================================================================
#            関連モジュールのインポート
#======================================================================================================================================
#【pip等で追加が必要なモジュール】
# numpy
# scipy
# matplotlib
# ezdxf
#
#【python標準モジュール（追加不要）】
# tkinter
# os
# datetime

# 外部ライブラリ
import tkinter as tk
from tkinter import ttk
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
from matplotlib.figure import Figure
import datetime
import os
import traceback

# 内部ライブラリ
from cam_generic_lib import *
from dxf_file import *
from messeage_window import *
from cam_global import *
from error_log import *

#======================================================================================================================================
#            クラスの実装
#======================================================================================================================================

#######################################################################################################################################
###############    configクラス   ここから　　　#########################################################################################

#【説明】
#　CAMで使用する設定値を格納するクラスである．
#
#【親クラス】
#　なし
#
#【メンバ変数】
#   変数名          型              説明
#   FILENAME_XY     string          デフォルトで読み込むXYのdxfファイル名（起動時にのみ変更）
#   FILENAME_UV     string          デフォルトで読み込むUVのdxfファイル名（起動時にのみ変更）
#   OX              float           切り出しの始点座標
#   OY              float           切り出しの始点座標
#   EX              float           切り出しの終点座標
#   EY              float           切り出しの終点座標
#   DELTA_LENGTH    float           G Codeの点群の間隔
#   OFFSET_DIST     float           オフセット距離
#   CUTSPEED        float           カット速度
#   XY_DIST         float           XY断面とマシン駆動面との距離
#   UV_DIST         float           UV断面とマシン駆動面との距離
#   WORK_LENGTH     float           ワークの長さ（XY-UV断面距離）
#   MACH_DIST       float           マシン駆動面の距離
#   HEADER          string          Gコードの書き出し文字列
#   x_str           string          G01でのX軸名称
#   y_str           string          G01でのY軸名称
#   u_str           string          G01でのU軸名称
#   v_str           string          G01でのV軸名称
#   offset_function object          オフセット距離の算出に使用する関数オブジェクト
#
#【実装メソッド】
#   __init__()
#   【引数】 なし
#   【戻り値】　なし
#   【機能】 メンバ変数をデフォルト値に設定する
#
#   load_config(string file_path)
#   【引数】 file_path
#   【戻り値】　なし
#   【機能】 file_pathで与えられるcsvファイルを開き、csvファイルから読み込んだ値をメンバ変数に設定する。問題があればデフォルト値を設定する
#
#   load_offset_func(string　file_path)
#   【引数】　string　file_path
#   【戻り値】　なし
#   【機能】 file_pathで与えられるcsvファイルを開き、csvファイルから読み込んだ値からoffset_functionを更新する。問題があればデフォルト値を設定する


class Config:
    def __init__(self):
        self.FILENAME_XY = "ファイル名を入力して下さい。"
        self.FILENAME_UV = "ファイル名を入力して下さい。"
        self.OX = 0.0
        self.OY = 0.0
        self.EX = 0.0
        self.EY = 0.0
        self.DELTA_LENGTH = 1.0
        self.XY_OFFSET_DIST = 0.0
        self.UV_OFFSET_DIST = 0.0
        self.CUTSPEED = 200
        self.XY_DIST = 25.0
        self.UV_DIST = 50.0
        self.CS_DEF = "Center"
        self.CNC_CS_DEF = "XY"
        self.MACH_DIST = 500
        self.OFFSET_X = 0
        self.OFFSET_Y = 0
        self.ROTATE = 0
        self.HEADER = "T1\nG17 G49 G54 G80 G90 G94 G21 G40 G64\n"
        self.X_STR = 'X'
        self.Y_STR = 'Y'
        self.U_STR = 'Z'
        self.V_STR = 'A'
        self.REFINE = False
        self.REMOVE_COLLISION = False
        x_data = [1,1000]
        y_data = [0,0]
        self.offset_function = generate_offset_function(x_data, y_data)
        
    def load_config(self, file_path):
        try:
            config_file = np.genfromtxt(file_path, delimiter = ",", skip_header = 1, dtype = str, encoding="shift-jis")
            config_data = config_file[:,2]
            self.FILENAME_XY = config_data[0]
            self.FILENAME_UV = config_data[1]
            self.OX = float(config_data[2])
            self.OY = float(config_data[3])
            self.EX = float(config_data[4])
            self.EY = float(config_data[5])
            self.DELTA_LENGTH = float(config_data[6])
            self.XY_OFFSET_DIST = float(config_data[7])
            self.UV_OFFSET_DIST = float(config_data[8])
            self.CUTSPEED = float(config_data[9])
            self.CS_DEF = str(config_data[10])
            self.CNC_CS_DEF = str(config_data[11])
            self.XY_DIST = float(config_data[12])
            self.UV_DIST = float(config_data[13])
            self.MACH_DIST = float(config_data[14])
            self.OFFSET_X = float(config_data[15])
            self.OFFSET_Y = float(config_data[16])
            self.ROTATE = float(config_data[17])           
            self.HEADER = config_data[18].replace("\\n", "\n")
            self.X_STR = str(config_data[19])
            self.Y_STR = str(config_data[20])
            self.U_STR = str(config_data[21])
            self.V_STR = str(config_data[22])
            if str(config_data[23]) == "ON":
                self.REMOVE_COLLISION = True
            else:
                self.REMOVE_COLLISION = False
                
            if str(config_data[24]) == "ON":
                self.REFINE = True
            else:
                self.REFINE = False            
            
            self.MESSEAGE = "設定ファイルの読み込み成功\n"
            
        except:
            traceback.print_exc()
            output_log(traceback.format_exc())
            self.FILENAME_XY = "ファイル名を入力して下さい。"
            self.FILENAME_UV = "ファイル名を入力して下さい。"
            self.OX = 0.0
            self.OY = 0.0
            self.EX = 0.0
            self.EY = 0.0
            self.DELTA_LENGTH = 1.0
            self.XY_OFFSET_DIST = 0.0
            self.UV_OFFSET_DIST = 0.0
            self.CUTSPEED = 200
            self.CS_DEF = "Center"
            self.CNC_CS_DEF = "XY"
            self.XY_DIST = 25.0
            self.UV_DIST = 50.0
            self.MACH_DIST = 500
            self.OFFSET_X = 0
            self.OFFSET_Y = 0
            self.ROTATE = 0
            self.HEADER = "T1\nG17 G49 G54 G80 G90 G94 G21 G40 G64\n"
            self.X_STR = 'X'
            self.Y_STR = 'Y'
            self.U_STR = 'Z'
            self.V_STR = 'A'
            self.REFINE = False
            self.REMOVE_COLLISION = False
            self.MESSEAGE = "設定ファイルの読み込み失敗\n"
            pass          

    def load_offset_func(self, file_path):
        try:
            offset_function_file = np.genfromtxt(file_path, delimiter = ",", skip_header = 1, dtype = str, encoding="shift-jis")
            x_data = offset_function_file[0,3:]
            y_data = offset_function_file[1,3:]
            x_data = x_data.astype(float)
            y_data = y_data.astype(float)
            self.offset_function = generate_offset_function(x_data, y_data)
            self.MESSEAGE = "%sの読み込み成功\n"%file_path
        except:
            traceback.print_exc()
            output_log(traceback.format_exc())
            x_data = [1,1000]
            y_data = [0,0]
            self.offset_function = generate_offset_function(x_data, y_data)
            self.MESSEAGE = "溶け量ファイルの読み込み失敗\n"


#======================================================================================================================================
#            ボタンにより呼び出される関数
#======================================================================================================================================
#
#   open_file_explorer(entry)
#   【引数】　entry
#   【戻り値】　なし
#   【機能】 エクスプローラーを使ってファイルパスを指定し、パスをEntryにセットする。
#
#   load_config(config, config_entry, dl_entry, cut_speed_entry, xy_dist_entry, uv_dist_entry, WorkLengthEntry, mech_dist_entry, message_window)
#   【引数】　config, config_entry, dl_entry, cut_speed_entry, xy_dist_entry, uv_dist_entry, WorkLengthEntry, mech_dist_entry, message_window
#   【戻り値】　なし
#   【機能】 open_file_explorerを用いて、config_entryにconfigファイルのパスを設定する
#           configクラスのload_configメソッドを使用して、configファイルのパスを読みこみ、configオブジェクトの値を更新する
#           dl_entry, cut_speed_entry, xy_dist_entry, uv_dist_entry, WorkLengthEntry, MachDistEntryの値を、configオブジェクトの値に更新する
#           MessageWindowにconfig.load_configの結果およびGコードの書き出しを出力する
#
#   load_offset_func(config, offset_func_entry, message_window)
#   【引数】　config, offset_func_entry, message_window
#   【戻り値】　なし
#   【機能】 open_file_explorerを用いて、offset_func_entryに溶け量ファイルのパスを設定する
#           configクラスのload_offset_funcメソッドを使用して、溶け量ファイルのパスを読みこみ、configオブジェクトのoffset_functionのメンバーを更新する
#           MessageWindowにconfig.load_offset_funcの結果を出力する
# 
#   open_dxf_explorer(dxf_obj, entry, messeage_window)
#   【引数】　dxf_obj, entry, messeage_window
#   【戻り値】　なし
#   【機能】 エクスプローラーを使ってファイルパスを読みこむ。パスをEntryにセットしたうえで、load_fileによりファイルを読み込む。
#
#   load_file(DxfFile　dxf_obj, tk.Entry entry, messeage_window messeage_window)
#   【引数】　dxf_obj, entry, messeage_window
#   【戻り値】　なし
#   【機能】 Entryに入力されたファイル名称をdxf_obj.load_fileにより読み込む．file_chkをコールし，読み取り可否をmesseage_windowに通知する．
#　　　　　　　　
#   xy_uv_link(tk.BooleanVar is_xy_uv_link, SuperTable xy_table, SuperTable uv_table, messeage_window  messeage_window)
#   【引数】 is_xy_uv_link, xy_table, uv_table, messeage_window
#   【戻り値】　なし
#   【機能】　chkValue=trueの場合，table_XY.parent=1, uv_table.parent=0に設定する．
#
#   swap_line(DxfFile　dxf_obj, messeage_window messeage_window)
#   【引数】 dxf_obj, messeage_window
#   【戻り値】 なし
#   【機能】 dxf_obj.Swap_Selected_lineをコールし，選択された2本のラインを入れ替える．入れ替え結果をmesseage_windowに表示する．
#
#   change_cut_dir(DxfFile　dxf_obj, messeage_window messeage_window)
#   【引数】 dxf_obj, messeage_window
#   【戻り値】 なし
#   【機能】 dxf_obj.change_cut_dirをコールし，選択したラインのカット方向を入れ替える．入れ替え結果をmesseage_windowに表示する．
#
#   Change_OffsetDir(DxfFile　dxf_obj, messeage_window messeage_window)
#   【引数】 dxf_obj, messeage_window
#   【戻り値】　なし
#   【機能】 dxf_obj.Change_OffsetDirをコールし，選択したラインのオフセット方向を入れ替える．入れ替え結果をmesseage_windowに表示する．
#   
#   merge_line(dxf_obj,  messeage_window)
#   【引数】　dxf_obj,  messeage_window
#   【戻り値】　なし
#   【機能】 テーブルで選択された２本のラインを結合する。後に選択した方のラインは削除する
#     
#   set_offset_dist(DxfFile　dxf_obj0, DxfFile　dxf_obj1, tk.Entry entry, messeage_window messeage_window)
#   【引数】　dxf_obj0, dxf_obj1, entry, messeage_window
#   【戻り値】　なし
#   【機能】 entryに入力されたオフセット距離を読み取り，dxf_obj0.set_offset_dist，dxf_obj1.set_offset_distをコールする．変更結果をmesseage_windowに表示する．
#
#   delete_line(DxfFile　dxf_obj, messeage_window messeage_window)
#   【引数】 dxf_obj, messeage_window
#   【戻り値】　なし
#   【機能】 delete_Selected_lineをコールし，選択したラインを削除する．削除した結果をmesseage_windowに表示する．
#
#   auto_sort_line(DxfFile　dxf_obj0, DxfFile　dxf_obj1, tk.Entry entry_x, tk.Entry entry_y, messeage_window messeage_window)
#   【引数】 dxf_obj0, dxf_obj1, entry_x, entry_y, messeage_window
#   【戻り値】 なし
#   【機能】 entry_x, entry_yからox, oyを読み取り．dxf_obj0.sort_line, dxf_obj1.sort_lineをコールする．結果をmesseage_windowに表示する．
#        
#   reverse_line(DxfFile　dxf_obj, messeage_window messeage_window)
#   【引数】　dxf_obj, messeage_window
#   【戻り値】　なし
#   【機能】 dxf_obj.reverse_allをコールし，カット順を逆転させる．結果をmesseage_windowに表示する．
#
#   Replace_G01_code(g_code_str, x_str, y_str, u_str, v_str)
#   【引数】g_code_str, x_str, y_str, u_str, v_str
#   【戻り値】g_code_str
#   【機能】g_code_strのX,Y,U,Vの座標文字をX_str, y_str, u_str, V_strで指定されるものに置換する
#
#   make_offset_path(x_array, y_array, u_array, v_array, z_xy, z_uv, z_mach)
#   【引数】x_array, y_array, u_array, v_array, z_xy, z_uv, z_mach
#   【戻り値】new_x, new_y, new_u, new_v
#   【機能】ワーク上のXY, UV座標点列（x_array, y_array, u_array, v_array）から、マシン駆動面上の座標点列を作成し、出力する
#
#   get_offset_and_cut_speed(length_xy, length_uv, z_xy, z_uv, z_mach, cut_speed, offset_function)
#   【引数】length_XY, length_uv, z_xy, z_uv, z_mach, cut_speed, offset_function
#   【戻り値】offset_XY_Work, offset_UV_Work, cutspeed_XY_Work, cutspeed_UV_Work, cutspeed_XY_Mech, cutspeed_UV_Mech
#   【機能】(1) XY断面の線長とUV断面の線長から、ワークの中間点での線長を算出する
#          (2) ワークの中間点でのカット速度が、CutSpeedとするとして、(1)の線長比から、XY、UV断面でのカット速度(cutspeed_XY_Work, cutspeed_UV_Work)を算出する
#          (3) offset_functionを用いて、XY、UV断面のカット速度における溶け量を推定し、これをキャンセルするようにオフセット量（offset_XY_Work, offset_UV_Work）を設定する。
#              ※マシン駆動面上での座標点列作成は、その他の線郡と同様に、gen_g_code側にて行う
#          (4) ワーク端面（XY面, UV面）とマシン駆動面との距離（Z_XY, z_uv, Z_Mach）から、cutspeed_XY_Work, cutspeed_UV_Workを実現するマシン駆動面速度（cutspeed_XY_Mech, cutspeed_UV_Mech）を算出する
#
#   set_offset_dist_from_function(dxf_obj0, dxf_obj1, xy_dist_entry, uv_dist_entry, mach_dist_entry, cut_speed_entry, offset_function, messeage_window)
#   【引数】dxf_obj0, dxf_obj1, xy_dist_entry, uv_dist_entry, mach_dist_entry, cut_speed_entry, offset_function, messeage_window
#   【戻り値】なし
#   【機能】dxf_obj0, dxf_obj1の対応する線から、XY断面の線長、UV断面の線長を取得し、get_offset_and_cut_speedにより線ごとにオフセット距離、カット速度を取得する
#          取得したオフセット距離、カット速度を線（line Object）に設定し、オフセット距離を更新する
#
#   gen_g_code(DxfFile　dxf_obj0, DxfFile　dxf_obj1, tk.Entry entry_ox, tk.Entry entry_oy, tk.Entry entry_ex, tk.Entry entry_ey, tk.Entry cut_speed_entry, tk.Entry entry_dl, str header, messeage_window messeage_window)
#   【引数】 dxf_obj0, dxf_obj1, entry_ox, entry_oy, entry_ex, entry_ey, cut_speed_entry, entry_dl, header, messeage_window
#   【戻り値】　なし
#   【機能】　gコードを生成する．始点をentry_ox, entry_oyから，終点をentry_ex, entry_eyから読み取る．カット速度をentry_CSから読み取る．分割距離をentry_dlから読み取る．gコードの書き出しをheaderとする．
#　　　　　　　　1. dxf_obj0, dxf_obj1のline_num_listにて0以上の値を取得し，a_line_num_list0,a_line_num_list1に格納する．
#　　　　　　　　2. a_line_num_list0,a_line_num_list1のライン数が一致しているかを確認する．
#　　　　　　　　3. a_line_num_list0,a_line_num_list1のラインを順にgコード化する．各ラインについてget_length()にてライン長を取得し，N=get_length()/dlから分割数を決定する
#　　　　　　　　4. 各ラインについてgenerate_arc_length_pointsをコールし，等間隔点列x, y, u, vを取得する．
#　　　　　　　　5. gen_g_code_line_str(x, y, u, v)をコールし，x, y, u, vからgコードを生成する．
#　　　　　　　　6. 各ラインのgコードを結合し，保存する．保存名は 「dxf_obj0.filename,dxf_obj1.filename,日付.nc」とする．　
#
#   path_chk(tk.Frame Root, DxfFile　dxf_obj0, DxfFile　dxf_obj1, tk.Entry entry_ox, tk.Entry entry_oy, tk.Entry entry_ex, tk.Entry entry_ey, tk.Entry mach_dist_entry, tk.Entry entry_dl, messeage_window messeage_window)
#   【引数】 Root, dxf_obj0, dxf_obj1, entry_ox, entry_oy, entry_ex, entry_ey, mach_dist_entry, entry_dl, messeage_window
#   【戻り値】 なし
#   【機能】 gコードを生成する．始点をentry_ox, entry_oyから，終点をentry_ex, entry_eyから読み取る．XY，UV平面距離をentry_MachDistから読み取る．分割距離をentry_dlから読み取る．
#　　　　　　　　1. カットパスをプロットするウィンドウをRootをベースとして生成する．
#　　　　　　　　2. dxf_obj0, dxf_obj1のline_num_listにて0以上の値を取得し，a_line_num_list0,a_line_num_list1に格納する．
#　　　　　　　　3. a_line_num_list0,a_line_num_list1のライン数が一致しているかを確認する．
#　　　　　　　　4. 各ラインについてgenerate_arc_length_pointsをコールし，等間隔点列x, y, u, vを取得する．また，各ライン間距離がdl*2より大きい場合，generate_arc_length_points4lineをコールし，補完点列を作成する，
#　　　　　　　　5. x,y,u,vを統合した配列x_array, y_array, u_array, v_arrayを生成する．
#　　　　　　　　6. plot_3d_cut_pathにより,x_array, y_array, u_array, v_arrayをプロットする．
#
#   _destroyWindow()
#   【引数】 なし
#   【戻り値】 なし
#   【機能】 メインウィンドウが閉じられた際，インスタンスを破棄する．
#
#   offset_origin(dxf_obj0, dxf_obj1, entry_offset_ox, entry_offset_oy, messeage_window)
#   【引数】 dxf_obj0, dxf_obj1, entry_offset_ox, entry_offset_oy, messeage_window
#   【戻り値】 なし
#   【機能】 entry_offset_ox, entry_offset_oyから原点のオフセット量を取得し、dxf_obj0、dxf_obj1のoffset_originメソッドを使用して、すべての線の座標を原点のオフセット量だけ移動する

def open_file_explorer(entry):
    fTyp = [("","*")]
    iDir = get_curdir()
    data = tk.filedialog.askopenfilename(filetypes = fTyp,initialdir = iDir)
    if not(len(data)==0):
        entry.delete(0,tk.END)
        entry.insert(tk.END, data)


def load_config(config, config_entry, dl_entry, xy_offset_entry, uv_offset_entry,\
                cut_speed_entry, cut_speed_def_cb, cnc_speed_def_cb,\
                xy_dist_entry, uv_dist_entry, mech_dist_entry, message_window):
    open_file_explorer(config_entry)
    
    config_path = config_entry.get()
    config.load_config(config_path)
    
    #【XYオフセット距離入力コンソール】 
    xy_offset_entry.delete(0,tk.END)
    xy_offset_entry.insert(tk.END, config.XY_OFFSET_DIST) 
    
    #【UVオフセット距離入力コンソール】
    uv_offset_entry.delete(0,tk.END)
    uv_offset_entry.insert(tk.END, config.UV_OFFSET_DIST)    
    
    #【分割距離入力コンソール】 
    dl_entry.delete(0,tk.END)
    dl_entry.insert(tk.END, config.DELTA_LENGTH) 

    #【カット速度入力コンソール】   
    cut_speed_entry.delete(0,tk.END)
    cut_speed_entry.insert(tk.END, config.CUTSPEED) 

    #【カット速度定義コンボボックス】   
    cut_speed_def_cb.set(config.CS_DEF) 

    #【CNCカット速度定義コンボボックス】   
    cnc_speed_def_cb.set(config.CNC_CS_DEF) 

    #【カット面距離入力コンソール1】   
    xy_dist_entry.delete(0,tk.END)
    xy_dist_entry.insert(tk.END, config.XY_DIST)

    #【カット面距離入力コンソール2】   
    uv_dist_entry.delete(0,tk.END)
    uv_dist_entry.insert(tk.END, config.UV_DIST)

    #【マシン距離入力コンソール】   
    mech_dist_entry.delete(0,tk.END)
    mech_dist_entry.insert(tk.END, config.MACH_DIST)  
        
    message_window.set_messeage(config.MESSEAGE)
    message_window.set_messeage("Gコードの書き出しは「%s」です。\n"%config.HEADER)


def load_offset_func(config, offset_func_entry, message_window):
    open_file_explorer(offset_func_entry)
    offset_file_path = offset_func_entry.get()
    config.load_offset_func(offset_file_path)
    
    message_window.set_messeage(config.MESSEAGE)


def open_dxf_explorer(dxf_obj, entry, is_spline_refine, messeage_window):
    open_file_explorer(entry)
    load_file(dxf_obj, entry, is_spline_refine, messeage_window)


def load_file(dxf_obj, entry, is_spline_refine, messeage_window):
    filename = entry.get()
    is_refine = is_spline_refine.get()
    
    if file_chk(filename) == 1:
        ox = dxf_obj.ox
        oy = dxf_obj.oy
        rx = dxf_obj.rx
        ry = dxf_obj.ry
        sita = dxf_obj.sita
        
        dxf_obj.load_file(filename, is_refine)
        dxf_obj.offset_origin(ox, oy)
        dxf_obj.rotate(sita, rx, ry)
        dxf_obj.update(keep_view = False)
        if is_refine == True:
            messeage_window.set_messeage("%sを点列をリファインして読み込みました。\n"%filename)
        else:
            messeage_window.set_messeage("%sをDXFファイルの座標点のまま読み込みました。\n"%filename)
    if file_chk(filename) == 0:
        messeage_window.set_messeage("%sを読み込めません。拡張子が.dxfであることを確認して下さい。\n"%filename)  
        
    if file_chk(filename) == -1:        
        messeage_window.set_messeage("%sを読み込めません。ファイルが存在することを確認して下さい。\n"%filename)  
   
    
def xy_uv_link(is_xy_uv_link, xy_table, uv_table, messeage_window):
    if is_xy_uv_link.get():
        xy_table.set_sync(True)
        uv_table.set_sync(True)
        messeage_window.set_messeage("U-V画面をX-Y画面と連動\n")
    else:
        xy_table.set_sync(False)
        uv_table.set_sync(False)   
        messeage_window.set_messeage("U-V画面とX-Y画面の連動を解除\n")


def enable_remove_self_collision(is_remove_collision, messeage_window):
    if is_remove_collision.get():
        messeage_window.set_messeage("自己交差除去を有効化\n")
    else:
        messeage_window.set_messeage("自己交差除去を無効化\n")


def enable_spline_refine(is_spline_refine, messeage_window):
    if is_spline_refine.get():
        messeage_window.set_messeage("スプライン点列のリファインを有効化\n")
    else:
        messeage_window.set_messeage("スプライン点列のリファインを無効化\n")


def enable_3d_path_check(is_3d_path_check, messeage_window):
    if is_3d_path_check.get():
        messeage_window.set_messeage("パスチェックを3Dで実施\n")
    else:
        messeage_window.set_messeage("パスチェックを2Dで実施\n")



def change_cut_dir(dxf_obj, x_dxf_obj, is_xy_uv_link, name, x_name, messeage_window):
    dxf_obj.change_cut_dir()
    dxf_obj.update()
    messeage_window.set_messeage("%sのカット方向を逆転\n"%name)
    if is_xy_uv_link.get():
        x_dxf_obj.change_cut_dir()
        x_dxf_obj.update()
        messeage_window.set_messeage("%sのカット方向を逆転\n"%x_name)
    
    
def auto_sort_line(dxf_obj, x_dxf_obj, is_xy_uv_link, name, x_name, messeage_window): 
    try:
        ret = dxf_obj.sort_line()    
        if ret == 1:
            dxf_obj.select_index(0)
            dxf_obj.update()
            messeage_window.set_messeage("%sを自動整列しました。\n"%name)
        else:
            messeage_window.set_messeage("%sで%s本の線が選択されています。起点とする１本の線のみを選択してください。\n"%(name,ret))
        
        if is_xy_uv_link.get():
            x_ret = x_dxf_obj.sort_line()
            if x_ret == 1:
                x_dxf_obj.select_index(0)
                x_dxf_obj.update()
                messeage_window.set_messeage("%sを自動整列しました。\n"%x_name)
            else:
                messeage_window.set_messeage("%sで%s本の線が選択されています。起点とする１本の線のみを選択してください。\n"%(x_name,ret))
        
    except:
        traceback.print_exc()
        output_log(traceback.format_exc())
        pass


def reverse_line(dxf_obj, x_dxf_obj, is_xy_uv_link, name, x_name, messeage_window):
    dxf_obj.reverse_all()
    dxf_obj.update()
    messeage_window.set_messeage("%sのカット順を逆転しました。\n"%name)
    if is_xy_uv_link.get():
        x_dxf_obj.reverse_all()
        x_dxf_obj.update()
        messeage_window.set_messeage("%sのカット順を逆転しました。\n"%x_name)



def merge_line(dxf_obj, x_dxf_obj, is_xy_uv_link, is_remove_collision, name, x_name, messeage_window):
    results, line_nums = dxf_obj.merge_selected_line()
    if len(results) >= 2:
        i = 1
        while i < len(results):
            if results[i] == True:
                messeage_window.set_messeage("%sの%s番目のラインに%s番目のラインを結合しました。\n"%(name,line_nums[0],line_nums[i]))
            else:
                messeage_window.set_messeage("%sの%s番目のラインを結合できませんでした。ライン端点が接しているかを確認してください。\n"%(name,line_nums[i]))
            i += 1
        if is_remove_collision.get():
            remove_collision(dxf_obj, name, messeage_window)
    else:
        messeage_window.set_messeage("%sで２本以上のラインを選択して下さい。%s本のラインが選択されています。\n"%(name,len(line_nums)))
    dxf_obj.update()
    
    
    if is_xy_uv_link.get():
        x_results, x_line_nums = x_dxf_obj.merge_selected_line()
        
        if len(x_results) >= 2:
            i = 1
            while i < len(x_results):
                if x_results[i] == True:
                    messeage_window.set_messeage("%sの%s番目のラインに%s番目のラインを結合しました。\n"%(x_name,x_line_nums[0],x_line_nums[i]))
                else:
                    messeage_window.set_messeage("%sの%s番目のラインを結合できませんでした。ライン端点が接しているかを確認してください。\n"%(x_name,x_line_nums[i]))
                i += 1
            if is_remove_collision.get():
                remove_collision(x_dxf_obj, x_name, messeage_window)      
        else:
            messeage_window.set_messeage("%sで２本以上のラインを選択して下さい。%s本のラインが選択されています。\n"%(x_name,len(x_line_nums)))
        x_dxf_obj.update()
  
def separate_line(dxf_obj, is_remove_collision, name, messeage_window):
    result, line_nums, point_index = dxf_obj.separate_line()
    if result == True:
        messeage_window.set_messeage("%sで%s番目のラインを分割し、%s番目のラインを作成しました\n"%(name,line_nums[0], line_nums[1]))
        
        if is_remove_collision.get():
            remove_collision(dxf_obj, name, messeage_window) 
            
        dxf_obj.update()
    else:
        if not (len(line_nums) == 1):
            messeage_window.set_messeage("%sで%s本のラインが選択されています。1本のみ選択してださい\n"%(name,len(line_nums)))
        elif point_index == None:
            messeage_window.set_messeage("%sで分割点を選択してださい\n"%name)
        else:
            messeage_window.set_messeage("%sで端点が選択されています。端点以外を選択してださい\n"%name)
        
        
def delete_line(dxf_obj, x_dxf_obj, is_xy_uv_link, is_remove_collision, name, x_name, messeage_window):
    dxf_obj.delete_selected_line()
    messeage_window.set_messeage("%sの選択したラインを削除しました。\n"%name)
    
    if is_remove_collision.get():
        remove_collision(dxf_obj, name, messeage_window) 
    
    dxf_obj.update()

    if is_xy_uv_link.get():
        x_dxf_obj.delete_selected_line()
        messeage_window.set_messeage("%sの選択したラインを削除しました。\n"%x_name)
        
        if is_remove_collision.get():
            remove_collision(x_dxf_obj, x_name, messeage_window)       
        
        x_dxf_obj.update()
        
    
def set_offset_dist(dxf_obj, entry, x_dxf_obj, x_entry, is_xy_uv_link, is_remove_collision, name, x_name, messeage_window):
    try:
        entry_value = entry.get()
        offset_dist = float(entry_value)
        dxf_obj.set_offset_dist(offset_dist)
        messeage_window.set_messeage("%sのオフセット距離を%sに設定しました。\n"%(name, offset_dist))
        
        if is_remove_collision.get():
            remove_collision(dxf_obj, name, messeage_window)
        dxf_obj.update()
        
        if is_xy_uv_link.get():
            x_entry_value = x_entry.get()
            x_offset_dist = float(x_entry_value)
            x_dxf_obj.set_offset_dist(x_offset_dist)
            messeage_window.set_messeage("%sのオフセット距離を%sに設定しました。\n"%(x_name, x_offset_dist))
            
            if is_remove_collision.get():
                remove_collision(x_dxf_obj, x_name, messeage_window)
                
            x_dxf_obj.update()
                
    except:
        traceback.print_exc()
        output_log(traceback.format_exc())
        messeage_window.set_messeage("実数値を入力して下さい。\n")
        pass

def remove_collision(dxf_obj, name, messeage_window):
    self_collision_list = dxf_obj.remove_self_collision()
    collision_line_list = dxf_obj.remove_line_collision()
    
    if len(self_collision_list) > 0:
        for num in self_collision_list:
            messeage_window.set_messeage("%sの%s番目の線で自己交差を修正しました。形状に問題がないかをチェックしてください。\n"%(name, num))
    if len(collision_line_list) > 0:
        for nums in collision_line_list:
            messeage_window.set_messeage("%sの%s本目と%s本目の線で自己交差を修正しました。形状に問題がないかをチェックしてください。\n"%(name, nums[0], nums[1]))            


def replace_g_code(g_code_str, x_str, y_str, u_str, v_str):
    
    if ('G' in g_code_str) and ('X' in g_code_str) and ('Y' in g_code_str) and ('U' in g_code_str) and ('V' in g_code_str):
        new_g_code_str = g_code_str
        new_g_code_str = new_g_code_str.replace('X', x_str)
        new_g_code_str = new_g_code_str.replace('Y', y_str)
        new_g_code_str = new_g_code_str.replace('U', u_str)
        new_g_code_str = new_g_code_str.replace('V', v_str)
        return new_g_code_str

    else:
        return g_code_str

def make_offset_path(x_array, y_array, u_array, v_array, z_xy, z_uv, z_mach):
    
    new_x = []
    new_y = []
    new_u = []
    new_v = []
    
    z_work_mid = (z_mach - z_xy - z_uv)/2.0 + z_xy
    l_xy_work = np.abs(z_work_mid - z_xy)
    l_uv_work = np.abs((z_mach - z_uv) - z_work_mid)
    l_xy_mach = np.abs(z_work_mid)
    l_uv_mach = np.abs(z_mach - z_work_mid)
    
    if l_xy_work == 0 or l_uv_work == 0:
        k_xy = 1.0
        k_uv = 1.0        
    else:
        k_xy = l_xy_mach/ l_xy_work
        k_uv = l_uv_mach/ l_uv_work
    
    i = 0
    while i < len(x_array):
        xu_mid = (x_array[i] + u_array[i])/ 2.0
        yv_mid = (y_array[i] + v_array[i])/ 2.0
        dx = x_array[i] - xu_mid
        du = u_array[i] - xu_mid
        dy = y_array[i] - yv_mid
        dv = v_array[i] - yv_mid
        
        new_x.append(dx*k_xy + xu_mid)
        new_y.append(dy*k_xy + yv_mid)
        new_u.append(du*k_uv + xu_mid)
        new_v.append(dv*k_uv + yv_mid)

        i += 1
    
    new_x = np.array(new_x)
    new_y = np.array(new_y)
    new_u = np.array(new_u)
    new_v = np.array(new_v)
    
    return new_x, new_y, new_u, new_v


def get_cutspeed(length_xy, length_uv, z_xy, z_uv, z_mach, cut_speed, cut_speed_def_value):
    z_work_mid = (z_mach - z_xy - z_uv)/2.0 + z_xy
    l_xy_work = np.abs(z_work_mid - z_xy)
    l_uv_work = np.abs((z_mach - z_uv) - z_work_mid)
    l_xy_mach = np.abs(z_work_mid)
    l_uv_mach = np.abs(z_mach - z_work_mid)
    
    if l_xy_work == 0 or l_uv_work == 0:
        k_xy = 1.0
        k_uv = 1.0        
    else:
        k_xy = l_xy_mach/ l_xy_work
        k_uv = l_uv_mach/ l_uv_work
           
    length_mid = (length_xy + length_uv)/ 2.0
    dl_XY = length_xy - length_mid
    dl_UV = length_uv - length_mid
    
    length_XY_Mech = k_xy*dl_XY + length_mid
    length_UV_Mech = k_uv*dl_UV + length_mid

    if cut_speed_def_value == "XY(Mech)":
        length_def = length_XY_Mech
    elif cut_speed_def_value == "XY(Work)":
        length_def = length_xy
    elif cut_speed_def_value == "Center":
        length_def = length_mid
    elif cut_speed_def_value == "UV(Work)":
        length_def = length_uv
    else: # cut_speed_def_value == "UV(Mech)"
        length_def = length_UV_Mech
    
    ratio_XY_Mech = length_XY_Mech/length_def
    ratio_XY_Work = length_xy/length_def
    ratio_mid = length_uv/length_def
    ratio_UV_Work = length_uv/length_def
    ratio_UV_Mech = length_UV_Mech/length_def
  
    cs_xy_mech = cut_speed*ratio_XY_Mech
    cs_xy_work = cut_speed*ratio_XY_Work
    cs_mid = cut_speed*ratio_mid
    cs_uv_work = cut_speed*ratio_UV_Work
    cs_uv_mech = cut_speed*ratio_UV_Mech
    
    return cs_xy_mech, cs_xy_work, cs_mid, cs_uv_work, cs_uv_mech



def set_cut_speed(dxf_obj0, dxf_obj1, xy_dist_entry, uv_dist_entry, mach_dist_entry, cut_speed_entry, cut_speed_def_cb):
    xy_dist_value = xy_dist_entry.get()
    uv_dist_value = uv_dist_entry.get()
    mach_dist_value = mach_dist_entry.get()
    cut_speed_value = cut_speed_entry.get()   
    cut_speed_def_value = cut_speed_def_cb.get()    

    all_items0 = dxf_obj0.get_item(all=True)
    all_items1 = dxf_obj1.get_item(all=True)
    
    try:
        z_xy = float(xy_dist_value)
        z_uv = float(uv_dist_value)
        z_mach = float(mach_dist_value)
        cut_speed = float(cut_speed_value)
                    
        if len(all_items0) == len(all_items1):
            i = 0
            while i < len(all_items0):
                line0 = dxf_obj0.line_list[i]
                line1 = dxf_obj1.line_list[i]
                
                line0_length = line0.get_length()
                line1_length = line1.get_length()
                
                cs_xy_mech, cs_xy_work, cs_mid, cs_uv_work, cs_uv_mech = \
                    get_cutspeed(line0_length, line1_length, z_xy, z_uv, z_mach, \
                                             cut_speed, cut_speed_def_value)
                
                line0.set_cutspeed(cs_xy_work, cs_xy_mech)
                line1.set_cutspeed(cs_uv_work, cs_uv_mech)
                i += 1

        else:
            for line0 in dxf_obj0.line_list:
                line0.set_cutspeed(cut_speed, cut_speed)
                
            for line1 in dxf_obj1.line_list:
                line1.set_cutspeed(cut_speed, cut_speed)
                
        dxf_obj0.update()
        dxf_obj1.update()
    
            
    except:
        traceback.print_exc()
        output_log(traceback.format_exc())



def set_offset_dist_from_function(dxf_obj0, dxf_obj1, xy_dist_entry, uv_dist_entry, mach_dist_entry, cut_speed_entry, cut_speed_def_cb, offset_function, is_remove_collision, messeage_window):
    xy_dist_value = xy_dist_entry.get()
    uv_dist_value = uv_dist_entry.get()
    mach_dist_value = mach_dist_entry.get()
    cut_speed_value = cut_speed_entry.get()   
    cut_speed_def_value = cut_speed_def_cb.get()
        
    all_items0 = dxf_obj0.get_item(all=True)
    all_items1 = dxf_obj1.get_item(all=True)

    try:
        z_xy = float(xy_dist_value)
        z_uv = float(uv_dist_value)
        z_mach = float(mach_dist_value)
        cut_speed = float(cut_speed_value)
                    
        if len(all_items0) == len(all_items1):
            i = 0
            while i < len(all_items0):

                line0 = dxf_obj0.line_list[i]
                line1 = dxf_obj1.line_list[i]
                
                line0_length = line0.get_length()
                line1_length = line1.get_length()
                
                cs_xy_mech, cs_xy_work, cs_mid, cs_uv_work, cs_uv_mech = \
                    get_cutspeed(line0_length, line1_length, z_xy, z_uv, z_mach, \
                                             cut_speed, cut_speed_def_value)
                offset_XY_Work = offset_function(cs_xy_work)
                offset_UV_Work = offset_function(cs_uv_work)
                line0.set_offset_dist(offset_XY_Work)
                line1.set_offset_dist(offset_UV_Work)
                
                line0.set_cutspeed(cs_xy_work, cs_xy_mech)
                line1.set_cutspeed(cs_uv_work, cs_uv_mech)
                
                i += 1
            
            if is_remove_collision.get():
                remove_collision(dxf_obj0, "XY面", messeage_window)
                remove_collision(dxf_obj1, "UV面", messeage_window)   
                
            dxf_obj0.update()
            dxf_obj1.update()
                
            messeage_window.set_messeage("オフセット値を更新しました。\n")
        else:
            messeage_window.set_messeage("XY座標とUV座標でライン数が一致しません。XY：%s本，UV：%s本\n"%(len(all_items0),len(all_items1)))

    except:
        traceback.print_exc()
        output_log(traceback.format_exc())
        messeage_window.set_messeage("入力値に誤りがあります。オフセット値更新を中止しました。\n")

# Ver2.1変更　引数追加，距離別指定可能
def gen_g_code(dxf_obj0, dxf_obj1, entry_ox, entry_oy, entry_ex, entry_ey, xy_dist_entry, uv_dist_entry, mach_dist_entry, cut_speed_entry, \
               cut_speed_def_cb, cb_CncCSDef, entry_dl, messeage_window, config):
    set_cut_speed(dxf_obj0, dxf_obj1, xy_dist_entry, uv_dist_entry, mach_dist_entry, cut_speed_entry, cut_speed_def_cb)
    
    entry_ox_value = entry_ox.get()
    entry_oy_value = entry_oy.get()
    entry_ex_value = entry_ex.get()
    entry_ey_value = entry_ey.get()
    xy_dist_value = xy_dist_entry.get()
    uv_dist_value = uv_dist_entry.get()
    mach_dist_value = mach_dist_entry.get()
    entry_dl_value = entry_dl.get()
    cut_speed_value = cut_speed_entry.get()
    CncCsdDef = cb_CncCSDef.get()
    
    code_line_list = []
    code_line_list.append(config.HEADER)
    
    try:
        temp_error_flg = False
        
        ox = float(entry_ox_value)
        oy = float(entry_oy_value)
        ex = float(entry_ex_value)
        ey = float(entry_ey_value)
        z_xy = float(xy_dist_value)
        z_uv = float(uv_dist_value)
        z_mach = float(mach_dist_value)
        dl = float(entry_dl_value)
        CS = float(cut_speed_value)

        if z_xy > z_mach:
            messeage_window.set_messeage("【警告】\nXY面距離が駆動面距離に対して%s mm 長いです。\n入力値を確認してください。\n\n"%(z_xy - z_mach))
            temp_error_flg = True
        if z_uv > z_mach:
            messeage_window.set_messeage("【警告】\nUV面距離が駆動面距離に対して%s mm 長いです。\n入力値を確認してください。\n\n"%(z_uv - z_mach))
            temp_error_flg = True
       
        if dl < 0.1:
            dl = 0.1
            
        #Ver2.0　変更 Gコード出力形式
        code_line_list.append("G00 X%f Y%f U%f V%f\n"%(ox, oy, ox, oy))
        
        all_items0 = dxf_obj0.get_item(all=True)
        all_items1 = dxf_obj1.get_item(all=True)
        
        x_array = np.array([ox])
        y_array = np.array([oy])
        u_array = np.array([ox])
        v_array = np.array([oy])
        
        x0 = ox
        y0 = oy
        u0 = ox
        v0 = oy
        
        xy_offset_dist = []
        uv_offset_dist = []
        
        if temp_error_flg == False:
            if len(all_items0) == len(all_items1):
                i = 0
                while i < len(all_items1):
                    line0 = dxf_obj0.line_list[i]
                    line1 = dxf_obj1.line_list[i]
                    
                    line0_length = line0.get_length()
                    line1_length = line1.get_length()
    
                    xy_offset_dist.append(line0.offset_dist)
                    uv_offset_dist.append(line1.offset_dist)
                    
                    n = int(max(line0_length, line1_length)/ dl)
                    if n < 2:
                        n = 2
                    
                    x, y = generate_arc_length_points(line0, n)
                    u, v = generate_arc_length_points(line1, n)
                    cs_xy = line0.cutspeed_mech
                    cs_uv = line1.cutspeed_mech
                    
                    if (i != 0) and (i != len(all_items0)):
                        # 始点と終点以外は、フィレット補完する
                        if FILET_INTERPOLATE == True:
                            l0_x = [x_array[-2], x_array[-1]]
                            l0_y = [y_array[-2], y_array[-1]]
                            l1_x = [x[0], x[1]]
                            l1_y = [y[0], y[1]]
                            
                            l0_u = [u_array[-2], u_array[-1]]
                            l0_v = [v_array[-2], v_array[-1]]
                            l1_u = [u[0], u[1]]
                            l1_v = [v[0], v[1]]   
                            
                            
                            x_f, y_f = generate_offset_interporate_point(l0_x, l0_y, l1_x, l1_y, xy_offset_dist[-1], xy_offset_dist[-2])
                            u_f, v_f = generate_offset_interporate_point(l0_u, l0_v, l1_u, l1_v, uv_offset_dist[-1], uv_offset_dist[-2])        
                            
                            if (not(len(x_f) == 0)) and (not(len(u_f) == 0)):
                                #オフセット面の作成
                                x_m_f, y_m_f, u_m_f, v_m_f = make_offset_path(x_f, y_f, u_f, v_f, z_xy, z_uv, z_mach)
                                code_line_list.append(gen_g_code_line_str(x_m_f, y_m_f, u_m_f, v_m_f, x0, y0, u0, v0, cs_xy, cs_uv, CncCsdDef))
                                x0 = x_m_f[-1]
                                y0 = y_m_f[-1]
                                u0 = u_m_f[-1]
                                v0 = v_m_f[-1]
                            
                                x_array = np.concatenate([x_array, x_f], 0)
                                y_array = np.concatenate([y_array, y_f], 0)
                                u_array = np.concatenate([u_array, u_f], 0)
                                v_array = np.concatenate([v_array, v_f], 0)      
                            else:
                                x[0] = x_array[-1]
                                y[0] = y_array[-1]
                                u[0] = u_array[-1]
                                v[0] = v_array[-1]                                     
                        
                    #オフセット面の作成
                    x_m, y_m, u_m, v_m = make_offset_path(x, y, u, v, z_xy, z_uv, z_mach)
                    code_line_list.append(gen_g_code_line_str(x_m, y_m, u_m, v_m, x0, y0, u0, v0, cs_xy, cs_uv, CncCsdDef))
                    x0 = x_m[-1]
                    y0 = y_m[-1]
                    u0 = u_m[-1]
                    v0 = v_m[-1]                    
                    
                    x_array = np.concatenate([x_array, x], 0)
                    y_array = np.concatenate([y_array, y], 0)
                    u_array = np.concatenate([u_array, u], 0)
                    v_array = np.concatenate([v_array, v], 0)
                    
                    i += 1
                #Ver2.0　変更 Gコード出力形式
                code_line_list.append(gen_g_code_line_str([ex], [ey], [ex], [ey], x0, y0, u0, v0, cs_xy, cs_uv, CncCsdDef))
                
                replaced_code_line_list = []
                for g_code_str in code_line_list:
                    replaced_code_line_list.append(replace_g_code(g_code_str, config.X_STR, config.Y_STR, config.U_STR, config.V_STR))
                
                line = ""
                for elem in replaced_code_line_list:
                    line += elem
                line += "M02"
                
                
                dt_now = datetime.datetime.now()
                
                time_str = dt_now.strftime('%Y%m%d_%H%M%S')
                
                name0 = os.path.splitext(os.path.basename(dxf_obj0.filename))[0]
                name1 = os.path.splitext(os.path.basename(dxf_obj1.filename))[0]
                
                Output_FileName = "%s,%s,%s_%s.nc"%(name0, name1, CS, time_str)
                
                f = open(Output_FileName,'w')
                f.write(line)
                f.close()
                
                messeage_window.set_messeage("Gコード生成成功。%sで保存しました。\n"%Output_FileName)
            
            else:
                messeage_window.set_messeage("XY座標とUV座標でライン数が一致しません。XY：%s本，UV：%s本\n"%(len(all_items0),len(all_items1)))
        if temp_error_flg == True:
            messeage_window.set_messeage("入力値に誤りがあります。Gコード生成を中止しました。\n\n")
    except:
        traceback.print_exc()
        output_log(traceback.format_exc())
        messeage_window.set_messeage("Gコード生成途中でエラーが発生しました。\n\n")
        pass


def path_chk(Root, dxf_obj0, dxf_obj1, entry_ox, entry_oy, entry_ex, entry_ey, \
             xy_dist_entry, uv_dist_entry, mach_dist_entry, entry_dl, use3dValue, messeage_window):
    is_plot_3d = use3dValue.get()
    
    
    fig = Figure(figsize=(15, 8), dpi=70)
    plot_window = tk.Toplevel(Root)
    plot_window.wm_title("Cut Path")
    plot_window.geometry("1500x800")
    canvas = FigureCanvasTkAgg(fig, master = plot_window)
    toolbar = NavigationToolbar2Tk(canvas, plot_window)
    toolbar.update()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)    

    if is_plot_3d == True:
        ax = fig.add_subplot(111, projection="3d", proj_type = 'ortho')
    else:
        ax = fig.add_subplot(111)
    
    entry_ox_value = entry_ox.get()
    entry_oy_value = entry_oy.get()
    entry_ex_value = entry_ex.get()
    entry_ey_value = entry_ey.get()    
    entry_dl_value = entry_dl.get()
    xy_dist_value = xy_dist_entry.get()
    uv_dist_value = uv_dist_entry.get()
    mach_dist_value = mach_dist_entry.get()
    
    try:
        ox = float(entry_ox_value)
        oy = float(entry_oy_value)
        ex = float(entry_ex_value)
        ey = float(entry_ey_value)
        dl = float(entry_dl_value)
        z_xy = float(xy_dist_value)
        z_uv = float(uv_dist_value)
        z_mach = float(mach_dist_value)
        
        x_array = np.array([ox])
        y_array = np.array([oy])
        u_array = np.array([ox])
        v_array = np.array([oy])
        length_sum = 0
        
        xy_offset_dist = []
        uv_offset_dist = []
        
        if dl < 0.1:
            dl = 0.1
        
        all_items0 = dxf_obj0.get_item(all=True)
        all_items1 = dxf_obj1.get_item(all=True)
        
        if len(all_items0) == len(all_items1):
            i = 0
            while i < len(all_items0):

                line0 = dxf_obj0.line_list[i]
                line1 = dxf_obj1.line_list[i]
                
                line0_length = line0.get_length()
                line1_length = line1.get_length()
                
                length_sum += (line0_length + line1_length)/2.0
                
                xy_offset_dist.append(line0.offset_dist)
                uv_offset_dist.append(line1.offset_dist)
                
                n = int(max(line0_length, line1_length)/ dl)
                if n < 2:
                    n = 2
                
                x, y = generate_arc_length_points(line0, n)
                u, v = generate_arc_length_points(line1, n)
                
                if (i != 0) and (i != len(all_items0)):
                    if FILET_INTERPOLATE == True:
                        # 始点と終点以外は、フィレット補完する
                        l0_x = [x_array[-2], x_array[-1]]
                        l0_y = [y_array[-2], y_array[-1]]
                        l1_x = [x[0], x[1]]
                        l1_y = [y[0], y[1]]
                        
                        l0_u = [u_array[-2], u_array[-1]]
                        l0_v = [v_array[-2], v_array[-1]]
                        l1_u = [u[0], u[1]]
                        l1_v = [v[0], v[1]]   
                        
                        x_f, y_f = generate_offset_interporate_point(l0_x, l0_y, l1_x, l1_y, xy_offset_dist[-1], xy_offset_dist[-2])
                        u_f, v_f = generate_offset_interporate_point(l0_u, l0_v, l1_u, l1_v, uv_offset_dist[-1], uv_offset_dist[-2])
                        
                        if (not(len(x_f) == 0)) and (not(len(u_f) == 0)):
                            x_array = np.concatenate([x_array, x_f], 0)
                            y_array = np.concatenate([y_array, y_f], 0)
                            u_array = np.concatenate([u_array, u_f], 0)
                            v_array = np.concatenate([v_array, v_f], 0)    
                        else:
                            x[0] = x_array[-1]
                            y[0] = y_array[-1]
                            u[0] = u_array[-1]
                            v[0] = v_array[-1]                    
                else:
                    norm_line2line0 = norm(x_array[-1], y_array[-1], x[0], y[0])
                    norm_line2line1 = norm(u_array[-1], v_array[-1], u[0], v[0])
                    
                    if norm_line2line0 > dl  or  norm_line2line1 > dl:
                        n_interp_line2line = int(max(norm_line2line0, norm_line2line1) / dl)
                        
                        if n_interp_line2line < 2:
                            n_interp_line2line = 2
                        
                        xp, yp = refine_line([x_array[-1], x[0]],  [y_array[-1], y[0]], n_interp_line2line)
                        up, vp = refine_line([u_array[-1], u[0]],  [v_array[-1], v[0]], n_interp_line2line)
                        x_array = np.concatenate([x_array, xp], 0)
                        y_array = np.concatenate([y_array, yp], 0)
                        u_array = np.concatenate([u_array, up], 0)
                        v_array = np.concatenate([v_array, vp], 0)
                    
                
                x_array = np.concatenate([x_array, x], 0)
                y_array = np.concatenate([y_array, y], 0)
                u_array = np.concatenate([u_array, u], 0)
                v_array = np.concatenate([v_array, v], 0)
                
                i += 1
            
            norm_line2line0 = norm(x_array[-1], y_array[-1], ex, ey)
            norm_line2line1 = norm(u_array[-1], v_array[-1], ex, ey)
            
            if norm_line2line0 > dl  or  norm_line2line1 > dl:
                n_interp_line2line = int(max(norm_line2line0, norm_line2line1) / dl)
                
                if n_interp_line2line < 2:
                    n_interp_line2line = 2
                
                xp, yp = refine_line([x_array[-1], ex], [y_array[-1], ey], n_interp_line2line)
                up, vp = refine_line([u_array[-1], ex], [v_array[-1], ey], n_interp_line2line)
                x_array = np.concatenate([x_array, xp], 0)
                y_array = np.concatenate([y_array, yp], 0)
                u_array = np.concatenate([u_array, up], 0)
                v_array = np.concatenate([v_array, vp], 0)
            
            #オフセット面の作成
            x_m_array, y_m_array, u_m_array, v_m_array = make_offset_path(x_array, y_array, u_array, v_array, z_xy, z_uv, z_mach)
            
            
            if is_plot_3d == True:
                point_dist_array = calc_point_dist(x_m_array, y_m_array, u_m_array, v_m_array, 0, z_mach)
                
                
                ax.plot(x_array, y_array, np.ones(len(x_array))*z_xy, 'k')
                ax.plot(u_array, v_array, np.ones(len(x_array))*(z_mach-z_uv), 'k')
                ax.plot(x_m_array, y_m_array, np.ones(len(x_array))*0, 'k')
                ax.plot(u_m_array, v_m_array, np.ones(len(x_array))*z_mach, 'k')
                
                
                num_per_plot = int(len(x_array) / length_sum * DIST_CUTPATH_PLOT)
                num_plot = int(len(x_array)/num_per_plot) + 1
                
                if num_per_plot < 1:
                    num_per_plot = 1
                
                def update(frame):
                    plot_3d_cut_path(ax, x_array, y_array, u_array, v_array, x_m_array, y_m_array, u_m_array, v_m_array, z_xy, z_uv, z_mach, num_per_plot, frame)
                
                
                x_max = max(max(x_array), max(u_array))
                x_min = min(min(x_array), min(u_array))
                y_max = max(max(y_array), max(v_array))
                y_min = min(min(y_array), min(v_array))
                
                z_max = z_mach
                z_min = 0.0
                
                max_range = max(np.array([x_max - x_min, y_max - y_min]))*0.5
                mid_x = (x_max + x_min) * 0.5
                mid_y = (y_max + y_min) * 0.5
                mid_z = (z_max + z_min) * 0.5
                ax.set_xlim(mid_x - max_range, mid_x + max_range)
                ax.set_ylim(mid_y - max_range, mid_y + max_range)
                ax.set_zlim(mid_z - max_range, mid_z + max_range)
                
                ax.view_init(elev=87, azim=66, roll = 154) 
                
                anim = FuncAnimation(fig, update, frames=num_plot, interval=100, repeat=False)
                canvas.draw()
                #anim.save('anim.gif', writer="imagemagick")
            else:
                point_dist_array = calc_point_dist(x_m_array, y_m_array, u_m_array, v_m_array, 0, z_mach)
                ax.plot(x_m_array, y_m_array, "b", label = "XY Mech Path")
                ax.plot(u_m_array, v_m_array, "r", label = "UV Mech Path")
                ax.plot(x_array, y_array, "b--", label = "XY Work Path")
                ax.plot(u_array, v_array, "r--", label = "UV Work Path")
                ax.set_aspect('equal')
                ax.legend()
            
            
            
            messeage_window.set_messeage("パスを描画しました。ワイヤーの最大長は%s mmです。（初期長%s mm）\n"%(int(max(point_dist_array)), int(z_mach)))
            messeage_window.set_messeage("\n【加工範囲】 \nX: %smm～%smm\nY: %smm～%smm\nU: %smm～%smm\nV: %smm～%smm\n\n"
                                         %(int(min(x_array)), int(max(x_array)), int(min(y_array)), int(max(y_array)), int(min(u_array)), int(max(u_array)), int(min(v_array)), int(max(v_array))))

            if z_xy > z_mach:
                messeage_window.set_messeage("【警告】\nXY面距離が駆動面距離に対して%s mm 長いです。\n入力値を確認してください。\n\n"%(z_xy - z_mach))
            if z_uv > z_mach:
                messeage_window.set_messeage("【警告】\nUV面距離が駆動面距離に対して%s mm 長いです。\n入力値を確認してください。\n\n"%(z_uv - z_mach))
            
        else:
            messeage_window.set_messeage("XY座標とUV座標でライン数が一致しません。XY：%s本，UV：%s本\n"%(len(all_items0), len(all_items1)))
        
    except:
        traceback.print_exc()
        output_log(traceback.format_exc())
        messeage_window.set_messeage("パスチェック中にエラーが発生しました。\n")
        pass      


def _destroyWindow():
    root.quit()
    root.destroy()


def offset_origin(dxf_obj0, dxf_obj1, entry_offset_ox, entry_offset_oy, messeage_window):
    offset_ox = entry_offset_ox.get()
    offset_oy = entry_offset_oy.get()
    
    try :
        offset_ox = float(offset_ox)
        offset_oy = float(offset_oy)
        if (len(dxf_obj0.line_list) == 0) or (len(dxf_obj1.line_list) == 0):
            messeage_window.set_messeage("XY, UV面の両方に図形を読み込んでください。\n")  
        else:
            dxf_obj0.offset_origin(offset_ox, offset_oy)
            dxf_obj1.offset_origin(offset_ox, offset_oy)
            dxf_obj0.update(keep_view = False)
            dxf_obj1.update(keep_view = False)
            messeage_window.set_messeage("XY,UV座標をX:%s, Y:%sオフセットしました。\n"%(offset_ox, offset_oy))
    except:
        traceback.print_exc()
        output_log(traceback.format_exc())
        messeage_window.set_messeage("全体オフセットに数値以外が設定されています。\n")


def rotate_origin(dxf_obj0, dxf_obj1, rotate_entry, messeage_window):
    sita = rotate_entry.get()
    
    try:
        sita = np.radians(float(sita))
        
        if (len(dxf_obj0.line_list) == 0) or (len(dxf_obj1.line_list) == 0):
            messeage_window.set_messeage("XY, UV面の両方に図形を読み込んでください。\n")  
        else:
            cg_x0, cg_y0 = dxf_obj0.get_cg()
            cg_x1, cg_y1 = dxf_obj1.get_cg()
            rx = (cg_x0 + cg_x1)/2
            ry = (cg_y0 + cg_y1)/2
            dxf_obj0.rotate(sita, rx, ry)
            dxf_obj1.rotate(sita, rx, ry)
            dxf_obj0.update(keep_view = False)
            dxf_obj1.update(keep_view = False)
            messeage_window.set_messeage("重心(%s, %s)を回転中心として、元の図形を%s deg回転しました。\n"\
                                         %(format(rx,'.1f'), format(ry,'.1f'), format(np.degrees(sita),'.1f'))) 
        
    except:
        traceback.print_exc()
        output_log(traceback.format_exc())
        messeage_window.set_messeage("回転値に数値以外が設定されています。\n")    



#======================================================================================================================================
#            メイン関数
#======================================================================================================================================


if __name__ == "__main__":


    #======================================================================================================================================
    #            config.csvファイルの読込
    #======================================================================================================================================

    curdir =  get_curdir()
    config = Config()
    config.load_config("%s\\config.csv"%curdir)
    config_read_messeage = config.MESSEAGE
    config.load_offset_func("%s\\offset_function.csv"%curdir)
    offset_function_read_messeage = config.MESSEAGE
    
    #======================================================================================================================================
    #            rootインスタンスの生成
    #======================================================================================================================================
    
    #【メインウィンドウ】
    root = tk.Tk()                                                   #メインウィンドウの枠となるインスタンス
    root.title("HotwireDXF CAM ver%s"%VERSION)                       #メインウィンドウの名称
    root.geometry("1700x950")                                        #メインウィンドウのサイズ（単位：pixcel）
    root.protocol('WM_DELETE_WINDOW', _destroyWindow)                #メインウィンドウを閉じたときにインスタンスを破棄する処理
    style = ttk.Style()
    style.theme_use('clam')


    #======================================================================================================================================
    #          canvasインスタンスの生成
    #======================================================================================================================================

    #【X-Y グラフ】
    fig0 = plt.Figure(dpi=100, figsize=(8,4.05))                     #XYグラフの枠となるインスタンス．XYグラフは0番とする．figsize（単位：インチ）      
    ax0 = fig0.add_subplot(1,1,1)                                    #XYグラフにプロットエリア(ax0)を追加   
    canvas0 = FigureCanvasTkAgg(fig0, master=root)                   #XYグラフをメインウィンドウのインスタンスに埋め込み
    canvas0.get_tk_widget().place(x = 20, y = 20)                    #XYグラフを配置
    
    toolbarFrame0 = tk.Frame(master=root)                            #XYグラフにツールバーを追加．ツールバーはmatplotlibにより提供されているもの
    toolbar0 = NavigationToolbar2Tk(canvas0, toolbarFrame0)          #ツールバーをグラフとリンク
    toolbar0.update()                                                #ツールバーを更新
    toolbarFrame0.place(x = 320, y = 430)                            #ツールバーを配置
    
    
    #【U-V グラフ】
    fig1 = plt.Figure(dpi=100, figsize=(8,4.05))                     #UVグラフの枠となるインスタンス．UVグラフは1番とする．figsize（単位：インチ）  
    ax1 = fig1.add_subplot(1,1,1)                                    #UVグラフにプロットエリア(ax1)を追加   
    canvas1 = FigureCanvasTkAgg(fig1, master=root)                   #UVグラフをメインウィンドウのインスタンスに埋め込み
    canvas1.get_tk_widget().place(x = 20, y = 480)                   #UVグラフを配置  
    
    toolbarFrame1 = tk.Frame(master=root)                            #UVグラフにツールバーを追加．ツールバーはmatplotlibにより提供されているもの
    toolbar1 = NavigationToolbar2Tk(canvas1, toolbarFrame1)          #ツールバーをグラフとリンク
    toolbar1.update()                                                #ツールバーを更新
    toolbarFrame1.place(x = 320, y = 890)                            #ツールバーを配置
    

    #======================================================================================================================================
    #          SuperTableインスタンスの生成
    #======================================================================================================================================
   
    #【X-Y ラインテーブル】
    table0 = SuperTable(root, y_height = 15, x = 850,y = 100)       #XYテーブルの枠となるインスタンスを生成
    table0_label = tk.Label(root, text="X-Y",font=("",20))          #XYテーブル用のテキスト
    table0_label.place(x = 860, y = 40)                             #XYテーブル用のテキストを配置

    
    #【U-V ラインテーブル】
    table1 = SuperTable(root, y_height = 15, x = 1250,y = 100)      #UVテーブルの枠となるインスタンスを生成
    table1_label = tk.Label(root, text="U-V",font=("",20))          #UVテーブル用のテキスト
    table1_label.place(x = 1260, y = 40)                            #UVテーブル用のテキストを配置  


    #======================================================================================================================================
    #          DxfFileインスタンスの生成
    #======================================================================================================================================

    #【dxfファイルを格納するクラス（DxfFile) のインスタンスを生成】
    dxf0 = DxfFile(ax0, canvas0, table0, table1, "X-Y")
    dxf1 = DxfFile(ax1, canvas1, table1, table0, "U-V")

    canvas0.mpl_connect('pick_event', dxf0.get_selected_point)
    canvas1.mpl_connect('pick_event', dxf1.get_selected_point)

    #======================================================================================================================================
    #      messeage_windowインスタンスの生成
    #======================================================================================================================================
    
    #Ver2.0 位置変更(下に40pix)
    #【メッセージウィンドウ】
    message_window = messeage_window(root, width=110, height = 9)
    message_window.place(x = 852, y = 805)
    message_window_label = tk.Label(root, text="メッセージウィンドウ",font=("",12))
    message_window_label.place(x = 860, y = 780)
    message_window.set_messeage(config_read_messeage)
    message_window.set_messeage(offset_function_read_messeage)
    message_window.set_messeage("Gコードの書き出しは「%s」です。\n"%config.HEADER)

    #======================================================================================================================================
    #           entryインスタンスの生成
    #======================================================================================================================================

    #【X-Y用 dxfファイル名の入力コンソール】
    filename_entry0 = tk.Entry(root, width=50) 
    filename_entry0.insert(tk.END, config.FILENAME_XY) 
    filename_entry0.place(x = 852, y = 75)
    
    
    #【U-V用 dxfファイル名の入力コンソール】
    filename_entry1 = tk.Entry(root, width=50) 
    filename_entry1.insert(tk.END, config.FILENAME_UV)   
    filename_entry1.place(x = 1252, y = 75) 


    #【X-Y用オフセット距離の入力コンソール】
    offset_dist_label0 = tk.Label(root, text="オフセット量[mm]",font=("",10))
    offset_dist_label0.place(x = 875, y = 498)
    offset_dist_entry0 = tk.Entry(root, width=14, justify=tk.RIGHT,font=("",12)) 
    offset_dist_entry0.insert(tk.END, config.XY_OFFSET_DIST)   
    offset_dist_entry0.place(x = 990, y = 495) 


    #【U-V用オフセット距離の入力コンソール】
    offset_dist_label1 = tk.Label(root, text="オフセット量[mm]",font=("",10))
    offset_dist_label1.place(x = 1275, y = 498)
    offset_dist_entry1 = tk.Entry(root, width=14, justify=tk.RIGHT,font=("",12)) 
    offset_dist_entry1.insert(tk.END, config.UV_OFFSET_DIST)   
    offset_dist_entry1.place(x = 1390, y = 495) 


    #【オフセット関数ファイル名の入力コンソール】
    offset_func_label = tk.Label(root, text="溶け量ファイル",font=("",12))
    offset_func_label.place(x = 850, y = 535)
    offset_func_entry = tk.Entry(root, width=36) 
    offset_func_entry.insert(tk.END, "offset_function.csv")   
    offset_func_entry.place(x = 970, y = 535) 
    

    #【configファイル名の入力コンソール】
    config_file_label = tk.Label(root, text="設定ファイル",font=("",12))
    config_file_label.place(x = 850, y = 575)
    config_file_entry = tk.Entry(root, width=36) 
    config_file_entry.insert(tk.END, "config.csv") 
    config_file_entry.place(x = 970, y = 575)
    
    
    
    #【原点オフセット入力コンソール】
    origin_offset_label0 = tk.Label(root, text="オフセット",font=("",12))
    origin_offset_label0.place(x = 850, y = 610)
    origin_offset_label1 = tk.Label(root, text="X：",font=("",12))
    origin_offset_label1.place(x = 970, y = 610)
    origin_offset_label2 = tk.Label(root, text="Y：",font=("",12))
    origin_offset_label2.place(x = 1070, y = 610)
    origin_offset_entry_x = tk.Entry(root, width=8,font=("",12)) 
    origin_offset_entry_x.insert(tk.END, config.OFFSET_X)       
    origin_offset_entry_x.place(x = 1000, y = 610)   
    origin_offset_entry_y = tk.Entry(root, width=8,font=("",12))     
    origin_offset_entry_y.insert(tk.END, config.OFFSET_Y)
    origin_offset_entry_y.place(x = 1100, y = 610)    



    #【全体回転入力コンソール】
    rotate_label = tk.Label(root, text="回転：",font=("",12))
    rotate_label.place(x = 1300, y = 610)
    rotate_entry = tk.Entry(root, width=8,font=("",12)) 
    rotate_entry.insert(tk.END, config.ROTATE)       
    rotate_entry.place(x = 1350, y = 610)


    #【切り出し原点入力コンソール】
    cut_start_label0 = tk.Label(root, text="切り出し始点",font=("",12))
    cut_start_label0.place(x = 850, y = 645)
    cut_start_label1 = tk.Label(root, text="X：",font=("",12))
    cut_start_label1.place(x = 970, y = 645)
    cut_start_label2 = tk.Label(root, text="Y：",font=("",12))
    cut_start_label2.place(x = 1070, y = 645)
    cut_start_entry_x = tk.Entry(root, width=8,font=("",12)) 
    cut_start_entry_x.insert(tk.END, config.OX)       
    cut_start_entry_x.place(x = 1000, y = 645)   
    cut_start_entry_y = tk.Entry(root, width=8,font=("",12))     
    cut_start_entry_y.insert(tk.END, config.OY)
    cut_start_entry_y.place(x = 1100, y = 645)


    #【切り出し終点入力コンソール】
    cut_end_label0 = tk.Label(root, text="切り出し終点",font=("",12))
    cut_end_label0.place(x = 1200, y = 645)
    cut_end_label1 = tk.Label(root, text="X：",font=("",12))
    cut_end_label1.place(x = 1320, y = 645)
    cut_end_label2 = tk.Label(root, text="Y：",font=("",12))
    cut_end_label2.place(x = 1420, y = 645)
    cut_end_entry_x = tk.Entry(root, width=8,font=("",12)) 
    cut_end_entry_x.insert(tk.END, config.EX)
    cut_end_entry_x.place(x = 1350, y = 645)   
    cut_end_entry_y = tk.Entry(root, width=8,font=("",12))     
    cut_end_entry_y.insert(tk.END, config.EY)
    cut_end_entry_y.place(x = 1450, y = 645) 


    #【分割距離入力コンソール】
    dl_label = tk.Label(root, text="分割距離[mm]",font=("",12))
    dl_label.place(x = 1150, y = 680)
    dl_entry = tk.Entry(root, width=8,font=("",12))     
    dl_entry.insert(tk.END, config.DELTA_LENGTH)
    dl_entry.place(x = 1300, y = 680)       


    #【カット速度入力コンソール】   
    cut_speed_label = tk.Label(root, text="カット速度[mm/分]",font=("",12))
    cut_speed_label.place(x = 850, y = 680)
    cut_speed_entry = tk.Entry(root, width=8,font=("",12))     
    cut_speed_entry.insert(tk.END, config.CUTSPEED)
    cut_speed_entry.place(x = 1000, y = 680)    


    #【カット速度定義面入力コンボボックス】   
    cut_speed_def_label = tk.Label(root, text="カット速度定義面",font=("",12))
    cut_speed_def_label.place(x = 850, y = 705) 
    cut_speed_def_list = ("XY(Mech)", "XY(Work)", "Center", "UV(Work)", "UV(Mech)")
    cut_speed_def_cb = ttk.Combobox(root, textvariable= tk.StringVar(), width = 15,\
                                 values=cut_speed_def_list, style="office.TCombobox")
    
    if config.CS_DEF in cut_speed_def_list:
        cut_speed_def_cb.set(config.CS_DEF)
    else:
        cut_speed_def_cb.set("Center")
    cut_speed_def_cb.bind(
        '<<ComboboxSelected>>', 
        lambda e: set_cut_speed(dxf0, dxf1, xy_dist_entry, uv_dist_entry, mech_dist_entry,\
                       cut_speed_entry, cut_speed_def_cb))
    cut_speed_def_cb.place(x = 1000, y = 705) 
    

    #【CNC速度定義入力コンボボックス】
    cnc_speed_def_label = tk.Label(root, text="CNC速度定義",font=("",12))
    cnc_speed_def_label.place(x = 1150, y = 705)
    cnc_speed_def_list = ("XY", "UV", "XYU", "XYV", "Faster" ,"InvertTime")
    cnc_speed_def_cb = ttk.Combobox(root, textvariable= tk.StringVar(), width = 15,\
                                 values=cnc_speed_def_list, style="office.TCombobox")
    if config.CNC_CS_DEF in cnc_speed_def_list:
        cnc_speed_def_cb.set(config.CNC_CS_DEF)
    else:
        cnc_speed_def_cb.set("XY")
    cnc_speed_def_cb.place(x = 1300, y = 705) 


    # Ver2.1 変更
    #【カット面距離入力コンソール1】   
    xy_dist_label = tk.Label(root, text="XY面距離[mm]",font=("",12))
    xy_dist_label.place(x = 850, y = 740)
    xy_dist_entry = tk.Entry(root, width=8,font=("",12))     
    xy_dist_entry.insert(tk.END, config.XY_DIST)
    xy_dist_entry.place(x = 970, y = 740)  

    # Ver2.1 追加
    #【カット面距離入力コンソール2】   
    uv_dist_label = tk.Label(root, text="UV面距離[mm]",font=("",12))
    uv_dist_label.place(x = 1070, y = 740)
    uv_dist_entry = tk.Entry(root, width=8,font=("",12))     
    uv_dist_entry.insert(tk.END, config.UV_DIST)
    uv_dist_entry.place(x = 1190, y = 740)

    #Ver2.1 位置変更 
    #【マシン距離入力コンソール】   
    mech_dist_label = tk.Label(root, text="駆動面距離[mm]",font=("",12))
    mech_dist_label.place(x = 1290, y = 740)
    mech_dist_entry = tk.Entry(root, width=8,font=("",12))     
    mech_dist_entry.insert(tk.END, config.MACH_DIST)
    mech_dist_entry.place(x = 1420, y = 740)  


    #======================================================================================================================================
    #            ボタンインスタンスの生成
    #======================================================================================================================================

    #【X-Y用 dxfファイル読込用のエクスプローラーを開くボタン】
    open_btn0 = tk.Button(root, text="開く", command = lambda: open_dxf_explorer(dxf0, filename_entry0, is_spline_refine, message_window))
    open_btn0.place(x=1160, y=70)  

    #【U-V用 dxfファイル読込用のエクスプローラーを開くボタン】   
    open_btn1 = tk.Button(root, text="開く", command = lambda: open_dxf_explorer(dxf1, filename_entry1, is_spline_refine, message_window))
    open_btn1.place(x=1560, y=70)    

    #【X-Y用 dxfファイル名の読込ボタン】
    load_btn0 = tk.Button(root, text="再読込", command = lambda: load_file(dxf0, filename_entry0, is_spline_refine, message_window))
    load_btn0.place(x=1200, y=70)  

    #【U-V用 dxfファイル名の読込ボタン】   
    load_btn1 = tk.Button(root, text="再読込", command = lambda: load_file(dxf1, filename_entry1, is_spline_refine, message_window))
    load_btn1.place(x=1600, y=70)    


    #【X-Y用 オフセット距離反映ボタン】
    offset_btn0 = tk.Button(root, text="オフセット量設定", width = 15, bg='#fffacd', \
                         command = lambda: set_offset_dist(dxf0, offset_dist_entry0, dxf1, offset_dist_entry1, \
                                                          is_xy_uv_link, is_remove_collision, "XY面", "UV面", message_window))
    offset_btn0.place(x=1125, y=492)  


    #【U-V用 オフセット距離反映ボタン】
    offset_btn1 = tk.Button(root, text="オフセット量設定", width = 15, bg='#fffacd', \
                         command = lambda: set_offset_dist(dxf1, offset_dist_entry1, dxf0, offset_dist_entry0, \
                                                          is_xy_uv_link, is_remove_collision, "UV面", "XY面", message_window))
    offset_btn1.place(x=1525, y=492)  


    #【configファイル読込用のエクスプローラーを開くボタン】
    config_load_btn = tk.Button(root, text="開く", command = lambda: load_config(config, config_file_entry, dl_entry,\
                                                                              offset_dist_entry0, offset_dist_entry1, cut_speed_entry,\
                                                                              cut_speed_def_cb, cnc_speed_def_cb, xy_dist_entry, uv_dist_entry,\
                                                                              mech_dist_entry, message_window))
    config_load_btn.place(x=1207, y=570)  

    #【オフセット関数ファイル読込用のエクスプローラーを開くボタン】   
    offset_func_load_btn = tk.Button(root, text="開く", command = lambda: load_offset_func(config, offset_func_entry, message_window))
    offset_func_load_btn.place(x=1207, y=532)    

    #【オフセット値更新ボタン】    
    offset_from_func_btn = tk.Button(root, text = "溶け量ファイルからオフセット量設定", height = 1, width = 34, font=("",10),  bg='#fffacd', \
                          command = lambda: set_offset_dist_from_function(dxf0, dxf1, xy_dist_entry, uv_dist_entry, mech_dist_entry, cut_speed_entry, cut_speed_def_cb,\
                                                                       config.offset_function, is_remove_collision, message_window))
    offset_from_func_btn.place(x = 1255, y = 532)


    #【オフセットボタン】
    origin_offset_btn = tk.Button(root, text="更新", command = lambda: offset_origin(dxf0, dxf1, origin_offset_entry_x, origin_offset_entry_y, message_window))
    origin_offset_btn.place(x=1205, y=607)   

    #【回転ボタン】
    rotate_btn = tk.Button(root, text="更新", command = lambda: rotate_origin(dxf0, dxf1, rotate_entry, message_window))
    rotate_btn.place(x=1450, y=607)   


    #【X-Yラインテーブル用　カット方向入れ替えボタン】
    change_cut_dir_btn0 = tk.Button(root, text="カット方向入替え", width =15, bg = "#3cb371", command = lambda: change_cut_dir(dxf0, dxf1, is_xy_uv_link, "XY面", "UV面", message_window))
    change_cut_dir_btn0.place(x=855, y=435)   
    
    #【X-Yラインテーブル用　ライン整列ボタン】    
    auto_alignment_btn0 = tk.Button(root, text="ライン整列", width =15, bg = "#3cb371", command = lambda: auto_sort_line(dxf0, dxf1, is_xy_uv_link, "XY面", "UV面", message_window))
    auto_alignment_btn0.place(x=990, y=435)
            
    #【X-Yラインテーブル用　カット順逆転ボタン】    
    reverse_line_btn0 = tk.Button(root, text="カット順逆転", width =15, bg = "#3cb371", command = lambda: reverse_line(dxf0, dxf1, is_xy_uv_link, "XY面", "UV面", message_window))
    reverse_line_btn0.place(x=1125, y=435)  
    
    
    #【X-Yラインテーブル用　ライン結合ボタン】
    merge_line_btn0 = tk.Button(root, text="ライン結合", width =15, bg = "#4ba3fb", command = lambda: merge_line(dxf0, dxf1, is_xy_uv_link, is_remove_collision, "XY面", "UV面", message_window))
    merge_line_btn0.place(x=855, y=465) 
    
    #【X-Yラインテーブル用　ライン分割ボタン】    
    separate_line_btn0 = tk.Button(root, text="ライン分割", width = 15, bg = "#b45c04", command = lambda: separate_line(dxf0, is_remove_collision, "XY面", message_window))
    separate_line_btn0.place(x=990, y=465)

    #【X-Yラインテーブル用　ライン削除ボタン】    
    delete_line_btn0 = tk.Button(root, text="ライン削除", width = 15, bg = "#ff6347", command = lambda: delete_line(dxf0, dxf1, is_xy_uv_link, is_remove_collision, "XY面", "UV面", message_window))
    delete_line_btn0.place(x=1125, y=465)
  
  
    #【U-Vラインテーブル用　カット方向入れ替えボタン】    
    change_cut_dir_btn1 = tk.Button(root, text="カット方向入替え", width =15, bg = "#3cb371", command = lambda: change_cut_dir(dxf1, dxf0, is_xy_uv_link, "UV面", "XY面", message_window))
    change_cut_dir_btn1.place(x=1255, y=435)
    
    #【U-Vラインテーブル用　ライン整列ボタン】    
    auto_alignment_btn1 = tk.Button(root, text="ライン整列", width =15, bg = "#3cb371", command = lambda: auto_sort_line(dxf1, dxf0, is_xy_uv_link, "UV面", "XY面", message_window))
    auto_alignment_btn1.place(x=1390, y=435)
    
    #【U-Vラインテーブル用　カット順逆転ボタン】    
    reverse_line_btn1 = tk.Button(root, text="カット順逆転", width =15, bg = "#3cb371", command = lambda: reverse_line(dxf1, dxf0, is_xy_uv_link, "UV面", "XY面", message_window))
    reverse_line_btn1.place(x=1525, y=435)   
    
    #【U-Vラインテーブル用　ライン結合ボタン】    
    merge_line_btn1 = tk.Button(root, text="ライン結合", width = 15, bg = "#4ba3fb" , command = lambda: merge_line(dxf1, dxf0, is_xy_uv_link, is_remove_collision, "UV面", "XY面", message_window))
    merge_line_btn1.place(x=1255, y=465)   
 
    #【U-Vラインテーブル用　ライン分割ボタン】    
    separate_line_btn1 = tk.Button(root, text="ライン分割", width = 15, bg = "#b45c04", command = lambda: separate_line(dxf1, is_remove_collision, "UV面", message_window))
    separate_line_btn1.place(x=1390, y=465) 
    
    #【U-Vラインテーブル用　ライン削除ボタン】    
    delete_line_btn1 = tk.Button(root, text="ライン削除", width = 15, bg = "#ff6347" , command = lambda: delete_line(dxf1, dxf0, is_xy_uv_link, is_remove_collision, "UV面", "XY面", message_window))
    delete_line_btn1.place(x=1525, y=465)
    

    #Ver2.0 変更　WorkDistWntryを追加
    #【パスチェックボタン】    
    path_check_btn = tk.Button(root, text = "パスチェック", height = 2, width = 12,font=("",12), bg='#3cb371', \
                           command = lambda: path_chk(root, dxf0, dxf1, cut_start_entry_x, cut_start_entry_y, cut_end_entry_x, cut_end_entry_y, \
                                                      xy_dist_entry, uv_dist_entry, mech_dist_entry, dl_entry, is_3d_path_check, message_window))
    path_check_btn.place(x = 1530, y = 660)
    

    #Ver2.0 変更　MechDistEntry, WorkDistWntryを追加
    #【Gコード生成ボタン】        
    generate_g_code_btn = tk.Button(root, text = "Gコード生成", height = 2, width = 12,font=("",12), bg='#ff6347', \
                            command = lambda: gen_g_code(dxf0, dxf1, cut_start_entry_x, cut_start_entry_y, cut_end_entry_x, cut_end_entry_y, \
                                                         xy_dist_entry, uv_dist_entry, mech_dist_entry, cut_speed_entry, cut_speed_def_cb, cnc_speed_def_cb, \
                                                         dl_entry, message_window, config))
    generate_g_code_btn.place(x = 1530, y = 720)



    #======================================================================================================================================
    #        Checkbuttonインスタンスの生成
    #======================================================================================================================================

    #【U-V画面とX-Y画面の連動チェックボックス】
    is_xy_uv_link = tk.BooleanVar()
    xy_uv_link_checkbox = tk.Checkbutton(root, text="X-Y画面とU-V画面を連動させる", var=is_xy_uv_link , command =  lambda: xy_uv_link(is_xy_uv_link, table0, table1, message_window))
    xy_uv_link_checkbox.place(x=1490, y=5)

    #【自己交差除去チェックボックス】
    is_remove_collision = tk.BooleanVar()
    is_remove_collision.set(config.REMOVE_COLLISION)
    remove_collision_checkbox = tk.Checkbutton(root, text="自己交差除去有効化", var=is_remove_collision, command =  lambda: enable_remove_self_collision(is_remove_collision, message_window))
    remove_collision_checkbox.place(x=1350, y=5)
    
    #【スプラインをリファインするかどうかのチェックボックス】
    is_spline_refine = tk.BooleanVar()
    is_spline_refine.set(config.REFINE)
    spline_refine_checkbox = tk.Checkbutton(root, text="スプライン点列をリファインする", var=is_spline_refine, command =  lambda: enable_spline_refine(is_spline_refine, message_window))
    spline_refine_checkbox.place(x=1180, y=5)  

    #【パスチェックを3Dで実施するかどうかのチェックボックス】
    is_3d_path_check = tk.BooleanVar()
    path_check_checkbox = tk.Checkbutton(root, text="3Dでパスチェックする", var=is_3d_path_check, command =  lambda: enable_3d_path_check(is_3d_path_check, message_window))
    path_check_checkbox.place(x=1525, y=635)  

    #======================================================================================================================================
    #                 メインループ
    #======================================================================================================================================

    tk.mainloop()
