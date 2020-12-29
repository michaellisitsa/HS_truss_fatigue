import streamlit as st
from streamlit_drawable_canvas import st_canvas

import pandas as pd
import forallpeople as u
u.environment('structural')
from PIL import Image

import sectionproperties.pre.sections as sections
from sectionproperties.analysis.cross_section import CrossSection

@st.cache
def load_data(code,chord_type):
    if code == "AS":
        if chord_type=="SHS":   return pd.read_csv(r"data/SHS.csv",header=0)
        elif chord_type=="RHS": return pd.read_csv(r"data/RHS.csv",header=0)
        elif chord_type=="CHS": return pd.read_csv(r"data/CHS.csv",header=0)
    elif code == "EN":
        if chord_type=="SHS":   return pd.read_csv(r"data/SHS.csv",header=0)
        elif chord_type=="RHS": return pd.read_csv(r"data/RHS.csv",header=0)
        elif chord_type=="CHS": return pd.read_csv(r"data/CHS_en.csv",header=0)

def hs_lookup(hs_type,member_type,chord_table):
    """Select a section size"""
    options = st.sidebar.selectbox("",chord_table,key=member_type)
    hs_chosen = chord_table[chord_table['Dimensions'] == options]
    reverse_axes = (st.sidebar.checkbox("Rotate 90 degrees W > H",key=member_type) if hs_type == "RHS" else False)
    return reverse_axes, hs_chosen

#@st.cache
def hs_populate(reverse_axes: bool, hs_chosen,srun):
    if reverse_axes:
        b = hs_chosen['d'] / 1000
        h = hs_chosen['b'] / 1000
        I_x =  hs_chosen['Iy'] * 10**6 / 1000**4
        I_y =  hs_chosen['Ix'] * 10**6 / 1000**4
    else:
        try:
            b = hs_chosen['b'] / 1000
        except:
            b = hs_chosen['d'] / 1000
        h = hs_chosen['d'] / 1000
        I_x =  hs_chosen['Ix'] * 10**6 / 1000**4
        try:
            I_y =  hs_chosen['Iy'] * 10**6 / 1000**4
        except:
            I_y = I_x #In RHS.csv I_y column does not exist, so needs to use I_x for SHS's
    t = hs_chosen['t'] / 1000
    area = hs_chosen['Area'] / 1000**2
    if srun:
        return b.iloc[0],h.iloc[0],t.iloc[0],area.iloc[0],I_x.iloc[0],I_y.iloc[0]
    else:
        return b,h,t,area,I_x,I_y

def overlap_sketch():
    col1, col2 = st.beta_columns(2)
    button_open = col1.button('Click to open sketch of overlap')
    button_close = col2.button('Click to close sketch of overlap')
    if button_open:
        st.image(r"data/overlap_calculation.png",use_column_width=True)
        st.image(r"data/gap_calculation.jpg",use_column_width=True)
    if button_close:
        pass

def geometry_sketch():
    col1, col2 = st.beta_columns(2)
    button_open = col1.button('Click to open sketch of truss properties')
    button_close = col2.button('Click to close truss properties')
    if button_open:
        st.image(r"data/geometric_parameters.png",use_column_width=True)
    if button_close:
        pass

def input_description(label):
    """Create Menu for user input includes
    'Write' - Custom text message
    'Draw' - Sketch field by Streamlit Component
    'Upload Image' - Insert a png, jpg, or jpeg image that is displayed
    """
    input_methods = ["Write","Draw","Upload image"]
    input_options = []
    #Load Images for input_description function
    
    @st.cache
    def load_image(image_file):
        """Display images using Pillow that 
        have been added via the streamlit file_uploader
        using the input_description function"""
        img = Image.open(image_file)
        return img
        
    with st.beta_expander(label):
        input_methods_cols = st.beta_columns(3)
        for ind,inputs in enumerate(input_methods):
            input_options.append(input_methods_cols[ind].checkbox(inputs))
        if input_options[0]:
            st.text_area("Write a description:",key="write_area")
        if input_options[1]:
            #Provide drawing canvas
            draw_cols = st.beta_columns(2)
            stroke_width = draw_cols[0].number_input("Stroke width: ", 1, 6, 3)
            stroke_color = draw_cols[1].color_picker("Stroke color: ")
            canvas_result = st_canvas(
                fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
                stroke_width=stroke_width,
                stroke_color=stroke_color,
                update_streamlit=False,
                height=300,
                drawing_mode="freedraw",
                key="canvas")
        if input_options[2]:
            st.subheader("Custom image:")
            image_file = st.file_uploader("Upload Images",
                type=["png","jpg","jpeg"])
            if image_file is not None:
                st.image(load_image(image_file),use_column_width=True)

#Class to define SHS Object and allow operations such as analyse geometry
class hs:
    def __init__(self,d,t):
        self.d = d
        self.t = t

    def rhs(self,b):
        geometry = sections.Rhs(d=self.d, b=b, t=self.t, r_out=self.t*2.0, n_r=3)
        mesh = geometry.create_mesh(mesh_sizes=[self.t**2])
        self.section = CrossSection(geometry, mesh)
        return self.section.calculate_frame_properties()

    def chs(self):
        geometry = sections.Chs(d=self.d,t=self.t,n=70)
        mesh = geometry.create_mesh(mesh_sizes=[self.t**2])
        self.section = CrossSection(geometry, mesh)
        return self.section.calculate_frame_properties()

    def visualise(self):
        fig, ax = self.section.plot_centroids()
        return fig, ax

    

