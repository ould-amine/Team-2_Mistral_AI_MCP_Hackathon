"""
Mistral AI client for post suggestions
"""
import requests
from typing import List, Dict, Any
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
