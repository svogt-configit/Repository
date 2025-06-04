import pandas as pd
import json
import os
import re
import fnmatch

# === Eingabedateien ===
char_file = 'Characteristics.xlsx'
cluster_file = 'Domain_Cluster.xlsx'

# === Daten laden ===
df_merkmale = pd.read_excel(char_file, sheet_name='Merkmale')
df_wertelisten = pd.read_excel(char_file, sheet_name='Wertelisten')
df_cluster = pd.read_excel(cluster_file, sheet_name='Cluster')
df_cluster_merkmale = pd.read_excel(cluster_file, sheet_name='Merkmale')

# === 1:1 Kopien ===
output = {
    'Merkmale': df_merkmale,
    'Wertelisten': df_wertelisten,
    'Cluster-Merkmale': df_cluster_merkmale
}

# === KPIs ===
kpi_data = {
    'Kennzahl': [
        'Anzahl Zeilen Merkmale',
        'Min Zeichen ID Merkmal',
        'Max Zeichen ID Merkmal',
        'Anzahl Zeilen Wertelisten',
        'Min Zeichen ID Wert',
        'Max Zeichen ID Wert',
        'Anzahl Domain Cluster'
    ],
    'Wert': [
        len(df_merkmale),
        df_merkmale['ID Merkmal'].astype(str).map(len).min(),
        df_merkmale['ID Merkmal'].astype(str).map(len).max(),
        len(df_wertelisten),
        df_wertelisten['ID Wert'].astype(str).map(len).min(),
        df_wertelisten['ID Wert'].astype(str).map(len).max(),
        df_cluster['ID Cluster'].nunique()
    ]
}
output['KPIs'] = pd.DataFrame(kpi_data)

# === Hilfsfunktionen ===
known_feature_ids = []  # Standardmäßig leer

ignored_outlier_values = {'-99999', '-99999.0', '-99999.00', '-99999.0000'}


def label_looks_like_numeric_unit(label, value):
    return str(value).strip() in str(label)
    
def detect_type(values, labels, merkmal_id):
    reason = ""

    if any(fnmatch.fnmatch(merkmal_id, pattern) for pattern in known_feature_ids):
        reason = "Blacklisted by pattern"
        return 'Feature', reason

    filtered_values = []
    filtered_labels = []

    for v, l in zip(values, labels):
        if str(v).strip() in ignored_outlier_values:
            if len(values) == 1:
                return "Numeric", "Contains only without value!"
            continue
        filtered_values.append(v)
        filtered_labels.append(l)

    numeric_values = pd.to_numeric(filtered_values, errors='coerce')
    is_numeric = pd.notna(numeric_values).all()
    unique_vals = pd.Series(numeric_values).dropna().unique()

    if is_numeric:
        label_patterns = sum(label_looks_like_numeric_unit(label, value) for label, value in zip(filtered_labels, filtered_values))
        if label_patterns > 0:
            return 'Numeric', ""
        else:
            reason = "No numeric-looking descriptions"
    else:
        reason = "Not all values convertible to numbers"

    return 'Feature', reason

   

def min_max_precision(values):
    numeric = pd.Series(pd.to_numeric(values, errors='coerce')).dropna()
    if numeric.empty:
        return '', '', ''
    str_values = pd.Series(values).dropna().astype(str)
    precision = str_values.map(lambda x: len(str(x).split('.')[-1]) if '.' in str(x) else 0)
    return numeric.min(), numeric.max(), precision.max()

# === Merkmalsanalyse & JSON ===
result_rows = []
json_dir = 'numeric_ranges'
os.makedirs(json_dir, exist_ok=True)

for merkmal in df_merkmale['ID Merkmal'].unique():
    sub_df = df_wertelisten[df_wertelisten['ID Merkmal'] == merkmal]
    values = sub_df['ID Wert']
    labels = sub_df['Bezeichnung Wert Englisch'] if 'Bezeichnung Wert Englisch' in sub_df.columns else pd.Series([''] * len(sub_df))
    merk_type, reason = detect_type(values, labels, merkmal)
    count_vals = len(values)
    min_val = max_val = precision = ''
    json_filename = ''

    filtered = list(zip(values, labels))
    if merk_type == 'Numeric':
        ranges = [{"minValue": float(v), "maxValue": float(v)} for v, _ in filtered]
        if ranges:
            json_filename = f"{merkmal}_ranges.json"
            with open(os.path.join(json_dir, json_filename), 'w') as f:
                json.dump({"ranges": ranges}, f, indent=2)
    min_val, max_val, precision = min_max_precision([v for v, _ in filtered])

    result_rows.append([
        merkmal,
        merk_type,
        count_vals,
        min_val,
        max_val,
        precision,
        json_filename,
        reason
    ])

df_analysis = pd.DataFrame(result_rows, columns=[
    'ID Merkmal', 'Typ', 'Anzahl Werte', 'Min Wert', 'Max Wert', 'Precision', 'Range-Datei', 'Begründung'
])
output['Merkmalsanalyse'] = df_analysis

# === Domain-Cluster-Auswertung ===
typ_dict = df_analysis.set_index('ID Merkmal')['Typ'].to_dict()
cluster_summary = []

for cluster_id in df_cluster['ID Cluster']:
    merkmale_in_cluster = df_cluster_merkmale[df_cluster_merkmale['ID Cluster'] == cluster_id]['ID Merkmal']
    total = len(merkmale_in_cluster)
    numeric = 0
    feature = 0
    unknown = 0

    for merkmal in merkmale_in_cluster:
        typ = typ_dict.get(merkmal)
        if typ == 'Numeric':
            numeric += 1
        elif typ == 'Feature':
            feature += 1
        else:
            unknown += 1

    cluster_summary.append([
        cluster_id,
        total,
        feature,
        numeric,
        unknown
    ])

df_domain_cluster = pd.DataFrame(cluster_summary, columns=[
    'ID Cluster', 'Anzahl Merkmale gesamt', 'Anzahl Feature Merkmale',
    'Anzahl Numeric Merkmale', 'Anzahl unbekannte Merkmale'
])
output['Domain-Cluster'] = df_domain_cluster

# === Alles in eine Datei schreiben ===
with pd.ExcelWriter('Import_data_analyze.xlsx') as writer:
    for name, df in output.items():
        df.to_excel(writer, sheet_name=name, index=False)

print("✅ Import_data_analyze.xlsx erfolgreich erstellt + JSON-Dateien im Ordner numeric_ranges.")
