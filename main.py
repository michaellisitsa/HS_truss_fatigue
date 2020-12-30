import streamlit as st
from handcalcs import handcalc

#Import other files
import Dimensions
import Parameters
import single_run
from Enum_vals import Section, Member, Code

def main():
    #Global settings
    code = Code[st.sidebar.radio("Which code:",[type.name for type in Code])]

    Dim_C = single_run.create_Dim(Member.CHORD,code)
    Dim_B = single_run.create_Dim(Member.BRACE,code)
    if (Dim_C.section_type is Section.CHS and Dim_B.section_type is not Section.CHS
    ) | (Dim_C.section_type is not Section.CHS and Dim_B.section_type is Section.CHS):
        st.sidebar.error("Cannot mix CHS and other types. Calculation terminated")
        st.stop()
    

if __name__ == '__main__':
    main()