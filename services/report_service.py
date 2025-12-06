"""
報表生成服務 - 生成各種 HTML 報表
"""

import os
import webbrowser
import sqlite3
import pandas as pd
from typing import Callable, Dict, Set
from datetime import datetime

from config import AppConfig, PathManager
from templates import HtmlTemplateManager, HtmlComponentGenerator


class ReportService:
    """報表生成服務"""
    
    def __init__(self, output_callback: Callable = None):
        self.output_callback = output_callback or (lambda x: None)
        self.path_mgr = PathManager()
    
    def generate_daily_punch_report(self, df: pd.DataFrame, date_str: str, driver_accounts: Set[str]) -> str:
        """生成單日打卡報表"""
        content = self._generate_daily_punch_content(df, date_str, driver_accounts)
        html = HtmlTemplateManager.get_bootstrap_template(f"單日打卡記錄 - {date_str}", content)
        
        output_file = os.path.join(self.path_mgr.get_output_dir(), f'punch_record_{date_str}.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.output_callback(f"報表已生成: {output_file}")
        self._auto_open(output_file)
        return output_file
    
    def generate_full_punch_report(self, df: pd.DataFrame, driver_accounts: Set[str]) -> str:
        """生成完整打卡報表"""
        content = self._generate_full_punch_content(df, driver_accounts)
        html = HtmlTemplateManager.get_bootstrap_template("完整打卡記錄總表", content)
        
        output_file = os.path.join(self.path_mgr.get_output_dir(), 'full_punch_record_report.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.output_callback(f"報表已生成: {output_file}")
        self._auto_open(output_file)
        return output_file
    
    def generate_night_meal_report(self, df: pd.DataFrame, driver_accounts: Set[str]) -> str:
        """生成夜點津貼報表"""
        content = self._generate_night_meal_content(df, driver_accounts)
        html = HtmlTemplateManager.get_bootstrap_template("夜點津貼彙總表", content)
        
        output_file = os.path.join(self.path_mgr.get_output_dir(), 'combined_night_meal_report.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.output_callback(f"報表已生成: {output_file}")
        self._auto_open(output_file)
        return output_file
    
    def generate_printable_daily_report(self, df: pd.DataFrame, date_str: str, driver_accounts: Set[str]) -> str:
        """生成列印版單日報表"""
        content = self._generate_printable_daily_content(df, date_str, driver_accounts)
        html = HtmlTemplateManager.get_printable_template(f"單日打卡記錄 - {date_str}", content)
        
        output_file = os.path.join(self.path_mgr.get_output_dir(), f'punch_record_{date_str}_print.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.output_callback(f"列印版報表已生成: {output_file}")
        self._auto_open(output_file)
        return output_file
    
    def generate_printable_full_report(self, df: pd.DataFrame, driver_accounts: Set[str]) -> str:
        """生成列印版完整報表"""
        content = self._generate_printable_full_content(df, driver_accounts)
        html = HtmlTemplateManager.get_printable_template("完整打卡記錄總表 (列印版)", content)
        
        output_file = os.path.join(self.path_mgr.get_output_dir(), 'punch_by_account_print.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.output_callback(f"列印版報表已生成: {output_file}")
        self._auto_open(output_file)
        return output_file
    
    def _auto_open(self, file_path: str):
        """自動開啟 HTML 檔案"""
        try:
            if os.path.exists(file_path):
                webbrowser.open(f'file:///{os.path.abspath(file_path)}')
                self.output_callback(f"📊 已在瀏覽器中開啟報表")
        except Exception as e:
            self.output_callback(f"開啟檔案失敗: {e}")
    
    def _generate_daily_punch_content(self, df: pd.DataFrame, date_str: str, driver_accounts: Set[str]) -> str:
        """生成單日打卡內容"""
        total = len(df)
        classes = df['班別'].nunique()
        drivers = len(df[df['公務帳號'].isin(driver_accounts)])
        
        content = f"""
        <div class="page-header">
            <h1><i class="fas fa-calendar-day me-3"></i>單日打卡記錄</h1>
            <div class="subtitle">查詢日期：{date_str}</div>
        </div>
        """
        
        stats = [
            {"title": "總打卡記錄", "value": str(total), "icon": "fas fa-users"},
            {"title": "班別數量", "value": str(classes), "icon": "fas fa-layer-group"},
            {"title": "司機人數", "value": str(drivers), "icon": "fas fa-star"}
        ]
        content += HtmlComponentGenerator.generate_stats_row(stats)
        
        for class_name, group in df.groupby('班別'):
            content += f"""
            <div class="section-card">
                <h3 class="section-header">
                    <i class="fas fa-users-cog me-2"></i>{class_name}
                    <span class="badge bg-light text-dark ms-2">{len(group)} 人</span>
                </h3>
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead class="table-dark">
                            <tr>
                                <th>卡號</th><th>公務帳號</th><th>姓名</th>
                                <th>打卡次數</th><th>時間戳記</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for _, row in group.iterrows():
                name = HtmlComponentGenerator.mark_driver_account(row['姓名'], row['公務帳號'], driver_accounts)
                timestamps = HtmlComponentGenerator.colorize_timestamps(row['所有時間戳記'].split(', '))
                
                content += f"""
                            <tr>
                                <td><strong>{row['卡號']}</strong></td>
                                <td><code>{row['公務帳號']}</code></td>
                                <td>{name}</td>
                                <td><span class="badge bg-primary">{row['打卡次數']}</span></td>
                                <td class="text-start">{timestamps}</td>
                            </tr>
                """
            
            content += "</tbody></table></div></div>"
        
        content += f"""
        <div class="footer-info">
            <i class="fas fa-info-circle me-2"></i>
            生成時間：{datetime.now().strftime(AppConfig.DISPLAY_DATETIME_FORMAT)} | 
            共 {total} 筆記錄，{classes} 個班別
        </div>
        """
        
        return content
    
    def _generate_full_punch_content(self, df: pd.DataFrame, driver_accounts: Set[str]) -> str:
        """生成完整打卡內容"""
        total_employees = df['卡號'].nunique()
        total_records = len(df)
        date_range = f"{df['日期'].min()} ~ {df['日期'].max()}"
        
        driver_count = 0
        if driver_accounts:
            driver_count = len(set(df[df['公務帳號'].isin(driver_accounts)]['公務帳號'].unique()))
        
        content = f"""
        <div class="page-header">
            <h1><i class="fas fa-calendar-check me-3"></i>完整打卡記錄</h1>
            <div class="subtitle">員工打卡記錄總表（按卡號分組）</div>
        </div>
        
        <div class="row mb-4">
            <div class="col-lg-3 col-md-6 mb-3">
                <div class="stats-card">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-users fa-2x me-3"></i>
                        <div><div class="stats-number">{total_employees}</div><div>總員工數</div></div>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 mb-3">
                <div class="stats-card">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-clock fa-2x me-3"></i>
                        <div><div class="stats-number">{total_records}</div><div>總記錄數</div></div>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 mb-3">
                <div class="stats-card">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-star fa-2x me-3"></i>
                        <div><div class="stats-number">{driver_count}</div><div>司機</div></div>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 mb-3">
                <div class="stats-card">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-calendar-alt fa-2x me-3"></i>
                        <div><div class="stats-number" style="font-size: 1rem;">{date_range}</div><div>日期範圍</div></div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-md-6 mx-auto">
                <div class="input-group">
                    <span class="input-group-text"><i class="fas fa-search"></i></span>
                    <input type="text" id="globalSearch" class="form-control" placeholder="搜尋卡號、公務帳號、姓名或班別...">
                </div>
            </div>
        </div>
        """
        
        for card_number, group in df.groupby('卡號'):
            accounts = '、'.join(map(str, group['公務帳號'].unique()))
            names = group['姓名'].unique()
            classes = '、'.join(map(str, group['班別'].unique()))
            
            # 處理司機標記
            formatted_names = []
            for name in names:
                emp_accounts = group[group['姓名'] == name]['公務帳號'].unique()
                is_driver = any(acc in driver_accounts for acc in emp_accounts) if driver_accounts else False
                if is_driver:
                    formatted_names.append(f'{name} <span class="badge bg-danger text-white ms-1">司機</span>')
                else:
                    formatted_names.append(str(name))
            names_display = '、'.join(formatted_names)
            
            punch_days = len(group[group['打卡次數'] > 0])
            total_days = len(group)
            
            content += f"""
            <div class="section-card employee-card" data-search="{card_number} {accounts} {' '.join(map(str, names))} {classes}">
                <div class="section-header d-flex justify-content-between align-items-center">
                    <div>
                        <i class="fas fa-user-circle me-2"></i>
                        <strong>卡號：{card_number}</strong>
                        <strong class="ms-3">{names_display}</strong>
                    </div>
                    <div>
                        <span class="badge bg-info me-1">{classes}</span>
                        <span class="badge bg-success">{punch_days}/{total_days} 天</span>
                    </div>
                </div>
                <div class="p-3">
                    <div class="table-responsive">
                        <table class="table table-sm table-hover">
                            <thead class="table-dark">
                                <tr>
                                    <th width="12%">日期</th><th width="8%">星期</th>
                                    <th width="10%">打卡次數</th><th>時間戳記</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            
            for _, row in group.iterrows():
                timestamps = HtmlComponentGenerator.colorize_timestamps(
                    [t for t in row['所有時間戳記'].split(', ') if t]
                ) if row['所有時間戳記'] else '<span class="text-muted">無打卡記錄</span>'
                
                punch = row['打卡次數']
                if punch == 0:
                    badge = '<span class="badge bg-danger">0</span>'
                elif punch <= 2:
                    badge = f'<span class="badge bg-warning text-dark">{punch}</span>'
                else:
                    badge = f'<span class="badge bg-success">{punch}</span>'
                
                content += f"""
                                <tr>
                                    <td><strong>{row['日期']}</strong></td>
                                    <td><span class="badge bg-secondary">{row['星期']}</span></td>
                                    <td>{badge}</td>
                                    <td class="text-start">{timestamps}</td>
                                </tr>
                """
            
            content += "</tbody></table></div></div></div>"
        
        content += """
        <script>
            document.getElementById('globalSearch').addEventListener('keyup', function() {
                const term = this.value.toLowerCase();
                document.querySelectorAll('.employee-card').forEach(card => {
                    const data = card.getAttribute('data-search').toLowerCase();
                    card.style.display = data.includes(term) ? 'block' : 'none';
                });
            });
        </script>
        
        <div class="alert alert-info">
            <h5><i class="fas fa-info-circle me-2"></i>說明</h5>
            <ul class="mb-0">
                <li><span class="badge bg-danger text-white">司機</span> 標籤：司機名單中的司機</li>
                <li><strong>奇數次打卡</strong>：<span class="timestamp-odd">藍色時間戳記</span></li>
                <li><strong>偶數次打卡</strong>：<span class="timestamp-even">紅色時間戳記</span></li>
            </ul>
        </div>
        """
        
        content += f"""
        <div class="footer-info">
            <i class="fas fa-info-circle me-2"></i>
            生成時間：{datetime.now().strftime(AppConfig.DISPLAY_DATETIME_FORMAT)} | 
            共 {total_employees} 位員工，{total_records} 筆記錄
        </div>
        """
        
        return content
    
    def _generate_night_meal_content(self, df: pd.DataFrame, driver_accounts: Set[str]) -> str:
        """生成夜點津貼內容"""
        # 處理統計
        df['月份'] = df['月份'].astype(str) + '月'
        
        conn = sqlite3.connect(':memory:')
        df.to_sql('data', conn, index=False)
        summary = pd.read_sql("""
            SELECT 班別, 卡號, 公務帳號, 姓名, 月份,
                   COUNT(DISTINCT 日期) AS 夜點天數,
                   GROUP_CONCAT(日期, ', ') AS 日期清單
            FROM data
            GROUP BY 班別, 卡號, 公務帳號, 姓名, 月份
            ORDER BY 班別, 卡號, 月份
        """, conn)
        conn.close()
        
        total_people = len(summary)
        total_classes = summary['班別'].nunique()
        total_days = summary['夜點天數'].sum()
        driver_count = len([1 for _, r in summary.iterrows() if r['公務帳號'] in driver_accounts])
        
        content = f"""
        <div class="page-header">
            <h1><i class="fas fa-moon me-3"></i>夜點津貼彙總表</h1>
            <div class="subtitle">按班別統計的夜點津貼明細</div>
        </div>
        """
        
        stats = [
            {"title": "總人數", "value": str(total_people), "icon": "fas fa-users"},
            {"title": "班別數", "value": str(total_classes), "icon": "fas fa-layer-group"},
            {"title": "總夜點天數", "value": str(total_days), "icon": "fas fa-calendar-alt"},
            {"title": "司機", "value": str(driver_count), "icon": "fas fa-star"}
        ]
        content += HtmlComponentGenerator.generate_stats_row(stats)
        
        for class_name, group in summary.groupby('班別'):
            class_days = group['夜點天數'].sum()
            
            content += f"""
            <div class="section-card">
                <h5 class="section-header">
                    <i class="fas fa-users-cog me-2"></i>{class_name}
                    <span class="badge bg-light text-dark ms-2">{len(group)} 人</span>
                    <span class="badge bg-warning text-dark ms-1">{class_days} 天</span>
                </h5>
                <div class="p-3">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-dark">
                                <tr>
                                    <th>卡號</th><th>公務帳號</th><th>姓名</th>
                                    <th>月份</th><th>夜點天數</th><th>日期清單</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            
            for _, row in group.iterrows():
                name = HtmlComponentGenerator.mark_driver_account(row['姓名'], row['公務帳號'], driver_accounts)
                date_list = row['日期清單']
                date_display = f'<small class="text-muted">{date_list}</small>' if len(date_list) > 50 else f'<span class="text-primary">{date_list}</span>'
                
                content += f"""
                            <tr>
                                <td><strong>{row['卡號']}</strong></td>
                                <td><code>{row['公務帳號']}</code></td>
                                <td>{name}</td>
                                <td><span class="badge bg-info">{row['月份']}</span></td>
                                <td><span class="badge bg-warning text-dark rounded-pill">{row['夜點天數']}</span></td>
                                <td>{date_display}</td>
                            </tr>
                """
            
            content += "</tbody></table></div></div></div>"
        
        content += f"""
        <div class="alert alert-info">
            <h5><i class="fas fa-info-circle me-2"></i>說明</h5>
            <ul class="mb-0">
                <li><span class="badge bg-warning text-dark">司機</span> 標籤：司機名單中的司機</li>
                <li><strong>夜點津貼標準</strong>：最後打卡時間超過 22:00</li>
                <li><strong>統計方式</strong>：每人每日最多計算一次</li>
            </ul>
        </div>
        
        <div class="footer-info">
            <i class="fas fa-info-circle me-2"></i>
            生成時間：{datetime.now().strftime(AppConfig.DISPLAY_DATETIME_FORMAT)} | 
            共 {total_people} 人，{total_classes} 個班別，{total_days} 夜點天數
        </div>
        """
        
        return content
    
    def _generate_printable_daily_content(self, df: pd.DataFrame, date_str: str, driver_accounts: Set[str]) -> str:
        """生成列印版單日內容"""
        content = f"""
        <div class="report-header">
            <div class="report-info">
                <span>查詢日期：{date_str}</span>
                <span>產生時間：{datetime.now().strftime(AppConfig.DISPLAY_DATETIME_FORMAT)}</span>
            </div>
        </div>
        """
        
        for class_name, group in df.groupby('班別'):
            content += f"""
            <div class="class-section">
                <div class="class-title">{class_name}</div>
                <table>
                    <thead><tr>
                        <th style="width: 10%;">卡號</th>
                        <th style="width: 15%;">公務帳號</th>
                        <th style="width: 15%;">姓名</th>
                        <th style="width: 10%;">打卡次數</th>
                        <th style="width: 50%;">時間戳記</th>
                    </tr></thead>
                    <tbody>
            """
            
            for _, row in group.iterrows():
                name = row['姓名']
                if driver_accounts and row['公務帳號'] in driver_accounts:
                    name = f"{name} <span class='driver-tag'>(司機)</span>"
                
                content += f"""
                    <tr>
                        <td class="center">{row['卡號']}</td>
                        <td class="center">{row['公務帳號']}</td>
                        <td class="center">{name}</td>
                        <td class="center">{row['打卡次數']}</td>
                        <td class="timestamps">{row['所有時間戳記']}</td>
                    </tr>
                """
            
            content += "</tbody></table></div>"
        
        return content
    
    def _generate_printable_full_content(self, df: pd.DataFrame, driver_accounts: Set[str]) -> str:
        """生成列印版完整內容"""
        content = f"""
        <div class="report-header">
            <h1>完整打卡記錄總表 (列印版)</h1>
            <div class="report-info">
                <span>日期範圍：{df['日期'].min()} ~ {df['日期'].max()}</span>
                <span>產生時間：{datetime.now().strftime(AppConfig.DISPLAY_DATETIME_FORMAT)}</span>
            </div>
        </div>
        """
        
        for card_number, group in df.groupby('卡號'):
            accounts = '、'.join(map(str, group['公務帳號'].unique()))
            names = group['姓名'].unique()
            classes = '、'.join(map(str, group['班別'].unique()))
            
            formatted_names = []
            for name in names:
                emp_accounts = group[group['姓名'] == name]['公務帳號'].unique()
                is_driver = any(acc in driver_accounts for acc in emp_accounts) if driver_accounts else False
                formatted_names.append(f"{name} (司機)" if is_driver else str(name))
            names_display = '、'.join(formatted_names)
            
            content += f"""
            <div class="employee-section">
                <div class="employee-header">
                    卡號：{card_number} | 姓名：{names_display} | 公務帳號：{accounts} | 班別：{classes}
                </div>
                <table>
                    <thead><tr>
                        <th>日期</th><th>星期</th><th>次數</th><th>時間戳記</th>
                    </tr></thead>
                    <tbody>
            """
            
            for _, row in group.iterrows():
                ts = row['所有時間戳記'].replace(', ', ' | ') if row['所有時間戳記'] else '－'
                punch = row['打卡次數'] if row['打卡次數'] > 0 else '－'
                
                content += f"""
                    <tr>
                        <td class="center">{row['日期'][5:]}</td>
                        <td class="center">{row['星期']}</td>
                        <td class="center">{punch}</td>
                        <td class="timestamps">{ts}</td>
                    </tr>
                """
            
            content += "</tbody></table></div>"
        
        return content
