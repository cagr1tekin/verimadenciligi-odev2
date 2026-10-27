"""
Trendyol sayfasının HTML yapısını incelemek için debug scripti
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# Chrome ayarları
chrome_options = Options()
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

driver = webdriver.Chrome(options=chrome_options)
driver.maximize_window()

# Bot tespitini engelle
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': '''
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    '''
})

try:
    url = "https://www.trendyol.com/erkek-ust-giyim-x-g2-c73"
    print(f"Sayfa yükleniyor: {url}")
    driver.get(url)
    
    # Bekle
    time.sleep(5)
    
    # Cookie popup'ını kapat
    try:
        cookie_buttons = driver.find_elements("css selector", "button")
        for btn in cookie_buttons:
            if 'cookie' in btn.get_attribute('id') or 'cookie' in btn.get_attribute('class') or 'accept' in btn.text.lower():
                btn.click()
                print("Cookie popup kapatıldı")
                time.sleep(1)
                break
    except:
        pass
    
    # Scroll yap
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    
    # Tüm linkleri bul
    print("\n=== TÜM LINKLER ===")
    all_links = driver.find_elements("css selector", "a")
    print(f"Toplam {len(all_links)} link bulundu")
    
    product_links = []
    for link in all_links:
        href = link.get_attribute('href')
        if href and ('/p-' in href or '/brand/' in href):
            product_links.append(href)
            print(f"  - {href}")
    
    print(f"\n=== ÜRÜN LİNKLERİ ({len(product_links)} adet) ===")
    for i, link in enumerate(product_links[:10], 1):  # İlk 10'unu göster
        print(f"{i}. {link}")
    
    # Sayfa kaynağını kontrol et
    print("\n=== SAYFA KAYNAĞI KONTROLÜ ===")
    page_source = driver.page_source
    if '/p-' in page_source:
        print("✓ Sayfa kaynağında '/p-' bulundu")
        # İlk birkaç örneği göster
        import re
        matches = re.findall(r'href=["\']([^"\']*\/p-[^"\']*)["\']', page_source)
        print(f"  Regex ile {len(matches)} link bulundu")
        for i, match in enumerate(matches[:5], 1):
            print(f"  {i}. {match}")
    else:
        print("✗ Sayfa kaynağında '/p-' bulunamadı")
    
    # Div yapısını kontrol et
    print("\n=== DIV YAPISI ===")
    divs = driver.find_elements("css selector", "div[class*='card'], div[class*='product'], div[data-testid]")
    print(f"Toplam {len(divs)} ilgili div bulundu")
    for i, div in enumerate(divs[:5], 1):
        print(f"{i}. Class: {div.get_attribute('class')}, Data-testid: {div.get_attribute('data-testid')}")
    
    # 10 saniye bekle (görsel kontrol için)
    print("\n10 saniye bekleniyor (tarayıcıyı kontrol edebilirsiniz)...")
    time.sleep(10)
    
except Exception as e:
    print(f"Hata: {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()

