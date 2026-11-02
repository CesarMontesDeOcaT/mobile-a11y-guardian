import os
from typing import Optional
from a11y_guardian.agent.base import BaseA11yAuditor
from a11y_guardian.agent.gemini_auditor import GeminiA11yAuditor
from a11y_guardian.agent.groq_auditor import GroqA11yAuditor

class AuditorFactory:
    """ Factory to decouple the AI engine from the rest of the application."""

    @staticmethod
    def create(provider: Optional[str] = None) -> BaseA11yAuditor:
        selected = (provider or os.environ.get("A11Y_PROVIDER", "groq")).lower().strip()

        if selected == "gemini":
            return GeminiA11yAuditor()
        elif selected == "groq":
            return GroqA11yAuditor()
        else:
            raise ValueError(
                f"AI provider '{selected}' not supported. Available options: 'groq', 'gemini'."
            )