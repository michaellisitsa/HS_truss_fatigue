import streamlit as st

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as lines
import altair as alt

#Bokeh Plots
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, CustomJS, Label

# import function
from streamlit_bokeh_events import streamlit_bokeh_events

import forallpeople as u
u.environment('structural')
import math

def dim_params_altair(val1_string,val1,val2_string,val2,param_string,min,max,x_max):
    """
    Plot the dimensional variables beta, 
    2*gamma and tau, showing the acceptable range in green highlighted area
    """
    x = np.array([0,x_max])
    source = pd.DataFrame({
            val1_string: x,
            'y_max': x * max,
            'y_min': x * min
            })
    source_points = pd.DataFrame({
            val1_string:val1,
            val2_string:val2},index=[0])
    area = alt.Chart(source).mark_area(opacity=0.3).encode(
        x=val1_string,
        y='y_min',
        y2='y_max',
        color=alt.value("#33bd81")
        ).properties(title=f'{min} <= {param_string}(={val2_string}/{val1_string}) <= {max}')
    points = alt.Chart(source_points).mark_point(size=80).encode(
        x=val1_string,
        y=val2_string
    )
    c = alt.layer(points,area)
    c.layer[0].encoding.y.title = val2_string + ' (mm)'
    c.layer[0].encoding.x.title = val1_string + ' (mm)'
    c.configure_title(
                fontSize=20,
                font='Courier',
                anchor='start',
                color='gray'
            )
    return c

def dim_params_plot(b0,t0,b1,t1,chord_type,beta_min,beta_max,twogamma_min,twogamma_max,tau_min,tau_max):
    """Not used as Altair produces faster results
    To be removed in future update"""
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
    ax[0].annotate(text=f"{b1/b0:.2f}",xy=(b0,b1),xytext=(b0-75,b1+25),fontsize=8)
    ax[1].annotate(text=f"{b0/t0:.2f}",xy=(t0,b0),xytext=(t0-2,b0+25),fontsize=8)
    ax[2].annotate(text=f"{t1/t0:.2f}",xy=(t0,t1),xytext=(t0-2,t1+2),fontsize=8)

    #Create shaded region of acceptable values
    ax[0].fill_between([0,500],[0,beta_max * 500],[0,beta_min * 500], facecolor='green', alpha=0.5)
    ax[1].fill_between([0,20],[0,twogamma_max * 20],[0,twogamma_min * 20], facecolor='green', alpha=0.5)
    ax[2].fill_between([0,20],[0,tau_max * 20],[0,tau_min*20], facecolor='green', alpha=0.5)

    #Set graph titles with allowable range
    ax[0].set_title(f'${beta_min} \\leq \\beta(=b_1/b_0) \leq {beta_max}$',fontsize=10)
    ax[1].set_title(f'${twogamma_min} \\leq 2\\gamma(=b_0/t_0) \leq {twogamma_max}$',fontsize=10)
    ax[2].set_title(f'$0.25 \\leq \\tau(=t_1/t_0) \leq 1.0$',fontsize=10)

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

def dim_params_bokeh(vals:dict,chord_type,min,max):
    """Not used as Altair produces cleaner results
    To be removed in future update"""
    x = np.array([0,500])
    source = ColumnDataSource(data=dict(x=x,
                                    min_plot=x*min,
                                    max_plot=x*max))

    plot = figure()
    plot.line(x='x',y='max_plot', line_width=2,source=source)
    plot.line(x='x',y='min_plot', line_width=2,source=source)
    plot.varea(x='x',y1='max_plot',y2='min_plot',alpha=0.5,color='green',source=source)
    plot.circle(vals['b0'],vals['b1'],size=20, color="red")
    plot.xaxis[0].axis_label = 'b0'
    plot.yaxis[0].axis_label = 'b1'
    labels = Label(x=vals['b0']+20, y=vals['b1'],
            text=f"{list(vals.keys())[1]}/{list(vals.keys())[0]}={vals['b1']/vals['b0']}",
            render_mode='css',text_font_size='2em')
    plot.add_layout(labels)
    return plot

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

def geom_plot_altair(h0,theta,g_prime,t0,h1,e,chord_type):
    """
    Plot the geometry of the chord and brace members including centerlines.
    """
    #Define key variables for brace
    length = 0.5 #length of brace member in metres that will be visible on graph on the diagonal
    br_top_x = length * math.cos(theta) #horizontal projection of the brace length
    br_top_y = length * math.sin(theta) #vertical projection of the brace length
    br_bot_left_x = g_prime*t0/2.0 #bottom left intersect of brace with chord
    p = h1/math.sin(theta) #horizontal slice width of brace (length of contact against chord)

    #Brace fill is generated by 2 parallel lines 'x' and 'x2'
    #brace1_x defines a linear array of numbers for the left line
    #(representing the left edge of the brace)
    #Then source is a dataframe that creates a similar length array of:
    #- 'x' - x-coord of left edge of brace
    #- 'x2' - x-coord of right edge of brace (+ projection)
    #- 'y' - y-coord of both lines above
    brace1_x = np.array([br_bot_left_x,br_bot_left_x+br_top_x])
    source = pd.DataFrame({'x':brace1_x,
                            'x2':brace1_x + p,
                            'x_CL':np.array([0, br_bot_left_x + br_top_x + p/2]),
                            'y_CL':np.array([-e, h0/2 + br_top_y]),
                            'x_neg':-brace1_x,
                            'x2_neg':-brace1_x - p,
                            'x_neg_CL':np.array([0, -br_bot_left_x - br_top_x - p/2]),
                            'y':np.array([h0/2,h0/2+br_top_y])})

    #Altair mark_area function plots lines [x,y] and [x2,y] and fills horizontally
    #between both lines. An override color in HEX is provided for the fill.
    brace_area1 = alt.Chart(source).mark_area(opacity=0.6).encode(
        x = alt.X('x', scale=alt.Scale(domain=[-(h0+br_top_y)-0.4, (h0+br_top_y)+0.4])),
        x2='x2',
        y = alt.Y('y', scale=alt.Scale(domain=[-h0/2-0.2, h0/2+br_top_y+0.2])),
        color=alt.value("#0000FF")
        ).properties(title=f'Geometry of joint',width=600, height=300)
    brace_area2 = alt.Chart(source).mark_area(opacity=0.6).encode(
        x='x_neg',
        x2='x2_neg',
        y='y',
        color=alt.value("#0000FF")
        )

    brace_CL1 = alt.Chart(source).mark_line().encode(
        x='x_CL',
        y='y_CL',
        strokeDash = alt.value([5, 5])
    )

    brace_CL2 = alt.Chart(source).mark_line().encode(
        x='x_neg_CL',
        y='y_CL',
        strokeDash = alt.value([5, 5])
    )
    #Altair configuration options for the graph title
    brace_area1.configure_title(
            fontSize=20,
            font='Courier',
            anchor='start',
            color='gray'
        )
    x_chord = br_bot_left_x + p + br_top_x
    source_chord = pd.DataFrame({'x':np.array([-x_chord,x_chord]),
                            'y':np.array([-h0/2,-h0/2]),
                            'y2':np.array([h0/2,h0/2])})
    chord_rect = alt.Chart(source_chord).mark_area(opacity=0.6).encode(
                                x='x',
                                y='y',
                                y2='y2',
                                color=alt.value("#FF0000")
    )
    
    # annotation = alt.Chart().mark_text(
    # align='left',
    # baseline='middle',
    # fontSize = 20,
    # dx = 7
    # ).encode(
    #     x=[0.],
    #     y=[-e],
    #     text=f'{theta*180/math.pi}')

    #Where CHS is used, an arc should be plotted at the intersection of brace and chord.
    #Although not precise, this arc indicates the saddle of the circular sections on each other.
    if chord_type=="CHS":
        
        chord_overlap = 0.15

        #Algorithm to determine the equation of a circle via 3 points along it:
        #https://stackoverflow.com/questions/28910718/give-3-points-and-a-plot-circle
        #Complex numbers result in simpler calculations.
        #c = (negated) center of the circle
        #(as a complex number, so use .real and .imag for the x/y coordinates)
        #abs(c+x) = the radius (a real number, abs makes it so).
        #x,y,z are 3 points on the circle, converted into complex coordinates first
        #(x-coord = real part)(y-coord = complex part)
        x = complex(br_bot_left_x,h0/2)
        y = complex(br_bot_left_x + p/2,h0/2-chord_overlap*p)
        z = complex(br_bot_left_x + p,h0/2)
        w = z-x #intermediate value, no physical definition known
        w /= y-x
        c = (x-y)*(w-abs(w)**2)/2j/w.imag-x

        #Determine the angle subtended by an arc
        #asin(opp/hyp) is used because both opp & hyp are known
        #opp = p/2: half projected width of brace on chord represents 1/2 the subtended arc
        #hyp = abs(c+x) = radius: where radius is the hypotenuse of the triangle
        theta = math.asin((p/2)/abs(c+x))

        #Now that the subtended angle is obtained, need to create an array of 'num' values
        #between -theta and +theta which represents the entire angle range of arc
        #the angle is positioned around pi, which is equivalent to 180 deg with 0 deg being vertically up
        #therefore arc1_x represents the angles that make up the cradle of the brace.
        #The angles are then converted into coordinates along the curve link:
        #https://math.stackexchange.com/questions/260096/find-the-coordinates-of-a-point-on-a-circle
        #x = rsinθ + c[x], y = rcosθ + c[y] are for a circle centered at (c[x],c[y])
        #where c is defined above
        arc1_x = np.linspace(2*math.pi/2 - theta,2*math.pi/2 + theta,num=20)
        source_arc = pd.DataFrame({'x':abs(c+x)*np.sin(arc1_x)-c.real,
                                    'x_neg':-abs(c+x)*np.sin(arc1_x)+c.real,
                                    'y':abs(c+x)*np.cos(arc1_x)-c.imag,
                                    'y_horiz':h0/2})

        #Altair mark_area function plots lines [x,y] and [x,y_horiz] and fills vertically
        # y_horiz is simply y-coords along the interface of brace and chord (always h0/2)
        # x and y defined above               
        brace_arc1 = alt.Chart(source_arc).mark_area(opacity=0.6).encode(
            x='x',
            y='y',
            y2='y_horiz',
            color=alt.value("#0000FF")
            )
        brace_arc2 = alt.Chart(source_arc).mark_area(opacity=0.6).encode(
            x='x_neg',
            y='y',
            y2='y_horiz',
            color=alt.value("#0000FF")
            )
        return  brace_CL1 + brace_CL2 + chord_rect + brace_arc1 + brace_arc2 + brace_area1 + brace_area2
    else:
        #Where SHS or RHS, there is no arc needed because brace sits on top of chord and does not cradle it.
        return  brace_CL1 + brace_CL2 + chord_rect + brace_area1 + brace_area2

def SCF_ochax_plot(beta,SCF_ochax,SCF_obax):
    #Create graph to visualise answer on graph
    fig, ax = plt.subplots(1,2)
    SCF_ochax_img = plt.imread("data/SCFochax.png")
    SCF_obax_img = plt.imread("data/SCFobax.png")
    ax[0].imshow(SCF_ochax_img, extent=[0, 1, 0, 4])
    ax[1].imshow(SCF_obax_img, extent=[0, 1, 0, 4])
    ax[0].set_title(r"$SCF_{o,ch,ax}$")
    ax[1].set_title(r"$SCF_{o,b,ax}$")
    ax[0].plot(beta,SCF_ochax,'ro')
    ax[1].plot(beta,SCF_obax,'ro')
    ax[0].set_aspect(0.25)
    ax[1].set_aspect(0.25)
    return fig, ax

def bokeh_interactive(sigma_chord,sigma_brace,sigma_max,chord_ind,brace_ind):
    # create plot
    p = figure(tools="lasso_select,reset",
                x_range=(0, sigma_max*3), 
                y_range=(0, sigma_max*3),
                x_axis_label='Chord Stress (MPa)',
                y_axis_label='Brace Stress (MPa)')
    cds = ColumnDataSource(
        data={
            "x": sigma_chord,
            "y": sigma_brace,
        }
    )
    p.circle("x", "y", source=cds)

    # define events
    cds.selected.js_on_change(
        "indices",
        CustomJS(
            args=dict(source=cds),
            code="""
            document.dispatchEvent(
                new CustomEvent("TestSelectEvent", {detail: {indices: cb_obj.indices}})
            )
            """
        )
    )

    # result will be a dict of {event_name: event.detail}
    # events by default is "", in case of more than one events pass it as a comma separated values
    # event1,event2 
    # debounce is in ms
    # refresh_on_update should be set to False only if we dont want to update datasource at runtime
    # override_height overrides the viewport height
    result = streamlit_bokeh_events(
            bokeh_plot=p,
            events="TestSelectEvent",
            key="foo",
            refresh_on_update=True,
            override_height=600,
            debounce_time=500)
    # some event was thrown
    if result is not None:
        # TestSelectEvent was thrown
        if "TestSelectEvent" in result:
            st.subheader("Selected Points")
            indices = result["TestSelectEvent"].get("indices", [])
            col1, col2 = st.beta_columns(2)
            col1.subheader("Chords")
            col1.table([chord_ind[i] for i in indices])
            col2.subheader("Brace")
            col2.table([brace_ind[i] for i in indices])
    #st.write(result)
    #return(result)