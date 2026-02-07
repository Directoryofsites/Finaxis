import sys

def check_balance(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    stack = []
    pairs = {'(': ')', '{': '}', '[': ']'}
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        for j, char in enumerate(line):
            if char in pairs.keys():
                stack.append((char, i + 1, j + 1))
            elif char in pairs.values():
                if not stack:
                    print(f"Extra closing '{char}' at line {i+1}, col {j+1}")
                    return False
                opening, line_num, col_num = stack.pop()
                if pairs[opening] != char:
                    print(f"Mismatched '{char}' at line {i+1}, col {j+1}. Expected '{pairs[opening]}' for '{opening}' from line {line_num}, col {col_num}")
                    return False
    
    if stack:
        for char, i, j in stack:
            print(f"Unclosed '{char}' from line {i}, col {j}")
        return False
    
    print("Balance OK")
    return True

if __name__ == "__main__":
    check_balance(sys.argv[1])
