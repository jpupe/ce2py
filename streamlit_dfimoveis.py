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
import scipy
from PIL import Image

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
    #st.subheader("Trabalho para Computação em Estatística com Python")
    coltitulo,colimagem = st.columns(2)
    with coltitulo:
        st.subheader("Análise de imóveis pesquisados - DFimóveis")
    with colimagem:
        image = Image.open("logo_colorida.png")
        st.image(image)
    st.write("Pesquise imóveis de interesse no site DFimóveis clicando [aqui.](https://www.dfimoveis.com.br/)")
    link = st.text_input("Feita a pesquisa, o site retornará a lista paginada de imóveis resultantes, copie o link da pesquisa e cole no campo abaixo :point_down:","https://www.dfimoveis.com.br/aluguel/df/brasilia/noroeste/apartamento?palavrachave=sqnw")
    dados_COLETA = coleta_dfimoveis(url=str(link))

dados = dados_COLETA
dados['Logradouro'] = dados["Titulo"].str.strip()
dados["Área_Útil"] = pd.to_numeric(pd.Series(dados["Área_Útil"].str.split(" ",expand=True).iloc[:,0].str.strip()))
dados["Detalhes"] = dados["Detalhes"].str.lower()

dados["Conferir_detalhes"] = dados["Detalhes"].str.find("m²")
dados = dados[dados["Conferir_detalhes"] != -1]

quartos = dados["Detalhes"].str.split("quarto",expand=True).iloc[:,0].str.split("\\n\\n\\n",expand=True).iloc[:,1].str.strip()
dados["Quartos"] = pd.to_numeric(quartos).fillna(0)
suites = dados["Detalhes"].str.extract("(\\n.*suíte)").iloc[:,0].str.replace("suíte","").str.replace("\\n","").str.strip()
dados["Suítes"] = pd.to_numeric(suites).fillna(0)
vagas = dados["Detalhes"].str.extract("(\\n.*vaga)").iloc[:,0].str.replace("vaga","").str.replace("\\n","").str.strip()
dados["Vagas"] = pd.to_numeric(vagas).fillna(0)
precos = dados["Preço"].str.replace("\\r\\n","").str.strip()
precos = precos.str.split("\\n",expand=True)
preco = precos.iloc[:,0].str.lower()
preco = preco.str.replace("a partir de","").str.replace("sob consulta","").str.replace("simular crédito","").str.replace("r","").str.replace("$","").str.replace(".","")
dados["Preço"] = pd.to_numeric(preco)
dados["CRECI_Anunciante"] = dados["CRECI_Anunciante"].str.replace("\\nCreci:\\n","").str.replace("\\n","")

dados = dados.dropna(subset=["Área_Útil","Preço"])
dados = dados[dados["Área_Útil"]>0]
dados = dados[dados["Preço"]>0]
dados["Preço/m²"] = dados["Preço"]/dados["Área_Útil"]

dados = dados[["Logradouro","Área_Útil","Quartos","Suítes","Vagas","Preço","Preço/m²","Link"]]

area_quantis = scipy.stats.mstats.mquantiles(dados["Área_Útil"])
LI_area = area_quantis[0] - 1.5 * (area_quantis[2]-area_quantis[0])
LS_area = area_quantis[2] + 1.5 * (area_quantis[2]-area_quantis[0])

preco_quantis = scipy.stats.mstats.mquantiles(dados["Preço"])
LI_preco = preco_quantis[0] - 1.5 * (preco_quantis[2]-preco_quantis[0])
LS_preco = preco_quantis[2] + 1.5 * (preco_quantis[2]-preco_quantis[0])

precom2_quantis = scipy.stats.mstats.mquantiles(dados["Preço/m²"])
LI_precom2 = precom2_quantis[0] - 1.5 * (precom2_quantis[2]-precom2_quantis[0])
LS_precom2 = precom2_quantis[2] + 1.5 * (precom2_quantis[2]-precom2_quantis[0])


dados = dados[dados["Área_Útil"]>= LI_area]
dados = dados[dados["Área_Útil"]<= LS_area]
dados = dados[dados["Preço"]>= LI_preco]
dados = dados[dados["Preço"]<= LS_preco]
dados = dados[dados["Preço/m²"]>= LI_precom2]
dados = dados[dados["Preço/m²"]<= LS_precom2]

dados.index = range(len(dados))


with st.container():
    st.write(f"Foram coletados {len(dados_COLETA)} imóveis, e deles, {len(dados)} estão, aparentemente, com informações corretas e serão úteis para as análise seguintes:")


tabdesc,tabpred,tabmet = st.tabs(["Análises Descritivas :bar_chart:","Análises Preditivas :dart:","Metodologias :memo:"])

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
        x=dados.iloc[:,[1,2,3,4]]
        x=sm.add_constant(x)
        variaveis = []
        list_aics = []
        interacoes = [[0,1],#[0,2],[0,3],[0,4],
                    [0,1,2],[0,1,3],[0,1,4],#[0,2,3],[0,2,4],[0,3,4],
                    [0,1,2,3],[0,1,2,4],[0,1,3,4],#[0,2,3,4],
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
        r2 = resultsdef.rsquared_adj
        if f"{round(r2*100,2)}%" == "nan%":
            r2 = 0

        dt_params = pd.DataFrame({"Parâmetros":pd.Series(resultsdef.params),
                                  "P-Valores":pd.Series(resultsdef.pvalues)})
        dt_params["Variável"] = dt_params.index
        dt_params = dt_params[["Variável","Parâmetros"]]

        dt_params_completa = pd.DataFrame({"Variável":["const","Área_Útil","Quartos","Suítes","Vagas"]})
        dt_params_completa = dt_params_completa.merge(dt_params,how="left",on=["Variável"])
        dt_params_completa["Parâmetros"] = dt_params_completa["Parâmetros"].fillna(0)

        vars = ""
        for i in range(1,len(dt_params.index)):
            vars = vars + dt_params.index[i] + ", "
        
        st.write(f"As variáveis selecionadas pela metodologia de StepWise (utilizando o critério de AICs) foram: {vars}e os parâmetros estimados para o modelo foram:")
        dt_params.index=range(len(dt_params.index))
        st.dataframe(dt_params)
        st.write(f"O R-quadrado ajustado do modelo foi {round(r2,2)}, logo, a(s) variável(is) selecionada(s) foram capazes de explicar aproximadamente {round(round(r2,2)*100)}% da variabilidade do preço dos imóveis.")
        if r2<0.5:
            st.write("O R-quadrado ajustado do modelo não está legal :confused:, provavelmente sua amostra não está específica ou significativa o suficiente, indicamos que faça uma nova pesquisa no site, filtrando uma amostra melhor, e dessa maneira renove o link aqui no app :wink:")
        if r2 > 0.5:
            st.write("O modelo aparentemente está explicando bem a variabilidade dos preços :grin:")
            st.write("Estime agora o valor de um imóvel :point_down:")
            colarea,colquartos,colsuites,colvagas = st.columns(4)
            area = colarea.number_input("Área útil",0)
            nquartos = colquartos.number_input("Nº de quartos",0)
            nsuites = colsuites.number_input("Nº de suítes",0)
            nvagas = colvagas.number_input("Nº de vagas",0)

            precoest = (dt_params_completa[dt_params_completa["Variável"]=="const"].iloc[0,1] + 
                     dt_params_completa[dt_params_completa["Variável"]=="Área_Útil"].iloc[0,1]*area +
                     dt_params_completa[dt_params_completa["Variável"]=="Quartos"].iloc[0,1]*nquartos +
                     dt_params_completa[dt_params_completa["Variável"]=="Suítes"].iloc[0,1]*nsuites + 
                     dt_params_completa[dt_params_completa["Variável"]=="Vagas"].iloc[0,1]*nvagas)
            
            st.metric(label="Preço estimado", value=f'R$ {precoest:,.2f}')

            

            





with tabmet:
    with st.container():
        st.title("Metodologias :memo:")
        st.subheader("Regressão Linear")
        st.write("A regressão linear é uma técnica estatística utilizada para modelar a relação entre uma variável dependente contínua e uma ou mais variáveis independentes. Na regressão linear simples, há apenas uma variável independente, enquanto na regressão linear múltipla, existem várias variáveis independentes. O objetivo é encontrar uma equação linear que melhor represente a relação entre essas variáveis, minimizando a diferença entre os valores observados e os valores previstos. Essa equação pode ser usada para fazer previsões ou inferências sobre os valores da variável dependente com base nas variáveis independentes. A regressão linear é amplamente utilizada em diversos campos, como economia, ciências sociais e engenharia, para analisar e entender as relações entre variáveis.")
        st.subheader("Mínimos Quadrados Ordinários")
        st.write("O método dos mínimos quadrados ordinários é uma técnica estatística utilizada na regressão linear para estimar os coeficientes da equação linear que melhor se ajusta aos dados observados. O método busca minimizar a soma dos quadrados dos resíduos, que são as diferenças entre os valores observados e os valores previstos pela equação de regressão. Para isso, ele calcula os coeficientes que reduzem ao máximo essa soma, resultando em uma linha ou superfície de regressão que melhor se ajusta aos dados. Esses coeficientes estimados são encontrados por meio de fórmulas matemáticas e podem ser interpretados como a contribuição relativa de cada variável independente para a variação da variável dependente. O método dos mínimos quadrados ordinários é amplamente utilizado devido à sua simplicidade e eficiência na obtenção de estimativas dos parâmetros da regressão linear.")
        st.subheader("StepWise")
        st.write("O método Stepwise é uma abordagem utilizado na regressão linear múltipla para selecionar as melhores variáveis independentes a serem incluídas no modelo de regressão. O processo ocorre em etapas, onde inicialmente o modelo é ajustado com uma variável independente e, em seguida, a cada passo, outras variáveis são adicionadas ou removidas com base em critérios estatísticos. O método Stepwise utiliza critérios como o valor-p, o coeficiente de determinação ajustado (R² ajustado) ou o critério de informação de Akaike (AIC) para avaliar a relevância e a contribuição de cada variável. No primeiro passo, o método pode começar com a variável independente mais significativa e, a partir daí, as variáveis são selecionadas ou removidas de acordo com um critério pré-definido (por exemplo, valor-p abaixo de um determinado limiar). O processo continua até que não haja mais melhorias significativas no modelo. O método Stepwise é uma maneira automatizada de selecionar variáveis relevantes para construir um modelo de regressão múltipla.")
        st.subheader("Critério AIC")
        st.write("O critério de informação de Akaike (AIC) é uma medida estatística utilizada para comparar e selecionar modelos estatísticos. Ele busca encontrar o equilíbrio entre o ajuste do modelo aos dados e a complexidade do modelo. O AIC é calculado a partir da função de verossimilhança do modelo, penalizando a adição de parâmetros ao modelo com base na quantidade de dados disponíveis. Quanto menor o valor do AIC, melhor é o ajuste do modelo. O critério de Akaike é amplamente utilizado na seleção de modelos, especialmente em regressão linear múltipla, onde diferentes combinações de variáveis independentes são testadas e o modelo com o menor AIC é considerado o mais adequado.")





with st.container():
    st.write("----")
    st.write("Aqui estão os dados limpos:")
    st.dataframe(dados)
