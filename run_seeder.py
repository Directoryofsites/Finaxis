
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core import seeder

if __name__ == "__main__":
    print("Executing seeder...")
    seeder.seed_database()
