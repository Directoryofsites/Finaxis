import os

path = r"c:\ContaPY2\app\services\propiedad_horizontal\pago_service.py"

try:
    with open(path, "rb") as f:
        content = f.read()

    print(f"Original Size: {len(content)}")
    null_count = content.count(b'\x00')
    print(f"Null Bytes found: {null_count}")

    if null_count > 0:
        new_content = content.replace(b'\x00', b'')
        with open(path, "wb") as f:
            f.write(new_content)
        print("File cleaned successfully.")
    else:
        print("No null bytes found.")

except Exception as e:
    print(f"Error: {e}")
