# 報表系統開發指南

本文件說明報表模組的架構與使用方式，幫助開發者快速理解並擴展報表功能。

## 架構概覽

```
services/
├── report_service.py      # 門面類別 (Facade)
└── reports/
    ├── __init__.py
    ├── base_report.py     # 抽象基礎類別
    ├── daily_punch_report.py
    ├── full_punch_report.py
    ├── night_meal_report.py
    └── printable_reports.py
```

### 設計模式

- **門面模式 (Facade)**: `ReportService` 提供統一的 API，隱藏各報表實作細節
- **模板方法模式 (Template Method)**: `BaseReport` 定義報表生成骨架，子類別實作具體內容

## 報表類型速查表

| 報表類別 | 用途 | 輸入資料 | 輸出檔案 |
|---------|------|---------|---------|
| `DailyPunchReport` | 單日打卡記錄 | 單日 DataFrame + 日期 | `punch_record_{date}.html` |
| `FullPunchReport` | 完整打卡總表 | 多日 DataFrame | `full_punch_record_report.html` |
| `NightMealReport` | 夜點津貼統計 | 夜點資料 DataFrame | `combined_night_meal_report.html` |
| `PrintableDailyReport` | 列印版單日報表 | 單日 DataFrame + 日期 | `punch_record_{date}_print.html` |
| `PrintableFullReport` | 列印版完整報表 | 多日 DataFrame | `punch_by_account_print.html` |

## 快速使用

### 基本呼叫方式

```python
from services.report_service import ReportService

# 初始化
report_service = ReportService(output_callback=print)

# 生成單日報表
report_service.generate_daily_punch_report(df, "2024-01-15", driver_accounts)

# 生成完整報表
report_service.generate_full_punch_report(df, driver_accounts)

# 生成夜點津貼報表
report_service.generate_night_meal_report(df, driver_accounts)

# 生成列印版報表
report_service.generate_printable_daily_report(df, "2024-01-15", driver_accounts)
report_service.generate_printable_full_report(df, driver_accounts)
```

### 輸入資料格式

所有報表接受的 DataFrame 須包含以下欄位：

| 欄位名稱 | 類型 | 說明 |
|---------|------|------|
| `卡號` | str | 員工卡號 |
| `公務帳號` | str | 員工帳號 |
| `姓名` | str | 員工姓名 |
| `班別` | str | 所屬班別 |
| `日期` | str | 日期 (YYYY-MM-DD) |
| `星期` | str | 星期幾 |
| `打卡次數` | int | 當日打卡次數 |
| `所有時間戳記` | str | 逗號分隔的時間戳記 |

夜點報表額外需要：

| 欄位名稱 | 類型 | 說明 |
|---------|------|------|
| `月份` | int | 月份數字 (會自動加上「月」) |

## 直接使用報表生成器

若需更細緻的控制，可直接使用報表類別：

```python
from services.reports import DailyPunchReport
from config import PathManager

path_mgr = PathManager()
report = DailyPunchReport(output_callback=print, path_mgr=path_mgr)

# 生成報表
output_path = report.generate(df, "2024-01-15", driver_accounts)
```

## 新增報表類型

### 1. 建立報表類別

在 `services/reports/` 下新增檔案：

```python
# services/reports/my_new_report.py
from typing import Set
import pandas as pd
from .base_report import BaseReport

class MyNewReport(BaseReport):
    """我的新報表"""

    def generate(self, df: pd.DataFrame, driver_accounts: Set[str]) -> str:
        """
        生成報表

        Args:
            df: 資料 DataFrame
            driver_accounts: 司機帳號集合

        Returns:
            生成的報表檔案路徑
        """
        content = self._generate_content(df, driver_accounts)
        html = HtmlTemplateManager.get_bootstrap_template("報表標題", content)

        output_file = os.path.join(self.path_mgr.get_output_dir(), 'my_report.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        self.output_callback(f"報表已生成: {output_file}")
        self._auto_open(output_file)
        return output_file

    def _generate_content(self, df: pd.DataFrame, driver_accounts: Set[str]) -> str:
        """生成報表內容 HTML"""
        # 實作報表內容...
        return "<div>...</div>"
```

### 2. 註冊到 `__init__.py`

```python
# services/reports/__init__.py
from .my_new_report import MyNewReport

__all__ = [
    # ...existing exports...
    'MyNewReport'
]
```

### 3. 加入門面方法 (可選)

```python
# services/report_service.py
def generate_my_new_report(self, df: pd.DataFrame, driver_accounts: Set[str]) -> str:
    return self.my_new.generate(df, driver_accounts)
```

## HTML 模板工具

`templates/` 模組提供兩種模板和組件工具：

### 模板類型

| 模板 | 用途 | 特點 |
|-----|------|-----|
| `get_bootstrap_template()` | 螢幕瀏覽 | Bootstrap 5、深淺色切換、響應式 |
| `get_printable_template()` | 列印輸出 | 簡潔、黑白友好、A4 最佳化 |

### 組件工具

```python
from templates import HtmlComponentGenerator

# 標記司機
HtmlComponentGenerator.mark_driver_account("王小明", "A001", driver_accounts)
# => '<span class="badge bg-warning...">司機</span>王小明' 或 '王小明'

# 時間戳記著色 (奇數藍、偶數紅)
HtmlComponentGenerator.colorize_timestamps(["08:00", "12:00", "18:00"])

# 統計卡片
HtmlComponentGenerator.generate_stats_row([
    {"title": "總人數", "value": "50", "icon": "fas fa-users"},
    {"title": "班別數", "value": "5", "icon": "fas fa-layer-group"}
])
```

## 報表輸出位置

所有報表輸出至 `PathManager.get_output_dir()` 指定的目錄，預設為 `output/`。

## 常見問題

### Q: 如何自訂報表樣式？

修改 `templates/html_templates.py` 中的 CSS 樣式，或在報表內容中加入 `<style>` 標籤。

### Q: 如何關閉自動開啟瀏覽器？

目前自動開啟是預設行為。若需關閉，可在子類別中覆寫 `generate()` 方法，移除 `self._auto_open()` 呼叫。

### Q: 報表中的司機標記邏輯？

傳入的 `driver_accounts: Set[str]` 包含所有司機的公務帳號，報表會自動標記符合的員工。
