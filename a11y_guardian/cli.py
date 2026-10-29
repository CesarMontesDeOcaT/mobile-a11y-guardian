import json
import typer
from pathlib import Path
from a11y_guardian.parsers.compose import ComposeParser
from a11y_guardian.agent.factory import AuditorFactory

app = typer.Typer(help="Mobile A11y Guardian CLI")

@app.command()
def audit(
        file_path: Path = typer.Argument(..., help="Ruta al archivo .kt a auditar"),
        json_output: Path = typer.Option(None, "--json-output", help="Ruta para volcar el resultado JSON")
):
    if not file_path.exists():
        typer.secho(f"El archivo {file_path} no existe.", fg=typer.colors.RED)
        raise typer.Exit(1)

    code = file_path.read_text(encoding="utf-8")

    # 1. Poda local y extracción del Árbol Semántico (IR)
    parser = ComposeParser()
    tree, distilled_code = parser.clean_and_extract(code)
    tree.file_path = str(file_path)

    # 2. Short-circuit: Si no hay elementos de UI que auditar, omitir llamadas a APIs
    if not tree.root_nodes:
        typer.echo(f"Sin elementos analizables en {file_path.name}. Omitiendo llamada a IA.")
        if json_output:
            json_output.write_text("[]", encoding="utf-8")
        return

    # 3. Auditoría polimórfica (resuelve Groq o Gemini según A11Y_PROVIDER)
    auditor = AuditorFactory.create()
    result = auditor.audit_screen(tree, distilled_code)

    if result.skipped:
        if json_output:
            json_output.write_text("[]", encoding="utf-8")
        return

    comments = []
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