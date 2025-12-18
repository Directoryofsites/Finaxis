from app.core.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
columns = inspector.get_columns('ph_conceptos')
print("Columnas en ph_conceptos:")
for column in columns:
    print(f"- {column['name']} ({column['type']})")

print("\nIndices:")
indexes = inspector.get_indexes('ph_conceptos')
for idx in indexes:
    print(f"- {idx['name']}: {idx['column_names']}")
