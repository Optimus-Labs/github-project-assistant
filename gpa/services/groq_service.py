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

    async def generate_issue_description(self, context: str, title: str) -> str:
        """Generate an issue description based on code context."""
        prompt = f"""Generate a comprehensive issue description based on the following context and title:

Title: {title}

Context:
{context}

Create a detailed issue description that includes:
- Problem statement/Feature request
- Expected behavior
- Technical context
- Potential implementation steps
- Any dependencies or prerequisites

Use markdown formatting for better readability."""

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=config.default_model,
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()

    async def suggest_issue_labels(self, title: str, description: str) -> List[str]:
        """Suggest appropriate labels for an issue."""
        prompt = f"""Based on the following issue title and description, suggest appropriate GitHub labels.
Consider common label categories like:
- Type (bug, feature, enhancement, documentation)
- Priority (high, medium, low)
- Status (ready for review, needs investigation)
- Component (frontend, backend, api, etc.)

Title: {title}
Description: {description}

Return only the label names, one per line."""

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=config.default_model,
            temperature=0.7,
            max_tokens=150,
        )
        return [
            label.strip()
            for label in response.choices[0].message.content.split("\n")
            if label.strip()
        ]

    async def categorize_issues(self, issues: List[dict]) -> str:
        """Categorize and summarize a list of issues."""
        issues_text = "\n".join(
            [f"#{issue['number']} - {issue['title']}" for issue in issues]
        )

        prompt = f"""Analyze and categorize the following GitHub issues:

{issues_text}

Provide a summary that:
1. Groups issues by type/theme
2. Highlights priority items
3. Identifies related issues
4. Suggests possible milestones

Use markdown formatting for the summary."""

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=config.default_model,
            temperature=0.7,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
