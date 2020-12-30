import streamlit as st
from handcalcs import handcalc

#Import other files
import Dimensions
import Parameters
from Enum_vals import Section, Member, Code

def main():
    #Global settings
    code = Code[st.sidebar.radio("Which code:",[type.name for type in Code])]
    chord_type = Section[st.sidebar.radio("Choose Type of Chord:",[type.name for type in Section],index=0)]

    #Instantiate Dimension Instance for Chord
    Dim = Dimensions.Dimensions(chord_type,Member.CHORD,code)
    if st.sidebar.checkbox("Custom Section:",key="custom_sec_chord"):
        Dim.st_custom_sec_picker()
        Dim.calculate_custom_sec()
        fig, ax = Dim.visualise()
        st.pyplot(fig)
        st.write(vars(Dim))
        # chord_func = secprops.custom_hs(self.d0,self.t0)
        # (area, ixx, iyy, ixy, j, phi) = (chord_func.chs() if section_type == "CHS" else chord_func.rhs(b0))
    else:
        Dim.load_data()
        Dim.st_lookup()
        Dim.populate()
        st.write(vars(Dim))

if __name__ == '__main__':
    main()