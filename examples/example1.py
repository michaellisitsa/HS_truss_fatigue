
"""This file shows how you can manually perform calculations without using the Streamlit app"""

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

import Dimensions
import Geometry
import Stresses
import forces
import st_funcs
import streamlit as st
from Enum_vals import Section, Member, Code, Run
import plotting_funcs

"""Create a Dimensions object based on the type of section and its dimensions.
The object contains calculated section properties from the section-properties module in SI units"""
Dim = Dimensions.custom_sec(Section.RHS,Member.CHORD, d=0.4, b=0.3, t=0.02)
print(vars(Dim))

"""This loads data from the relevant database stored in /data into a dataframe"""
hs_data = Dimensions.load_data(Section.CHS,Member.CHORD,Code.EN)
print(type(hs_data))

"""This picks a row from the hs_data dataframe and then creates a Dimension section from the chosen option"""
hs_chosen = hs_data[hs_data['Dimensions'] == "1219x12"]
Dim2 = Dimensions.database_sec(Section.CHS,Member.CHORD,hs_data,hs_chosen,False)
print(vars(Dim2))