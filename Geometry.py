import streamlit as st

from handcalcs import handcalc

import forallpeople as u
u.environment('structural')

from math import sin, cos, tan, atan, pi, asin
import numpy as np
import pandas as pd

import helper_funcs
from Enum_vals import Section, Member, Code, Run
from forces import Forces

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Dimensions import Dimensions

class Geometry:
    def __init__(self,Dim_C: 'Dimensions',Dim_B: 'Dimensions', e, chordspacing, L_chord, div_chord, run: Run = Run.SINGLE):
        self.Dim_C = Dim_C
        self.Dim_B = Dim_B
        self.run = run
        self.e = e
        self.chordspacing = chordspacing
        self.L_chord = L_chord
        self.div_chord = div_chord

        args = {'b_0':self.Dim_C.b * u.m,
                'h_0':self.Dim_C.d * u.m,
                't_0':self.Dim_C.t * u.m,
                'b_1':self.Dim_B.b * u.m,
                'h_1':self.Dim_B.d * u.m,
                't_1':self.Dim_B.t * u.m,
                'L_chord':self.L_chord * u.m,
                'chordspacing':self.chordspacing * u.m,
                'div_chord':self.div_chord,
                'e':self.e * u.m}
        
        def check_geom_func(b_0,h_0,t_0,b_1,h_1,t_1,L_chord,chordspacing,div_chord,e):
            """Calculate the dimensional variables beta, 
            2*gamma and tau
            Calculate the overlap percentage 
            'Ov' to be used in the calculation"""
            beta = b_1 / b_0 #Ratio of brace to chord width, where 0.35 <= beta <= 1.0
            twogamma = b_0 / t_0 #Ratio of chord width to 2*thickness, where 10 <= 2*gamma <= 35
            tau = t_1 / t_0 #Ratio of brace to chord thickness, where 0.25 < tau <= 1.0
            h_truss = chordspacing + 2 * e #Height of truss adjusted by eccentricity.
            l_truss = L_chord / div_chord #Length of truss (projection of brace onto the chord)
            theta = atan(h_truss / l_truss) #Angle between chord and brace
            theta_deg = (theta*180/pi)
            p = h_1 / sin(theta) #Projected width of brace
            x = (0.5*h_0 + e) / tan(theta) #Projection of Intersection
            q = p - 2 * x #Overlap Projection
            g_prime = -1 * q/t_0 #Ratio of gap to chord thickness
            O_v = q / p #Overlap
            return beta, twogamma, tau, O_v, theta, g_prime

        self.check_geom_latex, (self.beta,
                                self.twogamma,
                                self.tau,
                                self.O_v,
                                self.theta,
                                self.g_prime) = helper_funcs.func_by_run_type(self.run, args, check_geom_func)

        #Check for acceptable angles
        if 30*pi/180 < self.theta < 60 * pi/180:
            success = True
            message = "Angle OK"
        else:
            success = False
            message = "Angle NOT OK. Maintain 30 to 60deg"
        
        #Check of acceptable eccentricity
        if -0.55 <= self.e/self.Dim_C.d <= 0.25:
            message += " | Eccentricity OK"
        else:
            success = False
            message += " | Eccentricity NOT OK. Maintain {0:.0f}mm<=e/self.Dim_C.d<={1:.0f}mm".format(-self.Dim_C.d*0.55*1000,self.Dim_C.d*0.25*1000)

        #Check for acceptable overlap/gap for RHS, and for no overlap for CHS
        if 0 <= self.g_prime < 2 * self.tau and self.Dim_C.section_type is not Section.CHS:
            gap = True
            success = False
            message += " | Gap NOT OK. Increase so g'>= 2 * tau"
        elif self.O_v <= 0:
            gap = True
        elif (self.O_v < 0.5 or self.O_v > 1.0) and self.Dim_C.section_type is not Section.CHS:
            gap = False
            success = False
            message += " | Overlap NOT OK. Change to 50% to 100%"
        elif 0.0 < self.O_v <= 1.0 and self.Dim_C.section_type is not Section.CHS:
            gap = False
            message += " | Overlap OK"
        else:
            gap = False
            success = False
            message += " | Overlap NOT OK for CHS. Make gap joint"

        self.success, self.message, self.gap = success, message, gap

    def st_message_geom(self,container):
        #Output or stop script for angle, eccentricity, gap checks
        if self.success:
            container.success(self.message)
        else:
            container.error(self.message)
            st.stop()
