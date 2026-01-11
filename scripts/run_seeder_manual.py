import sys
import os

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.seeder import seed_database

if __name__ == "__main__":
    seed_database()
