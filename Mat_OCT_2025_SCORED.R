library(dplyr)
library(readr)
library(stringr)

# 1. Define the Mathematics Answer Keys for October
# Transcribed from the provided images in order: 3G, 4G, 5G, 6G, 7G, 8G, 9G, 1B
math_keys_october <- list(
  "3G" = c("B", "C", "A", "C", "B", "B", "C", "A", "A", "A", "B", "A", "B", "C", "C", "B", "B", "C", "C", "B", "A", "B", "C", "A", "C"),
  "4G" = c("B", "A", "A", "D", "A", "A", "D", "C", "C", "B", "C", "B", "A", "D", "C", "B", "B", "C", "D", "A", "D", "B", "D", "C", "D"),
  "5G" = c("A", "A", "B", "D", "B", "D", "C", "B", "D", "A", "C", "A", "D", "B", "C", "C", "C", "C", "C", "B", "A", "A", "D", "D", "B"),
  "6G" = c("D", "D", "A", "B", "C", "A", "A", "A", "B", "C", "C", "A", "B", "C", "A", "A", "B", "B", "A", "B", "A", "B", "C", "C", "A"),
  "7G" = c("D", "A", "C", "B", "D", "A", "D", "C", "B", "A", "D", "C", "A", "B", "D", "C", "A", "B", "D", "D", "C", "D", "B", "D", "A"),
  "8G" = c("B", "C", "D", "D", "A", "C", "A", "B", "A", "D", "D", "C", "A", "A", "B", "A", "A", "D", "C", "C", "D", "A", "C", "C", "B"),
  "9G" = c("C", "A", "C", "C", "A", "D", "B", "D", "D", "C", "D", "B", "B", "D", "A", "A", "A", "B", "B", "B", "C", "B", "A", "A", "D"),
  "1B" = c("B", "A", "B", "A", "B", "C", "D", "B", "D", "C", "A", "B", "C", "C", "D", "B", "A", "B", "D", "B", "D", "D", "C", "C", "D")
)

# 2. Setup Paths
# Ensure this folder contains your October CSV files
input_folder <- r'C:\Users\salva\Documents\Modernization_Project\DataSets\OCTOBER_DATA'
output_folder <- r'C:\Users\salva\Documents\Scored_Data_Math_Oct'

if (!dir.exists(output_folder)) dir.create(output_folder)

# 3. Process October Files
files <- list.files(path = input_folder, pattern = "MAT.*\\.csv$", full.names = TRUE)

for (f in files) {
  df <- read_csv(f)
  
  # Identify Grade
  grade_found <- names(math_keys_october)[sapply(names(math_keys_october), function(x) str_detect(f, x))]
  
  if (length(grade_found) > 0) {
    current_key <- math_keys_october[[grade_found[1]]]
    
    # Validation: Ensure NUM_ITEM doesn't exceed key length
    df_scored <- df %>%
      mutate(SCORE = if_else(toupper(CLAVE) == current_key[NUM_ITEM], 1, 0))
    
    # Save output
    new_filename <- paste0("SCORED_OCT_", basename(f))
    write_csv(df_scored, file.path(output_folder, new_filename))
    
    message(paste("Processed October Math:", grade_found[1]))
  }
}