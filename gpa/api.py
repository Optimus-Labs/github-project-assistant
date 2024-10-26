from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
import subprocess
import threading
import os
import signal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
api = Api(
    app,
    version="1.0",
    title="GitHub Project Assistant API",
    description="API for executing GitHub Project Assistant commands",
)

# Define request and response models for OpenAPI documentation
gpa_command_model = api.model(
    "GPACommand",
    {
        "command": fields.String(required=True, description="GPA command to execute"),
        "timeout": fields.Integer(
            default=120, description="Command timeout in seconds"
        ),
        "working_dir": fields.String(
            default=".", description="Working directory for command execution"
        ),
    },
)

error_response_model = api.model(
    "ErrorResponse",
    {
        "error": fields.String(description="Error message"),
        "partial_output": fields.String(
            description="Partial output if available", default=""
        ),
    },
)

success_response_model = api.model(
    "SuccessResponse",
    {
        "output": fields.String(description="Command output"),
        "error": fields.String(description="Error output if any", default=""),
        "status": fields.Integer(description="Command exit status"),
    },
)


def run_command_with_timeout(cmd: str, working_dir: str, timeout: int = 120):
    """
    Run a command with extended timeout and progress monitoring.
    """
    try:
        logger.info(f"Starting command: {cmd} in directory: {working_dir}")

        # Expand working directory path
        working_dir = os.path.expanduser(working_dir)
        working_dir = os.path.abspath(working_dir)

        if not os.path.exists(working_dir):
            return {
                "output": "",
                "error": f"Working directory does not exist: {working_dir}",
                "status": -1,
            }

        # Verify it's a git repository
        if not os.path.exists(os.path.join(working_dir, ".git")):
            return {
                "output": "",
                "error": f"Not a git repository: {working_dir}",
                "status": -1,
            }

        # Split command properly to handle arguments
        cmd_parts = cmd.split()

        # Create process with pipes
        process = subprocess.Popen(
            cmd_parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
            preexec_fn=os.setsid,
            cwd=working_dir,  # Set working directory
        )

        output_lines = []
        error_lines = []

        def read_output(pipe, lines):
            for line in iter(pipe.readline, ""):
                lines.append(line)
                logger.info(f"Output: {line.strip()}")

        stdout_thread = threading.Thread(
            target=read_output, args=(process.stdout, output_lines)
        )
        stderr_thread = threading.Thread(
            target=read_output, args=(process.stderr, error_lines)
        )

        stdout_thread.daemon = True
        stderr_thread.daemon = True

        stdout_thread.start()
        stderr_thread.start()

        # Wait for process with timeout
        try:
            process.wait(timeout=timeout)
            stdout_thread.join(1)
            stderr_thread.join(1)

            return {
                "output": "".join(output_lines),
                "error": "".join(error_lines),
                "status": process.returncode,
            }

        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)

            return {
                "output": "".join(output_lines),
                "error": f"Command timed out after {timeout} seconds. Partial output: {''.join(error_lines)}",
                "status": -1,
            }

    except Exception as e:
        logger.error(f"Error running command: {str(e)}")
        return {"output": "", "error": str(e), "status": -1}


@api.route("/api/gpa")
class GPACommandResource(Resource):
    @api.expect(gpa_command_model)
    @api.response(200, "Success", success_response_model)
    @api.response(400, "Bad Request", error_response_model)
    @api.response(500, "Internal Server Error", error_response_model)
    @api.response(504, "Gateway Timeout", error_response_model)
    def post(self):
        """
        Execute a GPA command in the specified working directory.
        """
        try:
            body = request.get_json()
            command = body.get("command", "").strip()
            if not command:
                return {"error": "Empty command"}, 400

            logger.info(f"Received command: {command}")

            # Construct the full command
            full_command = f"gpa {command}"

            # Execute command with timeout in specified directory
            result = run_command_with_timeout(
                full_command, body.get("working_dir", "."), body.get("timeout", 120)
            )

            if result["status"] == -1:
                logger.error(f"Command failed: {result['error']}")
                return {
                    "error": result["error"],
                    "partial_output": result["output"],
                }, 504 if "timeout" in result["error"] else 500

            logger.info("Command completed successfully")
            return {
                "output": result["output"],
                "error": result["error"],
                "status": result["status"],
            }

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
