import Dimensions
import Parameters
import stress_factors
import streamlit as st
from Enum_vals import Section, Member, Code, Run

def create_Dim(member:Member,code: Code):
    """Instantiate Dimensions"""
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

def create_Prm(Dim_C,Dim_B):
    """Instantiate Parameters"""
    geom_container = st.beta_container()
    Prm = Parameters.Parameters(Dim_C,Dim_B,Run.SINGLE)
    Prm.dim_params()
    st.latex(Prm.dim_params_latex)
    Prm.st_geom_picker()
    Prm.calc_overlap()
    st.latex(Prm.overlap_latex)
    Prm.check_geom()
    Prm.st_message_geom(geom_container)
    return Prm

def create_SF(Prm: Parameters.Parameters):
    """Instantiate stress factors"""
    SF = stress_factors.stress_factors(Prm, Run.SINGLE)
    SF.SCF()
    st.write(SF.SCF_chax)
    st.latex(SF.SCF_latex)