"""
Veri Temizleme ve Sayısallaştırma Scripti
1. Metin Temizliği
2. Sayısallaştırma
3. Eksik Veri Temizleme
"""

import pandas as pd
import re
import numpy as np

def clean_text(text):
    """Metin temizleme fonksiyonu."""
    if pd.isna(text) or text == '':
        return text
    
    text = str(text).strip()
    
    # Nokta-virgül hatalarını düzelt
    text = text.replace(';', ',')
    text = text.replace('..', '.')
    text = text.replace('  ', ' ')  # Çift boşlukları tek yap
    
    # İstenmeyen karakterleri temizle (sadece harf, rakam, boşluk, virgül, tire, parantez bırak)
    text = re.sub(r'[^\w\s\-,()%./]', '', text)
    
    return text

def clean_material(text):
    """Kumaş bilgilerini temizle: % işaretlerini ve gereksiz sayıları sil."""
    if pd.isna(text) or text == '':
        return text
    
    text = str(text).strip()
    
    # % işaretlerini kaldır
    text = text.replace('%', '')
    
    # Gereksiz sayıları temizle (örneğin: "100 Pamuk" -> "Pamuk")
    # Ama "3 İplik" gibi anlamlı sayıları koru
    # Önce yaygın kumaş isimlerini koru
    text = re.sub(r'^\d+\s+', '', text)  # Başta sadece sayı varsa kaldır
    text = re.sub(r'\s+\d+$', '', text)  # Sonda sadece sayı varsa kaldır
    
    # Fazla boşlukları temizle
    text = ' '.join(text.split())
    
    return text

def preprocess_data():
    """Veri temizleme ve sayısallaştırma işlemlerini gerçekleştirir."""
    
    input_file = 'xxx_verisi.xlsx'
    output_file = 'xxx_verisi.xlsx'  # Aynı dosyaya kaydet
    
    try:
        print(f"'{input_file}' dosyasi okunuyor...")
        df = pd.read_excel(input_file, engine='openpyxl')
        
        print(f"OK Dosya okundu. Toplam {len(df)} satir, {len(df.columns)} sutun.\n")
        
        original_count = len(df)
        
        # ============================================
        # 1. ADIM: METİN TEMİZLİĞİ
        # ============================================
        print("="*70)
        print("1. ADIM: METIN TEMIZLIGI")
        print("="*70)
        
        # Tüm metin sütunlarını temizle
        text_columns = ['Urun_Adi', 'Materyal_Kumas_Tipi', 'Dokuma_Tipi', 'Kol_Boyu', 
                       'Yaka_Tipi', 'Renk', 'Desen', 'Kalıp', 'Cep', 'Boy', 'Ortam', 
                       'Beden', 'Stil', 'Sezon', 'Paca_Tipi', 'Bel', 'Koleksiyon', 
                       'Astar_Durumu', 'Siluet', 'Dokuma_Tipi_Detay', 'Kemer_Kusak_Durumu',
                       'Surdurulebilirlik_Detayi', 'Mensei', 'Kutu_Durumu', 'Kapama_Sekli',
                       'Paket_Icerigi', 'Persona', 'Baski_Nakis_Teknigi', 'Parca_Sayisi',
                       'Urun_Tipi', 'Kalinlik', 'Ek_Ozellikler']
        
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].apply(clean_text)
        
        # Materyal sütununu özel olarak temizle
        if 'Materyal_Kumas_Tipi' in df.columns:
            df['Materyal_Kumas_Tipi'] = df['Materyal_Kumas_Tipi'].apply(clean_material)
            print(f"  - Materyal_Kumas_Tipi temizlendi (% isaretleri kaldirildi)")
        
        print(f"OK Metin temizligi tamamlandi.\n")
        
        # ============================================
        # 2. ADIM: SAYISALLAŞTIRMA
        # ============================================
        print("="*70)
        print("2. ADIM: SAYISALLASMA")
        print("="*70)
        
        # Cinsiyet: Erkek=1, Kadın=0
        if 'Cinsiyet' in df.columns:
            df['Cinsiyet'] = df['Cinsiyet'].map({'Erkek': 1, 'Kadın': 0, 'Kadin': 0})
            print(f"  - Cinsiyet sayisallastirildi: Erkek=1, Kadin=0")
        
        # Kategori (Ürün Türü): T-shirt=0, Kazak=1, Sweatshirt=2, Hırka=3, Gömlek=4, Ceket=5, Pantolon=6, Eşofman=7
        category_mapping = {
            'T-shirt': 0,
            'Tisort': 0,
            'Kazak': 1,
            'Sweatshirt': 2,
            'Hırka': 3,
            'Hirka': 3,
            'Gömlek': 4,
            'Gomlek': 4,
            'Ceket': 5,
            'Pantolon': 6,
            'Eşofman': 7,
            'Esofman': 7
        }
        
        if 'Kategori' in df.columns:
            df['Kategori'] = df['Kategori'].map(category_mapping)
            print(f"  - Kategori sayisallastirildi: T-shirt=0, Kazak=1, Sweatshirt=2, Hırka=3, Gömlek=4, Ceket=5, Pantolon=6, Eşofman=7")
        
        # Kol Boyu: Kısa=0, Uzun=1, Askılı=2, Kolsuz=3
        kol_mapping = {
            'Kısa': 0, 'Kisa': 0, 'Kısa Kol': 0, 'Kisa Kol': 0, 'Short': 0,
            'Uzun': 1, 'Uzun Kol': 1, 'Long': 1,
            'Askılı': 2, 'Askilı': 2, 'Sleeveless': 2,
            'Kolsuz': 3, 'Sleeveless': 3
        }
        
        if 'Kol_Boyu' in df.columns:
            # Önce mapping'e göre dönüştür
            df['Kol_Boyu'] = df['Kol_Boyu'].map(kol_mapping)
            # Mapping'de olmayan değerleri benzersiz sayılara çevir
            unique_values = df['Kol_Boyu'].dropna().unique()
            max_mapped = max([v for v in unique_values if isinstance(v, (int, np.integer))], default=-1)
            unmapped_values = df[df['Kol_Boyu'].isna() | ~df['Kol_Boyu'].isin(kol_mapping.values())]['Kol_Boyu'].unique()
            if len(unmapped_values) > 0:
                for idx, val in enumerate(unmapped_values, start=max_mapped + 1):
                    df.loc[df['Kol_Boyu'] == val, 'Kol_Boyu'] = idx
            print(f"  - Kol_Boyu sayisallastirildi: Kisa=0, Uzun=1, Askili=2, Kolsuz=3")
        
        # Yaka Tipi: V Yaka=0, Balıkçı=1, Bisiklet=2, Polo=3, vb.
        yaka_mapping = {
            'V Yaka': 0, 'V': 0, 'V Yaka': 0,
            'Balıkçı': 1, 'Balikci': 1, 'Balıkçı Yaka': 1,
            'Bisiklet': 2, 'Bisiklet Yaka': 2, 'Round': 2,
            'Polo': 3, 'Polo Yaka': 3,
            'Kapüşonlu': 4, 'Kapusonlu': 4, 'Hood': 4
        }
        
        if 'Yaka_Tipi' in df.columns:
            df['Yaka_Tipi'] = df['Yaka_Tipi'].map(yaka_mapping)
            # Mapping'de olmayan değerleri benzersiz sayılara çevir
            unique_values = df['Yaka_Tipi'].dropna().unique()
            max_mapped = max([v for v in unique_values if isinstance(v, (int, np.integer))], default=-1)
            unmapped_values = df[df['Yaka_Tipi'].isna() | ~df['Yaka_Tipi'].isin(yaka_mapping.values())]['Yaka_Tipi'].unique()
            if len(unmapped_values) > 0:
                for idx, val in enumerate(unmapped_values, start=max_mapped + 1):
                    df.loc[df['Yaka_Tipi'] == val, 'Yaka_Tipi'] = idx
            print(f"  - Yaka_Tipi sayisallastirildi")
        
        # Diğer kategorik sütunları da sayısallaştır (benzersiz değerlere göre)
        categorical_columns = ['Renk', 'Desen', 'Kalıp', 'Cep', 'Boy', 'Ortam', 'Beden', 
                              'Stil', 'Sezon', 'Paca_Tipi', 'Bel', 'Koleksiyon', 
                              'Astar_Durumu', 'Siluet', 'Dokuma_Tipi_Detay', 
                              'Kemer_Kusak_Durumu', 'Surdurulebilirlik_Detayi', 
                              'Mensei', 'Kutu_Durumu', 'Kapama_Sekli', 'Paket_Icerigi',
                              'Persona', 'Baski_Nakis_Teknigi', 'Parca_Sayisi', 
                              'Urun_Tipi', 'Kalinlik', 'Ek_Ozellikler', 'Dokuma_Tipi',
                              'Materyal_Kumas_Tipi']
        
        for col in categorical_columns:
            if col in df.columns:
                # Boş olmayan değerleri al
                unique_values = df[col].dropna().unique()
                if len(unique_values) > 0:
                    # Her benzersiz değere bir sayı ata
                    value_to_num = {val: idx for idx, val in enumerate(unique_values)}
                    df[col] = df[col].map(value_to_num)
                    print(f"  - {col} sayisallastirildi ({len(unique_values)} benzersiz deger)")
        
        print(f"OK Sayisallasma tamamlandi.\n")
        
        # ============================================
        # 3. ADIM: EKSİK VERİ TEMİZLEME
        # ============================================
        print("="*70)
        print("3. ADIM: EKSIK VERI TEMIZLEME")
        print("="*70)
        
        # Sadece kritik sütunlarda boş olan satırları sil
        # Kritik sütunlar: Ürün_Adi, Cinsiyet, Kategori, Materyal_Kumas_Tipi
        critical_columns = ['Urun_Adi', 'Cinsiyet', 'Kategori']
        
        # Kritik sütunları kontrol et
        available_critical = [col for col in critical_columns if col in df.columns]
        
        before_count = len(df)
        
        if available_critical:
            # Sadece kritik sütunlarda boş olan satırları sil
            df = df.dropna(subset=available_critical)
            after_count = len(df)
            removed_count = before_count - after_count
            
            print(f"  - Kritik sutunlar: {', '.join(available_critical)}")
            print(f"  - {before_count} satir baslangicta")
            print(f"  - {removed_count} satir silindi (kritik sutunlarda eksik veri)")
            print(f"  - {after_count} satir kaldi")
        else:
            print(f"  - Kritik sutunlar bulunamadi, eksik veri temizligi atlandi")
            after_count = before_count
            removed_count = 0
        
        print(f"OK Eksik veri temizligi tamamlandi.\n")
        
        # ============================================
        # DOSYAYA KAYDET
        # ============================================
        print("="*70)
        print("DOSYAYA KAYDET")
        print("="*70)
        
        df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"OK '{output_file}' dosyasina kaydedildi.")
        print(f"  - Toplam {len(df)} satir, {len(df.columns)} sutun")
        print(f"  - Orijinal: {original_count} satir")
        print(f"  - Silinen: {original_count - len(df)} satir")
        print(f"{'='*70}\n")
        
        return True
        
    except FileNotFoundError:
        print(f"HATA: '{input_file}' dosyasi bulunamadi!")
        return False
    except PermissionError:
        print(f"HATA: '{input_file}' dosyasi acik!")
        print(f"  Lutfen Excel'de dosyayi kapatin ve tekrar deneyin.")
        return False
    except Exception as e:
        print(f"HATA olustu: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    preprocess_data()

