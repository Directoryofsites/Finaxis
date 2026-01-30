
import sys
import os

# Agregamos el directorio raíz al path para poder importar la app
sys.path.append(os.getcwd())

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.usuario import Usuario, usuario_empresas
from app.models.permiso import Rol
from app.models.empresa import Empresa
from app.services.empresa import create_empresa_con_usuarios, get_empresas_para_usuario
from app.schemas.empresa import EmpresaConUsuariosCreate
# from app.services.usuario import create_user
from app.core.security import get_password_hash
import uuid

def reproduce():
    db = SessionLocal()
    try:
        # 1. Crear Rol Contador si no existe
        rol_contador = db.query(Rol).filter(Rol.nombre == "contador").first()
        if not rol_contador:
            print("Creando rol contador...")
            rol_contador = Rol(nombre="contador", descripcion="Contador")
            db.add(rol_contador)
            db.commit()
            db.refresh(rol_contador)

        # 2. Crear Usuario Contador
        email = f"contador_{uuid.uuid4()}@test.com"
        password = "password123"
        print(f"Creando usuario contador: {email}")
        
        # Usamos creación manual para asegurar roles
        nuevo_usuario = Usuario(
            email=email,
            password_hash=get_password_hash(password),
            nombre_completo="Contador Test"
        )
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        
        # Asignar rol
        nuevo_usuario.roles.append(rol_contador)
        db.commit()
        db.refresh(nuevo_usuario)

        # 3. Crear Empresa como Contador
        print("Creando empresa como contador...")
        from datetime import date
        empresa_data = EmpresaConUsuariosCreate(
            razon_social=f"Empresa Contabilidad {uuid.uuid4()}",
            nit=f"900{str(uuid.uuid4().int)[:6]}",
            email="empresa@test.com",
            fecha_inicio_operaciones=date.today(),
            usuarios=[{"email": f"dummy_{uuid.uuid4()}@test.com", "password": "password123"}]
        )
        
        # Simulamos la lógica del router
        # El contador crea empresas HIJAS de su Holding o de sí mismo
        padre_id = nuevo_usuario.empresa_id 
        owner_id = nuevo_usuario.id
        
        nueva_empresa = create_empresa_con_usuarios(
            db=db, 
            empresa_data=empresa_data,
            owner_id=owner_id,
            padre_id=padre_id
        )
        print(f"Empresa creada: {nueva_empresa.razon_social} (ID: {nueva_empresa.id})")
        
        # Verificar si se asignó a usuario_empresas
        relacion = db.query(usuario_empresas).filter_by(usuario_id=owner_id, empresa_id=nueva_empresa.id).first()
        print(f"Relación en usuario_empresas: {relacion}")

        # 4. Listar empresas para el usuario
        print("Listando empresas para el usuario...")
        empresas = get_empresas_para_usuario(db, nuevo_usuario)
        
        encontrada = False
        for emp in empresas:
            print(f"- {emp.razon_social} (ID: {emp.id})")
            if emp.id == nueva_empresa.id:
                encontrada = True
                
        if encontrada:
            print("SUCCESS: La empresa aparece en la lista.")
        else:
            print("FAILURE: La empresa NO aparece en la lista.")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    reproduce()
