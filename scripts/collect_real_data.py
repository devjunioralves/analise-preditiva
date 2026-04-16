#!/usr/bin/env python3
"""
Script de Coleta de Dados Reais de Tráfego via TomTom API

Coleta dados reais de tráfego das rotas configuradas em config/routes.json
usando a API do TomTom Traffic.

Uso:
    # Coleta única (1x todas as rotas)
    python scripts/collect_real_data.py --once
    
    # Coleta contínua (15 em 15 minutos)
    python scripts/collect_real_data.py --continuous
    
    # Coleta por N horas
    python scripts/collect_real_data.py --hours 24
"""

import os
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
import pandas as pd
import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
TOMTOM_API_KEY = os.getenv('TOMTOM_API_KEY')
COLLECTION_INTERVAL = int(os.getenv('COLLECTION_INTERVAL', 900))  # 15 min padrão
BASE_DIR = Path(__file__).parent.parent
ROUTES_FILE = BASE_DIR / 'config' / 'routes.json'
OUTPUT_DIR = BASE_DIR / 'data' / 'raw'


class TomTomTrafficCollector:
    """Coletor de dados de tráfego via TomTom API"""
    
    def __init__(self, api_key):
        if not api_key or api_key == 'sua_chave_tomtom_aqui':
            raise ValueError("API Key do TomTom não configurada! Configure no arquivo .env")
        
        self.api_key = api_key
        self.base_url = "https://api.tomtom.com/routing/1/calculateRoute"
        self.collected_data = []
        
    def load_routes(self):
        """Carrega rotas do arquivo de configuração"""
        with open(ROUTES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['routes']
    
    def get_route_traffic(self, route):
        """
        Faz requisição para TomTom API e obtém dados de tráfego
        
        Args:
            route: dict com informações da rota
            
        Returns:
            dict com dados coletados ou None se erro
        """
        # Montar coordenadas no formato TomTom: lat,lon:lat,lon
        origin = f"{route['origin']['lat']},{route['origin']['lon']}"
        destination = f"{route['destination']['lat']},{route['destination']['lon']}"
        
        # Endpoint completo
        url = f"{self.base_url}/{origin}:{destination}/json"
        
        # Parâmetros
        params = {
            'key': self.api_key,
            'traffic': 'true',  # Incluir dados de tráfego
            'travelMode': 'car',
            'departAt': 'now'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extrair informações relevantes
            if 'routes' in data and len(data['routes']) > 0:
                route_data = data['routes'][0]
                summary = route_data['summary']
                
                # Calcular métricas
                current_time_seconds = summary['travelTimeInSeconds']
                no_traffic_time_seconds = summary.get('trafficDelayInSeconds', 0)
                free_flow_time_seconds = current_time_seconds - no_traffic_time_seconds
                
                # Evitar divisão por zero
                if free_flow_time_seconds <= 0:
                    free_flow_time_seconds = current_time_seconds
                
                delay_seconds = current_time_seconds - free_flow_time_seconds
                
                # Calcular velocidades
                distance_km = summary['lengthInMeters'] / 1000
                current_speed_kmh = (distance_km / current_time_seconds) * 3600 if current_time_seconds > 0 else 0
                free_flow_speed_kmh = (distance_km / free_flow_time_seconds) * 3600 if free_flow_time_seconds > 0 else 0
                
                # Calcular índice de congestionamento
                if free_flow_time_seconds > 0:
                    congestion_index = min(100, (delay_seconds / free_flow_time_seconds) * 100)
                else:
                    congestion_index = 0
                
                # Timestamp
                now = datetime.now()
                
                # Detectar horário de rush (6-9h ou 17-20h)
                hour = now.hour
                is_rush_hour = (6 <= hour <= 9) or (17 <= hour <= 20)
                
                return {
                    'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
                    'route_name': route['name'],
                    'origin_lat': route['origin']['lat'],
                    'origin_lon': route['origin']['lon'],
                    'destination_lat': route['destination']['lat'],
                    'destination_lon': route['destination']['lon'],
                    'distance_km': round(distance_km, 2),
                    'current_speed_kmh': round(current_speed_kmh, 1),
                    'free_flow_speed_kmh': round(free_flow_speed_kmh, 1),
                    'travel_time_seconds': current_time_seconds,
                    'free_flow_time_seconds': free_flow_time_seconds,
                    'delay_seconds': delay_seconds,
                    'congestion_index': round(congestion_index, 1),
                    'hour_of_day': hour,
                    'day_of_week': now.weekday(),
                    'is_rush_hour': is_rush_hour
                }
            else:
                print(f"Sem dados para rota: {route['name']}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição para {route['name']}: {e}")
            return None
        except Exception as e:
            print(f"Erro ao processar {route['name']}: {e}")
            return None
    
    def collect_all_routes(self):
        """Coleta dados de todas as rotas configuradas"""
        routes = self.load_routes()
        print(f"\nColetando dados de {len(routes)} rotas...")
        
        collected_count = 0
        
        for i, route in enumerate(routes, 1):
            print(f"  [{i}/{len(routes)}] {route['name']}...", end=' ')
            
            data = self.get_route_traffic(route)
            
            if data:
                self.collected_data.append(data)
                collected_count += 1
                congestion = data['congestion_index']
                
                # Emoji baseado em congestionamento
                if congestion < 30:
                    emoji = "🟢"
                elif congestion < 60:
                    emoji = "🟡"
                else:
                    emoji = "X"
                
                print(f"{emoji} {congestion:.1f}% congestionamento")
            else:
                print("Falhou")
            
            # Aguardar 1s entre requisições para não sobrecarregar API
            if i < len(routes):
                time.sleep(1)
        
        print(f"\nColetados: {collected_count}/{len(routes)} rotas")
        return collected_count
    
    def save_to_csv(self):
        """Salva dados coletados em CSV"""
        if not self.collected_data:
            print("Nenhum dado para salvar")
            return None
        
        # Criar diretório se não existir
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = OUTPUT_DIR / f'traffic_data_{timestamp}.csv'
        
        # Criar DataFrame
        df = pd.DataFrame(self.collected_data)
        
        # Salvar
        df.to_csv(filename, index=False, encoding='utf-8')
        
        print(f"\nDados salvos: {filename}")
        print(f"   Registros: {len(df)}")
        print(f"   Colunas: {len(df.columns)}")
        
        # Estatísticas rápidas
        avg_congestion = df['congestion_index'].mean()
        max_congestion = df['congestion_index'].max()
        max_route = df.loc[df['congestion_index'].idxmax(), 'route_name']
        
        print(f"\nEstatísticas desta coleta:")
        print(f"   Congestionamento médio: {avg_congestion:.1f}%")
        print(f"   Congestionamento máximo: {max_congestion:.1f}% ({max_route})")
        
        return filename


def collect_once():
    """Executa uma coleta única"""
    print("╔════════════════════════════════════════════════════════════╗")
    print("║       COLETA ÚNICA - DADOS REAIS DE TRÁFEGO (TomTom)      ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    collector = TomTomTrafficCollector(TOMTOM_API_KEY)
    collector.collect_all_routes()
    collector.save_to_csv()
    
    print("\nColeta única concluída!")


def collect_continuous():
    """Executa coletas contínuas a cada intervalo configurado"""
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     COLETA CONTÍNUA - DADOS REAIS DE TRÁFEGO (TomTom)     ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"\n⏱Intervalo: {COLLECTION_INTERVAL} segundos ({COLLECTION_INTERVAL//60} minutos)")
    print("Pressione Ctrl+C para parar\n")
    
    collection_count = 0
    
    try:
        while True:
            collection_count += 1
            print(f"\n{'='*60}")
            print(f"COLETA #{collection_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            collector = TomTomTrafficCollector(TOMTOM_API_KEY)
            collector.collect_all_routes()
            collector.save_to_csv()
            
            print(f"\nAguardando {COLLECTION_INTERVAL//60} minutos até próxima coleta...")
            print(f"   Próxima coleta: {datetime.fromtimestamp(time.time() + COLLECTION_INTERVAL).strftime('%H:%M:%S')}")
            
            time.sleep(COLLECTION_INTERVAL)
            
    except KeyboardInterrupt:
        print(f"\n\nColeta interrompida pelo usuário")
        print(f"   Total de coletas realizadas: {collection_count}")


def collect_for_hours(hours):
    """Executa coletas por um número específico de horas"""
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   COLETA TEMPORIZADA - DADOS REAIS DE TRÁFEGO (TomTom)    ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    total_seconds = hours * 3600
    end_time = time.time() + total_seconds
    collection_count = 0
    
    print(f"\n Duração: {hours} horas")
    print(f"   Intervalo: {COLLECTION_INTERVAL//60} minutos")
    print(f"   Término previsto: {datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')}")
    print(" Pressione Ctrl+C para parar\n")
    
    try:
        while time.time() < end_time:
            collection_count += 1
            remaining = int(end_time - time.time())
            
            print(f"\n{'='*60}")
            print(f"COLETA #{collection_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Tempo restante: {remaining//3600}h {(remaining%3600)//60}min")
            print(f"{'='*60}")
            
            collector = TomTomTrafficCollector(TOMTOM_API_KEY)
            collector.collect_all_routes()
            collector.save_to_csv()
            
            if time.time() < end_time:
                print(f"\n⏳ Aguardando {COLLECTION_INTERVAL//60} minutos...")
                time.sleep(COLLECTION_INTERVAL)
        
        print(f"\n\n✅ Coleta temporizada concluída!")
        print(f"   Total de coletas: {collection_count}")
        
    except KeyboardInterrupt:
        print(f"\n\n Coleta interrompida pelo usuário")
        print(f"   Coletas realizadas: {collection_count}/{hours*60//COLLECTION_INTERVAL*60}")


def main():
    parser = argparse.ArgumentParser(
        description='Coleta dados reais de tráfego via TomTom API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Coleta única (1x)
  python scripts/collect_real_data.py --once
  
  # Coleta contínua (infinita)
  python scripts/collect_real_data.py --continuous
  
  # Coleta por 24 horas
  python scripts/collect_real_data.py --hours 24
  
  # Coleta por 7 dias
  python scripts/collect_real_data.py --hours 168
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--once', action='store_true', 
                      help='Executa uma coleta única')
    group.add_argument('--continuous', action='store_true',
                      help='Executa coletas contínuas (pressione Ctrl+C para parar)')
    group.add_argument('--hours', type=float,
                      help='Executa coletas por N horas')
    
    args = parser.parse_args()
    
    # Verificar se API key está configurada
    if not TOMTOM_API_KEY or TOMTOM_API_KEY == 'sua_chave_tomtom_aqui':
        print(" ERRO: API Key do TomTom não configurada!")
        print("\nConfigure no arquivo .env:")
        print("  TOMTOM_API_KEY=sua_chave_aqui")
        print("\nPara obter uma chave gratuita:")
        print("  https://developer.tomtom.com/")
        return 1
    
    # Executar modo selecionado
    if args.once:
        collect_once()
    elif args.continuous:
        collect_continuous()
    elif args.hours:
        collect_for_hours(args.hours)
    
    return 0


if __name__ == '__main__':
    exit(main())
