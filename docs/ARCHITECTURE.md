# 🏗️ Arquitectura del Sistema - Impulso Inversor v2

## Visión General

Impulso Inversor v2 es una aplicación web moderna que utiliza una arquitectura de microservicios con separación completa entre frontend y backend, desplegada en AWS para máxima escalabilidad.

## 🎨 Frontend Architecture (React + TypeScript)

### Tecnologías Principales
- **React 18** con TypeScript para type safety
- **Vite** como bundler y dev server
- **Tailwind CSS** + **shadcn/ui** para estilos
- **React Router v6** para navegación
- **React Query** para state management y cache
- **Chart.js/Recharts** para visualizaciones
- **Axios** para HTTP requests

### Estructura de Carpetas
```
frontend/
├── src/
│   ├── components/          # Componentes reutilizables
│   │   ├── ui/             # Componentes UI base (shadcn)
│   │   ├── forms/          # Componentes de formularios
│   │   ├── charts/         # Componentes de gráficos
│   │   └── layout/         # Componentes de layout
│   ├── pages/              # Páginas de la aplicación
│   │   ├── Dashboard/
│   │   ├── Portfolio/
│   │   ├── Analysis/
│   │   └── Profile/
│   ├── hooks/              # Custom React hooks
│   ├── services/           # API calls y servicios
│   ├── types/              # TypeScript types
│   ├── utils/              # Utilidades y helpers
│   ├── context/            # React Context providers
│   └── constants/          # Constantes de la aplicación
├── public/                 # Assets estáticos
└── tests/                  # Tests unitarios y e2e
```

### Patrones de Diseño
- **Component-based Architecture**: Componentes modulares y reutilizables
- **Custom Hooks**: Lógica reutilizable extraída en hooks personalizados
- **Context + Reducer**: Para estado global de la aplicación
- **Error Boundaries**: Manejo robusto de errores
- **Lazy Loading**: Carga perezosa de componentes para optimización

## 🔧 Backend Architecture (Flask + PostgreSQL)

### Tecnologías Principales
- **Flask** con **Flask-RESTful** para APIs
- **PostgreSQL** como base de datos principal
- **Redis** para caching y sesiones
- **SQLAlchemy** como ORM
- **Marshmallow** para validación y serialización
- **JWT** para autenticación
- **Swagger/OpenAPI** para documentación

### Estructura de Carpetas
```
backend/
├── app/
│   ├── api/                # Endpoints de la API
│   │   ├── portfolios.py   # CRUD portfolios
│   │   ├── analysis.py     # Análisis de perfil
│   │   ├── auth.py         # Autenticación
│   │   └── etfs.py         # Información ETFs
│   ├── models/             # Modelos SQLAlchemy
│   │   ├── user.py
│   │   ├── portfolio.py
│   │   └── risk_profile.py
│   ├── services/           # Lógica de negocio
│   │   ├── portfolio_service.py
│   │   ├── market_data_service.py
│   │   └── risk_analysis_service.py
│   └── utils/              # Utilidades
│       ├── validators.py
│       ├── decorators.py
│       └── helpers.py
├── config/                 # Configuraciones
├── migrations/             # Migraciones DB
└── tests/                  # Tests del backend
```

### Patrones de Diseño
- **Repository Pattern**: Abstracción de acceso a datos
- **Service Layer**: Lógica de negocio separada de controllers
- **Factory Pattern**: Para creación de la aplicación Flask
- **Dependency Injection**: Para servicios y configuraciones
- **Circuit Breaker**: Para llamadas a APIs externas

## 📊 Base de Datos (PostgreSQL)

### Esquema Principal
```sql
-- Usuarios
users (
    id, email, created_at, updated_at
)

-- Perfiles de riesgo
risk_profiles (
    id, user_id, answers, score, bucket, created_at
)

-- Portfolios
portfolios (
    id, user_id, risk_profile_id, allocations, created_at
)

-- Historiales de rebalanceo
rebalancing_history (
    id, portfolio_id, old_allocation, new_allocation, date
)
```

### Estrategia de Cache (Redis)
- **Market Data**: 30 minutos TTL
- **User Sessions**: 24 horas TTL
- **ETF Information**: 1 hora TTL
- **Historical Simulations**: 2 horas TTL

## ☁️ AWS Infrastructure

### Servicios Utilizados
- **S3 + CloudFront**: Hosting frontend estático con CDN global
- **ECS Fargate**: Containers para backend sin gestión de servidores
- **Application Load Balancer**: Distribución de tráfico y terminación SSL
- **RDS PostgreSQL**: Base de datos gestionada con backups automáticos
- **ElastiCache Redis**: Cache en memoria gestionado
- **Route 53**: Gestión DNS
- **ACM**: Certificados SSL/TLS
- **CloudWatch**: Monitoring y logs
- **Systems Manager**: Gestión de secrets y parámetros

### Arquitectura de Red
```
Internet Gateway
    ↓
CloudFront CDN (Frontend)
    ↓
Application Load Balancer
    ↓
ECS Service (Backend) - Multi-AZ
    ↓
RDS PostgreSQL (Multi-AZ)
ElastiCache Redis (Multi-AZ)
```

## 🔐 Seguridad

### Autenticación y Autorización
- **JWT Tokens**: Access tokens (1h) y refresh tokens (30d)
- **Rate Limiting**: Por IP y por usuario
- **CORS**: Configurado para dominios específicos
- **Input Validation**: En frontend y backend

### Protección de Datos
- **HTTPS**: Forzado en todas las conexiones
- **Secrets Management**: AWS Systems Manager Parameter Store
- **Database Encryption**: En reposo y en tránsito
- **PII Protection**: Minimización y anonimización de datos

## 🚀 CI/CD Pipeline

### GitHub Actions Workflow
```yaml
1. Code Push → GitHub
2. Run Tests (Frontend + Backend)
3. Security Scanning (SAST)
4. Build Docker Images
5. Push to ECR
6. Deploy to ECS
7. Update CloudFront Distribution
8. Run E2E Tests
9. Notify Team
```

### Environments
- **Development**: Auto-deploy en push a `develop`
- **Staging**: Auto-deploy en push a `staging`
- **Production**: Manual approval requerida

## 📈 Monitoring y Observabilidad

### Métricas Clave
- **Response Time**: P50, P95, P99
- **Error Rate**: 4xx, 5xx responses
- **Throughput**: Requests per second
- **Database Performance**: Query times, connections
- **Cache Hit Rate**: Redis performance

### Alertas
- **High Error Rate**: > 1%
- **Slow Response Time**: > 2s P95
- **Database Issues**: Connection failures
- **High Memory Usage**: > 80%

## 🔄 Escalabilidad

### Horizontal Scaling
- **Frontend**: CloudFront edge locations globales
- **Backend**: ECS Auto Scaling basado en CPU/memoria
- **Database**: Read replicas para queries
- **Cache**: Redis Cluster para alta disponibilidad

### Optimizaciones
- **Code Splitting**: Carga lazy de componentes React
- **Image Optimization**: WebP, lazy loading
- **Database Indexing**: Queries optimizados
- **API Caching**: Estrategias de cache inteligentes

## 🧪 Testing Strategy

### Frontend Testing
- **Unit Tests**: Jest + React Testing Library
- **Integration Tests**: Testing de flujos completos
- **E2E Tests**: Playwright para scenarios críticos
- **Visual Testing**: Chromatic para componentes UI

### Backend Testing
- **Unit Tests**: pytest para lógica de negocio
- **Integration Tests**: Testing de APIs completas
- **Database Tests**: Testing de modelos y queries
- **Load Testing**: Apache JMeter para performance

Esta arquitectura garantiza escalabilidad, mantenibilidad y alta disponibilidad para Impulso Inversor v2.