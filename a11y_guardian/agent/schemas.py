from typing import Any, List
from pydantic import BaseModel, Field, model_validator

class InlineSuggestion(BaseModel):
    line: int = 0
    issue: str = ""
    suggested_code: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize_suggestion(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Acepta line o line_number
            line = data.get("line") or data.get("line_number") or 0
            # Acepta issue, description o criterion
            issue = data.get("issue") or data.get("description") or data.get("criterion") or ""
            # Acepta suggested_code o recommendation
            code = data.get("suggested_code") or data.get("recommendation") or ""

            return {
                "line": int(line),
                "issue": str(issue),
                "suggested_code": str(code)
            }
        return data

class A11yAuditResult(BaseModel):
    skipped: bool = False
    suggestions: List[InlineSuggestion] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_root(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Captura 'suggestions', 'violations' o 'issues'
            items = (
                    data.get("suggestions")
                    or data.get("violations")
                    or data.get("issues")
                    or []
            )
            return {
                "skipped": data.get("skipped", False),
                "suggestions": items
            }
        return data