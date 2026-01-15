from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

class TipoItem(Enum):
    ESTOQUE = "estoque"
    PEDIDO = "pedido"

@dataclass
class Item:
    codigo: str
    comprimento: int
    largura_maxima: int
    quantidade: int
    tipo: TipoItem
    prioridade: int = 0
    
    def __hash__(self):
        return hash(self.codigo)
    
    def __eq__(self, other):
        return self.codigo == other.codigo

@dataclass
class Chapa:
    largura: int
    comprimento: int
    espessura: int
    material: str = "aço"
    
    @property
    def area_disponivel(self) -> int:
        return self.largura * self.comprimento

@dataclass
class Padrao:
    items: List[Item] = field(default_factory=list)
    quantidades: List[int] = field(default_factory=list)
    chapa: Optional[Chapa] = None
    
    @property
    def soma_largura(self) -> int:
        return sum(item.comprimento * qtd 
                  for item, qtd in zip(self.items, self.quantidades))
    
    @property
    def num_skus(self) -> int:
        return len(set(item.codigo for item in self.items))
    
    @property
    def aproveitamento(self) -> float:
        return self.soma_largura / self.chapa.largura if self.chapa else 0.0
    
    def is_valido(self, chapa: Chapa, min_aproveitamento: float = 0.95) -> bool:
        if self.soma_largura > chapa.largura:
            return False
        if self.num_skus > 3:
            return False
        if self.aproveitamento < min_aproveitamento:
            return False
        return True

@dataclass
class SolucaoOtimizacao:
    padroes: List[Padrao] = field(default_factory=list)
    aproveitamento_total: float = 0.0
    chapas_necessarias: int = 0
    items_cobertos: dict = field(default_factory=dict)
    tempo_processamento_ms: float = 0.0
    ranking: int = 0
    
    def resumo(self) -> dict:
        return {
            "ranking": self.ranking,
            "aproveitamento": f"{self.aproveitamento_total:.2%}",
            "chapas_necessarias": self.chapas_necessarias,
            "padroes": [
                {
                    "num_padrao": i,
                    "items": [item.codigo for item in padrao.items],
                    "quantidades": padrao.quantidades,
                    "aproveitamento": f"{padrao.aproveitamento:.2%}",
                    "soma_largura": padrao.soma_largura
                }
                for i, padrao in enumerate(self.padroes, 1)
            ]
        }
