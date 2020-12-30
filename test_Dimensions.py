"""
Testing Dimensions Class
"""
import Dimensions
import pytest
import pandas as pd
#from pandas._testing import assert_frame_equal
from Enum_vals import Section, Member, Code

#('SHS','AS'), ('RHS','AS'),('CHS','AS'),('SHS','EN'), ('RHS','EN'),('CHS','EN')

@pytest.mark.parametrize('section_type',
                        [s for s in Section]
                        )
def test_load_data_necessary_columns(section_type):
    """
    This test checks that all necessary column headers have been extracted.
    This ensures the dataframe will be able to be read by the database
    Future functionality requiring this test may be adding other standards csv
    """
    Dim = Dimensions.Dimensions(section_type,Member.CHORD,Code.AS)
    Dim.load_data()
    assert pd.Series(['d', 'Ix','t','Area']).isin(Dim.hs_data.columns).all()
    if section_type is not Section.CHS: assert "b" in Dim.hs_data
    if section_type is Section.RHS: assert "Iy" in Dim.hs_data

@pytest.mark.parametrize('section_type,options,props',
                        [(Section.SHS,'400 x 400 x 16.0 SHS',(0.4, 0.4, 0.016, 571e-6, 571e-6, 23700e-6))]
                        )
def test_populate(section_type,options,props):
    Dim = Dimensions.Dimensions(section_type,Member.CHORD,Code.AS)
    Dim.load_data()
    Dim.hs_chosen = Dim.hs_data[Dim.hs_data['Dimensions'] == options]
    Dim.reverse_axes = False
    Dim.populate()
    assert (Dim.b, Dim.d, Dim.t,Dim.Iy, Dim.Ix,Dim.area) == props

