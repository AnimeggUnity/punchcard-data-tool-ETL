"""
應用程式配置 - 集中管理所有配置常數

未來格式變更只需修改此檔案，不需要修改程式碼！
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional


def get_app_base_dir():
    """取得應用程式基礎目錄"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


class ExcelReadingConfig:
    """
    Excel 讀取配置類別
    
    未來格式變更時，只需修改這裡的設定！
    """
    
    # ========== 打卡資料 Excel 配置 ==========
    PUNCH_DATA = {
        # 跳過的行數（0-indexed，跳過前5行表示第6行是標題）
        'skip_rows': 5,
        
        # 標題行（相對於 skip_rows 後的位置，0 表示第一行）
        'header_row': 0,
        
        # 要移除的欄位前綴（如 'Unnamed' 開頭的空白欄位）
        'remove_unnamed_columns': True,
        
        # 用於過濾有效資料的欄位（只保留此欄位為數字的行）
        'filter_column': '序號',
        
        # 必要欄位（驗證時會檢查這些欄位是否存在）
        'required_columns': ['公務帳號', '刷卡日期', '刷卡時間'],
        
        # 欄位對應（Excel 欄位名稱 -> 資料模型欄位名稱）
        # 如果 Excel 欄位名稱與模型相同，可以省略
        'column_mapping': {
            # '人員姓名': '姓名',  # 範例：如果需要重新命名
        },
        
        # 日期欄位（需要轉換格式的欄位）
        'date_columns': ['刷卡日期'],
        
        # 時間欄位（需要轉換格式的欄位）
        'time_columns': ['刷卡時間'],
        
        # 轉為字串的欄位
        'string_columns': ['刷卡日期', '刷卡時間'],
    }
    
    # ========== 班別資料 Excel 配置 ==========
    SHIFT_DATA = {
        'skip_rows': 0,
        'header_row': 0,
        'remove_unnamed_columns': True,
        'filter_column': None,  # 不需要過濾
        'required_columns': ['公務帳號', '班別'],
        'column_mapping': {},
    }


class AppConfig:
    """應用程式配置類別"""
    
    # 路徑配置
    DB_PATH = 'db/source.db'
    PUNCH_DATA_PATH = 'data/刷卡資料.xlsx'
    SHIFT_CLASS_PATH = 'data/list.xlsx'
    LEAVE_DATA_PATH = 'data/work.xlsx'  # 請假資料（支援 .xls 或 .xlsx）
    OUTPUT_DIR = 'output/'
    DRIVER_LIST_PATH = 'data/司機名單.csv'
    
    # Excel 讀取配置（向後相容，建議使用 ExcelReadingConfig）
    PUNCH_DATA_SKIP_ROWS = ExcelReadingConfig.PUNCH_DATA['skip_rows']
    PUNCH_DATA_HEADER_ROW = ExcelReadingConfig.PUNCH_DATA['header_row']
    
    # 夜點時間門檻值
    NIGHT_MEAL_THRESHOLD = '21:00:00'
    
    # GUI 配置
    GUI_THEME = 'LightGreen'
    GUI_VERSION = 'v2.0 - ETL 重構版'
    
    # 日期格式配置
    DATE_FORMAT = '%Y-%m-%d'
    TIME_FORMAT = '%H:%M:%S'
    DISPLAY_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # 民國年偏移量
    TAIWAN_YEAR_OFFSET = 1911


class ColumnNaming:
    """
    欄位名稱標準化配置

    原則：
    - 資料庫統一用英文小寫 + 底線（snake_case）
    - Excel 原始欄位名保持不變
    - ETL 階段自動轉換
    """

    # 打卡資料欄位對照
    PUNCH_COLUMNS = {
        '序號': 'seq_no',
        '卡號': 'emp_id',
        '公務帳號': 'account_id',
        '身分證字號': 'id_number',
        '人員姓名': 'name',
        '刷卡日期': 'punch_date',
        '刷卡時間': 'punch_time',
        '門禁名稱': 'gate_name',
        '進出狀態': 'direction',
    }

    # 班別資料欄位對照
    SHIFT_COLUMNS = {
        '班別': 'shift_class',
        '卡號': 'emp_id',
        '姓名': 'name',
        '公務帳號': 'account_id',
        '班次ID': 'shift_id',
    }

    # 司機名單欄位對照
    DRIVER_COLUMNS = {
        '公務帳號': 'account_id',
        '卡號': 'emp_id',
        '姓名': 'name',
    }


class PathManager:
    """路徑管理類別"""

    def __init__(self):
        self.app_base_dir = get_app_base_dir()
    
    def get_db_path(self) -> str:
        """取得資料庫路徑"""
        return os.path.join(self.app_base_dir, AppConfig.DB_PATH)
    
    def get_punch_data_path(self) -> str:
        """取得打卡資料路徑"""
        return os.path.join(self.app_base_dir, AppConfig.PUNCH_DATA_PATH)
    
    def get_shift_class_path(self) -> str:
        """取得班別資料路徑"""
        return os.path.join(self.app_base_dir, AppConfig.SHIFT_CLASS_PATH)
    
    def get_driver_list_path(self) -> str:
        """取得司機名單路徑"""
        return os.path.join(self.app_base_dir, AppConfig.DRIVER_LIST_PATH)

    def get_leave_data_path(self) -> str:
        """取得請假資料路徑（自動檢測 .xlsx 或 .xls）"""
        base_path = os.path.join(self.app_base_dir, AppConfig.LEAVE_DATA_PATH)

        # 自動檢測 .xlsx 或 .xls
        if os.path.exists(base_path):
            return base_path
        elif os.path.exists(base_path.replace('.xlsx', '.xls')):
            return base_path.replace('.xlsx', '.xls')
        elif os.path.exists(base_path.replace('.xls', '.xlsx')):
            return base_path.replace('.xls', '.xlsx')
        else:
            return base_path  # 回傳預設路徑，讓呼叫者處理檔案不存在的情況

    def get_output_dir(self) -> str:
        """取得輸出目錄並確保其存在"""
        output_dir = os.path.join(self.app_base_dir, AppConfig.OUTPUT_DIR)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    def ensure_db_dir(self) -> str:
        """確保資料庫目錄存在並返回路徑"""
        db_path = self.get_db_path()
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        return db_path

