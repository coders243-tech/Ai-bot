"""
Data Fetcher - Fallback when Pocket Option is disconnected
"""

import requests

class DataFetcher:
    def __init__(self):
        self.cache = {}
    
    def get_price_eurusd(self):
        """Fallback price from free API"""
        try:
            url = "https://api.frankfurter.app/latest?from=EUR&to=USD"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data['rates']['USD']
        except:
            pass
        return 1.09234
    
    def get_price_gold(self):
        """Fallback gold price"""
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                result = data.get('chart', {}).get('result', [])
                if result:
                    return result[0].get('meta', {}).get('regularMarketPrice')
        except:
            pass
        return 2350.00
