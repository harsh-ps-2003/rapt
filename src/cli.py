"""CLI entry point for PromptLens."""

from __future__ import annotations

import argparse
import asyncio
import sys

from rich.console import Console

from src.analyzer import analyze
from src.methods import METHODS
from src.methods.paraphrase import Paraphrase
from src.providers import (
    PROVIDER_CONFIGS,
    Provider,
    call_llm,
    resolve_api_key,
    resolve_provider,
)
from src.renderer import console, create_progress, render_full, render_json

AVAILABLE_METHODS = list(METHODS.keys())
AVAILABLE_PROVIDERS = [p.value for p in Provider]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rapt",
        description=(
            "Colour-coded prompt saliency debugger for AI engineers.\n"
            "Analyze which phrases in your prompt actually drive model output."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  rapt system_prompt.md -p openai\n"
            "  rapt agent_rules.md -p anthropic -c 'Write a haiku about rust'\n"
            "  rapt prompt.md -p google -m omission --verbose\n"
            "  cat skills.md | rapt - -p openai --json\n"
        ),
    )

    parser.add_argument(
        "file",
        help="Prompt file to analyze (.md, .txt), or - for stdin",
    )
    parser.add_argument(
        "-p", "--provider",
        required=True,
        choices=AVAILABLE_PROVIDERS,
        help="LLM provider: openai, anthropic, or google",
    )
    parser.add_argument(
        "-m", "--method",
        default="perturbation",
        choices=AVAILABLE_METHODS,
        help="Saliency method (default: perturbation)",
    )
    parser.add_argument(
        "-c", "--context",
        default="",
        help="Fixed user message when analyzing a system prompt",
    )
    parser.add_argument(
        "--context-file",
        help="Load the fixed context from a file",
    )
    parser.add_argument(
        "--model",
        help="Override the default model for the provider",
    )
    parser.add_argument(
        "--api-key",
        help="API key (otherwise reads from env var)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=500,
        help="Max tokens for baseline response (default: 500)",
    )
    parser.add_argument(
        "--system",
        action="store_true",
        help="Treat the input file as a system prompt (context becomes the user message)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output raw JSON instead of coloured terminal",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show per-phrase scores in a table",
    )

    return parser


def _load_file(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        console.print(f"[red]Error:[/] File not found: {path}")
        sys.exit(1)
    except OSError as e:
        console.print(f"[red]Error:[/] Cannot read file: {e}")
        sys.exit(1)


async def _run(args: argparse.Namespace) -> None:
    prompt_text = _load_file(args.file)
    if not prompt_text.strip():
        console.print("[red]Error:[/] Prompt file is empty.")
        sys.exit(1)

    context_text = args.context
    if args.context_file:
        context_text = _load_file(args.context_file)

    provider = resolve_provider(args.provider)
    try:
        api_key = resolve_api_key(provider, args.api_key)
    except EnvironmentError as e:
        console.print(f"[red]Error:[/] {e}")
        sys.exit(1)

    method_cls = METHODS[args.method]
    if args.method == "paraphrase":
        async def _paraphrase_fn(text: str) -> str:
            return await call_llm(
                provider, api_key, text, "", max_tokens=60, model_override=args.model,
            )
        method = method_cls(paraphrase_fn=_paraphrase_fn)
    else:
        method = method_cls()

    progress = create_progress()

    with progress:
        task_id = progress.add_task("Analyzing...", total=100)

        def on_status(msg: str) -> None:
            progress.update(task_id, description=msg)

        def on_tick(done: int, total: int) -> None:
            pct = 10 + (done / total) * 85
            progress.update(task_id, completed=pct, description=f"{args.method}: {done}/{total} phrases")

        progress.update(task_id, completed=5)

        result = await analyze(
            prompt_text=prompt_text,
            context_text=context_text,
            method=method,
            provider=provider,
            api_key=api_key,
            model=args.model,
            max_tokens=args.max_tokens,
            analyze_as_system=args.system,
            on_status=on_status,
            on_tick=on_tick,
        )

        progress.update(task_id, completed=100, description="Done")

    if args.json_output:
        render_json(result)
    else:
        render_full(result, verbose=args.verbose)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        asyncio.run(_run(args))
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
        sys.exit(130)


if __name__ == "__main__":
    main()
