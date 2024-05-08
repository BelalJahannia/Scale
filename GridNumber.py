target_number = 262144

# Find all combinations of two integers whose multiplication is equal to target_number
combinations = []
for i in range(1, int(target_number ** 0.5) + 1):
    if target_number % i == 0:
        j = target_number // i
        combinations.append((i, j))
        if i != j:
            combinations.append((j, i))

# Sort the combinations based on the first number
combinations.sort(key=lambda x: x[0])

# Print the combinations
for combination in combinations:
    print(f'({combination[0]}, {combination[1]})')

output_file_path = 'Grids262144.txt'
with open(output_file_path, 'w') as output_file:
    for n in combinations:
        output_file.write(f'{n[0]}, {n[1]}\n')