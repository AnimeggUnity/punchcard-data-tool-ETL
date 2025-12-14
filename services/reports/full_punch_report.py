"""
完整打卡報表生成器
"""

import os
import pandas as pd
from typing import Set
from datetime import datetime

from config import AppConfig
from templates import HtmlTemplateManager, HtmlComponentGenerator
from .base_report import BaseReport


class FullPunchReport(BaseReport):
    """完整打卡報表生成器"""
    
    def generate(self, df: pd.DataFrame, driver_accounts: Set[str]) -> str:
        """
        生成完整打卡報表
        
        Args:
            df: 打卡資料 DataFrame
            driver_accounts: 司機帳號集合
            
        Returns:
            生成的報表檔案路徑
        """
        content = self._generate_content(df, driver_accounts)
        html = HtmlTemplateManager.get_bootstrap_template("完整打卡記錄總表", content)
        
        output_file = os.path.join(self.path_mgr.get_output_dir(), 'full_punch_record_report.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.output_callback(f"報表已生成: {output_file}")
        self._auto_open(output_file)
        return output_file
    
    def _generate_content(self, df: pd.DataFrame, driver_accounts: Set[str]) -> str:
        """生成完整打卡內容"""
        total_employees = df['emp_id'].nunique()
        total_records = len(df)
        date_range = f"{df['日期'].min()} ~ {df['日期'].max()}"
        
        driver_count = 0
        if driver_accounts:
            driver_count = len(set(df[df['account_id'].isin(driver_accounts)]['account_id'].unique()))
        
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
        
        for card_number, group in df.groupby('emp_id'):
            accounts = '、'.join(map(str, group['account_id'].unique()))
            names = group['name'].unique()
            classes = '、'.join(map(str, group['shift_class'].unique()))
            
            # 處理司機標記
            formatted_names = []
            for name in names:
                emp_accounts = group[group['name'] == name]['account_id'].unique()
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
