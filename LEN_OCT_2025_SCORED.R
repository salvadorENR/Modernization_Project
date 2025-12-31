library(dplyr)
library(readr)
library(stringr)

# 1. Corrected Language (LEN) Answer Keys for October
# Transcribed from the images in the requested order
len_keys_october <- list(
  "3G" = c("B", "A", "C", "A", "B", "A", "C", "B", "A", "B", "A", "C", "B", "A", "C", "C", "B", "B", "B", "C", "C", "C", "A", "B"),
  "4G" = c("C", "D", "A", "C", "B", "D", "A", "D", "B", "A", "C", "B", "D", "D", "B", "A", "D", "A", "A", "D", "D", "C", "B", "C"),
  "5G" = c("B", "C", "A", "B", "A", "C", "C", "C", "B", "A", "B", "D", "B", "C", "B", "C", "A", "A", "D", "A", "B", "C", "D", "A"),
  "6G" = c("C", "A", "A", "D", "B", "D", "B", "B", "C", "D", "A", "A", "A", "B", "B", "A", "C", "D", "A", "C", "A", "D", "B", "D"),
  "7G" = c("B", "D", "A", "C", "D", "C", "C", "D", "A", "C", "A", "D", "B", "D", "A", "D", "B", "C", "D", "B", "B", "D", "A", "C"),
  "8G" = c("D", "C", "B", "A", "D", "B", "A", "D", "B", "B", "D", "A", "D", "C", "B", "A", "B", "B", "A", "B", "D", "C", "C", "B"),
  "9G" = c("D", "A", "B", "D", "B", "C", "D", "C", "A", "A", "B", "C", "A", "C", "D", "D", "B", "A", "B", "A", "B", "D", "A", "C"),
  "1B" = c("C", "A", "D", "C", "B", "C", "C", "B", "A", "D", "A", "D", "A", "A", "C", "B", "C", "D", "D", "B", "A", "D", "C", "B")
)

# 2. Setup Paths
input_folder <- r'C:\Users\salva\Documents\Modernization_Project\DataSets\OCTOBER_DATA'
output_folder <- r'C:\Users\salva\Documents\Scored_Data_Len_Oct'

if (!dir.exists(output_folder)) dir.create(output_folder)

# 3. Process October LEN Files
# We look for "LEN" in the filename
files <- list.files(path = input_folder, pattern = "LEN.*\\.csv$", full.names = TRUE)

for (f in files) {
  df <- read_csv(f)
  
  # Identify Grade (3G, 4G, etc.) from the filename
  grade_found <- names(len_keys_october)[sapply(names(len_keys_october), function(x) str_detect(f, x))]
  
  if (length(grade_found) > 0) {
    current_key <- len_keys_october[[grade_found[1]]]
    
    # Validation and Scoring
    # toupper() handles any lowercase entries in the CSV
    df_scored <- df %>%
      mutate(SCORE = if_else(toupper(CLAVE) == current_key[NUM_ITEM], 1, 0))
    
    # Save the file with a prefix identifying it as scored and October
    new_filename <- paste0("SCORED_OCT_LEN_", basename(f))
    write_csv(df_scored, file.path(output_folder, new_filename))
    
    message(paste("Successfully processed October LEN for:", grade_found[1]))
  } else {
    message(paste("Warning: No grade match found for file:", basename(f)))
  }
}

message("--- October Language Scoring Completed ---")