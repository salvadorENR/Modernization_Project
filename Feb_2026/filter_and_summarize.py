import pandas as pd
import glob
import os
import re
import numpy as np

def filter_strict_complete_data_fixed():
    # 1. Setup path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Find Final_Grade files
    files = glob.glob(os.path.join(script_dir, "Final_Grade_*.csv"))
    
    # Sort files numerically
    files.sort(key=lambda x: int(re.search(r"(\d+)", os.path.basename(x)).group(1)) if re.search(r"(\d+)", os.path.basename(x)) else 0)

    if not files:
        print("❌ No 'Final_Grade_*.csv' files found.")
        return

    summary_data = []

    print(f"{'GRADE':<6} | {'STATUS':<10} | {'LEC ITEMS':<10} | {'MAT ITEMS':<10} | {'TOTAL':<10} | {'KEPT':<10} | {'REMOVED':<10}")
    print("-" * 90)

    for file_path in files:
        try:
            filename = os.path.basename(file_path)
            grade_match = re.search(r"Final_Grade_(\d+)\.csv", filename)
            grade = grade_match.group(1) if grade_match else "??"

            # 3. Read CSV
            df = pd.read_csv(file_path, encoding='utf-8-sig', dtype=str)
            
            # 4. Identify Item Columns
            lec_cols = [c for c in df.columns if c.startswith('LEC') and any(char.isdigit() for char in c)]
            mat_cols = [c for c in df.columns if c.startswith('MAT') and any(char.isdigit() for char in c)]
            all_item_cols = lec_cols + mat_cols

            if not all_item_cols:
                print(f"{grade:<6} | ⚠️ SKIP | - | - | - | - | -")
                continue

            # 5. STRICT FILTERING LOGIC (THE FIX)
            df_items = df[all_item_cols].copy()
            
            # Remove whitespace
            df_items = df_items.apply(lambda x: x.str.strip())
            
            # CRITICAL: Treat both empty strings AND hyphens as Missing (NaN)
            df_items = df_items.replace(['', '-'], np.nan)
            
            # Check completeness
            is_complete = df_items.notna().all(axis=1)
            
            # 6. Apply Filter
            df_clean = df[is_complete]
            
            # 7. Stats
            total = len(df)
            kept = len(df_clean)
            removed = total - kept
            
            # 8. Save
            output_name = f"Complete_Grade_{grade}.csv"
            output_path = os.path.join(script_dir, output_name)
            df_clean.to_csv(output_path, index=False, sep=',', encoding='utf-8-sig')
            
            # 9. Verification
            verify_df = pd.read_csv(output_path, encoding='utf-8-sig', dtype=str)
            check_vals = verify_df[all_item_cols].apply(lambda x: x.str.strip()).replace(['', '-'], np.nan)
            status = "✅ OK" if check_vals.isnull().sum().sum() == 0 else "❌ ERROR"

            print(f"{grade:<6} | {status:<10} | {len(lec_cols):<10} | {len(mat_cols):<10} | {total:<10} | {kept:<10} | {removed:<10}")
            
            summary_data.append({'Grade': grade, 'Total': total, 'Kept': kept, 'Removed': removed})

        except Exception as e:
            print(f"Error on {filename}: {e}")

    # 10. Final Summary
    print("-" * 90)
    print("\n FINAL SUMMARY:")
    total_kept_all = sum(d['Kept'] for d in summary_data)
    total_removed_all = sum(d['Removed'] for d in summary_data)
    print(f" Total Students Processed: {sum(d['Total'] for d in summary_data)}")
    print(f" Total Students Kept:      {total_kept_all} (Complete Data)")
    print(f" Total Students Removed:   {total_removed_all} (Incomplete/Hyphens)")

if __name__ == "__main__":
    filter_strict_complete_data_fixed()