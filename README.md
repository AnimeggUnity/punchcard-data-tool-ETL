# 打卡系統資料處理工具 - ETL 重構版

使用 ETL (Extract-Transform-Load) 架構重構的打卡資料處理工具，具備 Pydantic 資料驗證功能。

## 🚀 快速開始

```bash
# 安裝依賴
pip install -r requirements.txt

# 執行程式
python main.py
```

## 📁 專案結構

```
punch_helper_etl/
├── core/                   # 核心 ETL 框架
│   ├── models.py          # Pydantic 資料模型
│   ├── readers.py         # 資料讀取器
│   ├── validators.py      # 資料驗證器
│   └── pipeline.py        # ETL 管道
├── services/              # 業務邏輯服務
│   ├── data_service.py    # 資料處理服務
│   ├── report_service.py  # 報表生成服務（門面）
│   ├── reports/           # 報表生成器模組
│   │   ├── base_report.py
│   │   ├── daily_punch_report.py
│   │   ├── full_punch_report.py
│   │   ├── night_meal_report.py
│   │   └── printable_reports.py
│   └── driver_service.py  # 司機名單服務
├── templates/             # HTML 模板
│   └── html_templates.py
├── gui/                   # GUI 介面
│   └── main_window.py
├── tests/                 # 單元測試
├── data/                  # 資料檔案目錄
├── db/                    # SQLite 資料庫目錄
├── output/                # 輸出報表目錄
├── config.py              # ⚙️ 配置檔案（重要！）
├── main.py                # 主程式入口
└── requirements.txt
```

## ⚙️ 設定導向架構

**未來格式變更只需修改 `config.py`，不需要修改程式碼！**

### Excel 讀取設定

在 `config.py` 中的 `ExcelReadingConfig` 類別：

```python
class ExcelReadingConfig:
    PUNCH_DATA = {
        # 跳過的行數（第6行是標題，所以跳過5行）
        'skip_rows': 5,
        
        # 標題行位置（相對於 skip_rows 後）
        'header_row': 0,
        
        # 移除空白欄位（如 Unnamed: 0）
        'remove_unnamed_columns': True,
        
        # 過濾欄位（只保留此欄位為數字的行）
        'filter_column': '序號',
        
        # 必要欄位
        'required_columns': ['公務帳號', '刷卡日期', '刷卡時間'],
        
        # 欄位名稱對應
        'column_mapping': {
            # 'Excel欄位名': '模型欄位名',
        },
        
        # 日期/時間欄位
        'date_columns': ['刷卡日期'],
        'time_columns': ['刷卡時間'],
        'string_columns': ['刷卡日期', '刷卡時間'],
    }
```

## 🔧 常見格式變更處理

| 變更情況 | 如何處理 |
|---------|---------|
| **前面多一行** | 修改 `skip_rows`，例如從 5 改成 6 |
| **資料從 C 列開始** | `remove_unnamed_columns: True` 會自動處理 |
| **欄位名稱改變** | 在 `column_mapping` 加入對應關係 |
| **新增欄位** | 不需修改！Pydantic 會自動忽略多餘欄位 |
| **過濾欄位改變** | 修改 `filter_column` |
| **刪除欄位** | 如果不是必要欄位，不需修改 |

### 範例：前面多一行

```python
# 原本：第6行是標題
'skip_rows': 5,

# 改成：第7行是標題
'skip_rows': 6,
```

### 範例：欄位名稱改變

```python
'column_mapping': {
    '人員姓名': '姓名',      # Excel 的「人員姓名」對應到「姓名」
    '刷卡時間戳記': '刷卡時間',  # Excel 的「刷卡時間戳記」對應到「刷卡時間」
},
```

## � 功能說明

### 資料整理
- 讀取打卡資料 Excel（支援分頁格式）
- 自動轉換民國年日期與 4 位數時間格式
- Pydantic 資料驗證（100% 型別安全）
- 整合打卡與班別資料

### 報表生成
- 夜點津貼彙總表
- 單日打卡查詢（含列印版）
- 完整打卡記錄查詢（含列印版）
- 支援深色/淺色主題切換
- 模組化報表架構（詳見 [docs/reports_guide.md](docs/reports_guide.md)）

## 🏗️ ETL 架構優勢

| 優勢 | 說明 |
|------|------|
| **型別安全** | Pydantic 確保每筆資料格式正確 |
| **早期錯誤偵測** | 資料問題在載入階段就會發現 |
| **清晰的錯誤訊息** | 指出哪一列、哪個欄位有問題 |
| **模組化架構** | 易於維護和擴展 |
| **設定導向** | 格式變更只需改設定，不改程式碼 |
| **可測試性** | 各模組可獨立單元測試 |
| **報表擴展** | 新增報表只需繼承 BaseReport |

## � 資料檔案格式

### 打卡資料 (刷卡資料.xlsx)

```
第1-5行:   標題資訊（跳過）
第6行:     欄位標題：序號, 公務帳號, 身分證字號, 人員姓名, 刷卡日期, 刷卡時間, ...
第7-23行:  資料
第24-28行: 分頁重複標題（自動過濾）
...依此類推
```

**日期格式**：民國年 `1140210` → 自動轉換為 `2025-02-10`  
**時間格式**：`073251` → 自動轉換為 `07:32:51`

### 班別資料 (list.xlsx)

每個工作表代表一個班別，欄位：
- 班別、卡號、姓名、公務帳號、班次ID

### 司機名單 (司機名單.csv)

CSV 格式，必要欄位：公務帳號

## 🧪 測試

```bash
cd tests
python test_etl.py
```

## 📦 依賴套件

- pandas >= 1.5.0
- openpyxl >= 3.0.0
- pydantic >= 2.0.0
- FreeSimpleGUI >= 5.0.0

## 📝 版本歷史

- **v2.0** - ETL 重構版，加入 Pydantic 驗證和設定導向架構
- **v1.0** - 原始版本 (main_app.py)
