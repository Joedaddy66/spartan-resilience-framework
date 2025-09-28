"""
Test security-related functionality and validate security measures.
"""
import sys
import pathlib
import subprocess

# Ensure "src" is on path when running from repo without install
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))


def test_no_hardcoded_secrets():
    """Test that there are no obvious hardcoded secrets in the source code."""
    # This is a basic check - the real security scanning happens in CI
    src_dir = pathlib.Path(__file__).resolve().parents[1] / "src"
    
    # Check for common secret patterns
    secret_patterns = [
        "password",
        "api_key", 
        "secret_key",
        "private_key",
        "token"
    ]
    
    found_secrets = []
    for python_file in src_dir.glob("**/*.py"):
        content = python_file.read_text().lower()
        for pattern in secret_patterns:
            if pattern in content and "=" in content:
                # Likely a hardcoded assignment
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if pattern in line and "=" in line and not line.strip().startswith("#"):
                        found_secrets.append(f"{python_file.name}:{i+1}: {line.strip()}")
    
    # For this test, we expect no hardcoded secrets
    assert not found_secrets, f"Potential hardcoded secrets found: {found_secrets}"


def test_requests_library_version():
    """Test that we're using a secure version of the requests library."""
    try:
        import requests
        version = requests.__version__
        # Ensure we're using a reasonably recent version
        major, minor, patch = map(int, version.split('.'))
        assert major >= 2, f"requests major version too old: {version}"
        assert minor >= 25, f"requests minor version too old: {version}"
        print(f"✓ Using secure requests version: {version}")
    except ImportError:
        # requests is optional for this project - it's a transitive dependency
        print("ℹ requests not directly imported (transitive dependency only)")


def test_no_deprecated_imports():
    """Test that we don't use any deprecated or insecure imports."""
    src_dir = pathlib.Path(__file__).resolve().parents[1] / "src"
    
    # List of deprecated/insecure modules to avoid
    deprecated_modules = [
        "md5",  # deprecated, use hashlib
        "sha",  # deprecated, use hashlib
        "cgi",  # many vulnerabilities
    ]
    
    found_deprecated = []
    for python_file in src_dir.glob("**/*.py"):
        content = python_file.read_text()
        for module in deprecated_modules:
            if f"import {module}" in content or f"from {module}" in content:
                found_deprecated.append(f"{python_file.name}: imports {module}")
    
    assert not found_deprecated, f"Deprecated modules found: {found_deprecated}"


def test_random_usage_is_appropriate():
    """Test that random usage is appropriate for the mathematical context."""
    # This project uses random for mathematical algorithms (not cryptographic)
    # which is acceptable - bandit will flag this but it's a false positive
    # for mathematical/scientific code
    src_dir = pathlib.Path(__file__).resolve().parents[1] / "src"
    
    found_random = []
    for python_file in src_dir.glob("**/*.py"):
        content = python_file.read_text()
        if "import random" in content:
            # Check that it's used in mathematical context
            if "miller_rabin" in content or "pollards_rho" in content:
                found_random.append(f"{python_file.name}: mathematical random usage (OK)")
            else:
                found_random.append(f"{python_file.name}: non-mathematical random usage")
    
    # We expect to find mathematical usage
    math_usage = [item for item in found_random if "(OK)" in item]
    assert math_usage, "Should find mathematical random usage"
    
    # But no non-mathematical usage
    non_math_usage = [item for item in found_random if "(OK)" not in item]
    assert not non_math_usage, f"Non-mathematical random usage found: {non_math_usage}"