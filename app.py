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

# ========== FUNCIONES DE CALCULADORA FINANCIERA ==========

def calculate_retirement_goal(current_age, retirement_age, current_savings, monthly_expenses, inflation_rate=0.03):
    """Calcula cuánto necesitas para jubilarte"""
    years_to_retirement = retirement_age - current_age
    years_in_retirement = 25  # Promedio de años después de jubilarse
    
    # Gastos ajustados por inflación en el momento de jubilación
    future_monthly_expenses = monthly_expenses * (1 + inflation_rate) ** years_to_retirement
    annual_expenses_retirement = future_monthly_expenses * 12
    
    # Regla del 4%: necesitas 25 veces tus gastos anuales
    total_needed = annual_expenses_retirement * 25
    
    # Valor futuro de ahorros actuales
    future_value_current_savings = current_savings * (1 + inflation_rate) ** years_to_retirement
    
    # Cuánto falta ahorrar
    additional_needed = max(0, total_needed - future_value_current_savings)
    
    return {
        'total_needed': total_needed,
        'current_savings_future_value': future_value_current_savings,
        'additional_needed': additional_needed,
        'monthly_expenses_at_retirement': future_monthly_expenses,
        'years_to_retirement': years_to_retirement
    }

def calculate_monthly_investment_needed(target_amount, years, expected_return=0.07):
    """Calcula cuánto invertir mensualmente para alcanzar una meta"""
    if years <= 0:
        return target_amount
    
    months = years * 12
    monthly_rate = expected_return / 12
    
    if monthly_rate == 0:
        return target_amount / months
    
    # Fórmula de anualidad ordinaria
    monthly_payment = target_amount * monthly_rate / ((1 + monthly_rate) ** months - 1)
    return monthly_payment

def calculate_house_down_payment(house_price, down_payment_pct=0.20, years_to_buy=5, expected_return=0.07):
    """Calcula cuánto ahorrar para el enganche de una casa"""
    down_payment_needed = house_price * down_payment_pct
    monthly_needed = calculate_monthly_investment_needed(down_payment_needed, years_to_buy, expected_return)
    
    closing_costs = house_price * 0.03  # 3% costos de cierre típicos
    total_upfront = down_payment_needed + closing_costs
    monthly_total = calculate_monthly_investment_needed(total_upfront, years_to_buy, expected_return)
    
    return {
        'house_price': house_price,
        'down_payment_needed': down_payment_needed,
        'closing_costs': closing_costs,
        'total_upfront': total_upfront,
        'monthly_for_down_payment': monthly_needed,
        'monthly_total': monthly_total,
        'years_to_save': years_to_buy
    }

def calculate_education_fund(child_age, college_cost_today=50000, years_of_college=4, inflation_rate=0.05, expected_return=0.07):
    """Calcula cuánto ahorrar para la universidad"""
    years_until_college = max(0, 18 - child_age)
    
    # Costo futuro de la universidad ajustado por inflación
    future_annual_cost = college_cost_today * (1 + inflation_rate) ** years_until_college
    total_college_cost = future_annual_cost * years_of_college
    
    if years_until_college <= 0:
        return {
            'total_needed': total_college_cost,
            'monthly_needed': total_college_cost / 12,
            'years_to_save': 1,
            'future_annual_cost': future_annual_cost
        }
    
    monthly_needed = calculate_monthly_investment_needed(total_college_cost, years_until_college, expected_return)
    
    return {
        'total_needed': total_college_cost,
        'monthly_needed': monthly_needed,
        'years_to_save': years_until_college,
        'future_annual_cost': future_annual_cost
    }

def calculate_emergency_fund(monthly_expenses, months_coverage=6):
    """Calcula el fondo de emergencia necesario"""
    emergency_fund_target = monthly_expenses * months_coverage
    
    # Tiempo recomendado para construir el fondo: 2 años
    years_to_build = 2
    monthly_savings_needed = emergency_fund_target / (years_to_build * 12)
    
    return {
        'target_amount': emergency_fund_target,
        'monthly_savings_needed': monthly_savings_needed,
        'months_coverage': months_coverage,
        'years_to_build': years_to_build
    }

def calculate_portfolio_projection(initial_amount, monthly_contribution, years, expected_return):
    """Proyecta el crecimiento del portafolio"""
    months = years * 12
    monthly_rate = expected_return / 12
    
    # Valor futuro del monto inicial
    future_value_initial = initial_amount * (1 + monthly_rate) ** months
    
    # Valor futuro de contribuciones mensuales
    if monthly_rate == 0:
        future_value_contributions = monthly_contribution * months
    else:
        future_value_contributions = monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)
    
    total_future_value = future_value_initial + future_value_contributions
    total_contributions = initial_amount + (monthly_contribution * months)
    total_interest = total_future_value - total_contributions
    
    return {
        'future_value': total_future_value,
        'total_contributions': total_contributions,
        'total_interest': total_interest,
        'initial_amount': initial_amount,
        'monthly_contribution': monthly_contribution,
        'years': years
    }

# Configuración de la página
st.set_page_config(
    page_title="Impulso Inversor", 
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS estilo AmberLatam - Diseño minimalista y moderno
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;600;700;800;900&display=swap');
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
        font-family: 'Inter', sans-serif;
    }
    
    /* Variables CSS */
    :root {
        --primary-orange: rgb(252, 117, 2);
        --primary-blue: rgb(0, 109, 210);
        --accent-green: rgb(105, 188, 116);
        --accent-pink: rgb(204, 138, 196);
        --neutral-dark: rgb(94, 94, 94);
        --neutral-light: rgb(250, 250, 250);
        --neutral-border: rgb(238, 238, 238);
        --white: #ffffff;
        --text-primary: #1a1a1a;
        --text-secondary: #5e5e5e;
    }
    
    /* Tipografía global */
    .main {
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
        line-height: 1.6;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }
    
    /* Header principal */
    .main-header {
        text-align: center;
        margin-bottom: 3rem;
        padding: 2rem 0;
        border-bottom: 1px solid var(--neutral-border);
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 1rem;
        background: linear-gradient(135deg, var(--primary-orange) 0%, var(--primary-blue) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .main-subtitle {
        font-size: 1.25rem;
        font-weight: 400;
        color: var(--text-secondary);
        margin-bottom: 0;
    }
    
    /* Cards estilo AmberLatam */
    .amber-card {
        background: var(--white);
        border: 1px solid var(--neutral-border);
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        transition: all 0.3s ease;
    }
    
    .amber-card:hover {
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    .metric-card {
        background: var(--white);
        border: 1px solid var(--neutral-border);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        border-color: var(--primary-orange);
        box-shadow: 0 4px 16px rgba(252, 117, 2, 0.1);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-orange);
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* ETF Cards */
    .etf-card {
        background: var(--white);
        border: 1px solid var(--neutral-border);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .etf-card:hover {
        border-color: var(--primary-blue);
        box-shadow: 0 4px 16px rgba(0, 109, 210, 0.1);
    }
    
    .etf-name {
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }
    
    .etf-weight {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--primary-orange);
        margin: 0.5rem 0;
    }
    
    .etf-details {
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin: 0;
    }
    
    /* Sidebar */
    .sidebar-card {
        background: var(--white);
        border: 1px solid var(--neutral-border);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        text-align: center;
    }
    
    .sidebar-title {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    
    .sidebar-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--primary-orange);
        margin-bottom: 0.25rem;
    }
    
    .sidebar-level {
        font-size: 0.875rem;
        color: var(--text-secondary);
    }
    
    /* Alerts estilo AmberLatam */
    .alert-success {
        background-color: rgba(105, 188, 116, 0.1);
        border: 1px solid var(--accent-green);
        color: #2d5016;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-size: 0.875rem;
    }
    
    .alert-warning {
        background-color: rgba(252, 117, 2, 0.1);
        border: 1px solid var(--primary-orange);
        color: #8b4513;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-size: 0.875rem;
    }
    
    .alert-info {
        background-color: rgba(0, 109, 210, 0.1);
        border: 1px solid var(--primary-blue);
        color: #1e40af;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-size: 0.875rem;
    }
    
    /* Tabs estilo AmberLatam */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background-color: var(--neutral-light);
        border-radius: 8px;
        padding: 4px;
        margin-bottom: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        padding: 0 1.5rem;
        background-color: transparent;
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        color: var(--text-secondary);
        border: none;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: var(--white);
        color: var(--text-primary);
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: var(--white);
        color: var(--primary-orange);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
    }
    
    /* Botones */
    .stButton > button {
        background: var(--primary-orange);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: 0.875rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: #e6730a;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(252, 117, 2, 0.3);
    }
    
    /* Inputs y selectbox */
    .stSelectbox > div > div {
        border: 1px solid var(--neutral-border);
        border-radius: 8px;
        font-family: 'Inter', sans-serif;
    }
    
    .stSlider > div > div > div {
        color: var(--primary-orange);
    }
    
    /* Métricas principales */
    .main-metrics {
        display: flex;
        justify-content: space-between;
        margin: 2rem 0;
        gap: 1rem;
    }
    
    .main-metric {
        flex: 1;
        text-align: center;
        padding: 1.5rem;
        background: var(--white);
        border: 1px solid var(--neutral-border);
        border-radius: 12px;
        transition: all 0.3s ease;
    }
    
    .main-metric:hover {
        border-color: var(--primary-orange);
        box-shadow: 0 4px 16px rgba(252, 117, 2, 0.1);
    }
    
    /* Footer */
    .amber-footer {
        background: var(--neutral-light);
        border: 1px solid var(--neutral-border);
        border-radius: 12px;
        padding: 2rem;
        margin: 3rem 0 1rem 0;
        text-align: center;
    }
    
    .amber-footer h3 {
        color: var(--text-primary);
        margin-bottom: 1rem;
    }
    
    .amber-footer p {
        color: var(--text-secondary);
        font-size: 0.875rem;
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    
    /* Responsivo */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2rem;
        }
        
        .main-metrics {
            flex-direction: column;
        }
        
        .amber-card {
            padding: 1.5rem;
        }
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
    st.markdown("## ● Panel de Control")
    
    if 'profile' in st.session_state:
        profile = st.session_state['profile']
        st.markdown(f"""
        <div class="sidebar-card">
            <div class="sidebar-title">Tu Perfil de Inversión</div>
            <div class="sidebar-value">{profile['label']}</div>
            <div class="sidebar-level">Nivel de riesgo: {profile['bucket'] + 1}/5</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar alertas en sidebar
        alerts = generate_risk_alerts(profile['portfolio'], profile['bucket'])
        if alerts:
            st.markdown("### ◆ Alertas")
            for alert in alerts:
                alert_type = alert['type']
                if alert_type == 'warning':
                    alert_class = "alert-warning"
                elif alert_type == 'info':
                    alert_class = "alert-info"
                else:
                    alert_class = "alert-success"
                st.markdown(f'<div class="{alert_class}">{alert["message"]}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Simulador de inversión
    st.markdown("### $ Simulador de Inversión")
    investment_amount = st.number_input(
        "Monto a invertir ($)",
        min_value=1000,
        max_value=1000000,
        value=10000,
        step=1000
    )
    
    # Configuraciones avanzadas
    with st.expander("··· Configuraciones"):
        show_benchmarks = st.checkbox("Mostrar benchmarks", value=True)
        investment_period = st.selectbox(
            "Período de análisis",
            ["1 año", "3 años", "5 años", "10 años"],
            index=3
        )

# ========== INTERFAZ PRINCIPAL ==========
# Header con logo
col1, col2 = st.columns([1, 4])
with col1:
    st.image("logo.svg", width=120)
with col2:
    st.markdown("""
    <div class="main-header">
        <h1 class="main-title">Impulso Inversor</h1>
        <p class="main-subtitle">Tu asesor de inversiones inteligente y personalizado</p>
    </div>
    """, unsafe_allow_html=True)

# Métricas rápidas en la parte superior
if 'profile' in st.session_state:
    col1, col2, col3, col4 = st.columns(4)
    portfolio = st.session_state['profile']['portfolio']
    
    with col1:
        equity_pct = portfolio.get('ACWI', 0) * 100
        st.metric("▦ Acciones", f"{equity_pct:.0f}%")
    
    with col2:
        bonds_pct = portfolio.get('AGG', 0) * 100
        st.metric("▪ Bonos", f"{bonds_pct:.0f}%")
    
    with col3:
        reits_pct = portfolio.get('VNQ', 0) * 100
        st.metric("▫ REITs", f"{reits_pct:.0f}%")
    
    with col4:
        gold_pct = portfolio.get('GLD', 0) * 100
        st.metric("◇ Oro", f"{gold_pct:.0f}%")

st.markdown("---")

# Sección educativa prominente
with st.expander("🎓 ¿Por qué Impulso Inversor utiliza ETFs?", expanded=False):
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        <div class="amber-card">
            <h4>🏆 Ventajas Clave de los ETFs</h4>
            <ul>
                <li><strong>Diversificación instantánea</strong>: Un ETF = cientos de activos</li>
                <li><strong>Costos ultra bajos</strong>: 0.03% vs 2-3% fondos tradicionales</li>
                <li><strong>Transparencia total</strong>: Sabes exactamente qué posees</li>
                <li><strong>Acceso global</strong>: Invierte en todo el mundo fácilmente</li>
                <li><strong>Liquidez</strong>: Compra/vende en cualquier momento</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="amber-card">
            <h4>📊 Nuestra Selección Estratégica</h4>
            <ul>
                <li><strong>BIL</strong>: Efectivo seguro (0-5% riesgo)</li>
                <li><strong>AGG</strong>: Bonos estables (+10,000 bonos)</li>
                <li><strong>ACWI</strong>: Crecimiento global (+2,900 empresas)</li>
                <li><strong>VNQ</strong>: Bienes raíces (+160 propiedades)</li>
                <li><strong>GLD</strong>: Oro físico (protección)</li>
            </ul>
            <p><strong>🎯 Resultado:</strong> Portafolio completo y diversificado globalmente</p>
        </div>
        """, unsafe_allow_html=True)

# Tabs principales
tab1, tab2, tab3, tab4, tab5 = st.tabs(["▲ Análisis de Perfil", "↗ Simulación Histórica", "⟲ Rebalanceo", "⊡ Información ETFs", "🎯 Metas Financieras"])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## ▢ Cuestionario de Perfil de Riesgo")
        
        with st.form("questionnaire"):
            col_q1, col_q2 = st.columns(2)
            
            with col_q1:
                age = st.slider("❶ ¿Cuál es tu edad?", 18, 75, 30)
                horizon = st.selectbox(
                    "❷ Horizonte de inversión",
                    ("< 3 años", "3-5 años", "5-10 años", "> 10 años"),
                )
                income = st.selectbox(
                    "❸ % de ingresos para invertir",
                    ("< 5 %", "5-10 %", "10-20 %", "> 20 %"),
                )
                knowledge = st.selectbox(
                    "❹ Conocimiento financiero",
                    ("Principiante", "Intermedio", "Avanzado"),
                )
                max_drop = st.selectbox(
                    "❺ Caída máxima tolerable",
                    ("5 %", "10 %", "20 %", "30 %", "> 30 %"),
                )
            
            with col_q2:
                reaction = st.selectbox(
                    "❶ Si tu portafolio cae 15%",
                    ("Vendo todo", "Vendo una parte", "No hago nada", "Compro más"),
                )
                liquidity = st.selectbox(
                    "❷ Necesidad de liquidez",
                    ("Alta", "Media", "Baja"),
                )
                goal = st.selectbox(
                    "❸ Objetivo principal",
                    ("Proteger capital", "Ingresos regulares", "Crecimiento balanceado", "Máximo crecimiento"),
                )
                inflation = st.selectbox(
                    "❹ Preocupación por inflación",
                    ("No me preocupa", "Me preocupa moderadamente", "Me preocupa mucho"),
                )
                digital = st.selectbox(
                    "❺ Confianza en plataformas digitales",
                    ("Baja", "Media", "Alta"),
                )

            submitted = st.form_submit_button("● Calcular mi perfil", use_container_width=True)

    with col2:
        st.markdown("## ● Tu Resultado")
        
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
                
                # Mostrar resultado con el nuevo diseño
                st.markdown(f"""
                <div class="amber-card">
                    <div style="text-align: center;">
                        <div class="sidebar-title">Tu Perfil de Riesgo</div>
                        <div class="sidebar-value">{label}</div>
                        <div class="sidebar-level">Puntaje: {total_score}/50 - Nivel {bucket + 1}/5</div>
                    </div>
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
        st.markdown("## ◐ Tu Portafolio Recomendado")
        
        portfolio = st.session_state['profile']['portfolio']
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Gráfico de torta
            fig = create_pie_chart(portfolio)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### ▢ Detalle de ETFs")
            for ticker, weight in portfolio.items():
                info = ETF_INFO[ticker]
                st.markdown(f"""
                <div class="etf-card">
                    <div class="etf-name">{info['nombre']} ({ticker})</div>
                    <div class="etf-weight">{weight*100:.0f}%</div>
                    <div class="etf-details">{info['tipo']} - Riesgo {info['riesgo']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Explicación del portafolio recomendado
        with st.expander("💡 ¿Por qué este portafolio es perfecto para ti?", expanded=False):
            st.markdown(f"""
            <div class="amber-card">
                <h4>🎯 Justificación de tu portafolio <strong>{st.session_state['profile']['label']}</strong>:</h4>
                
                **📊 Composición actual:**
            """, unsafe_allow_html=True)
            
            # Mostrar explicación personalizada según el bucket
            bucket = st.session_state['profile']['bucket']
            
            if bucket == 0:  # Conservador
                st.markdown("""
                - **30% Efectivo (BIL)**: Liquidez inmediata para emergencias
                - **50% Bonos (AGG)**: Ingresos estables y predecibles
                - **10% Acciones (ACWI)**: Crecimiento mínimo pero presente
                - **10% Oro (GLD)**: Protección adicional del capital
                
                **🛡️ Enfoque:** Máxima preservación del capital con crecimiento muy conservador.
                **✅ Ideal para:** Jubilados, inversores cerca del retiro, o personas que priorizan seguridad absoluta.
                """)
            elif bucket == 1:  # Moderado
                st.markdown("""
                - **15% Efectivo (BIL)**: Reserva de emergencia
                - **35% Bonos (AGG)**: Base estable de ingresos
                - **30% Acciones (ACWI)**: Crecimiento balanceado
                - **10% REITs (VNQ)**: Diversificación en bienes raíces
                - **10% Oro (GLD)**: Cobertura contra volatilidad
                
                **⚖️ Enfoque:** Balance perfecto entre seguridad y crecimiento.
                **✅ Ideal para:** Inversores de mediana edad que buscan estabilidad con algo de crecimiento.
                """)
            elif bucket == 2:  # Balanceado
                st.markdown("""
                - **5% Efectivo (BIL)**: Liquidez mínima necesaria
                - **25% Bonos (AGG)**: Estabilización del portafolio
                - **45% Acciones (ACWI)**: Motor principal de crecimiento
                - **15% REITs (VNQ)**: Diversificación e ingresos por dividendos
                - **10% Oro (GLD)**: Protección en crisis
                
                **⚖️ Enfoque:** Crecimiento sólido con riesgo controlado.
                **✅ Ideal para:** Inversores con horizonte de 5-10 años que toleran cierta volatilidad.
                """)
            elif bucket == 3:  # Crecimiento
                st.markdown("""
                - **15% Bonos (AGG)**: Estabilidad mínima
                - **65% Acciones (ACWI)**: Máximo potencial de crecimiento
                - **15% REITs (VNQ)**: Diversificación y dividendos
                - **5% Oro (GLD)**: Cobertura mínima
                
                **📈 Enfoque:** Crecimiento agresivo a largo plazo.
                **✅ Ideal para:** Inversores jóvenes con horizonte +10 años y alta tolerancia al riesgo.
                """)
            else:  # Agresivo
                st.markdown("""
                - **80% Acciones (ACWI)**: Máximo crecimiento posible
                - **15% REITs (VNQ)**: Diversificación en sector inmobiliario
                - **5% Oro (GLD)**: Cobertura mínima contra crisis extremas
                
                **🚀 Enfoque:** Crecimiento máximo, volatilidad alta.
                **✅ Ideal para:** Inversores muy jóvenes, con horizontes +15 años y máxima tolerancia al riesgo.
                """)
            
            st.markdown("""
            **🎯 Resultado esperado:** Este portafolio está diseñado específicamente para tu perfil de riesgo, 
            edad, horizonte de inversión y objetivos financieros. La combinación de ETFs te da acceso a 
            miles de activos globales con una sola inversión.
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
            "⬇ Descargar portafolio detallado (CSV)",
            csv,
            f"impulso_inversor_{st.session_state['profile']['label']}_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            use_container_width=True
        )

with tab2:
    st.markdown("## ↗ Simulación Histórica del Portafolio")
    
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
                    "● Inversión Inicial",
                    f"${investment_amount:,}"
                )
            
            with col2:
                st.metric(
                    "◆ Valor Final",
                    f"${final_value:,.0f}",
                    delta=f"+${final_value-investment_amount:,.0f}"
                )
            
            with col3:
                st.metric(
                    "▲ Retorno Total",
                    f"{total_return:.1f}%"
                )
            
            with col4:
                st.metric(
                    "↗ Retorno Anual",
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
                st.metric("▼ Volatilidad Anual", f"{volatility:.1f}%")
            
            with col2:
                color = "normal" if sharpe > 1 else "inverse"
                st.metric("⚡ Ratio Sharpe", f"{sharpe:.2f}", delta_color=color)
            
            with col3:
                st.metric("▼ Máxima Caída", f"{max_drawdown:.1f}%")
            
            with col4:
                st.metric("△ VaR 95%", f"{var_95:.1f}%")
            
            # Comparación con benchmarks
            if show_benchmarks and benchmark_values is not None:
                st.markdown("### ◆ Comparación con Benchmarks")
                
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
            st.markdown("### ▣ Rendimientos por Año")
            
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
    st.markdown("## ⟲ Rebalanceo del Portafolio")
    
    if 'profile' in st.session_state:
        st.markdown("""
        El rebalanceo es importante para mantener tu portafolio alineado con tu perfil de riesgo.
        Aquí puedes ver si necesitas hacer ajustes.
        """)
        
        portfolio = st.session_state['profile']['portfolio']
        
        # Simulador de portafolio actual vs objetivo
        st.markdown("### ● Estado Actual vs Objetivo")
        
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
                st.success("✓ Los pesos suman 100%")
        
        # Generar sugerencias de rebalanceo
        if abs(total_weight - 100) <= 0.1:
            suggestions = suggest_rebalancing(current_portfolio, portfolio)
            
            if suggestions:
                st.markdown("### ▢ Sugerencias de Rebalanceo")
                for suggestion in suggestions:
                    st.markdown(f"• {suggestion}")
            else:
                st.success("✓ Tu portafolio está bien balanceado!")
        
        # Costo estimado de rebalanceo
        st.markdown("### $ Estimación de Costos")
        
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
            
            st.metric("▼ Costo Total Estimado", f"${total_cost:.2f}")
            
            if total_cost / portfolio_value_for_rebalance > 0.02:  # Más del 2%
                st.warning("⚠️ El costo de rebalanceo es alto (>2% del portafolio)")
            else:
                st.success("✓ Costo de rebalanceo razonable")
    
    else:
        st.info("👆 Primero completa el cuestionario en la pestaña 'Análisis de Perfil'")

with tab4:
    st.markdown("## ⊡ Información Detallada de los ETFs")
    
    # Sección educativa sobre ETFs
    with st.expander("▲ ¿Por qué elegimos ETFs para tu portafolio?", expanded=False):
        st.markdown("""
        <div class="amber-card">
            <h4>Ventajas de los ETFs sobre otros instrumentos financieros:</h4>
            
            **🆚 ETFs vs Acciones Individuales:**
            - ✓ **Diversificación instantánea**: Un solo ETF contiene cientos de acciones
            - ✓ **Menor riesgo**: No dependes del rendimiento de una sola empresa
            - ✓ **Gestión profesional**: Siguen índices creados por expertos
            
            **🆚 ETFs vs Fondos Mutuos:**
            - ✓ **Menores comisiones**: Costos típicos de 0.03%-0.75% vs 1%-3% de fondos activos
            - ✓ **Transparencia total**: Sabes exactamente qué tienes en tu portafolio
            - ✓ **Flexibilidad**: Se pueden comprar/vender en cualquier momento del día
            
            **🆚 ETFs vs Bonos Individuales:**
            - ✓ **Acceso institucional**: Accedes a bonos que normalmente requieren $100,000+ mínimo
            - ✓ **Diversificación**: Miles de bonos en un solo instrumento
            - ✓ **Liquidez**: Más fácil de comprar/vender que bonos individuales
            
            **🆚 ETFs vs Criptomonedas:**
            - ✓ **Estabilidad**: Respaldados por activos reales con historial comprobado
            - ✓ **Regulación**: Supervisados por autoridades financieras
            - ✓ **Volatilidad controlada**: Menos fluctuaciones extremas
        </div>
        """, unsafe_allow_html=True)
    
    # Resumen de instrumentos elegidos
    with st.expander("◆ Resumen de los 5 ETFs seleccionados", expanded=False):
        st.markdown("""
        <div class="amber-card">
            <h4>Nuestra selección estratégica de ETFs:</h4>
            
            **▦ BIL - SPDR Bloomberg 1-3 Month T-Bill ETF**
            - 🎯 **Propósito**: Efectivo y liquidez inmediata
            - 📊 **Contenido**: Letras del Tesoro de EE.UU. a 1-3 meses
            - ✓ **Ventaja**: Máxima seguridad, disponibilidad inmediata de fondos
            
            **▪ AGG - iShares Core U.S. Aggregate Bond ETF**
            - 🎯 **Propósito**: Estabilidad e ingresos regulares
            - 📊 **Contenido**: +10,000 bonos del gobierno y corporativos de EE.UU.
            - ✓ **Ventaja**: Diversificación masiva en renta fija, pagos de intereses estables
            
            **▫ ACWI - iShares MSCI ACWI ETF**
            - 🎯 **Propósito**: Crecimiento a largo plazo y diversificación global
            - 📊 **Contenido**: +2,900 acciones de 47 países (desarrollados y emergentes)
            - ✓ **Ventaja**: Exposición al crecimiento económico mundial en un solo ETF
            
            **▫ VNQ - Vanguard Real Estate ETF**
            - 🎯 **Propósito**: Protección contra inflación y diversificación
            - 📊 **Contenido**: +160 REITs de centros comerciales, oficinas, apartamentos
            - ✓ **Ventaja**: Ingresos por dividendos altos, correlación baja con acciones
            
            **◇ GLD - SPDR Gold Shares**
            - 🎯 **Propósito**: Cobertura contra crisis y diversificación
            - 📊 **Contenido**: Oro físico almacenado en bóvedas seguras
            - ✓ **Ventaja**: Protección en tiempos de incertidumbre, preservación de valor
            
            ---
            
            **🎯 Estrategia de combinación:**
            
            Esta selección te permite acceder a **TODA la economía global** con solo 5 instrumentos:
            - **Liquidez** (BIL): Para emergencias y oportunidades
            - **Estabilidad** (AGG): Para ingresos predecibles
            - **Crecimiento** (ACWI): Para multiplicar tu capital
            - **Inmuebles** (VNQ): Para diversificar y generar ingresos
            - **Protección** (GLD): Para preservar valor en crisis
            
            **💡 Resultado**: Un portafolio completo, diversificado globalmente, con costos bajos y gestión simple.
        </div>
        """, unsafe_allow_html=True)
    
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
                st.markdown(f"**▪ Descripción:** {info['descripcion']}")
                st.markdown(f"**▫ Tipo de activo:** {info['tipo']}")
                st.markdown(f"**△ Nivel de riesgo:** {info['riesgo']}")
                st.markdown(f"**↗ Rendimiento esperado:** {info['rendimiento_esperado']}")
                
                # Información adicional específica
                if ticker == "AGG":
                    st.markdown(f"**● Duración:** {info['duración']}")
                    st.markdown(f"**$ Yield:** {info['yield']}")
                elif ticker == "ACWI":
                    st.markdown(f"**○ Cobertura:** {info['países']}, {info['empresas']}")
                elif ticker == "VNQ":
                    st.markdown(f"**$ Dividend Yield:** {info['dividend_yield']}")
                elif ticker == "GLD":
                    st.markdown(f"**▫ Correlación:** {info['correlación']}")
            
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
    st.markdown("## ⊡ Glosario de Términos Financieros")
    
    with st.expander("⊡ Ver Glosario Completo"):
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

with tab5:
    st.markdown("## 🎯 Calculadora de Metas Financieras")
    st.markdown("### Planifica tu futuro financiero con precisión")
    
    # Selector de tipo de meta
    goal_type = st.selectbox(
        "¿Qué meta financiera quieres calcular?",
        ["🏖️ Jubilación", "🏠 Comprar Casa", "🎓 Educación/Universidad", "🚨 Fondo de Emergencia", "📊 Proyección de Portafolio"],
        index=0
    )
    
    if goal_type == "🏖️ Jubilación":
        st.markdown("---")
        st.markdown("### 🏖️ Calculadora de Jubilación")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### Información Personal")
            current_age = st.slider("Tu edad actual", 18, 65, 30)
            retirement_age = st.slider("Edad de jubilación deseada", current_age + 1, 75, 65)
            current_savings = st.number_input("Ahorros actuales para jubilación ($)", 0, 1000000, 10000, 1000)
            monthly_expenses = st.number_input("Gastos mensuales actuales ($)", 500, 20000, 3000, 100)
            inflation_rate = st.slider("Tasa de inflación anual (%)", 1.0, 6.0, 3.0, 0.1) / 100
        
        with col2:
            if st.button("🔮 Calcular Plan de Jubilación", use_container_width=True):
                result = calculate_retirement_goal(current_age, retirement_age, current_savings, monthly_expenses, inflation_rate)
                
                st.markdown("#### 🎯 Resultados:")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("💰 Total necesario", f"${result['total_needed']:,.0f}")
                    st.metric("📈 Valor futuro ahorros actuales", f"${result['current_savings_future_value']:,.0f}")
                
                with col_b:
                    st.metric("💸 Cantidad adicional a ahorrar", f"${result['additional_needed']:,.0f}")
                    st.metric("🏠 Gastos mensuales al jubilarte", f"${result['monthly_expenses_at_retirement']:,.0f}")
                
                # Calcular cuánto invertir mensualmente
                if result['additional_needed'] > 0:
                    expected_return = 0.07  # 7% anual promedio
                    monthly_needed = calculate_monthly_investment_needed(
                        result['additional_needed'], 
                        result['years_to_retirement'], 
                        expected_return
                    )
                    
                    st.markdown("---")
                    st.markdown("#### 📊 Plan de Inversión Sugerido:")
                    
                    col_x, col_y = st.columns(2)
                    with col_x:
                        st.metric("💵 Inversión mensual necesaria", f"${monthly_needed:,.0f}")
                        st.metric("⏱️ Años hasta jubilación", f"{result['years_to_retirement']} años")
                    
                    with col_y:
                        total_contributions = monthly_needed * result['years_to_retirement'] * 12
                        st.metric("💰 Total a contribuir", f"${total_contributions:,.0f}")
                        st.metric("📈 Rendimiento esperado", "7% anual")
                    
                    # Crear gráfico de proyección
                    years_data = list(range(0, result['years_to_retirement'] + 1))
                    values_data = []
                    
                    for year in years_data:
                        projection = calculate_portfolio_projection(
                            current_savings, monthly_needed, year, expected_return
                        )
                        values_data.append(projection['future_value'])
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=years_data,
                        y=values_data,
                        mode='lines',
                        name='Valor del portafolio',
                        line=dict(color='#667eea', width=3)
                    ))
                    
                    fig.add_hline(y=result['total_needed'], line_dash="dash", 
                                line_color="red", annotation_text="Meta de jubilación")
                    
                    fig.update_layout(
                        title="Proyección de tu Fondo de Jubilación",
                        xaxis_title="Años",
                        yaxis_title="Valor ($)",
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.success("🎉 ¡Felicitaciones! Ya tienes suficiente dinero ahorrado para tu jubilación.")
    
    elif goal_type == "🏠 Comprar Casa":
        st.markdown("---")
        st.markdown("### 🏠 Calculadora para Comprar Casa")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### Detalles de la Casa")
            house_price = st.number_input("Precio de la casa ($)", 50000, 2000000, 300000, 10000)
            down_payment_pct = st.slider("Porcentaje de enganche (%)", 5, 50, 20) / 100
            years_to_buy = st.slider("¿En cuántos años quieres comprar?", 1, 15, 5)
            expected_return = st.slider("Rendimiento esperado de inversiones (%)", 3.0, 12.0, 7.0, 0.5) / 100
        
        with col2:
            if st.button("🏠 Calcular Plan de Ahorro", use_container_width=True):
                result = calculate_house_down_payment(house_price, down_payment_pct, years_to_buy, expected_return)
                
                st.markdown("#### 🎯 Resultados:")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("🏠 Precio de la casa", f"${result['house_price']:,.0f}")
                    st.metric("💰 Enganche necesario", f"${result['down_payment_needed']:,.0f}")
                
                with col_b:
                    st.metric("📋 Costos de cierre", f"${result['closing_costs']:,.0f}")
                    st.metric("💸 Total necesario", f"${result['total_upfront']:,.0f}")
                
                st.markdown("---")
                st.markdown("#### 📊 Plan de Inversión:")
                
                col_x, col_y = st.columns(2)
                with col_x:
                    st.metric("💵 Inversión mensual total", f"${result['monthly_total']:,.0f}")
                    st.metric("💰 Solo para enganche", f"${result['monthly_for_down_payment']:,.0f}")
                
                with col_y:
                    st.metric("⏱️ Tiempo de ahorro", f"{result['years_to_save']} años")
                    st.metric("📈 Rendimiento asumido", f"{expected_return*100:.1f}% anual")
    
    elif goal_type == "🎓 Educación/Universidad":
        st.markdown("---")
        st.markdown("### 🎓 Calculadora de Educación/Universidad")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### Información del Estudiante")
            child_age = st.slider("Edad actual del estudiante", 0, 17, 5)
            college_cost_today = st.number_input("Costo anual universidad hoy ($)", 10000, 100000, 50000, 1000)
            years_of_college = st.slider("Años de universidad", 2, 6, 4)
            inflation_rate = st.slider("Inflación educativa anual (%)", 3.0, 8.0, 5.0, 0.1) / 100
            expected_return = st.slider("Rendimiento esperado (%)", 4.0, 10.0, 7.0, 0.5) / 100
        
        with col2:
            if st.button("🎓 Calcular Plan Educativo", use_container_width=True):
                result = calculate_education_fund(child_age, college_cost_today, years_of_college, inflation_rate, expected_return)
                
                st.markdown("#### 🎯 Resultados:")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("💰 Total necesario", f"${result['total_needed']:,.0f}")
                    st.metric("📈 Costo anual futuro", f"${result['future_annual_cost']:,.0f}")
                
                with col_b:
                    st.metric("💵 Inversión mensual", f"${result['monthly_needed']:,.0f}")
                    st.metric("⏱️ Años para ahorrar", f"{result['years_to_save']} años")
                
                if result['years_to_save'] > 0:
                    st.info(f"💡 **Consejo**: Empezar a ahorrar ${result['monthly_needed']:,.0f} mensuales te permitirá cubrir completamente los costos universitarios.")
                else:
                    st.warning("⚠️ El estudiante ya está en edad universitaria. Necesitas el dinero inmediatamente.")
    
    elif goal_type == "🚨 Fondo de Emergencia":
        st.markdown("---")
        st.markdown("### 🚨 Calculadora de Fondo de Emergencia")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### Información de Gastos")
            monthly_expenses = st.number_input("Gastos mensuales esenciales ($)", 500, 15000, 3000, 100)
            months_coverage = st.slider("Meses de cobertura deseados", 3, 12, 6)
            current_emergency_fund = st.number_input("Fondo de emergencia actual ($)", 0, 100000, 0, 500)
        
        with col2:
            if st.button("🚨 Calcular Fondo de Emergencia", use_container_width=True):
                result = calculate_emergency_fund(monthly_expenses, months_coverage)
                
                st.markdown("#### 🎯 Resultados:")
                
                target_needed = result['target_amount'] - current_emergency_fund
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("🎯 Meta total", f"${result['target_amount']:,.0f}")
                    st.metric("💰 Ya tienes", f"${current_emergency_fund:,.0f}")
                
                with col_b:
                    st.metric("💸 Aún necesitas", f"${max(0, target_needed):,.0f}")
                    st.metric("📅 Meses de cobertura", f"{months_coverage} meses")
                
                if target_needed > 0:
                    monthly_to_save = target_needed / (result['years_to_build'] * 12)
                    st.markdown("---")
                    st.markdown("#### 📊 Plan de Ahorro:")
                    
                    col_x, col_y = st.columns(2)
                    with col_x:
                        st.metric("💵 Ahorro mensual sugerido", f"${monthly_to_save:,.0f}")
                        st.metric("⏱️ Tiempo para completar", f"{result['years_to_build']} años")
                    
                    with col_y:
                        percentage_of_income = (monthly_to_save / monthly_expenses) * 100
                        st.metric("📊 % de tus gastos mensuales", f"{percentage_of_income:.1f}%")
                        st.metric("🎯 Cobertura objetivo", f"{months_coverage} meses")
                    
                    st.info("💡 **Recomendación**: Guarda este dinero en una cuenta de ahorros de alto rendimiento, no en inversiones riesgosas.")
                else:
                    st.success("🎉 ¡Felicitaciones! Ya tienes un fondo de emergencia completo.")
    
    elif goal_type == "📊 Proyección de Portafolio":
        st.markdown("---")
        st.markdown("### 📊 Proyección de Crecimiento del Portafolio")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### Parámetros de Inversión")
            initial_amount = st.number_input("Inversión inicial ($)", 0, 1000000, 10000, 1000)
            monthly_contribution = st.number_input("Contribución mensual ($)", 0, 10000, 500, 50)
            years = st.slider("Período de inversión (años)", 1, 40, 20)
            expected_return = st.slider("Rendimiento anual esperado (%)", 1.0, 15.0, 7.0, 0.5) / 100
        
        with col2:
            if st.button("📊 Calcular Proyección", use_container_width=True):
                result = calculate_portfolio_projection(initial_amount, monthly_contribution, years, expected_return)
                
                st.markdown("#### 🎯 Proyección Futura:")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("💰 Valor futuro total", f"${result['future_value']:,.0f}")
                    st.metric("💵 Total contribuido", f"${result['total_contributions']:,.0f}")
                
                with col_b:
                    st.metric("📈 Interés ganado", f"${result['total_interest']:,.0f}")
                    roi_percentage = (result['total_interest'] / result['total_contributions']) * 100
                    st.metric("📊 ROI total", f"{roi_percentage:.1f}%")
                
                # Crear gráfico de proyección año por año
                years_data = list(range(0, years + 1))
                values_data = []
                contributions_data = []
                
                for year in years_data:
                    proj = calculate_portfolio_projection(initial_amount, monthly_contribution, year, expected_return)
                    values_data.append(proj['future_value'])
                    contributions_data.append(proj['total_contributions'])
                
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=years_data,
                    y=contributions_data,
                    mode='lines',
                    name='Total Contribuido',
                    line=dict(color='#f093fb', width=2)
                ))
                
                fig.add_trace(go.Scatter(
                    x=years_data,
                    y=values_data,
                    mode='lines',
                    name='Valor Total',
                    line=dict(color='#667eea', width=3)
                ))
                
                fig.update_layout(
                    title="Crecimiento del Portafolio a lo Largo del Tiempo",
                    xaxis_title="Años",
                    yaxis_title="Valor ($)",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabla año por año (últimos 10 años)
                if years >= 10:
                    st.markdown("#### 📅 Proyección por Década:")
                    decade_data = []
                    for decade in [10, 20, 30, 40]:
                        if decade <= years:
                            proj = calculate_portfolio_projection(initial_amount, monthly_contribution, decade, expected_return)
                            decade_data.append({
                                'Años': decade,
                                'Valor Total': f"${proj['future_value']:,.0f}",
                                'Contribuciones': f"${proj['total_contributions']:,.0f}",
                                'Interés Ganado': f"${proj['total_interest']:,.0f}"
                            })
                    
                    if decade_data:
                        df_decades = pd.DataFrame(decade_data)
                        st.dataframe(df_decades, use_container_width=True)

# Footer estilo AmberLatam
st.markdown("""
<div class="amber-footer">
    <h3>△ Disclaimer Importante</h3>
    <p>Esta herramienta tiene fines <strong>educativos e informativos únicamente</strong>. 
    No constituye asesoramiento financiero personalizado.</p>
    <p>Los rendimientos pasados no garantizan resultados futuros. 
    <strong>Consulta con un asesor financiero profesional</strong> antes de tomar decisiones de inversión.</p>
    <p style="margin-top: 15px; font-size: 0.8rem; color: var(--text-secondary);">
        ✨ Impulso Inversor - Desarrollado con tecnología moderna
    </p>
</div>
""", unsafe_allow_html=True)