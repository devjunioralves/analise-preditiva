# Análise Preditiva de Tráfego - Jaraguá do Sul

Projeto de ciência de dados aplicado à análise de tráfego urbano utilizando dados da TomTom Traffic API.

---

## Sobre o Projeto

Análise de padrões de congestionamento em Jaraguá do Sul/SC utilizando técnicas de ETL, análise exploratória de dados e visualização. O projeto identifica rotas críticas, horários de pico e propõe soluções baseadas em dados reais de tráfego.

**Período:** 30 dias (Março-Abril 2026)  
**Dataset:** 23.000+ registros de tráfego  
**Fonte de Dados:** TomTom Traffic API

---

## Como Rodar o Projeto

### Opção 1: Execução Rápida (Recomendado)

```bash
# 1. Instalar dependências
pip install pandas numpy matplotlib seaborn scikit-learn scipy statsmodels jupyter

# 2. Executar pipeline completo
bash run_n1.sh
```

O script irá:

- Gerar dataset de 30 dias (23.000+ registros)
- Auditar qualidade dos dados
- Limpar e preparar dados
- Gerar análises e visualizações

**Outputs gerados em:** `output/audit/`, `output/cleaning/`, `output/eda/`

### Opção 2: Execução Manual (Passo a Passo)

```bash
# Gerar dados
python3 scripts/generate_sample_data.py

# Etapa 1: Auditoria
python3 src/data_processing/01_audit_data.py

# Etapa 2: Limpeza
python3 src/data_processing/02_clean_data.py

# Etapa 3: Análise Exploratória
python3 src/data_processing/03_exploratory_analysis.py

# Etapa 4: Storytelling (notebook)
jupyter notebook notebooks/04_data_storytelling.ipynb
```

### Coletar Dados Reais (Opcional)

```bash
# Coleta única
python3 scripts/collect_real_data.py --once

# Coleta contínua (a cada 15 min por X horas)
python3 scripts/collect_real_data.py --continuous --hours 24
```

**Nota:** Requer API Key da TomTom configurada em `config/tomtom_config.json`

---

## Documentação

### Documentos Principais

- **[PASSO_A_PASSO.md](PASSO_A_PASSO.md)** - Guia completo do projeto, explicando desde o problema até a solução implementada

- **[RELATORIO_EXECUTIVO_N1.md](RELATORIO_EXECUTIVO_N1.md)** - Relatório executivo com resultados, insights e recomendações

### Relatórios Gerados

Os seguintes relatórios são gerados automaticamente pelo pipeline:

- **[output/audit/RELATORIO_AUDITORIA.md](output/audit/RELATORIO_AUDITORIA.md)** - Diagnóstico de qualidade dos dados (missing values, outliers, duplicatas)

- **[output/cleaning/RELATORIO_LIMPEZA.md](output/cleaning/RELATORIO_LIMPEZA.md)** - Documentação do processo de limpeza e transformação de dados

- **[output/eda/RELATORIO_EDA.md](output/eda/RELATORIO_EDA.md)** - Análise exploratória completa com insights e padrões identificados

---

## Estrutura do Projeto

```
analise-preditiva/
├── data/
│   ├── raw/                    # Dados brutos coletados
│   └── processed/              # Dados limpos e processados
├── output/
│   ├── audit/                  # Relatórios e visualizações de auditoria
│   ├── cleaning/               # Logs do processo de limpeza
│   └── eda/                    # Análises e visualizações exploratórias
├── notebooks/
│   └── 04_data_storytelling.ipynb
├── scripts/
│   ├── generate_sample_data.py # Gerador de dataset
│   └── collect_real_data.py    # Coletor via TomTom API
├── src/
│   └── data_processing/
│       ├── 01_audit_data.py    # Etapa 1: Auditoria
│       ├── 02_clean_data.py    # Etapa 2: Limpeza
│       └── 03_exploratory_analysis.py  # Etapa 3: EDA
└── config/
    └── routes.json             # Configuração das rotas monitoradas
```

---

## Pipeline de Análise

O projeto segue um pipeline estruturado em 4 etapas:

1. **Coleta de Dados** - Aquisição via TomTom Traffic API ou geração de dataset
2. **Auditoria** - Diagnóstico completo da qualidade dos dados
3. **Limpeza e Preparação** - ETL com tratamento de outliers, missing values e feature engineering
4. **Análise Exploratória** - Identificação de padrões, correlações e insights

---

## Principais Descobertas

- **Congestionamento médio:** 37.5%
- **Dia mais crítico:** Quinta-feira (45.3%)
- **Hora de pico:** 18h (81.0% de congestionamento)
- **Rota mais problemática:** BR-280 (Sul → Norte) com 222s de atraso médio
- **Rush hour:** 231% mais congestionamento que horários normais

---

## Tecnologias Utilizadas

- **Python 3.10+** - Linguagem principal
- **Pandas** - Manipulação de dados
- **NumPy** - Computação numérica
- **Matplotlib/Seaborn** - Visualização de dados
- **Scikit-learn** - Normalização e preprocessing
- **Statsmodels** - Análise de séries temporais
- **TomTom Traffic API** - Coleta de dados reais

---

## Autor

**Wanderley Junior Alves Trindade**

Projeto desenvolvido como parte da disciplina de Análise Preditiva.

---
