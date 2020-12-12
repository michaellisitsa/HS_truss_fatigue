#Import streamlit modules
import streamlit as st

#Import associated py files with functions
import functions as fnc
import validation as vld
import plots

#Import data and plotting
import pandas as pd
import matplotlib.pyplot as plt

#Import unit aware modules
import forallpeople as u
u.environment('structural')

import math

#Main function calls made at each run of Streamlit
def main(ind_chord_type):
    """This function is run at each launch of streamlit"""
    #Create Title Markdown
    st.title("CIDECT-8 Fatigue - K-joint Trusses")
    st.markdown("The purpose of this worksheet is to determine the allowable stresses at the K-Joints of the trusses.\n\
        The CIDECT 8 design guide is adopted. It can be downloaded at: https://www.cidect.org/design-guides/")

    #Create Menu for various options
    vld.input_description("Click here to add custom description, sketch or image")
    # Out of order Results Summary
    st.header("Results Summary")
    results_container = st.beta_container()

    #Create section picker in streamlit sidebar
    st.sidebar.markdown("## Hollow Section Sizes")
    chord_type = st.sidebar.radio("Choose Type of Chord:",("SHS","RHS","CHS"),index=ind_chord_type)
    b0,h0,t0,A_chord,Ix_chord,Iy_chord = vld.hs_lookup(chord_type,"chord")
    if chord_type == "CHS":
        st.sidebar.markdown("Choose Size of Brace")
        brace_type = "CHS"
    else:
        brace_type = st.sidebar.radio("Choose Type of Brace:",("SHS","RHS"))
    b1,h1,t1,A_brace,Ix_brace,Iy_brace = vld.hs_lookup(brace_type,"brace")

    #Create Truss geometry input in streamlit sidebar
    st.sidebar.markdown('## Truss Geometry:')
    if chord_type == "CHS":
        e = 0
    else:
        e = st.sidebar.slider('Eccentricity',-400,400,-100,step=5,format='%f') / 1000
    chordspacing = st.sidebar.slider('Chord spacing (mm)',100,4000,2000,step=50,format='%i') / 1000
    L_chord = st.sidebar.slider('Length of Chord (mm)',100,30000,8000,step=100,format='%i') / 1000
    div_chord = st.sidebar.slider('Chord divisions',1,20,4,step=1,format='%i')

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

    #Show overlap images
    st.write('## Calculate overlap')
    with st.beta_expander("Expand for sketch describing overlap calculations:"):
        st.image(r"data/overlap_calculation.png",use_column_width=True)
        st.image(r"data/gap_calculation.jpg",use_column_width=True)

    #Create a container at the top of page to put results summaries into.
    st.beta_container()

    #Calculate overlap and display LATEX
    overlap_latex, overlap_outputs = fnc.overlap(L_chord*u.m,chordspacing*u.m,div_chord,e*u.m,h0*u.m,h1*u.m,t0*u.m)
    Ov,theta,g_prime = overlap_outputs
    st.latex(overlap_latex)

    #Plot geometry and check eccentricity and angle
    fig2, ax2 = plots.geom_plot(h0,theta,g_prime,t0,h1,e,chord_type)
    results_container.pyplot(fig2)
    if chord_type=="CHS":
        if 30*math.pi/180 < theta < 60 * math.pi/180:
            results_container.success("PASS - Brace angle within allowable limits")
        else:
            results_container.error("FAIL - Angle exceeded.")
            st.stop()
    else:
        if -0.55 <= e/h0 <= 0.25:
            if 30*math.pi/180 < theta < 60 * math.pi/180:
                results_container.success("PASS - Brace angle and eccentricity within allowable limits")
            else:
                results_container.error("FAIL - Angle exceeded.")
                st.stop()
        else:
            if 30*math.pi/180 < theta < 60 * math.pi/180:
                results_container.error("FAIL - Eccentricity exceeds allowable offset from chord centroid")
            else:
                results_container.error("FAIL - Eccentricity and Angle exceeded.")
                st.stop()
            
            st.stop()
        #If overlap is exceeding, end calculation
        if 0 < Ov < 0.5:
            st.error("Calculation terminated refer Results Summary for errors")
            fig2, ax2 = plots.geom_plot(h0,theta,g_prime,t0,h1,e,chord_type)
            results_container.error("Overlap is NOT ACCEPTABLE (between 0% to 50%)")
            results_container.error("Try amending eccentricity, or truss dimensions")
            st.stop()

    #Calculate Dimensional parameters beta, gamma and tau
    st.write('## Dimensional Parameters')
    with st.beta_expander("Expand for sketch describing truss dimensions:"):
        st.image(r"data/geometric_parameters.png",use_column_width=True)
    dim_params_latex, dim_params = fnc.dim_params(b0=b0*u.m,t0=t0*u.m,b1=b1*u.m,t1=t1*u.m,chord_type=chord_type)
    st.latex(dim_params_latex)
    beta, twogamma, tau = dim_params

    #Set limits for beta, gamma and tau
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

    #If gap is too small, end calculation
    if chord_type=="CHS":
        pass
    elif 0 <= g_prime <= 2 * tau:
        st.error("Calculation terminated refer Results Summary for errors")
        fig2, ax2 = plots.geom_plot(h0,theta,g_prime,t0,h1,e,chord_type)
        results_container.error("Gap to chord thick ratio IS NOT ACCEPTABLE $g^\prime < 2 \cdot tau$")
        results_container.error("Increase the gap between members, or overlap by at least 50%")
        st.stop()

    #Plot dimension parameters
    fig,ax = plots.dim_params_plot(b0*1000,t0*1000,b1*1000,t1*1000,chord_type,
                                beta_min,beta_max,twogamma_min,twogamma_max,tau_min,tau_max)
    results_container.pyplot(fig)
    # dimensions checks plotted at top of document

    #Check whether dimension parameters are exceeded and end script
    if (beta_min <= beta <= beta_max
        and twogamma_min <= twogamma <= twogamma_max
        and tau_min <= tau <= tau_max):
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
        SCF_ochax, SCF_obax, SCF_bax_min, fig4, ax4 = fnc.SCFochax_func(beta,theta)
        st.pyplot(fig4)
        SCF_chaxbax_latex, SCF_chaxbax_vals = fnc.SCF_chaxbaxchch_chs(twogamma/2,tau,theta,
                                        SCF_ochax[0],SCF_obax[0],SCF_bax_min)
        SCF_chax,SCF_bax,SCF_chch = SCF_chaxbax_vals
        st.latex(SCF_chaxbax_latex)
    elif 0.5 <= Ov <= 1.0:
        st.header("OVERLAP JOINT: $0.5 <= O_v <= 1.0$:")
        st.write("### $SCF_{chax}$")
        SCF_chax_latex, SCF_chax = fnc.SCF_chax_overlap(beta,twogamma,tau,Ov,theta)
        st.latex(SCF_chax_latex)
        st.write("### $SCF_{bax}$")
        SCF_bax_latex, SCF_bax = fnc.SCF_bax_overlap(beta,twogamma,tau,Ov,theta)
        st.latex(SCF_bax_latex)
        st.write("### $SCF_{chch}$")
        SCF_chch_latex,SCF_chch = fnc.SCF_chch_overlap(beta)
        st.latex(SCF_chch_latex)
    elif 2 * tau <= g_prime:
        st.header("GAP JOINT: $2 \cdot tau <= g^\prime$")
        st.write("### $SCF_{chax}$")
        SCF_chax_latex, SCF_chax = fnc.SCF_chax_gap(beta,twogamma,tau,g_prime,theta)
        st.latex(SCF_chax_latex)
        st.write("### $SCF_{bax}$")
        SCF_bax_latex, SCF_bax = fnc.SCF_bax_gap(beta,twogamma,tau,theta)
        st.latex(SCF_bax_latex)
        st.write("### $SCF_{chch}$")
        SCF_chch_latex,SCF_chch = fnc.SCF_chch_gap(beta,g_prime)
        st.latex(SCF_chch_latex)

    #Calculate Stresses:
    st.markdown("""## Nominal Stress Ranges

    Nominal stresses are obtained by getting:
    - principal stresses 
    - outer fiber bending stresses of each element defined in Sec 3.3.

    ### Axial Stresses - Chord""")

    chord_ax_stresses_latex, chord_ax_stresses = fnc.chord_ax_stresses(SCF_chax,
                                                                        SCF_chch,
                                                                        P_brace * u.kN,
                                                                        P_chord * u.kN,
                                                                        theta,
                                                                        A_chord * u.m**2,
                                                                        A_brace * u.m**2)
    st.latex(chord_ax_stresses_latex)
    sigma_chord1P, sigma_chord2P = chord_ax_stresses

    st.write("### Bending Moment Stresses - Chord")
    chord_BM_stresses_latex, chord_BM_stresses = fnc.chord_BM_stresses(
            h0*u.m,b0*u.m,b1*u.m,SCF_chch,SCF_ch_op,
            M_ip_chord * u.kN * u.m,M_op_chord * u.kN * u.m,
            Ix_chord * 10**6 * u.m**4,Iy_chord * 10**6 * u.m**4)
    st.latex(chord_BM_stresses_latex)
    sigma_chordM_ip, sigma_chordM_op = chord_BM_stresses

    st.write("### Stresses - Brace")
    brace_stresses_latex, brace_stresses = fnc.brace_stresses(b1 * u.m, 
                                                            SCF_bax,
                                                            P_brace * u.kN,
                                                            A_brace * u.m**2,
                                                            SCF_br_op,
                                                            M_op_brace * u.kN * u.m,
                                                            Iy_brace * 10**6 * u.m**4)
    st.latex(brace_stresses_latex)
    sigma_brace_1P, sigma_braceM_op = brace_stresses

    #Cumulative Stresses
    cum_stresses_latex, cum_stresses = fnc.cum_stresses(sigma_chord1P,
                    sigma_chord2P,
                    sigma_chordM_ip,
                    sigma_chordM_op,
                    sigma_brace_1P,
                    sigma_braceM_op)
    sigma_chord, sigma_brace = cum_stresses
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

    #Results Summary in sidebar
    results_container.pyplot(fig1)
    if sigma_chord <= sigma_max * u.MPa and sigma_brace <= sigma_max * u.MPa:
        results_container.success("PASS - Stresses are within allowable limits")
    else:
        results_container.error("FAIL - Stresses exceed allowable limits")
    
    return sigma_chord.value
    
if __name__ == '__main__':
    main(ind_chord_type=0)