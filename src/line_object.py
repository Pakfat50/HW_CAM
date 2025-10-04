# -*- coding: utf-8 -*-
"""LineObjectクラスを実装したパッケージ

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

class LineObject:
    """CAMで取り扱い線に関する情報を格納するクラスである。

    線（線分、スプライン）に対する操作は、本クラスを介して行う。
    
    Attributes:
        x_raw(numpy.array): オフセット適用前のx座標点列
        y_raw(numpy.array): オフセット適用前のy座標点列
        st(numpy.array): x_raw, y_rawの始点(0番目)の座標
        ed(numpy.array): x_raw, y_rawの終点(-1番目)の座標
        num(int): ラインの番号
        line_type(str): 線種(point/line/spline)
        offset_dist(float): オフセット距離
        ccw(bool): ラインが反時計回りかどうか(True:反時計回り/ False:時計周り)
        cutspeed_work(float): ワーク端面(ラインの座標面)でのカット速度
        cutspeed_mech(float): CNC駆動面(ラインの座標面からz軸方向にオフセットした面)でのカット速度
        x(numpy.array): オフセット適用後のx座標点列
        y(numpy.array): オフセット適用後のy座標点列
    
    """

    def __init__(self, x_points, y_points, num, is_refine, interp_mode = "cubic"):
        """LineObjectのコンストラクタ

        初期化処理を実行する。
        
        x座標点列x_points, y座標点列y_points　を、x_raw、y_rawおよびx, yに代入する。
        
        ライン名をnumに設定する。

        Args:
            x_points (numpy.array): x座標点列
            y_points (numpy.array): y座標点列
            num (int): ライン番号
            is_refine (bool): スプラインの場合、点列をリファインするかどうか。(True:リファインする/ False:リファインしない)
            interp_mode (str, optional): スプラインの場合、1次/3次補完のどちらとするか。("cubic":3d-spline, "linear":1d-line,) Defaults to "cubic".
        """

        self.interp_mode = interp_mode 

        # 点列の数から、線種を判定する
        if len(x_points)<2:
            self.line_type = "point"
        elif len(x_points)==2:
            self.line_type = "line"
        else: #len(x_points)>2
            self.line_type = "spline"
            # is_refine=Trueかつスプラインの場合、リファインする
            if (is_refine == True) and (self.interp_mode == "cubic"):
                # リファイン後の点列の数を線長から算出する
                length = get_spline_length(x_points, y_points)
                n_refine = int(length/DIST_REFINE_SPLINE)
                # 一定値未満とならないように下限設定
                if n_refine < N_REFINE_SPLINE_MIN:
                    n_refine = N_REFINE_SPLINE_MIN
                # リファイン後の点列でx,y座標を更新
                x_points, y_points = refine_spline_curvature(x_points, y_points, n_refine)              

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
        """座標データを更新する

        座標点列以外のデータは、設定済みのものを引き継ぐ。

        オフセットが設定されている場合は、入力された座標点列に対し、オフセットした座標点も計算する。

        Args:
            x_points (numpy.array): x座標点列
            y_points (numpy.array): y座標点列
        """

        # 座標点数が変更となるので、線種を再判定
        if len(x_points)<2:
            self.line_type = "point"
        elif len(x_points)==2:
            self.line_type = "line"
        else: # len(x_points)>2
            self.line_type = "spline"

        # 座標点列を更新。始点・終点も更新  
        self.x_raw = np.array(x_points)
        self.y_raw = np.array(y_points)
        self.st = np.array([x_points[0], y_points[0]])
        self.ed = np.array([x_points[-1], y_points[-1]])
        # オフセット距離が設定されている場合に備え、オフセット後の点列も再計算
        self.set_offset_dist(self.offset_dist)
        
    
    def move_origin(self, dx, dy):
        """座標点を指定の距離(dx,dy)だけすべてオフセットする

        線が持つ座標データ（x_raw, y_raw, st, ed, x, y）をすべて、指定の距離だけ移動する。

        原点の移動に相当する。

        Args:
            dx (float): x方向移動距離
            dy (float): y方向移動距離
        """
        self.x_raw = self.x_raw + dx
        self.y_raw = self.y_raw + dy
        self.x = self.x + dx
        self.y = self.y + dy
        self.st[0] = self.st[0] + dx
        self.ed[0] = self.ed[0] + dx
        self.st[1] = self.st[1] + dy
        self.ed[1] = self.ed[1] + dy
        
        
    def rotate(self, d_sita, rx, ry):
        """座標点を指定の座標(rx,ry)を中心に、指定の角度(d_sita)だけ回転する。

        線が持つ座標データ（x_raw, y_raw, st, ed, x, y）をすべて、指定の距離だけ回転する。
        
        Args:
            d_sita (float): 回転角度。正で時計回り、負で反時計周りに回転
            rx (float): 回転中心x座標
            ry (float): 回転中心y座標
        """

        self.x_raw, self.y_raw = rotate(self.x_raw, self.y_raw, d_sita, rx, ry)
        self.x, self.y = rotate(self.x, self.y, d_sita, rx, ry)
        self.st[0], self.st[1] = rotate(self.st[0], self.st[1], d_sita, rx, ry)
        self.ed[0], self.ed[1] = rotate(self.ed[0], self.ed[1], d_sita, rx, ry)
    
    
    def set_ccw(self, ccw):
        """線に回転方向を設定する

        回転方向が変更となった場合、オフセット方向も変更となるので、オフセットした座標点も更新する。

        Args:
            ccw (bool): ラインが反時計回りかどうか(True:反時計回り/ False:時計周り)
        """

        # 回転方向が変わる場合、オフセット後の座標点も更新する
        if not(self.ccw == ccw):
            self.ccw = ccw
            self.set_offset_dist(self.offset_dist)
        
        
    def set_offset_dist(self, offset_dist):
        """オフセット後の座標点を更新する

        オフセットする方向は、線が時計回りか反時計周りかで変更する。

        オフセット方向は、必ず閉曲線の外側向きにオフセットする。

        以下であれば、外向きにオフセットされる。

        ・閉曲線が反時計回り(ccw=True)のとき、接線を-90度回転させる方向

        ・閉曲線が時計回り(ccw=False)のとき、接線を90度回転させる方向

        オフセット座標点の計算は、時計回りを基準（90度回転）であるので、ccw=Trueのときはオフセット距離を負として計算する。

        Args:
            offset_dist (float): オフセット距離

        Note:
            float以外のデータが渡された場合、例外を発生させる。

            例外は、標準出力へ表示した上で、output_logによりエラーファイルにも出力する。

        """
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
        """オフセット後の座標点列に自己交差がある場合、除去する

        Returns:
            bool: 自己交差の有無(True:自己交差あり, False:自己交差なし)
        """
        self_col = True
        detection = False
        temp_x = self.x
        temp_y = self.y

       # 自己交差を1度で除去できない場合があるので、自己交差がなくなるまで繰り返し処理を行う
        while self_col == True:
            temp_x, temp_y, self_col = remove_self_collision(temp_x, temp_y)
            if self_col == True:
                detection = True
    
        self.x = temp_x
        self.y = temp_y
        return detection
        
    
        
    def set_cutspeed(self, cutspeed_work, cutspeed_mech):
        """カット速度を設定する

        Args:
            cutspeed_work (float): ワーク端面(ラインの座標面)でのカット速度
            cutspeed_mech (float): CNC駆動面(ラインの座標面からz軸方向にオフセットした面)でのカット速度
        """
        self.cutspeed_work = cutspeed_work
        self.cutspeed_mech = cutspeed_mech
        
        
    def set_num(self, num):
        """ライン番号を設定する

        Args:
            num (int): ラインの番号

        Note:
            int以外のデータが渡された場合、例外を発生させる。

            例外は、標準出力へ表示した上で、output_logによりエラーファイルにも出力する。

        """
        try:
            self.num = int(num)
        except:
            traceback.print_exc()
            output_log(traceback.format_exc())
            pass

    def toggle_cut_dir(self):
        """カット方向(座標点列の向き)を反転させる

        線が持つ座標データ（x_raw, y_raw, x, y）をすべて反転させる。

        始点、終点は、入れ替わるため座標点を入れ替える。

        回転方向は、点列の反転に併せて反転するので、回転方向もトグルする。

        """

        #座標データの反転
        self.x_raw = self.x_raw[::-1]
        self.y_raw = self.y_raw[::-1]
        self.x = self.x[::-1]
        self.y = self.y[::-1]
        #始点・終点座標の入れ替え
        self.st, self.ed = self.ed, self.st
        #回転方向のトグル
        if self.ccw == True:
            ccw = False
        else:
            ccw = True
        self.ccw = ccw
        
        
    def calc_length_array(self, mode = "offset"):
        """始点からi番目の座標点までの線長を計算した配列を出力する

        Args:
            mode (str, optional): 元の座標データとオフセット後の座標データのどちらで線長を計算するか. Defaults to "offset".

        Returns:
            np.array: 始点からi番目の座標点までの線長を計算した配列
        """
        length_array = [0]
        
        # オフセット前の座標点に対して計算
        if mode == "raw":
            x = self.x_raw
            y = self.y_raw
        # オフセット後の座標点に対して計算
        else:
            x = self.x
            y = self.y           
            
        # 点の場合、線長はゼロ
        if self.line_type == "point":
            length_array = [0]
        
        # 線の場合、始点と終点のnormが線長
        if self.line_type == "line":
            dl = np.sqrt((x[0]-x[1])**2 + (y[0]-y[1])**2)
            length_array.append(dl)
        
        # スプラインの場合、ライブラリの関数を用いて計算
        if self.line_type == "spline":
            length_array = get_spline_length_array(x, y)
            
        return np.array(length_array)
    
    
    def get_length(self, mode = "offset"):
        """始点から終点までの線長を計算する

        Args:
            mode (str, optional): 元の座標データとオフセット後の座標データのどちらで線長を計算するか. Defaults to "offset".

        Returns:
            float: 始点から終点までの線長
        """
        
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

