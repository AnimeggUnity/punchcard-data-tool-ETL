"""
基礎報表類別 - 提供報表生成的共用功能
"""

import os
import webbrowser
from typing import Callable
from abc import ABC, abstractmethod

from config import PathManager


class BaseReport(ABC):
    """報表生成基礎類別"""
    
    def __init__(self, output_callback: Callable, path_mgr: PathManager):
        """
        初始化報表生成器
        
        Args:
            output_callback: 輸出訊息的回調函數
            path_mgr: 路徑管理器
        """
        self.output_callback = output_callback
        self.path_mgr = path_mgr
    
    @abstractmethod
    def generate(self, *args, **kwargs) -> str:
        """
        生成報表（抽象方法，由子類別實作）
        
        Returns:
            生成的報表檔案路徑
        """
        pass
    
    def _auto_open(self, file_path: str):
        """
        自動開啟 HTML 檔案
        
        Args:
            file_path: 要開啟的檔案路徑
        """
        try:
            if os.path.exists(file_path):
                webbrowser.open(f'file:///{os.path.abspath(file_path)}')
                self.output_callback(f"📊 已在瀏覽器中開啟報表")
        except Exception as e:
            self.output_callback(f"開啟檔案失敗: {e}")
