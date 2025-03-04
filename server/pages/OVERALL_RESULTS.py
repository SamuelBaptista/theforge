import os
import json

import streamlit as st

import pandas as pd
import plotly.express as px


if not st.session_state.get('authenticated', False):
    st.warning("Please login at the login page")
    st.stop()

st.image("server/assets/images/arion_logo.png", use_container_width=True)
st.divider()

# Add evaluation visualization section
st.header("Evaluation Results")

# Get list of languages from evaluation folder
evaluation_dir = "server/assets/evaluation"
if not os.path.exists(evaluation_dir):
    os.makedirs(evaluation_dir)
    st.info("No evaluation data found.")
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
                # Create a DataFrame from the evaluation data
                df = pd.DataFrame(evaluation_data)
                
                # Get unique names
                unique_names = df['name'].unique()
                
                for name in unique_names:
                    # Filter data for this name
                    name_data = df[df['name'] == name]
                    
                    # Create expanded data for this person
                    expanded_data = []
                    for _, row in name_data.iterrows():
                        for attempt_num in range(1, row['attempts'] + 1):
                            is_this_attempt_correct = row['correct'] and attempt_num == row['attempts']
                            expanded_data.append({
                                'Attempt_Number': attempt_num,
                                'Correct': is_this_attempt_correct
                            })
                    
                    # Convert to DataFrame and calculate success rates
                    df_expanded = pd.DataFrame(expanded_data)
                    success_by_attempts = df_expanded.groupby('Attempt_Number').agg({
                        'Correct': ['count', 'sum']
                    }).reset_index()
                    
                    success_by_attempts.columns = ['Attempts', 'Total', 'Correct']
                    success_by_attempts['Success_Rate'] = (success_by_attempts['Correct'] / 
                                                         success_by_attempts['Total'] * 100)

                    # Create the bar chart
                    fig = px.bar(
                        success_by_attempts,
                        x='Attempts',
                        y='Success_Rate',
                        text=success_by_attempts['Success_Rate'].round(1).astype(str) + '%',
                        title=f"Success Rate by Attempt Number for {name}",
                        labels={
                            'Attempts': 'Number of attempts',
                            'Success_Rate': 'Accuracy (%)',
                        },
                        height=400
                    )

                    # Customize the chart
                    fig.update_traces(
                        textposition='inside',
                        width=0.7
                    )
                    
                    fig.update_layout(
                        yaxis=dict(
                            range=[0, 100],
                            ticksuffix='%'
                        ),
                        xaxis=dict(
                            tickmode='linear',
                            tick0=0,
                            dtick=1
                        ),
                        showlegend=False,
                        bargap=0.2
                    )
                    
                    # Display the chart
                    st.plotly_chart(fig, use_container_width=True)

                st.divider()

                # Extract names and attempts for the detailed breakdown
                names = [entry.get('name', 'Unknown') for entry in evaluation_data]
                attempts = [entry.get('attempts', 0) for entry in evaluation_data]
                correct = [entry.get('correct', False) for entry in evaluation_data]

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
                
        except FileNotFoundError:
            st.warning(f"Evaluation file for {selected_language} not found.")
        except json.JSONDecodeError:
            st.error(f"Error parsing the evaluation data for {selected_language}.")