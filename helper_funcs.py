
from collections.abc import Callable
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Dimensions import Dimensions

from handcalcs import handcalc
from Enum_vals import Section, Member, Code, Run

def func_by_run_type(run: 'Run',args: dict, Func: Callable):
    latex = None #initiate empty
    if run is Run.SINGLE:
        latex, vals = handcalc(override="long")(Func)(**args)
    elif run is Run.ALL_SECTIONS:
        vals = Func(**args)
    return latex, vals