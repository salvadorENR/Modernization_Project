import os

# 1. Get the absolute path of the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# List with the 'Lec' files
file_names = [
    "Lec_3.txt", "Lec_4.txt", "Lec_5.txt", "Lec_6.txt", 
    "Lec_7.txt", "Lec_8.txt", "Lec_9.txt", "Lec_10.txt", "Lec_11.txt"
]

# Variable to keep track of the grand total across all files
global_total = 0

for file_name in file_names:
    file_path = os.path.join(script_dir, file_name)
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                lines = [line.strip() for line in f if line.strip()]
        
        # Calculate total (excluding the header row)
        if lines:
            total_registers = len(lines) - 1
        else:
            total_registers = 0
            
        print(f"File '{file_name}' has {total_registers} registers.")
        
        # Add to the global total
        global_total += total_registers
    else:
        print(f"File '{file_name}' not found in {script_dir}")

# Print the final grand total
print("-" * 30)
print(f"GLOBAL TOTAL ACROSS ALL FILES: {global_total} registers.")