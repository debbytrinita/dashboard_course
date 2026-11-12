import streamlit as st
st.title("Profil Peserta")
nama = st.text_input("Nama")
divisi = st.selectbox("Divisi", ["HR", "Finance", "IT", "Marketing"])
tahun_pengalaman = st.slider("Tahun Pengalaman", min_value=0, max_value=50, value=0)

if st.button("Submit", type="primary"): 
    st.info(f"Nama: {nama}\n \n Divisi: {divisi}\n \n Tahun Pengalaman: {tahun_pengalaman}")
