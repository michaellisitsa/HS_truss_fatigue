import Dimensions
import Geometry
import SCFs
import Forces
import Stresses
import streamlit as st
from Enum_vals import Joint, Section, Member, Code, Run
from typing import Union

from math import pi

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

def create_Geom(Dim_C,Dim_B,joint: Joint):
    """Instantiate Geomery"""
    geom_container = st.beta_container()
    if joint is Joint.K:
        e, chordspacing, L_chord, div_chord = Geometry.st_geom_Kjoint_picker(Dim_C)
        Geom = Geometry.K_joint(Dim_C, Dim_B,e, chordspacing, L_chord, div_chord, Run.SINGLE)
        st.latex(Geom.latex)
        Geom.check_geom()
        Geom.st_message_geom(geom_container)
        force = Forces.Forces()
        force.st_forces_picker()
        fig = Geom.plot_geom(force=force)
        st.altair_chart(fig)
    else:
        L_chord, div_chord, angle = Geometry.st_geom_Tjoint_picker(Dim_C)
        Geom = Geometry.T_joint(Dim_C, Dim_B, L_chord, div_chord, angle, 0.7, Run.SINGLE)
        Geom.check_geom()
        Geom.st_message_geom(geom_container)
        st.latex(Geom.latex)
        force = Forces.Forces()
        force.st_forces_picker()
    return Geom, force

def create_SCFs(Geom, joint: Joint):
    """Instantiate stress factors"""
    if joint is Joint.K:
        SCF = SCFs.K_SCF(Geom, Run.SINGLE)
        st.latex(SCF.latex)
    else:
        SCF = SCFs.T_SCF(Geom, Run.SINGLE)
        st.latex(SCF.latex)
    return SCF

def create_Stresses(Dim_C: Union[Dimensions.database_sec,Dimensions.custom_sec],
                    Dim_B: Union[Dimensions.database_sec,Dimensions.custom_sec],
                    Geom: Geometry.K_joint, force, SCF):
    MF_chord = Stresses.MF_func(Dim_C.section_type, Geom.gap, Member.CHORD)
    MF_brace = Stresses.MF_func(Dim_B.section_type, Geom.gap, Member.BRACE)
    Stress = Stresses.Stress(Run.SINGLE,force,Dim_C, Dim_B, SCF, Geom,MF_chord, MF_brace)
    st.latex(Stress.stresses_latex)
    return Stress
