"""
Madam Herta AI Assistant Package.
"""

import sys
import warnings

# Ensure UTF-8 output streams on platforms where default console encoding is legacy (e.g. cp1252 on Windows)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Suppress PyTorch JIT and library future deprecation warnings for clean terminal output
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

__version__ = "1.0.0"


