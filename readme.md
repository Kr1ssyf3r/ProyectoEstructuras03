# Social UNA — Módulo de Usuarios y Autenticación

## Descripción

Social UNA es una plataforma de interacción universitaria desarrollada en Python. Este módulo contempla la gestión de usuarios, el registro de cuentas, la autenticación, los perfiles y la recuperación de contraseñas.

La implementación utiliza Flask para gestionar las solicitudes web, archivos JSON para la persistencia de información y Gmail SMTP para el envío de correos electrónicos.

## Funcionalidades desarrolladas

### 1. Registro de usuarios

El módulo incluye el proceso de creación de cuentas dentro de la plataforma.

Características:
- Registro de nombre completo.
- Nombre de usuario.
- Correo electrónico.
- Contraseña y confirmación.
- Validación de campos obligatorios.
- Validación básica del formato del correo.
- Comprobación de usuarios y correos duplicados.
- Generación de identificadores únicos mediante UUID.
- Fecha de registro automática.
- Envío de correo electrónico de bienvenida.

### 2. Gestión de contraseñas

Se implementa un mecanismo de protección para evitar almacenar las contraseñas directamente en los archivos JSON.

Se utiliza:
- PBKDF2-HMAC-SHA256.
- 600 000 iteraciones.
- Salt aleatorio de 16 bytes.
- Verificación de contraseñas mediante comparación de hashes.

### 3. Inicio y cierre de sesión

El sistema contempla:
- Inicio de sesión mediante las credenciales registradas.
- Validación de las credenciales.
- Gestión del estado de autenticación mediante sesiones de Flask.
- Restricción de acceso a páginas que requieren autenticación.
- Cierre de sesión.

### 4. Gestión de perfiles

Se incluyen funcionalidades para consultar y modificar la información personal del usuario.

Características:
- Visualización del perfil.
- Consulta de los datos del usuario autenticado.
- Edición del nombre.
- Edición del nombre de usuario.
- Edición del correo electrónico.
- Validación de los datos modificados.
- Comprobación de duplicados.
- Actualización de la información persistida.

### 5. Recuperación de contraseñas

El módulo incorpora un mecanismo de recuperación mediante enlaces enviados al correo electrónico del usuario.

Características:
- Solicitud de recuperación mediante correo electrónico.
- Generación de tokens aleatorios seguros.
- Almacenamiento del hash del token en lugar del token original.
- Tiempo de expiración de 30 minutos.
- Validación de la vigencia del token.
- Restricción de uso único.
- Invalidación de tokens anteriores del mismo usuario.
- Restablecimiento de la contraseña.
- Validación de la nueva contraseña y su confirmación.

### 6. Servicio de correo electrónico

Se incorpora `CorreoService` para centralizar el envío de correos mediante Gmail SMTP.

Actualmente contempla dos tipos de mensajes:

**Correo de bienvenida**
- Se utiliza durante el registro de una cuenta.
- Confirma la creación de la cuenta.
- Incluye un mensaje de bienvenida a Social UNA.

**Correo de recuperación**
- Se utiliza cuando un usuario solicita recuperar su contraseña.
- Incluye el enlace para restablecerla.
- Informa que el enlace expira después de 30 minutos y solo puede utilizarse una vez.

El servicio utiliza SMTP SSL mediante el servidor `smtp.gmail.com` y el puerto `465`.

### 7. Feed y reacciones

Este módulo contempla el feed de la pantalla de Inicio y las reacciones a las publicaciones. El feed muestra las publicaciones del usuario y las de sus amigos, de la más reciente a la más antigua, y permite dar y quitar "Me gusta", actualizar el feed y filtrar las publicaciones por autor.

Se apoya en los servicios de otros módulos: `usuario_service` (validar que el estudiante existe), `amistad_service` (obtener los amigos) y `publicacion_service` (obtener las publicaciones de cada autor).

**Feed**
- Muestra las publicaciones propias y las de los amigos.
- Ordena las publicaciones de la más reciente a la más antigua, mezclando autores distintos.
- Limita la cantidad de tarjetas mostradas (`LIMITE_FEED`, actualmente 20).
- Cada tarjeta muestra el autor, la fecha, el texto, la foto o el video, la cantidad de "Me gusta" y si el usuario activo ya dio el suyo.
- Se recalcula en cada petición, por lo que siempre refleja las publicaciones, las amistades y los "Me gusta" actuales.

**Reacciones ("Me gusta")**
- Dar y quitar "Me gusta" con un solo botón (con corazón).
- Un usuario no puede reaccionar dos veces a la misma publicación.
- Dar el mismo "Me gusta" dos veces o quitar uno que no existe no produce errores.
- No se permite reaccionar con un usuario inexistente ni a una publicación inexistente.
- Los "Me gusta" se guardan en `data/reacciones.json` y se reconstruyen al iniciar la aplicación.

**Actualizar y filtrar**
- Botón **Actualizar**, que vuelve a pedir el feed (y conserva el filtro si hay uno activo).
- Filtro por autor mediante `/inicio?autor=<id>`: se activa al pulsar el nombre de un autor en una tarjeta y se desactiva con "Ver todas".
- Solo se puede filtrar por el propio usuario o por sus amigos. Cualquier otro identificador se rechaza con un aviso.

**Mensajes en Inicio**

La pantalla de Inicio muestra los mensajes `flash` (por ejemplo, el aviso de que no se pudo dar un "Me gusta"), que antes no se mostraban.

## Estructuras de datos

### Reacciones (`ReaccionRepository`)

| Estructura | Contenido | Para qué sirve |
|---|---|---|
| Diccionario principal | `(usuario_id, publicacion_id)` → `Reaccion` | Fuente de datos. La clave identifica de forma única cada reacción, así que los duplicados se evitan por construcción |
| Diccionario de conjuntos | `publicacion_id` → conjunto de `usuario_id` | Saber cuántos "Me gusta" tiene una publicación |
| Diccionario de conjuntos | `usuario_id` → conjunto de `publicacion_id` | Saber a qué publicaciones reaccionó un usuario |

Los dos diccionarios de conjuntos son índices: se construyen a partir del principal y se actualizan siempre juntos. Con ellos, comprobar si existe una reacción, contar los "Me gusta" de una publicación y consultar las publicaciones de un usuario son operaciones de costo casi constante.

### Feed (`FeedService`)

- Los autores visibles se guardan en un diccionario `id` → `Usuario` (el propio usuario y sus amigos), para obtener el nombre del autor de cada tarjeta con una búsqueda directa.
- Cada autor entrega sus publicaciones ya ordenadas de la más reciente a la más antigua, y se combinan con `heapq.merge` (mezcla de listas ordenadas) en lugar de reordenar todo.
- `itertools.islice` limita el resultado. Como la mezcla es perezosa, solo se calculan los "Me gusta" de las tarjetas que realmente se muestran.

## Persistencia

Las reacciones se guardan en `data/reacciones.json` como una lista de objetos:

```json
[
    {
        "usuario_id": "...",
        "publicacion_id": "...",
        "tipo": "me_gusta",
        "fecha": "2026-11-07T10:30:00"
    }
]

## Estructura de archivos relacionados

```text
ProyectoEstructuras03/
│
├── app.py
│
├── models/
│   ├── usuario.py
│   ├── token_recuperacion.py
│   └── reaccion.py
│
├── repositories/
│   ├── usuario_repository.py
│   ├── token_repository.py
│   └── reaccion_repository.py
│
├── services/
│   ├── usuario_service.py
│   ├── recuperacion_service.py
│   ├── correo_service.py
│   ├── reaccion_service.py
│   └── feed_service.py
│
├── controllers/
│   ├── feed_routes.py
│   └── csrf.py
│
├── data/
│   ├── usuarios.json
│   ├── tokens_recuperacion.json
│   └── reacciones.json          (se genera al ejecutar)
│
├── templates/
│   ├── login.html
│   ├── registro.html
│   ├── recuperar.html
│   ├── restablecer.html
│   ├── perfil.html
│   └── editar_perfil.html
│
├── static/
│   ├── css/
│   │   ├── login.css
│   │   ├── registro.css
│   │   ├── recuperacion.css
│   │   ├── restablecer.css
│   │   ├── perfil.css
│   │   ├── editar_perfil.css
│   │   └── feed.css
│   │
│   └── js/
│       ├── login.js
│       ├── registro.js
│       ├── recuperacion.js
│       ├── perfil.js
│       └── editar_perfil.js
│
└── tests/
    ├── test_reaccion.py
    ├── test_reaccion_repository.py
    ├── test_reaccion_service.py
    ├── test_feed_service.py
    ├── test_feed_routes.py
    └── test_inicio_feed.py
```

## Tecnologías utilizadas

| Tecnología | Aplicación |
|---|---|
| Python | Lenguaje principal |
| Flask | Aplicación web y gestión de rutas |
| HTML5 | Estructura de las vistas |
| CSS3 | Estilos de la interfaz |
| JavaScript | Interactividad del frontend |
| JSON | Persistencia de información |
| UUID | Identificadores únicos |
| PBKDF2-HMAC-SHA256 | Protección de contraseñas |
| Gmail SMTP | Envío de correos electrónicos |
| python-dotenv | Lectura de variables de entorno |
| Git y GitHub | Control de versiones |

## Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone URL_DEL_REPOSITORIO
cd ProyectoEstructuras03
```

### 2. Crear un entorno virtual

En Windows:

```powershell
python -m venv .venv
```

Activarlo:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

Si el proyecto dispone de `requirements.txt`:

```bash
pip install -r requirements.txt
```

Si todavía no se cuenta con ese archivo, las dependencias principales del módulo incluyen:

```bash
pip install Flask python-dotenv
```

### 4. Configurar las variables de entorno

Crear una copia del archivo de ejemplo:

```powershell
Copy-Item .env.example .env
```

Editar `.env` con las credenciales correspondientes:

```env
GMAIL_USER=tu_correo@gmail.com
GMAIL_APP_PASSWORD=tu_contrasena_de_aplicacion
```

La contraseña debe ser una contraseña de aplicación de Google, no la contraseña habitual de la cuenta.

### 5. Ejecutar la aplicación

```bash
python app.py
```

La aplicación estará disponible en la dirección local configurada por Flask, normalmente:

```text
http://127.0.0.1:5000
```

## Configuración del correo electrónico

Para utilizar el envío de correos mediante Gmail es necesario:

1. Contar con una cuenta de Google.
2. Activar la verificación en dos pasos.
3. Generar una contraseña de aplicación.
4. Configurar `GMAIL_USER` y `GMAIL_APP_PASSWORD` en el archivo `.env`.

Las credenciales deben mantenerse fuera del repositorio.

## Archivos de configuración

### `.env`

Contiene las credenciales utilizadas para el envío de correos. Es un archivo local y no debe subirse a GitHub.

### `.env.example`

Contiene una plantilla de las variables necesarias para configurar el envío de correos. No debe incluir credenciales reales y puede compartirse mediante el repositorio.

### `.gitignore`

Incluye reglas para excluir:
- Entornos virtuales.
- Archivos temporales.
- Caché de Python.
- Credenciales y variables de entorno.
- Datos JSON locales.
- Archivos de configuración de editores.

## Pruebas

Para ejecutar las pruebas automatizadas del proyecto:

```bash
python -m pytest -v
```

Entre los escenarios que pueden contemplarse durante las pruebas se encuentran:

- Registro de usuarios.
- Validación de datos inválidos.
- Detección de usuarios y correos duplicados.
- Inicio de sesión con credenciales correctas e incorrectas.
- Acceso a páginas protegidas.
- Actualización de información del perfil.
- Solicitud de recuperación de contraseña.
- Validación de tokens expirados o utilizados.
- Restablecimiento de contraseñas.
- Envío de correos de bienvenida y recuperación.

Escenarios cubiertos por el módulo de Feed y Reacciones:

-Validación del modelo Reaccion (campos vacíos, tipos incorrectos, tipo y fecha inválidos) y conversión a diccionario y de vuelta.
-Repositorio: agregar, eliminar, duplicados, consultas, persistencia entre repositorios, pares repetidos en el archivo y deshacer en memoria cuando falla el guardado.
-Servicio de reacciones: dar, quitar y alternar, usuario o publicación inexistentes.
-Feed: publicaciones propias y de amigos, exclusión de desconocidos, orden, límite, filtro por autor y usuario inexistente.
-Ruta de "Me gusta": token CSRF ausente o incorrecto, dar y quitar, redirección a la misma tarjeta y acceso sin sesión.
-Pantalla de Inicio: contenido y orden del feed, botón de "Me gusta", botón de actualizar, filtro por autor y mensajes de error.

## Consideraciones de seguridad

- Evitar almacenar contraseñas en texto plano.
- Mantener las credenciales fuera del repositorio.
- Almacenar hashes de los tokens de recuperación.
- Validar los datos recibidos antes de procesarlos.
- Restringir el acceso a las rutas que requieren autenticación.
- Evitar mostrar los enlaces de recuperación directamente en la interfaz.
- Utilizar conexiones seguras para el envío de correos.
-El "Me gusta" modifica datos, así que solo se acepta por POST y exige un token CSRF guardado en la sesión.
-controllers/csrf.py ofrece obtener_token(clave_sesion) y validar_token(clave_sesion), reutilizables por otros módulos. El feed usa la clave csrf_feed, y las plantillas obtienen el token con csrf_feed().

## Alcance del módulo

El módulo comprende los componentes relacionados con la gestión de usuarios de Social UNA:

- Modelo de usuario.
- Registro y validación de cuentas.
- Autenticación y sesiones.
- Visualización y edición de perfiles.
- Recuperación y restablecimiento de contraseñas.
- Envío de correos electrónicos.
-Feed de Inicio con publicaciones propias y de amigos.
-Reacciones ("Me gusta") a las publicaciones.
-Filtro de publicaciones por autor.

Su desarrollo puede ampliarse conforme avance la integración con los demás módulos de la plataforma.
