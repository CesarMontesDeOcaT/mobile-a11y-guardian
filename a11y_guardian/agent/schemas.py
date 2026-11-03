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
            # Accept line or line_number
            line = data.get("line") or data.get("line_number") or 0
            # Accept issue, description or criterion
            issue = data.get("issue") or data.get("description") or data.get("criterion") or ""
            # Accept suggested_code or recommendation
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
            # Capture 'suggestions', 'violations' or 'issues'
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