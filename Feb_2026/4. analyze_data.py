import pandas as pd
import glob
import os
import numpy as np
import re

def analyze_completeness_fixed():
    # 1. Setup path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Find all Final_Grade files
    files = sorted(glob.glob(os.path.join(script_dir, "Final_Grade_*.csv")), 
                   key=lambda x: int(re.search(r"(\d+)", os.path.basename(x)).group(1)) if re.search(r"(\d+)", os.path.basename(x)) else 0)
    
    if not files:
        print("❌ No 'Final_Grade_*.csv' files found.")
        return

    print(f"{'GRADE':<10} | {'TOTAL STUDENTS':<15} | {'COMPLETE DATA':<15} | {'INCOMPLETE DATA':<15}")
    print("-" * 65)

    summary_data = []

    for file_path in files:
        try:
            filename = os.path.basename(file_path)
            grade_match = re.search(r"Final_Grade_(\d+)\.csv", filename)
            grade = grade_match.group(1) if grade_match else "??"
            
            # 3. Read File (as string to handle '-' detection)
            df = pd.read_csv(file_path, encoding='utf-8-sig', dtype=str)
            
            # 4. Identify Item Columns
            item_cols = [col for col in df.columns if (col.startswith('LEC') or col.startswith('MAT')) and any(char.isdigit() for char in col)]
            
            if not item_cols:
                print(f"{grade:<10} | No item columns found")
                continue

            # 5. Clean Data for checking (THE FIX)
            # - Strip whitespace
            # - Replace empty strings AND hyphens with NaN
            df_items = df[item_cols].apply(lambda x: x.str.strip())
            df_items = df_items.replace(['', '-'], np.nan)
            
            # 6. Calculate Stats
            total_students = len(df)
            
            # Count valid rows
            complete_mask = df_items.notna().all(axis=1)
            
            complete_count = complete_mask.sum()
            incomplete_count = total_students - complete_count
            
            # 7. Print Row
            print(f"{grade:<10} | {total_students:<15} | {complete_count:<15} | {incomplete_count:<15}")
            
            summary_data.append({
                'Grade': grade,
                'Total Students': total_students,
                'Complete Data': complete_count,
                'Incomplete Data': incomplete_count
            })

        except Exception as e:
            print(f"Error processing {filename}: {e}")

    # Save summary
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        output_path = os.path.join(script_dir, "Summary_Completeness.csv")
        summary_df.to_csv(output_path, index=False)
        print("-" * 65)
        print(f"\nSummary saved to: {output_path}")

if __name__ == "__main__":
    analyze_completeness_fixed()