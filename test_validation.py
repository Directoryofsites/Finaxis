from app.services.conciliacion_bancaria import ImportEngine
from app.schemas.conciliacion_bancaria import ImportConfig
from sqlalchemy.orm import Session
from decimal import Decimal

class MockDB:
    pass

engine = ImportEngine(MockDB())
config = ImportConfig(
    id=1,
    name="Test Config",
    bank_id=1,
    empresa_id=1,
    file_format="TEXTO",
    header_rows=0,
    field_mapping={"date": 0, "description": 1, "amount": 2, "balance": 3},
    date_format="DD/MM/YYYY",
    delimiter=",",
    is_active=True,
    created_at="2026-03-09T00:00:00",
    updated_at="2026-03-09T00:00:00",
    created_by=1
)

lines = [
    "1/02 SAVINGS INTEREST CREDIT 58.31",
    "2/02 INTERBANK PAYMENT IGLESIA CRISTIA 2,000,000.00 44,573,233.7:",
    "DESDE: Algo",
    "FROM: Algo",
    "28/02 PAGO PROVEEDORES 1,500.00 40,000.00"
]

print("TESTING _fallback_parse_line AND _validate_row_data")
import re
# Nueva expresión regular para incluir DD/MM además de completos
date_pattern = re.compile(r'^\s*(\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}|\d{1,2}[-/.]\d{1,2}|\d{1,2}\s+[A-Za-z]{2,8}\s+\d{0,4})')

for row_num, line in enumerate(lines, 1):
    print(f"\n--- Line {row_num}: {line}")
    if date_pattern.search(line):
        print("  Matched date pattern!")
        parts = engine._fallback_parse_line(line, config)
        print(f"  Parsed parts: {parts}")
        if parts and len(parts) >= 3:
            errors = engine._validate_row_data(parts, config, row_num)
            if errors:
                print(f"  Validation Errors: {errors}")
            else:
                print("  Validation SUCCESS")
    else:
        print("  Did NOT match date pattern")
