import streamlit as st

st.set_page_config(layout="wide")

st.title("Balança Comercial de Santa Catarina")
st.markdown("Bem-vindo! O aplicativo está funcionando corretamente. O problema de renderização está sendo corrigido.")
st.write("---")
st.write("Se você está vendo esta página, significa que o aplicativo está rodando. O problema provavelmente é com as dependências do Pydeck/Plotly. Estamos trabalhando para resolver isso.")

# Adicione esta linha para criar uma barra lateral vazia
st.sidebar.markdown("# Sobre")
st.sidebar.info("Este é um aplicativo para visualizar a balança comercial de Santa Catarina. Problemas técnicos serão resolvidos em breve.")

# Em um projeto real, você colocaria o código completo da sua aplicação aqui,
# dentro de uma estrutura que lida com possíveis erros de renderização.
# Por exemplo, usando try-except, mas como já fizemos isso, a melhor
# abordagem é simplificar para isolar o problema.

st.balloons()
