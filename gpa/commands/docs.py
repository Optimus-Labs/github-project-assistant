import typer
import asyncio
import uvicorn
import markdown2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import subprocess
import tempfile
import webbrowser
import threading
from typing import Optional
import os

from ..services.file_service import FileService
from ..services.doc_service import GitService
from ..services.groq_service import GroqService
from ..utils.formatting import print_success, print_error, print_warning, confirm_action

app = typer.Typer()


class ReadmePreviewServer:
    def __init__(self, readme_path: str):
        """
        Initialize the README preview server with live editing capabilities.

        :param readme_path: Path to the README.md file
        """
        self.readme_path = Path(readme_path)
        self.fastapi_app = FastAPI()

        # Create a temporary static directory if it doesn't exist
        self.static_dir = Path(__file__).parent / "static"
        self.static_dir.mkdir(exist_ok=True)

        self.setup_routes()

    def setup_routes(self):
        """
        Set up FastAPI routes for README preview and editing.
        """

        @self.fastapi_app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            try:
                while True:
                    # Receive markdown content from client
                    data = await websocket.receive_text()

                    # Save the updated content to the file
                    self.readme_path.write_text(data)

                    # Convert markdown to HTML for preview
                    html_content = markdown2.markdown(
                        data, extras=["tables", "fenced-code-blocks"]
                    )

                    # Send back the HTML preview
                    await websocket.send_text(html_content)

            except WebSocketDisconnect:
                print_warning("WebSocket connection closed")

        @self.fastapi_app.get("/")
        async def serve_editor():
            """
            Serve the live markdown editor and preview page.
            """
            return HTMLResponse(content=self.get_editor_html())

        # Serve static files from a directory that is guaranteed to exist
        self.fastapi_app.mount(
            "/static", StaticFiles(directory=self.static_dir), name="static"
        )

    def get_editor_html(self) -> str:
        """
        Generate the HTML for the live markdown editor.

        :return: HTML content with embedded JavaScript for live editing
        """
        # Create a simple CSS file in the static directory for custom styles
        (self.static_dir / "styles.css").write_text("""
        body { font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji; }
        .container { display: flex; height: 100vh; }
        #editor, #preview { width: 50%; padding: 10px; box-sizing: border-box; }
        #editor { background: #f4f4f4; resize: none; }
        #preview { background: white; overflow-y: auto; }
        .markdown-body { padding: 15px; }
        """)

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>README Preview</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.1.0/github-markdown.min.css">
            <link rel="stylesheet" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <textarea id="editor" rows="30">{self.readme_path.read_text()}</textarea>
                <div id="preview" class="markdown-body"></div>
            </div>
            <script>
                const socket = new WebSocket('ws://' + window.location.host + '/ws');
                const editor = document.getElementById('editor');
                const preview = document.getElementById('preview');
                
                // Initial render
                preview.innerHTML = marked.parse(editor.value);
                
                editor.addEventListener('input', () => {{
                    socket.send(editor.value);
                }});
                
                socket.onmessage = (event) => {{
                    preview.innerHTML = event.data;
                }};
            </script>
            <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        </body>
        </html>
        """

    def open_browser(self, port: int):
        """
        Open the default web browser to the preview server.

        :param port: Port number the server is running on
        """
        webbrowser.open(f"http://localhost:{port}")

    def run(self, host: str = "127.0.0.1", port: int = 8000):
        """
        Run the preview server.

        :param host: Host to bind the server
        :param port: Port to run the server on
        """
        # Use threading to open browser after server starts
        threading.Thread(target=self.open_browser, args=(port,), daemon=True).start()

        # Run the server
        uvicorn.run(self.fastapi_app, host=host, port=port)


@app.command()
def preview(
    path: str = typer.Option("README.md", "--path", "-p", help="Path to README file"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind the server"),
    port: int = typer.Option(8000, "--port", help="Port to run the server"),
    editor: Optional[str] = typer.Option(
        None, "--editor", "-e", help="Open with specific text editor"
    ),
) -> None:
    """
    Preview and edit README with live server and optional text editor.

    Supports live markdown rendering and optional external text editor integration.
    """
    try:
        # Ensure README exists, generate if not
        readme_path = Path(path)
        if not readme_path.exists():
            file_service = FileService()
            git_service = GitService()
            groq_service = GroqService()

            # Get project files and git info
            project_files = file_service.get_project_files([".py", ".md", ".txt"])

            try:
                git_info = git_service.get_repo_info()
            except Exception:
                git_info = {
                    "description": "No description available",
                    "default_branch": "main",
                    "topics": [],
                }

            # Generate README
            content = asyncio.run(groq_service.generate_readme(project_files, git_info))

            # Save generated README
            readme_path.write_text(content)
            print_success(f"Generated README at {path}")

        # Open with external editor if specified
        if editor:
            try:
                subprocess.Popen([editor, str(readme_path)])
                print_success(f"Opened {path} in {editor}")
            except Exception as e:
                print_error(f"Failed to open with {editor}: {e}")

        # Start preview server
        preview_server = ReadmePreviewServer(str(readme_path))
        print_success(f"Starting README preview server at http://{host}:{port}")
        print_warning("Press Ctrl+C to stop the server")
        preview_server.run(host, port)

    except Exception as e:
        print_error(f"An error occurred: {str(e)}")
        raise typer.Exit(1)
