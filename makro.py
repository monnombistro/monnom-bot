import sys
import re

def parse_price(price_str):
    try:
        clean = price_str.replace("zł", "").replace(" ", "").replace(",", ".")
        return float(re.findall(r"\d+\.\d+|\d+", clean)[0])
    except:
        return 0.0

def get_makro_price():
    with sync_playwright() as p:
        user_data_dir = "./makro_profile"
        
        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=["--start-maximized", "--disable-blink-features=AutomationControlled", "--no-sandbox"],
            viewport={"width": 1920, "height": 1080}
        )
        
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print("🤖 Робот: Открываю сайт Makro...")
        page.goto("https://www.makro.pl/", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        try:
            accept_btn = page.locator("button:has-text('Zaakceptuj'), button:has-text('Akceptuj')").first
            if accept_btn.is_visible(timeout=3000):
                accept_btn.click()
        except:
            pass

        try:
            zaloguj_btn = page.locator("a:has-text('Zaloguj'), button:has-text('Zaloguj')").first
            if zaloguj_btn.is_visible(timeout=2000):
                zaloguj_btn.click()
                page.wait_for_timeout(2000)
                page.locator("input[type='email'], input[name='username'], #email").first.click()
                page.keyboard.type("nikitich.242@gmail.com", delay=100)
                page.wait_for_timeout(500)
                page.locator("input[type='password'], input[name='password'], #password").first.click()
                page.keyboard.type("Makro2023", delay=120)
                page.wait_for_timeout(500)
                page.locator("button[type='submit'], button:has-text('Zaloguj')").first.click()
                page.wait_for_timeout(6000)
        except:
            pass

        try:
            gastronomii_link = page.get_by_text("Dla Gastronomii", exact=False).first
            gastronomii_link.click(force=True)
            page.wait_for_timeout(4000)
        except:
            pass

        SEARCH_TERM = sys.argv[1] if len(sys.argv) > 1 else "Favita"
        
        try:
            search_input = page.locator("input[placeholder*='Wyszukaj'], input[type='text']").first
            search_input.click(force=True)
        except:
            page.wait_for_timeout(2000)
            search_input = page.locator("input[placeholder*='Wyszukaj'], input[type='text']").first
            search_input.click(force=True)

        page.wait_for_timeout(500)
        page.keyboard.type(SEARCH_TERM, delay=150)
        page.keyboard.press("Enter")
        page.wait_for_timeout(6000)

        results = []
        page_text = page.evaluate("() => document.body.innerText")
        chunks = re.split(SEARCH_TERM, page_text, flags=re.IGNORECASE)
        
        for chunk in chunks[1:]:
            if "zł" in chunk:
                lines = [line.strip() for line in chunk.split('\n') if line.strip()]
                name = SEARCH_TERM.upper() + " " + lines[0] if lines else SEARCH_TERM.upper()
                
                unit_price = 0.0
                pack_price = 0.0
                
                for line in lines:
                    if "zł" in line:
                        val = parse_price(line)
                        # Если видим упоминание kg или l рядом с ценой
                        if "kg" in line.lower() or "l" in line.lower() and not "ml" in line.lower():
                            unit_price = val
                        elif val > 0:
                            # Последняя найденная цена обычно цена упаковки (брутто/нетто)
                            pack_price = val

                if pack_price > 0:
                    results.append({
                        "name": name[:60],
                        "unit_price": unit_price if unit_price > 0 else pack_price,
                        "pack_price": pack_price
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
    get_makro_price()