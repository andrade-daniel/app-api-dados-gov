import streamlit as st
import pandas as pd
import numpy as np
import base64
import os
import pickle
from PIL import Image
# from ftfy import fix_encoding
import joblib
import json
import requests
from urllib.parse import unquote
import unidecode
import warnings
from bokeh.plotting import figure
from math import pi

warnings.filterwarnings("ignore")

# functions

@st.cache(persist=True, suppress_st_warning=True)
def add_api_key(api_key):

    return api_key


# logo image

# img = Image.open('/img/logo_ticapp_black_500px.png')
img = Image.open('img/dados-gov-logo.png')

st.sidebar.image(img,
use_column_width=False, width=200)

st.title('API demos dados.gov.pt')

# create cache and data folders

cache_dir = 'tmp'
data_dir = 'data'
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir, exist_ok=True)

if not os.path.exists(data_dir):
    os.makedirs(data_dir, exist_ok=True)

cache_file = None

if st.sidebar.checkbox("Inserir API KEY"):
    cache_file = st.text_area(add_api_key("Insira aqui a sua API KEY..."))

    joblib.dump(cache_file, cache_dir + '/tmp.pickle')

    # st.success('API registada temporariamente')

cache_file = joblib.load(cache_dir + '/tmp.pickle')

# create session

session = requests.Session()

# update_session(cache_file)
session.headers.update({"X-API-KEY": cache_file})

#############
# API TESTS #
#############

# initial examples 

### SITE

if st.sidebar.checkbox("Exemplo 1: Dados de Utilização do Portal"):
    
    st.subheader("Dados de utilização do Portal")

    response_site = session.get("https://dados.gov.pt/api/1/site/")
    
    assert(response_site.status_code == '200', 'Erro no início de sessão!')
    
    # response_site.json()
    # response_site.json().get("metrics")

    st.table(pd.DataFrame.from_dict(response_site.json().get("metrics"), orient="index").T)


### FILE FORMATS ACCEPTED FOR DATASETS

if st.sidebar.checkbox("Exemplo 2: Formatos de Ficheiros"):
    
    st.subheader("Verificar formatos de ficheiros aceites")
    response_formats = session.get("https://dados.gov.pt/api/1/datasets/extensions/")

    assert(response_formats.status_code == '200', 'Erro no início de sessão!')

    st.text(st.json(response_formats.json()))

### GET ORGANIZATIONS

if st.sidebar.checkbox("Exemplo 3: Organizações"):
    
    st.subheader("Obter Organizações")

    response_org = session.get("https://dados.gov.pt/api/1/organizations/")

    assert(response_org.status_code == '200', 'Erro no início de sessão!')

    datasets_org = response_org.json().get("data")
    next_page = response_org.json().get("next_page")
    while next_page:
        response_org = session.get(next_page)
        datasets_org += response_org.json().get("data")
        next_page = response_org.json().get("next_page")
        print(next_page)
        if not next_page:
            print("Done!")
            break
    st.text(f"Nº de Organizações: {len(datasets_org)}")

    # into dataframe
    df_org = pd.DataFrame(datasets_org)
    # st.text(f"Campos devolvidos: {[cols for cols in df_org.columns]}")
    df_org.index = range(1, len(df_org)+1)

    # st.table(df_org[["acronym", "name", "description"]])
    st.dataframe(df_org, width=2000, height=500)

    joblib.dump(df_org, cache_dir + '/df_org.pickle')


### GET DATASETS FROM AN ORGANIZATION

if st.sidebar.checkbox("Exemplo 4: Obter um ficheiro de uma organização"):
    
    st.subheader("Obter um ficheiro de uma organização")

    df_org = joblib.load(cache_dir + '/df_org.pickle')
    sel_org = st.selectbox(label="Selecione Organização", options=np.unique(df_org['name']), \
        index=3)

    if sel_org:
        response_org_ds = session.get(
        f"https://dados.gov.pt/api/1/organizations/{sel_org}/datasets/"
    )
        assert(response_org_ds.status_code == '200', 'Erro no início de sessão!')

        datasets_org_ds = response_org_ds.json().get("data")
        next_page = response_org_ds.json().get("next_page")
        while next_page:
            response_org_ds = session.get(next_page)
            datasets_org_ds += response_org_ds.json().get("data")
            next_page = response_org_ds.json().get("next_page")
            print(next_page)
            if not next_page:
                print("Done!")
                break
        st.text(f"Nº de ficheiros: {len(datasets_org_ds)}")

        # into dataframe
        df_org_ds = pd.DataFrame(datasets_org_ds)
        df_org_ds.index = range(1, len(datasets_org_ds)+1)
        joblib.dump(df_org_ds, cache_dir + '/df_org_ds.pickle')

        st.dataframe(df_org_ds)
        
        st.subheader('Listando os ficheiros...')

        st.table(df_org_ds.loc[:, ['description']])

        st.subheader('Onde encontrar links de ficheiros?')
        st.text('No campo "resources"')
        st.json(df_org_ds.loc[:1, "resources"].values[0][0])

        st.subheader('Fazer download de um ficheiro')

        sel_file = st.selectbox(label="Selecione nome de ficheiro", options=np.unique(df_org_ds['description']), \
        index=0)


        format_files = [
            (f["format"], f["url"])
            for f in df_org_ds.loc[df_org_ds["description"] == sel_file, "resources"].values[0]
        ]

        [
    
        st.subheader(f"Formato: {elem[0]} \nLink: {elem[1]} \n------------------------------------------------------------------------")
    
    for elem in format_files
][0]

        file_url = st.text_area("Insira aqui o link do ficheiro...")

        if st.button("Descarregar ficheiro!"):
            org_dir = data_dir + "/" + sel_org
            if not os.path.exists(org_dir):
                os.makedirs(org_dir, exist_ok=True)
            
            with st.spinner('Aguarde...'):
                sel_org_path = (data_dir + "//" + sel_org + "//" + sel_file + "." + \
                    file_url.split("/")[-1].split(".")[-1])
                
                myfile = requests.get(file_url)
                open(sel_org_path, "wb").write(myfile.content)
            
            st.success(f'Documento transferido! \nGuardado na pasta: {data_dir}/{sel_org}.')


### RUN COMMANDS

## Simulate command line

if st.sidebar.checkbox("Exemplo 5: Correr comandos curl num terminal"):
    
    st.subheader("Correr comandos curl")

    commands = st.text_area("Insira aqui o comando pretendido...")

    if st.button("Clique para correr"):
        if commands:
            # removing certain characters that lead to errors (e.g. replacing "%20" by "-")
            commands = unquote(commands)
            commands = commands.split("https")[:-1][0] + "https" + '-'.join(commands.split("https")[-1].split(" "))
            
            commands = commands.replace("'", '"')
            commands = unidecode.unidecode(commands)
            joblib.dump(commands, cache_dir + '/commands.pickle')

            commands_to_file = commands + ' > ' + data_dir + '/out.json'
            os.system(commands_to_file)
            st.success(f'Pedido efectuado. \nFicheiro guardado na pasta: {data_dir}.')

            output_file = json.load(open(data_dir + "/out.json"))
            st.json(output_file)
            # st.table(pd.DataFrame(output_file['data']))


### VISUALIZATION

## Visualize certain features of downloaded data

if st.sidebar.checkbox("Exemplo 6: Olhar para os dados"):
    st.subheader("Escolher um dataset e uma visualização")

    uploaded_file = st.file_uploader(label="Escolha um ficheiro")
    
    file_types = ['json', 'csv', 'excel']
    sel_file_type = st.selectbox(label="Selecione o formato do ficheiro", options=file_types, \
        index=0)

    if uploaded_file is not None:
        if st.button("Clique para confirmar"):
            if sel_file_type == 'json':
                data = pd.read_json(uploaded_file)
            elif sel_file_type == 'csv':
                data = pd.read_csv(uploaded_file)
            else:
                data = pd.read_excel(uploaded_file)
        
            joblib.dump(data, cache_dir + '/data.pickle')
        
        data = joblib.load(cache_dir + '/data.pickle')

        st.write(data)
        st.table(pd.DataFrame(data))
        # st.text(pd.DataFrame(data['data']).columns)

        data_df = pd.DataFrame(data)

        if sel_file_type == 'json':
            data_df = [pd.DataFrame(elem, index=[0]) for elem in data_df['d']]
            data_df = pd.concat(data_df)
        
        joblib.dump(data_df, cache_dir + '/data_df.pickle')

        st.dataframe(data_df)


        # select type of viz

        st.subheader("Escolher um tipo de visualização")

        viz_types = ['Gráfico de barras', 'Gráfico de dispersão']
        sel_viz = st.selectbox(label="Selecione um tipo de visualização", options=viz_types, \
        index=0)

        sel_var1 = st.selectbox(label="Selecione uma variável", options=data_df.columns, \
        index=0, key='sel_var1')

        sel_var2 = st.selectbox(label="Selecione uma segunda variável", options=data_df.columns, \
        index=0, key='sel_var2')
        
        # bokeh plotting

        TOOLS = "hover,crosshair,pan,wheel_zoom,zoom_in,zoom_out,box_zoom,undo,redo,reset,tap,save,box_select,poly_select,lasso_select,"
        
        if sel_var1 and sel_var2:
            
            p = figure(title=sel_viz, x_range=data_df[sel_var1], tools=TOOLS)
            
            if sel_viz == 'Gráfico de barras':
                p.vbar(x=data_df[sel_var1], top=data_df[sel_var2], legend='Trend', width=0.9)
                
            else:
                p.scatter(x=data_df[sel_var1], y=data_df[sel_var2])
                
            p.xaxis.major_label_orientation = pi/4   # standard styling code
            st.bokeh_chart(p)





    