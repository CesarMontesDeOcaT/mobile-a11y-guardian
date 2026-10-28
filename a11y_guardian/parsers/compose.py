import re
from typing import List
from a11y_guardian.ir import UINode, ScreenSemanticTree

class ComposeParser:
    """Extractor de nodos y semántica básica para Jetpack Compose."""

    def parse_source(self, file_path: str, source_code: str) -> ScreenSemanticTree:
        # Busca la declaración del primer Composable como nombre de referencia
        composable_match = re.search(r"@Composable\s+fun\s+([A-Za-z0-9_]+)", source_code)
        composable_name = composable_match.group(1) if composable_match else "UnknownComposable"
        
        nodes: List[UINode] = []
        lines = source_code.splitlines()
        
        for idx, line in enumerate(lines, start=1):
            line_clean = line.strip()
            
            # Detecta contenedores que podrían necesitar agrupamiento semántico
            if any(k in line_clean for k in ["PokemonCard(", "Card(", "ListItem(", "Row(", "Column("]):
                has_merge = "mergeDescendants = true" in source_code
                nodes.append(UINode(
                    id=f"container_{idx}",
                    component_type="Container",
                    line_number=idx,
                    is_interactive=True,
                    merged_descendants=has_merge
                ))
                
            # Detecta imágenes o componentes gráficos
            elif any(k in line_clean for k in ["AsyncImage(", "Image(", "NetworkImage("]):
                desc_match = re.search(r'contentDescription\s*=\s*(null|"[^"]*")', line_clean)
                desc = desc_match.group(1) if desc_match else None
                nodes.append(UINode(
                    id=f"img_{idx}",
                    component_type="Image",
                    line_number=idx,
                    is_interactive=False,
                    content_description=desc
                ))
                
            # Detecta textos básicos
            elif "Text(" in line_clean:
                nodes.append(UINode(
                    id=f"text_{idx}",
                    component_type="Text",
                    line_number=idx
                ))
        
        return ScreenSemanticTree(
            file_path=file_path,
            composable_name=composable_name,
            root_nodes=nodes
        )
