import mojito
import yfinance as yf
import pandas as pd
import numpy as np
import time
import requests
import csv
import os
from datetime import datetime
import warnings
from sklearn.ensemble import RandomForestRegressor

warnings.filterwarnings('ignore')

# ==========================================
# 1. 지호 사장님 전용 설정
# ==========================================
key = "PSgiUu1bjrkWomUVvox8tsQtJPS71JHJeuPi"
secret = "B1put3i5vYVCEiaqbvWdHgHh7oPPi/JSLEDTV3kvUEPS4WV10SuxYOth2mQh9vEjlzjY7QUwWT46ww3zz16tF0hwQOS9Z8iNqv9bcENmMPeshcvBMFN7j0mrhihgziFjffQWE2oBscFHaXQanfK57Z8YcdR9q66D0Inn2xXsiZZDYiMO8bU="
acc_no = "50177946-01" 

TELEGRAM_TOKEN = "8688186843:AAE1mataEqNDhoZxXfz8sOZCNaDsnTZXsSc"
TELEGRAM_CHAT_ID = "7499693932" 

# 📈 [전략 지표]
PROFIT_TARGET = 0.008      # 0.8% 익절
STOP_LOSS_LIMIT = -0.015   # -1.5% 손절
ADD_BUY_MARGIN = -0.012    # -1.2% 하락 시 물타기
MAX_POSITIONS = 7          # 🔥 중요: 최대 7종목까지만 운용 (예수금 보호)

print("🏛️ 지호 퀀트 [V22: 파이널 엔진] 가동 중...")

broker = mojito.KoreaInvestment(api_key=key, api_secret=secret, acc_no=acc_no, exchange='나스닥', mock=True)

LOG_FILE = 'quant_trade_log.csv'
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode='w', newline='', encoding='utf-8-sig') as f:
        csv.writer(f).writerow(['Date', 'Time', 'Market', 'Action', 'Ticker', 'Price', 'Quantity', 'Reason', 'BetAmount'])

def send_telegram_msg(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=5)
    except: pass

def analyze_local_ai(yf_ticker):
    try:
        df = yf.download(yf_ticker, period="150d", progress=False)
        if len(df) < 50: return None
        df['MA5'] = df['Close'].rolling(5).mean(); df['MA20'] = df['Close'].rolling(20).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / loss)))
        df['Range'] = (df['High'] - df['Low']) / df['Close']
        df['Target'] = df['Close'].shift(-1)
        df.dropna(inplace=True)
        X = df[['MA5', 'MA20', 'RSI', 'Volume', 'Range']]
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, df['Target'])
        latest = df.iloc[-1:]
        curr_price = float(latest['Close'].iloc[0])
        pred_price = float(model.predict(latest[['MA5', 'MA20', 'RSI', 'Volume', 'Range']])[0])
        return {"curr": curr_price, "growth": (pred_price - curr_price) / curr_price, "rsi": float(latest['RSI'].iloc[0]), "vol": df['Range'].tail(5).mean()}
    except: return None

STOCKS = [("NVDA", "엔비디아"), ("TSLA", "테슬라"), ("AAPL", "애플"), ("MSFT", "마이크로소프트"), ("AMD", "AMD"), ("AMZN", "아마존"), ("META", "메타"), ("GOOGL", "구글"), ("TQQQ", "나스닥3배"), ("SOXL", "반도체3배")]

while True:
    try:
        now = datetime.now()
        balance = broker.fetch_present_balance()
        holdings = balance.get('output1', [])
        my_stocks = {s['ovrs_pdno']: float(s['pchs_avg_pric']) for s in holdings}

        # [매도 감시]
        for s in holdings:
            p_rt = float(s['evlu_pfls_rt']) / 100
            if p_rt >= PROFIT_TARGET or p_rt <= STOP_LOSS_LIMIT:
                broker.create_market_sell_order(s['ovrs_pdno'], int(s['ccld_qty_1']))
                with open(LOG_FILE, 'a', newline='') as f:
                    csv.writer(f).writerow([now.strftime('%Y-%m-%d'), now.strftime('%H:%M:%S'), "미국", "SELL", s['prdt_name'], 0, s['ccld_qty_1'], "익절" if p_rt > 0 else "손절", 0])
                send_telegram_msg(f"💰 [매도] {s['prdt_name']} ({p_rt*100:.2f}%)")

        # [매수 스캔]
        if len(holdings) < MAX_POSITIONS: # 🔥 종목 수 제한 체크
            for tck, name in STOCKS:
                res = analyze_local_ai(tck)
                if not res: continue
                
                # 자율 배팅액 결정
                bet = 3000 if res['growth'] >= 0.015 else 1500 if res['growth'] >= 0.005 else 500
                
                can_buy = False
                if tck not in my_stocks: can_buy = True
                elif (res['curr'] / my_stocks[tck] - 1) <= ADD_BUY_MARGIN: can_buy = True

                if can_buy and ((res['growth'] >= 0.003 and res['rsi'] < 75) or (res['rsi'] < 45)):
                    qty = max(1, int(bet / res['curr']))
                    broker.create_market_buy_order(tck, qty)
                    with open(LOG_FILE, 'a', newline='') as f:
                        csv.writer(f).writerow([now.strftime('%Y-%m-%d'), now.strftime('%H:%M:%S'), "미국", "BUY", name, res['curr'], qty, "공격진입", bet])
                    send_telegram_msg(f"🧨 [매수] {name} (${bet})\n예측: {res['growth']*100:.2f}%")
                    time.sleep(1)

        time.sleep(10)
    except Exception as e: print(f"Error: {e}"); time.sleep(10)
