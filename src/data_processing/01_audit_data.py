"""
ETAPA 1: AUDITORIA DE DADOS
Diagnóstico completo da qualidade da série temporal

Identifica:
- Valores ausentes (missing values)
- Outliers
- Inconsistências temporais (gaps, duplicatas, frequência irregular)
- Problemas de qualidade

Documenta cada problema com evidências e recomendações
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import glob

class DataAuditor:
    """Realiza auditoria completa dos dados de tráfego"""
    
    def __init__(self, data_path='data/raw'):
        self.data_path = data_path
        self.df = None
        self.report = []
        self.issues = {}
        
        # Configurar estilo de visualização
        sns.set_style('whitegrid')
        plt.rcParams['figure.figsize'] = (12, 6)
        
        # Criar diretório para outputs
        os.makedirs('output/audit', exist_ok=True)
    
    def load_data(self):
        """Carrega dados de CSV"""
        # Procura por arquivos CSV
        csv_files = glob.glob(f"{self.data_path}/traffic_data_*.csv")
        
        if not csv_files:
            raise FileNotFoundError(f"Nenhum arquivo encontrado em {self.data_path}")
        
        # Carrega o mais recente
        latest_file = max(csv_files, key=os.path.getmtime)
        print(f"Carregando dados de: {latest_file}")
        
        self.df = pd.read_csv(latest_file)
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        
        print(f" {len(self.df)} registros carregados")
        print(f" Período: {self.df['timestamp'].min()} até {self.df['timestamp'].max()}")
        
        self.add_to_report("### Dados Carregados")
        self.add_to_report(f"- **Arquivo:** `{os.path.basename(latest_file)}`")
        self.add_to_report(f"- **Registros:** {len(self.df):,}")
        self.add_to_report(f"- **Colunas:** {len(self.df.columns)}")
        self.add_to_report(f"- **Período:** {self.df['timestamp'].min()} até {self.df['timestamp'].max()}")
        self.add_to_report(f"- **Duração:** {(self.df['timestamp'].max() - self.df['timestamp'].min()).days} dias")
        
        return self.df
    
    def add_to_report(self, text):
        """Adiciona linha ao relatório"""
        self.report.append(text)
    
    def check_missing_values(self):
        """Identifica e documenta valores ausentes"""
        print("\n" + "="*60)
        print("VALORES AUSENTES (MISSING VALUES)")
        print("="*60)
        
        missing = self.df.isnull().sum()
        missing_pct = (missing / len(self.df)) * 100
        
        missing_df = pd.DataFrame({
            'Coluna': missing.index,
            'Total Missing': missing.values,
            'Percentual (%)': missing_pct.values
        }).sort_values('Total Missing', ascending=False)
        
        print("\n" + missing_df.to_string(index=False))
        
        # Visualização
        if missing.sum() > 0:
            fig, ax = plt.subplots(figsize=(10, 6))
            missing_cols = missing_df[missing_df['Total Missing'] > 0]
            
            if len(missing_cols) > 0:
                ax.barh(missing_cols['Coluna'], missing_cols['Percentual (%)'], color='coral')
                ax.set_xlabel('Percentual de Valores Ausentes (%)')
                ax.set_title('Valores Ausentes por Coluna')
                ax.set_xlim(0, max(missing_cols['Percentual (%)']) * 1.1)
                
                for i, v in enumerate(missing_cols['Percentual (%)']):
                    ax.text(v + 0.1, i, f'{v:.1f}%', va='center')
                
                plt.tight_layout()
                plt.savefig('output/audit/01_missing_values.png', dpi=300, bbox_inches='tight')
                plt.close()
                
                print(f"\n Gráfico salvo: output/audit/01_missing_values.png")
            
            # Adicionar ao relatório
            self.add_to_report("\n## 1. Valores Ausentes")
            self.add_to_report("\n### Diagnóstico")
            self.add_to_report(f"- **Total de valores ausentes:** {missing.sum():,}")
            self.add_to_report(f"- **Colunas afetadas:** {(missing > 0).sum()}")
            
            self.add_to_report("\n### Detalhamento")
            for _, row in missing_cols.iterrows():
                self.add_to_report(f"- **{row['Coluna']}:** {int(row['Total Missing'])} valores ({row['Percentual (%)']:.2f}%)")
            
            self.add_to_report("\n### Recomendações")
            for _, row in missing_cols.iterrows():
                col = row['Coluna']
                pct = row['Percentual (%)']
                
                if pct < 5:
                    self.add_to_report(f"- **{col}:** Percentual baixo ({pct:.1f}%) - Pode usar **imputação** (média, mediana ou interpolação)")
                elif pct < 15:
                    self.add_to_report(f"- **{col}:** Percentual moderado ({pct:.1f}%) - Avaliar **interpolação temporal** ou **remoção** se não crítico")
                else:
                    self.add_to_report(f"- **{col}:** Percentual alto ({pct:.1f}%) - Considerar **remoção da coluna** ou investigar causa")
            
            self.add_to_report("\n![Valores Ausentes](output/audit/01_missing_values.png)")
            
            self.issues['missing_values'] = missing_df[missing_df['Total Missing'] > 0].to_dict('records')
        else:
            print("\n✅ Nenhum valor ausente encontrado!")
            self.add_to_report("\n## 1. Valores Ausentes")
            self.add_to_report("\n✅ **Nenhum valor ausente encontrado!**")
    
    def check_duplicates(self):
        """Identifica duplicatas"""
        print("\n" + "="*60)
        print("VALORES DUPLICADOS")
        print("="*60)
        
        # Duplicatas completas
        duplicates_full = self.df.duplicated().sum()
        print(f"\nRegistros completamente duplicados: {duplicates_full}")
        
        # Duplicatas de timestamp + rota
        duplicates_time_route = self.df.duplicated(subset=['timestamp', 'route_name']).sum()
        print(f"Duplicatas timestamp + rota: {duplicates_time_route}")
        
        # Timestamps duplicados
        duplicates_time = self.df['timestamp'].duplicated().sum()
        print(f"Timestamps duplicados (mesma coleta): {duplicates_time}")
        
        self.add_to_report("\n## 2. Valores Duplicados")
        self.add_to_report(f"- **Registros completamente duplicados:** {duplicates_full}")
        self.add_to_report(f"- **Duplicatas (timestamp + rota):** {duplicates_time_route}")
        
        if duplicates_full > 0 or duplicates_time_route > 0:
            self.add_to_report("\n### Recomendação")
            self.add_to_report("- **Ação:** Remover duplicatas usando `drop_duplicates(subset=['timestamp', 'route_name'])`")
            self.add_to_report(f"- **Impacto:** {duplicates_time_route} registros serão removidos")
            
            self.issues['duplicates'] = {'full': duplicates_full, 'time_route': duplicates_time_route}
        else:
            self.add_to_report("\n✅ **Nenhuma duplicata encontrada!**")
    
    def check_temporal_consistency(self):
        """Verifica consistência temporal"""
        print("\n" + "="*60)
        print("CONSISTÊNCIA TEMPORAL")
        print("="*60)
        
        # Ordenar por timestamp
        df_sorted = self.df.sort_values('timestamp')
        
        # Calcular diferenças entre timestamps consecutivos
        time_diffs = df_sorted.groupby('route_name')['timestamp'].diff()
        
        # Frequência esperada (15 minutos)
        expected_freq = pd.Timedelta(minutes=15)
        
        # Gaps (diferenças maiores que o esperado)
        gaps = time_diffs[time_diffs > expected_freq]
        
        print(f"\nFrequência esperada: {expected_freq}")
        print(f"Gaps encontrados: {len(gaps)}")
        
        if len(gaps) > 0:
            print(f"Maior gap: {gaps.max()}")
            print(f"Gap médio: {gaps.mean()}")
            
            # Top 10 maiores gaps
            print("\nTop 10 Maiores Gaps:")
            top_gaps = gaps.nlargest(10)
            for idx, gap in top_gaps.items():
                timestamp = df_sorted.loc[idx, 'timestamp']
                route = df_sorted.loc[idx, 'route_name']
                print(f"  - {timestamp} | {route} | Gap: {gap}")
        
        # Frequência irregular (desvio padrão alto)
        freq_std = time_diffs.std()
        print(f"\nDesvio padrão da frequência: {freq_std}")
        
        self.add_to_report("\n## 3. Consistência Temporal")
        self.add_to_report(f"- **Frequência esperada:** {expected_freq}")
        self.add_to_report(f"- **Gaps encontrados:** {len(gaps)}")
        
        if len(gaps) > 0:
            self.add_to_report(f"- **Maior gap:** {gaps.max()}")
            self.add_to_report(f"- **Gap médio:** {gaps.mean()}")
            
            self.add_to_report("\n### Recomendações")
            self.add_to_report("- **Ação:** Preencher gaps com interpolação temporal")
            self.add_to_report("- **Método:** `interpolate(method='time')` para variáveis numéricas")
            self.add_to_report("- **Alternativa:** Forward fill (`ffill()`) para períodos curtos")
            
            self.issues['temporal_gaps'] = len(gaps)
        else:
            self.add_to_report("\n **Frequência regular, sem gaps significativos!**")
    
    def detect_outliers(self):
        """Detecta outliers usando IQR e Z-score"""
        print("\n" + "="*60)
        print("DETECÇÃO DE OUTLIERS")
        print("="*60)
        
        numeric_cols = ['congestion_index', 'current_speed_kmh', 'travel_time_seconds', 'delay_seconds']
        outliers_summary = []
        
        for col in numeric_cols:
            if col not in self.df.columns:
                continue
            
            # Método IQR
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers_iqr = ((self.df[col] < lower_bound) | (self.df[col] > upper_bound)).sum()
            outliers_pct = (outliers_iqr / len(self.df)) * 100
            
            outliers_summary.append({
                'Coluna': col,
                'Total Outliers': outliers_iqr,
                'Percentual (%)': outliers_pct,
                'Q1': Q1,
                'Q3': Q3,
                'IQR': IQR,
                'Lower Bound': lower_bound,
                'Upper Bound': upper_bound
            })
            
            print(f"\n{col}:")
            print(f"   Outliers (IQR): {outliers_iqr} ({outliers_pct:.2f}%)")
            print(f"   Range [Q1-1.5*IQR, Q3+1.5*IQR]: [{lower_bound:.2f}, {upper_bound:.2f}]")
        
        outliers_df = pd.DataFrame(outliers_summary)
        
        # Visualização - Boxplots
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.ravel()
        
        for i, col in enumerate(numeric_cols[:4]):
            if col in self.df.columns:
                self.df.boxplot(column=col, ax=axes[i])
                axes[i].set_title(f'Boxplot: {col}')
                axes[i].set_ylabel('Valor')
                outliers = outliers_df[outliers_df['Coluna'] == col]['Total Outliers'].values[0]
                axes[i].text(0.95, 0.95, f'Outliers: {outliers}', 
                           transform=axes[i].transAxes, ha='right', va='top',
                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig('output/audit/02_outliers_boxplot.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\n Gráfico salvo: output/audit/02_outliers_boxplot.png")
        
        self.add_to_report("\n## 4. Outliers")
        self.add_to_report("\n### Método: IQR (Interquartile Range)")
        self.add_to_report("Valores fora do intervalo [Q1 - 1.5×IQR, Q3 + 1.5×IQR]\n")
        
        for _, row in outliers_df.iterrows():
            self.add_to_report(f"#### {row['Coluna']}")
            self.add_to_report(f"- **Outliers:** {int(row['Total Outliers'])} ({row['Percentual (%)']:.2f}%)")
            self.add_to_report(f"- **Range aceito:** [{row['Lower Bound']:.2f}, {row['Upper Bound']:.2f}]")
            
        self.add_to_report("\n### Recomendações")
        self.add_to_report("- **Outliers < 5%:** Podem ser valores reais (acidentes, eventos) - **Manter** e documentar")
        self.add_to_report("- **Outliers 5-10%:** Investigar causas - Aplicar **Winsorization** (cap nos percentis 5 e 95)")
        self.add_to_report("- **Outliers > 10%:** Possível erro de coleta - Considerar **remoção** ou **transformação** (log)")
        
        self.add_to_report("\n![Outliers](output/audit/02_outliers_boxplot.png)")
        
        self.issues['outliers'] = outliers_df.to_dict('records')
    
    def check_data_types(self):
        """Verifica tipos de dados"""
        print("\n" + "="*60)
        print("TIPOS DE DADOS")
        print("="*60)
        
        print("\n" + self.df.dtypes.to_string())
        
        # Verificar se tipos estão corretos
        expected_types = {
            'timestamp': 'datetime64[ns]',
            'congestion_index': 'float64',
            'current_speed_kmh': 'float64',
            'travel_time_seconds': 'float64',
            'is_rush_hour': 'bool'
        }
        
        type_issues = []
        for col, expected_type in expected_types.items():
            if col in self.df.columns:
                actual_type = str(self.df[col].dtype)
                if actual_type != expected_type:
                    type_issues.append(f"{col}: esperado {expected_type}, encontrado {actual_type}")
        
        if type_issues:
            print("\n  Problemas de tipo encontrados:")
            for issue in type_issues:
                print(f"   - {issue}")
        else:
            print("\n Todos os tipos de dados estão corretos!")
        
        self.add_to_report("\n## 5. Tipos de Dados")
        if type_issues:
            self.add_to_report("\n **Problemas encontrados:**")
            for issue in type_issues:
                self.add_to_report(f"- {issue}")
            self.add_to_report("\n### Recomendação")
            self.add_to_report("- Converter tipos usando `astype()` ou `pd.to_datetime()`")
        else:
            self.add_to_report("\n **Todos os tipos estão corretos!**")
    
    def generate_summary_statistics(self):
        """Gera estatísticas descritivas"""
        print("\n" + "="*60)
        print("ESTATÍSTICAS DESCRITIVAS")
        print("="*60)
        
        print("\n" + self.df.describe().to_string())
        
        self.add_to_report("\n## 6. Estatísticas Descritivas")
        self.add_to_report("\n```")
        self.add_to_report(self.df.describe().to_string())
        self.add_to_report("```")
    
    def save_report(self):
        """Salva relatório em Markdown"""
        report_path = 'output/audit/RELATORIO_AUDITORIA.md'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# RELATÓRIO DE AUDITORIA DE DADOS\n")
            f.write(f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
            f.write("---\n\n")
            f.write("\n".join(self.report))
        
        print(f"\n Relatório salvo: {report_path}")
        
        # Salvar issues em JSON para uso posterior
        import json
        with open('output/audit/issues.json', 'w') as f:
            json.dump(self.issues, f, indent=2, default=str)
        
        print(f" Issues salvos: output/audit/issues.json")
    
    def run_full_audit(self):
        """Executa auditoria completa"""
        print("\n" + "="*70)
        print(" "*20 + "AUDITORIA DE DADOS")
        print("="*70)
        
        self.load_data()
        self.check_missing_values()
        self.check_duplicates()
        self.check_temporal_consistency()
        self.detect_outliers()
        self.check_data_types()
        self.generate_summary_statistics()
        self.save_report()
        
        print("\n" + "="*70)
        print(" AUDITORIA CONCLUÍDA!")
        print("="*70)
        print(f"\nOutputs gerados:")
        print(f"   - Relatório: output/audit/RELATORIO_AUDITORIA.md")
        print(f"   - Gráficos: output/audit/*.png")
        print(f"   - Issues: output/audit/issues.json")
        print(f"\nPróximo passo: Execute o tratamento de dados")
        print(f"   python src/data_processing/02_clean_data.py")


if __name__ == "__main__":
    auditor = DataAuditor()
    auditor.run_full_audit()
