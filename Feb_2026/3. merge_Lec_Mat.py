import pandas as pd
import glob
import os
import re

def merge_grades_final():
    # 1. Setup: Get the script's folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Find all "Cleaned" Lecture files
    # We use these to determine which grades exist (3, 4, 5... 11)
    lec_files = glob.glob(os.path.join(script_dir, "Cleaned_Lec_*.csv"))
    
    if not lec_files:
        print("❌ No 'Cleaned_Lec_*.csv' files found.")
        return

    print(f"Found {len(lec_files)} grades to process. Merging...\n")

    for lec_path in lec_files:
        try:
            # 3. Extract Grade Number
            # Matches "Cleaned_Lec_3.csv" -> "3"
            filename = os.path.basename(lec_path)
            match = re.search(r"Cleaned_Lec_(\d+)\.csv", filename)
            
            if not match:
                continue
                
            grade = match.group(1)
            
            # 4. Find matching Math file
            mat_filename = f"Cleaned_Mat_{grade}.csv"
            mat_path = os.path.join(script_dir, mat_filename)
            
            if not os.path.exists(mat_path):
                print(f"⚠️  Skipping Grade {grade}: Math file missing.")
                continue

            # 5. Read Files
            # dtype={'Documento': str} ensures IDs aren't read as numbers (keeps leading zeros if any)
            df_lec = pd.read_csv(lec_path, encoding='utf-8-sig', dtype={'Documento': str})
            df_mat = pd.read_csv(mat_path, encoding='utf-8-sig', dtype={'Documento': str})

            # 6. MERGE
            # on='Documento': Matches students by their ID
            # how='outer': Keeps students even if they took only one of the two exams
            # suffixes: Adds _Lec and _Mat to columns that appear in both (like 'Nombre')
            df_merged = pd.merge(df_lec, df_mat, on='Documento', how='outer', suffixes=('_Lec', '_Mat'))

            # 7. CLEAN DUPLICATE COLUMNS
            # We take the student info from Lecture. If missing, we take it from Math.
            # Then we remove the duplicate columns.
            student_info_cols = [
                'Departamento', 'Nro de centro', 'Centro', 'Grado', 'Grupo', 
                'Nombre', 'Apellido', 'Estado'
            ]

            for col in student_info_cols:
                col_lec = f"{col}_Lec"
                col_mat = f"{col}_Mat"
                
                # Check if both columns resulted from the merge
                if col_lec in df_merged.columns and col_mat in df_merged.columns:
                    # Combine: Use Lec value, fill gaps with Mat value
                    df_merged[col] = df_merged[col_lec].combine_first(df_merged[col_mat])
                    # Drop the redundant columns
                    df_merged.drop(columns=[col_lec, col_mat], inplace=True)
                
                # If only one exists (rare, but possible if file structures differ), just rename it
                elif col_lec in df_merged.columns:
                    df_merged.rename(columns={col_lec: col}, inplace=True)
                elif col_mat in df_merged.columns:
                    df_merged.rename(columns={col_mat: col}, inplace=True)

            # 8. REORDER COLUMNS
            # Put student info first for readability
            cols = df_merged.columns.tolist()
            # Define exact order for the start of the file
            start_cols = ['Departamento', 'Nro de centro', 'Centro', 'Grado', 'Grupo', 'Documento', 'Nombre', 'Apellido']
            
            # Remove them from current list and insert at front
            for p_col in reversed(start_cols):
                if p_col in cols:
                    cols.insert(0, cols.pop(cols.index(p_col)))
            
            df_merged = df_merged[cols]

            # 9. SAVE
            output_name = f"Final_Grade_{grade}.csv"
            output_path = os.path.join(script_dir, output_name)
            
            df_merged.to_csv(output_path, index=False, sep=',', encoding='utf-8-sig')
            
            print(f"✅ Grade {grade}: Merged successfully -> {output_name}")

        except Exception as e:
            print(f"❌ Error merging Grade {grade}: {e}")

    print("\n--- Merge Complete ---")

if __name__ == "__main__":
    merge_grades_final()