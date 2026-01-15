from ortools.linear_solver import pywraplp
from typing import List, Dict, Optional, Tuple
import time
from gerador_padroes import GeradorPadroes
from models import Chapa, Item, Padrao, SolucaoOtimizacao
class OtimizadorORTools:
    """
    Resolver usando OR-Tools Linear Optimizer
    
    Problema: Cutting Stock Problem (Bin Packing 1D)
    - Decisão: quantas vezes usar cada padrão?
    - Objetivo: minimizar chapas ou maximizar aproveitamento
    - Restrições: atender demanda, max 3 SKUs por chapa, 
                   aproveitamento > 95%
    """
    
    def __init__(self, chapa: Chapa, min_aproveitamento: float = 0.95):
        self.chapa = chapa
        self.min_aproveitamento = min_aproveitamento
        self.solver = pywraplp.Solver.CreateSolver('CBC')
    
    def otimizar(self, items_pedido: List[Item], 
                 items_estoque: List[Item],
                 max_solucoes: int = 5) -> List[SolucaoOtimizacao]:
        """
        Otimiza plano de corte gerando múltiplas soluções
        
        Args:
            items_pedido: Items que devem ser produzidos (com quantidade)
            items_estoque: Items disponíveis em estoque
            max_solucoes: Quantas soluções (top) retornar
        
        Returns:
            Lista ordenada de top 'max_solucoes' melhores soluções
        """
        
        inicio = time.time()
        
        todos_items = items_pedido + items_estoque
        gerador = GeradorPadroes(self.chapa, self.min_aproveitamento)
        padroes_validos = gerador.gerar_padroes_validos(todos_items)
        
        if not padroes_validos:
            return [SolucaoOtimizacao(
                padroes=[],
                tempo_processamento_ms=0,
                items_cobertos={}
            )]
        
        solucoes = []
        
        estrategias = [
            ("maximizar_aproveitamento", 1.0),
            ("minimizar_chapas", 0.5),
            ("balanceado", 0.7),
        ]
        
        for estrategia_nome, peso_aproveitamento in estrategias[:max_solucoes]:
            self.solver.Clear()
            solucao = self._resolver_modelo(
                padroes_validos, items_pedido, 
                peso_aproveitamento, estrategia_nome
            )
            
            if solucao:
                solucoes.append(solucao)
        
        solucoes.sort(key=lambda x: x.aproveitamento_total, reverse=True)
        
        for i, sol in enumerate(solucoes, 1):
            sol.ranking = i
            sol.tempo_processamento_ms = (time.time() - inicio) * 1000
        
        return solucoes[:max_solucoes]
    
    def _resolver_modelo(self, padroes: List[Padrao], 
                        items_pedido: List[Item],
                        peso_aproveitamento: float,
                        estrategia: str) -> Optional[SolucaoOtimizacao]:
        x = {}
        for i, padrao in enumerate(padroes):
            x[i] = self.solver.IntVar(0, 1000, f'padrao_{i}')
        
        demanda_por_codigo = {item.codigo: item.quantidade 
                              for item in items_pedido}
        
        for codigo, quantidade_demandada in demanda_por_codigo.items():
            constraint = self.solver.Constraint(
                quantidade_demandada, 
                self.solver.infinity(), 
                f'demanda_{codigo}'
            )
            
            for i, padrao in enumerate(padroes):
                idx_item = next(
                    (j for j, item in enumerate(padrao.items) 
                     if item.codigo == codigo), 
                    None
                )
                
                if idx_item is not None:
                    qtd_item_padrao = padrao.quantidades[idx_item]
                    constraint.SetCoefficient(x[i], qtd_item_padrao)
        
        objetivo = self.solver.Objective()
        
        if estrategia == "minimizar_chapas":
            for i in x:
                objetivo.SetCoefficient(x[i], 1.0)
        else:
            for i, padrao in enumerate(padroes):
                aproveitamento = padrao.soma_largura / self.chapa.largura
                objetivo.SetCoefficient(x[i], -aproveitamento)
        
        objetivo.SetMinimization()
        
        status = self.solver.Solve()
        
        if status != pywraplp.Solver.OPTIMAL:
            return None
        
        padroes_usados = []
        for i in x:
            if x[i].solution_value() > 0.5:
                qtd_uso = int(round(x[i].solution_value()))
                padroes_usados.append((padroes[i], qtd_uso))
        
        solucao = self._montar_solucao(padroes_usados, items_pedido)
        return solucao
    
    def _montar_solucao(self, padroes_usados: List[Tuple[Padrao, int]],
                       items_pedido: List[Item]) -> SolucaoOtimizacao:
        
        padroes_finais = []
        items_cobertos = {}
        aproveitamento_total = 0.0
        
        for padrao, qtd_uso in padroes_usados:
            padroes_finais.append(padrao)
            
            for item, qtd_item in zip(padrao.items, padrao.quantidades):
                items_cobertos[item.codigo] = items_cobertos.get(item.codigo, 0) + qtd_item
            
            aproveitamento_total += padrao.aproveitamento * qtd_uso
        
        num_chapas = len(padroes_finais)
        
        if num_chapas > 0:
            aproveitamento_total /= num_chapas
        
        return SolucaoOtimizacao(
            padroes=padroes_finais,
            aproveitamento_total=aproveitamento_total,
            chapas_necessarias=num_chapas,
            items_cobertos=items_cobertos
        )
