from math import sqrt
from handcalcs import handcalc
from math import sqrt, cos, sin, pi, atan, tan
import sectionproperties.pre.sections as sections
from sectionproperties.analysis.cross_section import CrossSection
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

@handcalc(override="long")
def dim_params(b0,t0,b1,t1):
    beta = b1 / b0 #Ratio of brace to chord width, where 0.35 <= beta <= 1.0
    twogamma = b0 / t0 #Ratio of chord width to 2*thickness, where 10 <= 2*gamma <= 35
    tau = t1 / t0 #Ratio of brace to chord thickness, where 0.25 < tau <= 1.0
    return beta, twogamma, tau

@handcalc(override="long")
def overlap(L_chord,chordspacing,div_chord,eccentricity,h0,h1):
    h_truss = chordspacing + 2 * eccentricity #Height of truss adjusted by eccentricity.
    l_truss = L_chord / div_chord #Length of truss (projection of brace onto the chord)
    theta = atan(h_truss / l_truss) #Angle between chord and brace
    p = h1 / sin(theta) #Projected width of brace
    x = (0.5*h0 + eccentricity) / tan(theta) #Projection of Intersection
    q = p - 2 * x #Overlap Projection
    Ov = q / p #Overlap, where 50% <= Ov <= 100%
    return Ov

def beta_chart(b0,t0,b1,t1):
    #Set up range and values
    beta_x = np.linspace(0,500,num=2)
    beta_y_max = beta_x
    beta_y_min = 0.35 * beta_x
    twogamma_x = np.linspace(0,20,num=2)
    twogamma_y_max = 35 * twogamma_x
    twogamma_y_min = 10 * twogamma_x
    tau_x = np.linspace(0,20,num=2)
    tau_y_max = tau_x
    tau_y_min = 0.25 * tau_x

    # plot it!
    fig, ax = plt.subplots(ncols=3,figsize=(9,3))
    ax[0].plot(beta_x,beta_y_max, label=r'$\beta=1$', color='red')
    ax[0].plot(beta_x,beta_y_min, label=r'$\beta=0.35$', color='yellow')
    ax[1].plot(twogamma_x,twogamma_y_max,label=r'$2\cdot \gamma = 35$', color='red')
    ax[1].plot(twogamma_x,twogamma_y_min,label=r'$2\cdot \gamma = 10$', color='yellow')
    ax[2].plot(tau_x,tau_y_max,label=r'$\tau=1.0$', color='red')
    ax[2].plot(tau_x,tau_y_min,label=r'$\tau=0.25$', color='yellow')

    ax[0].plot(b0,b1,'ro',c="black")
    ax[0].annotate(text=f"{b0},{b1}",xy=(b0,b1),xytext=(b0-75,b1+25),fontsize=8)
    ax[1].plot(t0,b0,'ro',c="black")
    ax[1].annotate(text=f"{t0},{b0}",xy=(t0,b0),xytext=(t0-2,b0+25),fontsize=8)
    ax[2].plot(t0,t1,'ro',c="black")
    ax[2].annotate(text=f"{t0},{t1}",xy=(t0,t1),xytext=(t0-2,t1+2),fontsize=8)
    ax[0].fill_between(beta_x, beta_y_max, beta_y_min, facecolor='green', alpha=0.5)
    ax[1].fill_between(twogamma_x, twogamma_y_max, twogamma_y_min, facecolor='green', alpha=0.5)
    ax[2].fill_between(tau_x, tau_y_max, tau_y_min, facecolor='green', alpha=0.5)
    ax[0].set_title(r'$0.35 \leq \beta(=\frac{b_1}{b_0}) \leq 1.0$',fontsize=10)
    ax[1].set_title(r'$10 \leq 2\gamma(=\frac{b_0}{t_0}) \leq 35$',fontsize=10)
    ax[2].set_title(r'$0.25 \leq \tau(=\frac{t_1}{t_0}) \leq 1.0$')
    ax[0].set_xlabel('b0')
    ax[0].set_ylabel('b1')
    ax[1].set_xlabel('t0')
    ax[1].set_ylabel('b0')
    ax[2].set_xlabel('t0')
    ax[2].set_ylabel('t1')
    [ax[i].legend(loc='upper left') for i in range(3)]
    [ax[i].grid() for i in range(3)]
    return fig, ax