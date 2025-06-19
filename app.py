import streamlit as st
import pandas as pd
import google.generativeai as genai
import matplotlib.pyplot as plt
from PIL import Image
import re
import time

# Configure the API key
api_key = '' # add your api key 
genai.configure(api_key=api_key)

categories = ["Personal Care", "Household Care", "Dairy", "Staples", "Snacks and Beverages", "Packaged Food", "Fruits and Vegetables"]

# Custom Background and Styling
page_bg_img = '''
<style>
.stApp {
    background-image: url("https://plus.unsplash.com/premium_photo-1664305029850-586fdf503060?q=80&w=1937&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
}
h1, h2, h3, .stButton>button {
    color: #00ffff;
    font-family: 'Courier New', monospace;
    text-align: center;
    font-weight: bold;
}
.stButton>button {
    background-color: #0000ff;
    color: white;
    border-radius: 12px;
    font-size: 18px;
}
.stButton>button:hover {
    background-color: #d94636;
}
.stSpinner {
    color: #0000ff !important;
}
h2 {
    animation: glowing 1.5s infinite;
}
@keyframes glowing {
    0% { color: #00ff00; }    /* Starting color: Green */
    50% { color: #00ffff; }   /* Midpoint color: Cyan */
    100% { color: #0000ff; }  /* Ending color: Blue */
}
.card {
    background-color: rgba(255, 255, 255, 0.8);
    border-radius: 15px;
    padding: 20px;
    margin: 10px 0;
}
</style>
'''
st.markdown(page_bg_img, unsafe_allow_html=True)

# Step 1: Upload Image
def upload_image(image):
    with st.spinner("Uploading image..."):
        sample_file = genai.upload_file(path=image, display_name="Product Image")
    st.success(f"Uploaded file '{sample_file.display_name}' successfully!")
    return sample_file

# Step 2: Display Image
def display_image(image, caption="Uploaded Product Image"):
    img = Image.open(image)
    st.image(img, caption=caption, use_column_width=True)

# Step 3: Classify image to decide whether it contains fruits/vegetables or other products
def classify_image(sample_file):
    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")

    with st.spinner("Classifying the image..."):
        response = model.generate_content([sample_file,
            "check whether it is an image of vegetable/fruit, do not get confused by the images of fruits and vegetables that are there on the packet of packaged food items? Answer 'yes' or 'no' only."
        ])
    
    classification = response.text.strip().lower()
    return classification == "yes"

# Step 4: Predict freshness (for fruits and vegetables)
def predict_freshness(sample_file):
    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")

    with st.spinner("Predicting freshness..."):
        response = model.generate_content([sample_file,
            "Provide a number between 1 and 10 to indicate the freshness index of the fruits or vegetables in the image. Only output the number and nothing else."
        ])

    match = re.search(r'\b\d+\b', response.text.strip())
    if match:
        freshness_index = int(match.group(0))
        return freshness_index
    else:
        st.error("Error: No valid number found in the response.")
        return None

# Step 5: Generate product details (for other products)
def generate_product_details(sample_file):
    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")

    with st.spinner("Generating product details..."):
        response = model.generate_content([sample_file,
            f"Tell me the name of each product, its category among the following list of categories: {categories}, brand, MRP, manufacturer, expiry date, and quantity in the image. "
            "Do not output anything else. Output format for each product: "
            "Product Name: [Extracted Product name], Category: [Extracted Category], Brand: [Extracted Brand name], MRP: [Extracted MRP], Manufacturer: [Extracted Manufacturer name], "
            "Expiry Date: [Extracted Expiry Date], Quantity: [Extracted Quantity]. "
            "Separate the details of each product with one newline character. If some information is not available, output NA."
        ])

    return response.text.strip() if response else ""

# Step 6: Parse the response into a DataFrame
def parse_response_to_dataframe(response_text):
    columns = ["Product Name", "Category", "Brand", "MRP", "Manufacturer", "Expiry Date", "Quantity"]
    product_sections = response_text.split("\n")
    products_list = []

    for product_section in product_sections:
        product_details = {col: "NA" for col in columns}
        response_parts = product_section.split(", ")

        for part in response_parts:
            if "Product Name" in part:
                product_details["Product Name"] = part.split(": ")[1]
            elif "Category" in part:
                product_details["Category"] = part.split(": ")[1]
            elif "Brand" in part:
                product_details["Brand"] = part.split(": ")[1]
            elif "MRP" in part:
                product_details["MRP"] = part.split(": ")[1]
            elif "Manufacturer" in part:
                product_details["Manufacturer"] = part.split(": ")[1]
            elif "Expiry Date" in part:
                product_details["Expiry Date"] = part.split(": ")[1]
            elif "Quantity" in part:
                product_details["Quantity"] = part.split(": ")[1]

        products_list.append(product_details)

    return pd.DataFrame(products_list, columns=columns)

# Step 7: Style the DataFrame for better display (simplified)
def style_dataframe(df):
    return df.style.set_table_styles(
        [{'selector': 'td', 'props': [('border', '1px solid grey')]}]
    )

# Custom Animated Text (Replacement for streamlit-extras.animated_text)
def display_custom_animated_text(text):
    placeholder = st.empty()

    # Reveal text one character at a time
    for i in range(len(text)):
        placeholder.markdown(f"<h2>{text[:i+1]}</h2>", unsafe_allow_html=True)
        time.sleep(0.05)

# Combined Pipeline
def combined_pipeline(image):
    # Step 1: Custom animated text
    st.subheader("Step 1: Upload Image")
    display_custom_animated_text("🚀 Uploading and Processing Image...")

    # Step 1: Upload the image
    sample_file = upload_image(image)
    if not sample_file:
        st.error("Error uploading image.")
        return

    # Step 2: Classify whether the image contains fruits/vegetables
    st.subheader("Step 2: Classify Image")
    is_fruits_or_vegetables = classify_image(sample_file)

    # Display image
    display_image(image)

    if is_fruits_or_vegetables:
        st.subheader("Step 3: Predict Freshness for Fruits/Vegetables")
        display_custom_animated_text("🍏 Fruits or Vegetables detected. Predicting freshness...")
        
        # Predict freshness for fruits and vegetables
        freshness_index = predict_freshness(sample_file)
        if freshness_index is not None:
            st.success(f"The predicted freshness index is: {freshness_index}")
        else:
            st.error("Failed to predict freshness.")
    else:
        st.subheader("Step 3: Extract Product Details")
        display_custom_animated_text("📦 Products detected. Extracting details...")
        
        # Generate product details for other products
        response_text = generate_product_details(sample_file)
        if not response_text:
            st.error("No product details generated.")
            return

        # Parse and display product details in a DataFrame
        df = parse_response_to_dataframe(response_text)
        styled_df = style_dataframe(df)
        
        st.write("Product Details:")
        st.dataframe(styled_df)

# Streamlit UI
st.title("🛒 Product Image Classifier & Details Extractor")
st.markdown(
    """
    ***This tool helps you classify product images and extract essential product information like brand, MRP, and category.***
    ***It also predicts the freshness of fruits and vegetables if detected in the image.***
    """
)

# File uploader
uploaded_file = st.file_uploader("Upload an image of products or fruits/vegetables", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    with open("temp_image.jpg", "wb") as f:
        f.write(uploaded_file.getbuffer())
    combined_pipeline("temp_image.jpg")
