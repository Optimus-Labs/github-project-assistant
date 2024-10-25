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
            commit_history_str = "\n".join(commit_history)
            prompt += f"\n\nPrevious commit messages for context:\n{commit_history_str}"

        return prompt

    async def generate_pr_description(self, commits: List[str], diff: str) -> str:
        """Generate a PR description based on commits and changes."""
        # Join commits with newline before creating f-string
        commits_str = "\n".join(commits)

        prompt = f"""Generate a comprehensive pull request description based on the following commits and changes:

Commits:
{commits_str}

Changes:
{diff}

Guidelines:
- Start with a clear summary of the changes
- List key modifications and their impact
- Include any breaking changes or dependencies
- Add any necessary setup instructions
- Keep it professional and informative"""

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=config.default_model,
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()

    async def summarize_pr_changes(self, diff: str) -> str:
        """Generate a concise summary of PR changes."""
        prompt = f"""Provide a concise summary of the following code changes, highlighting:
- Key modifications
- Potential impact
- Areas that need careful review

Changes:
{diff}"""

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=config.default_model,
            temperature=0.7,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
