"""
打卡系統助手 - ETL 重構版

主程式入口
"""

import os
import sys
import multiprocessing
from pathlib import Path


def get_app_base_dir():
    """取得應用程式基礎目錄"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


def setup_path():
    """設定 Python 路徑"""
    app_dir = get_app_base_dir()
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    return app_dir


def init_directories(app_dir: str) -> dict:
    """
    初始化必要的資料夾，檢查必要檔案
    
    Returns:
        dict: 初始化結果，包含警告訊息
    """
    result = {'warnings': [], 'created': []}
    
    # 必要的資料夾
    required_dirs = ['data', 'db', 'output']
    for dir_name in required_dirs:
        dir_path = Path(app_dir) / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            result['created'].append(dir_name)
    
    # 必要的資料檔案（提供警告，不阻斷執行）
    required_files = {
        'data/刷卡資料.xlsx': '打卡資料',
        'data/list.xlsx': '班別資料',
    }
    
    for file_path, desc in required_files.items():
        full_path = Path(app_dir) / file_path
        if not full_path.exists():
            result['warnings'].append(f"找不到{desc}檔案: {file_path}")
    
    return result


def main():
    """主程式入口"""
    # 設定路徑
    app_base_dir = setup_path()
    os.chdir(app_base_dir)
    
    print(f"應用程式目錄: {app_base_dir}")
    print(f"工作目錄: {os.getcwd()}")
    print("=" * 50)
    print("打卡系統資料處理工具 - ETL 重構版")
    print("=" * 50)
    
    # 初始化資料夾和檢查檔案
    init_result = init_directories(app_base_dir)
    
    if init_result['created']:
        print(f"已建立資料夾: {', '.join(init_result['created'])}")
    
    if init_result['warnings']:
        print("\n⚠️ 警告:")
        for warning in init_result['warnings']:
            print(f"  - {warning}")
        print("請將必要的資料檔案放入 data/ 資料夾\n")
    
    # 檢查依賴套件
    try:
        import pandas
        import pydantic
        import FreeSimpleGUI
        print(f"pandas: {pandas.__version__}")
        print(f"pydantic: {pydantic.__version__}")
        print(f"FreeSimpleGUI: {FreeSimpleGUI.__version__}")
    except ImportError as e:
        print(f"缺少必要套件: {e}")
        print("請執行: pip install -r requirements.txt")
        return
    
    # 啟動 GUI（使用絕對導入）
    from gui.main_window import run_app
    run_app()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()

