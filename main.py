import streamlit as st
from handcalcs import handcalc

#Import other files
import Dimensions
import Geometry
import Stresses
import single_run
from Enum_vals import Section, Member, Code, Run

def main():
    #Global settings
    code = Code[st.sidebar.radio("Which code:",[type.name for type in Code])]
    run = Run[st.sidebar.radio("Run Type:",[type.name for type in Run],index=0)]

    #Instantiate dimension Geometry
    Dim_C = single_run.create_Dim(Member.CHORD,code)
    Dim_B = single_run.create_Dim(Member.BRACE,code)
    #Error where CHS is mixed with other section types.
    if (Dim_C.section_type is Section.CHS and Dim_B.section_type is not Section.CHS
    ) | (Dim_C.section_type is not Section.CHS and Dim_B.section_type is Section.CHS):
        st.sidebar.error("Cannot mix CHS and other types. Calculation terminated")
        st.stop()

    Geom = single_run.create_Geom(Dim_C,Dim_B)

    Stress = single_run.create_Stress(Geom)

if __name__ == '__main__':
    main()