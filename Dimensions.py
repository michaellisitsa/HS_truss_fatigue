from handcalcs import handcalc
import streamlit as st
import pandas as pd
from Enum_vals import Section, Member, Code

#Section Properties module for custom calculations
import sectionproperties.pre.sections as sections
from sectionproperties.analysis.cross_section import CrossSection

class Dimensions:
    def __init__(self, section_type: Section, member_type: Member):
        self.section_type = section_type
        self.member_type = member_type
    
    def st_summarise_top(self, container):
        """Function to summarise all dimensions in container"""
        #TODO - create function
        st.write(f"The Section Type defined is {self.section_type}\n"
                 f"The member_type is {self.member_type}")

class custom_sec(Dimensions):
    def __init__(self,section_type: Section, member_type: Member,d,b,t):
        """Inits the Database section class
        Generate a section in sectionproperties
        returns: A tuple of area, ixx, iyy, ixy, j, phi"""
        self.d = d
        self.b = b
        self.t = t
        super().__init__(section_type, member_type)
        
        if self.section_type is Section.CHS:
            geometry = sections.Chs(d=self.d,t=self.t,n=70)
        else:
            geometry = sections.Rhs(d=self.d, b=self.b, t=self.t, r_out=self.t*2.0, n_r=3)
        mesh = geometry.create_mesh(mesh_sizes=[self.t**2])
        self.section = CrossSection(geometry, mesh)
        self.area, self.Ix, self.Iy, Ixy, j, phi = self.section.calculate_frame_properties()

    def visualise(self):
        """
        Visualises the geometry via a matplotlib object.
        returns: fig, ax
        """
        fig, ax = self.section.plot_centroids()
        return fig, ax

class database_sec(Dimensions):
    def __init__(self,section_type: Section, member_type: Member, hs_data, hs_chosen, reverse_axes: bool):
        """Inits the Database section class
        Function to extract the section properties out of a pandas single-row DataFrame 'hs_chosen'
        This function is separated from Streamlit input, to allow for testing."""
        super().__init__(section_type,member_type)

        #Initialise all variables and convert from passed in units to metres
        #Decisions are made to switch width and height based on whether:
        # - axes are reversed (RHS only)
        # - No Iy / b values exist (CHS only)
        self.b = (hs_chosen['d'] / 1000 if self.section_type is Section.CHS or reverse_axes else hs_chosen['b'] / 1000)
        self.d = (hs_chosen['b'] / 1000 if reverse_axes else hs_chosen['d'] / 1000)
        self.Iy = (hs_chosen['Ix'] * 10**6/1000**4 if section_type is not Section.RHS or reverse_axes else hs_chosen['Iy'] * 10**6/1000**4)
        self.Ix = (hs_chosen['Iy']* 10**6/1000**4 if reverse_axes else hs_chosen['Ix'] * 10**6/1000**4)
        self.t = hs_chosen['t'] / 1000
        self.area = hs_chosen['Area'] / 1000**2

        try:
            self.b = self.b.iloc[0]
            self.d = self.d.iloc[0]
            self.Iy = self.Iy.iloc[0]
            self.Ix = self.Ix.iloc[0]
            self.t = self.t.iloc[0]
            self.area = self.area.iloc[0]
        except:
            #need to rethink this whether needed for the all_options case
            pass

def st_custom_sec_picker(section_type: Section, member_type: Member, def_d = 400., def_b = 400., def_t = 16.):
    d = st.sidebar.number_input("Height/Diameter (mm)",
                                        min_value=20.,max_value=1000.,
                                        value=def_d,step=10.,key=member_type.name
                                        ) / 1000
    b = (d if section_type is Section.CHS else st.sidebar.number_input(
                                                        "Width (mm)",
                                                        min_value=20.,max_value=1000.,
                                                        value=def_b,step=10.,key=member_type.name
                                                        ) / 1000)
    t = st.sidebar.number_input("Thick (mm)",
                                        min_value=4.,max_value=30.,
                                        value=def_t,step=1.,key=member_type.name
                                        ) / 1000
    return d, b, t

#@st.cache
def load_data(section_type: Section, member_type: Member, code: Code):
    """
    Function to load csv data, run before defining a geometry
    """
    if code is Code.AS:
        if section_type is Section.SHS:   return pd.read_csv(r"data/SHS.csv",header=0)
        elif section_type is Section.RHS: return pd.read_csv(r"data/RHS.csv",header=0)
        elif section_type is Section.CHS: return pd.read_csv(r"data/CHS.csv",header=0)
    elif code is Code.EN:
        if section_type is Section.SHS:   return pd.read_csv(r"data/SHS.csv",header=0)
        elif section_type is Section.RHS: return pd.read_csv(r"data/RHS.csv",header=0)
        elif section_type is Section.CHS: return pd.read_csv(r"data/CHS_en.csv",header=0)

def st_lookup(hs_data, section_type: Section, member_type: Member, def_option = 0, def_reverse_axes = False):
    """
    Streamlit function to create a select box of hollow section types loaded in
    and extract the dimensions, including potentially reversing RHS width and height
    Default parameters are only used for testing
    """
    options = st.sidebar.selectbox("", hs_data,key=member_type.name,index=def_option)
    hs_chosen = hs_data[hs_data['Dimensions'] == options]
    reverse_axes = (st.sidebar.checkbox("Rotate 90 degrees W > H",key=member_type.name,value=def_reverse_axes) if section_type is Section.RHS else False)
    return hs_chosen, reverse_axes