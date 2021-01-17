
"""This file shows how you can manually perform calculations without using the Streamlit app
Parts of the app can therefore be re-used elsewhere, such as the custom or section_DB API call to get section properties"""

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) # type: ignore[comparison-overlap]
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

import Dimensions
import Geometry
import SCFs
import Forces
import streamlit as st
from Enum_vals import Section, Member, Code, Run
import plotting_funcs

#Create a Dimensions object based on the type of section and its dimensions.
#The object contains calculated section properties from the section-properties module in SI units
Dim = Dimensions.custom_sec(Section.RHS,Member.CHORD, d=0.4, b=0.4, t=0.016)
print(vars(Dim))

#This loads data from the relevant database stored in /data into a dataframe
section_db = Dimensions.Section_DB(Section.SHS,Member.CHORD,Code.EN)
print(type(section_db.hs_data))

#This picks a row from the hs_data dataframe and then creates a Dimension section from the chosen option
hs_chosen = section_db.pick_by_size(400,16,400)
Dim2 = Dimensions.database_sec(Section.SHS,Member.CHORD,section_db.hs_data,hs_chosen,False)

#This creates a geometry section
Geom = Geometry.Geometry(Dim, Dim2, -0.1, 2.0, 6.0, 3.0, Run.SINGLE)

#This Generates stress concentration factors
SCF = SCFs.SCFs(Geom, Run.SINGLE)
print(SCF.SCF_chax)
SCF.SCF_o_plot()