"""rosclaw namespace package — extend path for multi-package support."""
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)
