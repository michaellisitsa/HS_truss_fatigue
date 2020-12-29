from handcalcs import handcalc
import streamlit as st
import pandas as pd

#Section Properties module for custom calculations
import sectionproperties.pre.sections as sections
from sectionproperties.analysis.cross_section import CrossSection

#Related py files
import secprops

class Dimensions:
    def __init__(self, section_type,member_type, code):
        self.section_type = section_type
        self.member_type = member_type
        self.code = code
    
    # def area_method(self):
    #     @handcalc(override="long")
    #     def area_func(b0,h0,t0):
    #         area = b0*h0 - (b0-2*t0)*(h0-2*t0)
    #         return area
    #     self.area_latex, self.area = area_func(self.b0, self.h0, self.t0)

    #@st.cache
    def load_data(self):
        if self.code == "AS":
            if self.section_type=="SHS":   self.hs_data = pd.read_csv(r"data/SHS.csv",header=0)
            elif self.section_type=="RHS": self.hs_data = pd.read_csv(r"data/RHS.csv",header=0)
            elif self.section_type=="CHS": self.hs_data = pd.read_csv(r"data/CHS.csv",header=0)
        elif self.code == "EN":
            if self.section_type=="SHS":   self.hs_data = pd.read_csv(r"data/SHS.csv",header=0)
            elif self.section_type=="RHS": self.hs_data = pd.read_csv(r"data/RHS.csv",header=0)
            elif self.section_type=="CHS": self.hs_data = pd.read_csv(r"data/CHS_en.csv",header=0)

    def st_lookup(self):
        """
        Streamlit function to create a select box of hollow section types loaded in
        and extract the dimensions, including potentially reversing RHS width and height
        """
        options = st.sidebar.selectbox("",self.hs_data,key=self.member_type)
        self.hs_chosen = self.hs_data[self.hs_data['Dimensions'] == options]
        self.reverse_axes = (st.sidebar.checkbox("Rotate 90 degrees W > H",key=self.member_type) if self.section_type == "RHS" else False)

    def populate(self):
        """
        Function to extract the section properties out of a pandas single-row DataFrame 'hs_chosen'
        This function is separated from Streamlit input, to allow for testing.
        """
        #Initialise all variables and convert from passed in units to metres
        #Decisions are made to switch width and height based on whether:
        # - axes are reversed (RHS only)
        # - No Iy / b values exist (CHS only)
        self.b = (self.hs_chosen['d'] / 1000 if self.section_type != "RHS" or self.reverse_axes else self.hs_chosen['d'] / 1000)
        self.d = (self.hs_chosen['b'] / 1000 if self.reverse_axes else self.hs_chosen['d'] / 1000)
        self.Iy = (self.hs_chosen['Ix'] * 10**6/1000**4 if self.section_type != "RHS" or self.reverse_axes else self.hs_chosen['Iy'] * 10**6/1000**4)
        self.Ix = (self.hs_chosen['Iy']* 10**6/1000**4 if self.reverse_axes else self.hs_chosen['Ix'] * 10**6/1000**4)
        self.t = self.hs_chosen['t'] / 1000
        self.area = self.hs_chosen['Area'] / 1000**2

    def custom_section(self):
        self.d = st.sidebar.number_input("Height/Diameter (mm)",
                                            min_value=20.,max_value=1000.,
                                            value=200.,step=10.,key=self.section_type
                                            ) / 1000
        self.b = (self.d if self.section_type == "CHS" else st.sidebar.number_input(
                                                            "Width (mm)",
                                                            min_value=20.,max_value=1000.,
                                                            value=200.,step=10.,key=self.section_type
                                                            ) / 1000)
        self.t = st.sidebar.number_input("Thick (mm)",
                                            min_value=4.,max_value=30.,
                                            value=10.,step=1.,key=self.section_type
                                            ) / 1000

    def frame_props(self):
        """
        Generate a section in sectionproperties
        returns: A tuple of area, ixx, iyy, ixy, j, phi
        """
        if self.section_type == "CHS":
            geometry = sections.Chs(d=self.d,t=self.t,n=70)
        else:
            geometry = sections.Rhs(d=self.d, b=self.b, t=self.t, r_out=self.t*2.0, n_r=3)
        mesh = geometry.create_mesh(mesh_sizes=[self.t**2])
        self.section = CrossSection(geometry, mesh)
        self.area, self.ixx, self.iyy, ixy, j, phi = self.section.calculate_frame_properties()

    def visualise(self):
        """
        Visualises the geometry via a matplotlib object.
        returns: fig, ax
        """
        fig, ax = self.section.plot_centroids()
        return fig, ax
