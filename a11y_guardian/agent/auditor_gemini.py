import logging
import os
import re
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. Esquemas de salida estructurada (Pydantic)
# ---------------------------------------------------------------------------

class InlineSuggestion(BaseModel):
    line: int = Field(
        description="Número exacto de línea en el código numerado donde se anclará la sugerencia en GitHub"
    )
    issue: str = Field(
        description="Explicación concisa en una sola oración del problema de navegación en TalkBack"
    )
    suggested_code: str = Field(
        description="Código de reemplazo exacto, con la indentación correcta, para el bloque suggestion de GitHub"
    )

class A11yAuditResult(BaseModel):
    skipped: bool = Field(
        default=False,
        description="True únicamente si el archivo o bloque contiene // a11y-ignore global"
    )
    suggestions: List[InlineSuggestion] = Field(
        default_factory=list,
        description="Lista de sugerencias de accesibilidad detectadas"
    )

# ---------------------------------------------------------------------------
# 2. Orquestador del Auditor con Gemini
# ---------------------------------------------------------------------------
# class ClaudeA11yAuditor:
#     def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
#         api_key = api_key or os.environ.get("CLAUDE_API_KEY")
#         if not api_key:
#             raise ValueError(
#                 "No se encontró CLAUDE_API_KEY. Configúrala en tu entorno o en los Secrets de GitHub."
#             )


class GeminiA11yAuditor:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "No se encontró GEMINI_API_KEY. Configúrala en tu entorno o en los Secrets de GitHub."
            )

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name or os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")

        # Cargar skill y reglas relativas a la carpeta del paquete
        base_dir = Path(__file__).resolve().parent.parent
        skill_path = base_dir / "skills" / "compose_merge_semantics.md"
        rules_path = base_dir / "rules" / "wcag_2_2_mobile.md"

        skill_content = ""
        if skill_path.exists():
            raw_skill = skill_path.read_text(encoding="utf-8")
            skill_content = re.sub(r"^---[\s\S]*?---\n", "", raw_skill)
        else:
            skill_content = "Auditor de accesibilidad móvil para TalkBack y Jetpack Compose."

        wcag_content = ""
        if rules_path.exists():
            wcag_content = f"\n\nMarco de referencia normativo:\n{rules_path.read_text(encoding='utf-8')}"

        self.system_instruction = f"{skill_content}\n{wcag_content}".strip()

    def audit_screen(self, numbered_code: str) -> A11yAuditResult:
        if "// a11y-ignore: all" in numbered_code:
            return A11yAuditResult(skipped=True, suggestions=[])

        code_fence = "```"
        user_content = (
            "Analiza el siguiente código fuente numerado y genera sugerencias inline para corregir los problemas de merge de accesibilidad:\n\n"
            f"{code_fence}text\n"
            f"{numbered_code}\n"
            f"{code_fence}"
        )

        config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=A11yAuditResult,
        )

        try:
            logger.info("Código numerado enviado a Gemini:\n%s", numbered_code)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_content,
                config=config,
            )

            if hasattr(response, "parsed") and response.parsed is not None:
                return response.parsed

            return A11yAuditResult.model_validate_json(response.text)

        except Exception as e:
            print(f"[ERROR] Error al auditar con Gemini: {str(e)}")
            return A11yAuditResult(skipped=False, suggestions=[])