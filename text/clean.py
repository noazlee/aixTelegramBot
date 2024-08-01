import os

def process_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Find the index of the line containing "/"
    slash_index = next((i for i, line in enumerate(lines) if '/' in line), None)

    if slash_index is not None:
        # Keep only the lines after the slash
        new_lines = lines[slash_index + 1:]

        # Write the processed content back to the file
        with open(file_path, 'w') as file:
            file.writelines(new_lines)
        print(f"Processed: {file_path}")
    else:
        print(f"No '/' found in {file_path}")

def main():
    # Get all .txt files in the current directory
    txt_files = [f for f in os.listdir('.') if f.endswith('.txt')]

    for file_name in txt_files:
        process_file(file_name)

if __name__ == "__main__":
    main()