import pandas as pd
import glob
import os
import re

def convert_final_grades_to_excel():
    # 1. Setup path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Find the "Final_Grade" CSV files
    # We look for files starting with "Final_Grade_" and ending in ".csv"
    csv_files = glob.glob(os.path.join(script_dir, "Final_Grade_*.csv"))
    
    # Sort them numerically (3, 4, ... 11) so the process log is easy to read
    csv_files.sort(key=lambda x: int(re.search(r"(\d+)", os.path.basename(x)).group(1)) if re.search(r"(\d+)", os.path.basename(x)) else 0)

    if not csv_files:
        print(f"❌ No 'Final_Grade_*.csv' files found in: {script_dir}")
        return

    print(f"✅ Found {len(csv_files)} files. Starting conversion to Excel...\n")
    print(f"{'CSV FILE':<30} | {'EXCEL OUTPUT':<30} | {'STATUS':<10}")
    print("-" * 75)

    count = 0

    for file_path in csv_files:
        try:
            filename = os.path.basename(file_path)
            
            # 3. Read the CSV
            # dtype=str is CRITICAL: It forces pandas to treat the 'Documento' (ID) column
            # as text '00123' instead of number 123. This preserves leading zeros.
            df = pd.read_csv(file_path, encoding='utf-8-sig', dtype=str)
            
            # 4. Define Output Name
            # Takes "Final_Grade_3.csv" and changes it to "Final_Grade_3.xlsx"
            base_name = os.path.splitext(filename)[0]
            output_filename = f"{base_name}.xlsx"
            output_path = os.path.join(script_dir, output_filename)
            
            # 5. Write to Excel
            # index=False hides the pandas row numbers (0, 1, 2...)
            df.to_excel(output_path, index=False, engine='openpyxl')
            
            print(f"{filename:<30} | {output_filename:<30} | ✅ Done")
            count += 1

        except ImportError:
            print("\n❌ ERROR: Python library 'openpyxl' is missing.")
            print("   -> Please run this command in your terminal: pip install openpyxl")
            return
        except Exception as e:
            print(f"{filename:<30} | {'FAILED':<30} | ❌ {e}")

    print("-" * 75)
    print(f"🎉 Success! Converted {count} files to Excel format.")

if __name__ == "__main__":
    convert_final_grades_to_excel()