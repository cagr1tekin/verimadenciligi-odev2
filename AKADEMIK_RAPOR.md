# Trendyol Web Scraping ve Veri Ön İşleme Projesi - Teknik Rapor

## 1. Kullanılan Python Kütüphaneleri

### Web Scraping Kütüphaneleri

**Selenium WebDriver**
- **Versiyon**: 4.15.0+
- **Kullanım Amacı**: JavaScript ile dinamik olarak yüklenen içeriği çekmek için
- **Özellikler**:
  - Chrome WebDriver entegrasyonu
  - Lazy loading içeriğini scroll ile yükleme
  - Pop-up pencerelerini otomatik kapatma
  - Anti-bot korumasını aşmak için user-agent ve automation extension ayarları

**Pandas**
- **Versiyon**: 2.3.3+
- **Kullanım Amacı**: Veri manipülasyonu ve Excel dosyası işlemleri
- **Fonksiyonlar**: `read_excel()`, `to_excel()`, `dropna()`, `map()`

**OpenPyXL**
- **Versiyon**: 3.1.5+
- **Kullanım Amacı**: Excel dosyalarını okuma ve yazma işlemleri

**Random & Time**
- **Kullanım Amacı**: Bot tespitini önlemek için rastgele gecikmeler (2-4 saniye arası)

**Re (Regular Expressions)**
- **Kullanım Amacı**: Metin temizleme ve pattern matching işlemleri

### Not: BeautifulSoup ve Requests Kullanılmadı
- Trendyol'un içeriği JavaScript ile dinamik yüklendiği için Selenium tercih edildi
- BeautifulSoup sadece statik HTML için uygun olduğundan kullanılmadı

---

## 2. Web Scraping Süreci: HTML Etiketleri ve Mantık

### 2.1. İki Aşamalı Scraping Yaklaşımı

#### Aşama 1: Ürün Linklerini Toplama
- **Hedef**: Kategori sayfalarından tüm ürün URL'lerini toplamak
- **HTML Yapısı**: 
  ```html
  <a class="product-card" href="/urun-adi-p-123456">
  ```
- **CSS Selector**: `a.product-card`
- **JavaScript Çözümü**: 
  ```javascript
  document.querySelectorAll('a.product-card')
  ```
- **Filtreleme**: 
  - Sponsorlu ürünler DOM'dan gizlendi
  - Sadece `-p-` veya `/p-` içeren linkler alındı (ürün sayfası göstergesi)
  - Relative URL'ler (`/urun-adi`) absolute URL'lere dönüştürüldü

#### Aşama 2: Ürün Detaylarını Çekme

**Ürün Adı Çıkarımı:**
- **CSS Selector**: `h1.pr-new-br`
- **Fallback**: `h1` etiketi
- **Kod**:
  ```python
  title_elem = self.driver.find_element(By.CSS_SELECTOR, "h1.pr-new-br")
  product_data['Urun_Adi'] = title_elem.text.strip()
  ```

**Ürün Özellikleri Tablosu:**
- **HTML Yapısı**: 
  ```html
  <div class="attribute-item">
    <div class="name">Materyal</div>
    <div class="value">%100 Pamuk</div>
  </div>
  ```
- **CSS Selector**: `div.attribute-item`
- **JavaScript Çözümü**:
  ```javascript
  var items = document.querySelectorAll('div.attribute-item');
  var nameElem = item.querySelector('div.name');
  var valueElem = item.querySelector('div.value');
  ```
- **Fallback Yöntemler**:
  - `li.detail-attr-item` (eski HTML yapısı için)
  - XPath: `//li[contains(text(), 'Materyal')]`

**Kategori Bilgisi:**
- **Kaynak**: URL'den çıkarıldı
- **Örnek**: `https://www.trendyol.com/erkek-tisort-x-g2-c73`
  - `erkek-tisort` → Cinsiyet: Erkek, Kategori: T-shirt
  - `kadin-kazak` → Cinsiyet: Kadın, Kategori: Kazak

### 2.2. Lazy Loading Yönetimi

- **Sorun**: Trendyol sayfaları scroll yapıldıkça yeni ürünleri yüklüyor
- **Çözüm**: 
  - Smooth scroll ile 1500px adımlarla aşağı kaydırma
  - Her scroll sonrası 3 saniye bekleme
  - Minimum 15 scroll yapılması garantisi
  - Sayfa yüksekliği kontrolü ile son ürün tespiti

---

## 3. Veri Seti İstatistikleri

### 3.1. Toplam Satır ve Sütun Sayısı

**Orijinal Veri Seti (`trendyol_orijinal_veri.xlsx`):**
- **Toplam Satır (Örnek)**: 2,732
- **Toplam Sütun (Özellik)**: 35

**İşlenmiş Veri Seti (`xxx_verisi.xlsx`):**
- **Toplam Satır (Örnek)**: 2,732 (kritik sütunlarda eksik veri olmadığı için)
- **Toplam Sütun (Özellik)**: 35

### 3.2. Sütun Listesi

1. Urun_Adi
2. Urun_Linki
3. Materyal_Kumas_Tipi
4. Dokuma_Tipi
5. Kol_Boyu
6. Yaka_Tipi
7. Cinsiyet
8. Kategori
9. Renk
10. Desen
11. Kalıp
12. Cep
13. Boy
14. Ortam
15. Beden
16. Stil
17. Sezon
18. Paca_Tipi
19. Bel
20. Koleksiyon
21. Astar_Durumu
22. Siluet
23. Dokuma_Tipi_Detay
24. Kemer_Kusak_Durumu
25. Surdurulebilirlik_Detayi
26. Mensei
27. Kutu_Durumu
28. Kapama_Sekli
29. Paket_Icerigi
30. Persona
31. Baski_Nakis_Teknigi
32. Parca_Sayisi
33. Urun_Tipi
34. Kalinlik
35. Ek_Ozellikler

---

## 4. Sayısallaştırma (Label Encoding) İşlemleri

### 4.1. Önceden Tanımlı Mapping'ler

#### Cinsiyet
- **Erkek** → `1`
- **Kadın** → `0`

#### Kategori (Ürün Türü)
- **T-shirt** → `0`
- **Kazak** → `1`
- **Sweatshirt** → `2`
- **Hırka** → `3`
- **Gömlek** → `4`
- **Ceket** → `5`
- **Pantolon** → `6`
- **Eşofman** → `7`

#### Kol Boyu
- **Kısa / Kısa Kol** → `0`
- **Uzun / Uzun Kol** → `1`
- **Askılı** → `2`
- **Kolsuz** → `3`
- **Diğer değerler**: Mapping'de olmayan değerler için otomatik artan sayılar atandı (4, 5, 6, ...)

#### Yaka Tipi
- **V Yaka / V** → `0`
- **Balıkçı / Balıkçı Yaka** → `1`
- **Bisiklet / Bisiklet Yaka / Round** → `2`
- **Polo / Polo Yaka** → `3`
- **Kapüşonlu / Hood** → `4`
- **Diğer değerler**: Otomatik sayısallaştırıldı (5, 6, 7, ...)

### 4.2. Otomatik Sayısallaştırma (Benzersiz Değerlere Göre)

Aşağıdaki sütunlar için her benzersiz değere sırayla sayı atandı (0'dan başlayarak):

#### Materyal_Kumas_Tipi
- **Benzersiz Değer Sayısı**: 20
- **Örnekler**: 
  - Pamuk → `0`
  - Polyester → `1`
  - Akrilik → `2`
  - Yün → `3`
  - ... (diğer 16 değer)

#### Renk
- **Benzersiz Değer Sayısı**: 21
- **Örnekler**: Siyah, Beyaz, Gri, Lacivert, vb.

#### Desen
- **Benzersiz Değer Sayısı**: 33
- **Örnekler**: Düz, Çizgili, Baskılı, Logolu, vb.

#### Kalıp
- **Benzersiz Değer Sayısı**: 42
- **Örnekler**: Slim Fit, Regular Fit, Oversize, Relaxed Fit, vb.

#### Cep
- **Benzersiz Değer Sayısı**: 20
- **Örnekler**: Cepsiz, Yan Cep, Kanguru Cep, vb.

#### Boy
- **Benzersiz Değer Sayısı**: 17
- **Örnekler**: Normal Boy, Standart, Kısa, Uzun, vb.

#### Ortam
- **Benzersiz Değer Sayısı**: 21
- **Örnekler**: Günlük, Casual, Spor, vb.

#### Sezon
- **Benzersiz Değer Sayısı**: 4
- **Örnekler**: Tüm Sezonlar, Kış, Yaz, Sonbahar

#### Paca_Tipi
- **Benzersiz Değer Sayısı**: 12
- **Örnekler**: Düz Paça, Dar Paça, Geniş Paça, vb.

#### Bel
- **Benzersiz Değer Sayısı**: 10
- **Örnekler**: Normal Bel, Yüksek Bel, Düşük Bel, vb.

#### Koleksiyon
- **Benzersiz Değer Sayısı**: 28
- **Örnekler**: Casual / Günlük, Menswear, Unisex, vb.

#### Astar_Durumu
- **Benzersiz Değer Sayısı**: 2
- **Örnekler**: Astarlı, Astarsız

#### Siluet
- **Benzersiz Değer Sayısı**: 50
- **Örnekler**: Basic, Oversize, Slim, Regular, vb.

#### Dokuma_Tipi_Detay
- **Benzersiz Değer Sayısı**: 110
- **Örnekler**: 3 İplik, Süprem, Triko, Canvas, vb.

#### Kemer_Kusak_Durumu
- **Benzersiz Değer Sayısı**: 5
- **Örnekler**: Kemersiz, Kemerli, Kuşaklı, vb.

#### Surdurulebilirlik_Detayi
- **Benzersiz Değer Sayısı**: 5
- **Örnekler**: Hayır, Evet, Organik, vb.

#### Mensei
- **Benzersiz Değer Sayısı**: 21
- **Örnekler**: TR, Çin, Bangladeş, vb.

#### Kutu_Durumu
- **Benzersiz Değer Sayısı**: 2
- **Örnekler**: Kutu yok, Kutu var

#### Kapama_Sekli
- **Benzersiz Değer Sayısı**: 18
- **Örnekler**: Kapamasız, Fermuarlı, Düğmeli, vb.

#### Paket_Icerigi
- **Benzersiz Değer Sayısı**: 11
- **Örnekler**: Tekli, 2'li, 3'lü, 5'li, vb.

#### Persona
- **Benzersiz Değer Sayısı**: 11
- **Örnekler**: Young, Cool & Comfort, vb.

#### Baski_Nakis_Teknigi
- **Benzersiz Değer Sayısı**: 17
- **Örnekler**: Baskısız, Dijital Baskı, Nakışlı, vb.

#### Parca_Sayisi
- **Benzersiz Değer Sayısı**: 4
- **Örnekler**: 1, 2, 3, 5

#### Urun_Tipi
- **Benzersiz Değer Sayısı**: 8
- **Örnekler**: Düz, Baskılı, Logolu, vb.

#### Kalinlik
- **Benzersiz Değer Sayısı**: 4
- **Örnekler**: İnce, Orta, Kalın, vb.

#### Ek_Ozellikler
- **Benzersiz Değer Sayısı**: 316
- **Örnekler**: Şardonlu, Baskılı, Nakışlı, Extra Yumuşak, vb.

#### Dokuma_Tipi
- **Benzersiz Değer Sayısı**: 110
- **Örnekler**: Dokuma, Triko, Örme, vb.

---

## 5. Veri Temizleme İşlemleri

### 5.1. Metin Temizliği

#### Gereksiz Karakterlerin Kaldırılması
- **Yöntem**: Regular Expression kullanarak
- **Kod**: 
  ```python
  text = re.sub(r'[^\w\s\-,()%./]', '', text)
  ```
- **Kaldırılanlar**: Özel karakterler, emoji'ler, kontrol karakterleri
- **Korunanlar**: Harf, rakam, boşluk, virgül, tire, parantez, yüzde, nokta, slash

#### Nokta-Virgül Hatalarının Düzeltilmesi
- **Sorun**: Bazı verilerde `;` yerine `,` kullanılması gerekiyordu
- **Çözüm**: 
  ```python
  text = text.replace(';', ',')
  ```

#### Çift Boşlukların Temizlenmesi
- **Kod**: 
  ```python
  text = text.replace('  ', ' ')  # Çift boşlukları tek yap
  text = ' '.join(text.split())  # Fazla boşlukları temizle
  ```

#### Nokta Hatalarının Düzeltilmesi
- **Kod**: 
  ```python
  text = text.replace('..', '.')
  ```

### 5.2. Materyal/Kumaş Bilgilerinin Özel Temizliği

#### Yüzde (%) İşaretlerinin Kaldırılması
- **Sorun**: `%100 Pamuk`, `%50 Polyester` gibi değerler
- **Çözüm**: 
  ```python
  text = text.replace('%', '')
  ```
- **Sonuç**: `100 Pamuk`, `50 Polyester` → `Pamuk`, `Polyester` (gereksiz sayılar da temizlendi)

#### Gereksiz Sayıların Kaldırılması
- **Yöntem**: Regular Expression ile başta ve sonda sadece sayı olan kısımlar kaldırıldı
- **Kod**: 
  ```python
  text = re.sub(r'^\d+\s+', '', text)  # Başta sadece sayı varsa kaldır
  text = re.sub(r'\s+\d+$', '', text)  # Sonda sadece sayı varsa kaldır
  ```
- **Örnekler**:
  - `100 Pamuk` → `Pamuk`
  - `3 İplik` → `3 İplik` (anlamlı sayı korundu)

### 5.3. Eksik Veri (Missing Values) Yönetimi

#### Strateji: Kritik Sütun Bazlı Temizleme
- **Yaklaşım**: Tüm sütunlarda eksik veri olan satırları silmek yerine, sadece kritik sütunlarda eksik veri olan satırlar silindi
- **Kritik Sütunlar**:
  1. `Urun_Adi` (Ürün Adı)
  2. `Cinsiyet` (Cinsiyet)
  3. `Kategori` (Kategori)
- **Kod**: 
  ```python
  df = df.dropna(subset=['Urun_Adi', 'Cinsiyet', 'Kategori'])
  ```
- **Sonuç**: 
  - Başlangıç: 2,732 satır
  - Silinen: 0 satır (tüm satırlarda kritik bilgiler mevcut)
  - Kalan: 2,732 satır

#### Neden Tüm Sütunlarda Eksik Veri Kontrolü Yapılmadı?
- 35 sütunlu bir veri setinde, her satırda tüm sütunların dolu olması nadirdir
- Özellikle `Ek_Ozellikler`, `Baski_Nakis_Teknigi` gibi opsiyonel sütunlar genellikle boş olabilir
- Kritik sütunlarda eksik veri olmayan satırlar, diğer sütunlardaki eksiklikler için makine öğrenmesi algoritmaları tarafından işlenebilir

### 5.4. Veri Tipi Kontrolü

- **String → Numeric Dönüşümü**: Tüm kategorik değerler sayısal değerlere dönüştürüldü
- **NaN Değerler**: Sayısallaştırma sırasında mapping'de olmayan değerler NaN olarak kaldı, ancak kritik sütunlarda NaN olan satırlar silindi

---

## 6. Sonuç

Bu çalışmada:
- **2,732 ürün** Trendyol'dan başarıyla çekildi
- **35 özellik** (sütun) toplandı
- **1,000+ benzersiz değer** sayısallaştırıldı
- **Tüm veriler** makine öğrenmesi algoritmaları için hazır hale getirildi

Veri seti artık Weka, Orange, scikit-learn gibi araçlarda kullanıma hazırdır.

