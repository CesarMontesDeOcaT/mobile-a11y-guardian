import os
import re
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from a11y_guardian.ir import ScreenSemanticTree

logger = logging.getLogger(__name__)

class InlineSuggestion(BaseModel):
    line: int = Field(description="Línea original donde se anclará la sugerencia en GitHub")
    issue: str = Field(description="Explicación en una oración del problema de lectura TalkBack")
    suggested_code: str = Field(description="Código exacto para el bloque suggestion de GitHub")

class A11yAuditResult(BaseModel):
    skipped: bool = Field(default=False)
    suggestions: List[InlineSuggestion] = Field(default_factory=list)

class GeminiA11yAuditor:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Falta GEMINI_API_KEY en las variables de entorno.")

        self.client = genai.Client(api_key=api_key)
        # Usamos gemini-3.8-flash estable
        self.model_name = model_name or os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")

        base_dir = Path(__file__).resolve().parent.parent
        skill_path = base_dir / "skills" / "compose_merge_semantics.md"
        rules_path = base_dir / "rules" / "wcag_2_2_mobile.md"

        skill_content = ""
        if skill_path.exists():
            raw_skill = skill_path.read_text(encoding="utf-8")
            skill_content = re.sub(r"^---[\s\S]*?---\n", "", raw_skill)

        wcag_content = ""
        if rules_path.exists():
            wcag_content = f"\n\nMarco de referencia:\n{rules_path.read_text(encoding='utf-8')}"

        self.system_instruction = f"{skill_content}\n{wcag_content}".strip()

    def audit_screen(self, tree: ScreenSemanticTree, distilled_code: str) -> A11yAuditResult:
        if "// a11y-ignore: all" in distilled_code:
            return A11yAuditResult(skipped=True, suggestions=[])

        # Se envía la estructura JSON destilada + el código sin imports/previews
        code_fence = "```"
        user_content = (
            "Estructura de nodos detectada (IR):\n"
            f"{code_fence}json\n"
            f"{tree.model_dump_json(exclude_none=True, indent=2)}\n"
            f"{code_fence}\n\n"
            "Código relevante numerado:\n"
            f"{code_fence}text\n"
            f"{distilled_code}\n"
            f"{code_fence}"
        )
        logger.info("Código numerado enviado a Gemini:\n%s", user_content)
        config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=A11yAuditResult,
        )

        try:
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