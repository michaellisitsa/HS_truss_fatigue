import streamlit as st
from Enum_vals import Section, Member, Code, Run

class Forces:
    """
    Constructs an object containing forces necessary for the calculations
    """
    def __init__(self, P_chord=0., P_brace=0., M_op_chord=0., M_ip_chord=0., M_op_brace=0.):
        self.P_chord = P_chord
        self.P_brace = P_brace
        self.M_op_chord = M_op_chord
        self.M_ip_chord = M_ip_chord
        self.M_op_brace = M_op_brace
    
    def st_forces_picker(self):
        """Create Force Inputs via a Streamlit input function"""
        self.P_chord = st.sidebar.number_input("P_chord (kN)",value=70.0,step=10.0) * 1000 #N
        self.P_brace = st.sidebar.number_input("P_brace (kN)",value=50.0,step=10.0) * 1000 #N
        self.M_op_chord = st.sidebar.number_input("M_op_chord (kNm)",value=5.0,step=10.0) * 1000 #Nm
        self.M_ip_chord = st.sidebar.number_input("M_ip_chord (kNm)",value=5.0,step=10.0) * 1000 #Nm
        self.M_op_brace = st.sidebar.number_input("M_op_brace (kNm)",value=5.0,step=10.0) * 1000 #Nm