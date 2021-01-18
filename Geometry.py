import streamlit as st

from handcalcs import handcalc
import forallpeople as u
u.environment('structural')

from math import sin, cos, tan, atan, pi, asin, exp, sqrt
import numpy as np
import pandas as pd

import helper_funcs
from Enum_vals import Section, Member, Code, Run
import Dimensions
import Forces
# import SCFs

from scipy.interpolate import interp2d
import numpy as np
import matplotlib.patches as mpatches
import matplotlib.lines as lines
from matplotlib import pyplot as plt

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

    @abstractmethod
    def calc_SCFs(self):
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

    def calc_SCFs(self):
        return K_SCF(self,self.run)

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

    def calc_SCFs(self):
        return T_SCF(self,self.run)

    def plot_geom(self,force: Forces.Forces):
        """
        Plot the geometry of the chord and brace members including centerlines.
        """
        x_chord = 0.5
        source_chord = pd.DataFrame({'x':np.array([-x_chord,x_chord]),
                                'y':np.array([-self.Dim_C.d/2,-self.Dim_C.d/2]),
                                'y2':np.array([self.Dim_C.d/2,self.Dim_C.d/2])})
        chord_rect = alt.Chart(source_chord).mark_area(opacity=0.6).encode(
                                    x='x',
                                    y='y',
                                    y2='y2',
                                    color=alt.value("#FF0000"))
        source_brace = pd.DataFrame({'x':np.array([-self.Dim_B.d/2,self.Dim_B.d/2]),
                                'y':np.array([self.Dim_C.d/2,self.Dim_C.d/2]),
                                'y2':np.array([self.Dim_C.d/2 + 0.5,self.Dim_C.d/2 + 0.5])})
        brace_rect = alt.Chart(source_brace).mark_area(opacity=0.6).encode(
                                    x='x',
                                    y='y',
                                    y2='y2',
                                    color=alt.value("#1f77b4"))
        return chord_rect + brace_rect

class SCFs(ABC):
    """Base class used for initialising above"""
    def __init__(self, run: Run = Run.SINGLE):
        """Calculate the stress concentration factors
        Values vary depending on Section type and whether a gap exists"""
        self.run = run
        self.SCF_ochax, self.SCF_obax, self.SCF_bax_min = None, None, None
        self.latex = None

    @abstractmethod
    def calc_stresses(self,force: Forces.Forces, MF_chord, MF_brace):
        pass

class K_SCF(SCFs):
    def __init__(self,Geom: K_joint, run: Run = Run.SINGLE):
        self.Geom = Geom
        super().__init__(run)

        if self.Geom.Dim_C.section_type is Section.CHS:
            beta_vals = [0.3,0.6]
            theta_vals = [30,45,60]
            SCF_ochax_vals = [[2.73,2.5],[3.18,2.83],[3.52,3.19]]
            SCF_obax_vals = [[1.45,1.15],[2.03,1.7],[2.5,2.08]]
            SCF_ochax_func = interp2d(beta_vals, theta_vals, SCF_ochax_vals, kind='linear')
            SCF_obax_func = interp2d(beta_vals,theta_vals, SCF_obax_vals, kind='linear')
            self.SCF_ochax = SCF_ochax_func(self.Geom.beta,self.Geom.theta*180/pi)[0]
            self.SCF_obax = SCF_obax_func(self.Geom.beta,self.Geom.theta*180/pi)[0]
            self.SCF_bax_min = np.interp(self.Geom.theta*180/pi,[30,45,60],[2.64,2.30,2.12])
            
            def SCF_func(beta,twogamma,tau,O_v,g_prime,theta,SCF_ochax, SCF_obax, SCF_bax_min):
                SCF_chax = max(2,(twogamma/24)**0.4 * (tau/0.5)**1.1 * SCF_ochax)
                SCF_bax = max(SCF_bax_min,sqrt(twogamma/24) * sqrt(tau/0.5) * SCF_obax)
                SCF_chch = max(2,1.2*(tau/0.5)**0.3 * sin(theta)**-0.9)
                return SCF_chax, SCF_bax, SCF_chch
        
        elif self.Geom.gap is True:
            def SCF_func(beta,twogamma,tau,O_v,g_prime,theta,SCF_ochax, SCF_obax, SCF_bax_min):
                chax_pt1 = 0.48 * beta - 0.5 * beta**2 - 0.012 / beta + 0.012 / g_prime
                chax_pt2 = twogamma**1.72 * tau**0.78 * g_prime**0.2 * sin(theta)**2.09
                bax_pt1 = -0.008 + 0.45 * beta - 0.34 * beta**2
                bax_pt2 = twogamma**1.36 * tau**(-0.66) * sin(theta)**1.29
                SCF_chax = max(chax_pt1 * chax_pt2,2.0) #Balanced Loading condition Chord Forces
                SCF_bax = max(bax_pt1 * bax_pt2,2.0) #Balanced Loading condition Brace Forces
                SCF_chch = max((2.45 + 1.23 * beta) * g_prime**-0.27,2.0) #Unbalanced loading condition Chord Forces
                return SCF_chax, SCF_bax, SCF_chch

        elif self.Geom.gap is False:
            def SCF_func(beta,twogamma,tau,O_v,g_prime,theta,SCF_ochax, SCF_obax, SCF_bax_min):
                chax_pt1 = 0.5+ 2.38 * beta - 2.87 * beta**2 + 2.18 * beta * O_v + 0.39 * O_v - 1.43 * sin(theta)
                chax_pt2 = twogamma**0.29 * tau**0.7 * O_v**(0.73-5.53*sin(theta)**2) * sin(theta)**(-0.4-0.08*O_v)
                bax_pt1 = 0.15 + 1.1 * beta - 0.48 * beta**2 - 0.14 / O_v
                bax_pt2 = twogamma**0.55 * tau**(-0.3) * O_v**(-2.57 + 1.62 * beta**2) * sin(theta)**0.31
                SCF_chax = max(chax_pt1 * chax_pt2,2.0) #Balanced Loading condition Chord Forces
                SCF_bax = max(bax_pt1 * bax_pt2,2.0) #Balanced Loading condition Brace Forces
                SCF_chch = max(1.2 + 1.46 * beta - 0.028 * beta**2,2.0) #Unbalanced loading condition Chord Forces
                return SCF_chax, SCF_bax, SCF_chch
        
        else:
            def SCF_func(beta,twogamma,tau,O_v,g_prime,theta,SCF_ochax, SCF_obax, SCF_bax_min):
                print("Error, no gap/overlap calculated")
                return None, None, None

        args = {
            'beta':self.Geom.beta,
            'twogamma':self.Geom.twogamma,
            'tau':self.Geom.tau,
            'O_v':self.Geom.O_v,
            'g_prime':self.Geom.g_prime,
            'theta':self.Geom.theta,
            'SCF_ochax':self.SCF_ochax,
            'SCF_obax':self.SCF_obax,
            'SCF_bax_min':self.SCF_bax_min}
            
        self.latex, (self.SCF_chax,
                                self.SCF_bax,
                                self.SCF_chch) = helper_funcs.func_by_run_type(self.run,args,SCF_func)

    def SCF_o_plot(self):
        if self.SCF_ochax is None:
            print("SCF_o values not calculated for RHS and SHS sections.")
            fig, (ax1, ax2) = plt.subplots(1,2)
            return fig
        else:
            #Create graph to visualise answer on graph
            fig, (ax1, ax2) = plt.subplots(1,2)
            SCF_ochax_img = plt.imread("data/SCFochax.png")
            SCF_obax_img = plt.imread("data/SCFobax.png")
            ax1.imshow(SCF_ochax_img, extent=[0, 1, 0, 4])
            ax2.imshow(SCF_obax_img, extent=[0, 1, 0, 4])
            ax1.set_title(r"$SCF_{o,ch,ax}$")
            ax2.set_title(r"$SCF_{o,b,ax}$")
            ax1.plot(self.Geom.beta,self.SCF_ochax,'ro')
            ax2.plot(self.Geom.beta,self.SCF_obax,'ro')
            ax1.set_aspect(0.25)
            ax2.set_aspect(0.25)
            return fig

    def calc_stresses(self,force: Forces.Forces, MF_chord, MF_brace):
        return Stress(self,force,MF_chord, MF_brace)

    # def SCF_ochax_bokeh(self):
    #     SCF_ochax_img = r"data/SCFochax.png"
    #     SCF_obax_img = r"data/SCFobax.png"
    #     SCF_ochax_src = ColumnDataSource(dict(url = [SCF_ochax_img]))
    #     SCF_obax_src = ColumnDataSource(dict(url = [SCF_obax_img]))
    #     x_range = (-20,-10) # could be anything - e.g.(0,1)
    #     y_range = (20,30)
    #     p = figure(match_aspect=True,x_range=x_range, y_range=y_range)
    #     p.image_url(url='url', x=x_range[0],y=y_range[1],w=x_range[1]-x_range[0],h=y_range[1]-y_range[0],source=SCF_ochax_src)
    #     ## could also leave out keywords
    #     # p.image_url(['tree.png'], 0, 1, 0.8, h=0.6) 
    #     doc = curdoc()
    #     doc.add_root(p)
    #     st.bokeh_chart(p)

class T_SCF(SCFs):
    def __init__(self,Geom: T_joint, run: Run = Run.SINGLE):
        self.Geom = Geom
        super().__init__(run)

        if self.Geom.Dim_C.section_type is Section.CHS:
            args = {
            'beta':self.Geom.beta,
            'gamma':self.Geom.twogamma / 2,
            'tau':self.Geom.tau,
            'theta':self.Geom.theta,
            'alpha':self.Geom.alpha,
            'C_1':self.Geom.C_1,
            'C_2':self.Geom.C_2,
            'C_3':self.Geom.C_3}

            def SCF_func(beta, gamma, tau, theta, alpha, C_1, C_2, C_3):
                F_2 = 1 - (1.43 * beta - 0.97 * beta**2 - 0.03) * gamma**0.04 * exp(-0.71 * gamma**-1.38 * alpha**2.5)
                T_3 = 1.3 + gamma * tau**0.52 * alpha**0.1 * (0.187 - 1.25 * beta**1.1 * (beta - 0.96)) * sin(theta)**(2.7 - 0.01 * alpha)
                T_5 = gamma * tau**1.1 * (1.11 - 3 * (beta - 0.52)**2) * sin(theta)**1.6 + C_1 * (0.8 * alpha - 6) * tau * beta**2 * sqrt(1 - beta**2) * sin(2 * theta)**2
                T_6 = gamma**0.2 * tau * (2.65 + 5 * (beta - 0.65)**2) + tau * beta * (C_2 * alpha - 3) * sin(theta)
                T_7 = 3 + gamma**1.2 * (0.12 * exp(-4 * beta) + 0.011 * beta**2 - 0.045) + beta * tau * (C_3*alpha - 1.2)
                T_8 = 1.45 * beta * tau**0.85 * gamma**(1-0.68 * beta) * sin(theta)**0.7
                T_9 = 1 + 0.65 * beta * tau**0.4 * gamma**(1.09 - 0.77 * beta) * sin(theta)**(0.06 * gamma - 1.16)
                F_3 = 1 - 0.55 * beta**1.8 * gamma**0.16 * exp(-0.49 * gamma**-0.89 * alpha**1.8)
                T_10 = gamma * tau * beta * (1.7 - 1.05 * beta**3) * sin(theta)**1.6
                T_11 = gamma**0.95 * tau**0.46 * beta * (1.7 - 1.05 * beta**3) * (0.99 - 0.47 * beta + 0.08 * beta**4) * sin(theta)**1.6
                SCF_bsaddleax = T_3 * F_2
                SCF_chsaddleax = T_5 * F_2
                SCF_chcrownax = T_6 * 1
                SCF_bcrownax = T_7 * 1
                SCF_chcrownipb = T_8 * 1
                SCF_bcrownipb = T_9 * 1
                SCF_chsaddleopb = T_10 * F_3
                SCF_bsaddleopb = T_11 * F_3

                return SCF_bsaddleax, SCF_chsaddleax, SCF_chcrownax, SCF_bcrownax, SCF_chcrownipb, SCF_bcrownipb, SCF_chsaddleopb, SCF_bsaddleopb

            self.latex, (self.SCF_bsaddleax,
                             self.SCF_chsaddleax,
                             self.SCF_chcrownax,
                             self.SCF_bcrownax,
                             self.SCF_chcrownipb,
                             self.SCF_bcrownipb,
                             self.SCF_chsaddleopb,
                             self.SCF_bsaddleopb) = helper_funcs.func_by_run_type(self.run,args,SCF_func)
        elif self.Geom.Dim_C.section_type is not Section.CHS:
            print("Method not implemented")

    def SCF_o_plot(self):
        """Empty method as SCF_o_plot not initialised"""
        if self.SCF_ochax is None:
            print("SCF_o values not calculated for RHS and SHS sections.")
            fig, (ax1, ax2) = plt.subplots(1,2)
            return fig

    def calc_stresses(self,force: Forces.Forces, MF_chord, MF_brace):
        return Stress(self,force,MF_chord, MF_brace)

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

def st_SCF_op_picker(self):
    self.SCF_ch_op = st.sidebar.number_input("SCF_ch_op Input",min_value=1.0,max_value=10.0,value=2.0,step=0.1)
    self.SCF_br_op = st.sidebar.number_input("SCF_br_op Input",min_value=1.0,max_value=10.0,value=2.0,step=0.1)

class Stress:
    def __init__(self, SCF,
                       forces: Forces.Forces, 
                       MF_chord,
                       MF_brace):
        args = {'MF_chord':MF_chord,
                'MF_brace':MF_brace,
                'A_chord':SCF.Geom.Dim_C.area * u.m**2, #type: ignore
                'A_brace':SCF.Geom.Dim_B.area* u.m**2, #type: ignore
                'y_chord':SCF.Geom.Dim_C.d * u.m / 2, #type:ignore
                'Ix_chord':SCF.Geom.Dim_C.Ix * u.m**4, #type:ignore
                'P_brace':forces.P_brace * u.N, #type: ignore
                'P_chord':forces.P_chord * u.N, #type: ignore
                'Mip_chord':forces.M_ip_chord * u.N * u.m, #type: ignore
                'theta':SCF.Geom.theta,
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

        self.latex, (self.S_rhschord,
                                self.S_rhsbrace
                                ) = helper_funcs.func_by_run_type(SCF.Geom.run, args, stress_func)


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

# def st_forces_picker():
#     """Create Force Inputs via a Streamlit input function"""
#     st.sidebar.subheader("Force Inputs:")
#     P_chord = st.sidebar.number_input("P_chord (kN)",value=70.0,step=10.0) * 1000 #N
#     P_brace = st.sidebar.number_input("P_brace (kN)",value=50.0,step=10.0) * 1000 #N
#     M_op_chord = st.sidebar.number_input("M_op_chord (kNm)",value=5.0,step=10.0) * 1000 #Nm
#     M_ip_chord = st.sidebar.number_input("M_ip_chord (kNm)",value=5.0,step=10.0) * 1000 #Nm
#     M_op_brace = st.sidebar.number_input("M_op_brace (kNm)",value=5.0,step=10.0) * 1000 #Nm
#     return P_chord, P_brace, M_op_chord, M_ip_chord, M_op_brace