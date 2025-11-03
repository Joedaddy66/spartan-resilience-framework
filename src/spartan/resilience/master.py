"""Master node coordinator for the Spartan Resilience Framework."""
import subprocess  # nosec
from typing import List

def execute_command(command: List[str]):
    """
    Execute a system command safely.
    
    Args:
        command: Command to execute as a list of strings (e.g., ['ls', '-la'])
                 Commands are executed without shell interpretation for security.
        
    Returns:
        subprocess.CompletedProcess: Result of the command execution
        
    Example:
        >>> result = execute_command(['echo', 'hello'])
    """
    result = subprocess.run(command, shell=False, check=True, capture_output=True)  # nosec
    return result
