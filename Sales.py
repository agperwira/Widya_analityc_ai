import streamlit as st
import pandas as pd
import plotly.express as px

from utils import format_currency_short, get_top_orders_by_status, get_openrouter_completion, read_tabular_data_to_string   # Impor fungsi dari utils.py


st.title("📊 Sales")
# Daftar nama kolom (label) yang diambil dari gambar
columns = ['Activities',        
           'Creation Date',
           'Customer',
           'Order Reference',
           'Salesperson',
           'Status',
           'Total']

# Membuat DataFrame kosong dengan kolom-kolom tersebut
df = pd.DataFrame(columns=columns)

uploaded_file = st.file_uploader("Upload File (.xls, .xlsx, .csv)", type=["xls", "xlsx", "csv"])

if uploaded_file is not None:
    try:
        ext = uploaded_file.name.split('.')[-1].lower()

        if ext == 'csv':
            df = pd.read_csv(uploaded_file)
        elif ext in ['xls', 'xlsx']:
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Format file not supported.")
            st.stop()

        st.success(f"Success upload file: {uploaded_file.name}")
        st.subheader("📋 Table Data")
        st.dataframe(df)

    except Exception as e:
        st.error(f"failed read file: {e}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    quotation = df[df['Status'] == 'Quotation']
    num_quotation = len(quotation)
    st.subheader("Quotation")
    st.markdown(f"<h1 style='text-align: center;'>{num_quotation}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: green; font-size: 18px;'>⬆️ {num_quotation:.0f}% since last period</p>", unsafe_allow_html=True)

with col2:
    order = len(df[df['Status'] == 'Sales Order'])
    st.subheader("Order")
    st.markdown(f"<h1 style='text-align: center;'>{order}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: green; font-size: 18px;'>⬆️ {order:.0f}% since last period</p>", unsafe_allow_html=True)

with col3:
    revenue = df['Total'].sum()
    st.subheader("Revenue")
    st.markdown(f"<h1 style='text-align: center;'>{format_currency_short(revenue)}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: green; font-size: 18px;'>⬆️ {format_currency_short(revenue)} since last period</p>", unsafe_allow_html=True)

with col4:
    average = df['Total'].mean()
    st.subheader("Average")
    st.markdown(f"<h1 style='text-align: center;'>{format_currency_short(average)}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: green; font-size: 18px;'>⬆️ {format_currency_short(average)} since last period</p>", unsafe_allow_html=True)

# --- 2. Filter dan Urutkan Data ---

df_all_orders= df.copy()  # Salin DataFrame untuk menghindari perubahan pada data asli

# --- 3. Buat Kolom di Streamlit ---
col1, col2 = st.columns(2) # Membuat dua kolom

# --- 4. Tampilkan Tabel di Setiap Kolom ---

with col1:
    st.subheader("Top Quotations")
    st.markdown("---") # Garis pembatas
    st.dataframe(get_top_orders_by_status(df_all_orders, 'Quotation'), hide_index=True, use_container_width=True) # hide_index=True menyembunyikan indeks Pandas

available_top_statuses = df_all_orders['Status'].unique().tolist()
available_top_statuses.sort()

with col2:
    st.subheader("custom Top Sales Orders")
    st.markdown("---") # Garis pembatas
    selected_top_status = st.selectbox("Select status for Top Orders:",
                                       options=available_top_statuses,
                                       index=available_top_statuses.index('Quotation') if 'Quotation' in available_top_statuses else 0)
    top_n = st.number_input("Num of Top Orders to display:", min_value=1, max_value=20, value=5, step=1)
    st.dataframe(get_top_orders_by_status(df_all_orders, selected_top_status, top_n=top_n), hide_index=True, use_container_width=True)

st.write("---")
st.write("Ini adalah ringkasan Quotation dan Sales Order teratas berdasarkan pendapatan.")

# --- Agregasi Data untuk Grafik ---
# Kita ingin menjumlahkan 'Total' per 'Salesperson'.
# Asumsi kita hanya ingin Sales Orders yang Completed (bukan RFQ) untuk Sales Performance
sales_df = df[df['Status'] == 'Sales Order'].copy() # Filter hanya Sales Order
sales_by_salesperson = sales_df.groupby('Salesperson')['Total'].sum().reset_index()
sales_by_salesperson.columns = ['Salesperson', 'Total Sales'] # Ganti nama kolom agar lebih jelas

# Urutkan dari penjualan tertinggi
sales_by_salesperson = sales_by_salesperson.sort_values(by='Total Sales', ascending=False)

st.subheader("Total Sales per Salesperson")
st.markdown("---")

# --- Buat Grafik Batang Menggunakan Plotly Express ---
fig = px.bar(
    sales_by_salesperson,
    x='Salesperson',
    y='Total Sales',
    title='Total Penjualan oleh Setiap Salesperson (Sales Order)',
    labels={'Salesperson': 'Nama Salesperson', 'Total Sales': 'Total Penjualan (Rp)'},
    hover_data={'Total Sales': ':,2f'}, # Format tooltip untuk Total Sales
    color='Salesperson' # Memberi warna berbeda untuk setiap salesperson
)
sales_by_salesperson['Total Sales'] = sales_by_salesperson['Total Sales'].apply(format_currency_short) # Format Total Sales sebagai Rupiah

# Sesuaikan layout grafik
fig.update_layout(
    xaxis_title="Salesperson",
    yaxis_title="Total Penjualan (Rp)",
    yaxis_tickformat=",.0f", # Format sumbu Y tanpa desimal dan pemisah ribuan
    hovermode="x unified" # Mode hover untuk menampilkan semua data pada sumbu X
)

# Format nilai di bar grafik sebagai Rupiah (opsional, jika ingin ditampilkan di atas bar)
# fig.update_traces(texttemplate='Rp%{y:,.0f}', textposition='outside')


# Tampilkan grafik di Streamlit
st.plotly_chart(fig, use_container_width=True)

# Opsional: Tampilkan data yang digunakan untuk grafik
st.subheader("Data Agregasi Penjualan per Salesperson")
st.dataframe(sales_by_salesperson)


st.subheader("analitic with ai")
st.markdown("---")


default_prompt_template = """
Berikut adalah data penjualan dalam format CSV:
```csv
{csv_data_string}
```

Berdasarkan data penjualan ini, berikan analisis mendalam dan wawasan utama dalam poin-poin.
Fokus pada aspek-aspek berikut:
- Tren Penjualan Keseluruhan: Apakah ada peningkatan, penurunan, atau stabilitas? Sebutkan periode waktu jika relevan.
- Kinerja Produk: Identifikasi produk terlaris dan paling tidak laku. Jelaskan alasannya jika memungkinkan dari data.
- Kinerja Regional: Bandingkan penjualan di seluruh wilayah. Wilayah mana yang mendominasi atau tertinggal? Apakah ada anomali?
- Peluang dan Tantangan: Apa peluang potensial untuk pertumbuhan penjualan atau tantangan yang perlu ditangani?
- Tindakan yang Direkomendasikan: Berikan setidaknya 2-3 rekomendasi strategis dan dapat ditindaklanjuti berdasarkan wawasan yang ditemukan.

Sajikan setiap poin dengan jelas dan tambahkan penjelasan rinci yang relevan. Hindari format tabel.
Tulis dalam bahasa Inggris yang mudah dimengerti, hindari pemformatan teks seperti tebal atau miring atau simbol yang tidak perlu seperti #### dan **
    """

system_instruction = (
        "Anda adalah Konsultan Analis Data Bisnis yang berpengalaman. "
        "Peran Anda adalah meninjau data tabular (disediakan sebagai string CSV dari file Excel/CSV) dan mengekstrak wawasan strategis yang relevan untuk pengambilan keputusan bisnis. "
        "Fokus pada identifikasi peluang, risiko, dan inefisiensi. "
        "Sajikan temuan dan rekomendasi Anda dalam poin-poin yang jelas dan persuasif. "
        "Hindari jargon teknis yang tidak perlu. "
        "Setiap rekomendasi harus didukung oleh data dan analisis Anda. "
        "Jika berlaku, gunakan format mata uang atau persentase yang relevan untuk angka. "
        "Tujuan Anda adalah membantu pengguna memahami implikasi bisnis dari data mereka."
    )

st.subheader("Adjust the Prompt for AI")
custom_prompt_text = st.text_area(
        "Adjust the prompt template if needed for AI analysis",
        value=default_prompt_template,
        height=300
    )

st.subheader("analitic with AI")
if st.button("suggestion button"):
    if uploaded_file is not None:
        try:

            # Konversi DataFrame ke string CSV
            csv_data_string = df.to_csv(index=False)

            if csv_data_string:
                # Siapkan prompt untuk AI
                prompt = custom_prompt_text.format(csv_data_string=csv_data_string)

                # Panggil fungsi AI untuk mendapatkan analisis
                ai_response = get_openrouter_completion(
                    prompt_text=prompt,
                    system_instruction=system_instruction,
                    model="mistralai/mistral-small-3.2-24b-instruct"
                )

                # Tampilkan hasil analisis AI
                st.subheader("Hasil Analisis AI")
                st.markdown(ai_response)
            else:
                st.warning("AI response is empty.")

        except Exception as e:
            st.error(f"Error during AI analysis: {e}")
    else:
        st.warning("Please upload a file before running the analysis.")