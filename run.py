import asyncio
import websockets
import json
import datetime
from decimal import Decimal, getcontext
from requests import get
from urllib import parse

getcontext().prec = 6


def log(msg, level=0):
    print(datetime.datetime.now().isoformat(), ' ', msg)


log('Start')

# Load configuration settings
log('Loading config.json')
with open('config.json') as f:
    config = json.load(f)
    config['variance'] = Decimal(config['variance'])


async def main():
    lastHour = datetime.datetime.now().hour
    lastPrice = Decimal(0)
    log('Opening websocket to ' + config['uri'])
    async with websockets.connect(config['uri']) as websocket:
        sMsg = '{"action":"subscribe","subscribe":"kbar","kbar":"1min","pair":"' + \
            config['pair'] + '"}'
        log('Sending subscription message ' + sMsg)
        await websocket.send(sMsg)
        while True:
            log('Waiting for socket message')
            data = await websocket.recv()
            log('Got message ' + data)
            log('Converting to JSON')
            data = json.loads(data)
            # Check for ping so we can reply with pong 😁
            if 'ping' in data:
                log('Got ping message and responding with pong')
                await websocket.send('{"action":"pong","pong":"' + data['ping'] + '"}')

            # Check and get candlestick data
            if 'kbar' in data:
                price = Decimal(data['kbar']['c'])

                log('Got candlestick data')
                log('Current price is ' + str(price))
                log('Last price is ' + str(lastPrice))
                log('Last hour is ' + lastHour)
                if price < lastPrice * config['variance'] or price > lastPrice * (1 + config['variance']) or datetime.datetime.now().hour != lastHour:
                    log('Price variant hit or hour changed')

                    if lastPrice == 0:
                        text = '💱 1B BABYDOGE Price is ' + \
                            str(price * 1000000000)
                    else:
                        text = '💱 1B BABYDOGE Price is ' + str(price * 1000000000) + (
                            ' up ' if price > lastPrice else ' down ') + str(abs((price - lastPrice)) * 100 / price) + '%'

                    params = {
                        'chat_id': config['chatid'],
                        'text': text
                    }

                    payload_str = parse.urlencode(params, safe='@')
                    log('Sending message to Telegram bot 🤖')
                    get('https://api.telegram.org/bot' +
                        config['bot'] + '/sendMessage', params=payload_str)
                    lastPrice = price
                    lastHour = datetime.datetime.now().hour

log('Starting asyncio')
asyncio.get_event_loop().run_until_complete(main())
