import json

with open('alpaca_history.json', 'r') as f:
    d = json.load(f)

print(f'Data points: {len(d)}')
print(f'First entry: {d[0]}')
print(f'Last entry: {d[-1]}')

equities = [h['equity'] for h in d]
print(f'Min equity: ${min(equities):,.2f}')
print(f'Max equity: ${max(equities):,.2f}')
print(f'Values are different: {equities[-1] != equities[0]}')
print(f'Real portfolio data: {len(set(equities)) > 1}')