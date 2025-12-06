"""
打卡系統助手 - ETL 重構版

主程式入口
"""

import os
import sys
import multiprocessing


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
