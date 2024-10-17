import streamlit as st
import time
import random
from datetime import datetime

# Set the title of the app
st.title("Real-time Information Dashboard Without APIs")

# Display current system time
st.header("Current Time")
st.write("The current time is:")
current_time = st.empty()  # This creates a placeholder for the time
while True:
    current_time.text(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    time.sleep(1)  # Update the time every second
    st.experimental_rerun()

# Simulated Stock Price Section
st.header("Simulated Stock Price")
st.write("This is a simulated stock price for illustration.")

# Initialize with random stock price
stock_price = st.empty()  # Create a placeholder for stock price
initial_price = random.uniform(100, 200)
while True:
    price_change = random.uniform(-5, 5)  # Random change in stock price
    initial_price += price_change
    stock_price.text(f"Simulated Stock Price: ${initial_price:.2f}")
    time.sleep(5)  # Update every 5 seconds
    st.experimental_rerun()

# Random Number Generator
st.header("Random Number Generator")
st.write("Below is a randomly generated number:")
random_number_display = st.empty()

# Button to generate a random number
if st.button('Generate Random Number'):
    random_number = random.randint(1, 100)
    random_number_display.write(f"Random Number: {random_number}")

# User Input Section
st.header("User Input Section")
user_input = st.text_input("Enter any text to display below:")
if user_input:
    st.write(f"You entered: {user_input}")

# Countdown Timer Example
st.header("Countdown Timer")
seconds = st.number_input("Enter number of seconds for the countdown:", min_value=1, max_value=60, value=10)
if st.button("Start Countdown"):
    for i in range(seconds, 0, -1):
        st.write(f"Countdown: {i} seconds remaining")
        time.sleep(1)
    st.write("Time's up!")
