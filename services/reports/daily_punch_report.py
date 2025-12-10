"""
單日打卡報表生成器
"""

import os
import pandas as pd
from typing import Set
from datetime import datetime

from config import AppConfig
from templates import HtmlTemplateManager, HtmlComponentGenerator
from .base_report import BaseReport


class DailyPunchReport(BaseReport):
    """單日打卡報表生成器"""
    
    def generate(self, df: pd.DataFrame, date_str: str, driver_accounts: Set[str]) -> str:
        """
        生成單日打卡報表
        
        Args:
            df: 打卡資料 DataFrame
            date_str: 日期字串
            driver_accounts: 司機帳號集合
            
        Returns:
            生成的報表檔案路徑
        """
        content = self._generate_content(df, date_str, driver_accounts)
        html = HtmlTemplateManager.get_bootstrap_template(f"單日打卡記錄 - {date_str}", content)
        
        output_file = os.path.join(self.path_mgr.get_output_dir(), f'punch_record_{date_str}.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.output_callback(f"報表已生成: {output_file}")
        self._auto_open(output_file)
        return output_file
    
    def _generate_content(self, df: pd.DataFrame, date_str: str, driver_accounts: Set[str]) -> str:
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
