import subprocess

def execute_bash(command: str) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            timeout=30
        )
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nExit Code: {result.returncode}"
    except Exception as e:
        return f"Error executing command: {str(e)}"

available_tools = {
    "execute_bash": execute_bash
}

tools_description = """
execute_bash(command: str) -> str
Executes a bash command on the local machine and returns the stdout, stderr, and exit code.
"""
