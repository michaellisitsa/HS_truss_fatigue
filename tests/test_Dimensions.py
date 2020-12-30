"""
Testing Dimensions Class
"""

import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir) 

import Dimensions
import pytest
import pandas as pd
#from pandas._testing import assert_frame_equal
from Enum_vals import Section, Member, Code

#('SHS','AS'), ('RHS','AS'),('CHS','AS'),('SHS','EN'), ('RHS','EN'),('CHS','EN')

load_data_params = []
for s in Section:
    for c in Code:
        load_data_params.append((s,c))

@pytest.mark.parametrize('section_type,code',
                        load_data_params
                        )
def test_load_data_necessary_columns(section_type,code):
    """
    This test checks that all necessary column headers have been extracted.
    It does not check that the values extracted are equal to the csv
    This ensures the dataframe will be able to be read by the database
    Future functionality requiring this test may be adding other standards csv
    """
    Dim = Dimensions.Dimensions(section_type,Member.CHORD,code)
    Dim.load_data()
    assert pd.Series(['d', 'Ix','t','Area']).isin(Dim.hs_data.columns).all()
    if section_type is not Section.CHS: assert "b" in Dim.hs_data
    if section_type is Section.RHS: assert "Iy" in Dim.hs_data


@pytest.mark.parametrize('section_type,options,def_option,def_reverse_axes',
                        [(Section.SHS,'400 x 400 x 16.0 SHS',0,False),
                        (Section.RHS,'400 x 300 x 16.0 RHS',0,False)]
                        )
def test_st_lookup(section_type,options,def_option,def_reverse_axes):
    """
    Test to test func st_lookup which is a mixture of:
    - Streamlit commands (mocked by default values)
    - Conditional Expressions
    **Not sure if this test provides a lot of benefit, but keep it because it adds coverage.
    """
    Dim = Dimensions.Dimensions(section_type,Member.CHORD,Code.AS)
    Dim.load_data()
    Dim.st_lookup(def_option,def_reverse_axes)
    assert (Dim.hs_chosen['Dimensions'].iloc[0], Dim.reverse_axes) == (options,def_reverse_axes)


@pytest.mark.parametrize('section_type,options,props',
                        [(Section.SHS,'400 x 400 x 16.0 SHS',(0.4, 0.4, 0.016, 571e-6, 571e-6, 23700e-6))]
                        )
def test_populate(section_type,options,props):
    """
    This test checks that subject to a section_type (e.g. SHS), and selection in the list (e.g. 400 x 400 x 16 SHS)
    provide correct:
    - Section dimensions
    - Section Properties (e.g. Ix) 
    - Correct SI units on output (hardcoded values are in SI units)
    """
    Dim = Dimensions.Dimensions(section_type,Member.CHORD,Code.AS)
    Dim.load_data()
    Dim.hs_chosen = Dim.hs_data[Dim.hs_data['Dimensions'] == options]
    Dim.reverse_axes = False
    Dim.populate()
    assert (Dim.b, Dim.d, Dim.t,Dim.Iy, Dim.Ix,Dim.area) == props

@pytest.mark.parametrize('section_type,def_d,def_b,def_t',
                        [(Section.SHS,400.0,400.0,16.0),
                        (Section.RHS,400.0,300.0,16.0),
                        (Section.CHS,508.0,508.0,12.7)]
                        )
def test_st_custom_sec_picker(section_type,def_b,def_d,def_t):
    """
    Testing st_custom_sec_picker mainly for:
    - correct unit conversion is maintained
    - CHS check correctly sets 
    """
    Dim = Dimensions.Dimensions(section_type,Member.CHORD,Code.AS)
    Dim.st_custom_sec_picker(def_d,def_b,def_t)
    assert (def_d/1000,def_b/1000,def_t/1000) == pytest.approx((Dim.d,Dim.b,Dim.t))


@pytest.mark.parametrize('section_type,options,props',
                        [(Section.SHS,'400 x 400 x 16.0 SHS',(0.4, 0.4, 0.016, 571e-6, 571e-6, 23700e-6)),
                        (Section.CHS,'508 x 508 x 12.7 SHS',(0.508, 0.508, 0.0127, 606e-6, 606e-6, 19800e-6))]
                        )
def test_calculate_custom_sec(section_type,options,props):
    """
    Compare custom section calculator with tables. Checks that:
    - Returns equivalent (within 2%) values to data tables (in SI units) Ix, Iy, area 
    """
    Dim = Dimensions.Dimensions(section_type,Member.CHORD,Code.AS)
    Dim.b = props[0]
    Dim.d = props[1]
    Dim.t = props[2]
    Ix_compare = props[3]
    Iy_compare = props[4]
    area_compare = props[5]
    Dim.calculate_custom_sec()
    assert (Dim.Iy, Dim.Ix,Dim.area) == pytest.approx((Iy_compare,Ix_compare,area_compare),rel=2e-2)

