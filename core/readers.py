"""
資料讀取器 - 支援多種資料來源
"""

from typing import Protocol, List, Dict, Any, Optional
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DataReader(Protocol):
    """資料讀取器介面"""
    def read(self) -> pd.DataFrame: ...
    def get_source_info(self) -> Dict[str, Any]: ...


class ExcelReader:
    """Excel 檔案讀取器"""
    
    def __init__(
        self,
        file_path: str,
        skip_rows: int = 0,
        sheet_names: Optional[List[str]] = None,
        use_header_row: bool = True,
        header_row_index: int = 0
    ):
        self.file_path = Path(file_path)
        self.skip_rows = skip_rows
        self.sheet_names = sheet_names
        self.use_header_row = use_header_row
        self.header_row_index = header_row_index
        
        if not self.file_path.exists():
            raise FileNotFoundError(f"Excel 檔案不存在: {file_path}")
    
    def read(self) -> pd.DataFrame:
        print(f"正在讀取 Excel: {self.file_path}")
        excel_file = pd.ExcelFile(self.file_path)
        sheets = self.sheet_names or excel_file.sheet_names
        print(f"工作表: {sheets}, skip_rows={self.skip_rows}")
        
        dfs = []
        for sheet in sheets:
            if self.skip_rows > 0 and self.use_header_row:
                # 需要跳過行並手動設置標題（打卡資料的情況）
                df = pd.read_excel(excel_file, sheet_name=sheet, skiprows=self.skip_rows, header=None)
                print(f"  {sheet} 原始欄位: {list(df.columns)[:5]}...")
                
                if not df.empty:
                    # 使用第一行作為標題
                    df.columns = df.iloc[0]
                    df = df.drop(0).reset_index(drop=True)
                    df = df.loc[:, df.columns.notna()]
                    print(f"  {sheet} 處理後欄位: {list(df.columns)[:5]}...")
                    
                    # 過濾有效資料（檢查序號欄位）
                    if '序號' in df.columns:
                        df = df[pd.to_numeric(df['序號'], errors='coerce').notnull()]
            else:
                # 直接讀取，讓 pandas 自動處理標題（班別資料的情況）
                df = pd.read_excel(excel_file, sheet_name=sheet)
                print(f"  {sheet} 欄位: {list(df.columns)[:5]}...")
            
            df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
            
            if not df.empty:
                dfs.append(df)
                print(f"  {sheet}: {len(df)} 筆有效資料")
        
        result = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
        print(f"共讀取 {len(result)} 筆，欄位: {list(result.columns)}")
        return result
    
    def get_source_info(self) -> Dict[str, Any]:
        return {'type': 'excel', 'file': str(self.file_path)}


class CSVReader:
    """CSV 檔案讀取器"""
    
    def __init__(self, file_path: str, encoding: str = 'utf-8', delimiter: str = ','):
        self.file_path = Path(file_path)
        self.encoding = encoding
        self.delimiter = delimiter
        if not self.file_path.exists():
            raise FileNotFoundError(f"CSV 檔案不存在: {file_path}")
    
    def read(self) -> pd.DataFrame:
        logger.info(f"正在讀取 CSV: {self.file_path}")
        df = pd.read_csv(self.file_path, encoding=self.encoding, delimiter=self.delimiter)
        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
        return df
    
    def get_source_info(self) -> Dict[str, Any]:
        return {'type': 'csv', 'file': str(self.file_path)}


class DataFrameReader:
    """DataFrame 讀取器"""
    
    def __init__(self, dataframe: pd.DataFrame, source_name: str = "memory"):
        self.dataframe = dataframe.copy()
        self.source_name = source_name
    
    def read(self) -> pd.DataFrame:
        return self.dataframe.copy()
    
    def get_source_info(self) -> Dict[str, Any]:
        return {'type': 'dataframe', 'name': self.source_name}


class SQLReader:
    """SQL 資料庫讀取器"""
    
    def __init__(self, connection_string: str, query: str, params: Dict = None):
        self.connection_string = connection_string
        self.query = query
        self.params = params or {}
    
    def read(self) -> pd.DataFrame:
        import sqlite3
        conn = sqlite3.connect(self.connection_string)
        df = pd.read_sql_query(self.query, conn, params=self.params)
        conn.close()
        return df
    
    def get_source_info(self) -> Dict[str, Any]:
        return {'type': 'sql', 'connection': self.connection_string}


class MultiSourceReader:
    """多資料來源讀取器"""
    
    def __init__(self, readers: List[DataReader], merge_strategy: str = 'concat'):
        self.readers = readers
        self.merge_strategy = merge_strategy
    
    def read(self) -> pd.DataFrame:
        dfs = [r.read() for r in self.readers]
        if self.merge_strategy == 'concat':
            return pd.concat(dfs, ignore_index=True)
        return dfs[0] if dfs else pd.DataFrame()
    
    def get_source_info(self) -> Dict[str, Any]:
        return {'type': 'multi', 'sources': [r.get_source_info() for r in self.readers]}
