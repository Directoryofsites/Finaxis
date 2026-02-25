# PROMPT DE DESARROLLO — Módulo "Servicio al Cliente" para FINAXIS

## Contexto del proyecto

Estás desarrollando un módulo llamado **Portal de Servicio al Cliente** que se integrará dentro de un software contable y financiero llamado **FINAXIS** (Finanzas, Administración y Sistema Integrado). FINAXIS es una plataforma SaaS que se vende o alquila a empresas (condominios, distribuidoras, colegios, clínicas, cooperativas, etc.), quienes a su vez tienen sus propios clientes finales. El módulo que debes construir es un **portal de autogestión** para esos clientes finales, accesible desde la barra lateral derecha del sistema FINAXIS mediante un ícono de auricular (headset). El portal no reemplaza al software principal; es una extensión que vive dentro de él.

---

## Stack tecnológico obligatorio

- **Frontend:** Next.js (React) con Tailwind CSS. El diseño debe ser moderno, limpio y minimalista, coherente con la interfaz actual de FINAXIS que usa una paleta de azules corporativos, fondo claro y tipografía sans-serif.
- **Backend:** Python con FastAPI.
- **Base de datos:** PostgreSQL.
- **Autenticación:** JWT con dos niveles de acceso (detallado más adelante).

---

## Comportamiento general del portal

Al hacer clic en el ícono de Servicio al Cliente en la barra lateral de FINAXIS, debe emerger un **panel deslizante desde la derecha** (drawer/sidebar) sin abandonar la pantalla principal. Este panel tiene un botón de expansión a pantalla completa para cuando el usuario necesite más espacio. El diseño del panel debe respetar los colores y el estilo visual del sistema FINAXIS. Todas las vistas son de **solo lectura** para el cliente final; no puede modificar datos contables.

---

## Sistema de autenticación — Dos niveles

### Nivel 1: Acceso general al portal
El acceso al portal de Servicio al Cliente usa el **mismo usuario y contraseña estándar con el que cualquier usuario se loguea en FINAXIS**. No se crea un sistema de autenticación paralelo; se reutiliza la sesión activa de FINAXIS. Una vez autenticado en este nivel, el usuario puede acceder libremente a los bloques **Mis Solicitudes** y **Mi Comunidad** sin ningún paso adicional, ya que Mis Solicitudes se compone de formularios de entrada de información y Mi Comunidad contiene información general visible para cualquier usuario autenticado.

### Nivel 2: Acceso a "Mi Cuenta" (datos financieros personales)
Para ingresar al bloque **Mi Cuenta**, donde se muestra información financiera privada (estado de cuenta, facturas, pagos, saldos), se requiere una **contraseña personal de nivel 2**. Esta contraseña es independiente de la del nivel 1 y el usuario la crea él mismo a través de una **URL única enviada a su correo electrónico registrado**. El flujo es el siguiente:

1. La administración de la empresa registra el correo del cliente en FINAXIS.
2. El sistema envía automáticamente una URL de activación con token de un solo uso y tiempo de expiración.
3. El cliente accede a esa URL y define su contraseña personal de nivel 2.
4. A partir de ese momento, cada vez que quiera ver su información financiera dentro del portal, el sistema le solicitará esa contraseña antes de mostrar cualquier dato de Mi Cuenta.

Esta contraseña debe almacenarse hasheada con bcrypt en la base de datos. El token de activación de la URL debe expirar en 48 horas y ser de un solo uso; si expira, la administración puede reenviar el enlace manualmente.

**Regla de seguridad crítica:** Un usuario nunca puede ver datos financieros de otro tercero. Todas las consultas del backend al bloque Mi Cuenta deben validar que el `tercero_id` del token JWT coincida exactamente con el `tercero_id` de los datos solicitados. El nivel 2 aplica exclusivamente a Mi Cuenta; los otros dos bloques no lo requieren.

---

## Estructura del módulo — Tres bloques principales

### Dashboard de bienvenida (pantalla inicial del portal)
Al ingresar, el usuario ve un resumen ejecutivo con cuatro datos: saldo total pendiente, fecha del próximo vencimiento, fecha y monto del último pago registrado, y número de casos abiertos (con indicador en rojo si hay alguno). Desde aquí navega a los tres bloques mediante tarjetas clicables.

---

### Bloque 1: Mi Cuenta
Todo lo financiero y contable. Contiene:

- **Estado de cuenta interactivo:** filtrable por rango de fechas y por estado (pagado, pendiente, vencido). Cada fila es clicable y despliega el documento soporte original (factura, nota débito, nota crédito, recibo de caja).
- **Semáforo de vencimientos:** vista visual con indicadores verde (al día), amarillo (vence en menos de 7 días) y rojo (vencido).
- **Historial de pagos:** con detalle de a qué facturas fue aplicado cada pago.
- **Proyección de flujo de caja:** con base en facturas pendientes, muestra cuánto necesita tener disponible el cliente en los próximos 30, 60 y 90 días.
- **Detalle de retenciones y descuentos:** desglose de IVA, retención en la fuente, descuentos por pronto pago u otras deducciones por factura.
- **Descarga de documentos:** el usuario puede descargar cualquier factura o estado de cuenta en PDF o Excel con un solo clic.
- **Solicitud de paz y salvo:** botón que genera automáticamente un certificado de deuda o de saldo cero a la fecha actual, en PDF, sin intervención humana.

---

### Bloque 2: Mis Solicitudes
Canal formal y trazable para comunicación con la empresa. Contiene:

- **Centro de PQR (Peticiones, Quejas y Reclamos):** formulario estructurado. Al enviarlo, el sistema genera un número de radicado y notifica por correo. El usuario puede ver el estado del caso: Recibido → En revisión → Resuelto.
- **Disputa de factura o saldo:** flujo específico (separado de PQR) para cuando el cliente no reconoce un cobro o un pago no le fue aplicado. Tiene prioridad visual sobre PQR generales.
- **Solicitudes especiales:** refinanciación, ampliación de plazo, cambio en condiciones de crédito. El usuario llena un formulario y queda registro de la solicitud con estado de aprobación o rechazo.
- **Historial de solicitudes:** todas las solicitudes anteriores con su fecha, estado y resolución.

---

### Bloque 3: Mi Comunidad
Este bloque es **configurable**: aparece únicamente si la empresa que usa FINAXIS activa esta funcionalidad (condominios, cooperativas, fondos de empleados). Si no está activo, no aparece en el menú. Contiene:

- **Tablón de anuncios:** la administración publica comunicados que el usuario ve al ingresar.
- **Votaciones y encuestas activas:** el usuario puede votar sobre presupuestos, obras o cambios de reglamento. Queda trazabilidad de cada voto.
- **Propuestas:** el usuario puede publicar una propuesta formal. Si alcanza un umbral configurable de apoyos, sube automáticamente a la administración para revisión.
- **Repositorio de documentos:** actas de asamblea, reglamentos, presupuestos aprobados. Solo lectura.
- **Reserva de espacios comunes:** si la empresa lo habilita, el usuario puede reservar salones, canchas u otros espacios desde el portal.

---

## Elementos transversales (presentes en todo el portal)

- **Barra fija en todas las vistas:** acceso siempre visible a notificaciones, perfil del usuario y ayuda (FAQ).
- **Notificaciones configurables:** el usuario elige recibir alertas por correo cuando se registra una nueva factura, cuando se acerca un vencimiento (configurable: 3, 5 o 7 días antes), o cuando su solicitud cambia de estado.
- **Log de auditoría:** cada acción del usuario (descarga de documento, consulta de saldo, apertura de caso) queda registrada con timestamp. Esto es visible para la empresa pero no para el usuario final.
- **White label:** cada empresa que use FINAXIS puede configurar su propio logo, nombre y colores en el portal. El cliente final solo ve la marca de la empresa con la que hace negocios, no la marca FINAXIS.

---

## Modelo de base de datos — Tablas nuevas requeridas

Las siguientes tablas deben crearse en PostgreSQL. Los datos financieros (facturas, pagos, terceros) ya existen en la base de datos principal de FINAXIS; no deben duplicarse ni modificarse. Solo se crean tablas nuevas para lo que el módulo necesita.

```sql
-- Usuarios del portal (vinculados al tercero ya existente en FINAXIS)
portal_usuarios (id, tercero_id FK, email, password_nivel2_hash, token_activacion, token_expira, nivel2_activo BOOLEAN DEFAULT FALSE, activo, fecha_creacion, ultimo_acceso)


-- Casos de PQR y solicitudes
portal_solicitudes (id, portal_usuario_id FK, tipo ENUM[pqr, disputa, solicitud_especial], asunto, descripcion, estado ENUM[recibido, en_revision, resuelto], fecha_creacion, fecha_resolucion, respuesta)

-- Notificaciones
portal_notificaciones (id, portal_usuario_id FK, tipo, mensaje, leida, fecha)

-- Log de auditoría
portal_auditoria (id, portal_usuario_id FK, accion, detalle, ip, fecha)

-- Anuncios de comunidad
portal_anuncios (id, empresa_id FK, titulo, contenido, fecha_publicacion, activo)

-- Votaciones
portal_votaciones (id, empresa_id FK, titulo, descripcion, fecha_inicio, fecha_cierre, activo)
portal_votos (id, votacion_id FK, portal_usuario_id FK, opcion, fecha)

-- Propuestas
portal_propuestas (id, portal_usuario_id FK, titulo, descripcion, apoyos INT DEFAULT 0, estado ENUM[activa, enviada_admin, cerrada], fecha)

-- Reservas de espacios
portal_espacios (id, empresa_id FK, nombre, descripcion, activo)
portal_reservas (id, espacio_id FK, portal_usuario_id FK, fecha_inicio, fecha_fin, estado ENUM[pendiente, confirmada, cancelada])
```

---

## Endpoints FastAPI requeridos (backend)

### Autenticación
- `POST /auth/login` — reutiliza el login estándar de FINAXIS (usuario + contraseña), devuelve JWT con acceso al portal
- `POST /auth/activar-nivel2` — activa la contraseña de nivel 2 desde el enlace enviado por correo (token de un solo uso, expira en 48h)
- `POST /auth/login-mi-cuenta` — valida la contraseña de nivel 2 y devuelve un token extendido que habilita el acceso al bloque Mi Cuenta
- `POST /auth/reenviar-activacion` — permite a la administración reenviar el enlace de activación si expiró

### Mi Cuenta
- `GET /cuenta/estado` — estado de cuenta con filtros de fecha y estado
- `GET /cuenta/factura/{id}` — detalle y documento soporte de una factura
- `GET /cuenta/pagos` — historial de pagos con aplicación
- `GET /cuenta/vencimientos` — semáforo de vencimientos
- `GET /cuenta/proyeccion` — proyección de flujo a 30/60/90 días
- `GET /cuenta/paz-y-salvo` — genera certificado PDF

### Solicitudes
- `POST /solicitudes/nueva` — crea PQR, disputa o solicitud especial
- `GET /solicitudes/historial` — lista todas las solicitudes del usuario
- `GET /solicitudes/{id}` — detalle de una solicitud

### Comunidad (solo si está habilitada)
- `GET /comunidad/anuncios`
- `GET /comunidad/votaciones`
- `POST /comunidad/votar`
- `GET /comunidad/propuestas`
- `POST /comunidad/propuestas/nueva`
- `POST /comunidad/propuestas/{id}/apoyar`
- `GET /comunidad/espacios`
- `POST /comunidad/reservas/nueva`

### Notificaciones y perfil
- `GET /notificaciones`
- `PUT /notificaciones/{id}/leer`
- `GET /perfil`
- `PUT /perfil/preferencias-notificacion`

---

## Instrucciones de frontend (Next.js + Tailwind)

- El portal se monta como un componente drawer dentro del layout principal de FINAXIS, activado desde la barra lateral derecha.
- Usar **Tailwind CSS** para todo el estilo. La paleta base es azul corporativo (#1E40AF o similar), fondo blanco, texto gris oscuro.
- El diseño debe ser **moderno y limpio**: tarjetas con sombra suave, bordes redondeados, transiciones fluidas al abrir el drawer, iconografía consistente (usar Heroicons o Lucide).
- El **dashboard de bienvenida** usa cuatro tarjetas de resumen con ícono, valor numérico grande y etiqueta pequeña debajo.
- El **semáforo de vencimientos** usa badges de color (verde/amarillo/rojo) en una tabla.
- Las **solicitudes** tienen una línea de tiempo visual del estado del caso.
- Todos los formularios tienen validación del lado del cliente antes de enviar al backend.
- La descarga de documentos debe mostrar un loader y luego abrir el archivo o disparar la descarga sin navegar fuera del portal.
- Las vistas de **Mi Comunidad** solo renderizan si la variable de configuración de la empresa tiene ese módulo activo.
- El portal debe ser completamente **responsivo**: funcionar bien en desktop (drawer lateral) y en móvil (pantalla completa).

---

## Restricciones y reglas de negocio críticas

1. **Un usuario nunca puede ver datos de otro tercero.** Toda consulta debe validar el `tercero_id` del JWT en el backend.
2. **El portal es de solo lectura financieramente.** Ningún endpoint del portal modifica tablas contables de FINAXIS.
3. **El log de auditoría es obligatorio** para cada acción de consulta o descarga.
4. **Las contraseñas y PINs deben almacenarse hasheados** con bcrypt. Nunca en texto plano.
5. **El white label** se resuelve con una tabla de configuración por empresa que el frontend consume al inicializar el portal.
6. **El bloque Mi Comunidad es feature-flag:** controlado por un campo booleano en la tabla de configuración de empresa.
