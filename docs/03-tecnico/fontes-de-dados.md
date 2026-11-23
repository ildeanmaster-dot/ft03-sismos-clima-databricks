# Fontes de dados
Versão 0.1 · 23/11/2026

## USGS Earthquake Catalog (FDSN Event Web Service)
- Consulta: `https://earthquake.usgs.gov/fdsnws/event/1/query`; contagem: `.../count`.
- Parâmetros usados: `format=geojson`, `starttime`, `endtime`, `minmagnitude`, `orderby=time-asc`, `limit`, `offset`.
- Limite: `limit` aceita 1 a 20.000; consultas acima de 20.000 eventos devolvem HTTP 400 (docs.html, consultado 23/11/2026).
- Taxa: número não publicado; excesso devolve HTTP 429 (aviso na lista realtime-feeds da USGS, jan/2022). Adotar limite conservador (DT-04).
- Autenticação: não exige.

## Open-Meteo Historical Weather
- Endpoint: `https://archive-api.open-meteo.com/v1/archive`.
- Parâmetros: `latitude`, `longitude`, `start_date`, `end_date` (yyyy-mm-dd), `hourly`, `timezone` (padrão GMT).
- Variáveis previstas: `temperature_2m` (°C), `relative_humidity_2m` (%), `precipitation` (mm, soma da hora anterior), `wind_speed_10m` (km/h), `surface_pressure` (hPa).
- Erro: HTTP 400 com `{"error": true, "reason": ...}`.
- Atraso: ERA5 e ERA5-Land com 5 dias.
- Limites do plano gratuito: 600/min, 5.000/h, 10.000/dia, 300.000/mês; mais de 10 variáveis ou mais de 2 semanas conta como várias chamadas; limite aplicado por IP. Só uso não comercial; CC BY 4.0.
- Fontes: open-meteo.com/en/docs/historical-weather-api, /en/terms, /en/pricing (consultadas 23/11/2026).
