import pandas as pd

df = pd.read_csv("data/ai4i2020.csv")
print("Ukuran dataset:", df.shape)

print("\nDaftar kolom:")
print(df.columns.tolist())

print("\nContoh data:")
print(df.head())

print("\nTipe data:")
print(df.dtypes)

print("\nNilai kosong:")
print(df.isnull().sum())

print("\nJumlah baris duplikat:", df.duplicated().sum())