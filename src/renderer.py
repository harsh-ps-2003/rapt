"""Rich-based colour-coded terminal renderer for saliency results."""

from __future__ import annotations

import json

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.style import Style
from rich.table import Table
from rich.text import Text

from src.methods.base import SaliencyResult

console = Console()

# Gradient stops: blue (low) -> cyan (0.25) -> amber (0.5) -> orange (0.75) -> red (high)
_STOPS = [
    (0.00, ( 30,  80, 160)),
    (0.25, ( 40, 140, 210)),
    (0.50, (185, 130,   0)),
    (0.75, (235,  70,   0)),
    (1.00, (255,  30,   0)),
]


def _score_to_color(s: float) -> str:
    lo, hi = _STOPS[0], _STOPS[-1]
    for i in range(len(_STOPS) - 1):
        if _STOPS[i][0] <= s <= _STOPS[i + 1][0]:
            lo, hi = _STOPS[i], _STOPS[i + 1]
            break

    t_val = lo[0]
    t_hi = hi[0]
    t = 0.0 if t_hi == t_val else (s - t_val) / (t_hi - t_val)

    r = int(lo[1][0] + t * (hi[1][0] - lo[1][0]))
    g = int(lo[1][1] + t * (hi[1][1] - lo[1][1]))
    b = int(lo[1][2] + t * (hi[1][2] - lo[1][2]))
    return f"rgb({r},{g},{b})"


def create_progress() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    )


def render_header(result: SaliencyResult) -> None:
    header = Text()
    header.append("  rapt", style="bold bright_white")
    header.append("  |  ", style="dim")
    header.append(f"{result.provider}/{result.model}", style="cyan")
    header.append("  |  ", style="dim")
    header.append(result.method, style="yellow")
    header.append("  |  ", style="dim")
    header.append(f"{len(result.phrases)} phrases", style="green")
    console.print()
    console.print(header)
    console.print()


def render_saliency_map(result: SaliencyResult) -> None:
    console.rule("[bold]Saliency Map", style="dim")
    console.print()

    text = Text()
    for phrase, score in zip(result.phrases, result.norm_scores):
        pct = round(score * 100)
        color = _score_to_color(score)
        text.append(phrase, style=Style(color=color, bold=score > 0.7))
    console.print(text)
    console.print()


def render_saliency_map_verbose(result: SaliencyResult) -> None:
    console.rule("[bold]Saliency Map (verbose)", style="dim")
    console.print()

    table = Table(show_header=True, header_style="bold", expand=True, padding=(0, 1))
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Score", width=7, justify="right")
    table.add_column("Phrase")

    for i, (phrase, norm, raw) in enumerate(
        zip(result.phrases, result.norm_scores, result.raw_scores)
    ):
        pct = round(norm * 100)
        color = _score_to_color(norm)
        bar = "█" * max(1, round(norm * 20))
        score_str = f"{pct:3d}%"
        table.add_row(
            str(i + 1),
            Text(score_str, style=Style(color=color, bold=norm > 0.7)),
            Text(f"{bar} {phrase.strip()}", style=Style(color=color)),
        )

    console.print(table)
    console.print()


def render_stats(result: SaliencyResult) -> None:
    console.rule("[bold]Stats", style="dim")
    console.print()

    stats = result.stats
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim")
    table.add_column()
    table.add_row("Phrases", str(stats["phrase_count"]))

    top = stats["top_phrase"]
    if len(top) > 50:
        top = top[:48] + "..."
    table.add_row("Top phrase", f'"{top}"  ({stats["top_score"]}%)')
    table.add_row("Dead weight", f'{stats["dead_weight_pct"]}% of phrases below 25% impact')
    table.add_row("API calls", f'{result.api_calls} (1 baseline + {result.api_calls - 1} perturbations)')

    console.print(table)
    console.print()


def render_baseline(result: SaliencyResult) -> None:
    console.rule("[bold]Baseline Output", style="dim")
    console.print()
    baseline = result.baseline_output
    if len(baseline) > 800:
        baseline = baseline[:800] + "\n..."
    console.print(Panel(baseline, border_style="dim", expand=True, padding=(1, 2)))
    console.print()


def render_legend() -> None:
    legend = Text()
    legend.append("  Legend: ", style="dim")
    legend.append("██", style=Style(color=_score_to_color(0.1)))
    legend.append(" low impact  ", style="dim")
    legend.append("██", style=Style(color=_score_to_color(0.5)))
    legend.append(" medium  ", style="dim")
    legend.append("██", style=Style(color=_score_to_color(0.9)))
    legend.append(" high impact", style="dim")
    console.print(legend)
    console.print()


def render_full(result: SaliencyResult, *, verbose: bool = False) -> None:
    render_header(result)
    if verbose:
        render_saliency_map_verbose(result)
    else:
        render_saliency_map(result)
    render_stats(result)
    render_baseline(result)
    render_legend()


def render_json(result: SaliencyResult) -> None:
    output = {
        "method": result.method,
        "provider": result.provider,
        "model": result.model,
        "api_calls": result.api_calls,
        "stats": result.stats,
        "baseline_output": result.baseline_output,
        "phrases": [
            {
                "text": phrase.strip(),
                "raw_score": round(raw, 4),
                "norm_score": round(norm, 4),
                "impact_pct": round(norm * 100),
            }
            for phrase, raw, norm in zip(
                result.phrases, result.raw_scores, result.norm_scores
            )
        ],
    }
    console.print_json(json.dumps(output, indent=2))
