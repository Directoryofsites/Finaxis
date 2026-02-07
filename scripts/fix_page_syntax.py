
import os

file_path = r'c:\ContaPY2\frontend\app\contabilidad\captura-rapida\page.js'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if '</div >' in line:
        print(f"Found bad line: {line.strip()}")
        line = line.replace('</div >', '</div>')
        print(f"Fixed line: {line.strip()}")
    new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("File patched.")
