import pandas as pd
import glob
import os

def convert_entire_batch():
    # 1. Find all .txt files in the current folder
    # This will automatically pick up Lec_3 through Lec_11 and Mat_3 through Mat_11
    txt_files = glob.glob("*.txt")
    
    if not txt_files:
        print("No .txt files found in this folder.")
        return

    print(f"--- Starting Process for {len(txt_files)} files ---\n")

    # Counters for the summary
    lec_count = 0
    mat_count = 0
    errors = 0

    for input_file in txt_files:
        try:
            # Determine file type for the counter
            filename = os.path.basename(input_file)
            if filename.startswith("Lec"):
                lec_count += 1
            elif filename.startswith("Mat"):
                mat_count += 1

            # 2. Define the output filename (same name, but .csv)
            base_name = os.path.splitext(filename)[0]
            output_file = f"{base_name}.csv"

            # 3. Read the file
            # sep='|' : Your files use pipes, not commas
            # quotechar='"' : Handles the quotes around your text
            # encoding='utf-8' : Handles special characters like 'ñ' or '°' (found in your headers)
            # on_bad_lines='skip' : Ensures the script doesn't crash if one single line is broken
            df = pd.read_csv(
                input_file, 
                sep='|', 
                quotechar='"', 
                encoding='utf-8', 
                skip_blank_lines=True,
                on_bad_lines='skip' 
            )
            
            # 4. Clean Headers
            # Removes the extra spaces inside headers (e.g., "LEC3331             " -> "LEC3331")
            df.columns = df.columns.str.strip()
            
            # 5. Save as CSV
            # encoding='utf-8-sig' : Essential for Excel to read accents/tildes correctly
            df.to_csv(output_file, index=False, sep=',', encoding='utf-8-sig')
            
            print(f"[OK] Converted: {filename} -> {output_file}")
            
        except Exception as e:
            print(f"[ERROR] Failed to process {filename}: {e}")
            errors += 1

    # 6. Final Summary based on your file list
    print("\n" + "="*30)
    print("       BATCH PROCESS SUMMARY       ")
    print("="*30)
    print(f"Lectura Files Processed:    {lec_count}")
    print(f"Matemática Files Processed: {mat_count}")
    print(f"Total Files Converted:      {lec_count + mat_count}")
    
    if errors > 0:
        print(f"Files with errors:          {errors}")
    else:
        print("Status: All files converted successfully!")

if __name__ == "__main__":
    convert_entire_batch()