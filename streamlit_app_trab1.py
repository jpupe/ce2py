import pandas as pd
import numpy as np
import streamlit as st

st.set_page_config(page_title="Dados Olist")

with st.container():
    st.subheader("Trabalho para Computação em Estatística com Python")
    st.title("Análise de Pedidos - Olist Store")
    st.write("As bases de dados relacionais utilizadas para as análises a seguir estão disponíveis [aqui.](https://github.com/edunb01/dotfiles)")
    st.write("Esse banco de dados é aberto e vem da plataforma Olist, onde empresas podem vender seus produtos na internet com benefícios como: ampliar o alcance da sua loja no ambiente digital, fazer a gestão estratégica das operações e ter garantia de transações seguras.")
    st.write("----")


clientes = pd.read_csv("https://raw.githubusercontent.com/edunb01/dotfiles/master/olist_customers_dataset.csv")
itens= pd.read_csv("https://raw.githubusercontent.com/edunb01/dotfiles/master/olist_order_items_dataset.csv")
pagamentos = pd.read_csv("https://raw.githubusercontent.com/edunb01/dotfiles/master/olist_order_payments_dataset.csv")
avaliacoes = pd.read_csv("https://raw.githubusercontent.com/edunb01/dotfiles/master/olist_order_reviews_dataset.csv ")
pedidos = pd.read_csv("https://raw.githubusercontent.com/edunb01/dotfiles/master/olist_orders_dataset.csv")
produtos = pd.read_csv("https://raw.githubusercontent.com/edunb01/dotfiles/master/olist_products_dataset.csv")
vendedores    = pd.read_csv("https://raw.githubusercontent.com/edunb01/dotfiles/master/olist_sellers_dataset.csv")

data_1 = pedidos.merge(itens, how="left",on=["order_id"])
data_1 = data_1.merge(clientes, how="left",on=["customer_id"])
pagamentos2 = pagamentos[pagamentos["payment_sequential"]==1]
data_1 = data_1.merge(pagamentos2, how="left",on=["order_id"])


with st.container():
    st.write("Clientes que mais compraram/gastaram")
    ################# Q1
    dt1= data_1

    possiveispags = pd.dropna(dt1["payment_type"]).unique().tolist()
    #possiveispags = possiveispags.append("all")
    pags_selectbox = st.multiselect("Selecione o(s) tipo(s) de pagamento(s)",list(possiveispags),list(possiveispags))
    pags_selectbox = list(pags_selectbox)
    
    dt1 = dt1[dt1["payment_type"].isin(pags_selectbox)]

    count_clients = pd.DataFrame(dt1["customer_unique_id"].value_counts())
    count_clients.columns = [["Quantidade"]]
    count_clients["customer_unique_id"] = count_clients.index

    dt1["Valor gasto (R$)"]= dt1["price"]+dt1["freight_value"]
    gastos = dt1[["customer_unique_id","Valor gasto (R$)"]].groupby("customer_unique_id").sum()
    gastos["customer_unique_id"] = gastos.index
    gastos.index = range(len(gastos.index))
    count_clients.index = range(len(count_clients.index))
    count_clients.columns = ["Quantidade","customer_unique_id"]

    contclient = count_clients.merge(gastos,how="left",on="customer_unique_id")
    contclient = contclient[["customer_unique_id","Quantidade","Valor gasto (R$)"]]
    ##################
    st.dataframe(contclient)


with st.container():
    st.write("Produtos entregues com atraso")




with st.container():
    st.write("Compras/Preços por categoria")
    

with st.container():
    st.write("Produtos por preço/nº de vendas")
    

with st.container():
    st.write("Avaliações por notas")
    

with st.container():
    st.write("Avaliações por texto")
    


with st.container():
    st.write("Pedidos por dia da semana")
    


with st.container():
    st.write("Localização x Preços")
    
















































