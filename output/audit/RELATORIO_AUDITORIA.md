# RELATÓRIO DE AUDITORIA DE DADOS
**Data:** 16/04/2026 18:42

---

### Dados Carregados
- **Arquivo:** `traffic_data_20260416_182350.csv`
- **Registros:** 23,043
- **Colunas:** 17
- **Período:** 2026-03-01 00:00:00 até 2026-03-30 23:45:00
- **Duração:** 29 dias

## 1. Valores Ausentes

### Diagnóstico
- **Total de valores ausentes:** 691
- **Colunas afetadas:** 3

### Detalhamento
- **current_speed_kmh:** 235 valores (1.02%)
- **delay_seconds:** 233 valores (1.01%)
- **congestion_index:** 223 valores (0.97%)

### Recomendações
- **current_speed_kmh:** Percentual baixo (1.0%) - Pode usar **imputação** (média, mediana ou interpolação)
- **delay_seconds:** Percentual baixo (1.0%) - Pode usar **imputação** (média, mediana ou interpolação)
- **congestion_index:** Percentual baixo (1.0%) - Pode usar **imputação** (média, mediana ou interpolação)

![Valores Ausentes](output/audit/01_missing_values.png)

## 2. Valores Duplicados
- **Registros completamente duplicados:** 4
- **Duplicatas (timestamp + rota):** 4

### Recomendação
- **Ação:** Remover duplicatas usando `drop_duplicates(subset=['timestamp', 'route_name'])`
- **Impacto:** 4 registros serão removidos

## 3. Consistência Temporal
- **Frequência esperada:** 0 days 00:15:00
- **Gaps encontrados:** 1
- **Maior gap:** 0 days 00:30:00
- **Gap médio:** 0 days 00:30:00

### Recomendações
- **Ação:** Preencher gaps com interpolação temporal
- **Método:** `interpolate(method='time')` para variáveis numéricas
- **Alternativa:** Forward fill (`ffill()`) para períodos curtos

## 4. Outliers

### Método: IQR (Interquartile Range)
Valores fora do intervalo [Q1 - 1.5×IQR, Q3 + 1.5×IQR]

#### congestion_index
- **Outliers:** 0 (0.00%)
- **Range aceito:** [-52.55, 119.22]
#### current_speed_kmh
- **Outliers:** 2208 (9.58%)
- **Range aceito:** [14.41, 67.21]
#### travel_time_seconds
- **Outliers:** 1073 (4.66%)
- **Range aceito:** [-81.87, 896.51]
#### delay_seconds
- **Outliers:** 2546 (11.05%)
- **Range aceito:** [-196.43, 392.42]

### Recomendações
- **Outliers < 5%:** Podem ser valores reais (acidentes, eventos) - **Manter** e documentar
- **Outliers 5-10%:** Investigar causas - Aplicar **Winsorization** (cap nos percentis 5 e 95)
- **Outliers > 10%:** Possível erro de coleta - Considerar **remoção** ou **transformação** (log)

![Outliers](output/audit/02_outliers_boxplot.png)

## 5. Tipos de Dados

✅ **Todos os tipos estão corretos!**

## 6. Estatísticas Descritivas

```
                           timestamp    origin_lat    origin_lon  destination_lat  destination_lon   hour_of_day   day_of_week  congestion_index  current_speed_kmh  free_flow_speed_kmh  travel_time_seconds  free_flow_time_seconds  delay_seconds   distance_km
count                          23043  23043.000000  23043.000000     23043.000000     23043.000000  23043.000000  23043.000000      22820.000000       22808.000000         23043.000000         23043.000000            23043.000000   22810.000000  23043.000000
mean   2026-03-15 23:51:46.900143104    -26.491463    -49.071587       -26.476886       -49.071761     11.500022      2.999957         37.464627          42.648097            57.500325           435.877401              295.211249     146.465199      4.887736
min              2026-03-01 00:00:00    -26.530000    -49.110000       -26.500000       -49.095000      0.000000      0.000000          1.775782           6.666667            50.000000           175.241119              172.800000       2.441119      2.400000
25%              2026-03-08 11:52:30    -26.512500    -49.077700       -26.486700       -49.078850      5.500000      1.000000         11.862980          34.206489            50.000000           285.020489              252.000000      24.389861      3.500000
50%              2026-03-15 23:45:00    -26.486700    -49.070000       -26.482000       -49.077700     12.000000      3.000000         29.836671          41.736479            50.000000           362.023726              295.200000      66.464705      4.300000
75%              2026-03-23 11:45:00    -26.470000    -49.060000       -26.458000       -49.052000     17.000000      5.000000         54.805593          47.406421            65.000000           529.616692              345.600000     171.601806      5.200000
max              2026-03-30 23:45:00    -26.460000    -49.045000       -26.440000       -49.040000     23.000000      6.000000        100.000000          78.505051            80.000000          1512.000000              504.000000    3024.000000     11.200000
std                              NaN      0.024158      0.019410         0.017926         0.016272      6.922421      2.081628         29.840173          14.966655            12.990851           232.070182               93.051227     207.436548      2.556811
```