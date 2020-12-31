import streamlit as st

from handcalcs import handcalc
from Enum_vals import Section, Member, Code, Run

from math import sin, cos, tan, atan, pi

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Dimensions import Dimensions

class Parameters:
    def __init__(self,Dim_C: 'Dimensions',Dim_B: 'Dimensions',run: Run = Run.SINGLE):
        self.Dim_C = Dim_C
        self.Dim_B = Dim_B
        self.run = run

    def geom_picker(self):
        self.e = (0 if self.Dim_C.section_type is Section.CHS else st.sidebar.number_input('Eccentricity',-400,400,-100,step=5,format='%f') / 1000)
        self.chordspacing = st.sidebar.number_input('Chord spacing (mm)',100,4000,2000,step=50,format='%i') / 1000
        self.L_chord = st.sidebar.number_input('Length of Chord (mm)',100,30000,8000,step=100,format='%i') / 1000
        self.div_chord = st.sidebar.number_input('Chord divisions',1,20,4,step=1,format='%i')

    def overlap(self):
        #L_chord,chordspacing,div_chord,eccentricity,h0,h1,t0
        def overlap_func(L_chord,chordspacing,div_chord,e,h_0,h_1,t_0):
            """Calculate the overlap percentage 
            'Ov' to be used in the calculation"""
            h_truss = chordspacing + 2 * e #Height of truss adjusted by eccentricity.
            l_truss = L_chord / div_chord #Length of truss (projection of brace onto the chord)
            theta = atan(h_truss / l_truss) #Angle between chord and brace
            theta_deg = (theta*180/pi)
            p = h_1 / sin(theta) #Projected width of brace
            x = (0.5*h_0 + e) / tan(theta) #Projection of Intersection
            q = p - 2 * x #Overlap Projection
            g_prime = -1 * q/t_0 #Ratio of gap to chord thickness
            Ov = q / p #Overlap
            return Ov, theta, g_prime
        overlap_func_hc = handcalc(override="long")(overlap_func)
        
        #Used to call overlap_func, passed as kwargs to avoid human error (e.g. order of inputs)
        arg = {'L_chord':self.L_chord,
                'chordspacing':self.chordspacing,
                'div_chord':self.div_chord,
                'e':self.e,
                'h_0':self.Dim_C.d,
                'h_1':self.Dim_B.d,
                't_0':self.Dim_C.t}
        
        if self.run is Run.SINGLE:
            self.overlap_latex, vals = overlap_func_hc(**arg)
        elif self.run is Run.ALL_SECTIONS:
            Ov,theta,g_prime = overlap_func(**arg)
        self.Ov, self.theta, self.g_prime = vals

    def dim_params(self):
        def dim_params_func(b0,t0,b1,t1):
            """Calculate the dimensional variables beta, 
            2*gamma and tau
            Function is nested to avoid instance attributes which can't be read by handcalcs"""
            beta = b1 / b0 #Ratio of brace to chord width, where 0.35 <= beta <= 1.0
            twogamma = b0 / t0 #Ratio of chord width to 2*thickness, where 10 <= 2*gamma <= 35
            tau = t1 / t0 #Ratio of brace to chord thickness, where 0.25 < tau <= 1.0
            return beta, twogamma, tau
        dim_params_func_hc = handcalc(override="long")(dim_params_func)

        args = [self.Dim_C.b,
                self.Dim_C.t,
                self.Dim_B.b,
                self.Dim_B.t]

        #If a single run, use handcalcs module. If a multiple run, do not use handcalcs
        if self.run is Run.SINGLE:
            self.dim_params_latex, vals = dim_params_func_hc(*args)
        elif self.run is Run.ALL_SECTIONS:
            vals = dim_params_func(*args)
            
        self.beta, self.twogamma, self.tau = vals