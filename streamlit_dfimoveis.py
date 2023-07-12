import streamlit as st
from time import sleep
import pandas as pd
import cloudscraper #faz a requisição pra receber os dados da pagina
from bs4 import BeautifulSoup #faz o tratamento do texto e extração por css
import re #para expressoes regulares
import timeit
import unidecode
import re
import numpy as np
import math as mat
import time
import time, datetime, os
import statsmodels.api as sm

def coleta_dfimoveis(url):
    ts=1
    scraper = cloudscraper.create_scraper()
    content = scraper.get(url).text
    soup = BeautifulSoup(content, 'html.parser')
    titulopag = soup.find('h1',class_ = "titulo-pagina").text
    if url.find("palavrachave") == -1:
        numimos = int(titulopag.split(" ")[1].replace(".",""))
    if url.find("palavrachave") != -1:
        titulopag = titulopag.split('"')[2]
        numimos = int(titulopag.split(" ")[1].replace(".",""))
    numpags = round(numimos/30)+1
    numpags = range(2,numpags+1)

    def varrer_pagina(urlpag):
        content = scraper.get(urlpag).text
        soup = BeautifulSoup(content, 'html.parser')
        
        links = pd.Series([f"https://www.dfimoveis.com.br{link['href']}" for link in soup.find_all('a', {"class":"new-card"}, href=True)])

        titulos= soup.find_all('h2', {"class":"new-title phrase"})
        titulos = pd.Series([titulo.text for titulo in titulos])
        

        precos = soup.find_all('div',{"class":"new-price"})
        precos = pd.Series([preco.text for preco in precos])

        areas = soup.find_all('li', {"class":"m-area"})
        areas = pd.Series([area.text for area in areas])

        detalhes = soup.find_all('ul', {"class":"new-details-ul"})
        detalhes = pd.Series([detalhe.text for detalhe in detalhes])

        creci_anunciante = soup.find_all("div",{"class":"creci"})
        creci_anunciante = pd.Series([creci.text for creci in creci_anunciante])

        data_pag = pd.DataFrame({"Titulo":titulos,"Área_Útil": areas,"Preço":precos,"CRECI_Anunciante":creci_anunciante,"Link":links,"Detalhes":detalhes})
        return data_pag

    dados = varrer_pagina(url)

    for i in numpags:
        if url.find("?") == -1:
            url2 = f"{url}?pagina={i}"
        else:
            url2 = f"{url}&pagina={i}"
        
        dataloop = varrer_pagina(url2)
        dados = pd.concat([dados,dataloop])
        
        time.sleep(ts)
    
    dados.index = range(0,len(dados))
    return(dados)


st.set_page_config(page_title="Analytics ImoApp")
with st.container():
    st.subheader("Trabalho para Computação em Estatística com Python")
    st.title("Análise de imóveis pesquisados - DFimóveis")
    st.write("Pesquise imóveis de interesse no site DFimóveis clicando [aqui.](https://www.dfimoveis.com.br/)")
    link = st.text_input("Feita a pesquisa, o site retornará a lista paginada de imóveis resultantes, copie o link da pesquisa e copie no campo abaixo :point_down:","https://www.dfimoveis.com.br/aluguel/df/brasilia/asa-norte/apartamento")
    dados_COLETA = coleta_dfimoveis(url=str(link))

dados = dados_COLETA
dados['Logradouro'] = dados["Titulo"].str.strip()
dados["Área_Útil"] = pd.to_numeric(pd.Series(dados["Área_Útil"].str.split(" ",expand=True).iloc[:,0].str.strip()))
dados["Detalhes"] = dados["Detalhes"].str.lower()
quartos = dados["Detalhes"].str.split("quarto",expand=True).iloc[:,0].str.split("\\n\\n\\n",expand=True).iloc[:,1].str.strip()
dados["Quartos"] = pd.to_numeric(quartos).fillna(0)
suites = dados["Detalhes"].str.extract("(\\n.*suíte)").iloc[:,0].str.replace("suíte","").str.replace("\\n","").str.strip()
dados["Suítes"] = pd.to_numeric(suites).fillna(0)
vagas = dados["Detalhes"].str.extract("(\\n.*vaga)").iloc[:,0].str.replace("vaga","").str.replace("\\n","").str.strip()
dados["Vagas"] = pd.to_numeric(vagas).fillna(0)
precos = dados["Preço"].str.replace("\\r\\n","").str.strip()
precos = precos.str.split("\\n",expand=True)
preco = precos.iloc[:,0].str.lower()
preco = preco.str.replace("(r\\$|\\.|a partir de|sob consulta|simular crédito)","").str.strip()
preco = preco.str.replace("r","").str.replace("$","").str.replace(".","")
dados["Preço"] = pd.to_numeric(preco)
dados["CRECI_Anunciante"] = dados["CRECI_Anunciante"].str.replace("\\nCreci:\\n","").str.replace("\\n","")

dados = dados.dropna(subset=["Área_Útil","Preço"])
dados = dados[dados["Área_Útil"]>0]
dados = dados[dados["Preço"]>0]
dados["Preço/m²"] = dados["Preço"]/dados["Área_Útil"]

dados = dados[["Logradouro","CRECI_Anunciante","Área_Útil","Quartos","Suítes","Vagas","Preço","Preço/m²","Link"]]
dados.index = range(len(dados))


with st.container():
    st.write(f"Foram coletados {len(dados_COLETA)} imóveis, e deles, {len(dados)} estão, aparentemente, com informações corretas e serão úteis para as análise seguintes:")


tabdesc,tabpred,tabop = st.tabs(["Análises Descritivas :bar_chart:","Análises Preditivas :dart:","Oportunidade :four_leaf_clover:"])

with tabdesc:
    with st.container():
        st.title("Análises Descritivas :bar_chart:")
        dados_teste = dados
        col1, col2, col3 = st.columns(3)
        col1.metric(label="Mínimo de Área", value=f'{round(dados["Área_Útil"].min(),2)} m²')
        col1.metric(label="Média de Área", value=f'{round(dados["Área_Útil"].mean(),2)} m²')
        col1.metric(label="Máximo de Área", value=f'{round(dados["Área_Útil"].max(),2)} m²')
        minpreco = round(float(dados["Preço"].min()),2)
        col2.metric(label="Mínimo de Preço", value=f'R$ {minpreco:,.2f}')
        mpreco = round(float(dados["Preço"].mean()),2)
        col2.metric(label="Média de Preço", value=f'R$ {mpreco:,.2f}')
        maxpreco = round(float(dados["Preço"].max()),2)
        col2.metric(label="Máximo de Preço", value=f'R$ {maxpreco:,.2f}')
        minprecom2 = round(float(dados["Preço/m²"].min()),2)
        col3.metric(label="Mínimo de Preço/m²", value=f'R$ {minprecom2:,.2f}')
        mprecom2 = round(float(dados["Preço/m²"].mean()),2)
        col3.metric(label="Média de Preço/m²", value=f'R$ {mprecom2:,.2f}')
        maxprecom2 = round(float(dados["Preço/m²"].max()),2)
        col3.metric(label="Máximo de Preço/m²", value=f'R$ {maxprecom2:,.2f}')
        
        tab1,tab2,tab3 = st.tabs(["Quartos","Suítes","Vagas"])
        with tab1:
            col1,col2,col3 = st.columns(3)
            qts = pd.DataFrame(dados["Quartos"].value_counts())
            qts["Frequency"] = qts.iloc[:,0]
            qts["Quartos"] = qts.index
            col1.bar_chart(qts, x = 'Quartos', y = 'Frequency')
            dtspreco = dados[["Quartos","Preço"]].groupby(['Quartos']).mean()
            dtspreco["Quartos"]=dtspreco.index
            col2.bar_chart(dtspreco, x = 'Quartos', y = 'Preço')
            dtspreco2 = dados[["Quartos","Preço/m²"]].groupby(['Quartos']).mean()
            dtspreco2["Quartos"]=dtspreco2.index
            col3.bar_chart(dtspreco2, x = 'Quartos', y = 'Preço/m²')
        
        with tab2:
            col1,col2,col3 = st.columns(3)
            qts = pd.DataFrame(dados["Suítes"].value_counts())
            qts["Frequency"] = qts.iloc[:,0]
            qts["Suítes"] = qts.index
            col1.bar_chart(qts, x = 'Suítes', y = 'Frequency')
            dtspreco = dados[["Suítes","Preço"]].groupby(['Suítes']).mean()
            dtspreco["Suítes"]=dtspreco.index
            col2.bar_chart(dtspreco, x = 'Suítes', y = 'Preço')
            dtspreco2 = dados[["Suítes","Preço/m²"]].groupby(['Suítes']).mean()
            dtspreco2["Suítes"]=dtspreco2.index
            col3.bar_chart(dtspreco2, x = 'Suítes', y = 'Preço/m²')

        with tab3:
            col1,col2,col3 = st.columns(3)
            qts = pd.DataFrame(dados["Vagas"].value_counts())
            qts["Frequency"] = qts.iloc[:,0]
            qts["Vagas"] = qts.index
            col1.bar_chart(qts, x = 'Vagas', y = 'Frequency')
            dtspreco = dados[["Vagas","Preço"]].groupby(['Vagas']).mean()
            dtspreco["Vagas"]=dtspreco.index
            col2.bar_chart(dtspreco, x = 'Vagas', y = 'Preço')
            dtspreco2 = dados[["Vagas","Preço/m²"]].groupby(['Vagas']).mean()
            dtspreco2["Vagas"]=dtspreco2.index
            col3.bar_chart(dtspreco2, x = 'Vagas', y = 'Preço/m²')

with tabpred:
    with st.container():
        st.title("Análises Preditivas :dart:")
        st.write("Para estimar preços de imóveis semelhantes aos da pesquisa feita, utiliza-se as variáveis numéricas Área_Útil, Quartos, Suítes e Vagas para traçar um modelo de regressão múltipla por Método dos Mínimos Quadrados Ordinários (MQO)")
        y=dados["Preço"]
        x=dados.iloc[:,[2,3,4,5]]
        x=sm.add_constant(x)
        variaveis = []
        list_aics = []
        interacoes = [[0,1],[0,2],[0,3],[0,4],
                    [0,1,2],[0,1,3],[0,1,4],[0,2,3],[0,2,4],[0,3,4],
                    [0,1,2,3],[0,1,2,4],[0,1,3,4],[0,2,3,4],
                    [0,1,2,3,4]]
        
        for i in range(0,len(interacoes)):
            vars= interacoes[i]
            x_ = x.iloc[:,vars]
            results = sm.OLS(y,x_).fit()
            list_aics.append(results.aic)
            variaveis.append(interacoes[i])#list(x.columns[interacoes[i]]))
        dt=pd.DataFrame({"AICs":list_aics,"Variaveis":variaveis})

        dt=dt[dt.AICs == dt.AICs.min()]
        variaveis_select = dt.iloc[0,1]
        x_def = x.iloc[:,variaveis_select]
        resultsdef = sm.OLS(y,x_def).fit()

        dt_params = pd.DataFrame({"Parâmetros":pd.Series(resultsdef.params),
                                  "P-Valores":pd.Series(resultsdef.pvalues)})
        vars = ""
        for i in range(1,len(dt_params.index)):
            vars = vars + ", " + dt_params.index[i]
        
        st.write(f"As variáveis selecionadas pela metodologia de StepWise foram: {vars}. E os parâmetros estimados para o modelo foram:")
        st.dataframe(dt_params)











with st.container():
    st.write("----")
    st.write("Aqui estão os dados limpos:")
    st.dataframe(dados)
    #dadosdownload = dados
   # @st.cache_data
    #def convert_df(df):
    #    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    #    return df.to_csv().encode('utf-8')

    #csv = convert_df(dados)

    #st.download_button(
    #    label="Download data as CSV",
     #   data=csv,
     #   file_name='Dados_Limpos.csv',
     #   mime='text/csv'
    #)























