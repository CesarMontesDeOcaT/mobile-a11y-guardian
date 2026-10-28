import os
import re
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class InlineSuggestion(BaseModel):
    start_line: int = Field(description="Línea donde inicia el bloque a reemplazar")
    end_line: int = Field(description="Línea donde termina el bloque a reemplazar")
    issue_explanation: str = Field(description="Explicación en una oración del gap de navegación")
    suggested_code: str = Field(description="Fragmento de código corregido para el bloque suggestion de GitHub")

class A11yAuditResult(BaseModel):
    skipped: bool = Field(default=False, description="True si se detectó // a11y-ignore")
    suggestions: List[InlineSuggestion] = Field(default_factory=list)

class GeminiA11yAuditor:
    def __init__(self, api_key: Optional[str] = None):
        self.client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))
        self.model_name = "gemini-1.5-flash"

        # Cargar el archivo de skill
        skill_path = Path(__file__).resolve().parent.parent / "skills" / "compose_merge_semantics.md"
        raw_skill = skill_path.read_text(encoding="utf-8")

        # Eliminar el frontmatter YAML (--- metadata ---) para dejar solo el cuerpo del prompt
        self.skill_prompt = re.sub(r"^---[\s\S]*?---\n", "", raw_skill)

    def audit_screen(self, code_snippet: str) -> A11yAuditResult:
        # Si el desarrollador marcó el archivo completo o el bloque
        if "// a11y-ignore" in code_snippet:
            return A11yAuditResult(skipped=True)

        config = types.GenerateContentConfig(
            system_instruction=self.skill_prompt,
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=A11yAuditResult,
        )

        user_content = f"""
Analiza el siguiente código Kotlin/Compose con base en tus reglas de Merge Semantics:

```kotlin
{code_snippet}