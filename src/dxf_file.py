# -*- coding: utf-8 -*-
"""CAD図面(dxfファイル)に紐づくデータをまとめたライブラリ

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
    
class SuperTable:
    """dxfファイル内の線を管理するテーブルについてのクラスである
    
    tkinter.treeのインスタンスを格納する。

    tkinter.treeを初期化する方法がtreeの再生成しかないため、生成に必要な情報をメンバ変数として保存し、
    reset()関数がコールされた際にtableを削除、再生成する。
    
    Attributes:
        x_pos(int): テーブルの画面での配置位置 X座標
        y_pos(int): テーブルの画面での配置位置 Y座標
        root(tkinter.Frame): テーブル先のフレーム
        y_height(int): テーブル先の高さ（行）
        sync(bool): True:テーブルを他のテーブルと同期する, False:しない
        sync_update(bool): True:同期時に更新が必要, False:不要
        table(tkinter.tree): テーブルのインスタンス
        scrollbar(tkinter.Scrollbar): スクロールバーのインスタンス

    """
    def __init__(self, root, y_height, x, y):
        """SuperTableのコンストラクタ

        Args:
            root (tkinter.Frame): テーブル先のフレーム
            y_height (int): テーブル先の高さ（行）
            x (int): テーブルの画面での配置位置 X座標
            y (int): テーブルの画面での配置位置 Y座標
        """
        self.x_pos = x
        self.y_pos = y
        self.root = root
        self.y_height = y_height
        self.sync = False
        self.sync_update = False
        self.reset()
    
    
    def set_sync(self, sync):
        """テーブルの同期／非同期を設定する

        Args:
            sync (bool): True:テーブルを他のテーブルと同期する, False:しない
        """
        self.sync = sync
        self.sync_update = True
    
    
    def reset(self):
        """テーブルおよびスクロールバーを初期化する

        テーブルには、LineObjectの情報のうち、以下を表示する。

        +-----------------+--------------+
        |表示項目         |データソース  |
        +-----------------+--------------+
        |線番号           |num           |
        +-----------------+--------------+
        |オフセット距離   |offset_dist   |
        +-----------------+--------------+
        |タイプ           |line_type     |
        +-----------------+--------------+
        |カット速度       |cutspeed_work |
        +-----------------+--------------+

        """
        try:
            # 既存のtableオブジェクトを削除
            self.table.destroy()
            # 既存のスクロールバーオブジェクトの削除
            self.scrollbar.destroy()
        except:
            # 初回はtableオブジェクトがないので、例外を許容する
            pass
        # テーブルオブジェクトを新規作成
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
        
　　　　

class SelectedPoint:
    """図面上で選択された点の情報を格納する

    Attributes:
        x(float): 選択点のx座標
        y(float): 選択点のy座標 
        index(int): 選択点の線上でのインデックス  

    """


    def __init__(self, x, y, index):
        """SelectedPointのコンストラクタ

        Args:
            x (float): 選択点のx座標
            y (float): 選択点のy座標 
            index (int): 選択点の線上でのインデックス 
        """

        self.x = x
        self.y = y
        self.index = index
    

    def reset(self):
        """選択点を無効化する

        グラフで表示されないように、以下のように設定する。

        * x,y座標 -> numpy.nan
        * index -> None

        """
        self.x = np.nan
        self.y = np.nan
        self.index = None



class DxfFile:
    """dxfファイルに関連する情報として、LineObjectやSuperTableなどを格納する。

    Note:
        ox, oy, rx, ry, sitaの値は、元のdxfファイルに対しての値である。

    Note:
        line_listのインデックスと、tableのインデックスは同期させるように処理する。
        例えば、tableで線番号が[2,1,3]と線が並ぶとき、line_listの線も[2,1,3]と並べる。
    

    Attributes:
        ax(matplotlib.axes): 線をプロットするAxesオブジェクト
        canvas(matplotlib.backends.backend_tkagg.FigureCanvasTkAgg): グラフをtkinterに表示するためのオブジェクト(描画時に必要)
        table(SuperTable): dxfファイル内の線を管理するテーブル
        x_table(SuperTable): もう1つの断面のdxfファイル内の線を管理するテーブル（X-YであればU-V, U-VであればX-Y）
        name(str): 断面の名称(X-Y or U-V)
        line_list(list): dxfファイル内の線をLineObjectに変換したオブジェクトを格納するリスト
        selected_point(SelectedPoint): グラフ内で選択された点を管理するSelectedPointオブジェクト
        line_num_max(int): 線番号の最大値
        ox(float): グラフの原点のx座標
        oy(float): グラフの原点のy座標
        rx(float): グラフの回転中心のx座標
        ry(float): グラフの回転中心のy座標 
        sita(float): グラフの回転角度[rad]                



    """
    def __init__(self, ax, canvas, table, x_table, name):
        """DxfFileのコンストラクタ

        Args:
            ax(matplotlib.axes): 線をプロットするAxesオブジェクト
            canvas(matplotlib.backends.backend_tkagg.FigureCanvasTkAgg): グラフをtkinterに表示するためのオブジェクト(描画時に必要)
            table(SuperTable): dxfファイル内の線を管理するテーブル
            x_table(SuperTable): もう1つの断面のdxfファイル内の線を管理するテーブル（X-YであればU-V, U-VであればX-Y）
            name(str): 断面の名称(X-Y or U-V)

        """

        self.ax = ax
        self.canvas = canvas
        self.table = table
        self.x_table = x_table
        self.name = name
        self.line_list = []
        self.selected_point = SelectedPoint(np.nan, np.nan, None) # 選択点はないので、リセット時の値を設定
        self.line_num_max = 0
        self.ox = 0
        self.oy = 0
        self.rx = 0
        self.ry = 0
        self.sita = 0
    
    
    def load_file(self, filename, is_refine):
        """filenameで指定されたdxfファイルを読み込む

        AUTOSORT_WHEN_LOADFILE = Trueの場合、ロード時に自動で線を整列する

        Args:
            filename (str): 読み込むdxfファイルのパス
            is_refine (bool): True: スプライン点列をリファインして読み込む, False:リファインしない
        """
        
        # テーブル初期化
        self.table.reset()
        # ファイルのパス更新
        self.filename = filename
        # 線のリストを初期化
        self.line_list = []
        # dxfファイルをline_listへ読み込み
        self.reload(is_refine)
        # テーブルの選択イベントに、selectedをバインド
        self.table.table.bind("<<TreeviewSelect>>", self.selected)
        # 選択点を非選択に設定
        self.selected_point.reset()
        # 原点、回転中心、回転角を初期化
        self.ox = 0
        self.oy = 0
        self.rx = 0
        self.ry = 0
        self.sita = 0
        
        # テーブルの1番上のアイテムを選択
        items = self.table.table.get_children()
        self.table.table.selection_set(items[0])
        self.table.table.see(items[0])
        
        # ロード時に自動整列する場合
        if AUTOSORT_WHEN_LOADFILE == True:
            # 一番最初に読み込まれた線を始点として、自動整列
            self.sort_line()
            # 線の番号を、tableでの線の並び順に再設定する
            self.reset_line_num()

    
    def reset_line_num(self):
        """線の番号を、line_listのインデックス順に再設定する

        Note:
            line_listのインデックスとtableのインデックスは同期しているので、
            tableの並び順（昇順）に線の番号が振り直される。

        """
        i = 0
        # line_list内のすべての線に対して実行
        for line in self.line_list:
            # lineはLineObjectのインスタンス
            line.set_num(i)
            i += 1
        # tabelの表示を更新
        self.table_reload()
            

    def get_index(self, all = False):
        """table内のインデックスの番号を取得する

        Args:
            all (bool, optional): True: すべての行のインデックスを取得, False: 選択されている行のインデックスを取得. Defaults to False.

        Returns:
            list: 行のインデックスのリスト

        Note:
            all=Trueの場合、行の数をNとすると、[0,1,2, ... N]が返される。     

        Examples:
            tableが5行である場合に、
            tableの2,4行目(インデックス1, 3)が選択されている時
            
            >>> self.get_index()
            [1,3]

            >>> self.get_index(all=True)
            [0,1,2,3,4]

        """

        # all=Trueの場合、table内のすべてのアイテムを取得
        if all == True:
            items = self.table.table.get_children()
        # all=Falseの場合、table内の選択されたアイテムを取得
        else:
            items = self.table.table.selection()
        indexs = []
        # 選択されたアイテムが1つ以上の場合。0の場合は空リストを出力
        if not len(items) == 0:
            # 選択されたアイテムすべてに対して実行
            for item in items:
                # アイテムのインデックス(=行番号-1）を取得
                index = self.table.table.get_children().index(item)
                indexs.append(index)
        return indexs
    

    def get_item(self, all = False):
        """table内のアイテムのIDを取得する

        Note:
            アイテムのIDは、"I001"のような形式で、行追加時に自動的に割り当てられる。行固有の値。

        Args:
            all (bool, optional): True: すべてのアイテムのIDを取得, False: 選択されている行のアイテムのIDを取得。 Defaults to False.

        Returns:
            list: アイテムIDのリスト
        
        Examples:
            tableのアイテムIDが["I001", "I002", "I003"]の場合に、
            2行目と3行目が選択されている時
            
            >>> self.get_item()
            ["I002", "I003"]

            >>> self.get_item(all=True)
            ["I001", "I002", "I003"]

        """
        # all=Trueの場合、table内のすべてのアイテムを取得
        if all == True:
            items = self.table.table.get_children()
        # all=Falseの場合、table内の選択されたアイテムを取得
        else:
            items = self.table.table.selection()
        return items
    

    def get_item_from_index(self, indexs):
        """indexsで指定したインデックスのアイテムIDを出力する

        Args:
            indexs (list, int): 行のインデックスのリスト または 行番号

        Returns:
            list, str: indexsがリストの場合:アイテムIDのリスト, intの場合: アイテムIDの文字列
        
        Examples:
            tableのアイテムIDが["I001", "I002", "I003", "I004"]の場合

            >>> self.get_item_from_index([0,3])
            ["I001", "I004"]

            >>> self.get_item_from_index(2)
            "I002"        

        """
        # indexsがint型の場合
        if isinstance(indexs, int) == True:
            item = self.table.table.get_children()[indexs]
            return item
        # indexsがint型でない場合(リストの場合)
        else:
            items = []
            for index in indexs:
                item = self.table.table.get_children()[index]
                items.append(item)
            return items


    def get_index_from_item(self, items):
        """itemsで指定したアイテムIDを有する行のインデックスを取得する

        Args:
            items (list, str): アイテムIDのリスト または アイテムIDの文字列

        Returns:
            list, int: itemsがリストの場合:インデックスのリスト, strの場合: インデックスの番号

        Examples:
            tableのアイテムIDが["I001", "I002", "I003", "I004"]の場合

            >>> self.get_index_from_item(["I001", "I004"])
            [0, 3]

            >>> self.get_item_from_index("I003")
            2  

        """
        # itemsがstr型の場合
        if isinstance(items, str) == True:
            index = self.table.table.get_children().index(items)
            return index
        # itemsがstr型でない(リスト)場合
        else:
            indexs = []
            for item in items:
                index = self.table.table.get_children().index(item)
                indexs.append(index)
            return indexs


    def reload(self, is_refine):
        """filenameで指定されたdxfファイル上の線を読み込み、LineObjectに変換した上で、line_listへ格納する

        dxfファイルのうち、LINE, SPLINE, ARC, LWPOLYLINE のオブジェクトを抽出し、以下のLineObjectに変換する。

        +-----------+-----------+----------+------------+
        |読み込み順 |dxf object |LineObject             |
        |           +           +----------+------------+
        |           |           |line_type |interp_mode |
        +-----------+-----------+----------+------------+
        |1          |SPLINE     |spline    |cubic       |
        +-----------+-----------+----------+------------+
        |2          |ARC        |spline    |cubic       |
        +-----------+-----------+----------+------------+
        |3          |LWPOLYLINE |spline    |linear      |
        +-----------+-----------+----------+------------+
        |4          |LINE       |line      |None        |
        +-----------+-----------+----------+------------+

        LineObjectの線番号(num)は、読み込んだ順に付与する。同種のdxfオブジェクトでは線番号の付与順は任意である。
        (dxf objectのクエリで早く検索された順)

        線番号の最大値(=読み込んだ線の本数)は、line_num_maxに格納する。


        Args:
            is_refine (bool): True: スプライン点列をリファインして読み込む, False:リファインしない


        Note:
            ARCは、arc_to_splineにより円弧上の座標点列を計算し、splineに変換する。

        """

        # dxfファイルの読み込み
        dwg = ez.readfile(self.filename)
        modelspace = dwg.modelspace()

        # dxfファイルからのオブジェクトの取得
        line_segment_obj = modelspace.query('LINE')
        spline_obj = modelspace.query('SPLINE')
        arc_obj = modelspace.query('ARC')
        poly_obj = modelspace.query('LWPOLYLINE')
        
        # スプラインオブジェクトのLineObjectへの変換
        i = 0
        while i < len(spline_obj):
            spline = spline_obj[i]
            spline_data = np.array(spline.control_points)[:]
            line = LineObject(spline_data[:,0], spline_data[:,1], i, is_refine) 
            self.line_list.append(line)
            self.table.table.insert("", "end", values=(line.num, format(line.offset_dist, '.4f'),\
                                                       line.line_type, format(line.cutspeed_work,'.2f')))
            i += 1

        # 円弧オブジェクトのLineObjectへの変換
        i_arc = 0        
        while i_arc < len(arc_obj):
            arc = arc_obj[i_arc]
            # 円弧の情報から、スプライン座標点列の計算
            arc_data = arc_to_spline(arc)
            line = LineObject(arc_data[:,0], arc_data[:,1], i + i_arc, is_refine) 
            self.line_list.append(line)
            self.table.table.insert("", "end", values=(line.num, format(line.offset_dist, '.4f'), \
                                                       line.line_type, format(line.cutspeed_work,'.2f')))
            i_arc += 1        
        i = i + i_arc

        # ポリオブジェクトのLineObjectへの変換
        i_poly = 0
        while i_poly < len(poly_obj):
            poly = poly_obj[i_poly]
            poly_data = poly_to_spline(poly)
            line = LineObject(poly_data[:,0], poly_data[:,1], i + i_poly, is_refine) 
            line.interp_mode = "linear" #poly_lineであることを設定する
            self.line_list.append(line)
            self.table.table.insert("", "end", values=(line.num, format(line.offset_dist, '.4f'), \
                                                       line.line_type, format(line.cutspeed_work,'.2f')))
            i_poly += 1    
        i = i + i_poly

        # 線オブジェクトのLineObjectへの変換
        j = 0
        k = 0
        while j < len(line_segment_obj):
            line_segment = line_segment_obj[j]
            line_segment_data = [line_segment.dxf.start, line_segment.dxf.end]
            line_segment_data = np.array(line_segment_data)[:,0:2]
            
            # 長さがほとんどない線分は追加しない
            if norm(line_segment_data[0,0],line_segment_data[0,1],line_segment_data[1,0],line_segment_data[1,1]) > DIST_NEAR:
                line = LineObject(line_segment_data[:,0], line_segment_data[:,1], i+k, is_refine) 
                self.line_list.append(line)
                self.table.table.insert("", "end", values=(line.num, format(line.offset_dist, '.4f'), \
                                                           line.line_type, format(line.cutspeed_work,'.2f')))
                k += 1
            j += 1
        
        # 線番号の最大値(=読み込んだ線の本数)にて、line_num_maxを更新
        self.line_num_max = i+k-1
        

    def table_reload(self):
        """tableの情報を最新に更新する。

        1. テーブルのすべてのアイテムIDを取得する

        2. アイテムIDに対応する行のテーブルでのインデックスを取得する

        3. インデックスに対応するline_list内のLineObjectを取得する

        4. LineObjectの線番号、オフセット距離、線種、カット速度をテーブルに設定する

        """
        all_items = self.get_item(all=True)
        
        for item in all_items:
            index = self.get_index_from_item(item)
            line = self.line_list[index]
            self.table.table.item(item, values=(line.num, format(line.offset_dist, '.4f'), \
                                                line.line_type, format(line.cutspeed_work,'.2f')))

    
    def plot_vector(self, x0, y0, x1, y1, k,  col, alpha):
        """グラフ上にベクトルを表示する

        ベクトルの長さは、1に正規化した上で、kをかけることで長さをkとする。

        ただし、matplotlib側でベクトル長を自動設定としているので、効果なし。

        Args:
            x0 (float): 始点のx座標
            y0 (float): 始点のy座標
            x1 (float): 終点のx座標
            y1 (float): 終点のy座標
            k (float): プロットするベクトルの長さ
            col (str): ベクトルの色
            alpha (float): ベクトルの透明度

        """
        dist = norm(x0, y0, x1, y1)
        if dist > DIST_NEAR:
            u = (x1-x0)/dist * k
            v = (y1-y0)/dist * k
            self.ax.quiver(x0, y0, u, v ,color = col, alpha = alpha)
            
    
    
    def plot(self, keep_view=True):
        """グラフ上にline_list内の線をプロットする

        以下をプロットする。

        +----------------+----------+----------------+-------------------+-----------+-------+-------+
        |プロット対象    |選択状態  |データソース    |プロットデータ     |線種       |色     |透明度 |
        +----------------+----------+----------------+-------------------+-----------+-------+-------+
        |線              |選択中    |line_list       |x,y                |実線       |青     |1      |
        +                +----------+----------------+-------------------+-----------+-------+-------+
        |                |非選択    |line_list       |x,y                |実線       |青     |0.1    |
        +----------------+----------+----------------+-------------------+-----------+-------+-------+
        |線の向き        |選択中    |line_list       |x,y                |ベクトル   |青     |1      |
        +                +----------+----------------+-------------------+-----------+-------+-------+
        |                |非選択    |line_list       |x,y                |ベクトル   |青     |0.1    |
        +----------------+----------+----------------+-------------------+-----------+-------+-------+
        |オフセット方向  |選択中    |line_list       |x,y,x_raw,y_raw    |ベクトル   |黃     |1      |
        +                +----------+----------------+-------------------+-----------+-------+-------+
        |                |非選択    |line_list       |x,y,x_raw,y_raw    |ベクトル   |黃     |0.1    |
        +----------------+----------+----------------+-------------------+-----------+-------+-------+
        |選択点          |ー        |selected_point  |x,y                |点         |赤     |1      |
        +----------------+----------+----------------+-------------------+-----------+-------+-------+

        線の向きは、x,yの0番目→1番目の座標へのベクトルをプロットする。スプラインは、N-1番目→N番目のベクトルも併せてプロットする。

        オフセット方向は、x_raw, y_rawの0番目から、x,yの0番目へのベクトルをプロットする。

        プロット前にグラフの描画範囲をxlim,ylimに格納しておく。
        keep_view=Trueの場合は、プロット後に描画範囲をxlim,ylimに再適用することで、グラフの描画範囲を維持する。

        選択中の線はマーカーサイズを5、非選択の線はマーカーサイズを0とすることで、選択中の線のみ、分割点を設定できるようにする。
                
        Args:
            keep_view (bool, optional): True: グラフの描画範囲を変更しない, False:リセットする. Defaults to True.
        """

        # 現在の描画範囲を保存
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        # グラフをクリア
        self.ax.clear()

        # タイトル・アスペクト比を設定
        self.ax.set_title(self.name)
        self.ax.set_aspect('equal')

        # tableにて選択中の線のインデックスを取得
        indexs = self.get_index()
        
        # line_listのすべての線を再描画
        i = 0
        while i < len(self.line_list):
            line = self.line_list[i]

            # 線種による色の選択用
            # 現verでは無効化（すべて青）
            if line.line_type == "line":
                col = "b"
            else:
                col = "b"
                
            # 選択中/非選択で描画のパラメータを切り替える。
            # 選択中の線の場合
            if i in indexs:
                # 透明度を1
                alpha_line = 1
                alpha_vect = 1
                alpha_offset = 1
                # 選択有効となるようにマーカーサイズを5に設定
                pick = 5 
            # 非選択の線の場合
            else:
                # 透明度を0.1
                alpha_line = 0.1
                alpha_vect = 0.1
                alpha_offset = 0
                # 選択無効となるようにマーカーサイズを0に設定
                pick = 0 
            
            # 線をプロット
            self.ax.plot(line.x, line.y, color = col, alpha = alpha_line, marker='o', markersize=2, picker = pick)
            
            # 始点におけるカット方向のベクトルをプロット
            X,Y = line.x[0], line.y[0]
            U,V = line.x[1], line.y[1]
            self.plot_vector(line.x[0], line.y[0], line.x[1], line.y[1], 1, col, alpha_vect)
            
            # スプラインの場合、終点におけるカット方向のベクトルもプロット
            if not(line.line_type == "line"):
                self.plot_vector(line.x[-1], line.y[-1], line.x[-2], line.y[-2], -1, col, alpha_vect)

            # オフセット方向をプロット
            X,Y = line.x_raw[0], line.y_raw[0]
            U,V = line.x[0], line.y[0]
            self.plot_vector(line.x[0], line.y[0], line.x_raw[0], line.y_raw[0], -1, 'y', alpha_offset)

            i += 1
        
        # 選択点をプロット
        self.ax.plot(self.selected_point.x, self.selected_point.y, "ro")
        
        if keep_view == True:
            self.ax.set_xlim(xlim)
            self.ax.set_ylim(ylim)

        # 画面に描画
        self.canvas.draw()
        
    
    def get_selected_point(self, event):
        """matplotlibのpick_eventにバインドされるメソッド

        選択点の座標をeventから取得し、インデックス、座標を更新する。

        Args:
            event (matplotlib.backend_bases.PickEvent): matplotlibのpick_event

        Note:
            https://matplotlib.org/stable/users/explain/figure/event_handling.html

            https://matplotlib.org/stable/api/backend_bases_api.html#matplotlib.backend_bases.PickEvent

        """
        # pick_eventにて選択された線を取得する
        line = event.artist

        # 選択された線において、選択された点の座標とインデックスを取得する
        x, y = line.get_data() # 選択点の座
        index = event.ind[0] # 選択点のインデックス

        # 選択点を更新する
        self.selected_point = SelectedPoint(x[index], y[index], index)

        # 選択点をプロットするため、グラフを更新
        self.plot()
      
    
    def selected(self, event):
        """tkinterのtableの<<TreeviewSelect>>イベントにバインドされるメソッド

        tableのデータを選択した際に、グラフの再描画を行う。

        XY-UV同期中の場合は、相手のテーブル(x_table)に選択イベントを発生させる。
        この処理フローは下図による。

        .. uml::

            @startuml
            actor User

            User -> table : table内のi行目選択
            activate table
            table -> table : 1度のみグラフ更新

            alt XY-UV同期中
                table -> x_table : x_table内のi行目選択
                deactivate table
                activate x_table
                x_table -> x_table : 1度のみグラフ更新
                x_table -> table : table内のi行目選択
                deactivate x_table
                activate table
                table -> table : グラフ表示判定フラグ初期化
            end
            table -> User : 更新済みのグラフ表示

            @enduml

        Args:
            event (Event): Python標準のイベントクラス。本メソッドでは使用しない

        Note:
            https://docs.python.org/ja/3.13/library/tkinter.ttk.html

            https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/event-handlers.html

        """

        # 選択された行のアイテムを取得
        items = self.get_item()

        # グラフが更新されるので、選択点をリセット
        self.selected_point.reset()

        # 選択された行が0の場合、エラーとなるため防御
        if not len(items) == 0:
            # XY-UV同期中の場合
            if self.table.sync == True:
                # 1度目のグラフ描画かを判定フラグ(sync_update)を用いて判定
                if self.table.sync_update == True:
                    self.table.sync_update = False 
                    # 自身のグラフ描画
                    self.plot()
                
                    try:
                        # 相手テーブルの同じ行のインデックスを取得
                        x_selected_items = []
                        for item in items:
                            index = self.get_index_from_item(item)
                            x_item = self.x_table.table.get_children()[index]
                            x_selected_items.append(x_item)
                        # 相手テーブルに選択イベントを発生
                        self.x_table.table.selection_set(x_selected_items)
                        # 相手テーブルの同じ行を選択表示
                        self.x_table.table.see(x_selected_items)
                    except:
                        # XY-UV画面同期中に線数が異なると選択できないため、例外を許容する
                        self.table.sync_update = True
                        self.x_table.sync_update = True
                        # traceback.print_exc()
                        pass

                # 2度めの選択イベント(相手テーブルからの選択イベントの戻り)
                else:
                    # 自テーブルと相手テーブルのフラグを初期化して終了
                    self.table.sync_update = True
                    self.x_table.sync_update = True

            # XY-UV非同期中の場合
            else:
                # 自身のみグラフ描画
                self.plot()
    
    
    def update(self, keep_view=True):
        """グラフとtableの両方を更新する

        table_reloadとplotをまとめて実行するだけ。

        Args:
            keep_view (bool, optional): True: グラフの描画範囲を変更しない, False:リセットする. Defaults to True.
        """
        self.table_reload()
        self.plot(keep_view)        
    
                
    def set_offset_dist(self, offset_dist):
        """line_list内のLineObjectにオフセット距離を設定する

        Args:
            offset_dist (float): オフセット距離
        """

        # table内の全アイテムIDを取得。line_listの要素全てに対して操作しても同じ
        all_items = self.get_item(all=True)

        # すべての線にオフセット距離を設定
        for item in all_items:
            index = self.get_index_from_item(item)
            line = self.line_list[index]
            line.set_offset_dist(offset_dist)

        # グラフが更新されるので、選択点をリセット
        self.selected_point.reset()

    
    def remove_self_collision(self):
        """オフセットにより生じた自己交差を修正する

        table内のすべての線の自己交差を判定し、自己交差していれば修正する。

        自己交差が検出された線番号をリストとして出力する。

        Returns:
            list: 自己交差が検出された線番号のリスト
        """
        
        # table内のすべての線のアイテムIDを取得
        all_items = self.get_item(all=True)

        # 自己交差している線番号のリスト
        self_collision_line_nums = []
        
        # すべての線に自己交差判定&修正を実施
        for item in all_items:
            index = self.get_index_from_item(item)
            line = self.line_list[index]
            # 自己交差判定&修正
            detection = line.remove_self_collision()
            
            # 自己交差が検出された場合、線番号をリストに格納
            if detection == True:
                self_collision_line_nums.append(line.num)

        return self_collision_line_nums
        

    
    def remove_line_collision(self):
        """オフセットにより生じた線同時の端点の交差を修正する

        line_list内のi番目とi+1番目(i=0...N-1)に対し、remove_collisionにより交差を判定する。

        交差している場合、i番目とi+1番目の線の座標点列を、交差を修正した座標点列に置き換える。

        更に、交差が検出された線のペアをリストに格納し、出力する。

        Returns:
            list: 交差が検出された線同士の線番号（ペア）のリスト

        Note:
            オフセットが0の状態で、i番目の線の終点と、i+1番目の線の始点が一致している必要がある。
            
            自動整列後に実行すること。

        """

        # table内の全アイテムIDを取得。line_listの要素全てに対して操作しても同じ
        all_items = self.get_item(all=True)

        # 交差が検出された線同士の線番号（ペア）のリストを初期化
        line_nums = []

        # i番目とi+1番目の線のペアに対して、交差を判定する
        i = 0
        while i < len(all_items)-1:
            index1 = self.get_index_from_item(all_items[i]) # i番目のインデックス
            index2 = self.get_index_from_item(all_items[i+1]) # i+1番目のインデックス
            line1 = self.line_list[index1] # i番目の線
            line2 = self.line_list[index2] # i+1番目の線
            
            # 交差検出
            x1 = line1.x
            y1 = line1.y
            x2 = line2.x
            y2 = line2.y
            x1, y1, x2, y2, detection = remove_collision(x1, y1, x2, y2)

            # 交差が検出された場合
            if detection == True:
                # 交差除去後のx,y座標でi番目とi+1番目の座標点列を置換
                line1.x = x1
                line1.y = y1
                line2.x = x2
                line2.y = y2
                # 交差が検出された線のペアをリストに格納
                line_nums.append([line1.num, line2.num])
            i += 1

        # グラフが更新されるので、選択点をリセット
        self.selected_point.reset()

        return line_nums


    def change_cut_dir(self):
        """tableで選択された線の方向を入れ替える
        """

        # tableで選択されたアイテムIDを取得
        items = self.get_item()

        # tableで選択されたすべての行に対して実行
        for item in items:
            # アイテムIDに対応するLineObjectを取得
            index = self.get_index_from_item(item)
            line = self.line_list[index]
            # LineObjectの向きを反転
            line.toggle_cut_dir()

        self.selected_point.reset()


    def merge_selected_line(self):
        """選択された線を結合する

        結合は、選択された線の端点の距離がLINE_MARGE_NORM_MN未満の場合に実施する。

        端点が始点か終点かを判定し、始点→終点　の順になるように、必要に応じて線の向きを入れ替えて結合する。

        結合された方のLineObjectは削除されるので、どの線番号が結合されたかの情報が失われる。

        よって、結合する前に、どの線番号が選択されていたかを配列にて出力する。

        また、結合結果を配列にて出力する。

        Note:
            選択された線が複数の場合、tableにおけるインデックスの小さい順（上から下）に結合する。


        Returns:
            list: 結合前に選択されていた線番号のリスト
            list: 結合結果のリスト(True: 結合成功. False:失敗)
        """

        # 結合前に選択されていた線番号のリスト
        line_nums = []
        # 結合結果のリスト
        results = []
        
        # tableで選択されたアイテムIDを取得
        items = self.get_item()

        # 結合前に選択されていた線番号をリストに格納
        for item in items:
            index = self.get_index_from_item(item)
            line = self.line_list[index]
            line_nums.append(line.num)
            
        # 結合するには最低2本以上の線が必要
        if len(items) >= 2:
            # 1本目の線に次の線を結合していく。1本目の線の結合結果はTrueとしておく。
            results.append(True)
            
            # 選択したすべての線に対して結合操作を実施
            i = 1
            while i < len(items):
                # parentにchildを結合
                parent_index = self.get_index_from_item(items[0])
                child_index = self.get_index_from_item(items[i])
                parent_line = self.line_list[parent_index]
                child_line = self.line_list[child_index]
                
                # 始点と終点の座標をローカル変数に格納
                x_p_st = parent_line.st[0]
                y_p_st = parent_line.st[1]
                x_c_st = child_line.st[0]
                y_c_st = child_line.st[1]
        
                x_p_ed = parent_line.ed[0]
                y_p_ed = parent_line.ed[1]
                x_c_ed = child_line.ed[0]
                y_c_ed = child_line.ed[1]
                
                # 向きの入れ替えがしやすいように、numpy.arrayをリストに変換
                x_p = parent_line.x_raw.tolist()
                y_p = parent_line.y_raw.tolist()
                x_c = child_line.x_raw.tolist()
                y_c = child_line.y_raw.tolist()
            
                # 結合後の座標点列
                new_x = []
                new_y = []
                
                # 親ラインの終点→子ラインの始点　の場合（入れ替え不要）
                if norm(x_p_ed, y_p_ed, x_c_st, y_c_st) < LINE_MARGE_NORM_MN:
                    # 親ラインに子ラインを接続
                    new_x.extend(x_p)
                    new_y.extend(y_p)
                    new_x.extend(x_c)
                    new_y.extend(y_c)
                    result = True # 結合成功
                # 親ラインの終点→子ラインの終点　の場合（子ラインの向きの反転が必要）
                elif norm(x_p_ed, y_p_ed, x_c_ed, y_c_ed) < LINE_MARGE_NORM_MN:
                    # 子ラインを反転させたのち、親ラインに子ラインを接続
                    x_c.reverse()
                    y_c.reverse()
                    new_x.extend(x_p)
                    new_y.extend(y_p)
                    new_x.extend(x_c)
                    new_y.extend(y_c)
                    result = True # 結合成功
                # 親ラインの始点→子ラインの終点　の場合（子ライン→親ラインの順に結合）
                elif norm(x_p_st, y_p_st, x_c_ed, y_c_ed) < LINE_MARGE_NORM_MN:
                    # 子ラインに親ラインを接続
                    new_x.extend(x_c)
                    new_y.extend(y_c)
                    new_x.extend(x_p)
                    new_y.extend(y_p)
                    result = True # 結合成功
                # 親ラインの始点→子ラインの始点　の場合（子ラインの向きを入れ替え、子ライン→親ラインの順に結合）
                elif norm(x_p_st, y_p_st, x_c_st, y_c_st) < LINE_MARGE_NORM_MN:
                    # 子ラインを反転させたのち、子ラインに親ラインに接続
                    x_c.reverse()
                    y_c.reverse()
                    new_x.extend(x_c)
                    new_y.extend(y_c)
                    new_x.extend(x_p)
                    new_y.extend(y_p)
                    result = True # 結合成功
                # いずれの端点も近接していない場合
                else:
                    # 端点が隣接していない線同士であるので、結合すべきではない。
                    result = False # 結合失敗
                
                # 結合成功の場合
                if result == True:
                    # 親ラインの座標点列を、子ラインを結合したものに更新
                    parent_line.reset_point(new_x, new_y)
                    # 子ラインを削除
                    self.delete_line(items[i])
                
                # 結合結果を配列に格納
                results.append(result)
                i += 1
                
            # グラフが更新されるので、選択点を解除
            self.selected_point.reset()
        
        # 線が1本しか選択されていない場合
        elif len(items) == 1:
            results = [True]
        # 線が0本しか選択されていない場合
        else:
            results = []
            
        return results, line_nums
    
    
    def separate_line(self):
        """線を選択点で分割する

        以下の条件がすべて成立した場合、線を分割する。

        * tableにて線が1本だけ選択されている。

        * 選択点が選択されている。

        * 選択点が端点でない。(分割後の座標点列長の長さが2以上となる)

        分割結果を判定するための情報として、成否に加えて線番号のリストと分割点のインデックスも出力する。
        
        Returns:
            bool: True:分割成功, False:失敗
            list: 選択されている線番号のリスト
            int: 分割点のインデックス

        Note:
            選択されている線番号のリストには、分割が成功した場合、新しく生成されたLineObjectの線番号も格納する。

        """

        # 結果結果
        result = False
        # tableにて選択されている線番号のリスト
        line_nums = []

        # tableで選択されたアイテムIDを取得
        items = self.get_item()

        # 分割前に選択されていた線番号をリストに格納
        for item in items:
            index = self.get_index_from_item(item)
            line = self.line_list[index]
            line_nums.append(line.num)

        # 分割点のインデックス
        point_index = self.selected_point.index
        
        # tableにて線が1本のみ選択されている場合に分割を実施
        if (len(items) == 1):

            # 分割前の線
            index_org = self.get_index_from_item(items)[0]
            line_org = self.line_list[index_org]
            # 分割前の座標点列
            x_org = line_org.x_raw.tolist()
            y_org = line_org.y_raw.tolist()

            # 選択点が選択されており、かつ端点でない場合に分割を実施
            if (not(point_index == None)) and (not(point_index == 0)) \
                and (not(point_index == len(x_org)-1)):
    
                # 分割点のインデックスで線を分割し、分割後の座標点列を取得
                x1 = x_org[:point_index+1] # 前側
                y1 = y_org[:point_index+1] # 前側
                x2 = x_org[point_index:] # 後側
                y2 = y_org[point_index:] # 後側
                
                # 過去に分割済みの場合、同じ点が分割回数だけ生成されてしまうので、重複点を削除
                x1, y1 = remove_same_point(x1, y1)
                x2, y2 = remove_same_point(x2, y2)
                
                # 分割後のLineObjectは、元のLineObjectのプロパティを引き継ぐべきなのでオブジェクトをコピーする
                line1 = copy.deepcopy(line_org)
                line2 = copy.deepcopy(line_org)
                
                # コピーしたLineObjectの座標点列を、分割後のものに更新
                line1.reset_point(x1, y1)
                line2.reset_point(x2, y2)
                
                # 分割により追加されたLineObjectの線番号を計算
                # 最大の線番号の次の番号を付与する
                num_new = self.line_num_max + 1
                # 最大の線番号を更新
                self.line_num_max = num_new
                # 選択された線のリストに、追加したLineObjectの線番号を追加  
                line_nums.append(num_new)
                
                # 元の線を、分割した線の前側に置き換え
                self.line_list[index_org] = line1
                # 後側の線を追加
                line2.num = num_new
                self.add_line(items, line2)
                
                # グラフが更新されるので、選択点を解除
                self.selected_point.reset()

                #分割成功
                result = True

        return result, line_nums, point_index

    
    def delete_selected_line(self):
        """選択した線をtableおよびline_listから削除する。
        """

        # tableで選択されたアイテムIDを取得
        items = self.get_item()

        # tableにて選択されている線をすべて削除
        for item in items:
            self.delete_line(item)
        
        #グラフが更新されるので、選択点を解除
        self.selected_point.reset()
        
    
    def delete_line(self, item):
        """アイテムIDで指定された線をtableおよびline_listから削除する。

        Args:
            item (str): tableの行のアイテムID

        Note:
            同様の処理がdelete_selected_lineとmerge_lineで必要なので、別のメソッドとして実装。

        """

        # tableのアイテムID二対応するインデックスを取得
        index = self.get_index_from_item(item)
        # インデックスに該当するLineObjectをline_listから削除
        self.line_list.pop(index)
        # インデックスに該当する行をtableから削除
        self.table.table.delete(item)
    

    def add_line(self, item, line):
        """線をアイテムIDの次の位置に追加する。

        Args:
            item (str): tableの行のアイテムID
            line (LineObject): 追加する線
        """

        # 線を追加するインデックスを計算する
        # アイテムIDのインデックスを取得
        index = self.get_index_from_item(item)[0]
        # アイテムIDの次のインデックスを取得
        insert_index = index+1
        
        # line_listの指定のインデックスの位置にlineを挿入
        self.line_list.insert(insert_index, line)
        # tableの指定のインデックスの位置に行を挿入&lineの情報を表示
        self.table.table.insert("",  insert_index, values=(line.num, format(line.offset_dist, '.4f'),\
                                                   line.line_type, format(line.cutspeed_work,'.2f')))
    

    def reverse_all(self):
        """line_list内のLineObjectの座標点列と、line_listを反転する

        """

        # table内のすべての行のアイテムIDを取得
        items = self.get_item(all = True)

        # line_listを反転
        self.line_list.reverse()
        
        # すべての線の座標点列の向きを反転する
        for item in items:
            index = self.get_index_from_item(item)
            line = self.line_list[index]
            line.toggle_cut_dir()
        
        # グラフが更新されるので、選択点を解除
        self.selected_point.reset()
    
    
    def select_index(self, index):
        """インデックスで指定されたtableの行を選択する

        Args:
            index (int): tableの行のインデックス
        """

        # インデックス二対応するtableのアイテムIDを取得
        item = self.get_item_from_index(index)
        # アイテムIDの行を選択 -> <<TreeviewSelect>>イベント発生により、selectedがコールされる
        self.table.table.selection_set(item)
        # アイテムIDの行を表示
        self.table.table.see(item)      
    
    
    def sort_line(self):
        """選択されている線を起点に、残りの線を並び替える。並び替え後、座標点列の向きを判定し、線に設定する。

        線の並び替えは、以下の手順で実施する。

            1. 選択されている線の終点から最も近い位置にあるライン端を検索する。

            2. 1.のライン端を有するラインを、2番目に配置する。1.のライン端がラインの終端である場合，向きを入れ替える。

            3. 1.のライン端の逆端から最も近い位置にあるライン端を検索する。

            4. 3.のライン端を有するラインを、3番目に配置する。3.のライン端がラインの終端である場合，向きを入れ替える。

            5. 3.のライン端から最も近い位置にあるライン端を検索する。

            6. 3～5を、テーブルに表示されている全てのラインに対して実施する。
                
        Note:
            CAD図面に複数の閉曲線が含まれる場合、選択した線の向きと同じ向きにすべての閉曲線を並び替える。

        Note:
            閉曲線かどうかの判定は、端点間の距離がDIST_NEAR以下かで判定する。

        Returns:
            int: 選択されている線の数
        """

        # tableで選択されている行のアイテムIDを取得
        items = self.get_item()
        # tableのすべての行のアイテムIDを取得
        all_items = self.get_item(all = True)
        
        # 行の選択されている数が1つ以外の場合は終了
        if not(len(items) == 1):
            return len(items)
        # 行の選択されている数が1つの場合
        else:
            # ソートの開始点を、選択した線に設定
            item_st = items[0]
            index_st = self.get_index_from_item(item_st)
            line_st = self.line_list[index_st]

            norm_mn = np.inf
            x0 = line_st.ed[0]
            y0 = line_st.ed[1]

            x_array = np.array(line_st.x_raw)
            y_array = np.array(line_st.y_raw)                
            new_lines = [line_st]
            new_line_list = []
            x_array_list = []
            y_array_list = []
            
            # ソートを実行
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
                                toggle = False
                            else:
                                toggle = True
                    j += 1
                
                if toggle == True:
                    line_mn.toggle_cut_dir()
                x0 = line_mn.ed[0]
                y0 = line_mn.ed[1]
                
                # 同じ閉曲線かどうかを判定
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
             
            # 閉曲線の向きを判定
            ccw_list = []
            i = 0
            while i < len(x_array_list):
                x_array = x_array_list[i]
                y_array = y_array_list[i]
                ccw = detect_rotation(x_array, y_array)
                ccw_list.append(ccw)
                i += 1
            
            # 閉曲線が複数ある場合、残りの閉曲線の向きを最初の線の向きに合わせる
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
                    line.set_ccw(ccw_st)
                i += 1
            
            self.line_list = sum(new_line_list,[])

            # グラフが更新されるので、選択点を解除
            self.selected_point.reset()
            return 1


    def offset_origin(self, offset_ox, offset_oy):
        """指定の座標に原点をオフセットする。

        Args:
            offset_ox (float): 原点のx座標
            offset_oy (float): 原点のy座標
        """
        # 現在の原点の座標からの差分を計算する
        dx = offset_ox - self.ox
        dy = offset_oy - self.oy
        # 原点の座標を更新する
        self.ox = offset_ox
        self.oy = offset_oy
        # 回転中心の座標をオフセットする
        self.rx = self.rx + dx
        self.ry = self.ry + dy
        
        # table内のすべての行のアイテムIDを取得
        all_items = self.get_item(all=True)
        # table内のすべての線を、現在の原点の座標からの差分だけ移動する
        for item in all_items:
            index = self.get_index_from_item(item)
            line = self.line_list[index]
            line.move_origin(dx, dy)
        
        # グラフが更新されるので、選択点を解除する
        self.selected_point.reset()
    
    
    def rotate(self, sita, rx, ry):
        """指定の座標を中心に、指定の角度だけ線を回転する

        Args:
            sita (float): 回転角度[rad]
            rx (float): 回転中心x座標
            ry (float): 回転中心y座標
        """
        
        # 回転中心の座標を更新
        self.rx = rx
        self.ry = ry
        # 現在の回転角度からの差分を計算する
        d_sita = sita - self.sita
        # 回転角度を更新
        self.sita = sita
        
        # table内のすべての行のアイテムIDを取得
        all_items = self.get_item(all=True)
        # table内のすべての線を、現在の回転角度からの差分だけ回転する
        for item in all_items:
            index = self.get_index_from_item(item)
            line = self.line_list[index]
            line.rotate(d_sita, rx, ry)
        
        # グラフが更新されるので、選択点を解除する
        self.selected_point.reset()        
    
    
    def get_cg(self):
        """すべての線の重心の座標を計算する

        重心は、すべての点の座標の平均値で計算する。
        
        Returns:
            float: 重心のx座標
            float: 重心のy座標
        """
        
        # 平均値計算用にx,y座標を格納する配列を用意
        x = np.array([])
        y = np.array([])
        
        # table内のすべての行のアイテムIDを取得
        all_items = self.get_item(all=True)
        # table内のすべての線の座標を配列に格納
        for item in all_items:
            index = self.get_index_from_item(item)
            line = self.line_list[index]
            x = np.concatenate([x, line.x_raw], 0)
            y = np.concatenate([y, line.y_raw], 0)
        
        # 格納したx,y座標の平均値を計算
        # 配列長がゼロ出ない場合
        if not(len(x) == 0):
            cg_x = np.mean(x)
            cg_y = np.mean(y)
        # 配列長がゼロの場合
        else:
            cg_x = None
            cg_y = None
            
        return cg_x, cg_y
    

