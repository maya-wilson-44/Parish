import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
from google import genai
import plotly.express as px



# Cache the data loading and cleaning process
@st.cache_data
def load_and_clean_data():
    # Load the data
    df = pd.read_excel("socioeconomic_2.xlsx")
  
    # Clean the data
    df = df.rename(columns={" Population (2020)": "Population (2020)"})
    df["Median_Family_Income (2019 -2023)"] = (
        df["Median_Family_Income (2019 -2023)"]
        .astype(str)
        .str.replace(',', '')
        .replace('nan', '0')
        .astype(float)
    )
    df["GDP (2023)"] = (
        df["GDP (2023)"]
        .astype(str)
        .str.replace(',', '')
        .replace('nan', '0')
        .astype(float)
    )
    df["Population (2010)"] = (
        df["Population (2010)"]
        .astype(str)
        .str.replace(',', '')
        .replace('nan', '0')
        .astype(float)
    )
    df["Population (2020)"] = (
        df["Population (2020)"]
        .astype(str)
        .str.replace(',', '')
        .replace('nan', '0')
        .astype(float)
    )
    return df

# Initialize session state variables - Add this near the top of your code
if 'selected_parishes' not in st.session_state:
    st.session_state.selected_parishes = []

# Load the data
df = load_and_clean_data()

# App title and description
st.title("Louisiana Parish Data Explorer")
st.write("Access and analyze socioeconomic data across Louisiana parishes")

# Data visualization section
st.header("Data Visualization")

# Add an explanation for the user
st.markdown(
    """
    <div style="background-color: #f0f0f0; padding: 8px; border-radius: 6px; font-size: .7em; line-height: 1.6; color: #333; margin-bottom: 0px; padding-bottom: .5px;">
        <strong>How to Use the Visualization Tool:</strong>
        <ul>
            <li><strong>1 Variable Selected:</strong> Displays a Bar Chart showing the top parishes for the selected metric.</li>
            <li><strong>2 Variables Selected:</strong> Displays a Scatter Plot showing the relationship between the two selected metrics.</li>
            <li><strong>3+ Variables Selected:</strong> Displays a Correlation Heatmap showing the relationships between the selected metrics.</li>
            <li><strong>All Metrics Variable Selected:</strong> Displays a Correlation Heatmap for all available metrics.</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True
)

# Add white space before the multiselect
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# Add "All Metrics" as an option in the dropdown
metrics = [col for col in df.columns if col != "Parish"]
metrics_with_all = ["All Metrics"] + metrics

selected_variables = st.multiselect(
    "Select Variables for Visualization",  # Title of the multiselect
    metrics_with_all,  # Include "All Metrics" as an option
    default=["Population (2023)"]  # Default to "Population (2023)"
)

# Handle the "All Metrics" option
if "All Metrics" in selected_variables:
    selected_variables = metrics  # Select all metrics if "All Metrics" is chosen


# Create a modal-like experience with an expander
with st.expander("Parish Selection", expanded=False):
    st.write("Select which parishes to display in visualizations:")

    # Add Select All / Deselect All checkbox
    select_all = st.checkbox("Select All Parishes", value=False, key="select_all")

    # Add checkboxes for Top 5, Top 10, Bottom 5, and Bottom 10
    top_5 = st.checkbox("Top 5 Parishes", value=False, key="top_5")
    top_10 = st.checkbox("Top 10 Parishes", value=True, key="top_10")  # Default to True
    bottom_5 = st.checkbox("Bottom 5 Parishes", value=True, key="bottom_5")  # Default to True
    bottom_10 = st.checkbox("Bottom 10 Parishes", value=False, key="bottom_10")

    # Initialize an empty list for selected parishes
    temp_selected_parishes = []
    # Add parishes based on the selected checkboxes
    if select_all:
        temp_selected_parishes = df["Parish"].unique().tolist()
    else:
        if top_5:
            temp_selected_parishes += (
                df.sort_values(by=selected_variables[0], ascending=False)
                .head(5)["Parish"]
                .tolist()
            )
        if top_10:
            temp_selected_parishes += (
                df.sort_values(by=selected_variables[0], ascending=False)
                .head(10)["Parish"]
                .tolist()
            )
        if bottom_5:
            temp_selected_parishes += (
                df.sort_values(by=selected_variables[0], ascending=True)
                .head(5)["Parish"]
                .tolist()
            )
        if bottom_10:
            temp_selected_parishes += (
                df.sort_values(by=selected_variables[0], ascending=True)
                .head(10)["Parish"]
                .tolist()
            )
    
    # Remove duplicates from the selected parishes
    temp_selected_parishes = list(set(temp_selected_parishes))
    
    # Allow manual selection of parishes
    selected_parishes = st.multiselect(
        "Parishes:",
        options=df["Parish"].unique().tolist(),
        default=temp_selected_parishes,
    )
    
    # Apply button
    if st.button("Apply Selection"):
        st.session_state.selected_parishes = selected_parishes
# Determine which parishes to display
if st.session_state.selected_parishes:
    # Use the parishes from session state if available
    filtered_df = df[df["Parish"].isin(st.session_state.selected_parishes)]
else:
    # Default selection for first load - you can modify this as needed
    # For example, to show no parishes by default:
    # filtered_df = pd.DataFrame(columns=df.columns)
    
    # Or to show top 10 and bottom 5 by default:
    default_parishes = (
        df.sort_values(by=selected_variables[0], ascending=False)
        .head(10)["Parish"]
        .tolist()
    )
    default_parishes += (
        df.sort_values(by=selected_variables[0], ascending=True)
        .head(5)["Parish"]
        .tolist()
    )
    default_parishes = list(set(default_parishes))
    filtered_df = df[df["Parish"].isin(default_parishes)]    

    
# Chart section (takes up all the space below)

if len(selected_variables) == 1:
    metric = selected_variables[0]
    if not filtered_df.empty:
        # Sort the DataFrame by the selected metric in descending order
        filtered_df = filtered_df.sort_values(by=metric, ascending=False)

        # Determine the chart title based on the user's selection
        if select_all:
            chart_title = f"All Parishes by {metric}"
        elif top_10 and bottom_5:
            chart_title = f"Top 10 and Bottom 5 Parishes by {metric}"
        elif top_5 and bottom_10:
            chart_title = f"Top 5 and Bottom 10 Parishes by {metric}"
        elif top_5 and bottom_5:
            chart_title = f"Top 5 and Bottom 5 Parishes by {metric}"
        elif top_10 and bottom_10:
            chart_title = f"Top 10 and Bottom 10 Parishes by {metric}"
        elif top_10 and top_5:
            chart_title = f"Top 10 Parishes by {metric}"
        elif bottom_10 and bottom_5:
            chart_title = f"Bottom 10 Parishes by {metric}"
        elif top_5:
            chart_title = f"Top 5 Parishes by {metric}"
        elif top_10:
            chart_title = f"Top 10 Parishes by {metric}"
        elif bottom_5:
            chart_title = f"Bottom 5 Parishes by {metric}"
        elif bottom_10:
            chart_title = f"Bottom 10 Parishes by {metric}"
        else:
            chart_title = f"Selected Parishes by {metric}"

        # Create the interactive bar chart using Plotly
        fig = px.bar(
            filtered_df,
            x=metric,
            y="Parish",
            orientation="h",
            title=chart_title,
            text=metric,  # Display the exact number on hover
        )

        # Customize the layout
        fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
        fig.update_layout(
            xaxis_title=metric,
            yaxis_title="Parish",
            yaxis=dict(categoryorder="total ascending"),  # Sort bars by value
            title=dict(font=dict(size=24)),
        )

        # Display the chart
        st.plotly_chart(fig, use_container_width=True)


# Scatter plot section
if len(selected_variables) == 2:
    x_axis, y_axis = selected_variables
    if not filtered_df.empty:
        st.markdown("### Scatter Plot")

        # Create the interactive scatter plot using Plotly
        fig = px.scatter(
            filtered_df,
            x=x_axis,
            y=y_axis,
            color="Parish",  # Color points by Parish
            hover_data=["Parish", x_axis, y_axis],  # Show additional data on hover
            title=f"Scatter Plot: {x_axis} vs {y_axis}",
        )

        # Customize the layout
        fig.update_layout(
            xaxis_title=x_axis,
            yaxis_title=y_axis,
            title=dict(font=dict(size=24)),
        )

        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for the selected variables. Please adjust your filters.")

elif len(selected_variables) > 2:
    # More than two variables: Display a correlation heatmap
    numeric_df = filtered_df[selected_variables].select_dtypes(include=['float64', 'int64'])
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", ax=ax)
    ax.set_title("Correlation Heatmap", fontsize=24)
    plt.tight_layout()
    st.pyplot(fig)



client = genai.Client(api_key="AIzaSyAz56zLp5egYUz_2jGNTDYMddJW9KXNu88")

# Generate the prompt based on user selections
if len(selected_variables) == 1:
    metric = selected_variables[0]
    
    # Check if Bottom 5 or Bottom 10 is selected
    if bottom_5 or bottom_10:
        prompt = f"""
        I am working for a construction company in Louisiana and I would like to get information based on the selected metric '{metric}' for the selected parishes {selected_parishes}.
        
        The selected parishes include the bottom-performing parishes based on the metric '{metric}', which may indicate challenges or risks for construction projects in these areas.
        
        Please provide 2-3 business recommendations highlighting why these areas may not be ideal for construction work and suggest alternative strategies or locations.
        
        Format your response STRICTLY as a JSON array with objects containing 'recommendation', 'reason', 'source', and 'source_url' fields.
        Example format:
        [
          {{
            "recommendation": "Avoid construction projects in Parish X",
            "reason": "Parish X shows the lowest {metric} value, indicating limited economic potential",
            "source": "Analysis of provided Louisiana parish data",
            "source_url": "https://example.com/louisiana-economic-data"
          }},
          {{
            "recommendation": "Focus on alternative locations",
            "reason": "Parish Y has better economic indicators compared to the selected parishes",
            "source": "Internal analysis report",
            "source_url": "https://example.com/alternative-locations"
          }}
        ]
        """
    else:
        # Default prompt for other selections
        prompt = f"""
        I am working for a construction company in Louisiana and I would like to get information based on the selected metric '{metric}' for the selected parishes {selected_parishes}.
        
        Please provide 2-3 business recommendations based on this data.
        
        Format your response STRICTLY as a JSON array with objects containing 'recommendation', 'reason', 'source', and 'source_url' fields.
        Example format:
        [
          {{
            "recommendation": "Focus construction efforts in Parish X",
            "reason": "Parish X shows the highest {metric} value, indicating strong economic potential",
            "source": "Analysis of provided Louisiana parish data",
            "source_url": "https://example.com/louisiana-economic-data"
          }},
          {{
            "recommendation": "Another recommendation here",
            "reason": "Reasoning here",
            "source": "Source here",
            "source_url": "https://example.com/another-source"
          }}
        ]
        """

elif len(selected_variables) == 2:
    prompt = f"I am working for a construction company in Louisiana and I would like to get insights based on the relationship between '{selected_variables[0]}' and '{selected_variables[1]}' for the selected parishes {selected_parishes}."
    prompt += " Provide the response as a JSON with a 'recommendation', 'reason', and 'source'."

elif len(selected_variables) > 2:
    prompt = f"I am working for a construction company in Louisiana and I would like to get information on the correlation between metrics for the selected parishes {selected_parishes}."
    prompt += " Provide the response as a JSON with a 'recommendation', 'reason', and 'source'."

# Automatically generate the response
with st.spinner("Generating recommendation..."):
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    try:
        response_text = response.text
        # Sometimes the response might include markdown or other formatting
        if "```json" in response_text:
            json_text = response_text.split("```json")[1].split("```")[0].strip()
        else:
            json_text = response_text
            
        json_data = json.loads(json_text)
            
        # Check if the response is a list or a single object
        if isinstance(json_data, dict):
            json_data = [json_data]  # Convert to list for consistent handling
            
        # Display each recommendation
        st.markdown("### Recommendations")
        for idx, entry in enumerate(json_data, start=1):
            st.markdown(f"**Recommendation {idx}:** {entry.get('recommendation', 'No recommendation provided')}")
            st.markdown(f"- **Reason:** {entry.get('reason', 'No reason provided')}")
            
            # Check if source_url exists and is not empty
            source = entry.get('source', 'No source provided')
            source_url = entry.get('source_url', '')
            
            if source_url and source_url.startswith('http'):
                st.markdown(f"- **Source:** [{source}]({source_url})")
            else:
                st.markdown(f"- **Source:** {source}")
            
            st.markdown("---")
            
    except json.JSONDecodeError as e:
        st.error("Failed to parse the response as JSON.")
        st.write("Raw Response:")
        st.write(response.text)
        st.write(f"Error: {e}")
            
        # Attempt to display the raw response in a more readable format
        st.markdown("### Raw Insights")
        st.markdown(response.text)

    # Add this after displaying the recommendations from Gemini AI
    st.markdown(
        """
        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; font-size: 0.8em;">
        <strong>Note:</strong> The recommendations above were generated using Gemini AI and may not be completely accurate. 
        Please verify any critical information before making business decisions.
        </div>
        """, 
        unsafe_allow_html=True
    )
st.markdown("---")

# Analysis section
st.header("Parish Analysis")
if st.button("Show Summary Statistics"):
    st.write(filtered_df.describe())

st.markdown("---")

# Main content
st.header("Parish Data Overview")

# Add a button to toggle DataFrame display
if st.button("Show DataFrame"):
    st.dataframe(filtered_df)

# Download section
st.markdown("---")
st.header("Download Data")
st.download_button(
    label="Download Filtered Data as CSV",
    data=filtered_df.to_csv(index=False).encode('utf-8'),
    file_name='filtered_parish_data.csv',
    mime='text/csv',
)