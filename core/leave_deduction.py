"""
請假扣款計算器
計算扣款金額並生成 HTML 報表
"""

import pandas as pd
import math
from datetime import datetime
from typing import Dict

# 從專案現有的模板導入
try:
    from templates.html_templates import HtmlTemplateManager
    USE_PROJECT_TEMPLATE = True
except ImportError:
    USE_PROJECT_TEMPLATE = False


# ========================================================================
# 扣款規則設定區（可自訂）
# ========================================================================

# 扣款費率（元）- 階梯式費率表
DEDUCTION_RATES = {
    "事假": {
        "全天": 333,
        "半天": 167,
    },
    "傷病": {
        "全天": 167,
        "半天": 84,
    },
}

# 進位單位（天）
ROUNDING_UNIT = 0.5

# 規則說明
RULES_DESCRIPTION = {
    "事假": "1天=$333, 半天=$167, 1小時=算半天=$167",
    "傷病": "1天=$167, 半天=$84, 1小時=算半天=$84",
    "生理假": "生理假算傷病",
    "其他": "其他假別（特休、補休等）不計算扣款",
    "備註": "不滿半天以半天計算（0.5 為單位無條件進位）",
}


def calculate_deduction(leave_type: str, leave_day: float) -> int:
    """
    計算扣款金額

    Args:
        leave_type: 假別
        leave_day: 請假天數

    Returns:
        扣款金額（元）
    """
    if leave_type not in DEDUCTION_RATES:
        return 0

    if leave_day <= 0:
        return 0

    # 以設定的單位無條件進位
    adjusted_day = math.ceil(leave_day / ROUNDING_UNIT) * ROUNDING_UNIT

    # 取得費率表
    rates = DEDUCTION_RATES[leave_type]

    # 判斷是半天還是全天
    if adjusted_day <= 0.5:
        return rates["半天"]
    else:
        return rates["全天"]


def format_leave_type(leave_type: str, source_text: str) -> str:
    """
    格式化假別顯示
    生理假會顯示為 傷病(生理)

    Args:
        leave_type: 假別
        source_text: 原始文字

    Returns:
        格式化後的假別
    """
    if leave_type == "傷病" and "生理" in str(source_text):
        return "傷病(生理)"
    return leave_type


class LeaveDeductionCalculator:
    """請假扣款計算器"""

    def __init__(self, leave_df: pd.DataFrame, employee_info: pd.DataFrame = None, driver_accounts: set = None):
        """
        Args:
            leave_df: 請假資料 DataFrame
            employee_info: 員工資訊 DataFrame（包含 emp_id, 班別等）
            driver_accounts: 司機帳號集合
        """
        self.df = leave_df.copy()
        self.employee_info = employee_info if employee_info is not None else pd.DataFrame()
        self.driver_accounts = driver_accounts if driver_accounts is not None else set()

        # 如果有員工資訊，合併到請假資料
        if not self.employee_info.empty and 'emp_id' in self.df.columns:
            # 確保 employee_info 有 emp_id 欄位（可能是 卡號 或 公務帳號）
            if '卡號' in self.employee_info.columns and 'emp_id' not in self.employee_info.columns:
                self.employee_info = self.employee_info.rename(columns={'卡號': 'emp_id'})
            elif '公務帳號' in self.employee_info.columns and 'emp_id' not in self.employee_info.columns:
                self.employee_info = self.employee_info.rename(columns={'公務帳號': 'emp_id'})

            # 確保有班別欄位（可能是 shift_class 或 班別）
            shift_col = 'shift_class' if 'shift_class' in self.employee_info.columns else '班別'

            # 合併員工資訊
            self.df = self.df.merge(
                self.employee_info[['emp_id', shift_col]].drop_duplicates(),
                on='emp_id',
                how='left'
            )

            # 統一欄位名稱為 shift_class
            if shift_col == '班別':
                self.df = self.df.rename(columns={'班別': 'shift_class'})

    def calculate(self) -> pd.DataFrame:
        """
        計算扣款

        Returns:
            包含扣款欄位的 DataFrame
        """
        self.df["deduction"] = self.df.apply(
            lambda row: calculate_deduction(row["leave_type"], row["leave_day"]),
            axis=1
        )
        return self.df

    def generate_monthly_summary(self) -> pd.DataFrame:
        """
        生成每月彙總

        Returns:
            彙總 DataFrame
        """
        summary_data = []

        for (emp_id, name), group in self.df.groupby(["emp_id", "name"]):
            # 取得班別（如果有）
            shift_class = group['shift_class'].iloc[0] if 'shift_class' in group.columns else "-"

            # 判斷是否為司機
            is_driver = emp_id in self.driver_accounts if self.driver_accounts else False

            # 傷病統計
            sick_leave = group[group["leave_type"] == "傷病"]
            sick_days = sick_leave["leave_day"].sum() if len(sick_leave) > 0 else 0
            sick_deduction = sick_leave["deduction"].sum() if len(sick_leave) > 0 else 0

            # 事假統計
            personal_leave = group[group["leave_type"] == "事假"]
            personal_days = personal_leave["leave_day"].sum() if len(personal_leave) > 0 else 0
            personal_deduction = personal_leave["deduction"].sum() if len(personal_leave) > 0 else 0

            # 其他假別統計
            other_leave = group[~group["leave_type"].isin(["傷病", "事假"])]
            other_types = ", ".join(other_leave["leave_type"].unique()) if len(other_leave) > 0 else "-"
            other_days = other_leave["leave_day"].sum() if len(other_leave) > 0 else 0

            # 總扣款
            total_deduction = sick_deduction + personal_deduction

            summary_data.append({
                "emp_id": emp_id,
                "name": name,
                "shift_class": shift_class,
                "is_driver": is_driver,
                "sick_days": sick_days,
                "sick_deduction": sick_deduction,
                "personal_days": personal_days,
                "personal_deduction": personal_deduction,
                "other_types": other_types,
                "other_days": other_days,
                "total_deduction": total_deduction,
            })

        return pd.DataFrame(summary_data).sort_values("emp_id")

    def generate_html_report(self, output_path: str, monthly_summary: pd.DataFrame = None):
        """
        生成 HTML 報表

        Args:
            output_path: 輸出檔案路徑
            monthly_summary: 月彙總 DataFrame（可選）
        """
        if monthly_summary is None:
            monthly_summary = self.generate_monthly_summary()

        # 統計資訊
        total_employees = self.df["emp_id"].nunique()
        total_sick_deduction = monthly_summary["sick_deduction"].sum()
        total_personal_deduction = monthly_summary["personal_deduction"].sum()
        total_deduction = monthly_summary["total_deduction"].sum()

        # 生成統計卡片
        stats_html = f"""
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="stats-card">
                    <div class="stats-number">{total_employees}</div>
                    <div>請假員工數</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stats-card bg-danger">
                    <div class="stats-number">${int(total_sick_deduction):,}</div>
                    <div>傷病總扣款</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stats-card bg-warning">
                    <div class="stats-number">${int(total_personal_deduction):,}</div>
                    <div>事假總扣款</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stats-card bg-dark">
                    <div class="stats-number">${int(total_deduction):,}</div>
                    <div>總扣款金額</div>
                </div>
            </div>
        </div>
        """

        # 每月彙總表格
        monthly_html = self._generate_monthly_table(monthly_summary)

        # 每日明細表格
        daily_html = self._generate_daily_table()

        # 完整內容
        content = f"""
        <div class="page-header">
            <h1>請假扣款報表</h1>
            <div class="subtitle">
                報表產生時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </div>
        </div>

        {stats_html}
        {monthly_html}
        {daily_html}

        <div class="footer-info">
            <p><strong>扣款規則：</strong></p>
            <p>• {RULES_DESCRIPTION.get("事假", "")}</p>
            <p>• {RULES_DESCRIPTION.get("傷病", "")}</p>
            <p>• {RULES_DESCRIPTION.get("生理假", "")}</p>
            <p>• {RULES_DESCRIPTION.get("其他", "")}</p>
            <p class="text-muted small mt-2">※ {RULES_DESCRIPTION.get("備註", "")}</p>
        </div>

        <!-- 浮動搜尋框 -->
        <div class="search-box" id="searchBox">
            <div class="input-group input-group-sm">
                <input type="text" class="form-control" id="searchInput" placeholder="輸入店號或姓名" autocomplete="off">
                <button class="btn btn-primary" type="button" id="searchBtn">
                    <i class="fas fa-search"></i>
                </button>
                <button class="btn btn-secondary" type="button" id="clearBtn" title="清除">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div id="searchResults" class="search-results mt-2"></div>
        </div>
        """

        # 使用模板
        html = self._get_bootstrap_template("請假扣款報表", content)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"報表已生成: {output_path}")

    def _generate_monthly_table(self, monthly_summary: pd.DataFrame) -> str:
        """生成每月彙總表格 HTML"""
        monthly_table_rows = []

        for _, row in monthly_summary.iterrows():
            emp_id = row['emp_id']
            emp_details = self.df[self.df['emp_id'] == emp_id].sort_values('date')

            detail_rows = []
            for _, detail in emp_details.iterrows():
                display_leave_type = format_leave_type(detail['leave_type'], detail['source_text'])

                if detail['leave_type'] == "傷病":
                    badge_color = "danger"
                    amount_color = "text-danger"
                elif detail['leave_type'] == "事假":
                    badge_color = "warning"
                    amount_color = "text-warning"
                else:
                    badge_color = "secondary"
                    amount_color = "text-muted"

                if detail['deduction'] > 0:
                    deduction_display = f'<span class="{amount_color} fw-bold">${int(detail["deduction"]):,}</span>'
                else:
                    deduction_display = '<span class="text-muted">-</span>'

                detail_rows.append(f"""
                    <tr>
                        <td>{detail['date']} ({detail['weekday_zh']})</td>
                        <td><span class="badge bg-{badge_color}">{display_leave_type}</span></td>
                        <td class="text-end">{detail['leave_day']:.2f}</td>
                        <td class="text-end">{deduction_display}</td>
                    </tr>
                """)

            detail_html = f"""
                <table class="table table-sm table-bordered mb-0">
                    <thead class="table-secondary">
                        <tr>
                            <th width="25%">日期</th>
                            <th width="25%">假別</th>
                            <th width="25%" class="text-end">天數</th>
                            <th width="25%" class="text-end">扣款金額</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(detail_rows) if detail_rows else '<tr><td colspan="4" class="text-center text-muted">無請假記錄</td></tr>'}
                    </tbody>
                </table>
            """ if detail_rows else '<p class="text-center text-muted p-3 mb-0">無請假記錄</p>'

            # 班別和司機標記
            shift_display = row.get('shift_class', '-')
            driver_badge = '<span class="badge bg-warning text-dark">司機</span>' if row.get('is_driver', False) else ''

            monthly_table_rows.append(f"""
            <tr class="summary-row" data-bs-toggle="collapse" data-bs-target="#detail-{emp_id}" style="cursor: pointer;">
                <td><i class="fas fa-chevron-right collapse-icon me-2"></i>{row['emp_id']}</td>
                <td>{driver_badge} {row['name']}</td>
                <td>{shift_display}</td>
                <td class="text-end">{row['sick_days']:.2f}</td>
                <td class="text-end text-danger fw-bold">${int(row['sick_deduction']):,}</td>
                <td class="text-end">{row['personal_days']:.2f}</td>
                <td class="text-end text-warning fw-bold">${int(row['personal_deduction']):,}</td>
                <td>{row['other_types']}</td>
                <td class="text-end">{row['other_days']:.2f}</td>
                <td class="text-end fw-bold">${int(row['total_deduction']):,}</td>
            </tr>
            <tr class="collapse detail-row" id="detail-{emp_id}">
                <td colspan="10" class="p-0">
                    <div class="detail-container p-3 bg-light">
                        <h6 class="mb-3"><i class="fas fa-calendar-alt me-2"></i>{row['name']} 的扣款明細</h6>
                        {detail_html}
                    </div>
                </td>
            </tr>
            """)

        return f"""
        <div class="section-card">
            <h3 class="section-header">
                每月扣款彙總
                <small class="float-end fs-6 opacity-75"><i class="fas fa-hand-pointer me-1"></i>點擊展開明細</small>
            </h3>
            <div class="table-responsive p-3">
                <table class="table table-hover table-bordered">
                    <thead class="table-light">
                        <tr>
                            <th>員工編號</th>
                            <th>姓名</th>
                            <th>班別</th>
                            <th class="text-end">傷病天數</th>
                            <th class="text-end">傷病扣款</th>
                            <th class="text-end">事假天數</th>
                            <th class="text-end">事假扣款</th>
                            <th>其他假別</th>
                            <th class="text-end">其他天數</th>
                            <th class="text-end">總扣款</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(monthly_table_rows)}
                    </tbody>
                </table>
            </div>
        </div>
        """

    def _generate_daily_table(self) -> str:
        """生成每日明細表格 HTML"""
        daily_sections = []

        for (emp_id, name), group in self.df.groupby(["emp_id", "name"]):
            group_sorted = group.sort_values("date")

            daily_rows = []
            for _, row in group_sorted.iterrows():
                display_leave_type = format_leave_type(row['leave_type'], row['source_text'])

                if row["leave_type"] == "傷病":
                    deduction_class = "text-danger"
                    badge_color = "danger"
                elif row["leave_type"] == "事假":
                    deduction_class = "text-warning"
                    badge_color = "warning"
                else:
                    deduction_class = ""
                    badge_color = "secondary"

                daily_rows.append(f"""
                <tr>
                    <td>{row['date']} ({row['weekday_zh']})</td>
                    <td><span class="badge bg-{badge_color}">{display_leave_type}</span></td>
                    <td class="text-end">{row['leave_day']:.2f}</td>
                    <td class="text-end {deduction_class} fw-bold">${int(row['deduction']):,}</td>
                    <td class="text-muted small">{row['source_text']}</td>
                </tr>
                """)

            emp_total = group["deduction"].sum()

            daily_sections.append(f"""
            <div class="employee-section" id="emp-{emp_id}" data-emp-id="{emp_id}" data-name="{name}">
                <h5 class="employee-header">
                    {emp_id} - {name}
                    <span class="float-end text-primary">小計: ${int(emp_total):,}</span>
                </h5>
                <div class="table-responsive">
                    <table class="table table-sm table-hover table-bordered daily-table">
                        <thead class="table-light">
                            <tr>
                                <th width="15%">日期</th>
                                <th width="15%">假別</th>
                                <th width="12%" class="text-end">天數</th>
                                <th width="15%" class="text-end">扣款</th>
                                <th width="43%">原始記錄</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(daily_rows)}
                        </tbody>
                    </table>
                </div>
            </div>
            """)

        return f"""
        <div class="section-card">
            <h3 class="section-header">每日扣款明細</h3>
            <div class="p-3">
                {''.join(daily_sections)}
            </div>
        </div>
        """

    def _get_bootstrap_template(self, title: str, content: str) -> str:
        """取得 Bootstrap HTML 模板"""
        return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body {{ font-family: 'Segoe UI', 'Microsoft JhengHei', sans-serif; }}
        .page-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 15px; margin-bottom: 30px; text-align: center; }}
        .stats-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
        .stats-number {{ font-size: 2rem; font-weight: bold; }}
        .section-card {{ border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 30px; overflow: hidden; }}
        .section-header {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 15px 25px; margin: 0; }}
        .employee-section {{ border: 1px solid #dee2e6; border-radius: 8px; overflow: hidden; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .employee-header {{ background-color: #f8f9fa !important; margin: 0; padding: 12px 15px; border-bottom: 2px solid #dee2e6; }}
        .daily-table {{ margin-bottom: 0 !important; }}
        .daily-table th {{ font-weight: 600; background-color: #f8f9fa; border-bottom: 2px solid #dee2e6; }}
        .daily-table td {{ vertical-align: middle; }}
        .footer-info {{ text-align: center; padding: 20px; color: #666; font-size: 0.9rem; }}
        .summary-row:hover {{ background-color: #f8f9fa !important; }}
        .summary-row {{ transition: background-color 0.2s; }}
        .detail-row > td {{ border-top: none !important; }}
        .detail-container {{ border-top: 2px solid #dee2e6; }}
        .collapse-icon {{ transition: transform 0.2s; display: inline-block; }}
        .summary-row[aria-expanded="true"] .collapse-icon {{ transform: rotate(90deg); }}
        .search-box {{ position: fixed; bottom: 80px; right: 20px; z-index: 1000; background: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); width: 300px; }}
        .search-results {{ max-height: 300px; overflow-y: auto; font-size: 0.9rem; }}
        .search-result-item {{ padding: 8px 12px; cursor: pointer; border-radius: 5px; margin-bottom: 5px; background: #f8f9fa; transition: background 0.2s; }}
        .search-result-item:hover {{ background: #e9ecef; }}
        .employee-section.highlight {{ animation: highlightAnim 2s; }}
        @keyframes highlightAnim {{ 0%, 100% {{ background-color: transparent; }} 50% {{ background-color: #fff3cd; }} }}
        .fixed-header {{ position: fixed; top: 0; z-index: 1020; background: white; box-shadow: 0 2px 10px rgba(0,0,0,0.1); opacity: 0; visibility: hidden; transition: opacity 0.2s; }}
        .fixed-header.active {{ opacity: 1; visibility: visible; }}
        .fixed-header thead {{ background-color: #f8f9fa; }}
        .fixed-header th {{ border-top: none; }}
    </style>
</head>
<body class="bg-light">
    <div class="container-fluid">
        <div class="container bg-white p-4 my-4 rounded shadow">
            {content}
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const collapsibleRows = document.querySelectorAll('[data-bs-toggle="collapse"]');
            collapsibleRows.forEach(row => {{
                const target = row.getAttribute('data-bs-target');
                const collapseElement = document.querySelector(target);
                if (collapseElement) {{
                    collapseElement.addEventListener('show.bs.collapse', function() {{ row.setAttribute('aria-expanded', 'true'); }});
                    collapseElement.addEventListener('hide.bs.collapse', function() {{ row.setAttribute('aria-expanded', 'false'); }});
                }}
            }});

            const searchInput = document.getElementById('searchInput');
            const searchBtn = document.getElementById('searchBtn');
            const clearBtn = document.getElementById('clearBtn');
            const searchResults = document.getElementById('searchResults');

            function searchEmployee(keyword) {{
                if (!keyword.trim()) {{ searchResults.innerHTML = ''; return; }}
                const sections = document.querySelectorAll('.employee-section');
                const matches = [];
                sections.forEach(section => {{
                    const empId = section.dataset.empId || '';
                    const name = section.dataset.name || '';
                    if (empId.includes(keyword) || name.includes(keyword)) {{
                        matches.push({{ empId: empId, name: name, element: section }});
                    }}
                }});
                if (matches.length === 0) {{
                    searchResults.innerHTML = '<div class="text-muted small">找不到相符的員工</div>';
                }} else if (matches.length === 1) {{
                    scrollToEmployee(matches[0].element, true);
                }} else {{
                    let html = '<div class="small text-muted mb-2">找到 ' + matches.length + ' 位員工：</div>';
                    matches.forEach(match => {{
                        html += '<div class="search-result-item" data-emp-id="' + match.empId + '">' +
                                '<strong>' + match.empId + '</strong> - ' + match.name + '</div>';
                    }});
                    searchResults.innerHTML = html;
                    document.querySelectorAll('.search-result-item').forEach(item => {{
                        item.addEventListener('click', function() {{
                            const empId = this.dataset.empId;
                            const section = document.getElementById('emp-' + empId);
                            if (section) {{ scrollToEmployee(section, true); }}
                        }});
                    }});
                }}
            }}

            function scrollToEmployee(element, clearSearch) {{
                element.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                element.classList.add('highlight');
                setTimeout(() => element.classList.remove('highlight'), 2000);
                if (clearSearch) {{
                    setTimeout(() => {{ searchInput.value = ''; searchResults.innerHTML = ''; }}, 100);
                }}
            }}

            searchInput.addEventListener('input', function() {{ searchEmployee(this.value); }});
            searchBtn.addEventListener('click', function() {{ searchEmployee(searchInput.value); }});
            searchInput.addEventListener('keypress', function(e) {{ if (e.key === 'Enter') {{ searchEmployee(this.value); }} }});
            clearBtn.addEventListener('click', function() {{ searchInput.value = ''; searchResults.innerHTML = ''; searchInput.focus(); }});

            // 固定表頭功能
            const summaryTable = document.querySelector('.section-card .table-hover');
            if (summaryTable) {{
                const originalHeader = summaryTable.querySelector('thead');
                if (originalHeader) {{
                    const fixedTable = summaryTable.cloneNode(false);
                    fixedTable.classList.add('fixed-header', 'table', 'table-hover', 'table-bordered');
                    const fixedHeader = originalHeader.cloneNode(true);
                    fixedTable.appendChild(fixedHeader);
                    document.body.appendChild(fixedTable);

                    function updateFixedHeader() {{
                        const tableRect = summaryTable.getBoundingClientRect();
                        const headerRect = originalHeader.getBoundingClientRect();
                        if (headerRect.top < 0 && tableRect.bottom > 40) {{
                            fixedTable.classList.add('active');
                            fixedTable.style.width = summaryTable.offsetWidth + 'px';
                            fixedTable.style.left = tableRect.left + 'px';
                            const originalCells = originalHeader.querySelectorAll('th');
                            const fixedCells = fixedHeader.querySelectorAll('th');
                            originalCells.forEach((cell, index) => {{
                                if (fixedCells[index]) {{ fixedCells[index].style.width = cell.offsetWidth + 'px'; }}
                            }});
                        }} else {{
                            fixedTable.classList.remove('active');
                        }}
                    }}
                    window.addEventListener('scroll', updateFixedHeader);
                    window.addEventListener('resize', updateFixedHeader);
                }}
            }}
        }});
    </script>
</body>
</html>"""
