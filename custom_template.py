import streamlit as st
import pandas as pd

from utils import format_currency_short, get_top_orders_by_status, get_openrouter_completion, read_tabular_data_to_string  # Import functions from utils.py

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

model = st.selectbox("Select Model", ["mistralai", "gpt 4.0 mini", "gemini lite", "gemini flash", "deepseek"])

if model == "mistralai":
    model = "mistralai/mistral-small-3.2-24b-instruct"
elif model == "gpt 4.0 mini":
    model = "openai/gpt-4.1-mini"
elif model == "gemini lite":
    model = "google/gemini-2.5-flash-lite-preview-06-17"
elif model == "gemini flash":
    model = "google/gemini-2.5-flash"
elif model == "deepseek":
    model = "deepseek/deepseek-chat-v3-0324"


if st.button("Analyze Data"):
    if df.empty:
        st.error("Please upload a valid file first.")
    else:
        # Get the top orders by status
        csv_data_string = df.to_csv(index=False)
        if csv_data_string:
            # Prepare the prompt for AI
            prompt = default_prompt_template.format(csv_data_string=csv_data_string)

            # Call the AI function to get analysis
            ai_response = get_openrouter_completion(
                prompt_text=prompt,
                system_instruction=system_instruction,
                model=model
            )

            # Display the AI analysis result
            st.subheader("Result of AI Analysis")
            st.markdown(ai_response)                                    
