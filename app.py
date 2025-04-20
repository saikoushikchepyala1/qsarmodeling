import streamlit as st
import pandas as pd
import subprocess
import os
import base64
import pickle
import shutil
import uuid


# ---------- PaDEL Descriptor Calculation ----------
def desc_calc(smi_file_path, output_csv_path):
    # Run descriptor calculation ONLY for the uploaded file
    bash_cmd = f"java -Xms2G -Xmx2G -Djava.awt.headless=true -jar PaDEL-Descriptor/PaDEL-Descriptor.jar " \
               f"-removesalt -standardizenitro -fingerprints " \
               f"-descriptortypes PaDEL-Descriptor/PubchemFingerprinter.xml " \
               f"-dir {os.path.dirname(smi_file_path)} " \
               f"-file {output_csv_path}"

    process = subprocess.Popen(bash_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()

    if process.returncode != 0:
        st.error("Descriptor calculation failed!")
        st.text(error.decode())
        return False
    return True


# ---------- Downloadable Link ----------
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="prediction.csv">Download prediction CSV</a>'


# ---------- Run Model ----------
def predict_bioactivity(desc_subset, original_ids):
    model = pickle.load(open('bioactivity_prediction_model.pkl', 'rb'))
    predictions = model.predict(desc_subset)
    results = pd.DataFrame({
        'Compound_ID': original_ids,
        'pIC50': predictions
    }).sort_values(by='pIC50', ascending=False)
    return results


# ---------- Streamlit App ----------
st.title("🧪 QSAR-based Compound Activity Prediction")

with st.sidebar.header("1. Upload your compound file"):
    uploaded_file = st.sidebar.file_uploader("Upload SMILES file (.smi / .csv / .txt)", type=['smi', 'csv', 'txt'])

if st.sidebar.button("🔬 Run Prediction"):
    if uploaded_file is not None:
        # Create unique temp folder
        temp_dir = f"temp_{uuid.uuid4().hex[:8]}"
        os.makedirs(temp_dir, exist_ok=True)

        # Read uploaded file
        try:
            if uploaded_file.name.endswith('.csv'):
                data = pd.read_csv(uploaded_file)
            else:
                data = pd.read_table(uploaded_file, sep=None, engine='python', header=None)
        except Exception as e:
            st.error(f"Failed to read uploaded file: {e}")
            shutil.rmtree(temp_dir)
            st.stop()

        if data.shape[1] != 2:
            st.error("File must contain exactly 2 columns: [SMILES, Compound_ID]")
            shutil.rmtree(temp_dir)
            st.stop()

        st.subheader("📄 Uploaded Data")
        st.write(data)

        # Save to SMILES file
        smiles_path = os.path.join(temp_dir, "input.smi")
        data.to_csv(smiles_path, sep="\t", header=False, index=False)

        st.info("Calculating descriptors, please wait...")
        descriptor_path = os.path.join(temp_dir, "descriptors_output.csv")
        success = desc_calc(smiles_path, descriptor_path)

        if not success:
            shutil.rmtree(temp_dir)
            st.stop()

        # Read descriptors
        try:
            descriptors = pd.read_csv(descriptor_path)
        except:
            st.error("Failed to read descriptor file.")
            shutil.rmtree(temp_dir)
            st.stop()

        st.subheader("📊 All Molecular Descriptors")
        st.write(descriptors.head())

        # Select important descriptors
        try:
            top_descriptors = pd.read_csv("descriptor_list.csv").columns.tolist()
            desc_subset = descriptors[top_descriptors]
        except:
            st.error("Check that descriptor_list.csv exists and matches the model features.")
            shutil.rmtree(temp_dir)
            st.stop()

        st.subheader("📌 Selected Top Descriptors (used in model)")
        st.write(desc_subset.head())

        # Predict
        results = predict_bioactivity(desc_subset, data.iloc[:, 1])
        st.subheader("🔮 Prediction Results")
        st.write(results)

        st.markdown(filedownload(results), unsafe_allow_html=True)

        # Clean temp
        shutil.rmtree(temp_dir)
    else:
        st.warning("Please upload a file first.")
else:
    st.info("Upload a file and click 'Run Prediction' to begin.")
