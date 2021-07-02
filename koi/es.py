import datetime as dt
from elasticsearch import Elasticsearch
from typing import Dict, List, Tuple, Optional
from koi.models import Sentiment

NEWS_INDEX = 'news'

# helpers
def _initialize() -> Elasticsearch:
    es = Elasticsearch()
    return es

def all_listings(symbol: str, currency: Optional[str] = None) -> List[str]:
  crypto_pairs = {
    'BTC': ['BTC', 'BTCUSD', 'BTC-USD', '$BTC'], 'BTCUSD': ['BTC', 'BTCUSD', 'BTC-USD', '$BTC'],
    'ETH': ['ETH', 'ETHUSD', 'ETH-USD', '$ETH'], 'ETHUSD': ['ETH', 'ETHUSD', 'ETH-USD', '$ETH'],
    'LTC': ['LTC', 'LTCUSD', 'LTC-USD', '$LTC'], 'LTCUSD': ['LTC', 'LTCUSD', 'LTC-USD', '$LTC'],
    'XRP': ['XRP', 'XRPUSD', 'XRP-USD'], 'LTCUSD': ['XRP', 'XRPUSD', 'XRP-USD'],
    'BCH': ['BCH', 'BCHUSD', 'BCH-USD'], 'BCHUSD': ['BCH', 'BCHUSD', 'BCH-USD'],
    'BNB': ['BNB', 'BNBUSD', 'BNB-USD'], 'BCHUSD': ['BNB', 'BNBUSD', 'BNB-USD'],
  }

  forex_pairs = {
    'EUR-USD': ['EUR', 'USD', 'EUR-USD', 'USD-EUR', 'EUR/USD', 'EURUSD', 'USD/EUR', 'USDEUR'],
    'USD-EUR': ['EUR', 'USD', 'EUR-USD', 'USD-EUR', 'EUR/USD', 'EURUSD', 'USD/EUR', 'USDEUR'],
    'USD-JPY': [['JPY', 'USD', 'JPY-USD', 'USD-JPY', 'JPY/USD', 'JPYUSD', 'USD/JPY', 'USDJPY']],
    'JPY-USD': ['JPY', 'USD', 'JPY-USD', 'USD-JPY', 'JPY/USD', 'JPYUSD', 'USD/JPY', 'USDJPY'],
    'AUD-USD': ['AUD', 'USD', 'AUD-USD', 'USD-AUD', 'AUD/USD', 'AUDUSD', 'USD/AUD', 'USDAUD'],
    'USD-AUD': ['AUD', 'USD', 'AUD-USD', 'USD-AUD', 'AUD/USD', 'AUDUSD', 'USD/AUD', 'USDAUD'],
  }
  for pair, entries in forex_pairs.items(): forex_pairs[pair] += [f'{e}=X' for e in entries]

  if symbol in crypto_pairs: return crypto_pairs[symbol]
  elif currency is not None and f'{symbol}-{currency}' in forex_pairs: return forex_pairs[f'{symbol}-{currency}']
  return [symbol]

# News fetching
available_sources = [
    'seeking_alpha', 'cnbc', 'ap', 'investors', 'benzinga', 'bloomberg', 'reuters',
    'market_watch', 'wsb', 'cnn', 'hacker_news', 'twitter', 'forbes', 'themotleyfool',
]
def fetch_impressions(symbol: str, from_time: int, to_time: int, sources: Optional[List[str]] = None) -> Tuple[List[Sentiment], Dict[str, int]]:
    es = _initialize()

    entries: List[Sentiment] = []
    source_counts: Dict[str, int] = {}
    limit = 10000
    must_entries = [{ 'terms': { 'symbol.keyword': all_listings(symbol) }}]
    if sources is not None: must_entries.append({ 'terms': { 'source': sources  }})

    page = es.search(
        body={
            'query': {
                'bool': {
                    'must': must_entries,
                    'filter': [
                        { 'range': { 'timestamp': { 'gte': from_time }}},
                        { 'range': { 'timestamp': { 'lt': to_time }}}
                    ]
                }
            },
            'sort': [{ 'timestamp' : 'asc' }],
            'aggs': {
                'n_sources' : { 'cardinality' : { 'field' : 'source' } },
                'sources' : { 'terms' : { 'field' : 'source',  'size' : 500 } },
            },
            'size': limit
        },
        index=NEWS_INDEX,
        scroll = '2m',
    )
    for hit in page['hits']['hits']: entries.append(Sentiment(**(hit['_source'])))
    for bucket in page['aggregations']['sources']['buckets']: source_counts[bucket['key']] = bucket['doc_count']

    # Scroll through additional results if needed
    sid = page['_scroll_id']
    scroll_size = page['hits']['total']['value']
    while (scroll_size > 0):
        page = es.scroll(scroll_id = sid, scroll = '2m')
        sid = page['_scroll_id']
        scroll_size = len(page['hits']['hits'])
        for hit in page['hits']['hits']: entries.append(Sentiment(**(hit['_source'])))

    return entries, source_counts




