import pandas as pd
import glob
import os
import re

def create_excel_files():
    # 1. Setup path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Find the "Complete" CSV files
    csv_files = glob.glob(os.path.join(script_dir, "Complete_Grade_*.csv"))
    
    # Sort them numerically (3, 4, ... 11) for a clean log
    csv_files.sort(key=lambda x: int(re.search(r"(\d+)", os.path.basename(x)).group(1)) if re.search(r"(\d+)", os.path.basename(x)) else 0)

    if not csv_files:
        print(f"❌ No 'Complete_Grade_*.csv' files found in: {script_dir}")
        return

    print(f"✅ Found {len(csv_files)} files. Creating Excel versions...\n")
    print(f"{'CSV SOURCE':<30} | {'EXCEL OUTPUT':<30} | {'STATUS':<10}")
    print("-" * 75)

    count = 0

    for file_path in csv_files:
        try:
            filename = os.path.basename(file_path)
            
            # 3. Read the CSV
            # dtype=str is crucial: It keeps Student IDs as text (e.g. "00123") 
            # instead of turning them into numbers (123) which removes leading zeros.
            df = pd.read_csv(file_path, encoding='utf-8-sig', dtype=str)
            
            # 4. Define Output Name
            # Replaces .csv with .xlsx
            base_name = os.path.splitext(filename)[0]
            output_filename = f"{base_name}.xlsx"
            output_path = os.path.join(script_dir, output_filename)
            
            # 5. Write to Excel
            # index=False removes the generic row numbers (0, 1, 2...)
            df.to_excel(output_path, index=False, engine='openpyxl')
            
            print(f"{filename:<30} | {output_filename:<30} | ✅ Done")
            count += 1

        except ImportError:
            print("\n❌ ERROR: Missing library 'openpyxl'.")
            print("Please run: pip install openpyxl")
            return
        except Exception as e:
            print(f"{filename:<30} | {'FAILED':<30} | ❌ {e}")

    print("-" * 75)
    print(f"🎉 Process Finished. Created {count} Excel files.")

if __name__ == "__main__":
    create_excel_files()