import re

INPUT_FILE = r"c:\ContaPY2\Manual\maestros\activos.txt"

def check_file():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        # Check for non-printable chars (excluding newline)
        for char in line:
            if not char.isprintable() and char not in ['\n', '\r', '\t']:
                print(f"Line {i+1}: Found non-printable char code {ord(char)}")
                print(f"Content: {line.strip()}")
                
        # Check specifically around 124010
        if "124010" in line:
            print(f"Line {i+1} (Target): {line.strip()}")
            print(f"Hex: {line.encode('utf-8').hex()}")

if __name__ == "__main__":
    check_file()