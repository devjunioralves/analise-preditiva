import os
import glob
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.traffic_sqlite_manager import TrafficSQLiteManager

def import_csv_files():    
    print(f"\n{'='*60}")
    print(f"Importação de Dados CSV de Tráfego para o Banco")
    print(f"{'='*60}\n")
    
    db = TrafficSQLiteManager()
    if not db.connect():
        return
    
    csv_files = glob.glob('data/raw/traffic_data_*.csv')
    
    if not csv_files:
        print(" Nenhum arquivo CSV encontrado em data/raw/")
        print(" Execute primeiro: python src/data_collection/traffic_collector.py")
        db.close()
        return
    
    print(f"Encontrados {len(csv_files)} arquivo(s) CSV\n")
    
    for csv_file in csv_files:
        print(f"Importando: {csv_file}")
        db.insert_traffic_data_from_csv(csv_file)
    
    print(f"\n Importação concluída!")
    
    print("\n Atualizando padrões históricos...")
    db.update_historical_patterns()
    
    db.get_statistics()
    db.close()


if __name__ == "__main__":
    import_csv_files()
