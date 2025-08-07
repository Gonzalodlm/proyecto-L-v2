# 🚀 Impulso Inversor v2 - React + Flask + AWS

**Tu asesor de inversiones inteligente y personalizado - Versión Web Completa**

Impulso Inversor v2 es una aplicación web moderna desarrollada con React (frontend) y Flask (backend), diseñada para crear portafolios de inversión personalizados basados en perfiles de riesgo, con simulaciones históricas y análisis detallado. Desplegada en AWS para máxima escalabilidad y confiabilidad.

## 🏗️ Arquitectura

```
proyecto-L-v2/
├── frontend/          # React.js aplicación
├── backend/           # Flask API server
├── deployment/        # Configuración AWS (CloudFormation, Terraform)
├── docs/             # Documentación del proyecto
└── legacy/           # Código Streamlit original (referencia)
```

### 🎨 Frontend (React)
- **Framework**: React 18 con TypeScript
- **Estado**: Context API + useReducer
- **Routing**: React Router v6
- **Estilos**: Tailwind CSS + shadcn/ui
- **Gráficos**: Chart.js / Recharts
- **HTTP Client**: Axios
- **Build**: Vite

### 🔧 Backend (Flask)
- **Framework**: Flask con Flask-RESTful
- **Base de Datos**: PostgreSQL (AWS RDS)
- **Cache**: Redis (AWS ElastiCache)
- **Validación**: Marshmallow
- **Autenticación**: JWT
- **Documentación API**: Swagger/OpenAPI

### ☁️ AWS Infrastructure
- **Frontend**: S3 + CloudFront CDN
- **Backend**: ECS (Elastic Container Service)
- **Load Balancer**: Application Load Balancer
- **Database**: RDS PostgreSQL
- **Cache**: ElastiCache Redis
- **DNS**: Route 53
- **SSL**: AWS Certificate Manager
- **Monitoring**: CloudWatch

## 🚀 Características

- ✅ **Análisis de Perfil de Riesgo**: Cuestionario avanzado para determinar tolerancia al riesgo
- 📊 **Portafolios Personalizados**: 5 modelos de portafolio desde conservador hasta agresivo
- 📈 **Simulación Histórica**: Rendimiento histórico con datos reales de mercado
- 🎯 **Comparación con Benchmarks**: Análisis vs S&P 500 y mercado global
- 💰 **Calculadoras Financieras**: Jubilación, casa, educación, emergencia
- 🔄 **Rebalanceo Inteligente**: Sugerencias automáticas de optimización
- 📚 **Centro de Educación**: Información detallada sobre ETFs e inversiones
- 🚨 **Alertas Personalizadas**: Notificaciones basadas en perfil de riesgo
- 📱 **Responsive Design**: Optimizado para móvil, tablet y desktop
- 🔒 **Seguridad**: Autenticación JWT, validación de datos, HTTPS

## 📋 ETFs Incluidos

- **BIL**: SPDR Bloomberg 1-3 Month T-Bill ETF (Efectivo/T-Bills)
- **AGG**: iShares Core U.S. Aggregate Bond ETF (Bonos)
- **ACWI**: iShares MSCI ACWI ETF (Acciones Globales)
- **VNQ**: Vanguard Real Estate ETF (REITs)
- **GLD**: SPDR Gold Shares (Oro)

## 🛠️ Desarrollo Local

### Prerrequisitos
- Node.js 18+ y npm
- Python 3.9+
- PostgreSQL 13+
- Redis 6+

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\\Scripts\\activate  # Windows
pip install -r requirements.txt
flask run
```

## 🚀 Despliegue en AWS

### Usando Terraform
```bash
cd deployment/terraform
terraform init
terraform plan
terraform apply
```

### Usando CloudFormation
```bash
cd deployment/cloudformation
aws cloudformation deploy --template-file infrastructure.yaml --stack-name impulso-inversor-v2
```

## 📊 Modelos de Portafolio

1. **Conservador**: Preservación de capital (30% efectivo, 50% bonos)
2. **Moderado**: Balance seguridad-crecimiento (35% bonos, 30% acciones)
3. **Balanceado**: Distribución equilibrada (25% bonos, 45% acciones)
4. **Crecimiento**: Enfoque largo plazo (15% bonos, 65% acciones)
5. **Agresivo**: Máximo potencial (80% acciones, 15% REITs)

## 🔄 CI/CD Pipeline

- **GitHub Actions**: Integración y despliegue continuo
- **Testing**: Jest (frontend), pytest (backend)
- **Code Quality**: ESLint, Prettier, Black, Flake8
- **Security**: Dependabot, SAST scanning
- **Deployment**: Automatizado a AWS

## 📈 Performance

- **Frontend**: Lighthouse Score 95+
- **Backend**: Sub-200ms response times
- **Availability**: 99.9% uptime SLA
- **Scalability**: Auto-scaling basado en demanda

## 🔒 Seguridad

- HTTPS en todas las conexiones
- Validación de entrada en frontend y backend
- Rate limiting en API endpoints
- Secrets management con AWS Systems Manager
- Regular security updates

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## ⚠️ Disclaimer

Esta aplicación tiene fines **educativos e informativos únicamente**. No constituye asesoramiento financiero personalizado. Los rendimientos pasados no garantizan resultados futuros.

**Consulta siempre con un asesor financiero profesional antes de tomar decisiones de inversión.**

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 📞 Contacto

**Gonzalo** - [@Gonzalodlm](https://github.com/Gonzalodlm)

**Proyecto**: [https://github.com/Gonzalodlm/proyecto-L-v2](https://github.com/Gonzalodlm/proyecto-L-v2)

---

### 🏗️ Estado del Proyecto

- [x] Análisis y diseño de arquitectura
- [ ] Setup inicial React frontend
- [ ] Desarrollo Flask backend API
- [ ] Integración con PostgreSQL y Redis
- [ ] Configuración AWS infrastructure
- [ ] CI/CD pipeline
- [ ] Testing y optimización
- [ ] Documentación completa
- [ ] Deploy a producción