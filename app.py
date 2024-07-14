import streamlit as st 
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import time
import bcrypt
import datetime
import re
import pytz
import time

import mysql.connector

#st.set_page_config(layout="wide")

mydb = mysql.connector.connect(
  host = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
  port = 4000,
  user = "2qLpHd1msvnQLLk.root",
  password = "15zfn6vuMMwT2HXJ"
)
mycursor = mydb.cursor(buffered=True)
mycursor.execute('USE GUVI_DB')

# Check if username exists in the database
def username_exists(username):
    mycursor.execute("SELECT * FROM USERS_DATA WHERE username = %s", (username,))
    return mycursor.fetchone() is not None

# Check if email exists in the database
def email_exists(email):
    mycursor.execute("SELECT * FROM USERS_DATA WHERE email = %s", (email,))
    return mycursor.fetchone() is not None

# Validate email format using regular expressions
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Create a new user in the database
def create_user(username, password, email):
    if username_exists(username):
        return 'username_exists'
    
    if email_exists(email):
        return 'email_exists'
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    registered_date = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))

    # Insert user data into 'users' table
    mycursor.execute(
        "INSERT INTO USERS_DATA (username, password, email, registered_date) VALUES (%s, %s, %s, %s)",
        (username, hashed_password, email, registered_date)
    )
    mydb.commit()
    return 'success'

# Verify user credentials
def verify_user(username, password):
    mycursor.execute("SELECT password FROM USERS_DATA WHERE username = %s", (username,))
    record = mycursor.fetchone()
    if record and bcrypt.checkpw(password.encode('utf-8'), record[0].encode('utf-8')):
        # Update last login timestamp
        mycursor.execute("UPDATE USERS_DATA SET last_login = %s WHERE username = %s", (datetime.datetime.now(pytz.timezone('Asia/Kolkata')), username))
        mydb.commit()
        return True
    return False

# Reset user password
def reset_password(username, new_password):
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    # Update password in 'users' table
    mycursor.execute(
        "UPDATE USERS_DATA SET password = %s WHERE username = %s",
        (hashed_password, username)
    )
    mydb.commit()

# Session state management
if 'sign_up_successful' not in st.session_state:
    st.session_state.sign_up_successful = False
if 'login_successful' not in st.session_state:
    st.session_state.login_successful = False
if 'reset_password' not in st.session_state:
    st.session_state.reset_password = False
if 'username' not in st.session_state:
    st.session_state.username = ''
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'login'


# Login form
def login():
    st.subheader(':blue[**Login**]')
    with st.form(key='login', clear_on_submit=True):
        st.write(":red[Enter your username and password below.]")
        
        # Input fields for username and password
        username = st.text_input(label=':silver[USERNAME]', placeholder='Enter Your Username')
        password = st.text_input(label=':silver[PASSWORD]', placeholder='Enter Your Password', type='password')
        
        if st.form_submit_button('Login'):
            if not username or not password:
                st.error("Please fill out all fields.")
            elif verify_user(username, password):
                st.session_state.login_successful = True
                st.session_state.username = username
                st.session_state.current_page = 'home'
                st.rerun()
            else:
                st.error("Incorrect username or password. If you don't have an account, please sign up.")
                
    # Display sign-up and reset password button
    if not st.session_state.login_successful:
        c1, c2 = st.columns(2)
        with c1:
            st.write(":red[New user]")
            if st.button('Sign Up'):
                st.session_state.current_page = 'sign_up'
                st.rerun()
        with c2:
            st.write(":red[Forgot Password]")
            if st.button('Reset Password'):
                st.session_state.current_page = 'reset_password'
                st.rerun()


# Sign-up form
def signup(): 
    st.subheader(':blue[**Sign Up**]')
    with st.form(key='signup', clear_on_submit=True):
        st.write(":red[Enter the required fields to create a new account.]")

        # Input fields for email, username, and password
        email = st.text_input(label=':silver[Email]', placeholder='Enter Your Email')
        username = st.text_input(label=':silver[Username]', placeholder='Enter Your Username')
        password = st.text_input(label=':silver[Password]', placeholder='Enter Your Password', type='password')
        re_password = st.text_input(label=':silver[Confirm Password]', placeholder='Confirm Your Password', type='password')
        
        co1,co2=st.columns(2)
        with co1:
            if st.form_submit_button('Sign Up'):
                if not email or not username or not password or not re_password:
                    st.error("Please fill out all required fields.")
                elif not is_valid_email(email):
                    st.error("Please enter a valid email address.")
                elif len(password) <= 3:
                    st.error("Password too short")
                elif password != re_password:
                    st.error("Passwords does not match. Please re-enter.")
                else:
                    result = create_user(username, password, email)
                    if result == 'username_exists':
                        st.error("Username already registered. Please use a different username.")
                    elif result == 'email_exists':
                        st.error("Email already registered. Please use a different email.")
                    elif result == 'success':
                        st.success(f"Username {username} created successfully! Please login.")
                        st.session_state.sign_up_successful = True
                    else:
                        st.error("Failed to create user. Please try again later.")
        with co2: 
            if st.form_submit_button('Login'):
                st.session_state.current_page = 'login'
                st.rerun()
    if st.session_state.sign_up_successful:
        if st.button(':Red[Go to Login]'):
            st.session_state.current_page = 'login'
            st.rerun()


# Reset password form
def reset_password_page():
    st.subheader(':blue[Reset Password]')
    with st.form(key='reset_password', clear_on_submit=True):
        st.write(":red[Enter your username and new password below.]")

        # Input fields for username and new password       
        username = st.text_input(label=':silver[Username]', value='')
        new_password = st.text_input(label=':silver[New Password]', type='password')
        re_password = st.text_input(label=':silver[Confirm New Password]', type='password')

        if st.form_submit_button(':red[Reset Password]'):
            if not username:
                st.error("Please enter your username.")
            elif not username_exists(username):
                st.error("Username not found. Please enter a valid username.")
            elif not new_password or not re_password:
                st.error("Please fill out all required fields.")
            elif len(new_password) <= 3:
                st.error("Password too short")
            elif new_password != re_password:
                st.error("Passwords does not match. Please re-enter.")
            else:
                reset_password(username, new_password)
                st.success("Password reset successfully. Please login with your new password.")
                st.session_state.current_page = 'login'

    # Button to return to login page
    st.write(':red[Return to Login page]')
    if st.button('Login'):
        st.session_state.current_page = 'login'
        st.rerun() 

# CSS for glittering effect
glitter_css = """
<style>
@keyframes glitter {
  0%, 100% {
    text-shadow: 0 0 5px #ff00ff, 0 0 10px #ff00ff, 0 0 20px #ff00ff, 0 0 40px #ff00ff, 0 0 80px #ff00ff, 0 0 90px #ff00ff, 0 0 100px #ff00ff, 0 0 150px #ff00ff;
  }
  50% {
    text-shadow: 0 0 5px #00ff00, 0 0 10px #00ff00, 0 0 20px #00ff00, 0 0 40px #00ff00, 0 0 80px #00ff00, 0 0 90px #00ff00, 0 0 100px #00ff00, 0 0 150px #00ff00;
  }
}

.glitter {
  font-size: 40px;
  font-weight: normal;
  color: #fff;
  animation: glitter 4s infinite alternate;
}
</style>
"""

# Apply the CSS to the Streamlit app
st.markdown(glitter_css, unsafe_allow_html=True)

# Title with glitter effect
st.markdown('<h1 class="glitter">GUVI GPT Model - Text Generator</h1>', unsafe_allow_html=True)

#st.subheader('GUVI GPT Model - Text Generator') 


# Load the fine-tuned model and tokenizer
model_name_or_path = "./fine_tuned_model"
model = GPT2LMHeadModel.from_pretrained(model_name_or_path)
tokenizer = GPT2Tokenizer.from_pretrained(model_name_or_path)

# Set the pad_token to eos_token if it's not already set
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Move the model to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)


# Define the text generation function
def generate_text(model, tokenizer, seed_text, max_length=100, temperature=1.0, num_return_sequences=1):
    # Tokenize the input text with padding
    inputs = tokenizer(seed_text, return_tensors='pt', padding=True, truncation=True)

    input_ids = inputs['input_ids'].to(device)
    attention_mask = inputs['attention_mask'].to(device)

    # Generate text
    with torch.no_grad():
        output = model.generate(
            input_ids,
            attention_mask=attention_mask,
            max_length=max_length,
            temperature=temperature,
            num_return_sequences=num_return_sequences,
            do_sample=True,
            top_k=50,
            top_p=0.50,
            pad_token_id=tokenizer.eos_token_id  # Ensure padding token is set to eos_token_id
        )

    # Decode the generated text
    generated_texts = []
    for i in range(num_return_sequences):
        generated_text = tokenizer.decode(output[i], skip_special_tokens=True)
        generated_texts.append(generated_text)

    return generated_texts

#home page
def home_page():
    
    disclaimer_message = 'Disclaimer: Various online papers were the basis of the model data. Performance may be differ based on the relevancy and quality of the data'
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.username}")

        st.markdown('<br>',unsafe_allow_html=True)

        st.write("### Example Prompts")
        st.markdown(''' Guvi is an <br> Guvi history and founder <br> Guvi Zen class <br> Guvi Teaching Methodology <br> Guvi Zen class features codekata <br> What is the capstone Project <br> Guvi commitment to student''',unsafe_allow_html=True)

        st.markdown('<br>',unsafe_allow_html=True)

        max=st.select_slider('Max length',options=[10, 25, 50,75,100,125,150,175,200])

        if st.button("Logout"):
            st.session_state.clear()
            st.session_state.current_page = 'login'
            st.rerun() 
    st.markdown(f'<div class="ticker-wrap"><div class="ticker-item">{disclaimer_message}</div></div>', unsafe_allow_html=True)


    if prompt := st.chat_input("What up?"):
    
        with st.chat_message("user"):
            st.markdown(prompt)
    
        with st.chat_message("assistant"):
            generated_texts = generate_text(model, tokenizer, seed_text=prompt, max_length=max, temperature=0.7, num_return_sequences=1)
            # Define the generator function
            def generate_text_with_delay(generated_texts):
                for word in generated_texts:
                    yield word + " "
                    time.sleep(0.5)
            
            st.write(generate_text_with_delay(generated_texts))

# Display appropriate page based on session state
if st.session_state.current_page == 'home':
    home_page()
elif st.session_state.current_page == 'login':
    login()
elif st.session_state.current_page == 'sign_up':
    signup()
elif st.session_state.current_page == 'reset_password':
    reset_password_page()
