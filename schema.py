from pydantic import BaseModel, Field
from typing import List, Optional

class Item(BaseModel):
    classe: str = Field(..., description="erros | studio | xwork | integracao")
    titulo: str
    porque_ocorre: Optional[str] = ""
    tratativa: Optional[str] = ""
    resolucao: Optional[str] = ""
    link_da_base: Optional[str] = ""
    identificadores: List[str] = []

class IngestPayload(BaseModel):
    itens: List[Item]
