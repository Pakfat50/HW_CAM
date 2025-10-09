# -*- coding: utf-8 -*-
"""HW_CAMソフトウェア本体

"""

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


class Config:
    """CAMで使用する設定値を格納するクラス

    Attributes:
        FILENAME_XY(str): デフォルトで読み込むXYのdxfファイル名（起動時にのみ変更）
        FILENAME_UV(str): デフォルトで読み込むUVのdxfファイル名（起動時にのみ変更）
        OX(float): 切り出しの始点座標
        OY(float): 切り出しの始点座標
        EX(float): 切り出しの終点座標
        EY(float): 切り出しの終点座標
        DELTA_LENGTH(float): G Codeの点群の間隔
        XY_OFFSET_DIST(float): XY座標面のオフセット距離
        UV_OFFSET_DIST(float): UV座標面のオフセット距離
        CUTSPEED(float): カット速度
        XY_DIST(float): XY断面とマシン駆動面との距離
        UV_DIST(float): UV断面とマシン駆動面との距離
        CS_DEF(str): カット速度定義面
        CNC_CS_DEF(str): CNCコントローラーのカット速度定義
        MACH_DIST(float): マシン駆動面の距離
        OFFSET_X(float): 原点X座標
        OFFSET_Y(float): 原点Y座標
        ROTATE(float): 回転角度
        HEADER(str): Gコードの書き出し文字列
        X_STR(str): G01でのX軸名称
        Y_STR(str): G01でのY軸名称
        U_STR(str): G01でのU軸名称
        V_STR(str): G01でのV軸名称
        REFINE(bool): True:読み込み時にスプラインをリファインする, False:しない
        REMOVE_COLLISION(bool): True:自己交差を修正する, False:しない
        offset_function(scipy.interpolate.interp1d): オフセット距離の算出に使用する関数オブジェクト        

    """
    def __init__(self):
        """Configクラスのコンストラクタ

        メンバ変数をデフォルト値に設定する。  

        """

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
        """指定されたパスのコンフィギュレーションを読み込む。

        file_pathで与えられるcsvファイルを開き、csvファイルから読み込んだ値をメンバ変数に設定する。問題があればデフォルト値を設定する

        Args:
            file_path (str): コンフィギュレーションを記述したcsvファイルのパス

        """
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
        """指定されたパスのオフセット関数を読み込む

        file_pathで与えられるcsvファイルを開き、csvファイルから読み込んだ値からoffset_functionを更新する。問題があればデフォルト値を設定する

        Args:
            file_path (str): オフセット関数を記述したcsvファイルのパス
        """

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


def open_file_explorer(entry):
    """エクスプローラーからファイルパスを取得し、entryに挿入する

    Args:
        entry (tkinter.Entry): ファイルパスを入力するエントリー

    Note:
        https://shizenkarasuzon.hatenablog.com/entry/2020/03/21/002600
        
    """
    fTyp = [("","*")]
    # Current directoryは、exeから実行する場合とスクリプトから実行する場合で異なるので、get_Curdirを用いて取得
    iDir = get_curdir()
    data = tk.filedialog.askopenfilename(filetypes = fTyp,initialdir = iDir)
    # キャンセルされた場合は、更新しない
    if not(len(data)==0):
        entry.delete(0,tk.END)
        entry.insert(tk.END, data)


def load_config(config, config_entry, dl_entry, xy_offset_entry, uv_offset_entry,\
                cut_speed_entry, cut_speed_def_cb, cnc_speed_def_cb,\
                xy_dist_entry, uv_dist_entry, mach_dist_entry, message_window):
    """エクスプローラーを用いて設定ファイルを読み込み、各種エントリーを更新する

    open_file_explorerを用いて、config_entryにconfigファイルのパスを設定する。

    configクラスのload_configメソッドを使用して、configファイルのパスを読みこみ、configオブジェクトの値を更新する。

    各エントリーの値を、configオブジェクトの値に更新する。

    MessageWindowにconfig.load_configの結果およびGコードの書き出しを出力する。

    Args:
        config (Config): CAMで使用する設定値を格納するクラス
        config_entry (tkinter.Entry): 設定ファイルのパスを入力するエントリー
        dl_entry (tkinter.Entry): 分割距離を入力するエントリー
        xy_offset_entry (tkinter.Entry): XY面のオフセット距離を入力するエントリー
        uv_offset_entry (tkinter.Entry): UV面のオフセット距離を入力するエントリー
        cut_speed_entry (tkinter.Entry): カット速度を入力するエントリー
        cut_speed_def_cb (tkinter.Combobox): カット速度定義面のコンボボックス
        cnc_speed_def_cb (tkinter.Combobox): CNC速度定義のコンボボックス
        xy_dist_entry (tkinter.Entry): XY面距離を入力するエントリー
        uv_dist_entry (tkinter.Entry): UV面距離を入力するエントリー
        mach_dist_entry (tkinter.Entry): 駆動面距離を入力するエントリー
        message_window (MesseageWindow): メッセージウィンドウ
    """
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
    mach_dist_entry.delete(0,tk.END)
    mach_dist_entry.insert(tk.END, config.MACH_DIST)  
        
    message_window.set_messeage(config.MESSEAGE)
    message_window.set_messeage("Gコードの書き出しは「%s」です。\n"%config.HEADER)


def load_offset_func(config, offset_func_entry, message_window):
    """エクスプローラーを用いて溶け量ファイルを読み込む

    open_file_explorerを用いて、offset_func_entryに溶け量ファイルのパスを設定する。

    configクラスのload_offset_funcメソッドを使用して、溶け量ファイルのパスを読みこみ、configオブジェクトのoffset_functionのメンバーを更新する。

    MessageWindowにconfig.load_offset_funcの結果を出力する。

    Args:
        config (Config): CAMで使用する設定値を格納するクラス
        offset_func_entry (tkinter.Entry): 溶け量ファイルのパスを入力するエントリー
        message_window (MesseageWindow): メッセージウィンドウ
    """
    open_file_explorer(offset_func_entry)
    offset_file_path = offset_func_entry.get()
    config.load_offset_func(offset_file_path)
    
    message_window.set_messeage(config.MESSEAGE)


def open_dxf_explorer(dxf_obj, entry, is_spline_refine, messeage_window):
    """エクスプローラーを用いてdxfファイルを読み込む

    open_file_explorerを用いて、dxfファイルのパスを取得し、エントリーへ設定する。

    load_fileにdxfファイルのパスを渡し、DxfFileオブジェクトを更新する。

    Args:
        dxf_obj (DxfFile): dxfファイルを設定するDxfFileクラス
        entry (tkinter.Entry): dxfファイルのパスを入力するエントリー
        is_spline_refine (bool): True: スプライン点列をリファインして読み込む, False:リファインしない
        messeage_window (MesseageWindow): メッセージウィンドウ
    """
    open_file_explorer(entry)
    load_file(dxf_obj, entry, is_spline_refine, messeage_window)


def load_file(dxf_obj, entry, is_spline_refine, messeage_window):
    """dxfファイルをDxfFileクラスに設定する

    Args:
        dxf_obj (DxfFile): dxfファイルを設定するDxfFileクラス
        entry (tkinter.Entry): dxfファイルのパスを入力するエントリー
        is_spline_refine (bool): True: スプライン点列をリファインして読み込む, False:リファインしない
        messeage_window (MesseageWindow): メッセージウィンドウ
    """
    
    # dxfファイルのパスを取得
    filename = entry.get()
    # リファインするかどうかを取得
    is_refine = is_spline_refine.get()
    
    # dxfファイルが存在する場合
    if file_chk(filename) == 1:
        # 原点、回転中心、回転角を引き継ぐため、一時変数に格納
        ox = dxf_obj.ox
        oy = dxf_obj.oy
        rx = dxf_obj.rx
        ry = dxf_obj.ry
        sita = dxf_obj.sita
        
        # dxfファイルを読み込み
        dxf_obj.load_file(filename, is_refine)
        # 前の図面での原点を引き継ぎ
        dxf_obj.offset_origin(ox, oy)
        # 前の図面での回転角度・回転中心を引き継ぎ
        dxf_obj.rotate(sita, rx, ry)
        # 図面を更新
        dxf_obj.update(keep_view = False)
        # 結果をメッセージウィンドウに出力
        if is_refine == True:
            messeage_window.set_messeage("%sを点列をリファインして読み込みました。\n"%filename)
        else:
            messeage_window.set_messeage("%sをDXFファイルの座標点のまま読み込みました。\n"%filename)
    
    # 拡張子がdxfでないファイルが選択された場合
    if file_chk(filename) == 0:
        # 結果をメッセージウィンドウに出力
        messeage_window.set_messeage("%sを読み込めません。拡張子が.dxfであることを確認して下さい。\n"%filename)  
    
    # ファイルが存在しない場合
    if file_chk(filename) == -1:   
        # 結果をメッセージウィンドウに出力     
        messeage_window.set_messeage("%sを読み込めません。ファイルが存在することを確認して下さい。\n"%filename)  
   
    
def xy_uv_link(is_xy_uv_link, xy_table, uv_table, messeage_window):
    """XYとUV画面を連動するように設定し、設定変更を通知する

    Args:
        is_xy_uv_link (bool): True:XYテーブルをUVテーブルと同期する, False:しない
        xy_table (SuperTable): XYテーブル
        uv_table (SuperTable): UVテーブル
        messeage_window (MesseageWindow): メッセージウィンドウ
    """
    # 連動する場合
    if is_xy_uv_link.get():
        xy_table.set_sync(True)
        uv_table.set_sync(True)
        messeage_window.set_messeage("U-V画面をX-Y画面と連動\n")
    # 連動しない場合
    else:
        xy_table.set_sync(False)
        uv_table.set_sync(False)   
        messeage_window.set_messeage("U-V画面とX-Y画面の連動を解除\n")


def enable_remove_self_collision(is_remove_collision, messeage_window):
    """自己交差除去の設定変更を通知する

    Args:
        is_remove_collision (bool): True:自己交差を除去する, False:しない
        messeage_window (MesseageWindow): メッセージウィンドウ
    """
    # 自己交差を除去する場合
    if is_remove_collision.get():
        messeage_window.set_messeage("自己交差除去を有効化\n")
    # 自己交差を除去しない場合
    else:
        messeage_window.set_messeage("自己交差除去を無効化\n")


def enable_spline_refine(is_spline_refine, messeage_window):
    """リファインの設定変更を通知する

    Args:
        is_spline_refine (bool): True:スプライン点列をリファインして読み込む, False:リファインしない
        messeage_window (MesseageWindow): メッセージウィンドウ
    """
    # リファインする場合
    if is_spline_refine.get():
        messeage_window.set_messeage("スプライン点列のリファインを有効化\n")
    # リファインしない場合
    else:
        messeage_window.set_messeage("スプライン点列のリファインを無効化\n")


def enable_3d_path_check(is_3d_path_check, messeage_window):
    """パスチェックの設定変更を通知する

    Args:
        is_3d_path_check (bool): True:3Dでパスチェックする, False:2Dでパスチェックする
        messeage_window (MesseageWindow): メッセージウィンドウ
    """
    # 3Dでパスチェックをする場合
    if is_3d_path_check.get():
        messeage_window.set_messeage("パスチェックを3Dで実施\n")
    # 2Dでパスチェックをする場合
    else:
        messeage_window.set_messeage("パスチェックを2Dで実施\n")


def change_cut_dir(dxf_obj, x_dxf_obj, is_xy_uv_link, name, x_name, messeage_window):
    """テーブルで選択されている線のカット方向を入れ替え、結果を通知する

    Args:
        dxf_obj (DxfFile): 自身のDxfFileクラス
        x_dxf_obj (DxfFile): 相手のDxfFileクラス
        is_xy_uv_link (bool): True:XYテーブルをUVテーブルと同期する, False:しない
        name (str): 自身のテーブルの名称
        x_name (str): 相手のテーブルの名称
        messeage_window (MesseageWindow): メッセージウィンドウ
    
    Note:
        is_xy_uv_link=Trueの場合、相手のテーブルに対しても同様の操作を実施する。
        
    """

    # 選択されている線のカット方向を入れ替え
    dxf_obj.change_cut_dir()
    # グラフ・テーブルを更新
    dxf_obj.update()
    # 結果をメッセージウィンドウへ出力
    messeage_window.set_messeage("%sのカット方向を逆転\n"%name)

    # XY-UV画面を連動する場合
    if is_xy_uv_link.get():
        # 相手のテーブルの選択されている線のカット方向を入れ替え
        x_dxf_obj.change_cut_dir()
        # 相手のグラフ・テーブルを更新
        x_dxf_obj.update()
        # 結果をメッセージウィンドウへ出力
        messeage_window.set_messeage("%sのカット方向を逆転\n"%x_name)
    
    
def auto_sort_line(dxf_obj, x_dxf_obj, is_xy_uv_link, name, x_name, messeage_window): 
    """テーブルで選択した線を起点として、テーブル内の線を一筆書きとなるように並び替える

    Args:
        dxf_obj (DxfFile): 自身のDxfFileクラス
        x_dxf_obj (DxfFile): 相手のDxfFileクラス
        is_xy_uv_link (bool): True:XYテーブルをUVテーブルと同期する, False:しない
        name (str): 自身のテーブルの名称
        x_name (str): 相手のテーブルの名称
        messeage_window (MesseageWindow): メッセージウィンドウ
    
    Note:
        is_xy_uv_link=Trueの場合、相手のテーブルに対しても同様の操作を実施する。
        
        並び替え中に発生した例外は、標準出力へ表示した上で、output_logによりエラーファイルにも出力する。

    """
    try:
        # 自動整列を実行
        ret = dxf_obj.sort_line()
        # 選択されている線の本数が1本の場合
        if ret == 1:
            # 並び替えの起点となった線（テーブルで一番上の線）を選択
            dxf_obj.select_index(0)
            # グラフ・テーブルを更新
            dxf_obj.update()
            # 結果を出力
            messeage_window.set_messeage("%sを自動整列しました。\n"%name)
        # 選択されている線の本数が1本でない場合
        else:
            messeage_window.set_messeage("%sで%s本の線が選択されています。起点とする１本の線のみを選択してください。\n"%(name,ret))
        
        # XY-UV画面を連動する場合
        if is_xy_uv_link.get():
            # 相手のテーブルで自動整列を実行
            x_ret = x_dxf_obj.sort_line()
            # 相手のテーブルで選択されている線が1本の場合
            if x_ret == 1:
                # 相手のテーブルで並び替えの起点となった線（テーブルで一番上の線）を選択
                x_dxf_obj.select_index(0)
                # 相手のグラフ・テーブルを更新
                x_dxf_obj.update()
                # 結果をメッセージウィンドウへ出力 
                messeage_window.set_messeage("%sを自動整列しました。\n"%x_name)
            # 相手のテーブルで選択されている線の本数が1本でない場合
            else:
                messeage_window.set_messeage("%sで%s本の線が選択されています。起点とする１本の線のみを選択してください。\n"%(x_name,ret))
        
    except:
        # 例外の標準出力
        traceback.print_exc()
        # 例外のログ出力
        output_log(traceback.format_exc())
        pass


def reverse_line(dxf_obj, x_dxf_obj, is_xy_uv_link, name, x_name, messeage_window):
    """選択した画面のカット方向をすべて反転させる

    Args:
        dxf_obj (DxfFile): 自身のDxfFileクラス
        x_dxf_obj (DxfFile): 相手のDxfFileクラス
        is_xy_uv_link (bool): True:XYテーブルをUVテーブルと同期する, False:しない
        name (str): 自身のテーブルの名称
        x_name (str): 相手のテーブルの名称
        messeage_window (MesseageWindow): メッセージウィンドウ

    Note:
        is_xy_uv_link=Trueの場合、相手のテーブルに対しても同様の操作を実施する。

    """
    # テーブル内の線のカット方向反転＆線のならびを反転
    dxf_obj.reverse_all()
    # グラフ・テーブルを更新
    dxf_obj.update()
    # 結果をメッセージウィンドウへ出力
    messeage_window.set_messeage("%sのカット順を逆転しました。\n"%name)

    # XY-UV画面を連動する場合
    if is_xy_uv_link.get():
        # 相手のテーブル内の線のカット方向反転＆線のならびを反転
        x_dxf_obj.reverse_all()
        # 相手のテーブル・グラフを更新
        x_dxf_obj.update()
        # 結果をメッセージウィンドウへ出力
        messeage_window.set_messeage("%sのカット順を逆転しました。\n"%x_name)



def merge_line(dxf_obj, x_dxf_obj, is_xy_uv_link, is_remove_collision, name, x_name, messeage_window):
    """テーブル内で選択した線を結合する

    Args:
        dxf_obj (DxfFile): 自身のDxfFileクラス
        x_dxf_obj (DxfFile): 相手のDxfFileクラス
        is_xy_uv_link (bool): True:XYテーブルをUVテーブルと同期する, False:しない
        is_remove_collision (bool): True:自己交差を除去する, False:しない
        name (str): 自身のテーブルの名称
        x_name (str): 相手のテーブルの名称
        messeage_window (MesseageWindow): メッセージウィンドウ

    Note:
        is_xy_uv_link=Trueの場合、相手のテーブルに対しても同様の操作を実施する。

        is_remove_collision=Trueの場合、結合後の線に対して、自己交差を除去する。

    """
    # 選択された線を結合
    results, line_nums = dxf_obj.merge_selected_line()
    # 選択された線の本数が2本以上の場合
    if len(results) >= 2:
        # 結合結果を出力
        i = 1
        while i < len(results):
            if results[i] == True:
                messeage_window.set_messeage("%sの%s番目のラインに%s番目のラインを結合しました。\n"%(name,line_nums[0],line_nums[i]))
            else:
                messeage_window.set_messeage("%sの%s番目のラインを結合できませんでした。ライン端点が接しているかを確認してください。\n"%(name,line_nums[i]))
            i += 1
        # 自己交差を除去が有効の場合
        if is_remove_collision.get():
            # remove_collisionにより自己交差を除去
            remove_collision(dxf_obj, name, messeage_window)
        # テーブル・グラフを更新
        dxf_obj.update()
    # 選択された線の本数が2本未満の場合
    else:
        # 結果をメッセージウィンドウに出力
        messeage_window.set_messeage("%sで２本以上のラインを選択して下さい。%s本のラインが選択されています。\n"%(name,len(line_nums)))
    
    # XY-UV画面を連動する場合
    if is_xy_uv_link.get():
        # 相手テーブルの選択された線を結合
        x_results, x_line_nums = x_dxf_obj.merge_selected_line()
        
        # 相手テーブルで選択された線の本数が2本以上の場合
        if len(x_results) >= 2:
            # 結合結果を出力
            i = 1
            while i < len(x_results):
                if x_results[i] == True:
                    messeage_window.set_messeage("%sの%s番目のラインに%s番目のラインを結合しました。\n"%(x_name,x_line_nums[0],x_line_nums[i]))
                else:
                    messeage_window.set_messeage("%sの%s番目のラインを結合できませんでした。ライン端点が接しているかを確認してください。\n"%(x_name,x_line_nums[i]))
                i += 1
            # 自己交差を除去が有効の場合
            if is_remove_collision.get():
                # remove_collisionにより自己交差を除去
                remove_collision(x_dxf_obj, x_name, messeage_window)      
            # テーブル・グラフを更新    
            x_dxf_obj.update()
        # 相手のテーブルで選択された線の本数が2本未満の場合
        else:
            # 結果をメッセージウィンドウに出力
            messeage_window.set_messeage("%sで２本以上のラインを選択して下さい。%s本のラインが選択されています。\n"%(x_name,len(x_line_nums)))
        
  
def separate_line(dxf_obj, is_remove_collision, name, messeage_window):
    """テーブルで選択した線を、グラフで選択した分割点で分割する

    Args:
        dxf_obj (DxfFile): DxfFileクラス
        is_remove_collision (bool): True:自己交差を除去する, False:しない
        name (str): テーブルの名称
        messeage_window (MesseageWindow): メッセージウィンドウ

    Note:
        is_remove_collision=Trueの場合、分割後の線に対して、自己交差を除去する。

    """
    # 分割点での分割を実行
    result, line_nums, point_index = dxf_obj.separate_line()
    # 分割成功の場合
    if result == True:
        # メッセージウィンドウに結果を出力
        messeage_window.set_messeage("%sで%s番目のラインを分割し、%s番目のラインを作成しました\n"%(name,line_nums[0], line_nums[1]))
        # 自己交差を除去が有効の場合
        if is_remove_collision.get():
            # remove_collisionにより自己交差を除去
            remove_collision(dxf_obj, name, messeage_window) 
        # テーブル・グラフを更新
        dxf_obj.update()
    # 分割失敗の場合
    else:
        # 選択されている線の数が1本以外の場合
        if not (len(line_nums) == 1):
            messeage_window.set_messeage("%sで%s本のラインが選択されています。1本のみ選択してださい\n"%(name,len(line_nums)))
        # 分割点が選択されていない場合
        elif point_index == None:
            messeage_window.set_messeage("%sで分割点を選択してださい\n"%name)
        # 分割点が端点の場合
        else:
            messeage_window.set_messeage("%sで端点が選択されています。端点以外を選択してださい\n"%name)
        
        
def delete_line(dxf_obj, x_dxf_obj, is_xy_uv_link, is_remove_collision, name, x_name, messeage_window):
    """テーブルで選択した線を削除する

    Args:
        dxf_obj (DxfFile): 自身のDxfFileクラス
        x_dxf_obj (DxfFile): 相手のDxfFileクラス
        is_xy_uv_link (bool): True:XYテーブルをUVテーブルと同期する, False:しない
        is_remove_collision (bool): True:自己交差を除去する, False:しない
        name (str): 自身のテーブルの名称
        x_name (str): 相手のテーブルの名称
        messeage_window (MesseageWindow): メッセージウィンドウ

    Note:
        is_xy_uv_link=Trueの場合、相手のテーブルに対しても同様の操作を実施する。

        is_remove_collision=Trueの場合、削除後の線に対して、自己交差を除去する。        

    """
    # 選択した線を削除
    dxf_obj.delete_selected_line()
    # 結果をメッセージウィンドウに出力
    messeage_window.set_messeage("%sの選択したラインを削除しました。\n"%name)
    # 自己交差を除去が有効の場合
    if is_remove_collision.get():
        # 削除後の線に対して、remove_collisionにより自己交差を除去
        remove_collision(dxf_obj, name, messeage_window) 
    # テーブル・グラフを更新
    dxf_obj.update()

    # XY-UV画面を連動する場合
    if is_xy_uv_link.get():
        # 相手のテーブルで選択されている線を削除
        x_dxf_obj.delete_selected_line()
        # 結果をメッセージウィンドウに出力
        messeage_window.set_messeage("%sの選択したラインを削除しました。\n"%x_name)
        # 自己交差を除去が有効の場合
        if is_remove_collision.get():
            # 相手のテーブルでの削除後の線に対して、remove_collisionにより自己交差を除去
            remove_collision(x_dxf_obj, x_name, messeage_window)       
        # 相手のテーブル・グラフを更新
        x_dxf_obj.update()
        
    
def set_offset_dist(dxf_obj, entry, x_dxf_obj, x_entry, is_xy_uv_link, is_remove_collision, name, x_name, messeage_window):
    """オフセット距離を設定する

    Args:
        dxf_obj (DxfFile): 自身のDxfFileクラス
        entry (tkinter.Entry): 自身のオフセット距離の入力エントリー
        x_dxf_obj (DxfFile): 相手のDxfFileクラス
        x_entry (tkinter.Entry): 相手のオフセット距離の入力エントリー
        is_xy_uv_link (bool): True:XYテーブルをUVテーブルと同期する, False:しない
        is_remove_collision (bool): True:自己交差を除去する, False:しない
        name (str): 自身のテーブルの名称
        x_name (str): 相手のテーブルの名称
        messeage_window (MesseageWindow): メッセージウィンドウ

    Note:
        is_xy_uv_link=Trueの場合、相手のテーブルに対しても同様の操作を実施する。

        is_remove_collision=Trueの場合、オフセット後の線に対して、自己交差を除去する。

        オフセット距離が実数値でない場合は、例外を発生させ、標準出力へ表示した上で、output_logによりエラーファイルにも出力する。

    """
    try:
        # オフセット距離を取得
        entry_value = entry.get()
        # オフセット距離を実数へキャスト->数値以外の場合は例外発生
        offset_dist = float(entry_value)
        # オフセット距離を設定
        dxf_obj.set_offset_dist(offset_dist)
        # 結果をメッセージウィンドウに出力
        messeage_window.set_messeage("%sのオフセット距離を%sに設定しました。\n"%(name, offset_dist))
        # 自己交差を除去が有効の場合 
        if is_remove_collision.get():
            # remove_collisionにより自己交差を除去
            remove_collision(dxf_obj, name, messeage_window)
        # テーブル・グラフを更新
        dxf_obj.update()
        
        # XY-UV画面を連動する場合
        if is_xy_uv_link.get():
            # 相手のテーブルのオフセット距離を取得
            x_entry_value = x_entry.get()
            # 相手のテーブルのオフセット距離を実数へキャスト->数値以外の場合は例外発生
            x_offset_dist = float(x_entry_value)
            # 相手のテーブルへオフセット距離を設定
            x_dxf_obj.set_offset_dist(x_offset_dist)
            # 結果をメッセージウィンドウに出力
            messeage_window.set_messeage("%sのオフセット距離を%sに設定しました。\n"%(x_name, x_offset_dist))
            # 自己交差を除去が有効の場合 
            if is_remove_collision.get():
                # remove_collisionにより相手のテーブルの線に対して、自己交差を除去
                remove_collision(x_dxf_obj, x_name, messeage_window)
            # 相手のテーブル・グラフを更新    
            x_dxf_obj.update()
                
    except:
        # 実数値以外の場合、キャストエラーを補足
        traceback.print_exc()
        output_log(traceback.format_exc())
        messeage_window.set_messeage("実数値を入力して下さい。\n")
        pass

def remove_collision(dxf_obj, name, messeage_window):
    """dxf_objに含まれる線について、自己交差を除去する

    Args:
        dxf_obj (DxfFile): DxfFileクラス
        name (str): テーブルの名称
        messeage_window (MesseageWindow): メッセージウィンドウ

    Note:
        自己交差を除去では、線内の自己交差と、線同士の交差の２種類を除去する
        
    """
    # 線の内部の自己交差を除去
    self_collision_list = dxf_obj.remove_self_collision()
    # 線同士の交差を除去
    collision_line_list = dxf_obj.remove_line_collision()

    # 線の内部の自己交差があった場合
    if len(self_collision_list) > 0:
        # 自己交差のあった線を通知
        for num in self_collision_list:
            messeage_window.set_messeage("%sの%s番目の線で自己交差を修正しました。形状に問題がないかをチェックしてください。\n"%(name, num))
    # 線同士の交差があった場合
    if len(collision_line_list) > 0:
        # 交差のあった線のペアを通知
        for nums in collision_line_list:
            messeage_window.set_messeage("%sの%s本目と%s本目の線で自己交差を修正しました。形状に問題がないかをチェックしてください。\n"%(name, nums[0], nums[1]))            


def replace_g_code(g_code_str, x_str, y_str, u_str, v_str):
    """Gコード内の軸名称を指定のものに置き換える

    +--------------+---------------+-------------+
    |CAMでの軸名称 |対応する軸名称 |備考         |
    +--------------+---------------+-------------+
    |X             |x_str          |X-Y平面のX軸 |
    +--------------+---------------+-------------+
    |Y             |y_str          |X-Y平面のY軸 |
    +--------------+---------------+-------------+
    |U             |u_str          |U-V平面のU軸 |
    +--------------+---------------+-------------+
    |V             |v_str          |U-V平面のV軸 |
    +--------------+---------------+-------------+

    Args:
        g_code_str (str): Gコード命令の文字列
        x_str (str): CAMのX軸名称
        y_str (str): CAMのY軸名称
        u_str (str): CAMのU軸名称
        v_str (str): CAMのV軸名称

    Returns:
        str: 置換後のGコード命令の文字列
    """

    # Gコード命令が移動命令のフォーマットであることをチェック
    if ('G' in g_code_str) and ('X' in g_code_str) and ('Y' in g_code_str) and ('U' in g_code_str) and ('V' in g_code_str):
        # 軸名称を置換(元のGコード命令では、CAMの軸名称が付けられている)
        new_g_code_str = g_code_str
        new_g_code_str = new_g_code_str.replace('X', x_str)
        new_g_code_str = new_g_code_str.replace('Y', y_str)
        new_g_code_str = new_g_code_str.replace('U', u_str)
        new_g_code_str = new_g_code_str.replace('V', v_str)
        return new_g_code_str

    else:
        return g_code_str

def make_offset_path(x_array, y_array, u_array, v_array, z_xy, z_uv, z_mach):
    """CNCの駆動面における座標点列を生成する

    .. image:: 
        ../../documents/res/make_offset_path.png

    Args:
        x_array (numpy.array): x座標点列(XY断面)
        y_array (numpy.array): y座標点列(XY断面)
        u_array (numpy.array): u座標点列(UV断面)
        v_array (numpy.array): v座標点列(UV断面)
        z_xy (float): XY面距離
        z_uv (float): UV面距離
        z_mach (float): 駆動面距離

    Returns:
        numpy.array: XY面側のCNC駆動面におけるx座標点列
        numpy.array: XY面側のCNC駆動面におけるy座標点列
        numpy.array: UV面側のCNC駆動面におけるu座標点列
        numpy.array: UV面側のCNC駆動面におけるv座標点列
    """
    
    new_x = []
    new_y = []
    new_u = []
    new_v = []
    
    # Z軸方向の各種距離を計算
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
    
    # XY,UV座標で対応する点について、Z軸方向に線形に外挿し、駆動面での座標を計算
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
    """同時に加工するXY-UV断面の2本の線について、ワーク端／駆動面でのカット速度を計算する

    Args:
        length_xy (float): XY断面の線の長さ
        length_uv (float): UV断面の線の長さ
        z_xy (float): XY面距離
        z_uv (float): UV面距離
        z_mach (float): 駆動面距離
        cut_speed (float): カット速度
        cut_speed_def_value (str): カット速度定義面

    Returns:
        float: XY面側のCNC駆動面でのカット速度
        float: XYワーク端でのカット速度
        float: ワーク中央でのカット速度
        float: UVワーク端でのカット速度
        float: UV面側のCNC駆動面でのカット速度
  
    """

    # Z軸方向の各種距離を計算
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
           
    # ワーク中央での線長を計算
    length_mid = (length_xy + length_uv)/ 2.0

    # CNC駆動面での線長を計算
    dl_XY = length_xy - length_mid
    dl_UV = length_uv - length_mid
    length_XY_Mech = k_xy*dl_XY + length_mid
    length_UV_Mech = k_uv*dl_UV + length_mid

    # 速度を定義する断面の線長を基準長さ(length_def)に設定
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
    
    # 基準長さに対する、各断面での線長の比を計算
    ratio_XY_Mech = length_XY_Mech/length_def
    ratio_XY_Work = length_xy/length_def
    ratio_mid = length_uv/length_def
    ratio_UV_Work = length_uv/length_def
    ratio_UV_Mech = length_UV_Mech/length_def
  
    # 基準長さを指定のカット速度でカットするように
    # カット速度に各断面での線長の比をかけた値を各断面でのカット速度とする
    cs_xy_mech = cut_speed*ratio_XY_Mech
    cs_xy_work = cut_speed*ratio_XY_Work
    cs_mid = cut_speed*ratio_mid
    cs_uv_work = cut_speed*ratio_UV_Work
    cs_uv_mech = cut_speed*ratio_UV_Mech
    
    return cs_xy_mech, cs_xy_work, cs_mid, cs_uv_work, cs_uv_mech



def set_cut_speed(dxf_obj0, dxf_obj1, xy_dist_entry, uv_dist_entry, mach_dist_entry, cut_speed_entry, cut_speed_def_cb):
    """XYテーブルおよびUVテーブルの線のカット速度を設定する

    上下異形状の場合は、対応する線の長さの比と、カット速度を定義する断面からカット速度を設定する。

    Args:
        dxf_obj0 (DxfFile): XY断面のDxfFileクラス
        dxf_obj1 (DxfFile): UV断面のDxfFileクラス
        xy_dist_entry (tkinter.Entry): XY面距離を入力するエントリー
        uv_dist_entry (tkinter.Entry): UV面距離を入力するエントリー
        mach_dist_entry (tkinter.Entry): 駆動面距離を入力するエントリー
        cut_speed_entry (tkinter.Entry): カット速度を入力するエントリー
        cut_speed_def_cb (tkinter.Combobox): カット速度定義面のコンボボックス

    Note:
        上下異形状で線の本数が不一致の場合は、カット速度をそのまま各線のカット速度に設定する。

        エントリーの値が実数値でない場合は、例外を発生させ、標準出力へ表示した上で、output_logによりエラーファイルにも出力する。

    """

    # 各種エントリーの値・コンボボックスの値を取得
    xy_dist_value = xy_dist_entry.get()
    uv_dist_value = uv_dist_entry.get()
    mach_dist_value = mach_dist_entry.get()
    cut_speed_value = cut_speed_entry.get()   
    cut_speed_def_value = cut_speed_def_cb.get()    

    # XY,UVテーブルの行のアイテムIDの一覧を取得
    all_items0 = dxf_obj0.get_item(all=True)
    all_items1 = dxf_obj1.get_item(all=True)
    
    try:
        # エントリーから取得した値を浮動小数点にキャスト->エラーの場合は例外を発生
        z_xy = float(xy_dist_value)
        z_uv = float(uv_dist_value)
        z_mach = float(mach_dist_value)
        cut_speed = float(cut_speed_value)
                    
        # XY-UV断面で線の本数が一致している場合
        if len(all_items0) == len(all_items1):
            i = 0
            while i < len(all_items0):
                # 対応する線の線長の比から、それぞれの線のカット速度を設定する
                # 対応する2本の線の長さを取得
                line0 = dxf_obj0.line_list[i]
                line1 = dxf_obj1.line_list[i]
                line0_length = line0.get_length()
                line1_length = line1.get_length()
                
                # 線の比から、get_cutspeedにより、各断面での速度を取得
                cs_xy_mech, cs_xy_work, cs_mid, cs_uv_work, cs_uv_mech = \
                    get_cutspeed(line0_length, line1_length, z_xy, z_uv, z_mach, \
                                             cut_speed, cut_speed_def_value)
                
                # XY,UV断面の線に、計算したカット速度を設定
                line0.set_cutspeed(cs_xy_work, cs_xy_mech)
                line1.set_cutspeed(cs_uv_work, cs_uv_mech)
                i += 1

        # XY-UV断面で線の本数が不一致の場合
        else:
            # カット速度をそのまま各線に設定
            for line0 in dxf_obj0.line_list:
                line0.set_cutspeed(cut_speed, cut_speed)
                
            for line1 in dxf_obj1.line_list:
                line1.set_cutspeed(cut_speed, cut_speed)
        
        # テーブル・グラフを更新
        dxf_obj0.update()
        dxf_obj1.update()
    
            
    except:
        traceback.print_exc()
        output_log(traceback.format_exc())



def set_offset_dist_from_function(dxf_obj0, dxf_obj1, xy_dist_entry, uv_dist_entry, mach_dist_entry, cut_speed_entry, cut_speed_def_cb, offset_function, is_remove_collision, messeage_window):
    """ワーク端でのカット速度から、溶け量ファイルを用いてオフセット距離を設定する

    Args:
        dxf_obj0 (DxfFile): XY断面のDxfFileクラス
        dxf_obj1 (DxfFile): UV断面のDxfFileクラス
        xy_dist_entry (tkinter.Entry): XY面距離を入力するエントリー
        uv_dist_entry (tkinter.Entry): UV面距離を入力するエントリー
        mach_dist_entry (tkinter.Entry): 駆動面距離を入力するエントリー
        cut_speed_entry (tkinter.Entry): カット速度を入力するエントリー
        cut_speed_def_cb (tkinter.Combobox): カット速度定義面のコンボボックス
        offset_function (scipy.interpolate.interp1d): オフセット距離の算出に使用する関数オブジェクト
        is_remove_collision (bool): True:自己交差を修正する, False:しない
        message_window (MesseageWindow): メッセージウィンドウ

    Note:
        is_remove_collision=Trueの場合、結合後の線に対して、自己交差を除去する。 

        エントリーの値が実数値でない場合は、例外を発生させ、標準出力へ表示した上で、output_logによりエラーファイルにも出力する。 

    """

    # カット速度算出までの処理は、get_cutspeedと同様
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

        # XY-UV断面で線の本数が一致している場合
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

                # 算出したカット速度から、オフセット距離を計算
                offset_XY_Work = offset_function(cs_xy_work)
                offset_UV_Work = offset_function(cs_uv_work)
                # オフセット距離を線ごとに設定
                line0.set_offset_dist(offset_XY_Work)
                line1.set_offset_dist(offset_UV_Work)
                # カット速度も併せて設定
                line0.set_cutspeed(cs_xy_work, cs_xy_mech)
                line1.set_cutspeed(cs_uv_work, cs_uv_mech)
                
                i += 1
            
            # 自己交差を除去が有効の場合 
            if is_remove_collision.get():
                # remove_collisionにより自己交差を除去
                remove_collision(dxf_obj0, "XY面", messeage_window)
                remove_collision(dxf_obj1, "UV面", messeage_window)   
                
            # XY,UV面のグラフ・テーブルを更新
            dxf_obj0.update()
            dxf_obj1.update()
            
            # 結果をメッセージウィンドウに出力
            messeage_window.set_messeage("オフセット値を更新しました。\n")

        # XY-UV断面で線の本数が不一致の場合
        else:
            messeage_window.set_messeage("XY座標とUV座標でライン数が一致しません。XY：%s本，UV：%s本\n"%(len(all_items0),len(all_items1)))

    except:
        # キャストエラーによる例外を捕捉
        traceback.print_exc()
        output_log(traceback.format_exc())
        messeage_window.set_messeage("入力値に誤りがあります。オフセット値更新を中止しました。\n")


def gen_g_code(dxf_obj0, dxf_obj1, entry_ox, entry_oy, entry_ex, entry_ey, xy_dist_entry, uv_dist_entry, mach_dist_entry, cut_speed_entry, \
               cut_speed_def_cb, cb_CncCSDef, entry_dl, messeage_window, config):
    """XY-UVテーブルで指定したカットパスに従い、Gコードを生成する

    Args:
        dxf_obj0 (DxfFile): XY断面のDxfFileクラス
        dxf_obj1 (DxfFile): UV断面のDxfFileクラス
        entry_ox (tkinter.Entry): 切り出し始点(X座標)を入力するエントリー
        entry_oy (tkinter.Entry): 切り出し始点(Y座標)を入力するエントリー
        entry_ex (tkinter.Entry): 切り出し終点(X座標)を入力するエントリー
        entry_ey (tkinter.Entry): 切り出し終点(Y座標)を入力するエントリー
        xy_dist_entry (tkinter.Entry): XY面距離を入力するエントリー
        uv_dist_entry (tkinter.Entry): UV面距離を入力するエントリー
        mach_dist_entry (tkinter.Entry): 駆動面距離を入力するエントリー
        cut_speed_entry (tkinter.Entry): カット速度を入力するエントリー
        cut_speed_def_cb (tkinter.Combobox): カット速度定義面のコンボボックス
        cb_CncCSDef (tkinter.Combobox): CNC速度定義のコンボボックス
        entry_dl (tkinter.Entry): 分割距離を入力するエントリー
        messeage_window (MesseageWindow): メッセージウィンドウ
        config (Config): CAMで使用する設定値を格納するクラス

    """
    
    # Gコード生成前に、すべての線のカット速度を更新
    set_cut_speed(dxf_obj0, dxf_obj1, xy_dist_entry, uv_dist_entry, mach_dist_entry, cut_speed_entry, cut_speed_def_cb)
    
    # エントリー・コンボボックスから値を取得
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
    
    # Gコードの文字列を格納するリストを初期化
    code_line_list = []
    code_line_list.append(config.HEADER)
    
    try:
        # 入力値チェック用フラグ True:異常, False:異常なし
        temp_error_flg = False
        
        # エントリーの入力値を浮動小数点にキャスト->キャストエラーの場合は例外発生
        ox = float(entry_ox_value)
        oy = float(entry_oy_value)
        ex = float(entry_ex_value)
        ey = float(entry_ey_value)
        z_xy = float(xy_dist_value)
        z_uv = float(uv_dist_value)
        z_mach = float(mach_dist_value)
        dl = float(entry_dl_value)
        CS = float(cut_speed_value)

        # 座標面間の位置関係をチェック
        if z_xy > z_mach:
            messeage_window.set_messeage("【警告】\nXY面距離が駆動面距離に対して%s mm 長いです。\n入力値を確認してください。\n\n"%(z_xy - z_mach))
            temp_error_flg = True
        if z_uv > z_mach:
            messeage_window.set_messeage("【警告】\nUV面距離が駆動面距離に対して%s mm 長いです。\n入力値を確認してください。\n\n"%(z_uv - z_mach))
            temp_error_flg = True
       
        # 分割距離に下限リミットを設定
        if dl < 0.1:
            dl = 0.1
            
        # 切り出し始点までは早送り(G00)で移動
        code_line_list.append("G00 X%f Y%f U%f V%f\n"%(ox, oy, ox, oy))
        
        # すべての行のアイテムIDを取得
        all_items0 = dxf_obj0.get_item(all=True)
        all_items1 = dxf_obj1.get_item(all=True)
        
        # 座標点列格納用
        x_array = np.array([ox])
        y_array = np.array([oy])
        u_array = np.array([ox])
        v_array = np.array([oy])
        
        # 前の線の終点座標保持用
        x0 = ox
        y0 = oy
        u0 = ox
        v0 = oy
        
        # フィレット時のオフセット距離参照用
        xy_offset_dist = []
        uv_offset_dist = []
        
        # 入力値が正常な場合
        if temp_error_flg == False:
            # 線の本数がXY-UV断面で一致している場合
            if len(all_items0) == len(all_items1):
                i = 0
                while i < len(all_items1):
                    # 線の長さを取得
                    line0 = dxf_obj0.line_list[i]
                    line1 = dxf_obj1.line_list[i]
                    line0_length = line0.get_length()
                    line1_length = line1.get_length()
                    # 線のオフセット距離を取得
                    xy_offset_dist.append(line0.offset_dist)
                    uv_offset_dist.append(line1.offset_dist)
                    
                    # 線の長さを分割距離で割ることで、作成する座標点列の点数nを計算
                    n = int(max(line0_length, line1_length)/ dl)
                    if n < 2:
                        n = 2
                    
                    # 線長をn等分割する座標点列を計算
                    x, y = generate_arc_length_points(line0, n)
                    u, v = generate_arc_length_points(line1, n)
                    # カット速度を取得
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
                            
                            # フィレットの座標点列を取得
                            x_f, y_f = generate_offset_interporate_point(l0_x, l0_y, l1_x, l1_y, xy_offset_dist[-1], xy_offset_dist[-2])
                            u_f, v_f = generate_offset_interporate_point(l0_u, l0_v, l1_u, l1_v, uv_offset_dist[-1], uv_offset_dist[-2])        
                            
                            # XY平面およびUV平面でフィレットを作成できた場合
                            if (not(len(x_f) == 0)) and (not(len(u_f) == 0)):
                                #オフセット面の作成
                                x_m_f, y_m_f, u_m_f, v_m_f = make_offset_path(x_f, y_f, u_f, v_f, z_xy, z_uv, z_mach)
                                code_line_list.append(gen_g_code_line_str(x_m_f, y_m_f, u_m_f, v_m_f, x0, y0, u0, v0, cs_xy, cs_uv, CncCsdDef))
                                x0 = x_m_f[-1]
                                y0 = y_m_f[-1]
                                u0 = u_m_f[-1]
                                v0 = v_m_f[-1]

                                # フィレットの座標点列を追加
                                x_array = np.concatenate([x_array, x_f], 0)
                                y_array = np.concatenate([y_array, y_f], 0)
                                u_array = np.concatenate([u_array, u_f], 0)
                                v_array = np.concatenate([v_array, v_f], 0)
                            
                            # フィレットを作成できななった場合
                            else:
                                # 隙間があかないように、端点の座標を一致させる
                                x[0] = x_array[-1]
                                y[0] = y_array[-1]
                                u[0] = u_array[-1]
                                v[0] = v_array[-1]                                     
                        
                    # 駆動面での座標点列を計算
                    x_m, y_m, u_m, v_m = make_offset_path(x, y, u, v, z_xy, z_uv, z_mach)

                    # Gコード命令文を作成
                    code_line_list.append(gen_g_code_line_str(x_m, y_m, u_m, v_m, x0, y0, u0, v0, cs_xy, cs_uv, CncCsdDef))

                    # 前の線の終点座標を更新
                    x0 = x_m[-1]
                    y0 = y_m[-1]
                    u0 = u_m[-1]
                    v0 = v_m[-1]                    
                    
                    # 補完後の座標点列を追加
                    x_array = np.concatenate([x_array, x], 0)
                    y_array = np.concatenate([y_array, y], 0)
                    u_array = np.concatenate([u_array, u], 0)
                    v_array = np.concatenate([v_array, v], 0)
                    
                    i += 1
                
                # 切り出し終点への移動命令を追加
                code_line_list.append(gen_g_code_line_str([ex], [ey], [ex], [ey], x0, y0, u0, v0, cs_xy, cs_uv, CncCsdDef))
                
                # Gコード命令の軸名称を置き換え
                replaced_code_line_list = []
                for g_code_str in code_line_list:
                    replaced_code_line_list.append(replace_g_code(g_code_str, config.X_STR, config.Y_STR, config.U_STR, config.V_STR))
                
                # Gコード命令を1つの文字列に結合
                line = ""
                for elem in replaced_code_line_list:
                    line += elem
                # 加工終了命令の追加
                line += "M02"
                
                # ファイル名称の作成
                # 現在時刻を取得
                dt_now = datetime.datetime.now()
                time_str = dt_now.strftime('%Y%m%d_%H%M%S')
                # CAD図面名称の取得
                name0 = os.path.splitext(os.path.basename(dxf_obj0.filename))[0]
                name1 = os.path.splitext(os.path.basename(dxf_obj1.filename))[0]
                # ファイル名称の決定
                Output_FileName = "%s,%s,%s_%s.nc"%(name0, name1, CS, time_str)
                
                # Gコードファイル出力
                f = open(Output_FileName,'w')
                f.write(line)
                f.close()
                
                # メッセージウィンドウに結果を出力
                messeage_window.set_messeage("Gコード生成成功。%sで保存しました。\n"%Output_FileName)
            
            # 線の本数がXY-UV断面で不一致の場合
            else:
                messeage_window.set_messeage("XY座標とUV座標でライン数が一致しません。XY：%s本，UV：%s本\n"%(len(all_items0),len(all_items1)))
        
        # 入力値が異常な場合
        if temp_error_flg == True:
            messeage_window.set_messeage("入力値に誤りがあります。Gコード生成を中止しました。\n\n")
    except:
        # 予期しない例外が発生した場合
        traceback.print_exc()
        output_log(traceback.format_exc())
        messeage_window.set_messeage("Gコード生成途中でエラーが発生しました。\n\n")
        pass


def path_chk(Root, dxf_obj0, dxf_obj1, entry_ox, entry_oy, entry_ex, entry_ey, \
             xy_dist_entry, uv_dist_entry, mach_dist_entry, entry_dl, use3dValue, messeage_window):
    """カットパスを3Dまたは2Dとしてプロットする。

    3Dの場合は、始点から終点までのカットパスをアニメーションでプロットする。

    Args:
        Root (tkinter.Tk): メインウィンドウの枠となるインスタンス
        dxf_obj0 (DxfFile): XY断面のDxfFileクラス
        dxf_obj1 (DxfFile): UV断面のDxfFileクラス
        entry_ox (tkinter.Entry): 切り出し始点(X座標)を入力するエントリー
        entry_oy (tkinter.Entry): 切り出し始点(Y座標)を入力するエントリー
        entry_ex (tkinter.Entry): 切り出し終点(X座標)を入力するエントリー
        entry_ey (tkinter.Entry): 切り出し終点(Y座標)を入力するエントリー
        xy_dist_entry (tkinter.Entry): XY面距離を入力するエントリー
        uv_dist_entry (tkinter.Entry): UV面距離を入力するエントリー
        mach_dist_entry (tkinter.Entry): 駆動面距離を入力するエントリー
        entry_dl (tkinter.Entry): 分割距離を入力するエントリー
        use3dValue (bool): True;3Dでパスチェックする, False:2Dでパスチェックする
        messeage_window (MesseageWindow): メッセージウィンドウ
    """
    # チェックボックスの値を取得
    is_plot_3d = use3dValue.get()
    
    # グラフ描画用の新規ウィンドウを作成
    fig = Figure(figsize=(15, 8), dpi=70)
    plot_window = tk.Toplevel(Root)
    plot_window.wm_title("Cut Path")
    plot_window.geometry("1500x800")
    canvas = FigureCanvasTkAgg(fig, master = plot_window)
    toolbar = NavigationToolbar2Tk(canvas, plot_window)
    toolbar.update()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)    

    # 3Dの場合
    if is_plot_3d == True:
        ax = fig.add_subplot(111, projection="3d", proj_type = 'ortho')
    # 2Dの場合
    else:
        ax = fig.add_subplot(111)
    
    # Gコード生成(gen_g_code)と同様に座標点列を計算する
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
                
                # 切り出し始点からの移動 or 切り出し始点への移動出ない場合
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
                # 切り出し始点からの移動 or 切り出し始点への移動の場合
                else:
                    # 始点からの移動、終点への移動　までは端点しかないので、線の途中に座標点列を追加する
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
            
            # 駆動面での座標点列を計算
            x_m_array, y_m_array, u_m_array, v_m_array = make_offset_path(x_array, y_array, u_array, v_array, z_xy, z_uv, z_mach)
            
            # 3Dで描画する場合
            if is_plot_3d == True:
                # 熱線長を計算
                point_dist_array = calc_point_dist(x_m_array, y_m_array, u_m_array, v_m_array, 0, z_mach)
                
                # 3Dグラフに、ワーク端面、駆動面でのカットパスを黒線で描画
                ax.plot(x_array, y_array, np.ones(len(x_array))*z_xy, 'k')
                ax.plot(u_array, v_array, np.ones(len(x_array))*(z_mach-z_uv), 'k')
                ax.plot(x_m_array, y_m_array, np.ones(len(x_array))*0, 'k')
                ax.plot(u_m_array, v_m_array, np.ones(len(x_array))*z_mach, 'k')
                
                # すべての線を描画すると重いので、間引いて描画
                num_per_plot = int(len(x_array) / length_sum * DIST_CUTPATH_PLOT)
                num_plot = int(len(x_array)/num_per_plot) + 1
                
                if num_per_plot < 1:
                    num_per_plot = 1
                
                # 熱線のアニメーション描画用
                # frameで指定した時刻での熱線を描画する
                def update(frame):
                    plot_3d_cut_path(ax, x_array, y_array, u_array, v_array, x_m_array, y_m_array, u_m_array, v_m_array, z_xy, z_uv, z_mach, num_per_plot, frame)
                
                # 画角調整
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
                
                # アニメーション描画
                anim = FuncAnimation(fig, update, frames=num_plot, interval=100, repeat=False)
                canvas.draw()

                # アニメーション保存　デバッグ用
                #anim.save('anim.gif', writer="imagemagick")

            # 2Dで描画する場合
            else:
                # 熱線長を計算
                point_dist_array = calc_point_dist(x_m_array, y_m_array, u_m_array, v_m_array, 0, z_mach)
                # 3Dグラフに、ワーク端面、駆動面でのカットパスを描画
                ax.plot(x_m_array, y_m_array, "b", label = "XY Mech Path")
                ax.plot(u_m_array, v_m_array, "r", label = "UV Mech Path")
                ax.plot(x_array, y_array, "b--", label = "XY Work Path")
                ax.plot(u_array, v_array, "r--", label = "UV Work Path")
                # 画角調整
                ax.set_aspect('equal')
                # グラフ表示
                ax.legend()
            
            
            # 結果および熱線長をメッセージウィンドウに出力
            messeage_window.set_messeage("パスを描画しました。ワイヤーの最大長は%s mmです。（初期長%s mm）\n"%(int(max(point_dist_array)), int(z_mach)))
            messeage_window.set_messeage("\n【加工範囲】 \nX: %smm～%smm\nY: %smm～%smm\nU: %smm～%smm\nV: %smm～%smm\n\n"
                                         %(int(min(x_array)), int(max(x_array)), int(min(y_array)), int(max(y_array)), int(min(u_array)), int(max(u_array)), int(min(v_array)), int(max(v_array))))

            # 入力値がおかしい場合は警告をメッセージウィンドウに出力
            if z_xy > z_mach:
                messeage_window.set_messeage("【警告】\nXY面距離が駆動面距離に対して%s mm 長いです。\n入力値を確認してください。\n\n"%(z_xy - z_mach))
            if z_uv > z_mach:
                messeage_window.set_messeage("【警告】\nUV面距離が駆動面距離に対して%s mm 長いです。\n入力値を確認してください。\n\n"%(z_uv - z_mach))
        
        # 線の本数がXY-UV断面で不一致の場合
        else:
            messeage_window.set_messeage("XY座標とUV座標でライン数が一致しません。XY：%s本，UV：%s本\n"%(len(all_items0), len(all_items1)))
        
    except:
        # 予期しない例外が発生した場合
        traceback.print_exc()
        output_log(traceback.format_exc())
        messeage_window.set_messeage("パスチェック中にエラーが発生しました。\n")
        pass      


def _destroyWindow():
    """メインウィンドウが閉じられた際にインスタンスを破棄する
    """
    root.quit()
    root.destroy()


def offset_origin(dxf_obj0, dxf_obj1, entry_offset_ox, entry_offset_oy, messeage_window):
    """指定の距離だけ、XYおよびUV断面の原点をオフセットする。

    Args:
        dxf_obj0 (DxfFile): XY断面のDxfFileクラス
        dxf_obj1 (DxfFile): UV断面のDxfFileクラス
        entry_offset_ox (tkinter.Entry): 原点のX方向オフセット量の入力エントリー
        entry_offset_oy (tkinter.Entry): 原点のY方向オフセット量の入力エントリー
        message_window (MesseageWindow): メッセージウィンドウ

    Note:
        XY,UV断面にCADファイルを読み込み後にのみ、オフセット可能。

        エントリーの値が実数値でない場合は、例外を発生させ、標準出力へ表示した上で、output_logによりエラーファイルにも出力する。

    """
    # エントリーの値を取得
    offset_ox = entry_offset_ox.get()
    offset_oy = entry_offset_oy.get()
    
    try :
        # 浮動小数点にキャスト->キャストエラーの場合は例外派生
        offset_ox = float(offset_ox)
        offset_oy = float(offset_oy)
        
        # 線の読み込み前の場合はオフセットしない
        if (len(dxf_obj0.line_list) == 0) or (len(dxf_obj1.line_list) == 0):
            messeage_window.set_messeage("XY, UV面の両方に図形を読み込んでください。\n")  
        else:
            # XY, UV断面でオフセットを実行
            dxf_obj0.offset_origin(offset_ox, offset_oy)
            dxf_obj1.offset_origin(offset_ox, offset_oy)
            # XY, UV断面でグラフ・テーブルを更新
            dxf_obj0.update(keep_view = False)
            dxf_obj1.update(keep_view = False)
            messeage_window.set_messeage("XY,UV座標をX:%s, Y:%sオフセットしました。\n"%(offset_ox, offset_oy))
    except:
        # キャストエラーの例外を捕捉
        traceback.print_exc()
        output_log(traceback.format_exc())
        messeage_window.set_messeage("全体オフセットに数値以外が設定されています。\n")


def rotate_origin(dxf_obj0, dxf_obj1, rotate_entry, messeage_window):
    """指定の角度だけ、XYおよびUV断面を回転する。

    Args:
        dxf_obj0 (DxfFile): XY断面のDxfFileクラス
        dxf_obj1 (DxfFile): UV断面のDxfFileクラス
        rotate_entry (tkinter.Entry): 回転角度を入力するエントリー
        message_window (MesseageWindow): メッセージウィンドウ

    Note:
        XY,UV断面にCADファイルを読み込み後にのみ、回転可能。

        回転中心は、それぞれの断面の重心の平均値の座標とする。

        エントリーの値が実数値でない場合は、例外を発生させ、標準出力へ表示した上で、output_logによりエラーファイルにも出力する。

    """
    # エントリーの値を取得
    sita = rotate_entry.get()
    
    try:
        # 浮動小数点にキャスト->キャストエラーの場合は例外派生
        sita = np.radians(float(sita))
        
        # 線の読み込み前の場合はオフセットしない
        if (len(dxf_obj0.line_list) == 0) or (len(dxf_obj1.line_list) == 0):
            messeage_window.set_messeage("XY, UV面の両方に図形を読み込んでください。\n")  
        else:
            # XY, UV断面の重心座標を計算
            cg_x0, cg_y0 = dxf_obj0.get_cg()
            cg_x1, cg_y1 = dxf_obj1.get_cg()
            # 平均をとることで、回転中心を算出
            rx = (cg_x0 + cg_x1)/2
            ry = (cg_y0 + cg_y1)/2
            # XY,UV断面を回転
            dxf_obj0.rotate(sita, rx, ry)
            dxf_obj1.rotate(sita, rx, ry)
            # XY,UV断面のグラフ・テーブルを更新
            dxf_obj0.update(keep_view = False)
            dxf_obj1.update(keep_view = False)
            messeage_window.set_messeage("重心(%s, %s)を回転中心として、元の図形を%s deg回転しました。\n"\
                                         %(format(rx,'.1f'), format(ry,'.1f'), format(np.degrees(sita),'.1f'))) 
        
    except:
        # キャストエラーの例外を捕捉
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
    message_window = MesseageWindow(root, width=110, height = 9)
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
        lambda e: set_cut_speed(dxf0, dxf1, xy_dist_entry, uv_dist_entry, mach_dist_entry,\
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
    mach_dist_entry = tk.Entry(root, width=8,font=("",12))     
    mach_dist_entry.insert(tk.END, config.MACH_DIST)
    mach_dist_entry.place(x = 1420, y = 740)  


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
                                                                              mach_dist_entry, message_window))
    config_load_btn.place(x=1207, y=570)  

    #【オフセット関数ファイル読込用のエクスプローラーを開くボタン】   
    offset_func_load_btn = tk.Button(root, text="開く", command = lambda: load_offset_func(config, offset_func_entry, message_window))
    offset_func_load_btn.place(x=1207, y=532)    

    #【オフセット値更新ボタン】    
    offset_from_func_btn = tk.Button(root, text = "溶け量ファイルからオフセット量設定", height = 1, width = 34, font=("",10),  bg='#fffacd', \
                          command = lambda: set_offset_dist_from_function(dxf0, dxf1, xy_dist_entry, uv_dist_entry, mach_dist_entry, cut_speed_entry, cut_speed_def_cb,\
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
                                                      xy_dist_entry, uv_dist_entry, mach_dist_entry, dl_entry, is_3d_path_check, message_window))
    path_check_btn.place(x = 1530, y = 660)
    

    #Ver2.0 変更　MechDistEntry, WorkDistWntryを追加
    #【Gコード生成ボタン】        
    generate_g_code_btn = tk.Button(root, text = "Gコード生成", height = 2, width = 12,font=("",12), bg='#ff6347', \
                            command = lambda: gen_g_code(dxf0, dxf1, cut_start_entry_x, cut_start_entry_y, cut_end_entry_x, cut_end_entry_y, \
                                                         xy_dist_entry, uv_dist_entry, mach_dist_entry, cut_speed_entry, cut_speed_def_cb, cnc_speed_def_cb, \
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
