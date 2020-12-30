from handcalcs import handcalc
import streamlit as st
import pandas as pd
from Enum_vals import Section, Member, Code

#Section Properties module for custom calculations
import sectionproperties.pre.sections as sections
from sectionproperties.analysis.cross_section import CrossSection

class Dimensions:
    def __init__(self, section_type: Section, member_type: Member, code: Code):
        self.section_type = section_type
        self.member_type = member_type
        self.code = code

    #@st.cache
    def load_data(self):
        if self.code is Code.AS:
            if self.section_type is Section.SHS:   self.hs_data = pd.read_csv(r"data/SHS.csv",header=0)
            elif self.section_type is Section.RHS: self.hs_data = pd.read_csv(r"data/RHS.csv",header=0)
            elif self.section_type is Section.CHS: self.hs_data = pd.read_csv(r"data/CHS.csv",header=0)
        elif self.code is Code.EN:
            if self.section_type is Section.SHS:   self.hs_data = pd.read_csv(r"data/SHS.csv",header=0)
            elif self.section_type is Section.RHS: self.hs_data = pd.read_csv(r"data/RHS.csv",header=0)
            elif self.section_type is Section.CHS: self.hs_data = pd.read_csv(r"data/CHS_en.csv",header=0)

    def st_lookup(self,def_option = 0, def_reverse_axes = False):
        """
        Streamlit function to create a select box of hollow section types loaded in
        and extract the dimensions, including potentially reversing RHS width and height
        Default parameters are only used for testing
        """
        options = st.sidebar.selectbox("",self.hs_data,key=self.member_type.name,index=def_option)
        self.hs_chosen = self.hs_data[self.hs_data['Dimensions'] == options]
        self.reverse_axes = (st.sidebar.checkbox("Rotate 90 degrees W > H",key=self.member_type.name,value=def_reverse_axes) if self.section_type is Section.RHS else False)

    def populate(self):
        """
        Function to extract the section properties out of a pandas single-row DataFrame 'hs_chosen'
        This function is separated from Streamlit input, to allow for testing.
        """
        #Initialise all variables and convert from passed in units to metres
        #Decisions are made to switch width and height based on whether:
        # - axes are reversed (RHS only)
        # - No Iy / b values exist (CHS only)
        self.b = (self.hs_chosen['d'] / 1000 if self.section_type is Section.CHS or self.reverse_axes else self.hs_chosen['b'] / 1000)
        self.d = (self.hs_chosen['b'] / 1000 if self.reverse_axes else self.hs_chosen['d'] / 1000)
        self.Iy = (self.hs_chosen['Ix'] * 10**6/1000**4 if self.section_type is not Section.RHS or self.reverse_axes else self.hs_chosen['Iy'] * 10**6/1000**4)
        self.Ix = (self.hs_chosen['Iy']* 10**6/1000**4 if self.reverse_axes else self.hs_chosen['Ix'] * 10**6/1000**4)
        self.t = self.hs_chosen['t'] / 1000
        self.area = self.hs_chosen['Area'] / 1000**2

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

    def st_custom_sec_picker(self, def_d = 400., def_b = 400., def_t = 16.):
        self.d = st.sidebar.number_input("Height/Diameter (mm)",
                                            min_value=20.,max_value=1000.,
                                            value=def_d,step=10.,key=self.member_type.name
                                            ) / 1000
        self.b = (self.d if self.section_type is Section.CHS else st.sidebar.number_input(
                                                            "Width (mm)",
                                                            min_value=20.,max_value=1000.,
                                                            value=def_b,step=10.,key=self.member_type.name
                                                            ) / 1000)
        self.t = st.sidebar.number_input("Thick (mm)",
                                            min_value=4.,max_value=30.,
                                            value=def_t,step=1.,key=self.member_type.name
                                            ) / 1000

    def calculate_custom_sec(self):
        """
        Generate a section in sectionproperties
        returns: A tuple of area, ixx, iyy, ixy, j, phi
        """
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
