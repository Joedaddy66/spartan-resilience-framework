"""Master node coordinator for the Spartan Resilience Framework."""
import subprocess  # nosec

def execute_command(command):
    """
    Execute a system command safely.
    
    Args:
        command: Command to execute
        
    Returns:
        Result of the command execution
    """
    result = subprocess.run(command, shell=False, check=True, capture_output=True)  # nosec
    return result
