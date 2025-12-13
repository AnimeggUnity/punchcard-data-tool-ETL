"""
主視窗 GUI - 使用 FreeSimpleGUI
"""

import threading
import traceback
from typing import Callable, Dict, List

import FreeSimpleGUI as sg
import pandas as pd

from config import AppConfig, PathManager
from services import DataProcessingService, ReportService, DriverListService
from core.leave_parser import LeaveDataParser
from core.leave_deduction import LeaveDeductionCalculator


class MainWindow:
    """主視窗類別"""

    def __init__(self, config_source: str = "未知"):
        self.path_mgr = PathManager()
        self.window = None
        self.config_source = config_source

        # 功能映射
        self.function_mapping = {
            "資料整理": self._process_data_organization,
            "夜點清單": self._process_night_meal_report,
            "單日打卡查詢": self._process_daily_punch_with_selection,
            "單日打卡查詢 (列印版)": self._process_daily_punch_print_with_selection,
            "打卡紀錄完整查詢": self._process_full_punch_record,
            "完整查詢 (列印版)": self._process_full_punch_print,
            "請假扣款處理": self._process_leave_deduction,
        }
    
    def _output_callback(self, text: str):
        """輸出到 GUI"""
        if self.window:
            self.window.write_event_value('-OUTPUT_UPDATE-', text + '\n')
    
    def _run_in_thread(self, func: Callable):
        """在新線程中執行函數"""
        def wrapper():
            try:
                self.window['-STATUS-'].update(f"正在執行...")
                result = func(self._output_callback)

                # 處理日期選擇
                if result and result.get('action') == 'select_date':
                    self.window.write_event_value('-DATE_SELECTION-', {
                        'available_dates': result['available_dates'],
                        'is_print': False
                    })
                elif result and result.get('action') == 'select_date_for_print':
                    self.window.write_event_value('-DATE_SELECTION-', {
                        'available_dates': result['available_dates'],
                        'is_print': True
                    })
                elif result and result.get('action') == 'select_leave_file':
                    # 觸發檔案選擇（在主執行緒）
                    self.window.write_event_value('-FILE_SELECTION-', {})
                else:
                    if result and 'message' in result:
                        self._output_callback(result['message'])
                    self.window['-STATUS-'].update("執行完成")

            except Exception as e:
                self._output_callback(f"執行錯誤: {traceback.format_exc()}")
                self.window['-STATUS-'].update("執行發生錯誤")

        threading.Thread(target=wrapper, daemon=True).start()
    
    def _process_data_organization(self, output_callback: Callable) -> Dict:
        """資料整理"""
        service = DataProcessingService(output_callback)
        return service.process_data_organization()
    
    def _process_night_meal_report(self, output_callback: Callable) -> Dict:
        """夜點清單"""
        try:
            data_service = DataProcessingService(output_callback)
            report_service = ReportService(output_callback)
            
            driver_accounts = DriverListService.load_driver_list(
                self.path_mgr.get_driver_list_path(), output_callback
            )
            
            df = data_service.get_night_meal_data()
            if df.empty:
                return {'success': True, 'message': '沒有符合夜點條件的資料'}
            
            output_file = report_service.generate_night_meal_report(df, driver_accounts)
            return {'success': True, 'message': f'夜點清單生成完成: {output_file}'}
            
        except Exception as e:
            return {'success': False, 'message': f'處理失敗: {traceback.format_exc()}'}
    
    def _process_daily_punch_with_selection(self, output_callback: Callable) -> Dict:
        """單日打卡查詢（帶日期選擇）"""
        data_service = DataProcessingService(output_callback)
        available_dates = data_service.get_available_dates()
        
        if not available_dates:
            return {'success': False, 'message': '沒有可用的打卡日期，請先執行資料整理'}
        
        return {'success': True, 'action': 'select_date', 'available_dates': available_dates}
    
    def _process_daily_punch_print_with_selection(self, output_callback: Callable) -> Dict:
        """單日打卡查詢列印版（帶日期選擇）"""
        data_service = DataProcessingService(output_callback)
        available_dates = data_service.get_available_dates()
        
        if not available_dates:
            return {'success': False, 'message': '沒有可用的打卡日期，請先執行資料整理'}
        
        return {'success': True, 'action': 'select_date_for_print', 'available_dates': available_dates}
    
    def _process_daily_punch(self, date_str: str, is_print: bool = False):
        """處理單日打卡查詢"""
        def task():
            try:
                data_service = DataProcessingService(self._output_callback)
                report_service = ReportService(self._output_callback)
                
                driver_accounts = DriverListService.load_driver_list(
                    self.path_mgr.get_driver_list_path(), self._output_callback
                )
                
                df = data_service.get_punch_data_for_date(date_str)
                if df.empty:
                    self._output_callback(f'日期 {date_str} 沒有打卡資料')
                    return
                
                if is_print:
                    output_file = report_service.generate_printable_daily_report(df, date_str, driver_accounts)
                else:
                    output_file = report_service.generate_daily_punch_report(df, date_str, driver_accounts)
                
                self._output_callback(f'[成功] 報表已生成: {output_file}')
                self.window['-STATUS-'].update("執行完成")
                
            except Exception as e:
                self._output_callback(f'處理失敗: {traceback.format_exc()}')
        
        threading.Thread(target=task, daemon=True).start()
    
    def _process_full_punch_record(self, output_callback: Callable) -> Dict:
        """完整打卡查詢"""
        try:
            data_service = DataProcessingService(output_callback)
            report_service = ReportService(output_callback)
            
            driver_accounts = DriverListService.load_driver_list(
                self.path_mgr.get_driver_list_path(), output_callback
            )
            
            df = data_service.get_full_punch_data()
            output_file = report_service.generate_full_punch_report(df, driver_accounts)
            
            return {'success': True, 'message': f'完整打卡記錄已生成: {output_file}'}
            
        except Exception as e:
            return {'success': False, 'message': f'處理失敗: {traceback.format_exc()}'}
    
    def _process_full_punch_print(self, output_callback: Callable) -> Dict:
        """完整打卡查詢列印版"""
        try:
            data_service = DataProcessingService(output_callback)
            report_service = ReportService(output_callback)

            driver_accounts = DriverListService.load_driver_list(
                self.path_mgr.get_driver_list_path(), output_callback
            )

            df = data_service.get_full_punch_data()
            output_file = report_service.generate_printable_full_report(df, driver_accounts)

            return {'success': True, 'message': f'列印版完整打卡記錄已生成: {output_file}'}

        except Exception as e:
            return {'success': False, 'message': f'處理失敗: {traceback.format_exc()}'}

    def _process_leave_deduction(self, output_callback: Callable) -> Dict:
        """請假扣款處理 - 觸發檔案選擇"""
        output_callback("請選擇請假資料 Excel 檔案...")

        # 回傳特殊 action，讓主迴圈處理檔案選擇
        return {'success': True, 'action': 'select_leave_file'}

    def _process_leave_deduction_with_file(self, leave_data_path: str, output_callback: Callable) -> Dict:
        """請假扣款處理 - 實際處理邏輯"""
        import os
        import sqlite3
        import webbrowser

        try:
            output_callback("=" * 50)
            output_callback("請假扣款處理")
            output_callback("=" * 50)

            output_dir = self.path_mgr.get_output_dir()
            db_path = self.path_mgr.get_db_path()

            output_callback(f"請假資料路徑: {leave_data_path}")
            output_callback(f"資料庫路徑: {db_path}")
            output_callback(f"輸出目錄: {output_dir}\n")

            # 1. 解析請假資料
            output_callback("📊 步驟 1/5: 解析請假資料...")
            parser = LeaveDataParser(leave_data_path)
            parsed_df, unparsed_df = parser.parse()
            output_callback(f"   ✓ 已解析 {len(parsed_df)} 筆請假記錄")
            if len(unparsed_df) > 0:
                output_callback(f"   ⚠ 有 {len(unparsed_df)} 筆資料無法解析")

            # 2. 從資料庫載入員工資訊（班別）
            output_callback("🗄️  步驟 2/5: 載入員工資訊（班別）...")
            employee_info = pd.DataFrame()
            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    query = "SELECT DISTINCT emp_id, name, shift_class FROM integrated_punch"
                    employee_info = pd.read_sql(query, conn)
                    conn.close()
                    output_callback(f"   ✓ 已載入 {len(employee_info)} 位員工資訊")
                except Exception as e:
                    output_callback(f"   ⚠ 無法載入員工資訊: {e}")
                    output_callback(f"   ℹ 將不顯示班別資訊")
            else:
                output_callback(f"   ⚠ 資料庫不存在，請先執行「資料整理」")
                output_callback(f"   ℹ 將不顯示班別資訊")

            # 3. 載入司機名單（從資料庫）
            output_callback("🚗 步驟 3/5: 載入司機名單...")
            driver_accounts = set()
            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    driver_query = "SELECT DISTINCT emp_id FROM driver_list WHERE is_driver = 1"
                    driver_df = pd.read_sql(driver_query, conn)
                    conn.close()
                    driver_accounts = set(driver_df['emp_id'].tolist())
                    output_callback(f"   ✓ 已載入 {len(driver_accounts)} 位司機")
                except Exception as e:
                    output_callback(f"   ⚠ 無法載入司機名單: {e}")
                    output_callback(f"   ℹ 將不標記司機資訊")
            else:
                output_callback(f"   ⚠ 資料庫不存在，請先執行「資料整理」")
                output_callback(f"   ℹ 將不標記司機資訊")

            # 4. 計算扣款
            output_callback("💰 步驟 4/5: 計算扣款金額...")
            calculator = LeaveDeductionCalculator(parsed_df, employee_info, driver_accounts)
            result_df = calculator.calculate()
            output_callback(f"   ✓ 計算完成")

            # 5. 生成月彙總
            output_callback("📈 步驟 5/5: 生成月彙總與輸出檔案...")
            monthly_summary = calculator.generate_monthly_summary()
            output_callback(f"   ✓ 共 {len(monthly_summary)} 位員工")

            # 輸出檔案
            output_callback("📁 輸出檔案...")

            # CSV 輸出
            parsed_csv_path = os.path.join(output_dir, "leave_basic.csv")
            result_df.to_csv(parsed_csv_path, index=False, encoding="utf-8-sig")
            output_callback(f"   ✓ 已解析資料: {parsed_csv_path}")

            if len(unparsed_df) > 0:
                unparsed_csv_path = os.path.join(output_dir, "leave_unparsed.csv")
                unparsed_df.to_csv(unparsed_csv_path, index=False, encoding="utf-8-sig")
                output_callback(f"   ✓ 未解析資料: {unparsed_csv_path}")

            # HTML 報表
            html_path = os.path.join(output_dir, "deduction_report.html")
            calculator.generate_html_report(html_path, monthly_summary)
            output_callback(f"   ✓ HTML 報表: {html_path}")

            # 自動在瀏覽器中開啟報表
            try:
                webbrowser.open(f'file:///{os.path.abspath(html_path).replace(chr(92), "/")}')
                output_callback(f"   🌐 已在瀏覽器中開啟報表")
            except Exception as e:
                output_callback(f"   ⚠ 無法自動開啟瀏覽器: {e}")

            # 統計資訊
            output_callback("")
            output_callback("=" * 50)
            output_callback("處理完成！統計資訊：")
            output_callback("=" * 50)
            output_callback(f"總請假記錄: {len(parsed_df)} 筆")
            output_callback(f"請假員工數: {result_df['emp_id'].nunique()} 位")
            output_callback(f"傷病總扣款: ${int(monthly_summary['sick_deduction'].sum()):,}")
            output_callback(f"事假總扣款: ${int(monthly_summary['personal_deduction'].sum()):,}")
            output_callback(f"總扣款金額: ${int(monthly_summary['total_deduction'].sum()):,}")
            output_callback("=" * 50)

            return {
                'success': True,
                'message': f'\n✅ 請假扣款處理完成！\n報表路徑: {html_path}'
            }

        except FileNotFoundError as e:
            return {'success': False, 'message': f'❌ 檔案錯誤: {e}'}
        except ValueError as e:
            return {'success': False, 'message': f'❌ 資料錯誤: {e}'}
        except Exception as e:
            return {'success': False, 'message': f'❌ 處理失敗:\n{traceback.format_exc()}'}

    def _show_date_selection(self, available_dates: List[Dict]) -> str:
        """顯示日期選擇對話框"""
        options = [d['display'] for d in available_dates]
        
        layout = [
            [sg.Text("請選擇要查詢的日期：", font=('Arial', 12))],
            [sg.Listbox(options, size=(40, min(15, len(options))), key='-DATE_LIST-',
                       default_values=[options[0]] if options else [])],
            [sg.Text(f"共有 {len(available_dates)} 個可用日期", font=('Arial', 10), text_color='gray')],
            [sg.Button("確定", key="-OK-"), sg.Button("取消", key="-CANCEL-")]
        ]
        
        dialog = sg.Window("選擇查詢日期", layout, modal=True, finalize=True)
        
        selected_date = None
        while True:
            event, values = dialog.read()
            
            if event in (sg.WIN_CLOSED, "-CANCEL-"):
                break
            
            if event == "-OK-" and values['-DATE_LIST-']:
                selected_display = values['-DATE_LIST-'][0]
                for d in available_dates:
                    if d['display'] == selected_display:
                        selected_date = d['mm_dd']
                        break
                break
        
        dialog.close()
        return selected_date
    
    def _load_readme(self) -> str:
        """載入 README.md 內容"""
        try:
            import os
            # 尋找 README.md
            readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'README.md')
            if not os.path.exists(readme_path):
                # 打包後可能在不同位置
                readme_path = os.path.join(os.getcwd(), 'README.md')

            if os.path.exists(readme_path):
                with open(readme_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return "歡迎使用打卡系統資料處理工具 (ETL 版)\n\n請從左側選單選擇功能開始使用。"
        except Exception as e:
            return f"歡迎使用打卡系統資料處理工具 (ETL 版)\n\n(無法載入 README: {e})"

    def run(self):
        """執行主視窗"""
        sg.theme(AppConfig.GUI_THEME)

        buttons = [[sg.Button(name, size=(30, 2), key=name)] for name in self.function_mapping.keys()]

        left_col = sg.Column(buttons, scrollable=True, vertical_scroll_only=True, size=(280, 400))
        right_col = sg.Column([
            [sg.Text("執行結果:")],
            [sg.Multiline(size=(80, 25), key='-OUTPUT-', autoscroll=True,
                         reroute_stdout=False, write_only=True, disabled=True)]
        ])

        layout = [
            [sg.Pane([left_col, right_col], orientation='h', relief=sg.RELIEF_SUNKEN)],
            [sg.StatusBar("就緒", size=(50, 1), key='-STATUS-'),
             sg.Text(f"配置: {self.config_source}", size=(40, 1), key='-CONFIG-', relief=sg.RELIEF_SUNKEN),
             sg.Text(AppConfig.GUI_VERSION, justification='right')]
        ]

        self.window = sg.Window("打卡系統資料處理工具 (ETL 版)", layout, resizable=True, finalize=True)
        self.window.set_min_size(self.window.size)

        # 載入並顯示 README
        readme_content = self._load_readme()
        self.window['-OUTPUT-'].update(readme_content)
        # 先捲動到文件底部，再捲回到第 115 行（確保 115 行顯示在視窗頂部）
        self.window['-OUTPUT-'].Widget.see("end")
        self.window['-OUTPUT-'].Widget.see("115.0")
        # 設定 yview 讓第 115 行位於視窗頂部
        self.window['-OUTPUT-'].Widget.yview("115.0")
        
        while True:
            event, values = self.window.read()
            
            if event == sg.WIN_CLOSED:
                break
            
            if event == '-OUTPUT_UPDATE-':
                self.window['-OUTPUT-'].print(values[event], end='')
                continue
            
            if event == '-DATE_SELECTION-':
                data = values[event]
                selected_date = self._show_date_selection(data['available_dates'])

                if selected_date:
                    self._output_callback(f"選擇日期: {selected_date}")
                    self._process_daily_punch(selected_date, data['is_print'])
                else:
                    self._output_callback("[取消] 使用者取消了日期選擇")
                continue

            if event == '-FILE_SELECTION-':
                # 檔案選擇對話框（主執行緒）
                import os
                default_path = self.path_mgr.get_leave_data_path()
                initial_folder = os.path.dirname(default_path)

                selected_file = sg.popup_get_file(
                    '請選擇請假資料 Excel 檔案',
                    title='選擇請假資料',
                    initial_folder=initial_folder,
                    file_types=(
                        ("Excel 檔案", "*.xlsx *.xls"),
                        ("所有檔案", "*.*")
                    )
                )

                if selected_file:
                    self._output_callback(f"✓ 已選擇檔案: {selected_file}")
                    # 在執行緒中處理
                    def process_task():
                        try:
                            self.window['-STATUS-'].update("正在處理...")
                            result = self._process_leave_deduction_with_file(selected_file, self._output_callback)
                            if result and 'message' in result:
                                self._output_callback(result['message'])
                            self.window['-STATUS-'].update("執行完成")
                        except Exception as e:
                            self._output_callback(f"執行錯誤: {traceback.format_exc()}")
                            self.window['-STATUS-'].update("執行發生錯誤")

                    threading.Thread(target=process_task, daemon=True).start()
                else:
                    self._output_callback("[取消] 使用者取消選擇檔案")
                    self.window['-STATUS-'].update("就緒")
                continue

            if event in self.function_mapping:
                self.window['-OUTPUT-'].update('')
                self._run_in_thread(self.function_mapping[event])
        
        self.window.close()


def run_app(config_source: str = "未知"):
    """啟動應用程式"""
    app = MainWindow(config_source=config_source)
    app.run()
