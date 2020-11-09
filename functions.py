from math import sqrt
from handcalcs import handcalc
from math import sqrt, cos, sin, pi, atan, tan
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

@handcalc(override="long")
def dim_params(b0,t0,b1,t1):
    beta = b1 / b0 #Ratio of brace to chord width, where 0.35 <= beta <= 1.0
    twogamma = b0 / t0 #Ratio of chord width to 2*thickness, where 10 <= 2*gamma <= 35
    tau = t1 / t0 #Ratio of brace to chord thickness, where 0.25 < tau <= 1.0
    return beta, twogamma, tau

def dim_params_plot(b0,t0,b1,t1):

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
    SCF_chaxpt1 = (0.5+ 2.38 * beta - 2.87 * beta**2 + 2.18 * beta * Ov + 0.39 * Ov - 1.43 * sin(theta))
    SCF_chaxpt2 =  (twogamma**0.29 * tau**0.7 * Ov**(0.73-5.53*sin(theta)**2) * sin(theta)**(-0.4-0.08*Ov))
    SCF_chax = SCF_chaxpt1 * SCF_chaxpt2 #Balanced Loading condition Chord Forces
    return SCF_chax