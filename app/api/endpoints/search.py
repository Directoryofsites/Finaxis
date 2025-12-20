from fastapi import APIRouter, Depends, HTTPException, Body
from app.services.smart_search import SmartSearchDispatcher
from pydantic import BaseModel

router = APIRouter()

class SearchQuery(BaseModel):
    query: str

@router.post("/smart")
def smart_search(search_data: SearchQuery):
    """
    Endpoint para procesar búsquedas inteligentes.
    Recibe un JSON { "query": "texto" } y retorna la acción a realizar.
    """
    if not search_data.query:
        raise HTTPException(status_code=400, detail="Query vacio")

    result = SmartSearchDispatcher.process_query(search_data.query)
    return result
