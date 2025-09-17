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
from matplotlib.figure import Figure
import datetime
import os
import traceback

# 内部ライブラリ
from cam_generic_lib import *
from line_object import *
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
#   X_str           string          G01でのX軸名称
#   Y_str           string          G01でのY軸名称
#   U_str           string          G01でのU軸名称
#   V_str           string          G01でのV軸名称
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


class config:
    def __init__(self):
        self.FILENAME_XY = "ファイル名を入力して下さい。"
        self.FILENAME_UV = "ファイル名を入力して下さい。"
        self.OX = 0.0
        self.OY = 0.0
        self.EX = 0.0
        self.EY = 0.0
        self.DELTA_LENGTH = 1.0
        self.OFFSET_DIST = 0.0
        self.CUTSPEED = 200
        self.XY_DIST = 25.0
        self.UV_DIST = 50.0
        self.WORK_LENGTH = 425
        self.MACH_DIST = 500
        self.HEADER = "T1\nG17 G49 G54 G80 G90 G94 G21 G40 G64\n"
        self.X_str = 'X'
        self.Y_str = 'Y'
        self.U_str = 'Z'
        self.V_str = 'A'
        x_data = [1,1000]
        y_data = [0,0]
        self.offset_function = generate_offset_function(x_data, y_data)
        
    def load_config(self, file_path):
        try:
            config_file = np.genfromtxt(file_path, delimiter = ",", skip_header = 1, dtype = str)
            config_data = config_file[:,2]
            self.FILENAME_XY = config_data[0]
            self.FILENAME_UV = config_data[1]
            self.OX = float(config_data[2])
            self.OY = float(config_data[3])
            self.EX = float(config_data[4])
            self.EY = float(config_data[5])
            self.DELTA_LENGTH = float(config_data[6])
            self.OFFSET_DIST = float(config_data[7])
            self.CUTSPEED = float(config_data[8])
            self.XY_DIST = float(config_data[9])
            self.UV_DIST = float(config_data[10])
            self.WORK_LENGTH = float(config_data[11])
            self.MACH_DIST = float(config_data[12])
            self.HEADER = config_data[13].replace("\\n", "\n")
            self.X_str = str(config_data[14])
            self.Y_str = str(config_data[15])
            self.U_str = str(config_data[16])
            self.V_str = str(config_data[17])
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
            self.OFFSET_DIST = 0.0
            self.CUTSPEED = 200
            self.XY_DIST = 25.0
            self.UV_DIST = 50.0
            self.WORK_LENGTH = 425
            self.MACH_DIST = 500
            self.HEADER = "T1\nG17 G49 G54 G80 G90 G94 G21 G40 G64\n"
            self.X_str = 'X'
            self.Y_str = 'Y'
            self.U_str = 'Z'
            self.V_str = 'A'
            self.MESSEAGE = "設定ファイルの読み込み失敗\n"
            pass          

    def load_offset_func(self, file_path):
        try:
            offset_function_file = np.genfromtxt(file_path, delimiter = ",", skip_header = 1, dtype = str)
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
#   load_config(config, config_entry, dlEntry, CutSpeedEntry, XYDistEntry, UVDistEntry, WorkLengthEntry, MachDistEntry, MessageWindow)
#   【引数】　config, config_entry, dlEntry, CutSpeedEntry, XYDistEntry, UVDistEntry, WorkLengthEntry, MachDistEntry, MessageWindow
#   【戻り値】　なし
#   【機能】 open_file_explorerを用いて、config_entryにconfigファイルのパスを設定する
#           configクラスのload_configメソッドを使用して、configファイルのパスを読みこみ、configオブジェクトの値を更新する
#           dlEntry, CutSpeedEntry, XYDistEntry, UVDistEntry, WorkLengthEntry, MachDistEntryの値を、configオブジェクトの値に更新する
#           MessageWindowにconfig.load_configの結果およびGコードの書き出しを出力する
#
#   load_offset_func(config, offset_func_entry, MessageWindow)
#   【引数】　config, offset_func_entry, MessageWindow
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
#   load_file(dxf_file　dxf_obj, tk.Entry entry, messeage_window messeage_window)
#   【引数】　dxf_obj, entry, messeage_window
#   【戻り値】　なし
#   【機能】 Entryに入力されたファイル名称をdxf_obj.load_fileにより読み込む．file_chkをコールし，読み取り可否をmesseage_windowに通知する．
#　　　　　　　　
#   XY_UV_Link(tk.BooleanVar chkValue, super_table table_XY, super_table table_UV, messeage_window  messeage_window)
#   【引数】 chkValue, table_XY, table_UV, messeage_window
#   【戻り値】　なし
#   【機能】　chkValue=trueの場合，table_XY.parent=1, table_UV.parent=0に設定する．
#
#   swap_line(dxf_file　dxf_obj, messeage_window messeage_window)
#   【引数】 dxf_obj, messeage_window
#   【戻り値】 なし
#   【機能】 dxf_obj.Swap_Selected_lineをコールし，選択された2本のラインを入れ替える．入れ替え結果をmesseage_windowに表示する．
#
#   Change_CutDir(dxf_file　dxf_obj, messeage_window messeage_window)
#   【引数】 dxf_obj, messeage_window
#   【戻り値】 なし
#   【機能】 dxf_obj.Change_CutDirをコールし，選択したラインのカット方向を入れ替える．入れ替え結果をmesseage_windowに表示する．
#
#   Change_OffsetDir(dxf_file　dxf_obj, messeage_window messeage_window)
#   【引数】 dxf_obj, messeage_window
#   【戻り値】　なし
#   【機能】 dxf_obj.Change_OffsetDirをコールし，選択したラインのオフセット方向を入れ替える．入れ替え結果をmesseage_windowに表示する．
#   
#   Merge_line(dxf_obj,  messeage_window)
#   【引数】　dxf_obj,  messeage_window
#   【戻り値】　なし
#   【機能】 テーブルで選択された２本のラインを結合する。後に選択した方のラインは削除する
#     
#   Set_OffsetDist(dxf_file　dxf_obj0, dxf_file　dxf_obj1, tk.Entry entry, messeage_window messeage_window)
#   【引数】　dxf_obj0, dxf_obj1, entry, messeage_window
#   【戻り値】　なし
#   【機能】 entryに入力されたオフセット距離を読み取り，dxf_obj0.set_offset_dist，dxf_obj1.set_offset_distをコールする．変更結果をmesseage_windowに表示する．
#
#   delete_line(dxf_file　dxf_obj, messeage_window messeage_window)
#   【引数】 dxf_obj, messeage_window
#   【戻り値】　なし
#   【機能】 delete_Selected_lineをコールし，選択したラインを削除する．削除した結果をmesseage_windowに表示する．
#
#   AutoLineSort(dxf_file　dxf_obj0, dxf_file　dxf_obj1, tk.Entry entry_x, tk.Entry entry_y, messeage_window messeage_window)
#   【引数】 dxf_obj0, dxf_obj1, entry_x, entry_y, messeage_window
#   【戻り値】 なし
#   【機能】 entry_x, entry_yからox, oyを読み取り．dxf_obj0.SortLine, dxf_obj1.SortLineをコールする．結果をmesseage_windowに表示する．
#        
#   Reverse(dxf_file　dxf_obj, messeage_window messeage_window)
#   【引数】　dxf_obj, messeage_window
#   【戻り値】　なし
#   【機能】 dxf_obj.reverse_allをコールし，カット順を逆転させる．結果をmesseage_windowに表示する．
#
#   Replace_G01_code(g_code_str, X_str, Y_str, U_str, V_str)
#   【引数】g_code_str, X_str, Y_str, U_str, V_str
#   【戻り値】g_code_str
#   【機能】g_code_strのX,Y,U,Vの座標文字をX_str, Y_str, U_str, V_strで指定されるものに置換する
#
#   make_offset_path(x_array, y_array, u_array, v_array, Z_XY, Z_UV, Z_Mach)
#   【引数】x_array, y_array, u_array, v_array, Z_XY, Z_UV, Z_Mach
#   【戻り値】new_x, new_y, new_u, new_v
#   【機能】ワーク上のXY, UV座標点列（x_array, y_array, u_array, v_array）から、マシン駆動面上の座標点列を作成し、出力する
#
#   get_offset_and_cut_speed(length_XY, length_UV, Z_XY, Z_UV, Z_Mach, CutSpeed, offset_function)
#   【引数】length_XY, length_UV, Z_XY, Z_UV, Z_Mach, CutSpeed, offset_function
#   【戻り値】offset_XY_Work, offset_UV_Work, cutspeed_XY_Work, cutspeed_UV_Work, cutspeed_XY_Mech, cutspeed_UV_Mech
#   【機能】(1) XY断面の線長とUV断面の線長から、ワークの中間点での線長を算出する
#          (2) ワークの中間点でのカット速度が、CutSpeedとするとして、(1)の線長比から、XY、UV断面でのカット速度(cutspeed_XY_Work, cutspeed_UV_Work)を算出する
#          (3) offset_functionを用いて、XY、UV断面のカット速度における溶け量を推定し、これをキャンセルするようにオフセット量（offset_XY_Work, offset_UV_Work）を設定する。
#              ※マシン駆動面上での座標点列作成は、その他の線郡と同様に、gen_g_code側にて行う
#          (4) ワーク端面（XY面, UV面）とマシン駆動面との距離（Z_XY, Z_UV, Z_Mach）から、cutspeed_XY_Work, cutspeed_UV_Workを実現するマシン駆動面速度（cutspeed_XY_Mech, cutspeed_UV_Mech）を算出する
#
#   Set_OffsetDistFromFunction(dxf_obj0, dxf_obj1, entry_XYDist, entry_UVDist, entry_MachDist, entry_CS, offset_function, messeage_window)
#   【引数】dxf_obj0, dxf_obj1, entry_XYDist, entry_UVDist, entry_MachDist, entry_CS, offset_function, messeage_window
#   【戻り値】なし
#   【機能】dxf_obj0, dxf_obj1の対応する線から、XY断面の線長、UV断面の線長を取得し、get_offset_and_cut_speedにより線ごとにオフセット距離、カット速度を取得する
#          取得したオフセット距離、カット速度を線（line Object）に設定し、オフセット距離を更新する
#
#   gen_g_code(dxf_file　dxf_obj0, dxf_file　dxf_obj1, tk.Entry entry_ox, tk.Entry entry_oy, tk.Entry entry_ex, tk.Entry entry_ey, tk.Entry entry_CS, tk.Entry entry_dl, str header, messeage_window messeage_window)
#   【引数】 dxf_obj0, dxf_obj1, entry_ox, entry_oy, entry_ex, entry_ey, entry_CS, entry_dl, header, messeage_window
#   【戻り値】　なし
#   【機能】　gコードを生成する．始点をentry_ox, entry_oyから，終点をentry_ex, entry_eyから読み取る．カット速度をentry_CSから読み取る．分割距離をentry_dlから読み取る．gコードの書き出しをheaderとする．
#　　　　　　　　1. dxf_obj0, dxf_obj1のline_num_listにて0以上の値を取得し，a_line_num_list0,a_line_num_list1に格納する．
#　　　　　　　　2. a_line_num_list0,a_line_num_list1のライン数が一致しているかを確認する．
#　　　　　　　　3. a_line_num_list0,a_line_num_list1のラインを順にgコード化する．各ラインについてget_length()にてライン長を取得し，N=get_length()/dlから分割数を決定する
#　　　　　　　　4. 各ラインについてgenerate_arc_length_pointsをコールし，等間隔点列x, y, u, vを取得する．
#　　　　　　　　5. gen_g_code_line_str(x, y, u, v)をコールし，x, y, u, vからgコードを生成する．
#　　　　　　　　6. 各ラインのgコードを結合し，保存する．保存名は 「dxf_obj0.filename,dxf_obj1.filename,日付.nc」とする．　
#
#   path_chk(tk.Frame Root, dxf_file　dxf_obj0, dxf_file　dxf_obj1, tk.Entry entry_ox, tk.Entry entry_oy, tk.Entry entry_ex, tk.Entry entry_ey, tk.Entry entry_MachDist, tk.Entry entry_dl, messeage_window messeage_window)
#   【引数】 Root, dxf_obj0, dxf_obj1, entry_ox, entry_oy, entry_ex, entry_ey, entry_MachDist, entry_dl, messeage_window
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
    entry.delete(0,tk.END)
    entry.insert(tk.END, data)


def load_config(config, config_entry, dlEntry, CutSpeedEntry, XYDistEntry, UVDistEntry, WorkLengthEntry, MachDistEntry, MessageWindow):
    open_file_explorer(config_entry)
    
    config_path = config_entry.get()
    config.load_config(config_path)
    
    #【分割距離入力コンソール】 
    dlEntry.delete(0,tk.END)
    dlEntry.insert(tk.END, config.DELTA_LENGTH) 

    #【カット速度入力コンソール】   
    CutSpeedEntry.delete(0,tk.END)
    CutSpeedEntry.insert(tk.END, config.CUTSPEED) 

    #【カット面距離入力コンソール1】   
    XYDistEntry.delete(0,tk.END)
    XYDistEntry.insert(tk.END, config.XY_DIST)

    #【カット面距離入力コンソール2】   
    UVDistEntry.delete(0,tk.END)
    UVDistEntry.insert(tk.END, config.UV_DIST)

    #【XY-UV面距離入力コンソール】 
    WorkLengthEntry.delete(0,tk.END)
    WorkLengthEntry.insert(tk.END, config.WORK_LENGTH)

    #【マシン距離入力コンソール】   
    MachDistEntry.delete(0,tk.END)
    MachDistEntry.insert(tk.END, config.MACH_DIST)  
        
    MessageWindow.set_messeage(config.MESSEAGE)
    MessageWindow.set_messeage("Gコードの書き出しは「%s」です。\n"%config.HEADER)


def load_offset_func(config, offset_func_entry, MessageWindow):
    open_file_explorer(offset_func_entry)
    offset_file_path = offset_func_entry.get()
    config.load_offset_func(offset_file_path)
    
    MessageWindow.set_messeage(config.MESSEAGE)


def open_dxf_explorer(dxf_obj, entry, messeage_window):
    open_file_explorer(entry)
    load_file(dxf_obj, entry, messeage_window)


def load_file(dxf_obj, entry, messeage_window):
    filename = entry.get()
    if file_chk(filename) == 1:
        dxf_obj.load_file(filename)
        messeage_window.set_messeage("%sを読み込みました。\n"%filename)
    if file_chk(filename) == 0:
        messeage_window.set_messeage("%sを読み込めません。拡張子が.dxfであることを確認して下さい。\n"%filename)  
        
    if file_chk(filename) == -1:        
        messeage_window.set_messeage("%sを読み込めません。ファイルが存在することを確認して下さい。\n"%filename)  


def XY_UV_Link(chkValue, table_XY, table_UV, messeage_window):
    if chkValue.get():
        table_XY.set_sync(True)
        table_UV.set_sync(True)
        messeage_window.set_messeage("U-V画面をX-Y画面と連動\n")
    else:
        table_XY.set_sync(False)
        table_UV.set_sync(False)       
        messeage_window.set_messeage("U-V画面とX-Y画面の連動を解除\n")


def swap_line(dxf_obj, messeage_window):
    selected_items = dxf_obj.Swap_Selected_line()
    if len(selected_items) == 2:
        messeage_window.set_messeage("%sと%s番目のラインを入れ替えました。\n"%(item2num(selected_items[0]), item2num(selected_items[1])))
    else:
        messeage_window.set_messeage("２つのラインを選択して下さい。%s本のラインが選択されています。\n"%len(selected_items))


def Change_CutDir(dxf_obj, x_dxf_obj, chkValue, messeage_window):
    dxf_obj.Change_CutDir()
    if chkValue.get():
        x_dxf_obj.Change_CutDir()
    messeage_window.set_messeage("カット方向を逆転\n")
    

def Change_OffsetDir(dxf_obj, x_dxf_obj, chkValue, messeage_window):
    dxf_obj.Change_OffsetDir()
    if chkValue.get():
        x_dxf_obj.Change_OffsetDir()
    messeage_window.set_messeage("オフセット方向を逆転\n")



def AutoLineSort(dxf_obj, x_dxf_obj, chkValue, messeage_window): 
    try:
        ret = dxf_obj.SortLine()
        if chkValue.get():
            x_ret = x_dxf_obj.SortLine()
        else:
            x_ret = 1
            
        if (ret == 1) and (x_ret == 1):
            messeage_window.set_messeage("自動整列しました。\n")
        else:
            messeage_window.set_messeage("%s本の線が選択されています。起点とする１本の線のみを選択してください。\n"%max(ret, x_ret))

    except:
        traceback.print_exc()
        output_log(traceback.format_exc())
        pass


def Reverse(dxf_obj, x_dxf_obj, chkValue, messeage_window):
    dxf_obj.reverse_all()
    if chkValue.get():
        x_dxf_obj.reverse_all()
    messeage_window.set_messeage("カット順を逆転しました。\n")



def Merge_line(dxf_obj, messeage_window):
    error, selected_items = dxf_obj.Merge_Selected_line()
    if error == 0:
        messeage_window.set_messeage("%s番目のラインに結合しました。\n"%item2num(selected_items[0]))
    elif error == 2:
        messeage_window.set_messeage("２つの近接したラインを選択して下さい。ラインの端点間の距離が遠すぎます。\n")
    else:
        messeage_window.set_messeage("２つのラインを選択して下さい。%s本のラインが選択されています。\n"%len(selected_items))
        
        
def delete_line(dxf_obj, messeage_window):
    dxf_obj.delete_Selected_line()
    messeage_window.set_messeage("ラインを削除しました。\n")
    
    
def Set_OffsetDist(dxf_obj, entry, messeage_window):
    entry_value = entry.get()
    try:
        OffsetDist = float(entry_value)
        dxf_obj.set_offset_dist(OffsetDist)
        messeage_window.set_messeage("オフセット距離を%sに設定しました。\n"%OffsetDist)
    except:
        traceback.print_exc()
        output_log(traceback.format_exc())
        messeage_window.set_messeage("実数値を入力して下さい。\n")
        pass


def Replace_G01_code(g_code_str, X_str, Y_str, U_str, V_str):
    
    if ('G01' in g_code_str) and ('X' in g_code_str) and ('Y' in g_code_str) and ('U' in g_code_str) and ('V' in g_code_str):
        new_g_code_str = g_code_str
        new_g_code_str = new_g_code_str.replace('X', X_str)
        new_g_code_str = new_g_code_str.replace('Y', Y_str)
        new_g_code_str = new_g_code_str.replace('U', U_str)
        new_g_code_str = new_g_code_str.replace('V', V_str)
        return new_g_code_str

    else:
        return g_code_str

#Ver2.1 追加　引数変更
def make_offset_path(x_array, y_array, u_array, v_array, Z_XY, Z_UV, Z_Mach):
    
    new_x = []
    new_y = []
    new_u = []
    new_v = []
    
    Z_work_mid = (Z_Mach - Z_XY - Z_UV)/2.0 + Z_XY
    L_XY_work = np.abs(Z_work_mid - Z_XY)
    L_UV_work = np.abs((Z_Mach - Z_UV) - Z_work_mid)
    L_XY_Mach = np.abs(Z_work_mid)
    L_UV_Mach = np.abs(Z_Mach - Z_work_mid)
    
    if L_XY_work == 0 or L_UV_work == 0:
        k_xy = 1.0
        k_uv = 1.0        
    else:
        k_xy = L_XY_Mach/ L_XY_work
        k_uv = L_UV_Mach/ L_UV_work
    
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


def get_offset_and_cut_speed(length_XY, length_UV, Z_XY, Z_UV, Z_Mach, CutSpeed, offset_function):
    
    Z_work_mid = (Z_Mach - Z_XY - Z_UV)/2.0 + Z_XY
    L_XY_work = np.abs(Z_work_mid - Z_XY)
    L_UV_work = np.abs((Z_Mach - Z_UV) - Z_work_mid)
    L_XY_Mach = np.abs(Z_work_mid)
    L_UV_Mach = np.abs(Z_Mach - Z_work_mid)
    
    if L_XY_work == 0 or L_UV_work == 0:
        k_xy = 1.0
        k_uv = 1.0        
    else:
        k_xy = L_XY_Mach/ L_XY_work
        k_uv = L_UV_Mach/ L_UV_work
           
    length_mid = (length_XY + length_UV)/ 2.0
    dl_XY = length_XY - length_mid
    dl_UV = length_UV - length_mid
    
    length_XY_Mech = k_xy*dl_XY + length_mid
    length_UV_Mech = k_uv*dl_UV + length_mid
    
    length_ratio_XY_Mech = length_XY_Mech/length_mid
    length_ratio_UV_Mech = length_UV_Mech/length_mid
    length_ratio_XY_Work = length_XY/length_mid
    length_ratio_UV_Work = length_UV/length_mid

    cutspeed_XY_Mech = CutSpeed*length_ratio_XY_Mech
    cutspeed_UV_Mech = CutSpeed*length_ratio_UV_Mech
    cutspeed_XY_Work = CutSpeed*length_ratio_XY_Work
    cutspeed_UV_Work = CutSpeed*length_ratio_UV_Work
    
    offset_XY_Mech = offset_function(cutspeed_XY_Mech)
    offset_UV_Mech = offset_function(cutspeed_UV_Mech)
    offset_XY_Work = offset_function(cutspeed_XY_Work)
    offset_UV_Work = offset_function(cutspeed_UV_Work)
    offset_mid = offset_function(CutSpeed)
    
    #for debug
    """   
    #plt.plot([0, Z_XY, Z_work_mid, Z_Mach-Z_UV, Z_Mach],[length_XY_Mech, length_XY, length_mid, length_UV, length_UV_Mech], "-o")
    #plt.plot([0, Z_XY, Z_work_mid, Z_Mach-Z_UV, Z_Mach],[cutspeed_XY_Mech, cutspeed_XY_Work, CutSpeed, cutspeed_UV_Work, cutspeed_UV_Mech], "-o")
    #plt.plot([0, Z_XY, Z_work_mid, Z_Mach-Z_UV, Z_Mach],[offset_XY_Mech, offset_XY_Work, offset_mid, offset_UV_Work, offset_UV_Mech], "-o")    
    """
    
    return offset_XY_Work, offset_UV_Work, cutspeed_XY_Work, cutspeed_UV_Work, cutspeed_XY_Mech, cutspeed_UV_Mech


def Set_OffsetDistFromFunction(dxf_obj0, dxf_obj1, entry_XYDist, entry_UVDist, entry_MachDist, entry_CS, offset_function, messeage_window):
    entry_XYDist_value = entry_XYDist.get()
    entry_UVDist_value = entry_UVDist.get()
    entry_MachDist_value = entry_MachDist.get()
    entry_CS_value = entry_CS.get()    

    # 削除済みの線は、インデックスが-1となっているので、有効な線（インデックスが0以上の線）のみを抽出する
    a_line_num_list0 = np.array(np.array(dxf_obj0.line_num_list.copy())[np.where(np.array(dxf_obj0.line_num_list.copy()) >= 0)])
    a_line_num_list1 = np.array(np.array(dxf_obj1.line_num_list.copy())[np.where(np.array(dxf_obj1.line_num_list.copy()) >= 0)])
    
    try:
        Z_XY = float(entry_XYDist_value)
        Z_UV = float(entry_UVDist_value)
        Z_Mach = float(entry_MachDist_value)
        CutSpeed = float(entry_CS_value)
                    
        if len(a_line_num_list0) == len(a_line_num_list1):
            i = 0
            while i < len(a_line_num_list0):
                line_num0 = a_line_num_list0[i]
                line_num1 = a_line_num_list1[i]
                
                line0 = dxf_obj0.line_list[line_num0]
                line1 = dxf_obj1.line_list[line_num1]
                
                line0_length = line0.get_length()
                line1_length = line1.get_length()
                
                offset_XY_Work, offset_UV_Work, cutspeed_XY_Work, cutspeed_UV_Work, cutspeed_XY_Mech, cutspeed_UV_Mech = \
                    get_offset_and_cut_speed(line0_length, line1_length, Z_XY, Z_UV, Z_Mach, \
                                             CutSpeed, offset_function)
                line0.set_offset_dist(offset_XY_Work)
                line1.set_offset_dist(offset_UV_Work)
                
                line0.set_cutspeed(cutspeed_XY_Work, cutspeed_XY_Mech)
                line1.set_cutspeed(cutspeed_UV_Work, cutspeed_UV_Mech)
                
                i += 1
            dxf_obj0.table_reload()
            dxf_obj1.table_reload()
            dxf_obj0.plot()
            dxf_obj1.plot()
            messeage_window.set_messeage("オフセット値を更新しました。\n")
        else:
            messeage_window.set_messeage("XY座標とUV座標でライン数が一致しません。XY：%s本，UV：%s本\n"%(len(a_line_num_list0),len(a_line_num_list1)))

    except:
        traceback.print_exc()
        output_log(traceback.format_exc())
        messeage_window.set_messeage("入力値に誤りがあります。オフセット値更新を中止しました。\n")

# Ver2.1変更　引数追加，距離別指定可能
def gen_g_code(dxf_obj0, dxf_obj1, entry_ox, entry_oy, entry_ex, entry_ey, entry_XYDist, entry_UVDist, entry_WorkLength, entry_MachDist, entry_CS, entry_dl, messeage_window, config):
    entry_ox_value = entry_ox.get()
    entry_oy_value = entry_oy.get()
    entry_ex_value = entry_ex.get()
    entry_ey_value = entry_ey.get()
    entry_XYDist_value = entry_XYDist.get()
    entry_UVDist_value = entry_UVDist.get()
    entry_WorkLength_value = entry_WorkLength.get()
    entry_MachDist_value = entry_MachDist.get()
    entry_dl_value = entry_dl.get()
    entry_CS_value = entry_CS.get()
    
    code_line_list = []
    code_line_list.append(config.HEADER)
    
    try:
        temp_error_flg = False
        
        ox = float(entry_ox_value)
        oy = float(entry_oy_value)
        ex = float(entry_ex_value)
        ey = float(entry_ey_value)
        Z_XY = float(entry_XYDist_value)
        Z_UV = float(entry_UVDist_value)
        Z_Work = float(entry_WorkLength_value)
        Z_Mach = float(entry_MachDist_value)
        dl = float(entry_dl_value)
        CS = float(entry_CS_value)


        if np.abs(Z_XY + Z_UV + Z_Work - Z_Mach) > np.abs(Z_ERROR):
            if (Z_XY + Z_UV + Z_Work - Z_Mach) > 0.0:
                messeage_window.set_messeage("【警告】\nXY面距離，UV面距離，加工物サイズの和が，駆動面距離に対して%s mm 長いです。（許容誤差：%s mm）\n入力値を確認してください。\n\n"%((Z_XY + Z_UV + Z_Work - Z_Mach), np.abs(Z_ERROR)))
                temp_error_flg = True
            else:
                messeage_window.set_messeage("【警告】\nXY面距離，UV面距離，加工物サイズの和が，駆動面距離に対して%s mm 短いです。（許容誤差：%s mm）\n入力値を確認してください。\n\n"%((Z_Mach - Z_XY - Z_UV - Z_Work), np.abs(Z_ERROR)))
                temp_error_flg = True
        if Z_XY > Z_Mach:
            messeage_window.set_messeage("【警告】\nXY面距離が駆動面距離に対して%s mm 長いです。\n入力値を確認してください。\n\n"%(Z_XY - Z_Mach))
            temp_error_flg = True
        if Z_UV > Z_Mach:
            messeage_window.set_messeage("【警告】\nUV面距離が駆動面距離に対して%s mm 長いです。\n入力値を確認してください。\n\n"%(Z_UV - Z_Mach))
            temp_error_flg = True
       
        if dl < 0.1:
            dl = 0.1
        #Ver2.0　変更 Gコード出力形式
        code_line_list.append("G01 X%f Y%f U%f V%f F%s\n"%(ox, oy, ox, oy, CS))
        
        a_line_num_list0 = np.array(np.array(dxf_obj0.line_num_list.copy())[np.where(np.array(dxf_obj0.line_num_list.copy()) >= 0)])
        a_line_num_list1 = np.array(np.array(dxf_obj1.line_num_list.copy())[np.where(np.array(dxf_obj1.line_num_list.copy()) >= 0)])

        x_array = np.array([ox])
        y_array = np.array([oy])
        u_array = np.array([ox])
        v_array = np.array([oy])
        
        xy_offset_dist = []
        uv_offset_dist = []
        
        if temp_error_flg == False:
            if len(a_line_num_list0) == len(a_line_num_list1):
                i = 0
                while i < len(a_line_num_list0):
                    line_num0 = a_line_num_list0[i]
                    line_num1 = a_line_num_list1[i]
                    
                    line0 = dxf_obj0.line_list[line_num0]
                    line1 = dxf_obj1.line_list[line_num1]
                    
                    line0_length = line0.get_length()
                    line1_length = line1.get_length()
    
                    xy_offset_dist.append(line0.offset_dist)
                    uv_offset_dist.append(line1.offset_dist)
                    
                    N = int(max(line0_length, line1_length)/ dl)
                    if N < 2:
                        N = 2
                    
                    x, y = generate_arc_length_points(line0, N)
                    u, v = generate_arc_length_points(line1, N)
                    cut_speed = max(line0.cutspeed_mech, line1.cutspeed_mech)
                    
                    if (i != 0) and (i != len(a_line_num_list0)):
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
                        
                        #オフセット面の作成
                        x_m_f, y_m_f, u_m_f, v_m_f = make_offset_path(x_f, y_f, u_f, v_f, Z_XY, Z_UV, Z_Mach)
                        code_line_list.append(gen_g_code_line_str(x_m_f, y_m_f, u_m_f, v_m_f, cut_speed))
                    
                        x_array = np.concatenate([x_array, x_f], 0)
                        y_array = np.concatenate([y_array, y_f], 0)
                        u_array = np.concatenate([u_array, u_f], 0)
                        v_array = np.concatenate([v_array, v_f], 0)      
                    
                    #オフセット面の作成
                    x_m, y_m, u_m, v_m = make_offset_path(x, y, u, v, Z_XY, Z_UV, Z_Mach)
                    code_line_list.append(gen_g_code_line_str(x_m, y_m, u_m, v_m, cut_speed))
                    
                    x_array = np.concatenate([x_array, x], 0)
                    y_array = np.concatenate([y_array, y], 0)
                    u_array = np.concatenate([u_array, u], 0)
                    v_array = np.concatenate([v_array, v], 0)
                    
                    i += 1
                #Ver2.0　変更 Gコード出力形式
                code_line_list.append("G01 X%f Y%f U%f V%f\n"%(ex, ey, ex, ey))
                
                replaced_code_line_list = []
                for g_code_str in code_line_list:
                    replaced_code_line_list.append(Replace_G01_code(g_code_str, config.X_str, config.Y_str, config.U_str, config.V_str))
                
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
                messeage_window.set_messeage("XY座標とUV座標でライン数が一致しません。XY：%s本，UV：%s本\n"%(len(a_line_num_list0),len(a_line_num_list1)))
        if temp_error_flg == True:
            messeage_window.set_messeage("入力値に誤りがあります。Gコード生成を中止しました。\n\n")
    except:
        traceback.print_exc()
        output_log(traceback.format_exc())
        messeage_window.set_messeage("Gコード生成途中でエラーが発生しました。\n\n")
        pass

    
#Ver2.1変更　引数追加，距離別指定可能
def path_chk(Root, dxf_obj0, dxf_obj1, entry_ox, entry_oy, entry_ex, entry_ey, \
             entry_XYDist, entry_UVDist, entry_WorkLength, entry_MachDist, entry_dl, messeage_window):
        
    PLOT_PER_POINT = 2
    
    if PLOT_PER_POINT < 1:
        PLOT_PER_POINT = 1
    
    Window_3d_plot = tk.Toplevel(Root)
    Window_3d_plot.wm_title("Cut Path")
    Window_3d_plot.geometry("1000x800")
    
    fig = Figure(figsize=(8, 6), dpi=100)
    
    canvas = FigureCanvasTkAgg(fig, master = Window_3d_plot)
    
    ax = fig.add_subplot(111, projection="3d", proj_type = 'ortho')

    toolbar = NavigationToolbar2Tk(canvas, Window_3d_plot)
    toolbar.update()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    
    entry_ox_value = entry_ox.get()
    entry_oy_value = entry_oy.get()
    entry_ex_value = entry_ex.get()
    entry_ey_value = entry_ey.get()    
    entry_dl_value = entry_dl.get()
    entry_XYDist_value = entry_XYDist.get()
    entry_UVDist_value = entry_UVDist.get()
    entry_WorkLength_value = entry_WorkLength.get()
    entry_MachDist_value = entry_MachDist.get()

    
    try:
        ox = float(entry_ox_value)
        oy = float(entry_oy_value)
        ex = float(entry_ex_value)
        ey = float(entry_ey_value)
        dl = float(entry_dl_value)
        Z_XY = float(entry_XYDist_value)
        Z_UV = float(entry_UVDist_value)
        Z_Work = float(entry_WorkLength_value)
        Z_Mach = float(entry_MachDist_value)
        
        x_array = np.array([ox])
        y_array = np.array([oy])
        u_array = np.array([ox])
        v_array = np.array([oy])
        
        xy_offset_dist = []
        uv_offset_dist = []
        
        if dl < 0.1:
            dl = 0.1
        
        a_line_num_list0 = np.array(np.array(dxf_obj0.line_num_list.copy())[np.where(np.array(dxf_obj0.line_num_list.copy()) >= 0)])
        a_line_num_list1 = np.array(np.array(dxf_obj1.line_num_list.copy())[np.where(np.array(dxf_obj1.line_num_list.copy()) >= 0)])
        
        if len(a_line_num_list0) == len(a_line_num_list1):
            i = 0
            while i < len(a_line_num_list0):
                line_num0 = a_line_num_list0[i]
                line_num1 = a_line_num_list1[i]
                
                line0 = dxf_obj0.line_list[line_num0]
                line1 = dxf_obj1.line_list[line_num1]
                
                line0_length = line0.get_length()
                line1_length = line1.get_length()
                
                xy_offset_dist.append(line0.offset_dist)
                uv_offset_dist.append(line1.offset_dist)
                
                N = int(max(line0_length, line1_length)/ dl)
                if N < 2:
                    N = 2
                
                x, y = generate_arc_length_points(line0, N)
                u, v = generate_arc_length_points(line1, N)
                
                if (i != 0) and (i != len(a_line_num_list0)):
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

                    x_array = np.concatenate([x_array, x_f], 0)
                    y_array = np.concatenate([y_array, y_f], 0)
                    u_array = np.concatenate([u_array, u_f], 0)
                    v_array = np.concatenate([v_array, v_f], 0)                    
                    
                else:
                    norm_line2line0 = norm(x_array[-1], y_array[-1], x[0], y[0])
                    norm_line2line1 = norm(u_array[-1], v_array[-1], u[0], v[0])
                    
                    if norm_line2line0 > dl*PLOT_PER_POINT  or  norm_line2line1 > dl*PLOT_PER_POINT:
                        N_interp_line2line = int(max(norm_line2line0, norm_line2line1) / dl / PLOT_PER_POINT)
                        
                        if N_interp_line2line < 2:
                            N_interp_line2line = 2
                        
                        xp, yp = generate_arc_length_points4line(x_array[-1], y_array[-1], x[0], y[0], N_interp_line2line)
                        up, vp = generate_arc_length_points4line(u_array[-1], v_array[-1], u[0], v[0], N_interp_line2line)
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
            
            if norm_line2line0 > dl*PLOT_PER_POINT  or  norm_line2line1 > dl*PLOT_PER_POINT:
                N_interp_line2line = int(max(norm_line2line0, norm_line2line1) / dl / PLOT_PER_POINT)
                
                if N_interp_line2line < 2:
                    N_interp_line2line = 2
                
                xp, yp = generate_arc_length_points4line(x_array[-1], y_array[-1], ex, ey, N_interp_line2line)
                up, vp = generate_arc_length_points4line(u_array[-1], v_array[-1], ex, ey, N_interp_line2line)
                x_array = np.concatenate([x_array, xp], 0)
                y_array = np.concatenate([y_array, yp], 0)
                u_array = np.concatenate([u_array, up], 0)
                v_array = np.concatenate([v_array, vp], 0)
            
            #オフセット面の作成
            x_m_array, y_m_array, u_m_array, v_m_array = make_offset_path(x_array, y_array, u_array, v_array, Z_XY, Z_UV, Z_Mach)
            
            point_dist_array = plot_3d_cut_path(ax, x_array, y_array, u_array, v_array, x_m_array, y_m_array, u_m_array, v_m_array, Z_XY, Z_UV, Z_Mach, int(len(x_array)/PLOT_PER_POINT))
            
            ax.view_init(elev=90, azim=-90) 
            
            x_max = max(max(x_array), max(u_array))
            x_min = min(min(x_array), min(u_array))
            y_max = max(max(y_array), max(v_array))
            y_min = min(min(y_array), min(v_array))
            
            z_max = Z_Mach
            z_min = 0.0
            
            max_range = max(np.array([x_max - x_min, y_max - y_min, z_max - z_min])) * 0.5
            mid_x = (x_max + x_min) * 0.5
            mid_y = (y_max + y_min) * 0.5
            mid_z = (z_max + z_min) * 0.5
            ax.set_xlim(mid_x - max_range, mid_x + max_range)
            ax.set_ylim(mid_y - max_range, mid_y + max_range)
            ax.set_zlim(mid_z - max_range, mid_z + max_range)
            
            canvas.draw()
            
            messeage_window.set_messeage("パスを描画しました。ワイヤーの最大長は%s mmです。（初期長%s mm）\n"%(int(max(point_dist_array)), int(Z_Mach)))
            messeage_window.set_messeage("\n【加工範囲】 \nX: %smm～%smm\nY: %smm～%smm\nU: %smm～%smm\nV: %smm～%smm\n\n"
                                         %(int(min(x_array)), int(max(x_array)), int(min(y_array)), int(max(y_array)), int(min(u_array)), int(max(u_array)), int(min(v_array)), int(max(v_array))))
            if np.abs(Z_XY + Z_UV + Z_Work - Z_Mach) > np.abs(Z_ERROR):
                if (Z_XY + Z_UV + Z_Work - Z_Mach) > 0.0:
                    messeage_window.set_messeage("【警告】\nXY面距離，UV面距離，加工物サイズの和が，駆動面距離に対して%s mm 短いです。（許容誤差：%s mm）\n入力値を確認してください。\n\n"%((Z_Mach - Z_XY - Z_UV - Z_Work), np.abs(Z_ERROR)))
                else:
                    messeage_window.set_messeage("【警告】\nXY面距離，UV面距離，加工物サイズの和が，駆動面距離に対して%s mm 短いです。（許容誤差：%s mm）\n入力値を確認してください。\n\n"%((Z_Mach - Z_XY - Z_UV - Z_Work), np.abs(Z_ERROR)))
            if Z_XY > Z_Mach:
                messeage_window.set_messeage("【警告】\nXY面距離が駆動面距離に対して%s mm 長いです。\n入力値を確認してください。\n\n"%(Z_XY - Z_Mach))
            if Z_UV > Z_Mach:
                messeage_window.set_messeage("【警告】\nUV面距離が駆動面距離に対して%s mm 長いです。\n入力値を確認してください。\n\n"%(Z_UV - Z_Mach))
            
        else:
            messeage_window.set_messeage("XY座標とUV座標でライン数が一致しません。XY：%s本，UV：%s本\n"%(len(a_line_num_list0), len(a_line_num_list1)))
        
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
        dxf_obj0.offset_origin(offset_ox, offset_oy)
        dxf_obj1.offset_origin(offset_ox, offset_oy)
        messeage_window.set_messeage("XY,UV座標をX:%s, Y:%sオフセットしました。\n"%(offset_ox, offset_oy))
    except:
        traceback.print_exc()
        output_log(traceback.format_exc())
        messeage_window.set_messeage("オフセット中にエラーが発生しました\n")


#======================================================================================================================================
#            メイン関数
#======================================================================================================================================


if __name__ == "__main__":


    #======================================================================================================================================
    #            config.csvファイルの読込
    #======================================================================================================================================

    curdir =  get_curdir()
    config = config()
    config.load_config("%s\\config.csv"%curdir)
    config.load_offset_func("%s\\offset_function.csv"%curdir)
       
    #======================================================================================================================================
    #            rootインスタンスの生成
    #======================================================================================================================================
    
    #【メインウィンドウ】
    root = tk.Tk()                                                   #メインウィンドウの枠となるインスタンス
    root.title("HotwireDXF CAM ver%s"%VERSION)                          #メインウィンドウの名称
    root.geometry("1700x950")                                        #メインウィンドウのサイズ（単位：pixcel）
    root.protocol('WM_DELETE_WINDOW', _destroyWindow)                #メインウィンドウを閉じたときにインスタンスを破棄する処理



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
    #          super_tableインスタンスの生成
    #======================================================================================================================================
   
    #【X-Y ラインテーブル】
    table0 = super_table(root, y_height = 17, x = 850,y = 60)        #XYテーブルの枠となるインスタンスを生成
    table0Label = tk.Label(root, text="X-Y",font=("",20))            #XYテーブル用のテキスト
    table0Label.place(x = 860, y = 0)                                #XYテーブル用のテキストを配置

    
    #【U-V ラインテーブル】
    table1 = super_table(root, y_height = 17, x = 1250,y = 60)       #UVテーブルの枠となるインスタンスを生成
    table1Label = tk.Label(root, text="U-V",font=("",20))            #UVテーブル用のテキスト
    table1Label.place(x = 1260, y = 0)                               #UVテーブル用のテキストを配置  


    #======================================================================================================================================
    #          dxf_fileインスタンスの生成
    #======================================================================================================================================

    #【dxfファイルを格納するクラス（dxf_file) のインスタンスを生成】
    dxf0 = dxf_file(ax0, canvas0, table0, table1, "X-Y")
    dxf1 = dxf_file(ax1, canvas1, table1, table0, "U-V")


    #======================================================================================================================================
    #      messeage_windowインスタンスの生成
    #======================================================================================================================================
    
    #Ver2.0 位置変更(下に40pix)
    #【メッセージウィンドウ】
    MessageWindow = messeage_window(root, width=110, height = 9)
    MessageWindow.place(x = 852, y = 815)
    MessageWindowLabel = tk.Label(root, text="メッセージウィンドウ",font=("",12))
    MessageWindowLabel.place(x = 860, y = 790)


    #======================================================================================================================================
    #           entryインスタンスの生成
    #======================================================================================================================================

    #【X-Y用 dxfファイル名の入力コンソール】
    FileNameEntry0 = tk.Entry(root, width=50) 
    FileNameEntry0.insert(tk.END, config.FILENAME_XY) 
    FileNameEntry0.place(x = 852, y = 35)
    
    
    #【U-V用 dxfファイル名の入力コンソール】
    FileNameEntry1 = tk.Entry(root, width=50) 
    FileNameEntry1.insert(tk.END, config.FILENAME_UV)   
    FileNameEntry1.place(x = 1252, y = 35) 


    #【X-Y用オフセット距離の入力コンソール】
    OffsetDistLabel0 = tk.Label(root, text="オフセット量[mm]",font=("",10))
    OffsetDistLabel0.place(x = 875, y = 498)
    OffsetDistEntry0 = tk.Entry(root, width=14, justify=tk.RIGHT,font=("",12)) 
    OffsetDistEntry0.insert(tk.END, "0.0")   
    OffsetDistEntry0.place(x = 990, y = 495) 


    #【U-V用オフセット距離の入力コンソール】
    OffsetDistLabel1 = tk.Label(root, text="オフセット量[mm]",font=("",10))
    OffsetDistLabel1.place(x = 1275, y = 498)
    OffsetDistEntry1 = tk.Entry(root, width=14, justify=tk.RIGHT,font=("",12)) 
    OffsetDistEntry1.insert(tk.END, "0.0")   
    OffsetDistEntry1.place(x = 1390, y = 495) 


    #【オフセット関数ファイル名の入力コンソール】
    OffsetFuncLabel0 = tk.Label(root, text="溶け量ファイル",font=("",12))
    OffsetFuncLabel0.place(x = 850, y = 535)
    OffsetFuncEntry = tk.Entry(root, width=36) 
    OffsetFuncEntry.insert(tk.END, "offset_function.csv")   
    OffsetFuncEntry.place(x = 970, y = 535) 
    

    #【configファイル名の入力コンソール】
    ConfigFileLabel0 = tk.Label(root, text="設定ファイル",font=("",12))
    ConfigFileLabel0.place(x = 850, y = 575)
    ConfigFileEntry = tk.Entry(root, width=36) 
    ConfigFileEntry.insert(tk.END, "config.csv") 
    ConfigFileEntry.place(x = 970, y = 575)
    
    
    
    #【原点オフセット入力コンソール】
    OriginOffsetLabel0 = tk.Label(root, text="全体オフセット",font=("",12))
    OriginOffsetLabel0.place(x = 850, y = 610)
    OriginOffsetLabel1 = tk.Label(root, text="X：",font=("",12))
    OriginOffsetLabel1.place(x = 970, y = 610)
    OriginOffsetLabel2 = tk.Label(root, text="Y：",font=("",12))
    OriginOffsetLabel2.place(x = 1070, y = 610)
    OriginOffsetEntry_X = tk.Entry(root, width=8,font=("",12)) 
    OriginOffsetEntry_X.insert(tk.END, 0)       
    OriginOffsetEntry_X.place(x = 1000, y = 610)   
    OriginOffsetEntry_Y = tk.Entry(root, width=8,font=("",12))     
    OriginOffsetEntry_Y.insert(tk.END, 0)
    OriginOffsetEntry_Y.place(x = 1100, y = 610)    


    #【切り出し原点入力コンソール】
    AutoAlignmentLabel0 = tk.Label(root, text="切り出し始点",font=("",12))
    AutoAlignmentLabel0.place(x = 850, y = 645)
    AutoAlignmentLabel1 = tk.Label(root, text="X：",font=("",12))
    AutoAlignmentLabel1.place(x = 970, y = 645)
    AutoAlignmentLabel2 = tk.Label(root, text="Y：",font=("",12))
    AutoAlignmentLabel2.place(x = 1070, y = 645)
    AutoAlignmentEntry_X = tk.Entry(root, width=8,font=("",12)) 
    AutoAlignmentEntry_X.insert(tk.END, config.OX)       
    AutoAlignmentEntry_X.place(x = 1000, y = 645)   
    AutoAlignmentEntry_Y = tk.Entry(root, width=8,font=("",12))     
    AutoAlignmentEntry_Y.insert(tk.END, config.OY)
    AutoAlignmentEntry_Y.place(x = 1100, y = 645)


    #【切り出し終点入力コンソール】
    CutEndLabel0 = tk.Label(root, text="切り出し終点",font=("",12))
    CutEndLabel0.place(x = 1200, y = 645)
    CutEndLabel1 = tk.Label(root, text="X：",font=("",12))
    CutEndLabel1.place(x = 1320, y = 645)
    CutEndLabel2 = tk.Label(root, text="Y：",font=("",12))
    CutEndLabel2.place(x = 1420, y = 645)
    CutEndEntry_X = tk.Entry(root, width=8,font=("",12)) 
    CutEndEntry_X.insert(tk.END, config.EX)       
    CutEndEntry_X.place(x = 1350, y = 645)   
    CutEndEntry_Y = tk.Entry(root, width=8,font=("",12))     
    CutEndEntry_Y.insert(tk.END, config.EY)
    CutEndEntry_Y.place(x = 1450, y = 645) 


    #【分割距離入力コンソール】
    dlLabel = tk.Label(root, text="分割距離[mm]",font=("",12))
    dlLabel.place(x = 1150, y = 680)
    dlEntry = tk.Entry(root, width=8,font=("",12))     
    dlEntry.insert(tk.END, config.DELTA_LENGTH)
    dlEntry.place(x = 1300, y = 680)       


    #【カット速度入力コンソール】   
    CutSpeedLabel = tk.Label(root, text="カット速度[mm/分]",font=("",12))
    CutSpeedLabel.place(x = 850, y = 680)
    CutSpeedEntry = tk.Entry(root, width=8,font=("",12))     
    CutSpeedEntry.insert(tk.END, config.CUTSPEED)
    CutSpeedEntry.place(x = 1000, y = 680)    


    #【カット速度定義面入力コンボボックス】   
    CutSpeedDefLabel = tk.Label(root, text="カット速度定義面",font=("",12))
    CutSpeedDefLabel.place(x = 850, y = 705) 
    CutSpeedDefList = ("XY(Mech)", "XY(Work)", "Center", "UV(Work)", "UV(Mech)")
    CutSpeedDefCB = ttk.Combobox(root, textvariable= tk.StringVar(), width = 15,\
                                 values=CutSpeedDefList, style="office.TCombobox")
    CutSpeedDefCB.place(x = 1000, y = 705) 
    

    #【CNC速度定義入力コンボボックス】
    CNCSpeedDefLabel = tk.Label(root, text="CNC速度定義",font=("",12))
    CNCSpeedDefLabel.place(x = 1150, y = 705)
    CNCSpeedDefList = ("XY", "UV", "XYZ", "InvertTime")
    CNCSpeedDefCB = ttk.Combobox(root, textvariable= tk.StringVar(), width = 15,\
                                 values=CNCSpeedDefList, style="office.TCombobox")
    CNCSpeedDefCB.place(x = 1300, y = 705) 


    # Ver2.1 変更
    #【カット面距離入力コンソール1】   
    XYDistLabel = tk.Label(root, text="XY面距離[mm]",font=("",12))
    XYDistLabel.place(x = 850, y = 735)
    XYDistEntry = tk.Entry(root, width=8,font=("",12))     
    XYDistEntry.insert(tk.END, config.XY_DIST)
    XYDistEntry.place(x = 1000, y = 735)  

    # Ver2.1 追加
    #【カット面距離入力コンソール2】   
    UVDistLabel = tk.Label(root, text="UV面距離[mm]",font=("",12))
    UVDistLabel.place(x = 1150, y = 735)
    UVDistEntry = tk.Entry(root, width=8,font=("",12))     
    UVDistEntry.insert(tk.END, config.UV_DIST)
    UVDistEntry.place(x = 1300, y = 735)  


    #Ver2.1 追加 
    #【XY-UV面距離入力コンソール】   
    WorkLengthLabel = tk.Label(root, text="XY-UV面距離[mm]",font=("",12))
    WorkLengthLabel.place(x = 850, y = 760)
    WorkLengthEntry = tk.Entry(root, width=8,font=("",12))     
    WorkLengthEntry.insert(tk.END, config.WORK_LENGTH)
    WorkLengthEntry.place(x = 1000, y = 760)


    #Ver2.1 位置変更 
    #【マシン距離入力コンソール】   
    MachDistLabel = tk.Label(root, text="駆動面距離[mm]",font=("",12))
    MachDistLabel.place(x = 1150, y = 760)
    MachDistEntry = tk.Entry(root, width=8,font=("",12))     
    MachDistEntry.insert(tk.END, config.MACH_DIST)
    MachDistEntry.place(x = 1300, y = 760)  


    #======================================================================================================================================
    #            ボタンインスタンスの生成
    #======================================================================================================================================

    #【X-Y用 dxfファイル読込用のエクスプローラーを開くボタン】
    LoadBtn0 = tk.Button(root, text="開く", command = lambda: open_dxf_explorer(dxf0, FileNameEntry0, MessageWindow))
    LoadBtn0.place(x=1160, y=30)  

    #【U-V用 dxfファイル読込用のエクスプローラーを開くボタン】   
    LoadBtn1 = tk.Button(root, text="開く", command = lambda: open_dxf_explorer(dxf1, FileNameEntry1, MessageWindow))
    LoadBtn1.place(x=1560, y=30)    

    #【X-Y用 dxfファイル名の読込ボタン】
    LoadBtn0 = tk.Button(root, text="再読込", command = lambda: load_file(dxf0, FileNameEntry0, MessageWindow))
    LoadBtn0.place(x=1200, y=30)  

    #【U-V用 dxfファイル名の読込ボタン】   
    LoadBtn1 = tk.Button(root, text="再読込", command = lambda: load_file(dxf1, FileNameEntry1, MessageWindow))
    LoadBtn1.place(x=1600, y=30)    


    #【X-Y用 オフセット距離反映ボタン】
    OffsetBtn0 = tk.Button(root, text="オフセット量設定", width = 15, bg='#fffacd', \
                         command = lambda: Set_OffsetDist(dxf0, OffsetDistEntry0, MessageWindow))
    OffsetBtn0.place(x=1125, y=492)  


    #【U-V用 オフセット距離反映ボタン】
    OffsetBtn1 = tk.Button(root, text="オフセット量設定", width = 15, bg='#fffacd', \
                         command = lambda: Set_OffsetDist(dxf1, OffsetDistEntry1, MessageWindow))
    OffsetBtn1.place(x=1525, y=492)  


    #【configファイル読込用のエクスプローラーを開くボタン】
    ConfigLoadBtn0 = tk.Button(root, text="開く", command = lambda: load_config(config, ConfigFileEntry, \
                                                                              dlEntry, CutSpeedEntry, XYDistEntry, UVDistEntry, \
                                                                                  WorkLengthEntry, MachDistEntry, MessageWindow))
    ConfigLoadBtn0.place(x=1207, y=570)  

    #【オフセット関数ファイル読込用のエクスプローラーを開くボタン】   
    OffsetFuncLoadBtn1 = tk.Button(root, text="開く", command = lambda: load_offset_func(config, OffsetFuncEntry, MessageWindow))
    OffsetFuncLoadBtn1.place(x=1207, y=532)    

    #【オフセット値更新ボタン】    
    OffsetBtn = tk.Button(root, text = "溶け量ファイルからオフセット量設定", height = 1, width = 34, font=("",10),  bg='#fffacd', \
                          command = lambda: Set_OffsetDistFromFunction(dxf0, dxf1, XYDistEntry, UVDistEntry, MachDistEntry, CutSpeedEntry, config.offset_function, MessageWindow))
    OffsetBtn.place(x = 1255, y = 532)


    #【原点オフセットボタン】
    OriginOffsetBtn0 = tk.Button(root, text="全体オフセット更新", width =15, command = lambda: offset_origin(dxf0, dxf1, OriginOffsetEntry_X, OriginOffsetEntry_Y, MessageWindow))
    OriginOffsetBtn0.place(x=1205, y=607)   

    #【X-Yラインテーブル用　カット方向入れ替えボタン】
    ChangeCutDirBtn0 = tk.Button(root, text="カット方向入替え", width =15, bg = "#3cb371", command = lambda: Change_CutDir(dxf0, dxf1, chkValue, MessageWindow))
    ChangeCutDirBtn0.place(x=855, y=435)   
    
    #【X-Yラインテーブル用　ライン整列ボタン】    
    AutoAlignmentBtn0 = tk.Button(root, text="ライン整列", width =15, bg = "#3cb371", command = lambda: AutoLineSort(dxf0, dxf1, chkValue, MessageWindow))
    AutoAlignmentBtn0.place(x=990, y=435)
            
    #【X-Yラインテーブル用　カット順逆転ボタン】    
    ReverseBtn0 = tk.Button(root, text="カット順逆転", width =15, bg = "#3cb371", command = lambda: Reverse(dxf0, dxf1, chkValue, MessageWindow))
    ReverseBtn0.place(x=1125, y=435)  
    
    
    #【X-Yラインテーブル用　ライン結合ボタン】
    SwapBtn0 = tk.Button(root, text="ライン結合", width =15, bg = "#4ba3fb", command = lambda: Merge_line(dxf0, MessageWindow))
    SwapBtn0.place(x=855, y=465) 
        
    #【X-Yラインテーブル用　ライン削除ボタン】    
    DelateBtn0 = tk.Button(root, text="ライン削除", width = 15, bg = "#ff6347", command = lambda: delete_line(dxf0, MessageWindow))
    DelateBtn0.place(x=990, y=465)
  
  
    #【U-Vラインテーブル用　カット方向入れ替えボタン】    
    ChangeCutDirBtn1 = tk.Button(root, text="カット方向入替え", width =15, bg = "#3cb371", command = lambda: Change_CutDir(dxf1, dxf0, chkValue, MessageWindow))
    ChangeCutDirBtn1.place(x=1255, y=435)
    
    #【U-Vラインテーブル用　ライン整列ボタン】    
    AutoAlignmentBtn1 = tk.Button(root, text="ライン整列", width =15, bg = "#3cb371", command = lambda: AutoLineSort(dxf1, dxf0, chkValue, MessageWindow))
    AutoAlignmentBtn1.place(x=1390, y=435)
    
    #【U-Vラインテーブル用　カット順逆転ボタン】    
    ReverseBtn1 = tk.Button(root, text="カット順逆転", width =15, bg = "#3cb371", command = lambda: Reverse(dxf1, dxf0, chkValue, MessageWindow))
    ReverseBtn1.place(x=1525, y=435)   
    
    
    #【U-Vラインテーブル用　ライン結合ボタン】    
    DelateBtn1 = tk.Button(root, text="ライン結合", width = 15, bg = "#4ba3fb" , command = lambda: Merge_line(dxf1, MessageWindow))
    DelateBtn1.place(x=1255, y=465)   
 
    #【U-Vラインテーブル用　ライン削除ボタン】    
    DelateBtn1 = tk.Button(root, text="ライン削除", width = 15, bg = "#ff6347" , command = lambda: delete_line(dxf1, MessageWindow))
    DelateBtn1.place(x=1390, y=465)
    
    """
    #【自動整列ボタン】    
    AutoAlignmentBtn = tk.Button(root, text = "自動整列", height = 1, width = 12, font=("",12), bg='#fffacd', command = lambda: AutoLineSort(dxf0, dxf1, MessageWindow))
    AutoAlignmentBtn.place(x = 1530, y = 555)
    """

    #Ver2.0 変更　WorkDistWntryを追加
    #【パスチェックボタン】    
    ChkPassBtn = tk.Button(root, text = "パスチェック", height = 2, width = 14,font=("",12), bg='#3cb371', \
                           command = lambda: path_chk(root, dxf0, dxf1, AutoAlignmentEntry_X, AutoAlignmentEntry_Y, CutEndEntry_X, CutEndEntry_Y, XYDistEntry, UVDistEntry, WorkLengthEntry, MachDistEntry, dlEntry, MessageWindow))
    ChkPassBtn.place(x = 1530, y = 690)
    

    #Ver2.0 変更　MechDistEntry, WorkDistWntryを追加
    #【Gコード生成ボタン】        
    GenGCodeBtn = tk.Button(root, text = "Gコード生成", height = 2, width = 14,font=("",12), bg='#ff6347', \
                            command = lambda: gen_g_code(dxf0, dxf1, AutoAlignmentEntry_X, AutoAlignmentEntry_Y, CutEndEntry_X, CutEndEntry_Y, XYDistEntry, UVDistEntry, WorkLengthEntry, MachDistEntry, CutSpeedEntry, dlEntry, MessageWindow, config))
    GenGCodeBtn.place(x = 1530, y = 740)



    #======================================================================================================================================
    #        Checkbuttonインスタンスの生成
    #======================================================================================================================================

    #【U-V画面とX-Y画面の連動チェックボックス】
    chkValue = tk.BooleanVar()
    chk0 = tk.Checkbutton(root, text="U-V画面をX-Y画面に連動させる", var=chkValue , command =  lambda: XY_UV_Link(chkValue, table0, table1, MessageWindow))
    chk0.place(x=1460, y=5)
    

    #======================================================================================================================================
    #                 メインループ
    #======================================================================================================================================

    tk.mainloop()
