"""
資料處理服務 - 整合 ETL 管道和業務邏輯
"""

import os
import sqlite3
import traceback
import pandas as pd
from pathlib import Path
from typing import Callable, Dict, List, Any
from datetime import datetime, time

from config import AppConfig, PathManager
from core import ExcelReader, CSVReader, PunchDataETL


class DatabaseManager:
    """資料庫管理器"""
    
    def __init__(self, db_path: str, output_callback: Callable = None):
        self.db_path = db_path
        self.output_callback = output_callback or (lambda x: None)
    
    def get_connection(self):
        """取得資料庫連線"""
        return sqlite3.connect(self.db_path)
    
    def get_time_columns(self) -> List[str]:
        """取得時間欄位列表"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(integrated_punch)")
            columns = cursor.fetchall()
            conn.close()
            return [col[1] for col in columns if col[1].startswith('punch_time')]
        except:
            return []


class TimeProcessor:
    """時間處理工具"""
    
    @staticmethod
    def parse_time(time_str: str) -> time:
        if pd.isna(time_str):
            return None
        return datetime.strptime(time_str, AppConfig.TIME_FORMAT).time()
    
    @staticmethod
    def format_timestamp(ts) -> str:
        if pd.isna(ts):
            return None
        ts = str(ts).strip()
        if not ts:
            return None
        if len(ts) == 6:
            return f"{ts[:2]}:{ts[2:4]}:{ts[4:6]}"
        return ts if ':' in ts else ts


class DataProcessingService:
    """資料處理服務"""
    
    def __init__(self, output_callback: Callable = None):
        self.output_callback = output_callback or (lambda x: None)
        self.path_mgr = PathManager()
    
    def process_data_organization(self) -> Dict[str, Any]:
        """執行資料整理"""
        self.output_callback("開始資料整理...")
        
        try:
            db_path = self.path_mgr.ensure_db_dir()
            punch_path = self.path_mgr.get_punch_data_path()
            shift_path = self.path_mgr.get_shift_class_path()
            driver_path = self.path_mgr.get_driver_list_path()

            self.output_callback(f"資料庫路徑: {db_path}")
            self.output_callback(f"打卡資料: {punch_path}")
            self.output_callback(f"班別資料: {shift_path}")
            self.output_callback(f"司機名單: {driver_path}")

            # 清理現有資料庫
            if Path(db_path).exists():
                Path(db_path).unlink()
                self.output_callback("已刪除現有資料庫")

            # 檢查檔案
            if not Path(punch_path).exists():
                return {'success': False, 'message': f'檔案不存在: {punch_path}'}
            if not Path(shift_path).exists():
                return {'success': False, 'message': f'檔案不存在: {shift_path}'}

            # 使用 ETL 管道處理
            punch_reader = ExcelReader(
                punch_path,
                skip_rows=AppConfig.PUNCH_DATA_SKIP_ROWS,
                use_header_row=True,
                header_row_index=AppConfig.PUNCH_DATA_HEADER_ROW
            )
            shift_reader = ExcelReader(shift_path)

            # 司機名單（可選）
            driver_reader = None
            if Path(driver_path).exists():
                driver_reader = CSVReader(driver_path, encoding='utf-8-sig')

            etl = PunchDataETL(punch_reader, shift_reader, driver_reader, self.output_callback)
            result = etl.execute(db_path)

            if result['success']:
                driver_msg = f"，司機: {result['driver_records']} 筆" if result['driver_records'] > 0 else ""
                msg = f"資料處理完成！打卡: {result['punch_records']} 筆，班別: {result['shift_records']} 筆{driver_msg}，整合: {result['integrated_records']} 筆"
                self.output_callback(f"[成功] {msg}")
                return {'success': True, 'message': msg}
            else:
                return result
                
        except Exception as e:
            error_msg = f"執行錯誤: {traceback.format_exc()}"
            self.output_callback(f"[錯誤] {error_msg}")
            return {'success': False, 'message': error_msg}
    
    def get_available_dates(self) -> List[Dict]:
        """取得可用日期列表"""
        try:
            db_mgr = DatabaseManager(self.path_mgr.get_db_path())
            conn = db_mgr.get_connection()

            query = """
            SELECT punch_date, strftime('%m-%d', punch_date) as mm_dd,
                   strftime('%w', punch_date) as weekday, COUNT(*) as count
            FROM integrated_punch
            GROUP BY punch_date
            ORDER BY punch_date DESC
            """
            df = pd.read_sql(query, conn)
            conn.close()

            weekday_map = {'0': '日', '1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六'}

            dates = []
            for _, row in df.iterrows():
                weekday = weekday_map.get(row['weekday'], '?')
                dates.append({
                    'date': row['punch_date'],
                    'mm_dd': row['mm_dd'],
                    'display': f"{row['mm_dd']} (週{weekday}) - {row['count']}筆",
                    'count': row['count']
                })
            
            self.output_callback(f"找到 {len(dates)} 個可用日期")
            return dates
            
        except Exception as e:
            self.output_callback(f"取得日期失敗: {e}")
            return []
    
    def get_punch_data_for_date(self, date_str: str) -> pd.DataFrame:
        """取得指定日期的打卡資料"""
        db_mgr = DatabaseManager(self.path_mgr.get_db_path())
        time_columns = db_mgr.get_time_columns()

        conn = db_mgr.get_connection()
        query = f"""
        SELECT shift_class, emp_id, account_id, name, punch_date, {', '.join(time_columns)}
        FROM integrated_punch
        WHERE strftime('%m-%d', punch_date) = ?
        ORDER BY shift_class, emp_id
        """
        df = pd.read_sql_query(query, conn, params=(date_str,))
        conn.close()
        
        # 格式化時間
        for col in time_columns:
            df[col] = df[col].map(TimeProcessor.format_timestamp)
        
        df['所有時間戳記'] = df[time_columns].apply(
            lambda row: ', '.join([t for t in row if pd.notna(t)]), axis=1
        )
        df['打卡次數'] = df[time_columns].apply(
            lambda row: sum(1 for t in row if pd.notna(t)), axis=1
        )
        
        return df
    
    def get_full_punch_data(self) -> pd.DataFrame:
        """取得完整打卡資料"""
        db_mgr = DatabaseManager(self.path_mgr.get_db_path())
        time_columns = db_mgr.get_time_columns()
        time_fields = ', '.join(time_columns) if time_columns else ''
        time_fields = f", {time_fields}" if time_fields else ''

        conn = db_mgr.get_connection()

        # 取得日期範圍
        date_query = "SELECT MIN(punch_date) as min_date, MAX(punch_date) as max_date FROM integrated_punch"
        date_range = pd.read_sql(date_query, conn)
        min_date = pd.to_datetime(date_range['min_date'].iloc[0])
        max_date = pd.to_datetime(date_range['max_date'].iloc[0])

        self.output_callback(f"日期範圍: {min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}")

        # 建立完整日期範圍
        date_range_df = pd.DataFrame({
            '日期': pd.date_range(min_date, max_date, freq='D').strftime('%Y-%m-%d'),
            '星期': pd.date_range(min_date, max_date, freq='D').strftime('%w').map({
                '0': '日', '1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六'
            })
        })

        # 取得打卡資料
        query = f"""
        SELECT shift_class, emp_id, account_id, name,
               strftime('%Y-%m-%d', punch_date) as 日期,
               CASE strftime('%w', punch_date)
                   WHEN '0' THEN '日' WHEN '1' THEN '一' WHEN '2' THEN '二'
                   WHEN '3' THEN '三' WHEN '4' THEN '四' WHEN '5' THEN '五'
                   WHEN '6' THEN '六'
               END as 星期
               {time_fields}
        FROM integrated_punch
        ORDER BY account_id, 日期
        """
        df = pd.read_sql(query, conn)
        conn.close()

        # 處理時間
        for col in time_columns:
            df[col] = df[col].map(TimeProcessor.format_timestamp)

        df['所有時間戳記'] = df[time_columns].apply(
            lambda row: ', '.join([t for t in row if pd.notna(t)]), axis=1
        )
        df['打卡次數'] = df[time_columns].apply(
            lambda row: sum(1 for t in row if pd.notna(t)), axis=1
        )

        # 整合員工記錄
        employees = df[['emp_id', 'account_id', 'name', 'shift_class']].drop_duplicates()
        complete_records = []

        for _, emp in employees.iterrows():
            emp_dates = date_range_df.copy()
            for col, val in emp.items():
                emp_dates[col] = val

            emp_dates = emp_dates.merge(
                df[df['emp_id'] == emp['emp_id']][['日期', '所有時間戳記', '打卡次數']],
                on='日期', how='left'
            )
            emp_dates['所有時間戳記'] = emp_dates['所有時間戳記'].fillna('')
            emp_dates['打卡次數'] = emp_dates['打卡次數'].fillna(0).astype(int)
            complete_records.append(emp_dates)

        return pd.concat(complete_records, ignore_index=True)
    
    def get_night_meal_data(self) -> pd.DataFrame:
        """取得夜點津貼資料"""
        db_mgr = DatabaseManager(self.path_mgr.get_db_path())
        time_columns = db_mgr.get_time_columns()
        night_threshold = TimeProcessor.parse_time(AppConfig.NIGHT_MEAL_THRESHOLD)

        conn = db_mgr.get_connection()

        # 取得所有班別
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT shift_class FROM integrated_punch")
        classes = [row[0] for row in cursor.fetchall()]

        all_data = []

        for class_name in classes:
            self.output_callback(f"處理班別: {class_name}")

            time_cols_str = ', '.join(time_columns)
            query = f"""
            SELECT account_id, name, emp_id, shift_class, punch_date {',' if time_columns else ''} {time_cols_str}
            FROM integrated_punch
            WHERE shift_class = ?
            ORDER BY emp_id, punch_date
            """
            df = pd.read_sql_query(query, conn, params=(class_name,))

            processed_dates = {}
            for _, row in df.iterrows():
                account = row['account_id']
                date = row['punch_date']
                
                if account not in processed_dates:
                    processed_dates[account] = set()
                
                # 檢查是否符合夜點條件
                for col in reversed(time_columns):
                    if not pd.isna(row[col]):
                        last_time_str = str(row[col])
                        if len(last_time_str) == 6:
                            last_time_str = f"{last_time_str[:2]}:{last_time_str[2:4]}:{last_time_str[4:6]}"
                        try:
                            last_time = datetime.strptime(last_time_str, '%H:%M:%S').time()
                            if last_time > night_threshold and date not in processed_dates[account]:
                                all_data.append({
                                    'emp_id': row['emp_id'],
                                    'account_id': account,
                                    'name': row['name'],
                                    'shift_class': class_name,
                                    '月份': date[5:7],
                                    '日期': date[8:10]
                                })
                                processed_dates[account].add(date)
                        except:
                            pass
                        break
        
        conn.close()
        return pd.DataFrame(all_data)
