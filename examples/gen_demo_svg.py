#!/usr/bin/env python3
"""Generate examples/rapt-demo.svg from captured rapt output data."""

from pathlib import Path

PHRASES = [
    (1,  56, "# Customer Support Agent"),
    (2,  27, "You are Aria, a senior customer support specialist at Luma,"),
    (3,  92, "a cloud-based project management platform used by software teams worldwide."),
    (4,  61, "## Persona"),
    (5,  26, "Your name is Aria."),
    (6,  58, "You are empathetic, concise, and technically fluent."),
    (7,  62, "You speak in a warm but professional tone."),
    (8, 100, "Avoid jargon unless the user is clearly a developer."),
    (9,  92, "Never be sarcastic or dismissive, even when a user is frustrated."),
    (10, 62, "## Your Mission"),
    (11, 32, "Help users resolve issues with Luma quickly and completely."),
    (12, 35, "A resolved issue means the user has what they need to move forward — not just a link to documentation."),
    (13,  6, "## Scope"),
    (14, 17, "You handle:"),
    (15, 66, "- Billing questions and subscription changes"),
    (16, 29, "- Bug reports and unexpected behavior"),
    (17, 64, "- Onboarding and feature walkthroughs"),
    (18, 60, "- Integration questions (GitHub, Slack, Jira, Figma)"),
    (19, 57, "- Account access, permissions, and SSO configuration"),
    (20, 21, "You do not handle:"),
    (21, 17, "- Feature requests (direct to feedback."),
    (22,  6, "luma."),
    (23, 61, "io)"),
    (24, 26, "- Legal or compliance questions (escalate to legal@luma."),
    (25, 13, "io)"),
    (26, 24, "- Refund decisions over $500 (escalate to billing@luma."),
    (27, 13, "io with full context)"),
    (28, 63, "## Response Format"),
    (29, 24, "Always structure your response as follows:"),
    (30,  0, "1."),
    (31, 27, "**Acknowledge** — one sentence confirming you understand what they need."),
    (32, 56, "2."),
    (33, 23, "**Resolve** — the clearest possible fix or answer."),
    (34, 32, "3."),
    (35, 16, "**Verify** — ask if this solved their problem or if they need more help."),
    (36, 23, "Keep responses under 200 words unless a step-by-step walkthrough is genuinely required."),
    (37, 20, "## Guardrails"),
    (38, 22, "- Never fabricate product features,"),
    (39, 18, "pricing tiers, or integration capabilities that are not in your knowledge base."),
    (40, 23, "- Never share another customer's data,"),
    (41, 62, "account details, or usage information."),
    (42, 21, "- Never promise a bug will be fixed by a specific date unless engineering has confirmed it."),
    (43, 19, "- If you are uncertain, say so clearly and offer to escalate rather than guessing."),
    (44, 30, "- Do not discuss competitors by name."),
    (45, 11, "If asked to compare, focus on Luma's strengths."),
    (46, 34, "## Tone Examples"),
    (47, 40, '**Good:** "That\'s frustrating — let me help you fix it right now.'),
    (48, 29, '"'),
    (49, 60, '**Bad:** "Unfortunately, this is a known limitation of the platform.'),
    (50, 15, '"'),
    (51, 62, '**Good:** "Here are the exact steps to reconnect your GitHub integration.'),
    (52, 15, '"'),
    (53, 62, '**Bad:** "Have you tried checking the documentation?'),
    (54, 33, '"'),
    (55, 65, "## Escalation Protocol"),
    (56, 19, "Escalate to a human agent when:"),
    (57, 13, "- The user has been waiting more than 48 hours for a response to a previous ticket."),
    (58, 15, "- The issue involves data loss or a security concern."),
    (59, 61, "- The user explicitly asks to speak to a human."),
    (60, 24, "- You have attempted two resolutions and neither has worked."),
    (61, 59, "To escalate, say: \"I'm going to loop in a specialist who can give this the dedicated attention it deserves."),
    (62, 22, "Can I get your email and a one-line summary of the issue?"),
    (63, 65, '"'),
    (64, 10, "## Context"),
    (65,  8, "Luma's current version is 4."),
    (66, 16, "2."),
    (67, 14, "The GitHub and Slack integrations were updated in version 4."),
    (68, 12, "1."),
    (69, 43, "The mobile app (iOS and Android) was released in version 3."),
    (70, 16, "8."),
    (71, 32, "SSO via SAML 2."),
    (72, 58, "0 is available on Business and Enterprise plans only."),
    (73, 30, "## Important Note"),
    (74, 59, "This is a support context."),
    (75, 17, "Be helpful."),
    (76, 21, "Responses should feel human."),
]

BASELINE = (
    "It sounds like your GitHub integration isn't syncing correctly after the Luma update, "
    "and I can certainly help you get that back on track.\n\n"
    "Often, after an update, integrations just need a quick refresh. Could you please try "
    "navigating to your Project Settings, then selecting the Integrations tab, and for the "
    "GitHub integration, click to Disconnect and then Reconnect? This usually resolves "
    "syncing issues.\n\n"
    "Please let me know if that gets your GitHub integration syncing again, or if you need "
    "further assistance!"
)

BG       = "#0d1117"
BG_ROW   = "#0d1117"
FG_DIM   = "#8b949e"
FG_HEAD  = "#e6edf3"
BORDER   = "#21262d"

def score_color(score: int) -> str:
    if score >= 67:
        return "#f85149"   # red
    elif score >= 34:
        return "#d29922"   # amber
    else:
        return "#388bfd"   # blue

def score_label_color(score: int) -> str:
    return score_color(score)

def bar(score: int) -> str:
    filled = round(score * 20 / 100)
    return "█" * filled + "░" * (20 - filled)

def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

FONT = "ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, monospace"
FONT_SIZE = 12
LINE_H = 20
PAD_X = 20
PAD_Y = 24

HEADER_LINES = [
    ("dim",    "$ uv run rapt examples/customer_support_agent.md -p google --system \\"),
    ("dim",    "      -c \"My GitHub integration stopped syncing after I updated Luma.\" -v"),
    ("blank",  ""),
    ("head",   "  rapt  |  google/gemini-2.5-flash  |  perturbation  |  76 phrases"),
    ("blank",  ""),
    ("sep",    "─" * 82),
    ("blank",  ""),
    ("head",   f"  {'#':>4}   {'Score':>5}   {'Bar':<22}  Phrase"),
    ("sep",    "─" * 82),
]

STATS_LINES = [
    ("sep",    "─" * 82),
    ("blank",  ""),
    ("head",   "  Stats"),
    ("blank",  ""),
    ("dim",    "  Phrases        76"),
    ("dim",    '  Top phrase     "Avoid jargon unless the user is clearly a develo…"  (100%)'),
    ("dim",    "  Dead weight    46% of phrases below 25% impact"),
    ("dim",    "  API calls      77 (1 baseline + 76 perturbations)"),
    ("blank",  ""),
    ("sep",    "─" * 82),
    ("blank",  ""),
    ("head",   "  Baseline Output"),
    ("blank",  ""),
]

baseline_wrapped = []
for para in BASELINE.split("\n\n"):
    words = para.split()
    line = "  "
    for w in words:
        if len(line) + len(w) + 1 > 84:
            baseline_wrapped.append(("dim", line.rstrip()))
            line = "  " + w + " "
        else:
            line += w + " "
    if line.strip():
        baseline_wrapped.append(("dim", line.rstrip()))
    baseline_wrapped.append(("blank", ""))

FOOTER_LINES = [
    ("blank",  ""),
    ("sep",    "─" * 82),
    ("blank",  ""),
    ("dim",    "  Legend:  "),
]

total_lines = len(HEADER_LINES) + len(PHRASES) + len(STATS_LINES) + len(baseline_wrapped) + len(FOOTER_LINES)
W = 900
H = PAD_Y + total_lines * LINE_H + PAD_Y + 30


def render_line(kind: str, text: str, y: int) -> str:
    x = PAD_X
    if kind == "blank":
        return ""
    if kind == "sep":
        return f'<text x="{x}" y="{y}" fill="{BORDER}" font-family="{FONT}" font-size="{FONT_SIZE}">{esc(text)}</text>'
    if kind == "dim":
        return f'<text x="{x}" y="{y}" fill="{FG_DIM}" font-family="{FONT}" font-size="{FONT_SIZE}">{esc(text)}</text>'
    if kind == "head":
        return f'<text x="{x}" y="{y}" fill="{FG_HEAD}" font-family="{FONT}" font-size="{FONT_SIZE}" font-weight="600">{esc(text)}</text>'
    return ""


def render_phrase_row(num: int, score: int, phrase: str, y: int) -> str:
    color = score_color(score)
    ch = score_label_color(score)
    num_str   = f"{num:>4}"
    score_str = f"{score:>3}%"
    bar_str   = bar(score)

    # char width approximation for monospace 12px ≈ 7.2px per char
    cw = 7.22
    x0 = PAD_X
    x_score = x0 + 5  * cw   # after "  #  "
    x_bar   = x0 + 12 * cw   # after score + gap
    x_phrase= x0 + 35 * cw   # after bar + gap

    parts = []
    parts.append(f'<text x="{x0}" y="{y}" fill="{FG_DIM}" font-family="{FONT}" font-size="{FONT_SIZE}">{esc(num_str)}</text>')
    parts.append(f'<text x="{x0 + 5*cw:.1f}" y="{y}" fill="{ch}" font-family="{FONT}" font-size="{FONT_SIZE}" font-weight="600">{esc(score_str)}</text>')
    parts.append(f'<text x="{x0 + 12*cw:.1f}" y="{y}" fill="{color}" font-family="{FONT}" font-size="{FONT_SIZE}">{esc(bar_str)}</text>')
    # Truncate phrase to keep within SVG width
    max_phrase_chars = 52
    display_phrase = phrase[:max_phrase_chars] + ("…" if len(phrase) > max_phrase_chars else "")
    parts.append(f'<text x="{x0 + 35*cw:.1f}" y="{y}" fill="{FG_HEAD}" font-family="{FONT}" font-size="{FONT_SIZE}">{esc(display_phrase)}</text>')
    return "\n".join(parts)


def build_svg() -> str:
    lines_svg: list[str] = []
    y = PAD_Y + LINE_H

    for kind, text in HEADER_LINES:
        svg = render_line(kind, text, y)
        if svg:
            lines_svg.append(svg)
        y += LINE_H

    for num, score, phrase in PHRASES:
        lines_svg.append(render_phrase_row(num, score, phrase, y))
        y += LINE_H

    for kind, text in STATS_LINES:
        svg = render_line(kind, text, y)
        if svg:
            lines_svg.append(svg)
        y += LINE_H

    for kind, text in baseline_wrapped:
        svg = render_line(kind, text, y)
        if svg:
            lines_svg.append(svg)
        y += LINE_H

    for kind, text in FOOTER_LINES:
        svg = render_line(kind, text, y)
        if svg:
            lines_svg.append(svg)
        y += LINE_H

    # Legend colored squares
    legend_y = y - LINE_H
    cw = 7.22
    lx = PAD_X + 12 * cw
    sq = 12
    labels = [("low impact", "#388bfd"), ("medium", "#d29922"), ("high impact", "#f85149")]
    for label, col in labels:
        lines_svg.append(f'<rect x="{lx:.1f}" y="{legend_y - sq + 2}" width="{sq}" height="{sq}" rx="2" fill="{col}"/>')
        lx += sq + 4
        lines_svg.append(f'<text x="{lx:.1f}" y="{legend_y}" fill="{FG_DIM}" font-family="{FONT}" font-size="{FONT_SIZE}">{label}</text>')
        lx += len(label) * cw + 16

    actual_h = y + PAD_Y
    body = "\n  ".join(lines_svg)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{actual_h}" viewBox="0 0 {W} {actual_h}">
  <rect width="{W}" height="{actual_h}" rx="8" fill="{BG}"/>
  <!-- top bar -->
  <rect width="{W}" height="32" rx="8" fill="#161b22"/>
  <rect y="24" width="{W}" height="8" fill="#161b22"/>
  <circle cx="20" cy="16" r="6" fill="#f85149"/>
  <circle cx="40" cy="16" r="6" fill="#d29922"/>
  <circle cx="60" cy="16" r="6" fill="#3fb950"/>
  <text x="{W//2}" y="20" fill="{FG_DIM}" font-family="{FONT}" font-size="11" text-anchor="middle">rapt — prompt saliency</text>
  {body}
</svg>"""


out = Path(__file__).parent / "rapt-demo.svg"
out.write_text(build_svg())
print(f"Written {out}  ({out.stat().st_size // 1024} KB)")
