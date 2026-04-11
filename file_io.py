import time
import tracemalloc
import pancake_brain as pb

def read_board(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    num_pancakes = int(lines[0].strip())
    initial_order = tuple(map(int, lines[1].strip().split()))
    return initial_order

def write_result(filename, initial_state, path, moves, time_taken, memory, states):
    with open(filename, 'w') as f:
        f.write(f"Initial State: {initial_state}\n")
        f.write(f"Steps ({moves} moves):\n")
        for state in path:
            f.write(f"{state}\n")
        f.write(f"\nCalculation time: {time_taken:.5f} s\n")
        f.write(f"Used memory: {memory} bytes\n")
        f.write(f"Explored states: {states}\n")

# This was just for testing
if __name__ == '__main__':
    # Creates a quick test file
    with open('test_input.txt', 'w') as f:
        f.write("4\n3 1 4 2")
    
    board = read_board('test_input.txt')
    print("Read board:", board)
