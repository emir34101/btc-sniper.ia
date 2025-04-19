import pandas as pd
import requests
from datetime import datetime
import time
import telegram

# Configura tu bot
TELEGRAM_TOKEN = 'TU_TOKEN'
CHAT_ID = 'TU_CHAT_ID'
bot = telegram.Bot(token=TELEGRAM_TOKEN)

def get_binance_data(symbol='BTCUSDT', interval='1h', limit=200):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
    response = requests.get(url)
    data = response.json()
    
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_vol', 'taker_buy_quote_vol', 'ignore'
    ])
    
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = df['close'].astype(float)
    df['open'] = df['open'].astype(float)
    df['low'] = df['low'].astype(float)
    df['high'] = df['high'].astype(float)
    
    return df[['timestamp', 'open', 'high', 'low', 'close']]

def detectar_senal_trading_latino(df, tf):
    df['EMA_11'] = df['close'].ewm(span=11, adjust=False).mean()
    df['EMA_55'] = df['close'].ewm(span=55, adjust=False).mean()

    ema_cross_up = df['EMA_11'].iloc[-2] < df['EMA_55'].iloc[-2] and df['EMA_11'].iloc[-1] > df['EMA_55'].iloc[-1]
    ema_cross_down = df['EMA_11'].iloc[-2] > df['EMA_55'].iloc[-2] and df['EMA_11'].iloc[-1] < df['EMA_55'].iloc[-1]

    precio = df['close'].iloc[-1]
    ema11 = df['EMA_11'].iloc[-1]
    vela_actual = df.iloc[-1]
    vela_anterior = df.iloc[-2]

    pullback_confirmado = False

    # Confirmación tipo "pullback" (cierre sobre EMA + cuerpo mayor a la vela anterior)
    if vela_actual['low'] <= ema11 <= vela_actual['close']:
        cuerpo_actual = abs(vela_actual['close'] - vela_actual['open'])
        cuerpo_anterior = abs(vela_anterior['close'] - vela_anterior['open'])
        if cuerpo_actual > cuerpo_anterior:
            pullback_confirmado = True

    if ema_cross_up and pullback_confirmado:
        return f"🟢 HORA DE COMPRAR BTC ({tf}) – Pullback confirmado sobre EMA11"
    elif ema_cross_down and pullback_confirmado:
        return f"🔴 HORA DE CERRAR POSICIÓN BTC ({tf}) – Señal bajista con confirmación"
    else:
        return None

def revisar_y_enviar_senal():
    for tf in ['1h', '4h']:
        df = get_binance_data(interval=tf)
        señal = detectar_senal_trading_latino(df, tf)
        if señal:
            bot.send_message(chat_id=CHAT_ID, text=señal)

# Loop de revisión cada 15 minutos
while True:
    try:
        print(f"🔍 Revisión en curso - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        revisar_y_enviar_senal()
        time.sleep(900)  # 15 minutos
    except Exception as e:
        print(f"⚠️ Error: {e}")
        time.sleep(60)
