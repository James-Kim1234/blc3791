import streamlit as st
import pandas as pd
import plotly.express as px
import kagglehub

st.set_page_config(layout="wide")
st.title('COVID-19 Time Series Data by Country')

@st.cache_data
def load_data():
    # Download the dataset using kagglehub
    path = kagglehub.dataset_download("imdevskp/corona-virus-report")
    csv_file_path = f"{path}/covid_19_clean_complete.csv"
    df = pd.read_csv(csv_file_path, parse_dates=['Date'])
    
    # Calculate 'Active' cases
    df['Active'] = df['Confirmed'] - df['Deaths'] - df['Recovered']
    return df

df = load_data()

# Get unique countries for the multiselect widget
countries = df['Country/Region'].unique()
selected_countries = st.multiselect('Select Countries', countries, default=['Afghanistan', 'US', 'China'])

if not selected_countries:
    st.warning('Please select at least one country.')
elif len(selected_countries) > 5: # Added a limit to avoid cluttered plots
    st.warning('Please select up to 5 countries for better visualization.')
else:
    # Filter data for selected countries
    df_filtered = df[df['Country/Region'].isin(selected_countries)]

    # Group by Date and Country/Region to sum up cases (important for multi-region countries like China, US)
    df_grouped = df_filtered.groupby(['Date', 'Country/Region'])[['Confirmed', 'Deaths', 'Recovered', 'Active']].sum().reset_index()

    # Melt the DataFrame for Plotly Express
    df_melted = df_grouped.melt(id_vars=['Date', 'Country/Region'], 
                                value_vars=['Confirmed', 'Deaths', 'Recovered', 'Active'],
                                var_name='Case Type', value_name='Number of Cases')

    st.subheader('COVID-19 Cases Over Time')
    fig = px.line(df_melted,
                  x='Date',
                  y='Number of Cases',
                  color='Country/Region',
                  line_dash='Case Type',
                  title=f'COVID-19 Case Trends for {', '.join(selected_countries)}',
                  labels={'Number of Cases': 'Number of Cases'})
    st.plotly_chart(fig, use_container_width=True)

    st.subheader('Raw Data for Selected Countries')
    st.dataframe(df_filtered)
