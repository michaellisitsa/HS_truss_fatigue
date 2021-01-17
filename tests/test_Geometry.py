"""
Testing Geometry Class
"""

"""
Testing Dimensions Class
"""

import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) # type: ignore[comparison-overlap]
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir) 

import Geometry
import pytest
import pandas as pd
#from pandas._testing import assert_frame_equal
from Enum_vals import Section, Member, Code

@pytest.mark.parametrize('section_type,code',
                        [(1.,1.)]
                        )
def test_calculate_overlap(section_type,code):
    assert section_type == code
