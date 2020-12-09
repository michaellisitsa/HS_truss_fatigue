import streamlit as st

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as lines

import forallpeople as u
u.environment('structural')
import math

def dim_params_plot(b0,t0,b1,t1,chord_type,beta_min,beta_max,twogamma_min,twogamma_max,tau_min,tau_max):
    """Plot the dimensional variables beta, 
    2*gamma and tau, showing the acceptable range in green highlighted area"""
    # Create Plot
    fig, ax = plt.subplots(ncols=3,figsize=(9,3))

    #Plot max and min lines
    ax[0].plot([0,500],[0,beta_max * 500], label=f'$\\beta={beta_max}$', color='red') #max line
    ax[0].plot([0,500],[0.,beta_min * 500.], label=f'$\\beta={beta_min}$', color='yellow') #min line
    ax[1].plot([0,20],[0,twogamma_max * 20],label=f'$2\\cdot \\gamma = {twogamma_max}$', color='red')
    ax[1].plot([0,20],[0,twogamma_min * 20],label=f'$2\\cdot \\gamma = {twogamma_min}$', color='yellow')
    ax[2].plot([0,20],[0,tau_max * 20],label=r'$\tau=1.0$', color='red')
    ax[2].plot([0,20],[0,tau_min*20],label=r'$\tau=0.25$', color='yellow')

    #Plot single points for each of graph
    ax[0].plot(b0,b1,'ro',c="black")
    ax[1].plot(t0,b0,'ro',c="black")
    ax[2].plot(t0,t1,'ro',c="black")

    #Annotate single points for each graph with beta,gamma,tau values
    ax[0].annotate(text=b1/b0,xy=(b0,b1),xytext=(b0-75,b1+25),fontsize=8)
    ax[1].annotate(text=b0/t0,xy=(t0,b0),xytext=(t0-2,b0+25),fontsize=8)
    ax[2].annotate(text=t1/t0,xy=(t0,t1),xytext=(t0-2,t1+2),fontsize=8)

    #Create shaded region of acceptable values
    ax[0].fill_between([0,500],[0,beta_max * 500],[0,beta_min * 500], facecolor='green', alpha=0.5)
    ax[1].fill_between([0,20],[0,twogamma_max * 20],[0,twogamma_min * 20], facecolor='green', alpha=0.5)
    ax[2].fill_between([0,20],[0,tau_max * 20],[0,tau_min*20], facecolor='green', alpha=0.5)

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

def geom_plot(h0,theta,g_prime,t0,h1,e,chord_type):
    """
    Plot the geometry of the chord and brace members incl Centerlines.
    """
    fig, ax = plt.subplots()
    
    #Define variables for brace
    length = 0.5 #Length of brace to show
    br_top_x = length * math.cos(theta) #change in x to top of brace
    br_top_y = length * math.sin(theta) #change in t to top of brace
    br_bot_left_x = g_prime*t0/2.0 #bottom left intersect of brace with chord
    p = h1/math.sin(theta)

    #Plot brace shape:
    brace1_points = [
                [br_bot_left_x,                 h0/2],
                [br_bot_left_x + br_top_x,      h0/2 + br_top_y],
                [br_bot_left_x + p + br_top_x,  h0/2 + br_top_y],
                [br_bot_left_x + p,             h0/2]
                    ]
    brace2_points = [
            [-br_bot_left_x,                 h0/2],
            [-br_bot_left_x - br_top_x,      h0/2 + br_top_y],
            [-br_bot_left_x - p - br_top_x,  h0/2 + br_top_y],
            [-br_bot_left_x - p,             h0/2]
                ]
    brace1_obj = plt.Polygon(brace1_points,fc='blue',alpha=0.4,edgecolor='black')
    brace2_obj = plt.Polygon(brace2_points,fc='blue',alpha=0.4,edgecolor='black')
    ax.add_patch(brace1_obj)
    ax.add_patch(brace2_obj)

    #Plot brace centerlines
    ax.plot([0, br_bot_left_x + br_top_x + p/2],
            [-e, h0/2 + br_top_y],linestyle='dashdot',color='black')
    ax.plot([0, -br_bot_left_x - br_top_x - p/2],
            [-e, h0/2 + br_top_y],linestyle='dashdot',color='black')
    
    #Plot chord
    if chord_type == "CHS:":
        fc='none'
    else:
        fc='red'
    rectangle = plt.Rectangle((-(br_bot_left_x + p + br_top_x),-h0/2),
                            2*(br_bot_left_x + p + br_top_x),h0,fc=fc,alpha=0.4,edgecolor='black')
    ax.add_patch(rectangle)

    #Figure options
    ax.grid(True, which='both')
    ax.axhline(y=0, color='k')
    ax.axvline(x=0, color='k')
    ax.set_aspect('equal')

    #Angle between brace
    angle_arc = mpatches.Arc([0,-e],0.3,0.3,0,0,theta*180/math.pi)
    line_1 = lines.Line2D([0,0.2], [-e,-e], linewidth=1, linestyle = "-", color="black")
    ax.add_line(line_1)
    ax.annotate(f"$\\theta = {theta*180/math.pi:.0f}\\degree$",(0.2,-e))
    ax.add_patch(angle_arc)

    #Plot a filled arc to show the CHS brace cradling the cord
    if chord_type=="CHS":
        #Calculate the equation of a circle from 3 points on the circle (using complex numbers)
        chord_overlap = 0.15
        x = complex(br_bot_left_x,h0/2)
        y = complex(br_bot_left_x + p/2,h0/2-chord_overlap*p)
        z = complex(br_bot_left_x + p,h0/2)
        w = z-x
        w /= y-x
        c = (x-y)*(w-abs(w)**2)/2j/w.imag-x

        #Generate arc under each brace termination to simulate cradle
        theta = math.asin((p/2)/abs(c+x))*180/math.pi
        pac = mpatches.Arc([-c.real, -c.imag], 2 * abs(c+x), 2 * abs(c+x), 0, theta1=270-theta, theta2=270 + theta, hatch = '.........', alpha=0.7)
        pac2 = mpatches.Arc([c.real, -c.imag], 2 * abs(c+x), 2 * abs(c+x), 0, theta1=270-theta, theta2=270 + theta, hatch = '.........', alpha=0.7)
        pac.set_color('blue')
        pac2.set_color('blue')        
        ax.add_patch(pac)
        ax.add_patch(pac2)

        #Assign gradient fill to rectangular chord, to give impression of being curved
        im = plt.imshow([[0.,0.],[1.,1.]], interpolation='bicubic', cmap=plt.cm.Reds,
                origin='lower', extent=[-(br_bot_left_x + p + br_top_x+0.05), br_bot_left_x + p + br_top_x + 0.05, -h0/2-0.05, h0/2 + br_top_y+0.05],
                clip_path=rectangle, clip_on=True)
        im.set_clip_path(rectangle)
    else:
        pass
    return fig,ax
    