"""cronlish — translate cron expressions into plain human language.

>>> from cronlish import describe
>>> describe("*/5 * * * *")
'Every 5 minutes'
"""
from cronlish.describe import DescribeError, describe
from cronlish.locale import terse

__version__ = "0.2.0"

__all__ = ["describe", "terse", "DescribeError", "__version__"]
