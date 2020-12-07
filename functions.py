from math import sqrt
from handcalcs import handcalc
from math import sqrt, cos, sin, pi, atan, tan
import streamlit as st
import forallpeople as u
u.environment('structural')

@handcalc(override="long")
def dim_params(b0,t0,b1,t1,chord_type):
    """Calculate the dimensional variables beta, 
    2*gamma and tau"""
    beta = b1 / b0 #Ratio of brace to chord width, where 0.35 <= beta <= 1.0
    twogamma = b0 / t0 #Ratio of chord width to 2*thickness, where 10 <= 2*gamma <= 35
    tau = t1 / t0 #Ratio of brace to chord thickness, where 0.25 < tau <= 1.0
    return beta, twogamma, tau

@handcalc(override="long")
def overlap(L_chord,chordspacing,div_chord,eccentricity,h0,h1,t0):
    """Calculate the overlap percentage 
    'Ov' to be used in the calculation"""
    h_truss = chordspacing + 2 * eccentricity #Height of truss adjusted by eccentricity.
    l_truss = L_chord / div_chord #Length of truss (projection of brace onto the chord)
    theta = atan(h_truss / l_truss) #Angle between chord and brace
    theta_deg = (theta*180/pi)
    p = h1 / sin(theta) #Projected width of brace
    x = (0.5*h0 + eccentricity) / tan(theta) #Projection of Intersection
    q = p - 2 * x #Overlap Projection
    g_prime = -1 * q/t0 #Ratio of gap to chord thickness
    Ov = q / p #Overlap
    return Ov, theta, g_prime

@handcalc(override="long")
def SCF_chax_overlap(beta,twogamma,tau,Ov,theta):
    """Calculate the stress concentration 
    factor for balanced condition (1) axial stresses in the chord
    overlap joint"""
    pt1 = 0.5+ 2.38 * beta - 2.87 * beta**2 + 2.18 * beta * Ov + 0.39 * Ov - 1.43 * sin(theta)
    pt2 = twogamma**0.29 * tau**0.7 * Ov**(0.73-5.53*sin(theta)**2) * sin(theta)**(-0.4-0.08*Ov)
    SCF_chax = max(pt1 * pt2,2.0) #Balanced Loading condition Chord Forces
    return SCF_chax

@handcalc(override="long")
def SCF_chax_gap(beta,twogamma,tau,g_prime,theta):
    """Calculate the stress concentration 
    factor for balanced condition (1) axial stresses in the chord
    gap joint"""
    pt1 = 0.48 * beta - 0.5 * beta**2 - 0.012 / beta + 0.012 / g_prime
    pt2 =  twogamma**1.72 * tau**0.78 * g_prime**0.2 * sin(theta)**2.09
    SCF_chax = max(pt1 * pt2,2.0) #Balanced Loading condition Chord Forces
    return SCF_chax

@handcalc(override="long")
def SCF_bax_overlap(beta,twogamma,tau,Ov,theta):
    """Calculate the stress concentration 
    factor for balanced condition (1) axial stresses in the brace
    overlap joint"""
    pt1 = 0.15 + 1.1 * beta - 0.48 * beta**2 - 0.14 / Ov
    pt2 = twogamma**0.55 * tau**(-0.3) * Ov**(-2.57 + 1.62 * beta**2) * sin(theta)**0.31
    SCF_bax = max(pt1 * pt2,2.0) #Balanced Loading condition Brace Forces
    return SCF_bax

@handcalc(override="long")
def SCF_bax_gap(beta,twogamma,tau,theta):
    """Calculate the stress concentration 
    factor for balanced condition (1) axial stresses in the brace
    gap joint"""
    pt1 = -0.008 + 0.45 * beta - 0.34 * beta**2
    pt2 = twogamma**1.36 * tau**(-0.66) * sin(theta)**1.29
    SCF_bax = max(pt1 * pt2,2.0) #Balanced Loading condition Brace Forces
    return SCF_bax

@handcalc(override="long")
def SCF_chch_overlap(beta):
    """Calculate the stress concentration 
    factor for unbalanced condition (2) stresses in the chord
    overlap joint"""
    SCF_chch = max(1.2 + 1.46 * beta - 0.028 * beta**2,2.0) #Unbalanced loading condition Chord Forces
    return SCF_chch

@handcalc(override="long")
def SCF_chch_gap(beta,g_prime):
    """Calculate the stress concentration 
    factor for unbalanced condition (2) stresses in the chord
    gap joint"""
    SCF_chch = max((2.45 + 1.23 * beta) * g_prime**-0.27,2.0) #Unbalanced loading condition Chord Forces
    return SCF_chch

@handcalc(override="long")
def chord_ax_stresses(SCF_chax,SCF_chch,P_brace,P_chord,theta,A_chord,A_brace):
    """Calculate the axial stresses in the 
    chords for both balanced (1) and unbalanced (2) load conditions"""
    sigma_chord1P = SCF_chax * P_brace / A_brace
    sigma_chord2P = SCF_chch * (P_chord - P_brace * cos(theta))/ A_chord
    return sigma_chord1P, sigma_chord2P

@handcalc(override="long")
def chord_BM_stresses(h0,b0,b1,SCF_chch,SCF_ch_op,M_ip_chord,M_op_chord,Ix_chord,Iy_chord):
    """Calculate the distance to fibre of chord where the extreme fibers of the brace,
    and calculate associated stresses due to bending moment in the chords for the unbalanced (2) load condition"""
    y_ip_chord = h0/2 #Dist from NA to top/bottom of brace
    y_op_chord = b1/2 #Dist from NA to left/right of brace
    sigma_chordM_ip = SCF_chch * (M_ip_chord * y_ip_chord) / Ix_chord
    sigma_chordM_op = SCF_ch_op * (M_op_chord * y_op_chord) / Iy_chord
    return sigma_chordM_ip, sigma_chordM_op

@handcalc(override="long")
def brace_stresses(b1, SCF_bax,P_brace,A_brace,SCF_br_op,M_op_brace,Iy_brace):
    """Calculate the distance to the extreme fiber of the brace,
    and calculated associated stresses due to bending moment in the brace for the unbalanced condition
    and the axial stresses due to the balanced condition"""
    sigma_brace_1P = SCF_bax * P_brace / A_brace
    z_op_brace = b1 / 2
    sigma_braceM_op = SCF_br_op * M_op_brace * z_op_brace / Iy_brace
    return sigma_brace_1P, sigma_braceM_op

@handcalc(override="long")
def cum_stresses(sigma_chord1P,sigma_chord2P,sigma_chordM_ip,sigma_chordM_op,sigma_brace_1P,sigma_braceM_op):
    """Sum stresses from each load condition 
    and out of plane bending stress components"""
    sigma_chord = sum((sigma_chord1P, sigma_chord2P, sigma_chordM_ip, sigma_chordM_op))
    sigma_brace = sum((sigma_brace_1P,sigma_braceM_op))
    return sigma_chord, sigma_brace