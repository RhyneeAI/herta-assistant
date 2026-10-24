"""
Madam Herta AI Assistant Package.
"""

import warnings

# Suppress PyTorch JIT and library future deprecation warnings for clean terminal output
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

__version__ = "1.0.0"

