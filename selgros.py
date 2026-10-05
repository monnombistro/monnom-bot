import sys
from playwright.sync_api import sync_playwright
import re

def get_selgros_price():
    with sync_playwright() as p:
        user_data_dir = "./selgros_profile"
        
        browser = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True, 
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=Translate"
            ],
            viewport={"width": 1920, "height": 1080} 
        )
        
        page = browser.pages[0]
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("🤖 Робот: Открываю сайт Selgros...")
        page.goto("https://www.selgros.pl/", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        try:
            accept_cookies = page.get_by_role("button", name="AKCEPTUJĘ").first
            if accept_cookies.is_visible(timeout=2000):
                accept_cookies.click()
                page.wait_for_timeout(1000)
        except:
            pass

        try:
            login_btn = page.get_by_role("button", name="ZALOGUJ SIĘ").first
            if not login_btn.is_visible(timeout=2000):
                login_btn = page.locator("a[href*='login'], button:has-text('Zaloguj')").first
                 
            if login_btn.is_visible(timeout=2000):
                print("🤖 Робот: Выполняю авторизацию на Selgros...")
                login_btn.click()
                page.wait_for_timeout(2000)
                
                page.locator("input[type='text'], input[name='login'], input[name='username'], input[id*='login']").first.fill("309633295")
                page.locator("input[type='password']").first.fill("Monnom2023")
                page.locator("button[type='submit'], button:has-text('Zaloguj')").first.click()
                page.wait_for_timeout(5000)
        except Exception:
            pass

        SEARCH_TERM = sys.argv[1] if len(sys.argv) > 1 else "Favita"
        print(f"🤖 Робот: Перехожу по прямой ссылке поиска '{SEARCH_TERM}'...")
        page.goto(f"https://www.selgros.pl/search?text={SEARCH_TERM}", wait_until="domcontentloaded")       
        
        try:
            page.wait_for_selector("text='Nr produktu:'", timeout=8000)
        except:
            pass

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(3000)

        results = []
        page_text = page.evaluate("() => document.body.innerText")
        chunks = re.split(r'Nr produktu:', page_text, flags=re.IGNORECASE)
        
        for chunk in chunks[1:]:
            lines = [line.strip() for line in chunk.split('\n') if line.strip()]
            name = ""
            price_val = 0.0
            
            for i, line in enumerate(lines):
                if SEARCH_TERM.upper() in line.upper() and not name:
                    name = line
                    
                if "Z VAT" in line.upper():
                    candidates = []
                    for offset in range(1, 5):
                        if i - offset >= 0:
                            found = re.findall(r'(\d+[.,]\d{2})', lines[i-offset])
                            candidates.extend([float(x.replace(',', '.')) for x in found])
                    if candidates:
                        price_val = min(candidates)
                    break
            
            if price_val == 0.0 and name:
                all_numbers = re.findall(r'(\d+[.,]\d{2})', chunk)
                if all_numbers:
                    price_val = min([float(x.replace(',', '.')) for x in all_numbers])

            if name and price_val > 0:
                if 2 < price_val < 500:
                    clean_name = name[:70]
                    
                    # Пытаемся найти цену за кг (часто в Selgros она пишется с приставкой /kg или /l)
                    unit_price = price_val
                    kg_match = re.search(r'(\d+[.,]\d{2})\s*zł\s*/\s*(kg|l|szt)', chunk, re.IGNORECASE)
                    if kg_match:
                        unit_price = float(kg_match.group(1).replace(',', '.'))
                        
                    if not any(r['name'] == clean_name for r in results):
                        results.append({
                            "name": clean_name,
                            "unit_price": unit_price,
                            "pack_price": price_val
                        })

        sorted_results = sorted(results, key=lambda x: x['unit_price'])

        if sorted_results:
            for i, item in enumerate(sorted_results, 1):
                print(f"{i}. {item['name']}")
                if item['unit_price'] != item['pack_price']:
                    print(f"   ⚖️ Цена за кг/л: {item['unit_price']} zł")
                print(f"   💰 Цена: {item['pack_price']} zł")
        
        browser.close()

if __name__ == "__main__":
    get_selgros_price()