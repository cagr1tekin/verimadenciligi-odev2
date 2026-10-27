"""
Trendyol Web Scraping Script - Detaylı Ürün Bilgileri
Erkek ve Kadın T-shirt, Kazak, Sweatshirt, Hırka kategorilerinden veri çeker.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import random
import re

class TrendyolScraper:
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
            
            # "Tümüne İzin Ver" butonunu bul ve tıkla
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
    
    def check_session(self):
        """WebDriver session'ının aktif olup olmadığını kontrol eder."""
        try:
            self.driver.current_url
            return True
        except:
            return False
    
    def restart_driver(self):
        """WebDriver'ı yeniden başlatır (session hatası durumunda)."""
        try:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
        except:
            pass
        
        print("  ⚠ WebDriver session hatası! Yeniden başlatılıyor...")
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.driver.maximize_window()
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            '''
        })
        self.wait = WebDriverWait(self.driver, 15)
        print("  ✓ WebDriver yeniden başlatıldı.")
        time.sleep(2)
    
    def close(self):
        """WebDriver'ı kapatır."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def extract_product_links_with_scroll(self, category_url, max_products=1000):
        """
        Lazy loading ile belirli pixel değerlerinde scroll yaparak ürün linklerini çıkarır.
        3000px, 3500px, 4000px gibi belirli aralıklarda scroll yapıp yeni ürünlerin yüklenmesini bekler.
        """
        print(f"  Kategori sayfası yükleniyor ve scroll ile ürünler toplanıyor...")
        
        try:
            self.driver.get(category_url)
            time.sleep(4)
            self.close_all_popups()
            time.sleep(2)
            
            # Scroll pozisyonunu sıfırla (her kategori için temiz başlangıç)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # İlk sayfa yüksekliğini al
            initial_page_height = self.driver.execute_script("return document.body.scrollHeight;")
            print(f"  İlk sayfa yüksekliği: {initial_page_height}px")
            
            all_links = set()
            last_link_count = 0
            no_new_products_count = 0
            scroll_position = 0
            scroll_increment = 1500  # Her scroll'da 1500px ilerle
            max_scroll_position = 100000  # Maksimum scroll pozisyonu
            min_scrolls = 15  # Minimum scroll sayısı (erken durmayı önlemek için)
            scroll_count = 0
            
            print(f"  Scroll yaparak ürünler yükleniyor (Hedef: {max_products} ürün)...")
            
            while len(all_links) < max_products and scroll_position < max_scroll_position:
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
                except:
                    pass
                
                # Adım adım 1500px scroll yap (smooth scroll)
                scroll_count += 1
                # Smooth scroll ile 1500px aşağı kaydır
                self.driver.execute_script(f"""
                    window.scrollBy({{
                        top: {scroll_increment},
                        left: 0,
                        behavior: 'smooth'
                    }});
                """)
                # Scroll pozisyonunu güncelle
                scroll_position += scroll_increment
                # Smooth scroll'un tamamlanmasını bekle
                time.sleep(3)  # Smooth scroll için daha uzun bekleme
                
                # Popup'ları kapat
                self.close_all_popups()
                time.sleep(0.5)  # Popup kapatma sonrası kısa bekleme
                
                # Mevcut linkleri çek
                links_js = self.driver.execute_script("""
                    var links = [];
                    var cards = document.querySelectorAll('a.product-card');
                    for (var i = 0; i < cards.length; i++) {
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
                    new_links = set(links_js)
                    all_links.update(new_links)
                    
                    # Yeni ürün yüklendi mi kontrol et
                    if len(all_links) > last_link_count:
                        last_link_count = len(all_links)
                        no_new_products_count = 0  # Yeni ürün varsa sıfırla
                        scroll_increment = 1500  # Scroll increment'i resetle
                        if scroll_position % 2000 == 0:  # Her 2000px'de bir rapor
                            print(f"    İlerleme: {len(all_links)}/{max_products} ürün toplandı (Scroll: {scroll_position}px)")
                    else:
                        # Yeni ürün yok
                        no_new_products_count += 1
                        # Minimum scroll sayısına ulaşmadan durma
                        if scroll_count < min_scrolls:
                            no_new_products_count = 0  # Minimum scroll'a kadar sayma
                        elif no_new_products_count >= 3:
                            scroll_increment = 300  # Daha hızlı scroll
                        if no_new_products_count >= 8 and scroll_count >= min_scrolls:  # Daha fazla tolerans
                            print(f"    Yeni ürün yüklenmedi. Toplam {len(all_links)} ürün bulundu.")
                            break
                else:
                    no_new_products_count += 1
                    # Minimum scroll sayısına ulaşmadan durma
                    if scroll_count < min_scrolls:
                        no_new_products_count = 0
                    elif no_new_products_count >= 8 and scroll_count >= min_scrolls:
                        break
                
                # Sayfa yüksekliğini kontrol et (sadece minimum scroll'dan sonra)
                if scroll_count >= min_scrolls:
                    page_height = self.driver.execute_script("return document.body.scrollHeight;")
                    if scroll_position >= page_height - 1500:  # Daha fazla tolerans
                        # Sayfa sonuna yaklaşıldı, biraz daha bekle
                        time.sleep(3)
                        # Yeni sayfa yüksekliğini kontrol et
                        new_page_height = self.driver.execute_script("return document.body.scrollHeight;")
                        if new_page_height == page_height and scroll_count >= min_scrolls:
                            # Sayfa yüksekliği değişmedi ve minimum scroll'a ulaşıldı
                            print(f"    Sayfa sonuna ulaşıldı. Toplam {len(all_links)} ürün bulundu.")
                            break
                        page_height = new_page_height
                
                # İlerleme raporu (her 5 scroll'da bir)
                if scroll_count % 5 == 0:
                    print(f"    İlerleme: {len(all_links)}/{max_products} ürün toplandı (Scroll: {scroll_position}px, Scroll Sayısı: {scroll_count})")
            
            product_links = list(all_links)[:max_products]
            print(f"  ✓ Toplam {len(product_links)} benzersiz ürün linki toplandı.\n")
            return product_links
                
        except Exception as e:
            print(f"  ✗ Hata: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def extract_product_links(self, category_url, max_products=1000):
        """Lazy loading ile scroll yaparak ürün linklerini toplar."""
        return self.extract_product_links_with_scroll(category_url, max_products)
    
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
            # Session kontrolü
            if not self.check_session():
                self.restart_driver()
            
            self.driver.get(product_url)
            time.sleep(3)  # Sayfa yüklenmesi için daha fazla bekleme
            self.close_all_popups()
            time.sleep(2)  # Popup kapatıldıktan sonra bekle
            
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
            
            # Yeni HTML yapısı: div.attribute-item içinde div.name ve div.value
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
            
            # Fallback: Selenium ile dene
            if not product_data['Materyal_Kumas_Tipi'] or not product_data['Kol_Boyu']:
                try:
                    attributes = self.driver.find_elements(By.CSS_SELECTOR, "div.attribute-item")
                    for attr in attributes:
                        try:
                            attr_text = attr.text.strip()
                            lines = attr_text.split('\n')
                            
                            if len(lines) >= 2:
                                key = lines[0].strip().lower()
                                value = lines[1].strip()
                            else:
                                parts = attr_text.split()
                                if len(parts) >= 2:
                                    key = parts[0].lower()
                                    value = ' '.join(parts[1:])
                                else:
                                    continue
                            
                            if 'materyal' in key and not product_data['Materyal_Kumas_Tipi']:
                                product_data['Materyal_Kumas_Tipi'] = value
                            elif ('kol tipi' in key or 'kol boyu' in key) and not product_data['Kol_Boyu']:
                                product_data['Kol_Boyu'] = value
                            elif 'yaka' in key and not product_data['Yaka_Tipi']:
                                product_data['Yaka_Tipi'] = value
                        except:
                            continue
                except:
                    pass
            
            # Eski yapı için fallback: li.detail-attr-item
            if not product_data['Materyal_Kumas_Tipi'] or not product_data['Kol_Boyu']:
                try:
                    attributes = self.driver.find_elements(By.CSS_SELECTOR, "li.detail-attr-item")
                    for attr in attributes:
                        try:
                            attr_text = attr.text.strip()
                            if ':' in attr_text:
                                key, value = attr_text.split(':', 1)
                                key = key.strip().lower()
                                value = value.strip()
                                
                                if 'materyal' in key and not product_data['Materyal_Kumas_Tipi']:
                                    product_data['Materyal_Kumas_Tipi'] = value
                                elif 'kol' in key and not product_data['Kol_Boyu']:
                                    product_data['Kol_Boyu'] = value
                                elif 'yaka' in key and not product_data['Yaka_Tipi']:
                                    product_data['Yaka_Tipi'] = value
                        except:
                            continue
                except:
                    pass
            
            # Eğer hala bulunamadıysa XPATH ile dene
            if not product_data['Materyal_Kumas_Tipi']:
                try:
                    material_elem = self.driver.find_element(By.XPATH, "//li[contains(text(), 'Materyal')]")
                    material_text = material_elem.text
                    if ':' in material_text:
                        product_data['Materyal_Kumas_Tipi'] = material_text.split(':', 1)[1].strip()
                except:
                    try:
                        material_elem = self.driver.find_element(By.XPATH, "//li[contains(text(), 'Kumaş')]")
                        material_text = material_elem.text
                        if ':' in material_text:
                            product_data['Materyal_Kumas_Tipi'] = material_text.split(':', 1)[1].strip()
                    except:
                        pass
            
            if not product_data['Kol_Boyu']:
                try:
                    sleeve_elem = self.driver.find_element(By.XPATH, "//li[contains(text(), 'Kol')]")
                    sleeve_text = sleeve_elem.text
                    if ':' in sleeve_text:
                        product_data['Kol_Boyu'] = sleeve_text.split(':', 1)[1].strip()
                except:
                    pass
            
            if not product_data['Yaka_Tipi']:
                try:
                    collar_elem = self.driver.find_element(By.XPATH, "//li[contains(text(), 'Yaka')]")
                    collar_text = collar_elem.text
                    if ':' in collar_text:
                        product_data['Yaka_Tipi'] = collar_text.split(':', 1)[1].strip()
                except:
                    pass
            
            if not product_data['Dokuma_Tipi']:
                try:
                    dokuma_elem = self.driver.find_element(By.XPATH, "//li[contains(text(), 'Dokuma')]")
                    dokuma_text = dokuma_elem.text
                    if ':' in dokuma_text:
                        product_data['Dokuma_Tipi'] = dokuma_text.split(':', 1)[1].strip()
                except:
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
    
    def scrape_category_combined(self, erkek_url, kadin_url, category_name, max_products=400):
        """
        Erkek ve Kadın kategorilerini birleşik olarak çeker.
        Her kategoriden 200'er ürün toplar (toplam 400).
        """
        print(f"\n{'='*70}")
        print(f"{category_name} kategorisi çekiliyor (Erkek + Kadın birleşik)...")
        print(f"{'='*70}\n")
        
        # Zaten kaydedilmiş ürünleri kontrol et
        existing_names, existing_links = self.get_existing_products(category_name)
        if existing_names or existing_links:
            total_existing = len(existing_names) if existing_names else len(existing_links)
            print(f"  ℹ️  Excel'de {total_existing} ürün zaten kayıtlı. Bunlar atlanacak.\n")
        
        category_products = []
        
        # Erkek kategorisi (sadece URL varsa)
        if erkek_url:
            print(f"\n--- Erkek {category_name} ---")
            print("1. Adım: Ürün linkleri toplanıyor...")
            erkek_links = self.extract_product_links(erkek_url, max_products=200)
            
            if erkek_links:
                print(f"\n2. Adım: {len(erkek_links)} erkek ürünün detayları çekiliyor...\n")
                for idx, link in enumerate(erkek_links, 1):
                    try:
                        print(f"[Erkek {idx}/{len(erkek_links)}] İşleniyor...")
                        
                        # Her 50 üründe bir session kontrolü ve Excel'e kaydet
                        if idx % 50 == 0:
                            if not self.check_session():
                                self.restart_driver()
                            # Mevcut verileri Excel'e kaydet
                            if category_products:
                                saved = self.save_category_to_excel(category_products, category_name, append=True)
                                if saved is not None:
                                    print(f"  ✓ Ara kayıt: {len(category_products)} ürün kaydedildi.\n")
                                    # Başarılı kayıt sonrası listeyi temizle (duplicate'leri önlemek için)
                                    category_products = []
                        
                        product_data = self.extract_product_details(link, "Erkek", category_name)
                        if product_data and product_data['Urun_Adi']:
                            # Zaten kaydedilmiş mi kontrol et (hem link hem ürün adı)
                            product_name_lower = product_data['Urun_Adi'].strip().lower()
                            product_link_lower = link.strip().lower()
                            if product_name_lower in existing_names or product_link_lower in existing_links:
                                print(f"  ⏭️  Atlanıyor (zaten kayıtlı): {product_data['Urun_Adi'][:50]}...")
                                continue
                            
                            category_products.append(product_data)
                            print(f"  ✓ {product_data['Urun_Adi'][:50]}...")
                        time.sleep(random.uniform(2, 4))
                        if idx % 20 == 0:
                            print(f"  İlerleme: {idx}/{len(erkek_links)} ürün işlendi. Toplam: {len(category_products)}\n")
                    except Exception as e:
                        print(f"  ✗ Hata: {str(e)}")
                        # Hata olsa bile mevcut verileri kaydet
                        if category_products:
                            self.save_category_to_excel(category_products, category_name, append=True)
                        continue
        
        # Kadın kategorisi
        print(f"\n--- Kadın {category_name} ---")
        print("1. Adım: Ürün linkleri toplanıyor...")
        kadin_links = self.extract_product_links(kadin_url, max_products=200)
        
        if kadin_links:
            print(f"\n2. Adım: {len(kadin_links)} kadın ürünün detayları çekiliyor...\n")
            for idx, link in enumerate(kadin_links, 1):
                try:
                    print(f"[Kadın {idx}/{len(kadin_links)}] İşleniyor...")
                    
                    # Her 50 üründe bir session kontrolü ve Excel'e kaydet
                    if idx % 50 == 0:
                        if not self.check_session():
                            self.restart_driver()
                        # Mevcut verileri Excel'e kaydet
                        if category_products:
                            saved = self.save_category_to_excel(category_products, category_name, append=True)
                            if saved is not None:
                                print(f"  ✓ Ara kayıt: {len(category_products)} ürün kaydedildi.\n")
                                # Başarılı kayıt sonrası listeyi temizle (duplicate'leri önlemek için)
                                category_products = []
                    
                    product_data = self.extract_product_details(link, "Kadın", category_name)
                    if product_data and product_data['Urun_Adi']:
                        # Zaten kaydedilmiş mi kontrol et (hem link hem ürün adı)
                        product_name_lower = product_data['Urun_Adi'].strip().lower()
                        product_link_lower = link.strip().lower()
                        if product_name_lower in existing_names or product_link_lower in existing_links:
                            print(f"  ⏭️  Atlanıyor (zaten kayıtlı): {product_data['Urun_Adi'][:50]}...")
                            continue
                        
                        category_products.append(product_data)
                        print(f"  ✓ {product_data['Urun_Adi'][:50]}...")
                    time.sleep(random.uniform(2, 4))
                    if idx % 20 == 0:
                        print(f"  İlerleme: {idx}/{len(kadin_links)} ürün işlendi. Toplam: {len(category_products)}\n")
                except Exception as e:
                    print(f"  ✗ Hata: {str(e)}")
                    # Hata olsa bile mevcut verileri kaydet
                    if category_products:
                        self.save_category_to_excel(category_products, category_name, append=True)
                    continue
        
        # Kategoriyi son kez kaydet (kalan veriler için)
        if category_products:
            self.save_category_to_excel(category_products, category_name, append=True)
            print(f"\n{'='*70}")
            print(f"✓ {category_name} kategorisi tamamlandı. Toplam {len(category_products)} ürün kaydedildi.")
            print(f"{'='*70}\n")
        
        return category_products
    
    def get_existing_products(self, category_name):
        """Excel dosyasından zaten kaydedilmiş ürün adlarını ve linklerini döndürür."""
        filename = f"{category_name.lower().replace(' ', '_').replace('-', '_')}.xlsx"
        existing_names = set()
        existing_links = set()
        try:
            df = pd.read_excel(filename, engine='openpyxl')
            if 'Urun_Adi' in df.columns:
                existing_names = set(df['Urun_Adi'].str.strip().str.lower())
            if 'Urun_Linki' in df.columns:
                existing_links = set(df['Urun_Linki'].str.strip().str.lower())
            return existing_names, existing_links
        except FileNotFoundError:
            return set(), set()
    
    def save_category_to_excel(self, products_list, category_name, append=False):
        """Bir kategorinin verilerini ayrı Excel dosyasına kaydeder. Append=True ise mevcut dosyaya ekler."""
        if not products_list:
            return None
        
        # Dosya adı: tisort.xlsx, kazak.xlsx gibi
        filename = f"{category_name.lower().replace(' ', '_').replace('-', '_')}.xlsx"
        
        # Sütun sıralaması
        columns_order = [
            'Urun_Adi', 'Urun_Linki', 'Materyal_Kumas_Tipi', 'Dokuma_Tipi', 
            'Kol_Boyu', 'Yaka_Tipi', 'Cinsiyet', 'Kategori',
            'Renk', 'Desen', 'Kalıp', 'Cep', 'Boy', 'Ortam', 'Beden', 'Stil', 'Sezon',
            'Paca_Tipi', 'Bel', 'Koleksiyon', 'Astar_Durumu', 'Siluet', 'Dokuma_Tipi_Detay',
            'Kemer_Kusak_Durumu', 'Surdurulebilirlik_Detayi', 'Mensei', 'Kutu_Durumu',
            'Kapama_Sekli', 'Paket_Icerigi', 'Persona', 'Baski_Nakis_Teknigi', 'Parca_Sayisi',
            'Urun_Tipi', 'Kalinlik', 'Ek_Ozellikler'
        ]
        
        # Yeni verileri DataFrame'e çevir
        df_new = pd.DataFrame(products_list)
        df_new = df_new[columns_order]
        
        try:
            if append:
                # Mevcut dosyayı oku (varsa)
                try:
                    df_existing = pd.read_excel(filename, engine='openpyxl')
                    # Mevcut verilerle yeni verileri birleştir
                    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                    # Duplicate'leri kaldır (hem Ürün_Adı hem Ürün_Linki'ne göre)
                    duplicate_subset = []
                    if 'Urun_Linki' in df_combined.columns:
                        duplicate_subset.append('Urun_Linki')
                    if 'Urun_Adi' in df_combined.columns:
                        duplicate_subset.append('Urun_Adi')
                    if duplicate_subset:
                        df_combined = df_combined.drop_duplicates(subset=duplicate_subset, keep='last')
                    df_combined = df_combined[columns_order]
                    df_combined.to_excel(filename, index=False, engine='openpyxl')
                    print(f"  💾 {len(df_new)} yeni satır eklendi. Toplam: {len(df_combined)} satır '{filename}' dosyasına kaydedildi.")
                except FileNotFoundError:
                    # Dosya yoksa yeni oluştur
                    df_new.to_excel(filename, index=False, engine='openpyxl')
                    print(f"  💾 {len(df_new)} satır '{filename}' dosyasına kaydedildi.")
            else:
                # Normal kaydetme (append=False)
                df_new.to_excel(filename, index=False, engine='openpyxl')
                print(f"\n{'='*70}")
                print(f"✓ {category_name}: {len(df_new)} satır '{filename}' dosyasına kaydedildi.")
                print(f"{'='*70}\n")
        except PermissionError:
            print(f"  ⚠️  UYARI: '{filename}' dosyası açık! Lütfen Excel'de dosyayı kapatın.")
            print(f"  ⚠️  {len(df_new)} ürün kaydedilemedi. Dosyayı kapattıktan sonra script devam edecek.")
            print(f"  ⚠️  Bir sonraki kayıt denemesinde tekrar denenecek.\n")
            return None
        except Exception as e:
            print(f"  ✗ Excel kayıt hatası: {str(e)}")
            return None
        
        return df_new
    
    def save_to_excel(self, filename='trendyol_orijinal_veri.xlsx'):
        """Tüm verileri birleşik Excel dosyasına kaydeder."""
        if not self.products:
            print("Kaydedilecek veri yok!")
            return
        
        df = pd.DataFrame(self.products)
        
        columns_order = [
            'Urun_Adi', 'Urun_Linki', 'Materyal_Kumas_Tipi', 'Dokuma_Tipi', 
            'Kol_Boyu', 'Yaka_Tipi', 'Cinsiyet', 'Kategori',
            'Renk', 'Desen', 'Kalıp', 'Cep', 'Boy', 'Ortam', 'Beden', 'Stil', 'Sezon',
            'Paca_Tipi', 'Bel', 'Koleksiyon', 'Astar_Durumu', 'Siluet', 'Dokuma_Tipi_Detay',
            'Kemer_Kusak_Durumu', 'Surdurulebilirlik_Detayi', 'Mensei', 'Kutu_Durumu',
            'Kapama_Sekli', 'Paket_Icerigi', 'Persona', 'Baski_Nakis_Teknigi', 'Parca_Sayisi',
            'Urun_Tipi', 'Kalinlik', 'Ek_Ozellikler'
        ]
        # Sadece mevcut sütunları seç
        available_columns = [col for col in columns_order if col in df.columns]
        df = df[available_columns]
        
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"\n{'='*70}")
        print(f"✓ Tüm veriler '{filename}' dosyasına kaydedildi.")
        print(f"✓ Toplam {len(df)} satır veri toplandı.")
        print(f"{'='*70}\n")
        
        return df

def main():
    """Ana fonksiyon"""
    scraper = None
    try:
        scraper = TrendyolScraper(headless=False)
        
        # Kategori URL'leri (Erkek ve Kadın birleşik)
        categories = {
            'T-shirt': {
                # 'erkek': 'https://www.trendyol.com/erkek-tisort-x-g2-c73',  # Erkek T-shirt atlandı
                'erkek': '',  # Erkek T-shirt atlandı
                'kadin': 'https://www.trendyol.com/kadin-tisort-x-g1-c73'
            },
            'Kazak': {
                # 'erkek': 'https://www.trendyol.com/erkek-kazak-x-g2-c1092',  # Erkek Kazak atlandı (200 ürün zaten çekildi)
                'erkek': '',  # Erkek Kazak atlandı
                'kadin': 'https://www.trendyol.com/kadin-kazak-x-g1-c1092'
            },
            'Gömlek': {
                'erkek': 'https://www.trendyol.com/erkek-gomlek-x-g2-c75',
                'kadin': 'https://www.trendyol.com/kadin-gomlek-x-g1-c75'
            },
            'Ceket': {
                'erkek': 'https://www.trendyol.com/erkek-ceket-x-g2-c1030',
                'kadin': 'https://www.trendyol.com/kadin-ceket-x-g1-c1030'
            },
            'Hırka': {
                'erkek': 'https://www.trendyol.com/erkek-hirka-x-g2-c1066',
                'kadin': 'https://www.trendyol.com/kadin-hirka-x-g1-c1066'
            },
            'Pantolon': {
                'erkek': 'https://www.trendyol.com/erkek-pantolon-x-g2-c70',
                'kadin': 'https://www.trendyol.com/kadin-pantolon-x-g1-c70'
            },
            'Eşofman': {
                'erkek': 'https://www.trendyol.com/erkek-esofman-x-g2-c101451',
                'kadin': 'https://www.trendyol.com/kadin-esofman-alti-x-g1-c101451'
            }
        }
        
        # Her kategoriyi tara (her biri için 1000 ürün: 500 erkek + 500 kadın)
        for cat_name, urls in categories.items():
            erkek_url = urls.get('erkek', '')
            kadin_url = urls.get('kadin', '')
            
            if erkek_url and kadin_url:
                category_products = scraper.scrape_category_combined(
                    erkek_url, kadin_url, cat_name, max_products=400
                )
                scraper.products.extend(category_products)
                
                # Kategori arasında kısa bekleme
                time.sleep(2)
        
        # Excel'e kaydet
        scraper.save_to_excel('trendyol_orijinal_veri.xlsx')
        
        print("\n✓ Scraping işlemi tamamlandı!")
        
    except KeyboardInterrupt:
        print("\n\n⚠ İşlem kullanıcı tarafından durduruldu.")
        if scraper:
            scraper.save_to_excel('trendyol_orijinal_veri.xlsx')
            print("Mevcut veriler kaydedildi.")
    except Exception as e:
        print(f"\n✗ Hata oluştu: {str(e)}")
        import traceback
        traceback.print_exc()
        if scraper:
            scraper.save_to_excel('trendyol_orijinal_veri.xlsx')
            print("Mevcut veriler kaydedildi.")
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()
