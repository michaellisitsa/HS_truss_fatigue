#Import streamlit modules
import streamlit as st

#Import associated py files with functions
import functions as fnc
import validation as vld
import plots


#Import data and plotting
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

#Allow horizontal stacking plots
from bokeh.layouts import row

#Import unit aware modules
import forallpeople as u
u.environment('structural')

import math
import time


def inputs(srun: bool):
    """This function is run at each launch of streamlit"""
    #Create Title Markdown
    st.title("CIDECT-8 Fatigue - K-joint Trusses")
    st.markdown("The purpose of this worksheet is to determine the allowable stresses at the K-Joints of the trusses.\n\
        The CIDECT 8 design guide is adopted. It can be downloaded at: https://www.cidect.org/design-guides/")

    #Create Menu for various options
    vld.input_description("Click here to add custom description, sketch or image")    

    #Create section picker in streamlit sidebar
    st.sidebar.markdown("## Hollow Section Sizes")
    code = st.sidebar.radio("Which code:",["AS","EN"])
    chord_type = st.sidebar.radio("Choose Type of Chord:",("SHS","RHS","CHS"),index=0)
    chord_table = vld.load_data(code,chord_type)
    if srun:
        reverse_axes_chord, hs_chosen_chord = vld.hs_lookup(chord_type,"chord",chord_table)
        chord_props = vld.hs_populate(reverse_axes_chord, hs_chosen_chord,srun)
    else:
        reverse_axes_chord = False
        chord_df = vld.hs_populate(reverse_axes_chord, chord_table,srun)
        chord_props = []
        for b,h,t,area,I_x,I_y in zip(chord_df[0],chord_df[1],chord_df[2],chord_df[3],chord_df[4],chord_df[5]):
            chord_props.append((b,h,t,area,I_x,I_y))
    if chord_type == "CHS":
        st.sidebar.markdown("Choose Size of Brace")
        brace_type = "CHS"
    else:
        brace_type = st.sidebar.radio("Choose Type of Brace:",("SHS","RHS"))
    brace_table = vld.load_data(code,brace_type)
    if srun:
        reverse_axes_brace, hs_chosen_brace = vld.hs_lookup(brace_type,"brace",brace_table)
        brace_props = vld.hs_populate(reverse_axes_brace, hs_chosen_brace, srun)
    else:
        reverse_axes_brace = False
        brace_df = vld.hs_populate(reverse_axes_brace, brace_table,srun)
        brace_props = []
        for b,h,t,area,I_x,I_y in zip(brace_df[0],brace_df[1],brace_df[2],brace_df[3],brace_df[4],brace_df[5]):
            brace_props.append((b,h,t,area,I_x,I_y))
    #Create Truss geometry input in streamlit sidebar
    st.sidebar.markdown('## Truss Geometry:')
    if chord_type == "CHS":
        e = 0
    else:
        e = st.sidebar.number_input('Eccentricity',-400,400,-100,step=5,format='%f') / 1000
    chordspacing = st.sidebar.number_input('Chord spacing (mm)',100,4000,2000,step=50,format='%i') / 1000
    L_chord = st.sidebar.number_input('Length of Chord (mm)',100,30000,8000,step=100,format='%i') / 1000
    div_chord = st.sidebar.number_input('Chord divisions',1,20,4,step=1,format='%i')

    #Create Force Inputs
    st.sidebar.markdown('## Input Forces')
    P_chord = st.sidebar.number_input("P_chord (kN)",value=70.0,step=10.0)
    P_brace = st.sidebar.number_input("P_brace (kN)",value=50.0,step=10.0)
    M_ip_chord = st.sidebar.number_input("M_ip_chord (kNm)",value=5.0,step=10.0)
    M_op_chord = st.sidebar.number_input("M_op_chord (kNm)",value=5.0,step=10.0)
    M_op_brace = st.sidebar.number_input("M_op_brace (kNm)",value=5.0,step=10.0)

    #Create max stress
    st.sidebar.markdown('## Allowable Stress')
    sigma_max = st.sidebar.number_input("$sigma_{MAX}$ (MPa)",value=24.0,step=1.0)

    #SCF out of plane
    st.sidebar.markdown('## SCF Manual input')
    SCF_ch_op = st.sidebar.number_input("SCF_ch_op Input",min_value=1.0,max_value=10.0,value=2.0,step=0.1)
    SCF_br_op = st.sidebar.number_input("SCF_br_op Input",min_value=1.0,max_value=10.0,value=2.0,step=0.1)
    return (chord_type,chord_props,brace_props,
            e,chordspacing,L_chord,div_chord,
            P_chord,P_brace,M_ip_chord,M_op_chord,M_op_brace,
            sigma_max,SCF_ch_op,SCF_br_op)

def main(srun: bool,chord_type,chord_props,brace_props,
                    e,chordspacing,L_chord,div_chord,
                    P_chord,P_brace,M_ip_chord,M_op_chord,M_op_brace,
                    sigma_max,SCF_ch_op,SCF_br_op):
    #Unpack section properties
    b0,h0,t0,A_chord,Ix_chord,Iy_chord = chord_props
    b1,h1,t1,A_brace,Ix_brace,Iy_brace = brace_props
    #Calculate overlap and Plot geometry and check eccentricity and angle
    #Calculate Dimensional parameters beta, gamma, tau, and check angle, eccentricity, if gap
    if srun: overlap_latex, (Ov,theta,g_prime) = fnc.overlap_hc(L_chord*u.m,chordspacing*u.m,div_chord,e*u.m,h0*u.m,h1*u.m,t0*u.m)
    else:                      (Ov,theta,g_prime) = fnc.overlap(L_chord*u.m,chordspacing*u.m,div_chord,e*u.m,h0*u.m,h1*u.m,t0*u.m)
    if srun: dim_params_latex, (beta, twogamma, tau) = fnc.dim_params_hc(b0=b0*u.m,t0=t0*u.m,b1=b1*u.m,t1=t1*u.m,chord_type=chord_type)
    else:                         (beta, twogamma, tau) = fnc.dim_params(b0=b0*u.m,t0=t0*u.m,b1=b1*u.m,t1=t1*u.m,chord_type=chord_type)
    success, message, gap = fnc.check_angle_ecc_gap(chord_type,theta,e,h0,Ov,g_prime,tau)
    tau_min,tau_max,beta_min,beta_max,twogamma_min,twogamma_max = fnc.dim_limits(chord_type)
    if (beta_min <= beta <= beta_max
        and twogamma_min <= twogamma <= twogamma_max
        and tau_min <= tau <= tau_max):
        dim_success = True
    else:
        dim_success = False
    #Single run outputs
    if srun:
        #Create a container at the top of the page for plotting graphs
        st.header("Results Summary")
        geom_container = st.beta_container()
        res_col1, res_col2, res_col3 = st.beta_columns(3)
        results_container = st.beta_container()
        #Expander showing how calculations done
        st.write('## Calculate overlap')
        vld.overlap_sketch()
        #Overlap and geometry plots
        st.latex(overlap_latex)
        c_geo = plots.geom_plot_altair(h0,theta,g_prime,t0,h1,e,chord_type)
        geom_container.altair_chart(c_geo)
        # fig2, ax2 = plots.geom_plot(h0,theta,g_prime,t0,h1,e,chord_type)
        # geom_container.pyplot(fig2)
        #Render equations and helper drawing
        st.write('## Dimensional Parameters')
        vld.geometry_sketch()
        st.latex(dim_params_latex)
        #Output or stop script for angle, eccentricity, gap checks
        if success:
            geom_container.success(message)
        else:
            geom_container.error(message)
            st.stop()

        #Plot dimensional parameters using Altair
        beta_plot = plots.dim_params_altair('b0',b0*1000,'b1',b1*1000,'β',
                                    beta_min,beta_max,500)
        twogamma_plot = plots.dim_params_altair('t0',t0*1000,'b0',b0*1000,'2γ',
                                    twogamma_min,twogamma_max,20)
        tau_plot = plots.dim_params_altair('t0',t0*1000,'t1',t1*1000,'τ',
                                    tau_min,tau_max,20)
        res_col1.altair_chart(beta_plot, use_container_width=True)
        res_col2.altair_chart(twogamma_plot, use_container_width=True)
        res_col3.altair_chart(tau_plot, use_container_width=True)
        
        #Output or stop script whether dimension parameters are exceeded
        if dim_success:
            results_container.success("PASS - Dimensions are within allowable limits")
        else:
            results_container.error("FAIL - Dimensional Parameters exceeded.")
            st.stop()    

        #Calculate SCF values
        st.markdown("""## SCF Calculations
        The follow calculations determine the Stress Concentration Factors (SCF) for each:
        - LC1 chord -> $SCF_{ch,ax}$
        - LC1 brace -> $SCF_{b,ax}$
        - LC2 chord -> $SCF_{ch,ch}$""")

    #Calculate stress concentration factors
    if chord_type=="CHS":
        try:
            SCF_ochax, SCF_obax, SCF_bax_min = fnc.SCFochax_func(beta,theta)
        except:
            SCF_ochax , SCF_obax, SCF_bax_min = 2, 2, 2
        if srun: SCF_chaxbax_latex, (SCF_chax,SCF_bax,SCF_chch) = fnc.SCF_chaxbaxchch_chs_hc(twogamma/2,tau,theta,
                                        SCF_ochax[0],SCF_obax[0],SCF_bax_min)
        else:                          (SCF_chax,SCF_bax,SCF_chch) = fnc.SCF_chaxbaxchch_chs(twogamma/2,tau,theta,
                                        SCF_ochax[0],SCF_obax[0],SCF_bax_min)
        if srun:
            fig4, ax4 = plots.SCF_ochax_plot(beta,SCF_ochax,SCF_obax)
            st.pyplot(fig4)
            st.latex(SCF_chaxbax_latex)
    elif gap:
        if srun: SCF_latex_rhs, (SCF_chax, SCF_bax, SCF_chch) = fnc.SCF_gap_rhs_hc(beta,twogamma,tau,g_prime,theta)
        else:                       (SCF_chax, SCF_bax, SCF_chch) = fnc.SCF_gap_rhs(beta,twogamma,tau,g_prime,theta)
        if srun:
            st.header("GAP JOINT: $2 \cdot tau <= g^\prime$")
            st.latex(SCF_latex_rhs)
    else:
        if srun: SCF_latex_rhs, (SCF_chax,SCF_bax,SCF_chch) = fnc.SCF_overlap_rhs_hc(beta,twogamma,tau,Ov,theta)
        else:                    (SCF_chax,SCF_bax,SCF_chch) = fnc.SCF_overlap_rhs(beta,twogamma,tau,Ov,theta)
        if srun:
            st.header("OVERLAP JOINT: $0.5 <= O_v <= 1.0$:")
            st.latex(SCF_latex_rhs)

    #Calculate all stresses
    if srun: chord_ax_stresses_latex, (sigma_chord1P, sigma_chord2P) = fnc.chord_ax_stresses_hc(SCF_chax, SCF_chch,P_brace * u.kN,P_chord * u.kN,
                                                            theta, A_chord * u.m**2, A_brace * u.m**2)          
    else:       (sigma_chord1P, sigma_chord2P) = fnc.chord_ax_stresses(SCF_chax, SCF_chch,P_brace * u.kN,P_chord * u.kN,
                                                            theta, A_chord * u.m**2, A_brace * u.m**2)  
    if srun:    chord_BM_stresses_latex, (sigma_chordM_ip, sigma_chordM_op) = fnc.chord_BM_stresses_hc(h0*u.m,b0*u.m,b1*u.m,SCF_chch,SCF_ch_op,
                                            M_ip_chord * u.kN * u.m,M_op_chord * u.kN * u.m,
                                            Ix_chord * 10**6 * u.m**4,Iy_chord * 10**6 * u.m**4)
    else:                                 (sigma_chordM_ip, sigma_chordM_op) = fnc.chord_BM_stresses(h0*u.m,b0*u.m,b1*u.m,SCF_chch,SCF_ch_op,
                                            M_ip_chord * u.kN * u.m,M_op_chord * u.kN * u.m,
                                            Ix_chord * 10**6 * u.m**4,Iy_chord * 10**6 * u.m**4)
    if srun: brace_stresses_latex, (sigma_brace_1P, sigma_braceM_op) = fnc.brace_stresses_hc(b1 * u.m, SCF_bax,
                                                            P_brace * u.kN,A_brace * u.m**2,SCF_br_op,
                                                            M_op_brace * u.kN * u.m,Iy_brace * 10**6 * u.m**4)
    else:                           (sigma_brace_1P, sigma_braceM_op) = fnc.brace_stresses(b1 * u.m, SCF_bax,
                                                            P_brace * u.kN,A_brace * u.m**2,SCF_br_op,
                                                            M_op_brace * u.kN * u.m,Iy_brace * 10**6 * u.m**4)
    if srun: cum_stresses_latex, (sigma_chord, sigma_brace) = fnc.cum_stresses_hc(sigma_chord1P,sigma_chord2P,sigma_chordM_ip,
                                                                    sigma_chordM_op,sigma_brace_1P,sigma_braceM_op)
    else:                     (sigma_chord, sigma_brace) = fnc.cum_stresses(sigma_chord1P,sigma_chord2P,sigma_chordM_ip,
                                                                    sigma_chordM_op,sigma_brace_1P,sigma_braceM_op)
    if sigma_chord <= sigma_max * u.MPa and sigma_brace <= sigma_max * u.MPa:
        success_stress = True
    else:
        success_stress = False

    if srun:
        st.write("### Axial Stresses - Chord")
        st.latex(chord_ax_stresses_latex)
        #Calculate Stresses:
        st.markdown("""## Nominal Stress Ranges

        Nominal stresses are obtained by getting:
        - principal stresses 
        - outer fiber bending stresses of each element defined in Sec 3.3.

        ### Axial Stresses - Chord""")
        st.write("### Bending Moment Stresses - Chord")
        st.latex(chord_BM_stresses_latex)
        st.write("### Stresses - Brace")
        st.latex(brace_stresses_latex)
        st.markdown("### TOTAL Stresses")
        st.latex(cum_stresses_latex)
        #Stresses Bar Charts
        fig1, ax1 = plots.bar_chart(sigma_chord1P.value*10**-6, 
                                sigma_chord2P.value*10**-6, 
                                sigma_chordM_ip.value*10**-6, 
                                sigma_chordM_op.value*10**-6,
                                sigma_brace_1P.value*10**-6, 
                                sigma_braceM_op.value*10**-6,
                                sigma_max)
        results_container.pyplot(fig1)
        #Check for stresses and output message
        if success_stress:
            results_container.success("PASS - Stresses are within allowable limits")
        else:
            results_container.error("FAIL - Stresses exceed allowable limits")
    return sigma_chord.value, sigma_brace.value
    
if __name__ == '__main__':
    start = time.time()
    runtime = st.empty()
    results = st.sidebar.checkbox("CHECKED: Choose Size\n UNCHECKED: All Sizes (experimental)",value=True)
    if results:
        (chord_type,chord_props,brace_props,
            e,chordspacing,L_chord,div_chord,
            P_chord,P_brace,M_ip_chord,M_op_chord,M_op_brace,
            sigma_max,SCF_ch_op,SCF_br_op) = inputs(results)
        main(results,chord_type,chord_props,brace_props,
                        e,chordspacing,L_chord,div_chord,
                        P_chord,P_brace,M_ip_chord,M_op_chord,M_op_brace,
                        sigma_max,SCF_ch_op,SCF_br_op)
    else:
        (chord_type,chord_props,brace_props,
            e,chordspacing,L_chord,div_chord,
            P_chord,P_brace,M_ip_chord,M_op_chord,M_op_brace,
            sigma_max,SCF_ch_op,SCF_br_op) = inputs(results)
        lin_sigma_chord = []
        lin_sigma_brace = []
        chord_ind = []
        brace_ind = []
        for ch in chord_props:
            for br in brace_props:
                if br[0]<=ch[0]:
                    sigma_chord, sigma_brace = main(results,chord_type,ch,br,
                                e,chordspacing,L_chord,div_chord,
                                P_chord,P_brace,M_ip_chord,M_op_chord,M_op_brace,
                                sigma_max,SCF_ch_op,SCF_br_op)
                    #st.text(f"Chord: {ch[0]*1000,ch[1]*1000,ch[2]*1000}\n"
                    #        f"Brace: {br[0]*1000,br[1]*1000,br[2]*1000}\n"
                    #        f"sigma_chord = {sigma_chord/1e6:.2f}MPa\n"
                    #        f"sigma_brace = {sigma_brace/1e6:.2f}MPa")
                    lin_sigma_chord.append(sigma_chord/1e6)
                    lin_sigma_brace.append(sigma_brace/1e6)
                    chord_ind.append([ch[0],ch[1],ch[2]])
                    brace_ind.append([br[0],br[1],br[2]])
        plots.bokeh_interactive(lin_sigma_chord, lin_sigma_brace,sigma_max,chord_ind,brace_ind)
    end = time.time()
    runtime.write(f'Runtime: {end-start:.2f}s')
