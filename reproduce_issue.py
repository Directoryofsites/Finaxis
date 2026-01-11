
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

try:
    print("Attempting to import app.schemas.empresa...")
    from app.schemas import empresa
    print("Import successful!")
except ImportError as e:
    print(f"Import failed as expected: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
