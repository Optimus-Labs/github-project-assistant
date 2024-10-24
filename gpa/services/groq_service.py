from groq import Groq
from typing import List, Optional
from ..config import config


class GroqService:
    def __init__(self):
        self.client = Groq(api_key=config.groq_api_key)

    async def generate_commit_message(
        self, diff: str, commit_history: Optional[List[str]] = None
    ) -> str:
        prompt = self._build_commit_prompt(diff, commit_history)

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=config.default_model,
            temperature=0.7,
            max_tokens=150,
        )

        return response.choices[0].message.content.strip()

    def _build_commit_prompt(
        self, diff: str, commit_history: Optional[List[str]] = None
    ) -> str:
        prompt = f"""Generate a concise and descriptive commit message for the following changes:

{diff}

Guidelines:
- Use the conventional commits format (type: description)
- Keep the message under 72 characters
- Use present tense
- Be specific but concise"""

        if commit_history:
            prompt += "\n\nPrevious commit messages for context:\n" + "\n".join(
                commit_history
            )

        return prompt
