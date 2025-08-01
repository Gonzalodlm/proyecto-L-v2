# 💎 Impulso Inversor

**Tu asesor de inversiones inteligente y personalizado**

Impulso Inversor es una aplicación web desarrollada con Streamlit que te ayuda a crear portafolios de inversión personalizados basados en tu perfil de riesgo, con simulaciones históricas y análisis detallado.

## 🚀 Características

- ✅ **Análisis de Perfil de Riesgo**: Cuestionario completo para determinar tu tolerancia al riesgo
- 📊 **Portafolios Personalizados**: 5 modelos de portafolio desde conservador hasta agresivo
- 📈 **Simulación Histórica**: Rendimiento histórico de tu portafolio con datos reales
- 🎯 **Comparación con Benchmarks**: Compara tu portafolio con S&P 500 y mercado global
- 💰 **Simulador de Inversión**: Prueba diferentes montos de inversión
- 🔄 **Rebalanceo Automático**: Sugerencias para mantener tu portafolio optimizado
- 📚 **Base de Conocimiento**: Información detallada sobre ETFs y términos financieros
- ⚠️ **Alertas de Riesgo**: Notificaciones personalizadas sobre tu portafolio

## 📋 Requisitos

- Python 3.8 o superior
- Conexión a internet (para obtener datos financieros)

## 🛠️ Instalación

1. **Clona el repositorio:**
   ```bash
   git clone https://github.com/Gonzalodlm/proyecto-l-claude.git
   cd proyecto-l-claude
   ```

2. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecuta la aplicación:**
   ```bash
   streamlit run app.py
   ```

4. **Abre tu navegador** en `http://localhost:8501`

## 📁 Estructura del Proyecto

```
impulso-inversor/
├── app.py                 # Aplicación principal de Streamlit
├── scoring.py             # Lógica de puntuación de perfil de riesgo
├── portfolios.py          # Definición de modelos de portafolio
├── etf_descriptions.py    # Información detallada de ETFs
├── requirements.txt       # Dependencias de Python
├── tests/                 # Tests unitarios
└── README.md             # Este archivo
```

## 💼 ETFs Incluidos

La aplicación trabaja con los siguientes ETFs:

- **BIL**: SPDR Bloomberg 1-3 Month T-Bill ETF (Efectivo/T-Bills)
- **AGG**: iShares Core U.S. Aggregate Bond ETF (Bonos)
- **ACWI**: iShares MSCI ACWI ETF (Acciones Globales)
- **VNQ**: Vanguard Real Estate ETF (REITs)
- **GLD**: SPDR Gold Shares (Oro)

## 🎯 Modelos de Portafolio

1. **Conservador**: Prioriza preservación de capital (30% efectivo, 50% bonos)
2. **Moderado**: Balance entre seguridad y crecimiento
3. **Balanceado**: Distribución equilibrada entre activos
4. **Crecimiento**: Enfoque en crecimiento a largo plazo
5. **Agresivo**: Máximo potencial de crecimiento (80% acciones)

## 📊 Cómo Usar

1. **Completa el cuestionario** de perfil de riesgo
2. **Revisa tu portafolio** personalizado recomendado
3. **Analiza la simulación histórica** para entender el rendimiento pasado
4. **Explora los ETFs** para conocer cada inversión
5. **Descarga tu portafolio** en formato CSV

## ⚠️ Disclaimer Importante

Esta herramienta tiene fines **educativos e informativos únicamente**. No constituye asesoramiento financiero personalizado. Los rendimientos pasados no garantizan resultados futuros. 

**Siempre consulta con un asesor financiero profesional antes de tomar decisiones de inversión.**

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Contacto

**Gonzalo** - [@Gonzalodlm](https://github.com/Gonzalodlm)

**Link del Proyecto**: [https://github.com/Gonzalodlm/proyecto-l-claude](https://github.com/Gonzalodlm/proyecto-l-claude)