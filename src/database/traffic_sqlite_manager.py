import os
import sqlite3
from datetime import datetime
import pandas as pd

class TrafficSQLiteManager:
    
    def __init__(self, db_path='data/traffic_data.db'):
        self.db_path = db_path
        self.conn = None
        
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f" Conexão estabelecida: {self.db_path}")
            return True
        except Exception as e:
            print(f" Erro ao conectar: {e}")
            return False
    
    def create_tables(self):
        if not self.conn:
            print("Não há conexão ativa")
            return False
        
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS traffic_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                route_name TEXT NOT NULL,
                
                -- Coordenadas geográficas
                origin_lat REAL NOT NULL,
                origin_lon REAL NOT NULL,
                destination_lat REAL NOT NULL,
                destination_lon REAL NOT NULL,
                
                -- Dados temporais
                hour_of_day INTEGER,
                day_of_week INTEGER,
                is_rush_hour BOOLEAN,
                
                -- Métricas de tráfego
                congestion_index REAL,
                current_speed_kmh REAL,
                free_flow_speed_kmh REAL,
                travel_time_seconds INTEGER,
                free_flow_time_seconds INTEGER,
                delay_seconds INTEGER,
                distance_meters INTEGER,
                
                -- Metadados
                api_provider TEXT,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_name TEXT NOT NULL UNIQUE,
                origin_lat REAL NOT NULL,
                origin_lon REAL NOT NULL,
                origin_address TEXT,
                destination_lat REAL NOT NULL,
                destination_lon REAL NOT NULL,
                destination_address TEXT,
                description TEXT,
                route_type TEXT,
                distance_km REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                incident_type TEXT,
                lat REAL,
                lon REAL,
                description TEXT,
                severity TEXT,
                route_affected TEXT,
                reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_name TEXT NOT NULL,
                hour_of_day INTEGER NOT NULL,
                day_of_week INTEGER NOT NULL,
                avg_congestion REAL,
                avg_travel_time REAL,
                avg_delay REAL,
                sample_count INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(route_name, hour_of_day, day_of_week)
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON traffic_data(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_route ON traffic_data(route_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hour ON traffic_data(hour_of_day)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_day ON traffic_data(day_of_week)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rush ON traffic_data(is_rush_hour)')
        
        self.conn.commit()
        print("Tabelas criadas com sucesso:")
        print("  - traffic_data")
        print("  - routes")
        print("  - incidents")
        print("  - historical_patterns")
        return True
    
    def insert_traffic_data_from_csv(self, csv_path):
        try:
            df = pd.read_csv(csv_path)
            
            if 'is_rush_hour' in df.columns:
                df['is_rush_hour'] = df['is_rush_hour'].astype(int)
            
            df.to_sql('traffic_data', self.conn, if_exists='append', index=False)
            
            print(f"{len(df)} registros inseridos do arquivo {csv_path}")
            return True
            
        except Exception as e:
            print(f"Erro ao inserir dados: {e}")
            return False
    
    def insert_routes_from_config(self, routes_data):
        cursor = self.conn.cursor()
        
        for route in routes_data.get('routes', []):
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO routes 
                    (route_name, origin_lat, origin_lon, origin_address,
                     destination_lat, destination_lon, destination_address,
                     description, route_type, distance_km)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    route['name'],
                    route['origin']['lat'],
                    route['origin']['lon'],
                    route['origin'].get('address'),
                    route['destination']['lat'],
                    route['destination']['lon'],
                    route['destination'].get('address'),
                    route.get('description'),
                    route.get('type'),
                    route.get('distance_km')
                ))
            except Exception as e:
                print(f" Erro ao inserir rota {route['name']}: {e}")
        
        self.conn.commit()
        print(f" Rotas cadastradas no banco")
    
    def get_all_data(self):
        query = "SELECT * FROM traffic_data ORDER BY timestamp DESC"
        return pd.read_sql_query(query, self.conn)
    
    def get_route_data(self, route_name):
        query = "SELECT * FROM traffic_data WHERE route_name = ? ORDER BY timestamp DESC"
        return pd.read_sql_query(query, self.conn, params=(route_name,))
    
    def get_rush_hour_data(self):
        query = "SELECT * FROM traffic_data WHERE is_rush_hour = 1 ORDER BY timestamp DESC"
        return pd.read_sql_query(query, self.conn)
    
    def get_congestion_by_hour(self, route_name=None):
        if route_name:
            query = '''
                SELECT hour_of_day, 
                       AVG(congestion_index) as avg_congestion,
                       COUNT(*) as samples
                FROM traffic_data 
                WHERE route_name = ?
                GROUP BY hour_of_day
                ORDER BY hour_of_day
            '''
            return pd.read_sql_query(query, self.conn, params=(route_name,))
        else:
            query = '''
                SELECT hour_of_day, 
                       AVG(congestion_index) as avg_congestion,
                       COUNT(*) as samples
                FROM traffic_data 
                GROUP BY hour_of_day
                ORDER BY hour_of_day
            '''
            return pd.read_sql_query(query, self.conn)
    
    def update_historical_patterns(self):
        cursor = self.conn.cursor()
        
        query = '''
            INSERT OR REPLACE INTO historical_patterns 
            (route_name, hour_of_day, day_of_week, avg_congestion, 
             avg_travel_time, avg_delay, sample_count, last_updated)
            SELECT 
                route_name,
                hour_of_day,
                day_of_week,
                AVG(congestion_index) as avg_congestion,
                AVG(travel_time_seconds) as avg_travel_time,
                AVG(delay_seconds) as avg_delay,
                COUNT(*) as sample_count,
                datetime('now') as last_updated
            FROM traffic_data
            GROUP BY route_name, hour_of_day, day_of_week
        '''
        
        cursor.execute(query)
        self.conn.commit()
        
        count = cursor.execute('SELECT COUNT(*) FROM historical_patterns').fetchone()[0]
        print(f" Padrões históricos atualizados: {count} registros")
    
    def get_statistics(self):
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM traffic_data")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT route_name) FROM traffic_data")
        routes = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(congestion_index) FROM traffic_data")
        avg_congestion = cursor.fetchone()[0]
        
        print(f"\n{'='*60}")
        print(f"Estatísticas do Banco de Dados")
        print(f"{'='*60}")
        print(f"  Total de registros: {total}")
        print(f"  Rotas monitoradas: {routes}")
        
        if total > 0:
            print(f"  Congestionamento médio: {avg_congestion:.1f}%")
            
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM traffic_data")
            first, last = cursor.fetchone()
            print(f"  Primeiro registro: {first}")
            print(f"  Último registro: {last}")
            
            cursor.execute('''
                SELECT route_name, AVG(congestion_index) as avg_cong
                FROM traffic_data
                GROUP BY route_name
                ORDER BY avg_cong DESC
                LIMIT 1
            ''')
            worst = cursor.fetchone()
            if worst:
                print(f"  Rota mais congestionada: {worst[0]} ({worst[1]:.1f}%)")
        
        print(f"{'='*60}\n")
    
    def close(self):
        if self.conn:
            self.conn.close()
            print("Conexão fechada")


def main():
    print(f"\n{'='*60}")
    print(f"Setup do Banco de Dados - SQLite (Tráfego)")
    print(f"{'='*60}\n")
    
    db = TrafficSQLiteManager()
    
    if db.connect():
        db.create_tables()
        
        try:
            import json
            with open('config/routes.json', 'r') as f:
                routes_config = json.load(f)
            db.insert_routes_from_config(routes_config)
        except FileNotFoundError:
            print("Arquivo routes.json não encontrado")
        
        print("\nBanco de dados configurado com sucesso!")
        print(f"\nLocalização: {db.db_path}")
        print("\nPróximos passos:")
        print("  1. Execute o coletor: python src/data_collection/traffic_collector.py")
        print("  2. Importe dados: python src/database/import_traffic_to_db.py")
        
        db.get_statistics()
        db.close()


if __name__ == "__main__":
    main()
