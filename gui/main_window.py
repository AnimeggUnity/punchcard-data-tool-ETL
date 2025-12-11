"""
主視窗 GUI - 使用 FreeSimpleGUI
"""

import threading
import traceback
from typing import Callable, Dict, List

import FreeSimpleGUI as sg

from config import AppConfig, PathManager
from services import DataProcessingService, ReportService, DriverListService


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
            
            if event in self.function_mapping:
                self.window['-OUTPUT-'].update('')
                self._run_in_thread(self.function_mapping[event])
        
        self.window.close()


def run_app(config_source: str = "未知"):
    """啟動應用程式"""
    app = MainWindow(config_source=config_source)
    app.run()
