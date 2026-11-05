import os
from typing import Optional
from openai import OpenAI
from pydantic import ValidationError

from a11y_guardian.ir import ScreenSemanticTree
from a11y_guardian.agent.base import BaseA11yAuditor
from a11y_guardian.agent.schemas import A11yAuditResult

class GroqA11yAuditor(BaseA11yAuditor):
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None, language: str = "kotlin"):
        super().__init__(language=language)
        api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("No GROQ_API_KEY found in environment variables.")

        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key
        )
        self.model_name = model_name or os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b")
        print(f"[DEBUG Groq] Initialized auditor with model: {self.model_name}")

    def audit_screen(self, tree: ScreenSemanticTree, distilled_code: str) -> A11yAuditResult:
        if "// a11y-ignore: all" in distilled_code:
            print("[DEBUG Groq] Directive // a11y-ignore detected. Skipping analysis.")
            return A11yAuditResult(skipped=True, suggestions=[])

        user_content = self.build_user_prompt(tree, distilled_code)

        print(f"[DEBUG Groq] Sending request to Groq ({self.model_name})...")
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_instruction},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.0,
                max_tokens=2500,  # Aumentado para evitar truncamiento
                response_format={"type": "json_object"}
            )

            raw_json = response.choices[0].message.content
            print("\n==================== [DEBUG Groq: RESPUESTA RAW] ====================")
            print(raw_json)
            print("====================================================================\n")

            if not raw_json or raw_json.strip() == "{}":
                return A11yAuditResult(skipped=False, suggestions=[])

            parsed_result = A11yAuditResult.model_validate_json(raw_json)
            print(f"[DEBUG Groq] Successful parsing. Total suggestions identified: {len(parsed_result.suggestions)}")
            return parsed_result

        except Exception as e:
            print(f"[ERROR Groq] Exception during API call: {type(e).__name__} - {str(e)}")
            # If Groq attaches the failed generation snippet, we print it to the console
            if hasattr(e, "response") and hasattr(e.response, "json"):
                try:
                    err_data = e.response.json()
                    print(f"[DEBUG Groq Failed Generation]: {err_data.get('error', {}).get('failed_generation')}")
                except Exception:
                    pass
            return A11yAuditResult(skipped=False, suggestions=[])