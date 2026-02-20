
import sys
import os
sys.path.append(os.getcwd())

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.usuario import Usuario
from app.core.security import create_access_token

client = TestClient(app)
db = SessionLocal()

from app.models.empresa import Empresa

def get_or_create_company(db, name, nit):
    emp = db.query(Empresa).filter_by(nit=nit).first()
    if not emp:
        emp = Empresa(
            razon_social=name, 
            nit=nit, 
            dv="1", 
            direccion="Calle Test", 
            telefono="123", 
            email="test@test.com", 
            regimen_fiscal="48"
        )
        db.add(emp)
        db.commit()
        db.refresh(emp)
    return emp

def test_busquedas_isolation():
    print("--- Testing Busquedas Isolation ---")
    
    # 1. Get User and Token
    user = db.query(Usuario).first()
    if not user:
        print("No user found. Skipping.")
        return

    access_token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 2. Get 2 Companies
    co1 = get_or_create_company(db, "Company A Test", "900000001")
    co2 = get_or_create_company(db, "Company B Test", "900000002")
    
    id1 = str(co1.id)
    id2 = str(co2.id)
    
    print(f"User: {user.email}")
    print(f"Testing with Company IDs: {id1} and {id2}")
    
    # 3. Cleanup previous searches for this test (optional, or just ignore)
    import time
    timestamp = int(time.time())
    title_c1 = f"Search Co {id1} - {timestamp}"
    title_c2 = f"Search Co {id2} - {timestamp}"
    
    # 4. Create Search for Company 1
    print(f"Creating search for Company {id1}...")
    headers_c1 = {**headers, "X-Company-ID": id1}
    res1 = client.post("/api/usuarios/busquedas/", json={
        "titulo": title_c1,
        "comando": "test command 1"
    }, headers=headers_c1)
    
    if res1.status_code != 200:
        print(f"Failed to create search 1: {res1.text}")
        return
    print("Created Search 1.")

    # 5. Create Search for Company 2
    print(f"Creating search for Company {id2}...")
    headers_c2 = {**headers, "X-Company-ID": id2}
    res2 = client.post("/api/usuarios/busquedas/", json={
        "titulo": title_c2,
        "comando": "test command 2"
    }, headers=headers_c2)
    
    if res2.status_code != 200:
        print(f"Failed to create search 2: {res2.text}")
        return
    print("Created Search 2.")
    
    # 6. List for Company 1
    print(f"Listing for Company {id1}...")
    list1 = client.get("/api/usuarios/busquedas/", headers=headers_c1)
    data1 = list1.json()
    
    found_c1_in_c1 = any(s['titulo'] == title_c1 for s in data1)
    found_c2_in_c1 = any(s['titulo'] == title_c2 for s in data1)
    
    print(f"In Co{id1}: Found Title1? {found_c1_in_c1} (Expected True)")
    print(f"In Co{id1}: Found Title2? {found_c2_in_c1} (Expected False)")
    
    if found_c1_in_c1 and not found_c2_in_c1:
        print("PASS: Company 1 Isolation OK.")
    else:
        print("FAIL: Company 1 Isolation.")

    # 7. List for Company 2
    print(f"Listing for Company {id2}...")
    list2 = client.get("/api/usuarios/busquedas/", headers=headers_c2)
    data2 = list2.json()
    
    found_c1_in_c2 = any(s['titulo'] == title_c1 for s in data2)
    found_c2_in_c2 = any(s['titulo'] == title_c2 for s in data2)
    
    print(f"In Co{id2}: Found Title1? {found_c1_in_c2} (Expected False)")
    print(f"In Co{id2}: Found Title2? {found_c2_in_c2} (Expected True)")

    if found_c2_in_c2 and not found_c1_in_c2:
        print("PASS: Company 2 Isolation OK.")
    else:
        print("FAIL: Company 2 Isolation.")

if __name__ == "__main__":
    test_busquedas_isolation()
