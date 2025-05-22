import io
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(page_title="GSD-180: One Eleven")
st.title("GSD-180: One Eleven")


def process_file(file):
    # Read incoming file
    if file.name.lower().endswith(".csv"):
        df = pd.read_csv(file, header=None)
    elif file.name.lower().endswith((".xls", ".xlsx")):
        df = pd.read_excel(file, header=None)
    else:
        st.error("Unsupported file format. Please upload a CSV or Excel file.")
        return None
    if df.empty:
        st.error("The uploaded file is empty.")
        return None
    if df.shape[1] < 5:
        st.error("Input file must have at least 5 columns (A-E).")
        return None

    # Prepare output DataFrame
    output = pd.DataFrame()

    # 1. Add Column Titles
    output["Debtor Reference"] = ""
    output["Transaction Type"] = ""
    output["Document Number"] = ""
    output["Document Date"] = ""
    output["Document Balance"] = ""

    # 2. Data from column A reformatted to DD/MM/YYYY goes to Column D ("Document Date")
    # Try multiple date parsing strategies
    def parse_date(val):
        # Try common date formats
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(str(val), fmt).strftime("%d/%m/%Y")
            except Exception:
                continue
        try:
            # Last resort: pandas to_datetime
            return pd.to_datetime(val, dayfirst=True, errors="coerce").strftime(
                "%d/%m/%Y"
            )
        except Exception:
            return ""

    output["Document Date"] = df.iloc[:, 0].apply(parse_date)

    # 3. Data from column B goes into Column A ("Debtor Reference")
    output["Debtor Reference"] = df.iloc[:, 1]

    # 4. Data from column C stays in Column C ("Document Number")
    output["Document Number"] = df.iloc[:, 2]

    # 5. Data in Column D reformatted as number with 2 decimals goes into Column E ("Document Balance")
    def to_float_str(x):
        try:
            return f"{float(str(x).replace(',', '')):.2f}"
        except Exception:
            return ""

    output["Document Balance"] = df.iloc[:, 3].apply(to_float_str)

    # 6. Data from Column E is put into column B ("Transaction Type") and transformed
    #    a. ALL CAPS
    #    b. Replace CRN -> CRD
    def transform_transaction_type(x):
        x = str(x).upper().replace("CRN", "CRD")
        return x

    output["Transaction Type"] = df.iloc[:, 4].apply(transform_transaction_type)

    # 7. Reorder columns according to requirements
    output = output[
        [
            "Debtor Reference",
            "Transaction Type",
            "Document Number",
            "Document Date",
            "Document Balance",
        ]
    ]

    return output


def get_csv_download_link(df):
    csv = df.to_csv(index=False)
    return io.BytesIO(csv.encode())


st.write("Upload your Excel or CSV file:")
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    processed_df = process_file(uploaded_file)
    if processed_df is not None:
        st.write("Processed Data:")
        st.dataframe(processed_df)
        csv_buffer = get_csv_download_link(processed_df)
        st.download_button(
            label="Download Processed File",
            data=csv_buffer,
            file_name="one_eleven_upload.csv",
            mime="text/csv",
        )
