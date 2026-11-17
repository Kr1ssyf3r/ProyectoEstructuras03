# Social UNA — Red social universitaria

## Descripción

Social UNA es una plataforma de interacción universitaria desarrollada en Python para el curso EIF 207 Estructuras de Datos. Permite registrarse, iniciar sesión, publicar texto con fotos o videos, compartir historias de 24 horas, agregar amigos, bloquear usuarios y ver un feed con las publicaciones propias y las de los amigos.

La interfaz es web (HTML, CSS y JavaScript sobre Flask). La información se guarda en archivos JSON y los correos se envían con Gmail SMTP. El proyecto está organizado en capas (modelos, repositorios, servicios, controladores y vistas) y varios módulos usan estructuras de datos propias: diccionarios de conjuntos, un grafo de amistades, un árbol de prefijos (Trie) y mezcla de listas ordenadas.

## Módulos del proyecto

| Módulo | Qué hace | Archivos principales |
|---|---|---|
| Usuarios y autenticación | Registro, inicio de sesión, perfil, recuperación de contraseña y correos | `usuario_service.py`, `recuperacion_service.py`, `correo_service.py` |
| Amistades y bloqueos | Solicitudes, amigos, amigos en común, recomendaciones y bloqueos | `amistadService.py`, `grafoAmistades.py`, `gestorSolicitudes.py`, `gestorBloqueos.py` |
| Publicaciones y muro personal | Crear, editar y eliminar publicaciones con texto, foto o video | `publicacion_service.py`, `publicacion_repository.py`, `publicaciones_routes.py` |
| Feed y reacciones | Feed de Inicio y "Me gusta" | `feed_service.py`, `reaccion_service.py`, `feed_routes.py` |
| Historias | Fotos o videos que expiran a las 24 horas | `historiaService.py`, `historiaRepository.py`, `historias_routes.py` |
| Multimedia | Validación y almacenamiento de fotos y videos | `multimediaService.py` |
| Búsqueda | Autocompletado de usuarios con un Trie | `busquedaService.py`, `Trie.py` |

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

### 8. Publicaciones y muro personal

Cada usuario tiene un muro (`/publicaciones`) donde ve sus propias publicaciones, de la más reciente a la más antigua, y puede crearlas, editarlas y eliminarlas. También puede publicar desde la pantalla de Inicio.

**Crear**
- Texto de hasta 500 caracteres (`MAX_LONGITUD`).
- Una foto o un video opcional. Se acepta una publicación solo con archivo, pero no una vacía.
- Fotos: `jpg`, `jpeg`, `png`, `gif` y `webp` (máximo 5 MB). Videos: `mp4` y `webm` (máximo 25 MB).
- Los archivos se guardan en `data/uploads/` con un nombre aleatorio (UUID), nunca con el nombre original.
- Se rechazan las etiquetas HTML en el texto y las palabras de la lista `PALABRAS_PROHIBIDAS` (se comparan en minúscula y sin tildes).
- Solo se permite publicar a un usuario que existe.

**Editar y eliminar**
- Solo el autor puede editar o eliminar su publicación.
- Editar cambia el texto; el archivo adjunto no se modifica. El texto editado pasa por las mismas validaciones.
- Al eliminar una publicación también se borra su archivo de `data/uploads/`.

**Rutas**

| Ruta | Método | Función |
|---|---|---|
| `/publicaciones` | GET | Muro del usuario (acepta `?editar=<id>`) |
| `/publicaciones/crear` | POST | Crear una publicación |
| `/publicaciones/<id>/editar` | POST | Editar el texto |
| `/publicaciones/<id>/eliminar` | POST | Eliminar |
| `/publicaciones/media/<nombre>` | GET | Entrega la foto o el video (solo con sesión iniciada) |

**Interfaz**
- Botón de modo oscuro en la página de publicaciones. La preferencia se guarda en el navegador (`localStorage`, clave `social-una-theme`) y se comparte con el resto de las páginas.

### 9. Amistades y bloqueos

- **Solicitudes:** enviar, aceptar, rechazar y cancelar. No pueden existir a la vez una solicitud A→B y otra B→A.
- **Amigos:** lista de amigos y eliminación de amistades. La amistad es bidireccional.
- **Amigos en común y recomendaciones:** "Personas que quizás conocés" se calcula contando los amigos que dos usuarios tienen en común; se ordena por mayor cantidad y se excluyen los usuarios con bloqueo en cualquier sentido y aquellos con los que ya hay una solicitud pendiente.
- **Bloqueos:** son dirigidos (que A bloquee a B no implica que B bloquee a A). Al bloquear se elimina la amistad y cualquier solicitud pendiente entre ambos. Se puede desbloquear desde la pestaña "Bloqueados".
- **Notificaciones:** el contador de solicitudes pendientes se consulta en `/api/amistades/notificaciones`.
- **Persistencia:** `data/relaciones.json` guarda las amistades, las solicitudes y los bloqueos.

### 10. Historias

- Una historia es una foto o un video que expira 24 horas después de crearse (`HORAS_VIGENCIA`).
- Los videos de historias están limitados a 10 MB. Los archivos se guardan en `data/historias_media/`.
- Una historia necesita siempre un archivo, a diferencia de una publicación.
- Solo la ven su autor y sus amigos, y no se muestra si hay un bloqueo entre ambos.
- El autor puede eliminar sus historias.
- Rutas: `/historias/crear` (POST), `/historias/archivo/<nombre>` (GET) y `/historias/eliminar/<id>` (POST).
- Si falla el guardado en el JSON, se deshace la historia y se borra el archivo para no dejar archivos huérfanos.

### 11. Búsqueda y autocompletado

`BusquedaService` mantiene un Trie (árbol de prefijos) con las palabras del nombre y el nombre de usuario de cada persona. Las búsquedas ignoran mayúsculas y tildes. Se usa en la pestaña "Buscar personas" de Amigos mediante `/amigos/autocompletar`, y las sugerencias no incluyen usuarios con bloqueo en cualquier sentido. Los archivos JSON siguen siendo la fuente de datos; el Trie es solo un índice en memoria que se reconstruye al iniciar.

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

### Publicaciones (`PublicacionService`)

| Estructura | Contenido | Para qué sirve |
|---|---|---|
| `publicaciones_por_id` | `id` (UUID) → `Publicacion` | Buscar, editar y eliminar una publicación en costo casi constante |
| `ids_por_usuario` | `usuario_id` → lista de `id` | Obtener las publicaciones de un usuario sin recorrer todas |

Las dos estructuras se actualizan siempre juntas. Los identificadores son UUID (`uuid4`) y las publicaciones se guardan en `data/publicaciones.json` con escritura atómica: se escribe un archivo temporal y luego se reemplaza el original, para que un fallo a la mitad no deje el JSON dañado.

### Amistades

| Estructura | Contenido | Para qué sirve |
|---|---|---|
| `GrafoAmistades` | diccionario `usuario_id` → conjunto de amigos | Comprobar si dos usuarios son amigos y calcular amigos en común y recomendaciones |
| `GestorSolicitudes` | `id_solicitud` → solicitud, y un índice `frozenset({A, B})` → `id_solicitud` | Buscar solicitudes y evitar A→B y B→A al mismo tiempo |
| `GestorBloqueos` | `emisor` → conjunto de bloqueados | Consultar bloqueos dirigidos en costo casi constante |

### Historias y búsqueda

- `HistoriaService` guarda las historias en un diccionario por id y otro por autor.
- `Trie` (árbol de prefijos): cada nodo representa una letra, así que buscar por prefijo solo recorre las letras escritas.

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
```

Archivos que genera la aplicación dentro de `data/`:

| Archivo o carpeta | Contenido |
|---|---|
| `usuarios.json` | Cuentas de usuario (contraseñas con hash) |
| `publicaciones.json` | Publicaciones |
| `relaciones.json` | Amistades, solicitudes y bloqueos |
| `reacciones.json` | "Me gusta" |
| `historias.json` | Historias |
| `tokens_recuperacion.json` | Tokens de recuperación (solo hashes). **No se sube al repositorio** |
| `uploads/` | Fotos y videos de las publicaciones |
| `historias_media/` | Fotos y videos de las historias |

Las rutas son relativas, por lo que `python app.py` debe ejecutarse desde la carpeta raíz del proyecto.

## Estructura de archivos

```text
ProyectoEstructuras03/
│
├── app.py
├── requirements.txt
├── .env.example
│
├── application/
│   └── __init__.py              (create_app: construye los servicios y registra las rutas)
│
├── models/
│   ├── usuario.py
│   ├── token_recuperacion.py
│   ├── publicacion.py
│   ├── reaccion.py
│   ├── historia.py
│   ├── solicitudAmistad.py
│   ├── grafoAmistades.py
│   ├── gestorSolicitudes.py
│   ├── gestorBloqueos.py
│   ├── Trie.py
│   └── nodoTrie.py
│
├── repositories/
│   ├── usuario_repository.py
│   ├── token_repository.py
│   ├── publicacion_repository.py
│   ├── reaccion_repository.py
│   ├── historiaRepository.py
│   └── amistadRepository.py
│
├── services/
│   ├── usuario_service.py
│   ├── recuperacion_service.py
│   ├── correo_service.py
│   ├── publicacion_service.py
│   ├── reaccion_service.py
│   ├── feed_service.py
│   ├── amistadService.py
│   ├── historiaService.py
│   ├── multimediaService.py
│   └── busquedaService.py
│
├── controllers/
│   ├── autenticacion_routes.py
│   ├── perfil_routes.py
│   ├── inicio_routes.py
│   ├── publicaciones_routes.py
│   ├── feed_routes.py
│   ├── amistades_routes.py
│   ├── historias_routes.py
│   ├── decorators.py
│   └── csrf.py
│
├── data/                        (datos de ejemplo incluidos, ver más abajo)
│   ├── usuarios.json
│   ├── publicaciones.json
│   ├── relaciones.json
│   ├── reacciones.json
│   ├── historias.json
│   ├── uploads/
│   └── historias_media/
│
├── templates/
│   ├── base.html
│   ├── macros.html
│   ├── login.html
│   ├── registro.html
│   ├── recuperar.html
│   ├── restablecer.html
│   ├── inicio.html
│   ├── publicaciones.html
│   ├── amigos.html
│   ├── perfil.html
│   └── editar_perfil.html
│
├── static/
│   ├── css/    (global, login, registro, recuperacion, restablecer, inicio, feed, publicaciones, amigos, perfil, editar_perfil)
│   └── js/     (login, registro, recuperacion, restablecer, inicio, publicaciones, amigos, autocompletar, historias, notificaciones, perfil, editar_perfil)
│
└── tests/
    ├── test_usuario_service.py
    ├── test_usuario_repository.py
    ├── test_recuperacion_service.py
    ├── test_publicacion_service.py
    ├── test_publicacion_repository.py
    ├── test_reaccion.py
    ├── test_reaccion_repository.py
    ├── test_reaccion_service.py
    ├── test_feed_service.py
    ├── test_feed_routes.py
    ├── test_inicio_feed.py
    ├── testAmistades.py
    ├── testHistoria.py
    └── testTrie.py
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

```bash
pip install -r requirements.txt
```

El archivo instala Flask, python-dotenv y pytest.

Si PowerShell bloquea la activación del entorno virtual, ejecutar antes `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` (solo afecta a esa ventana).

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

Debe ejecutarse desde la carpeta raíz del proyecto, porque las rutas de `data/` son relativas. La aplicación estará disponible en la dirección local configurada por Flask, normalmente:

```text
http://127.0.0.1:5000
```

## Datos de ejemplo

El repositorio incluye datos de ejemplo en `data/` para probar todas las funciones sin registrar cuentas a mano: 7 usuarios, 13 publicaciones (4 con foto y 2 con video), 17 "Me gusta", amistades, solicitudes, bloqueos y 4 historias. Al clonar el repositorio y ejecutar `python app.py` ya están disponibles.

**Todas las cuentas usan la contraseña `Contrasena123`.**

| Usuario | Nombre | Qué permite ver |
|---|---|---|
| `ana` | Ana Mora | La cuenta más completa: 2 amigos (Beto y Carla), 2 solicitudes recibidas (Elena y Fabio), 1 solicitud enviada (a Diego), 1 bloqueado (Gaby), Diego como recomendación con 2 amigos en común, publicaciones con foto y video, y una historia |
| `beto` | Beto Solís | Amigo de Ana, Carla y Diego; tiene bloqueado a Fabio; publicaciones con foto; historia en video |
| `carla` | Carla Jiménez | Amiga de Ana, Beto y Diego; publicaciones con foto; historia |
| `diego` | Diego Rojas | Amigo de Beto, Carla y Elena; recibió una solicitud de Ana; historia |
| `elena` | Elena Vargas | Amiga de Diego; tiene una solicitud enviada a Ana |
| `fabio` | Fabio Núñez | Sin amigos; tiene una solicitud enviada a Ana y está bloqueado por Beto |
| `gaby` | Gaby Salas | Sin amigos; está bloqueada por Ana |

Cómo probar cada función:

- **Amigos, solicitudes y bloqueados:** entrar como `ana` y abrir **Amigos** (pestañas "Mis amigos", "Solicitudes" y "Bloqueados").
- **Amigos en común y recomendaciones:** como `ana`, "Personas que quizás conocés" recomienda a Diego, con Beto y Carla como amigos en común. El autocompletar de `ana` no sugiere a `gaby` porque está bloqueada.
- **Publicaciones, fotos y videos:** el feed de **Inicio** y **Mis publicaciones** muestran publicaciones con foto y con video.
- **Historias:** el círculo "Tú" y los de amigos en la parte superior de **Inicio**.
- **Bloqueo en el otro sentido:** entrar como `fabio` o `gaby` y comprobar que no ven las publicaciones ni historias de quien los bloqueó.

Notas:

- Las historias de ejemplo están configuradas para vencer el 31 de enero de 2027, de modo que sigan visibles durante la evaluación. Las historias nuevas que se creen vencen a las 24 horas.
- Las contraseñas están guardadas con hash (PBKDF2), igual que en cualquier cuenta real.
- Para empezar con la aplicación vacía, detener el servidor y borrar los `.json` de `data/` y el contenido de `uploads/` y `historias_media/`.
- Los datos de ejemplo no envían correos: se crearon sin pasar por el registro por la web.

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

Los archivos de `data/` (JSON, `uploads/` e `historias_media/`) **no** se ignoran, porque forman parte de los datos de ejemplo del entregable. Incluye reglas para excluir:
- Entornos virtuales.
- Archivos temporales.
- Caché de Python.
- Credenciales y variables de entorno.
- El archivo de tokens de recuperación (`data/tokens_recuperacion.json`).
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

Escenarios cubiertos por el módulo de Publicaciones:

- Crear con texto y con foto; rechazo de publicaciones vacías, de más de 500 caracteres, con etiquetas HTML y con palabras prohibidas.
- Usuario inexistente, editar y eliminar solo por el autor, y borrado del archivo al eliminar.
- Formato de archivo no permitido, publicar solo con foto, y que las publicaciones se conserven al reiniciar.
- Repositorio: archivo inexistente, publicaciones antiguas sin foto, guardado atómico (sin archivos temporales y con el original intacto si falla el guardado).

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
- Las acciones de publicaciones (crear, editar, eliminar) solo se aceptan por POST y exigen un token CSRF guardado en la sesión (clave `csrf_publicaciones`).
- Las fotos y los videos se guardan con nombre aleatorio y se entregan solo a usuarios con sesión iniciada.
- Se rechazan las etiquetas HTML en el texto de las publicaciones.
-El "Me gusta" modifica datos, así que solo se acepta por POST y exige un token CSRF guardado en la sesión.
-controllers/csrf.py ofrece obtener_token(clave_sesion) y validar_token(clave_sesion), reutilizables por otros módulos. El feed usa la clave csrf_feed, y las plantillas obtienen el token con csrf_feed().

## Alcance del proyecto

- Registro, autenticación, sesiones, perfiles y recuperación de contraseñas.
- Envío de correos electrónicos.
- Publicaciones con texto, foto o video, y muro personal.
- Feed de Inicio con publicaciones propias y de amigos, reacciones ("Me gusta") y filtro por autor.
- Amistades, solicitudes, amigos en común, recomendaciones y bloqueos.
- Historias de 24 horas.
- Autocompletado de usuarios con un Trie.
- Datos de ejemplo para probar todas las funciones.

Pendiente de mejora: el filtro de palabras prohibidas usa una lista fija y puede ampliarse.