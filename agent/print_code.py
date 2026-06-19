import os

# Set the directory you want to search
root_dir = '.'  # current directory, change if needed

# File extensions to include
extensions = ('.py', '.env')

# Files to exclude
excluded_files = {'print_code.py', 'all_code_output.txt', 'app.log'}

# Output file
output_file = 'all_code_output.txt'

with open(output_file, 'w', encoding='utf-8') as out_f:
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            # Include only specified extensions and exclude specific files
            if file.endswith(extensions) and file not in excluded_files:
                file_path = os.path.join(subdir, file)

                out_f.write(f"#### {file_path} ####\n\n")

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        out_f.write(f.read())
                except Exception as e:
                    out_f.write(f"Error reading {file_path}: {e}\n")

                out_f.write("\n\n")  # extra newline between files

print(f"All file contents saved to {output_file}")