from datasets import load_dataset

print("Loading edgar-corpus (streaming)...")
ds = load_dataset('eloukas/edgar-corpus', split='train', streaming=True)

count = 0
for item in ds:
    ticker = item.get('ticker', '?')
    text = str(item.get('text', ''))[:100]
    if ticker and len(text) > 20:
        print(f"{ticker}: {text}...")
        count += 1
    if count >= 15:
        break

print(f"Working! Found {count} items")