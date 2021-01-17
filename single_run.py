import Dimensions
import Geometry
import Stresses
import forces
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

def create_Geom(Dim_C,Dim_B):
    """Instantiate Geomery"""
    geom_container = st.beta_container()
    Geom = Geometry.Geometry(Dim_C,Dim_B,Run.SINGLE)
    Geom.dim_params()
    st.latex(Geom.dim_params_latex)
    Geom.st_geom_picker()
    Geom.calc_overlap()
    st.latex(Geom.overlap_latex)
    Geom.check_geom()
    Geom.st_message_geom(geom_container)
    force = forces.Forces()
    force.st_forces_picker()
    fig = Geom.geom_plot_altair(force)
    st.altair_chart(fig)
    return Geom

def create_Stress(Geom: Geometry.Geometry):
    """Instantiate stress factors"""
    Stress = Stresses.Stresses(Geom, Run.SINGLE)
    Stress.SCF()
    st.latex(Stress.SCF_latex)
