"""
Chart generation tools (LIVE Facebook data)
- Fetch recent posts via connected Facebook client (analytics.fetch_analytics_data)
- Build Chart.js configs and QuickChart URLs (no AI dependency)
- Return charts + optional data tables

Presets supported:
  - overview     : bar of metric per post (latest N)
  - by_type      : bar of average metric by post type (has_image vs text-only)
  - top_posts    : horizontal bar for top N posts by metric

Params:
  limit            : number of recent posts to analyze (1..100)
  metric           : "views" | "likes" | "reactions" (default "reactions")
  presets_csv      : comma-separated list of presets (default: "overview,by_type,top_posts")
  top_n            : for "top_posts" preset (default 10)
  include_tables   : include the underlying table data in response (default True)
  return_configs   : include raw Chart.js configs alongside URLs (default False)
"""

import os
import re
import json
import time
import uuid
import math
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from pydantic import Field
from mcp.server.fastmcp import FastMCP

import urllib.parse

# -------------------------------
# QuickChart helpers
# -------------------------------

def _quickchart_url(chart_config: Dict[str, Any]) -> str:
    return "https://quickchart.io/chart?c=" + urllib.parse.quote(json.dumps(chart_config, ensure_ascii=False))

# -------------------------------
# Data normalization
# -------------------------------

def _normalize_posts_data(data: Any) -> List[Dict[str, Any]]:
    """
    Accept list or JSON string of list; tolerate dict wrappers like {"data": [...]}
    Shape expected per post (examples fields):
      - post_id: str
      - text: str
      - has_image: bool
      - analytics: { views: int, likes: int, clicks: int, metadata: { reactions: {...} } }
    """
    if isinstance(data, str):
        data = json.loads(data)

    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], list):
            data = data["data"]
        elif "posts" in data and isinstance(data["posts"], list):
            data = data["posts"]
        else:
            raise ValueError("Unexpected analytics data dict shape (no 'data' or 'posts').")

    if not isinstance(data, list):
        raise ValueError("Analytics data must be a list of posts.")

    return data

def _safe_int(x: Any) -> int:
    try:
        return int(x)
    except Exception:
        return 0

def _extract_metrics(post: Dict[str, Any]) -> Dict[str, int]:
    a = post.get("analytics", {}) or {}
    views = _safe_int(a.get("views", 0))
    likes = _safe_int(a.get("likes", 0))
    # Reactions total = likes + sum(metadata.reactions values)
    reactions_meta = ((a.get("metadata", {}) or {}).get("reactions", {}) or {})
    extra_reacts = sum(_safe_int(v) for v in reactions_meta.values())
    reactions_total = likes + extra_reacts
    return {"views": views, "likes": likes, "reactions": reactions_total}


# -------------------------------
# Chart builders
# -------------------------------

def _build_overview_bar(posts: List[Dict[str, Any]], metric: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    labels = []
    data = []
    table = []
    for p in posts:
        pid = str(p.get("post_id", "")) or "?"
        text = (p.get("text") or p.get("content") or "").strip()
        text_short = (text[:60] + "…") if len(text) > 60 else text

        m = _extract_metrics(p)
        val = m.get(metric, 0)
        labels.append(f"#{pid}")
        data.append(val)

        table.append({
            "post_id": pid,
            "snippet": text_short,
            metric: val
        })

    cfg = {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [{"label": metric.capitalize(), "data": data}]
        },
        "options": {
            "plugins": {"legend": {"display": True}},
            "scales": {
                "x": {"title": {"display": True, "text": "Post ID"}},
                "y": {"beginAtZero": True, "title": {"display": True, "text": metric.capitalize()}}
            }
        }
    }

    return cfg, table

def _avg(vals: List[int]) -> float:
    return (sum(vals) / len(vals)) if vals else 0.0


def _build_by_type(posts: List[Dict[str, Any]], metric: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    img_vals, txt_vals = [], []
    for p in posts:
        m = _extract_metrics(p)
        val = m.get(metric, 0)
        (img_vals if p.get("has_image") else txt_vals).append(val)

    labels = ["Image", "Text"]
    data = [round(_avg(img_vals), 2), round(_avg(txt_vals), 2)]
    table = [
        {"type": "Image", f"avg_{metric}": data[0], "count": len(img_vals)},
        {"type": "Text", f"avg_{metric}": data[1], "count": len(txt_vals)}
    ]

    cfg = {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [{"label": f"Avg {metric} by type", "data": data}]
        },
        "options": {
            "plugins": {"legend": {"display": True}},
            "scales": {
                "x": {"title": {"display": True, "text": "Post Type"}},
                "y": {"beginAtZero": True, "title": {"display": True, "text": f"Avg {metric}"}}
            }
        }
    }

    return cfg, table

def _build_top_posts(posts: List[Dict[str, Any]], metric: str, top_n: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    scored = []
    for p in posts:
        pid = str(p.get("post_id", "")) or "?"
        text = (p.get("text") or p.get("content") or "").strip()
        text_short = (text[:60] + "…") if len(text) > 60 else text
        m = _extract_metrics(p)
        scored.append({"post_id": pid, "snippet": text_short, metric: m.get(metric, 0)})

    scored.sort(key=lambda x: x[metric], reverse=True)
    top = scored[: max(1, top_n)]

    labels = [f"#{row['post_id']}" for row in top]
    data = [row[metric] for row in top]

    cfg = {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [{"label": f"Top {len(top)} by {metric}", "data": data}]
        },
        "options": {
            "indexAxis": "y",
            "plugins": {"legend": {"display": True}},
            "scales": {
                "x": {"beginAtZero": True, "title": {"display": True, "text": metric.capitalize()}},
                "y": {"title": {"display": True, "text": "Post ID"}}
            }
        }
    }

    return cfg, top

# -------------------------------
# MCP tool registration
# -------------------------------

def register_chart_tools(mcp: FastMCP, client, analytics):
    """
    Registers:
      - generate_charts(limit, metric, presets_csv, top_n, include_tables, return_configs)

    Returns JSON:
      {
        "charts": [
          {"name":"overview","chart_url":"...","config":{...}?},
          ...
        ],
        "tables": { "overview":[...], "by_type":[...], ... }?,
        "provenance": {"tool":"generate_charts","run_id":"...","timestamp":169...}
      }
    """

    @mcp.tool(
        title="Generate charts for Facebook posts",
        description="Build QuickChart URLs (and optional data tables) from recent Facebook posts."
    )
    def generate_charts(
        limit: int = Field(default=50, ge=1, le=100, description="Number of recent posts to analyze (1-100)"),
        metric: str = Field(default="reactions", description="Metric to chart: 'views' | 'likes' | 'reactions'"),
        presets_csv: str = Field(default="overview,by_type,top_posts", description="Comma-separated presets to include"),
        top_n: int = Field(default=10, ge=1, le=50, description="Top N posts for 'top_posts' preset"),
        include_tables: bool = Field(default=True, description="Include underlying table data"),
        return_configs: bool = Field(default=False, description="Include raw Chart.js config alongside URLs")
    ) -> str:
        run_id = str(uuid.uuid4())
        ts = int(time.time())

        # Validate metric
        metric = (metric or "reactions").lower().strip()
        if metric not in {"views", "likes", "reactions"}:
            return json.dumps({
                "error": "Invalid metric. Use one of: views, likes, reactions.",
                "provenance": {"tool":"generate_charts","run_id":run_id,"timestamp":ts}
            }, ensure_ascii=False)

        # Check connection
        if not hasattr(client, "is_connected") or not client.is_connected():
            return json.dumps({
                "error": "Facebook not connected. Use 'get_facebook_auth_url()' to authorize.",
                "provenance": {"tool":"generate_charts","run_id":run_id,"timestamp":ts}
            }, ensure_ascii=False)

        # Fetch data
        try:
            raw = analytics.fetch_analytics_data(limit)
            posts = _normalize_posts_data(raw)
            if not posts:
                return json.dumps({
                    "error": "No posts found or error fetching data.",
                    "provenance": {"tool":"generate_charts","run_id":run_id,"timestamp":ts}
                }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                "error": f"Fetching analytics failed: {e}",
                "provenance": {"tool":"generate_charts","run_id":run_id,"timestamp":ts}
            }, ensure_ascii=False)

        # Determine presets
        presets = [p.strip().lower() for p in (presets_csv or "").split(",") if p.strip()]
        valid_presets = {"overview", "by_type", "top_posts"}
        presets = [p for p in presets if p in valid_presets] or ["overview"]

        charts: List[Dict[str, Any]] = []
        tables: Dict[str, List[Dict[str, Any]]] = {}

        # Build each requested preset
        for preset in presets:
            try:
                if preset == "overview":
                    cfg, tbl = _build_overview_bar(posts, metric)
                elif preset == "by_type":
                    cfg, tbl = _build_by_type(posts, metric)
                elif preset == "top_posts":
                    cfg, tbl = _build_top_posts(posts, metric, top_n)
                else:
                    continue

                item = {"name": preset, "chart_url": _quickchart_url(cfg)}
                if return_configs:
                    item["config"] = cfg
                charts.append(item)

                if include_tables:
                    tables[preset] = tbl

            except Exception as e:
                charts.append({"name": preset, "error": f"Failed to build '{preset}': {e}"})

        out = {
            "charts": charts,
            "provenance": {"tool": "generate_charts", "run_id": run_id, "timestamp": ts}
        }
        if include_tables:
            out["tables"] = tables

        return json.dumps(out, indent=2, ensure_ascii=False)
