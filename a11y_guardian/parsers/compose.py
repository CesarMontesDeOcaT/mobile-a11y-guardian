import re
from typing import List, Tuple
from a11y_guardian.ir import UINode, ScreenSemanticTree

class ComposeParser:
    """Extractor semántico y podador de ruido para Jetpack Compose."""

    def clean_and_extract(self, source_code: str) -> Tuple[ScreenSemanticTree, str]:
        lines = source_code.splitlines()
        nodes: List[UINode] = []
        cleaned_lines: List[str] = []

        in_preview = False
        composable_name = "UnknownComposable"

        for idx, line in enumerate(lines, start=1):
            line_strip = line.strip()

            # 1. Ignorar imports y paquetes para no gastar tokens
            if line_strip.startswith("import ") or line_strip.startswith("package "):
                continue

            # 2. Descartar bloques @Preview (no afectan la accesibilidad en runtime)
            if "@Preview" in line_strip:
                in_preview = True
                continue

            # Detectar salida del bloque preview al encontrar un composable nuevo
            if in_preview:
                if line_strip.startswith("@Composable") or line_strip.startswith("fun "):
                    # Asumimos que los previews suelen ser funciones cortas
                    if "Preview" in line_strip:
                        continue
                    else:
                        in_preview = False
                else:
                    continue

            # Detectar nombre del primer Composable de producción
            if "@Composable" in line_strip:
                match = re.search(r"fun\s+([A-Za-z0-9_]+)", line_strip)
                if match and composable_name == "UnknownComposable" and "Preview" not in match.group(1):
                    composable_name = match.group(1)

            # 3. Extraer nodos relevantes para el árbol semántico (IR)
            if any(k in line_strip for k in ["Card(", "Row(", "Column(", "ListItem(", "PokemonCard("]):
                has_merge = "mergeDescendants = true" in source_code
                nodes.append(UINode(
                    id=f"container_{idx}",
                    component_type="Container",
                    line_number=idx,
                    is_interactive=True,
                    merged_descendants=has_merge
                ))
            elif any(k in line_strip for k in ["Image(", "AsyncImage(", "LandscapistImage(", "Icon("]):
                desc_match = re.search(r'contentDescription\s*=\s*(null|"[^"]*")', line_strip)
                desc = desc_match.group(1) if desc_match else None
                nodes.append(UINode(
                    id=f"img_{idx}",
                    component_type="Image",
                    line_number=idx,
                    content_description=desc
                ))
            elif "Text(" in line_strip:
                nodes.append(UINode(
                    id=f"text_{idx}",
                    component_type="Text",
                    line_number=idx
                ))

            # Conservamos el número de línea original para que GitHub ancle el comentario en el lugar exacto
            cleaned_lines.append(f"{idx}: {line}")

        tree = ScreenSemanticTree(
            file_path="",
            composable_name=composable_name,
            root_nodes=nodes
        )
        return tree, "\n".join(cleaned_lines)