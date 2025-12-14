# HTML 模板系統使用指南

## TL;DR（太長不看版）

**別自己寫 HTML 框架，用 `HtmlTemplateManager` 就對了。**

```python
from templates import HtmlTemplateManager

# 生成你的報表內容
content = "<h1>我的報表</h1><p>資料...</p>"

# 套用模板
html = HtmlTemplateManager.get_bootstrap_template("報表標題", content)

# 寫入檔案
with open("report.html", "w", encoding="utf-8") as f:
    f.write(html)
```

---

## 為什麼要用模板系統？

### ❌ **錯誤做法（別這樣做）**

```python
def generate_report(self):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link href="bootstrap...">
        <style>...</style>
    </head>
    <body>
        {content}
    </body>
    </html>
    """
```

**問題：**
- 每個報表都重複寫一次 HTML 框架
- 要升級 Bootstrap？改 10 個檔案
- 要改樣式？到處找

### ✅ **正確做法（這樣做）**

```python
from templates import HtmlTemplateManager

def generate_report(self):
    content = self._generate_content()
    html = HtmlTemplateManager.get_bootstrap_template("標題", content)
```

**優點：**
- 框架統一，改一個地方就好
- 專注在業務邏輯，不用管 HTML 結構
- 所有報表風格一致

---

## 基礎用法

### 1. 最簡單的報表

```python
from templates import HtmlTemplateManager

# 生成內容
content = """
<h1>單日打卡記錄</h1>
<table class="table">
    <tr><th>員工</th><th>時間</th></tr>
    <tr><td>張三</td><td>08:30</td></tr>
</table>
"""

# 套用模板
html = HtmlTemplateManager.get_bootstrap_template(
    title="單日打卡記錄",
    content=content
)

# 儲存
with open("output.html", "w", encoding="utf-8") as f:
    f.write(html)
```

**這樣你就有一個完整的 HTML，包含：**
- Bootstrap 5 樣式
- Font Awesome 圖示
- 響應式設計
- 深色模式切換

---

## 進階用法

### 2. 加入自訂樣式

如果你的報表需要特殊樣式：

```python
# 定義你的特殊樣式
custom_styles = """
.my-special-table {
    border: 2px solid red;
}
.highlight-row {
    background-color: yellow;
}
"""

# 套用模板時加入
html = HtmlTemplateManager.get_bootstrap_template(
    title="特殊報表",
    content=content,
    custom_styles=custom_styles  # ← 加這個
)
```

### 3. 加入自訂功能（JavaScript）

需要搜尋、排序、互動功能？

```python
# 定義你的功能
custom_scripts = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    // 搜尋功能
    const searchInput = document.getElementById('searchBox');
    searchInput.addEventListener('input', function() {
        // 你的搜尋邏輯
    });

    // 排序功能
    const sortButton = document.getElementById('sortBtn');
    sortButton.addEventListener('click', function() {
        // 你的排序邏輯
    });
});
</script>
"""

# 套用模板
html = HtmlTemplateManager.get_bootstrap_template(
    title="互動報表",
    content=content,
    custom_scripts=custom_scripts  # ← 加這個
)
```

---

## 實際案例

### 案例 1：請假扣款報表

```python
class LeaveDeductionCalculator:
    def generate_html_report(self, output_path: str):
        # 1. 生成報表內容（統計卡片、表格等）
        content = f"""
        <div class="page-header">
            <h1>請假扣款報表</h1>
        </div>

        <div class="stats-card">總扣款: ${total}</div>

        <table class="table">
            {table_html}
        </table>
        """

        # 2. 定義特殊功能
        custom_scripts = self._generate_custom_scripts()  # 搜尋、折疊等
        custom_styles = self._generate_custom_styles()    # 特殊樣式

        # 3. 套用模板
        html = HtmlTemplateManager.get_bootstrap_template(
            title="請假扣款報表",
            content=content,
            custom_scripts=custom_scripts,
            custom_styles=custom_styles
        )

        # 4. 儲存
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
```

### 案例 2：夜點費報表（更簡單）

```python
class NightMealReport:
    def generate(self, output_path: str):
        # 只需要生成內容，不需要特殊功能
        content = self._generate_content()

        # 直接套用基礎模板
        html = HtmlTemplateManager.get_bootstrap_template(
            title="夜點津貼彙總表",
            content=content
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
```

---

## 列印版報表

需要列印友善的版本？用 `get_printable_template()`：

```python
html = HtmlTemplateManager.get_printable_template(
    title="列印版報表",
    content=content
)
```

**差異：**
- 移除深色模式切換按鈕
- 優化列印樣式
- 更緊湊的排版
- 黑白友善

---

## 可用的 CSS 類別

模板已經包含以下常用樣式：

### 頁面結構
- `.page-header` - 漂亮的漸變色標題區
- `.section-card` - 區塊卡片
- `.section-header` - 區塊標題

### 統計卡片
- `.stats-card` - 統計數字卡片
- `.stats-number` - 大數字顯示

### 其他
- `.footer-info` - 頁尾資訊

### Bootstrap 5 所有類別都可用
- `table`, `table-hover`, `table-bordered`
- `btn`, `btn-primary`, `btn-secondary`
- `badge`, `bg-danger`, `bg-warning`
- `row`, `col-md-3`, `col-md-6`
- 等等...

---

## 輔助組件（HtmlComponentGenerator）

### 1. 標記司機

```python
from templates import HtmlComponentGenerator

name = HtmlComponentGenerator.mark_driver_account(
    name="張三",
    account="A001",
    driver_accounts={'A001', 'B002'}  # 司機帳號集合
)
# 輸出：<span class="badge bg-warning">司機</span>張三
```

### 2. 時間戳記著色

```python
timestamps = HtmlComponentGenerator.colorize_timestamps(
    ['08:30', '12:00', '13:00', '17:30']
)
# 奇數時間藍色，偶數時間紅色
```

### 3. 統計卡片

```python
card = HtmlComponentGenerator.generate_stats_card(
    title="總人數",
    value="150",
    icon="fas fa-users"
)
```

### 4. 統計卡片行

```python
stats = [
    {'title': '總人數', 'value': '150', 'icon': 'fas fa-users'},
    {'title': '總金額', 'value': '$12,000', 'icon': 'fas fa-dollar-sign'}
]
row = HtmlComponentGenerator.generate_stats_row(stats)
```

---

## 常見問題

### Q1: 我需要完全客製化的 HTML 怎麼辦？

**A:** 別這樣做。99% 的情況下，用 `custom_styles` 和 `custom_scripts` 就夠了。

如果真的需要，請：
1. 先問問自己是不是過度設計
2. 再問一次
3. 如果還是需要，考慮擴展 `HtmlTemplateManager`

### Q2: 可以改模板的基礎樣式嗎？

**A:** 可以，但要小心。改 `templates/html_templates.py` 會影響所有報表。

**正確做法：**
- 加新功能 → 用可選參數（`custom_scripts`, `custom_styles`）
- 改基礎樣式 → 確認不會破壞現有報表

### Q3: 為什麼不用 Jinja2 或其他模板引擎？

**A:** 因為我們不需要。

- 當前需求：生成靜態 HTML 報表
- f-string 已經夠用
- 不引入額外依賴
- Keep it simple

---

## 最佳實踐

### ✅ **DO（這樣做）**

```python
# 1. 業務邏輯和展示邏輯分離
def generate_html_report(self):
    data = self._calculate_data()      # 業務邏輯
    content = self._format_html(data)  # 展示邏輯
    html = HtmlTemplateManager.get_bootstrap_template(title, content)

# 2. 特殊功能獨立方法
def _generate_custom_scripts(self):
    return """<script>...</script>"""

# 3. 使用 Bootstrap 現有類別
content = '<div class="table-responsive"><table class="table">...'
```

### ❌ **DON'T（別這樣做）**

```python
# 1. 別自己寫完整 HTML
html = "<!DOCTYPE html><html>..."  # ✗

# 2. 別硬編碼樣式
html = '<div style="color: red">...'  # ✗ 用 CSS 類別

# 3. 別重複造輪子
def my_own_template_system():  # ✗ 我們已經有了
```

---

## 參考範例

專案中的實際使用案例：

1. **簡單報表**：`services/reports/daily_punch_report.py`
2. **複雜報表**：`core/leave_deduction.py`（有搜尋、折疊功能）
3. **列印報表**：`services/reports/printable_reports.py`

---

## API 參考

### HtmlTemplateManager.get_bootstrap_template()

```python
def get_bootstrap_template(
    title: str,              # 報表標題（顯示在瀏覽器標籤）
    content: str,            # 報表內容 HTML
    custom_scripts: str = "", # 自訂 JavaScript（可選）
    custom_styles: str = ""   # 自訂 CSS 樣式（可選）
) -> str:
    """
    生成完整的 Bootstrap 5 HTML 頁面

    包含：
    - Bootstrap 5.3.0
    - Font Awesome 6.4.0
    - 響應式設計
    - 深色模式切換
    """
```

### HtmlTemplateManager.get_printable_template()

```python
def get_printable_template(
    title: str,    # 報表標題
    content: str   # 報表內容
) -> str:
    """
    生成列印友善的 HTML 頁面

    特點：
    - 無深色模式切換
    - 優化列印樣式
    - 緊湊排版
    """
```

---

## 總結

**三個原則：**

1. **Don't Repeat Yourself** - 別重複寫 HTML 框架
2. **Keep It Simple** - 用現有的就好，別重新發明
3. **Separation of Concerns** - 業務邏輯歸業務，模板歸模板

**記住：**
> "The best code is no code. The second best is code you didn't write yourself."
> — 某個聰明人

用 `HtmlTemplateManager`，專注在你的業務邏輯上。
