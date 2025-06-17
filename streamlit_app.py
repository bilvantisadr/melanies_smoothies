# Import python packages
import streamlit as st
import requests
import pandas as pd
from snowflake.snowpark.functions import col

# App title and instructions
st.title(":cup_with_straw: Customize Your Smoothie :cup_with_straw:")
st.write("Choose up to 5 fruits for your custom smoothie!")

# Name input
name_on_order = st.text_input("Name on Smoothie:")

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Query fruit options
fruit_df = session.table("smoothies.public.fruit_options").select(
    col("FRUIT_NAME"), col("SEARCH_ON")
).to_pandas()

# Show table of available fruits
st.subheader("Available Fruits")
st.dataframe(fruit_df, use_container_width=True)

# Get fruit names as a list for multiselect
fruit_list = fruit_df["FRUIT_NAME"].tolist()

# Multiselect for ingredients (up to 5)
selected_fruits = st.multiselect(
    "Choose up to 5 ingredients:",
    options=fruit_list,
    max_selections=5
)

# Process selected ingredients
if selected_fruits:

    # Display nutrition info and build ingredients string
    ingredients_string = ""
    for fruit in selected_fruits:
        ingredients_string += fruit + ", "
        search_on = fruit_df.loc[fruit_df["FRUIT_NAME"] == fruit, "SEARCH_ON"].iloc[0]
        
        st.subheader(f"{fruit} Nutrition Information")
        response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")
        
        if response.status_code == 200:
            nutrition_data = pd.DataFrame([response.json()])
            st.dataframe(nutrition_data)
        else:
            st.error(f"Failed to fetch nutrition info for {fruit}.")

    ingredients_string = ingredients_string.rstrip(", ")

    # Show final ingredients and SQL
    st.markdown(f"**Ingredients:** {ingredients_string}")
    st.markdown(f"**Name on Order:** {name_on_order}")

    insert_stmt = f"""
        INSERT INTO smoothies.public.orders (ingredients, NAME_ON_ORDER)
        VALUES ('{ingredients_string}', '{name_on_order}')
    """

    # Button to submit order
    if st.button("Submit Order"):
        try:
            session.sql(insert_stmt).collect()
            st.success("Your Smoothie is ordered! ✅")
        except Exception as e:
            st.error(f"Order failed: {e}")
