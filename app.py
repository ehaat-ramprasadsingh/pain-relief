import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt

# Streamlit page setup
st.set_page_config(page_title="Pain Relief Drugs Analysis", layout="wide")

# Load data
st.sidebar.header("Upload your Excel files")
patients_file = st.sidebar.file_uploader("Upload Patients Data (Excel)", type=["xlsx"])
drugs_file = st.sidebar.file_uploader("Upload Drugs Data (Excel)", type=["xlsx"])

if patients_file and drugs_file:
    # Read Excel files
    patients_df = pd.read_excel(patients_file)
    drugs_df = pd.read_excel(drugs_file)
    
    # Process data
    patients_df['999 Time'] = pd.to_datetime(patients_df['Job Date'] + ' ' + patients_df['999 Time'])
    patients_df['Patient Side Time'] = pd.to_datetime(patients_df['Job Date'] + ' ' + patients_df['Patient Side Time'])
    drugs_df['Time'] = pd.to_datetime(drugs_df['Time'])

    # Filter for records from 5th October 2023 onwards
    cutoff_date = pd.Timestamp('2023-10-05')
    patients_df = patients_df[patients_df['999 Time'] >= cutoff_date]
    drugs_df = drugs_df[drugs_df['Time'] >= cutoff_date]

    # Fix time crossover issues
    patients_df.loc[patients_df['Patient Side Time'] < patients_df['999 Time'], 'Patient Side Time'] += pd.Timedelta(days=1)
    drugs_df = pd.merge(drugs_df, patients_df[['Patient ID', '999 Time']], on='Patient ID')
    drugs_df.loc[drugs_df['Time'] < drugs_df['999 Time'], 'Time'] += pd.Timedelta(days=1)

    # Merge data
    merged_df = pd.merge(drugs_df, patients_df[['Patient ID', 'Patient Side Time']], on='Patient ID')
    merged_df['time_taken_minutes'] = (merged_df['Time'] - merged_df['Patient Side Time']).dt.total_seconds() / 60
    filtered_df = merged_df[(merged_df['time_taken_minutes'] >= 0) & (merged_df['time_taken_minutes'] <= 60)]

    # Define tabs
    tabs = st.tabs(["Drug Visualizations", "Subsequent Drugs Analysis", "Unique Patients Count"])

    # Drug Visualizations Tab
    with tabs[0]:
        st.header("Drug Administration Time Analysis")
        specific_drugs = ['Paracetamol', 'Morphine', 'Fentanyl', 'Ketamine', 'Methoxyflurane (Penthrox)']
        selected_drugs = st.multiselect("Select drugs to visualize", specific_drugs, default=specific_drugs)

        if selected_drugs:
            for drug in selected_drugs:
                drug_df = filtered_df[filtered_df['Drug'] == drug]

                # Calculate statistics
                mean_duration = drug_df['time_taken_minutes'].mean()
                median_duration = drug_df['time_taken_minutes'].median()

                # Display statistics
                st.write(f"**{drug}**")
                st.write(f"Mean Time: {mean_duration:.2f} minutes")
                st.write(f"Median Time: {median_duration:.2f} minutes")

                # Plot distribution
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.histplot(drug_df['time_taken_minutes'], bins=20, kde=True, ax=ax)
                ax.set_title(f'Distribution of Time Taken to Administer {drug}')
                ax.set_xlabel("Time Taken (minutes)")
                ax.set_ylabel("Frequency")
                ax.axvline(x=mean_duration, color='blue', linestyle='--', label='Mean')
                ax.axvline(x=median_duration, color='green', linestyle='--', label='Median')
                ax.legend()
                st.pyplot(fig)
        else:
            st.write("No drugs selected for visualization.")

    # Subsequent Drugs Analysis Tab
    with tabs[1]:
        st.header("Subsequent Drugs Analysis")
        specific_drugs = ['Paracetamol', 'Morphine', 'Fentanyl', 'Ketamine', 'Methoxyflurane (Penthrox)']
        selected_drugs = st.multiselect(
            "Select drugs to analyze subsequent drugs administered", specific_drugs, default=specific_drugs)

        if selected_drugs:
            for selected_drug in selected_drugs:
                st.subheader(f"Subsequent Drugs Administered After {selected_drug}")
                selected_patients = merged_df[merged_df['Drug'] == selected_drug]
                
                if not selected_patients.empty:
                    subsequent_drugs = []
                    for _, row in selected_patients.iterrows():
                        patient_id = row['Patient ID']
                        selected_time = row['Time']
                        subsequent = merged_df[(merged_df['Patient ID'] == patient_id) & (merged_df['Time'] > selected_time)]
                        subsequent_drugs.extend(subsequent['Drug'].tolist())

                    subsequent_drug_counts = pd.Series(subsequent_drugs).value_counts()

                    if not subsequent_drug_counts.empty:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        sns.barplot(x=subsequent_drug_counts.index, y=subsequent_drug_counts.values, ax=ax)
                        ax.set_title(f"Subsequent Drugs Administered After {selected_drug}")
                        ax.set_xlabel("Drug Name")
                        ax.set_ylabel("Count")
                        plt.xticks(rotation=45)
                        for i, v in enumerate(subsequent_drug_counts.values):
                            ax.text(i, v + 0.5, str(v), ha='center', va='bottom')
                        st.pyplot(fig)
                    else:
                        st.write(f"No subsequent drugs found after {selected_drug}.")
                else:
                    st.write(f"No patients received {selected_drug}.")
        else:
            st.write("No drugs selected for analysis.")

    # Unique Patients Count Tab
    with tabs[2]:
        st.header("Unique Patients per Drug")
        patient_counts = merged_df.groupby('Drug')['Patient ID'].nunique().sort_values(ascending=False)
        if not patient_counts.empty:
            st.bar_chart(patient_counts)
        else:
            st.write("No data available for unique patient counts.")

else:
    st.info("Please upload both patients and drugs data to proceed.")