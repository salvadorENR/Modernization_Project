# 1. Load necessary libraries
library(dplyr)
library(readr)
library(stringr)

# 2. Define the Language (LEN) Answer Keys
# Transcribed from the images provided
len_keys <- list(
  "3G" = c("B", "B", "C", "C", "A", "B", "C", "A", "B", "C", "A", "C", "B", "B", "A", "C", "B", "A"),
  "4G" = c("B", "A", "C", "C", "A", "B", "C", "B", "A", "B", "A", "B", "C", "A", "B", "C", "B", "A", "B", "B", "C", "A", "C", "B"),
  "5G" = c("C", "D", "A", "C", "B", "D", "A", "D", "B", "A", "C", "B", "D", "D", "B", "A", "D", "A", "A", "D", "D", "C", "B", "C"),
  "6G" = c("B", "C", "A", "B", "A", "C", "C", "C", "B", "A", "B", "D", "B", "C", "B", "C", "A", "A", "D", "A", "B", "C", "D", "A"),
  "7G" = c("C", "A", "A", "D", "B", "D", "B", "B", "C", "D", "A", "A", "A", "B", "B", "A", "C", "D", "A", "C", "A", "D", "B", "D"),
  "8G" = c("B", "D", "A", "C", "D", "C", "C", "D", "A", "C", "A", "D", "B", "D", "A", "D", "B", "C", "D", "B", "B", "D", "A", "C"),
  "9G" = c("D", "C", "B", "A", "D", "B", "A", "D", "B", "B", "D", "A", "D", "C", "B", "A", "B", "B", "A", "B", "D", "C", "C", "B"),
  "1B" = c("D", "A", "B", "D", "B", "C", "D", "C", "A", "A", "B", "C", "A", "C", "D", "D", "B", "A", "B", "A", "B", "D", "A", "C"),
  "2B" = c("C", "A", "D", "C", "B", "C", "C", "B", "A", "D", "A", "D", "A", "A", "C", "B", "C", "D", "D", "B", "A", "D", "C", "B")
)

# 3. Define your folder paths
csv_folder <- "DataSets/CML 2025 FEBRERO/LEN_CSV" # Folder from Python
scored_folder <- "DataSets/CML 2025 FEBRERO/LEN_SCORED_CSV"
if (!dir.exists(scored_folder)) dir.create(scored_folder)

# 4. Get list of Language (LEN) CSV files
files <- list.files(path = csv_folder, pattern = "LEN.*\\.csv$", full.names = TRUE)

# 5. Loop through each file and score it
for (f in files) {
  # Read the data
  df <- read_csv(f)
  
  # Identify which grade key to use (3G, 4G, etc.)
  grade_found <- names(len_keys)[sapply(names(len_keys), function(x) str_detect(f, x))]
  
  if (length(grade_found) > 0) {
    current_key <- len_keys[[grade_found[1]]]
    
    # Check if the CSV has the required columns
    if ("CLAVE" %in% names(df) & "NUM_ITEM" %in% names(df)) {
      
      # Score the CLAVE column: 1 if correct, 0 if incorrect
      df_scored <- df %>%
        mutate(SCORE = if_else(CLAVE == current_key[NUM_ITEM], 1, 0))
      
      # Save the new scored file
      new_filename <- paste0("SCORED_LEN_", basename(f))
      write_csv(df_scored, file.path(scored_folder, new_filename))
      
      message(paste("Successfully scored:", basename(f), "using LEN key for", grade_found[1]))
    } else {
      warning(paste("File", basename(f), "is missing 'CLAVE' or 'NUM_ITEM' columns."))
    }
  } else {
    message(paste("No matching grade key found for file:", basename(f)))
  }
}

message("--- LEN Scoring Process Completed ---")