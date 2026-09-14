import pandas as pd


# Kolom yang wajib tersedia pada file FOL
REQUIRED_COLUMNS = [
    "Depo",
    "Tanggal DO",
    "Location",
    "Nama Driver",
]


def read_excel_fol(uploaded_file):
    """
    Membaca file Excel yang diupload oleh user.
    Menggunakan sheet pertama sebagai sumber data.
    """

    try:
        df = pd.read_excel(uploaded_file)

        return df

    except Exception as e:
        raise ValueError(f"File Excel tidak dapat dibaca: {e}")


def validate_columns(df):
    """
    Memeriksa apakah semua kolom yang dibutuhkan tersedia.
    """

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        return False, missing_columns

    return True, []


def clean_data(df):
    """
    Membersihkan data FOL sesuai kebutuhan dashboard.

    Tanggal DO yang kosong dipertahankan sebagai data
    yang tidak diketahui untuk kebutuhan analisis.
    Nama Driver yang kosong diberi label khusus.
    """

    df = df.copy()

    # Membersihkan spasi pada nama kolom
    df.columns = df.columns.str.strip()

    # Membersihkan kolom kategori dari spasi berlebih
    for column in ["Depo", "Location", "Nama Driver"]:
        df[column] = df[column].astype("string").str.strip()

    # Mengubah nilai kosong pada Location menjadi tidak diketahui
    df["Location"] = df["Location"].fillna("Tidak Diketahui")

    # Mengubah Nama Driver yang kosong menjadi kategori khusus
    df["Nama Driver"] = df["Nama Driver"].fillna(
        "Driver Tidak Terdata"
    )

    # Mengubah Tanggal DO ke format tanggal
    df["Tanggal DO"] = pd.to_datetime(
        df["Tanggal DO"],
        errors="coerce"
    )

    # Membuat kolom tanggal untuk kebutuhan tampilan
    df["Tanggal DO Tampilan"] = df["Tanggal DO"].dt.strftime(
        "%d-%b-%Y"
    )

    # Memberikan label pada tanggal DO yang kosong
    df["Tanggal DO Tampilan"] = df["Tanggal DO Tampilan"].fillna(
        "Tidak Diketahui"
    )

    return df


def get_data_period(df):
    """
    Mengambil periode tanggal DO yang tersedia.
    Data dengan tanggal DO tidak diketahui tidak dihitung
    dalam periode.
    """

    valid_dates = df["Tanggal DO"].dropna()

    if valid_dates.empty:
        return None, None

    return valid_dates.min(), valid_dates.max()


def get_unique_values(df, column):
    """
    Mengambil daftar nilai unik dari suatu kolom.
    """

    if column not in df.columns:
        return []

    values = (
        df[column]
        .dropna()
        .astype(str)
        .str.strip()
    )

    return sorted(values.unique().tolist())