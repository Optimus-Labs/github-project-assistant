from groq import Groq
from typing import List, Dict, Optional
from ..config import config
import json


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

    async def generate_scanned_result(self, repo_info: Dict) -> List[Dict]:
        """Generate a comprehensive report based on the scanned results."""

        # Prepare a more structured prompt
        prompt = """You are a code analysis expert. Analyze the provided repository information for potential issues and vulnerabilities.
        Examine each file's content and commit history for:

        1. Code Security:
           - Security vulnerabilities (e.g., SQL injection, XSS)
           - Insecure data handling
           - Authentication/authorization issues
           - Unsafe dependencies

        2. Code Quality:
           - Anti-patterns
           - Code duplication
           - Complex/unmaintainable code
           - Poor error handling
           - Performance bottlenecks

        3. Data Safety:
           - Exposed credentials
           - API keys or tokens
           - Sensitive data in code
           - Insecure configurations

        For each issue found, return a JSON object in this exact format:
        {
            "findings": [
                {
                    "severity": "Critical/High/Medium/Low",
                    "category": "Security/Quality/Data",
                    "description": "Clear description of the issue",
                    "location": "Specific file path or location",
                    "recommendation": "Specific steps to fix the issue"
                }
            ]
        }

        Repository Information:
        """

        # Add relevant repo info while keeping prompt size manageable
        filtered_repo_info = {
            "metadata": repo_info.get("repo_metadata", {}),
            "files": [
                {
                    "path": f.get("path"),
                    "content": f.get("content")[:1000],  # Limit content size
                    "last_modified": f.get("last_modified"),
                }
                for f in repo_info.get("files", [])
            ],
            "recent_commits": repo_info.get("commit_history", [])[:5],  # Last 5 commits
        }

        prompt += json.dumps(filtered_repo_info, indent=2)

        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=config.default_model,
                temperature=0.7,
                max_tokens=2000,
            )

            response_text = response.choices[0].message.content.strip()

            # Try to extract JSON from the response
            try:
                # First try to parse the entire response as JSON
                result = json.loads(response_text)

                # Ensure we have the expected structure
                if isinstance(result, dict) and "findings" in result:
                    findings = result["findings"]
                elif isinstance(result, list):
                    findings = result
                else:
                    findings = [result]

            except json.JSONDecodeError:
                # If that fails, try to find JSON-like structure in the text
                import re

                json_match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", response_text)

                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        if isinstance(result, dict) and "findings" in result:
                            findings = result["findings"]
                        elif isinstance(result, list):
                            findings = result
                        else:
                            findings = [result]
                    except:
                        # If JSON parsing fails, create a structured finding about the issue
                        findings = [
                            {
                                "severity": "Medium",
                                "category": "Quality",
                                "description": "Code analysis completed with parsing issues",
                                "location": "Repository-wide",
                                "recommendation": "Review the codebase manually or try scanning specific directories",
                            }
                        ]
                else:
                    # Create findings from text analysis if no JSON structure found
                    findings = [
                        {
                            "severity": "Medium",
                            "category": "Quality",
                            "description": "Code analysis completed but structured results unavailable",
                            "location": "Repository-wide",
                            "recommendation": "Try scanning with different parameters or review specific files",
                        }
                    ]

            # Validate and clean findings
            cleaned_findings = []
            for finding in findings:
                if isinstance(finding, dict):
                    cleaned_finding = {
                        "severity": finding.get("severity", "Medium"),
                        "category": finding.get("category", "Quality"),
                        "description": finding.get(
                            "description", "No description provided"
                        ),
                        "location": finding.get("location", "Unknown"),
                        "recommendation": finding.get(
                            "recommendation", "No recommendation provided"
                        ),
                    }
                    cleaned_findings.append(cleaned_finding)

            return cleaned_findings or [
                {
                    "severity": "Low",
                    "category": "Info",
                    "description": "No significant issues found",
                    "location": "Repository-wide",
                    "recommendation": "Continue monitoring and following best practices",
                }
            ]

        except Exception as e:
            return [
                {
                    "severity": "High",
                    "category": "Error",
                    "description": f"Analysis error: {str(e)}",
                    "location": "N/A",
                    "recommendation": "Check your Groq API configuration and try again",
                }
            ]
