import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

# Configuración de la página
st.set_page_config(page_title="Gráfica de Precios en Guatemala", layout="wide")

# Función para obtener datos de precios
def get_price_data(product):
    api_key = st.secrets["SERPER_API_KEY"]
    
    # Calcular la fecha de hace un año
    one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    # Consulta de búsqueda
    query = f"precio de {product} en Guatemala desde {one_year_ago}"
    
    url = "https://google.serper.dev/search"
    
    payload = {
        "q": query,
        "gl": "gt"
    }
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error al obtener datos: {response.status_code}")
        return None

# Función para procesar los datos y crear un DataFrame
def process_data(data):
    prices = []
    dates = []
    
    for item in data.get('organic', []):
        title = item.get('title', '')
        snippet = item.get('snippet', '')
        
        # Buscar precios en el título y snippet
        price_info = [info for info in [title, snippet] if "Q" in info]
        
        if price_info:
            # Extraer el precio
            price = price_info[0].split("Q")[1].split()[0]
            try:
                price = float(price.replace(',', ''))
                prices.append(price)
                
                # Extraer la fecha (asumiendo que está en formato "DD MMM YYYY")
                date_str = snippet.split()[-3:]
                date = datetime.strptime(' '.join(date_str), "%d %b %Y")
                dates.append(date)
            except:
                pass
    
    return pd.DataFrame({'fecha': dates, 'precio': prices}).sort_values('fecha')

# Interfaz de usuario
st.title("Gráfica de Precios en Guatemala")

product = st.text_input("Ingrese el nombre del producto:")

if st.button("Generar Gráfica"):
    if product:
        with st.spinner("Obteniendo datos..."):
            data = get_price_data(product)
            
        if data:
            df = process_data(data)
            
            if not df.empty:
                st.success("Datos obtenidos con éxito!")
                
                # Crear la gráfica
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.plot(df['fecha'], df['precio'])
                ax.set_xlabel('Fecha')
                ax.set_ylabel('Precio (Q)')
                ax.set_title(f'Precio de {product} en Guatemala - Último Año')
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                st.pyplot(fig)
            else:
                st.warning("No se encontraron datos de precios para este producto.")
    else:
        st.warning("Por favor, ingrese el nombre de un producto.")
