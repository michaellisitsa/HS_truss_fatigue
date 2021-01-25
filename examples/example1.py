
"""This file shows how you can manually perform calculations without using the Streamlit app
Parts of the app can therefore be re-used elsewhere, such as the custom or section_DB API call to get section properties"""

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) # type: ignore[comparison-overlap]
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

import Dimensions
import Geometry
import Forces
import streamlit as st
from Enum_vals import Section, Member, Code, Run

#Create a Dimensions object based on the type of section and its dimensions.
#The object contains calculated section properties from the section-properties module in SI units
P_chord1 = [242_000, 100_000, 40_000]
P_brace1 = [70_000, 20_000, 10_000]
M_ipchord = [800, 1_200,1_000]
for Pc, Pb, Mipb in zip(P_chord1, P_brace1, M_ipchord):
    section_db = Dimensions.Section_DB(Section.SHS,Member.CHORD,Code.AS)
    hs_chosen = section_db.pick_by_size(400,16,400)
    Dim_C = Dimensions.custom_sec(Section.RHS,Member.CHORD, d=0.4, b=0.4, t=0.016)
    Dim_B = Dimensions.database_sec(Section.SHS,Member.CHORD,section_db.hs_data,hs_chosen,False)
    Geom = Geometry.K_joint(Dim_C,Dim_B,-0.1,2.0,6.0,3.0,Run.API)
    SCF = Geom.calc_SCFs()
    force = Forces.Forces(P_chord = Pc, P_brace = Pb, M_ip_chord = Mipb)
    Stress = SCF.calc_stresses(force)
    print(f"S_rhschord = {Stress.S_rhschord},\nS_rhsbrace = {Stress.S_rhsbrace}")
#This creates a geometry section
