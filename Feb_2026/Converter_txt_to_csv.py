import pandas as pd
import glob
import os

def convert_files_fixed():
    # 1. INTELLIGENCE: Find the folder where THIS script is
    script_location = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Look for .txt files in THAT specific folder
    search_pattern = os.path.join(script_location, "*.txt")
    txt_files = glob.glob(search_pattern)
    
    if not txt_files:
        print(f"❌ No .txt files found in: {script_location}")
        return

    print(f"✅ Found {len(txt_files)} files. Starting conversion...\n")

    lec_count = 0
    mat_count = 0
    errors = 0

    for input_file in txt_files:
        filename = os.path.basename(input_file)
        
        # Categorize for the report
        if filename.startswith("Lec"):
            lec_count += 1
        elif filename.startswith("Mat"):
            mat_count += 1

        # Create Output Filename
        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(script_location, f"{base_name}.csv")

        try:
            # 3. READ THE FILE (The Fix)
            # changed encoding to 'latin-1' to handle Spanish characters (Ñ, °)
            # added engine='python' to handle the pipes '|' more robustly
            df = pd.read_csv(
                input_file, 
                sep='|', 
                quotechar='"', 
                encoding='latin-1',  # <--- KEY FIX FOR SPANISH TEXT
                skip_blank_lines=True,
                on_bad_lines='skip',
                engine='python'
            )
            
            # 4. Clean headers (remove extra spaces)
            df.columns = df.columns.str.strip()
            
            # 5. Save (using utf-8-sig so Excel opens it correctly)
            df.to_csv(output_path, index=False, sep=',', encoding='utf-8-sig')
            
            print(f"[OK] Converted: {filename}")
            
        except PermissionError:
            print(f"❌ ERROR: Please close the file '{base_name}.csv' in Excel and try again.")
            errors += 1
        except Exception as e:
            print(f"❌ ERROR on {filename}: {e}")
            errors += 1

    # 6. Final Report
    print("\n" + "="*30)
    print(f"Lectura Files:    {lec_count}")
    print(f"Matemática Files: {mat_count}")
    print(f"Total Converted:  {lec_count + mat_count}")
    
    if errors == 0:
        print("\n🎉 SUCCESS! All files converted.")
    else:
        print(f"\n⚠️ Finished with {errors} errors.")

if __name__ == "__main__":
    convert_files_fixed()