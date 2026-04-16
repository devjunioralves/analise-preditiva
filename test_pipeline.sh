#!/bin/bash
# Script de teste rápido - Executa pipeline completo e verifica outputs

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              TESTE COMPLETO - PROJETO N1                     ║"
echo "║         Verificação de Pipeline e Outputs                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

PYTHON=".venv/bin/python"
ERRORS=0

# Função para verificar arquivo
check_file() {
    if [ -f "$1" ]; then
        echo "✅ $1"
    else
        echo "❌ FALTANDO: $1"
        ((ERRORS++))
    fi
}

# Verificar estrutura de diretórios
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  VERIFICANDO ESTRUTURA DE DIRETÓRIOS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

DIRS=("data/raw" "data/processed" "output/audit" "output/cleaning" "output/eda" "scripts" "notebooks" "src/data_collection" "src/data_processing" "src/database")

for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir/"
    else
        echo "⚠️  Criando: $dir/"
        mkdir -p "$dir"
    fi
done

echo ""

# Verificar scripts
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  VERIFICANDO SCRIPTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_file "scripts/generate_sample_data.py"
check_file "src/data_processing/01_audit_data.py"
check_file "src/data_processing/02_clean_data.py"
check_file "src/data_processing/03_exploratory_analysis.py"
check_file "notebooks/04_data_storytelling.ipynb"
check_file "run_n1.sh"

echo ""

# Verificar documentação
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  VERIFICANDO DOCUMENTAÇÃO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_file "PASSO_A_PASSO.md"
check_file "RELATORIO_EXECUTIVO_N1.md"
check_file "DOCUMENTACAO.md"

echo ""

# Executar pipeline de teste
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  EXECUTANDO PIPELINE DE TESTE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "[GERAR] Gerando dataset..."
$PYTHON scripts/generate_sample_data.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Geração de dados: OK"
else
    echo "❌ Geração de dados: FALHOU"
    ((ERRORS++))
fi

echo ""
echo "[AUDIT] Auditando dados..."
$PYTHON src/data_processing/01_audit_data.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Auditoria: OK"
else
    echo "❌ Auditoria: FALHOU"
    ((ERRORS++))
fi

echo ""
echo "🧹 Limpando dados..."
$PYTHON src/data_processing/02_clean_data.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Limpeza: OK"
else
    echo "❌ Limpeza: FALHOU"
    ((ERRORS++))
fi

echo ""
echo "[DADOS] Análise exploratória..."
$PYTHON src/data_processing/03_exploratory_analysis.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ EDA: OK"
else
    echo "❌ EDA: FALHOU"
    ((ERRORS++))
fi

echo ""

# Verificar outputs gerados
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  VERIFICANDO OUTPUTS GERADOS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "[DIR] Dados:"
DATA_CSV=$(ls data/raw/traffic_data_*.csv 2>/dev/null | head -1)
CLEAN_CSV=$(ls data/processed/traffic_data_cleaned_*.csv 2>/dev/null | head -1)

check_file "$DATA_CSV"
check_file "$CLEAN_CSV"

echo ""
echo "[INFO] Relatórios:"
check_file "output/audit/RELATORIO_AUDITORIA.md"
check_file "output/cleaning/RELATORIO_LIMPEZA.md"
check_file "output/eda/RELATORIO_EDA.md"

echo ""
echo "[DADOS] Visualizações Auditoria:"
check_file "output/audit/01_missing_values.png"
check_file "output/audit/02_outliers_boxplot.png"

echo ""
echo "[DADOS] Visualizações EDA:"
check_file "output/eda/01_estatisticas_descritivas.png"
check_file "output/eda/02_analise_temporal.png"
check_file "output/eda/03_decomposicao_temporal.png"
check_file "output/eda/04_comparacao_rotas.png"
check_file "output/eda/05_correlacao.png"
check_file "output/eda/06_heatmap_hora_rota.png"
check_file "output/eda/07_rush_hour_analysis.png"
check_file "output/eda/08_anomalias.png"

echo ""
echo "[FILE] JSONs:"
check_file "output/audit/issues.json"
check_file "output/eda/insights.json"

echo ""

# Estatísticas
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  ESTATÍSTICAS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "$DATA_CSV" ]; then
    LINES=$(wc -l < "$DATA_CSV")
    SIZE=$(du -h "$DATA_CSV" | cut -f1)
    echo "[DADOS] Dados brutos: $LINES linhas, $SIZE"
fi

if [ -f "$CLEAN_CSV" ]; then
    LINES=$(wc -l < "$CLEAN_CSV")
    SIZE=$(du -h "$CLEAN_CSV" | cut -f1)
    COLS=$(head -1 "$CLEAN_CSV" | tr ',' '\n' | wc -l)
    echo "[DADOS] Dados limpos: $LINES linhas, $COLS colunas, $SIZE"
fi

TOTAL_IMGS=$(find output/ -name "*.png" 2>/dev/null | wc -l)
echo "🖼️  Visualizações: $TOTAL_IMGS imagens"

TOTAL_MDS=$(find output/ -name "*.md" 2>/dev/null | wc -l)
echo "[INFO] Relatórios: $TOTAL_MDS documentos"

echo ""

# Resumo final
echo "╔══════════════════════════════════════════════════════════════╗"
if [ $ERRORS -eq 0 ]; then
    echo "║                    ✅ TESTE CONCLUÍDO                        ║"
    echo "║              Todos os outputs foram gerados!                 ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "🎉 PROJETO PRONTO PARA ENTREGA!"
    echo ""
    echo "[INFO] Próximos passos:"
    echo "   1. Revisar RELATORIO_EXECUTIVO_N1.md (adicionar seu nome)"
    echo "   2. Executar: jupyter notebook notebooks/04_data_storytelling.ipynb"
    echo "   3. Fazer commit no GitHub"
    echo "   4. Preparar apresentação"
    echo ""
    exit 0
else
    echo "║                 ⚠️  TESTE COM ERROS                          ║"
    echo "║            $ERRORS arquivo(s) faltando ou falha              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "❌ Corrija os erros acima e execute novamente."
    echo ""
    exit 1
fi
