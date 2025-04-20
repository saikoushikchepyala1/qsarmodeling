import streamlit as st
import pandas as pd
from PIL import Image
import subprocess
import os
import base64
import pickle


def desc_calc():
    bashCommand = "java -Xms2G -Xmx2G -Djava.awt.headless=true -jar ./PaDEL-Descriptor/PaDEL-Descriptor.jar -removesalt -standardizenitro -fingerprints -descriptortypes ./PaDEL-Descriptor/PubchemFingerprinter.xml -dir ./ -file descriptors_output.csv"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    os.remove('alzheimers_molecule.smi')


def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  
    href = f'<a href="data:file/csv;base64,{b64}" download="prediction.csv">Download Predictions</a>'
    return href


def build_model(input_data):
  
    load_model = pickle.load(open('bioactivity_prediction_model.pkl', 'rb'))
    
    prediction = load_model.predict(input_data)
    st.header('**Prediction output**')
    prediction_output = pd.Series(prediction, name='pIC50')
    chembl_id = pd.Series(load_data.iloc[:, 1], name='chembl_id') 
    df = pd.concat([chembl_id, prediction_output], axis=1)
    
    df_sorted = df.sort_values(by='pIC50', ascending=False)
    st.write(df_sorted)
    st.markdown(filedownload(df_sorted), unsafe_allow_html=True)
    


st.markdown("""
# Compounds Bioactivity Prediction
""")


with st.sidebar.header('1. Upload your CSV or SMI data'):
    uploaded_file = st.sidebar.file_uploader("Upload your input file", type=['txt', 'csv', 'smi'])
    st.sidebar.markdown("""

""")

if st.sidebar.button('Predict'):
    if uploaded_file is not None:
       
        if uploaded_file.name.endswith('.csv'):
            load_data = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.smi') or uploaded_file.name.endswith('.txt'):
            load_data = pd.read_table(uploaded_file, sep=' ', header=None)
        else:
            st.error("Unsupported file format. Please upload a CSV, SMI, or TXT file.")
            st.stop()

       
        load_data.to_csv('alzheimers_molecule.smi', sep='\t', header=False, index=False)

        st.header('**Original input data**')
        st.write(load_data)

        with st.spinner("Calculating descriptors..."):
            desc_calc()

        
        st.header('**Calculated molecular descriptors**')
        desc = pd.read_csv('descriptors_output.csv')
        st.write(desc)
        st.write(desc.shape)

      
        st.header('**Subset of descriptors from previously built models**')
        Xlist = list(pd.read_csv('descriptor_list.csv').columns)
        desc_subset = desc[Xlist]
        st.write(desc_subset)
        st.write(desc_subset.shape)

        
        build_model(desc_subset)
    else:
        st.error("Please upload a file to proceed.")
else:
    st.info('Upload input data in the sidebar to start!')