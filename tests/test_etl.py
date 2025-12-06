"""
單元測試 - 測試 ETL 框架
"""

import unittest
import pandas as pd
from datetime import date, time
import sys
import os

# 確保可以導入模組
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models import PunchRecord, ShiftClass, ValidationResult
from core.validators import DataValidator, CustomValidator, ValidationRules
from core.readers import DataFrameReader


class TestPunchRecordModel(unittest.TestCase):
    """測試打卡記錄模型"""
    
    def test_valid_record(self):
        """測試有效記錄"""
        data = {'公務帳號': 'EMP001', '刷卡日期': '2023-12-01', '刷卡時間': '08:30:00'}
        record = PunchRecord(**data)
        self.assertEqual(record.公務帳號, 'EMP001')
        self.assertEqual(record.刷卡日期, date(2023, 12, 1))
        self.assertEqual(record.刷卡時間, time(8, 30, 0))
    
    def test_taiwan_date_conversion(self):
        """測試民國年轉換"""
        data = {'公務帳號': 'EMP001', '刷卡日期': '1121201', '刷卡時間': '0830'}
        record = PunchRecord(**data)
        self.assertEqual(record.刷卡日期, date(2023, 12, 1))
    
    def test_time_format_conversion(self):
        """測試時間格式轉換"""
        data = {'公務帳號': 'EMP001', '刷卡日期': '2023-12-01', '刷卡時間': '0830'}
        record = PunchRecord(**data)
        self.assertEqual(record.刷卡時間, time(8, 30, 0))


class TestDataValidator(unittest.TestCase):
    """測試資料驗證器"""
    
    def test_validate_valid_data(self):
        """測試驗證有效資料"""
        df = pd.DataFrame([
            {'公務帳號': 'EMP001', '刷卡日期': '2023-12-01', '刷卡時間': '0830'},
            {'公務帳號': 'EMP002', '刷卡日期': '2023-12-01', '刷卡時間': '0900'},
        ])
        
        validator = DataValidator(PunchRecord)
        valid_records, result = validator.validate(df)
        
        self.assertEqual(len(valid_records), 2)
        self.assertEqual(result.valid_count, 2)
        self.assertTrue(result.success)
    
    def test_validate_invalid_data(self):
        """測試驗證無效資料"""
        df = pd.DataFrame([
            {'公務帳號': 'EMP001', '刷卡日期': '2023-12-01', '刷卡時間': '0830'},
            {'公務帳號': '', '刷卡日期': '2023-12-01', '刷卡時間': '0900'},
        ])
        
        validator = DataValidator(PunchRecord)
        valid_records, result = validator.validate(df)
        
        self.assertEqual(len(valid_records), 1)
        self.assertEqual(result.error_count, 1)


class TestDataFrameReader(unittest.TestCase):
    """測試 DataFrame 讀取器"""
    
    def test_read_dataframe(self):
        """測試讀取 DataFrame"""
        df = pd.DataFrame([{'col1': 'a', 'col2': 'b'}])
        reader = DataFrameReader(df, 'test')
        result = reader.read()
        self.assertEqual(len(result), 1)


class TestValidationResult(unittest.TestCase):
    """測試驗證結果"""
    
    def test_summary(self):
        """測試摘要"""
        result = ValidationResult(success=True)
        result.add_valid()
        result.add_valid()
        result.add_error(3, 'field1', 'error')
        
        self.assertIn('成功 2 筆', result.summary)
        self.assertIn('錯誤 1 筆', result.summary)


def run_tests():
    """執行測試"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestPunchRecordModel))
    suite.addTests(loader.loadTestsFromTestCase(TestDataValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestDataFrameReader))
    suite.addTests(loader.loadTestsFromTestCase(TestValidationResult))
    
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


if __name__ == '__main__':
    print("=" * 60)
    print("ETL 框架單元測試")
    print("=" * 60)
    
    result = run_tests()
    
    print("\n" + "=" * 60)
    print(f"執行: {result.testsRun}, 成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print("✅ 測試通過！" if result.wasSuccessful() else "❌ 有測試失敗")
