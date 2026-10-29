import logging
import os
import time
from typing import Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError

from a11y_guardian.ir import ScreenSemanticTree
from a11y_guardian.agent.base import BaseA11yAuditor
from a11y_guardian.agent.schemas import A11yAuditResult

logger = logging.getLogger(__name__)

class GeminiA11yAuditor(BaseA11yAuditor):
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        super().__init__()
        api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Falta GEMINI_API_KEY en las variables de entorno.")

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name or os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")

    def audit_screen(
            self,
            tree: ScreenSemanticTree,
            distilled_code: str,
            max_retries: int = 4,
            initial_delay: float = 3.0
    ) -> A11yAuditResult:
        if "// a11y-ignore: all" in distilled_code:
            return A11yAuditResult(skipped=True, suggestions=[])

        user_content = self.build_user_prompt(tree, distilled_code)
        logger.info("Código numerado enviado a Gemini:\n%s", user_content)
        config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=A11yAuditResult,
        )


        delay = initial_delay
        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_content,
                    config=config,
                )

                if hasattr(response, "parsed") and response.parsed is not None:
                    return response.parsed

                return A11yAuditResult.model_validate_json(response.text)

            except APIError as e:
                if e.code in [503, 429] and attempt < max_retries:
                    print(f"[RETRY Gemini] Servidor ocupado ({e.code}). Reintentando en {delay:.1f}s (Intento {attempt}/{max_retries})...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    print(f"[ERROR Gemini] Falló la auditoría tras {attempt} intentos: {e.message}")
                    return A11yAuditResult(skipped=False, suggestions=[])
            except Exception as e:
                print(f"[ERROR Gemini] Error inesperado: {str(e)}")
                return A11yAuditResult(skipped=False, suggestions=[])

        return A11yAuditResult(skipped=False, suggestions=[])