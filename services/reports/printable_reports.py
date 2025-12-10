"""
列印版報表生成器
"""

import os
import pandas as pd
from typing import Set
from datetime import datetime

from config import AppConfig
from templates import HtmlTemplateManager
from .base_report import BaseReport


class PrintableDailyReport(BaseReport):
    """列印版單日報表生成器"""
    
    def generate(self, df: pd.DataFrame, date_str: str, driver_accounts: Set[str]) -> str:
        """
        生成列印版單日報表
        
        Args:
            df: 打卡資料 DataFrame
            date_str: 日期字串
            driver_accounts: 司機帳號集合
            
        Returns:
            生成的報表檔案路徑
        """
        content = self._generate_content(df, date_str, driver_accounts)
        html = HtmlTemplateManager.get_printable_template(f"單日打卡記錄 - {date_str}", content)
        
        output_file = os.path.join(self.path_mgr.get_output_dir(), f'punch_record_{date_str}_print.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.output_callback(f"列印版報表已生成: {output_file}")
        self._auto_open(output_file)
        return output_file
    
    def _generate_content(self, df: pd.DataFrame, date_str: str, driver_accounts: Set[str]) -> str:
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


class PrintableFullReport(BaseReport):
    """列印版完整報表生成器"""
    
    def generate(self, df: pd.DataFrame, driver_accounts: Set[str]) -> str:
        """
        生成列印版完整報表
        
        Args:
            df: 打卡資料 DataFrame
            driver_accounts: 司機帳號集合
            
        Returns:
            生成的報表檔案路徑
        """
        content = self._generate_content(df, driver_accounts)
        html = HtmlTemplateManager.get_printable_template("完整打卡記錄總表 (列印版)", content)
        
        output_file = os.path.join(self.path_mgr.get_output_dir(), 'punch_by_account_print.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.output_callback(f"列印版報表已生成: {output_file}")
        self._auto_open(output_file)
        return output_file
    
    def _generate_content(self, df: pd.DataFrame, driver_accounts: Set[str]) -> str:
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
