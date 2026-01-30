# Documento de Diseño - Corrección Visualización Empresas para Rol Contador

## Introducción

Este documento describe la solución técnica para corregir el problema donde los usuarios con rol "contador" no pueden visualizar las empresas que ellos mismos han creado. El problema se encuentra en la función `get_empresas_para_usuario` del servicio de empresas.

## Arquitectura

### Problema Identificado

La función `get_empresas_para_usuario` en `app/services/empresa.py` tiene una lógica que no está incluyendo correctamente las empresas creadas por usuarios con rol "contador". Actualmente:

1. Si el usuario es "soporte": ve todas las empresas
2. Si el usuario tiene `empresa_id`: ve su empresa principal
3. Ve empresas asignadas a través de la relación `empresas_asignadas`
4. **PROBLEMA**: Las empresas donde el usuario es `owner_id` no se están incluyendo correctamente en todos los casos

### Análisis del Código Actual

```python
def get_empresas_para_usuario(db: Session, current_user: usuario_model.Usuario) -> List[empresa_model.Empresa]:
    # ... código existente ...
    
    # 3. Empresas Propiedad del Usuario (Creador)
    owned_companies = db.query(empresa_model.Empresa).filter(
        empresa_model.Empresa.owner_id == current_user.id
    ).all()
    otras_empresas.extend(owned_companies)
```

El código ya incluye la lógica para obtener empresas donde el usuario es owner, pero hay un problema en la implementación o en cómo se está asignando el `owner_id` al crear empresas.

## Componentes y Interfaces

### Componentes Afectados

1. **Servicio de Empresa** (`app/services/empresa.py`)
   - Función `get_empresas_para_usuario`
   - Función `create_empresa_con_usuarios`

2. **Modelo de Empresa** (`app/models/empresa.py`)
   - Campo `owner_id`
   - Relación con Usuario

3. **Modelo de Usuario** (`app/models/usuario.py`)
   - Relación `empresas_asignadas`
   - Tabla de asociación `usuario_empresas`

### Interfaces de API

- **GET /empresas/**: Endpoint que utiliza `get_empresas_para_usuario`

## Datos del Problema

### Relaciones de Base de Datos

```sql
-- Tabla empresas
CREATE TABLE empresas (
    id INTEGER PRIMARY KEY,
    owner_id INTEGER REFERENCES usuarios(id),
    -- otros campos...
);

-- Tabla de asociación usuario_empresas
CREATE TABLE usuario_empresas (
    usuario_id INTEGER REFERENCES usuarios(id),
    empresa_id INTEGER REFERENCES empresas(id),
    is_owner BOOLEAN DEFAULT FALSE
);
```

### Flujo de Datos Actual

1. Usuario contador crea empresa
2. Se asigna `owner_id` en la tabla empresas
3. Se puede crear entrada en `usuario_empresas` con `is_owner=True`
4. Al consultar empresas, se busca por `owner_id` y por `usuario_empresas`

## Análisis de la Causa Raíz

Después de revisar el código, identifiqué que el problema puede estar en uno de estos puntos:

1. **Asignación incorrecta de owner_id**: Al crear empresas, el `owner_id` no se está asignando correctamente
2. **Falta de entrada en usuario_empresas**: La relación many-to-many no se está creando
3. **Problema en la consulta**: La lógica de consulta tiene un bug

## Solución Propuesta

### Estrategia de Corrección

1. **Verificar y corregir la asignación de owner_id** al crear empresas
2. **Asegurar la creación de la relación en usuario_empresas**
3. **Mejorar la lógica de consulta** para ser más robusta
4. **Agregar logging detallado** para debugging

### Cambios Específicos

#### 1. Corrección en create_empresa_con_usuarios

```python
def create_empresa_con_usuarios(db: Session, empresa_data, owner_id: int = None, padre_id: int = None):
    # ... código existente ...
    
    # CORRECCIÓN: Asegurar que owner_id se asigne correctamente
    nueva_empresa = empresa_model.Empresa(
        # ... otros campos ...
        owner_id=owner_id,  # Asegurar que se asigne
        # ... resto del código ...
    )
    
    # CORRECCIÓN: Asegurar entrada en usuario_empresas
    if owner_id:
        from ..models.usuario import usuario_empresas
        stmt = usuario_empresas.insert().values(
            usuario_id=owner_id, 
            empresa_id=nueva_empresa.id, 
            is_owner=True
        )
        db.execute(stmt)
```

#### 2. Mejora en get_empresas_para_usuario

```python
def get_empresas_para_usuario(db: Session, current_user: usuario_model.Usuario) -> List[empresa_model.Empresa]:
    print(f"DEBUG: get_empresas_para_usuario - User: {current_user.email} (ID: {current_user.id})")
    
    user_roles = {rol.nombre for rol in current_user.roles} if current_user.roles else set()
    
    # Soporte ve todo
    if "soporte" in user_roles:
        print("DEBUG: User is Soporte - returning ALL")
        return db.query(empresa_model.Empresa).order_by(empresa_model.Empresa.razon_social).all()
    
    empresas_map = {}
    
    # 1. Empresa Principal (si tiene)
    if current_user.empresa_id:
        emp_principal = db.query(empresa_model.Empresa).filter(
            empresa_model.Empresa.id == current_user.empresa_id
        ).first()
        if emp_principal: 
            empresas_map[emp_principal.id] = emp_principal
            print(f"DEBUG: Main Company: {emp_principal.razon_social}")
    
    # 2. Empresas donde es owner (CRÍTICO PARA CONTADORES)
    owned_companies = db.query(empresa_model.Empresa).filter(
        empresa_model.Empresa.owner_id == current_user.id
    ).all()
    for empresa in owned_companies:
        empresas_map[empresa.id] = empresa
        print(f"DEBUG: Owned Company: {empresa.razon_social} (ID: {empresa.id})")
    
    # 3. Empresas asignadas via relación M2M
    for asignada in current_user.empresas_asignadas:
        empresas_map[asignada.id] = asignada
        print(f"DEBUG: Assigned Company: {asignada.razon_social} (ID: {asignada.id})")
    
    # 4. Empresas hijas (si es holding)
    if current_user.empresa_id:
        child_companies = db.query(empresa_model.Empresa).filter(
            empresa_model.Empresa.padre_id == current_user.empresa_id
        ).all()
        for empresa in child_companies:
            empresas_map[empresa.id] = empresa
            print(f"DEBUG: Child Company: {empresa.razon_social} (ID: {empresa.id})")
    
    result_list = list(empresas_map.values())
    print(f"DEBUG: Total Companies Found: {len(result_list)}")
    
    # Agregar información de consumo
    # ... código existente para consumo ...
    
    return result_list
```

## Propiedades de Correctitud

*Una propiedad es una característica o comportamiento que debe mantenerse verdadero en todas las ejecuciones válidas del sistema - esencialmente, una declaración formal sobre lo que el sistema debe hacer. Las propiedades sirven como puente entre especificaciones legibles por humanos y garantías de correctitud verificables por máquina.*

### Reflexión de Propiedades

Después de analizar los criterios de aceptación, identifiqué algunas redundancias que pueden consolidarse:

- Las propiedades 1.1, 1.2 y 1.4 están relacionadas con la visibilidad de empresas para contadores y pueden combinarse en una propiedad más comprehensiva
- Las propiedades 2.2 y 2.3 se superponen en la validación de permisos y pueden unificarse
- La propiedad 2.5 sobre consistencia de sesión es más bien un requisito de infraestructura que una propiedad testeable específica

### Propiedades de Correctitud

**Propiedad 1: Visibilidad completa de empresas para contadores**
*Para cualquier* usuario con rol contador, la lista de empresas devuelta debe incluir todas las empresas donde él es el owner_id y todas las empresas que le han sido asignadas explícitamente
**Valida: Requisitos 1.1, 1.2, 1.4**

**Propiedad 2: Persistencia inmediata de empresas creadas**
*Para cualquier* usuario contador que crea una empresa, esa empresa debe aparecer inmediatamente en su próxima consulta de lista de empresas
**Valida: Requisitos 1.2**

**Propiedad 3: Preservación de empresas asignadas por soporte**
*Para cualquier* empresa asignada por soporte a un contador, esa empresa debe permanecer visible para el contador mientras la asignación esté activa
**Valida: Requisitos 1.3**

**Propiedad 4: Visibilidad bidireccional soporte-contador**
*Para cualquier* empresa creada por soporte para un contador específico, tanto el usuario soporte como el contador deben poder ver esa empresa en sus respectivas listas
**Valida: Requisitos 1.5**

**Propiedad 5: Acceso total para usuarios soporte**
*Para cualquier* usuario con rol soporte, la lista de empresas debe incluir todas las empresas existentes en el sistema sin excepción
**Valida: Requisitos 2.1**

**Propiedad 6: Validación correcta de permisos**
*Para cualquier* usuario y empresa, la validación de acceso debe retornar verdadero si y solo si el usuario es owner de la empresa, tiene la empresa asignada, o tiene rol soporte
**Valida: Requisitos 2.2, 2.3**

**Propiedad 7: Denegación de acceso no autorizado**
*Para cualquier* usuario sin permisos sobre una empresa específica (no es owner, no tiene asignación, no es soporte), el sistema debe denegar el acceso a esa empresa
**Valida: Requisitos 2.4**

## Manejo de Errores

### Escenarios de Error

1. **Usuario sin rol definido**: Retornar lista vacía
2. **Empresa inexistente en owner_id**: Ignorar y continuar con otras fuentes
3. **Relación usuario_empresas corrupta**: Usar solo owner_id como fallback
4. **Error de base de datos**: Propagar excepción con mensaje claro

### Estrategias de Recuperación

- **Logging detallado**: Cada paso de la consulta debe ser loggeado para debugging
- **Consultas defensivas**: Usar LEFT JOIN y manejar NULLs apropiadamente
- **Fallback a owner_id**: Si la relación M2M falla, usar solo la relación directa

## Estrategia de Testing

### Testing Unitario

- Crear usuarios con diferentes roles (contador, soporte, admin)
- Crear empresas con diferentes configuraciones de owner_id
- Verificar que cada tipo de usuario ve las empresas correctas

### Testing de Propiedades (Property-Based Testing)

Se utilizará **pytest** con **hypothesis** para implementar las propiedades de correctitud:

- Configurar cada test de propiedades para ejecutar mínimo 100 iteraciones
- Generar usuarios aleatorios con roles específicos
- Generar empresas aleatorias con diferentes configuraciones de ownership
- Verificar que las propiedades se mantienen para todas las combinaciones

### Testing de Integración

- Probar el endpoint completo GET /empresas/
- Verificar que los cambios no afecten otros endpoints
- Probar escenarios de concurrencia (múltiples usuarios consultando simultáneamente)

### Configuración de Testing

```python
# Configuración mínima para property-based testing
@given(
    user_role=st.sampled_from(['contador', 'soporte', 'administrador']),
    num_empresas=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=100)
def test_empresa_visibility_property(user_role, num_empresas):
    # Implementación del test de propiedad
    pass
```

Cada test de propiedad será etiquetado con comentarios que referencien explícitamente la propiedad del documento de diseño usando el formato: '**Feature: fix-empresas-contador, Property {number}: {property_text}**'