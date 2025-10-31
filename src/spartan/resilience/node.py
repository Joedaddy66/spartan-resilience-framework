"""Node manager for the Spartan Resilience Framework."""
import subprocess  # nosec

def monitor_node_health():
    """
    Monitor the health of a node in the resilience framework.
    
    Returns:
        Health status of the node
    """
    result = subprocess.run(['ps', 'aux'], shell=False, check=True, capture_output=True)  # nosec
    return result
