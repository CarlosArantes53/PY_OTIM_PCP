from itertools import combinations
from typing import List, Set, Tuple
from models import Chapa, Item, Padrao

class GeradorPadroes:
    """Gera todos os padrões válidos respeitando restrições"""
    
    def __init__(self, chapa: Chapa, min_aproveitamento: float = 0.95):
        self.chapa = chapa
        self.min_aproveitamento = min_aproveitamento
        self.padroes_gerados: Set[Padrao] = set()
    
    def gerar_padroes_validos(self, items: List[Item]) -> List[Padrao]:
        """
        Gera todos os padrões válidos combinando até 3 SKUs diferentes
        
        Args:
            items: Lista de items disponíveis (estoque + pedido)
        
        Returns:
            Lista de Padrao válidos (aproveitamento > min_aproveitamento)
        """
        padroes_validos = []
        
        # Gera combinações de até 3 SKUs distintos
        for num_skus in range(1, 4):  # 1, 2 ou 3 SKUs
            for combo_items in combinations(items, num_skus):
                # Encontra todas as formas de distribuir esses SKUs
                padroes = self._encontrar_distribuicoes(combo_items)
                
                for padrao in padroes:
                    if self._validar_padrao(padrao):
                        padroes_validos.append(padrao)
        
        return padroes_validos
    
    def _encontrar_distribuicoes(self, items: Tuple[Item, ...]) -> List[Padrao]:
        """
        Para um conjunto de items, encontra todas as quantidades possíveis
        que somam exatamente a largura da chapa
        
        Usa programação dinâmica com backtracking
        """
        padroes = []
        largura_alvo = self.chapa.largura
        
        def backtrack(idx: int, quantidades_atuais: List[int], soma_atual: int):
            """Backtracking para encontrar combinações que somam exatamente"""
            
            # Caso base: chegou ao final ou soma = alvo
            if idx == len(items):
                if soma_atual == largura_alvo:
                    padrao = Padrao(
                        items=list(items),
                        quantidades=quantidades_atuais.copy()
                    )
                    padroes.append(padrao)
                return
            
            # Poda: se soma já ultrapassou, não continua
            if soma_atual > largura_alvo:
                return
            
            item_atual = items[idx]
            
            # Calcula máxima quantidade possível do item atual
            espaco_restante = largura_alvo - soma_atual
            max_quantidade = espaco_restante // item_atual.comprimento
            
            # Tenta todas as quantidades possíveis
            for qtd in range(max_quantidade + 1):
                quantidades_atuais.append(qtd)
                nova_soma = soma_atual + qtd * item_atual.comprimento
                
                backtrack(idx + 1, quantidades_atuais, nova_soma)
                
                quantidades_atuais.pop()
        
        backtrack(0, [], 0)
        return padroes
    
    def _validar_padrao(self, padrao: Padrao) -> bool:
        """Valida se padrão atende todas as restrições"""
        
        # Restrição 1: Soma deve ser <= largura chapa
        if padrao.soma_largura > self.chapa.largura:
            return False
        
        # Restrição 2: Máximo 3 SKUs distintos
        if padrao.num_skus > 3:
            return False
        
        # Restrição 3: Aproveitamento > 95%
        aproveitamento = padrao.soma_largura / self.chapa.largura
        if aproveitamento < self.min_aproveitamento:
            return False
        
        # Restrição 4: Nenhuma quantidade pode ser negativa
        if any(qtd < 0 for qtd in padrao.quantidades):
            return False
        
        return True
