import streamlit as st
import cv2
import numpy as np
import os
import base64
import hashlib
import tempfile
from cryptography.fernet import Fernet

# Function to generate a secure encryption key from a password
def generate_key(password):
    key = hashlib.sha256(password.encode()).digest()  # Create 32-byte hash
    return base64.urlsafe_b64encode(key)  # Convert to Fernet-compatible format

# Convert text to binary
def text_to_binary(text):
    return ''.join(format(ord(char), '08b') for char in text)

# Convert binary to text
def binary_to_text(binary):
    return ''.join(chr(int(binary[i:i+8], 2)) for i in range(0, len(binary), 8))

# Encrypt the message
def encrypt_message(message, password):
    key = generate_key(password)
    cipher = Fernet(key)
    encrypted = cipher.encrypt(message.encode())
    return encrypted.decode()

# Decrypt the message
def decrypt_message(encrypted_message, password):
    try:
        key = generate_key(password)
        cipher = Fernet(key)
        decrypted = cipher.decrypt(encrypted_message.encode()).decode()
        return decrypted
    except Exception:
        return "Invalid Password or Corrupted Data"

# Function to hide secret data in an image
def hide_data(image_path, secret_message, password):
    img = cv2.imread(image_path)
    if img is None:
        return None, "Error: Image not found!"

    encrypted_msg = encrypt_message(secret_message, password)
    binary_secret = text_to_binary(encrypted_msg) + '1111111111111110'  # End marker

    data_index = 0
    total_pixels = img.shape[0] * img.shape[1] * 3  # Total number of channels (R, G, B)

    if len(binary_secret) > total_pixels:
        return None, "Error: Image is too small to hide this message!"

    for row in img:
        for pixel in row:
            for channel in range(3):  # Modify R, G, B values
                if data_index < len(binary_secret):
                    pixel[channel] = pixel[channel] & ~1 | int(binary_secret[data_index])
                    data_index += 1

    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    cv2.imwrite(output_path, img)
    return output_path, "Secret message hidden successfully!"

# Function to retrieve hidden data from an image
def retrieve_data(image_path, password):
    img = cv2.imread(image_path)
    if img is None:
        return "Error: Image not found!"

    binary_secret = ""
    for row in img:
        for pixel in row:
            for channel in range(3):
                binary_secret += str(pixel[channel] & 1)

    end_marker = "1111111111111110"
    if end_marker in binary_secret:
        binary_secret = binary_secret[:binary_secret.index(end_marker)]
    else:
        return "Error: No hidden data found!"

    encrypted_msg = binary_to_text(binary_secret)
    decrypted_msg = decrypt_message(encrypted_msg, password)
    
    return decrypted_msg

# Streamlit App UI
st.title("🔐 Image Steganography App")
st.write("Hide and retrieve secret messages in images securely!")

# Tabs for hiding and retrieving data
tab1, tab2 = st.tabs(["🖼️ Hide Data", "🔍 Retrieve Data"])

with tab1:
    st.subheader("Hide a Secret Message in an Image")

    uploaded_image = st.file_uploader("Upload an image (PNG/JPG)", type=["png", "jpg", "jpeg"])
    secret_message = st.text_area("Enter the secret message:")
    password = st.text_input("Set a password for encryption", type="password")

    if uploaded_image and secret_message and password:
        if st.button("Hide Message"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_img:
                temp_img.write(uploaded_image.read())
                temp_img_path = temp_img.name

            output_image, msg = hide_data(temp_img_path, secret_message, password)
            if output_image:
                st.success(msg)
                with open(output_image, "rb") as file:
                    st.download_button(label="📥 Download Image with Hidden Message",
                                       data=file, file_name="stego_image.png", mime="image/png")
            else:
                st.error(msg)

with tab2:
    st.subheader("Retrieve Hidden Message from an Image")

    uploaded_encoded_image = st.file_uploader("Upload an image with hidden data", type=["png", "jpg", "jpeg"])
    password_for_decoding = st.text_input("Enter the password to decode", type="password")

    if uploaded_encoded_image and password_for_decoding:
        if st.button("Retrieve Message"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_img:
                temp_img.write(uploaded_encoded_image.read())
                temp_img_path = temp_img.name

            hidden_message = retrieve_data(temp_img_path, password_for_decoding)
            if "Error" in hidden_message:
                st.error(hidden_message)
            else:
                st.success(f"🔓 Hidden Message: {hidden_message}")
