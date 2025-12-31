# 1. Load necessary library
library(dplyr)
library(readr)
library(stringr)

# 2. Define the Answer Keys (Extracted from your images)
# We store them in a list where the name matches the grade in your filename
math_keys <- list(
  "3G" = c("C", "B", "B", "B", "A", "B", "B", "C", "B", "C", "B", "C", "A", "A", "A", "C", "A", "B", "B", "A"),
  "4G" = c("B", "C", "A", "C", "B", "B", "C", "A", "A", "A", "B", "A", "B", "C", "C", "B", "B", "C", "C", "B", "A", "B", "C", "A", "C"),
  "5G" = c("B", "A", "A", "D", "A", "A", "D", "C", "C", "B", "C", "B", "A", "D", "C", "B", "B", "C", "D", "A", "D", "B", "D", "C", "D"),
  "6G" = c("A", "A", "B", "D", "B", "D", "C", "B", "D", "A", "C", "A", "D", "B", "C", "C", "C", "C", "C", "B", "A", "A", "D", "D", "B"),
  "7G" = c("D", "D", "A", "B", "C", "A", "A", "A", "B", "C", "C", "A", "B", "C", "A", "A", "B", "B", "A", "B", "A", "B", "C", "C", "A"),
  "8G" = c("D", "A", "C", "B", "D", "A", "D", "C", "B", "A", "D", "C", "A", "B", "D", "C", "A", "B", "D", "D", "C", "D", "B", "D", "A"),
  "9G" = c("B", "C", "D", "D", "A", "C", "A", "B", "A", "D", "D", "C", "A", "A", "B", "A", "A", "D", "C", "C", "D", "A", "C", "C", "B"),
  "1B" = c("C", "A", "C", "C", "A", "D", "B", "D", "D", "C", "D", "B", "B", "D", "A", "A", "A", "B", "B", "B", "C", "B", "A", "A", "D"),
  "2B" = c("B", "A", "B", "A", "B", "C", "D", "B", "D", "C", "A", "B", "C", "C", "D", "B", "A", "B", "D", "B", "D", "D", "C", "C", "D")
)

# 3. Define your folder paths
csv_folder <- "DataSets/CML 2025 FEBRERO/MAT_CSV" # Folder from Python
scored_folder <- "DataSets/CML 2025 FEBRERO/MAT_SCORED_CSV"
if (!dir.exists(scored_folder)) dir.create(scored_folder)

# 4. Get list of Math CSV files
files <- list.files(path = csv_folder, pattern = "MAT.*\\.csv$", full.names = TRUE)

# 5. Loop through each file and score it
for (f in files) {
  # Read the data
  df <- read_csv(f)
  
  # Identify which grade key to use based on the filename
  # This assumes your filename contains "3G", "4G", etc.
  grade_found <- names(math_keys)[sapply(names(math_keys), function(x) str_detect(f, x))]
  
  if (length(grade_found) > 0) {
    current_key <- math_keys[[grade_found[1]]]
    
    # Score the CLAVE column
    # If the student's answer (CLAVE) equals the key for that item index, 1 else 0
    df_scored <- df %>%
      mutate(SCORE = if_else(CLAVE == current_key[NUM_ITEM], 1, 0))
    
    # Save the new scored file
    new_filename <- paste0("SCORED_", basename(f))
    write_csv(df_scored, file.path(scored_folder, new_filename))
    
    message(paste("Scored:", basename(f), "using key for", grade_found[1]))
  }
}