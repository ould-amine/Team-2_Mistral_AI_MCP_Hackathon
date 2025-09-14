"""
Mistral AI client for post suggestions
"""
import requests
import os
from typing import List, Dict, Any, Optional
from ..config.settings import MISTRAL_API_KEY


class MistralClient:
    """Mistral AI client for generating post suggestions"""
    
    def __init__(self):
        self.api_key = MISTRAL_API_KEY
        self.base_url = "https://api.mistral.ai/v1/chat/completions"
    
    def generate_post_suggestion(self, business_info: str, analytics_data: List[Dict[str, Any]], additional_context: str = "") -> str:
        """Generate post suggestion using Mistral AI based on business info and analytics"""
        try:
            # Prepare analytics summary
            analytics_summary = self._prepare_analytics_summary(analytics_data)
            
            # Prepare prompt for Mistral
            prompt = self._prepare_prompt(business_info, analytics_summary, additional_context)
            
            # Call Mistral API
            response = self._call_mistral_api(prompt)
            
            if response:
                return response
            else:
                return "❌ Error generating post suggestion with Mistral AI"
                
        except Exception as e:
            return f"❌ Error generating post suggestion: {str(e)}"
    
    def _prepare_analytics_summary(self, analytics_data: List[Dict[str, Any]]) -> str:
        """Prepare analytics summary for AI context"""
        if not analytics_data:
            return "No previous analytics data available."
        
        total_posts = len(analytics_data)
        total_views = sum(post['analytics'].get('views', 0) for post in analytics_data)
        total_reactions = sum(post['analytics'].get('likes', 0) for post in analytics_data)
        avg_views = total_views / total_posts if total_posts > 0 else 0
        avg_reactions = total_reactions / total_posts if total_posts > 0 else 0
        
        # Find best performing posts
        best_posts = sorted(analytics_data, key=lambda x: x['analytics'].get('views', 0), reverse=True)[:3]
        
        analytics_summary = f"""
Previous Performance Summary:
- Total posts analyzed: {total_posts}
- Average views per post: {avg_views:.0f}
- Average reactions per post: {avg_reactions:.0f}
- Best performing posts:
"""
        for i, post in enumerate(best_posts, 1):
            analytics_summary += f"  {i}. Views: {post['analytics'].get('views', 0)}, Reactions: {post['analytics'].get('likes', 0)}\n"
            analytics_summary += f"     Text: {post['text'][:100]}{'...' if len(post['text']) > 100 else ''}\n"
            analytics_summary += f"     Type: {'Image post' if post['has_image'] else 'Text post'}\n"
        
        return analytics_summary
    
    def _prepare_prompt(self, business_info: str, analytics_summary: str, additional_context: str) -> str:
        """Prepare prompt for Mistral AI"""
        return f"""
You are a social media marketing expert. Generate a Facebook post suggestion based on the following information:

Business Information:
{business_info}

{analytics_summary}

Additional Context:
{additional_context}

Please generate:
1. A compelling Facebook post text (2-3 sentences max)
2. Post type recommendation (text or image)
3. Best time to post (if analytics suggest patterns)
4. Engagement strategy tips

Format your response as:
POST SUGGESTION:
[Your post text here]

TYPE: [text/image]

TIMING: [Your timing recommendation]

TIPS: [Your engagement tips]
"""
    
    def _call_mistral_api(self, prompt: str) -> str:
        """Call Mistral API with the prepared prompt"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "mistral-medium-latest",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        response = requests.post(self.base_url, headers=headers, json=data)
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            return None
        
        
    def chat_complete(
        self,
        model: Optional[str] = None,
        messages: List[Dict[str, str]] = None,
        temperature: float = 0.7,
        max_tokens: int = 800,
    ):
        """
        Thin wrapper around the Mistral REST chat completions endpoint.
        Returns the parsed JSON (dict) from Mistral.

        messages: [{"role":"system"|"user"|"assistant", "content":"..."}]
        """
        if not self.api_key:
            raise RuntimeError("MistralClient: MISTRAL_API_KEY is not set")

        model = model or self.default_model
        messages = messages or []

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        resp = requests.post(self.base_url, headers=headers, json=payload, timeout=self.timeout)
        try:
            data = resp.json()
        except Exception:
            resp.raise_for_status()
            raise

        if resp.status_code >= 400:
            # Return the API error content for easier debugging
            raise RuntimeError(f"Mistral API error {resp.status_code}: {data}")

        return data
    
        

    def analyze_posts(self, posts_data, model: str = None):
        """
        Returns dict:
        {
            "insights": {...},
            "engagement_table": [...],
            "chart_config": {...},
            "chart_url": "https://quickchart.io/chart?c=..."
        }
        """
        import json, re, urllib.parse

        model = model or os.getenv("MCP_MODEL_TEXT", "mistral-medium-latest")

        instruction = """
    You are a data analyst. Analyze the following social media posts using BOTH (if present):
    1) Textual content (post content)
    2) Image-derived features (vision/vision_summary: captions, tags, dominant colors, flags)

    Return ONLY one JSON object, with NO Markdown or code fences.
    Wrap your JSON exactly between the two lines:
    JSON_ONLY_START
    ...your JSON object...
    JSON_ONLY_END

    Schema:
    {
    "insights": {
        "overall_sentiment": "string",
        "top_topics": ["string", "..."],
        "image_patterns": ["string", "..."],
        "notable_patterns": ["string", "..."],
        "recommendations": ["string", "..."]
    },
    "engagement_table": [
        {"post_id":"string","content_summary":"string","image_summary":"string","total_reactions":number}
    ],
    "chart_config": {
        "type":"bar",
        "data": {"labels": ["Post 1","Post 2","..."], "datasets": [{"label":"Total reactions","data":[...]}]},
        "options": {"plugins": {"legend": {"display": true}}, "scales": {"y": {"beginAtZero": true}}}
    }
    }

    Rules:
    - content_summary ≤ 12 words.
    - image_summary derives from image features (≤ 10 words), empty if no image fields.
    - Use total_reactions for the bar chart.

    Posts JSON follows:
    """ + json.dumps(posts_data, ensure_ascii=False)

        # call whichever interface your client exposes
        messages = [
            {"role": "system", "content": "You are a precise data analyst. Always follow output-format instructions exactly."},
            {"role": "user", "content": instruction}
        ]
        resp = self.chat_complete(model=model, messages=messages)
        raw = resp["choices"][0]["message"]["content"] if isinstance(resp, dict) else resp.choices[0].message.content

        # extract between sentinels
        def _strip_code_fences(t):
            t = t.strip()
            if t.startswith("```"):
                import re
                t = re.sub(r"^```[a-zA-Z0-9]*\n?", "", t)
                t = re.sub(r"\n?```$", "", t)
            return t
        import re, json, urllib.parse
        t = _strip_code_fences(raw)
        m = re.search(r"JSON_ONLY_START\s*(\{.*\})\s*JSON_ONLY_END", t, flags=re.DOTALL)
        if not m:
            raise ValueError("Analysis: JSON_ONLY_* sentinels not found. First 400 chars:\n" + t[:400])
        result = json.loads(m.group(1))

        # add QuickChart URL
        chart_url = "https://quickchart.io/chart?c=" + urllib.parse.quote(json.dumps(result["chart_config"], ensure_ascii=False))
        result["chart_url"] = chart_url
        return result


    def generate_post_copy(
        self,
        posts_data,
        new_post_idea: str,
        client_goal: str = "maximize overall engagement (reactions, comments, shares)",
        constraints: Any = None,   # <-- accept dict OR str
        model: str = None,
        temperature: float = 0.1,
    ):
        """
        Returns dict:
        {
            "post_text": "...",
            "impact_estimate": "...",
            "image_needed": bool,
            "image_prompt": "...",        # if image_needed
        }
        (No Bria call here; the tool will decide whether to call Bria.)
        """
        import json, re
        constraints_dict = constraints if isinstance(constraints, dict) else None
        constraints_text = constraints if isinstance(constraints, str) else None
        model = model or os.getenv("MCP_MODEL_TEXT", "mistral-medium-latest")

        instruction = (
            "You are a marketing analyst. Use BOTH text and image-derived features from historical posts to advise a NEW post.\n"
            "Based on the provided posts_data, write:\n"
            "1) The final post copy (short and compelling, on-brand).\n"
            "2) A concise estimated impact (e.g., relative to historical median).\n"
            "3) If an image would significantly improve impact, say IMAGE_NEEDED: yes and provide ONE Bria-ready image prompt.\n\n"
            "Return ONLY plain text in EXACTLY this template (no extra text, no markdown, no code fences):\n\n"
            "POST_TEXT:\n"
            "<final copy here>\n\n"
            "IMPACT_ESTIMATE:\n"
            "<short estimate>\n\n"
            "IMAGE_NEEDED: yes|no\n"
            "BRIA_PROMPT:\n"
            "<one-line image prompt if yes; otherwise leave empty>\n"
        )

        payload = {
        "context": {
            "objective": client_goal,
            "constraints_structured": constraints_dict,   # may be None
            "constraints_text": constraints_text,         # may be None
            "new_post_idea": new_post_idea,
            "historical_posts": posts_data,
        }
    }

        messages = [
            {"role": "system", "content": "You are a precise marketing analyst who strictly follows output formatting."},
            {"role": "user", "content": instruction + "\n\nposts_data_payload:\n" + json.dumps(payload, ensure_ascii=False)}
        ]
        resp = self.chat_complete(model=model, messages=messages)
        raw = resp["choices"][0]["message"]["content"] if isinstance(resp, dict) else resp.choices[0].message.content
        raw = (raw or "").strip()

        regex = re.compile(
            r"POST_TEXT:\s*(?P<post_text>.*?)\n\s*IMPACT_ESTIMATE:\s*(?P<impact>.*?)\n\s*IMAGE_NEEDED:\s*(?P<needed>yes|no)\s*\n\s*BRIA_PROMPT:\s*(?P<bria_prompt>.*)\Z",
            re.DOTALL | re.IGNORECASE
        )
        m = regex.search(raw)
        if not m:
            raise ValueError("Generation: model output did not match the required template. Output was:\n" + raw[:800])

        out = {
            "post_text": m.group("post_text").strip(),
            "impact_estimate": m.group("impact").strip(),
            "image_needed": (m.group("needed").strip().lower() == "yes"),
        }
        if out["image_needed"]:
            out["image_prompt"] = m.group("bria_prompt").strip()
        return out

