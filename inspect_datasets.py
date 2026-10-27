import pandas as pd

# İki dosyayı incele
df1 = pd.read_excel('Trendyol_Urun_Veri_Seti_2732.xlsx')
df2 = pd.read_excel('Trendyol_Wide_Veri_Seti_2732.xlsx')

print('='*70)
print('TRENDYOL_URUN_VERI_SETI_2732.xlsx')
print('='*70)
print(f'Boyut: {df1.shape}')
print(f'\nSütunlar:')
for i, col in enumerate(df1.columns, 1):
    print(f'{i}. {col}')

if 'Kategori' in df1.columns:
    print(f'\nKategori dağılımı:')
    print(df1['Kategori'].value_counts().sort_index())
    print(f'\nBenzersiz kategoriler: {df1["Kategori"].unique()}')

print('\n\n' + '='*70)
print('TRENDYOL_WIDE_VERI_SETI_2732.xlsx')
print('='*70)
print(f'Boyut: {df2.shape}')
print(f'\nSütunlar:')
for i, col in enumerate(df2.columns, 1):
    print(f'{i}. {col}')

if 'Kategori' in df2.columns:
    print(f'\nKategori dağılımı:')
    print(df2['Kategori'].value_counts().sort_index())
    print(f'\nBenzersiz kategoriler: {df2["Kategori"].unique()}')
    print(f'\nKategori veri tipi: {df2["Kategori"].dtype}')

print('\n\n' + '='*70)
print('İLK 5 SATIR (Wide Dataset)')
print('='*70)
print(df2.head())
