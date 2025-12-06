"""
司機名單服務
"""

import pandas as pd
from pathlib import Path
from typing import Set, Callable
import logging

logger = logging.getLogger(__name__)


class DriverListService:
    """司機名單管理服務"""
    
    _cache: Set[str] = None
    _cache_path: str = None
    
    @classmethod
    def load_driver_list(cls, list_path: str, output_callback: Callable = None) -> Set[str]:
        """載入司機名單"""
        output_callback = output_callback or (lambda x: None)
        
        # 快取檢查
        if cls._cache is not None and cls._cache_path == list_path:
            output_callback(f"使用快取的司機名單，共 {len(cls._cache)} 筆")
            return cls._cache
        
        try:
            output_callback(f"正在讀取司機名單: {list_path}")
            
            if not Path(list_path).exists():
                output_callback(f"司機名單不存在: {list_path}，使用空清單")
                cls._cache = set()
                cls._cache_path = list_path
                return cls._cache
            
            df = pd.read_csv(list_path)
            
            if '公務帳號' not in df.columns:
                output_callback("司機名單缺少「公務帳號」欄位")
                cls._cache = set()
                cls._cache_path = list_path
                return cls._cache
            
            cls._cache = set(df['公務帳號'].dropna())
            cls._cache_path = list_path
            output_callback(f"已讀取司機名單，共 {len(cls._cache)} 筆")
            
            return cls._cache
            
        except Exception as e:
            output_callback(f"讀取司機名單錯誤: {e}")
            cls._cache = set()
            cls._cache_path = list_path
            return cls._cache
    
    @classmethod
    def clear_cache(cls):
        """清除快取"""
        cls._cache = None
        cls._cache_path = None
    
    @classmethod
    def is_driver(cls, account: str) -> bool:
        """檢查是否為司機"""
        if cls._cache is None:
            return False
        return account in cls._cache
