import Dimensions
import Geometry
import SCFs
import Forces
import Stresses
import streamlit as st
from Enum_vals import Section, Member, Code, Run
import plotting_funcs
from typing import Union

def create_Dim(member:Member, code: Code):
    """Instantiate Dimensions"""
    section_type = Section[st.sidebar.radio(f"Choose Type of {member.name} : ",[type.name for type in Section],index=0)]
    #Instantiate Dimension Instance for Chord
    if st.sidebar.checkbox("Custom Section:",key=f"custom_sec_{member.name}"):
        d, b, t = Dimensions.st_custom_sec_picker(section_type, member)
        return Dimensions.custom_sec(section_type, member, d, b, t)
    else:
        #For standard sections from catalogue
        section_db = Dimensions.Section_DB(section_type, member, code)
        hs_chosen, reverse_axes = Dimensions.st_lookup(section_db.hs_data, section_type, member)
        return Dimensions.database_sec(section_type, member, section_db.hs_data, hs_chosen, reverse_axes)

def create_Geom(Dim_C,Dim_B):
    """Instantiate Geomery"""
    geom_container = st.beta_container()
    e, chordspacing, L_chord, div_chord = Geometry.st_geom_picker(Dim_C)
    Geom = Geometry.Geometry(Dim_C, Dim_B,e, chordspacing, L_chord, div_chord, Run.SINGLE)
    st.latex(Geom.check_geom_latex)
    Geom.st_message_geom(geom_container)
    force = Forces.Forces()
    force.st_forces_picker()
    fig = plotting_funcs.geom_plot_altair(force=force,geom=Geom)
    st.altair_chart(fig)
    return Geom, force

def create_SCFs(Geom: Geometry.Geometry):
    """Instantiate stress factors"""
    SCF = SCFs.SCFs(Geom, Run.SINGLE)
    st.latex(SCF.SCF_latex)
    return SCF

def create_Stresses(Dim_C: Union[Dimensions.database_sec,Dimensions.custom_sec],
                    Dim_B: Union[Dimensions.database_sec,Dimensions.custom_sec],
                    Geom: Geometry.Geometry, force, SCF):
    MF_chord = Stresses.MF_func(Dim_C.section_type, Geom.gap, Member.CHORD)
    MF_brace = Stresses.MF_func(Dim_B.section_type, Geom.gap, Member.BRACE)
    Stress = Stresses.Stress(Run.SINGLE,force,Dim_C, Dim_B, SCF, Geom,MF_chord, MF_brace)
    st.latex(Stress.stresses_latex)
    return Stress
