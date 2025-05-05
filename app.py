import streamlit as st
import yfinance as yf
import pandas as pd

# 🔧 Personaliza el estilo general
st.markdown("""
    <style>
    /* Fondo general */
    .stApp {
        background-color: #1e1b2e;
        color: white;
    }
    /* Títulos y markdowns */
    h1, h2, h3, h4, h5, h6, .stMarkdown, .stText {
        color: white;
    }
    /* Labels de los selectbox */
    label {
        color: white !important;
        font-weight: bold;
    }
    /* Bordes y redondeado para containers */
    .stContainer {
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Logo opcional: descomenta si vuelves a agregarlo
# st.image("logo_gbc.png", width=250)

# Tickers disponibles
tickers = ["AAPL", "MSFT", "TSLA", "GOOGL", "NVDA"]

st.title("📈 Dashboard Financiero")
st.subheader("Selecciona un ticker e intervalo para ver su comportamiento:")

# Selección en columnas
col1, col2, col3 = st.columns(3)
with col1:
    selected_ticker = st.selectbox("Ticker", tickers)
with col2:
    interval = st.selectbox("Intervalo de tiempo", ["15m", "30m", "60m", "1d"], index=2)
with col3:
    pivot_type = st.selectbox("Tipo de pivots", ["Day", "Week", "Month"], index=0)

# Descargar datos (30 días para cubrir Month)
df = yf.download(selected_ticker, period="30d", interval=interval, progress=False)
df.dropna(inplace=True)

if len(df) < 5:
    st.warning("⚠️ No hay suficientes datos para mostrar el gráfico.")
    st.dataframe(df.tail())
else:
    # Calcular EMAs
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()

    # Calcular pivots según selección
    df["Date"] = pd.to_datetime(df.index)
    df["Day"] = df["Date"].dt.date
    df["Week"] = df["Date"].dt.isocalendar().week
    df["Month"] = df["Date"].dt.month

    if pivot_type == "Day":
        last_period = df["Day"].unique()[-2]
        df_pivot = df[df["Day"] == last_period]
    elif pivot_type == "Week":
        last_period = df["Week"].unique()[-2]
        df_pivot = df[df["Week"] == last_period]
    elif pivot_type == "Month":
        last_period = df["Month"].unique()[-2]
        df_pivot = df[df["Month"] == last_period]

    # Obtener High, Low, Close previos
    high = df_pivot["High"].max()
    low = df_pivot["Low"].min()
    close_prev = df_pivot["Close"].iloc[-1]

    # Limpieza
    high = high.item() if hasattr(high, "item") else float(high)
    low = low.item() if hasattr(low, "item") else float(low)
    close_prev = close_prev.item() if hasattr(close_prev, "item") else float(close_prev)

    pp = (high + low + close_prev) / 3
    r1 = (2 * pp) - low
    r2 = pp + (high - low)
    s1 = (2 * pp) - high
    s2 = pp - (high - low)

    # Última fila
    ultima = df.iloc[-1]
    precio = ultima["Close"]
    ema20 = ultima["EMA20"]
    ema50 = ultima["EMA50"]

    precio = precio.item() if hasattr(precio, "item") else float(precio)
    ema20 = ema20.item() if hasattr(ema20, "item") else float(ema20)
    ema50 = ema50.item() if hasattr(ema50, "item") else float(ema50)

    # Evaluación de condiciones
    ema_diff_pct = abs(ema20 - ema50) / ema50 * 100
    criterios = [
        ("📈 EMA20 > EMA50", ema20 > ema50),
        ("📊 Diferencia EMA20/EMA50 > 0.5%", ema_diff_pct > 0.5),
        ("💲 Precio actual > PP", precio > pp),
        ("📏 Precio entre S1 y R1", s1 < precio < r1)
    ]

    # Diagnóstico
    st.markdown("### 🧠 Diagnóstico")
    zona = ""
    if criterios[0][1] and criterios[1][1] and criterios[2][1]:
        zona = "🟢 Zona Alcista"
    elif not criterios[0][1] and criterios[1][1] and not criterios[2][1]:
        zona = "🔴 Zona Bajista"
    elif criterios[3][1] and ema_diff_pct < 0.5:
        zona = "🟡 Zona Lateral"
    else:
        zona = "⚪ Zona no definida"
    st.markdown(f"<div style='font-size:24px; font-weight:bold; color:white'>{zona}</div>", unsafe_allow_html=True)

    # 🚨 Alerta pivots
    target = None
    stop = None

    if precio < pp:
        target = pp
        stop = s1
        zona_pivote = f"🔸 Precio entre S1 y PP → Target: PP | Stop: S1"
    elif pp <= precio < r1:
        target = r1
        stop = pp
        zona_pivote = f"🔸 Precio entre PP y R1 → Target: R1 | Stop: PP"
    elif r1 <= precio < r2:
        target = r2
        stop = r1
        zona_pivote = f"🔸 Precio entre R1 y R2 → Target: R2 | Stop: R1"
    else:
        zona_pivote = None

    if target and stop:
        distancia_up = target - precio
        distancia_down = precio - stop
        ratio = distancia_up / distancia_down if distancia_down != 0 else None

        if ratio and ratio > 1:
            st.markdown("### 🚨 Alerta 📏 Análisis de espacio hasta pivots")
            st.write(f"<span style='color:white'>{zona_pivote}</span>", unsafe_allow_html=True)
            st.write(f"<span style='color:white'>🎯 Distancia al target: {round(distancia_up, 2)}</span>", unsafe_allow_html=True)
            st.write(f"<span style='color:white'>🛡️ Distancia al stop: {round(distancia_down, 2)}</span>", unsafe_allow_html=True)
            st.write(f"<span style='color:white'>⚖️ <b>Ratio (target/stop): {round(ratio, 2)}</b></span>", unsafe_allow_html=True)
            st.success("✅ La relación riesgo/beneficio es positiva (mayor espacio hacia el target)")

    # Criterios técnicos
    st.markdown("### 🧪 Evaluación de criterios técnicos")
    for texto, cumple in criterios:
        icono = "✅" if cumple else "❌"
        color = "aqua" if cumple else "red"
        st.markdown(f"<span style='color:{color}'>{icono} {texto}</span>", unsafe_allow_html=True)

    # 🌐 Rango últimos 7 días
    st.markdown("### 🌐 Rango de los últimos 7 días")
    precio_max_7d = df["High"].tail(7 * 24).max()
    precio_min_7d = df["Low"].tail(7 * 24).min()
    precio_max_7d = precio_max_7d.item() if hasattr(precio_max_7d, "item") else float(precio_max_7d)
    precio_min_7d = precio_min_7d.item() if hasattr(precio_min_7d, "item") else float(precio_min_7d)

    col1, col2 = st.columns(2)
    col1.markdown(f"<div style='color:aqua; font-size:20px; font-weight:bold'>🔺 Máximo: ${round(precio_max_7d, 2)}</div>", unsafe_allow_html=True)
    col2.markdown(f"<div style='color:purple; font-size:20px; font-weight:bold'>🔻 Mínimo: ${round(precio_min_7d, 2)}</div>", unsafe_allow_html=True)
