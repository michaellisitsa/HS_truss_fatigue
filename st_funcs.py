import streamlit as st
import Dimensions
from Enum_vals import Section

def st_geom_picker(Dim_C: Dimensions.Dimensions):
    e = (0 if Dim_C.section_type is Section.CHS else st.sidebar.number_input('Eccentricity',-400,400,-100,step=5,format='%f') / 1000)
    chordspacing = st.sidebar.number_input('Chord spacing (mm)',100,4000,2000,step=50,format='%i') / 1000
    L_chord = st.sidebar.number_input('Length of Chord (mm)',100,30000,8000,step=100,format='%i') / 1000
    div_chord = st.sidebar.number_input('Chord divisions',1,20,4,step=1,format='%i')
    return e, chordspacing, L_chord, div_chord