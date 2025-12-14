"""
HTML 模板和組件生成器
"""

from typing import List, Set


class HtmlComponentGenerator:
    """HTML 組件生成器"""
    
    @staticmethod
    def mark_driver_account(name: str, account: str, driver_accounts: Set[str]) -> str:
        """標記司機"""
        if driver_accounts and account in driver_accounts:
            return f'<span class="badge bg-warning text-dark me-1">司機</span>{name}'
        return str(name)
    
    @staticmethod
    def colorize_timestamps(timestamps: List[str]) -> str:
        """為時間戳記添加顏色"""
        if not timestamps:
            return ""
        colored = []
        for i, ts in enumerate(timestamps):
            if ts and ts.strip():
                css = "timestamp-odd" if (i+1) % 2 else "timestamp-even"
                colored.append(f'<span class="{css}">{ts}</span>')
        return " ".join(colored)
    
    @staticmethod
    def generate_stats_card(title: str, value: str, icon: str = "fas fa-chart-bar") -> str:
        """生成統計卡片"""
        return f"""
        <div class="col-md-3">
            <div class="stats-card">
                <div class="d-flex align-items-center">
                    <i class="{icon} fa-2x me-3"></i>
                    <div>
                        <div class="stats-number">{value}</div>
                        <div>{title}</div>
                    </div>
                </div>
            </div>
        </div>"""
    
    @staticmethod
    def generate_stats_row(stats: List[dict]) -> str:
        """生成統計行"""
        cards = [HtmlComponentGenerator.generate_stats_card(
            s.get('title', ''), s.get('value', ''), s.get('icon', 'fas fa-chart-bar')
        ) for s in stats]
        return f'<div class="row mb-4">{"".join(cards)}</div>'


class HtmlTemplateManager:
    """HTML 模板管理器"""
    
    @staticmethod
    def get_bootstrap_template(title: str, content: str, custom_scripts: str = "", custom_styles: str = "") -> str:
        """Bootstrap 5 HTML 模板

        Args:
            title: 報表標題
            content: 報表內容 HTML
            custom_scripts: 自訂 JavaScript 代碼（可選）
            custom_styles: 自訂 CSS 樣式（可選）
        """
        return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; transition: all 0.2s; }}
        .main-container {{ border-radius: 15px; box-shadow: 0 0 20px rgba(0,0,0,0.1); margin: 20px auto; padding: 30px; }}
        .page-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 15px; margin-bottom: 30px; text-align: center; }}
        .page-header h1 {{ margin: 0; font-weight: 300; }}
        .page-header .subtitle {{ opacity: 0.9; margin-top: 10px; }}
        .section-card {{ border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 30px; overflow: hidden; }}
        .section-header {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 15px 25px; margin: 0; font-weight: 500; }}
        .stats-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .stats-number {{ font-size: 2rem; font-weight: bold; }}
        .timestamp-odd {{ color: #0d6efd; font-weight: 500; }}
        .timestamp-even {{ color: #dc3545; font-weight: 500; }}
        [data-bs-theme="dark"] .timestamp-odd {{ color: #63b3ed; }}
        [data-bs-theme="dark"] .timestamp-even {{ color: #f56565; }}
        [data-bs-theme="dark"] .page-header, [data-bs-theme="dark"] .stats-card {{ background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%); }}
        [data-bs-theme="dark"] .section-header {{ background: linear-gradient(135deg, #2b6cb0 0%, #1a202c 100%); }}
        .theme-switcher-btn {{ position: fixed; bottom: 20px; right: 20px; z-index: 1000; }}
        .footer-info {{ text-align: center; padding: 20px; color: #666; font-size: 0.9rem; }}
        {custom_styles}
    </style>
</head>
<body class="bg-body-tertiary">
    <div class="container-fluid">
        <div class="main-container bg-body p-4">
            {content}
        </div>
    </div>
    <button class="btn btn-secondary theme-switcher-btn" id="theme-toggle-btn" type="button" title="Toggle theme">
        <i class="fas fa-moon" id="theme-icon"></i>
    </button>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        (() => {{
            'use strict'
            const getStoredTheme = () => localStorage.getItem('theme')
            const setStoredTheme = theme => localStorage.setItem('theme', theme)
            const getPreferredTheme = () => {{
                const storedTheme = getStoredTheme()
                if (storedTheme) return storedTheme
                return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
            }}
            const setTheme = theme => {{
                document.documentElement.setAttribute('data-bs-theme', theme)
                const icon = document.getElementById('theme-icon')
                if(icon) {{
                    icon.classList.toggle('fa-sun', theme === 'dark')
                    icon.classList.toggle('fa-moon', theme === 'light')
                }}
            }}
            setTheme(getPreferredTheme())
            window.addEventListener('DOMContentLoaded', () => {{
                const btn = document.getElementById('theme-toggle-btn')
                if(btn) {{
                    btn.addEventListener('click', () => {{
                        const current = getPreferredTheme()
                        const newTheme = current === 'light' ? 'dark' : 'light'
                        setStoredTheme(newTheme)
                        setTheme(newTheme)
                    }})
                }}
            }})
        }})()
    </script>
    {custom_scripts}
</body>
</html>"""
    
    @staticmethod
    def get_printable_template(title: str, content: str) -> str:
        """列印專用 HTML 模板"""
        return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Segoe UI', 'Microsoft JhengHei', sans-serif; line-height: 1.6; color: #000; background-color: #fff; }}
        .print-container {{ width: 95%; margin: 0 auto; }}
        .report-header {{ text-align: center; margin-bottom: 20px; border-bottom: 2px solid #000; padding-bottom: 10px; }}
        .report-header h1 {{ margin: 0; font-size: 24px; }}
        .report-info {{ display: flex; justify-content: space-between; font-size: 14px; margin-top: 10px; }}
        .class-section {{ margin-top: 25px; page-break-inside: avoid; }}
        .class-title {{ font-size: 18px; font-weight: bold; padding-bottom: 5px; border-bottom: 1px solid #ccc; margin-bottom: 10px; }}
        .employee-section {{ margin-top: 8px; page-break-inside: auto; }}
        .employee-header {{ font-size: 14px; font-weight: bold; padding: 4px 6px; background-color: #ddd; border: 1px solid #000; border-bottom: none; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 8px; }}
        th, td {{ border: 1px solid #000; padding: 4px 6px; text-align: left; line-height: 1.3; }}
        th {{ background-color: #eee; font-weight: bold; text-align: center; }}
        td.center {{ text-align: center; }}
        .driver-tag {{ font-weight: bold; color: #000; font-size: 10px; }}
        .timestamps {{ word-break: break-all; font-size: 10px; line-height: 1.2; }}
        @media print {{
            @page {{ size: A4 portrait; margin: 1cm; }}
            body {{ font-size: 10px; line-height: 1.2; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            .print-button {{ display: none; }}
            .report-header {{ margin-bottom: 12px; padding-bottom: 8px; }}
            .report-header h1 {{ font-size: 20px; }}
            .employee-section {{ margin-top: 6px; }}
            table {{ font-size: 9px; margin-bottom: 4px; }}
            th {{ font-size: 9px; padding: 3px 4px; }}
            td {{ padding: 3px 4px; line-height: 1.1; }}
            .timestamps {{ font-size: 8px; line-height: 1.1; }}
        }}
    </style>
</head>
<body>
    <div class="print-container">
        {content}
    </div>
</body>
</html>"""
