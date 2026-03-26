# Projeto de Análise Preditiva - Tráfego Urbano 🚗

## 📋 Descrição do Projeto

Este projeto realiza a coleta, armazenamento e tratamento de dados de tráfego urbano para treinar modelos de aprendizado de máquina com foco em previsão de congestionamentos, tempo de viagem e análise de mobilidade urbana.

## 🎯 Caso Escolhido: Análise de Tráfego e Mobilidade Urbana

### Tema
Análise e previsão de condições de tráfego incluindo tempo de viagem, velocidade média, incidentes, congestionamentos e padrões de mobilidade urbana em São Paulo.

### Fonte de Dados
- **API**: TomTom Traffic API / Google Maps Distance Matrix API
- **Dados Complementares**: Waze Alerts, OpenStreetMap
- **Tipo**: Dados em tempo real de tráfego
- **Formato**: JSON

### Variáveis Dependentes do Tempo
- Tempo de Viagem (minutos)
- Velocidade Média (km/h)
- Índice de Congestionamento (0-100)
- Acidentes/Incidentes (quantidade e localização)
- Volume de Tráfego (veículos/hora)
- Fluxo vs Capacidade da Via (%)

## 🏗️ Estrutura do Projeto

```
analise-preditiva/
├── README.md                 # Documentação principal
├── requirements.txt          # Dependências Python
├── config/
│   └── routes.json          # Rotas monitoradas
├── src/
│   ├── data_collection/     # Scripts de coleta de tráfego
│   ├── database/            # Configuração e conexão com BD
│   ├── data_processing/     # Limpeza e tratamento de dados
│   ├── geospatial/          # Análise geoespacial
│   └── ml_preparation/      # Preparação para ML
├── data/
│   ├── raw/                 # Dados brutos de tráfego
│   ├── processed/           # Dados processados
│   └── maps/                # Mapas e visualizações
├── notebooks/               # Jupyter notebooks para análise
└── docs/                    # Documentação adicional
```

## 🚀 Como Executar

### 1. Instalação de Dependências
```bash
pip install -r requirements.txt
```

### 2. Configuração
- Obtenha uma chave API gratuita em: https://developer.tomtom.com/ (ou Google Maps)
- Configure a chave no arquivo `.env`
- Defina rotas de interesse no arquivo `config/routes.json`

### 3. Coleta de Dados de Tráfego
```bash
python src/data_collection/traffic_collector.py
```

### 4. Armazenamento no Banco de Dados
```bash
python src/database/setup_database.py
```

### 5. Tratamento de Dados
```bash
python src/data_processing/clean_data.py
```

## 📊 Banco de Dados

**Tipo**: PostgreSQL (SQL) + PostGIS (Dados Geoespaciais) ou SQLite

### Esquema SQL
- Tabela `traffic_data`: dados de tráfego em tempo real
- Tabela `routes`: rotas monitoradas (origem-destino)
- Tabela `incidents`: acidentes e eventos
- Tabela `historical_patterns`: padrões históricos

### Extensão Geoespacial (PostGIS)
- Armazena coordenadas geográficas
- Permite consultas espaciais (distância, proximidade)
- Visualização de mapas de calor

## 📈 Análise e ML

O conjunto de dados preparado pode ser usado para:
- **Previsão de Tempo de Viagem**: Prever quanto tempo levará de A para B
- **Detecção de Congestionamentos**: Identificar padrões de tráfego intenso
- **Classificação de Rotas**: Melhor rota em tempo real
- **Análise de Incidentes**: Prever probabilidade de acidentes
- **Otimização de Trajetos**: Rotas alternativas inteligentes
- **Padrões Temporais**: Rush hour, fins de semana, eventos

## 📝 Documentação Completa

Consulte a pasta `docs/` para documentação detalhada sobre:
- Processo de coleta de dados
- Estrutura do banco de dados
- Desafios encontrados e soluções
- Guia de análise exploratória

## 👨‍💻 Autor

Junior Trindade

## 📅 Data

Março de 2026
