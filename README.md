# 🏀 Scouting Hub - Sistema de Análisis de Baloncesto

Sistema profesional de análisis y scouting de baloncesto con autenticación de usuarios, gestión de equipos, estadísticas avanzadas y generación de reportes.

## ✨ Características Principales

### 🔐 Sistema de Autenticación

- Autenticación segura con contraseñas hasheadas
- Roles diferenciados (Admin/Usuario)
- Gestión completa de usuarios
- Logs de actividad y estadísticas de uso
- Panel de administración para admins

### 📊 Análisis de Equipos

- Visualización de equipos y jugadores
- Estadísticas detalladas por equipo
- Comparativas entre equipos
- Historial de rendimiento

### 👥 Gestión de Jugadores

- Perfiles completos de jugadores
- Estadísticas individuales
- Análisis de rendimiento
- Comparativas entre jugadores

### 📈 Reportes y Análisis

- Generación de informes profesionales
- Exportación de datos
- Análisis avanzado de estadísticas
- Visualizaciones interactivas

## 🚀 Instalación y Configuración

### Requisitos

- Python 3.8+
- Streamlit
- Pandas
- Plotly (opcional para gráficos avanzados)

### Instalación

```bash
# Clonar repositorio
git clone <repository-url>
cd scouting_app

# Instalar dependencias
pip install -r requirements.txt

# Generar usuarios iniciales
python generate_users.py

# Ejecutar aplicación
streamlit run app.py
```

## 👥 Usuarios Iniciales

### Administradores

- **admin** / ScoutingAdmin2025! (Administrador Principal)
- **admin_coach** / [password_generada] (Entrenador Principal)
- **admin_scout** / [password_generada] (Scout Jefe)

### Usuarios Normales

- 12 usuarios con roles específicos (scout, coach, analyst, observer, reporter, guest)

**⚠️ Importante**: Las credenciales completas se encuentran en `data/auth/initial_credentials.txt`

## 🛠️ Gestión de Usuarios

### Script de Gestión Manual

```bash
python manage_users.py
```

Funcionalidades disponibles:

- ✅ Listar usuarios
- ➕ Crear nuevos usuarios
- ❌ Desactivar/Activar usuarios
- 🔑 Resetear contraseñas
- 🗑️ Eliminar usuarios
- 📊 Ver estadísticas del sistema

### Gestión Programática

```python
from src.auth.user_manager import UserManager

user_manager = UserManager()

# Crear usuario
success, message = user_manager.create_user(
    username="nuevo_usuario",
    password="password123",
    role="user",
    full_name="Nuevo Usuario",
    email="email@domain.com"
)

# Desactivar usuario
success, message = user_manager.deactivate_user("username")

# Resetear contraseña
success, message, new_password = user_manager.reset_password("username")
```

## 📂 Estructura del Proyecto

```
scouting_app/
├── app.py                          # Aplicación principal
├── generate_users.py               # Script generación usuarios
├── manage_users.py                 # Script gestión manual
├── requirements.txt                # Dependencias
├── docs/
│   └── USERS_MANUAL.md            # Manual de usuarios
├── src/
│   ├── auth/                      # Sistema de autenticación
│   │   ├── __init__.py
│   │   ├── authenticator.py       # Autenticador principal
│   │   ├── user_manager.py        # Gestión de usuarios
│   │   ├── logger.py              # Logging de actividad
│   │   └── stats.py               # Estadísticas y métricas
│   ├── components/                # Componentes UI
│   │   ├── header.py              # Header con auth
│   │   └── breadcrumb.py
│   ├── views/                     # Vistas de la aplicación
│   │   ├── login.py               # Vista de login
│   │   ├── home.py
│   │   ├── teams.py
│   │   ├── players.py
│   │   └── reports.py
│   ├── data/                      # Gestión de datos
│   └── utils/                     # Utilidades
├── data/
│   ├── auth/                      # Datos de autenticación
│   │   ├── users.json             # Base de datos usuarios
│   │   ├── access_logs.json       # Logs de acceso
│   │   ├── user_stats.json        # Estadísticas de uso
│   │   └── initial_credentials.txt # Credenciales iniciales
│   ├── cache/                     # Cache de datos
│   └── club_images/               # Imágenes de clubes
└── credentials/
    └── google_drive_credentials.json
```

## 🔒 Seguridad

### Autenticación

- Contraseñas hasheadas con salt SHA-256
- Sesiones seguras en Streamlit
- Validación de roles y permisos
- Logs de todos los accesos

### Gestión de Datos

- Almacenamiento seguro en archivos JSON
- Backup automático recomendado
- Validación de entrada de datos
- Sanitización de parámetros

## 📊 Panel de Administración

Los administradores tienen acceso a:

- 📈 Estadísticas de uso del sistema
- 👥 Gestión completa de usuarios
- 🔍 Logs de actividad detallados
- 📊 Métricas de rendimiento
- 🏀 Estadísticas de equipos más consultados

### Acceso al Panel

1. Iniciar sesión como administrador
2. Header → Usuario → Estadísticas
3. O navegar directamente a la ruta `stats`

## 🔧 Configuración Avanzada

### Variables de Entorno

```bash
# Opcional: Configurar rutas personalizadas
export SCOUTING_DATA_PATH="/custom/path/data"
export SCOUTING_CREDENTIALS_PATH="/custom/path/credentials"
```

### Personalización

- Modificar roles en `src/auth/user_manager.py`
- Personalizar métricas en `src/auth/stats.py`
- Configurar logging en `src/auth/logger.py`

## 📱 Uso de la Aplicación

### Flujo Básico

1. **Login**: Autenticación con credenciales
2. **Dashboard**: Vista principal con métricas
3. **Equipos**: Navegación y análisis de equipos
4. **Jugadores**: Perfiles y estadísticas individuales
5. **Reportes**: Generación de informes avanzados

### Funcionalidades por Rol

- **Admin**: Acceso completo + gestión de usuarios + estadísticas
- **Usuario**: Acceso a todas las funciones de análisis

## 🐛 Troubleshooting

### Problemas Comunes

**Login no funciona**

```bash
# Verificar usuarios
python manage_users.py
# Opción 1: Listar usuarios
```

**Error de permisos**

```bash
# Verificar rol del usuario
python -c "
from src.auth.user_manager import UserManager
um = UserManager()
user = um.get_user('username')
print(f'Rol: {user.get(\"role\") if user else \"Usuario no encontrado\"}')
"
```

**App no carga datos**

```bash
# Verificar estructura de archivos
ls -la data/auth/
```

### Logs de Debug

- Access logs: `data/auth/access_logs.json`
- User stats: `data/auth/user_stats.json`
- App logs: Consola de Streamlit

## 🔄 Mantenimiento

### Backup Regular

```bash
# Crear backup de datos de autenticación
tar -czf backup_auth_$(date +%Y%m%d).tar.gz data/auth/
```

### Limpieza de Logs

Los logs se limpian automáticamente manteniendo los últimos 1000 registros.

### Actualización de Usuarios

```bash
# Regenerar todos los usuarios (⚠️ CUIDADO: Elimina usuarios existentes)
python generate_users.py
```

## 📞 Soporte

### Contacto

Para soporte técnico, proporciona:

- Descripción detallada del problema
- Logs relevantes (`data/auth/access_logs.json`)
- Pasos para reproducir el issue
- Información del entorno (SO, Python, dependencias)

### Contribución

1. Fork del repositorio
2. Crear rama para nueva feature
3. Commit con mensaje descriptivo
4. Pull request con descripción detallada

## 📜 Licencia

© 2025 Scouting Hub - Sistema de Análisis de Baloncesto

---

**¡Disfruta analizando el baloncesto como un profesional! 🏀**
