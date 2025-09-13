"""
Generation of text + image new post (LIVE Facebook data).
Calls Bria to generate an image.
"""

import os
import re
import json
import time
import uuid
import urllib.parse
from typing import Any, Dict, List, Optional

import requests
from pydantic import Field
from mcp.server.fastmcp import FastMCP

# --- Bria config ---
BRIA_API_TOKEN = os.getenv("BRIA_API_TOKEN")
BRIA_MODEL_VERSION = os.getenv("BRIA_MODEL_VERSION", "3.2")
BRIA_URL = f"https://engine.prod.bria-api.com/v1/text-to-image/base/{BRIA_MODEL_VERSION}"

IMG_URL_RE = re.compile(
    r"https?://[^\s\"']+\.(?:png|jpg|jpeg|webp|gif)(?:\?[^\s\"']*)?$",
    re.IGNORECASE
)

def _collect_image_urls(obj: Any, found: List[str]) -> None:
    if obj is None:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                if k.lower() in {"url", "image_url"} and IMG_URL_RE.search(v):
                    found.append(v)
                elif IMG_URL_RE.search(v):
                    found.append(v)
            else:
                _collect_image_urls(v, found)
    elif isinstance(obj, list):
        for it in obj:
            _collect_image_urls(it, found)
    elif isinstance(obj, str):
        if IMG_URL_RE.search(obj):
            found.append(obj)

def _normalize_posts_data(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, str):
        data = json.loads(data)
    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], list):
            data = data["data"]
        elif "posts" in data and isinstance(data["posts"], list):
            data = data["posts"]
        else:
            raise ValueError("Unexpected analytics data dict shape (no 'data' or 'posts' list).")
    if not isinstance(data, list):
        raise ValueError("Analytics data must be a list of posts.")
    return data

def register_post_generation_tools(mcp: FastMCP, client, analytics, mistral):
    """
    Registers:
      - post_generation(limit, new_post_idea, client_goal?, constraints?, bria_num_results?)
    Calls Bria to generate an image.
    """

    @mcp.tool(
        title="Generate content for new Facebook post",
        description="Fetch recent Facebook posts, analyze with Mistral, and generate a new post suggestion with a Bria image URL."
    )
    def post_generation(
        limit: int = Field(default=20, ge=1, le=100, description="Number of recent posts to analyze (1-100)"),
        new_post_idea: str = Field(description="Short description of the new post idea"),
        client_goal: str = Field(default="maximize overall engagement (reactions, comments, shares)"),
        constraints: str = Field(default="", description="Optional JSON string for constraints (tone, region, platform, etc.)"),
        bria_num_results: int = Field(default=1, ge=1, le=4, description="Number of Bria images to generate (1-4)")
    ) -> str:
        run_id = str(uuid.uuid4())
        ts = int(time.time())

        # 1) LIVE Facebook data
        if not hasattr(client, "is_connected") or not client.is_connected():
            return json.dumps({
                "error": "Facebook not connected. Use 'get_facebook_auth_url()' to authorize.",
                "provenance": {"tool": "post_generation", "run_id": run_id, "timestamp": ts}
            }, ensure_ascii=False)

        try:
            raw = analytics.fetch_analytics_data(limit)
            posts_data = _normalize_posts_data(raw)
            if not posts_data:
                return json.dumps({
                    "error": "No posts found or error fetching data.",
                    "provenance": {"tool": "post_generation", "run_id": run_id, "timestamp": ts}
                }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                "error": f"Fetching analytics failed: {e}",
                "provenance": {"tool": "post_generation", "run_id": run_id, "timestamp": ts}
            }, ensure_ascii=False)

        # 2) Analytics via MistralClient
        try:
            analysis = mistral.analyze_posts(posts_data)
        except Exception as e:
            return json.dumps({
                "error": f"Analysis error: {e}",
                "provenance": {"tool": "post_generation", "run_id": run_id, "timestamp": ts}
            }, ensure_ascii=False)

        # 3) Final copy
        try:
            constraints_obj: Optional[Dict[str, Any]] = json.loads(constraints) if constraints.strip() else None
        except Exception:
            constraints_obj = {"raw": constraints}

        try:
            final = mistral.generate_post_copy(
                posts_data=posts_data,
                new_post_idea=new_post_idea,
                client_goal=client_goal,
                constraints=constraints_obj
            )
        except Exception as e:
            return json.dumps({
                "error": f"Generation error: {e}",
                "provenance": {"tool": "post_generation", "run_id": run_id, "timestamp": ts}
            }, ensure_ascii=False)

        # 4) Call Bria
        final["image_urls"] = []
        if not BRIA_API_TOKEN:
            final["image_error"] = "BRIA_API_TOKEN not set"
        else:
            headers = {"Content-Type": "application/json", "api_token": BRIA_API_TOKEN}
            # fallback to new_post_idea if model didn’t give an image_prompt
            bria_prompt = final.get("image_prompt") or new_post_idea
            payload = {"prompt": bria_prompt, "num_results": int(bria_num_results), "sync": True}
            try:
                resp = requests.post(BRIA_URL, headers=headers, json=payload, timeout=120)
                if resp.status_code >= 400:
                    final["image_error"] = f"Bria error {resp.status_code}: {resp.text}"
                else:
                    data = resp.json()
                    if isinstance(data, dict) and "result" in data:
                        data = data["result"]
                    urls: List[str] = []
                    _collect_image_urls(data, urls)
                    seen = set()
                    final["image_urls"] = [u for u in urls if not (u in seen or seen.add(u))]
            except Exception as e:
                final["image_error"] = str(e)

        # 5) Response
        return json.dumps({
            "analysis": {
                "insights": analysis.get("insights"),
                "engagement_table": analysis.get("engagement_table"),
                "chart_url": analysis.get("chart_url"),
            },
            "final": final,
            "provenance": {
                "tool": "post_generation",
                "run_id": run_id,
                "timestamp": ts
            }
        }, indent=2, ensure_ascii=False)
