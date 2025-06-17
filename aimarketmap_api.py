from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import openai
import os
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.cryptocurrencies import CryptoCurrencies
from analysis import generar_prompt_y_analizar
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

openai.api_key = os.getenv("OPENAI_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

class AnalisisRequest(BaseModel):
    ticker: str
    intervalo: str

@app.get("/")
def root():
    return {"status": "API online"}

@app.post("/analizar")
def analizar(request: AnalisisRequest):
    ticker = request.ticker.upper()
    intervalo = request.intervalo

    # === Detectar si es criptomoneda ===
    crypto_symbols = {
        "BTC", "BTC/USD", "ETH", "ETH/USD", "SOL", "SOL/USD", "ADA", "ADA/USD", "BNB", "BNB/USD"
    }

    try:
        if ticker in crypto_symbols:
            # === LIMPIAR ticker (BTC/USD -> BTC) ===
            crypto_symbol = ticker.split("/")[0]
            market = "USD"

            cc = CryptoCurrencies(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
            data, meta = cc.get_digital_currency_daily(symbol=crypto_symbol, market=market)

            # Renombrar columnas para mantener consistencia
            data = data.rename(columns={
                '1a. open (USD)': 'Open',
                '2a. high (USD)': 'High',
                '3a. low (USD)': 'Low',
                '4a. close (USD)': 'Close',
                '5. volume': 'Volume'
            }).dropna().tail(50)

        else:
            # === FLUJO PARA ACCIONES ===
            av_intervals = {
                '15M': ('15min', 'compact'),
                '1H': ('60min', 'compact'),
                '1D': ('daily', 'compact'),
                '1W': ('weekly', 'compact'),
                '1M': ('monthly', 'compact'),
            }
            interval, outputsize = av_intervals.get(intervalo, ('daily', 'compact'))

            ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')

            if interval in ['15min', '60min']:
                data, meta = ts.get_intraday(symbol=ticker, interval=interval, outputsize=outputsize)
            elif interval == 'daily':
                data, meta = ts.get_daily(symbol=ticker, outputsize=outputsize)
            elif interval == 'weekly':
                data, meta = ts.get_weekly(symbol=ticker)
            elif interval == 'monthly':
                data, meta = ts.get_monthly(symbol=ticker)
            else:
                data, meta = ts.get_daily(symbol=ticker, outputsize=outputsize)

            data = data.rename(columns={
                '1. open': 'Open',
                '2. high': 'High',
                '3. low': 'Low',
                '4. close': 'Close',
                '5. volume': 'Volume'
            }).dropna().tail(50)

    except Exception as e:
        print("❌ ERROR al obtener datos:", e)
        return {"error": f"Error obteniendo datos de Alpha Vantage: {e}"}

    print("✅ DATA ENVIADA AL PROMPT:\n", data.head())
    resultado = generar_prompt_y_analizar(ticker, intervalo, data)
    print("🧠 RESULTADO DEL ANALISIS:\n", resultado)

    return {"resultado": resultado}


# Debug prints al iniciar
print("🔐 OPENAI_API_KEY:", openai.api_key)
print("🔐 ALPHA_VANTAGE_API_KEY:", ALPHA_VANTAGE_API_KEY)


#git add .
#git commit -m "Corrijo formato de llaves en el prompt de conclusión"
#git pull
#git push

