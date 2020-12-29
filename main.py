import streamlit as st
from handcalcs import handcalc

#Import other files
import Dimensions
import Parameters

#Global settings
code = st.sidebar.radio("Which code:",["AS","EN"])
chord_type = st.sidebar.radio("Choose Type of Chord:",("SHS","RHS","CHS"),index=0)

#Instantiate Dimension Instance for Chord
Dim = Dimensions.Dimensions(chord_type,'chord',code)
if st.sidebar.checkbox("Custom Section:",key="custom_sec_chord"):
    Dim.custom_section()
    Dim.frame_props()
    fig, ax = Dim.visualise()
    st.pyplot(fig)
    st.write(vars(Dim))
    # chord_func = secprops.custom_hs(self.d0,self.t0)
    # (area, ixx, iyy, ixy, j, phi) = (chord_func.chs() if section_type == "CHS" else chord_func.rhs(b0))
else:
    Dim.load_data()
    Dim.st_lookup()
    Dim.populate()
    st.write(vars(Dim))