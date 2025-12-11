"""
打卡系統助手 - ETL 重構版
主程式入口
"""

import os
import sys
import multiprocessing
from pathlib import Path
from importlib.machinery import SourceFileLoader


# ==================== 關鍵修改：嘗試從外部載入 config.py ====================
CONFIG_SOURCE = "預設參數"  # 全域變數，記錄 config 來源

if getattr(sys, 'frozen', False):
    # PyInstaller 打包後 → exe 同目錄
    config_path = os.path.join(os.path.dirname(sys.executable), "config.py")
else:
    # 開發時 → 目前檔案同目錄
    config_path = os.path.join(os.path.dirname(__file__), "config.py")

if os.path.exists(config_path):
    # 外部 config.py 存在，動態載入
    try:
        config_module = SourceFileLoader("config", config_path).load_module()
        CONFIG_SOURCE = "外部參數檔案"
        print(f"已載入外部參數檔案: {config_path}")
    except Exception as e:
        print(f"警告: 外部 config.py 載入失敗 ({e})，使用預設參數")
        import config as config_module
        CONFIG_SOURCE = "預設參數"
else:
    # 外部 config.py 不存在，使用內建
    import config as config_module
    CONFIG_SOURCE = "預設參數"

# 把常用的三個類別拉到全域
AppConfig           = config_module.AppConfig
ExcelReadingConfig  = config_module.ExcelReadingConfig
PathManager         = config_module.PathManager
# ===========================================================================


def get_app_base_dir():
    """取得應用程式基礎目錄（保留您原本邏輯，與 config 完全相容）"""
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
    """初始化必要的資料夾，檢查必要檔案"""
    result = {'warnings': [], 'created': []}
    
    required_dirs = ['data', 'db', 'output']
    for dir_name in required_dirs:
        dir_path = Path(app_dir) / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            result['created'].append(dir_name)
    
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
    app_base_dir = setup_path()
    os.chdir(app_base_dir)

    print(f"應用程式目錄: {app_base_dir}")
    print(f"工作目錄: {os.getcwd()}")
    print(f"配置來源: {CONFIG_SOURCE}")
    print("=" * 50)
    print("打卡系統資料處理工具 - ETL 重構版")
    print("=" * 50)

    init_result = init_directories(app_base_dir)

    if init_result['created']:
        print(f"已建立資料夾: {', '.join(init_result['created'])}")

    if init_result['warnings']:
        print("\n警告:")
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

    # 啟動 GUI，傳遞 config 來源資訊
    from gui.main_window import run_app
    run_app(config_source=CONFIG_SOURCE)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()