#!/bin/bash
# Script para executar pipeline completo da Tarefa N1

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         EXECUÇÃO COMPLETA - TAREFA N1 (ETL + EDA)          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Verificar venv
if [ ! -d ".venv" ]; then
    echo "❌ Ambiente virtual não encontrado!"
    echo "   Execute: python -m venv .venv"
    exit 1
fi

PYTHON=".venv/bin/python"

# Etapa 0: Escolher fonte de dados
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ETAPA 0: Fonte de Dados"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Escolha:"
echo "  [1] Gerar dataset completo (30 dias, ~23k registros, instantâneo)"
echo "  [2] Coletar dados via TomTom API (1 coleta, 8 rotas, ~2 min)"
echo "  [3] Usar dados existentes em data/raw/"
echo ""
read -p "Opção (1/2/3): " data_option

if [ "$data_option" = "1" ]; then
    echo ""
    echo "Gerando dataset..."
    $PYTHON scripts/generate_sample_data.py
    if [ $? -ne 0 ]; then
        echo "❌ Erro na geração de dados"
        exit 1
    fi
elif [ "$data_option" = "2" ]; then
    echo ""
    echo "Coletando dados via TomTom API..."
    $PYTHON scripts/collect_real_data.py --once
    if [ $? -ne 0 ]; then
        echo "❌ Erro na coleta de dados"
        exit 1
    fi
elif [ "$data_option" = "3" ]; then
    echo ""
    echo "ℹ️  Usando dados existentes"
else
    echo "❌ Opção inválida"
    exit 1
fi

echo ""

# Etapa 1: Auditoria
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ETAPA 1: Auditoria de Dados"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
$PYTHON src/data_processing/01_audit_data.py
if [ $? -ne 0 ]; then
    echo "❌ Erro na auditoria"
    exit 1
fi

echo ""
sleep 2

# Etapa 2: Limpeza
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ETAPA 2: Limpeza e Preparação"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
$PYTHON src/data_processing/02_clean_data.py
if [ $? -ne 0 ]; then
    echo "❌ Erro na limpeza"
    exit 1
fi

echo ""
sleep 2

# Etapa 3: Análise Exploratória
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ETAPA 3: Análise Exploratória (EDA)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
$PYTHON src/data_processing/03_exploratory_analysis.py
if [ $? -ne 0 ]; then
    echo "❌ Erro na análise exploratória"
    exit 1
fi

echo ""
sleep 2

# Resumo Final
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   ✅ PIPELINE CONCLUÍDO!                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📂 Outputs gerados:"
echo "   - Auditoria:  output/audit/"
echo "   - Limpeza:    output/cleaning/"
echo "   - EDA:        output/eda/"
echo "   - Dados:      data/processed/"
echo ""
echo "📋 Próximos passos:"
echo "   1. Revisar relatórios em output/"
echo "   2. Abrir notebook Jupyter (Etapa 4):"
echo "      jupyter notebook notebooks/04_data_storytelling.ipynb"
echo "   3. Preparar apresentação final"
echo "   4. Subir no GitHub"
echo ""
echo "Dica: Abra os relatórios .md com:"
echo "   code output/audit/RELATORIO_AUDITORIA.md"
echo "   code output/cleaning/RELATORIO_LIMPEZA.md"
echo "   code output/eda/RELATORIO_EDA.md"
echo ""
