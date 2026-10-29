import logging
import os
from typing import Optional
from openai import OpenAI

from a11y_guardian.ir import ScreenSemanticTree
from a11y_guardian.agent.base import BaseA11yAuditor
from a11y_guardian.agent.schemas import A11yAuditResult

logger = logging.getLogger(__name__)

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
        self.model_name = model_name or os.environ.get("GROQ_MODEL", "meta-llama/llama-prompt-guard-2-86m")

    def audit_screen(self, tree: ScreenSemanticTree, distilled_code: str) -> A11yAuditResult:
        if "// a11y-ignore: all" in distilled_code:
            return A11yAuditResult(skipped=True, suggestions=[])

        user_content = self.build_user_prompt(tree, distilled_code)

        logger.info("Código numerado enviado a GROQ:\n%s", user_content)
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_instruction},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )

            raw_json = response.choices[0].message.content
            return A11yAuditResult.model_validate_json(raw_json)

        except Exception as e:
            print(f"[ERROR Groq] Error al auditar: {str(e)}")
            return A11yAuditResult(skipped=False, suggestions=[])