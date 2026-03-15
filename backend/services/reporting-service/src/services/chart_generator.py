"""Server-side SVG chart generation for report embedding."""

from __future__ import annotations

from src.models.domain import ReportStatistics

# Severity colors matching CSS
SEVERITY_COLORS = {
    "critical": "#dc2626",
    "high": "#ea580c",
    "medium": "#ca8a04",
    "low": "#2563eb",
    "info": "#6b7280",
}


def generate_severity_pie_chart(statistics: ReportStatistics) -> str:
    """Generate an SVG pie chart showing finding severity distribution."""
    total = statistics.total_findings
    if total == 0:
        return "<p>No findings to display.</p>"

    data = []
    for sev in ["critical", "high", "medium", "low", "info"]:
        count = statistics.by_severity.get(sev, 0)
        if count > 0:
            data.append((sev, count, SEVERITY_COLORS.get(sev, "#6b7280")))

    # Build SVG pie chart
    svg_parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 250" width="400" height="250">',
    ]

    cx, cy, r = 120, 120, 100
    start_angle = 0.0

    import math

    for label, count, color in data:
        pct = count / total
        angle = pct * 360
        end_angle = start_angle + angle

        start_rad = math.radians(start_angle - 90)
        end_rad = math.radians(end_angle - 90)

        x1 = cx + r * math.cos(start_rad)
        y1 = cy + r * math.sin(start_rad)
        x2 = cx + r * math.cos(end_rad)
        y2 = cy + r * math.sin(end_rad)

        large_arc = 1 if angle > 180 else 0

        path = (
            f'<path d="M {cx},{cy} L {x1:.1f},{y1:.1f} '
            f'A {r},{r} 0 {large_arc},1 {x2:.1f},{y2:.1f} Z" '
            f'fill="{color}" stroke="white" stroke-width="2"/>'
        )
        svg_parts.append(path)
        start_angle = end_angle

    # Legend
    legend_y = 30
    for label, count, color in data:
        pct = count / total * 100
        svg_parts.append(
            f'<rect x="260" y="{legend_y}" width="14" height="14" fill="{color}" rx="2"/>'
            f'<text x="280" y="{legend_y + 12}" font-size="12" font-family="sans-serif" fill="#374151">'
            f'{label.upper()}: {count} ({pct:.0f}%)</text>'
        )
        legend_y += 24

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def generate_severity_bar_chart(statistics: ReportStatistics) -> str:
    """Generate an SVG horizontal bar chart for severity distribution."""
    total = statistics.total_findings
    if total == 0:
        return ""

    max_count = max(statistics.by_severity.values()) if statistics.by_severity else 1
    svg_parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 180" width="400" height="180">',
    ]

    y = 10
    for sev in ["critical", "high", "medium", "low", "info"]:
        count = statistics.by_severity.get(sev, 0)
        if count == 0:
            continue
        bar_width = (count / max_count) * 250
        color = SEVERITY_COLORS.get(sev, "#6b7280")

        svg_parts.append(
            f'<text x="0" y="{y + 14}" font-size="11" font-family="sans-serif" fill="#374151">'
            f'{sev.upper()}</text>'
            f'<rect x="80" y="{y}" width="{bar_width:.0f}" height="20" fill="{color}" rx="3"/>'
            f'<text x="{80 + bar_width + 6:.0f}" y="{y + 14}" font-size="11" '
            f'font-family="sans-serif" fill="#374151">{count}</text>'
        )
        y += 30

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)
