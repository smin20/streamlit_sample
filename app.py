import streamlit as st
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt

# Set the title of the app
st.title("Streamlit Feature Showcase")

# Text Input Example
st.header("User Input Section")
name = st.text_input("What's your name?", "Guest")
st.write(f"Hello, {name}! Welcome to the Streamlit app.")

# Slider Example
st.header("Slider Example")
age = st.slider("Select your age", min_value=0, max_value=100, value=25)
st.write(f"Your age is: {age}")

# Button Example
st.header("Button Example")
if st.button("Click Me!"):
    st.write("You clicked the button!")

# Checkbox Example
st.header("Checkbox Example")
agree = st.checkbox("I agree to the terms and conditions")
if agree:
    st.write("Thank you for agreeing!")

# Selectbox Example
st.header("Selectbox Example")
option = st.selectbox("Choose a fruit:", ["Apple", "Banana", "Cherry"])
st.write(f"You selected: {option}")

# Radio Button Example
st.header("Radio Button Example")
radio_option = st.radio("Select a color:", ["Red", "Green", "Blue"])
st.write(f"You chose: {radio_option}")

# Sidebar Example
st.sidebar.header("Sidebar Example")
sidebar_option = st.sidebar.selectbox("Select a number:", [1, 2, 3, 4, 5])
st.sidebar.write(f"You chose the number: {sidebar_option}")

# DataFrame Example
st.header("DataFrame Example")
data = pd.DataFrame(np.random.randn(10, 5), columns=["A", "B", "C", "D", "E"])
st.dataframe(data)  # Display the dataframe

# Line Chart Example
st.header("Line Chart Example")
chart_data = pd.DataFrame(np.random.randn(20, 3), columns=["A", "B", "C"])
st.line_chart(chart_data)

# Matplotlib Chart Example
st.header("Matplotlib Chart Example")
fig, ax = plt.subplots()
ax.plot([1, 2, 3, 4], [10, 20, 15, 25])
st.pyplot(fig)

# File Upload Example
st.header("File Upload Example")
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write(df)

# Progress Bar Example
st.header("Progress Bar Example")
progress_bar = st.progress(0)
for i in range(100):
    time.sleep(0.05)
    progress_bar.progress(i + 1)

# Expander Example
st.header("Expander Example")
with st.expander("Click to expand for more info"):
    st.write("This is inside the expander.")

# Columns Example
st.header("Columns Example")
col1, col2, col3 = st.columns(3)
with col1:
    st.write("This is column 1")
with col2:
    st.write("This is column 2")
with col3:
    st.write("This is column 3")

# Multiselect Example
st.header("Multiselect Example")
multiselect_option = st.multiselect(
    "Choose multiple options:", ["Option 1", "Option 2", "Option 3", "Option 4"]
)
st.write(f"You selected: {multiselect_option}")

# Text Area Example
st.header("Text Area Example")
text_area = st.text_area("Type your message here")
st.write(f"Your message: {text_area}")

# Number Input Example
st.header("Number Input Example")
number = st.number_input("Input a number", min_value=0, max_value=100, value=50)
st.write(f"The number you entered is: {number}")

# Date Input Example
st.header("Date Input Example")
date = st.date_input("Pick a date")
st.write(f"You selected: {date}")

# Time Input Example
st.header("Time Input Example")
time_input = st.time_input("Pick a time")
st.write(f"You selected: {time_input}")
