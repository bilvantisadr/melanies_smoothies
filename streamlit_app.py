# Import python packages
import streamlit as st
import requests
import pandas as pd
from snowflake.snowpark.functions import col

# App title and description
st.title(":cup_with_straw: Customize Your Smoothie :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Input field for name
name_on_order = st.text_input("Name on Smoothie:")
st.write('The name on your Smoothie will be:', name_on_order)

# Connect to Snowflake and get fruit options
cnx = st.connection("snowflake")
session = cnx.session()

# Query fruit options from Snowflake
my_dataframe = session.table("smoothies.public.fruit_options").select(
    col('FRUIT_NAME'), col('SEARCH_ON')
)

# Convert Snowpark DataFrame to Pandas
pd_df = my_dataframe.to_pandas()

# Display the fruit options as a table
st.dataframe(pd_df)

# Convert fruit names to list for the multiselect
ingredient_options = pd_df['FRUIT_NAME'].tolist()

# Ingredient selection (up to 5)
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    ingredient_options,
    max_selections=5
)

# If user selected ingredients, show nutrition info and allow order
if ingredients_list:

    ingredients_string = ''
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        
        # Fetch and display nutrition info
        st.subheader(f"{fruit_chosen} Nutrition Information")
        fruityvice_response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")
        
        if fruityvice_response.status_code == 200:
            nutrition_data = fruityvice_response.json()
            st.dataframe(data=nutrition_data, use_container_width=True)
        else:
            st.error(f"Could not retrieve data for {fruit_chosen}.")

    # Prepare SQL insert statement
    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders (ingredients, NAME_ON_ORDER)
        VALUES ('{ingredients_string.strip()}', '{name_on_order}')
    """

    # Display the query for reference (optional)
    st.code(my_insert_stmt)

    # Submit order button
    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success('Your Smoothie is ordered! ✅')
