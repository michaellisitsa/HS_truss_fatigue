from numpy.lib.type_check import imag
import streamlit as st

from handcalcs import handcalc
from Enum_vals import Section, Member, Code, Run, Joint
import helper_funcs

import forallpeople as u
u.environment('structural')

from math import sin, cos, tan, atan, pi, sqrt, exp
from scipy.interpolate import interp2d
import numpy as np
import matplotlib.patches as mpatches
import matplotlib.lines as lines
from matplotlib import pyplot as plt

from bokeh.models import ColumnDataSource, Grid, LinearAxis, Plot
from bokeh.plotting import figure, show, output_file, curdoc

from typing import Union, Type

import Dimensions
import Geometry

class SCFs:
    def __init__(self, run: Run = Run.SINGLE):
        """Calculate the stress concentration factors
        Values vary depending on Section type and whether a gap exists"""
        self.run = run
        self.SCF_ochax, self.SCF_obax, self.SCF_bax_min = None, None, None
        self.latex = None

class K_SCF(SCFs):
    def __init__(self,Geom: Geometry.K_joint, run: Run = Run.SINGLE):
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
    def __init__(self,Geom: Geometry.T_joint, run: Run = Run.SINGLE):
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


def st_SCF_op_picker(self):
    self.SCF_ch_op = st.sidebar.number_input("SCF_ch_op Input",min_value=1.0,max_value=10.0,value=2.0,step=0.1)
    self.SCF_br_op = st.sidebar.number_input("SCF_br_op Input",min_value=1.0,max_value=10.0,value=2.0,step=0.1)