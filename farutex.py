import sys
from playwright.sync_api import sync_playwright
import os
import re

def parse_price(price_str):
    try:
        clean = price_str.replace("zł", "").replace(" ", "").replace(",", ".")
        return float(re.findall(r"\d+\.\d+|\d+", clean)[0])
    except:
        return 0.0

def get_farutex_price():
    with sync_playwright() as p:
        user_data_dir = "./farutex_profile"
        
        browser = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True,
            channel="chrome", 
            args=["--disable-blink-features=AutomationControlled", "--disable-features=Translate"],
            viewport={"width": 1920, "height": 1080} 
        )
        
        page = browser.pages[0]
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("🤖 Робот: Открываю сайт e-Bidfood...")
        page.goto("https://e-bidfood.pl/", wait_until="domcontentloaded")
        page.wait_for_timeout(4000)

        try:
            login_btn = page.get_by_role("button", name="Zaloguj").first
            if login_btn.is_visible(timeout=3000):
                login_btn.click()
                page.wait_for_load_state("networkidle")
                
                inputs = page.locator("input").all()
                if len(inputs) >= 2:
                    inputs[0].fill("monnombistro@gmail.com")
                    page.locator("input[type='password']").first.fill("Monnom2023")
                    page.get_by_role("button", name="Zaloguj się").click()
                    page.wait_for_timeout(8000)
        except:
            pass

        try:
            if "login" in page.url:
                page.goto("https://e-bidfood.pl/", wait_until="domcontentloaded")
                page.wait_for_timeout(3000)

            page.wait_for_selector("input[type='text'], input[type='search'], input[placeholder*='Szukaj']", timeout=10000)
            search_input = page.locator("input[type='text'], input[type='search'], input[placeholder*='Szukaj']").first
            search_input.click(force=True)
            page.wait_for_timeout(1000)
           
            SEARCH_TERM = sys.argv[1] if len(sys.argv) > 1 else "Favita"
            search_input.fill(SEARCH_TERM)
            page.keyboard.press("Enter")
            page.wait_for_timeout(6000)
        except Exception as e:
            pass
        
        page_text = page.evaluate("() => document.body.innerText")
        results = []
        chunks = re.split(SEARCH_TERM, page_text, flags=re.IGNORECASE)
        
        for chunk in chunks[1:]:
            if "zł" in chunk:
                lines = [line.strip() for line in chunk.split('\n') if line.strip()]
                name = SEARCH_TERM.upper() + " " + lines[0] if lines else SEARCH_TERM.upper()
                
                price_val = 0.0
                unit_price = 0.0
                
                for line in lines:
                    if "zł" in line:
                        val = parse_price(line)
                        if val > 0:
                            if "kg" in line.lower() or "l" in line.lower():
                                unit_price = val
                            else:
                                price_val = val

                if price_val > 0 or unit_price > 0:
                    if price_val == 0: price_val = unit_price
                    if unit_price == 0: unit_price = price_val
                    
                    if not any(r['pack_price'] == price_val for r in results):
                        results.append({
                            "name": name[:70],
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
    get_farutex_price()