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
│   ├── pipeline.py        # ETL 管道
│   ├── leave_parser.py    # 請假資料解析器
│   └── leave_deduction.py # 請假扣款計算器
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
├── scripts/               # 獨立執行腳本
│   └── process_leave_deduction.py  # 請假扣款處理腳本
├── templates/             # HTML 模板系統
│   └── html_templates.py  # 統一模板管理器（Bootstrap 5）
├── docs/                  # 專案文件
│   ├── reports_guide.md   # 報表系統指南
│   ├── template_system_guide.md  # 模板系統使用指南
│   └── testing_guide.md   # 測試指南
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

### 欄位標準化配置

系統自動將 Excel 中文欄位名稱轉換為標準化英文欄位名稱，存入資料庫。

在 `config.py` 中的 `ColumnNaming` 類別：

```python
class ColumnNaming:
    # 打卡資料欄位對照
    PUNCH_COLUMNS = {
        '序號': 'seq_no',
        '卡號': 'emp_id',
        '公務帳號': 'account_id',
        '人員姓名': 'name',
        '刷卡日期': 'punch_date',
        '刷卡時間': 'punch_time',
        # ...
    }

    # 班別資料欄位對照
    SHIFT_COLUMNS = {
        '班別': 'shift_class',
        '卡號': 'emp_id',
        '姓名': 'name',
        # ...
    }

    # 司機名單欄位對照
    DRIVER_COLUMNS = {
        '公務帳號': 'account_id',
        '卡號': 'emp_id',
        '姓名': 'name',
    }
```

**優勢**：
- ✅ 資料庫使用統一的英文欄位名稱
- ✅ 所有 SQL 查詢清晰易讀
- ✅ 避免欄位名稱不一致導致的 bug
- ✅ ETL 階段自動轉換，應用程式無需處理

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
- 整合打卡、班別與司機名單資料
- **自動欄位標準化**：Excel 中文欄位自動轉換為英文 snake_case 格式

### 報表生成
- 夜點津貼彙總表
- 單日打卡查詢（含列印版）
- 完整打卡記錄查詢（含列印版）
- 支援深色/淺色主題切換
- **統一 HTML 模板系統**：所有報表使用 Bootstrap 5 統一模板，一處修改全域生效
- 模組化報表架構（詳見 [docs/reports_guide.md](docs/reports_guide.md)）
- 模板系統使用指南（詳見 [docs/template_system_guide.md](docs/template_system_guide.md)）

### 請假扣款處理
- 解析請假資料（支援 .xls 與 .xlsx 格式）
- 自動計算傷病、事假扣款
- 整合員工班別資訊（從資料庫）
- 整合司機名單（從資料庫）
- 生成互動式 HTML 報表
- 支援命令列和 GUI 兩種操作方式

**命令列使用方式**：
```bash
# 使用預設檔案（data/work.xlsx）
python scripts/process_leave_deduction.py

# 指定請假資料檔案
python scripts/process_leave_deduction.py data/114年11月.xlsx

# 處理後自動開啟報表
python scripts/process_leave_deduction.py data/114年11月.xlsx --open
```

**GUI 使用方式**：在主介面點選「請假扣款處理」按鈕，選擇請假資料檔案即可。

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

CSV 格式，必要欄位：
- 公務帳號 或 卡號
- 姓名（可選）

**注意**：司機名單會在「資料整理」時自動載入到資料庫的 `driver_list` 表。

## 🗄️ 資料庫 Schema

執行「資料整理」後，資料庫包含以下表格（所有欄位已標準化為英文）：

### `punch` 表 - 打卡原始資料
- `seq_no`: 序號
- `emp_id`: 員工編號（卡號）
- `account_id`: 公務帳號
- `name`: 姓名
- `punch_date`: 打卡日期
- `punch_time`: 打卡時間
- `gate_name`: 門禁名稱
- `direction`: 進出狀態

### `shift_class` 表 - 班別資料
- `emp_id`: 員工編號（卡號）
- `account_id`: 公務帳號
- `name`: 姓名
- `shift_class`: 班別
- `shift_id`: 班次ID

### `driver_list` 表 - 司機名單
- `emp_id`: 員工編號（卡號）
- `account_id`: 公務帳號
- `name`: 姓名
- `is_driver`: 是否為司機（布林值）

### `integrated_punch` 表 - 整合資料
- `emp_id`: 員工編號（卡號）
- `account_id`: 公務帳號
- `name`: 姓名
- `shift_class`: 班別
- `punch_date`: 打卡日期
- `punch_time_1`, `punch_time_2`, ... : 各次打卡時間

## 🧪 測試

```bash
cd tests
python test_etl.py
```

## 📦 依賴套件

- pandas >= 1.5.0
- openpyxl >= 3.0.0
- xlrd == 1.2.0 (支援舊版 .xls 格式)
- pydantic >= 2.0.0
- FreeSimpleGUI >= 5.0.0
- pyinstaller >= 5.0.0 (打包用)

## 📝 版本歷史

### v2.1.1 - 模板系統統一與文件完善 (2025-12-14)
- 🎨 **統一 HTML 模板系統**：所有報表使用 `HtmlTemplateManager`，消除重複代碼
  - 增強模板支援自訂樣式與腳本
  - 降低維護成本，改樣式只需一處修改
  - 請假扣款報表重構使用統一模板（保留搜索、折疊、固定表頭等功能）
- 📚 **完善專案文件**：新增 `docs/template_system_guide.md` 模板系統使用指南
  - TL;DR 快速上手
  - 進階用法（自訂樣式/腳本）
  - 實際案例與最佳實踐
- 🔧 **建置改進**：build.cmd 自動創建必要資料夾 (data, db, output)

### v2.1 - 資料標準化與整合優化 (2025-12)
- ✨ **欄位標準化**：資料庫欄位統一使用英文 snake_case 命名
- ✨ **司機名單整合**：司機名單整合到資料庫，不再依賴外部 CSV
- 🔧 **請假扣款處理**：新增請假資料解析與扣款計算功能
- 📊 **互動式報表**：請假扣款生成 Bootstrap 5 互動式 HTML 報表
- 🚀 **自動化**：ETL Pipeline 自動處理欄位名稱轉換
- 📁 **模組化**：清晰的 library vs application 分離

### v2.0 - ETL 重構版
- 加入 Pydantic 驗證和設定導向架構
- 模組化報表生成系統

### v1.0 - 原始版本
- 基礎打卡資料處理 (main_app.py)
