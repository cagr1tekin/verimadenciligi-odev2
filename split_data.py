"""
Trendyol Verilerini İkiye Bölme Scripti
1. xxx_orijinal_veri.xlsx - Ham veri (değiştirilmemiş)
2. xxx_verisi.xlsx - İşlenmiş veri için kopya
"""

import pandas as pd
import os

def split_data():
    """Trendyol verilerini iki ayrı dosyaya böler."""
    
    # Orijinal dosya adı
    input_file = 'trendyol_orijinal_veri.xlsx'
    
    # Çıktı dosya adları
    original_output = 'xxx_orijinal_veri.xlsx'
    processed_output = 'xxx_verisi.xlsx'
    
    try:
        # Excel dosyasını oku
        print(f"'{input_file}' dosyasi okunuyor...")
        df = pd.read_excel(input_file, engine='openpyxl')
        
        print(f"OK Dosya okundu. Toplam {len(df)} satir, {len(df.columns)} sutun bulundu.")
        print(f"  Sutunlar: {', '.join(df.columns.tolist())}\n")
        
        # 1. Adım: Orijinal veriyi hiçbir değişiklik yapmadan kaydet
        print(f"1. Adim: Orijinal veri kaydediliyor...")
        df.to_excel(original_output, index=False, engine='openpyxl')
        print(f"  OK '{original_output}' dosyasi olusturuldu ({len(df)} satir)\n")
        
        # 2. Adım: İşlenmiş veri için kopya oluştur
        print(f"2. Adim: Islenmis veri icin kopya olusturuluyor...")
        df_copy = df.copy()  # Verinin bir kopyasını oluştur
        df_copy.to_excel(processed_output, index=False, engine='openpyxl')
        print(f"  OK '{processed_output}' dosyasi olusturuldu ({len(df_copy)} satir)\n")
        
        print(f"{'='*70}")
        print(f"OK Islem tamamlandi!")
        print(f"  - {original_output}: Ham veri (degistirilmemis)")
        print(f"  - {processed_output}: Islenmis veri icin kopya")
        print(f"{'='*70}\n")
        
        return True
        
    except FileNotFoundError:
        print(f"HATA: '{input_file}' dosyasi bulunamadi!")
        print(f"  Lutfen dosyanin mevcut dizinde oldugundan emin olun.")
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
    split_data()

