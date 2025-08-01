import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

from scoring import score_user, bucket_to_label
from portfolios import MODEL_PORTFOLIOS
from etf_descriptions import ETF_INFO

# Configuración de la página
st.set_page_config(
    page_title="Impulso Inversor", 
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado mejorado
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin: 10px 0;
        color: white;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .etf-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        color: white;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .etf-card:hover {
        transform: translateY(-5px);
    }
    
    .sidebar-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        color: white;
        text-align: center;
    }
    
    .alert-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 12px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    .alert-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 12px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    .alert-danger {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 12px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f0f2f6;
        border-radius: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Función mejorada para obtener datos históricos con manejo de errores
@st.cache_data(ttl=3600)  # Cache por 1 hora
def get_historical_data(tickers, start_date, end_date):
    """Obtiene datos históricos de Yahoo Finance con manejo robusto de errores"""
    data = {}
    failed_tickers = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(tickers):
        try:
            status_text.text(f'Descargando datos para {ticker}...')
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            
            if not hist.empty:
                data[ticker] = hist['Close']
            else:
                failed_tickers.append(ticker)
                st.warning(f"No se encontraron datos para {ticker}")
                
        except Exception as e:
            failed_tickers.append(ticker)
            st.error(f"Error obteniendo datos para {ticker}: {str(e)}")
        
        progress_bar.progress((i + 1) / len(tickers))
    
    progress_bar.empty()
    status_text.empty()
    
    if failed_tickers:
        st.warning(f"No se pudieron obtener datos para: {', '.join(failed_tickers)}")
    
    return pd.DataFrame(data)

# Función para obtener datos de benchmarks
@st.cache_data(ttl=3600)
def get_benchmark_data(start_date, end_date):
    """Obtiene datos de benchmarks para comparación"""
    benchmarks = {
        'SPY': 'S&P 500',
        'VTI': 'Total Stock Market',
        'VXUS': 'International Stocks'
    }
    
    benchmark_data = {}
    
    for ticker, name in benchmarks.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            if not hist.empty:
                benchmark_data[name] = hist['Close']
        except:
            st.warning(f"No se pudo obtener datos del benchmark {name}")
    
    return pd.DataFrame(benchmark_data)

# Función mejorada para simular portafolio
def simulate_portfolio(weights, initial_investment=10000, include_benchmarks=True):
    """Simula el rendimiento histórico de un portafolio con comparación de benchmarks"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*10)  # 10 años atrás
    
    # Obtener datos históricos
    tickers = list(weights.keys())
    
    with st.spinner('📊 Obteniendo datos históricos...'):
        historical_data = get_historical_data(tickers, start_date, end_date)
        
        if include_benchmarks:
            benchmark_data = get_benchmark_data(start_date, end_date)
    
    if historical_data.empty:
        return None, None
    
    # Calcular retornos diarios
    returns = historical_data.pct_change().fillna(0)
    
    # Calcular retorno del portafolio
    portfolio_returns = (returns * list(weights.values())).sum(axis=1)
    
    # Calcular valor acumulado
    cumulative_returns = (1 + portfolio_returns).cumprod()
    portfolio_value = initial_investment * cumulative_returns
    
    benchmark_values = None
    if include_benchmarks and not benchmark_data.empty:
        benchmark_returns = benchmark_data.pct_change().fillna(0)
        benchmark_cumulative = (1 + benchmark_returns).cumprod()
        benchmark_values = initial_investment * benchmark_cumulative
    
    return portfolio_value, benchmark_values

# Función para generar alertas de riesgo
def generate_risk_alerts(portfolio, bucket):
    """Genera alertas personalizadas basadas en el perfil de riesgo"""
    alerts = []
    
    # Calcular concentración en acciones
    equity_weight = portfolio.get('ACWI', 0)
    
    if bucket <= 1 and equity_weight > 0.4:  # Conservador/Moderado
        alerts.append({
            'type': 'warning',
            'message': f'Tu portafolio tiene {equity_weight*100:.0f}% en acciones. Para tu perfil conservador, considera reducir la exposición.'
        })
    
    if bucket >= 3 and equity_weight < 0.5:  # Crecimiento/Agresivo
        alerts.append({
            'type': 'info',
            'message': f'Tu portafolio tiene {equity_weight*100:.0f}% en acciones. Podrías considerar aumentar la exposición para mayor crecimiento.'
        })
    
    # Alertas sobre diversificación
    if len(portfolio) < 3:
        alerts.append({
            'type': 'warning',
            'message': 'Tu portafolio tiene pocos activos. Considera diversificar más para reducir riesgo.'
        })
    
    # Alerta sobre oro
    gold_weight = portfolio.get('GLD', 0)
    if gold_weight > 0.15:
        alerts.append({
            'type': 'info',
            'message': f'Tienes {gold_weight*100:.0f}% en oro. El oro puede ser volátil y no genera ingresos.'
        })
    
    return alerts

# Función para sugerir rebalanceo
def suggest_rebalancing(current_portfolio, target_portfolio):
    """Sugiere ajustes para rebalancear el portafolio"""
    suggestions = []
    
    for ticker in target_portfolio:
        current_weight = current_portfolio.get(ticker, 0)
        target_weight = target_portfolio[ticker]
        difference = abs(current_weight - target_weight)
        
        if difference > 0.05:  # Diferencia mayor al 5%
            if current_weight > target_weight:
                suggestions.append(f"Reducir {ticker} en {difference*100:.1f}%")
            else:
                suggestions.append(f"Aumentar {ticker} en {difference*100:.1f}%")
    
    return suggestions

# Función para crear gráfico de torta
def create_pie_chart(portfolio):
    """Crea un gráfico de torta interactivo para el portafolio"""
    labels = []
    values = []
    colors = []
    
    for ticker, weight in portfolio.items():
        info = ETF_INFO[ticker]
        labels.append(f"{info['nombre']}<br>({ticker})")
        values.append(weight * 100)
        colors.append(info['color'])
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker_colors=colors,
        textinfo='label+percent',
        textposition='outside'
    )])
    
    fig.update_layout(
        title="Composición del Portafolio",
        title_x=0.5,
        font=dict(size=12),
        showlegend=True,
        height=400
    )
    
    return fig

# Función para validar inputs
def validate_user_inputs(answers):
    """Valida que todos los inputs del usuario sean válidos"""
    required_fields = ['age', 'horizon', 'income', 'knowledge', 'max_drop', 
                      'reaction', 'liquidity', 'goal', 'inflation', 'digital']
    
    for field in required_fields:
        if field not in answers or answers[field] is None:
            return False, f"Falta completar el campo: {field}"
    
    if answers['age'] < 18 or answers['age'] > 75:
        return False, "La edad debe estar entre 18 y 75 años"
    
    return True, "Válido"

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("## 🎯 Panel de Control")
    
    if 'profile' in st.session_state:
        profile = st.session_state['profile']
        st.markdown(f"""
        <div class="sidebar-card">
            <h3 style="margin: 0;">Tu Perfil</h3>
            <h2 style="margin: 5px 0;">{profile['label']}</h2>
            <p style="margin: 0;">Nivel de riesgo: {profile['bucket'] + 1}/5</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar alertas en sidebar
        alerts = generate_risk_alerts(profile['portfolio'], profile['bucket'])
        if alerts:
            st.markdown("### ⚠️ Alertas")
            for alert in alerts:
                alert_class = f"alert-{alert['type']}"
                st.markdown(f'<div class="{alert_class}">{alert["message"]}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Simulador de inversión
    st.markdown("### 💰 Simulador de Inversión")
    investment_amount = st.number_input(
        "Monto a invertir ($)",
        min_value=1000,
        max_value=1000000,
        value=10000,
        step=1000
    )
    
    # Configuraciones avanzadas
    with st.expander("⚙️ Configuraciones"):
        show_benchmarks = st.checkbox("Mostrar benchmarks", value=True)
        investment_period = st.selectbox(
            "Período de análisis",
            ["1 año", "3 años", "5 años", "10 años"],
            index=3
        )

# ========== INTERFAZ PRINCIPAL ==========
st.title("💎 Impulso Inversor")
st.subheader("Tu asesor de inversiones inteligente y personalizado")

# Métricas rápidas en la parte superior
if 'profile' in st.session_state:
    col1, col2, col3, col4 = st.columns(4)
    portfolio = st.session_state['profile']['portfolio']
    
    with col1:
        equity_pct = portfolio.get('ACWI', 0) * 100
        st.metric("🏢 Acciones", f"{equity_pct:.0f}%")
    
    with col2:
        bonds_pct = portfolio.get('AGG', 0) * 100
        st.metric("🏛️ Bonos", f"{bonds_pct:.0f}%")
    
    with col3:
        reits_pct = portfolio.get('VNQ', 0) * 100
        st.metric("🏠 REITs", f"{reits_pct:.0f}%")
    
    with col4:
        gold_pct = portfolio.get('GLD', 0) * 100
        st.metric("🥇 Oro", f"{gold_pct:.0f}%")

st.markdown("---")

# Tabs principales
tab1, tab2, tab3, tab4 = st.tabs(["📊 Análisis de Perfil", "📈 Simulación Histórica", "🔄 Rebalanceo", "📚 Información ETFs"])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## 📋 Cuestionario de Perfil de Riesgo")
        
        with st.form("questionnaire"):
            col_q1, col_q2 = st.columns(2)
            
            with col_q1:
                age = st.slider("1️⃣ ¿Cuál es tu edad?", 18, 75, 30)
                horizon = st.selectbox(
                    "2️⃣ Horizonte de inversión",
                    ("< 3 años", "3-5 años", "5-10 años", "> 10 años"),
                )
                income = st.selectbox(
                    "3️⃣ % de ingresos para invertir",
                    ("< 5 %", "5-10 %", "10-20 %", "> 20 %"),
                )
                knowledge = st.selectbox(
                    "4️⃣ Conocimiento financiero",
                    ("Principiante", "Intermedio", "Avanzado"),
                )
                max_drop = st.selectbox(
                    "5️⃣ Caída máxima tolerable",
                    ("5 %", "10 %", "20 %", "30 %", "> 30 %"),
                )
            
            with col_q2:
                reaction = st.selectbox(
                    "6️⃣ Si tu portafolio cae 15%",
                    ("Vendo todo", "Vendo una parte", "No hago nada", "Compro más"),
                )
                liquidity = st.selectbox(
                    "7️⃣ Necesidad de liquidez",
                    ("Alta", "Media", "Baja"),
                )
                goal = st.selectbox(
                    "8️⃣ Objetivo principal",
                    ("Proteger capital", "Ingresos regulares", "Crecimiento balanceado", "Máximo crecimiento"),
                )
                inflation = st.selectbox(
                    "9️⃣ Preocupación por inflación",
                    ("No me preocupa", "Me preocupa moderadamente", "Me preocupa mucho"),
                )
                digital = st.selectbox(
                    "🔟 Confianza en plataformas digitales",
                    ("Baja", "Media", "Alta"),
                )

            submitted = st.form_submit_button("🎯 Calcular mi perfil", use_container_width=True)

    with col2:
        st.markdown("## 🎯 Tu Resultado")
        
        if submitted:
            answers = dict(
                age=age, horizon=horizon, income=income, knowledge=knowledge,
                max_drop=max_drop, reaction=reaction, liquidity=liquidity,
                goal=goal, inflation=inflation, digital=digital
            )
            
            # Validar inputs
            is_valid, validation_message = validate_user_inputs(answers)
            
            if not is_valid:
                st.error(f"Error en los datos: {validation_message}")
            else:
                bucket, total_score = score_user(answers)
                label = bucket_to_label[bucket]
                
                # Mostrar resultado con animación
                st.markdown(f"""
                <div class="metric-card">
                    <h2 style="margin: 0;">Perfil: {label}</h2>
                    <p style="font-size: 1.2rem; margin: 10px 0;">Puntaje: {total_score}/50</p>
                    <p style="margin: 0;">Nivel de riesgo: {bucket + 1}/5</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Guardar en sesión
                st.session_state['profile'] = {
                    'bucket': bucket,
                    'label': label,
                    'portfolio': MODEL_PORTFOLIOS[bucket],
                    'score': total_score
                }
                
                # Mostrar progress bar del nivel de riesgo
                st.progress((bucket + 1) / 5)
                
                time.sleep(0.5)  # Pequeña pausa para efecto
                st.rerun()

    # Mostrar portafolio recomendado
    if 'profile' in st.session_state:
        st.markdown("---")
        st.markdown("## 💼 Tu Portafolio Recomendado")
        
        portfolio = st.session_state['profile']['portfolio']
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Gráfico de torta
            fig = create_pie_chart(portfolio)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 📋 Detalle de ETFs")
            for ticker, weight in portfolio.items():
                info = ETF_INFO[ticker]
                st.markdown(f"""
                <div class="etf-card">
                    <h4 style="margin: 0;">{info['nombre']} ({ticker})</h4>
                    <p style="margin: 5px 0; font-size: 1.2rem; font-weight: bold;">{weight*100:.0f}%</p>
                    <p style="margin: 0; font-size: 0.9rem;">{info['tipo']} - Riesgo {info['riesgo']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Descargar CSV mejorado
        pf_df = pd.DataFrame([
            {
                'ETF': ticker,
                'Nombre': ETF_INFO[ticker]['nombre'],
                'Peso %': weight * 100,
                'Tipo': ETF_INFO[ticker]['tipo'],
                'Riesgo': ETF_INFO[ticker]['riesgo'],
                'Descripción': ETF_INFO[ticker]['descripcion']
            }
            for ticker, weight in portfolio.items()
        ])
        
        csv = pf_df.to_csv(index=False).encode()
        st.download_button(
            "📥 Descargar portafolio detallado (CSV)",
            csv,
            f"impulso_inversor_{st.session_state['profile']['label']}_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            use_container_width=True
        )

with tab2:
    st.markdown("## 📈 Simulación Histórica del Portafolio")
    
    if 'profile' in st.session_state:
        portfolio = st.session_state['profile']['portfolio']
        
        portfolio_value, benchmark_values = simulate_portfolio(
            portfolio, 
            investment_amount, 
            show_benchmarks
        )
        
        if portfolio_value is not None:
            # Calcular métricas
            final_value = portfolio_value.iloc[-1]
            total_return = (final_value / investment_amount - 1) * 100
            years = len(portfolio_value) / 252  # Días de trading por año
            annual_return = (final_value / investment_amount) ** (1/years) - 1
            
            # Mostrar métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "💰 Inversión Inicial",
                    f"${investment_amount:,}"
                )
            
            with col2:
                st.metric(
                    "💎 Valor Final",
                    f"${final_value:,.0f}",
                    delta=f"+${final_value-investment_amount:,.0f}"
                )
            
            with col3:
                st.metric(
                    "📊 Retorno Total",
                    f"{total_return:.1f}%"
                )
            
            with col4:
                st.metric(
                    "📈 Retorno Anual",
                    f"{annual_return*100:.1f}%"
                )
            
            # Gráfico interactivo con benchmarks
            fig = go.Figure()
            
            # Agregar portafolio
            fig.add_trace(go.Scatter(
                x=portfolio_value.index,
                y=portfolio_value.values,
                mode='lines',
                name='Tu Portafolio',
                line=dict(color='#667eea', width=3)
            ))
            
            # Agregar benchmarks si están disponibles
            if show_benchmarks and benchmark_values is not None:
                colors = ['#f093fb', '#4facfe', '#00f2fe']
                for i, (name, values) in enumerate(benchmark_values.items()):
                    if not values.empty:
                        fig.add_trace(go.Scatter(
                            x=values.index,
                            y=values.values,
                            mode='lines',
                            name=name,
                            line=dict(color=colors[i % len(colors)], width=2, dash='dash')
                        ))
            
            fig.update_layout(
                title="Evolución del Portafolio vs Benchmarks",
                xaxis_title="Fecha",
                yaxis_title="Valor del Portafolio ($)",
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Análisis detallado
            st.markdown("### 📊 Análisis de Rendimiento Detallado")
            
            # Calcular estadísticas avanzadas
            daily_returns = portfolio_value.pct_change().dropna()
            volatility = daily_returns.std() * np.sqrt(252) * 100
            sharpe = (annual_return * 100 - 2) / volatility if volatility > 0 else 0
            max_drawdown = ((portfolio_value / portfolio_value.cummax() - 1) * 100).min()
            
            # Calcular VaR (Value at Risk) al 95%
            var_95 = np.percentile(daily_returns, 5) * 100
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📉 Volatilidad Anual", f"{volatility:.1f}%")
            
            with col2:
                color = "normal" if sharpe > 1 else "inverse"
                st.metric("⚡ Ratio Sharpe", f"{sharpe:.2f}", delta_color=color)
            
            with col3:
                st.metric("📉 Máxima Caída", f"{max_drawdown:.1f}%")
            
            with col4:
                st.metric("⚠️ VaR 95%", f"{var_95:.1f}%")
            
            # Comparación con benchmarks
            if show_benchmarks and benchmark_values is not None:
                st.markdown("### 🏆 Comparación con Benchmarks")
                
                comparison_data = []
                
                # Agregar datos del portafolio
                comparison_data.append({
                    'Activo': 'Tu Portafolio',
                    'Retorno Anual': f"{annual_return*100:.2f}%",
                    'Volatilidad': f"{volatility:.2f}%",
                    'Sharpe': f"{sharpe:.2f}",
                    'Máx. Caída': f"{max_drawdown:.2f}%"
                })
                
                # Agregar benchmarks
                for name, values in benchmark_values.items():
                    if not values.empty:
                        bench_returns = values.pct_change().dropna()
                        bench_annual = (values.iloc[-1] / values.iloc[0]) ** (1/years) - 1
                        bench_vol = bench_returns.std() * np.sqrt(252) * 100
                        bench_sharpe = (bench_annual * 100 - 2) / bench_vol if bench_vol > 0 else 0
                        bench_dd = ((values / values.cummax() - 1) * 100).min()
                        
                        comparison_data.append({
                            'Activo': name,
                            'Retorno Anual': f"{bench_annual*100:.2f}%",
                            'Volatilidad': f"{bench_vol:.2f}%",
                            'Sharpe': f"{bench_sharpe:.2f}",
                            'Máx. Caída': f"{bench_dd:.2f}%"
                        })
                
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df, use_container_width=True)
            
            # Tabla de rendimientos anuales
            st.markdown("### 📅 Rendimientos por Año")
            
            yearly_returns = portfolio_value.resample('Y').last().pct_change().dropna() * 100
            yearly_df = pd.DataFrame({
                'Año': yearly_returns.index.year,
                'Rendimiento %': yearly_returns.values.round(2)
            })
            
            # Agregar colores basados en rendimiento
            def color_returns(val):
                color = 'green' if val > 0 else 'red'
                return f'color: {color}'
            
            styled_df = yearly_df.style.applymap(color_returns, subset=['Rendimiento %'])
            st.dataframe(styled_df, use_container_width=True)
        
        else:
            st.error("No se pudieron obtener suficientes datos históricos para la simulación.")
    
    else:
        st.info("👆 Primero completa el cuestionario en la pestaña 'Análisis de Perfil'")

with tab3:
    st.markdown("## 🔄 Rebalanceo del Portafolio")
    
    if 'profile' in st.session_state:
        st.markdown("""
        El rebalanceo es importante para mantener tu portafolio alineado con tu perfil de riesgo.
        Aquí puedes ver si necesitas hacer ajustes.
        """)
        
        portfolio = st.session_state['profile']['portfolio']
        
        # Simulador de portafolio actual vs objetivo
        st.markdown("### 🎯 Estado Actual vs Objetivo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Portafolio Objetivo")
            target_data = []
            for ticker, weight in portfolio.items():
                target_data.append({
                    'ETF': ticker,
                    'Peso Objetivo': f"{weight*100:.1f}%"
                })
            st.dataframe(pd.DataFrame(target_data), use_container_width=True)
        
        with col2:
            st.markdown("#### Simular Portafolio Actual")
            
            current_portfolio = {}
            total_weight = 0
            
            for ticker in portfolio.keys():
                weight = st.slider(
                    f"{ticker} - Peso actual (%)",
                    0.0, 100.0, 
                    portfolio[ticker] * 100,
                    0.5,
                    key=f"current_{ticker}"
                )
                current_portfolio[ticker] = weight / 100
                total_weight += weight
            
            if abs(total_weight - 100) > 0.1:
                st.warning(f"⚠️ Los pesos suman {total_weight:.1f}%. Deben sumar 100%")
            else:
                st.success("✅ Los pesos suman 100%")
        
        # Generar sugerencias de rebalanceo
        if abs(total_weight - 100) <= 0.1:
            suggestions = suggest_rebalancing(current_portfolio, portfolio)
            
            if suggestions:
                st.markdown("### 📋 Sugerencias de Rebalanceo")
                for suggestion in suggestions:
                    st.markdown(f"• {suggestion}")
            else:
                st.success("🎉 Tu portafolio está bien balanceado!")
        
        # Costo estimado de rebalanceo
        st.markdown("### 💰 Estimación de Costos")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            commission_per_trade = st.number_input("Comisión por operación ($)", 0.0, 50.0, 0.0, 0.5)
        
        with col2:
            spread_cost = st.number_input("Costo de spread (%)", 0.0, 1.0, 0.05, 0.01)
        
        with col3:
            portfolio_value_for_rebalance = st.number_input("Valor del portafolio ($)", 1000, 1000000, 50000, 1000)
        
        if suggestions and abs(total_weight - 100) <= 0.1:
            num_trades = len([s for s in suggestions if "Reducir" in s or "Aumentar" in s])
            total_commission = num_trades * commission_per_trade
            total_spread = portfolio_value_for_rebalance * (spread_cost / 100)
            total_cost = total_commission + total_spread
            
            st.metric("💸 Costo Total Estimado", f"${total_cost:.2f}")
            
            if total_cost / portfolio_value_for_rebalance > 0.02:  # Más del 2%
                st.warning("⚠️ El costo de rebalanceo es alto (>2% del portafolio)")
            else:
                st.success("✅ Costo de rebalanceo razonable")
    
    else:
        st.info("👆 Primero completa el cuestionario en la pestaña 'Análisis de Perfil'")

with tab4:
    st.markdown("## 📚 Información Detallada de los ETFs")
    
    # Agregar filtros
    col1, col2 = st.columns([1, 1])
    
    with col1:
        risk_filter = st.selectbox(
            "Filtrar por nivel de riesgo:",
            ["Todos", "Bajo", "Medio", "Medio-Alto", "Alto"]
        )
    
    with col2:
        type_filter = st.selectbox(
            "Filtrar por tipo:",
            ["Todos", "Efectivo/T-Bills", "Bonos", "Acciones", "REITs", "Commodities"]
        )
    
    # Mostrar ETFs filtrados
    for ticker, info in ETF_INFO.items():
        # Aplicar filtros
        if risk_filter != "Todos" and info['riesgo'] != risk_filter:
            continue
        if type_filter != "Todos" and info['tipo'] != type_filter:
            continue
        
        with st.expander(f"{info['nombre']} ({ticker}) - {info['tipo']}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**📝 Descripción:** {info['descripcion']}")
                st.markdown(f"**📊 Tipo de activo:** {info['tipo']}")
                st.markdown(f"**⚠️ Nivel de riesgo:** {info['riesgo']}")
                st.markdown(f"**📈 Rendimiento esperado:** {info['rendimiento_esperado']}")
                
                # Información adicional específica
                if ticker == "AGG":
                    st.markdown(f"**⏱️ Duración:** {info['duración']}")
                    st.markdown(f"**💰 Yield:** {info['yield']}")
                elif ticker == "ACWI":
                    st.markdown(f"**🌍 Cobertura:** {info['países']}, {info['empresas']}")
                elif ticker == "VNQ":
                    st.markdown(f"**💵 Dividend Yield:** {info['dividend_yield']}")
                elif ticker == "GLD":
                    st.markdown(f"**📊 Correlación:** {info['correlación']}")
            
            with col2:
                # Intentar obtener precio actual (con manejo de errores)
                try:
                    stock = yf.Ticker(ticker)
                    current_data = stock.history(period="1d")
                    if not current_data.empty:
                        current_price = current_data['Close'].iloc[-1]
                        prev_close = current_data['Open'].iloc[-1]
                        change = current_price - prev_close
                        change_pct = (change / prev_close) * 100
                        
                        st.metric(
                            f"Precio actual ({ticker})",
                            f"${current_price:.2f}",
                            delta=f"{change:+.2f} ({change_pct:+.2f}%)"
                        )
                    else:
                        st.info("Precio no disponible")
                except:
                    st.info("Precio no disponible")
    
    # Glosario de términos
    st.markdown("---")
    st.markdown("## 📖 Glosario de Términos Financieros")
    
    with st.expander("📚 Ver Glosario Completo"):
        glossary = {
            "ETF": "Exchange Traded Fund - Fondo cotizado que replica un índice",
            "Volatilidad": "Medida de la variabilidad de los precios",
            "Ratio Sharpe": "Medida de rentabilidad ajustada por riesgo",
            "Drawdown": "Pérdida máxima desde un pico hasta un valle",
            "VaR": "Value at Risk - Pérdida máxima esperada con cierta probabilidad",
            "Diversificación": "Distribuir inversiones para reducir riesgo",
            "Rebalanceo": "Ajustar pesos para mantener la asignación objetivo",
            "Benchmark": "Índice de referencia para comparar rendimiento",
            "Yield": "Rendimiento por dividendos o intereses",
            "Duration": "Sensibilidad de bonos a cambios en tasas de interés"
        }
        
        for term, definition in glossary.items():
            st.markdown(f"**{term}:** {definition}")

# Footer mejorado
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white; margin: 20px 0;">
    <h3>⚠️ Disclaimer Importante</h3>
    <p>Esta herramienta tiene fines <strong>educativos e informativos únicamente</strong>. 
    No constituye asesoramiento financiero personalizado.</p>
    <p>Los rendimientos pasados no garantizan resultados futuros. 
    <strong>Consulta con un asesor financiero profesional</strong> antes de tomar decisiones de inversión.</p>
    <p style="margin-top: 15px; font-size: 0.9rem;">
        💎 Impulso Inversor - Desarrollado con ❤️ usando Streamlit
    </p>
</div>
""", unsafe_allow_html=True)