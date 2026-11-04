import re
from abc import ABC, abstractmethod
from pathlib import Path
from a11y_guardian.ir import ScreenSemanticTree
from a11y_guardian.agent.schemas import A11yAuditResult

class BaseA11yAuditor(ABC):
    """Base interface for all AI auditing engines."""

    def __init__(self, language: str = "kotlin"):
        # 1. Define robust paths based on the current module
        # Assumes the a11y_guardian/ directory is structured as follows:
        # a11y_guardian/
        # ├── agent/
        # │   └── base.py
        # ├── skills/
        # │   └── compose_accessibility_skill_template.md
        # │   └── swiftui_accessibility_skill_template.md
        # └── rules/
        #     └── wcag_2_2_mobile.md
        if language == "swift":
            skill_filename = "swiftui_accessibility_skill_template.md"
        else:
            skill_filename = "compose_accessibility_skill_template.md"

        base_dir = Path(__file__).resolve().parent.parent
        skill_path = base_dir / "skills" / skill_filename
        rules_path = base_dir / "rules" / "wcag_2_2_mobile.md"

        # 2. Strict validation. Fail if the files do not exist in CI/CD
        if not skill_path.exists():
            raise FileNotFoundError(f"Missing critical skill file: {skill_path}")
        if not rules_path.exists():
            raise FileNotFoundError(f"Missing WCAG rules file: {rules_path}")

        # 3. Read content
        raw_skill = skill_path.read_text(encoding="utf-8")
        # Remove frontmatter (yaml blocks between ---)
        skill_content = re.sub(r"^---[\s\S]*?---\n", "", raw_skill).strip()

        wcag_content = f"\n\nLegal and technical reference framework:\n{rules_path.read_text(encoding='utf-8')}".strip()

        # 4. Assign the consolidated directive
        self.system_instruction = f"{skill_content}\n\n{wcag_content}".strip()

        # Optional: print the size for debug and confirmation
        print(f"[DEBUG BaseA11yAuditor] System Instructions loaded successfully ({len(self.system_instruction)} characters).")

    def build_user_prompt(self, tree: ScreenSemanticTree, distilled_code: str) -> str:
        """
        Build the user prompt in a generic way.
        Python only establishes the GitHub line replacement protocol.
        """
        code_fence = "```"
        return (
            f"Detected node structure (IR):\n"
            f"{code_fence}json\n"
            f"{tree.model_dump_json(exclude_none=True, indent=2)}\n"
            f"{code_fence}\n\n"
            f"Numbered relevant code:\n"
            f"{code_fence}text\n"
            f"{distilled_code}\n"
            f"{code_fence}\n\n"
            "GITHUB INLINE SUGGESTION MECHANICS:\n"
            "- Each item in 'suggestions' is anchored at 'line'.\n"
            "- GitHub will ONLY replace that line with the content of 'suggested_code'.\n"
            "- To avoid duplicating code, 'suggested_code' should not overwrite adjacent lines that must remain intact.\n\n"
            "Respond with strict JSON starting with '{' and ending with '}':\n"
            '{"suggestions": [{"line": <int>, "issue": "<string>", "suggested_code": "<string>"}]}'
        )

    @abstractmethod
    def audit_screen(self, tree: ScreenSemanticTree, distilled_code: str) -> A11yAuditResult:
        """Abstract method that each AI provider must implement."""
        pass