"""
資料驗證器 - 使用 Pydantic 進行資料驗證
"""

from typing import List, Tuple, Type, Callable, Optional
import pandas as pd
from pydantic import BaseModel, ValidationError
import logging

from .models import ValidationResult

logger = logging.getLogger(__name__)


class DataValidator:
    """Pydantic 資料驗證器"""
    
    def __init__(self, model: Type[BaseModel], stop_on_error: bool = False, max_errors: int = 100):
        self.model = model
        self.stop_on_error = stop_on_error
        self.max_errors = max_errors
    
    def validate(self, df: pd.DataFrame, output_callback: Callable = None) -> Tuple[List[BaseModel], ValidationResult]:
        output_callback = output_callback or (lambda x: None)
        output_callback(f"開始驗證 {len(df)} 筆資料...")
        
        valid_records = []
        result = ValidationResult(success=True)
        
        for idx, row in df.iterrows():
            try:
                record = self.model(**row.to_dict())
                valid_records.append(record)
                result.add_valid()
            except ValidationError as e:
                result.success = False
                for err in e.errors():
                    field = '.'.join(str(loc) for loc in err['loc'])
                    if result.error_count < self.max_errors:
                        result.add_error(idx + 1, field, err['msg'], row.to_dict())
                if self.stop_on_error:
                    break
            except Exception as e:
                result.success = False
                if result.error_count < self.max_errors:
                    result.add_error(idx + 1, 'unknown', str(e), row.to_dict())
                if self.stop_on_error:
                    break
        
        output_callback(result.summary)
        if result.error_count > 0:
            output_callback(result.get_error_summary(5))
        
        return valid_records, result


class CustomValidator:
    """自訂驗證器"""
    
    def __init__(self, validation_func: Callable[[pd.Series], Tuple[bool, str]]):
        self.validation_func = validation_func
    
    def validate(self, df: pd.DataFrame, output_callback: Callable = None) -> Tuple[pd.DataFrame, ValidationResult]:
        output_callback = output_callback or (lambda x: None)
        
        valid_rows = []
        result = ValidationResult(success=True)
        
        for idx, row in df.iterrows():
            is_valid, error_msg = self.validation_func(row)
            if is_valid:
                valid_rows.append(row)
                result.add_valid()
            else:
                result.success = False
                result.add_error(idx + 1, 'custom', error_msg, row.to_dict())
        
        return pd.DataFrame(valid_rows), result


class CompositeValidator:
    """組合驗證器"""
    
    def __init__(self, validators: List):
        self.validators = validators
    
    def validate(self, df: pd.DataFrame, output_callback: Callable = None) -> Tuple[pd.DataFrame, List[ValidationResult]]:
        output_callback = output_callback or (lambda x: None)
        
        current_df = df
        all_results = []
        
        for i, validator in enumerate(self.validators, 1):
            output_callback(f"執行驗證器 {i}/{len(self.validators)}")
            
            if isinstance(validator, DataValidator):
                valid_records, result = validator.validate(current_df, output_callback)
                current_df = pd.DataFrame([r.model_dump() for r in valid_records])
            else:
                current_df, result = validator.validate(current_df, output_callback)
            
            all_results.append(result)
            if len(current_df) == 0:
                break
        
        return current_df, all_results


class ValidationRules:
    """常用驗證規則"""
    
    @staticmethod
    def not_null(field_name: str):
        def validator(row):
            if pd.isna(row.get(field_name)):
                return False, f"{field_name} 不可為空"
            return True, ""
        return validator
    
    @staticmethod
    def in_range(field_name: str, min_val, max_val):
        def validator(row):
            value = row.get(field_name)
            if pd.isna(value):
                return True, ""
            if not (min_val <= value <= max_val):
                return False, f"{field_name} 必須在 {min_val} 到 {max_val} 之間"
            return True, ""
        return validator
