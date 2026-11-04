import re
from typing import Tuple, List, Optional
from a11y_guardian.ir import ScreenSemanticTree, UINode

class SwiftUIParser:
    """Parser estático para extraer el Árbol Semántico (IR) de vistas SwiftUI."""

    # Contenedores estructurales equivalentes a Row/Column/Card
    CONTAINERS = {"VStack", "HStack", "ZStack", "List", "Section", "ScrollView", "LazyVStack", "LazyHStack", "Group", "Form"}

    # Elementos interactivos nativos
    INTERACTIVE_COMPONENTS = {"Button", "NavigationLink", "Toggle", "TextField", "SecureField"}

    # Elementos de contenido visual/texto
    CONTENT_COMPONENTS = {"Text", "Image", "Label", "AsyncImage"}

    def __init__(self):
        # Expresión para identificar el nombre de la View
        self.view_regex = re.compile(r"struct\s+([A-Za-z0-9_]+)\s*:\s*.*View")

        # Expresión para llamadas a componentes UI
        self.component_regex = re.compile(r"\b([A-Za-z0-9_]+)\s*(\(.*?\)|\{)")

    def clean_and_extract(self, code: str) -> Tuple[ScreenSemanticTree, str]:
        lines = code.splitlines()
        view_name = self._find_view_name(lines) or "SwiftUIView"

        root_nodes: List[UINode] = []
        in_preview = False
        preview_brace_depth = 0
        distilled_lines: List[str] = []

        for idx, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()

            # 1. Ignorar bloques de Preview (#Preview o PreviewProvider)
            if line.startswith("#Preview") or "PreviewProvider" in line:
                in_preview = True
                preview_brace_depth += line.count("{") - line.count("}")
                continue

            if in_preview:
                preview_brace_depth += line.count("{") - line.count("}")
                if preview_brace_depth <= 0:
                    in_preview = False
                continue

            # 2. Ignorar imports y directivas de preprocesador
            if line.startswith("import ") or line.startswith("//") or not line:
                continue

            # 3. Guardar en el código destilado numerado
            distilled_lines.append(f"{idx}: {raw_line}")

            # 4. Detección de nodos semánticos
            node = self._analyze_line(idx, raw_line, lines)
            if node:
                root_nodes.append(node)

        tree = ScreenSemanticTree(
            file_path="",
            composable_name=view_name,
            root_nodes=root_nodes
        )

        return tree, "\n".join(distilled_lines)

    def _find_view_name(self, lines: List[str]) -> Optional[str]:
        for line in lines:
            match = self.view_regex.search(line)
            if match:
                return match.group(1)
        return None

    def _analyze_line(self, line_number: int, current_line: str, all_lines: List[str]) -> Optional[UINode]:
        match = self.component_regex.search(current_line)
        if not match:
            return None

        comp_name = match.group(1)

        # Caso A: Contenedor (VStack, HStack, List, etc.)
        if comp_name in self.CONTAINERS:
            # Inspeccionar hasta 10 líneas subsiguientes para evaluar modificadores del contenedor
            subsequent_block = "\n".join(all_lines[line_number - 1 : min(line_number + 10, len(all_lines))])

            is_interactive = (
                    comp_name in self.INTERACTIVE_COMPONENTS or
                    ".onTapGesture" in subsequent_block
            )

            merged_descendants = (
                    ".accessibilityElement(children: .combine)" in subsequent_block or
                    ".accessibilityElement(children: .ignore)" in subsequent_block
            )

            return UINode(
                id=f"container_{line_number}",
                component_type="Container",
                line_number=line_number,
                is_interactive=is_interactive,
                merged_descendants=merged_descendants,
                children=[]
            )

        # Caso B: Botones o Controles Interactivos
        elif comp_name in self.INTERACTIVE_COMPONENTS:
            subsequent_block = "\n".join(all_lines[line_number - 1 : min(line_number + 10, len(all_lines))])
            merged_descendants = ".accessibilityElement(children: .combine)" in subsequent_block

            return UINode(
                id=f"container_{line_number}",
                component_type="Container",
                line_number=line_number,
                is_interactive=True,
                merged_descendants=merged_descendants,
                children=[]
            )

        # Caso C: Textos
        elif comp_name == "Text":
            return UINode(
                id=f"text_{line_number}",
                component_type="Text",
                line_number=line_number,
                is_interactive=False,
                merged_descendants=False,
                children=[]
            )

        # Caso D: Imágenes o Iconos
        elif comp_name in {"Image", "Label", "AsyncImage"}:
            return UINode(
                id=f"img_{line_number}",
                component_type="Image",
                line_number=line_number,
                is_interactive=False,
                merged_descendants=False,
                children=[]
            )

        return None