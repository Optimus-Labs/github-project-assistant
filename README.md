# GitHub Project Assistant (GPA)

A comprehensive CLI tool for managing GitHub projects, leveraging Groq's AI models for intelligent PR descriptions, commit messages, and issue management.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Optimus-Labs/github-project-assistant
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

### Commit Management

```bash
# Generate and create a commit
gpa commit

# Preview generated commit message without committing
gpa commit --preview

# Use manual commit message
gpa commit -m "feat: add new feature"
```

### Pull Request Management

Create pull requests with AI-generated descriptions based on your commits:

```bash
# Preview PR description before creation
gpa pr create --preview

# Create PR with default settings
gpa pr create

# Create PR with custom title
gpa pr create --title "Feature: Add authentication system"

# Create PR with specific base branch
gpa pr create --base main
```

#### PR Creation Process:

1. Ensure your changes are committed and pushed to your branch
2. Run the PR creation command
3. Review the generated description
4. Confirm creation when prompted

### Issue Management

#### Creating Issues

```bash
# Create a basic issue
gpa issue create --title "Add user authentication"

# Create issue with context from a file
gpa issue create --title "Fix performance bug" --file ./slow_function.py

# Preview issue before creation
gpa issue create --title "Update documentation" --preview
```

#### Summarizing Issues

```bash
# Get overview of all open issues
gpa issue summarize

# View closed issues
gpa issue summarize --state closed

# Filter issues by labels
gpa issue summarize --label bug --label high-priority
```

#### Managing Labels

```bash
# Get AI-suggested labels for an issue
gpa issue label 123

# Apply suggested labels automatically
gpa issue label 123 --no-preview
```

## Best Practices

### For Pull Requests

1. **Before Creating:**

   - Ensure all changes are committed and pushed
   - Fetch latest changes from the base branch
   - Resolve any conflicts

2. **During Creation:**
   - Use descriptive titles
   - Review the AI-generated description
   - Verify the base branch is correct

### For Issues

1. **Creating Issues:**

   - Use clear, concise titles
   - Provide context files when relevant
   - Always preview before creating
   - Include reproduction steps for bugs

2. **Managing Issues:**
   - Regularly summarize to maintain project overview
   - Use labels for better organization
   - Review suggested labels before applying

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

## Troubleshooting

### Common PR Issues

1. **"Repository not initialized"**

```bash
# Initialize git repository
git init
git remote add origin your-repo-url
```

2. **Base branch comparison fails**

```bash
# Fetch latest changes
git fetch origin
```

3. **Cannot push to GitHub**

```bash
# Verify remote URL
git remote -v

# Update if needed
git remote set-url origin your-repo-url
```

### Common Issue Management Issues

1. **Context file not found:**

   - Verify file path is correct
   - Ensure file has read permissions

2. **Label application fails:**
   - Verify issue number exists
   - Check GitHub permissions
   - Ensure labels are valid for repository
