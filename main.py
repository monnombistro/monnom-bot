import subprocess
import re
import os
import sys

SUPPLIERS = {
    "Makro": "makro.py",
    "Farutex": "farutex.py",
    "Selgros": "selgros.py",
    "Flid": "flid.py",
    "Goldfish": "goldfish.py"
}

def search_basket(items_to_search):
    if not items_to_search:
        return "⚠️ Список товаров пуст."
    
    custom_env = os.environ.copy()
    custom_env["PYTHONIOENCODING"] = "utf-8"

    report_lines = ["📦 **АНАЛИЗ ЗАКУПОК MONNOM BISTRO**\n"]
    all_item_results = {}

    for item in items_to_search:
        print(f"\n🔎 === ИЩЕМ ТОВАР: {item.upper()} ===")
        supplier_results = {}
        
        for name, script in SUPPLIERS.items():
            try:
                result = subprocess.run(
                    [sys.executable, script, item], 
                    capture_output=True, 
                    text=True, 
                    encoding="utf-8", 
                    errors="replace",
                    env=custom_env
                )
                
                output = result.stdout + "\n" + result.stderr
                output = result.stdout + "\n" + result.stderr
                print(f"--- ЛОГИ ОТ {name} ---")
                print(output)
                
                valid_items = []
                current_name = None
                current_unit_price = None
                current_pack_price = None
                bad_markers = ["🤖", "⏳", "⚠️", "🛒", "===", "АНАЛИЗ", "ВАРИАНТЫ", "ЦЕНЫ", "ИТОГ", "САМЫЙ ВЫГОДНЫЙ"]
                
                for line in output.split('\n'):
                    line_str = line.strip()
                    
                    if not line_str or any(marker in line_str for marker in bad_markers):
                        continue
                        
                    if '⚖️ Цена' in line_str or '💰 Цена' in line_str:
                        match = re.search(r'([\d\.,]+)\s*zł', line_str)
                        if match:
                            val = float(match.group(1).replace(',', '.'))
                            if '⚖️' in line_str:
                                current_unit_price = val
                            else:
                                current_pack_price = val
                        
                        # Сохраняем товар, когда найдена цена за упаковку (она выводится последней)
                        if '💰' in line_str and current_pack_price is not None and current_name:
                            # Если парсер не нашел цену за кг, используем цену упаковки для сравнения
                            u_price = current_unit_price if current_unit_price else current_pack_price
                            
                            name_lower = current_name.lower()
                            if not re.search(r'(mini|10\s*g|15\s*g|20\s*g|portion|порцион)', name_lower):
                                valid_items.append({
                                    "name": current_name, 
                                    "unit_price": u_price,
                                    "pack_price": current_pack_price
                                })
                            current_name = None
                            current_unit_price = None
                            current_pack_price = None
                        
                    elif len(line_str) > 4 and not "zł" in line_str and not "Упаковка" in line_str:
                        clean_line = re.sub(r'^\d+\.\s*', '', line_str)
                        current_name = clean_line
                
                if valid_items:
                    # СОРТИРУЕМ И ВЫБИРАЕМ ПОБЕДИТЕЛЯ ПО ЦЕНЕ ЗА КГ/ЛИТР
                    best_item = min(valid_items, key=lambda x: x["unit_price"])
                    
                    final_name = best_item["name"]
                    if len(final_name) > 55:
                        final_name = final_name[:52] + "..."
                        
                    supplier_results[name] = {
                        "status": "found",
                        "unit_price": best_item["unit_price"],
                        "pack_price": best_item["pack_price"],
                        "name": final_name
                    }
                else:
                    supplier_results[name] = {
                        "status": "not_found"
                    }
            except Exception as e:
                supplier_results[name] = {
                    "status": "error"
                }

        all_item_results[item] = supplier_results
        report_lines.append(f"🔹 **{item.upper()}**")
        
        found_suppliers = sorted(
            [s for s, data in supplier_results.items() if data["status"] == "found"],
            key=lambda x: supplier_results[x]["unit_price"]
        )
        
        for i, s_name in enumerate(found_suppliers, 1):
            data = supplier_results[s_name]
            badge = "🥇 БЕРЕМ" if i == 1 else ("🥈 РЕЗЕРВ" if i == 2 else "")
            # Красивый вывод двух цен
            if data['unit_price'] != data['pack_price']:
                report_lines.append(f"   {i}. `{s_name.ljust(8)}` — **{data['unit_price']:.2f} zł/кг** _(упак. {data['pack_price']:.2f} zł)_ {badge}")
            else:
                report_lines.append(f"   {i}. `{s_name.ljust(8)}` — **{data['pack_price']:.2f} zł** {badge}")
            report_lines.append(f"      └ _{data['name']}_")
            
        not_found_suppliers = [s for s, data in supplier_results.items() if data["status"] != "found"]
        for s_name in not_found_suppliers:
            report_lines.append(f"   • `{s_name.ljust(8)}` — ❌ _нет в наличии_")
            
        report_lines.append("")

    basket_totals = {}
    for name in SUPPLIERS.keys():
        can_buy_all = True
        total_price = 0.0
        for item in items_to_search:
            res = all_item_results[item].get(name, {})
            if res.get("status") == "found":
                # В ИТОГОВУЮ КОРЗИНУ ИДЕТ ЦЕНА УПАКОВКИ
                total_price += res["pack_price"]
            else:
                can_buy_all = False
                break
        if can_buy_all:
            basket_totals[name] = total_price

    if basket_totals:
        report_lines.append("🏆 **ИТОГ ПО ВСЕЙ КОРЗИНЕ (суммируем упаковки):**")
        sorted_basket = sorted(basket_totals.items(), key=lambda x: x[1])
        for i, (s_name, t_price) in enumerate(sorted_basket, 1):
            crown = "👑 АБСОЛЮТНЫЙ ПОБЕДИТЕЛЬ" if i == 1 else ""
            report_lines.append(f"   {i}. `{s_name.ljust(8)}` — **{t_price:.2f} zł** {crown}")
        report_lines.append("")
    else:
        report_lines.append("⚠️ *Ни у одного поставщика нет в наличии полного набора товаров из корзины.*\n")

    report_lines.append("✅ *Срез рынка по поставщикам готов*")
    return "\n".join(report_lines)