# Trendyol Web Scraping Script - Selenium ile

Bu script, Trendyol sitesinden Erkek ve Kadın "Üst Giyim" kategorisindeki ürünleri çeker.

## Özellikler

- ✅ **Selenium WebDriver** kullanarak JavaScript ile yüklenen içeriği çeker
- ✅ **İki Adımlı Scraping**: Önce liste sayfalarından linkler, sonra detay sayfalarından bilgiler
- ✅ Erkek ve Kadın kategorilerinden veri çekme (her biri için ilk 5 sayfa)
- ✅ Ürün adı, materyal, kol tipi ve cinsiyet bilgilerini toplama
- ✅ Excel formatında kaydetme

## Kurulum

### 1. Python Kütüphaneleri

```bash
pip install -r requirements.txt
```

### 2. Chrome WebDriver

Selenium için Chrome WebDriver gereklidir. İki seçenek:

**Seçenek A: Otomatik (Önerilen)**
- Selenium 4.6+ otomatik olarak WebDriver'ı yönetir
- Chrome tarayıcısı yüklü olmalı

**Seçenek B: Manuel**
- [ChromeDriver](https://chromedriver.chromium.org/) indirin
- PATH'e ekleyin veya script içinde belirtin

## Kullanım

```bash
python trendyol_scraper.py
```

### Script Çalışma Mantığı

1. **1. Adım**: Liste sayfalarından (ilk 5 sayfa) tüm ürün linklerini toplar
2. **2. Adım**: Her linke gidip "Ürün Özellikleri" bölümünden:
   - **Materyal** bilgisini çeker (örn: %100 Pamuk)
   - **Kol Tipi** bilgisini çeker (örn: Kısa Kol)
   - **Ürün Adı** bilgisini çeker
3. Verileri `trendyol_orijinal_veri.xlsx` dosyasına kaydeder

## Çıktı Formatı

Excel dosyası şu sütunları içerir:
- `Urun_Adi`: Ürün adı
- `Materyal`: Kumaş materyali bilgisi (örn: %100 Pamuk)
- `Kol_Tipi`: Kol tipi bilgisi (örn: Kısa Kol, Uzun Kol)
- `Cinsiyet`: Erkek veya Kadın

## Notlar

- Script, Trendyol'un bot korumasını aşmak için:
  - Rastgele gecikmeler kullanır (2-4 saniye)
  - User-Agent header'ı ekler
  - Tarayıcı otomasyonunu gizler
- Her kategori için ilk 5 sayfa işlenir
- Her 20 üründe bir ilerleme raporu gösterilir
- Ctrl+C ile durdurulursa mevcut veriler kaydedilir

## Önemli Uyarılar

⚠️ Bu script eğitim amaçlıdır. Trendyol'un kullanım şartlarına uygun olarak kullanın.
⚠️ Web scraping yaparken sitenin sunucularına aşırı yük bindirmemeye dikkat edin.
⚠️ Chrome tarayıcısının yüklü olması gereklidir.

