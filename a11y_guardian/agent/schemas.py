from typing import List
from pydantic import BaseModel, Field

class InlineSuggestion(BaseModel):
    line: int = Field(description="Línea original donde se anclará la sugerencia en GitHub")
    issue: str = Field(description="Explicación concisa en una sola oración del problema de lectura TalkBack")
    suggested_code: str = Field(description="Código exacto de reemplazo para el bloque suggestion de GitHub")

class A11yAuditResult(BaseModel):
    skipped: bool = Field(default=False, description="True si el Composable está marcado con // a11y-ignore")
    suggestions: List[InlineSuggestion] = Field(default_factory=list, description="Lista de sugerencias detectadas")