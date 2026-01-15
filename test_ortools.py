import requests
import json

payload = {
    "items_pedido": [
        {"codigo": "ITEM_A", "comprimento": 200, "quantidade": 5, "tipo": "pedido"},
        {"codigo": "ITEM_B", "comprimento": 300, "quantidade": 3, "tipo": "pedido"},
        {"codigo": "ITEM_C", "comprimento": 150, "quantidade": 8, "tipo": "pedido"}
    ],
    "items_estoque": [
        {"codigo": "ESTOQUE_001", "comprimento": 250, "quantidade": 100, "tipo": "estoque"},
        {"codigo": "ESTOQUE_002", "comprimento": 400, "quantidade": 50, "tipo": "estoque"},
        {"codigo": "ESTOQUE_003", "comprimento": 120, "quantidade": 80, "tipo": "estoque"},
    ],
    "chapa": {
        "largura": 1200,
        "comprimento": 6000,
        "espessura": 2,
        "material": "aço"
    },
    "min_aproveitamento": 0.95,
    "max_solucoes": 5
}

response = requests.post("http://localhost:8000/otimizar", json=payload)

print(json.dumps(response.json(), indent=2, ensure_ascii=False))
