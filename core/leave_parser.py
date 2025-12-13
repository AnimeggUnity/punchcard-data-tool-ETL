"""
請假資料解析器
從 Excel 解析請假記錄並正規化資料
"""

import pandas as pd
import re
import os
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any


# ========= 假別正規化映射 =========
LEAVE_TYPE_MAPPING = {
    "扣事": "事假",
    "扣病": "傷病",
    "扣特": "特休",
    "扣補": "補休",
    "生理": "傷病",
    "生理假": "傷病",
}

LEAVE_PAIR_RE = re.compile(r"([^\d,]+)(\d+(?:\.\d+)?)")


def parse_rest_days(text: str) -> List[int]:
    """
    解析休息日

    Args:
        text: 包含休息日資訊的文字（如：休三例日）

    Returns:
        星期索引清單（0=週一, 6=週日）
    """
    if not isinstance(text, str):
        return []

    rest_days = []
    weekday_map = {
        "一": 0, "二": 1, "三": 2,
        "四": 3, "五": 4, "六": 5, "日": 6
    }

    for char, idx in weekday_map.items():
        if f"休{char}" in text or f"例{char}" in text:
            if idx not in rest_days:
                rest_days.append(idx)

    if "例假" in text and 6 not in rest_days:
        rest_days.append(6)

    return rest_days


def expand_leave_days(start_date: datetime, num_days: int, rest_days: List[int]) -> List[datetime]:
    """
    展開請假日期，跳過休息日

    Args:
        start_date: 開始日期
        num_days: 實際請假天數
        rest_days: 休息日列表（0=週一, 6=週日）

    Returns:
        請假日期列表
    """
    dates = []
    cur = start_date
    max_iter = num_days * 3  # 防無窮迴圈

    while len(dates) < num_days and max_iter > 0:
        if cur.weekday() not in rest_days:
            dates.append(cur)
        cur += timedelta(days=1)
        max_iter -= 1

    return dates


def parse_leave_pairs(text: str) -> List[Tuple[str, float, List[int]]]:
    """
    解析單一儲存格的請假資訊

    Args:
        text: 儲存格文字（如：傷病(休三例日)2）

    Returns:
        [(假別, 天數, 休息日清單), ...]
    """
    if not isinstance(text, str):
        return []

    # 移除時間區段
    text = re.sub(r"\d{1,2}:\d{2}\s*~\s*\d{1,2}:\d{2}", "", text)

    pairs = []
    for raw_type, raw_day in LEAVE_PAIR_RE.findall(text):
        leave_day = float(raw_day)
        if leave_day <= 0:
            continue

        rest_days = parse_rest_days(raw_type)
        leave_type = re.sub(r"\([^)]*\)", "", raw_type).strip()
        leave_type = LEAVE_TYPE_MAPPING.get(leave_type, leave_type)

        pairs.append((leave_type, leave_day, rest_days))

    return pairs


class LeaveDataParser:
    """請假資料解析器"""

    def __init__(self, file_path: str):
        """
        Args:
            file_path: Excel 檔案路徑（支援 .xlsx 或 .xls）
        """
        self.file_path = file_path
        self.df = None
        self.year_roc = None
        self.month = None
        self.year = None

    def load_excel(self) -> pd.DataFrame:
        """
        載入 Excel 檔案

        Returns:
            原始 DataFrame

        Raises:
            FileNotFoundError: 檔案不存在
            ValueError: 無法解析年月資訊
        """
        # 自動檢測檔案格式
        if self.file_path.endswith('.xlsx'):
            self.df = pd.read_excel(self.file_path, header=None)
        elif self.file_path.endswith('.xls'):
            self.df = pd.read_excel(self.file_path, header=None, engine='xlrd')
        else:
            # 嘗試自動偵測
            if os.path.exists(self.file_path.replace('.xls', '.xlsx')):
                self.df = pd.read_excel(self.file_path.replace('.xls', '.xlsx'), header=None)
            elif os.path.exists(self.file_path.replace('.xlsx', '.xls')):
                self.df = pd.read_excel(self.file_path.replace('.xlsx', '.xls'), header=None, engine='xlrd')
            else:
                raise FileNotFoundError(f"找不到檔案: {self.file_path}")

        # 解析年月
        title = self.df.iloc[0, 0]
        m = re.search(r"(\d+)\s*年\s*(\d+)\s*月", str(title))
        if not m:
            raise ValueError(f"無法解析年月資訊: {title}")

        self.year_roc = int(m.group(1))
        self.month = int(m.group(2))
        self.year = self.year_roc + 1911

        return self.df

    def parse(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        解析請假資料

        Returns:
            (parsed_df, unparsed_df) - 已解析和未解析的資料
        """
        if self.df is None:
            self.load_excel()

        # 找表頭
        header_row = self.df[self.df[0] == "人事編號"].index[0]
        df = self.df.iloc[header_row + 2:].reset_index(drop=True)

        total_cols = df.shape[1]
        df.columns = ["emp_id", "name"] + list(range(1, total_cols - 1))
        df["emp_id"] = df["emp_id"].ffill()
        df["name"] = df["name"].ffill()

        parsed_records = []
        unparsed_records = []

        # 主處理邏輯
        for _, row in df.iterrows():
            emp = row["emp_id"]
            name = row["name"]

            for day in range(1, total_cols - 1):
                cell = row[day]

                if not isinstance(cell, str) or not cell.strip():
                    continue

                pairs = parse_leave_pairs(cell)
                date_obj = datetime(self.year, self.month, day)

                if not pairs:
                    unparsed_records.append({
                        "emp_id": emp,
                        "name": name,
                        "year_roc": self.year_roc,
                        "year": self.year,
                        "month": self.month,
                        "day": day,
                        "date": date_obj.strftime("%m/%d"),
                        "raw_text": cell,
                        "reason": "無法解析假別或天數",
                    })
                    continue

                for leave_type, leave_day, rest_days in pairs:
                    if leave_day == int(leave_day) and leave_day >= 1:
                        # 整數天，展開
                        num_days = int(leave_day)
                        dates = (
                            expand_leave_days(date_obj, num_days, rest_days)
                            if rest_days
                            else [date_obj + timedelta(days=i) for i in range(num_days)]
                        )

                        for d in dates:
                            parsed_records.append({
                                "emp_id": emp,
                                "name": name,
                                "year_roc": d.year - 1911,
                                "year": d.year,
                                "month": d.month,
                                "day": d.day,
                                "date": d.strftime("%m/%d"),
                                "weekday": d.weekday(),
                                "weekday_zh": ["一","二","三","四","五","六","日"][d.weekday()],
                                "leave_type": leave_type,
                                "leave_day": 1.0,
                                "source_text": cell,
                            })
                    else:
                        # 非整數天
                        parsed_records.append({
                            "emp_id": emp,
                            "name": name,
                            "year_roc": self.year_roc,
                            "year": self.year,
                            "month": self.month,
                            "day": day,
                            "date": date_obj.strftime("%m/%d"),
                            "weekday": date_obj.weekday(),
                            "weekday_zh": ["一","二","三","四","五","六","日"][date_obj.weekday()],
                            "leave_type": leave_type,
                            "leave_day": leave_day,
                            "source_text": cell,
                        })

        parsed_df = pd.DataFrame(parsed_records).sort_values(["emp_id", "date", "leave_type"])
        unparsed_df = pd.DataFrame(unparsed_records)

        return parsed_df, unparsed_df
