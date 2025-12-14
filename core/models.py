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
    """打卡記錄資料模型（標準化欄位）"""

    # 自動忽略 Excel 中的多餘欄位
    model_config = ConfigDict(extra='ignore')

    # 使用標準化欄位名稱
    account_id: str = Field(..., min_length=1, max_length=50)
    punch_date: str  # 已轉換為 YYYY-MM-DD 格式的字串
    punch_time: str  # 已轉換為 HH:MM:SS 格式的字串
    seq_no: Optional[int] = None
    emp_id: Optional[str] = None
    name: Optional[str] = None

    @field_validator('account_id')
    @classmethod
    def validate_account(cls, v):
        if not v or v.strip() == '':
            raise ValueError('account_id 不可為空')
        return v.strip()

    @field_validator('punch_date')
    @classmethod
    def validate_date(cls, v):
        """驗證日期格式（已轉換後的 YYYY-MM-DD）"""
        if not v or v.strip() == '':
            raise ValueError('punch_date 不可為空')
        # 簡單驗證格式
        if not re.match(r'\d{4}-\d{2}-\d{2}', v):
            raise ValueError(f'punch_date 格式錯誤: {v}')
        return v.strip()

    @field_validator('punch_time')
    @classmethod
    def validate_time(cls, v):
        """驗證時間格式（已轉換後的 HH:MM:SS）"""
        if not v or v.strip() == '':
            raise ValueError('punch_time 不可為空')
        # 簡單驗證格式
        if not re.match(r'\d{2}:\d{2}:\d{2}', v):
            raise ValueError(f'punch_time 格式錯誤: {v}')
        return v.strip()


class ShiftClass(BaseModel):
    """班別資料模型（標準化欄位）"""

    # 使用標準化欄位名稱
    account_id: str = Field(..., min_length=1, max_length=50)
    emp_id: Optional[str] = None
    name: Optional[str] = None
    shift_class: str = Field(..., min_length=1, max_length=50)
    shift_id: Optional[str] = None

    @field_validator('account_id', 'shift_class')
    @classmethod
    def validate_required(cls, v):
        if not v or v.strip() == '':
            raise ValueError('此欄位不可為空')
        return v.strip()


class IntegratedPunchRecord(BaseModel):
    """整合後的打卡記錄（標準化欄位）"""

    account_id: str
    emp_id: Optional[str] = None
    name: Optional[str] = None
    shift_class: Optional[str] = None
    punch_date: str  # YYYY-MM-DD 格式
    punch_times: List[str] = Field(default_factory=list)  # HH:MM:SS 格式列表

    @property
    def last_punch_time(self) -> Optional[str]:
        return max(self.punch_times) if self.punch_times else None

    @property
    def first_punch_time(self) -> Optional[str]:
        return min(self.punch_times) if self.punch_times else None

    @property
    def punch_count(self) -> int:
        return len(self.punch_times)

    def is_night_meal_eligible(self, threshold: str = "22:00:00") -> bool:
        last_time = self.last_punch_time
        return last_time is not None and last_time > threshold


class DriverInfo(BaseModel):
    """司機資訊模型（標準化欄位）"""
    account_id: str = Field(..., min_length=1)
    emp_id: Optional[str] = None
    name: Optional[str] = None
    is_driver: bool = True


class NightMealRecord(BaseModel):
    """夜點津貼記錄（標準化欄位）"""
    emp_id: Optional[str] = None
    account_id: str
    name: Optional[str] = None
    shift_class: str
    month: str  # 月份
    day: str    # 日期
    is_driver: bool = False


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
