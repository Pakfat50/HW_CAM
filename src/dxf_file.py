# -*- coding: utf-8 -*-
"""
Created on Mon Aug 11 15:43:11 2025

@author: hirar
"""

# 外部ライブラリ
import tkinter as tk
import tkinter.ttk as ttk
import ezdxf as ez
import numpy as np
from matplotlib import pyplot as plt
import traceback

# 内部ライブラリ
from cam_generic_lib import *
from line_object import *
from cam_global import *
from error_log import *

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
        self.sync = False
        self.sync_update = False
        self.reset()
    
    
    def set_sync(self, sync):
        self.sync = sync
        self.sync_update = True
    
    
    def reset(self):
        try:
            self.table.destroy()
        except:
            # 初回はtableオブジェクトがないので、例外を許容する
            pass
        self.table = ttk.Treeview(self.root, height = self.y_height)
        self.table.place(x = self.x_pos, y = self.y_pos)
        self.table["column"] = (1,2,3,4)
        self.table["show"] = "headings"
        self.table.heading(1,text="番号")
        self.table.heading(2,text="オフセット距離")
        self.table.heading(3,text="タイプ")
        self.table.heading(4,text="カット速度")
        self.table.column(1, width=50)
        self.table.column(2, width=110)
        self.table.column(3, width=100)
        self.table.column(4, width=110)
        # スクロールバーの追加
        self.scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.table.yview)
        self.table.configure(yscroll=self.scrollbar.set)
        self.scrollbar.place(x = self.x_pos+375, y = self.y_pos+2, height = (self.y_height+1) * 20 + 7)
        
    
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
#   Merge_Selected_line()
#   【引数】 なし
#   【戻り値】　error, selected_items
#   【機能】　tableで選択されているラインが２本のみの場合、この２本を結合する。error（0: 成功, 1: 選択数が誤り, 2: 隣接していない）と、その時選択されているラインを取得する
#
#   Merge_line(char parent_item_num, char child_item_num)
#   【引数】 なし
#   【戻り値】　結合可否（boolean)
#   【機能】　parent_item_numで指定された線（parent_line）に、child_item_numで指定された線（child_line）を結合する
#            parent_lineとchild_lineの端点が一致するように線の向きを変更したうえで結合する。端点が一致しない場合、エラーとしてFalseを出力する
#            端点が一致する場合、parent_lineの座標点列（x_dxf, y_dxf）を結合した座標点に更新する（よって結合するのは、原点オフセット前のx_dxf, y_dxfとする）
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
#   offset_origin(float offset_ox, float offset_oy)
#   【引数】 offset_ox, offset_oy
#   【戻り値】　なし
#   【機能】　テーブルで表示しているラインの座標点を、offset_ox, offset_oyで指定される分だけオフセットする．　　　　　　　

class selected_point:
    def __init__(self, x, y, index):
        self.x = x
        self.y = y
        self.index = index
    
    def reset(self):
        self.x = np.nan
        self.y = np.nan
        self.index = None

class dxf_file:
    def __init__(self, ax, canvas, table, x_table, name):
        self.ax = ax
        self.canvas = canvas
        self.table = table
        self.x_table = x_table
        self.name = name
        self.line_list = []
        self.line_num_list = []
        self.selected_point = selected_point(np.nan, np.nan, None)
    
    
    def load_file(self, filename, is_refine):
        self.table.reset()
        self.filename = filename
        self.line_list = []
        self.line_num_list = []
        self.reload(is_refine)
        self.table.table.bind("<<TreeviewSelect>>", self.selected)
        self.table.table.loaded_item_num = len(self.table.table.get_children())
        self.selected_point.reset()
        
        items = self.table.table.get_children()
        self.table.table.selection_set(items[0])
        self.table.table.see(items[0])
        
        if AUTOSORT_WHEN_LOADFILE == True:
            self.SortLine()
        else:
            self.plot(keep_view=False)

    def reload(self, is_refine):
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
            temp_line_object = line_object(temp_spline_data[:,0], temp_spline_data[:,1], i, is_refine) 
            self.line_list.append(temp_line_object)
            self.line_num_list.append(i)
            self.table.table.insert("", "end", values=(temp_line_object.num, format(temp_line_object.offset_dist, '.4f'),\
                                                       temp_line_object.line_type, format(temp_line_object.cutspeed_work,'.2f')))
            i += 1
 
        #ver2.2追加　円弧，ポリラインの読み込み　ここから
        i_arc = 0        
        while i_arc < len(arc_obj):
            temp_arc = arc_obj[i_arc]
            temp_arc_data = arc_to_spline(temp_arc)
            temp_line_object = line_object(temp_arc_data[:,0], temp_arc_data[:,1], i + i_arc, is_refine) 
            self.line_list.append(temp_line_object)
            self.line_num_list.append(i + i_arc)
            self.table.table.insert("", "end", values=(temp_line_object.num, format(temp_line_object.offset_dist, '.4f'), \
                                                       temp_line_object.line_type, format(temp_line_object.cutspeed_work,'.2f')))
            i_arc += 1        
        i = i + i_arc

        i_poly = 0
        while i_poly < len(poly_obj):
            temp_poly = poly_obj[i_poly]
            temp_poly_data = poly_to_spline(temp_poly)
            temp_line_object = line_object(temp_poly_data[:,0], temp_poly_data[:,1], i + i_poly, is_refine) 
            temp_line_object.interp_mode = "linear" #poly_lineであることを設定する
            self.line_list.append(temp_line_object)
            self.line_num_list.append(i + i_poly)
            self.table.table.insert("", "end", values=(temp_line_object.num, format(temp_line_object.offset_dist, '.4f'), \
                                                       temp_line_object.line_type, format(temp_line_object.cutspeed_work,'.2f')))
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
                temp_line_object = line_object(temp_line_data[:,0], temp_line_data[:,1], i+k, is_refine) 
                self.line_list.append(temp_line_object)
                self.line_num_list.append(i+k)
                self.table.table.insert("", "end", values=(temp_line_object.num, format(temp_line_object.offset_dist, '.4f'), \
                                                           temp_line_object.line_type, format(temp_line_object.cutspeed_work,'.2f')))
                k += 1
            j += 1
            

    def table_reload(self):
        table_item_list = self.table.table.get_children()
        i = 0
        while i < len(table_item_list):
            temp_item_num = table_item_list[i]
            line_num = self.line_num_list[item2num(temp_item_num)]
            temp_line_object = self.line_list[line_num]
            self.table.table.item(temp_item_num, values=(temp_line_object.num, format(temp_line_object.offset_dist, '.4f'), \
                                                         temp_line_object.line_type, format(temp_line_object.cutspeed_work,'.2f')))
            i += 1

    
    def plot(self, keep_view=True):
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
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
                    
                if line_num in self.get_selected_lines():
                    alpha_line = 1
                    alpha_vect = 1
                    alpha_offset = 1
                    pick = True
                else:
                    alpha_line = 0.1
                    alpha_vect = 0.1
                    alpha_offset = 0
                    pick = None
                    
                self.ax.plot(temp_line_object.x, temp_line_object.y, color = col, alpha = alpha_line, marker='o', markersize=2, picker = pick)
                X,Y = temp_line_object.x[0], temp_line_object.y[0]
                U,V = temp_line_object.x[1], temp_line_object.y[1]
                self.ax.quiver(X,Y,U-X,V-Y,color = col, alpha = alpha_vect)
                if temp_line_object.cut_dir == "F":
                    X,Y = temp_line_object.x_raw[0], temp_line_object.y_raw[0]
                    U,V = temp_line_object.x[0], temp_line_object.y[0]
                else:
                    X,Y = temp_line_object.x_raw[-1], temp_line_object.y_raw[-1]
                    U,V = temp_line_object.x[0], temp_line_object.y[0]            
                if norm(X,Y,U,V) != 0:
                    self.ax.quiver(X,Y,U-X,V-Y,color = "y", alpha = alpha_offset) #ver2.2 バグ修正 Y を y に変更
  
            i += 1
        
        self.ax.plot(self.selected_point.x, self.selected_point.y, "ro")
        
        if keep_view == True:
            self.ax.set_xlim(xlim)
            self.ax.set_ylim(ylim)
        self.canvas.draw()
        
        
    def get_selected_lines(self):
        selected_items = self.table.table.selection()
        if not selected_items:
            return [9999]
        
        ret = []
        for item in selected_items:
            item_num = item2num(item)
            line_num = self.line_num_list[item_num]
            ret.append(line_num)
        return ret
    
    
    def get_selected_point(self, event):
        line = event.artist
        x, y = line.get_data()
        index = event.ind[0]
        self.selected_point = selected_point(x[index], y[index], index)
        self.plot()
        
    
    def selected(self, event):
        selected_items = self.table.table.selection()
        self.selected_point.reset()
        if not len(selected_items) == 0:
            self.plot()
            
            if self.table.sync == True:
                if self.x_table.sync_update == True:
                    self.x_table.sync_update = False
                    try:
                        x_selected_items = []
                        for item in selected_items:
                            item_index = self.table.table.get_children().index(item)
                            x_item = self.x_table.table.get_children()[item_index]
                            x_selected_items.append(x_item)
                        self.x_table.table.selection_set(x_selected_items)
                        self.x_table.table.see(x_selected_items)
                    except:
                        # XY-UV画面同期中に線数が異なると選択できないため、例外を許容する
                        # traceback.print_exc()
                        pass
                else:
                    self.x_table.sync_update = True
                    self.table.sync_update = True
            
                
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
            temp_line_object.toggle_offset_dir()
            temp_line_object.update()
            self.table.table.item(temp_item_num, values=(temp_line_object.num, format(temp_line_object.offset_dist, '.4f'), \
                                                         temp_line_object.line_type, format(temp_line_object.cutspeed_work,'.2f')))
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
            self.table.table.item(temp_item_num, values=(temp_line_object.num, format(temp_line_object.offset_dist, '.4f'), \
                                                         temp_line_object.line_type, format(temp_line_object.cutspeed_work,'.2f')))
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


    def Merge_Selected_line(self):
        selected_items = self.table.table.selection()
        
        if len(selected_items) >= 2:
            result_list= [True]
            line_num_list = []
            for item in selected_items:
                line_num_list.append(self.line_num_list[item2num(item)])
            
            i = 1
            while i < len(selected_items):      
                result = self.Merge_line(selected_items[0], selected_items[i])
                self.delete_line(selected_items[i])
                result_list.append(result)
                i += 1
            self.table_reload()
            self.plot()
        elif len(selected_items) == 1:
            result_list = [True]
            line_num_list = [self.line_num_list[item2num(selected_items[0])]]
        else:
            result_list = []
            line_num_list = []
            
        return result_list, line_num_list


    def Merge_line(self, parent_item_num, child_item_num):
        parent_line_num = self.line_num_list[item2num(parent_item_num)]
        child_line_num = self.line_num_list[item2num(child_item_num)]
        parent_line = self.line_list[parent_line_num]
        child_line = self.line_list[child_line_num]
        
        x_p_st = parent_line.st[0]
        y_p_st = parent_line.st[1]
        x_c_st = child_line.st[0]
        y_c_st = child_line.st[1]

        x_p_ed = parent_line.ed[0]
        y_p_ed = parent_line.ed[1]
        x_c_ed = child_line.ed[0]
        y_c_ed = child_line.ed[1]
        
        x_p = parent_line.x_dxf.tolist()
        y_p = parent_line.y_dxf.tolist()
        x_c = child_line.x_dxf.tolist()
        y_c = child_line.y_dxf.tolist()     
        
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
        
        parent_line.reset_point(new_x, new_y, parent_line.offset_ox, parent_line.offset_oy)
        return True    
    
    """
    def Separate_line(self):
        selected_item = self.table.table.selection()
        
        if len(selected_items) == 1: 
            
            result = self.Merge_line(selected_items[0], selected_items[i])
            self.delete_line(selected_items[i])


            self.table_reload()
            self.plot()
            
        else:
            result_list = []
            line_num_list = []
            
        return result_list, line_num_list        
    """
    
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
                temp_line.toggle_offset_dir()
                self.line_num_list[i] = temp_num                
                j += 1
                i += 1
            else:
                i += 1
        
        self.table_reload()
        self.plot()
        
    
    def SortLine(self):
        selected_items = self.table.table.selection()   
        
        if not(len(selected_items) == 1):
            return len(selected_items)
        else:
            item_num_st = selected_items[0]
            line_num_st = self.line_num_list[item2num(item_num_st)]
            line_object_st = self.line_list[line_num_st]
            cut_dir_st = line_object_st.cut_dir
            i = 0
            norm_mn = np.inf
            if cut_dir_st == 'F':
                x0 = line_object_st.ed[0]
                y0 = line_object_st.ed[1]
                x_array = np.array(line_object_st.x_raw)
                y_array = np.array(line_object_st.y_raw)
            else:
                x0 = line_object_st.st[0]
                y0 = line_object_st.st[1]   
                x_array = np.array(line_object_st.x_raw[::-1])
                y_array = np.array(line_object_st.y_raw[::-1])
                
            alaivable_line_num_list = sorted(np.array(self.line_num_list.copy())[np.where(np.array(self.line_num_list.copy()) >= 0)])
            new_line_nums = [line_num_st]
            
            new_line_num_list = []
            x_array_list = []
            y_array_list = []
            
    
            while i < len(alaivable_line_num_list) - 1:
                norm_mn = np.inf
                j = 0
                while j < len(alaivable_line_num_list):
                    num1 = alaivable_line_num_list[j]
                    if (num1 in sum(new_line_num_list, [])) or (num1 in new_line_nums):
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
                    temp_x = temp_line1.x_raw
                    temp_y = temp_line1.y_raw
                                             
                if temp_cut_dir == 'R':
                    x0 = temp_line1.st[0]
                    y0 = temp_line1.st[1]
                    temp_x = temp_line1.x_raw[::-1]
                    temp_y = temp_line1.y_raw[::-1]
                          
                temp_line1.set_cut_dir(temp_cut_dir)
                
                if norm_mn <= DIST_NEAR:
                    new_line_nums.append(temp_line_num1)
                    x_array = np.concatenate([x_array, temp_x], 0)
                    y_array = np.concatenate([y_array, temp_y], 0)
                else:
                    new_line_num_list.append(new_line_nums)
                    x_array_list.append(x_array)
                    y_array_list.append(y_array)
                    new_line_nums = [temp_line_num1]
                    x_array = np.array(temp_x)
                    y_array = np.array(temp_y)
                
                i += 1
                
            new_line_num_list.append(new_line_nums)
            x_array_list.append(x_array)
            y_array_list.append(y_array)    
             
            
            ccw_list = []
            i = 0
            while i < len(x_array_list):
                temp_x_array = x_array_list[i]
                temp_y_array = y_array_list[i]
                temp_ccw = detectRotation(temp_x_array, temp_y_array)
                ccw_list.append(temp_ccw)
                i += 1
            
            ccw_st = ccw_list[0]
            i = 0
            while i < len(ccw_list):
                temp_ccw = ccw_list[i]
                temp_line_nums = new_line_num_list[i]
                if not(temp_ccw == ccw_st):
                    temp_line_nums = temp_line_nums[::-1]
                    new_line_num_list[i] = temp_line_nums
                    
                for num in temp_line_nums:
                    temp_line = self.line_list[num]
                    if not(temp_ccw == ccw_st):
                        temp_line.toggle_cut_dir()
                    if ccw_st == True:
                        temp_line.set_offset_dir('O')
                    else:
                        temp_line.set_offset_dir('I')
                i += 1
            
            
            i = 0
            j = 0
            while i < len(self.line_num_list):
                if self.line_num_list[i] >= 0:
                    self.line_num_list[i] = sum(new_line_num_list,[])[j]
                    j += 1
                    i += 1
                else:
                    i += 1
            
            items = self.table.table.get_children()
            
            self.table_reload()
            self.table.table.selection_set(items[0])
            self.table.table.see(items[0])
            self.plot(keep_view=False)
            return 1


    def offset_origin(self, offset_ox, offset_oy):
        table_item_list = self.table.table.get_children()
        i = 0
        while i < len(table_item_list):
            temp_item_num = table_item_list[i]
            line_num = self.line_num_list[item2num(temp_item_num)]
            temp_line_object = self.line_list[line_num]
            temp_line_object.reset_point(temp_line_object.x_dxf, temp_line_object.y_dxf, offset_ox, offset_oy)
            temp_line_object.update()
            i += 1   
        self.table_reload()
        self.plot()
    
    def set_remove_self_collision(self, val):
        alaivable_line_num_list = np.array(np.array(self.line_num_list.copy())[np.where(np.array(self.line_num_list.copy()) >= 0)])
        
        i = 0
        j = 0
        while i < len(self.line_num_list):
            if self.line_num_list[i] >= 0:
                temp_num = alaivable_line_num_list[j]
                temp_line = self.line_list[temp_num]
                temp_line.remove_self_collision = val
                j += 1
                i += 1
            else:
                i += 1    

    def check_self_collision(self):
        alaivable_line_num_list = np.array(np.array(self.line_num_list.copy())[np.where(np.array(self.line_num_list.copy()) >= 0)])
        col_line_num_list = []
        
        i = 0
        j = 0
        while i < len(self.line_num_list):
            if self.line_num_list[i] >= 0:
                temp_num = alaivable_line_num_list[j]
                temp_line = self.line_list[temp_num]
                temp_line.update()
                
                if temp_line.self_collision == True:
                    col_line_num_list.append(temp_num)
                j += 1
                i += 1
            else:
                i += 1
                
        self.table_reload()
        self.plot()
        return col_line_num_list
    

###############   dxf_fileクラス   ここまで　　    　#########################################################################################
#######################################################################################################################################     

