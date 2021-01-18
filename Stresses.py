from Forces import Forces
from Dimensions import Dimensions, custom_sec, database_sec
from Geometry import Geometry
from SCFs import SCFs
import helper_funcs
from Enum_vals import Section, Member, Code, Run

from typing import Union
import forallpeople as u
u.environment('structural')

from math import sin, cos

class Stress:
    def __init__(self, run: Run,
                       forces: Forces, 
                       Dim_C: Union[database_sec,custom_sec], 
                       Dim_B: Union[database_sec,custom_sec],
                       SCF: SCFs,
                       Geom: Geometry,
                       MF_chord,
                       MF_brace):
        args = {'MF_chord':MF_chord,
                'MF_brace':MF_brace,
                'A_chord':Dim_C.area * u.m**2, #type: ignore
                'A_brace':Dim_B.area* u.m**2, #type: ignore
                'y_chord':Dim_C.d * u.m / 2, #type:ignore
                'Ix_chord':Dim_C.Ix * u.m**4, #type:ignore
                'P_brace':forces.P_brace * u.N, #type: ignore
                'P_chord':forces.P_chord * u.N, #type: ignore
                'Mip_chord':forces.M_ip_chord * u.N * u.m, #type: ignore
                'theta':Geom.theta,
                'SCF_chax':SCF.SCF_chax,
                'SCF_bax':SCF.SCF_bax,
                'SCF_chch':SCF.SCF_chch
                }
        def stress_func(MF_chord, MF_brace, A_chord, A_brace, y_chord, Ix_chord, P_brace, P_chord, Mip_chord, theta, SCF_chax, SCF_bax, SCF_chch):
            """
            Calculate the stresses in the members in order:
            - nominal stresses for each load condition (forces x magnification factors)
            - Adjusted stresses with SCFs
            """
            sigma_braceax = MF_brace * P_brace / A_brace
            F_chordLC2 = P_chord - P_brace * cos(theta)
            sigma_chordax = MF_chord * F_chordLC2 / A_chord + Mip_chord * y_chord / Ix_chord
            S_rhschord = SCF_chax * sigma_braceax + SCF_chch * sigma_chordax
            S_rhsbrace = SCF_bax * sigma_braceax
            return S_rhschord, S_rhsbrace

        self.stresses_latex, (self.S_rhschord,
                                self.S_rhsbrace
                                ) = helper_funcs.func_by_run_type(run, args, stress_func)


def MF_func(section_type: Section,gap: bool,member: Member):
    if member is Member.CHORD:
        #Chords for all member types have same MF
        return 1.5
    elif section_type is Section.CHS:
        #Overlap CHS joints not allowed, so excluded from conditional
        return 1.3
    elif gap:
        return 1.5
    elif not gap:
        return 1.3
    else:
        return "error"