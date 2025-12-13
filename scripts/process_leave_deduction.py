"""
請假扣款處理腳本
獨立執行腳本，處理請假資料並生成扣款報表

使用方式：
    python scripts/process_leave_deduction.py [檔案路徑] [選項]

參數：
    檔案路徑          請假資料 Excel 檔案路徑（可選，預設為 data/work.xlsx）
    --open           生成報表後自動在瀏覽器開啟

範例：
    python scripts/process_leave_deduction.py
    python scripts/process_leave_deduction.py data/114年11月.xlsx
    python scripts/process_leave_deduction.py data/114年11月.xlsx --open
"""

import os
import sys
import argparse
import sqlite3
import webbrowser
from pathlib import Path

# 設定路徑（腳本在 scripts/ 資料夾，需要往上一層到專案根目錄）
app_dir = Path(__file__).parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

import pandas as pd
from config import PathManager
from core.leave_parser import LeaveDataParser
from core.leave_deduction import LeaveDeductionCalculator
from services.driver_service import DriverListService


def main():
    """主處理流程"""
    # 解析命令列參數
    parser = argparse.ArgumentParser(
        description='請假扣款處理程式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  python scripts/process_leave_deduction.py
  python scripts/process_leave_deduction.py data/114年11月.xlsx
  python scripts/process_leave_deduction.py data/114年11月.xlsx --open
        """
    )
    parser.add_argument('file', nargs='?', help='請假資料 Excel 檔案路徑')
    parser.add_argument('--open', action='store_true', help='自動在瀏覽器開啟報表')
    args = parser.parse_args()

    print("=" * 50)
    print("請假扣款處理程式")
    print("=" * 50)

    # 初始化路徑管理器
    path_manager = PathManager()

    # 取得檔案路徑
    if args.file:
        leave_data_path = args.file
    else:
        leave_data_path = path_manager.get_leave_data_path()

    output_dir = path_manager.get_output_dir()
    db_path = path_manager.get_db_path()

    print(f"請假資料路徑: {leave_data_path}")
    print(f"資料庫路徑: {db_path}")
    print(f"輸出目錄: {output_dir}")
    print()

    # 檢查檔案是否存在
    if not os.path.exists(leave_data_path):
        print(f"❌ 錯誤: 找不到請假資料檔案")
        print(f"   指定路徑: {leave_data_path}")
        print(f"")
        print(f"使用方式:")
        print(f"   python scripts/process_leave_deduction.py [檔案路徑]")
        print(f"")
        print(f"範例:")
        print(f"   python scripts/process_leave_deduction.py data/114年11月.xlsx")
        return

    try:
        # 1. 解析請假資料
        print("📊 步驟 1/5: 解析請假資料...")
        parser_obj = LeaveDataParser(leave_data_path)
        parsed_df, unparsed_df = parser_obj.parse()
        print(f"   ✓ 已解析 {len(parsed_df)} 筆請假記錄")
        if len(unparsed_df) > 0:
            print(f"   ⚠ 有 {len(unparsed_df)} 筆資料無法解析")

        # 2. 從資料庫載入員工資訊（班別）
        print("🗄️  步驟 2/5: 載入員工資訊（班別）...")
        employee_info = pd.DataFrame()
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                query = "SELECT DISTINCT emp_id, name, shift_class FROM integrated_punch"
                employee_info = pd.read_sql(query, conn)
                conn.close()
                print(f"   ✓ 已載入 {len(employee_info)} 位員工資訊")
            except Exception as e:
                print(f"   ⚠ 無法載入員工資訊: {e}")
                print(f"   ℹ 將不顯示班別資訊")
        else:
            print(f"   ⚠ 資料庫不存在，請先執行「資料整理」")
            print(f"   ℹ 將不顯示班別資訊")

        # 3. 載入司機名單（從資料庫）
        print("🚗 步驟 3/5: 載入司機名單...")
        driver_accounts = set()
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                driver_query = "SELECT DISTINCT emp_id FROM driver_list WHERE is_driver = 1"
                driver_df = pd.read_sql(driver_query, conn)
                conn.close()
                driver_accounts = set(driver_df['emp_id'].tolist())
                print(f"   ✓ 已載入 {len(driver_accounts)} 位司機")
            except Exception as e:
                print(f"   ⚠ 無法載入司機名單: {e}")
                print(f"   ℹ 將不標記司機資訊")
        else:
            print(f"   ⚠ 資料庫不存在，請先執行「資料整理」")
            print(f"   ℹ 將不標記司機資訊")

        # 4. 計算扣款
        print("💰 步驟 4/5: 計算扣款金額...")
        calculator = LeaveDeductionCalculator(parsed_df, employee_info, driver_accounts)
        result_df = calculator.calculate()
        print(f"   ✓ 計算完成")

        # 5. 生成月彙總
        print("📈 步驟 5/5: 生成月彙總...")
        monthly_summary = calculator.generate_monthly_summary()
        print(f"   ✓ 共 {len(monthly_summary)} 位員工")

        # 6. 輸出檔案
        print("📁 輸出檔案...")

        # CSV 輸出
        parsed_csv_path = os.path.join(output_dir, "leave_basic.csv")
        result_df.to_csv(parsed_csv_path, index=False, encoding="utf-8-sig")
        print(f"   ✓ 已解析資料: {parsed_csv_path}")

        if len(unparsed_df) > 0:
            unparsed_csv_path = os.path.join(output_dir, "leave_unparsed.csv")
            unparsed_df.to_csv(unparsed_csv_path, index=False, encoding="utf-8-sig")
            print(f"   ✓ 未解析資料: {unparsed_csv_path}")

        # HTML 報表
        html_path = os.path.join(output_dir, "deduction_report.html")
        calculator.generate_html_report(html_path, monthly_summary)
        print(f"   ✓ HTML 報表: {html_path}")

        # 如果指定 --open 參數，自動在瀏覽器開啟報表
        if args.open:
            print(f"   ⏳ 正在開啟瀏覽器...")
            abs_path = os.path.abspath(html_path)
            file_url = f'file:///{abs_path.replace(chr(92), "/")}'
            webbrowser.open(file_url)
            print(f"   ✓ 已開啟報表")

        # 統計資訊
        print()
        print("=" * 50)
        print("處理完成！統計資訊：")
        print("=" * 50)
        print(f"總請假記錄: {len(parsed_df)} 筆")
        print(f"請假員工數: {result_df['emp_id'].nunique()} 位")
        print(f"傷病總扣款: ${int(monthly_summary['sick_deduction'].sum()):,}")
        print(f"事假總扣款: ${int(monthly_summary['personal_deduction'].sum()):,}")
        print(f"總扣款金額: ${int(monthly_summary['total_deduction'].sum()):,}")
        print("=" * 50)

    except FileNotFoundError as e:
        print(f"❌ 錯誤: {e}")
    except ValueError as e:
        print(f"❌ 錯誤: {e}")
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
