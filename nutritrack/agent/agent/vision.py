"""Claude API integration for screenshot analysis."""

from __future__ import annotations

import anthropic

from agent.config import AgentConfig


class VisionAnalyzer:
    """Uses Claude's vision capabilities to analyze UI screenshots."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        self.model = config.model

    def analyze_screenshot(self, image_base64: str, prompt: str) -> str:
        """Send a screenshot to Claude for analysis."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_base64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        return response.content[0].text

    def analyze_health(self, image_base64: str, service_name: str) -> dict:
        """Analyze a service screenshot for health status."""
        prompt = f"""Analyze this screenshot of the {service_name} UI.

Determine:
1. **status**: Is the service healthy? (healthy / degraded / down / unknown)
2. **summary**: One-sentence summary of what you see.
3. **issues**: List any errors, warnings, or problems visible. Empty list if none.
4. **metrics**: Any key numbers visible (counts, percentages, durations).

Respond in this exact JSON format:
{{
  "status": "healthy|degraded|down|unknown",
  "summary": "...",
  "issues": ["issue1", "issue2"],
  "metrics": {{"key": "value"}}
}}

Only output the JSON, nothing else."""

        text = self.analyze_screenshot(image_base64, prompt)
        # Parse JSON from response
        import json

        try:
            # Handle markdown code blocks
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return {
                "status": "unknown",
                "summary": text[:200],
                "issues": ["Failed to parse Claude response as JSON"],
                "metrics": {},
            }

    def decide_next_action(self, image_base64: str, goal: str, history: list[str]) -> str:
        """Given a screenshot and goal, decide what to do next."""
        history_text = "\n".join(f"  - {h}" for h in history[-10:]) if history else "  (none)"
        prompt = f"""You are a UI navigation agent. Your goal: {goal}

Actions taken so far:
{history_text}

Looking at the current screenshot, what should be done next?
Respond with ONE of these action types:
- NAVIGATE <url> — go to a URL
- CLICK <css_selector> — click an element
- FILL <css_selector> <value> — type into an input
- SCREENSHOT <name> — take a screenshot for the report
- DONE <summary> — goal is complete, summarize findings

Respond with just the action, nothing else."""

        return self.analyze_screenshot(image_base64, prompt)
