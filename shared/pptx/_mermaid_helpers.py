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
                ml = mil.get("label", "M")
                lines.append(f"    {ml} : milestone, {start or '2025-01-01'}, 0d")
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
    lines = ["flowchart TD"]
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


# === NEW: Additional Mermaid types for E2E coverage ===


def _mmd_quadrant(content: dict | None, title: str = "") -> str:
    """Build a Mermaid quadrantChart definition from content.data_points."""
    c = content or {}
    points = c.get("data_points", c.get("items", []))
    lines = ["quadrantChart",
             f"    title {title}" if title else "    title Matrix",
             "    x-axis Low --> High",
             "    y-axis Low --> High",
             "    quadrant-1 Top Priority",
             "    quadrant-2 Invest",
             "    quadrant-3 Monitor",
             "    quadrant-4 Deprioritize"]
    for i, pt in enumerate(points):
        if isinstance(pt, dict):
            name = pt.get("name", pt.get("label", f"Item {i+1}"))
            x = pt.get("x", pt.get("value", 0.5))
            y_val = pt.get("y", 0.5)
            lines.append(f"    {name}: [{x}, {y_val}]")
        else:
            lines.append(f"    Item {i+1}: [0.5, 0.5]")
    return "\n".join(lines)


def _mmd_pie(content: dict | None, title: str = "") -> str:
    """Build a Mermaid pie chart from content.segments."""
    c = content or {}
    segments = c.get("segments", c.get("items", []))
    lines = ["pie", f"    title {title}" if title else "    title Distribution"]
    for seg in segments:
        if isinstance(seg, dict):
            label = seg.get("label", seg.get("name", ""))
            value = seg.get("value", seg.get("size", 10))
            lines.append(f"    \"{label}\" : {value}")
        else:
            lines.append(f"    \"{seg}\" : 10")
    return "\n".join(lines)


def _mmd_sankey(content: dict | None, title: str = "") -> str:
    """Build a Mermaid sankey diagram from content.links (source,target,value)."""
    c = content or {}
    links = c.get("links", c.get("items", []))
    lines = ["sankey-beta"]
    for link in links:
        if isinstance(link, dict):
            src = link.get("source", link.get("from", ""))
            tgt = link.get("target", link.get("to", ""))
            val = link.get("value", link.get("size", 10))
            lines.append(f"    {src},{tgt},{val}")
        elif isinstance(link, str):
            lines.append(f"    {link}")
    return "\n".join(lines)


def _mmd_kanban(content: dict | None, title: str = "") -> str:
    """Build a Mermaid kanban board from content.columns (items grouped by status)."""
    c = content or {}
    columns = c.get("columns", {})
    items = c.get("items", [])
    lines = ["kanban"]
    if columns:
        for col_name, col_items in columns.items():
            for item in col_items:
                label = item if isinstance(item, str) else item.get("label", item.get("name", ""))
                lines.append(f"    {col_name}[{label}]")
    elif items:
        for item in items:
            if isinstance(item, dict):
                status = item.get("status", "Todo")
                label = item.get("label", item.get("name", ""))
                lines.append(f"    {status}[{label}]")
            else:
                lines.append(f"    Todo[{item}]")
    return "\n".join(lines)


def _mmd_architecture(content: dict | None, title: str = "") -> str:
    """Build a Mermaid architecture diagram from content.services and content.connections."""
    c = content or {}
    groups = c.get("groups", [])
    services = c.get("services", c.get("items", []))
    connections = c.get("connections", c.get("links", []))
    lines = ["architecture"]
    for g in groups:
        name = g.get("name", g.get("label", "Group"))
        label = g.get("title", name)
        lines.append(f"    group {name}[{label}]")
    for svc in services:
        if isinstance(svc, dict):
            name = svc.get("name", svc.get("id", ""))
            label = svc.get("label", svc.get("title", name))
            lines.append(f"    service {name}[{label}]")
        else:
            lines.append(f"    service {svc}[{svc}]")
    for conn in connections:
        if isinstance(conn, dict):
            src = conn.get("from", conn.get("source", ""))
            tgt = conn.get("to", conn.get("target", ""))
            lines.append(f"    {src} -> {tgt}")
        elif isinstance(conn, str):
            lines.append(f"    {conn}")
    return "\n".join(lines)


def _mmd_gitgraph(content: dict | None, title: str = "") -> str:
    """Build a Mermaid gitGraph from content.commits."""
    c = content or {}
    commits = c.get("commits", [])
    branches = c.get("branches", [])
    lines = ["gitGraph"]
    for br in branches:
        if isinstance(br, dict):
            name = br.get("name", "")
            action = br.get("action", "branch")
            lines.append(f"    {action} {name}")
    for cm in commits:
        if isinstance(cm, dict):
            action = cm.get("action", "commit")
            msg = cm.get("message", cm.get("label", ""))
            if msg:
                lines.append(f"    {action} id: \"{msg}\"")
            else:
                lines.append(f"    {action}")
        elif isinstance(cm, str):
            lines.append(f"    commit id: \"{cm}\"")
    return "\n".join(lines)


def _mmd_flowchart_architecture(content: dict | None, title: str = "") -> str:
    """Build a Mermaid flowchart TB with subgraphs for architecture diagrams."""
    c = content or {}
    groups = c.get("groups", [])
    services = c.get("services", c.get("items", []))
    connections = c.get("connections", c.get("links", []))
    lines = ["flowchart TB"]
    if title:
        lines.insert(0, f"%%{{init: {{'theme':'base','themeVariables': {{'fontFamily':'Arial'}}}}}}%%")
        lines.append(f"    title[{title}]")
    # Render groups as subgraphs with their services inside
    group_services = {}
    for g in groups:
        gname = g.get("name", g.get("label", "Group"))
        glabel = g.get("title", gname)
        lines.append(f"    subgraph {gname}[{glabel}]")
        group_services[gname] = []
        for svc in services:
            if svc.get("group", svc.get("parent", "")) == gname:
                sname = svc.get("name", svc.get("id", ""))
                slabel = svc.get("label", svc.get("title", sname))
                lines.append(f"        {sname}[{slabel}]")
                group_services[gname].append(sname)
        lines.append("    end")
    # Services without a group
    for svc in services:
        gname = svc.get("group", svc.get("parent", ""))
        if gname not in [g.get("name", g.get("label", "")) for g in groups]:
            sname = svc.get("name", svc.get("id", ""))
            slabel = svc.get("label", svc.get("title", sname))
            lines.append(f"    {sname}[{slabel}]")
    # Connections
    for conn in connections:
        src = conn.get("from", conn.get("source", ""))
        tgt = conn.get("to", conn.get("target", ""))
        label = conn.get("label", conn.get("description", ""))
        if label:
            lines.append(f"    {src} -->|{label}| {tgt}")
        else:
            lines.append(f"    {src} --> {tgt}")
    return "\n".join(lines)
