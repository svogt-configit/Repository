import requests

class APIClient:
    def __init__(self, api_key, base_url):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"ApiKey {api_key}",
            "Content-Type": "application/json"
        }

    def create_work_item(self, name, description):

    

        url = f"{self.base_url}/"
        payload = {
            "name": name,
            "description": description,
            "assignedUsers": ["admin"]
        }
        r = requests.post(url, headers=self.headers, json=payload)
        print(f"Workitem creation returns: {r.status_code}")
        return r.json().get("id")

    def create_product(self, wi_id, cluster_id):
        code = cluster_id
        payload = {
            "code": code,
            "description": f"{code}",
            "featureCode": code,
            "brandCode": "DEFAULT",
            "useArithmeticRules": True,
            "useBrochureModels": False,
            "useAdvancedEffectivity": False,
            "canBeUsedAsSubmodel": False
        }
        self._post(f"{self.base_url}/{wi_id}/products/productmodels", payload)

    def create_family(self, wi_id, fam):
        payload = {
            "familyType": "Numeric" if fam["type"] == "numeric" else "Feature",
            "code": fam["code"],
            "description": fam["description"],
            "lifecycle": "Enabled",
            "labels": ["SAP"]
        }
        if fam["type"] == "numeric":
            payload["minValue"] = fam["min"]
            payload["maxValue"] = fam["max"]
            payload["precision"] = fam["precision"]
        self._post(f"{self.base_url}/{wi_id}/library/families", payload)

    def create_feature(self, wi_id, feat):
        payload = {
            "familyType": "Feature",
            "code": feat["code"],
            "familyCode": feat["familyCode"],
            "description": feat["description"],
            "lifecycle": "Enabled"
        }
        self._post(f"{self.base_url}/{wi_id}/library/features", payload)

    def add_family_to_product(self, wi_id, product_code, family_code):
        payload = {
            "familyType": "Feature",
            "code": family_code,
            "isCalculated": False,
            "isPrivate": False,
            "effectivities": [{
                "startEventCode": f"{product_code}_START",
                "endEventCode": f"{product_code}_END"
            }]
        }
        self._post(f"{self.base_url}/{wi_id}/products/productmodels/{product_code}/families", payload)

    def create_view(self, wi_id, product_code, family_codes):
        payload = {
            "code": "STANDARD",
            "description": "Standard View",
            "sections": [{
                "code": "ALL_FEATURES",
                "description": "Alle Merkmale",
                "type": "Standard",
                "sections": [],
                "contentCodes": family_codes
            }]
        }
        self._post(f"{self.base_url}/{wi_id}/products/productmodels/{product_code}/views", payload)

    def _post(self, url, payload):
        r = requests.post(url, headers=self.headers, json=payload)
        if not r.ok:
            print(f"Fehler bei POST {url}: {r.status_code} {r.text}")
