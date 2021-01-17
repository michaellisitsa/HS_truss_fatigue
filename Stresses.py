import streamlit as st

from handcalcs import handcalc
from Enum_vals import Section, Member, Code, Run
import helper_funcs

import forallpeople as u
u.environment('structural')

from math import sin, cos, tan, atan, pi, sqrt
from scipy.interpolate import interp2d
import numpy as np

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Dimensions import Dimensions
    from Geometry import Geometry

class Stresses:
    def __init__(self,Geom: 'Geometry',run: Run = Run.SINGLE):
        self.Geom = Geom
        self.run = run

    def st_SCF_op_picker(self):
        self.SCF_ch_op = st.sidebar.number_input("SCF_ch_op Input",min_value=1.0,max_value=10.0,value=2.0,step=0.1)
        self.SCF_br_op = st.sidebar.number_input("SCF_br_op Input",min_value=1.0,max_value=10.0,value=2.0,step=0.1)

    def SCF(self):
        """Calculate the stress concentration factors
        Values vary depending on Section type and whether a gap exists"""
        self.SCF_ochax, self.SCF_obax, self.SCF_bax_min = None, None, None

        if self.Geom.Dim_C.section_type is Section.CHS:
            beta_vals = [0.3,0.6]
            theta_vals = [30,45,60]
            SCF_ochax_vals = [[2.73,2.5],[3.18,2.83],[3.52,3.19]]
            SCF_obax_vals = [[1.45,1.15],[2.03,1.7],[2.5,2.08]]
            SCF_ochax_func = interp2d(beta_vals, theta_vals, SCF_ochax_vals, kind='linear')
            SCF_obax_func = interp2d(beta_vals,theta_vals, SCF_obax_vals, kind='linear')
            self.SCF_ochax = SCF_ochax_func(self.Geom.beta,self.Geom.theta*180/pi)[0]
            self.SCF_obax = SCF_obax_func(self.Geom.beta,self.Geom.theta*180/pi)[0]
            self.SCF_bax_min = np.interp(self.Geom.theta*180/pi,[30,45,60],[2.64,2.30,2.12])
            
            def SCF_func(beta,twogamma,tau,O_v,g_prime,theta,SCF_ochax, SCF_obax, SCF_bax_min):
                SCF_chax = max(2,(twogamma/6)**0.4 * (tau/0.5)**1.1 * SCF_ochax)
                SCF_bax = max(SCF_bax_min,sqrt(twogamma/6) * sqrt(tau/0.5) * SCF_obax)
                SCF_chch = max(2,1.2*(tau/0.5)**0.3 * sin(theta)**-0.9)
                return SCF_chax, SCF_bax, SCF_chch
        
        elif self.Geom.gap is True:
            def SCF_func(beta,twogamma,tau,O_v,g_prime,theta,SCF_ochax, SCF_obax, SCF_bax_min):
                chax_pt1 = 0.48 * beta - 0.5 * beta**2 - 0.012 / beta + 0.012 / g_prime
                chax_pt2 = twogamma**1.72 * tau**0.78 * g_prime**0.2 * sin(theta)**2.09
                bax_pt1 = -0.008 + 0.45 * beta - 0.34 * beta**2
                bax_pt2 = twogamma**1.36 * tau**(-0.66) * sin(theta)**1.29
                SCF_chax = max(chax_pt1 * chax_pt2,2.0) #Balanced Loading condition Chord Forces
                SCF_bax = max(bax_pt1 * bax_pt2,2.0) #Balanced Loading condition Brace Forces
                SCF_chch = max((2.45 + 1.23 * beta) * g_prime**-0.27,2.0) #Unbalanced loading condition Chord Forces
                return SCF_chax, SCF_bax, SCF_chch

        elif self.Geom.gap is False:
            def SCF_func(beta,twogamma,tau,O_v,g_prime,theta,SCF_ochax, SCF_obax, SCF_bax_min):
                chax_pt1 = 0.5+ 2.38 * beta - 2.87 * beta**2 + 2.18 * beta * O_v + 0.39 * O_v - 1.43 * sin(theta)
                chax_pt2 = twogamma**0.29 * tau**0.7 * O_v**(0.73-5.53*sin(theta)**2) * sin(theta)**(-0.4-0.08*O_v)
                bax_pt1 = 0.15 + 1.1 * beta - 0.48 * beta**2 - 0.14 / O_v
                bax_pt2 = twogamma**0.55 * tau**(-0.3) * O_v**(-2.57 + 1.62 * beta**2) * sin(theta)**0.31
                SCF_chax = max(chax_pt1 * chax_pt2,2.0) #Balanced Loading condition Chord Forces
                SCF_bax = max(bax_pt1 * bax_pt2,2.0) #Balanced Loading condition Brace Forces
                SCF_chch = max(1.2 + 1.46 * beta - 0.028 * beta**2,2.0) #Unbalanced loading condition Chord Forces
                return SCF_chax, SCF_bax, SCF_chch

        args = {
            'beta':self.Geom.beta,
            'twogamma':self.Geom.twogamma,
            'tau':self.Geom.tau,
            'O_v':self.Geom.O_v,
            'g_prime':self.Geom.g_prime,
            'theta':self.Geom.theta,
            'SCF_ochax':self.SCF_ochax,
            'SCF_obax':self.SCF_obax,
            'SCF_bax_min':self.SCF_bax_min}
            
        self.SCF_latex, (self.SCF_chax,
                                self.SCF_bax,
                                self.SCF_chch) = helper_funcs.func_by_run_type(self.run,args,SCF_func)