import json
import typer
from pathlib import Path
from a11y_guardian.parsers.compose import ComposeParser
from a11y_guardian.agent.auditor_gemini import GeminiA11yAuditor

app = typer.Typer(help="Mobile A11y Guardian CLI")

@app.command()
def audit(
    file_path: Path = typer.Argument(..., help="Ruta al archivo .kt o .swift a auditar"),
    json_output: Path = typer.Option(None, "--json-output", help="Ruta para volcar el resultado JSON para GitHub Actions")
):
    if not file_path.exists():
        typer.secho(f"El archivo {file_path} no existe.", fg=typer.colors.RED)
        raise typer.Exit(1)

    code = file_path.read_text(encoding="utf-8")
    
    # Numerar las líneas del código para mapeo exacto en Gemini
    code_lines = code.splitlines()
    numbered_code = "\n".join(f"{idx}: {line}" for idx, line in enumerate(code_lines, start=1))
    
    # Extracción de estructura semántica (IR)
    parser = ComposeParser()
    tree = parser.parse_source(str(file_path), code)

    # Si no hay nodos interactivos detectados, saltar el análisis para ahorrar tokens
    if not tree.root_nodes:
        typer.echo(f"Sin elementos de UI analizables en {file_path.name}. Saltando análisis.")
        if json_output:
            json_output.write_text("[]", encoding="utf-8")
        return

    # Invocación de la IA con el SDK de Gemini
    auditor = GeminiA11yAuditor()
    result = auditor.audit_screen(numbered_code)

    # Revisar si se disparó el escape hatch (// a11y-ignore) a nivel global
    if getattr(result, "skipped", False):
        typer.echo(f"Archivo {file_path.name} ignorado por directiva // a11y-ignore")
        if json_output:
            json_output.write_text("[]", encoding="utf-8")
        return

    comments = []
    # Formatear sugerencias para GitHub PR Comments
    for item in result.suggestions:
        body = (
            f"### ♿ A11y: Fragmentación de lectura en TalkBack\n\n"
            f"**Problema:** {item.issue}\n\n"
            f"```suggestion\n"
            f"{item.suggested_code}\n"
            f"```"
        )
        comments.append({
            "path": str(file_path),
            "line": item.line,
            "body": body
        })

    if json_output:
        json_output.write_text(json.dumps(comments, indent=2), encoding="utf-8")
    else:
        typer.echo(json.dumps(comments, indent=2))

if __name__ == "__main__":
    app()
