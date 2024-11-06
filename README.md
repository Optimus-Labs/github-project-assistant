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

## Installing the CLI Tool in your OS

### Windows

1. **Create a Virtual Environment (Optional)**:

   - It's recommended to use a virtual environment to isolate the GPA dependencies from your system Python installation.
   - Open the command prompt and run the following commands:
     ```
     python -m venv gpa-venv
     gpa-venv\Scripts\activate
     ```

2. **Install the Package**:

   - Download the latest release from the [GitHub repository](https://github.com/Optimus-Labs/github-project-assistant/releases).
   - Unzip the downloaded file and navigate to the project directory.
   - Run the following command to install the package:
     ```
     pip install gpa-0.1.0-py3-none-any.whl
     ```

3. **Set up Environment Variables**:
   - Open the Windows environment variables editor (e.g., search for "environment variables" in the start menu).
   - Add the following variables:
     - `GROQ_API_KEY`: Your Groq API key
     - `GITHUB_TOKEN`: Your GitHub personal access token

Now you can use the `gpa` command from anywhere in your Windows command prompt or PowerShell.

### Linux/macOS

1. **Create a Virtual Environment (Optional)**:

   - It's recommended to use a virtual environment to isolate the GPA dependencies from your system Python installation.
   - Open a terminal and run the following commands:
     ```
     python3 -m venv gpa-venv
     source gpa-venv/bin/activate
     ```

2. **Install the Package**:

   - Download the latest release from the [GitHub repository](https://github.com/Optimus-Labs/github-project-assistant/releases).
   - Unzip the downloaded file and navigate to the project directory.
   - Run the following command to install the package:
     ```
     pip install gpa-0.1.0-py3-none-any.whl
     ```

3. **Set up Environment Variables**:
   - Open your shell configuration file (e.g., `.bashrc`, `.zshrc`) in a text editor.
   - Add the following lines:
     ```
     export GROQ_API_KEY="your-groq-api-key"
     export GITHUB_TOKEN="your-github-token"
     ```
   - Save the file and run `source ~/.bashrc` (or the appropriate command for your shell) to apply the changes.

Now you can use the `gpa` command from anywhere in your terminal.

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

### Code Review Assistant

Analyze and review pull requests with AI-powered insights:

```bash
# Analyze a pull request
gpa review analyze 123

# Analyze with simple explanation
gpa review analyze 123 --explain

# Generate specific review comments
gpa review analyze 123 --comments

# Analyze and merge a pull request
gpa review merge 123

# Merge with specific method
gpa review merge 123 --method rebase

# Merge without analysis
gpa review merge 123 --no-analyze
```

#### Code Review Features:

1. **Comprehensive Analysis**

   - Code quality assessment
   - Potential bugs and issues
   - Performance considerations
   - Security implications
   - Best practices evaluation

2. **Simple Explanations**

   - Non-technical summaries of changes
   - Impact analysis
   - Functionality changes
   - Business value assessment

3. **Review Comments**

   - Specific, actionable feedback
   - Location-based suggestions
   - Implementation recommendations
   - Best practice guidance

4. **Merge Assistance**
   - Pre-merge analysis
   - Conflict detection
   - Multiple merge methods
   - Safety checks

#### Best Practices for Code Reviews

1. **Before Review:**

   - Ensure CI checks have passed
   - Verify PR description is complete
   - Check for merge conflicts

2. **During Review:**

   - Start with the AI analysis
   - Review simple explanation for context
   - Consider generated comments
   - Verify suggestions manually

3. **Before Merging:**
   - Run analysis with `--analyze`
   - Choose appropriate merge method
   - Verify mergeable status
   - Review final changes

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

### GPA Scan

```bash
# Basic scan
gpa scan run --repo "your-username/your-repo-name"

# Scan with specific category (e.g., security)
gpa scan run --repo "your-username/your-repo-name" --category security

# Output results in JSON format
gpa scan run --repo "your-username/your-repo-name" --output json
```

#### Scan Categories and Features

1. **Security Checks**

   - Detects vulnerabilities such as SQL injections, XSS, insecure data handling, and more.

2. **Code Quality**

   - Identifies code duplication, anti-patterns, unmaintainable code, and error handling issues.

3. **Data Safety**
   - Flags exposed credentials, sensitive data, and insecure configurations.

#### Example Usage:

- **Basic Scan**: Run a quick scan on your repository.
- **Category Filter**: Focus on specific categories like security or quality.
- **Detailed Output**: Generate structured JSON output for custom integrations.

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

### Documentation Helper

Automatically generate and improve project documentation:

```bash
# Generate or update README
gpa docs readme

# Preview README without saving
gpa docs readme --preview

# Save README to custom location
gpa docs readme --output ./docs/README.md

# Get documentation improvement suggestions
gpa docs suggest ./docs/api.md

# Suggest improvements based on specific changes
gpa docs suggest ./docs/api.md --diff changes.diff

# Generate code documentation
gpa docs generate ./src/module.py

# Generate with specific style
gpa docs generate ./src/module.py --style numpy

# Preview code documentation
gpa docs generate ./src/module.py --preview
```

#### Documentation Features:

1. **README Generation**

   - Project structure analysis
   - Automatic section organization
   - Installation instructions
   - Usage examples
   - Feature documentation

2. **Documentation Improvements**

   - Change-based suggestions
   - Missing documentation detection
   - Clarity improvements
   - Example suggestions
   - Technical accuracy checks

3. **Code Documentation**
   - Multiple documentation styles
   - Function and class documentation
   - Parameter descriptions
   - Return value documentation
   - Usage examples
   - Exception documentation

#### Best Practices for Documentation

1. **README Management:**

   - Preview before saving
   - Keep installation steps updated
   - Include all configuration options
   - Maintain clear examples
   - Regular updates with changes

2. **Documentation Updates:**

   - Review suggestions regularly
   - Update with code changes
   - Maintain consistency
   - Include practical examples
   - Verify technical accuracy

3. **Code Documentation:**
   - Choose appropriate style
   - Document all parameters
   - Include return values
   - Add usage examples
   - Note important exceptions

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
