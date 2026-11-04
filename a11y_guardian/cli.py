import json
import textwrap
import typer
from pathlib import Path
from a11y_guardian.parsers.compose import ComposeParser
from a11y_guardian.parsers.swift import SwiftUIParser
from a11y_guardian.agent.factory import AuditorFactory

app = typer.Typer(help="Mobile A11y Guardian CLI")

def align_indentation(suggested_code: str, original_line: str) -> str:
    """
    Adjusts the suggested code to match the exact base indentation of the original line in the source file.
    """
    # 1. Detect how many leading spaces the original line has
    leading_spaces = len(original_line) - len(original_line.lstrip(" "))
    target_indent = " " * leading_spaces

    # 2. Normalize the LLM block to indentation 0 (remove inconsistent indents)
    dedented = textwrap.dedent(suggested_code).strip("\r\n")

    # 3. Re-indent each line with the exact spaces from the original file
    return textwrap.indent(dedented, target_indent)

@app.command()
def audit(
        file_path: Path = typer.Argument(..., help="Path to the .kt file to audit"),
        json_output: Path = typer.Option(None, "--json-output", help="Path to dump the JSON result")
):
    if not file_path.exists():
        typer.secho(f"The file {file_path} does not exist.", fg=typer.colors.RED)
        raise typer.Exit(1)

    # 1. Detect language and parser based on extension
    file_extension = file_path.suffix.lower()
    if file_extension == ".swift":
        language = "swift"
        parser = SwiftUIParser()
    else:
        language = "kotlin"
        parser = ComposeParser()

    code = file_path.read_text(encoding="utf-8")
    code_lines = code.splitlines()

    # 2. Local pruning and extraction of the Semantic Tree (IR)
    tree, distilled_code = parser.clean_and_extract(code)
    tree.file_path = str(file_path)

    # 3. Short-circuit: If there are no UI elements, skip AI calls
    if not tree.root_nodes:
        typer.echo(f"No analyzable elements in {file_path.name}. Skipping AI call.")
        if json_output:
            json_output.write_text("[]", encoding="utf-8")
        return

    # 4. Polymorphic auditing (Groq / Gemini)
    auditor = AuditorFactory.create(language=language)
    result = auditor.audit_screen(tree, distilled_code)

    if result.skipped:
        if json_output:
            json_output.write_text("[]", encoding="utf-8")
        return

    comments = []
    for item in result.suggestions:
        # Get the original code line to calculate its indentation
        if 1 <= item.line <= len(code_lines):
            orig_line = code_lines[item.line - 1]
            aligned_code = align_indentation(item.suggested_code, orig_line)
        else:
            aligned_code = item.suggested_code

        body = (
            f"### ♿ A11y: Fragmentation of reading in TalkBack\n\n"
            f"**Problem:** {item.issue}\n\n"
            f"```suggestion\n"
            f"{aligned_code}\n"
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