import json, time, urllib.request as urllib2, sys, platform, time, base64, hashlib, hmac, urllib
from typing import List, Dict, Tuple, Union
from dotenv import dotenv_values

from koi.market_data.root import CryptoOrder
from koi.market_data.helpers.kraken_ws import WssClient
from koi.market_data.helpers.market_models import CryptoTick, KrakenTick

env = dotenv_values('.env')

class Client():
    ws: WssClient
    # ws: WebSocket
    api_url = 'https://api.kraken.com'
    stream_ticks: bool
    ws_token: str

    prev_tick_state: Dict[str, CryptoTick] = {}
    latest_tick_state: Dict[str, CryptoTick] = {}

    open_oders: List[Dict[str, dict]]

    
    def __init__(self, sandbox: bool = True) -> None:
        self.stream_ticks = False
        
        # Set up websocket
        ws_url = 'wss://ws-sandbox.kraken.com' if sandbox else 'wss://ws.kraken.com'
        try:
            self.ws = WssClient(env['KRAKEN_API_KEY'], env['KRAKEN_API_SECRET'])
            self.ws.start()

            # Acquire token
            self._configure_token()

            # Set up subscriptions
            print(f'\nSetting up kraken ws subscriptions with token: {self.ws_token}')
            # self.ws.subscribe_private(
            #     subscription = { 'name': 'openOrders', 'token': self.ws_token },
            #     callback = self.handle_open_orders_cb
            # )
            # self.ws.subscribe_private(
            #     subscription = { 'name': 'ownTrades', 'token': self.ws_token },
            #     callback = self.handle_own_trades_cb
            # )

            # self.add_order(CryptoOrder('BTC-USD', 'buy', 1, 1))



        except Exception as e:
            print('Kraken Client: connect_ws error:', e)
            return


    # Helpers
    def _configure_token(self) -> str:
        token_url = 'https://api.kraken.com/0/private/GetWebSocketsToken'
        # req = requests.get(token_url, headers={
        #     'API-Key': KRAKEN_API_KEY,
        #     'API-Sign': ''
        # })
        api_nonce = bytes(str(int(time.time()*1000)), "utf-8")
        api_request = urllib.request.Request(token_url, b"nonce=%s" % api_nonce)
        api_request.add_header("API-Key", env['KRAKEN_API_KEY'])
        api_request.add_header("API-Sign", base64.b64encode(hmac.new(base64.b64decode(env['KRAKEN_API_SECRET']), b"/0/private/GetWebSocketsToken" + hashlib.sha256(api_nonce + b"nonce=%s" % api_nonce).digest(), hashlib.sha512).digest()))
        self.ws_token = json.loads(urllib.request.urlopen(api_request).read())['result']['token']

    def _sanitize_pair(self, symbol: str) -> str:
        return symbol.replace('-', '/').replace('BTC', 'XBT')
    def _desanitize_pair(self, symbol: str) -> str:
        return symbol.replace('/', '-').replace('XBT', 'BTC')


    # Ticks
    def has_symbol_tick_data(self, symbol: str) -> bool:
        return self._sanitize_pair(symbol) in self.latest_tick_state

    def get_symbol_tick_data(self, symbol: str) -> Tuple[KrakenTick, KrakenTick]:
        pair = self._sanitize_pair(symbol)
        if not self.has_symbol_tick_data(pair): return None
        return (self.prev_tick_state[pair], self.latest_tick_state[pair])

    def handle_tick_data(self, msg: Union[list, dict]):
        if not isinstance(msg, list) or len(msg) < 4: return

        data, channel, symbol = msg[1], msg[2], msg[3]
        tick = KrakenTick(data, self._desanitize_pair(symbol))

        if symbol in self.latest_tick_state:
            self.prev_tick_state[symbol] = self.latest_tick_state[symbol]
            self.latest_tick_state[symbol] = tick
        else:
            self.prev_tick_state[symbol] = tick
            self.latest_tick_state[symbol] = tick

    def _handle_spread_data(self, msg: dict):
        if isinstance(msg, dict) and 'event' in msg and msg['event'] in ['heartbeat', 'systemStatus']: return
        pass

    def start_tick_streaming(self, pairs: List[str]):
        if self.ws is None: raise Exception('No Active Kraken WS Connection')
        self.stream_ticks = True
        print('start_tick_streaming:', pairs)

        self.ws.subscribe_public(
            subscription={ 'name': 'ticker' },
            pair=[self._sanitize_pair(p) for p in pairs],
            callback=self.handle_tick_data
        )
        self.ws.subscribe_public(
            subscription={ 'name': 'spread' },
            pair=[self._sanitize_pair(p) for p in pairs],
            callback=self._handle_spread_data
        )





    # Orders
    def handle_open_orders_cb(self, msg: dict):
        if isinstance(msg, dict) and 'event' in msg and msg['event'] in ['heartbeat', 'systemStatus']: return

        print('handle_open_orders_cb:', msg)

    def handle_own_trades_cb(self, msg: dict):
        if isinstance(msg, dict) and 'event' in msg and msg['event'] in ['heartbeat', 'systemStatus']: return

        print('handle_own_trades_cb:', msg)

    # def start_order_ws(self):
    #     self.ws.subscribe_private(
    #         subscription = { 'name': 'openOrders', 'token': self.ws_token },
    #         callback = self.handle_order_cb
    #     )

    def handle_add_order_cb(self, msg: dict):
        if isinstance(msg, dict) and 'event' in msg and msg['event'] in ['heartbeat', 'systemStatus']: return
        print('handle_add_order_cb:', msg)
        
    def add_order(self, order: CryptoOrder):
        if self.ws is None: raise Exception('No Active Kraken WS Connection')
        print('\nAdding Crypto Order:', order)

        res = self.ws.request(
            request={
                'event': "addOrder",
                'ordertype': "limit",
                'pair': self._sanitize_pair(order.symbol),
                'price': f'{order.price}',
                'token': self.ws_token,
                'type': order.side,
                'volume': f'{round(order.quantity, 8)}'
            },
            callback=self.handle_add_order_cb
        )

        print('add_order res:', res)



