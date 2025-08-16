# Guía de Despliegue - Impulso Inversor

Esta guía te ayudará a desplegar tu aplicación Flask en Render (backend) y React en Vercel (frontend).

## 📋 Prerrequisitos

- Cuenta en GitHub, Render y Vercel
- Python 3.10+ y Node 18+ instalados localmente
- Código subido a repositorios de GitHub

## 🚀 1. Despliegue del Backend (Flask) en Render

### 1.1 Preparación del repositorio

Asegúrate de que tu repositorio backend tenga estos archivos:

```
backend/
├── Procfile
├── requirements-prod.txt
├── .env.example
├── run.py
└── ... (resto de archivos)
```

### 1.2 Configuración en Render

1. **Crear Web Service**:
   - Ve a [Render](https://render.com) → New → Web Service
   - Conecta tu repositorio de GitHub
   - Selecciona la carpeta `backend/` si es un monorepo

2. **Configuración del servicio**:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements-prod.txt`
   - **Start Command**: `gunicorn -w 2 -k gthread -b 0.0.0.0:$PORT run:app`
   - **Root Directory**: `backend` (si usas monorepo)

3. **Variables de entorno**:
   ```
   FLASK_ENV=production
   SECRET_KEY=tu-clave-secreta-super-segura
   JWT_SECRET_KEY=tu-jwt-secret-key-aqui
   DEBUG=False
   PYTHONUNBUFFERED=1
   DATABASE_URL=postgresql://... (Render PostgreSQL)
   REDIS_URL=redis://... (Render Redis)
   CORS_ORIGINS=https://tu-frontend.vercel.app
   ```

4. **Bases de datos** (opcional):
   - PostgreSQL: New → PostgreSQL → conectar a tu web service
   - Redis: New → Redis → conectar a tu web service

### 1.3 Verificación

Una vez desplegado, tu API estará disponible en:
`https://tu-api.onrender.com`

Prueba el endpoint de salud: `GET https://tu-api.onrender.com/api/auth/profile`

## 🌐 2. Despliegue del Frontend (React) en Vercel

### 2.1 Preparación del repositorio

Asegúrate de que tu repositorio frontend tenga:

```
frontend/
├── vercel.json
├── .env.example
├── package.json
├── vite.config.ts
└── ... (resto de archivos)
```

### 2.2 Configuración en Vercel

1. **Crear proyecto**:
   - Ve a [Vercel](https://vercel.com) → Add New → Project
   - Conecta tu repositorio de GitHub
   - Selecciona la carpeta `frontend/` si es un monorepo

2. **Configuración automática**:
   - Vercel detecta automáticamente Vite/React
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

3. **Variables de entorno**:
   
   En Project Settings → Environment Variables, añade:
   ```
   VITE_API_BASE_URL=https://tu-api.onrender.com
   NODE_ENV=production
   ```

### 2.3 Configuración de proxy (Recomendado)

El archivo `vercel.json` ya configurado redirige las llamadas `/api/*` a tu backend de Render:

```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://tu-api.onrender.com/api/$1"
    }
  ]
}
```

**¡Importante!** Actualiza la URL en `vercel.json` con tu dominio real de Render.

### 2.4 Verificación

Tu frontend estará disponible en:
`https://tu-proyecto.vercel.app`

## 🔧 3. Configuración final

### 3.1 Actualizar CORS en el backend

Una vez tengas tu dominio de Vercel, actualiza la variable de entorno en Render:

```
CORS_ORIGINS=https://tu-proyecto.vercel.app
```

### 3.2 Actualizar vercel.json

Reemplaza `tu-api.onrender.com` con tu URL real de Render:

```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://TU-API-REAL.onrender.com/api/$1"
    }
  ]
}
```

### 3.3 Test completo

1. Ve a tu frontend: `https://tu-proyecto.vercel.app`
2. Prueba el login/registro
3. Verifica que las llamadas a la API funcionen
4. Revisa los logs en Render si hay errores

## 🐛 4. Resolución de problemas

### Backend no responde
- Verifica las variables de entorno en Render
- Revisa los logs en Render Dashboard
- Asegúrate de que `Procfile` esté configurado correctamente

### CORS errors
- Verifica que `CORS_ORIGINS` incluya tu dominio de Vercel
- Asegúrate de que no haya espacios extra en las URLs

### 502/503 errors
- Render puede tardar en iniciar (cold start)
- Verifica que el comando de inicio sea correcto
- Revisa que todas las dependencias estén en `requirements-prod.txt`

### Frontend no conecta con API
- Verifica que `VITE_API_BASE_URL` sea correcta
- Confirma que `vercel.json` tenga la URL correcta de Render
- Usa DevTools del navegador para ver errores de red

## 📝 5. Comandos útiles

### Desarrollo local
```bash
# Backend
cd backend
pip install -r requirements.txt
python run.py

# Frontend  
cd frontend
npm install
npm run dev
```

### Deploy manual
```bash
# Render (automático con git push)
git push origin main

# Vercel CLI
npx vercel --prod
```

## 🔒 6. Seguridad

- Nunca commites archivos `.env` reales
- Usa claves secretas fuertes y únicas
- Configura CORS solo para tu dominio en producción
- Considera usar HTTPS únicamente

---

¡Tu aplicación ya está lista para producción! 🎉