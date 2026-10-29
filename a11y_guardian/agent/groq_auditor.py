import os
import json
from typing import Optional
from openai import OpenAI
from pydantic import ValidationError

from a11y_guardian.ir import ScreenSemanticTree
from a11y_guardian.agent.base import BaseA11yAuditor
from a11y_guardian.agent.schemas import A11yAuditResult

class GroqA11yAuditor(BaseA11yAuditor):
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        super().__init__()
        api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Falta GROQ_API_KEY en las variables de entorno.")

        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key
        )
        self.model_name = model_name or os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
        print(f"[DEBUG Groq] Inicializado auditor con modelo: {self.model_name}")

    def audit_screen(self, tree: ScreenSemanticTree, distilled_code: str) -> A11yAuditResult:
        if "// a11y-ignore: all" in distilled_code:
            print("[DEBUG Groq] Directiva // a11y-ignore: all detectada. Saltando análisis.")
            return A11yAuditResult(skipped=True, suggestions=[])

        user_content = self.build_user_prompt(tree, distilled_code)

        print(f"[DEBUG Groq] Enviando petición a Groq ({self.model_name})...")
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_instruction},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.0,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )

            raw_json = response.choices[0].message.content
            print("\n==================== [DEBUG Groq: RESPUESTA RAW] ====================")
            print(raw_json)
            print("====================================================================\n")

            if not raw_json or raw_json.strip() == "{}":
                print("[WARN Groq] El modelo devolvió un JSON vacío o sin contenido.")
                return A11yAuditResult(skipped=False, suggestions=[])

            # Intentar validación estricta con Pydantic
            try:
                parsed_result = A11yAuditResult.model_validate_json(raw_json)
                print(f"[DEBUG Groq] Parseo exitoso. Total sugerencias identificadas: {len(parsed_result.suggestions)}")
                return parsed_result
            except ValidationError as ve:
                print(f"[ERROR Groq] Falló la validación del esquema Pydantic:\n{ve}")
                # Fallback: intentar ver si metió las sugerencias bajo otra clave
                data = json.loads(raw_json)
                print(f"[DEBUG Groq] Claves recibidas en el objeto JSON: {list(data.keys())}")
                return A11yAuditResult(skipped=False, suggestions=[])

        except Exception as e:
            print(f"[ERROR Groq] Excepción durante la llamada a la API: {type(e).__name__} - {str(e)}")
            return A11yAuditResult(skipped=False, suggestions=[])