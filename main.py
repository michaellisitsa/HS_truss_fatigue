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

def run_type(srun: bool):
    pass

#Main function calls made at each run of Streamlit
def main(ind_chord_type,srun: bool):
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
    chord_type = st.sidebar.radio("Choose Type of Chord:",("SHS","RHS","CHS"),index=ind_chord_type)
    reverse_axes_chord, hs_chosen_chord = vld.hs_lookup(chord_type,"chord",code)
    b0,h0,t0,A_chord,Ix_chord,Iy_chord = vld.hs_populate(reverse_axes_chord, hs_chosen_chord)
    if chord_type == "CHS":
        st.sidebar.markdown("Choose Size of Brace")
        brace_type = "CHS"
    else:
        brace_type = st.sidebar.radio("Choose Type of Brace:",("SHS","RHS"))
    reverse_axes_brace, hs_chosen_brace = vld.hs_lookup(brace_type,"brace",code)
    b1,h1,t1,A_brace,Ix_brace,Iy_brace = vld.hs_populate(reverse_axes_brace, hs_chosen_brace)

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


    #Calculate overlap and Plot geometry and check eccentricity and angle
    #Calculate Dimensional parameters beta, gamma, tau, and check angle, eccentricity, if gap
    overlap_latex, (Ov,theta,g_prime) = fnc.overlap(L_chord*u.m,chordspacing*u.m,div_chord,e*u.m,h0*u.m,h1*u.m,t0*u.m)
    dim_params_latex, (beta, twogamma, tau) = fnc.dim_params(b0=b0*u.m,t0=t0*u.m,b1=b1*u.m,t1=t1*u.m,chord_type=chord_type)
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
        results_container = st.beta_container()
        #Expander showing how calculations done
        st.write('## Calculate overlap')
        with st.beta_expander("Expand for sketch describing overlap calculations:"):
            st.image(r"data/overlap_calculation.png",use_column_width=True)
            st.image(r"data/gap_calculation.jpg",use_column_width=True)
        #Overlap and geometry plots
        st.latex(overlap_latex)
        fig2, ax2 = plots.geom_plot(h0,theta,g_prime,t0,h1,e,chord_type)
        results_container.pyplot(fig2)
        #Render equations and helper drawing
        st.write('## Dimensional Parameters')
        with st.beta_expander("Expand for sketch describing truss dimensions:"):
            st.image(r"data/geometric_parameters.png",use_column_width=True)
        st.latex(dim_params_latex)
        #Output or stop script for angle, eccentricity, gap checks
        if success:
            results_container.success(message)
        else:
            results_container.error(message)
            st.stop()
        fig,ax = plots.dim_params_plot(b0*1000,t0*1000,b1*1000,t1*1000,chord_type,
                                    beta_min,beta_max,twogamma_min,twogamma_max,tau_min,tau_max)
        results_container.pyplot(fig)
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
        SCF_ochax, SCF_obax, SCF_bax_min, fig4, ax4 = fnc.SCFochax_func(beta,theta)
        SCF_chaxbax_latex, (SCF_chax,SCF_bax,SCF_chch) = fnc.SCF_chaxbaxchch_chs(twogamma/2,tau,theta,
                                        SCF_ochax[0],SCF_obax[0],SCF_bax_min)
        if srun:
            st.pyplot(fig4)
            st.latex(SCF_chaxbax_latex)
    elif gap:
        SCF_chax_latex, SCF_chax = fnc.SCF_chax_gap(beta,twogamma,tau,g_prime,theta)
        SCF_bax_latex, SCF_bax = fnc.SCF_bax_gap(beta,twogamma,tau,theta)
        SCF_chch_latex,SCF_chch = fnc.SCF_chch_gap(beta,g_prime)
        if srun:
            st.header("GAP JOINT: $2 \cdot tau <= g^\prime$")
            st.write("### $SCF_{chax}$")
            st.latex(SCF_chax_latex)
            st.write("### $SCF_{bax}$")
            st.latex(SCF_bax_latex)
            st.write("### $SCF_{chch}$")
            st.latex(SCF_chch_latex)
    else:
        SCF_chax_latex, SCF_chax = fnc.SCF_chax_overlap(beta,twogamma,tau,Ov,theta)
        SCF_bax_latex, SCF_bax = fnc.SCF_bax_overlap(beta,twogamma,tau,Ov,theta)
        SCF_chch_latex,SCF_chch = fnc.SCF_chch_overlap(beta)
        if srun:
            st.header("OVERLAP JOINT: $0.5 <= O_v <= 1.0$:")
            st.write("### $SCF_{chax}$")
            st.latex(SCF_chax_latex)
            st.write("### $SCF_{bax}$")
            st.latex(SCF_bax_latex)
            st.write("### $SCF_{chch}$")
            st.latex(SCF_chch_latex)


    #Calculate all stresses
    chord_ax_stresses_latex, (sigma_chord1P, sigma_chord2P) = fnc.chord_ax_stresses(SCF_chax,
                                                                        SCF_chch,
                                                                        P_brace * u.kN,
                                                                        P_chord * u.kN,
                                                                        theta,
                                                                        A_chord * u.m**2,
                                                                        A_brace * u.m**2)
    chord_BM_stresses_latex, (sigma_chordM_ip, sigma_chordM_op) = fnc.chord_BM_stresses(
                                            h0*u.m,b0*u.m,b1*u.m,SCF_chch,SCF_ch_op,
                                            M_ip_chord * u.kN * u.m,M_op_chord * u.kN * u.m,
                                            Ix_chord * 10**6 * u.m**4,Iy_chord * 10**6 * u.m**4)
    brace_stresses_latex, (sigma_brace_1P, sigma_braceM_op) = fnc.brace_stresses(b1 * u.m, 
                                                            SCF_bax,
                                                            P_brace * u.kN,
                                                            A_brace * u.m**2,
                                                            SCF_br_op,
                                                            M_op_brace * u.kN * u.m,
                                                            Iy_brace * 10**6 * u.m**4)
    cum_stresses_latex, (sigma_chord, sigma_brace) = fnc.cum_stresses(sigma_chord1P,
                                                                    sigma_chord2P,
                                                                    sigma_chordM_ip,
                                                                    sigma_chordM_op,
                                                                    sigma_brace_1P,
                                                                    sigma_braceM_op)
    if sigma_chord <= sigma_max * u.MPa and sigma_brace <= sigma_max * u.MPa:
        success_stress = True
    else:
        success_stress = False

    if srun:
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
    
    return sigma_chord.value
    
if __name__ == '__main__':
    results = st.sidebar.checkbox("Display results?",value=True)
    st.write(main(0,results))