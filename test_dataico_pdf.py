import requests

cufe = "8128cff5f4fb5c4a18a6ce2dcf1e3703b741a0a9ef9ad5b32e70911bc313ac4363fb8db95450467047bbdab0e923bf88"
account_id = "002979c5-7c23-43ab-aa98-3fa7dce6e4d0"
auth_token = "a4afb1e20e856e8fb031b487efbfd239"

url = f"https://api.dataico.com/direct/dataico_api/v2/invoices/{cufe}/pdf"

headers = {
    "Dataico-Account-Id": account_id,
    "Auth-token": auth_token
}

print(f"Buscando con AUTH...")
res = requests.get(url, headers=headers)
print(res.status_code)
if res.status_code == 200:
    print(f"Recibidos {len(res.content)} bytes de PDF (Con Auth)")

print(f"Buscando SIN AUTH...")
res_pub = requests.get(url)
print(res_pub.status_code)
if res_pub.status_code == 200:
    print(f"Recibidos {len(res_pub.content)} bytes de PDF (Sin Auth)")
