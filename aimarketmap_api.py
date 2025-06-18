from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import openai
import os
from alpha_vantage.timeseries import TimeSeries
from analysis import generar_prompt_y_analizar
from dotenv import load_dotenv
from pycoingecko import CoinGeckoAPI
from datetime import datetime

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
    intervalo = request.intervalo.upper()

    crypto_symbols = {
        "BTC", "BTC/USD",
        "ETH", "ETH/USD",
        "SOL", "SOL/USD",
        "ADA", "ADA/USD",
        "BNB", "BNB/USD"
    }

    try:
        if ticker in crypto_symbols:
            print(f"🔍 Analizando {ticker} con CoinGecko...")

            # Map de símbolos -> ID reales de CoinGecko
            coingecko_ids = {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "SOL": "solana",
                "ADA": "cardano",
                "BNB": "binancecoin"
            }

            base_symbol = ticker.split("/")[0]
            crypto_symbol = coingecko_ids.get(base_symbol)

            if not crypto_symbol:
                raise Exception(f"Ticker {base_symbol} no tiene un ID válido en CoinGecko.")

            cg = CoinGeckoAPI()
            days_map = {"1D": 1, "1W": 7, "1M": 30}
            days = days_map.get(intervalo, 1)

            ohlc = cg.get_coin_ohlc_by_id(id=crypto_symbol, vs_currency='usd', days=days)

            df = pd.DataFrame(ohlc, columns=['timestamp', 'Open', 'High', 'Low', 'Close'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df['Volume'] = None
            data = df.tail(50)

        else:
            print(f"📈 Analizando {ticker} con Alpha Vantage...")
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
        return {"error": f"Error obteniendo datos de mercado: {str(e)}"}

    print("✅ DATA ENVIADA AL PROMPT:\n", data.head())
    try:
        resultado = generar_prompt_y_analizar(ticker, intervalo, data)
    except Exception as e:
        print("❌ ERROR en generar_prompt_y_analizar:", e)
        return {"error": f"Error al generar análisis con AI: {str(e)}"}

    print("🧠 RESULTADO DEL ANALISIS:\n", resultado)

    return {"resultado": resultado}


# Debug prints al iniciar
print("🔐 OPENAI_API_KEY:", openai.api_key)
print("🔐 ALPHA_VANTAGE_API_KEY:", ALPHA_VANTAGE_API_KEY)



#git add .
#git commit -m "agrego coingeco datos criptos"
#git pull
#git push

