import openai


def generar_prompt_y_analizar(ticker, intervalo, data):
    if data is None or data.empty:
        return "No hay datos de mercado disponibles para analizar el ticker solicitado."
    # ...resto de tu función...


    tabla = data[["Open", "High", "Low", "Close", "Volume"]].to_csv(index=True)

    if intervalo == "15M":
        horizonte = "las próximas 8 a 24 horas"
    elif intervalo == "1H":
        horizonte = "las próximas 8 a 24 horas"
    elif intervalo == "1D":
        horizonte = "los próximos 10 a 20 días"
    elif intervalo == "1W":
        horizonte = "las próximas 4 a 8 semanas"
    elif intervalo == "1M":
        horizonte = "los próximos meses"
    else:
        horizonte = "los próximos días"

    prompt = f"""
Usa el análisis técnico más detallado posible y responde en cinco bloques, siempre usando estos títulos exactos (los números y los dos puntos son obligatorios):

1. Resumen Técnico:
2. Pivots Mensuales:
3. Probabilidad de Subida o Bajada en %:
4. Proyección de Precios Target y Stop Loss:
5. Evaluación de Riesgo/Beneficio:

Conclusion:
Al final del análisis, **devuelve únicamente la conclusión en una línea de JSON estrictamente válido. NO EXPLIQUES, NO COMENTES, NO AGREGUES TEXTO ANTES O DESPUÉS.**
Solo el bloque JSON, así (esto es SOLO FORMATO, NO valores reales):

{{"conclusion": {{"last_price": X, "probable_target": X, "probable_stop": X, "risk_reward_ratio": X, "probability": X}}}}

Solo entrega ese bloque de JSON, en una sola línea, al final del análisis.

Para el análisis utiliza los siguientes datos históricos del ticker {ticker} en temporalidad {intervalo}:
{tabla}

Analiza y responde:
- Revisa la tendencia general y detecta impulsos y retrocesos relevantes.
- Calcula los pivots mensuales o diarios segun veas relevante con su dirección (alcista o bajista).
- Dame la probabilidad de subida o bajada para {horizonte}.
- Proyecta precios target y stop loss realistas y especifica en negrita si es alcista o bajista.
- Usa regresión, volatilidad, rangos para detectar estructuras coherentes.
- Dame el resultado de riesgo/recompenza utilizando los valores de target y stop
- Explica cómo llegaste al resultado y qué métodos usaste.
"""  # ← SOLO AQUÍ CIERRAS LAS TRES COMILLAS

    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=1200
    )

    return response.choices[0].message.content

#git add .
#git commit -m "Corrijo formato de prompt"
#git pull
#git push
