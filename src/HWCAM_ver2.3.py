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

import tkinter as tk
import tkinter.ttk as ttk
import ezdxf as ez
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.mplot3d import Axes3D
from scipy import interpolate as intp
from matplotlib.figure import Figure
from scipy.integrate import quad
import os.path as op
import datetime
import os


#======================================================================================================================================
#            グローバル変数
#======================================================================================================================================
Z_ERROR = 5.0           #2020.10.13　ver2.1 新規追加  単位：mm Z面の許容誤差 
LINE_MARGE_NORM_MN = 1  #単位:mm ラインを結合時にラインを結合してよいかを判断するためのライン端点間距離

   
#======================================================================================================================================
#            クラスの実装
#======================================================================================================================================


#######################################################################################################################################
###############    line_objectクラス   ここから　　　#########################################################################################

#【説明】
#　ライン，スプラインを格納するクラスである．
#
#【親クラス】
#　なし
#
#【メンバ変数】
#   変数名          型              説明
#   x_raw           list            x座標点列の初期値　変更されない
#   y_raw           list            y座標点列の初期値　変更されない
#   st              list            x_raw, y_rawの 始点 
#   ed              list            x_raw, y_rawの 終点 
#   N               int             座標点列の個数
#   num             int             ラインの番号
#   offset_dist     float           オフセット距離
#   offset_dir      char            オフセット方向["O"/ "I"]
#   cut_dir         char            x, y配列の方向["F"/ "R"]（x_raw，y_rawに対して順方向が"F"，逆方向が"R"）
#   x               list            オフセット，配列方向を適用したあとの x座標点列
#   y               list            オフセット，配列方向を適用したあとの y座標点列
#
#【実装メソッド】
#   __init__(list x_points, list y_points, int num)
#   【引数】 x_points, y_points, num
#   【戻り値】　なし
#   【機能】 初期化処理を実行する．x座標点列x_points, y座標点列y_points　を，x_raw，y_rawおよびx, yに代入する．ライン名をnumに設定する．
#
#   update()
#   【引数】　なし
#   【戻り値】　なし
#   【機能】 cut_dir, offset_dir, offset_distの現在値をもとに，x, yの配列を再生成する
#
#   set_offset_dir(char offset_dir)
#   【引数】 offset_dir
#   【戻り値】　なし
#   【機能】　メンバ変数であるoffset_dirを入力値に設定する．offset_dirが"O", "I"以外は処理しない．
#
#   set_offset_dist(float offset_dist)
#   【引数】 offset_dist
#   【戻り値】 なし
#   【機能】 メンバ変数であるoffset_distを入力値に設定する．
#
#   set_cut_dir(char cut_dir)
#   【引数】 cut_dir 
#   【戻り値】 なし
#   【機能】 メンバ変数であるcut_dirtを入力値に設定する．cut_dirが"F", "R"以外は処理しない．
#
#   set_num(int num)
#   【引数】　num 
#   【戻り値】　なし
#   【機能】 メンバ変数であるnumを入力値に設定する．
#
#   toggle_cut_dir()
#   【引数】 なし
#   【戻り値】　なし
#   【機能】　カット方向を逆転させる
#
#   toggle_offset_dir()
#   【引数】　なし
#   【戻り値】　なし
#   【機能】　オフセット方向を逆転させる
#
#   calc_length_array(str mode = "offset")
#   【引数】 mode（オプション）
#   【戻り値】　list length_array
#   【機能】　x, yのスプラインに沿った線長を，配列として返す．mode = "raw"の場合，x_raw，y_rawのスプラインに沿った線長を配列として返す．
#
#   get_length(str mode = "offset")
#   【引数】 mode（オプション）
#   【戻り値】 float length
#   【機能】 x, yのスプラインに沿った線長を返す．mode = "raw"の場合，x_raw，y_rawのスプラインに沿った線長を返す．


class line_object:
    def __init__(self, x_points, y_points, num):
        self.x_raw = np.array(x_points)
        self.y_raw = np.array(y_points)
        self.st = np.array([x_points[0], y_points[0]])
        self.ed = np.array([x_points[-1], y_points[-1]])
        self.N = max(len(x_points), len(y_points))
        self.num = num
        self.offset_dist = 0
        self.offset_dir = "O"
        self.cut_dir = "F"
        self.x = x_points
        self.y = y_points
        self.interp_mode = "cubic" #ver.2.2追加 "cubic":3d-spline, "linear":1d-line, ポリラインの指定用

        if len(x_points)<2:
            self.line_type = "point"
        if len(x_points)==2:
            self.line_type = "line"
        if len(x_points)>2:
            self.line_type = "spline"
       
        
    def reset_point(self, x_points, y_points):
        self.x_raw = np.array(x_points)
        self.y_raw = np.array(y_points)
        self.st = np.array([x_points[0], y_points[0]])
        self.ed = np.array([x_points[-1], y_points[-1]])
        self.N = max(len(x_points), len(y_points))
        self.x = x_points
        self.y = y_points
        self.interp_mode = "cubic" 

        if len(x_points)<2:
            self.line_type = "point"
        if len(x_points)==2:
            self.line_type = "line"
        if len(x_points)>2:
            self.line_type = "spline"        
    
    
    def update(self):
        if self.cut_dir == "R":
            temp_x = self.x_raw[::-1]
            temp_y = self.y_raw[::-1]
        else:
            temp_x = self.x_raw
            temp_y = self.y_raw
        
        if self.offset_dir == "I":
            self.x, self.y = offset_line(temp_x, temp_y, self.offset_dist, self.cut_dir, self.interp_mode) 
            
        else:
            self.x, self.y = offset_line(temp_x, temp_y, -self.offset_dist, self.cut_dir, self.interp_mode)
    
    
    def set_offset_dir(self, offset_dir):
        if offset_dir == 'O' or offset_dir == 'I':
            self.offset_dir = offset_dir
            self.update()
        
        
    def set_offset_dist(self, offset_dist):
        try:             
            self.offset_dist = float(offset_dist)
            self.update()
        except:
            pass
    
    
    def set_cut_dir(self, cut_dir):
        if cut_dir == 'F' or cut_dir == 'R':
            self.cut_dir = cut_dir
            self.update()
        
        
    def set_num(self, num):
        try:
            self.num = int(num)
        except:
            pass
    
    
    def toggle_cut_dir(self):
        if self.cut_dir == "F":
            self.cut_dir = "R"
        else:
            self.cut_dir = "F"
    
    
    def toggle_offset_dir(self):
        if self.offset_dir == "O":
            self.offset_dir = "I"
        else:
            self.offset_dir = "O"

        
    def calc_length_array(self, mode = "offset"):
        
        length_array = [0]
        
        if mode == "raw":
            x = self.x_raw
            y = self.y_raw
        
        else:
            x = self.x
            y = self.y           
            
        if self.line_type == "point":
            length_array = []
        
        if self.line_type == "line":
            dl = np.sqrt((x[0]-x[1])**2 + (y[0]-y[1])**2)
            length_array.append(dl)
        
        if self.line_type == "spline":
            dl = 0
            dt = 1
            s_l = 0
            t_p = np.linspace(0, dt * len(x), len(x))

            fx_t = intp.CubicSpline(t_p, x)
            fy_t = intp.CubicSpline(t_p, y)
            
            dfx_t = fx_t.derivative(1)
            dfy_t = fy_t.derivative(1)
            
            fdl = lambda t: np.sqrt(dfx_t(t)**2 + dfy_t(t)**2)
            
            i = 0
            while i < len(t_p) - 1:
                dl = quad(fdl, t_p[i], t_p[i+1])
                s_l += dl[0]
                length_array.append(s_l)
                i += 1
            
        return np.array(length_array)
    
    
    def get_length(self, mode = "offset"):
        
        length = 0
        
        if mode == "raw":
            x = self.x_raw
            y = self.y_raw
        
        else:
            x = self.x
            y = self.y           
            
        if self.line_type == "point":
            length = 0
        
        if self.line_type == "line":
            length = np.sqrt((x[0]-x[1])**2 + (y[0]-y[1])**2)
        
        if self.line_type == "spline":
            dl = 0
            dt = 1
            s_l = 0
            t_p = np.linspace(0, dt * len(x), len(x))

            fx_t = intp.CubicSpline(t_p, x)
            fy_t = intp.CubicSpline(t_p, y)
            
            dfx_t = fx_t.derivative(1)
            dfy_t = fy_t.derivative(1)
            
            fdl = lambda t: np.sqrt(dfx_t(t)**2 + dfy_t(t)**2)
            
            i = 0
            while i < len(t_p) - 1:
                dl = quad(fdl, t_p[i], t_p[i+1])
                s_l += dl[0]
                i += 1
            length = s_l
        
        return length

###############    line_objectクラス   ここまで　　　#########################################################################################
#######################################################################################################################################



#######################################################################################################################################
###############    super_tableクラス   ここから　　　#########################################################################################
        
#【説明】
#　ラインのテーブルを作成するクラスである．tk.treeのインスタンスを格納する．tk.treeを初期化する方法がtreeの再生成しかないため，生成に必要な情報をメンバ変数として保存し，
#　reset()関数がコールされた際にtableを削除，再生成する．注意：tk.treeは親クラスではない．
#
#【親クラス】
#　なし
#
#【メンバ変数】
#   変数名          型              説明
#   x_pos           int            テーブルの配置位置 X座標
#   y_pos           int            テーブルの配置位置 Y座標
#   root            tk.Frame       テーブル先のフレーム
#   y_height        int            テーブル先の高さ（行）
#   parent          int            テーブルの親子設定[0 / 1]（1：親，0：子）
#   table           tk.tree        テーブルのインスタンス
#
#【実装メソッド】
#   __init__(tk.Frame root, int y_height, int x, int y)
#   【引数】 root, y_height, x, y
#   【戻り値】　なし
#   【機能】 クラスを初期化する．
#
#   set_parent(int parent):
#   【引数】　parent
#   【戻り値】　なし
#   【機能】 parentを入力値に変更する
#
#   reset()
#   【引数】 なし
#   【戻り値】　なし
#   【機能】　既存のtableインスタンスを破棄する．その後再生成する．テーブルのヘッダなどを設定する．

    
class super_table:
    def __init__(self, root, y_height, x, y):
        self.x_pos = x
        self.y_pos = y
        self.root = root
        self.y_height = y_height
        self.parent = 0
        self.reset()
    
    
    def set_parent(self, parent):
        if parent == 1 or parent == 0:
            self.parent = parent
    
    
    def reset(self):
        try:
            self.table.destroy()
        except:
            pass
        self.table = ttk.Treeview(self.root, height = self.y_height)
        self.table.place(x = self.x_pos, y = self.y_pos)
        self.table["column"] = (1,2,3,4)
        self.table["show"] = "headings"
        self.table.heading(1,text="ライン番号")
        self.table.heading(2,text="カット方向")
        self.table.heading(3,text="オフセット方向")
        self.table.heading(4,text="ラインタイプ")
        self.table.column(1, width=100)
        self.table.column(2, width=100)
        self.table.column(3, width=100)
        self.table.column(4, width=100)
    
    
###############    super_tableクラス   ここまで　　　#########################################################################################
#######################################################################################################################################



#######################################################################################################################################
###############   dxf_fileクラス   ここから　　    　#########################################################################################

#【説明】
#　dxfファイルに関連する，line_object，super_tableなどを格納する．main関数以外ではトップレベルモジュールである．
#
#【親クラス】
#　なし
#
#【メンバ変数】
#   変数名          型                   説明
#   ax              Axes                グラフのプロットエリアのインスタンス
#   canvas          FigureCanvasTkAgg   グラフを配置しているフレームのインスタンス
#   table           super_table         x_raw, y_rawの 始点 
#   x_table         super_table         x_raw, y_rawの 終点 
#   name            str                 グラフに表示する名前"X-Y", "U-V"など
#   line_list       list                line_objectをすべて格納するリスト
#   line_num_list   list                テーブル番号とline_objectを対応付けるリスト
#   selected_line   int                 テーブルにて選択されたラインの番号
#   filename        str                 dxfファイルの名称
#
#【実装メソッド】
#   __init__(Axes ax, FigureCanvasTkAgg canvas, super_table table, super_table x_table, str name)
#   【引数】 x_points, y_points, num
#   【戻り値】　なし
#   【機能】 初期化処理を実行する．ax，canvas，table，x_table，nameを自身のメンバ変数に格納する，またline_list，line_num_listを空のリストとして作成する．
#　　　　　　　　またselected_numを0として作成する．
#
#   load_file(str filename)
#   【引数】　なし
#   【戻り値】　なし
#   【機能】 filenameをメンバ変数にかくのうし，他のメンバ変数を初期化する，新しいdxfファイルを読み込む．reload()，plot()をコールする，
#　　　　　　　　テーブルの選択イベントと，selectedをバインドする．
#
#   reload()
#   【引数】 なし
#   【戻り値】　なし
#   【機能】　filemameのdxfファイルを読み込み，lineとsplineの座標点列を取得する．座標点列からline_objectを生成し，line_listに追加する．
#　　　　　　　　line_num_listに自身の番号を追加する．（初期値はline_object.numと同じ）　tabelにline_objectの情報を追加する．
#
#   table_reload()
#   【引数】 なし
#   【戻り値】 なし
#   【機能】 tableに表示する情報を，line_objectのメンバ変数が持つ情報に更新する，
#
#   plot()
#   【引数】 なし 
#   【戻り値】 なし
#   【機能】 グラフを更新する．グラフは，selected_line以外を透明度を低下させて描画する．グラフは，selected_lineの始点からカット方向ベクトルを描画する．
#　　　　　　　　グラフは，offset_distが 0以外である場合，オフセット方向ベクトルを描画する．グラフは，item_num_listの値が0以上の場合にのみプロットする．
#
#   set_selected_line(int selected_line)
#   【引数】 selected_line
#   【戻り値】　なし
#   【機能】 メンバ変数であるselected_lineを入力値に設定する．plot()をコールする．
#
#   selected(event)
#   【引数】 event
#   【戻り値】　なし
#   【機能】　テーブルの選択イベントが発生した場合，本関数がコールされる．バインドはload_dile()で設定される．本関数ではset_selected_lineをコールする．
#　　　　　　　　table.parent=1かつ x_table.parent=0の場合，tableで選択された行と同じ行を，x_tableに選択させる．(X-YテーブルとU-Vテーブルの連動選択時の処理である．）
#
#   set_offset_dist(float offset_dist)
#   【引数】　offset_dist
#   【戻り値】　なし
#   【機能】　tableに表示されているライン全てのoffset_distを入力値に更新する．plot()，table_reload()をコールし，グラフ，表を更新する．
#
#   Change_CutDir()
#   【引数】 なし
#   【戻り値】　なし
#   【機能】　tableで選択されているラインの向きをすべて逆転させる．plot()，table_reload()をコールし，グラフ，表を更新する．
#
#   Change_OffsetDir()
#   【引数】 なし
#   【戻り値】 なし
#   【機能】 tableで選択されているラインのオフセット方向をすべて逆転させる．plot()，table_reload()をコールし，グラフ，表を更新する．
#
#   Swap_Selected_line()
#   【引数】 なし 
#   【戻り値】 list selected_items
#   【機能】 tableで選択されている２本のラインのカット順を入れ替える．選択が2本である場合，Swap_lineをコールする．plot()，table_reload()をコールし，グラフ，表を更新する．
#　　　　　　　　戻り値として，選択されたラインの番号をリストとして返す．（上位関数で入れ替えが成功したかを通知するために使用する．）
#
#   Swap_line(int item_num0, int item_num1):
#   【引数】　int item_num0, item_num1
#   【戻り値】　なし
#   【機能】 入力された2本のラインについて，line_num_listの値を入れ替える．set_selected_lineをコールし，line_num1をselected_lineに設定する．
#
#   delete_Selected_line()
#   【引数】 なし
#   【戻り値】　なし
#   【機能】　tableで選択されているラインをすべて非表示とする．delete_lineをコールする．plot()，table_reload()をコールし，グラフ，表を更新する．
#
#   delete_line(int item_num)
#   【引数】　int item_num
#   【戻り値】　なし
#   【機能】　item_numに対応するラインのlin_num_listの値を-1に上書きする．tableからitem_numを削除する．
#
#   reverse_all()
#   【引数】 なし
#   【戻り値】　なし
#   【機能】　テーブルで表示しているラインの順番を逆転させ，カット方向を逆転させる．
#
#   SortLine(float ox0, float oy0)
#   【引数】 
#   【戻り値】 なし
#   【機能】 テーブルで表示しているラインを下記のルールに基づき並び替え，要すればカット方向，オフセット方向を変更する．
#　　　　　　　　1. ox, oyから最も近い位置にあるライン端を検索する
#　　　　　　　　2. 1.のライン端を有するラインを，カット番号0に設定する.1.のライン端がラインの終端である場合，カット方向，オフセット方向を逆転させる．
#　　　　　　　　3. 1.のライン端の逆端から最も近い位置にあるライン端を検索する．        
#　　　　　　　　4.　3.のライン端を有するラインを，カット番号1に設定する．3.のライン端がラインの終端である場合，カット方向，オフセット方向を逆転させる.
#　　　　　　　　5. 3.のライン端から最も近い位置にあるライン端を検索する．
#　　　　　　　　6. 3～5を，テーブルに表示されている全てのラインに対して実施する．
#　　　　　　　　

class dxf_file:
    def __init__(self, ax, canvas, table, x_table, name):
        self.ax = ax
        self.canvas = canvas
        self.table = table
        self.x_table = x_table
        self.name = name
        self.line_list = []
        self.line_num_list = []
        self.selected_line = 0
    
    
    def load_file(self, filename):
        self.table.reset()
        self.filename = filename
        self.line_list = []
        self.line_num_list = []
        self.selected_line = 0
        self.reload()
        self.plot()
        self.table.table.bind("<<TreeviewSelect>>", self.selected)
        self.table.table.loaded_item_num = len(self.table.table.get_children())


    def reload(self):
        dwg = ez.readfile(self.filename)
        modelspace = dwg.modelspace()
        line_obj = modelspace.query('LINE')
        spline_obj = modelspace.query('SPLINE')
        arc_obj = modelspace.query('ARC') #ver2.2追加
        poly_obj = modelspace.query('LWPOLYLINE') #ver2.2追加
        
        i = 0
        while i < len(spline_obj):
            temp_spline = spline_obj[i]
            temp_spline_data = np.array(temp_spline.control_points)[:]
            temp_line_object = line_object(temp_spline_data[:,0], temp_spline_data[:,1], i) 
            self.line_list.append(temp_line_object)
            self.line_num_list.append(i)
            self.table.table.insert("", "end", values=(temp_line_object.num, temp_line_object.cut_dir, temp_line_object.offset_dir, temp_line_object.line_type))
            i += 1
 
        #ver2.2追加　円弧，ポリラインの読み込み　ここから
        i_arc = 0        
        while i_arc < len(arc_obj):
            temp_arc = arc_obj[i_arc]
            temp_arc_data = arc_to_spline(temp_arc)
            temp_line_object = line_object(temp_arc_data[:,0], temp_arc_data[:,1], i + i_arc) 
            self.line_list.append(temp_line_object)
            self.line_num_list.append(i + i_arc)
            self.table.table.insert("", "end", values=(temp_line_object.num, temp_line_object.cut_dir, temp_line_object.offset_dir, temp_line_object.line_type))
            i_arc += 1        
        i = i + i_arc

        i_poly = 0
        while i_poly < len(poly_obj):
            temp_poly = poly_obj[i_poly]
            temp_poly_data = poly_to_spline(temp_poly)
            temp_line_object = line_object(temp_poly_data[:,0], temp_poly_data[:,1], i + i_poly) 
            temp_line_object.interp_mode = "linear" #poly_lineであることを設定する
            self.line_list.append(temp_line_object)
            self.line_num_list.append(i + i_poly)
            self.table.table.insert("", "end", values=(temp_line_object.num, temp_line_object.cut_dir, temp_line_object.offset_dir, temp_line_object.line_type))
            i_poly += 1    
        i = i + i_poly
        #ver2.2追加　ここまで

        j = 0
        k = 0
        while j < len(line_obj):
            temp_line = line_obj[j]
            temp_line_data = []
            temp_line_data.append(temp_line.dxf.start)
            temp_line_data.append(temp_line.dxf.end)
            temp_line_data = np.array(temp_line_data)[:,0:2]
            if norm(temp_line_data[0,0],temp_line_data[0,1],temp_line_data[1,0],temp_line_data[1,1]) != 0:
                temp_line_object = line_object(temp_line_data[:,0], temp_line_data[:,1], i+k) 
                self.line_list.append(temp_line_object)
                self.line_num_list.append(i+k)
                self.table.table.insert("", "end", values=(temp_line_object.num, temp_line_object.cut_dir, temp_line_object.offset_dir, temp_line_object.line_type))
                k += 1
            j += 1
            

    def table_reload(self):
        table_item_list = self.table.table.get_children()
        i = 0
        while i < len(table_item_list):
            temp_item_num = table_item_list[i]
            line_num = self.line_num_list[item2num(temp_item_num)]
            temp_line_object = self.line_list[line_num]
            self.table.table.item(temp_item_num, values=(temp_line_object.num, temp_line_object.cut_dir, temp_line_object.offset_dir, temp_line_object.line_type))
            i += 1

    
    def plot(self):
        self.ax.clear()
        self.ax.set_title(self.name)
        self.ax.set_aspect('equal')
        i = 0
        while i < len(self.line_num_list):
            line_num = self.line_num_list[i]
            if line_num >= 0:
                temp_line_object = self.line_list[line_num]
                temp_line_object.update()
                if temp_line_object.line_type == "line":
                    col = "b"
                else:
                    col = "b"
                    
                if line_num == self.selected_line:
                    self.ax.plot(temp_line_object.x, temp_line_object.y, color = col)
                    X,Y = temp_line_object.x[0], temp_line_object.y[0]
                    U,V = temp_line_object.x[1], temp_line_object.y[1]
                    self.ax.quiver(X,Y,U-X,V-Y,color = col)
                    if temp_line_object.cut_dir == "F":
                        X,Y = temp_line_object.x_raw[0], temp_line_object.y_raw[0]
                        U,V = temp_line_object.x[0], temp_line_object.y[0]
                    else:
                        X,Y = temp_line_object.x_raw[-1], temp_line_object.y_raw[-1]
                        U,V = temp_line_object.x[0], temp_line_object.y[0]            
                    if norm(X,Y,U,V) != 0:
                        self.ax.quiver(X,Y,U-X,V-Y,color = "y") #ver2.2 バグ修正 Y を y に変更
                else :
                    self.ax.plot(temp_line_object.x, temp_line_object.y ,color = col, alpha = 0.2)    
            i += 1
        self.canvas.draw()
        
        
    def set_selected_line(self, selected_line):
        self.selected_line = selected_line
        self.plot()
    
    
    def selected(self, event):
        selected_items = self.table.table.selection()
        if not selected_items:
            return None
        item_num = item2num(selected_items[0])
        item_index = self.table.table.get_children().index(selected_items[0])
        line_num = self.line_num_list[item_num]
        if self.table.parent == 1:
            if self.x_table.parent == 0:            
                try:
                    x_item = self.x_table.table.get_children()[item_index]
                    self.x_table.table.selection_set(x_item)
                    self.x_table.table.see(x_item)
                except:
                    pass
        self.set_selected_line(line_num)
        
        
    def set_offset_dist(self, offset_dist):
        table_item_list = self.table.table.get_children()
        i = 0
        while i < len(table_item_list):
            temp_item_num = table_item_list[i]
            line_num = self.line_num_list[item2num(temp_item_num)]
            temp_line_object = self.line_list[line_num]
            temp_line_object.offset_dist = offset_dist
            temp_line_object.update()
            i += 1   
        self.table_reload()
        self.plot()
    
    def Change_CutDir(self):
        selected_items = self.table.table.selection()
        i = 0
        while i < len(selected_items):
            temp_item_num = selected_items[i]
            line_num = self.line_num_list[item2num(temp_item_num)]
            temp_line_object = self.line_list[line_num]
            temp_line_object.toggle_cut_dir()
            temp_line_object.update()
            self.table.table.item(temp_item_num, values=(temp_line_object.num, temp_line_object.cut_dir, temp_line_object.offset_dir, temp_line_object.line_type))
            i += 1   
        self.table_reload()
        self.plot()
    
    
    def Change_OffsetDir(self):
        selected_items = self.table.table.selection()
        i = 0
        while i < len(selected_items):
            temp_item_num = selected_items[i]
            line_num = self.line_num_list[item2num(temp_item_num)]
            temp_line_object = self.line_list[line_num]
            temp_line_object.toggle_offset_dir()
            temp_line_object.update()
            self.table.table.item(temp_item_num, values=(temp_line_object.num, temp_line_object.cut_dir, temp_line_object.offset_dir, temp_line_object.line_type))
            i += 1      
        self.table_reload()
        self.plot()


    def Swap_Selected_line(self):
        selected_items = self.table.table.selection()
        if len(selected_items) == 2:
            swap_line_num0 = item2num(selected_items[0])
            swap_line_num1 = item2num(selected_items[1])
            self.Swap_line(swap_line_num0, swap_line_num1)
            self.table_reload()
            self.plot()
        return selected_items
    

    def Swap_line(self, item_num0, item_num1):
        self.line_num_list[item_num0], self.line_num_list[item_num1] = self.line_num_list[item_num1], self.line_num_list[item_num0] 
        self.set_selected_line(item_num1)    


    def Merge_Selected_line(self):
        selected_items = self.table.table.selection()
        if len(selected_items) == 2:
            parent_line_num = item2num(selected_items[0])
            child_line_num = item2num(selected_items[1])
            if self.Merge_line(parent_line_num, child_line_num) == True:
                self.delete_line(selected_items[1])
                self.table_reload()
                self.plot()
                return [selected_items[0]]
            
        elif len(selected_items) == 1:
            return []
        
        else:
            return selected_items


    def Merge_line(self, parent_item_num, child_item_num):
        parent_line = self.line_list[parent_item_num]
        child_line = self.line_list[child_item_num]
        
        x_p_st = parent_line.st[0]
        y_p_st = parent_line.st[1]
        x_c_st = child_line.st[0]
        y_c_st = child_line.st[1]

        x_p_ed = parent_line.ed[0]
        y_p_ed = parent_line.ed[1]
        x_c_ed = child_line.ed[0]
        y_c_ed = child_line.ed[1]
        
        x_p = parent_line.x_raw.tolist()
        y_p = parent_line.y_raw.tolist()
        x_c = child_line.x_raw.tolist()
        y_c = child_line.y_raw.tolist()     
        
        new_x = []
        new_y = []

        if norm(x_p_ed, y_p_ed, x_c_st, y_c_st) < LINE_MARGE_NORM_MN:
            # 親ラインに子ラインを接続
            new_x.extend(x_p)
            new_y.extend(y_p)
            new_x.extend(x_c)
            new_y.extend(y_c)
        elif norm(x_p_ed, y_p_ed, x_c_ed, y_c_ed) < LINE_MARGE_NORM_MN:
            # 子ラインを反転させたのち、親ラインに子ラインを接続
            x_c.reverse()
            y_c.reverse()
            new_x.extend(x_p)
            new_y.extend(y_p)
            new_x.extend(x_c)
            new_y.extend(y_c)
        elif norm(x_p_st, y_p_st, x_c_ed, y_c_ed) < LINE_MARGE_NORM_MN:
            # 子ラインに親ラインを接続
            new_x.extend(x_c)
            new_y.extend(y_c)
            new_x.extend(x_p)
            new_y.extend(y_p)
        elif norm(x_p_st, y_p_st, x_c_st, y_c_st) < LINE_MARGE_NORM_MN:
            # 子ラインを反転させたのち、子ラインに親ラインに接続
            x_c.reverse()
            y_c.reverse()
            new_x.extend(x_c)
            new_y.extend(y_c)
            new_x.extend(x_p)
            new_y.extend(y_p)
            
        else:
            # 端点が隣接していない線同士であるので、結合すべきではない。
            return False
        
        parent_line.reset_point(new_x, new_y)
        return True
                
        
    def delete_Selected_line(self):
        selected_items = self.table.table.selection()
        i = 0
        while i < len(selected_items):
            self.delete_line(selected_items[i])
            i += 1             
        self.table_reload()
        self.plot()
        
        
    def delete_line(self, item_num):
        line_num = self.line_num_list[item2num(item_num)]
        index = self.line_num_list.index(line_num)
        if self.line_num_list[index] >= 0:            
            self.line_num_list[index] = -1
        self.table.table.delete(item_num)
    
    
    def reverse_all(self):
        alaivable_line_num_list = np.array(np.array(self.line_num_list.copy())[np.where(np.array(self.line_num_list.copy()) >= 0)])
        new_line_num_list = alaivable_line_num_list[-1::-1]
        
        i = 0
        j = 0
        while i < len(self.line_num_list):
            if self.line_num_list[i] >= 0:
                temp_num = new_line_num_list[j]
                temp_line = self.line_list[temp_num]
                temp_line.toggle_cut_dir()
                self.line_num_list[i] = temp_num                
                j += 1
                i += 1
            else:
                i += 1
        
        self.table_reload()
        self.plot()        
        
    
    def SortLine(self, ox0, oy0):
        i = 0
        norm_mn = np.inf
        temp_cut_dir = 'F'
        x0 = ox0
        y0 = oy0
        alaivable_line_num_list = sorted(np.array(self.line_num_list.copy())[np.where(np.array(self.line_num_list.copy()) >= 0)])
        new_line_num_list = []

        while i < len(alaivable_line_num_list) :
            norm_mn = np.inf
            j = 0
            while j < len(alaivable_line_num_list):
                num1 = alaivable_line_num_list[j]
                if num1 in new_line_num_list:
                    pass
                
                else:
                    temp_line1 = self.line_list[num1]
                    temp_norm_st = norm(x0, y0, temp_line1.st[0], temp_line1.st[1])
                    temp_norm_ed = norm(x0, y0, temp_line1.ed[0], temp_line1.ed[1])
                    if min(temp_norm_st, temp_norm_ed) < norm_mn:
                        temp_line_num1 = num1
                        norm_mn = min(temp_norm_st, temp_norm_ed)                      
                        if temp_norm_st < temp_norm_ed:
                            temp_cut_dir = 'F'
                        else:
                            temp_cut_dir = 'R'
                j += 1
                
            temp_line1 = self.line_list[temp_line_num1]
            if temp_cut_dir == 'F':
                x0 = temp_line1.ed[0]
                y0 = temp_line1.ed[1]
                if temp_line1.cut_dir != temp_cut_dir:
                    temp_line1.toggle_offset_dir()
                    
            if temp_cut_dir == 'R':
                x0 = temp_line1.st[0]
                y0 = temp_line1.st[1]
                if temp_line1.cut_dir != temp_cut_dir:
                    temp_line1.toggle_offset_dir()
                        
            temp_line1.set_cut_dir(temp_cut_dir)
            new_line_num_list.append(temp_line_num1)
            i += 1
        
        i = 0
        j = 0
        while i < len(self.line_num_list):
            if self.line_num_list[i] >= 0:
                self.line_num_list[i] = new_line_num_list[j]
                j += 1
                i += 1
            else:
                i += 1
        
        self.table_reload()
        self.plot()        


###############   dxf_fileクラス   ここまで　　    　#########################################################################################
#######################################################################################################################################     



#######################################################################################################################################
###############   messeage_windowクラス   ここから　　    　##################################################################################

#【説明】
#　tk.Textクラスに，set_messeageメソッドを追加したクラスである．
#
#【親クラス】
#　tk.Text
#
#【メンバ変数】
#   変数名          型                   説明
#   root            tk.Frame            textウィンドウを配置するフレームのインスタンス
#   width           int                 textウィンドウの幅（文字数で指定）
#   height          int                 textウィンドウの高さ（文字列数で指定）
#
#【実装メソッド】
#   __init__(tk.Frame root, int width, int height)
#   【引数】 root, width, height
#   【戻り値】　なし
#   【機能】 初期化処理を実行する．メンバ変数width，heightを入力値に設定する．
#
#   set_messeage(str messeage):
#   【引数】　str messeage
#   【戻り値】　なし
#   【機能】 textウインドウの最下列にmesseageを挿入する．最下列を表示する．
#　　　　　　　　
#

class messeage_window(tk.Text):
    def __init__(self, root, width, height):
        self.width = width
        self.height = height
        super().__init__(root, width = self.width, height = self.height)
    
    def set_messeage(self, messeage):
        self.insert("end", messeage)
        self.see(self.index('end'))


###############   messeage_windowクラス   ここまで　　    　##################################################################################
#######################################################################################################################################  



#======================================================================================================================================
#            関数の実装
#======================================================================================================================================



#======================================================================================================================================
#            汎用関数
#======================================================================================================================================
#
#   offset_line(list x, list y, float d, str cut_dir, str interp_mode)
#   【引数】　x, y, d, cut_dir
#   【戻り値】　new_x, new_y
#   【機能】 x,y の座標点列をdだけオフセットした点列を作成する．カット方向により，オフセット方向が変わらないように，cut_dirによってオフセット方向を変更する．
#　　　　　　　　アルゴリズムは下記を実装する．(円弧補間は不要なので省略している)
#          https://stackoverflow.com/questions/32772638/python-how-to-get-the-x-y-coordinates-of-a-offset-spline-from-a-x-y-list-of-poi
#　　　　　　　　
#   norm(float x0, float y0, float x, float y)
#   【引数】 x0, y0, x, y
#   【戻り値】　float 距離
#   【機能】　(x0,y0) と(x,y)の距離を計算する．
#
#   norm_3d(float x0, float y0, float z0, float x, float y, float z)
#   【引数】 x0, y0, z0, x, y, z
#   【戻り値】 float 距離
#   【機能】 (x0,y0,z0) と(x,y,z)の距離を計算する
#
#   item2num(str item_num)
#   【引数】 item_num
#   【戻り値】 int num
#   【機能】 tk.treeのItem番号（I***，***がアイテム番号）から***を抽出し，int型に変換して出力する．***は16進法である．
#
#   generate_arc_length_points(line_object line_object, int N)
#   【引数】 line_object, N
#   【戻り値】　list x_p, y_p
#   【機能】 line_objectのx, y点列をスプライン補完し，これをN等分した点列を作成する．
#        
#   generate_arc_length_points4line(float x_st, float  y_st, float x_ed, float y_ed, int N)
#   【引数】　x_st, y_st, x_ed, y_ed, N
#   【戻り値】　list x_p, y_p
#   【機能】 (x_st, y_st), (x_ed, y_ed)を両端に持つ直線を，N等分した点列を作成する．
#
#   plot_3d_cut_path(Axes ax, list x, list y, list u, list v, float Z, int n_plot)
#   【引数】 ax, x, y, u, v, Z, n_plot
#   【戻り値】　list point_dist_list
#   【機能】　axにx,y,u,vをプロットする．x,y平面とu,v平面の距離はZとする．各(x,y),(u,v)の点の距離を計算し，point_dist_list配列として出力する．
#
#   file_chk(str filename)
#   【引数】 file_name
#   【戻り値】 int 成功可否(1：読み取り成功, 0:拡張子が.dxfでない, -1:ファイル存在せず)
#   【機能】 指定されたfilenameのファイルが存在するか，拡張子が.dxfかをチェックする．
#
#   gen_g_code_line_str(list x, list y, list u, list v)
#   【引数】 x, y, u, v
#   【戻り値】 list code_str
#   【機能】 x, y, u, vの各座標からgコードを生成する．gコードはX,Y,Z,A軸を使用するとする，gコードは「G01 X** Y** U** V**」のフォーマットとする．（G01は移動指令）
#
#   arc_to_spline(ezdxf.entities.Arc arc_obj)
#   【引数】 arc_obj
#   【戻り値】 np.array [xp, yp]
#   【機能】 円弧からスプラインの点列を作成する．点数は10degにつき1点とする．点数は最少で3点以上となる．
#
#   poly_to_spline(ezdxf.entities.LWPolyline poly_obj)
#   【引数】 poly_obj
#   【戻り値】 np.array [xp, yp]
#   【機能】 ポリラインから点列を作成する．
#

def offset_line(x, y, d, cut_dir, interp_mode): #ver2.2 interp_mode 追加　ポリラインの場合，オフセット点を中点ではなく，点列を使用するため
    new_x = []
    new_y = []
    k = 0
    sign = 1
    sign_cut_dir = 1
    
    if cut_dir == "R":
        sign_cut_dir = -1
    
    if len(x) < 2: 
        return x, y

    if len(x) == 2:
        if x[0] == x[1]:
            k = np.pi/2.0
        else:
            k = np.arctan((y[1]-y[0])/(x[1]-x[0]))
        
        new_x.append(x[0] - d*np.sin(k))
        new_x.append(x[1] - d*np.sin(k))
        new_y.append(y[0] + d*np.cos(k))
        new_y.append(y[1] + d*np.cos(k))

    if len(x) > 2:
        if interp_mode == "linear" and len(x)%2 == 0:
            num = 0
            while num < len(x)/2:
                i = num * 2
                if x[i] == x[i+1]:
                    k = np.pi/2.0
                else:
                    k = np.arctan((y[i+1]-y[i])/(x[i+1]-x[i]))

                new_x.append(x[i]   - d*np.sin(k))
                new_x.append(x[i+1] - d*np.sin(k))
                new_y.append(y[i]   + d*np.cos(k))
                new_y.append(y[i+1] + d*np.cos(k))

                num += 1
            
        else:
            i = 0
            while i < len(x):
                if i < len(x) - 1: 
                    if x[i] == x[i+1]:
                        k = np.pi/2.0
                    else:
                        k = np.arctan((y[i+1]-y[i])/(x[i+1]-x[i]))
                    if (x[i] < x[i+1]):
                        sign = 1
                    else:
                        sign = -1
                    
                    if i == 0:
                        new_x.append(x[0] - d*np.sin(k) * sign * sign_cut_dir)
                        new_y.append(y[0] + d*np.cos(k) * sign * sign_cut_dir)
                    else:
                        new_x.append((x[i]+x[i+1])/2.0 - d*np.sin(k) * sign * sign_cut_dir)
                        new_y.append((y[i]+y[i+1])/2.0 + d*np.cos(k) * sign * sign_cut_dir)                        
                else:
                    if x[i-1] == x[i]:
                        k = np.pi/2.0
                    else:
                        k = np.arctan((y[i]-y[i-1])/(x[i]-x[i-1]))
                    if (x[i-1] < x[i]):
                        sign = 1
                    else:
                        sign = -1
                    new_x.append(x[i] - d*np.sin(k) * sign * sign_cut_dir)      
                    new_y.append(y[i] + d*np.cos(k) * sign * sign_cut_dir)
                i += 1
    
    new_x = np.array(new_x)
    new_y = np.array(new_y)
    
    return new_x, new_y


def norm(x0, y0, x, y):
    return np.sqrt((x-x0)**2 + (y-y0)**2)


def norm_3d(x0, y0, z0, x, y, z):
    return np.sqrt((x-x0)**2 + (y-y0)**2 + (z-z0)**2)


def item2num(item_num):
    temp = item_num.replace("I","")
    temp = '0x0%s'%temp
    num = int(temp,0) - 1    
    return num


def generate_arc_length_points(line_object, N):
    
    N = int(N)
    if N < 2:
        N = 2

    length_array = line_object.calc_length_array()
    sum_length = length_array[-1]
    
    t_p = length_array/sum_length
    
    x = line_object.x
    y = line_object.y
    
    if line_object.line_type == "point":  
        x_p = x
        y_p = y
        
    if line_object.line_type == "line":  
        fx_t = intp.interp1d(t_p, x, kind = "linear")
        fy_t = intp.interp1d(t_p, y, kind = "linear")
            
        t_p_arc = np.linspace(t_p[0], t_p[-1], N)
        
        x_p = fx_t(t_p_arc)
        y_p = fy_t(t_p_arc)

    if line_object.line_type == "spline":
        if line_object.interp_mode == "linear":
            fx_t = intp.interp1d(t_p, x, kind = "linear")
            fy_t = intp.interp1d(t_p, y, kind = "linear")
                
            t_p_arc = np.linspace(t_p[0], t_p[-1], N)
            
            t_p_arc_add_orgine_point = np.append(t_p, t_p_arc)
            t_p_arc_add_orgine_point = np.sort(t_p_arc_add_orgine_point)              
                    
            x_p = fx_t(t_p_arc_add_orgine_point)
            y_p = fy_t(t_p_arc_add_orgine_point)
            

        else:
            fx_t = intp.CubicSpline(t_p, x)
            fy_t = intp.CubicSpline(t_p, y)
            
            t_p_arc = np.linspace(t_p[0], t_p[-1], N)
            
            x_p = fx_t(t_p_arc)
            y_p = fy_t(t_p_arc)
    
    return x_p, y_p
    

def generate_arc_length_points4line(x_st, y_st, x_ed, y_ed, N):
    
    t_p = np.array([0,1])
    fx_t = intp.interp1d(t_p, [x_st, x_ed], kind = "linear")
    fy_t = intp.interp1d(t_p, [y_st, y_ed], kind = "linear")
        
    t_p_arc = np.linspace(t_p[0], t_p[-1], N)
    
    x_p = fx_t(t_p_arc)
    y_p = fy_t(t_p_arc)
    
    return x_p, y_p


# Ver2.1変更 　引数追加
def plot_3d_cut_path(ax, x, y, u, v, xm, ym, um, vm, z_xy, z_uv, z_m, n_plot):
    
    point_dist_list = []
    
    try:
        if len(x) == len(y) == len(u) == len(v) == len(xm) == len(ym) == len(um) == len(vm):
            zm = np.ones(len(x)) * 0.0
            z = np.ones(len(x)) * z_xy
            w = np.ones(len(x)) * z_m - z_uv
            wm = np.ones(len(x)) * z_m
            
            ax.plot(x, y, z, 'k')
            ax.plot(u, v, w, 'k')
            
            ax.plot(xm, ym, zm, 'k')
            ax.plot(um, vm, wm, 'k')
            
            
            if n_plot < 1:
                n_plot = 1
            
            num_per_plot = int(len(x)/n_plot)
            if num_per_plot < 1:
                num_per_plot = 1
                
            i = 0
            j = 0
            while i < len(x):
                if j > num_per_plot:
                    ax.plot([x[i],u[i]], [y[i],v[i]],  [z_xy, z_m - z_uv], color = 'r', alpha = 0.5)
                    ax.plot([x[i],xm[i]],[y[i],ym[i]], [z_xy, 0] , color = 'b', alpha = 0.5)
                    ax.plot([u[i],um[i]],[v[i],vm[i]], [z_m - z_uv, z_m], color = 'b', alpha = 0.5)
                    
                    j = 0
                temp_norm = norm_3d(xm[i], ym[i], 0, um[i], vm[i], z_m)
                point_dist_list.append(temp_norm)
                j += 1
                i += 1
            
            return np.array(point_dist_list)                  
            
        
        else:
            return np.array([])
    except:
        return np.array([])
        pass


def file_chk(filename):
    if op.exists(filename) == True:
        if filename.split('.')[-1] == "dxf":
            return 1
        else:
            return 0
    else:
        return -1


#Ver2.0　変更 Gコード出力形式
def gen_g_code_line_str(x,y,u,v):
    code_str = ""
    if len(x) == len(y) == len(u) == len(v):
        i = 0
        while i < len(x):
            code_str += "G01 X%s Y%s U%s V%s\n"%(x[i], y[i], u[i], v[i])
            i += 1
        return code_str


#ver2.2 追加　円弧をスプライン化する機能の追加
def arc_to_spline(arc_obj): #ezdxf arcオブジェクト
    
    radius = arc_obj.dxf.radius
    x_center_point  = arc_obj.dxf.center[0]
    y_center_point  = arc_obj.dxf.center[1]
    start_angle     = arc_obj.dxf.start_angle
    end_angle       = arc_obj.dxf.end_angle
    
    if end_angle < start_angle:
        end_angle += 360
        
    num_point = int(np.abs(end_angle - start_angle)/10.0)
    if num_point < 3:
        num_point = 3
    angle_array = np.radians(np.linspace(start_angle, end_angle, num_point))
    x_p = radius * np.cos(angle_array) + x_center_point
    y_p = radius * np.sin(angle_array) + y_center_point
    
    return np.array([x_p, y_p]).T


#ver2.2　追加 ポリラインを点列化する機能の追加 
def poly_to_spline(poly_obj):
    point_x = np.array(poly_obj.get_points())[:,0]
    point_y = np.array(poly_obj.get_points())[:,1]
    new_point_x = [point_x[0]]
    new_point_y = [point_y[0]]
    
    i = 1
    while i < len(point_x)-1:
        new_point_x.append(point_x[i])
        new_point_x.append(point_x[i])
        
        new_point_y.append(point_y[i])
        new_point_y.append(point_y[i])
        
        i += 1

    new_point_x.append(point_x[-1])
    new_point_y.append(point_y[-1])
    
    return np.array([new_point_x, new_point_y]).T



#======================================================================================================================================
#            ボタンにより呼び出される関数
#======================================================================================================================================
#
#   open_explorer(dxf_file　dxf_obj, tk.Entry entry, messeage_window messeage_window)
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
        

def open_explorer(dxf_obj, entry, messeage_window):
    fTyp = [("","*")]
    iDir = os.path.abspath(os.path.dirname(__file__))
    selected_file_path = tk.filedialog.askopenfilename(filetypes = fTyp,initialdir = iDir)
    entry.delete(0,tk.END)
    entry.insert(tk.END, selected_file_path)
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
        table_XY.set_parent(1)
        table_UV.set_parent(0)
        messeage_window.set_messeage("U-V画面をX-Y画面と連動\n")
    else:
        table_XY.set_parent(0)
        table_UV.set_parent(0)       
        messeage_window.set_messeage("U-V画面とX-Y画面の連動を解除\n")


def swap_line(dxf_obj, messeage_window):
    selected_items = dxf_obj.Swap_Selected_line()
    if len(selected_items) == 2:
        messeage_window.set_messeage("%sと%s番目のラインを入れ替えました。\n"%(item2num(selected_items[0]), item2num(selected_items[1])))
    else:
        messeage_window.set_messeage("２つのラインを選択して下さい。%s本のラインが選択されています。\n"%len(selected_items))


def Change_CutDir(dxf_obj, messeage_window):
    dxf_obj.Change_CutDir()
    messeage_window.set_messeage("カット方向を逆転\n")
    

def Change_OffsetDir(dxf_obj, messeage_window):
    dxf_obj.Change_OffsetDir()
    messeage_window.set_messeage("オフセット方向を逆転\n")


def Set_OffsetDist(dxf_obj0, dxf_obj1, entry, messeage_window):
    entry_value = entry.get()
    try:
        OffsetDist = float(entry_value)
        dxf_obj0.set_offset_dist(OffsetDist)
        dxf_obj1.set_offset_dist(OffsetDist)
        messeage_window.set_messeage("オフセット距離を%sに設定しました。\n"%OffsetDist)
    except:
        messeage_window.set_messeage("実数値を入力して下さい。\n")
        pass


def Merge_line(dxf_obj, messeage_window):
    selected_items = dxf_obj.Merge_Selected_line()
    if len(selected_items) == 1:
        messeage_window.set_messeage("%s番目のラインに結合しました。\n"%item2num(selected_items[0]))
    elif len(selected_items) == 2:
        messeage_window.set_messeage("２つの近接したラインを選択して下さい。ラインの端点間の距離が遠すぎます。\n")
    elif len(selected_items) == 0:
        messeage_window.set_messeage("２つのラインを選択してください。1本しかラインが選択されていません。\n")
    else:
        messeage_window.set_messeage("２つのラインを選択して下さい。%s本のラインが選択されています。\n"%len(selected_items))
        
        
def delete_line(dxf_obj, messeage_window):
    dxf_obj.delete_Selected_line()
    messeage_window.set_messeage("ラインを削除しました。\n")
    
    
def AutoLineSort(dxf_obj0, dxf_obj1, entry_x, entry_y, messeage_window):
    entry_x_value = entry_x.get()
    entry_y_value = entry_y.get()
    
    try:
        ox = float(entry_x_value)
        oy = float(entry_y_value)
        dxf_obj0.SortLine(ox, oy)
        dxf_obj1.SortLine(ox, oy)
        messeage_window.set_messeage("自動整列しました。\n")
    except:
        messeage_window.set_messeage("実数値を入力して下さい。\n")
        pass


def Reverse(dxf_obj, messeage_window):
    dxf_obj.reverse_all()
    messeage_window.set_messeage("カット順を逆転しました。\n")


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


# Ver2.1変更　引数追加，距離別指定可能
def gen_g_code(dxf_obj0, dxf_obj1, entry_ox, entry_oy, entry_ex, entry_ey, entry_XYDist, entry_UVDist, entry_WorkLength, entry_MachDist, entry_CS, entry_dl, header, messeage_window, X_str, Y_str, U_str, V_str):
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
    code_line_list.append(header)
    
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
        code_line_list.append("F%s\n"%CS)
        code_line_list.append("G01 X%f Y%f U%f V%f\n"%(ox, oy, ox, oy))
        
        a_line_num_list0 = np.array(np.array(dxf_obj0.line_num_list.copy())[np.where(np.array(dxf_obj0.line_num_list.copy()) >= 0)])
        a_line_num_list1 = np.array(np.array(dxf_obj1.line_num_list.copy())[np.where(np.array(dxf_obj1.line_num_list.copy()) >= 0)])
        
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
                    
                    N = int(max(line0_length, line1_length)/ dl)
                    if N < 2:
                        N = 2
                    
                    x, y = generate_arc_length_points(line0, N)
                    u, v = generate_arc_length_points(line1, N)
                    
                    #オフセット面の作成
                    x_m, y_m, u_m, v_m = make_offset_path(x, y, u, v, Z_XY, Z_UV, Z_Mach)
                    
                    code_line_list.append(gen_g_code_line_str(x_m, y_m, u_m, v_m))
                    
                    i += 1
                #Ver2.0　変更 Gコード出力形式
                code_line_list.append("G01 X%f Y%f U%f V%f\n"%(ex, ey, ex, ey))
                
                replaced_code_line_list = []
                for g_code_str in code_line_list:
                    replaced_code_line_list.append(Replace_G01_code(g_code_str, X_str, Y_str, U_str, V_str))
                
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
        messeage_window.set_messeage("Gコード生成途中でエラーが発生しました。\n\n")
        pass

    
#Ver2.1変更　引数追加，距離別指定可能
def path_chk(Root, dxf_obj0, dxf_obj1, entry_ox, entry_oy, entry_ex, entry_ey, entry_XYDist, entry_UVDist, entry_WorkLength, entry_MachDist, entry_dl, messeage_window):
        
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
                
                N = int(max(line0_length, line1_length)/ dl)
                if N < 2:
                    N = 2
                
                x, y = generate_arc_length_points(line0, N)
                u, v = generate_arc_length_points(line1, N)
                
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
        messeage_window.set_messeage("パスチェック中にエラーが発生しました。\n")
        pass      


def _destroyWindow():
    root.quit()
    root.destroy()



#======================================================================================================================================
#            メイン関数
#======================================================================================================================================


if __name__ == "__main__":


    #======================================================================================================================================
    #            config.csvファイルの読込
    #======================================================================================================================================
    try:
        file = np.genfromtxt("config.csv", delimiter = ",", skip_header = 1, dtype = np.str)
        data = file[:,2]
        FILENAME_XY = data[0]
        FILENAME_UV = data[1]
        OX = float(data[2])
        OY = float(data[3])
        EX = float(data[4])
        EY = float(data[5])
        DELTA_LENGTH = float(data[6])
        OFFSET_DIST = float(data[7])
        CUTSPEED = float(data[8])
        XY_DIST = float(data[9])
        UV_DIST = float(data[10])
        WORK_LENGTH = float(data[11])
        MACH_DIST = float(data[12])
        HEADER = data[13].replace("\\n", "\n")
        X_str = str(data[14])
        Y_str = str(data[15])
        U_str = str(data[16])
        V_str = str(data[17])
        MESSEAGE = "config.csvを読み込みました。\n"
        
    except:
        FILENAME_XY = "ファイル名を入力して下さい。"
        FILENAME_UV = "ファイル名を入力して下さい。"
        OX = 0.0
        OY = 0.0
        EX = 0.0
        EY = 0.0
        DELTA_LENGTH = 1.0
        OFFSET_DIST = 0.0
        CUTSPEED = 200
        XY_DIST = 25.0
        UV_DIST = 50.0
        WORK_LENGTH = 425
        MACH_DIST = 500
        HEADER = "T1\nG17 G49 G54 G80 G90 G94 G21 G40 G64\n"
        X_str = 'X'
        Y_str = 'Y'
        U_str = 'Z'
        V_str = 'A'
        MESSEAGE = "config.csvを読み込めませんでした。\n"
        pass
    
       
    #======================================================================================================================================
    #            rootインスタンスの生成
    #======================================================================================================================================
    
    #【メインウィンドウ】
    root = tk.Tk()                                                   #メインウィンドウの枠となるインスタンス
    root.title("HotwireDXF CAM")                                     #メインウィンドウの名称
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
    MessageWindow.place(x = 852, y = 805)
    MessageWindow.set_messeage(MESSEAGE)
    MessageWindow.set_messeage("Gコードの書き出しは「%s」です。\n"%HEADER)
    MessageWindowLabel = tk.Label(root, text="メッセージウィンドウ",font=("",12))
    MessageWindowLabel.place(x = 860, y = 780)



    #======================================================================================================================================
    #           entryインスタンスの生成
    #======================================================================================================================================

    #【X-Y用 dxfファイル名の入力コンソール】
    FileNameEntry0 = tk.Entry(root, width=50) 
    FileNameEntry0.insert(tk.END, FILENAME_XY) 
    FileNameEntry0.place(x = 852, y = 35)
    
    
    #【U-V用 dxfファイル名の入力コンソール】
    FileNameEntry1 = tk.Entry(root, width=50) 
    FileNameEntry1.insert(tk.END, FILENAME_UV)   
    FileNameEntry1.place(x = 1252, y = 35) 


    #【切り出し原点入力コンソール】
    AutoAlignmentLabel0 = tk.Label(root, text="切り出し原点",font=("",15))
    AutoAlignmentLabel0.place(x = 850, y = 510)
    AutoAlignmentLabel1 = tk.Label(root, text="X：",font=("",15))
    AutoAlignmentLabel1.place(x = 1000, y = 510)
    AutoAlignmentLabel2 = tk.Label(root, text="Y：",font=("",15))
    AutoAlignmentLabel2.place(x = 1120, y = 510)
    AutoAlignmentEntry_X = tk.Entry(root, width=8,font=("",15)) 
    AutoAlignmentEntry_X.insert(tk.END, OX)       
    AutoAlignmentEntry_X.place(x = 1030, y = 510)   
    AutoAlignmentEntry_Y = tk.Entry(root, width=8,font=("",15))     
    AutoAlignmentEntry_Y.insert(tk.END, OY)
    AutoAlignmentEntry_Y.place(x = 1150, y = 510)    


    #【切り出し終点入力コンソール】
    CutEndLabel0 = tk.Label(root, text="切り出し終点",font=("",15))
    CutEndLabel0.place(x = 850, y = 540)
    CutEndLabel1 = tk.Label(root, text="X：",font=("",15))
    CutEndLabel1.place(x = 1000, y = 540)
    CutEndLabel2 = tk.Label(root, text="Y：",font=("",15))
    CutEndLabel2.place(x = 1120, y = 540)
    CutEndEntry_X = tk.Entry(root, width=8,font=("",15)) 
    CutEndEntry_X.insert(tk.END, EX)       
    CutEndEntry_X.place(x = 1030, y = 540)   
    CutEndEntry_Y = tk.Entry(root, width=8,font=("",15))     
    CutEndEntry_Y.insert(tk.END, EY)
    CutEndEntry_Y.place(x = 1150, y = 540) 


    #【分割距離入力コンソール】
    dlLabel = tk.Label(root, text="分割距離[mm]",font=("",15))
    dlLabel.place(x = 850, y = 580)
    dlEntry = tk.Entry(root, width=8,font=("",15))     
    dlEntry.insert(tk.END, DELTA_LENGTH)
    dlEntry.place(x = 1030, y = 580)       


    #【オフセット距離入力コンソール】    
    OffsetLabel = tk.Label(root, text="オフセット距離[mm]",font=("",15))
    OffsetLabel.place(x = 850, y = 620)
    OffsetEntry = tk.Entry(root, width=8,font=("",15))     
    OffsetEntry.insert(tk.END, OFFSET_DIST)
    OffsetEntry.place(x = 1030, y = 620)    


    #【カット速度入力コンソール】   
    CutSpeedLabel = tk.Label(root, text="カット速度[mm/分]",font=("",15))
    CutSpeedLabel.place(x = 850, y = 660)
    CutSpeedEntry = tk.Entry(root, width=8,font=("",15))     
    CutSpeedEntry.insert(tk.END, CUTSPEED)
    CutSpeedEntry.place(x = 1030, y = 660)    


    # Ver2.1 変更
    #【カット面距離入力コンソール1】   
    XYDistLabel = tk.Label(root, text="XY面距離[mm]",font=("",15))
    XYDistLabel.place(x = 850, y = 700)
    XYDistEntry = tk.Entry(root, width=8,font=("",15))     
    XYDistEntry.insert(tk.END, XY_DIST)
    XYDistEntry.place(x = 1030, y = 700)  

    # Ver2.1 追加
    #【カット面距離入力コンソール2】   
    UVDistLabel = tk.Label(root, text="UV面距離[mm]",font=("",15))
    UVDistLabel.place(x = 1150, y = 700)
    UVDistEntry = tk.Entry(root, width=8,font=("",15))     
    UVDistEntry.insert(tk.END, UV_DIST)
    UVDistEntry.place(x = 1330, y = 700)  


    #Ver2.1 追加 
    #【XY-UV面距離入力コンソール】   
    WorkLengthLabel = tk.Label(root, text="XY-UV面距離[mm]",font=("",15))
    WorkLengthLabel.place(x = 850, y = 740)
    WorkLengthEntry = tk.Entry(root, width=8,font=("",15))     
    WorkLengthEntry.insert(tk.END, WORK_LENGTH)
    WorkLengthEntry.place(x = 1030, y = 740)


    #Ver2.1 位置変更 
    #【マシン距離入力コンソール】   
    MachDistLabel = tk.Label(root, text="駆動面距離[mm]",font=("",15))
    MachDistLabel.place(x = 1150, y = 740)
    MachDistEntry = tk.Entry(root, width=8,font=("",15))     
    MachDistEntry.insert(tk.END, MACH_DIST)
    MachDistEntry.place(x = 1330, y = 740)  




    #======================================================================================================================================
    #            ボタンインスタンスの生成
    #======================================================================================================================================

    #【X-Y用 dxfファイル読込用のエクスプローラーを開くボタン】
    LoadBtn0 = tk.Button(root, text="開く", command = lambda: open_explorer(dxf0, FileNameEntry0, MessageWindow))
    LoadBtn0.place(x=1160, y=30)  

    #【U-V用 dxfファイル読込用のエクスプローラーを開くボタン】   
    LoadBtn1 = tk.Button(root, text="開く", command = lambda: open_explorer(dxf1, FileNameEntry1, MessageWindow))
    LoadBtn1.place(x=1560, y=30)    

    #【X-Y用 dxfファイル名の読込ボタン】
    LoadBtn0 = tk.Button(root, text="再読込", command = lambda: load_file(dxf0, FileNameEntry0, MessageWindow))
    LoadBtn0.place(x=1200, y=30)  

    #【U-V用 dxfファイル名の読込ボタン】   
    LoadBtn1 = tk.Button(root, text="再読込", command = lambda: load_file(dxf1, FileNameEntry1, MessageWindow))
    LoadBtn1.place(x=1600, y=30)    

    #【X-Yラインテーブル用　カット方向入れ替えボタン】
    ChangeCutDirBtn0 = tk.Button(root, text="カット方向入替え", width =15, bg = "#3cb371", command = lambda: Change_CutDir(dxf0, MessageWindow))
    ChangeCutDirBtn0.place(x=855, y=435)   
       
    #【X-Yラインテーブル用　オフセット方向入れ替えボタン】    
    ChangeOffsetDirBtn0 = tk.Button(root, text="オフセット方向入替え", width =15, bg = "#3cb371", command = lambda: Change_OffsetDir(dxf0, MessageWindow))
    ChangeOffsetDirBtn0.place(x=990, y=435)
            
    #【X-Yラインテーブル用　カット順逆転ボタン】    
    ReverseBtn0 = tk.Button(root, text="カット順逆転", width =15, bg = "#3cb371", command = lambda: Reverse(dxf0, MessageWindow))
    ReverseBtn0.place(x=1125, y=435)  
    
    #【X-Yラインテーブル用　ライン入れ替えボタン】
    SwapBtn0 = tk.Button(root, text="ライン入れ替え", width =15, bg = "#fffacd", command = lambda: swap_line(dxf0, MessageWindow))
    SwapBtn0.place(x=855, y=465)    
    
    #【X-Yラインテーブル用　ライン結合ボタン】
    SwapBtn0 = tk.Button(root, text="ライン結合", width =15, bg = "#4ba3fb", command = lambda: Merge_line(dxf0, MessageWindow))
    SwapBtn0.place(x=990, y=465) 
        
    #【X-Yラインテーブル用　ライン削除ボタン】    
    DelateBtn0 = tk.Button(root, text="ライン削除", width = 15, bg = "#ff6347", command = lambda: delete_line(dxf0, MessageWindow))
    DelateBtn0.place(x=1125, y=465)
  
  
    #【U-Vラインテーブル用　カット方向入れ替えボタン】    
    ChangeCutDirBtn1 = tk.Button(root, text="カット方向入替え", width =15, bg = "#3cb371", command = lambda: Change_CutDir(dxf1, MessageWindow))
    ChangeCutDirBtn1.place(x=1255, y=435)
    
    #【U-Vラインテーブル用　オフセット方向入れ替えボタン】    
    ChangeOffsetDirBtn1 = tk.Button(root, text="オフセット方向入替え", width =15, bg = "#3cb371", command = lambda: Change_OffsetDir(dxf1, MessageWindow))
    ChangeOffsetDirBtn1.place(x=1390, y=435)
    
    #【U-Vラインテーブル用　カット順逆転ボタン】    
    ReverseBtn1 = tk.Button(root, text="カット順逆転", width =15, bg = "#3cb371", command = lambda: Reverse(dxf1, MessageWindow))
    ReverseBtn1.place(x=1525, y=435)   
    
    #【U-Vラインテーブル用　ライン入れ替えボタン】    
    SwapBtn1 = tk.Button(root, text="ライン入れ替え", width = 15, bg = "#fffacd", command = lambda: swap_line(dxf1, MessageWindow))
    SwapBtn1.place(x=1255, y=465)
 
    #【U-Vラインテーブル用　ライン結合ボタン】    
    DelateBtn1 = tk.Button(root, text="ライン結合", width = 15, bg = "#4ba3fb" , command = lambda: Merge_line(dxf1, MessageWindow))
    DelateBtn1.place(x=1390, y=465)   
 
    #【U-Vラインテーブル用　ライン削除ボタン】    
    DelateBtn1 = tk.Button(root, text="ライン削除", width = 15, bg = "#ff6347" , command = lambda: delete_line(dxf1, MessageWindow))
    DelateBtn1.place(x=1525, y=465)
    

    #【オフセット値更新ボタン】    
    OffsetBtn = tk.Button(root, text = "更新", height = 1, width = 5, command = lambda: Set_OffsetDist(dxf0, dxf1, OffsetEntry, MessageWindow))
    OffsetBtn.place(x = 1120, y = 618)


    #【自動整列ボタン】    
    AutoAlignmentBtn = tk.Button(root, text = "自動整列", height = 1, width = 12,font=("",15), bg='#fffacd', command = lambda: AutoLineSort(dxf0, dxf1, AutoAlignmentEntry_X, AutoAlignmentEntry_Y, MessageWindow))
    AutoAlignmentBtn.place(x = 1290, y = 505)


    #Ver2.0 変更　WorkDistWntryを追加
    #【パスチェックボタン】    
    ChkPassBtn = tk.Button(root, text = "パスチェック", height = 2, width = 12,font=("",15), bg='#3cb371', command = lambda: path_chk(root, dxf0, dxf1, AutoAlignmentEntry_X, AutoAlignmentEntry_Y, CutEndEntry_X, CutEndEntry_Y, XYDistEntry, UVDistEntry, WorkLengthEntry, MachDistEntry, dlEntry, MessageWindow))
    ChkPassBtn.place(x = 1480, y = 630)
    

    #Ver2.0 変更　MechDistEntry, WorkDistWntryを追加
    #【Gコード生成ボタン】        
    GenGCodeBtn = tk.Button(root, text = "Gコード生成", height = 2, width = 12,font=("",15), bg='#ff6347', command = lambda: gen_g_code(dxf0, dxf1, AutoAlignmentEntry_X, AutoAlignmentEntry_Y, CutEndEntry_X, CutEndEntry_Y, XYDistEntry, UVDistEntry, WorkLengthEntry, MachDistEntry, CutSpeedEntry, dlEntry, HEADER, MessageWindow, X_str, Y_str, U_str, V_str))
    GenGCodeBtn.place(x = 1480, y = 700)



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
