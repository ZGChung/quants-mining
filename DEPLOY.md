# QuantMining Deployment Guide / 部署指南

## Quick Deploy / 快速部署

### Option 1: Streamlit Community Cloud (Recommended) / 推荐

```bash
# 1. Push code to GitHub
 add .
gitgit commit -m "Ready for deployment"
git push

# 2. Go to https://share.streamlit.io
# 3. Sign in with GitHub
# 4. Select your repo: ZGChung/quants-mining
# 5. Set: Main file path = app.py
# 6. Deploy!

# 访问地址: https://your-app-name.streamlit.app
```

### Option 2: Railway (Free)

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Initialize
railway init

# 4. Deploy
railway up
```

### Option 3: Render (Free)

```bash
# 1. Push to GitHub

# 2. Go to https://render.com
# 3. Create Web Service
# 4. Connect GitHub repo
# 5. Build command: pip install -r requirements.txt
# 6. Start command: streamlit run app.py --server.port $PORT
```

### Option 4: Heroku (Free Tier Ending)

```bash
# Heroku 免费版将于 2026 年 11 月结束
# 不推荐新项目使用
```

---

## Environment Variables / 环境变量

创建 `.env` 文件:

```bash
# 数据源 API Keys (可选)
ALPHAVANTAGE_API_KEY=your_key_here
POLYGON_API_KEY=your_key_here
FINNHUB_API_KEY=your_key_here

# Telegram 通知 (可选)
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## Free API Keys / 免费 API Keys

### Alpha Vantage
- 注册: https://www.alphavantage.co/support/#api-key
- 免费: 5 calls/min, 500 calls/day
- Demo key: `demo` (仅限部分股票)

### Polygon.io
- 注册: https://polygon.io/dashboard/signup
- 免费: 5 calls/min

### Finnhub
- 注册: https://finnhub.io/
- 免费: 60 calls/min

### Yahoo Finance
- 免费，无需 API key
- 有速率限制

---

## Usage / 使用方法

```bash
# 本地运行
pip install -r requirements.txt
streamlit run app.py

# 使用真实数据
python run.py --source yahoo --tickers AAPL MSFT --portfolio
python run.py --source alphavantage --tickers AAPL MSFT
```

---

## Notes / 注意事项

1. **Streamlit Community Cloud** 是最简单的免费选项
2. 免费主机有资源限制，不适合大规模回测
3. 大规模回测建议在本地运行
4. Telegram 通知功能已集成
