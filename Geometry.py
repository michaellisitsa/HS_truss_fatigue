import streamlit as st

from handcalcs import handcalc
import forallpeople as u
u.environment('structural')

from math import sin, cos, tan, atan, pi, asin
import numpy as np
import pandas as pd

import helper_funcs
from Enum_vals import Section, Member, Code, Run
import Dimensions
import Forces

import altair as alt

from typing import Union, Any

from abc import ABC, abstractmethod

class Geometry(ABC):
    def __init__(self,Dim_C: Union[Dimensions.custom_sec,Dimensions.database_sec],
                      Dim_B: Union[Dimensions.custom_sec,Dimensions.database_sec], 
                      e, chordspacing, L_chord, div_chord, run: Run = Run.SINGLE):
        self.Dim_C = Dim_C
        self.Dim_B = Dim_B
        self.run = run
        self.e = e
        self.chordspacing = chordspacing
        self.L_chord = L_chord
        self.div_chord = div_chord

        #Initialised variables:
        self.success = False #to be overriden by child class
        self.message = "No message passed in" #to be overriden by child class
        self.latex = None #To be overriden with latex representation of the calculations
        self.beta = None
        self.twogamma = None
        self.tau = None
        self.alpha = None
        self.theta = None

    @abstractmethod
    def check_geom(self):
        pass

    @abstractmethod
    def plot_geom(self, force: Forces.Forces):
        pass

    def st_message_geom(self,container):
        """Output or stop script for angle, 
        eccentricity, gap checks"""
        if self.success:
            container.success(self.message)
        else:
            container.error(self.message)
            st.stop()

class K_joint(Geometry):
    def __init__(self,Dim_C: Union[Dimensions.custom_sec,Dimensions.database_sec],
                      Dim_B: Union[Dimensions.custom_sec,Dimensions.database_sec], 
                      e, chordspacing, L_chord, div_chord, run: Run = Run.SINGLE):
        super().__init__(Dim_C, Dim_B, e, chordspacing, L_chord, div_chord, run)

        args = {'b_0':self.Dim_C.b * u.m, # type: ignore
                'h_0':self.Dim_C.d * u.m, # type: ignore
                't_0':self.Dim_C.t * u.m, # type: ignore
                'b_1':self.Dim_B.b * u.m, # type: ignore
                'h_1':self.Dim_B.d * u.m, # type: ignore
                't_1':self.Dim_B.t * u.m, # type: ignore
                'L_chord':self.L_chord * u.m, # type: ignore
                'chordspacing':self.chordspacing * u.m, # type: ignore
                'div_chord':self.div_chord,
                'e':self.e * u.m} # type: ignore
        
        def check_geom_func(b_0,h_0,t_0,b_1,h_1,t_1,L_chord,chordspacing,div_chord,e):
            """Calculate the dimensional variables beta, 
            2*gamma and tau
            Calculate the overlap percentage 
            'Ov' to be used in the calculation"""
            beta = b_1 / b_0 #Ratio of brace to chord width, where 0.35 <= beta <= 1.0
            twogamma = b_0 / t_0 #Ratio of chord width to 2*thickness, where 10 <= 2*gamma <= 35
            tau = t_1 / t_0 #Ratio of brace to chord thickness, where 0.25 < tau <= 1.0
            h_truss = chordspacing + 2 * e #Height of truss adjusted by eccentricity.
            l_truss = L_chord / div_chord #Length of truss (projection of brace onto the chord)
            theta = atan(h_truss / l_truss) #Angle between chord and brace
            theta_deg = (theta*180/pi)
            p = h_1 / sin(theta) #Projected width of brace
            x = (0.5*h_0 + e) / tan(theta) #Projection of Intersection
            q = p - 2 * x #Overlap Projection
            g_prime = -1 * q/t_0 #Ratio of gap to chord thickness
            O_v = q / p #Overlap
            return beta, twogamma, tau, O_v, theta, g_prime

        self.latex, (self.beta,
                                self.twogamma,
                                self.tau,
                                self.O_v,
                                self.theta,
                                self.g_prime) = helper_funcs.func_by_run_type(self.run, args, check_geom_func)

    def check_geom(self):
        #Check for acceptable angles
        if 30*pi/180 < self.theta < 60 * pi/180:
            success = True
            message = "Angle OK"
        else:
            success = False
            message = "Angle NOT OK. Maintain 30 to 60deg"
        
        #Check of acceptable eccentricity
        if -0.55 <= self.e/self.Dim_C.d <= 0.25:
            message += " | Eccentricity OK"
        else:
            success = False
            message += " | Eccentricity NOT OK. Maintain {0:.0f}mm<=e/self.Dim_C.d<={1:.0f}mm".format(-self.Dim_C.d*0.55*1000,self.Dim_C.d*0.25*1000)

        #Check for acceptable overlap/gap for RHS, and for no overlap for CHS
        if 0 <= self.g_prime < 2 * self.tau and self.Dim_C.section_type is not Section.CHS:
            gap = True
            success = False
            message += " | Gap NOT OK. Increase so g'>= 2 * tau"
        elif self.O_v <= 0:
            gap = True
        elif (self.O_v < 0.5 or self.O_v > 1.0) and self.Dim_C.section_type is not Section.CHS:
            gap = False
            success = False
            message += " | Overlap NOT OK. Change to 50% to 100%"
        elif 0.0 < self.O_v <= 1.0 and self.Dim_C.section_type is not Section.CHS:
            gap = False
            message += " | Overlap OK"
        else:
            gap = False
            success = False
            message += " | Overlap NOT OK for CHS. Make gap joint"

        self.success, self.message, self.gap = success, message, gap

    def plot_geom(self,force: Forces.Forces):
        """
        Plot the geometry of the chord and brace members including centerlines.
        """
        #Define key variables for brace
        length = 0.5 #length of brace member in metres that will be visible on graph on the diagonal
        br_top_x = length * cos(self.theta) #horizontal projection of the brace length
        br_top_y = length * sin(self.theta) #vertical projection of the brace length
        br_bot_left_x = self.g_prime*self.Dim_C.t/2.0 #bottom left intersect of brace with chord
        p = self.Dim_B.d/sin(self.theta) #horizontal slice width of brace (length of contact against chord)

        #Brace fill is generated by 2 parallel lines 'x' and 'x2'
        #brace1_x defines a linear array of numbers for the left line
        #(representing the left edge of the brace)
        #Then source is a dataframe that creates a similar length array of:
        #- 'x' - x-coord of left edge of brace
        #- 'x2' - x-coord of right edge of brace (+ projection)
        #- 'y' - y-coord of both lines above
        #- 'y_CL' - Centerline plot ending at intersection point
        #- 'y_CL_label' - Label value for centrline plot
        brace1_x = np.array([br_bot_left_x,br_bot_left_x+br_top_x])
        source = pd.DataFrame({'x':brace1_x,
                                'x2':brace1_x + p,
                                'x_CL':np.array([0, br_bot_left_x + br_top_x + p/2]),
                                'y_CL':np.array([-self.e, self.Dim_C.d/2 + br_top_y]),
                                'y_CL_label':np.array([f'{self.theta*180/pi:.0f} deg','']),
                                'x_neg':-brace1_x,
                                'x2_neg':-brace1_x - p,
                                'x_neg_CL':np.array([0, -br_bot_left_x - br_top_x - p/2]),
                                'y':np.array([self.Dim_C.d/2,self.Dim_C.d/2+br_top_y])})

        #Altair mark_area function plots lines [x,y] and [x2,y] and fills horizontally
        #between both lines. An override color in HEX is provided for the fill.
        brace_area1 = alt.Chart(source).mark_area(opacity=0.6).encode(
            x = alt.X('x', scale=alt.Scale(domain=[-(self.Dim_C.d+br_top_y)-0.4, (self.Dim_C.d+br_top_y)+0.4])),
            x2='x2',
            y = alt.Y('y', scale=alt.Scale(domain=[-self.Dim_C.d/2-0.2, self.Dim_C.d/2+br_top_y+0.2])),
            color=alt.value("#0000FF")
            ).properties(title=f'Geometry of joint',width=600, height=300)
        brace_area2 = alt.Chart(source).mark_area(opacity=0.6).encode(
            x='x_neg',
            x2='x2_neg',
            y='y',
            color=alt.value("#0000FF")
            )

        #Plot brace centerlines using:
        #- x_CL & y_CL: coordinates of centerline line
        #- y_CL_label: angle label to be placed at bottom of line
        brace_CL1 = alt.Chart(source).mark_line().encode(
            x='x_CL',
            y='y_CL',
            strokeDash = alt.value([5, 5])
        )

        angle_text = alt.Chart(source).mark_text(align='left', dx=20).encode(
            x=alt.X('x_CL:Q',aggregate='min'),
            y=alt.Y('y_CL:Q', aggregate={'argmin': 'x_CL'}),
            text=alt.Text('y_CL_label:N',aggregate='min')
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
                                'y':np.array([-self.Dim_C.d/2,-self.Dim_C.d/2]),
                                'y2':np.array([self.Dim_C.d/2,self.Dim_C.d/2])})
        chord_rect = alt.Chart(source_chord).mark_area(opacity=0.6).encode(
                                    x='x',
                                    y='y',
                                    y2='y2',
                                    color=alt.value("#FF0000")
        )

        #Unicode arrow codes are: ← → U-2190 U-2192 ⤾ ⤿ U-293e U-293f 
        Fx_left = 240
        Fx_right = 220
        a = {'x': [-(br_bot_left_x + br_top_x + p),
                        br_bot_left_x + br_top_x + p,
                        -(br_bot_left_x + br_top_x+ p/2),
                        br_bot_left_x + br_top_x+ p/2],
            'angle':[0.,0.,self.theta*180/pi,180-self.theta*180/pi],
            'y': [0.,0.,0.5,0.5],
            'name': [f'⤾ {force.M_ip_chord / 1000} kNm, {(force.P_chord - 2 * force.P_brace * cos(self.theta))/1000:.2f} kN ←',
                        f'→ {force.P_chord / 1000:.2f} kN, ⤿ {force.M_ip_chord / 1000} kNm',
                        f'{force.P_brace / 1000:.2f} kN ←',
                        f'→ {force.P_brace / 1000:.2f} kN']}
        df_arrows = pd.DataFrame(a)

        arrow_1 = alt.Chart(df_arrows).encode(
            x='x',
            y='y',
            text='name')

        #The list comprehension for generating arrows at different angles is stated in:
        #https://stackoverflow.com/questions/55991996/altair-rotate-text-by-value-specified-in-feature
        arrow_layers = [
            arrow_1.transform_filter(alt.datum.name == name).mark_text(angle=angle,fontSize=15)
            for (name, angle) in zip(df_arrows.name, df_arrows.angle)]
        brace_area1.encoding.x.title = 'X (m)'
        brace_area1.encoding.y.title = 'Y (m)'

        #Where CHS is used, an arc should be plotted at the intersection of brace and chord.
        #Although not precise, this arc indicates the saddle of the circular sections on each other.
        if self.Dim_C.section_type is Section.CHS:
            
            chord_overlap = 0.15

            #Algorithm to determine the equation of a circle via 3 points along it:
            #https://stackoverflow.com/questions/28910718/give-3-points-and-a-plot-circle
            #Complex numbers result in simpler calculations.
            #c = (negated) center of the circle
            #(as a complex number, so use .real and .imag for the x/y coordinates)
            #abs(c+x) = the radius (a real number, abs makes it so).
            #x,y,z are 3 points on the circle, converted into complex coordinates first
            #(x-coord = real part)(y-coord = complex part)
            x = complex(br_bot_left_x,self.Dim_C.d/2)
            y = complex(br_bot_left_x + p/2,self.Dim_C.d/2-chord_overlap*p)
            z = complex(br_bot_left_x + p,self.Dim_C.d/2)
            w = z-x #intermediate value, no physical definition known
            w /= y-x
            c = (x-y)*(w-abs(w)**2)/2j/w.imag-x

            #Determine the angle subtended by an arc
            #asin(opp/hyp) is used because both opp & hyp are known
            #opp = p/2: half projected width of brace on chord represents 1/2 the subtended arc
            #hyp = abs(c+x) = radius: where radius is the hypotenuse of the triangle
            theta = asin((p/2)/abs(c+x))

            #Now that the subtended angle is obtained, need to create an array of 'num' values
            #between -theta and +theta which represents the entire angle range of arc
            #the angle is positioned around pi, which is equivalent to 180 deg with 0 deg being vertically up
            #therefore arc1_x represents the angles that make up the cradle of the brace.
            #The angles are then converted into coordinates along the curve link:
            #https://math.stackexchange.com/questions/260096/find-the-coordinates-of-a-point-on-a-circle
            #x = rsinθ + c[x], y = rcosθ + c[y] are for a circle centered at (c[x],c[y])
            #where c is defined above
            arc1_x = np.linspace(2*pi/2 - theta,2*pi/2 + theta,num=20)
            source_arc = pd.DataFrame({'x':np.subtract(np.multiply(abs(c+x),np.sin(arc1_x)),c.real),
                                        'x_neg':np.add(np.multiply(-abs(c+x),np.sin(arc1_x)),c.real),
                                        'y':np.subtract(np.multiply(abs(c+x),np.cos(arc1_x)),c.imag),
                                        'y_horiz':self.Dim_C.d/2})

            #Altair mark_area function plots lines [x,y] and [x,y_horiz] and fills vertically
            # y_horiz is simply y-coords along the interface of brace and chord (always self.Dim_C.d/2)
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
            return alt.layer(angle_text,brace_CL1,brace_CL2,chord_rect,brace_arc1,brace_arc2,brace_area1,brace_area2,*arrow_layers)
        else:
            #Where SHS or RHS, there is no arc needed because brace sits on top of chord and does not cradle it.
            return alt.layer(angle_text,brace_CL1,brace_CL2,chord_rect,brace_area1,brace_area2,*arrow_layers)

class T_joint(Geometry):
    def __init__(self,Dim_C: Union[Dimensions.custom_sec,Dimensions.database_sec],
                      Dim_B: Union[Dimensions.custom_sec,Dimensions.database_sec], 
                      L_chord, div_chord, theta, C_fixity, run: Run = Run.SINGLE):
        super().__init__(Dim_C, Dim_B, 0., 0., L_chord, div_chord, run)
        self.theta = theta
        self.C_fixity = C_fixity
        args = {'b_0':self.Dim_C.b * u.m, # type: ignore
                'h_0':self.Dim_C.d * u.m, # type: ignore
                't_0':self.Dim_C.t * u.m, # type: ignore
                'b_1':self.Dim_B.b * u.m, # type: ignore
                'h_1':self.Dim_B.d * u.m, # type: ignore
                't_1':self.Dim_B.t * u.m, # type: ignore
                'L_chord':self.L_chord * u.m, # type: ignore
                'div_chord':self.div_chord,
                'C':self.C_fixity
                }
        
        def check_geom_func(b_0,h_0,t_0,b_1,h_1,t_1,L_chord,div_chord,C):
            """Calculate the dimensional variables beta, 
            2*gamma and tau
            Calculate the overlap percentage 
            'Ov' to be used in the calculation"""
            beta = b_1 / b_0 #Ratio of brace to chord width, where 0.2 <= beta <= 1.0
            twogamma = b_0 / t_0 #Ratio of chord width to 2*thickness, where 15 <= 2*gamma <= 64
            tau = t_1 / t_0 #Ratio of brace to chord thickness, where 0.2 < tau <= 1.0
            alpha = 4 * (L_chord / div_chord) / b_0 #2 * span/depth of chord 4 <= alpha <= 40
            C_1 = 2 * (C - 0.5)
            C_2 = C / 2
            C_3 = C / 5
            return beta, twogamma, tau, alpha, C_1, C_2, C_3

        self.latex, (self.beta,
                    self.twogamma, 
                    self.tau, 
                    self.alpha, 
                    self.C_1, 
                    self.C_2, 
                    self.C_3) = helper_funcs.func_by_run_type(self.run, args, check_geom_func)
        
    def check_geom(self):
        #Check for acceptable angles
        if 30*pi/180 <= self.theta <= 90 * pi/180:
            success = True
            message = "Angle OK"
        else:
            success = False
            message = "Angle NOT OK. Maintain 30 to 90deg"
        
        #Check of acceptable 2*span/depth ratio
        if 4 <= self.alpha <= 40:
            message += " | Span to Depth OK"
        else:
            success = False
            message += f" | Span to Depth NOT OK. Maintain 4 <= alpha ({self.alpha}) <= 40"

        #Check dimension parameters
        if 0.2 <= self.beta <= 1.0:
            message += " | Beta OK"
        else:
            success = False
            message += f" | Beta NOT OK. Maintain 0.2 <= beta ({self.beta}) <= 1.0"

        if 15 <= self.twogamma <= 64:
            message += " | gamma OK"
        else:
            success = False
            message += f" | twogamma NOT OK. Maintain 0.2 <= twogamma ({self.twogamma}) <= 1.0"

        if 0.2 <= self.tau <= 1.0:
            message += " | tau OK"
        else:
            success = False
            message += f" | tau NOT OK. Maintain 0.2 <= tau ({self.tau}) <= 1.0"

        self.success, self.message = success, message

    def plot_geom(self,force: Forces.Forces):
        #TODO - Implement plot for T-joint
        pass

def st_geom_Kjoint_picker(Dim_C: Dimensions.Dimensions):
    """
    Create Streamlit input boxes for various geometry properties, and return those.
    Dim_C: Dimension of chord check for CHS which must have zero eccentricity
    """
    st.sidebar.subheader("Geometry Inputs:")
    e = (0 if Dim_C.section_type is Section.CHS else st.sidebar.number_input('Eccentricity',-400,400,-100,step=5,format='%f') / 1000)
    chordspacing = st.sidebar.number_input('Chord spacing (mm)',100,4000,2000,step=50,format='%i') / 1000
    L_chord = st.sidebar.number_input('Length of Chord (mm)',100,30000,8000,step=100,format='%i') / 1000
    div_chord = st.sidebar.number_input('Chord divisions',1,20,4,step=1,format='%i')
    return e, chordspacing, L_chord, div_chord

def st_geom_Tjoint_picker(Dim_C: Dimensions.Dimensions):
    """
    Create Streamlit input boxes for various geometry properties, and return those.
    Dim_C: Dimension of chord check for CHS which must have zero eccentricity
    """
    st.sidebar.subheader("Geometry Inputs:")
    L_chord = st.sidebar.number_input('Length of Chord (mm)',100,30000,8000,step=100,format='%i') / 1000
    div_chord = st.sidebar.number_input('Chord divisions:',1,20,4,step=1,format='%i')
    angle = st.sidebar.number_input('Angle:',30.0,90.0,90.0,step=1.0) * pi / 180
    return L_chord, div_chord, angle