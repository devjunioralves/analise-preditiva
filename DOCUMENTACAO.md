# Documentação do Projeto - Análise Preditiva de Tráfego

## Propósito

Projeto de análise preditiva que coleta dados de tráfego em tempo real de Jaraguá do Sul (SC), armazena em banco de dados, processa e prepara para modelos de Machine Learning que prevêem:

- Tempo de viagem entre pontos
- Nível de congestionamento
- Melhor horário para trafegar em rotas específicas

## Fluxo do Projeto

### 1. Coleta de Dados

**Script:** `src/data_collection/traffic_collector.py`

- Lê rotas configuradas em `config/routes.json` (8 rotas de Jaraguá do Sul)
- Faz requisições para API TomTom Traffic (ou Google Maps)
- Para cada rota coleta:
  - Velocidade atual e velocidade ideal
  - Tempo de viagem e tempo sem tráfego
  - Atraso em segundos
  - Coordenadas geográficas
- Calcula índice de congestionamento (0-100%)
- Detecta se é horário de pico
- Salva em CSV (`data/raw/traffic_data_YYYYMMDD_HHMMSS.csv`)
- Gera mapa interativo HTML (`data/maps/traffic_map_YYYYMMDD_HHMMSS.html`)

**Frequência:** A cada 15 minutos (configurável no `.env`)

### 2. Armazenamento

**Script:** `src/database/import_traffic_to_db.py`

- Importa CSVs para banco SQLite (`database/traffic.db`)
- Cria 4 tabelas:
  - `traffic_data`: dados brutos coletados
  - `routes`: registro de rotas monitoradas
  - `incidents`: eventos/acidentes (futuro)
  - `historical_patterns`: agregações por rota/hora/dia
- Atualiza padrões históricos automaticamente

### 3. Processamento (em desenvolvimento)

**Script:** `src/data_processing/clean_traffic_data.py` (a criar)

- Remove duplicados
- Trata valores ausentes
- Detecta e trata outliers
- Cria features derivadas:
  - `hour_sin`, `hour_cos` (hora cíclica)
  - `day_sin`, `day_cos` (dia da semana cíclico)
  - `speed_ratio` (velocidade atual / velocidade ideal)
  - `congestion_category` (baixo/médio/alto)
- Salva em `data/processed/`

### 4. Análise Exploratória (em desenvolvimento)

**Script:** `src/data_processing/traffic_analysis.py` (a criar)

- Gera visualizações:
  - Heatmap: congestionamento por rota e hora
  - Gráficos: velocidade média por período
  - Comparações: rush hour vs horário normal
- Identifica padrões temporais
- Salva gráficos em `data/analysis/`

### 5. Preparação para ML (em desenvolvimento)

**Script:** `src/ml_preparation/prepare_traffic_ml.py` (a criar)

- Divide dados em features (X) e targets (y)
- Duas tarefas ML:
  - **Regressão:** prever tempo de viagem
  - **Classificação:** prever nível de congestionamento
- Split treino/teste (80/20)
- Normalização de features (StandardScaler)
- Salva datasets em `data/ml_ready/`

### 6. Treinamento de Modelos (em desenvolvimento)

**Script:** `src/ml_preparation/train_traffic_models.py` (a criar)

- Treina 3 modelos:
  - Linear Regression (baseline)
  - Random Forest
  - XGBoost
- Métricas:
  - Regressão: MAE, RMSE, R²
  - Classificação: Accuracy, F1-score
- Salva modelos em `models/`
- Gera relatório de performance

### 7. Predição (futuro)

Usuário informa:
- Rota desejada
- Hora de partida
- Dia da semana

Sistema retorna:
- Tempo estimado de viagem
- Nível de congestionamento esperado
- Sugestão de melhor horário

## Estrutura de Dados

### Dados Coletados (16 campos)

```
timestamp, route_name, origin_lat, origin_lon, destination_lat, 
destination_lon, hour_of_day, day_of_week, is_rush_hour, 
api_provider, congestion_index, current_speed_kmh, 
free_flow_speed_kmh, travel_time_seconds, free_flow_time_seconds, 
delay_seconds
```

### Rotas Monitoradas

1. Centro → WEG (industrial)
2. Baependi → Centro (residencial)
3. João Pessoa → Malwee (industrial)
4. Nereu Ramos → Centro (residencial)
5. Czerniewicz → Shopping (comercial)
6. Rau → UNERJ (estudantil)
7. Vila Lalau → Centro (residencial)
8. BR-280 Sul → Norte (rodovia)

## Requisitos

### APIs
- TomTom Traffic API (2500 requisições/dia gratuitas)
- Ou Google Maps Distance Matrix API

### Python 3.8+
Principais bibliotecas:
- `requests`, `pandas`, `numpy` (coleta e processamento)
- `folium`, `geopandas` (mapas e geoespacial)
- `scikit-learn`, `xgboost` (machine learning)
- `matplotlib`, `seaborn`, `plotly` (visualização)

## Execução

### Coleta única
```bash
.venv/bin/python src/data_collection/traffic_collector.py
```

### Coleta contínua
```bash
while true; do
  .venv/bin/python src/data_collection/traffic_collector.py
  sleep 900
done
```

### Pipeline completo (quando implementado)
```bash
./run_pipeline.sh
```

## Outputs

- **CSV brutos:** `data/raw/traffic_data_*.csv`
- **Mapas:** `data/maps/traffic_map_*.html`
- **Banco de dados:** `database/traffic.db`
- **Processados:** `data/processed/` (futuro)
- **Análises:** `data/analysis/` (futuro)
- **ML-ready:** `data/ml_ready/` (futuro)
- **Modelos:** `models/` (futuro)

## Status Atual

- Coleta: **Implementado e funcional**
- Banco de dados: **Implementado**
- Processamento: **Pendente**
- Análise: **Pendente**
- ML: **Pendente**

Para ML funcional, recomenda-se coletar dados por no mínimo 1-2 semanas para ter padrões temporais suficientes.
