import pandas as pd
import requests
import json
import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

# Mengambil nilai variabel lingkungan
# api_key = os.getenv("MY_API_KEY")
# model = os.getenv("MODEL")
# Asumsi fungsi format_currency_short sudah didefinisikan
st.secrets["api_key"] == "MY_API_KEY"
st.secrets["model"] == "MODEL"


#print(api_key, model)  # Debugging: Pastikan api_key dan model diambil dengan benar

def format_currency_short(amount, decimal_places=2):
    """
    Mengubah nilai mata uang numerik menjadi format singkat (K, M, B).
    Ini adalah fungsi yang sama dari jawaban sebelumnya.
    """
    if not isinstance(amount, (int, float)):
        return ""
    if amount == 0:
        return "Rp0"

    abs_amount = abs(amount)

    if abs_amount >= 1_000_000_000:  # Billion (Miliar)
        value = round(amount / 1_000_000_000, decimal_places)
        suffix = "B"
    elif abs_amount >= 1_000_000:  # Million (Juta)
        value = round(amount / 1_000_000, decimal_places)
        suffix = "M"
    elif abs_amount >= 1_000:  # Thousand (Ribu)
        value = round(amount / 1_000, decimal_places)
        suffix = "K"
    else:  # Less than a thousand
        value = round(amount, decimal_places)
        suffix = ""

    formatted_value = f"{value:.{decimal_places}f}"
    if formatted_value.endswith(".00"):
        formatted_value = formatted_value[:-3]

    prefix = "-" if amount < 0 and abs_amount >= 1000 else ""

    return f"Rp{prefix}{formatted_value}{suffix}"

def get_top_orders_by_status(df_all_orders, status_to_filter, top_n=5, ascending=False):
    """
    Memproses DataFrame pesanan untuk mendapatkan daftar pesanan teratas berdasarkan status tertentu.

    Args:
        df_all_orders (pd.DataFrame): DataFrame yang berisi semua data pesanan,
                                      termasuk kolom 'Status', 'Total',
                                      'Order Reference', 'Customer', 'Salesperson'.
        status_to_filter (str): Status pesanan yang ingin difilter (misal: 'Quotation', 'Sales Order').
        top_n (int): Jumlah pesanan teratas yang ingin ditampilkan. Default adalah 5.

    Returns:
        pd.DataFrame: DataFrame yang difilter, diurutkan, dengan kolom yang dipilih,
                      dan kolom 'Revenue' yang sudah diformat.
                      Mengembalikan DataFrame kosong jika tidak ada pesanan dengan status tersebut.
    """
    # Pastikan 'Total' adalah tipe numerik untuk sorting
    # Ini penting jika 'Total' mungkin dibaca sebagai string dari CSV
    df_all_orders['Total'] = pd.to_numeric(df_all_orders['Total'], errors='coerce')

    # 1. Filter berdasarkan Status yang diberikan sebagai parameter
    df_filtered_orders = df_all_orders[df_all_orders['Status'] == status_to_filter].copy()

    # Periksa apakah ada pesanan setelah filter
    if df_filtered_orders.empty:
        print(f"Tidak ada pesanan dengan status '{status_to_filter}' ditemukan.")
        # Buat DataFrame kosong dengan kolom yang diharapkan
        return pd.DataFrame(columns=['Order Ref', 'Customer', 'Salesperson', 'Revenue'])

    # 2. Urutkan berdasarkan 'Total' sesuai dengan parameter ascending
    df_filtered_orders = df_filtered_orders.sort_values(by='Total', ascending=ascending)

    # 3. Pilih kolom yang ingin ditampilkan
    df_display = df_filtered_orders[['Order Reference', 'Customer', 'Salesperson', 'Total']].copy()

    # 4. Ganti nama kolom untuk tampilan
    # Ganti 'Order Reference' menjadi nama yang lebih dinamis berdasarkan status
    new_order_ref_col_name = f"{status_to_filter.replace(' ', '_')}_Ref" # Contoh: 'Sales_Order_Ref'
    df_display = df_display.rename(columns={
        'Order Reference': new_order_ref_col_name,
        'Total': 'Revenue'
    })

    # 5. Format kolom 'Revenue' ke format mata uang RpX.XXX.XX
    df_display['Revenue'] = df_display['Revenue'].apply(
        lambda x: f"Rp{x:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    )

    # 6. Ambil top_n pesanan
    return df_display.head(top_n)

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

import requests
import json
import pandas as pd
from io import StringIO

def read_tabular_data_to_string(file_content, file_name: str) -> str | None:
    """
    Membaca konten file CSV atau Excel (XLS/XLSX) dan mengembalikan kontennya
    sebagai string yang diformat (misalnya, sebagai string CSV).
    Menggunakan pandas untuk fleksibilitas.
    """
    try:
        if file_name.endswith('.csv'):
            df = pd.read_csv(StringIO(file_content.decode('utf-8')))
        elif file_name.endswith('.xls') or file_name.endswith('.xlsx'):
            # Untuk Excel, pandas dapat membaca langsung dari bytes
            df = pd.read_excel(file_content)
        else:
            # Mengangkat ValueError jika format file tidak didukung
            raise ValueError(f"Error: Format file tidak didukung untuk {file_name}. Hanya CSV, XLS, XLSX yang didukung.")

        csv_string_representation = df.to_csv(index=False)
        return csv_string_representation
    except Exception as e:
        # Mengangkat Exception untuk kesalahan umum saat membaca file
        raise Exception(f"Error membaca file {file_name}: {e}")

def get_openrouter_completion(
    prompt_text: str,
    system_instruction: str,
    api_key: str = api_key,
    model: str = model,
    temperature: float = 0.4,
    max_tokens: int = 1000, # Meningkatkan max_tokens untuk analisis yang lebih detail
    stream_response: bool = False,
    base_url: str = "https://openrouter.ai/api/v1/chat/completions"
) -> str | None:
    """
    Mengirim permintaan penyelesaian ke OpenRouter API.

    Args:
        prompt_text: Konten prompt utama.
        system_instruction: Instruksi sistem untuk AI.
        api_key: Kunci API OpenRouter Anda.
        model: Model yang akan digunakan (default: mistralai/mistral-small-3.2-24b-instruct).
        temperature: Mengontrol keacakan (default: 0.4).
        max_tokens: Jumlah maksimum token yang akan dihasilkan (default: 1000).
        stream_response: Apakah akan melakukan streaming respons (default: False).
        base_url: URL dasar untuk OpenRouter API.

    Returns:
        Konten teks yang dihasilkan dari AI, atau None jika terjadi kesalahan.
    """
    if not api_key:
        # Mengangkat ValueError jika kunci API tidak ditemukan
        raise ValueError("Kunci API OpenRouter tidak ditemukan. Harap masukkan.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = [
        {"role": "user", "content": [{"type": "text", "text": prompt_text}]},
        {"role": "system", "content": [{"type": "text", "text": system_instruction}]}
    ]

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream_response,
    }

    try:
        response = requests.post(base_url, headers=headers, json=payload, stream=stream_response)
        response.raise_for_status()

        if stream_response:
            full_content = []
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        json_data = decoded_line[len('data: '):]
                        if json_data == '[DONE]':
                            break
                        try:
                            chunk = json.loads(json_data)
                            if 'choices' in chunk and chunk['choices'] and \
                               'delta' in chunk['choices'][0] and 'content' in chunk['choices'][0]['delta']:
                                content = chunk['choices'][0]['delta']['content']
                                full_content.append(content)
                        except json.JSONDecodeError:
                            # Lanjutkan jika ada kesalahan JSONDecodeError dalam stream
                            continue
            return "".join(full_content)
        else:
            response_data = response.json()
            try:
                content = response_data['choices'][0]['message']['content']
                return content
            except (KeyError, TypeError) as e:
                # Mengangkat Exception jika tidak dapat mengurai konten respons
                print(f"Full response (JSON): {json.dumps(response_data, indent=2)}") # Untuk debugging
                raise Exception(f"cannot parse response content: {e}")

    except requests.exceptions.RequestException as e:
        # Mengangkat RequestException untuk kesalahan API
        error_details = ""
        if response is not None:
            error_details += f"Response status code: {response.status_code}\n"
            try:
                error_details += f"Response error details: {json.dumps(response.json(), indent=2)}"
            except json.JSONDecodeError:
                error_details += f"Response content: {response.text}"
        raise requests.exceptions.RequestException(f"Terjadi kesalahan selama panggilan API ke OpenRouter: {e}\n{error_details}")
