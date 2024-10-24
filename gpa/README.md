# GitHub Project Assistant (GPA)

A comprehensive CLI tool for managing GitHub projects, leveraging Groq's AI models.

## Installation

1. Clone the repository:

```bash
git clone <your-repo-url>
cd github-project-assistant
```

2. Install the package in editable mode:

```bash
pip install -e .
```

3. Set up environment variables:

```bash
export GROQ_API_KEY="your-groq-api-key"
export GITHUB_TOKEN="your-github-token"
```

## Usage

```bash
# Generate and create a commit
gpa commit

# Preview generated commit message without committing
gpa commit --preview

# Use manual commit message
gpa commit -m "feat: add new feature"
```

## Development

To set up the development environment:

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install development dependencies:

```bash
pip install -e ".[dev]"
```
