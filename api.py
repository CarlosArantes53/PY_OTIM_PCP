from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import logging
from models import Chapa, Item, TipoItem
from otimizador_ortools import OtimizadorORTools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ItemRequest(BaseModel):
    codigo: str
    comprimento: int
    quantidade: int
    tipo: str = "estoque"
    prioridade: int = 0

class ChapaRequest(BaseModel):
    largura: int
    comprimento: int
    espessura: int
    material: str = "aço"

class OtimizacaoRequest(BaseModel):
    items_pedido: List[ItemRequest]
    items_estoque: List[ItemRequest]
    chapa: ChapaRequest
    min_aproveitamento: float = 0.95
    max_solucoes: int = 5

class PadraoResponse(BaseModel):
    num_padrao: int
    items: List[str]
    quantidades: List[int]
    aproveitamento: str
    soma_largura: int

class SolucaoResponse(BaseModel):
    ranking: int
    aproveitamento: str
    chapas_necessarias: int
    padroes: List[PadraoResponse]

app = FastAPI(
    title="Otimizador de Corte",
    description="API para otimização de planos de corte de chapas",
    version="1.0.0"
)

@app.post("/otimizar", response_model=List[SolucaoResponse])
async def otimizar_plano_corte(request: OtimizacaoRequest):
    """
    Otimiza plano de corte de chapas metálicas
    
    Retorna top 5 melhores soluções ordenadas por aproveitamento
    
    **Restrições implementadas:**
    - Máximo 3 SKUs distintos por chapa
    - Aproveitamento mínimo de 95%
    - Soma de itens = largura da chapa
    - Demanda dos pedidos deve ser atendida
    """
    
    try:
        if not request.items_pedido:
            raise HTTPException(
                status_code=400,
                detail="Lista de itens pedido vazia"
            )
        
        if request.min_aproveitamento < 0.5 or request.min_aproveitamento > 1.0:
            raise HTTPException(
                status_code=400,
                detail="Aproveitamento mínimo deve estar entre 0.5 e 1.0"
            )
        
        chapa = Chapa(
            largura=request.chapa.largura,
            comprimento=request.chapa.comprimento,
            espessura=request.chapa.espessura,
            material=request.chapa.material
        )
        
        items_pedido = [
            Item(
                codigo=item.codigo,
                comprimento=item.comprimento,
                largura_maxima=chapa.largura,
                quantidade=item.quantidade,
                tipo=TipoItem.PEDIDO,
                prioridade=item.prioridade
            )
            for item in request.items_pedido
        ]
        
        items_estoque = [
            Item(
                codigo=item.codigo,
                comprimento=item.comprimento,
                largura_maxima=chapa.largura,
                quantidade=item.quantidade,
                tipo=TipoItem.ESTOQUE,
                prioridade=item.prioridade
            )
            for item in request.items_estoque
        ]
        
        logger.info(f"Iniciando otimização com {len(items_pedido)} items pedido")
        
        otimizador = OtimizadorORTools(chapa, request.min_aproveitamento)
        
        solucoes = otimizador.otimizar(
            items_pedido, 
            items_estoque,
            max_solucoes=request.max_solucoes
        )
        
        if not solucoes or not solucoes[0].padroes:
            raise HTTPException(
                status_code=400,
                detail="Nenhuma solução viável encontrada com as restrições"
            )
        
        logger.info(f"Otimização concluída. {len(solucoes)} soluções geradas")
        
        respostas = []
        for sol in solucoes:
            resumo = sol.resumo()
            resp = SolucaoResponse(
                ranking=resumo['ranking'],
                aproveitamento=resumo['aproveitamento'],
                chapas_necessarias=resumo['chapas_necessarias'],
                padroes=[
                    PadraoResponse(**p) 
                    for p in resumo['padroes']
                ]
            )
            respostas.append(resp)
        
        return respostas
    
    except Exception as e:
        logger.error(f"Erro na otimização: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Verifica saúde da API"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
