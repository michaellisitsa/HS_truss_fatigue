from handcalcs import handcalc
from math import sqrt, cos, sin, pi, atan, tan
import streamlit as st
import forallpeople as u
u.environment('structural')
from scipy.interpolate import interp2d
import numpy as np

def dim_params(b0,t0,b1,t1,chord_type):
    """Calculate the dimensional variables beta, 
    2*gamma and tau"""
    beta = b1 / b0 #Ratio of brace to chord width, where 0.35 <= beta <= 1.0
    twogamma = b0 / t0 #Ratio of chord width to 2*thickness, where 10 <= 2*gamma <= 35
    tau = t1 / t0 #Ratio of brace to chord thickness, where 0.25 < tau <= 1.0
    return beta, twogamma, tau

dim_params_hc = handcalc(override="long")(dim_params)

def dim_limits(chord_type):
    tau_min = 0.25
    tau_max = 1.0
    if chord_type == "CHS":
        beta_min = 0.3
        beta_max = 0.6
        twogamma_min = 24
        twogamma_max = 60
    else:
        beta_min = 0.35
        beta_max = 1.0
        twogamma_min = 10
        twogamma_max = 35
    return tau_min,tau_max,beta_min,beta_max,twogamma_min,twogamma_max

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

overlap_hc = handcalc(override="long")(overlap)

def MF(chord_type: str,gap: bool,member: str):
    if member == 'chord':
        #Chords for all member types have same MF
        return 1.5
    elif chord_type == "CHS":
        #Overlap CHS joints not allowed, so excluded from conditional
        return 1.3
    elif gap:
        return 1.5
    elif not gap:
        return 1.3
    else:
        return "error"

def check_angle_ecc_gap(chord_type,theta,e,h0,Ov,g_prime,tau):
    """
    Checks for a suitable angle, eccentricity and gap/overlap dependent on CHS or SHS/RHS
    
    Returns:
    success: bool - Whether or not all checks pass
    message: str - Comment on each check
    gap: bool - Whether joint is gap or not, used later for MF and for SCF formulas (SHS/RHS only)
    """

    #Check for acceptable angles
    if 30*pi/180 < theta < 60 * pi/180:
        success = True
        message = "Angle OK"
    else:
        success = False
        message = "Angle NOT OK. Maintain 30 to 60deg"
    
    #Check of acceptable eccentricity
    if -0.55 <= e/h0 <= 0.25:
        message += " | Eccentricity OK"
    else:
        success = False
        message += " | Eccentricity NOT OK. Maintain {0:.0f}mm<=e/h0<={1:.0f}mm".format(-h0*0.55*1000,h0*0.25*1000)

    #Check for acceptable overlap/gap for RHS, and for no overlap for CHS
    if 0 <= g_prime < 2 * tau and chord_type != "CHS":
        gap = True
        success = False
        message += " | Gap NOT OK. Increase so g'>= 2 * tau"
    elif Ov <= 0:
        gap = True
    elif (Ov < 0.5 or Ov > 1.0) and chord_type != "CHS":
        gap = False
        success = False
        message += " | Overlap NOT OK. Change to 50% to 100%"
    elif 0.0 < Ov <= 1.0 and chord_type != "CHS":
        gap = False
        message += " | Overlap OK"
    else:
        gap = False
        success = False
        message += " | Overlap NOT OK for CHS. Make gap joint"

    return success, message, gap

def SCF_overlap_rhs(beta,twogamma,tau,Ov,theta):
    """Calculate the stress concentration 
    factor for balanced condition (1) axial stresses in the chord
    overlap joint"""
    chax_pt1 = 0.5+ 2.38 * beta - 2.87 * beta**2 + 2.18 * beta * Ov + 0.39 * Ov - 1.43 * sin(theta)
    chax_pt2 = twogamma**0.29 * tau**0.7 * Ov**(0.73-5.53*sin(theta)**2) * sin(theta)**(-0.4-0.08*Ov)
    bax_pt1 = 0.15 + 1.1 * beta - 0.48 * beta**2 - 0.14 / Ov
    bax_pt2 = twogamma**0.55 * tau**(-0.3) * Ov**(-2.57 + 1.62 * beta**2) * sin(theta)**0.31
    SCF_chax = max(chax_pt1 * chax_pt2,2.0) #Balanced Loading condition Chord Forces
    SCF_bax = max(bax_pt1 * bax_pt2,2.0) #Balanced Loading condition Brace Forces
    SCF_chch = max(1.2 + 1.46 * beta - 0.028 * beta**2,2.0) #Unbalanced loading condition Chord Forces
    return SCF_chax, SCF_bax, SCF_chch

SCF_overlap_rhs_hc = handcalc(override="long")(SCF_overlap_rhs)

def SCF_gap_rhs(beta,twogamma,tau,g_prime,theta):
    """Calculate the stress concentration 
    factor for balanced condition (1) axial stresses in the chord
    gap joint"""
    chax_pt1 = 0.48 * beta - 0.5 * beta**2 - 0.012 / beta + 0.012 / g_prime
    chax_pt2 =  twogamma**1.72 * tau**0.78 * g_prime**0.2 * sin(theta)**2.09
    bax_pt1 = -0.008 + 0.45 * beta - 0.34 * beta**2
    bax_pt2 = twogamma**1.36 * tau**(-0.66) * sin(theta)**1.29
    SCF_chax = max(chax_pt1 * chax_pt2,2.0) #Balanced Loading condition Chord Forces
    SCF_bax = max(bax_pt1 * bax_pt2,2.0) #Balanced Loading condition Brace Forces
    SCF_chch = max((2.45 + 1.23 * beta) * g_prime**-0.27,2.0) #Unbalanced loading condition Chord Forces
    return SCF_chax, SCF_bax, SCF_chch

SCF_gap_rhs_hc = handcalc(override="long")(SCF_gap_rhs)

def SCFochax_func(beta,theta):
    """
    SCFochax and SCFobax are functions of both beta and theta
    Use Scipy interp2d function to create interpolation between curves
    Then plot the image of the graphs and the plotted value.
    This gives user re-assurance that the value was correctly calculated.
    """
    beta_vals = [0.3,0.6]
    theta_vals = [30,45,60]
    SCF_ochax_vals = [[2.73,2.5],[3.18,2.83],[3.52,3.19]]
    SCF_obax_vals = [[1.45,1.15],[2.03,1.7],[2.5,2.08]]
    SCF_ochax_func = interp2d(beta_vals, theta_vals, SCF_ochax_vals, kind='linear')
    SCF_obax_func = interp2d(beta_vals,theta_vals, SCF_obax_vals, kind='linear')
    SCF_ochax = SCF_ochax_func(beta,theta*180/pi)
    SCF_obax = SCF_obax_func(beta,theta*180/pi)

    #Interpolate SCF_bax_min
    SCF_bax_min = np.interp(theta*180/pi,[30,45,60],[2.64,2.30,2.12])

    return SCF_ochax, SCF_obax, SCF_bax_min

def SCF_chaxbaxchch_chs(gamma,tau,theta,SCF_ochax,SCF_obax,SCF_bax_min):
    """
    Calculate SCF_chax and SCF_bax and render with handcalcs
    """
    SCF_chax = max(2,(gamma/12)**0.4 * (tau/0.5)**1.1 * SCF_ochax)
    SCF_bax = max(SCF_bax_min,sqrt(gamma/12) * sqrt(tau/0.5) * SCF_obax)
    SCF_chch = max(2,1.2*(tau/0.5)**0.3 * sin(theta)**-0.9)
    return SCF_chax,SCF_bax,SCF_chch
SCF_chaxbaxchch_chs_hc = handcalc(override="long")(SCF_chaxbaxchch_chs)

def chord_ax_stresses(SCF_chax,SCF_chch,P_brace,P_chord,theta,A_chord,A_brace,MF_chord,MF_brace):
    """Calculate the axial stresses in the 
    chords for both balanced (1) and unbalanced (2) load conditions"""
    sigma_chord1P = SCF_chax * MF_brace * P_brace / A_brace
    sigma_chord2P = SCF_chch * MF_chord * (P_chord - P_brace * cos(theta))/ A_chord
    return sigma_chord1P, sigma_chord2P
chord_ax_stresses_hc = handcalc(override="long")(chord_ax_stresses)

def chord_BM_stresses(h0,b0,b1,SCF_chch,SCF_ch_op,M_ip_chord,M_op_chord,Ix_chord,Iy_chord):
    """Calculate the distance to fibre of chord where the extreme fibers of the brace,
    and calculate associated stresses due to bending moment in the chords for the unbalanced (2) load condition"""
    y_ip_chord = h0/2 #Dist from NA to top/bottom of brace
    y_op_chord = b1/2 #Dist from NA to left/right of brace
    sigma_chordM_ip = SCF_chch * (M_ip_chord * y_ip_chord) / Ix_chord
    sigma_chordM_op = SCF_ch_op * (M_op_chord * y_op_chord) / Iy_chord
    return sigma_chordM_ip, sigma_chordM_op
chord_BM_stresses_hc = handcalc(override="long")(chord_BM_stresses)

def brace_stresses(b1, SCF_bax,P_brace,A_brace,SCF_br_op,M_op_brace,Iy_brace,MF_brace):
    """Calculate the distance to the extreme fiber of the brace,
    and calculated associated stresses due to bending moment in the brace for the unbalanced condition
    and the axial stresses due to the balanced condition"""
    sigma_brace_1P = SCF_bax * MF_brace * P_brace / A_brace
    z_op_brace = b1 / 2
    sigma_braceM_op = SCF_br_op * M_op_brace * z_op_brace / Iy_brace
    return sigma_brace_1P, sigma_braceM_op
brace_stresses_hc = handcalc(override="long")(brace_stresses)

def cum_stresses(sigma_chord1P,sigma_chord2P,sigma_chordM_ip,sigma_chordM_op,sigma_brace_1P,sigma_braceM_op):
    """Sum stresses from each load condition 
    and out of plane bending stress components"""
    sigma_chord = sum((sigma_chord1P, sigma_chord2P, sigma_chordM_ip, sigma_chordM_op))
    sigma_brace = sum((sigma_brace_1P,sigma_braceM_op))
    return sigma_chord, sigma_brace
cum_stresses_hc = handcalc(override="long")(cum_stresses)