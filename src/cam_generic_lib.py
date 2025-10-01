# -*- coding: utf-8 -*-
"""CAMで共通する処理をまとめたライブラリ

"""
# 外部ライブラリ
import numpy as np
from matplotlib import pyplot as plt
from scipy import interpolate as intp
from scipy.integrate import quad
from scipy.optimize import fmin
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
#   generate_arc_length_points(line line, int N)
#   【引数】 line, N
#   【戻り値】　list x_p, y_p
#   【機能】 lineのx, y点列をスプライン補完し，これをN等分した点列を作成する．
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



def offset_line(x, y, d, interp_mode):
    """オフセットした座標点列を計算する

    x,y の座標点列をdだけオフセットした点列を作成する。

    オフセットした座標は、座標点における接線の傾きkを計算し、以下から計算する

    .. math:: 
        x_{new} = x-d\\cdot\\sin(k)

        y_{new} = x+d\\cdot\\cos(k)

    接線の傾きkは、x座標の増減の向きを反映させるため、およびy軸と並行な座標点列に対応するため、arctan2を用いて計算する

    Args:
        x (numpy.array): 元のx座標点列
        y (numpy.array): 元のy座標点列
        d (float): オフセット距離
        interp_mode (str): スプラインの場合、ポリラインとしてオフセットするかどうか(linear:ポリラインとしてオフセット)

    Returns:
        np.array: オフセット後のx座標点列
        np.array: オフセット後のy座標点列
    
    See Also:
        アルゴリズムの参考

        https://stackoverflow.com/questions/32772638/python-how-to-get-the-x-y-coordinates-of-a-offset-spline-from-a-x-y-list-of-poi
    """
    new_x = []
    new_y = []
    k = 0
    
    # 点の場合はオフセット方向を定義できないので、オフセットせずに元の点列を出力する
    if len(x) < 2: 
        return x, y

    # 線分の場合、始点と終点で傾きは同じなので、同じkを用いてそれぞれオフセットする
    if len(x) == 2:
        k = np.arctan2((y[1]-y[0]), (x[1]-x[0]))
        new_x.append(x[0] - d*np.sin(k))
        new_x.append(x[1] - d*np.sin(k))
        new_y.append(y[0] + d*np.cos(k))
        new_y.append(y[1] + d*np.cos(k))

    # スプラインの場合
    if len(x) > 2:
        # ポリラインの場合、角が失われないように、線の端点をそれぞれオフセットする（点の数は2倍になる）
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
            # スプラインの場合、始点と中点以外は、１つ先と１つ前の点を用いて傾きを計算する
            # 点列の間隔が狭い場合、傾きが正常に計算できないことがあるので、近傍点の場合(normがDIST_NEAR未満の場合）はスキップする
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
    """2次元座標における、2点(x0, y0)と(x, y)の距離dを計算する

    .. math::
        d = \\sqrt{(x-x_0)^2 + (y-y_0)^2}

    Args:
        x0 (float): 1つめの座標点のx座標
        y0 (float): 1つめの座標点のy座標
        x (float): 2つめの座標点のx座標
        y (float): 2つめの座標点のy座標

    Returns:
        float: 2点(x0, y0)と(x, y)の間の距離
    """
    return np.sqrt((x-x0)**2 + (y-y0)**2)


def norm_3d(x0, y0, z0, x, y, z):
    """3次元座標における、2点(x0, y0, z0)と(x, y, z)の距離dを計算する

    .. math::
        d = \\sqrt{(x-x_0)^2 + (y-y_0)^2 +(z-z_0)^2 }

    Args:
        x0 (float): 1つめの座標点のx座標
        y0 (float): 1つめの座標点のy座標
        z0 (float): 1つめの座標点のz座標
        x (float): 2つめの座標点のx座標
        y (float): 2つめの座標点のy座標
        z (float): 2つめの座標点のz座標

    Returns:
        float: 2点(x0, y0, z0)と(x, y, z)の間の距離
    """
    return np.sqrt((x-x0)**2 + (y-y0)**2 + (z-z0)**2)


def remove_same_point(x, y):
    """座標点列に含まれる近傍点を削除する

    Args:
        x (np.array): 元の座標点列のx座標配列
        y (np.array): 元の座標点列のy座標配列

    Returns:
        np.array: 近傍点を削除した座標点列のx座標配列
        np.array: 近傍点を削除した座標点列のy座標配列
    """
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
    """与えられた座標点列に対して、始点からi番目の座標点までの線長を計算した配列を出力する

    線長は、以下で計算する。x,yの微分は、x,y座標配列を媒介変数形式の3次スプラインで補完した後、媒介変数で微分する

    .. math:: 
        L_k = \\int_{0}^{t_k}\\Delta l(t) dt

        \\Delta l=\\sqrt{(\\frac{\\text{d}x}{\\text{d}t})^2 + (\\frac{\\text{d}y}{\\text{d}t})^2 }

    Args:
        x (numpy.array): x座標点列
        y (numpy.array): y座標点列

    Returns:
        np.array: 始点からi番目の座標点までの線長を計算した配列
    """

    length_array = [0] # 始点からi番目の座標点までの線長を計算した配列
    
    dl = 0
    dt = 1
    s_l = 0
    t_p = np.linspace(0, dt * len(x), len(x)) #媒介変数

    # 媒介変数で3次スプライン補完
    # 補完アルゴリズムを簡単に変更できるように、slprevは用いていない
    fx_t = intp.CubicSpline(t_p, x)
    fy_t = intp.CubicSpline(t_p, y)
    
    # 微分値を計算
    dfx_t = fx_t.derivative(1)
    dfy_t = fy_t.derivative(1)
    
    # dlの関数
    fdl = lambda t: np.sqrt(dfx_t(t)**2 + dfy_t(t)**2)
    
    i = 0
    while i < len(t_p) - 1:
        # i~i+1の区間での数値積分
        dl = quad(fdl, t_p[i], t_p[i+1])
        # 前の区間までの線長に加算
        s_l += dl[0]
        # i番目までの線長を配列に格納
        length_array.append(s_l)
        i += 1
        
    return np.array(length_array)
    

def get_spline_length(x, y):
    """始点から終点までの線長を計算する

    get_spline_length_arrayにより始点からi番目の座標点までの線長を計算した配列を計算し、配列の最後の値を出力する
    
    Args:
        x (numpy.array): x座標点列
        y (numpy.array): y座標点列

    Returns:
        float: 始点から終点までの線長
    """
    length_array = get_spline_length_array(x, y)
    length = length_array[-1]
    
    return length


def refine_spline_curvature(x, y, N):
    """スプラインの座標点列を、曲率に基づいてリファインした座標を計算する

    媒介変数表示されたスプラインでは、下式により曲率cを計算できる

    .. math::
        c = \\frac{|x'y''-y'x''|}{(x'^2+y'^2)^{\\frac{3}{2}}}

    曲率cの積算値を0~1の範囲で正規化したものを用いてスプライン点列を補完することで、曲率に比例して点列を増すようにする

    スプラインの端点は、間隔が大きいと、スプラインと他の線を結合した場合に形状を維持できないので、間隔を狭める

    Args:
        x (numpy.array): x座標点列
        y (numpy.array): y座標点列
        N (int): リファイン後の座標点列の点数

    Returns:
        numpy.array: リファイン後のx座標点列
        numpy.array: リファイン後のy座標点列
    """

    # 近傍点があるとスプライン補完がうまく計算できないため、除去する
    x, y = remove_same_point(x,y)
    
    # スプライン補完は最低4点必要なので下限リミットを設ける
    N = int(N)
    if N < 4:
        N = 4
    
    # PCHIP補完用 等間隔点作成のため、長さ配列を計算する
    length_array = get_spline_length_array(x, y)
    sum_length = length_array[-1]
    u = length_array/sum_length

    # 等間隔点用の補完用媒介変数
    t = np.linspace(0, 1, N)
    
    # PCHIPで補完する場合
    if REFINE_SPLINE_PCHIP == True:
        # 座標補完関数
        fx = intp.PchipInterpolator(u, x)
        fy = intp.PchipInterpolator(u, y)
        # 媒介変数による1階微分(x', y')
        dfx = fx.derivative(1)
        dfy = fy.derivative(1)
        # 媒介変数による2階微分(x'', y'')
        d2fx = fx.derivative(2)
        d2fy = fy.derivative(2)
        # tでの1階微分値を取得
        dx = dfx(t)
        dy = dfy(t)
        # tでの2階微分値を取得
        d2x = d2fx(t)
        d2y = d2fy(t)
    
    # 3次スプライン補完で補完する場合(CADと同じ)
    else:
        # 座標補完関数
        tck, u = intp.splprep([x, y], k=3, s=0)
        # tでの1階微分値を取得(x', y')
        dp = intp.splev(t, tck, 1)
        dx = dp[0]
        dy = dp[1]
        # tでの2階微分値を取得(x'', y'')
        d2p = intp.splev(t, tck, 2)
        d2x = d2p[0]
        d2y = d2p[1]
    
    # tにおける曲率を格納する配列
    curvature = []
        
    i = 0
    while i < len(t):
        # 0割防止のため、分母の値に下限リミットを設ける
        det = (dx[i]**2 + dy[i]**2)**1.5
        if det < DIST_DELTA:
            # 分母が著しく小さい(曲率が大のとき)は上限にサチらせる
            c = 1/R_C_MIN
        else:
            # 曲率を計算
            c = np.abs(dx[i]*d2y[i] - dy[i]*d2x[i])/det
            # 曲率の値に対し、上下限リミットを設ける
            if c < 1/R_C_MAX:
                c = 1/R_C_MAX
            if c > 1/R_C_MIN:
                c = 1/R_C_MIN
                
        curvature.append(c)
        i += 1
    
    # 曲率の積算値を計算
    sum_curvature = [0]
    i = 0
    while i < len(t)-1:
        sum_curvature.append(sum_curvature[-1] + (curvature[i] + curvature[i+1])/2)
        i += 1
    sum_curvature = np.array(sum_curvature)

    # 曲率の積算値を0~1に正規化
    u = sum_curvature/sum_curvature[-1]
    
    # 曲率の積算値を用いて、点列作成用媒介変数(u_acc)を作成
    # 補完は、cubicだと波打った場合、座標が戻るため、波打たないようにlinearを使用
    fu = intp.interp1d(u, t, kind = 'linear')
    u_acc = fu(t)
    u_acc_st = u_acc[1] # 始点の次の点
    u_acc_ed = u_acc[-2] # 終点の前の点
    
    # スプラインの端点の補完点列を、DIST_SPLINE_EDGEの間隔で作成する
    if REFINE_SPLINE_EDGE == True:
        # DIST_SPLINE_EDGEの線長に対する比が、媒介変数の間隔となる
        delta = DIST_SPLINE_EDGE/sum_length
        
        # N_SPLINE_EDGEだけDIST_SPLINE_EDGEの間隔で作成
        i = 1
        while i <= N_SPLINE_EDGE:
            p_st = delta*i
            p_ed = 1 - delta*i
            # 始点の次の点／終点の前の点　にオーバラップする場合は作成しない
            if p_st < u_acc_st:
                u_acc = np.insert(u_acc, i, p_st)
            if p_ed > u_acc_ed:
                u_acc = np.insert(u_acc, -i, p_ed)
            i += 1

    # PCHIPで補完する場合
    if REFINE_SPLINE_PCHIP == True:
        x_p = fx(u_acc)
        y_p = fy(u_acc)
    # 3次スプライン補完で補完する場合(CADと同じ)
    else:
        p = intp.splev(u_acc, tck, 0)
        x_p = p[0]
        y_p = p[1]
        
    return x_p, y_p


def refine_line(x, y, N):
    """線分の座標点列をリファインした座標を計算する

    線分の場合、始点、終点のx,y座標を等間隔で分割すればよい

    Args:
        x (numpy.array): x座標点列
        y (numpy.array): y座標点列
        N (int): リファイン後の座標点列の点数

    Returns:
        numpy.array: リファイン後のx座標点列
        numpy.array: リファイン後のy座標点列
    """
    # x,y座標を等間隔でN等分したものをリファイン後の座標とする
    xp = np.linspace(x[0], x[-1], N)
    yp = np.linspace(y[0], y[-1], N)

    return xp, yp

def generate_arc_length_points(line, N):
    """線を等間隔分割した座標点を算出する

    点の場合、同じ座標をN個格納した配列を出力する

    線分の場合、線をN分割した配列を出力する

    スプラインの場合、スプライン補完関数により線長をN等分した配列を出力する

    スプラインで線長をN等分する場合、i(i=0...N）点目までの線長を計算し、
    これを0~1に正規化した媒介変数を用いて座標点列を補完することで、
    等間隔の媒介変数を用いて補完点列を作成すると、出力される座標点列の間隔も
    線長に対して等間隔となる

    スプライン補完の補完方法は、CADと同じ3次スプラインと、角があっても線がうねらない
    PCHIPアルゴリズムを選択できるようにする

    Args:
        line (LineObject): LineObjectクラスのインスタンス
        N (int): 等間隔分割点数

    Returns:
        numpy.array: 等間隔分割後のx座標点列
        numpy.array: 等間隔分割後のy座標点列
    """
    
    # スプラインの場合、補完点列が4未満では適切に演算できないため、下限リミットを設ける
    N = int(N)
    if N < 4:
        N = 4
    
    x = line.x
    y = line.y
    
    # 点の場合、同じ座標をN点格納
    if line.line_type == "point":  
        x_p = [x]*N
        y_p = [y]*N
    
    # 線分の場合、refine_lineにより等間隔点列作成
    if line.line_type == "line":  
        x_p, y_p = refine_line(x, y, N)

    # スプラインの場合
    if line.line_type == "spline":
        # 線長を正規化した配列（t_p）を作成
        length_array = line.calc_length_array()
        sum_length = length_array[-1]
        t_p = length_array/sum_length
        
        # スプラインが1次スプラインの場合、linearで補完関数を作成
        if line.interp_mode == "linear":
            # t_pを媒介変数として補完
            fx_t = intp.interp1d(t_p, x, kind = "linear")
            fy_t = intp.interp1d(t_p, y, kind = "linear")
            
            # 等間隔な媒介変数を作成
            t_p_arc = np.linspace(t_p[0], t_p[-1], N)
            
            # ポリラインの場合、角の情報が失われないように、オリジナル点列を追加する
            # t_pは元の座標点に対応する
            t_p_arc_add_orgine_point = np.append(t_p, t_p_arc)
            t_p_arc_add_orgine_point = np.sort(t_p_arc_add_orgine_point)              
                    
            # 補完後の点列を作成
            x_p = fx_t(t_p_arc_add_orgine_point)
            y_p = fy_t(t_p_arc_add_orgine_point)
            
        # スプラインが3次スプラインの場合、cubicまたはPCHIPで補完関数を作成
        else:
            # 角の存在を想定する場合、PCHIPで補完
            if USE_PCHIP == True:
                fx_t = intp.PchipInterpolator(t_p, x)
                fy_t = intp.PchipInterpolator(t_p, y) 
            # CADに厳密に補完方法を合わせたい場合、cubicで補完
            else:
                fx_t = intp.CubicSpline(t_p, x)
                fy_t = intp.CubicSpline(t_p, y)

            # 等間隔な媒介変数を作成
            t_p_arc = np.linspace(t_p[0], t_p[-1], N)
            
            # 補完後の点列を作成
            x_p = fx_t(t_p_arc)
            y_p = fy_t(t_p_arc)
            
    return x_p, y_p


def calc_point_dist(x, y, u, v, z1, z2):
    """z1とz2の並行した２平面上の、対応するx,y座標とu,v座標間の距離を計算する

    Args:
        x (numpy.array): z1の平面に存在するx座標点列(x[i],y[i])と(u[i],v[i])は対応する
        y (numpy.array): z1の平面に存在するy座標点列(x[i],y[i])と(u[i],v[i])は対応する
        u (numpy.array): z2の平面に存在するu座標点列(x[i],y[i])と(u[i],v[i])は対応する
        v (numpy.array): z2の平面に存在するv座標点列(x[i],y[i])と(u[i],v[i])は対応する
        z1 (float): x,y座標点列が存在する平面のz座標
        z2 (float): u,v座標点列が存在する平面のz座標

    Returns:
        numpy.array: 対応する(x[i],y[i])と(u[i],v[i])間の距離を計算した配列
    """
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


def plot_3d_cut_path(ax, x, y, u, v, xm, ym, um, vm, z_xy, z_uv, z_m, num_per_plot, frame):
    """3Dカットパスのうち、frameで指定された線を描画する

    axに対し、以下の3本の線を作図する。ここでi = num_per_plot*frame

    1. (x[i],y[i])->(u[i],v[i])    
        赤線で作図。ワークを表現する

    2. (xm[i],ym[i])->(x[i],y[i])   
        青線で作図。ワークとCNC駆動面間の空間を表現する

    3. (u[i],v[i])->(um[i],vm[i])   
        青線で作図。ワークとCNC駆動面間の空間を表現する

    Args:
        ax (matplotlib.axes): 線をプロットするAxesオブジェクト
        x (numpy.array): xy平面におけるワーク端のx座標点列
        y (numpy.array): xy平面におけるワーク端のy座標点列
        u (numpy.array): uv平面におけるワーク端のu座標点列
        v (numpy.array): uv平面におけるワーク端のv座標点列
        xm (numpy.array): xy駆動面側のCNC駆動面におけるx座標点列
        ym (numpy.array): xy駆動面側のCNC駆動面におけるy座標点列
        um (numpy.array): uv駆動面側のCNC駆動面におけるu座標点列
        vm (numpy.array): uv駆動面側のCNC駆動面におけるv座標点列
        z_xy (float): xy平面とxy駆動面側のCNC駆動面間の距離
        z_uv (float): uv平面とuv駆動面側のCNC駆動面間の距離
        z_m (float): xy駆動面側のCNC駆動面と、uv駆動面側のCNC駆動面との距離
        num_per_plot (int): x,y,u,v配列の何点に1つ線をプロットするか（すべてプロットすると重いため）
        frame (int): 作図する線の番号

    Note:
        描画処理中に、例外が発生した場合、標準出力へ表示した上で、output_logによりエラーファイルにも出力する

    See Also:
        https://matplotlib.org/stable/api/axes_api.html
        
    """
    
    try:
        # 座標点列がすべて対応している（つまり点列数が等しい）場合作図
        if len(x) == len(y) == len(u) == len(v) == len(xm) == len(ym) == len(um) == len(vm):
            i = frame * num_per_plot
            # 端点調整
            if i >= len(x):
                i = len(x)-1
            elif i < 0:
                i = 0
            
            # 3Dで線を3本プロット
            # 重い場合は、1本にまとめても良いかもしれない
            ax.plot([x[i],u[i]], [y[i],v[i]],  [z_xy, z_m - z_uv], color = 'r', alpha = 0.5)
            ax.plot([x[i],xm[i]],[y[i],ym[i]], [z_xy, 0] , color = 'b', alpha = 0.5)
            ax.plot([u[i],um[i]],[v[i],vm[i]], [z_m - z_uv, z_m], color = 'b', alpha = 0.5)
    except:
        traceback.print_exc()
        output_log(traceback.format_exc())
        pass


def file_chk(filename):
    """dxfファイルが存在し、かつ拡張子がdxfかを確認する

    Args:
        filename (str): dxfファイルのパス

    Returns:
        int: チェック結果(1:OK, 0:ファイルの拡張子がdxfでない, -1:ファイルが存在しない)
    """
    if op.exists(filename) == True:
        if filename.split('.')[-1] == "dxf":
            return 1
        else:
            return 0
    else:
        return -1


def gen_g_code_line_str(x,y,u,v, x0,y0,u0,v0, cs_xy, cs_uv, cnc_cs_def):
    """座標点列からGコードに出力する文字列を作成する

    Gコードは、G01で生成する

    G01のFeedRate(F)は、xy平面のカット速度指令値およびuv平面のカット速度指令値を用いて、
    CNCコントローラーにおける速度指令値の解釈方法に併せて、以下のように計算する

    1. CNCコントローラーがXY(UV)座標軸の速度を採用している場合
        この場合、XY(UV)のカット速度指令値をそのままFeedRateとする

        .. math:: 
            F =  CS_{xy}

    2. CNCコントローラーがXYU(XYV)座標軸の速度を採用している場合
        この場合は、CAMはXY座標速度でカットしたいにもかかわらず、U(V)軸の移動速度もCNCコントローラー側は考慮してしまう

        よって、XY速度をXYU速度に直して指令値とする

        .. math:: 
            F = CS_{xy}\\cdot\\frac{\\sqrt{\\Delta x^2 + \\Delta y^2 +\\Delta u^2 }}{\\sqrt{\\Delta x^2 + \\Delta y^2 }}
    
    3. CNCコントローラーがG93(逆時間送り)を採用している場合
        この場合、次の点までの移動時間をFeedRateとする

        .. math:: 
            F_{xy} = \\frac{\\sqrt{\\Delta x^2 + \\Delta y^2 }}{CS_{xy}}

            F_{uv} = \\frac{\\sqrt{\\Delta u^2 + \\Delta v^2 }}{CS_{uv}}

            F = min(F_{xy}, F_{uv})

    Args:
        x (numpy.array): Gコードに出力するx座標点列
        y (numpy.array): Gコードに出力するy座標点列
        u (numpy.array): Gコードに出力するu座標点列
        v (numpy.array): Gコードに出力するv座標点列
        x0 (float): x[0]の前の座標点（前の線の終端点のx座標）
        y0 (float): y[0]の前の座標点（前の線の終端点のy座標）
        u0 (float): u[0]の前の座標点（前の線の終端点のu座標）
        v0 (float): v[0]の前の座標点（前の線の終端点のv座標）
        cs_xy (float): xy平面側のCNC駆動面におけるカット速度指令値
        cs_uv (float): uv平面側のCNC駆動面におけるカット速度指令値
        cnc_cs_def (str): CNCコントローラーにおける速度指令値の解釈方法

    Returns:
        str: Gコードに出力する文字列
    """
    code_str = ""
    
    if cnc_cs_def == "InvertTime":
        cs_digits = '.8f' # 逆時間送りの場合は、分解能を上げる(小数点8桁)
    else:
        cs_digits = '.2f' # 速度の場合は、分解能はそこそこでOK(小数点2桁)
    
    # 座標点列が対応している（点数が揃っている）場合にGコードを生成する
    if len(x) == len(y) == len(u) == len(v):
        # 前の線の終端点から開始点までの速度を計算
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

        # 前の線の終端点から開始点までの移動司令
        code_str += "G01 X%s Y%s U%s V%s F%s\n"%(format(x[0], '.6f'), format(y[0], '.6f'), \
                                                 format(u[0], '.6f'), format(v[0], '.6f'), \
                                                 format(cut_speed, cs_digits))
        
        # 線の中での移動指令
        i = 1
        while i < len(x):
            # 前回の点から今回の点までの移動速度を算出
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

            # 前回の点から今回の点での移動司令
            code_str += "G01 X%s Y%s U%s V%s F%s\n"%(format(x[i], '.6f'), format(y[i], '.6f'), \
                                                     format(u[i], '.6f'), format(v[i], '.6f'), \
                                                         format(cut_speed, cs_digits))
            i += 1
        return code_str


def arc_to_spline(arc_obj):
    """ezdxfのArcオブジェクトから、座標点列を作成する

    座標点列は、10degに1点作成する。

    Args:
        arc_obj (ezdxf.entities.Arc): ezdxfの円弧オブジェクト

    Returns:
        numpy.array: 円弧上のx, y座標点列

    See Also:
        https://ezdxf.readthedocs.io/en/stable/dxfentities/arc.html#ezdxf.entities.Arc 
    """
    
    # Arcオブジェクトから円弧の情報を取得
    radius = arc_obj.dxf.radius # 円弧の半径
    x_center_point  = arc_obj.dxf.center[0] # 円弧の中心x座標
    y_center_point  = arc_obj.dxf.center[1] # 円弧の中心y座標
    start_angle     = arc_obj.dxf.start_angle # 円弧の開始角度
    end_angle       = arc_obj.dxf.end_angle # 円弧の終了角度
    
    # 角度ラッピング
    if end_angle < start_angle:
        end_angle += 360
    
    # 座標点列の個数を計算。10degに1点作成する
    num_point = int(np.abs(end_angle - start_angle)/10.0)

    # 3点未満だと直線になるので、下限リミットを設ける
    if num_point < 3:
        num_point = 3
    
    # 補完点列を作成
    angle_array = np.radians(np.linspace(start_angle, end_angle, num_point))
    x_p = radius * np.cos(angle_array) + x_center_point
    y_p = radius * np.sin(angle_array) + y_center_point
    
    return np.array([x_p, y_p]).T


def poly_to_spline(poly_obj):
    """ezdxfのPolylineオブジェクトから、座標点列を作成する

    ポリラインは線分の集合体なので、同じ座標点列を２個ずつ作成する
    
    Args:
        poly_obj (ezdxf.entities.Polyline): ezdxfのポリラインオブジェクト

    Returns:
        numpy.array: ポリラインの座標点列

    Todo:
        同じ座標点列を２個ずつ作成する必要性は、要検討

    See Also:
        https://ezdxf.readthedocs.io/en/stable/dxfentities/polyline.html 
    
    """
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
    """スクリプトが実行されている絶対パスを取得する

    PyInstallerでExe化した場合、実行パスがExeの保存場所でない場所を示してしまう。

    この対策として、PyInstallerから実行されているかを判定し、スクリプトまたはExeの実行パス出力する。

    Returns:
        str: 実行ファイルのカレントディレクトリ

    See Also:
        https://qiita.com/Authns/items/f3cf6e9f27fc0b5632b3 

    """
    # PyInstallerで実行されているかどうかをチェック
    if getattr(sys, "frozen", False):
        # EXEの実行ファイルのパスを取得
        curdir = os.path.dirname(sys.executable)
    else:
        # スクリプトの実行ファイルのパスを取得
        curdir =  os.path.dirname(os.path.abspath(__file__))
    return curdir


def generate_offset_function(x_array, y_array):
    """カット速度vs溶け量のグラフから線形補完関数を作成する

    グラフの範囲外のカット速度がCAM側で計算された場合に備えて、0~10000 mm/minの範囲で端点を0次ホールドする
    更に、保管時に外挿オプション（fill_value="extrapolate"）とする

    Args:
        x_array (numpy.array): カット速度
        y_array (numpy.array): オフセット量（溶け量）

    Returns:
        interp1d: オフセット関数のオブジェクト

    See Also:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.interp1d.html

    """

    # カット速度の下端が0より大きい場合、0まで0次ホールド
    if x_array[0] > 0:
        x_array_func = np.append(0, x_array)
        y_array_func = np.append(y_array[0], y_array)
    
    # カット速度の上端が10000より小さい場合、10000まで0次ホールド
    if x_array[-1] < 10000:
        x_array_func = np.append(x_array, 10000)
        y_array_func = np.append(y_array, y_array[-1])   
    
    # SciPyのinterp1にて線形補完。外挿オプションをONとする。
    offset_function = intp.interp1d(x_array_func, y_array_func, kind = "linear", fill_value="extrapolate")
    
    return offset_function


def get_cross_point_from_point(p1_x, p1_y, p2_x, p2_y, p3_x, p3_y, p4_x, p4_y):
    """4点(p1,p2,p3,p4)の交点の座標を求める

    Args:
        p1_x (float): p1のx座標
        p1_y (float): p1のy座標
        p2_x (float): p2のx座標
        p2_y (float): p2のy座標
        p3_x (float): p3のx座標
        p3_y (float): p3のy座標
        p4_x (float): p4のx座標
        p4_y (float): p4のy座標

    Returns:
        float: 交点のx座標
        float: 交点のy座標
    
    See Also:
        https://imagingsolution.blog.fc2.com/blog-entry-137.html
        
    """

    s1 = ((p4_x - p2_x) * (p1_y - p2_y) - (p4_y - p2_y) * (p1_x - p2_x)) / 2.0
    s2 = ((p4_x - p2_x) * (p2_y - p3_y) - (p4_y - p2_y) * (p2_x - p3_x)) / 2.0
    
    c1_x = p1_x + (p3_x - p1_x) * (s1 / (s1 + s2))
    c1_y = p1_y + (p3_y - p1_y) * (s1 / (s1 + s2))
    
    return c1_x, c1_y


def get_cross_point_from_lines(a, b, c, d):
    """傾きa,切片bの直線と、傾きc,切片dの直線の交点の座標を求める

    Args:
        a (float): 1本目の直線の傾き
        b (float): 1本目の直線の切片
        c (float): 2本目の直線の傾き
        d (float): 2本目の直線の切片

    Returns:
        float: 交点のx座標
        float: 交点のy座標

    See Also:
        https://mathwords.net/nityokusenkoten
    """
    
    c1_x = (d-b)/(a-c)
    c1_y = (a*d - b*c)/(a-c)
    return c1_x, c1_y



def get_flatten(array):
    """1*1のサイズの配列が含まれる長さNの配列を、1*Nの配列に整形する

    Args:
        array (numpy.array): 元の配列（内包されるデータはfloat型）

    Returns:
        numpy.array: 整形後の配列
    """
    
    ret = []
    for val in array:
        ret.append(float(val))
    return np.array(ret)


def detect_rotation(x, y):
    """点列の回転方向（ccw/cw）を検出する

    Args:
        x (numpy.array): x座標点列
        y (numpy.array): y座標点列

    Returns:
        bool: ccwかcwか(True:CCW, False/CW)

    See Also:
        https://okwave.jp/qa/q5568876.html 
        
    """
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


def get_filet_sita(sita_st, sita_ed):
    
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
        
        if (p2p_dist > DIST_FILET) and (p2p_dist < l0_offset *2) and (p2p_dist < l1_offset *2) :
            
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
            cx, cy = get_cross_point_from_point(l0_x[0], l0_y[0], l1_x[0], l1_y[0], l0_x[1], l0_y[1], l1_x[1], l1_y[1])
            
            # 幾何より、l0延長線上のフィレット開始点（p1）および、フィレットの中心座標（p0）を求める
            p1_x = cx - r * (1/np.tan(sita)) * np.cos(-alpha)
            p1_y = cy + r * (1/np.tan(sita)) * np.sin(-alpha)
    
            p2_x = cx - r * (1/np.tan(sita)) * np.cos(-beta)
            p2_y = cy + r * (1/np.tan(sita)) * np.sin(-beta)
            
            m2_0 = np.tan(alpha + np.pi/2)
            m2_1 = np.tan(beta + np.pi/2)
            b0 = -m2_0*p1_x + p1_y
            b1 = -m2_1*p2_x + p2_y
            
            f_x, f_y = get_cross_point_from_lines(m2_0, b0, m2_1, b1)
    
            # 円弧の始点角と終点角を計算する。
            sita_st = float(np.arctan2(p1_y-f_y, p1_x-f_x))
            sita_ed = float(np.arctan2(p2_y-f_y, p2_x-f_x))
            sita_st, sita_ed = get_filet_sita(sita_st, sita_ed)
            
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
    x, y = remove_same_point(x, y)
    
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
                #cx, cy = get_cross_point_from_point(p1[0], p1[1], p3[0], p3[1], p2[0], p2[1], p4[0], p4[1])
                #new_x.append(cx)
                #new_y.append(cy)             
                i = j+1
            j += 1
        new_x.append(x[i])
        new_y.append(y[i])
        i += 1
        
    return np.array(new_x), np.array(new_y), detection


def remove_collision(x1, y1, x2, y2):
    # 前提：x1[-1] -> x2[0] と繋がる
    x1, y1 = remove_same_point(x1, y1)
    x2, y2 = remove_same_point(x2, y2)
    
    detection = False 
    num1 = 0
    num2 = 0
    cx = 0
    cy = 0
    
    i = 1
    while (i < len(x1)) and (detection==False):
        j = 1
        p1 = [x1[i-1], y1[i-1]]
        p2 = [x1[i], y1[i]]
        while (j < len(x2)) and (detection==False):
            p3 = [x2[j-1], y2[j-1]]
            p4 = [x2[j], y2[j]]
            if cross_judge(p1, p2, p3, p4) == True:
                detection = True
                num1 = i
                num2 = j 
                cx, cy = get_cross_point_from_point(p1[0], p1[1], p3[0], p3[1], p2[0], p2[1], p4[0], p4[1])         
            j += 1
        i += 1
        
    if detection == True:
        new_x1 = x1[:num1]
        new_y1 = y1[:num1]
        new_x2 = x2[num2:]
        new_y2 = y2[num2:]
        new_x1 = np.append(new_x1, cx)
        new_y1 = np.append(new_y1, cy)
        new_x2 = np.insert(new_x2, 0, cx)
        new_y2 = np.insert(new_y2, 0, cy)
        return new_x1, new_y1, new_x2, new_y2, detection
    else:
        return x1, y1, x2, y2, detection

def rotate(x, y, sita, rx, ry):
    A = np.array([[np.cos(sita), -np.sin(sita)],
                  [np.sin(sita), np.cos(sita)]])
    x = np.array(x) - rx
    y = np.array(y) - ry
    p = np.array([x, y])

    rot_p = np.dot(A, p)
    rot_x = rot_p[0] + rx
    rot_y = rot_p[1] + ry

    return rot_x, rot_y
    