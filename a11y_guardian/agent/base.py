import re
from abc import ABC, abstractmethod
from pathlib import Path
from a11y_guardian.ir import ScreenSemanticTree
from a11y_guardian.agent.schemas import A11yAuditResult

class BaseA11yAuditor(ABC):
    """Interfaz base para todos los motores de auditoría con IA."""

    def __init__(self):
        # 1. Definimos rutas robustas basadas en el módulo actual
        # Asume que el directorio a11y_guardian/ está estructurado así:
        # a11y_guardian/
        # ├── agent/
        # │   └── base.py
        # ├── skills/
        # │   └── compose_merge_semantics_skill_template_android.md
        # └── rules/
        #     └── wcag_2_2_mobile.md

        base_dir = Path(__file__).resolve().parent.parent
        skill_path = base_dir / "skills" / "compose_merge_semantics_skill_template_android.md"
        rules_path = base_dir / "rules" / "wcag_2_2_mobile.md"

        # 2. Validación estricta. Falla si los archivos no existen en CI/CD
        if not skill_path.exists():
            raise FileNotFoundError(f"Falta el archivo crítico de la skill: {skill_path}")
        if not rules_path.exists():
            raise FileNotFoundError(f"Falta el archivo de reglas WCAG: {rules_path}")

        # 3. Lectura de contenido
        raw_skill = skill_path.read_text(encoding="utf-8")
        # Elimina el frontmatter (bloques de yaml entre ---)
        skill_content = re.sub(r"^---[\s\S]*?---\n", "", raw_skill).strip()

        wcag_content = f"\n\nMarco de referencia legal y técnico:\n{rules_path.read_text(encoding='utf-8')}".strip()

        # 4. Asigna la directiva consolidada
        self.system_instruction = f"{skill_content}\n\n{wcag_content}".strip()

        # Opcional: imprimir el tamaño para debug y confirmación
        print(f"[DEBUG BaseA11yAuditor] System Instructions cargadas exitosamente ({len(self.system_instruction)} caracteres).")

    def build_user_prompt(self, tree: ScreenSemanticTree, distilled_code: str) -> str:
        """
        Construye el prompt de usuario de forma genérica.
        Python solo establece el protocolo de reemplazo de líneas de GitHub.
        """
        code_fence = "```"
        return (
            f"Estructura de nodos detectada (IR):\n"
            f"{code_fence}json\n"
            f"{tree.model_dump_json(exclude_none=True, indent=2)}\n"
            f"{code_fence}\n\n"
            f"Código relevante numerado:\n"
            f"{code_fence}text\n"
            f"{distilled_code}\n"
            f"{code_fence}\n\n"
            "MECÁNICA DE REEMPLAZO (GITHUB INLINE SUGGESTION):\n"
            "- Cada elemento en 'suggestions' se ancla en 'line'.\n"
            "- GitHub reemplazará ÚNICAMENTE esa línea por el contenido de 'suggested_code'.\n"
            "- Para evitar duplicar código, 'suggested_code' no debe reescribir líneas adyacentes que deban permanecer intactas.\n\n"
            "Responde con un JSON estricto que comience en '{' y termine en '}':\n"
            '{"suggestions": [{"line": <int>, "issue": "<string>", "suggested_code": "<string>"}]}'
        )

    @abstractmethod
    def audit_screen(self, tree: ScreenSemanticTree, distilled_code: str) -> A11yAuditResult:
        """Método abstracto que cada proveedor de IA debe implementar obligatoriamente."""
        pass