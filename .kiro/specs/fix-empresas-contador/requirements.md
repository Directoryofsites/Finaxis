# Documento de Requisitos - Corrección Visualización Empresas para Rol Contador

## Introducción

El sistema actualmente presenta un problema donde los usuarios con rol "contador" no pueden visualizar las empresas que ellos mismos han creado. Solo pueden ver empresas creadas por usuarios con rol "soporte". Este comportamiento es incorrecto y debe ser corregido para permitir que los contadores vean todas las empresas que han creado.

## Glosario

- **Sistema**: La aplicación Torre de Control Contable
- **Usuario_Contador**: Usuario con rol "contador" en el sistema
- **Usuario_Soporte**: Usuario con rol "soporte" (empresa creadora del programa)
- **Empresa**: Entidad empresarial gestionada en el sistema
- **Lista_Empresas**: Interfaz que muestra las empresas disponibles para un usuario

## Requisitos

### Requisito 1

**Historia de Usuario:** Como usuario con rol contador, quiero ver todas las empresas que he creado en la lista de empresas gestionadas, para poder acceder y administrar mis empresas.

#### Criterios de Aceptación

1. CUANDO un Usuario_Contador accede a la Lista_Empresas ENTONCES el Sistema DEBERÁ mostrar todas las empresas creadas por ese usuario
2. CUANDO un Usuario_Contador crea una nueva empresa ENTONCES el Sistema DEBERÁ incluir esa empresa en su Lista_Empresas inmediatamente
3. CUANDO un Usuario_Contador visualiza la Lista_Empresas ENTONCES el Sistema DEBERÁ mantener la visibilidad de empresas creadas por Usuario_Soporte que le hayan sido asignadas
4. CUANDO se consultan las empresas de un Usuario_Contador ENTONCES el Sistema DEBERÁ filtrar por el ID del usuario creador o por asignación específica
5. CUANDO un Usuario_Soporte crea una empresa para un Usuario_Contador ENTONCES el Sistema DEBERÁ hacer visible esa empresa para ambos usuarios

### Requisito 2

**Historia de Usuario:** Como administrador del sistema, quiero que los permisos de visualización de empresas funcionen correctamente según el rol del usuario, para mantener la seguridad y funcionalidad del sistema.

#### Criterios de Aceptación

1. CUANDO un Usuario_Soporte accede a la Lista_Empresas ENTONCES el Sistema DEBERÁ mostrar todas las empresas del sistema
2. CUANDO se validan permisos de empresa ENTONCES el Sistema DEBERÁ verificar tanto la creación como la asignación del usuario
3. CUANDO se actualiza la lista de empresas ENTONCES el Sistema DEBERÁ aplicar los filtros correctos según el rol del usuario
4. CUANDO un usuario sin permisos intenta acceder a una empresa ENTONCES el Sistema DEBERÁ denegar el acceso
5. MIENTRAS un usuario tenga sesión activa ENTONCES el Sistema DEBERÁ mantener consistencia en la visualización de empresas