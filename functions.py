from math import sqrt
from handcalcs import handcalc
from math import sqrt, cos, sin, pi, atan, tan
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import forallpeople as u
u.environment('structural')
from PIL import Image

@handcalc(override="long")
def dim_params(b0,t0,b1,t1):
    """Calculate the dimensional variables beta, 
    2*gamma and tau"""
    beta = b1 / b0 #Ratio of brace to chord width, where 0.35 <= beta <= 1.0
    twogamma = b0 / t0 #Ratio of chord width to 2*thickness, where 10 <= 2*gamma <= 35
    tau = t1 / t0 #Ratio of brace to chord thickness, where 0.25 < tau <= 1.0
    return beta, twogamma, tau

def dim_params_plot(b0,t0,b1,t1):
    """Plot the dimensional variables beta, 
    2*gamma and tau, showing the acceptable range in green highlighted area"""
    # Create Plot
    fig, ax = plt.subplots(ncols=3,figsize=(9,3))

    #Plot max and min lines
    ax[0].plot([0,500],[0,500], label=r'$\beta=1$', color='red') #max line
    ax[0].plot([0,500],[0.,0.35 * 500.], label=r'$\beta=0.35$', color='yellow') #min line
    ax[1].plot([0,20],[0,35 * 20],label=r'$2\cdot \gamma = 35$', color='red')
    ax[1].plot([0,20],[0,10 * 20],label=r'$2\cdot \gamma = 10$', color='yellow')
    ax[2].plot([0,20],[0,20],label=r'$\tau=1.0$', color='red')
    ax[2].plot([0,20],[0,0.25*20],label=r'$\tau=0.25$', color='yellow')

    #Plot single points for each of graph
    ax[0].plot(b0,b1,'ro',c="black")
    ax[1].plot(t0,b0,'ro',c="black")
    ax[2].plot(t0,t1,'ro',c="black")

    #Annotate single points for each graph with beta,gamma,tau values
    ax[0].annotate(text=b1/b0,xy=(b0,b1),xytext=(b0-75,b1+25),fontsize=8)
    ax[1].annotate(text=b0/t0,xy=(t0,b0),xytext=(t0-2,b0+25),fontsize=8)
    ax[2].annotate(text=t1/t0,xy=(t0,t1),xytext=(t0-2,t1+2),fontsize=8)

    #Create shaded region of acceptable values
    ax[0].fill_between([0,500],[0,500],[0,0.35 * 500], facecolor='green', alpha=0.5)
    ax[1].fill_between([0,20],[0,35 * 20],[0,10 * 20], facecolor='green', alpha=0.5)
    ax[2].fill_between([0,20],[0,20],[0,0.25*20], facecolor='green', alpha=0.5)

    #Set graph titles with allowable range
    ax[0].set_title(r'$0.35 \leq \beta(=\frac{b_1}{b_0}) \leq 1.0$',fontsize=10)
    ax[1].set_title(r'$10 \leq 2\gamma(=\frac{b_0}{t_0}) \leq 35$',fontsize=10)
    ax[2].set_title(r'$0.25 \leq \tau(=\frac{t_1}{t_0}) \leq 1.0$',fontsize=10)

    #Label axes
    ax[0].set_xlabel('b0')
    ax[0].set_ylabel('b1')
    ax[1].set_xlabel('t0')
    ax[1].set_ylabel('b0')
    ax[2].set_xlabel('t0')
    ax[2].set_ylabel('t1')

    #Turn on legends and grid for each graph
    [ax[i].legend(loc='upper left') for i in range(3)]
    [ax[i].grid() for i in range(3)]

    return fig, ax

@handcalc(override="long")
def overlap(L_chord,chordspacing,div_chord,eccentricity,h0,h1):
    """Calculate the overlap percentage 
    'Ov' to be used in the calculation"""
    h_truss = chordspacing + 2 * eccentricity #Height of truss adjusted by eccentricity.
    l_truss = L_chord / div_chord #Length of truss (projection of brace onto the chord)
    theta = atan(h_truss / l_truss) #Angle between chord and brace
    theta_deg = (theta*180/pi)
    p = h1 / sin(theta) #Projected width of brace
    x = (0.5*h0 + eccentricity) / tan(theta) #Projection of Intersection
    q = p - 2 * x #Overlap Projection
    Ov = q / p #Overlap, where 50\% <= Ov <= 100\%
    return Ov, theta

@handcalc(override="long")
def SCF_chax(beta,twogamma,tau,Ov,theta):
    """Calculate the stress concentration 
    factor for balanced condition (1) axial stresses in the chord"""
    pt1 = (0.5+ 2.38 * beta - 2.87 * beta**2 + 2.18 * beta * Ov + 0.39 * Ov - 1.43 * sin(theta))
    pt2 =  (twogamma**0.29 * tau**0.7 * Ov**(0.73-5.53*sin(theta)**2) * sin(theta)**(-0.4-0.08*Ov))
    SCF_chax = pt1 * pt2 #Balanced Loading condition Chord Forces
    return SCF_chax

@handcalc(override="long")
def SCF_bax(beta,twogamma,tau,Ov,theta):
    """Calculate the stress concentration 
    factor for balanced condition (1) axial stresses in the brace"""
    pt1 = 0.15 + 1.1 * beta - 0.48 * beta**2 - 0.14 / Ov
    pt2 = twogamma**0.55 * tau**(-0.3) * Ov**(-2.57 + 1.62 * beta**2) * sin(theta)**0.31
    SCF_bax = pt1 * pt2 #Balanced Loading condition Brace Forces
    return SCF_bax

@handcalc(override="long")
def SCF_chch(beta):
    """Calculate the stress concentration 
    factor for unbalanced condition (2) stresses in the chord"""
    SCF_chch = 1.2 + 1.46 * beta - 0.028 * beta**2 #Unbalanced loading condition Chord Forces
    return SCF_chch

@handcalc(override="long")
def chord_ax_stresses(SCF_chax,SCF_chch,P_brace,P_chord,theta,A_chord):
    """Calculate the axial stresses in the 
    chords for both balanced (1) and unbalanced (2) load conditions"""
    sigma_chord1P = SCF_chax * P_brace / A_chord
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

def bar_chart(sigma_chord1P,
                sigma_chord2P,
                sigma_chordM_ip,
                sigma_chordM_op,
                sigma_brace_1P,
                sigma_braceM_op,
                sigma_max):
    """Generate a bar chart showing the total stresses on the brace and chord,
    and compare these to the max allowable stress"""
    fig, ax = plt.subplots()
    members = ['chord','brace']
    sigma_1P = [sigma_chord1P,sigma_brace_1P]
    sigma_2P = [sigma_chord2P,0]
    sigma_M_ip = [sigma_chordM_ip,0]
    sigma_M_op = [sigma_chordM_op,sigma_braceM_op]
    y_pos = np.arange(len(members))
    # horizontal line indicating the threshold
    ax.plot([sigma_max, sigma_max],[-0.5, 1.5], "k--",label="$\sigma_{MAX}$")

    #Add stacked elements
    sigma_1and2 = np.add(sigma_1P, sigma_2P).tolist()
    sigma_1to3 = np.add(np.add(sigma_1P, sigma_2P), sigma_M_ip).tolist()


    ax.barh(y_pos,sigma_1P,left=0,label=r"$\sigma_{ax}$ - Balanced LC")
    ax.barh(y_pos,sigma_2P,left=sigma_1P,label=r"$\sigma_{ax}$ - Unbalanced LC")
    ax.barh(y_pos,sigma_M_ip,left=sigma_1and2,label=r"$\sigma_{Mip}$ - Unbalanced LC")
    ax.barh(y_pos,sigma_M_op,left=sigma_1to3,label=r"$\sigma_{Mop}$")
    plt.yticks(y_pos, members)
    ax.set_ylabel("Members")
    ax.set_xlabel("Stresses (MPa)")
    ax.legend(loc="best")
    ax.set_title("Member Stresses")
    ax.set_xlim(left=0)
    ax.plot([])

    return fig, ax

#Load Images
@st.cache
def load_image(image_file):
    """Display images using Pillow that 
    have been added via the streamlit file_uploader"""
    img = Image.open(image_file)
    return img