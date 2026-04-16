"""
ETAPA 2: TRATAMENTO E PREPARAÇÃO DE DADOS
Aplica técnicas de ETL para deixar dados prontos para análise

Realiza:
- Padronização do índice temporal e frequência
- Tratamento de valores ausentes, duplicatas, outliers  
- Normalização e escalonamento de variáveis
- Criação de variáveis derivadas (features engineering)
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import glob
import json

class DataCleaner:
    """Limpa e prepara dados de tráfego para análise"""
    
    def __init__(self, data_path='data/raw'):
        self.data_path = data_path
        self.df = None
        self.df_original = None
        self.log = []
        
        os.makedirs('data/processed', exist_ok=True)
        os.makedirs('output/cleaning', exist_ok=True)
    
    def log_action(self, action, details=""):
        """Registra ações de limpeza"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details
        }
        self.log.append(entry)
        print(f" {action}: {details}")
    
    def load_data(self):
        """Carrega dados brutos"""
        csv_files = glob.glob(f"{self.data_path}/traffic_data_*.csv")
        
        if not csv_files:
            raise FileNotFoundError(f"Nenhum arquivo encontrado em {self.data_path}")
        
        latest_file = max(csv_files, key=os.path.getmtime)
        print(f"\nCarregando: {latest_file}")
        
        self.df = pd.read_csv(latest_file)
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.df_original = self.df.copy()
        
        print(f" {len(self.df)} registros carregados")
        self.log_action("Dados carregados", f"{len(self.df)} registros")
        
        return self.df
    
    def remove_duplicates(self):
        """Remove duplicatas"""
        print("\n" + "="*60)
        print("REMOÇÃO DE DUPLICATAS")
        print("="*60)
        
        before = len(self.df)
        
        # Remove duplicatas completas primeiro
        self.df = self.df.drop_duplicates()
        duplicates_full = before - len(self.df)
        
        # Remove duplicatas de timestamp + rota
        self.df = self.df.drop_duplicates(subset=['timestamp', 'route_name'], keep='first')
        after = len(self.df)
        
        total_removed = before - after
        
        print(f"Duplicatas removidas: {total_removed}")
        print(f"Registros restantes: {after}")
        
        self.log_action("Duplicatas removidas", f"{total_removed} registros")
        
        return self.df
    
    def handle_missing_values(self):
        """Trata valores ausentes"""
        print("\n" + "="*60)
        print("TRATAMENTO DE VALORES AUSENTES")
        print("="*60)
        
        missing_before = self.df.isnull().sum().sum()
        
        # Estratégia por tipo de coluna
        numeric_cols = ['congestion_index', 'current_speed_kmh', 'travel_time_seconds', 
                       'delay_seconds', 'free_flow_speed_kmh', 'free_flow_time_seconds']
        
        for col in numeric_cols:
            if col not in self.df.columns:
                continue
                
            missing_count = self.df[col].isnull().sum()
            
            if missing_count == 0:
                continue
            
            missing_pct = (missing_count / len(self.df)) * 100
            
            # Ordenar por timestamp para interpolação temporal correta
            self.df = self.df.sort_values(['route_name', 'timestamp'])
            
            if missing_pct < 5:
                # Interpolação linear para valores próximos
                self.df[col] = self.df.groupby('route_name')[col].transform(
                    lambda x: x.interpolate(method='linear', limit_direction='both')
                )
                print(f" {col}: Interpolação linear ({missing_count} valores)")
                self.log_action(f"Interpolação: {col}", f"{missing_count} valores")
                
            elif missing_pct < 15:
                # Forward fill + backward fill para gaps maiores
                self.df[col] = self.df.groupby('route_name')[col].transform(
                    lambda x: x.fillna(method='ffill').fillna(method='bfill')
                )
                print(f" {col}: Forward/Backward fill ({missing_count} valores)")
                self.log_action(f"Forward/Backward fill: {col}", f"{missing_count} valores")
                
            else:
                # Mediana por rota e hora
                self.df[col] = self.df.groupby(['route_name', 'hour_of_day'])[col].transform(
                    lambda x: x.fillna(x.median())
                )
                print(f" {col}: Mediana por rota/hora ({missing_count} valores)")
                self.log_action(f"Mediana: {col}", f"{missing_count} valores")
        
        missing_after = self.df.isnull().sum().sum()
        
        print(f"\nMissing antes: {missing_before}")
        print(f"Missing depois: {missing_after}")
        print(f"Resolvidos: {missing_before - missing_after}")
        
        return self.df
    
    def handle_outliers(self):
        """Trata outliers usando Winsorization"""
        print("\n" + "="*60)
        print("TRATAMENTO DE OUTLIERS")
        print("="*60)
        
        numeric_cols = ['congestion_index', 'current_speed_kmh', 'travel_time_seconds', 'delay_seconds']
        
        for col in numeric_cols:
            if col not in self.df.columns:
                continue
            
            # Calcular bounds
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Contar outliers
            outliers_count = ((self.df[col] < lower_bound) | (self.df[col] > upper_bound)).sum()
            
            if outliers_count > 0:
                # Winsorization - substituir por percentis 5 e 95
                p5 = self.df[col].quantile(0.05)
                p95 = self.df[col].quantile(0.95)
                
                self.df[col] = self.df[col].clip(lower=p5, upper=p95)
                
                print(f" {col}: {outliers_count} outliers tratados")
                print(f"   Range: [{p5:.2f}, {p95:.2f}]")
                
                self.log_action(f"Outliers tratados: {col}", 
                              f"{outliers_count} valores winsorized (p5={p5:.2f}, p95={p95:.2f})")
        
        return self.df
    
    def standardize_temporal_index(self):
        """Padroniza índice temporal"""
        print("\n" + "="*60)
        print("PADRONIZAÇÃO DO ÍNDICE TEMPORAL")
        print("="*60)
        
        # Ordenar por timestamp
        self.df = self.df.sort_values(['route_name', 'timestamp'])
        
        # Verificar frequência
        freq_mode = self.df.groupby('route_name')['timestamp'].diff().mode()[0]
        print(f" Frequência detectada: {freq_mode}")
        
        # Resetar index
        self.df = self.df.reset_index(drop=True)
        
        print(f" Índice padronizado")
        self.log_action("Índice temporal padronizado", f"Frequência: {freq_mode}")
        
        return self.df
    
    def create_derived_features(self):
        """Cria variáveis derivadas (Feature Engineering)"""
        print("\n" + "="*60)
        print("CRIAÇÃO DE VARIÁVEIS DERIVADAS")
        print("="*60)
        
        features_created = []
        
        # 1. Média móvel de congestionamento (janela 4 períodos = 1 hora)
        self.df['congestion_ma_1h'] = self.df.groupby('route_name')['congestion_index'].transform(
            lambda x: x.rolling(window=4, min_periods=1).mean()
        )
        features_created.append("congestion_ma_1h: Média móvel 1 hora")
        print(" congestion_ma_1h (média móvel 1 hora)")
        
        # 2. Variação percentual de velocidade
        self.df['speed_variation_pct'] = (
            (self.df['free_flow_speed_kmh'] - self.df['current_speed_kmh']) / 
            self.df['free_flow_speed_kmh'] * 100
        )
        features_created.append("speed_variation_pct: Variação % velocidade")
        print(" speed_variation_pct (variação % velocidade)")
        
        # 3. Razão de velocidade (speed ratio)
        self.df['speed_ratio'] = self.df['current_speed_kmh'] / self.df['free_flow_speed_kmh']
        features_created.append("speed_ratio: Razão velocidade atual/ideal")
        print(" speed_ratio (atual/ideal)")
        
        # 4. Categoria de congestionamento
        def categorize_congestion(value):
            if value < 30:
                return 'baixo'
            elif value < 60:
                return 'moderado'
            else:
                return 'alto'
        
        self.df['congestion_category'] = self.df['congestion_index'].apply(categorize_congestion)
        features_created.append("congestion_category: Categorias (baixo/moderado/alto)")
        print(" congestion_category (baixo/moderado/alto)")
        
        # 5. Hora do dia em formato cíclico (sin/cos)
        self.df['hour_sin'] = np.sin(2 * np.pi * self.df['hour_of_day'] / 24)
        self.df['hour_cos'] = np.cos(2 * np.pi * self.df['hour_of_day'] / 24)
        features_created.append("hour_sin/hour_cos: Hora cíclica")
        print(" hour_sin/hour_cos (representação cíclica da hora)")
        
        # 6. Dia da semana em formato cíclico
        self.df['day_sin'] = np.sin(2 * np.pi * self.df['day_of_week'] / 7)
        self.df['day_cos'] = np.cos(2 * np.pi * self.df['day_of_week'] / 7)
        features_created.append("day_sin/day_cos: Dia semana cíclico")
        print(" day_sin/day_cos (representação cíclica do dia)")
        
        # 7. Atraso por km (delay_per_km)
        self.df['delay_per_km'] = self.df['delay_seconds'] / self.df['distance_km']
        features_created.append("delay_per_km: Atraso normalizado por distância")
        print(" delay_per_km (atraso/km)")
        
        # 8. Flag fim de semana
        self.df['is_weekend'] = (self.df['day_of_week'] >= 5).astype(int)
        features_created.append("is_weekend: Indicador fim de semana")
        print(" is_weekend (0/1)")
        
        print(f"\nTotal de features criadas: {len(features_created)}")
        
        for feat in features_created:
            self.log_action("Feature criada", feat)
        
        return self.df
    
    def normalize_features(self):
        """Normaliza variáveis numéricas"""
        print("\n" + "="*60)
        print("NORMALIZAÇÃO DE VARIÁVEIS")
        print("="*60)
        
        # Variáveis para normalizar (StandardScaler - média 0, desvio 1)
        scale_cols = ['congestion_index', 'congestion_ma_1h', 'current_speed_kmh', 
                     'travel_time_seconds', 'delay_seconds', 'delay_per_km',
                      'speed_ratio', 'speed_variation_pct']
        
        scale_cols = [col for col in scale_cols if col in self.df.columns]
        
        scaler = StandardScaler()
        
        # Criar versões normalizadas
        for col in scale_cols:
            scaled_col = f"{col}_scaled"
            self.df[scaled_col] = scaler.fit_transform(self.df[[col]])
            print(f" {col} → {scaled_col}")
            self.log_action("Normalização", f"{col} → StandardScaler")
        
        print(f"\n{len(scale_cols)} variáveis normalizadas")
        
        return self.df
    
    def save_cleaned_data(self):
        """Salva dados limpos"""
        print("\n" + "="*60)
        print("SALVANDO DADOS PROCESSADOS")
        print("="*60)
        
        # Salvar CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/processed/traffic_data_cleaned_{timestamp}.csv"
        self.df.to_csv(filename, index=False)
        
        print(f" CSV salvo: {filename}")
        print(f" Tamanho: {os.path.getsize(filename) / 1024:.1f} KB")
        print(f" Registros: {len(self.df)}")
        print(f" Colunas: {len(self.df.columns)}")
        
        # Salvar log
        log_file = f"output/cleaning/cleaning_log_{timestamp}.json"
        with open(log_file, 'w') as f:
            json.dump(self.log, f, indent=2)
        
        print(f" Log salvo: {log_file}")
        
        # Gerar comparação antes/depois
        comparison = {
            'original': {
                'registros': len(self.df_original),
                'colunas': len(self.df_original.columns),
                'missing_values': int(self.df_original.isnull().sum().sum())
            },
            'cleaned': {
                'registros': len(self.df),
                'colunas': len(self.df.columns),
                'missing_values': int(self.df.isnull().sum().sum())
            },
            'changes': {
                'registros_removidos': len(self.df_original) - len(self.df),
                'colunas_adicionadas': len(self.df.columns) - len(self.df_original.columns),
                'missing_resolvidos': int(self.df_original.isnull().sum().sum() - self.df.isnull().sum().sum())
            }
        }
        
        comparison_file = f"output/cleaning/comparison_{timestamp}.json"
        with open(comparison_file, 'w') as f:
            json.dump(comparison, f, indent=2)
        
        print(f" Comparação salva: {comparison_file}")
        
        return filename
    
    def generate_cleaning_report(self):
        """Gera relatório de limpeza"""
        report_lines = []
        report_lines.append("# RELATÓRIO DE LIMPEZA E PREPARAÇÃO DE DADOS")
        report_lines.append(f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        report_lines.append("---\n")
        
        report_lines.append("## Resumo das Ações\n")
        
        # Agrupar ações por tipo
        actions_by_type = {}
        for entry in self.log:
            action_type = entry['action'].split(':')[0]
            if action_type not in actions_by_type:
                actions_by_type[action_type] = []
            actions_by_type[action_type].append(entry)
        
        for action_type, entries in actions_by_type.items():
            report_lines.append(f"### {action_type}")
            for entry in entries:
                report_lines.append(f"- {entry['details']}")
            report_lines.append("")
        
        report_lines.append("\n## Comparação Antes/Depois\n")
        report_lines.append(f"| Métrica | Original | Limpo | Diferença |")
        report_lines.append(f"|---------|----------|-------|-----------|")
        report_lines.append(f"| Registros | {len(self.df_original):,} | {len(self.df):,} | {len(self.df) - len(self.df_original):+,} |")
        report_lines.append(f"| Colunas | {len(self.df_original.columns)} | {len(self.df.columns)} | {len(self.df.columns) - len(self.df_original.columns):+} |")
        report_lines.append(f"| Missing | {self.df_original.isnull().sum().sum()} | {self.df.isnull().sum().sum()} | {self.df.isnull().sum().sum() - self.df_original.isnull().sum().sum():+} |")
        
        report_lines.append("\n## Novas Features Criadas\n")
        new_cols = set(self.df.columns) - set(self.df_original.columns)
        for col in sorted(new_cols):
            report_lines.append(f"- `{col}`")
        
        # Salvar relatório
        report_path = 'output/cleaning/RELATORIO_LIMPEZA.md'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
        
        print(f" Relatório salvo: {report_path}")
    
    def run_full_cleaning(self):
        """Executa pipeline completo de limpeza"""
        print("\n" + "="*70)
        print(" "*20 + "LIMPEZA E PREPARAÇÃO DE DADOS")
        print("="*70)
        
        self.load_data()
        self.remove_duplicates()
        self.handle_missing_values()
        self.handle_outliers()
        self.standardize_temporal_index()
        self.create_derived_features()
        self.normalize_features()
        filename = self.save_cleaned_data()
        self.generate_cleaning_report()
        
        print("\n" + "="*70)
        print("✅ LIMPEZA CONCLUÍDA!")
        print("="*70)
        print(f"\nDados limpos: {filename}")
        print(f"{len(self.df)} registros | {len(self.df.columns)} colunas")
        print(f"\nPróximo passo: Execute a análise exploratória")
        print(f"   python src/data_processing/03_exploratory_analysis.py")


if __name__ == "__main__":
    cleaner = DataCleaner()
    cleaner.run_full_cleaning()
