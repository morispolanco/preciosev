import streamlit as st
import requests
import json
import hashlib
from datetime import datetime

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'users' not in st.session_state:
    st.session_state.users = {'admin': hashlib.sha256('password'.encode()).hexdigest()}
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Login function
def login(username, password):
    if username in st.session_state.users and st.session_state.users[username] == hash_password(password):
        st.session_state.logged_in = True
        st.session_state.current_user = username
        return True
    return False

# Logout function
def logout():
    st.session_state.logged_in = False
    st.session_state.current_user = None

# Function to add new user (admin only)
def add_user(username, password):
    if username not in st.session_state.users:
        st.session_state.users[username] = hash_password(password)
        return True
    return False

# Function to call Serper API
def search_serper(query):
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": query
    })
    headers = {
        'X-API-KEY': st.secrets['SERPER_API_KEY'],
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()

# Function to call Together API
def process_with_together(prompt):
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {st.secrets['TOGETHER_API_KEY']}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2512,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "repetition_penalty": 1,
        "stop": ["<|eot_id|>"]
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code}, {response.text}"

# Page configuration
st.set_page_config(page_title="Precios de Productos en Guatemala", page_icon="🛒")

# Login/Logout UI
if not st.session_state.logged_in:
    st.title("Inicio de Sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar Sesión"):
        if login(username, password):
            st.success("Inicio de sesión exitoso!")
        else:
            st.error("Usuario o contraseña incorrectos")
else:
    # Main application UI (only shown when logged in)
    st.title("Comparación de Precios de Productos en Guatemala")
    
    st.sidebar.button("Cerrar Sesión", on_click=logout)

    if st.session_state.current_user == 'admin':
        st.sidebar.title("Panel de Administrador")
        with st.sidebar.expander("Agregar Nuevo Usuario"):
            new_username = st.text_input("Nuevo Usuario")
            new_password = st.text_input("Nueva Contraseña", type="password")
            if st.button("Agregar Usuario"):
                if add_user(new_username, new_password):
                    st.success(f"Usuario {new_username} agregado exitosamente")
                else:
                    st.error("El usuario ya existe")

    # Main content
    st.write(f"Fecha de consulta: {datetime.now().strftime('%d/%m/%Y')}")

    producto = st.text_input("Ingrese el nombre del producto a consultar:")

    if st.button("Buscar Precios"):
        if producto:
            with st.spinner(f"Buscando precios de {producto} en diferentes mercados de Guatemala..."):
                # Use Serper to search for recent information
                search_results = search_serper(f"precio {producto} mercados Guatemala " + datetime.now().strftime("%B %Y"))
                
                # Process the search results with Together API
                prompt = f"""
                Analiza la siguiente información sobre los precios de {producto} en diferentes mercados de Guatemala:

                {json.dumps(search_results, indent=2)}

                Proporciona un resumen en forma de tabla con las siguientes columnas:
                1. Mercado
                2. Precio (en Quetzales)
                3. Fecha del precio (si está disponible)

                Asegúrate de incluir el precio más bajo y el más alto encontrados.
                Al final de la tabla, proporciona una lista de las fuentes utilizadas para esta información.

                Presenta la información en formato Markdown para que pueda ser fácilmente mostrada en Streamlit.
                """
                
                analysis = process_with_together(prompt)
                st.markdown(analysis)
        else:
            st.warning("Por favor, ingrese el nombre de un producto.")

    # Instructions
    st.sidebar.header("Instrucciones")
    st.sidebar.write("""
    1. Ingrese el nombre del producto que desea consultar.
    2. Haga clic en el botón "Buscar Precios" para obtener la información.
    3. Se mostrará una tabla con los precios en diferentes mercados.
    4. Al final de la tabla encontrará las fuentes de la información.
    """)

    # Note about the APIs
    st.sidebar.info("Esta aplicación utiliza las APIs de Serper y Together para buscar y procesar información sobre precios.")
