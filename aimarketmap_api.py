from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import openai
import os
from alpha_vantage.timeseries import TimeSeries
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
    ticker = request.ticker
    intervalo = request.intervalo

    av_intervals = {
        '15M': ('15min', 'compact'),
        '1H': ('60min', 'compact'),
        '1D': ('daily', 'compact'),
        '1W': ('weekly', 'compact'),
        '1M': ('monthly', 'compact'),
    }
    interval, outputsize = av_intervals.get(intervalo, ('daily', 'compact'))

    ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')

    try:
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
        print("ERROR AL OBTENER DATOS:", e)
        return {"error": f"Error obteniendo datos de Alpha Vantage: {e}"}

    print("DATA ENVIADA AL PROMPT:\n", data.head())  # <- Te muestra las primeras filas

    resultado = generar_prompt_y_analizar(ticker, intervalo, data)
    print("RESULTADO DEL ANALISIS:\n", resultado)     # <- Te muestra la respuesta de OpenAI

    return {"resultado": resultado}


print("OPENAI_API_KEY:", openai.api_key)
print("ALPHA_VANTAGE_API_KEY:", ALPHA_VANTAGE_API_KEY)
