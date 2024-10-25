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

    async def analyze_code_changes(self, diff: str, files_content: dict) -> str:
        """Analyze code changes and suggest improvements."""
        prompt = f"""Analyze the following code changes and provide a detailed review:

Diff:
{diff}

Full files content:
{files_content}

Provide analysis including:
1. Code quality assessment
2. Potential bugs or issues
3. Performance considerations
4. Security implications
5. Suggested improvements
6. Best practices violations
7. Documentation needs

Format the response in markdown with clear sections."""

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=config.default_model,
            temperature=0.7,
            max_tokens=1500,
        )
        return response.choices[0].message.content.strip()

    async def explain_changes(self, diff: str) -> str:
        """Explain code changes in simple terms."""
        prompt = f"""Explain the following code changes in simple, non-technical terms:

{diff}

Focus on:
1. What changed
2. Why it matters
3. Impact on functionality
4. Benefits of the changes

Use clear, concise language suitable for non-technical stakeholders."""

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=config.default_model,
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()

    async def generate_review_comments(self, diff: str) -> List[dict]:
        """Generate specific review comments for code changes."""
        prompt = f"""Review the following code changes and generate specific, actionable review comments:

{diff}

For each issue found, provide:
1. The specific location/context
2. What the issue is
3. Why it's important
4. How to fix it

Format each comment as a constructive suggestion."""

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=config.default_model,
            temperature=0.7,
            max_tokens=1000,
        )

        # Parse the response into structured comments
        comments_text = response.choices[0].message.content.strip()
        comments = []
        for comment in comments_text.split("\n\n"):
            if comment.strip():
                comments.append(
                    {
                        "content": comment,
                        "type": "suggestion"
                        if "suggestion" in comment.lower()
                        else "issue",
                    }
                )
        return comments

    async def generate_readme(self, project_files: dict, git_info: dict) -> str:
        """Generate a comprehensive README based on project structure and git info."""
        project_summary = "\n".join(
            [f"{path}:\n{content[:200]}..." for path, content in project_files.items()]
        )

        prompt = f"""Generate a comprehensive README.md for the following project:

Project Files:
{project_summary}

Git Info:
{git_info}

Create a README that includes:
1. Project title and description
2. Installation instructions
3. Usage examples
4. Configuration details
5. Main features
6. Development setup
7. Contributing guidelines
8. License information

Use clear markdown formatting with appropriate sections."""

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=config.default_model,
            temperature=0.7,
            max_tokens=2000,
        )
        return response.choices[0].message.content.strip()

    async def suggest_doc_improvements(
        self, current_docs: str, code_changes: str
    ) -> str:
        """Suggest documentation improvements based on code changes."""
        prompt = f"""Analyze the following code changes and current documentation:

Current Documentation:
{current_docs}

Code Changes:
{code_changes}

Suggest documentation improvements including:
1. Missing documentation
2. Outdated sections
3. Clarity improvements
4. Additional examples needed
5. Technical accuracy updates

Provide specific suggestions with markdown formatting."""

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=config.default_model,
            temperature=0.7,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()

    async def generate_code_docs(self, code: str, style: str = "google") -> str:
        """Generate code documentation in specified style."""
        prompt = f"""Generate documentation for the following code using {style} style:

{code}

Include:
1. Function/class purpose
2. Parameters
3. Return values
4. Exceptions
5. Usage examples
6. Important notes

Follow {style} documentation style guide strictly."""

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=config.default_model,
            temperature=0.7,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
