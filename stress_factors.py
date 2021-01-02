import streamlit as st

from handcalcs import handcalc
from Enum_vals import Section, Member, Code, Run

import forallpeople as u
u.environment('structural')

from math import sin, cos, tan, atan, pi

import helper_funcs

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Dimensions import Dimensions
    from Parameters import Parameters

class stress_factors:
    def __init__(self,Prm: 'Parameters',run: Run = Run.SINGLE):
        self.Prm = Prm
        self.run = run

    def SCF_overlap_rhs(self):
        args = {
            'beta':self.Prm.beta,
            'twogamma':self.Prm.twogamma,
            'tau':self.Prm.tau,
            'O_v':self.Prm.O_v,
            'theta':self.Prm.theta}

        def SCF_overlap_rhs_func(beta,twogamma,tau,O_v,theta):
            """Calculate the stress concentration 
            factor for balanced condition (1) axial stresses in the chord
            overlap joint"""
            chax_pt1 = 0.5+ 2.38 * beta - 2.87 * beta**2 + 2.18 * beta * O_v + 0.39 * O_v - 1.43 * sin(theta)
            chax_pt2 = twogamma**0.29 * tau**0.7 * O_v**(0.73-5.53*sin(theta)**2) * sin(theta)**(-0.4-0.08*O_v)
            bax_pt1 = 0.15 + 1.1 * beta - 0.48 * beta**2 - 0.14 / O_v
            bax_pt2 = twogamma**0.55 * tau**(-0.3) * O_v**(-2.57 + 1.62 * beta**2) * sin(theta)**0.31
            SCF_chax = max(chax_pt1 * chax_pt2,2.0) #Balanced Loading condition Chord Forces
            SCF_bax = max(bax_pt1 * bax_pt2,2.0) #Balanced Loading condition Brace Forces
            SCF_chch = max(1.2 + 1.46 * beta - 0.028 * beta**2,2.0) #Unbalanced loading condition Chord Forces
            
            return SCF_chax, SCF_bax, SCF_chch

        self.overlap_rhs_latex, (self.SCF_chax,
                                self.SCF_bax,
                                self.SCF_chch) = helper_funcs.func_by_run_type(self.run,args,SCF_overlap_rhs_func)