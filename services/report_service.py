"""
報表生成服務 - 生成各種 HTML 報表

此服務採用門面模式（Facade Pattern），將報表生成委派給專門的報表生成器。
各個報表生成器位於 reports/ 子模組中。
"""

from typing import Callable, Set
import pandas as pd

from config import PathManager
from .reports import (
    DailyPunchReport,
    FullPunchReport,
    NightMealReport,
    PrintableDailyReport,
    PrintableFullReport
)


class ReportService:
    """報表生成服務（門面）"""
    
    def __init__(self, output_callback: Callable = None):
        """
        初始化報表服務
        
        Args:
            output_callback: 輸出訊息的回調函數
        """
        self.output_callback = output_callback or (lambda x: None)
        self.path_mgr = PathManager()
        
        # 初始化各個報表生成器
        self.daily_punch = DailyPunchReport(self.output_callback, self.path_mgr)
        self.full_punch = FullPunchReport(self.output_callback, self.path_mgr)
        self.night_meal = NightMealReport(self.output_callback, self.path_mgr)
        self.printable_daily = PrintableDailyReport(self.output_callback, self.path_mgr)
        self.printable_full = PrintableFullReport(self.output_callback, self.path_mgr)
    
    def generate_daily_punch_report(self, df: pd.DataFrame, date_str: str, driver_accounts: Set[str]) -> str:
        """
        生成單日打卡報表
        
        Args:
            df: 打卡資料 DataFrame
            date_str: 日期字串
            driver_accounts: 司機帳號集合
            
        Returns:
            生成的報表檔案路徑
        """
        return self.daily_punch.generate(df, date_str, driver_accounts)
    
    def generate_full_punch_report(self, df: pd.DataFrame, driver_accounts: Set[str]) -> str:
        """
        生成完整打卡報表
        
        Args:
            df: 打卡資料 DataFrame
            driver_accounts: 司機帳號集合
            
        Returns:
            生成的報表檔案路徑
        """
        return self.full_punch.generate(df, driver_accounts)
    
    def generate_night_meal_report(self, df: pd.DataFrame, driver_accounts: Set[str]) -> str:
        """
        生成夜點津貼報表
        
        Args:
            df: 打卡資料 DataFrame
            driver_accounts: 司機帳號集合
            
        Returns:
            生成的報表檔案路徑
        """
        return self.night_meal.generate(df, driver_accounts)
    
    def generate_printable_daily_report(self, df: pd.DataFrame, date_str: str, driver_accounts: Set[str]) -> str:
        """
        生成列印版單日報表
        
        Args:
            df: 打卡資料 DataFrame
            date_str: 日期字串
            driver_accounts: 司機帳號集合
            
        Returns:
            生成的報表檔案路徑
        """
        return self.printable_daily.generate(df, date_str, driver_accounts)
    
    def generate_printable_full_report(self, df: pd.DataFrame, driver_accounts: Set[str]) -> str:
        """
        生成列印版完整報表
        
        Args:
            df: 打卡資料 DataFrame
            driver_accounts: 司機帳號集合
            
        Returns:
            生成的報表檔案路徑
        """
        return self.printable_full.generate(df, driver_accounts)
