import os

# Function to traverse the directory and extract .csv files
def extract_csv_files(directory):
    csv_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                csv_files.append([file, file_path])
    return csv_files

# Specify the directory path
directory_path = './topologies'

# Extract .csv files and their directories
csv_files_info = extract_csv_files(directory_path)

# Print the 2D array containing .csv file names and directories
for csv_info in csv_files_info:
    print(f'File Name: {csv_info[0]}, Directory: {csv_info[1]}')

# Write the CSV file information to a text file
output_file_path = 'csv_files_info.txt'
with open(output_file_path, 'w') as output_file:
    for csv_info in csv_files_info:
        output_file.write(f'{csv_info[0]}, {csv_info[1]}\n')


"""
# Specify the directory path
directory_path = './topologies/conv_nets'

# List all files in the directory
files = os.listdir(directory_path)

# Print the list of file names
for file in files:
    if file.endswith(".csv"):
        print(file)
"""