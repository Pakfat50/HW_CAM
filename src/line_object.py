# -*- coding: utf-8 -*-
"""
Created on Mon Aug 11 15:40:37 2025

@author: hirar
"""

# 外部ライブラリ
import numpy as np
from matplotlib import pyplot as plt
from scipy import interpolate as intp
from scipy.integrate import quad
import traceback

# 内部ライブラリ
from cam_generic_lib import *
from error_log import *
from cam_global import *

#######################################################################################################################################
###############    LineObjectクラス   ここから　　　#########################################################################################

#【説明】
#　ライン，スプラインを格納するクラスである．
#
#【親クラス】
#　なし
#
#【メンバ変数】
#   変数名          型              説明
#   x_dxf           list            dxfファイルから読み込んだx座標点列　変更されない
#   y_dxf           list            dxfファイルから読み込んだy座標点列　変更されない
#   x_raw           list            x座標点列の初期値　原点オフセットを除き、変更されない
#   y_raw           list            y座標点列の初期値　原点オフセットを除き、変更されない
#   st              list            x_raw, y_rawの 始点 
#   ed              list            x_raw, y_rawの 終点 
#   N               int             座標点列の個数
#   num             int             ラインの番号
#   offset_dist     float           オフセット距離
#   offset_dir      char            オフセット方向["O"/ "I"]
#   cut_dir         char            x, y配列の方向["F"/ "R"]（x_raw，y_rawに対して順方向が"F"，逆方向が"R"）
#   cutspeed_work   float           ワーク面（XY or UV断面）でのカット速度
#   cutspeed_mech   float           マシン駆動面でのカット速度
#   x               list            オフセット，配列方向を適用したあとの x座標点列
#   y               list            オフセット，配列方向を適用したあとの y座標点列
#   offset_ox       float           原点のx方向オフセット量
#   offset_oy       float           原点のy方向オフセット量
#
#【実装メソッド】
#   __init__(list x_points, list y_points, int num)
#   【引数】 x_points, y_points, num
#   【戻り値】　なし
#   【機能】 初期化処理を実行する．x座標点列x_points, y座標点列y_points　を，x_raw，y_rawおよびx, yに代入する．ライン名をnumに設定する．
#
#   reset_point(list x_points, list y_points, float offset_ox, float offset_oy)
#   【引数】 x_points, y_points, offset_ox, offset_oy
#   【戻り値】　なし
#   【機能】 x_dxf、y_dxf座標点列を更新し、それら以外の座標点列をoffset_ox、offset_oyで指定される量だけオフセットする
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
#   set_cutspeed(float cutspeed_work, float cutspeed_mech)
#   【引数】 cutspeed_work, cutspeed_mech
#   【戻り値】 なし
#   【機能】 メンバ変数であるcutspeed_work, cutspeed_mechを入力値に設定する．
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


class LineObject:
    def __init__(self, x_points, y_points, num, is_refine, interp_mode = "cubic"):
        self.interp_mode = interp_mode  #ver.2.2追加 "cubic":3d-spline, "linear":1d-line, ポリラインの指定用
        if len(x_points)<2:
            self.line_type = "point"
        elif len(x_points)==2:
            self.line_type = "line"
        else: #len(x_points)>2
            self.line_type = "spline"
            if (is_refine == True) and (self.interp_mode == "cubic"):
                length = get_spline_length(x_points, y_points)
                N_refine = int(length/DIST_REFINE_SPLINE)
                if N_refine < N_REFINE_SPLINE_MIN:
                    N_refine = N_REFINE_SPLINE_MIN
                x_points, y_points = refine_spline_curvature(x_points, y_points, N_refine)              
                
        self.x_raw = np.array(x_points)
        self.y_raw = np.array(y_points)
        self.st = np.array([x_points[0], y_points[0]])
        self.ed = np.array([x_points[-1], y_points[-1]])
        self.num = num
        self.offset_dist = 0
        self.ccw = True
        self.cutspeed_work = CUTSPEED_DEFAULT
        self.cutspeed_mech = CUTSPEED_DEFAULT
        self.x = np.array(x_points)
        self.y = np.array(y_points)

        
    def reset_point(self, x_points, y_points):
        if len(x_points)<2:
            self.line_type = "point"
        elif len(x_points)==2:
            self.line_type = "line"
        else: # len(x_points)>2
            self.line_type = "spline"
                
        self.x_raw = np.array(x_points)
        self.y_raw = np.array(y_points)
        self.st = np.array([x_points[0], y_points[0]])
        self.ed = np.array([x_points[-1], y_points[-1]])
        self.set_offset_dist(self.offset_dist)
        
    
    def move_origin(self, dx, dy):
        self.x_raw = self.x_raw + dx
        self.y_raw = self.y_raw + dy
        self.x = self.x + dx
        self.y = self.y + dy
        self.st[0] = self.st[0] + dx
        self.ed[0] = self.ed[0] + dx
        self.st[1] = self.st[1] + dy
        self.ed[1] = self.ed[1] + dy
        
        
    def rotate(self, d_sita, rx, ry):
        self.x_raw, self.y_raw = rotate(self.x_raw, self.y_raw, d_sita, rx, ry)
        self.x, self.y = rotate(self.x, self.y, d_sita, rx, ry)
        self.st[0], self.st[1] = rotate(self.st[0], self.st[1], d_sita, rx, ry)
        self.ed[0], self.ed[1] = rotate(self.ed[0], self.ed[1], d_sita, rx, ry)
    
    
    def set_ccw(self, ccw):
        if not(self.ccw == ccw):
            self.ccw = ccw
            self.set_offset_dist(self.offset_dist)
        
        
    def set_offset_dist(self, offset_dist):
        try:
            self.offset_dist = float(offset_dist)
            if self.ccw == True:
                dist = -self.offset_dist
            else:
                dist = self.offset_dist
                
            self.x, self.y = offset_line(self.x_raw, self.y_raw, dist, self.interp_mode) 
            
        except:
            traceback.print_exc()
            output_log(traceback.format_exc())
            pass
    
    def remove_self_collision(self):
        self_col = True
        detection = False
        temp_x = self.x
        temp_y = self.y
        
        while self_col == True:
            temp_x, temp_y, self_col = remove_self_collision(temp_x, temp_y)
            if self_col == True:
                detection = True
    
        self.x = temp_x
        self.y = temp_y
        return detection
        
    
        
    def set_cutspeed(self, cutspeed_work, cutspeed_mech):
        self.cutspeed_work = cutspeed_work
        self.cutspeed_mech = cutspeed_mech
        
        
    def set_num(self, num):
        try:
            self.num = int(num)
        except:
            traceback.print_exc()
            output_log(traceback.format_exc())
            pass

    def toggle_cut_dir(self):         
        self.x_raw = self.x_raw[::-1]
        self.y_raw = self.y_raw[::-1]
        self.x = self.x[::-1]
        self.y = self.y[::-1]
        self.st, self.ed = self.ed, self.st
        if self.ccw == True:
            ccw = False
        else:
            ccw = True
        self.ccw = ccw
        
        
    def calc_length_array(self, mode = "offset"):
        
        length_array = [0]
        
        if mode == "raw":
            x = self.x_raw
            y = self.y_raw
        
        else:
            x = self.x
            y = self.y           
            
        if self.line_type == "point":
            length_array = [0]
        
        if self.line_type == "line":
            dl = np.sqrt((x[0]-x[1])**2 + (y[0]-y[1])**2)
            length_array.append(dl)
        
        if self.line_type == "spline":
            length_array = get_spline_length_array(x, y)
            
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
            length = get_spline_length(x, y)
        
        return length

###############    LineObjectクラス   ここまで　　　#########################################################################################
#######################################################################################################################################

