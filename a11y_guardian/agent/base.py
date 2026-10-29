import re
from abc import ABC, abstractmethod
from pathlib import Path
from a11y_guardian.ir import ScreenSemanticTree
from a11y_guardian.agent.schemas import A11yAuditResult

class BaseA11yAuditor(ABC):
    """Interfaz base para todos los motores de auditoría con IA."""

    def __init__(self):
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
            wcag_content = f"\n\nMarco de referencia:\n{rules_path.read_text(encoding='utf-8')}"

        self.system_instruction = f"{skill_content}\n{wcag_content}".strip()

    def build_user_prompt(self, tree: ScreenSemanticTree, distilled_code: str) -> str:
        """Construye un payload estructurado uniforme para cualquier LLM."""
        code_fence = "```"
        return (
            f"Estructura de nodos detectada (IR):\n"
            f"{code_fence}json\n"
            f"{tree.model_dump_json(exclude_none=True, indent=2)}\n"
            f"{code_fence}\n\n"
            f"Código relevante numerado:\n"
            f"{code_fence}text\n"
            f"{distilled_code}\n"
            f"{code_fence}"
        )

    @abstractmethod
    def audit_screen(self, tree: ScreenSemanticTree, distilled_code: str) -> A11yAuditResult:
        """Método abstracto que cada proveedor de IA debe implementar obligatoriamente."""
        pass