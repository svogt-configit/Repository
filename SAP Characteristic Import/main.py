from data_loader import load_all_data
from api_client import APIClient
import os
from dotenv import load_dotenv
from tqdm import tqdm
from collections import defaultdict

EXEC_CREATE_WORKITEM = False         # Neues Work Item erstellen?
WORKITEM_ID_OVERRIDE = "3"      # Manuelle ID nutzen, wenn vorhanden

EXEC_CREATE_PRODUCTS = False
EXEC_CREATE_FAMILIES = False
EXEC_CREATE_FEATURES = False
EXEC_ADD_FAMILIES_TO_PRODUCTS = False
EXEC_CREATE_VIEWS = True

def main():
    print("Lade .env Konfiguration...")
    load_dotenv()
    api_key = os.getenv("API_KEY")
    base_url = os.getenv("ACE_ENVIRONMENT")
    client = APIClient(api_key, base_url)

    # Excel-Daten laden
    print("Lade Excel-Daten...")
    clusters, families, features, cluster_families = load_all_data("Import_data_analyze.xlsx")

    # Work Item
    if EXEC_CREATE_WORKITEM:
        print("Erstelle Work Item...")
        wi_id = client.create_work_item("Automatischer Import", "Work Item über Migration")
    else:
        print(f"Nutze vorhandenes Work Item: {WORKITEM_ID_OVERRIDE}")
        wi_id = WORKITEM_ID_OVERRIDE

    # Produkte
    if EXEC_CREATE_PRODUCTS:
        print("Erstelle Produktmodelle (Cluster)...")
        for cluster in clusters:
            client.create_product(wi_id, cluster)

    # Familien
    if EXEC_CREATE_FAMILIES:
        print("Erstelle Familien...")
        for family in tqdm(families, desc="Families"):
            client.create_family(wi_id, family)

    # Features
    if EXEC_CREATE_FEATURES:
        print("Erstelle Features...")
        for feature in tqdm(features, desc="Features"):
            client.create_feature(wi_id, feature)



    if EXEC_ADD_FAMILIES_TO_PRODUCTS:
        print("Verknüpfe Familien mit Produkten...")
        for (cluster_code, family_code) in tqdm(cluster_families, desc="Family-Mappings"):
            client.add_family_to_product(wi_id, cluster_code, family_code)
        
    if EXEC_CREATE_VIEWS:
        # Familien zu Produkten zuordnen + View erstellen
        print("Erstelle Views...")
        cluster_to_families = defaultdict(set)
        for (cluster_code, family_code) in tqdm(cluster_families, desc="Lade Family-Mappings for View"):
            cluster_to_families[cluster_code].add(family_code)


        for cluster in tqdm(clusters, desc="Views"):
            family_codes = list(cluster_to_families.get(cluster, []))
            if family_codes:
                client.create_view(wi_id, cluster, family_codes)

    print("Fertig.")
    
if __name__ == "__main__":
    main()