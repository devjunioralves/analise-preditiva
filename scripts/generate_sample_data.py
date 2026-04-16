"""
Gerador de Dataset de Tráfego
Cria dataset para análise do projeto
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

class TrafficDataGenerator:
    """Gera dados de tráfego com padrões realistas"""
    
    def __init__(self, start_date='2026-03-01', days=30):
        self.start_date = pd.to_datetime(start_date)
        self.days = days
        self.load_routes()
        
    def load_routes(self):
        """Carrega rotas do arquivo de configuração"""
        with open('config/routes.json', 'r') as f:
            config = json.load(f)
        self.routes = config['routes']
    
    def generate_timestamp_sequence(self):
        """Gera sequência de timestamps (coleta a cada 15 minutos)"""
        timestamps = []
        current = self.start_date
        end = self.start_date + timedelta(days=self.days)
        
        while current < end:
            timestamps.append(current)
            current += timedelta(minutes=15)
        
        return timestamps
    
    def calculate_base_congestion(self, hour, day_of_week, route_type):
        """
        Calcula congestionamento base com padrões realistas
        
        Padrões:
        - Pico manhã: 6h-9h (alta)
        - Almoço: 11h-14h (média)
        - Pico tarde: 17h-20h (muito alta)
        - Noite/madrugada: baixa
        - Fim de semana: redução de 60%
        """
        # Fator dia da semana (0=segunda, 6=domingo)
        if day_of_week >= 5:  # Fim de semana
            day_factor = 0.4
        else:  # Dia útil
            day_factor = 1.0
        
        # Fator horário (curva com picos)
        if 6 <= hour < 9:  # Pico manhã
            hour_factor = 0.7 + 0.3 * np.sin((hour - 6) * np.pi / 3)
        elif 11 <= hour < 14:  # Almoço
            hour_factor = 0.5 + 0.2 * np.sin((hour - 11) * np.pi / 3)
        elif 17 <= hour < 20:  # Pico tarde (mais intenso)
            hour_factor = 0.8 + 0.4 * np.sin((hour - 17) * np.pi / 3)
        elif 0 <= hour < 6:  # Madrugada
            hour_factor = 0.1
        else:  # Outros horários
            hour_factor = 0.3
        
        # Fator tipo de rota
        route_factors = {
            'highway': 1.2,  # Rodovias mais congestionadas
            'arterial': 1.0,
            'industrial': 1.1  # Rotas industriais pico nos horários de trabalho
        }
        route_factor = route_factors.get(route_type, 1.0)
        
        # Congestionamento base (0-100%)
        base = hour_factor * day_factor * route_factor * 100
        
        return np.clip(base, 0, 100)
    
    def add_realistic_noise(self, base_value, noise_level=0.15):
        """Adiciona ruído realista aos valores"""
        noise = np.random.normal(0, noise_level * base_value)
        return base_value + noise
    
    def inject_anomalies(self, data, anomaly_rate=0.02):
        """Injeta anomalias (acidentes, eventos) nos dados"""
        n_anomalies = int(len(data) * anomaly_rate)
        anomaly_indices = np.random.choice(len(data), n_anomalies, replace=False)
        
        for idx in anomaly_indices:
            # Aumenta drasticamente o congestionamento
            data.loc[idx, 'congestion_index'] = min(95, data.loc[idx, 'congestion_index'] * 2.5)
            data.loc[idx, 'delay_seconds'] = data.loc[idx, 'delay_seconds'] * 3
            data.loc[idx, 'current_speed_kmh'] = data.loc[idx, 'current_speed_kmh'] * 0.4
        
        return data
    
    def introduce_missing_values(self, data, missing_rate=0.03):
        """Introduz valores ausentes (falhas de API, sensores)"""
        n_missing = int(len(data) * missing_rate)
        missing_indices = np.random.choice(len(data), n_missing, replace=False)
        
        # Campos que podem ter missing
        columns_to_null = ['current_speed_kmh', 'delay_seconds', 'congestion_index']
        
        for idx in missing_indices:
            col = np.random.choice(columns_to_null)
            data.loc[idx, col] = np.nan
        
        return data
    
    def generate_data(self):
        """Gera dataset completo"""
        print(f"\n{'='*60}")
        print(f"Gerando dataset de tráfego")
        print(f"Período: {self.days} dias ({self.start_date.strftime('%Y-%m-%d')} até {(self.start_date + timedelta(days=self.days)).strftime('%Y-%m-%d')})")
        print(f"{'='*60}\n")
        
        timestamps = self.generate_timestamp_sequence()
        all_data = []
        
        for route in self.routes:
            print(f"Gerando dados para: {route['name']}")
            
            for ts in timestamps:
                hour = ts.hour
                day_of_week = ts.weekday()
                
                # Congestionamento base
                congestion = self.calculate_base_congestion(
                    hour, 
                    day_of_week, 
                    route['type']
                )
                
                # Adiciona ruído
                congestion = self.add_realistic_noise(congestion, noise_level=0.15)
                congestion = np.clip(congestion, 0, 100)
                
                # Calcula velocidade baseada no congestionamento
                # Assume free_flow_speed baseado no tipo de rota
                free_flow_speeds = {'highway': 80, 'arterial': 50, 'industrial': 45}
                free_flow_speed = free_flow_speeds.get(route['type'], 50)
                
                # Velocidade diminui com congestionamento
                current_speed = free_flow_speed * (1 - congestion / 150)
                current_speed = max(10, current_speed)  # Mínimo 10 km/h
                
                # Calcula tempos de viagem
                distance_km = route.get('distance_km', 5.0)
                free_flow_time = (distance_km / free_flow_speed) * 3600  # segundos
                travel_time = (distance_km / current_speed) * 3600
                delay = travel_time - free_flow_time
                
                # Define rush hour
                is_rush_hour = (6 <= hour < 9 or 17 <= hour < 20) and day_of_week < 5
                
                record = {
                    'timestamp': ts,
                    'route_name': route['name'],
                    'origin_lat': route['origin']['lat'],
                    'origin_lon': route['origin']['lon'],
                    'destination_lat': route['destination']['lat'],
                    'destination_lon': route['destination']['lon'],
                    'hour_of_day': hour,
                    'day_of_week': day_of_week,
                    'is_rush_hour': is_rush_hour,
                    'api_provider': 'dataset',
                    'congestion_index': congestion,
                    'current_speed_kmh': current_speed,
                    'free_flow_speed_kmh': free_flow_speed,
                    'travel_time_seconds': travel_time,
                    'free_flow_time_seconds': free_flow_time,
                    'delay_seconds': delay,
                    'distance_km': distance_km
                }
                
                all_data.append(record)
        
        df = pd.DataFrame(all_data)
        
        # Introduz problemas realistas para demonstrar capacidade de tratamento
        print("\nIntroduzindo anomalias e valores ausentes...")
        df = self.inject_anomalies(df, anomaly_rate=0.02)  # 2% anomalias
        df = self.introduce_missing_values(df, missing_rate=0.03)  # 3% missing
        
        # Introduz duplicatas (2-3 registros)
        n_duplicates = 3
        duplicate_indices = np.random.choice(len(df), n_duplicates, replace=False)
        duplicates = df.iloc[duplicate_indices].copy()
        df = pd.concat([df, duplicates], ignore_index=True)
        
        # Introduz timestamps duplicados (inconsistência temporal)
        if len(df) > 10:
            df.iloc[5] = df.iloc[4].copy()  # Timestamp duplicado
        
        print(f"Total de registros gerados: {len(df)}")
        print(f"Período: {df['timestamp'].min()} a {df['timestamp'].max()}")
        print(f"Rotas: {df['route_name'].nunique()}")
        print(f"Anomalias injetadas: ~{int(len(df) * 0.02)}")
        print(f"Valores ausentes: ~{df.isnull().sum().sum()}")
        print(f"Duplicatas: {n_duplicates}")
        
        return df
    
    def save_data(self, df, output_dir='data/raw'):
        """Salva dados em CSV"""
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{output_dir}/traffic_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        
        print(f"\nDados salvos em: {filename}")
        print(f"Tamanho do arquivo: {os.path.getsize(filename) / 1024:.1f} KB")
        
        return filename


def main():
    """Função principal"""
    print("\n" + "="*60)
    print("GERADOR DE DATASET - Análise de Tráfego")
    print("="*60)
    
    # Configurações
    start_date = '2026-03-01'
    days = 30  # 1 mês de dados
    
    # Gera dados
    generator = TrafficDataGenerator(start_date=start_date, days=days)
    df = generator.generate_data()
    
    # Salva
    filename = generator.save_data(df)
    
    # Estatísticas resumidas
    print("\n" + "="*60)
    print("RESUMO DOS DADOS GERADOS")
    print("="*60)
    print(f"\nEstatísticas de Congestionamento:")
    print(df['congestion_index'].describe())
    
    print(f"\nDistribuição por Rota:")
    print(df['route_name'].value_counts())
    
    print(f"\nPeríodo de Pico:")
    print(f"  Rush hour: {df['is_rush_hour'].sum()} registros ({df['is_rush_hour'].sum()/len(df)*100:.1f}%)")
    
    print("\n" + "="*60)
    print("Dados prontos para análise")
    print("="*60)
    print(f"\nPróximos passos:")
    print(f"  1. Execute a auditoria: python src/data_processing/01_audit_data.py")
    print(f"  2. Execute o tratamento: python src/data_processing/02_clean_data.py")
    print(f"  3. Execute a EDA: python src/data_processing/03_exploratory_analysis.py")
    print(f"  4. Abra o notebook: jupyter notebook notebooks/04_data_storytelling.ipynb")


if __name__ == "__main__":
    main()
