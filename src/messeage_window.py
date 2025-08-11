# -*- coding: utf-8 -*-
"""
Created on Mon Aug 11 15:46:13 2025

@author: hirar
"""
# 外部ライブラリ
import tkinter as tk

# 内部ライブラリ
from cam_global import *

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
