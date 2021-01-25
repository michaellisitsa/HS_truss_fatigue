
from collections.abc import Callable
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Dimensions import Dimensions

from handcalcs import handcalc
from Enum_vals import Section, Member, Code, Run

def func_by_run_type(run: 'Run',args: dict, Func: Callable):
    latex = None #initiate empty
    if run is Run.HANDCALCS:
        latex, vals = handcalc(override="long")(Func)(**args)
    elif run is Run.API:
        vals = Func(**args)
    else:
        vals = [] #will cause an error and execution to stop
    return latex, vals