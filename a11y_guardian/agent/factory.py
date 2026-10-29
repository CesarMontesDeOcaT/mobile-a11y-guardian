import os
from typing import Optional
from a11y_guardian.agent.base import BaseA11yAuditor
from a11y_guardian.agent.gemini_auditor import GeminiA11yAuditor
from a11y_guardian.agent.groq_auditor import GroqA11yAuditor

class AuditorFactory:
    """Factory para desacoplar el motor de IA del resto de la aplicación."""

    @staticmethod
    def create(provider: Optional[str] = None) -> BaseA11yAuditor:
        selected = (provider or os.environ.get("A11Y_PROVIDER", "groq")).lower().strip()

        if selected == "gemini":
            return GeminiA11yAuditor()
        elif selected == "groq":
            return GroqA11yAuditor()
        else:
            raise ValueError(
                f"Proveedor de IA '{selected}' no soportado. Opciones disponibles: 'groq', 'gemini'."
            )