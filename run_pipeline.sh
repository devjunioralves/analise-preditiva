#!/bin/bash

# Script de Automação Completa do Projeto
# Executa todas as etapas em sequência

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   PROJETO DE ANÁLISE PREDITIVA - AUTOMAÇÃO COMPLETA       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Verifica se .env existe
if [ ! -f .env ]; then
    echo "⚠️  Arquivo .env não encontrado!"
    echo "   Execute: cp .env.example .env"
    echo "   E configure sua chave da API"
    exit 1
fi

# 1. Coleta de Dados
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ETAPA 1: Coleta de Dados de Tráfego"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python src/data_collection/traffic_collector.py
if [ $? -ne 0 ]; then
    echo "❌ Erro na coleta de dados"
    exit 1
fi
echo ""

# 2. Importação de Dados
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ETAPA 2: Importação de Dados para o Banco"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python src/database/import_traffic_to_db.py data/raw/traffic_data_*.csv
if [ $? -ne 0 ]; then
    echo "❌ Erro na importação de dados"
    exit 1
fi
echo ""

# 4. Limpeza de Dados
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ETAPA 3: Limpeza e Tratamento de Dados"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python src/data_processing/clean_traffic_data.py
if [ $? -ne 0 ]; then
    echo "❌ Erro no tratamento de dados"
    exit 1
fi
echo ""

# 5. Análise Exploratória
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ETAPA 4: Análise Exploratória de Dados"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python src/data_processing/traffic_analysis.py
if [ $? -ne 0 ]; then
    echo "⚠️  Erro na análise exploratória (continuando...)"
fi
echo ""

# 6. Preparação para ML
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ETAPA 5: Preparação para Machine Learning"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python src/ml_preparation/prepare_traffic_ml.py
if [ $? -ne 0 ]; then
    echo "❌ Erro na preparação para ML"
    exit 1
fi
echo ""

# 7. Treinamento de Modelos
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ETAPA 6: Treinamento de Modelos (Opcional)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
read -p "Treinar modelos agora? (s/N): " train_models
if [ "$train_models" = "s" ] || [ "$train_models" = "S" ]; then
    python src/ml_preparation/train_traffic_models.py
fi
echo ""

# Resumo Final
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   ✅ PIPELINE COMPLETO!                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Resultados disponíveis em:"
echo "   - Dados brutos:      data/raw/"
echo "   - Dados processados: data/processed/"
echo "   - Banco de dados:    database/traffic.db"
echo "   - Mapas tráfego:     data/maps/"
echo "   - Análises:          data/analysis/"
echo "   - Dados ML-ready:    data/ml_ready/"
echo "   - Modelos treinados: models/"
echo ""
echo "📚 Documentação:"
echo "   - README.md"
echo "   - QUICK_START.md"
echo "   - docs/GUIA_COMPLETO.md"
echo "   - docs/PROCESSO.md"
echo ""
echo "🎉 Projeto concluído com sucesso!"
