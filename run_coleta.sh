#!/bin/bash
# Script para executar primeira coleta de tráfego

echo "Executando primeira coleta de tráfego..."
echo "================================================"
echo ""

# Verificar se .env existe e está configurado
if [ ! -f ".env" ]; then
    echo "ERRO: Arquivo .env não encontrado!"
    exit 1
fi

# Executar coleta
.venv/bin/python src/data_collection/traffic_collector.py

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================"
    echo "Coleta concluída com sucesso!"
    echo ""
    echo "Resultados em:"
    echo "   - CSV: data/raw/traffic_*.csv"
    echo "   - Mapa: data/maps/traffic_map_*.html"
    echo ""
    echo "Abrir mapa no navegador?"
    read -p "   (s/n): " resposta
    
    if [ "$resposta" = "s" ] || [ "$resposta" = "S" ]; then
        LATEST_MAP=$(ls -t data/maps/traffic_map_*.html 2>/dev/null | head -1)
        if [ -n "$LATEST_MAP" ]; then
            echo "🌐 Abrindo $LATEST_MAP..."
            xdg-open "$LATEST_MAP" 2>/dev/null || open "$LATEST_MAP" 2>/dev/null || echo "Abra manualmente: $LATEST_MAP"
        fi
    fi
    
    echo ""
    echo "🔄 Próximos passos:"
    echo "   - Coletar mais dados (deixar rodando por dias/semanas)"
    echo "   - Importar para banco: .venv/bin/python src/database/import_traffic_to_db.py data/raw/*.csv"
    echo "   - Treinar modelos ML (depois de coletar dados históricos)"
    echo ""
else
    echo ""
    echo "Erro na coleta!"
    echo "Verifique:"
    echo "   - Chave da API está correta no .env"
    echo "   - Conexão com internet está funcionando"
    echo "   - Arquivo config/routes.json existe"
    echo ""
fi
