# 🚀 Setup Local - Impulso Inversor v2

Esta guía te ayudará a configurar la aplicación localmente para desarrollo y testing.

## 📋 Prerrequisitos

### Software Requerido

- **Node.js 20+** (recomendado) o 18+
- **Python 3.9+**
- **PostgreSQL 13+** (opcional, puede usar SQLite para desarrollo)
- **Redis 6+** (opcional, usará cache en memoria si no está disponible)
- **Git**

### Verificar Versiones
```bash
node --version    # v20.x.x recomendado
npm --version     # v10.x.x
python3 --version # v3.9+
git --version     # cualquier versión reciente
```

## 🛠️ Instalación

### 1. Clonar el Repositorio
```bash
git clone https://github.com/Gonzalodlm/proyecto-L-v2.git
cd proyecto-L-v2
```

### 2. Setup Backend (Flask)

```bash
cd backend

# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# En Linux/Mac:
source venv/bin/activate
# En Windows:
# venv\\Scripts\\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones
```

#### Configuración `.env` del Backend
```bash
# Flask Environment
FLASK_ENV=development
FLASK_APP=run.py

# Security
SECRET_KEY=tu-clave-secreta-aqui
JWT_SECRET_KEY=tu-clave-jwt-aqui

# Database (opcional - usará SQLite si no se configura)
DATABASE_URL=postgresql://usuario:password@localhost/impulso_inversor

# Redis (opcional - usará cache en memoria si no está disponible)
REDIS_URL=redis://localhost:6379/0

# API Configuration
PORT=5000
LOG_LEVEL=INFO
```

#### Inicializar Base de Datos
```bash
# Crear tablas (solo primera vez)
python init_db.py
```

### 3. Setup Frontend (React)

```bash
cd ../frontend

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env
# Editar .env si es necesario
```

#### Configuración `.env` del Frontend
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:5000

# App Configuration  
VITE_APP_NAME="Impulso Inversor"
VITE_APP_VERSION="2.0.0"

# Environment
VITE_NODE_ENV=development
```

## 🚀 Ejecutar la Aplicación

### Opción 1: Manual (Recomendado para desarrollo)

#### Terminal 1 - Backend
```bash
cd backend
source venv/bin/activate  # Activar entorno virtual
python run.py
```
El backend estará disponible en: http://localhost:5000

#### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```
El frontend estará disponible en: http://localhost:5173

### Opción 2: Scripts de Desarrollo

```bash
# Desde la raíz del proyecto
npm run dev:all    # Ejecuta ambos servicios
npm run dev:backend
npm run dev:frontend
```

## 🧪 Testing

### Verificar Backend
```bash
cd backend
curl http://localhost:5000/health
# Respuesta esperada: {"status": "healthy", "service": "impulso-inversor-backend"}
```

### Verificar APIs
```bash
# Obtener ETFs
curl http://localhost:5000/api/etfs

# Obtener estructura del cuestionario
curl http://localhost:5000/api/analysis/questionnaire/structure
```

### Verificar Frontend
```bash
cd frontend
npm run build    # Debe compilar sin errores
npm run preview  # Servir build de producción
```

## 🎯 Flujo de Testing Manual

1. **Acceder**: http://localhost:5173
2. **Registro**: Crear cuenta nueva
3. **Login**: Iniciar sesión
4. **Dashboard**: Ver pantalla principal
5. **Risk Assessment**: Completar cuestionario (10 preguntas)
6. **Resultados**: Ver perfil de riesgo y portfolio recomendado

### Cuentas de Prueba
- **Email**: demo@impulso.com
- **Password**: Demo123!

## 🐛 Troubleshooting

### Problemas Comunes

#### Backend no inicia
```bash
# Verificar que el entorno virtual esté activado
which python  # Debe mostrar ruta en /venv/

# Reinstalar dependencias
pip install -r requirements.txt

# Verificar puertos
lsof -i :5000  # Ver si el puerto está ocupado
```

#### Frontend no compila
```bash
# Verificar versión de Node.js
node --version  # Debe ser 18+ (20+ recomendado)

# Limpiar cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# Verificar tipos TypeScript
npm run type-check
```

#### Error de CORS
- Verificar que `VITE_API_BASE_URL` apunte al backend correcto
- Backend debe estar corriendo en puerto 5000
- CORS está configurado para localhost:5173 y localhost:3000

#### Error de Base de Datos
```bash
# Si usas PostgreSQL, crear base de datos
createdb impulso_inversor

# Si no, el sistema usará SQLite automáticamente
# Las tablas se crean automáticamente con init_db.py
```

### Logs de Debug

#### Backend
```bash
# Logs en consola con nivel DEBUG
export LOG_LEVEL=DEBUG
python run.py
```

#### Frontend
```bash
# Abrir Developer Tools en el navegador
# Console: errores de JavaScript
# Network: llamadas a API
# Application: tokens y localStorage
```

## 🏗️ Estructura del Proyecto

```
proyecto-L-v2/
├── backend/           # Flask API server
│   ├── app/          # Código principal
│   │   ├── api/      # Endpoints REST
│   │   ├── models/   # Modelos SQLAlchemy
│   │   └── services/ # Lógica de negocio
│   ├── config/       # Configuraciones
│   └── run.py        # Punto de entrada
├── frontend/         # React TypeScript app
│   ├── src/
│   │   ├── components/  # Componentes UI
│   │   ├── pages/      # Páginas principales
│   │   ├── services/   # API client
│   │   ├── types/      # Tipos TypeScript
│   │   └── context/    # Estado global
│   └── public/        # Assets estáticos
├── docs/             # Documentación
└── legacy/           # Código Streamlit original
```

## 📚 Documentación Adicional

- [Arquitectura del Sistema](./ARCHITECTURE.md)
- [API Documentation](http://localhost:5000/apidocs) (cuando backend esté corriendo)
- [Despliegue AWS](./AWS_DEPLOYMENT.md) (por crear)

## 💬 Soporte

Si encuentras problemas:

1. Revisa esta documentación
2. Verifica logs en backend y frontend
3. Abre un issue en GitHub con detalles del error
4. Incluye versiones de software y sistema operativo

¡La aplicación está lista para desarrollo! 🎉