import pandas as pd

# Kolom yang wajib tersedia pada file FOL
REQUIRED_COLUMNS = [
    "Depo",
    "Tanggal Order Priority",
    "Location",
    "Nama Driver",
    "Week",
]

VALID_DRIVERS = [
    "Dedi Siswanto",
    "M  Hafizzul",
    "Hendri",
    "Didiet Satriawandy Saragih",
    "ANJU SALMAN FAHRAUZI",
    "Randa Syahputra",
    "Rimson Sinaga",
    "Martogi Sagala",
    "Ahmad Budi Amin Nasution",
    "Teddy  Desrian",
    "Hermawan Susanto",
    "Dedi Rohadi",
    "Mukhlis",
    "Rido Al Fazar",
    "Rizki Ade Syahputra",
    "Ilham Saputra",
    "Yoppi Ananda Situmorang",
    "Rikky Satria",
    "Harun Hasibuan",
    "Muhammad Yusuf Ritonga",
    "Rindra  Pradifta",
    "Mhd Syamsul Sinulingga",
    "MUHAMMAD SHOLAHUDDIN ASHARY",
    "Harry Tamara Pane",
    "Guntur Asmara",
    "Rahmat Saleh Purba",
    "M. Yusuf",
    "Muhammad Ramzi",
    "Legi manono",
    "Suhermanto",
    "Joko Saputra",
    "SANDI ARIES",
    "Bobby Irawan",
    "ARIANTO",
    "Deston Marbun",
    "Yudi Hertanto",
    "Jannes Fernando Simangunsong",
    "Muhammad Imam Santoso",
]

def read_excel_fol(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)

        return df

    except Exception as e:
        raise ValueError(f"File Excel tidak dapat dibaca: {e}")


def validate_columns(df):
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        return False, missing_columns

    return True, []


def clean_data(df):
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

    # Mengubah Tanggal Order Priority ke format tanggal
    df["Tanggal Order Priority"] = pd.to_datetime(
        df["Tanggal Order Priority"],
        errors="coerce"
    )

    df["Week"] = pd.to_numeric(
        df["Week"],
        errors="coerce"
    )

    df["Tanggal Order Priority Tampilan"] = (
        df["Tanggal Order Priority"]
        .dt.strftime("%d-%b-%Y")
    )

    return df


def get_data_period(df):
    valid_dates = df["Tanggal Order Priority"].dropna()

    if valid_dates.empty:
        return None, None

    return valid_dates.min(), valid_dates.max()


def get_unique_values(df, column):
    if column not in df.columns:
        return []

    values = (
        df[column]
        .dropna()
        .astype(str)
        .str.strip()
    )

    return sorted(values.unique().tolist())

def get_valid_drivers(df):
    if "Nama Driver" not in df.columns:
        return []

    available_drivers = (
        df["Nama Driver"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    return sorted(
        [
            driver
            for driver in VALID_DRIVERS
            if driver in available_drivers
        ]
    )