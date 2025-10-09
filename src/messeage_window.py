# -*- coding: utf-8 -*-
"""メッセージ出力に関連するライブラリ

"""

# 外部ライブラリ
import tkinter as tk

# 内部ライブラリ
from cam_global import *


class MesseageWindow(tk.Text):
    """メッセージ出力用のクラス

    Attributes:
        root(tkinter.Frame): textウィンドウを配置するフレーム
        width(int): textウィンドウの幅（文字数で指定）
        height(int): textウィンドウの高さ（文字列数で指定）

    Args:
        tk (tkinter.Text): メッセージ出力先のtkinter.Textクラス

    """
    def __init__(self, root, width, height):
        """メッセージウィンドウのコンストラクタ

        Args:
            root(tkinter.Frame): textウィンドウを配置するフレーム
            width(int): textウィンドウの幅（文字数で指定）
            height(int): textウィンドウの高さ（文字列数で指定）

        """
        self.width = width
        self.height = height
        super().__init__(root, width = self.width, height = self.height)
    
    def set_messeage(self, messeage):
        """指定の文字列をメッセージウィンドウの最下行に出力する。

        文字列を挿入後に、最下列を表示する。

        Args:
            messeage (str): メッセージウィンドウに出力する文字列
        """
        self.insert("end", messeage)
        self.see(self.index('end'))

