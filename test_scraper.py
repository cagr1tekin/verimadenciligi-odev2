"""
Trendyol Test Scraper - 24 Ürün Test
Yeni özelliklerle birlikte 24 ürün çeker.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import random
import re

class TrendyolTestScraper:
    def __init__(self, headless=False):
        """Selenium WebDriver'ı başlatır."""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        chrome_options.add_argument('--disable-ads')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--lang=tr-TR')
        
        prefs = {
            "profile.managed_default_content_settings.images": 1,
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.popups": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            '''
        })
        self.base_url = "https://www.trendyol.com"
        self.products = []
        self.wait = WebDriverWait(self.driver, 15)
        self.headless = headless
        self.chrome_options = chrome_options
        
    def close_all_popups(self):
        """Tüm popup'ları kapatır."""
        try:
            self.driver.execute_script("""
                var selectors = [
                    '[class*="privacy"]', '[class*="cookie"]', '[class*="popup"]',
                    '[class*="modal"]', '[class*="overlay"]', '[id*="privacy"]',
                    '[id*="cookie"]', '[id*="popup"]', '[id*="modal"]',
                    '[class*="gdpr"]', '[class*="consent"]'
                ];
                selectors.forEach(function(selector) {
                    var elements = document.querySelectorAll(selector);
                    elements.forEach(function(el) {
                        el.style.display = 'none';
                        el.remove();
                    });
                });
                document.body.classList.remove('modal-open', 'popup-open', 'overlay-open', 'cookie-open');
            """)
            time.sleep(0.5)
            
            try:
                accept_xpaths = [
                    "//button[contains(text(), 'Tümüne İzin Ver')]",
                    "//button[contains(text(), 'Kabul Et')]",
                    "//button[contains(text(), 'Accept All')]",
                ]
                for xpath in accept_xpaths:
                    buttons = self.driver.find_elements(By.XPATH, xpath)
                    for btn in buttons:
                        try:
                            if btn.is_displayed() and btn.is_enabled():
                                self.driver.execute_script("arguments[0].click();", btn)
                                time.sleep(0.5)
                                return True
                        except:
                            continue
            except:
                pass
        except:
            pass
    
    def extract_product_links_test(self, category_url, max_products=24):
        """Test için sadece 5 ürün linki çeker."""
        print(f"  Kategori sayfası yükleniyor...")
        
        try:
            self.driver.get(category_url)
            time.sleep(4)
            self.close_all_popups()
            time.sleep(2)
            
            # Sponsorlu ürünleri gizle
            try:
                self.driver.execute_script("""
                    var sponsoredElements = document.querySelectorAll('*');
                    sponsoredElements.forEach(function(el) {
                        var text = el.textContent || el.innerText || '';
                        if (text.includes('Sponsorlu') || text.includes('SPONSORLU')) {
                            var parent = el.closest('a.product-card');
                            if (parent) {
                                parent.style.display = 'none';
                            }
                        }
                    });
                """)
                time.sleep(1)
            except:
                pass
            
            # Sadece ilk birkaç scroll yap
            for i in range(2):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                self.close_all_popups()
            
            # Linkleri çek
            links_js = self.driver.execute_script("""
                var links = [];
                var cards = document.querySelectorAll('a.product-card');
                for (var i = 0; i < cards.length && links.length < 24; i++) {
                    var card = cards[i];
                    if (card.style.display === 'none') continue;
                    
                    var cardText = card.textContent || card.innerText || '';
                    var isSponsored = cardText.toLowerCase().includes('sponsorlu') || 
                                     cardText.toLowerCase().includes('sponsored');
                    
                    if (!isSponsored) {
                        var href = card.getAttribute('href');
                        if (href) {
                            if (href.startsWith('/')) {
                                href = 'https://www.trendyol.com' + href;
                            }
                            if (href.includes('-p-') || href.includes('/p-')) {
                                links.push(href);
                            }
                        }
                    }
                }
                return links;
            """)
            
            if links_js:
                product_links = list(set(links_js))[:max_products]
                print(f"  ✓ {len(product_links)} ürün linki bulundu.\n")
                return product_links
            else:
                return []
                
        except Exception as e:
            print(f"  ✗ Hata: {str(e)}")
            return []
    
    def extract_product_details(self, product_url, gender, category):
        """Ürün detay sayfasından tüm bilgileri çıkarır."""
        product_data = {
            'Urun_Adi': '',
            'Urun_Linki': product_url,  # Ürün linkini kaydet
            'Materyal_Kumas_Tipi': '',
            'Dokuma_Tipi': '',
            'Kol_Boyu': '',
            'Yaka_Tipi': '',
            'Cinsiyet': gender,
            'Kategori': category,
            'Renk': '',
            'Desen': '',
            'Kalıp': '',
            'Cep': '',
            'Boy': '',
            'Ortam': '',
            'Beden': '',
            'Stil': '',
            'Sezon': '',
            'Paca_Tipi': '',
            'Bel': '',
            'Koleksiyon': '',
            'Astar_Durumu': '',
            'Siluet': '',
            'Dokuma_Tipi_Detay': '',
            'Kemer_Kusak_Durumu': '',
            'Surdurulebilirlik_Detayi': '',
            'Mensei': '',
            'Kutu_Durumu': '',
            'Kapama_Sekli': '',
            'Paket_Icerigi': '',
            'Persona': '',
            'Baski_Nakis_Teknigi': '',
            'Parca_Sayisi': '',
            'Urun_Tipi': '',
            'Kalinlik': '',
            'Ek_Ozellikler': ''  # Şardonlu, Baskılı, vb. için
        }
        
        try:
            self.driver.get(product_url)
            time.sleep(3)
            self.close_all_popups()
            time.sleep(2)
            
            # Ürün adı
            try:
                title_elem = self.driver.find_element(By.CSS_SELECTOR, "h1.pr-new-br")
                product_data['Urun_Adi'] = title_elem.text.strip()
            except:
                try:
                    title_elem = self.driver.find_element(By.TAG_NAME, "h1")
                    product_data['Urun_Adi'] = title_elem.text.strip()
                except:
                    pass
            
            # Yeni HTML yapısı: div.attribute-item - JavaScript ile direkt çek
            try:
                attributes_data = self.driver.execute_script("""
                    var result = {};
                    var items = document.querySelectorAll('div.attribute-item');
                    
                    for (var i = 0; i < items.length; i++) {
                        var item = items[i];
                        
                        // div.name ve div.value elementlerini bul
                        var nameElem = item.querySelector('div.name');
                        var valueElem = item.querySelector('div.value');
                        
                        if (nameElem && valueElem) {
                            var key = (nameElem.textContent || nameElem.innerText || '').trim().toLowerCase();
                            var value = (valueElem.textContent || valueElem.innerText || '').trim();
                            
                            if (key && value) {
                                result[key] = value;
                            }
                        } else {
                            // Fallback: Eğer div.name ve div.value yoksa, textContent'i kullan
                            var text = item.textContent || item.innerText || '';
                            text = text.trim();
                            if (!text) continue;
                            
                            var lines = text.split('\\n');
                            var key = '';
                            var value = '';
                            
                            if (lines.length >= 2) {
                                key = lines[0].trim().toLowerCase();
                                value = lines[1].trim();
                            } else {
                                // ":" ile ayırmayı dene
                                if (text.includes(':')) {
                                    var parts = text.split(':');
                                    key = parts[0].trim().toLowerCase();
                                    value = parts.slice(1).join(':').trim();
                                } else {
                                    var words = text.split(/\\s+/);
                                    if (words.length >= 2) {
                                        key = words[0].toLowerCase();
                                        value = words.slice(1).join(' ').trim();
                                    } else {
                                        continue;
                                    }
                                }
                            }
                            
                            if (key && value) {
                                result[key] = value;
                            }
                        }
                    }
                    
                    return result;
                """)
                
                # JavaScript'ten gelen verileri işle
                for key, value in attributes_data.items():
                    # Key'den gereksiz kelimeleri temizle
                    clean_key = key.replace('tipi', '').replace('boyu', '').replace('bileşeni', '').replace('içerik', '').strip()
                    
                    if 'materyal' in key or 'kumaş' in key:
                        if not product_data['Materyal_Kumas_Tipi']:
                            product_data['Materyal_Kumas_Tipi'] = value
                    elif 'kumaş tipi' in key or 'dokuma' in key or clean_key == 'dokuma':
                        if not product_data['Dokuma_Tipi']:
                            product_data['Dokuma_Tipi'] = value
                    elif 'kol tipi' in key or 'kol boyu' in key or key == 'kol' or clean_key == 'kol':
                        if not product_data['Kol_Boyu']:
                            product_data['Kol_Boyu'] = value
                    elif 'yaka tipi' in key or 'yaka' in key or clean_key == 'yaka':
                        if not product_data['Yaka_Tipi']:
                            product_data['Yaka_Tipi'] = value
            except Exception as e:
                pass
            
            # Tüm attribute'ları çek (bir kez çek, sonra kullan) - div.name ve div.value kullan
            all_attrs = {}
            try:
                all_attrs = self.driver.execute_script("""
                    var result = {};
                    var items = document.querySelectorAll('div.attribute-item');
                    for (var i = 0; i < items.length; i++) {
                        var item = items[i];
                        
                        // div.name ve div.value elementlerini bul
                        var nameElem = item.querySelector('div.name');
                        var valueElem = item.querySelector('div.value');
                        
                        if (nameElem && valueElem) {
                            var key = (nameElem.textContent || nameElem.innerText || '').trim().toLowerCase();
                            var value = (valueElem.textContent || valueElem.innerText || '').trim();
                            
                            if (key && value) {
                                result[key] = value;
                            }
                        } else {
                            // Fallback: Eğer div.name ve div.value yoksa, textContent'i kullan
                            var text = item.textContent || item.innerText || '';
                            text = text.trim();
                            if (!text) continue;
                            
                            var lines = text.split('\\n');
                            var key = '';
                            var value = '';
                            
                            if (lines.length >= 2) {
                                key = lines[0].trim().toLowerCase();
                                value = lines[1].trim();
                            } else {
                                // ":" ile ayırmayı dene
                                if (text.includes(':')) {
                                    var parts = text.split(':');
                                    key = parts[0].trim().toLowerCase();
                                    value = parts.slice(1).join(':').trim();
                                } else {
                                    var words = text.split(/\\s+/);
                                    if (words.length >= 2) {
                                        key = words[0].toLowerCase();
                                        value = words.slice(1).join(' ').trim();
                                    }
                                }
                            }
                            
                            if (key && value) {
                                result[key] = value;
                            }
                        }
                    }
                    return result;
                """)
            except:
                pass
            
            # Ayrı kolonlara yaz - key'leri daha esnek kontrol et
            # Önce tüm key'leri normalize et (boşlukları kaldır, küçük harfe çevir)
            for key, value in all_attrs.items():
                if not key or not value:
                    continue
                
                # Key'i normalize et
                key_normalized = key.lower().strip()
                # Boşlukları ve özel karakterleri kaldır
                key_clean = key_normalized.replace(' ', '').replace('_', '').replace('-', '')
                
                # Her özellik için esnek eşleştirme
                if 'renk' in key_normalized or key_clean == 'renk' or key_normalized.startswith('renk'):
                    if not product_data['Renk']:
                        product_data['Renk'] = value
                elif 'desen' in key_normalized or key_clean == 'desen' or key_normalized.startswith('desen'):
                    if not product_data['Desen']:
                        product_data['Desen'] = value
                elif 'kalıp' in key_normalized or key_clean == 'kalıp' or key_normalized.startswith('kalıp'):
                    if not product_data['Kalıp']:
                        product_data['Kalıp'] = value
                elif 'cep' in key_normalized or key_clean == 'cep' or key_normalized.startswith('cep'):
                    if not product_data['Cep']:
                        product_data['Cep'] = value
                elif ('boy' in key_normalized or key_clean == 'boy' or key_normalized.startswith('boy')) and 'kol' not in key_normalized:  # "Kol Boyu" ile karışmasın
                    if not product_data['Boy']:
                        product_data['Boy'] = value
                elif 'ortam' in key_normalized or key_clean == 'ortam' or key_normalized.startswith('ortam'):
                    if not product_data['Ortam']:
                        product_data['Ortam'] = value
                elif 'beden' in key_normalized or key_clean == 'beden' or key_normalized.startswith('beden'):
                    if not product_data['Beden']:
                        product_data['Beden'] = value
                elif 'stil' in key_normalized or key_clean == 'stil' or key_normalized.startswith('stil'):
                    if not product_data['Stil']:
                        product_data['Stil'] = value
                elif 'sezon' in key_normalized or key_clean == 'sezon' or key_normalized.startswith('sezon'):
                    if not product_data['Sezon']:
                        product_data['Sezon'] = value
                elif 'paça tipi' in key_normalized or 'paça' in key_normalized or key_clean == 'paça' or key_clean == 'paca':
                    if not product_data['Paca_Tipi']:
                        product_data['Paca_Tipi'] = value
                elif 'bel' in key_normalized and 'durumu' not in key_normalized:
                    if not product_data['Bel']:
                        product_data['Bel'] = value
                elif 'koleksiyon' in key_normalized or key_clean == 'koleksiyon':
                    if not product_data['Koleksiyon']:
                        product_data['Koleksiyon'] = value
                elif 'astar durumu' in key_normalized or 'astar' in key_normalized:
                    if not product_data['Astar_Durumu']:
                        product_data['Astar_Durumu'] = value
                elif 'siluet' in key_normalized or key_clean == 'siluet':
                    if not product_data['Siluet']:
                        product_data['Siluet'] = value
                elif 'dokuma tipi' in key_normalized and not product_data['Dokuma_Tipi_Detay']:
                    if not product_data['Dokuma_Tipi_Detay']:
                        product_data['Dokuma_Tipi_Detay'] = value
                elif 'kemer' in key_normalized or 'kuşak' in key_normalized or 'kemer/kuşak' in key_normalized:
                    if not product_data['Kemer_Kusak_Durumu']:
                        product_data['Kemer_Kusak_Durumu'] = value
                elif 'sürdürülebilirlik' in key_normalized or 'surdurulebilirlik' in key_normalized:
                    if not product_data['Surdurulebilirlik_Detayi']:
                        product_data['Surdurulebilirlik_Detayi'] = value
                elif 'menşei' in key_normalized or 'mensei' in key_normalized or 'menşe' in key_normalized:
                    if not product_data['Mensei']:
                        product_data['Mensei'] = value
                elif 'kutu durumu' in key_normalized or 'kutu' in key_normalized:
                    if not product_data['Kutu_Durumu']:
                        product_data['Kutu_Durumu'] = value
                elif 'kapama şekli' in key_normalized or 'kapama' in key_normalized:
                    if not product_data['Kapama_Sekli']:
                        product_data['Kapama_Sekli'] = value
                elif 'paket içeriği' in key_normalized or 'paket' in key_normalized:
                    if not product_data['Paket_Icerigi']:
                        product_data['Paket_Icerigi'] = value
                elif 'persona' in key_normalized or key_clean == 'persona':
                    if not product_data['Persona']:
                        product_data['Persona'] = value
                elif 'baskı' in key_normalized or 'nakış' in key_normalized or 'baski' in key_normalized or 'nakis' in key_normalized:
                    if 'tekniği' in key_normalized or 'teknigi' in key_normalized:
                        if not product_data['Baski_Nakis_Teknigi']:
                            product_data['Baski_Nakis_Teknigi'] = value
                elif 'parça sayısı' in key_normalized or 'parça' in key_normalized or 'parca' in key_normalized:
                    if not product_data['Parca_Sayisi']:
                        product_data['Parca_Sayisi'] = value
                elif 'ürün tipi' in key_normalized or 'urun tipi' in key_normalized:
                    if not product_data['Urun_Tipi']:
                        product_data['Urun_Tipi'] = value
                elif 'kalınlık' in key_normalized or 'kalinlik' in key_normalized or 'kalınlık' in key_normalized:
                    if not product_data['Kalinlik']:
                        product_data['Kalinlik'] = value
                elif 'ek özellik' in key_normalized or 'ek ozellik' in key_normalized:
                    # Eğer "Ek Özellik Mevcut Değil" değilse, değeri kaydet
                    if value.lower() != 'ek özellik mevcut değil' and value.lower() != 'ek ozellik mevcut degil':
                        if not product_data['Ek_Ozellikler']:
                            product_data['Ek_Ozellikler'] = value
                        else:
                            product_data['Ek_Ozellikler'] += ', ' + value
            
            # Ek özellikler (Şardonlu, Baskılı, vb.) - sadece özel özellikler için
            # Eğer Ek_Ozellikler boşsa, keyword bazlı kontrol yap
            if not product_data['Ek_Ozellikler']:
                ek_ozellikler = []
                ek_ozellik_keywords = ['şardonlu', 'baskılı', 'nakışlı', 'desenli', 'logolu', 'oversize', 'slim fit', 'regular fit', 'relaxed fit', 'extra yumuşak', 'yumuşak']
                
                try:
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                    product_name_lower = product_data['Urun_Adi'].lower()
                    
                    for keyword in ek_ozellik_keywords:
                        if keyword in product_name_lower or keyword in page_text:
                            ek_ozellikler.append(keyword.capitalize())
                except:
                    pass
                
                if ek_ozellikler:
                    product_data['Ek_Ozellikler'] = ', '.join(ek_ozellikler)
            
            return product_data
            
        except Exception as e:
            print(f"    ✗ Hata: {str(e)}")
            return None
    
    def test_scrape(self, category_url, gender, category_name, max_products=24):
        """Test için 24 ürün çeker."""
        print(f"\n{'='*70}")
        print(f"TEST: {gender} - {category_name} (Sadece {max_products} ürün)")
        print(f"{'='*70}\n")
        
        # Ürün linklerini topla
        print("1. Adım: Ürün linkleri toplanıyor...")
        product_links = self.extract_product_links_test(category_url, max_products=max_products)
        
        if not product_links:
            print("  ✗ Hiç ürün linki bulunamadı!")
            return
        
        # Her ürünün detaylarını çek
        print(f"\n2. Adım: {len(product_links)} ürünün detayları çekiliyor...\n")
        
        for idx, link in enumerate(product_links, 1):
            print(f"[{idx}/{len(product_links)}] İşleniyor...")
            
            product_data = self.extract_product_details(link, gender, category_name)
            
            if product_data and product_data['Urun_Adi']:
                self.products.append(product_data)
                print(f"  ✓ {product_data['Urun_Adi'][:60]}...")
                print(f"    Materyal: {product_data['Materyal_Kumas_Tipi'] or 'Bulunamadı'}")
                print(f"    Dokuma: {product_data['Dokuma_Tipi'] or 'Bulunamadı'}")
                print(f"    Kol: {product_data['Kol_Boyu'] or 'Bulunamadı'}")
                print(f"    Yaka: {product_data['Yaka_Tipi'] or 'Bulunamadı'}")
                print(f"    Renk: {product_data['Renk'] or 'Bulunamadı'}")
                print(f"    Desen: {product_data['Desen'] or 'Bulunamadı'}")
                print(f"    Kalıp: {product_data['Kalıp'] or 'Bulunamadı'}")
                print(f"    Cep: {product_data['Cep'] or 'Bulunamadı'}")
                print(f"    Boy: {product_data['Boy'] or 'Bulunamadı'}")
                print(f"    Ortam: {product_data['Ortam'] or 'Bulunamadı'}")
                print(f"    Beden: {product_data['Beden'] or 'Bulunamadı'}")
                print(f"    Stil: {product_data['Stil'] or 'Bulunamadı'}")
                print(f"    Sezon: {product_data['Sezon'] or 'Bulunamadı'}")
                print(f"    Ek Özellikler: {product_data['Ek_Ozellikler'] or 'Bulunamadı'}")
                print()
            else:
                print(f"  ✗ Veri çekilemedi\n")
            
            time.sleep(random.uniform(2, 3))
    
    def save_to_excel(self, filename='test.xlsx'):
        """Test verilerini Excel'e kaydeder."""
        if not self.products:
            print("Kaydedilecek veri yok!")
            return
        
        df = pd.DataFrame(self.products)
        
        columns_order = [
            'Urun_Adi', 'Materyal_Kumas_Tipi', 'Dokuma_Tipi', 
            'Kol_Boyu', 'Yaka_Tipi', 'Cinsiyet', 'Kategori',
            'Renk', 'Desen', 'Kalıp', 'Cep', 'Boy', 'Ortam', 'Beden', 'Stil', 'Sezon',
            'Paca_Tipi', 'Bel', 'Koleksiyon', 'Astar_Durumu', 'Siluet', 'Dokuma_Tipi_Detay',
            'Kemer_Kusak_Durumu', 'Surdurulebilirlik_Detayi', 'Mensei', 'Kutu_Durumu',
            'Kapama_Sekli', 'Paket_Icerigi', 'Persona', 'Baski_Nakis_Teknigi', 'Parca_Sayisi',
            'Urun_Tipi', 'Kalinlik', 'Ek_Ozellikler'
        ]
        df = df[columns_order]
        
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"\n{'='*70}")
        print(f"✓ Test verileri '{filename}' dosyasına kaydedildi.")
        print(f"✓ Toplam {len(df)} satır veri toplandı.")
        print(f"{'='*70}\n")
        
        return df
    
    def close(self):
        """WebDriver'ı kapatır."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

def main():
    """Test fonksiyonu"""
    scraper = None
    try:
        scraper = TrendyolTestScraper(headless=False)
        
        # Test için sadece Erkek T-shirt kategorisinden 24 ürün
        erkek_tisort_url = 'https://www.trendyol.com/erkek-tisort-x-g2-c73'
        scraper.test_scrape(erkek_tisort_url, "Erkek", "T-shirt", max_products=24)
        
        # Excel'e kaydet
        scraper.save_to_excel('test.xlsx')
        
        print("\n✓ Test tamamlandı!")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Test kullanıcı tarafından durduruldu.")
        if scraper:
            scraper.save_to_excel('test.xlsx')
            print("Mevcut veriler kaydedildi.")
    except Exception as e:
        print(f"\n✗ Hata oluştu: {str(e)}")
        import traceback
        traceback.print_exc()
        if scraper:
            scraper.save_to_excel('test.xlsx')
            print("Mevcut veriler kaydedildi.")
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()

