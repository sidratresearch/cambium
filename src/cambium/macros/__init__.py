"""Import macro classes and provide the result for other modules."""

from ..utils.other_utils import get_all_subclasses
from . import macros as macros
from .macro_utils import Macro

REGISTERED_MACROS = {cls.__name__: cls for cls in get_all_subclasses(Macro)}
