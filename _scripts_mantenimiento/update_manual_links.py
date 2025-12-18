import os
import re

# Configuration
FRONTEND_DIR = r"c:\ContaPY2\frontend\app"

def update_manual_links():
    count_files = 0
    count_replacements = 0

    # Walk through all directories
    for root, dirs, files in os.walk(FRONTEND_DIR):
        for file in files:
            if file.endswith(".js"):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Regex to find: window.open('/manual?file=MESSAGE.md', '_blank')
                    # We capture the filename inside group 1
                    # Pattern matches: window.open('/manual?file=  CAPTURE   ', '_blank')
                    pattern = r"window\.open\('/manual\?file=([^']+)\.md', '_blank'\)"
                    
                    # Function to handle the replacement logic per match
                    def replace_match(match):
                        filename = match.group(1) # e.g. "capitulo_42_traslados"
                        # Construct new path: /manual/filename.html
                        return f"window.open('/manual/{filename}.html', '_blank')"

                    new_content, num_subs = re.subn(pattern, replace_match, content)

                    if num_subs > 0:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        print(f"Updated: {file_path} ({num_subs} matches)")
                        count_files += 1
                        count_replacements += num_subs
                
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

    print("-" * 30)
    print(f"Total files updated: {count_files}")
    print(f"Total links replaced: {count_replacements}")

if __name__ == "__main__":
    update_manual_links()
