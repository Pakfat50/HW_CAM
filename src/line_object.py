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
###############    line_objectクラス   ここから　　　#########################################################################################

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


class line_object:
    def __init__(self, x_points, y_points, num):
        self.x_dxf = np.array(x_points)
        self.y_dxf = np.array(y_points)
        self.x_raw = np.array(x_points)
        self.y_raw = np.array(y_points)
        self.st = np.array([x_points[0], y_points[0]])
        self.ed = np.array([x_points[-1], y_points[-1]])
        self.N = max(len(x_points), len(y_points))
        self.num = num
        self.offset_dist = 0
        self.offset_dir = "O"
        self.cut_dir = "F"
        self.cutspeed_work = 100
        self.cutspeed_mech = 100
        self.x = x_points
        self.y = y_points
        self.interp_mode = "cubic" #ver.2.2追加 "cubic":3d-spline, "linear":1d-line, ポリラインの指定用
        self.offset_ox = 0
        self.offset_oy = 0
        self.self_collision = False

        if len(x_points)<2:
            self.line_type = "point"
        if len(x_points)==2:
            self.line_type = "line"
        if len(x_points)>2:
            self.line_type = "spline"
       
        
    def reset_point(self, x_points, y_points, offset_ox, offset_oy):
        self.x_dxf = np.array(x_points)
        self.y_dxf = np.array(y_points)
        self.offset_ox = offset_ox
        self.offset_oy = offset_oy
        self.x_raw = np.array(x_points) + offset_ox
        self.y_raw = np.array(y_points) + offset_oy
        self.st = np.array([x_points[0], y_points[0]]) + offset_ox
        self.ed = np.array([x_points[-1], y_points[-1]]) + offset_oy
        self.N = max(len(x_points), len(y_points))
        self.x = np.array(x_points) + offset_ox
        self.y = np.array(y_points) + offset_oy
        self.interp_mode = "cubic"
        self.self_collision = False

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
            temp_x, temp_y = offset_line(temp_x, temp_y, self.offset_dist, self.cut_dir, self.interp_mode) 

        else:
            temp_x, temp_y = offset_line(temp_x, temp_y, -self.offset_dist, self.cut_dir, self.interp_mode) 
        
        self_col = True
        detection = False
        while self_col == True:
            temp_x, temp_y, self_col = remove_self_collision(temp_x, temp_y)
            if self_col == True:
                detection = True
    
        self.x = temp_x
        self.y = temp_y
        self.self_collision = detection
    
    def set_offset_dir(self, offset_dir):
        if offset_dir == 'O' or offset_dir == 'I':
            self.offset_dir = offset_dir
            self.update()
        
        
    def set_offset_dist(self, offset_dist):
        try:             
            self.offset_dist = float(offset_dist)
            self.update()
        except:
            traceback.print_exc()
            output_log(traceback.format_exc())
            pass
    
    
    def set_cut_dir(self, cut_dir):
        if cut_dir == 'F' or cut_dir == 'R':
            self.cut_dir = cut_dir
            self.update()
        
            
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

