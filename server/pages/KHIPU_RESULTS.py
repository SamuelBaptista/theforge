import os
import json

import streamlit as st

import pandas as pd
import plotly.express as px


if not st.session_state.get('authenticated', False):
    st.warning("Please login at the login page")
    st.stop()

# Add evaluation visualization section
st.header("Evaluation Results")

# Get list of languages from evaluation folder
evaluation_dir = "server/assets/evaluation"
if not os.path.exists(evaluation_dir):
    os.makedirs(evaluation_dir)
    st.info("No evaluation data found. Evaluation directory created.")
else:
    # Get all JSON files from the evaluation directory
    evaluation_files = [f for f in os.listdir(evaluation_dir) if f.endswith('.json')]
    
    if not evaluation_files:
        st.info("No evaluation data files found.")
    else:
        # Create a selectbox for the user to choose a language
        selected_language = st.selectbox("Select a language:", 
                                         [os.path.splitext(f)[0] for f in evaluation_files])
        
        # Load the selected language data
        evaluation_path = os.path.join(evaluation_dir, f"{selected_language}.json")
        
        try:
            with open(evaluation_path, 'r') as f:
                evaluation_data = json.load(f)
            
            if not evaluation_data:
                st.info(f"No evaluation data available for {selected_language}.")
            else:
                # Extract names and attempts for the chart
                names = [entry.get('name', 'Unknown') for entry in evaluation_data]
                attempts = [entry.get('attempts', 0) for entry in evaluation_data]
                correct = [entry.get('correct', False) for entry in evaluation_data]

                st.divider()
                
                # Display summary statistics with improved visuals
                st.subheader("Summary Statistics")
                
                # Create a metrics container with custom styling
                metrics_container = st.container()
                with metrics_container:
                    # Use 4 columns for better spacing
                    col1, col2, col3, col4 = st.columns(4)
                    
                    # Calculate success rate as a percentage
                    success_rate = (sum(correct) / len(evaluation_data) * 100) if evaluation_data else 0
                    
                    with col1:
                        st.metric(
                            "Total Participants", 
                            len(evaluation_data),
                            help="Number of people who attempted pronunciation"
                        )
                    with col2:
                        st.metric(
                            "Correct Pronunciations", 
                            sum(correct),
                            # delta=f"{success_rate:.1f}%" if success_rate > 0 else None,
                            help="Number of participants who pronounced correctly"
                        )
                    with col3:
                        avg_attempts = sum(attempts) / len(attempts) if attempts else 0
                        st.metric(
                            "Average Attempts", 
                            f"{avg_attempts:.2f}",
                            help="Average number of attempts per participant"
                        )
                    with col4:
                        max_attempts = max(attempts) if attempts else 0
                        st.metric(
                            "Max Attempts",
                            max_attempts,
                            help="Maximum number of attempts by any participant"
                        )          
                
                df = pd.DataFrame({
                    'Name': names,
                    'Attempts': attempts,
                    'Correct': correct
                })
                
                # Create color mapping based on correctness
                color_discrete_map = {True: 'green', False: 'red'}
                
                # Create the bar chart
                fig = px.bar(
                    df, 
                    x='Name', 
                    y='Attempts',
                    color='Correct',
                    color_discrete_map=color_discrete_map,
                    title=f"Evaluation Results for {selected_language}",
                    labels={'Name': 'Name', 'Attempts': 'Number of Attempts'},
                    height=400,
                    barmode='group',  # Group bars instead of stacking them
                )

                fig.update_traces(marker_line_width=2, marker_line_color="white")                
                
                # Customize the chart
                fig.update_layout(
                    xaxis_title="Name",
                    yaxis_title="Number of Attempts",
                    yaxis=dict(
                        tickmode='linear',
                        tick0=0,
                        dtick=1,
                    ),                   
                    legend_title="Correct Pronunciation"
                )
                
                # Display the chart
                st.plotly_chart(fig, use_container_width=True)
                
        except FileNotFoundError:
            st.warning(f"Evaluation file for {selected_language} not found.")
        except json.JSONDecodeError:
            st.error(f"Error parsing the evaluation data for {selected_language}.")

        st.divider()

        df = pd.DataFrame({
            'Name': names,
            'Total Attempts': attempts,
            'Correct': correct,
            'Wrong Attempts': [a-1 if c else a for a, c in zip(attempts, correct)],
            'Successful Attempts': [1 if c else 0 for c in correct]
        })

        st.subheader("Detailed Breakdown")

        name = st.selectbox("Select a name:", df['Name'].unique())
        df2 = df[df['Name'] == name].copy()

        detailed_df = df2[['Name', 'Total Attempts', 'Wrong Attempts', 'Correct']].copy()
        detailed_df['Status'] = detailed_df['Correct'].map({True: '✅ Correct', False: '❌ Incorrect'})
        detailed_df = detailed_df.drop('Correct', axis=1)

        st.dataframe(
            detailed_df,
            hide_index=True,
            use_container_width=True
        )