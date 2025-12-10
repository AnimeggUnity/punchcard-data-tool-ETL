"""
夜點津貼報表生成器
"""

import os
import sqlite3
import pandas as pd
from typing import Set
from datetime import datetime

from config import AppConfig
from templates import HtmlTemplateManager, HtmlComponentGenerator
from .base_report import BaseReport


class NightMealReport(BaseReport):
    """夜點津貼報表生成器"""
    
    def generate(self, df: pd.DataFrame, driver_accounts: Set[str]) -> str:
        """
        生成夜點津貼報表
        
        Args:
            df: 打卡資料 DataFrame
            driver_accounts: 司機帳號集合
            
        Returns:
            生成的報表檔案路徑
        """
        content = self._generate_content(df, driver_accounts)
        html = HtmlTemplateManager.get_bootstrap_template("夜點津貼彙總表", content)
        
        output_file = os.path.join(self.path_mgr.get_output_dir(), 'combined_night_meal_report.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.output_callback(f"報表已生成: {output_file}")
        self._auto_open(output_file)
        return output_file
    
    def _generate_content(self, df: pd.DataFrame, driver_accounts: Set[str]) -> str:
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
