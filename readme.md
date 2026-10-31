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

## Estructura de archivos relacionados

```text
ProyectoEstructuras03/
│
├── app.py
│
├── models/
│   ├── usuario.py
│   └── token_recuperacion.py
│
├── repositories/
│   ├── usuario_repository.py
│   └── token_repository.py
│
├── services/
│   ├── usuario_service.py
│   ├── recuperacion_service.py
│   └── correo_service.py
│
├── data/
│   ├── usuarios.json
│   └── tokens_recuperacion.json
│
├── templates/
│   ├── login.html
│   ├── registro.html
│   ├── recuperar.html
│   ├── restablecer.html
│   ├── perfil.html
│   └── editar_perfil.html
│
└── static/
    ├── css/
    │   ├── login.css
    │   ├── registro.css
    │   ├── recuperacion.css
    │   ├── restablecer.css
    │   ├── perfil.css
    │   └── editar_perfil.css
    │
    └── js/
        ├── login.js
        ├── registro.js
        ├── recuperacion.js
        ├── perfil.js
        └── editar_perfil.js
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

## Consideraciones de seguridad

- Evitar almacenar contraseñas en texto plano.
- Mantener las credenciales fuera del repositorio.
- Almacenar hashes de los tokens de recuperación.
- Validar los datos recibidos antes de procesarlos.
- Restringir el acceso a las rutas que requieren autenticación.
- Evitar mostrar los enlaces de recuperación directamente en la interfaz.
- Utilizar conexiones seguras para el envío de correos.

## Alcance del módulo

El módulo comprende los componentes relacionados con la gestión de usuarios de Social UNA:

- Modelo de usuario.
- Registro y validación de cuentas.
- Autenticación y sesiones.
- Visualización y edición de perfiles.
- Recuperación y restablecimiento de contraseñas.
- Envío de correos electrónicos.

Su desarrollo puede ampliarse conforme avance la integración con los demás módulos de la plataforma.
