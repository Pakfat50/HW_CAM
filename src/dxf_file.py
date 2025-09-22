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
import copy

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
        self.selected_point = selected_point(np.nan, np.nan, None)
        self.line_num_max = 0
    
    
    def load_file(self, filename, is_refine):
        self.table.reset()
        self.filename = filename
        self.line_list = []
        self.reload(is_refine)
        self.table.table.bind("<<TreeviewSelect>>", self.selected)
        self.table.table.loaded_item_num = len(self.table.table.get_children())
        self.selected_point.reset()
        
        items = self.table.table.get_children()
        self.table.table.selection_set(items[0])
        self.table.table.see(items[0])
        
        if AUTOSORT_WHEN_LOADFILE == True:
            self.SortLine()
            self.reset_line_num()

    
    def reset_line_num(self):
        i = 0
        for line in self.line_list:
            line.num = i
            i += 1
        self.table_reload()
            

    def get_index(self, all = False):
        if all == True:
            items = self.table.table.get_children()
        else:
            items = self.table.table.selection()
        indexs = []
        if not len(items) == 0:
            for item in items:
                index = self.table.table.get_children().index(item)
                indexs.append(index)
        return indexs
    
    def get_item(self, all = False):
        if all == True:
            items = self.table.table.get_children()
        else:
            items = self.table.table.selection()
        return items
    
    def get_item_from_index(self, indexs):
        if isinstance(indexs, int) == True:
            item = self.table.table.get_children()[indexs]
            return item
        else:
            items = []
            for index in indexs:
                item = self.table.table.get_children()[index]
                items.append(item)
            return items

    def get_index_from_item(self, items):
        if isinstance(items, str) == True:
            index = self.table.table.get_children().index(items)
            return index
        
        else:
            indexs = []
            for item in items:
                index = self.table.table.get_children().index(item)
                indexs.append(index)
            return indexs

    def reload(self, is_refine):
        dwg = ez.readfile(self.filename)
        modelspace = dwg.modelspace()
        line_segment_obj = modelspace.query('LINE')
        spline_obj = modelspace.query('SPLINE')
        arc_obj = modelspace.query('ARC') #ver2.2追加
        poly_obj = modelspace.query('LWPOLYLINE') #ver2.2追加
        
        i = 0
        while i < len(spline_obj):
            spline = spline_obj[i]
            spline_data = np.array(spline.control_points)[:]
            line = line_object(spline_data[:,0], spline_data[:,1], i, is_refine) 
            self.line_list.append(line)
            self.table.table.insert("", "end", values=(line.num, format(line.offset_dist, '.4f'),\
                                                       line.line_type, format(line.cutspeed_work,'.2f')))
            i += 1
 
        #ver2.2追加　円弧，ポリラインの読み込み　ここから
        i_arc = 0        
        while i_arc < len(arc_obj):
            arc = arc_obj[i_arc]
            arc_data = arc_to_spline(arc)
            line = line_object(arc_data[:,0], arc_data[:,1], i + i_arc, is_refine) 
            self.line_list.append(line)
            self.table.table.insert("", "end", values=(line.num, format(line.offset_dist, '.4f'), \
                                                       line.line_type, format(line.cutspeed_work,'.2f')))
            i_arc += 1        
        i = i + i_arc

        i_poly = 0
        while i_poly < len(poly_obj):
            poly = poly_obj[i_poly]
            poly_data = poly_to_spline(poly)
            line = line_object(poly_data[:,0], poly_data[:,1], i + i_poly, is_refine) 
            line.interp_mode = "linear" #poly_lineであることを設定する
            self.line_list.append(line)
            self.table.table.insert("", "end", values=(line.num, format(line.offset_dist, '.4f'), \
                                                       line.line_type, format(line.cutspeed_work,'.2f')))
            i_poly += 1    
        i = i + i_poly
        #ver2.2追加　ここまで

        j = 0
        k = 0
        while j < len(line_segment_obj):
            line_segment = line_segment_obj[j]
            line_segment_data = [line_segment.dxf.start, line_segment.dxf.end]
            line_segment_data = np.array(line_segment_data)[:,0:2]
            
            if norm(line_segment_data[0,0],line_segment_data[0,1],line_segment_data[1,0],line_segment_data[1,1]) > DIST_NEAR:
                line = line_object(line_segment_data[:,0], line_segment_data[:,1], i+k, is_refine) 
                self.line_list.append(line)
                self.table.table.insert("", "end", values=(line.num, format(line.offset_dist, '.4f'), \
                                                           line.line_type, format(line.cutspeed_work,'.2f')))
                k += 1
            j += 1
            
        self.line_num_max = i+k-1
        
    def table_reload(self):
        all_items = self.get_item(all=True)
        
        for item in all_items:
            index = self.get_index_from_item(item)
            line = self.line_list[index]
            self.table.table.item(item, values=(line.num, format(line.offset_dist, '.4f'), \
                                                line.line_type, format(line.cutspeed_work,'.2f')))

    
    def plot(self, keep_view=True):
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        self.ax.clear()
        self.ax.set_title(self.name)
        self.ax.set_aspect('equal')
        indexs = self.get_index()
        
        i = 0
        while i < len(self.line_list):
            line = self.line_list[i]
            if line.line_type == "line":
                col = "b"
            else:
                col = "b"
                
            if i in indexs:
                alpha_line = 1
                alpha_vect = 1
                alpha_offset = 1
                pick = True
            else:
                alpha_line = 0.1
                alpha_vect = 0.1
                alpha_offset = 0
                pick = None
                
            self.ax.plot(line.x, line.y, color = col, alpha = alpha_line, marker='o', markersize=2, picker = pick)
            X,Y = line.x[0], line.y[0]
            U,V = line.x[1], line.y[1]
            self.ax.quiver(X,Y,U-X,V-Y,color = col, alpha = alpha_vect)
            
            X,Y = line.x_raw[0], line.y_raw[0]
            U,V = line.x[0], line.y[0]
            if norm(X,Y,U,V) != 0:
                self.ax.quiver(U,V,U-X,V-Y,color = "y", alpha = alpha_offset) #ver2.2 バグ修正 Y を y に変更
  
            i += 1
        
        self.ax.plot(self.selected_point.x, self.selected_point.y, "ro")
        
        if keep_view == True:
            self.ax.set_xlim(xlim)
            self.ax.set_ylim(ylim)
        self.canvas.draw()
        
    
    def get_selected_point(self, event):
        line = event.artist
        x, y = line.get_data()
        index = event.ind[0]
        self.selected_point = selected_point(x[index], y[index], index)
        self.plot()
      
    
    def selected(self, event):
        items = self.get_item()

        self.selected_point.reset()
        if not len(items) == 0:
            self.plot()
            
            if self.table.sync == True:
                if self.x_table.sync_update == True:
                    self.x_table.sync_update = False
                    try:
                        x_selected_items = []
                        for item in items:
                            index = self.get_index_from_item(item)
                            x_item = self.x_table.table.get_children()[index]
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
    
    
    def update(self, keep_view=True):
        self.table_reload()
        self.plot(keep_view)        
    
                
    def set_offset_dist(self, offset_dist):
        all_items = self.get_item(all=True)

        for item in all_items:
            index = self.get_index_from_item(item)
            line = self.line_list[index]
            line.set_offset_dist(offset_dist)
        
        self.selected_point.reset()

    
    def remove_line_collision(self):
        all_items = self.get_item(all=True)
        line_nums = []

        i = 0
        while i < len(all_items)-1:
            index1 = self.get_index_from_item(all_items[i])
            index2 = self.get_index_from_item(all_items[i+1])
            line1 = self.line_list[index1]
            line2 = self.line_list[index2]
            x1 = line1.x
            y1 = line1.y
            x2 = line2.x
            y2 = line2.y
            x1, y1, x2, y2, detection = remove_collision(x1, y1, x2, y2)
            if detection == True:
                line1.x = x1
                line1.y = y1
                line2.x = x2
                line2.y = y2
                line_nums.append([line1.num, line2.num])
            i += 1

        self.selected_point.reset()
        return line_nums

    def Change_CutDir(self):
        items = self.get_item()

        for item in items:
            index = self.get_index_from_item(item)
            line = self.line_list[index]
            line.toggle_cut_dir()
            self.table.table.item(item, values=(line.num, format(line.offset_dist, '.4f'), \
                                                         line.line_type, format(line.cutspeed_work,'.2f')))
        self.selected_point.reset()


    def Merge_Selected_line(self):
        items = self.get_item()
        line_nums = []
        results = []
        
        for item in items:
            index = self.get_index_from_item(item)
            line = self.line_list[index]
            line_nums.append(line.num)
            
        if len(items) >= 2:
            results.append(True)
            
            i = 1
            while i < len(items):
                parent_index = self.get_index_from_item(items[0])
                child_index = self.get_index_from_item(items[i])
                parent_line = self.line_list[parent_index]
                child_line = self.line_list[child_index]
                
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
                    result = True
                elif norm(x_p_ed, y_p_ed, x_c_ed, y_c_ed) < LINE_MARGE_NORM_MN:
                    # 子ラインを反転させたのち、親ラインに子ラインを接続
                    x_c.reverse()
                    y_c.reverse()
                    new_x.extend(x_p)
                    new_y.extend(y_p)
                    new_x.extend(x_c)
                    new_y.extend(y_c)
                    result = True
                elif norm(x_p_st, y_p_st, x_c_ed, y_c_ed) < LINE_MARGE_NORM_MN:
                    # 子ラインに親ラインを接続
                    new_x.extend(x_c)
                    new_y.extend(y_c)
                    new_x.extend(x_p)
                    new_y.extend(y_p)
                    result = True
                elif norm(x_p_st, y_p_st, x_c_st, y_c_st) < LINE_MARGE_NORM_MN:
                    # 子ラインを反転させたのち、子ラインに親ラインに接続
                    x_c.reverse()
                    y_c.reverse()
                    new_x.extend(x_c)
                    new_y.extend(y_c)
                    new_x.extend(x_p)
                    new_y.extend(y_p)
                    result = True
                else:
                    # 端点が隣接していない線同士であるので、結合すべきではない。
                    result = False
                
                if result == True:
                    parent_line.reset_point(new_x, new_y, parent_line.offset_ox, parent_line.offset_oy)
                    self.delete_line(items[i])
                
                results.append(result)
                i += 1
                
            self.selected_point.reset()

        elif len(items) == 1:
            results = [True]
        else:
            results = []
            
        return results, line_nums
    
    
    def Separate_line(self):
        result = False
        items = self.get_item()
        line_nums = []
        for item in items:
            index = self.get_index_from_item(item)
            line = self.line_list[index]
            line_nums.append(line.num)
        point_index = self.selected_point.index
        
        if (len(items) == 1):
            index_org = self.get_index_from_item(items)[0]
            line_org = self.line_list[index_org]

            x_org = line_org.x_dxf.tolist()
            y_org = line_org.y_dxf.tolist()
            
            if (not(point_index == None)) and (not(point_index == 0)) \
                and (not(point_index == len(x_org)-1)):
            
                if not(line_org.cut_dir == 'F'):
                    point_index = len(x_org) - point_index -1
                
                x1 = x_org[:point_index+1]
                y1 = y_org[:point_index+1]
                x2 = x_org[point_index:]
                y2 = y_org[point_index:]
                
                x1, y1 = removeSamePoint(x1, y1)
                x2, y2 = removeSamePoint(x2, y2)
                
                line1 = copy.deepcopy(line_org)
                line2 = copy.deepcopy(line_org)
                
                line1.reset_point(x1, y1, line_org.offset_ox, line_org.offset_oy)
                line2.reset_point(x2, y2, line_org.offset_ox, line_org.offset_oy)
                
                num_new = self.line_num_max + 1
                self.line_num_max = num_new  
                line_nums.append(num_new)
                
                if line_org.cut_dir == 'F':
                    self.line_list[index_org] = line1
                    line2.num = num_new
                    self.add_line(items, line2)
                else:
                    self.line_list[index_org] = line2
                    line1.num = num_new
                    self.add_line(items, line1)
                
                self.selected_point.reset()
                result = True

        return result, line_nums, point_index

    
    def delete_Selected_line(self):
        items = self.get_item()
        for item in items:
            self.delete_line(item)           
        self.selected_point.reset()
        
        
    def delete_line(self, item):
        index = self.get_index_from_item(item)
        self.line_list.pop(index)
        self.table.table.delete(item)
    
    def add_line(self, item, line):
        index = self.get_index_from_item(item)[0]
        insert_index = index+1
        
        self.line_list.insert(insert_index, line)
        self.table.table.insert("",  insert_index, values=(line.num, format(line.offset_dist, '.4f'),\
                                                   line.line_type, format(line.cutspeed_work,'.2f')))
    
    def reverse_all(self):
        items = self.get_item(all = True)
        self.line_list.reverse()
        
        for item in items:
            index = self.get_index_from_item(item)
            line = self.line_list[index]
            line.toggle_cut_dir()
        
        self.selected_point.reset()
    
    
    def select_index(self, index):
        item = self.get_item_from_index(index)
        self.table.table.selection_set(item)
        self.table.table.see(item)      
    
    
    def SortLine(self):
        items = self.get_item()
        all_items = self.get_item(all = True)
        
        if not(len(items) == 1):
            return len(items)
        else:
            item_st = items[0]
            index_st = self.get_index_from_item(item_st)
            line_st = self.line_list[index_st]
            cut_dir_st = line_st.cut_dir
            norm_mn = np.inf
            if cut_dir_st == 'F':
                x0 = line_st.ed[0]
                y0 = line_st.ed[1]
            else:
                x0 = line_st.st[0]
                y0 = line_st.st[1]   

                
            x_array = np.array(line_st.x_raw)
            y_array = np.array(line_st.y_raw)                
            new_lines = [line_st]
            new_line_list = []
            x_array_list = []
            y_array_list = []
            
            i = 0
            while i < len(all_items) - 1:
                norm_mn = np.inf
                j = 0
                while j < len(all_items):
                    index = self.get_index_from_item(all_items[j])
                    line = self.line_list[index]

                    if (line in sum(new_line_list, [])) or (line in new_lines):
                        pass
                    
                    else:
                        norm_st = norm(x0, y0, line.st[0], line.st[1])
                        norm_ed = norm(x0, y0, line.ed[0], line.ed[1])
                        if min(norm_st, norm_ed) < norm_mn:
                            line_mn = line
                            norm_mn = min(norm_st, norm_ed)                      
                            if norm_st < norm_ed:
                                cut_dir = 'F'
                            else:
                                cut_dir = 'R'
                    j += 1
                    
                if cut_dir == 'F':
                    x0 = line_mn.ed[0]
                    y0 = line_mn.ed[1]
                if cut_dir == 'R':
                    x0 = line_mn.st[0]
                    y0 = line_mn.st[1]
                     
                line_mn.set_cut_dir(cut_dir)
                
                if norm_mn <= DIST_NEAR:
                    new_lines.append(line_mn)
                    x_array = np.concatenate([x_array, line_mn.x_raw], 0)
                    y_array = np.concatenate([y_array, line_mn.y_raw], 0)
                else:
                    new_line_list.append(new_lines)
                    x_array_list.append(x_array)
                    y_array_list.append(y_array)
                    new_lines = [line_mn]
                    x_array = np.array(line_mn.x_raw)
                    y_array = np.array(line_mn.y_raw)
                
                i += 1
                
            new_line_list.append(new_lines)
            x_array_list.append(x_array)
            y_array_list.append(y_array)    
             
            
            ccw_list = []
            i = 0
            while i < len(x_array_list):
                x_array = x_array_list[i]
                y_array = y_array_list[i]
                ccw = detectRotation(x_array, y_array)
                ccw_list.append(ccw)
                i += 1
            
            ccw_st = ccw_list[0]
            i = 0
            while i < len(ccw_list):
                ccw = ccw_list[i]
                new_lines = new_line_list[i]
                if not(ccw == ccw_st):
                    new_line_list[i] = new_lines[::-1]
                    
                for line in new_lines:
                    if not(ccw == ccw_st):
                        line.toggle_cut_dir()
                    if ccw_st == True:
                        line.set_offset_dir('O')
                    else:
                        line.set_offset_dir('I')
                i += 1
            
            self.line_list = sum(new_line_list,[])
            self.selected_point.reset()
            return 1


    def offset_origin(self, offset_ox, offset_oy):
        all_items = self.get_item(all=True)
        
        for item in all_items:
            index = self.get_index_from_item(item)
            line = self.line_list[index]
            line.reset_point(line.x_dxf, line.y_dxf, offset_ox, offset_oy)
        
        self.selected_point.reset()
    
    
    def remove_collision(self):
        all_items = self.get_item(all=True)
        self_collision_line_nums = []
        
        for item in all_items:
            index = self.get_index_from_item(item)
            line = self.line_list[index]
            detection = line.remove_self_collision()
            
            if detection == True:
                self_collision_line_nums.append(line.num)

        line_collision_nums = self.remove_line_collision()
        return self_collision_line_nums, line_collision_nums
    

###############   dxf_fileクラス   ここまで　　    　#########################################################################################
#######################################################################################################################################     

