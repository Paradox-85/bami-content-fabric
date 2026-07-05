# Helper: build Mermaid definition strings from layout content dicts
# Each function returns a Mermaid definition string ready for kind: "mermaid"


def _mmd_timeline(content: dict | None, title: str = "") -> str:
    """Build a Mermaid timeline definition from content.periods or content.events."""
    c = content or {}
    events = c.get("events", [])
    periods = c.get("periods", [])
    lines = ["timeline"]
    if title:
        lines.append(f"    title {title}")
    if events:
        for ev in events:
            date = ev.get("date", ev.get("period_key", ""))
            desc = ev.get("title", ev.get("label", ""))
            detail = ev.get("description", ev.get("body", ""))
            if detail:
                lines.append(f"    {date} : {desc} : {detail}")
            else:
                lines.append(f"    {date} : {desc}")
    elif periods:
        for p in periods:
            label = p.get("label", p.get("key", ""))
            desc = p.get("description", "")
            if desc:
                lines.append(f"    {label} : {desc}")
            else:
                lines.append(f"    {label}")
    return "\n".join(lines)


def _mmd_gantt(content: dict | None, title: str = "") -> str:
    """Build a Mermaid gantt definition from content.sections or content.tasks."""
    c = content or {}
    lines = ["gantt", f"    title {title}" if title else "    title Timeline",
             "    dateFormat  YYYY-MM-DD"]
    sections = c.get("sections", [])
    tasks = c.get("tasks", [])
    if sections:
        for sec in sections:
            sec_title = sec.get("title", "Phase")
            lines.append(f"    section {sec_title}")
            for t in sec.get("tasks", []):
                label = t.get("label", "Task")
                start = t.get("start_str", t.get("start", "2025-01-01"))
                end = t.get("end_str", t.get("end", "2025-06-01"))
                if isinstance(start, (int, float)):
                    start = f"2025-{(int(start) % 12) + 1:02d}-01"
                if isinstance(end, (int, float)):
                    end = f"2025-{((int(end) + 3) % 12) + 1:02d}-01"
                lines.append(f"    {label} : {start}, {end}")
            mil = sec.get("milestone")
            if mil:
                pk = mil.get("period_key", "")
                pos = mil.get("position", 0)
                ml = mil.get("label", "M")
                lines.append(f"    {ml} : milestone, milestone, 2025-01-01, 0d")
    elif tasks:
        for t in tasks:
            label = t.get("label", "Task")
            start = t.get("start_str", "2025-01-01")
            end = t.get("end_str", "2025-06-01")
            lines.append(f"    {label} : {start}, {end}")
    return "\n".join(lines)


def _mmd_flowchart_td(content: dict | None, title: str = "") -> str:
    """Build a Mermaid top-down flowchart from content.items (decision steps)."""
    c = content or {}
    items = c.get("items", [])
    lines = ["flowchart TD", f"    title[{title}]" if title else ""]
    if title:
        lines.pop()
        lines.append(f"    T[{title}] --> A0")
    for i, item in enumerate(items):
        node_id = f"N{i}"
        lines.append(f"    {node_id}[{item}]")
        if i > 0:
            lines.append(f"    N{i-1} --> {node_id}")
    return "\n".join(lines)


def _mmd_flowchart_lr_swimlane(content: dict | None, title: str = "") -> str:
    """Build a Mermaid flowchart with subgraphs from content.header + content.rows."""
    c = content or {}
    header = c.get("header", [])
    rows = c.get("rows", [])
    lines = ["flowchart LR"]
    if not rows:
        return "\n".join(lines)
    for ri, row in enumerate(rows):
        role = row[0] if row else f"Role {ri}"
        lines.append(f"    subgraph {role}")
        for ci in range(1, min(len(row), len(header))):
            stage = header[ci] if ci < len(header) else f"S{ci}"
            val = row[ci] if ci < len(row) else "-"
            nid = f"R{ri}C{ci}"
            lines.append(f"        {nid}[{stage}: {val}]")
        lines.append("    end")
    return "\n".join(lines)


def _mmd_mindmap(content: dict | None, title: str = "") -> str:
    """Build a Mermaid mindmap from content.items (branches)."""
    c = content or {}
    items = c.get("items", [])
    lines = ["mindmap", f"  root(({title or 'Map'}))"]
    for item in items:
        if isinstance(item, dict):
            label = item.get("label", item.get("name", ""))
            children = item.get("children", [])
            lines.append(f"    {label}")
            for ch in children:
                lines.append(f"      {ch}")
        else:
            lines.append(f"    {item}")
    return "\n".join(lines)
