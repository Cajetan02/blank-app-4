import streamlit as st
import csv
import os
import random
from fpdf import FPDF
from PIL import Image
import requests
from io import BytesIO
from collections import Counter
# Initialize session state for page navigation
if "page" not in st.session_state:
    st.session_state.page = "home"

# Backend Functions
def save_to_csv(recipe):
    """Saves a recipe to the CSV file."""
    file_exists = os.path.exists("recipes.csv")
    with open("recipes.csv", "a", newline="") as csvfile:
        fieldnames = ["Name", "Ingredients", "Steps", "Background", "State", "Image"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()
        writer.writerow(recipe)

def load_recipes():
    """Loads all recipes from the CSV file."""
    if not os.path.exists("recipes.csv"):
        return []
    with open("recipes.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)

def consolidate_ingredients(selected_recipes):
    """Consolidates ingredients and counts repeated items."""
    all_ingredients = []
    for recipe in selected_recipes:
        ingredients = recipe["Ingredients"].split(",")  # Assuming comma-separated ingredients
        ingredients = [ingredient.strip() for ingredient in ingredients]
        all_ingredients.extend(ingredients)

    return Counter(all_ingredients)

# Page Navigation
def go_to_page(page):
    st.session_state.page = page

def format_steps(steps):
    """
    Splits the steps into new lines if they start with a number.
    Assumes steps are separated by a period followed by a space.
    """
    # Split the steps based on the pattern of a number followed by a period and space
    step_lines = steps.split('.')
    
    # Format each step and filter out any empty strings
    formatted_steps = " \n".join([f"{i + 1}. {step.strip()}" for i, step in enumerate(step_lines) if step.strip()])
    
    return formatted_steps

# Apply Custom CSS
def apply_custom_css():
    st.markdown("""
    <style>
    .block-container {
        padding: 2rem 3rem;  /* Increased padding for better spacing */
        background-color: #FFFFFF;  /* Subtle background color for better readability */
        border-radius: 10px;  /* Rounded corners for a polished look */
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);  /* Add a soft shadow */
    }
    .stButton > button {
        width: 100%;  /* Make buttons align and occupy full column width */
        background-color: #4CAF50;  /* Green button */
        color: white;  /* White text */
        border: none;  /* No border */
        padding: 10px 20px;  /* Padding for a better look */
        font-size: 16px;  /* Larger font size */
        cursor: pointer;  /* Pointer cursor */
        border-radius: 5px;  /* Rounded button corners */
    }
    .stButton > button:hover {
        background-color: #45a049;  /* Darker green on hover */
    }
    .special-section {
        background-color: #ffffff;  /* White background for the section */
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;  /* Spacing between sections */
    }
    .special-header {
        font-size: 24px;
        color: #4CAF50;  /* Green header */
        margin-bottom: 10px;
    }
    .special-content {
        font-size: 18px;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Recipe Flipbook", 0, 1, "C")

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_flipbook(recipes, states):
    """Generates a PDF flipbook of recipes for the selected states."""
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Create the front page
    pdf.add_page()
    pdf.set_fill_color(240, 240, 240)  # Light gray background
    pdf.rect(0, 0, pdf.w, pdf.h, 'F')  # Fill the background

    # Title
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 40, 'Welcome to My Recipe Book', 0, 1, 'C')

    # Subtitle
    pdf.set_font("Arial", "I", 16)
    pdf.cell(0, 10, 'Delicious Recipes for Every Occasion', 0, 1, 'C')

    # Add an image (optional)
    pdf.image('cover_image.jpg', x=30, y=60, w=150)  # Adjust path and size

    # Additional information
    pdf.set_font("Arial", "U", 14)
    pdf.cell(0, 20, 'Compiled by: C-10', 0, 1, 'C')

    # Add a page for recipes
    for recipe in recipes:
        pdf.add_page()
        pdf.set_fill_color(255, 255, 255)  # White background
        pdf.rect(0, 0, pdf.w, pdf.h, 'F')  # Fill the background

        # Recipe Name
        pdf.set_font("Arial", "B", 18)  # Larger font for recipe name
        pdf.cell(0, 10, txt=recipe["Name"], ln=True, align="C")

        # Ingredients and Steps
        pdf.set_font("Arial", size=12)
        
        # Add image on the left
        if recipe['Image'] and recipe['Image'] != "N/A":
            try:
                response = requests.get(recipe['Image'])
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    img_path = f"temp_{recipe['Name']}.jpg"
                    img.save(img_path)

                    # Add image with aspect ratio
                    pdf.image(img_path, x=10, y=30, w=60)  # Adjust width as needed
                    os.remove(img_path)
            except Exception as e:
                print(f"Error adding image for {recipe['Name']}: {e}")

        # Move cursor to the right of the image
        pdf.set_x(80)  # Move to the right of the image

        # Multi-cell for wrapping text
        formatted_steps = format_steps(recipe['Steps'])
        pdf.multi_cell(0, 10, txt=f"\nIngredients:\n{recipe['Ingredients']}\n", align="L")
        pdf.multi_cell(0, 10, txt=f"\n\n\nSteps:\n{formatted_steps}\n\nBackground:\n{recipe['Background']}", align="L")
    pdf_output = "flipbook.pdf"
    pdf.output(pdf_output)
    return pdf_output

# Pages
def home_page():
    st.title("Namaste, Foodie")
    st.subheader("Reviving Traditions, One Recipe at a Time!")

    # Search bar and Add Recipe button
    search_query = st.text_input("Search for Recipes", placeholder="Enter a recipe name...")
    if st.button("Search"):
        recipes = load_recipes()
        matching_recipes = [
            recipe for recipe in recipes if search_query.lower() in recipe["Name"].lower()
        ]

        if matching_recipes:
            for recipe in matching_recipes:
                st.subheader(recipe["Name"])
                st.write(f"*Ingredients:* {recipe['Ingredients']}")
                formatted_steps = format_steps(recipe['Steps'])
                st.write(f"*Steps:*\n{formatted_steps}")
                st.write(f"*Background:* {recipe['Background']}")
                st.write(f"*State:* {recipe['State']}")
                if recipe['Image'] and recipe['Image'] != "N/A":
                    st.image(recipe['Image'], caption=recipe['Name'])
                st.write("---")
        else:
            st.info("No matching recipes found.")

    if st.button("ADD RECIPE", key="add_recipe_button"):
        st.session_state.page = "add_recipe"

     # Today's Specials Section
    st.subheader("Today's Specials")
    recipes = load_recipes()
    if recipes:
        i = random.randint(0, len(recipes) - 1)
        random_recipe = recipes[i]
        formatted_steps = format_steps(random_recipe['Steps'])
        st.markdown(f"""
        *{random_recipe['Name']}*
        - *Ingredients:* {random_recipe['Ingredients']}
        - *Steps:* {formatted_steps}
        - *Background:* {random_recipe['Background']}
        """)
    else:
        st.write("No recipes available yet!")

    # Flipbook generator
    st.subheader("Generate Recipe Flipbook")
    recipes = load_recipes()
    states = list(set(recipe['State'] for recipe in recipes if recipe['State']))
    selected_states = st.multiselect("Select States", options=states)

    if st.button("Create Flipbook"):
        state_recipes = [recipe for recipe in recipes if recipe['State'] in selected_states]
        if state_recipes:
            pdf_path = generate_flipbook(state_recipes, selected_states)
            with open(pdf_path, "rb") as pdf_file:
                st.download_button(label="Download Flipbook", data=pdf_file, file_name=f"recipes_{'_'.join(selected_states)}.pdf", mime="application/pdf")
        else:
            st.warning("No recipes available for the selected states.")

    # Categories Section
    st.subheader("Categories")
    col1, col2, col3,col4,col5 = st.columns([1,1,1,1,1])  # Equal column widths

    with col1:
        if st.button("Nani's Secrets", key="nani_secrets"):
            go_to_page("nani_secrets")
    with col3:
        if st.button("Shopping List Generator", key="shopping_list"):
            go_to_page("shopping_list")
    with col5:
        if st.button("View All Recipes",key="view_recipe"):
            go_to_page("view_recipe")

def view_recipe_page():
    st.title("View all Recipes")
    recipes=load_recipes()
    for recipe in recipes:
        col1, col2, = st.columns([1,1])
        with col1:
            st.subheader(recipe["Name"])
            st.write(f"*Ingredients:* {recipe['Ingredients']}")
            formatted_steps = format_steps(recipe['Steps'])
            st.write(f"*Steps:*\n{formatted_steps}")
        with col2:
            if recipe['Image'] and recipe['Image'] != "N/A":
                st.image(recipe['Image'], caption=recipe['Name'])
        st.write(f"*Background:* {recipe['Background']}")
        st.write(f"*State:* {recipe['State']}")
        st.write("---")
    if st.button("Back to Home"):
        go_to_page("home")

def add_recipe_page():
    st.title("Add Your Recipe")
    with st.form("add_recipe_form"):
        name = st.text_input("Recipe Name")
        ingredients = st.text_area("Ingredients (comma-separated)")
        steps = st.text_area("Steps")
        background = st.text_area("Background/Story")
        state = st.text_input("State of Origin")
        image = st.text_input("Image URL (optional)")
        submitted = st.form_submit_button("Submit Recipe")

        if submitted:
            if name and ingredients and steps and background and state:
                recipe = {
                    "Name": name,
                    "Ingredients": ingredients,
                    "Steps": steps,
                    "Background": background,
                    "State": state,
                    "Image": image or "N/A",
                }
                save_to_csv(recipe)
                st.success("Recipe added successfully!")
                st.session_state.page = "home"
            else:
                st.error("Please fill out all fields!")

    if st.button("Back to Home"):
        go_to_page("home")

def nani_secrets_page():
    st.title("Nani's Secrets")
    st.markdown("""
    ### Timeless Tips from Nani's Kitchen:
    - **Spices:** Roast spices to enhance flavor and aroma.
    - **Preservation:** Store herbs in damp towels to keep them fresh.
    - **Rotis:** Add yogurt to your dough for softer, fluffier rotis.
    - **Soups:** Use vegetable scraps to make delicious broths.
    """)
    if st.button("Back to Home"):
        go_to_page("home")

def shopping_list_page():
    st.title("Shopping List Generator")
    recipes = load_recipes()

    if not recipes:
        st.warning("No recipes available! Please add some first.")
        if st.button("Back to Home"):
            go_to_page("home")
        return

    # Recipe selection
    selected_recipe_names = st.multiselect(
        "Select Recipes to Generate a Shopping List:",
        options=[recipe["Name"] for recipe in recipes],
    )
    selected_recipes = [
        recipe for recipe in recipes if recipe["Name"] in selected_recipe_names
    ]

    if st.button("Generate Shopping List"):
        if not selected_recipes:
            st.error("Please select at least one recipe!")
        else:
            consolidated = consolidate_ingredients(selected_recipes)

            st.subheader("Consolidated Shopping List:")
            for ingredient, count in consolidated.items():
                st.write(f"- {ingredient}: {count} Portions")

            # Download button
            shopping_list_data = "\n".join(
                [f"{ingredient}: {count}" for ingredient, count in consolidated.items()]
            )
            st.download_button(
                label="Download Shopping List",
                data=shopping_list_data,
                file_name="shopping_list.txt",
                mime="text/plain",
            )

    # Sustainability and Theme Additions
    st.markdown("### Sustainable Tips:")
    st.write("- **Reduce Waste:** Store unused ingredients for later.")
    st.write("- **Buy Locally:** Support farmers by choosing fresh, local produce.")
    st.write("- **Smart Substitutes:** Use alternatives like jaggery for sugar or coconut oil instead of butter.")

    if st.button("Back to Home"):
        go_to_page("home")

# Routing Pages
if st.session_state.page == "home":
    home_page()
elif st.session_state.page == "add_recipe":
    add_recipe_page()
elif st.session_state.page == "nani_secrets":
    nani_secrets_page()
elif st.session_state.page == "shopping_list":
    shopping_list_page()
elif st.session_state.page == "view_recipe":
    view_recipe_page()