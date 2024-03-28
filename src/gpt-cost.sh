#!/bin/bash

# Function to convert timestamp to a human-readable date
timestamp_to_date() {
    local ts=$1
    date -d @"$ts"
}


# Check for proper number of command line args.
if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <csv_file_path> <user_email>"
    exit 1
fi

# Set the file path and user email from command line arguments
CSV_FILE="$1"
USER_EMAIL="$2"

# Check if the specified file exists and is readable
if [[ ! -f "$CSV_FILE" ]] || [[ ! -r "$CSV_FILE" ]]; then
    echo "Error: Cannot read file '$CSV_FILE'"
    exit 1
fi

# Set cost per token and convert to cents to avoid floating point arithmetic
COST_PER_INPUT_TOKEN=0.01    # $0.01 per 1000 tokens -> 0.00001 per token
COST_PER_OUTPUT_TOKEN=0.03   # $0.03 per 1000 tokens -> 0.00003 per token

# Accumulate total cost in cents to avoid floating-point issues
TOTAL_COST=0

# Prepare a filtered temporary file with relevant user data
TEMP_FILE=$(mktemp)
grep "$USER_EMAIL" "$CSV_FILE" > "$TEMP_FILE"

# Read the header and get column indexes
HEADER=$(head -n 1 "$CSV_FILE")
IFS=',' read -r -a HEADER_COLUMNS <<< "$HEADER"
for i in "${!HEADER_COLUMNS[@]}"; do
    case "${HEADER_COLUMNS[i]}" in
        "n_context_tokens_total") CONTEXT_INDEX=$i ;;
        "n_generated_tokens_total") GENERATED_INDEX=$i ;;
        "model") MODEL_INDEX=$i ;;
        "timestamp") TIMESTAMP_INDEX=$i ;; 
    esac
done

# Check if we found the necessary columns
if [[ -z $CONTEXT_INDEX || -z $GENERATED_INDEX || -z $MODEL_INDEX || -z $TIMESTAMP_INDEX ]]; then
    echo "Error: Failed to find required columns in the CSV header."
    rm "$TEMP_FILE"
    exit 1
fi

# Process each line
while IFS=, read -r -a row
do
  # Extract the values based on the column indexes
  n_context_tokens_total="${row[$CONTEXT_INDEX]}"
  n_generated_tokens_total="${row[$GENERATED_INDEX]}"
  model="${row[$MODEL_INDEX]}"
  timestamp="${row[$TIMESTAMP_INDEX]}"
  
  # Ensure the model matches the pricing scheme provided
  if [[ $model == "gpt-4-1106-preview" || $model == "gpt-4-1106-vision-preview" ]]; then
      # Calculate costs for input and output tokens
      input_cost=$(echo "scale=6; $n_context_tokens_total * $COST_PER_INPUT_TOKEN / 1000" | bc)
      output_cost=$(echo "scale=6; $n_generated_tokens_total * $COST_PER_OUTPUT_TOKEN / 1000" | bc)
      line_cost=$(echo "scale=6; $input_cost + $output_cost" | bc)
      
      # Convert to cents and update total cost
      line_cost_cents=$(echo "scale=2; $line_cost * 100" | bc) # Convert to cents for accumulation
      TOTAL_COST=$(echo "scale=2; $TOTAL_COST + $line_cost_cents" | bc) # Sum up in cents to keep precision

      echo "Date: $(timestamp_to_date $timestamp), Cost for Entry: $(printf "%.2f" $line_cost) USD"
  fi
done < "$TEMP_FILE"

# Cleanup the temporary file
rm "$TEMP_FILE"

# Output the total cost in dollars
echo "Total cost for user $USER_EMAIL: $(echo "scale=2; $TOTAL_COST / 100" | bc) USD"

