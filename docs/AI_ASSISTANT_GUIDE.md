# AI 助手快速導覽指南

> **目的**: 幫助接手的 LLM 助手快速理解專案結構和開發脈絡

---

## 🎯 專案核心概念

**專案名稱**: 打卡系統資料處理工具 - ETL 重構版  
**核心架構**: Extract-Transform-Load (ETL) + Pydantic 驗證  
**主要語言**: Python  
**GUI 框架**: FreeSimpleGUI

### 一句話總結
使用 ETL 架構和 Pydantic 驗證，處理 Excel 打卡資料（民國年、4位數時間）並生成 HTML 報表的桌面應用程式。

---

## 📁 專案結構快速導覽

```
punch_helper_etl/
├── main.py                    # 主程式入口，初始化資料夾、檢查依賴、啟動 GUI
├── config.py                  # ⚙️ 重要！所有配置集中管理（路徑、Excel讀取設定、規則）
│
├── core/                      # 🔧 ETL 核心框架
│   ├── models.py             # Pydantic 資料模型（PunchRecord, ShiftClass）
│   ├── readers.py            # 資料讀取器（ExcelReader, CSVReader）
│   ├── validators.py         # 資料驗證器（DataValidator）
│   └── pipeline.py           # ETL 管道（PunchDataETL 是核心！）
│
├── services/                  # 🔄 業務邏輯
│   ├── data_service.py       # 資料處理（get_punch_data_for_date, get_night_meal_data）
│   ├── report_service.py     # 報表生成（各種 HTML 報表）
│   └── driver_service.py     # 司機名單管理
│
├── templates/                 # 📄 HTML 模板
│   └── html_templates.py     # Bootstrap 和列印版 HTML 模板
│
├── gui/                       # 🖥️ GUI 介面
│   └── main_window.py        # FreeSimpleGUI 主視窗
│
├── tests/                     # ✅ 單元測試
│   └── test_etl.py           # ETL 框架測試
│
├── docs/                      # 📚 文件
│   ├── README.md             # 文件索引
│   ├── testing_guide.md      # 測試指南
│   └── future_features/      # 預備開發功能
│       ├── shift_validation_design.md  # 班別驗證設計
│       └── README.md
│
├── data/                      # 📊 資料檔案（.gitignore 排除）
│   ├── 刷卡資料.xlsx         # 打卡資料（民國年、4位數時間）
│   └── list.xlsx             # 班別資料
│
├── db/                        # 💾 SQLite 資料庫（.gitignore 排除）
└── output/                    # 📤 輸出報表（.gitignore 排除）
```

---

## 🔑 關鍵檔案詳解

### 1. `config.py` - 配置中心 ⭐⭐⭐⭐⭐
**最重要的檔案！所有設定都在這裡**

```python
ExcelReadingConfig.PUNCH_DATA = {
    'skip_rows': 5,              # Excel 跳過前5行
    'filter_column': '序號',      # 用序號過濾有效資料
    'required_columns': [...],   # 必要欄位
    'column_mapping': {...},     # 欄位重新命名
}
```

**未來格式變更只需改這裡，不改程式碼！**

### 2. `core/pipeline.py` - ETL 核心 ⭐⭐⭐⭐⭐
**最核心的處理邏輯**

- `PunchDataETL.execute()` - 主要流程
  1. 讀取打卡資料（處理分頁 Excel）
  2. 轉換日期時間格式（民國年→西元年、HHMM→HH:MM:SS）
  3. 驗證資料（可選）
  4. 載入 SQLite
  5. 整合打卡與班別資料

### 3. `gui/main_window.py` - GUI 入口 ⭐⭐⭐⭐
**使用者操作界面**

主要功能：
- 資料整理（ETL 處理）
- 夜點津貼清單
- 單日打卡查詢
- 完整打卡記錄

### 4. `services/data_service.py` - 資料服務 ⭐⭐⭐
**業務邏輯處理**

關鍵方法：
- `process_data_organization()` - 執行 ETL
- `get_punch_data_for_date()` - 查詢單日資料
- `get_night_meal_data()` - 夜點統計

---

## 🔍 資料處理流程

### Excel 格式特性（重要！）

**打卡資料 Excel 結構**：
```
第1-5行:   標題資訊（跳過）
第6行:     欄位標題: 序號, 公務帳號, 身分證字號, 人員姓名, 刷卡日期, 刷卡時間, ...
第7-23行:  資料（第1頁）
第24-28行: 重複標題（用序號過濾掉）
第29行:    重複欄位標題
第30-x行:  資料（第2頁）
...分頁重複
```

**資料格式轉換**：
- 日期：`1140210` (民國114年) → `2025-02-10`
- 時間：`0830` → `08:30:00`

### 核心驗證邏輯

```python
# Pydantic 模型自動驗證
class PunchRecord(BaseModel):
    model_config = ConfigDict(extra='ignore')  # 忽略多餘欄位
    
    公務帳號: str
    刷卡日期: date  # 自動轉換民國年
    刷卡時間: time  # 自動轉換4位數
```

---

## 🛠️ 常見開發任務

### 任務 1: Excel 格式變更

**情境**: 前面多一行，第7行變成標題

**解決方案**:
```python
# config.py
ExcelReadingConfig.PUNCH_DATA['skip_rows'] = 6  # 改成6
```

### 任務 2: 新增欄位

**情境**: Excel 新增「部門」欄位

**解決方案**:
1. Pydantic 模型會自動忽略（`extra='ignore'`）
2. 如果需要使用，修改 `core/models.py`:
```python
class PunchRecord(BaseModel):
    # ... 現有欄位
    部門: Optional[str] = None  # 新增欄位
```

### 任務 3: 新增報表

**步驟**:
1. 在 `services/report_service.py` 新增方法
2. 在 `gui/main_window.py` 新增按鈕
3. 在 `templates/html_templates.py` 新增模板（如需要）

### 任務 4: 新增驗證規則

**步驟**:
1. 修改 `core/validators.py`
2. 寫測試 `tests/test_validators.py`
3. 執行測試確認

---

## 📝 開發注意事項

### 設定導向原則 ⭐⭐⭐⭐⭐
**所有可配置的參數都應該在 `config.py`，不要寫死在程式碼中！**

### 模組獨立測試
**每個模組都應該可以獨立測試**

```bash
# 測試資料模型
python -m unittest tests.test_etl.TestPunchRecordModel

# 測試驗證器
python -m unittest tests.test_validators
```

### Pydantic 驗證狀態
**目前採用「可選驗證」模式**：
- 驗證會執行，但不會阻斷資料載入
- 用於品質檢查，不影響功能運作

---

## 🔄 Git 工作流程

### 分支策略
```
main     # 穩定版本
└─ feature/xxx  # 新功能開發
```

### 提交訊息範例
```
Add shift validation design document for future development
Update config.py to support flexible Excel format
Fix: Incorrect date conversion for Taiwan calendar
```

---

## 📚 快速查找指令

### 查找功能實作位置
```bash
# 找 "夜點津貼" 在哪裡實作
grep -r "夜點津貼" --include="*.py"

# 找特定函數定義
grep -r "def get_night_meal_data" --include="*.py"
```

### 查看檔案結構
```bash
# 查看模組大綱
python -c "import ast; print(ast.dump(ast.parse(open('core/models.py').read())))"
```

---

## 🎯 常見問題速查

### Q: 如何新增一個組別的打卡規則？
**A**: 目前規則寫在程式碼中，未來版本會移到 `data/班別規則.xlsx`（見 `docs/future_features/`）

### Q: 打卡資料讀取失敗怎麼辦？
**A**: 檢查：
1. `config.py` 的 `skip_rows` 是否正確
2. Excel 是否有合併儲存格
3. `序號` 欄位是否存在

### Q: 如何修改報表樣式？
**A**: 修改 `templates/html_templates.py` 中的 CSS

### Q: 測試失敗怎麼辦？
**A**: 
1. 查看錯誤訊息定位問題
2. 檢查測試資料是否正確
3. 參考 `docs/testing_guide.md`

---

## 🚀 快速上手流程

### 接手新任務時的檢查清單

1. **理解需求**
   - [ ] 閱讀相關 issue/需求文件
   - [ ] 確認是修改現有功能還是新增功能

2. **定位相關檔案**
   - [ ] 在 `config.py` 查找相關設定
   - [ ] 在 `services/` 查找業務邏輯
   - [ ] 在 `core/` 查找底層實作

3. **寫測試**
   - [ ] 在 `tests/` 新增或修改測試
   - [ ] 執行測試確保不破壞現有功能

4. **實作修改**
   - [ ] 優先考慮修改設定而非程式碼
   - [ ] 保持模組獨立性
   - [ ] 加入必要的註解

5. **驗證**
   - [ ] 執行所有測試
   - [ ] GUI 手動測試
   - [ ] 更新文件

---

## 💡 進階主題

### 預備開發功能
**位置**: `docs/future_features/`

目前規劃的功能：
- 班別驗證系統（規則驅動）
- 異常打卡過濾
- 加班機制

**注意**: 這些是「設計」，不是「實作」，需先確認需求再開發

### 架構優勢
1. **設定導向**: 格式變更只需改 `config.py`
2. **型別安全**: Pydantic 確保資料正確
3. **模組化**: 易於測試和維護
4. **可擴展**: 新增功能不影響現有程式碼

---

## 📞 需要協助時

### 查閱文件
1. `README.md` - 專案介紹
2. `docs/testing_guide.md` - 測試指南
3. `docs/future_features/` - 未來功能設計

### 程式碼範例
- `tests/test_etl.py` - 測試範例
- `core/pipeline.py` - ETL 實作範例
- `services/report_service.py` - 業務邏輯範例

---

**最後更新**: 2025-12-07  
**維護者**: 開發團隊
