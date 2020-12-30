import Dimensions
import streamlit as st
from Enum_vals import Section, Member, Code

def create_Dim(member:Member,code: Code):
    section_type = Section[st.sidebar.radio(f"Choose Type of {member.name} : ",[type.name for type in Section],index=0)]
    #Instantiate Dimension Instance for Chord
    Dim = Dimensions.Dimensions(section_type,member,code)
    if st.sidebar.checkbox("Custom Section:",key=f"custom_sec_{member.name}"):
        Dim.st_custom_sec_picker()
        Dim.calculate_custom_sec()
        st.write(vars(Dim))
    else:
        #For standard sections from catalogue
        Dim.load_data()
        Dim.st_lookup()
        Dim.populate()
        st.write(vars(Dim))
    return Dim