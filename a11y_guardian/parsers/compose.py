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
        in_block_comment = False
        composable_name = "UnknownComposable"
        saw_composable_annotation = False

        for idx, line in enumerate(lines, start=1):
            line_strip = line.strip()

            # 1. Ignorar comentarios en bloque (licencias de copyright al inicio)
            if line_strip.startswith("/*"):
                in_block_comment = True
            if in_block_comment:
                if "*/" in line_strip:
                    in_block_comment = False
                continue

            # 2. Ignorar imports, packages y líneas vacías de cabecera
            if line_strip.startswith("import ") or line_strip.startswith("package "):
                continue

            # 3. Detectar si entramos en un bloque Preview
            if "@Preview" in line_strip:
                in_preview = True
                continue

            # Si estamos en preview, omitir hasta que termine la función
            if in_preview:
                # Si encontramos un Composable que NO tiene "Preview" en su nombre, salimos del preview
                if "fun " in line_strip and "Preview" not in line_strip:
                    in_preview = False
                else:
                    continue

            # 4. Capturar el nombre real del Composable (soporta @Composable en línea separada)
            if line_strip.startswith("@Composable"):
                saw_composable_annotation = True
                continue

            if saw_composable_annotation:
                if "fun " in line_strip:
                    match = re.search(r"fun\s+([A-Za-z0-9_]+)", line_strip)
                    if match and composable_name == "UnknownComposable" and "Preview" not in match.group(1):
                        composable_name = match.group(1)
                    saw_composable_annotation = False
                elif not line_strip.startswith("@"):  # Si no es otra anotación intermedia
                    saw_composable_annotation = False

            # 5. Extraer nodos para el árbol semántico
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
            elif "Text(" in line_strip or "PokedexText(" in line_strip:
                nodes.append(UINode(
                    id=f"text_{idx}",
                    component_type="Text",
                    line_number=idx
                ))

            # Solo agregar líneas relevantes
            if line_strip:
                cleaned_lines.append(f"{idx}: {line}")

        tree = ScreenSemanticTree(
            file_path="",
            composable_name=composable_name,
            root_nodes=nodes
        )
        return tree, "\n".join(cleaned_lines)