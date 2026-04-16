"""
ETAPA 3: ANÁLISE EXPLORATÓRIA DE DADOS (EDA)
Realiza análise profunda dos dados limpos para identificar padrões, tendências e insights

Inclui:
- Estatísticas descritivas completas
- Visualizações de séries temporais
- Decomposição temporal (tendência, sazonalidade, resíduo)
- Análise de correlação
- Padrões por rota, dia e hora
- Heatmaps e dashboards
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import glob
import json
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose
import warnings
warnings.filterwarnings('ignore')

# Configuração de estilo
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10

class TrafficEDA:
    """Análise Exploratória de Dados de Tráfego"""
    
    def __init__(self, data_path='data/processed'):
        self.data_path = data_path
        self.df = None
        self.insights = []
        
        os.makedirs('output/eda', exist_ok=True)
    
    def add_insight(self, category, insight):
        """Registra descobertas importantes"""
        self.insights.append({
            'category': category,
            'insight': insight,
            'timestamp': datetime.now().isoformat()
        })
        print(f"Insight - {category}: {insight}")
    
    def load_data(self):
        """Carrega dados processados"""
        csv_files = glob.glob(f"{self.data_path}/traffic_data_cleaned_*.csv")
        
        if not csv_files:
            raise FileNotFoundError(f"Nenhum arquivo limpo encontrado em {self.data_path}")
        
        latest_file = max(csv_files, key=os.path.getmtime)
        print(f"\nCarregando: {latest_file}")
        
        self.df = pd.read_csv(latest_file)
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        
        print(f" {len(self.df)} registros carregados")
        print(f" Período: {self.df['timestamp'].min()} a {self.df['timestamp'].max()}")
        
        return self.df
    
    def descriptive_statistics(self):
        """Estatísticas descritivas completas"""
        print("\n" + "="*70)
        print("ESTATÍSTICAS DESCRITIVAS")
        print("="*70)
        
        # Estatísticas numéricas
        numeric_cols = ['congestion_index', 'current_speed_kmh', 'travel_time_seconds', 
                       'delay_seconds', 'speed_ratio', 'delay_per_km']
        
        stats_df = self.df[numeric_cols].describe()
        
        print("\nResumo Estatístico:")
        print(stats_df.round(2))
        
        # Insights
        mean_congestion = self.df['congestion_index'].mean()
        max_congestion = self.df['congestion_index'].max()
        
        self.add_insight("Estatísticas", 
                        f"Congestionamento médio: {mean_congestion:.1f}% (máx: {max_congestion:.1f}%)")
        
        # Salvar tabela
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.axis('tight')
        ax.axis('off')
        
        table_data = stats_df.round(2).reset_index()
        table = ax.table(cellText=table_data.values,
                        colLabels=table_data.columns,
                        cellLoc='center',
                        loc='center',
                        bbox=[0, 0, 1, 1])
        
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # Colorir header
        for i in range(len(table_data.columns)):
            table[(0, i)].set_facecolor('#4472C4')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        plt.title('Estatísticas Descritivas - Métricas de Tráfego', 
                 fontsize=14, weight='bold', pad=20)
        plt.savefig('output/eda/01_estatisticas_descritivas.png', 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        print(" Salvo: output/eda/01_estatisticas_descritivas.png")
    
    def temporal_analysis(self):
        """Análise de séries temporais"""
        print("\n" + "="*70)
        print("ANÁLISE TEMPORAL")
        print("="*70)
        
        fig, axes = plt.subplots(3, 1, figsize=(16, 12))
        
        # 1. Série temporal completa
        daily_avg = self.df.groupby(self.df['timestamp'].dt.date)['congestion_index'].mean()
        
        axes[0].plot(daily_avg.index, daily_avg.values, 
                    linewidth=2, color='#E74C3C', marker='o', markersize=4)
        axes[0].set_title('Congestionamento Médio Diário - 30 Dias', 
                         fontsize=12, weight='bold')
        axes[0].set_ylabel('Congestionamento (%)')
        axes[0].grid(True, alpha=0.3)
        axes[0].axhline(y=daily_avg.mean(), color='green', 
                       linestyle='--', label=f'Média: {daily_avg.mean():.1f}%')
        axes[0].legend()
        
        # 2. Padrão semanal
        weekly_pattern = self.df.groupby('day_of_week')['congestion_index'].mean()
        days = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
        
        axes[1].bar(range(7), weekly_pattern.values, color='#3498DB', alpha=0.7)
        axes[1].set_xticks(range(7))
        axes[1].set_xticklabels(days)
        axes[1].set_title('Padrão Semanal de Congestionamento', 
                         fontsize=12, weight='bold')
        axes[1].set_ylabel('Congestionamento (%)')
        axes[1].grid(True, axis='y', alpha=0.3)
        
        # 3. Padrão horário
        hourly_pattern = self.df.groupby('hour_of_day')['congestion_index'].mean()
        
        axes[2].plot(hourly_pattern.index, hourly_pattern.values, 
                    linewidth=2.5, color='#9B59B6', marker='s', markersize=6)
        axes[2].fill_between(hourly_pattern.index, hourly_pattern.values, 
                            alpha=0.3, color='#9B59B6')
        axes[2].set_title('Padrão Horário de Congestionamento (24h)', 
                         fontsize=12, weight='bold')
        axes[2].set_xlabel('Hora do Dia')
        axes[2].set_ylabel('Congestionamento (%)')
        axes[2].set_xticks(range(0, 24, 2))
        axes[2].grid(True, alpha=0.3)
        
        # Destacar rush hours
        axes[2].axvspan(6, 9, alpha=0.2, color='orange', label='Rush Manhã')
        axes[2].axvspan(17, 20, alpha=0.2, color='red', label='Rush Tarde')
        axes[2].legend()
        
        plt.tight_layout()
        plt.savefig('output/eda/02_analise_temporal.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(" Salvo: output/eda/02_analise_temporal.png")
        
        # Insights
        peak_day = days[weekly_pattern.idxmax()]
        peak_hour = hourly_pattern.idxmax()
        
        self.add_insight("Temporal", 
                        f"Dia mais crítico: {peak_day} ({weekly_pattern.max():.1f}%)")
        self.add_insight("Temporal", 
                        f"Hora de pico: {peak_hour}h ({hourly_pattern.max():.1f}%)")
    
    def decomposition_analysis(self):
        """Decomposição de série temporal"""
        print("\n" + "="*70)
        print("DECOMPOSIÇÃO TEMPORAL")
        print("="*70)
        
        # Preparar série temporal com frequência regular
        ts_data = self.df.groupby(self.df['timestamp'].dt.date)['congestion_index'].mean()
        ts_data.index = pd.to_datetime(ts_data.index)
        
        # Decomposição
        decomposition = seasonal_decompose(ts_data, model='additive', period=7)
        
        fig, axes = plt.subplots(4, 1, figsize=(16, 12))
        
        # Original
        axes[0].plot(decomposition.observed, linewidth=2, color='#2C3E50')
        axes[0].set_title('Série Original', fontsize=12, weight='bold')
        axes[0].set_ylabel('Congestionamento (%)')
        axes[0].grid(True, alpha=0.3)
        
        # Tendência
        axes[1].plot(decomposition.trend, linewidth=2, color='#E74C3C')
        axes[1].set_title('Tendência', fontsize=12, weight='bold')
        axes[1].set_ylabel('Tendência')
        axes[1].grid(True, alpha=0.3)
        
        # Sazonalidade
        axes[2].plot(decomposition.seasonal, linewidth=2, color='#3498DB')
        axes[2].set_title('Sazonalidade (Semanal)', fontsize=12, weight='bold')
        axes[2].set_ylabel('Sazonalidade')
        axes[2].grid(True, alpha=0.3)
        
        # Resíduo
        axes[3].plot(decomposition.resid, linewidth=1, color='#95A5A6', alpha=0.7)
        axes[3].set_title('Resíduo (Ruído)', fontsize=12, weight='bold')
        axes[3].set_xlabel('Data')
        axes[3].set_ylabel('Resíduo')
        axes[3].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('output/eda/03_decomposicao_temporal.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(" Salvo: output/eda/03_decomposicao_temporal.png")
        
        # Insight sobre tendência
        trend_change = decomposition.trend.dropna().iloc[-1] - decomposition.trend.dropna().iloc[0]
        trend_direction = "crescente" if trend_change > 0 else "decrescente"
        
        self.add_insight("Decomposição", 
                        f"Tendência {trend_direction} de {abs(trend_change):.1f}% no período")
    
    def route_comparison(self):
        """Comparação entre rotas"""
        print("\n" + "="*70)
        print("COMPARAÇÃO ENTRE ROTAS")
        print("="*70)
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Boxplot de congestionamento por rota
        route_data = [self.df[self.df['route_name'] == route]['congestion_index'].values 
                     for route in self.df['route_name'].unique()]
        
        bp = axes[0, 0].boxplot(route_data, labels=self.df['route_name'].unique(), 
                                patch_artist=True)
        
        for patch in bp['boxes']:
            patch.set_facecolor('#3498DB')
            patch.set_alpha(0.6)
        
        axes[0, 0].set_title('Distribuição de Congestionamento por Rota', 
                            fontsize=12, weight='bold')
        axes[0, 0].set_ylabel('Congestionamento (%)')
        axes[0, 0].tick_params(axis='x', rotation=45)
        axes[0, 0].grid(True, axis='y', alpha=0.3)
        
        # 2. Velocidade média por rota
        speed_by_route = self.df.groupby('route_name')['current_speed_kmh'].mean().sort_values()
        
        axes[0, 1].barh(range(len(speed_by_route)), speed_by_route.values, 
                       color='#2ECC71', alpha=0.7)
        axes[0, 1].set_yticks(range(len(speed_by_route)))
        axes[0, 1].set_yticklabels(speed_by_route.index, fontsize=9)
        axes[0, 1].set_title('Velocidade Média por Rota', fontsize=12, weight='bold')
        axes[0, 1].set_xlabel('Velocidade (km/h)')
        axes[0, 1].grid(True, axis='x', alpha=0.3)
        
        # 3. Atraso médio por rota
        delay_by_route = self.df.groupby('route_name')['delay_seconds'].mean().sort_values(ascending=False)
        
        colors = ['#E74C3C' if x > delay_by_route.mean() else '#F39C12' 
                 for x in delay_by_route.values]
        
        axes[1, 0].bar(range(len(delay_by_route)), delay_by_route.values, 
                      color=colors, alpha=0.7)
        axes[1, 0].set_xticks(range(len(delay_by_route)))
        axes[1, 0].set_xticklabels([r.split('→')[0][:10] for r in delay_by_route.index], 
                                  rotation=45, ha='right', fontsize=9)
        axes[1, 0].set_title('Atraso Médio por Rota', fontsize=12, weight='bold')
        axes[1, 0].set_ylabel('Atraso (segundos)')
        axes[1, 0].axhline(y=delay_by_route.mean(), color='red', 
                          linestyle='--', linewidth=2, label='Média')
        axes[1, 0].legend()
        axes[1, 0].grid(True, axis='y', alpha=0.3)
        
        # 4. Frequência de congestionamento alto (>60%) por rota
        high_congestion = self.df[self.df['congestion_index'] > 60]
        freq_by_route = high_congestion.groupby('route_name').size().sort_values(ascending=False)
        
        axes[1, 1].barh(range(len(freq_by_route)), freq_by_route.values, 
                       color='#9B59B6', alpha=0.7)
        axes[1, 1].set_yticks(range(len(freq_by_route)))
        axes[1, 1].set_yticklabels([r.split('→')[0][:15] for r in freq_by_route.index], 
                                  fontsize=9)
        axes[1, 1].set_title('Ocorrências de Congestionamento Alto (>60%)', 
                            fontsize=12, weight='bold')
        axes[1, 1].set_xlabel('Número de Ocorrências')
        axes[1, 1].grid(True, axis='x', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('output/eda/04_comparacao_rotas.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(" Salvo: output/eda/04_comparacao_rotas.png")
        
        # Insights
        worst_route = delay_by_route.index[0]
        best_route = speed_by_route.index[-1]
        
        self.add_insight("Rotas", 
                        f"Rota mais problemática: {worst_route} ({delay_by_route.iloc[0]:.0f}s atraso)")
        self.add_insight("Rotas", 
                        f"Rota mais fluida: {best_route} ({speed_by_route.iloc[-1]:.1f} km/h)")
    
    def correlation_analysis(self):
        """Análise de correlação"""
        print("\n" + "="*70)
        print("ANÁLISE DE CORRELAÇÃO")
        print("="*70)
        
        # Selecionar variáveis numéricas relevantes
        corr_cols = ['congestion_index', 'current_speed_kmh', 'travel_time_seconds', 
                    'delay_seconds', 'speed_ratio', 'hour_of_day', 'day_of_week',
                    'is_rush_hour', 'is_weekend']
        
        corr_cols = [col for col in corr_cols if col in self.df.columns]
        corr_matrix = self.df[corr_cols].corr()
        
        # Heatmap
        fig, ax = plt.subplots(figsize=(12, 10))
        
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        
        sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', 
                   cmap='RdYlGn_r', center=0, square=True, linewidths=1,
                   cbar_kws={"shrink": 0.8}, ax=ax)
        
        ax.set_title('Matriz de Correlação - Variáveis de Tráfego', 
                    fontsize=14, weight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig('output/eda/05_correlacao.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(" Salvo: output/eda/05_correlacao.png")
        
        # Top correlações com congestionamento
        congestion_corr = corr_matrix['congestion_index'].sort_values(ascending=False)
        
        print("\nTop Correlações com Congestionamento:")
        for var, corr in congestion_corr.items():
            if var != 'congestion_index':
                print(f"   {var}: {corr:.3f}")
        
        self.add_insight("Correlação", 
                        f"Maior correlação positiva: {congestion_corr.index[1]} ({congestion_corr.iloc[1]:.2f})")
    
    def heatmap_hour_route(self):
        """Heatmap: Hora × Rota"""
        print("\n" + "="*70)
        print("HEATMAP HORA × ROTA")
        print("="*70)
        
        # Pivot table
        pivot = self.df.pivot_table(values='congestion_index', 
                                    index='hour_of_day', 
                                    columns='route_name', 
                                    aggfunc='mean')
        
        fig, ax = plt.subplots(figsize=(16, 10))
        
        sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlOrRd', 
                   linewidths=0.5, cbar_kws={"shrink": 0.8}, ax=ax)
        
        ax.set_title('Mapa de Calor: Congestionamento por Hora e Rota', 
                    fontsize=14, weight='bold', pad=20)
        ax.set_xlabel('Rota', fontsize=12)
        ax.set_ylabel('Hora do Dia', fontsize=12)
        
        plt.tight_layout()
        plt.savefig('output/eda/06_heatmap_hora_rota.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(" Salvo: output/eda/06_heatmap_hora_rota.png")
        
        # Identificar hotspot
        max_val = pivot.max().max()
        max_route = pivot.max().idxmax()
        max_hour = pivot[max_route].idxmax()
        
        self.add_insight("Hotspot", 
                        f"Pior combinação: {max_route} às {max_hour}h ({max_val:.1f}%)")
    
    def rush_hour_analysis(self):
        """Análise Rush Hour vs Normal"""
        print("\n" + "="*70)
        print("RUSH HOUR VS HORÁRIO NORMAL")
        print("="*70)
        
        rush = self.df[self.df['is_rush_hour'] == True]
        normal = self.df[self.df['is_rush_hour'] == False]
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. Comparação de congestionamento
        data_congestion = [normal['congestion_index'], rush['congestion_index']]
        bp1 = axes[0, 0].boxplot(data_congestion, labels=['Normal', 'Rush Hour'], 
                                 patch_artist=True)
        bp1['boxes'][0].set_facecolor('#2ECC71')
        bp1['boxes'][1].set_facecolor('#E74C3C')
        
        axes[0, 0].set_title('Congestionamento: Rush Hour vs Normal', 
                            fontsize=12, weight='bold')
        axes[0, 0].set_ylabel('Congestionamento (%)')
        axes[0, 0].grid(True, axis='y', alpha=0.3)
        
        # 2. Velocidade
        data_speed = [normal['current_speed_kmh'], rush['current_speed_kmh']]
        bp2 = axes[0, 1].boxplot(data_speed, labels=['Normal', 'Rush Hour'], 
                                patch_artist=True)
        bp2['boxes'][0].set_facecolor('#2ECC71')
        bp2['boxes'][1].set_facecolor('#E74C3C')
        
        axes[0, 1].set_title('Velocidade: Rush Hour vs Normal', 
                            fontsize=12, weight='bold')
        axes[0, 1].set_ylabel('Velocidade (km/h)')
        axes[0, 1].grid(True, axis='y', alpha=0.3)
        
        # 3. Histograma congestionamento
        axes[1, 0].hist([normal['congestion_index'], rush['congestion_index']], 
                       bins=30, label=['Normal', 'Rush Hour'], 
                       color=['#2ECC71', '#E74C3C'], alpha=0.6)
        axes[1, 0].set_title('Distribuição de Congestionamento', 
                            fontsize=12, weight='bold')
        axes[1, 0].set_xlabel('Congestionamento (%)')
        axes[1, 0].set_ylabel('Frequência')
        axes[1, 0].legend()
        axes[1, 0].grid(True, axis='y', alpha=0.3)
        
        # 4. Estatísticas comparativas
        stats_data = {
            'Métrica': ['Congestionamento Médio (%)', 'Velocidade Média (km/h)', 
                       'Atraso Médio (s)', 'Desvio Padrão Congestionamento'],
            'Normal': [
                normal['congestion_index'].mean(),
                normal['current_speed_kmh'].mean(),
                normal['delay_seconds'].mean(),
                normal['congestion_index'].std()
            ],
            'Rush Hour': [
                rush['congestion_index'].mean(),
                rush['current_speed_kmh'].mean(),
                rush['delay_seconds'].mean(),
                rush['congestion_index'].std()
            ]
        }
        
        stats_df = pd.DataFrame(stats_data)
        stats_df['Diferença (%)'] = ((stats_df['Rush Hour'] - stats_df['Normal']) / 
                                     stats_df['Normal'] * 100)
        
        axes[1, 1].axis('tight')
        axes[1, 1].axis('off')
        
        table = axes[1, 1].table(cellText=stats_df.round(1).values,
                                colLabels=stats_df.columns,
                                cellLoc='center',
                                loc='center',
                                bbox=[0, 0, 1, 1])
        
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 2.5)
        
        for i in range(len(stats_df.columns)):
            table[(0, i)].set_facecolor('#34495E')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        axes[1, 1].set_title('Comparação Estatística', fontsize=12, weight='bold')
        
        plt.tight_layout()
        plt.savefig('output/eda/07_rush_hour_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(" Salvo: output/eda/07_rush_hour_analysis.png")
        
        # Insight
        diff_pct = ((rush['congestion_index'].mean() - normal['congestion_index'].mean()) / 
                   normal['congestion_index'].mean() * 100)
        
        self.add_insight("Rush Hour", 
                        f"Congestionamento {diff_pct:.1f}% maior no rush hour")
    
    def anomaly_detection(self):
        """Detecção de anomalias"""
        print("\n" + "="*70)
        print("DETECÇÃO DE ANOMALIAS")
        print("="*70)
        
        # Z-score para congestionamento
        z_scores = np.abs(stats.zscore(self.df['congestion_index']))
        anomalies = self.df[z_scores > 3]
        
        print(f"Anomalias detectadas: {len(anomalies)} ({len(anomalies)/len(self.df)*100:.2f}%)")
        
        if len(anomalies) > 0:
            fig, axes = plt.subplots(2, 1, figsize=(16, 10))
            
            # 1. Série temporal com anomalias destacadas
            axes[0].plot(self.df['timestamp'], self.df['congestion_index'], 
                        color='#3498DB', alpha=0.6, linewidth=1, label='Normal')
            axes[0].scatter(anomalies['timestamp'], anomalies['congestion_index'], 
                          color='red', s=100, marker='X', zorder=5, label='Anomalias')
            axes[0].set_title('Série Temporal com Anomalias Destacadas', 
                             fontsize=12, weight='bold')
            axes[0].set_ylabel('Congestionamento (%)')
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)
            
            # 2. Distribuição com anomalias
            axes[1].hist(self.df['congestion_index'], bins=50, 
                        color='#2ECC71', alpha=0.6, label='Normal')
            axes[1].hist(anomalies['congestion_index'], bins=20, 
                        color='#E74C3C', alpha=0.8, label='Anomalias')
            axes[1].axvline(x=self.df['congestion_index'].mean(), 
                          color='blue', linestyle='--', linewidth=2, label='Média')
            axes[1].set_title('Distribuição com Anomalias', fontsize=12, weight='bold')
            axes[1].set_xlabel('Congestionamento (%)')
            axes[1].set_ylabel('Frequência')
            axes[1].legend()
            axes[1].grid(True, axis='y', alpha=0.3)
            
            plt.tight_layout()
            plt.savefig('output/eda/08_anomalias.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            print(" Salvo: output/eda/08_anomalias.png")
            
            # Top 5 anomalias
            print("\nTop 5 Anomalias:")
            top_anomalies = anomalies.nlargest(5, 'congestion_index')[
                ['timestamp', 'route_name', 'congestion_index', 'delay_seconds']
            ]
            print(top_anomalies.to_string(index=False))
            
            self.add_insight("Anomalias", 
                            f"{len(anomalies)} eventos anômalos identificados (Z-score > 3)")
    
    def generate_report(self):
        """Gera relatório completo da EDA"""
        report_lines = []
        report_lines.append("# RELATÓRIO DE ANÁLISE EXPLORATÓRIA DE DADOS")
        report_lines.append(f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        report_lines.append("---\n")
        
        report_lines.append("## Dataset")
        report_lines.append(f"- **Registros:** {len(self.df):,}")
        report_lines.append(f"- **Período:** {self.df['timestamp'].min()} a {self.df['timestamp'].max()}")
        report_lines.append(f"- **Rotas:** {self.df['route_name'].nunique()}")
        report_lines.append(f"- **Variáveis:** {len(self.df.columns)}\n")
        
        report_lines.append("## Principais Descobertas\n")
        
        # Agrupar insights por categoria
        insights_by_category = {}
        for insight in self.insights:
            cat = insight['category']
            if cat not in insights_by_category:
                insights_by_category[cat] = []
            insights_by_category[cat].append(insight['insight'])
        
        for category, insights in insights_by_category.items():
            report_lines.append(f"### {category}")
            for insight in insights:
                report_lines.append(f"- {insight}")
            report_lines.append("")
        
        report_lines.append("## Visualizações Geradas\n")
        viz_files = [
            "01_estatisticas_descritivas.png - Tabela de estatísticas",
            "02_analise_temporal.png - Séries temporais (diária, semanal, horária)",
            "03_decomposicao_temporal.png - Decomposição (tendência, sazonalidade, resíduo)",
            "04_comparacao_rotas.png - Comparação entre rotas",
            "05_correlacao.png - Matriz de correlação",
            "06_heatmap_hora_rota.png - Heatmap hora × rota",
            "07_rush_hour_analysis.png - Rush hour vs normal",
            "08_anomalias.png - Detecção de anomalias"
        ]
        
        for viz in viz_files:
            report_lines.append(f"- `output/eda/{viz}`")
        
        report_lines.append("\n## Recomendações\n")
        report_lines.append("1. **Otimização de Rotas:** Priorizar melhorias nas rotas com maior atraso")
        report_lines.append("2. **Gestão de Horários:** Considerar flexibilização de horários comerciais")
        report_lines.append("3. **Monitoramento:** Focar vigilância nos hotspots identificados")
        report_lines.append("4. **Modelagem Preditiva:** Utilizar padrões descobertos para ML")
        report_lines.append("5. **Ações Preventivas:** Investigar causas das anomalias recorrentes")
        
        # Salvar relatório
        report_path = 'output/eda/RELATORIO_EDA.md'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
        
        print(f"\n Relatório salvo: {report_path}")
        
        # Salvar insights em JSON
        insights_path = 'output/eda/insights.json'
        with open(insights_path, 'w', encoding='utf-8') as f:
            json.dump(self.insights, f, indent=2, ensure_ascii=False)
        
        print(f" Insights salvos: {insights_path}")
    
    def run_full_eda(self):
        """Executa análise exploratória completa"""
        print("\n" + "="*70)
        print(" "*15 + "ANÁLISE EXPLORATÓRIA DE DADOS (EDA)")
        print("="*70)
        
        self.load_data()
        self.descriptive_statistics()
        self.temporal_analysis()
        self.decomposition_analysis()
        self.route_comparison()
        self.correlation_analysis()
        self.heatmap_hour_route()
        self.rush_hour_analysis()
        self.anomaly_detection()
        self.generate_report()
        
        print("\n" + "="*70)
        print("✅ ANÁLISE EXPLORATÓRIA CONCLUÍDA!")
        print("="*70)
        print(f"\nVisualizações: output/eda/")
        print(f"Relatório: output/eda/RELATORIO_EDA.md")
        print(f"Insights: output/eda/insights.json")
        print(f"\nPróximo passo: Criar storytelling no Jupyter")
        print(f"   jupyter notebook notebooks/04_data_storytelling.ipynb")


if __name__ == "__main__":
    eda = TrafficEDA()
    eda.run_full_eda()
