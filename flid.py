import sys
import imaplib
import email
from email.header import decode_header
import os
import pandas as pd
import warnings
import re

# Игнорируем предупреждения от Excel-файлов с нестандартным форматированием
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def get_flid_price():
    EMAIL = "monnombistro@gmail.com"
    APP_PASSWORD = "rvjtrusishqrmulk" 
    IMAP_SERVER = "imap.gmail.com"

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, APP_PASSWORD)
        mail.select("inbox")
    except Exception as e:
        return

    # Ищем письма от Виктории
    status, messages = mail.search(None, '(FROM "vh@flid-delivery.pl")')
    
    if status != "OK" or not messages[0]:
        return

    email_ids = messages[0].split()
    latest_email_id = email_ids[-1] 

    status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
    
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            if msg.is_multipart():
                for part in msg.walk():
                    content_disposition = str(part.get("Content-Disposition"))
                    if "attachment" in content_disposition:
                        filename = part.get_filename()
                        if filename:
                            decoded_filename, encoding = decode_header(filename)[0]
                            if isinstance(decoded_filename, bytes):
                                decoded_filename = decoded_filename.decode(encoding if encoding else "utf-8")
                            
                            if decoded_filename.endswith(('.xlsx', '.xls')):
                                filepath = os.path.join(os.getcwd(), "flid_price.xlsx")
                                with open(filepath, "wb") as f:
                                    f.write(part.get_payload(decode=True))
                                
                                process_excel(filepath)
                                return 

def process_excel(filepath):
    SEARCH_TERM = sys.argv[1] if len(sys.argv) > 1 else "Favita"

    try:
        xls = pd.ExcelFile(filepath)
        results = []
        
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
            mask = df.astype(str).apply(lambda x: x.str.contains(SEARCH_TERM, case=False, na=False))
            rows_with_item = df[mask.any(axis=1)]
            
            if not rows_with_item.empty:
                for index, row in rows_with_item.iterrows():
                    values = [str(val).strip() for val in row.values if pd.notna(val) and str(val).strip() != '']
                    if not values:
                        continue
                        
                    name = " | ".join(values[:2]) # Берем первые колонки как название
                    price = 0.0
                    
                    # Ищем цену с конца (обычно она в последних колонках)
                    for v in reversed(values):
                        clean_v = v.replace('zł', '').replace('PLN', '').strip().replace(',', '.')
                        try:
                            # Игнорируем штрихкоды и артикулы (слишком большие числа)
                            if '.' in clean_v or clean_v.isdigit():
                                f = float(clean_v)
                                if 0 < f < 5000:
                                    price = f
                                    break
                        except:
                            pass
                    
                    if price > 0:
                        results.append({
                            "name": name,
                            "price": price
                        })
        
        if results:
            for i, item in enumerate(results, 1):
                print(f"{i}. {item['name'][:60]}")
                print(f"   💰 Цена: {item['price']} zł")
            
    except Exception as e:
        pass

if __name__ == "__main__":
    get_flid_price()