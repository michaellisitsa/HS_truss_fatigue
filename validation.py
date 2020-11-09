import streamlit as st
import pandas as pd

def pass_fail(value,lessthan=None,greaterthan=None):
    passing = True
    if lessthan is not None:
        st.write('Check for ', value,' <= ',lessthan)
        if value > lessthan:
            passing = False
        if value >= 0 and lessthan >= 0:
            st.write('Util = ',value/lessthan)
    if greaterthan is not None:
        st.write('Check for ', value,' <= ',greaterthan)
        if value < greaterthan:
            passing = False
        if value >= 0 and greaterthan >= 0:
            st.write('Util = ',greaterthan/value)
    if passing:
        st.write("**PASS**")
    else:
        st.write("**FAIL**")

def hs_lookup(hs_type,member_type):
    shs = pd.read_csv(r"data/SHS.csv",header=0)
    rhs = pd.read_csv(r"data/RHS.csv",header=0)
    if hs_type == "SHS":
        options = st.sidebar.selectbox("",shs,key=member_type)
        hs_chosen = shs[shs['Dimensions'] == options]
    elif hs_type == "RHS":
        options = st.sidebar.selectbox("",rhs,key=member_type)
        hs_chosen = rhs[rhs['Dimensions'] == options]
    b = hs_chosen.iloc[0]['b'] / 1000
    h = hs_chosen.iloc[0]['d'] / 1000
    t = hs_chosen.iloc[0]['t'] / 1000
    area = hs_chosen.iloc[0]['Area'] / 1000**2
    I_x =  hs_chosen.iloc[0]['Ix'] / 1000**4
    try:
        I_y =  hs_chosen.iloc[0]['Iy']
    except:
        I_y = I_x
    return b,h,t,area,I_x,I_y
