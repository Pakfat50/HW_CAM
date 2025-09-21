# -*- coding: utf-8 -*-
"""
Created on Mon Aug 11 15:37:04 2025

@author: hirar
"""
# 外部ライブラリ
import numpy as np
from matplotlib import pyplot as plt
from scipy import interpolate as intp
from scipy.integrate import quad
import os.path as op
import os
import sys
import traceback

# 内部ライブラリ
from cam_global import *
from error_log import *

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
#   gen_g_code_line_str(list x, list y, list u, list v, float cut_speed)
#   【引数】 x, y, u, v, cut_speed
#   【戻り値】 list code_str
#   【機能】 x, y, u, vの各座標および移動速度指令からgコードを生成する．gコードはX,Y,Z,A軸を使用するとする，gコードは「G01 X** Y** U** V** F**」のフォーマットとする．（G01は移動指令）
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
#   get_curdir()
#   【引数】 なし
#   【戻り値】 curdir
#   【機能】 メイン関数が実行されているディレクトリを取得し、出力する
#
#   generate_offset_function(list x_array, list y_array)
#   【引数】 x_array, y_array
#   【戻り値】 offset_function
#   【機能】 x_array、y_arrayを線形補完し、offset_functionを作成する。0～10000のカット速度の範囲で対応できるように、x_arrayの範囲外は0次補完する
#
#   get_cross_point(float p1_x, float p1_y, float p2_x, float p2_y, float p3_x, pfloat 3_y, float p4_x, float p4_y)
#   【引数】 p1_x, p1_y, p2_x, p2_y, p3_x, p3_y, p4_x, p4_y
#   【戻り値】 c1_x, c1_y
#   【機能】 4点（p1,p2,p3,p4）の交点座標（c1_x, c1_y）を算出する
#
#   enerate_offset_interporate_point(list l0_x, list l0_y, list l1_x, list l1_y, float l0_offset, float l1_offset)
#   【引数】 l0_x, l0_y, l1_x, l1_y, l0_offset, l1_offset
#   【戻り値】 x_intp, y_intp
#   【機能】 l0の終端およびl1の始点を、l0_offset, l1_offsetの小さい方のRでフィレット補完する点群を作成する



def offset_line(x, y, d, cut_dir, interp_mode): #ver2.2 interp_mode 追加　ポリラインの場合，オフセット点を中点ではなく，点列を使用するため
    new_x = []
    new_y = []
    k = 0
    
    if len(x) < 2: 
        return x, y

    if len(x) == 2:
        k = np.arctan2((y[1]-y[0]), (x[1]-x[0]))
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
                    k = np.arctan2((y[i+1]-y[i]), (x[i+1]-x[i]))

                new_x.append(x[i]   - d*np.sin(k))
                new_x.append(x[i+1] - d*np.sin(k))
                new_y.append(y[i]   + d*np.cos(k))
                new_y.append(y[i+1] + d*np.cos(k))

                num += 1
            
        else:
            i = 0
            while i < len(x):
                if i == 0:
                    if norm(x[0],y[0],x[1],y[1])>DIST_NEAR:
                        k = np.arctan2((y[1]-y[0]), (x[1]-x[0]))
                        new_x.append(x[0] - d*np.sin(k))      
                        new_y.append(y[0] + d*np.cos(k))
                elif i == len(x) - 1:
                    if norm(x[i-1],y[i-1],x[i],y[i])>DIST_NEAR:
                        k = np.arctan2((y[i]-y[i-1]), (x[i]-x[i-1]))
                        new_x.append(x[i] - d*np.sin(k))      
                        new_y.append(y[i] + d*np.cos(k))                    
                else:
                    if norm(x[i-1],y[i-1],x[i+1],y[i+1])>DIST_NEAR:
                        k = np.arctan2((y[i+1]-y[i-1]), (x[i+1]-x[i-1]))
                        new_x.append(x[i] - d*np.sin(k))      
                        new_y.append(y[i] + d*np.cos(k))
                i += 1

    return np.array(new_x), np.array(new_y)


def norm(x0, y0, x, y):
    return np.sqrt((x-x0)**2 + (y-y0)**2)


def norm_3d(x0, y0, z0, x, y, z):
    return np.sqrt((x-x0)**2 + (y-y0)**2 + (z-z0)**2)


def item2num(item_num):
    temp = item_num.replace("I","")
    temp = '0x0%s'%temp
    num = int(temp,0) - 1    
    return num

def removeSamePoint(x, y):
    i = 1
    new_x = [x[0]]
    new_y = [y[0]]
    while i < len(x):
        if norm(new_x[-1], new_y[-1], x[i], y[i]) > DIST_DELTA:
            new_x.append(x[i])
            new_y.append(y[i])
        i += 1
        
    return new_x, new_y

def get_spline_length_array(x, y):
    length_array = [0]
    
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
    

def get_spline_length(x, y):
    length_array = get_spline_length_array(x, y)
    length = length_array[-1]
    
    return length


def refine_spline_curvature(x, y, N):
    x, y = removeSamePoint(x,y)
    
    N = int(N)
    if N < 4:
        N = 4
    
    length_array = get_spline_length_array(x, y)
    sum_length = length_array[-1]
    u = length_array/sum_length
    t = np.linspace(0, 1, N)
    
    if REFINE_SPLINE_PCHIP == True:
        fx = intp.PchipInterpolator(u, x)
        fy = intp.PchipInterpolator(u, y)
        dfx = fx.derivative(1)
        dfy = fy.derivative(1)
        d2fx = fx.derivative(2)
        d2fy = fy.derivative(2)
        dx = dfx(t)
        dy = dfy(t)
        d2x = d2fx(t)
        d2y = d2fy(t)
    else:
        tck, u = intp.splprep([x, y], k=3, s=0)
        dp = intp.splev(t, tck, 1)
        d2p = intp.splev(t, tck, 2)
        dx = dp[0]
        dy = dp[1]
        d2x = d2p[0]
        d2y = d2p[1]
    
    curvature = []
        
    i = 0
    while i < len(t):
        det = (dx[i]**2 + dy[i]**2)**1.5
        if det < DIST_DELTA:
            c = 1/R_C_MIN
        else:
            c = np.abs(dx[i]*d2y[i] - dy[i]*d2x[i])/det
            if c < 1/R_C_MAX:
                c = 1/R_C_MAX
            if c > 1/R_C_MIN:
                c = 1/R_C_MIN
                
        curvature.append(c)
        i += 1
    
    sum_curvature = [0]
    i = 0
    while i < len(t)-1:
        sum_curvature.append(sum_curvature[-1] + (curvature[i] + curvature[i+1])/2)
        i += 1
    sum_curvature = np.array(sum_curvature)
    u = sum_curvature/sum_curvature[-1]
    
    fu = intp.interp1d(u, t, kind = 'linear')
    
    u_acc = fu(t)
    u_acc_st = u_acc[1]
    u_acc_ed = u_acc[-2]
    
    if REFINE_SPLINE_EDGE == True:
        delta = DIST_SPLINE_EDGE/sum_length
        
        i = 1
        while i <= N_SPLINE_EDGE:
            p_st = delta*i
            p_ed = 1 - delta*i
            if p_st < u_acc_st:
                u_acc = np.insert(u_acc, i, p_st)
            if p_ed > u_acc_ed:
                u_acc = np.insert(u_acc, -i, p_ed)
            i += 1
    
    if REFINE_SPLINE_PCHIP == True:
        x_p = fx(u_acc)
        y_p = fy(u_acc)
    else:
        p = intp.splev(u_acc, tck, 0)
        x_p = p[0]
        y_p = p[1]
        
    return x_p, y_p


def refine_line(x, y, N):
    xp = np.linspace(x[0], x[-1], N)
    yp = np.linspace(y[0], y[-1], N)

    return xp, yp

def generate_arc_length_points(line_object, N):
    
    N = int(N)
    if N < 4:
        N = 4
    
    x = line_object.x
    y = line_object.y

    
    if line_object.line_type == "point":  
        x_p = [x]*N
        y_p = [y]*N
        
    if line_object.line_type == "line":  
        x_p, y_p = refine_line(x, y, N)

    if line_object.line_type == "spline":
        length_array = line_object.calc_length_array()
        sum_length = length_array[-1]
        t_p = length_array/sum_length
        
        if line_object.interp_mode == "linear":
            fx_t = intp.interp1d(t_p, x, kind = "linear")
            fy_t = intp.interp1d(t_p, y, kind = "linear")
                
            t_p_arc = np.linspace(t_p[0], t_p[-1], N)
            
            t_p_arc_add_orgine_point = np.append(t_p, t_p_arc)
            t_p_arc_add_orgine_point = np.sort(t_p_arc_add_orgine_point)              
                    
            x_p = fx_t(t_p_arc_add_orgine_point)
            y_p = fy_t(t_p_arc_add_orgine_point)
            

        else:
            if USE_PCHIP == True:
                fx_t = intp.PchipInterpolator(t_p, x)
                fy_t = intp.PchipInterpolator(t_p, y) 
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


def calc_point_dist(x, y, u, v, z1, z2):
    point_dist_list = []
    
    if len(x) == len(y) == len(u) == len(v):
        i = 0
        while i < len(x):
            temp_norm = norm_3d(x[i], y[i], z1, u[i], v[i], z2)
            point_dist_list.append(temp_norm)
            i += 1
        return np.array(point_dist_list)
        
    else:
        return np.array([])

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
        traceback.print_exc()
        output_log(traceback.format_exc())
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
def gen_g_code_line_str(x,y,u,v, x0,y0,u0,v0, cs_xy, cs_uv, cnc_cs_def):
    code_str = ""
    
    if cnc_cs_def == "InvertTime":
        cs_digits = '.8f' # 逆時間送りの場合は、分解能を上げる
    else:
        cs_digits = '.2f'
    
    if len(x) == len(y) == len(u) == len(v):
        if cnc_cs_def == "XY":
            cut_speed = cs_xy
        elif cnc_cs_def == "UV":
            cut_speed = cs_uv
        elif cnc_cs_def == "XYU":
            l_xyu = np.sqrt((x[0]-x0)**2 + (y[0]-y0)**2 + (u[0]-u0)**2)
            l_xy = np.sqrt((x[0]-x0)**2 + (y[0]-y0)**2)
            if (l_xyu > DIST_NEAR) and (l_xy > DIST_NEAR):
                cut_speed = cs_xy * l_xyu / l_xy
            else:
                cut_speed = cs_xy
        elif cnc_cs_def == "XYV":
            l_xyv = np.sqrt((x[0]-x0)**2 + (y[0]-y0)**2 + (v[0]-v0)**2)
            l_xy = np.sqrt((x[0]-x0)**2 + (y[0]-y0)**2)
            if (l_xyv > DIST_NEAR) and (l_xy > DIST_NEAR):
                cut_speed = cs_xy * l_xyv / l_xy
            else:
                cut_speed = cs_xy                
        elif cnc_cs_def == "InvertTime":
            l_xy = np.sqrt((x[0]-x0)**2 + (y[0]-y0)**2)
            l_uv = np.sqrt((u[0]-u0)**2 + (v[0]-v0)**2)
            t_xy = l_xy/cs_xy
            t_uv = l_uv/cs_uv
            cut_speed = min(t_xy, t_uv)
        else: # cnc_cs_def == "Faster"
            cut_speed = max(cs_xy, cs_uv)

        code_str += "G01 X%s Y%s U%s V%s F%s\n"%(format(x[0], '.6f'), format(y[0], '.6f'), \
                                                 format(u[0], '.6f'), format(v[0], '.6f'), \
                                                 format(cut_speed, cs_digits))
        
        i = 1
        while i < len(x):
            if cnc_cs_def == "XY":
                cut_speed = cs_xy
            elif cnc_cs_def == "UV":
                cut_speed = cs_uv
            elif cnc_cs_def == "XYU":
                l_xyu = np.sqrt((x[i]-x[i-1])**2 + (y[i]-y[i-1])**2 + (u[i]-u[i-1])**2)
                l_xy = np.sqrt((x[i]-x[i-1])**2 + (y[i]-y[i-1])**2)
                if (l_xyu > DIST_NEAR) and (l_xy > DIST_NEAR):
                    cut_speed = cs_xy * l_xyu / l_xy
                else:
                    cut_speed = cs_xy
            elif cnc_cs_def == "XYV":
                l_xyv = np.sqrt((x[i]-x[i-1])**2 + (y[i]-y[i-1])**2 + (v[i]-v[i-1])**2)
                l_xy = np.sqrt((x[i]-x[i-1])**2 + (y[i]-y[i-1])**2)
                if (l_xyv > DIST_NEAR) and (l_xy > DIST_NEAR):
                    cut_speed = cs_xy * l_xyv / l_xy
                else:
                    cut_speed = cs_xy                
            elif cnc_cs_def == "InvertTime":
                l_xy = np.sqrt((x[i]-x[i-1])**2 + (y[i]-y[i-1])**2)
                l_uv = np.sqrt((u[i]-u[i-1])**2 + (v[i]-v[i-1])**2)
                t_xy = l_xy/cs_xy
                t_uv = l_uv/cs_uv
                cut_speed = min(t_xy, t_uv)
            else: # cnc_cs_def == "Faster"
                cut_speed = max(cs_xy, cs_uv)

            code_str += "G01 X%s Y%s U%s V%s F%s\n"%(format(x[i], '.6f'), format(y[i], '.6f'), \
                                                     format(u[i], '.6f'), format(v[i], '.6f'), \
                                                         format(cut_speed, cs_digits))
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


def get_curdir():
    # PyInstallerで実行されているかどうかをチェック
    if getattr(sys, "frozen", False):
        # EXEの実行ファイルのパスを取得
        curdir = os.path.dirname(sys.executable)
    else:
        # スクリプトの実行ファイルのパスを取得
        curdir =  os.path.dirname(os.path.abspath(__file__))
    return curdir


def generate_offset_function(x_array, y_array):
    if x_array[0] > 0:
        x_array_func = np.append(0, x_array)
        y_array_func = np.append(y_array[0], y_array)
    
    if x_array[-1] < 10000:
        x_array_func = np.append(x_array, 10000)
        y_array_func = np.append(y_array, y_array[-1])   
    
    offset_function = intp.interp1d(x_array_func, y_array_func, kind = "linear")
    
    return offset_function


def get_cross_point(p1_x, p1_y, p2_x, p2_y, p3_x, p3_y, p4_x, p4_y):
    # https://imagingsolution.blog.fc2.com/blog-entry-137.html
    s1 = ((p4_x - p2_x) * (p1_y - p2_y) - (p4_y - p2_y) * (p1_x - p2_x)) / 2.0
    s2 = ((p4_x - p2_x) * (p2_y - p3_y) - (p4_y - p2_y) * (p2_x - p3_x)) / 2.0
    
    c1_x = p1_x + (p3_x - p1_x) * (s1 / (s1 + s2))
    c1_y = p1_y + (p3_y - p1_y) * (s1 / (s1 + s2))
    
    return c1_x, c1_y


def getCrossPointFromPoint(p1_x, p1_y, p2_x, p2_y, p3_x, p3_y, p4_x, p4_y):
    # https://imagingsolution.blog.fc2.com/blog-entry-137.html
    s1 = ((p4_x - p2_x) * (p1_y - p2_y) - (p4_y - p2_y) * (p1_x - p2_x)) / 2.0
    s2 = ((p4_x - p2_x) * (p2_y - p3_y) - (p4_y - p2_y) * (p2_x - p3_x)) / 2.0
    
    c1_x = p1_x + (p3_x - p1_x) * (s1 / (s1 + s2))
    c1_y = p1_y + (p3_y - p1_y) * (s1 / (s1 + s2))
    
    return c1_x, c1_y


def getCrossPointFromLines(a, b, c, d):
    # https://mathwords.net/nityokusenkoten
    c1_x = (d-b)/(a-c)
    c1_y = (a*d - b*c)/(a-c)
    return c1_x, c1_y



def getFlatten(array):
    ret = []
    for val in array:
        ret.append(float(val))
    return np.array(ret)


def detectRotation(x, y):
    i = 0
    temp_s = 0

    while i < len(x) - 1:
        temp_s += x[i]*y[i+1] - x[i+1]*y[i]
        i += 1
    temp_s += x[-1]*y[0] - x[0]*y[-1]
    
    if temp_s > 0:
        ccw = True
    else:
        ccw = False
    
    return ccw


def getFiletSita(sita_st, sita_ed):
    
    # 開始角から終了角までの変化量（sita_stとsita_edの傾きをもつ線のなす角）を計算
    delta_sita = sita_ed - sita_st
    
    if delta_sita <= np.pi and delta_sita > -np.pi:
        # 鋭角なのでそのままでOK
        return sita_st, sita_ed
    elif delta_sita > np.pi:
        # 反時計回りとしたとき、終了角が1周分オーバーラップしているので、終了角から2piを引く
        return sita_st, sita_ed-2*np.pi
    else:
        # 反時計回りとしたとき、終了角が1周分不足しているので、終了角に2piを足す
        return sita_st, sita_ed +2*np.pi,
    

def generate_offset_interporate_point(l0_x, l0_y, l1_x, l1_y, l0_offset, l1_offset):
    #x_intp = np.array([l0_x[1], l1_x[0]])
    #y_intp = np.array([l0_y[1], l1_y[0]])  
    x_intp = np.array([])
    y_intp = np.array([])
    
    try:
        p2p_dist = norm(l0_x[1], l0_y[1], l1_x[0], l1_y[0])
        
        if (p2p_dist > DIST_NEAR) and (p2p_dist < l0_offset *2) and (p2p_dist < l1_offset *2) :
            
            # フィレットのRをオフセット距離から決定する（Rが大きいと、線端とフィレット補完点がオーバーラップしうるため、小さい方をRとする）
            r = min(l0_offset, l1_offset)
            
            # l0とl1のなす角sitaを内積により求める
            # https://w3e.kanazawa-it.ac.jp/math/category/vector/henkan-tex.cgi?target=/math/category/vector/naiseki-wo-fukumu-kihonsiki.html&pcview=2
            a1 = l0_x[1] - l0_x[0]
            a2 = l0_y[1] - l0_y[0]
            b1 = l1_x[0] - l1_x[1]
            b2 = l1_y[0] - l1_y[1]
                
            sita = np.arccos( (a1*b1 + a2*b2)/(np.sqrt(a1**2 + a2**2) * np.sqrt(b1**2 + b2**2)) ) / 2.0
    
            # l0がx軸となす角をarctan2により求める
            alpha = np.arctan2(a2, a1)
            
            # l1がx軸となす角をarctan2により求める
            beta = np.arctan2(b2, b1)
            
            # l0とl1の交点を求める
            cx, cy = getCrossPointFromPoint(l0_x[0], l0_y[0], l1_x[0], l1_y[0], l0_x[1], l0_y[1], l1_x[1], l1_y[1])
            
            # 幾何より、l0延長線上のフィレット開始点（p1）および、フィレットの中心座標（p0）を求める
            p1_x = cx - r * (1/np.tan(sita)) * np.cos(-alpha)
            p1_y = cy + r * (1/np.tan(sita)) * np.sin(-alpha)
    
            p2_x = cx - r * (1/np.tan(sita)) * np.cos(-beta)
            p2_y = cy + r * (1/np.tan(sita)) * np.sin(-beta)
            
            m2_0 = np.tan(alpha + np.pi/2)
            m2_1 = np.tan(beta + np.pi/2)
            b0 = -m2_0*p1_x + p1_y
            b1 = -m2_1*p2_x + p2_y
            
            f_x, f_y = getCrossPointFromLines(m2_0, b0, m2_1, b1)
    
            # 円弧の始点角と終点角を計算する。
            sita_st = float(np.arctan2(p1_y-f_y, p1_x-f_x))
            sita_ed = float(np.arctan2(p2_y-f_y, p2_x-f_x))
            sita_st, sita_ed = getFiletSita(sita_st, sita_ed)
            
            if r <= DIST_NEAR*10:
                r = DIST_NEAR*10
                N = 4
            else:
                N = N_FILLET_INTERPORATE
            sita = np.linspace(sita_st, sita_ed, N)
            sita = sita[1:-1] # 重複点が生じないように、始点と終点は削除する
    
            x_intp = r*np.cos(sita) + f_x
            y_intp = r*np.sin(sita) + f_y

    except:
        traceback.print_exc()
        pass
    
    return x_intp, y_intp


# https://qiita.com/wihan23/items/03efd7cd40dfec96a987
def max_min_cross(p1, p2, p3, p4):
    min_ab, max_ab = min(p1, p2), max(p1, p2)
    min_cd, max_cd = min(p3, p4), max(p3, p4)

    if min_ab > max_cd or max_ab < min_cd:
        return False

    return True

# https://qiita.com/wihan23/items/03efd7cd40dfec96a987
def cross_judge(a, b, c, d):
    
    # x座標による判定
    if not max_min_cross(a[0], b[0], c[0], d[0]):
        return False

    # y座標による判定
    if not max_min_cross(a[1], b[1], c[1], d[1]):
        return False
    
    tc1 = (a[0] - b[0]) * (c[1] - a[1]) + (a[1] - b[1]) * (a[0] - c[0])
    tc2 = (a[0] - b[0]) * (d[1] - a[1]) + (a[1] - b[1]) * (a[0] - d[0])
    td1 = (c[0] - d[0]) * (a[1] - c[1]) + (c[1] - d[1]) * (c[0] - a[0])
    td2 = (c[0] - d[0]) * (b[1] - c[1]) + (c[1] - d[1]) * (c[0] - b[0])
    return tc1 * tc2 <= 0 and td1 * td2 <= 0


def remove_self_collision(x, y):
    # 同一点があると正しく自己交差を検出できないため、削除する
    x, y = removeSamePoint(x, y)
    
    new_x = [x[0]]
    new_y = [y[0]]
    detection = False
    
    i = 1
    while i < len(x):
        j = i+1
        p1 = [x[i-1], y[i-1]]
        p2 = [x[i], y[i]]
        while j < len(x)-3:
            p3 = [x[j], y[j]]
            p4 = [x[j+1], y[j+1]]
            if cross_judge(p1, p2, p3, p4) == True:
                detection = True
                #cx, cy = getCrossPointFromPoint(p1[0], p1[1], p3[0], p3[1], p2[0], p2[1], p4[0], p4[1])
                #new_x.append(cx)
                #new_y.append(cy)             
                i = j+1
            j += 1
        new_x.append(x[i])
        new_y.append(y[i])
        i += 1
        
    return new_x, new_y, detection

