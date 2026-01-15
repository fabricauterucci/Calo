#!/usr/bin/env python3
"""
Script de prueba para ver qué HTML recibe Selenium de Rentola
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.binary_location = '/usr/bin/chromium'

driver = webdriver.Chrome(options=chrome_options)

try:
    print("📍 Navegando a Rentola...")
    driver.get('https://rentola.ar/alquiler/rosario')
    
    print("⏳ Esperando 10 segundos...")
    time.sleep(10)
    
    print("📜 Scroll...")
    for i in range(3):
        driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/3});")
        time.sleep(2)
    
    print("\n📄 URL actual:", driver.current_url)
    print("📄 Título:", driver.title)
    
    # Buscar links
    links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/alquiler/"]')
    print(f"\n✅ Links con /alquiler/: {len(links)}")
    
    for i, link in enumerate(links[:10]):
        href = link.get_attribute('href')
        text = link.text.strip()[:50]
        print(f"  {i+1}. {href} - {text}")
    
    # Guardar HTML
    with open('/tmp/rentola_selenium.html', 'w') as f:
        f.write(driver.page_source)
    print("\n💾 HTML guardado en /tmp/rentola_selenium.html")
    
finally:
    driver.quit()
