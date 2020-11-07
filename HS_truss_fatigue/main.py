import streamlit as st
import functions as fnc
import validation as vld
import pandas as pd

#Create Title Markdown
st.title("CIDECT-8 Fatigue - K-joint Trusses")
st.markdown("The purpose of this worksheet is to determine the allowable stresses at the K-Joints of the trusses.\n\
    The CIDECT 8 design guide is adopted. It can be downloaded at: https://www.cidect.org/design-guides/")

#Create section picker in streamlit sidebar
chord_type = st.sidebar.radio("Choose Type of Chord:",("SHS","RHS"))
b0,d0,t0,A_chord,Ix_chord,Iy_chord = vld.hs_lookup(chord_type,"chord")
brace_type = st.sidebar.radio("Choose Type of Brace:",("SHS","RHS"))
b1,d1,t1,A_brace,Ix_brace,Iy_brace = vld.hs_lookup(brace_type,"brace")

#Create Truss geometry input in streamlit sidebar
st.sidebar.markdown('## Truss Geometry:')
e = st.sidebar.slider('Eccentricity',-400,400,-100,step=5,format='%f') / 1000
chordspacing = st.sidebar.slider('Chord spacing (mm)',100,4000,2000,step=50,format='%i') / 1000
L_chord = st.sidebar.slider('Length of Chord (mm)',100,30000,2000,step=100,format='%i') / 1000
div_chord = st.sidebar.slider('Chord divisions',1,20,10,step=1,format='%i')

#Calculate Dimensional parameters beta, gamma and tau, check compliant
dim_params_latex, dim_params = fnc.dim_params(b0=b0,t0=t0,b1=b1,t1=t1)
st.latex(dim_params_latex)
beta, twogamma, tau = dim_params

#Dimension parameter values
fig,ax = fnc.beta_chart(b0,t0,b1,t1)
st.pyplot(fig)

