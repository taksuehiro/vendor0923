import json

# ファイルを読み込み
with open('vendors.json', 'r', encoding='utf-8') as f:
    vendors = json.load(f)

# 重複を除去するための辞書
unique_vendors = {}
seen_names = set()

for vendor in vendors:
    name = vendor['name']
    
    # 既に見た名前の場合は、より情報が充実している方を残す
    if name in seen_names:
        existing = unique_vendors[name]
        # より多くの情報がある方を選択（capabilitiesの長さで判断）
        if len(vendor.get('capabilities', [])) > len(existing.get('capabilities', [])):
            unique_vendors[name] = vendor
        elif len(vendor.get('capabilities', [])) == len(existing.get('capabilities', [])):
            # 同じ情報量の場合は、より詳細なdescription_shortがある方を選択
            if len(vendor.get('offerings', {}).get('description_short', '')) > len(existing.get('offerings', {}).get('description_short', '')):
                unique_vendors[name] = vendor
    else:
        unique_vendors[name] = vendor
        seen_names.add(name)

# 重複除去後のリストを作成
cleaned_vendors = list(unique_vendors.values())

print(f'元の件数: {len(vendors)}')
print(f'重複除去後: {len(cleaned_vendors)}')
print(f'削除された重複: {len(vendors) - len(cleaned_vendors)}件')

# 重複除去後のデータを保存
with open('vendors_cleaned.json', 'w', encoding='utf-8') as f:
    json.dump(cleaned_vendors, f, ensure_ascii=False, indent=2)

print('重複除去完了: vendors_cleaned.json に保存')
