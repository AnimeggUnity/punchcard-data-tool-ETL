"""
ETL 管道 - 整合資料讀取、驗證、轉換和載入
"""

from typing import List, Callable, Optional, Dict, Any
import pandas as pd
import sqlite3
from pathlib import Path
import logging
from datetime import datetime

from .models import PunchRecord, ShiftClass, ValidationResult
from .readers import DataReader
from .validators import DataValidator

logger = logging.getLogger(__name__)


class ETLPipeline:
    """通用 ETL 管道"""
    
    def __init__(self, reader: DataReader, validator: Optional[DataValidator] = None,
                 output_callback: Callable = None):
        self.reader = reader
        self.validator = validator
        self.output_callback = output_callback or (lambda x: logger.info(x))
        
        self.extracted_data: Optional[pd.DataFrame] = None
        self.valid_records: List = []
        self.validation_result: Optional[ValidationResult] = None
    
    def extract(self) -> pd.DataFrame:
        self.output_callback("=" * 50)
        self.output_callback("階段 1: 提取資料")
        self.output_callback("=" * 50)
        self.extracted_data = self.reader.read()
        self.output_callback(f"提取完成，共 {len(self.extracted_data)} 筆")
        return self.extracted_data
    
    def validate(self, df: pd.DataFrame = None) -> tuple:
        self.output_callback("=" * 50)
        self.output_callback("階段 2: 驗證資料")
        self.output_callback("=" * 50)
        
        df = df if df is not None else self.extracted_data
        if df is None:
            raise ValueError("尚未提取資料")
        
        if self.validator is None:
            self.valid_records = df.to_dict('records')
            self.validation_result = ValidationResult(success=True, valid_count=len(df))
        else:
            self.valid_records, self.validation_result = self.validator.validate(df, self.output_callback)
        
        return self.valid_records, self.validation_result
    
    def load_to_sqlite(self, db_path: str, table_name: str, if_exists: str = 'replace') -> int:
        self.output_callback("=" * 50)
        self.output_callback("階段 3: 載入資料")
        self.output_callback("=" * 50)
        
        if not self.valid_records:
            self.output_callback("沒有資料可載入")
            return 0
        
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        df = pd.DataFrame([
            r.model_dump() if hasattr(r, 'model_dump') else r
            for r in self.valid_records
        ])
        
        conn = sqlite3.connect(db_path)
        df.to_sql(table_name, conn, if_exists=if_exists, index=False)
        conn.close()
        
        self.output_callback(f"載入完成，{len(df)} 筆至 {table_name}")
        return len(df)
    
    def execute(self, db_path: str, table_name: str, if_exists: str = 'replace') -> Dict[str, Any]:
        start = datetime.now()
        try:
            self.extract()
            self.validate()
            loaded = self.load_to_sqlite(db_path, table_name, if_exists)
            duration = (datetime.now() - start).total_seconds()
            
            self.output_callback("=" * 50)
            self.output_callback(f"ETL 完成，耗時 {duration:.2f} 秒")
            
            return {
                'success': True,
                'extracted': len(self.extracted_data) if self.extracted_data is not None else 0,
                'valid': len(self.valid_records),
                'errors': self.validation_result.error_count if self.validation_result else 0,
                'loaded': loaded,
                'duration': duration
            }
        except Exception as e:
            self.output_callback(f"ETL 失敗: {e}")
            return {'success': False, 'error': str(e)}


class PunchDataETL:
    """打卡資料專用 ETL - 正確的 Extract → Transform → Validate → Load 流程"""
    
    def __init__(self, punch_reader: DataReader, shift_reader: DataReader, output_callback: Callable = None):
        self.punch_reader = punch_reader
        self.shift_reader = shift_reader
        self.output_callback = output_callback or (lambda x: logger.info(x))
    
    def execute(self, db_path: str) -> Dict[str, Any]:
        self.output_callback("開始處理打卡資料...")
        start = datetime.now()
        
        try:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # === 處理打卡資料（與 main_app.py 相同邏輯）===
            self.output_callback("=" * 50)
            self.output_callback("處理打卡資料")
            self.output_callback("=" * 50)
            
            punch_df = self._read_punch_data()
            if punch_df.empty:
                return {'success': False, 'error': '沒有打卡資料'}
            
            self.output_callback(f"欄位: {list(punch_df.columns)}")
            self.output_callback(f"前3筆資料範例:")
            for i, row in punch_df.head(3).iterrows():
                self.output_callback(f"  {i}: 帳號={row.get('公務帳號', 'N/A')}, 日期={row.get('刷卡日期', 'N/A')}, 時間={row.get('刷卡時間', 'N/A')}")
            
            # 轉換格式
            punch_df = self._transform_punch_data(punch_df)
            
            # 嘗試 Pydantic 驗證（可選）
            try:
                punch_validator = DataValidator(PunchRecord)
                valid_punch, punch_result = punch_validator.validate(punch_df, self.output_callback)
                self.output_callback(f"Pydantic 驗證: {punch_result.valid_count} 成功, {punch_result.error_count} 失敗")
            except Exception as ve:
                self.output_callback(f"Pydantic 驗證跳過: {ve}")
            
            # 直接載入（與原始程式相同）
            conn = sqlite3.connect(db_path)
            punch_df.to_sql('punch', conn, if_exists='replace', index=False)
            conn.close()
            punch_loaded = len(punch_df)
            self.output_callback(f"載入完成，{punch_loaded} 筆至 punch")
            
            # === 處理班別資料 ===
            self.output_callback("=" * 50)
            self.output_callback("處理班別資料")
            self.output_callback("=" * 50)
            
            shift_df = self.shift_reader.read()
            self.output_callback(f"欄位: {list(shift_df.columns)}")
            
            conn = sqlite3.connect(db_path)
            shift_df.to_sql('shift_class', conn, if_exists='replace', index=False)
            conn.close()
            shift_loaded = len(shift_df)
            self.output_callback(f"載入完成，{shift_loaded} 筆至 shift_class")
            
            # === 整合資料 ===
            integrated = self._integrate_data(db_path)
            
            duration = (datetime.now() - start).total_seconds()
            self.output_callback("=" * 50)
            self.output_callback(f"ETL 完成，耗時 {duration:.2f} 秒")
            
            return {
                'success': True,
                'punch_records': punch_loaded,
                'shift_records': shift_loaded,
                'integrated_records': integrated,
                'total_duration': duration
            }
        except Exception as e:
            import traceback
            self.output_callback(f"處理失敗: {traceback.format_exc()}")
            return {'success': False, 'error': str(e)}
    
    def _read_punch_data(self) -> pd.DataFrame:
        """
        讀取打卡資料 - 使用 ExcelReadingConfig 設定
        
        未來格式變更只需修改 config.py 中的 ExcelReadingConfig.PUNCH_DATA
        """
        from config import ExcelReadingConfig
        config = ExcelReadingConfig.PUNCH_DATA
        
        source_info = self.punch_reader.get_source_info()
        file_path = source_info.get('file', '')
        
        self.output_callback(f"讀取打卡資料: {file_path}")
        self.output_callback(f"設定: skip_rows={config['skip_rows']}, filter={config['filter_column']}")
        excel_file = pd.ExcelFile(file_path)
        
        dfs = []
        for sheet_name in excel_file.sheet_names:
            self.output_callback(f"  處理工作表: {sheet_name}")
            
            # 使用設定檔的 skip_rows 和 header_row
            df = pd.read_excel(
                excel_file, 
                sheet_name=sheet_name, 
                skiprows=config['skip_rows'], 
                header=config['header_row']
            )
            
            # 移除空白欄位
            if config.get('remove_unnamed_columns', True):
                df = df.loc[:, ~df.columns.str.contains('^Unnamed', na=False)]
                df = df.loc[:, df.columns.notna()]
            
            self.output_callback(f"    讀取後欄位: {list(df.columns)[:6]}")
            
            if df.empty:
                continue
            
            # 使用設定檔的過濾欄位
            filter_col = config.get('filter_column')
            if filter_col and filter_col in df.columns:
                before_count = len(df)
                df = df[pd.to_numeric(df[filter_col], errors='coerce').notnull()]
                after_count = len(df)
                self.output_callback(f"    {filter_col}過濾: {before_count} -> {after_count} 筆")
            
            # 欄位重新命名（如果有設定）
            column_mapping = config.get('column_mapping', {})
            if column_mapping:
                df = df.rename(columns=column_mapping)
            
            df = df.dropna(axis=1, how='all')
            
            # 確保指定欄位為字串
            for col in config.get('string_columns', []):
                if col in df.columns:
                    df[col] = df[col].astype(str)
            
            if not df.empty:
                dfs.append(df)
                self.output_callback(f"    {sheet_name}: {len(df)} 筆有效資料")
        
        result = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
        self.output_callback(f"共讀取 {len(result)} 筆打卡資料")
        return result
    
    def _transform_punch_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """轉換打卡資料格式 - 在驗證前進行"""
        self.output_callback("轉換日期時間格式...")
        
        df = df.copy()
        
        # 轉換日期：民國年 (YYYMMDD) → 西元年 (YYYY-MM-DD)
        if '刷卡日期' in df.columns:
            def convert_date(val):
                if pd.isna(val):
                    return val
                val = str(val).strip()
                if len(val) == 7 and val.isdigit():
                    year = int(val[:3]) + 1911
                    return f"{year}-{val[3:5]}-{val[5:7]}"
                return val
            df['刷卡日期'] = df['刷卡日期'].apply(convert_date)
        
        # 轉換時間：HHMM → HH:MM:SS
        if '刷卡時間' in df.columns:
            def convert_time(val):
                if pd.isna(val):
                    return val
                val = str(val).strip()
                if len(val) == 4 and val.isdigit():
                    return f"{val[:2]}:{val[2:4]}:00"
                return val
            df['刷卡時間'] = df['刷卡時間'].apply(convert_time)
        
        self.output_callback("格式轉換完成")
        return df
    
    def _load_records(self, records: List, db_path: str, table_name: str, if_exists: str) -> int:
        """載入記錄到資料庫"""
        if not records:
            self.output_callback(f"沒有資料可載入到 {table_name}")
            return 0
        
        df = pd.DataFrame([
            r.model_dump() if hasattr(r, 'model_dump') else r
            for r in records
        ])
        
        conn = sqlite3.connect(db_path)
        df.to_sql(table_name, conn, if_exists=if_exists, index=False)
        conn.close()
        
        self.output_callback(f"載入完成，{len(df)} 筆至 {table_name}")
        return len(df)
    
    def _integrate_data(self, db_path: str) -> int:
        """整合打卡與班別資料"""
        self.output_callback("整合打卡與班別資料...")
        
        conn = sqlite3.connect(db_path)
        query = """
            SELECT p.公務帳號, s.卡號, s.姓名, s.班別, p.刷卡日期,
                   GROUP_CONCAT(p.刷卡時間) AS 刷卡時間列表
            FROM punch p
            LEFT JOIN shift_class s ON p.公務帳號 = s.公務帳號
            GROUP BY p.公務帳號, p.刷卡日期, s.班別
            ORDER BY p.公務帳號, p.刷卡日期
        """
        df = pd.read_sql_query(query, conn)
        
        # 分割時間
        if not df.empty and '刷卡時間列表' in df.columns:
            split_times = df['刷卡時間列表'].str.split(',', expand=True)
            if split_times.shape[1] > 0:
                time_cols = [f'刷卡時間{i+1}' for i in range(split_times.shape[1])]
                new_cols = pd.DataFrame(split_times.values, columns=time_cols).dropna(axis=1, how='all')
                df = pd.concat([df.drop(columns=['刷卡時間列表']), new_cols], axis=1)
        
        df.to_sql('integrated_punch', conn, if_exists='replace', index=False)
        conn.close()
        
        self.output_callback(f"整合完成，{len(df)} 筆")
        return len(df)


