import requests
import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv
import pandas as pd
import folium
from folium.plugins import HeatMap

load_dotenv()

class TrafficDataCollector:
    
    def __init__(self):
        self.tomtom_api_key = os.getenv('TOMTOM_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.use_api = os.getenv('TRAFFIC_API_PROVIDER', 'tomtom')  # tomtom ou google
        
        self.routes = self.load_routes()
        
        self.raw_data_path = 'data/raw/'
        os.makedirs(self.raw_data_path, exist_ok=True)
    
    def load_routes(self):
        try:
            with open('config/routes.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️  Arquivo routes.json não encontrado. Usando rotas padrão.")
            return self.get_default_routes()
    
    def get_default_routes(self):
        return {
            "routes": [
                {
                    "name": "Centro → Zona Sul (Av. 23 de Maio)",
                    "origin": {"lat": -23.5505, "lon": -46.6333},
                    "destination": {"lat": -23.6231, "lon": -46.6556},
                    "description": "Principal corredor Sul"
                },
                {
                    "name": "Zona Oeste → Centro (Av. Paulista)",
                    "origin": {"lat": -23.5489, "lon": -46.7161},
                    "destination": {"lat": -23.5615, "lon": -46.6563},
                    "description": "Avenida Paulista - principal via"
                },
                {
                    "name": "Zona Leste → Centro (Radial Leste)",
                    "origin": {"lat": -23.5558, "lon": -46.4731},
                    "destination": {"lat": -23.5505, "lon": -46.6333},
                    "description": "Corredor Leste-Oeste"
                },
                {
                    "name": "Zona Norte → Centro (Av. Tiradentes)",
                    "origin": {"lat": -23.4862, "lon": -46.6315},
                    "destination": {"lat": -23.5505, "lon": -46.6333},
                    "description": "Corredor Norte"
                },
                {
                    "name": "Marginal Pinheiros (Sul → Norte)",
                    "origin": {"lat": -23.6272, "lon": -46.6986},
                    "destination": {"lat": -23.5272, "lon": -46.7014},
                    "description": "Marginal Pinheiros - via expressa"
                },
                {
                    "name": "Marginal Tietê (Oeste → Leste)",
                    "origin": {"lat": -23.5272, "lon": -46.7014},
                    "destination": {"lat": -23.5256, "lon": -46.4842},
                    "description": "Marginal Tietê - via expressa"
                }
            ]
        }
    
    def collect_tomtom_traffic(self, origin, destination):
        
        base_url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
        
        mid_lat = (origin['lat'] + destination['lat']) / 2
        mid_lon = (origin['lon'] + destination['lon']) / 2
        
        params = {
            'key': self.tomtom_api_key,
            'point': f"{mid_lat},{mid_lon}",
            'unit': 'KMPH'
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            flow_data = data.get('flowSegmentData', {})
            
            return {
                'current_speed': flow_data.get('currentSpeed'),
                'free_flow_speed': flow_data.get('freeFlowSpeed'),
                'current_travel_time': flow_data.get('currentTravelTime'),
                'free_flow_travel_time': flow_data.get('freeFlowTravelTime'),
                'confidence': flow_data.get('confidence'),
                'coordinates': flow_data.get('coordinates', {})
            }
            
        except Exception as e:
            print(f"✗ Erro ao coletar dados TomTom: {e}")
            return None
    
    def collect_google_traffic(self, origin, destination):
        base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        
        params = {
            'origins': f"{origin['lat']},{origin['lon']}",
            'destinations': f"{destination['lat']},{destination['lon']}",
            'departure_time': 'now',
            'traffic_model': 'best_guess',
            'key': self.google_api_key
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] != 'OK':
                print(f"✗ API Error: {data.get('error_message', 'Unknown error')}")
                return None
            
            element = data['rows'][0]['elements'][0]
            
            if element['status'] != 'OK':
                return None
            
            return {
                'distance_meters': element['distance']['value'],
                'distance_text': element['distance']['text'],
                'duration_seconds': element['duration']['value'],
                'duration_text': element['duration']['text'],
                'duration_in_traffic_seconds': element.get('duration_in_traffic', {}).get('value'),
                'duration_in_traffic_text': element.get('duration_in_traffic', {}).get('text')
            }
            
        except Exception as e:
            print(f"✗ Erro ao coletar dados Google: {e}")
            return None
    
    def calculate_congestion_index(self, traffic_data, api='tomtom'):
        if not traffic_data:
            return None
        
        if api == 'tomtom':
            current = traffic_data.get('current_speed', 0)
            free_flow = traffic_data.get('free_flow_speed', 1)
            if free_flow == 0:
                return 100
            congestion = ((free_flow - current) / free_flow) * 100
            return max(0, min(100, congestion))
        
        elif api == 'google':
            normal = traffic_data.get('duration_seconds', 0)
            with_traffic = traffic_data.get('duration_in_traffic_seconds', normal)
            if normal == 0:
                return None
            congestion = ((with_traffic - normal) / normal) * 100
            return max(0, min(100, congestion))
        
        return None
    
    def collect_route_data(self, route):
        print(f"  Coletando: {route['name']}")
        
        if self.use_api == 'google' and self.google_api_key:
            traffic_data = self.collect_google_traffic(route['origin'], route['destination'])
            api_used = 'google'
        else:
            traffic_data = self.collect_tomtom_traffic(route['origin'], route['destination'])
            api_used = 'tomtom'
        
        if not traffic_data:
            print(f"    ✗ Falha na coleta")
            return None
        
        congestion_index = self.calculate_congestion_index(traffic_data, api_used)
        
        structured_data = {
            'timestamp': datetime.now().isoformat(),
            'route_name': route['name'],
            'origin_lat': route['origin']['lat'],
            'origin_lon': route['origin']['lon'],
            'destination_lat': route['destination']['lat'],
            'destination_lon': route['destination']['lon'],
            'hour_of_day': datetime.now().hour,
            'day_of_week': datetime.now().weekday(),
            'is_rush_hour': self.is_rush_hour(),
            'api_provider': api_used,
            'congestion_index': congestion_index
        }
        
        if api_used == 'tomtom':
            structured_data.update({
                'current_speed_kmh': traffic_data.get('current_speed'),
                'free_flow_speed_kmh': traffic_data.get('free_flow_speed'),
                'travel_time_seconds': traffic_data.get('current_travel_time'),
                'free_flow_time_seconds': traffic_data.get('free_flow_travel_time'),
                'delay_seconds': (traffic_data.get('current_travel_time', 0) - 
                                 traffic_data.get('free_flow_travel_time', 0))
            })
        else:
            structured_data.update({
                'distance_meters': traffic_data.get('distance_meters'),
                'travel_time_seconds': traffic_data.get('duration_seconds'),
                'travel_time_traffic_seconds': traffic_data.get('duration_in_traffic_seconds'),
                'delay_seconds': (traffic_data.get('duration_in_traffic_seconds', 0) - 
                                 traffic_data.get('duration_seconds', 0))
            })
        
        print(f"    ✓ Congestionamento: {congestion_index:.1f}% | Atraso: {structured_data.get('delay_seconds', 0)}s")
        
        return structured_data
    
    def is_rush_hour(self):
        hour = datetime.now().hour
        weekday = datetime.now().weekday()
        
        if weekday < 5:
            return (6 <= hour <= 9) or (17 <= hour <= 20)
        
        return False
    
    def collect_all_routes(self):
        print(f"\n{'='*70}")
        print(f"Coleta de Dados de Tráfego - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        all_data = []
        routes_list = self.routes.get('routes', [])
        
        for i, route in enumerate(routes_list, 1):
            print(f"[{i}/{len(routes_list)}]")
            data = self.collect_route_data(route)
            
            if data:
                all_data.append(data)
                self.save_raw_json(data, route['name'])
            
            if i < len(routes_list):
                time.sleep(2)
        
        print(f"\n{'='*70}")
        print(f"Coleta finalizada: {len(all_data)}/{len(routes_list)} rotas coletadas")
        print(f"{'='*70}\n")
        
        return all_data
    
    def save_raw_json(self, data, route_name):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = route_name.replace(' ', '_').replace('→', 'to')[:50]
        filename = f"{self.raw_data_path}traffic_{safe_name}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_to_csv(self, data):
        if not data:
            print("Nenhum dado para salvar")
            return
        
        df = pd.DataFrame(data)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.raw_data_path}traffic_data_{timestamp}.csv"
        
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"✓ Dados salvos em CSV: {filename}")
        
        print(f"\nResumo da coleta:")
        print(f"  - Total de registros: {len(df)}")
        print(f"  - Rotas monitoradas: {df['route_name'].nunique()}")
        print(f"  - Congestionamento médio: {df['congestion_index'].mean():.1f}%")
        print(f"  - Atraso médio: {df['delay_seconds'].mean():.0f}s")
        
        worst_route = df.loc[df['congestion_index'].idxmax()]
        print(f"  - Rota mais congestionada: {worst_route['route_name']} ({worst_route['congestion_index']:.1f}%)")
    
    def create_traffic_map(self, data):
        if not data:
            return
        
        map_center = [-23.5505, -46.6333]
        traffic_map = folium.Map(location=map_center, zoom_start=11)
        
        for route_data in data:
            origin = [route_data['origin_lat'], route_data['origin_lon']]
            destination = [route_data['destination_lat'], route_data['destination_lon']]
            
            congestion = route_data.get('congestion_index', 0)
            if congestion < 30:
                color = 'green'
            elif congestion < 60:
                color = 'orange'
            else:
                color = 'red'
            
            folium.PolyLine(
                [origin, destination],
                color=color,
                weight=5,
                opacity=0.7,
                popup=f"{route_data['route_name']}<br>Congestionamento: {congestion:.1f}%"
            ).add_to(traffic_map)
            
            folium.Marker(
                origin,
                popup=f"Origem: {route_data['route_name']}",
                icon=folium.Icon(color='blue', icon='play')
            ).add_to(traffic_map)
            
            folium.Marker(
                destination,
                popup=f"Destino: {route_data['route_name']}",
                icon=folium.Icon(color='purple', icon='stop')
            ).add_to(traffic_map)
        
        os.makedirs('data/maps', exist_ok=True)
        map_file = f"data/maps/traffic_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        traffic_map.save(map_file)
        print(f"✓ Mapa interativo salvo: {map_file}")


def main():
    collector = TrafficDataCollector()
    
    if collector.use_api == 'tomtom':
        if not collector.tomtom_api_key or collector.tomtom_api_key == 'sua_chave_tomtom_aqui':
            print("\n ATENÇÃO: Configure sua chave TomTom API no arquivo .env")
            print("   1. Copie .env.example para .env")
            print("   2. Obtenha chave em: https://developer.tomtom.com/")
            print("   3. Substitua 'sua_chave_tomtom_aqui' pela sua chave\n")
            return
    elif collector.use_api == 'google':
        if not collector.google_api_key or collector.google_api_key == 'sua_chave_google_aqui':
            print("\n ATENÇÃO: Configure sua chave Google Maps API no arquivo .env")
            print("   1. Copie .env.example para .env")
            print("   2. Obtenha chave em: https://console.cloud.google.com/")
            print("   3. Ative Distance Matrix API")
            print("   4. Substitua 'sua_chave_google_aqui' pela sua chave\n")
            return
    
    data = collector.collect_all_routes()
    
    if data:
        collector.save_to_csv(data)
        
        collector.create_traffic_map(data)
        
        print(f"\n Coleta concluída com sucesso!")
    else:
        print("\n Nenhum dado foi coletado")


if __name__ == "__main__":
    main()
