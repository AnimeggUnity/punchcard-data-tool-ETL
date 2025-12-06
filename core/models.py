"""
資料模型定義 - 使用 Pydantic 進行資料驗證

注意：使用 extra='ignore' 讓模型自動忽略 Excel 中的多餘欄位，
這樣未來 Excel 新增欄位時不需要修改模型。
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import date, time, datetime
from typing import Optional, List
import re


class PunchRecord(BaseModel):
    """打卡記錄資料模型"""
    
    # 自動忽略 Excel 中的多餘欄位
    model_config = ConfigDict(extra='ignore')
    
    公務帳號: str = Field(..., min_length=1, max_length=50)
    刷卡日期: date
    刷卡時間: time
    序號: Optional[int] = None
    
    @field_validator('公務帳號')
    @classmethod
    def validate_account(cls, v):
        if not v or v.strip() == '':
            raise ValueError('公務帳號不可為空')
        return v.strip()
    
    @field_validator('刷卡日期', mode='before')
    @classmethod
    def parse_date(cls, v):
        """處理多種日期格式"""
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            v = v.strip()
            # 民國年格式（7位數字：YYYMMDD）
            if len(v) == 7 and v.isdigit():
                year = int(v[:3]) + 1911
                month = int(v[3:5])
                day = int(v[5:7])
                return date(year, month, day)
            # 西元年格式（YYYY-MM-DD）
            if '-' in v:
                return datetime.strptime(v, '%Y-%m-%d').date()
        try:
            return datetime.fromisoformat(str(v)).date()
        except:
            raise ValueError(f'無法解析日期格式: {v}')
    
    @field_validator('刷卡時間', mode='before')
    @classmethod
    def parse_time(cls, v):
        """處理多種時間格式"""
        if isinstance(v, time):
            return v
        if isinstance(v, str):
            v = v.strip()
            # 4位數字格式（HHMM）
            if len(v) == 4 and v.isdigit():
                return time(int(v[:2]), int(v[2:4]), 0)
            # 6位數字格式（HHMMSS）
            if len(v) == 6 and v.isdigit():
                return time(int(v[:2]), int(v[2:4]), int(v[4:6]))
            # 標準格式（HH:MM:SS 或 HH:MM）
            if ':' in v:
                parts = v.split(':')
                if len(parts) == 2:
                    return time(int(parts[0]), int(parts[1]), 0)
                elif len(parts) == 3:
                    return time(int(parts[0]), int(parts[1]), int(parts[2]))
        raise ValueError(f'無法解析時間格式: {v}')


class ShiftClass(BaseModel):
    """班別資料模型"""
    
    公務帳號: str = Field(..., min_length=1, max_length=50)
    卡號: Optional[str] = None
    姓名: Optional[str] = None
    班別: str = Field(..., min_length=1, max_length=50)
    
    @field_validator('公務帳號', '班別')
    @classmethod
    def validate_required(cls, v):
        if not v or v.strip() == '':
            raise ValueError('此欄位不可為空')
        return v.strip()


class IntegratedPunchRecord(BaseModel):
    """整合後的打卡記錄"""
    
    公務帳號: str
    卡號: Optional[str] = None
    姓名: Optional[str] = None
    班別: Optional[str] = None
    刷卡日期: date
    刷卡時間列表: List[time] = Field(default_factory=list)
    
    @property
    def 最後刷卡時間(self) -> Optional[time]:
        return max(self.刷卡時間列表) if self.刷卡時間列表 else None
    
    @property
    def 第一次刷卡時間(self) -> Optional[time]:
        return min(self.刷卡時間列表) if self.刷卡時間列表 else None
    
    @property
    def 刷卡次數(self) -> int:
        return len(self.刷卡時間列表)
    
    def is_night_meal_eligible(self, threshold: time = time(22, 0, 0)) -> bool:
        last_time = self.最後刷卡時間
        return last_time is not None and last_time > threshold


class DriverInfo(BaseModel):
    """司機資訊模型"""
    公務帳號: str = Field(..., min_length=1)


class NightMealRecord(BaseModel):
    """夜點津貼記錄"""
    卡號: Optional[str] = None
    公務帳號: str
    姓名: Optional[str] = None
    班別: str
    月份: str
    日期: str
    是否為司機: bool = False


class ValidationResult(BaseModel):
    """資料驗證結果"""
    success: bool
    valid_count: int = 0
    error_count: int = 0
    errors: List[dict] = Field(default_factory=list)
    
    def add_error(self, row_number: int, field: str, error: str, data: dict = None):
        self.error_count += 1
        self.errors.append({
            'row': row_number, 'field': field, 'error': error, 'data': data
        })
    
    def add_valid(self):
        self.valid_count += 1
    
    @property
    def summary(self) -> str:
        return f"驗證完成：成功 {self.valid_count} 筆，錯誤 {self.error_count} 筆"
    
    def get_error_summary(self, max_errors: int = 10) -> str:
        if not self.errors:
            return "無錯誤"
        lines = [f"發現 {self.error_count} 筆錯誤："]
        for i, err in enumerate(self.errors[:max_errors], 1):
            lines.append(f"  {i}. 第 {err['row']} 列，欄位 '{err['field']}'：{err['error']}")
        if len(self.errors) > max_errors:
            lines.append(f"  ... 還有 {len(self.errors) - max_errors} 筆錯誤")
        return '\n'.join(lines)
