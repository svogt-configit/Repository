import pandas as pd

def load_all_data(file_path):
    xl = pd.read_excel(file_path, sheet_name=None)

    # Clusternamen extrahieren aus ClusterMerkmale
    cluster_df = xl["Cluster-Merkmale"]
    clusters = sorted(cluster_df["ID Cluster"].dropna().unique())

    # Merkmale aus Merkmale & Merkmalsanalyse
    merkmale_df = xl["Merkmale"]
    analyse_df = xl["Merkmalsanalyse"]
    merged = pd.merge(merkmale_df, analyse_df, left_on="ID Merkmal", right_on="ID Merkmal")

    families = []
    features = []
    # Erstelle eine Set-Menge für Feature-Familien
    feature_family_codes = set()

    for _, row in merged.iterrows():
        fid = row["ID Merkmal"]
        code = fid
        family_type = row["Typ"].lower()
        desc = row.get("Bezeichnung Merkmal Englisch (generell)", "")
        fam = {
            "code": code,
            "description": desc,
            "type": family_type,
            "min": row["Min Wert"],
            "max": row["Max Wert"],
            "precision": row["Precision"]
        }
        families.append(fam)
        # Speichere nur Family-Codes mit Typ "feature"
        if family_type == "feature":
            feature_family_codes.add(code)

    # Features (Werte) – nur für Feature-Familien
    values_df = xl["Wertelisten"]
    for _, row in values_df.iterrows():
        family_code = row['ID Merkmal']
        if family_code not in feature_family_codes:
            continue 
        code = row['ID Wert']
        desc = row.get("Bezeichnung Wert Englisch", "")
        features.append({
            "code": code,
            "familyCode": family_code,
            "description": desc
        })

    # Cluster-Merkmal-Zuordnung
    cluster_fam = []
    for _, row in cluster_df.iterrows():
        fam_code = row['ID Merkmal']

        cluster_code = row['ID Cluster']
        cluster_fam.append((cluster_code, fam_code))

    return clusters, families, features, cluster_fam
