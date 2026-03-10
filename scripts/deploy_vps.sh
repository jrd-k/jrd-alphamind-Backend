#!/bin/bash
# VPS Deployment Script for 24/7 AI Trading Bot
# This script sets up the trading bot on a VPS server

set -e

echo "🚀 Starting VPS deployment for AI Trading Bot..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and pip
echo "🐍 Installing Python and dependencies..."
sudo apt install -y python3 python3-pip python3-venv git

# Install MetaTrader 5 (wine required for Linux)
echo "📈 Installing MetaTrader 5 dependencies..."
sudo apt install -y wine-stable xvfb

# Create trading bot directory
echo "📁 Setting up trading bot directory..."
mkdir -p ~/trading-bot
cd ~/trading-bot

# Clone the repository
echo "📥 Cloning repository..."
git clone https://github.com/jrd-k/jrd-alphamind-Backend.git .
cd backend

# Create virtual environment
echo "🔧 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
pip install MetaTrader5
pip install pytrader  # If available, otherwise use MetaTrader5

# Setup environment variables
echo "⚙️ Setting up environment variables..."
cat > .env << EOF
# Database
DATABASE_URL=sqlite:///./trading_bot.db

# AI API Keys (configure these)
OPENAI_API_KEY=your_openai_key_here
KIMI_API_KEY=your_kimi_key_here
DEEPLSEEK_API_KEY=your_deepseek_key_here

# Broker settings
MT5_LOGIN=your_mt5_login
MT5_PASSWORD=your_mt5_password
MT5_SERVER=your_mt5_server

# PyTrader settings
PYTRADER_HOST=localhost
PYTRADER_PORT=1122

# Trading settings
BRAIN_MIN_CONFIDENCE=0.6
TRADING_ENABLED=true
EOF

echo "🗄️ Initializing database..."
python -c "from app.core.database import init_db; init_db()"

# Setup MetaTrader 5
echo "📈 Setting up MetaTrader 5..."
# Download and install MT5 terminal (manual step required)
echo "⚠️  MANUAL STEP REQUIRED: Download and install MetaTrader 5 terminal"
echo "   1. Download MT5 from https://www.metatrader5.com/en/download"
echo "   2. Install using wine: wine MT5Setup.exe"
echo "   3. Login to your broker account"
echo "   4. Install PyTrader EA if using PyTrader"

# Create systemd service for 24/7 running
echo "🔄 Creating systemd service for 24/7 operation..."
sudo tee /etc/systemd/system/trading-bot.service > /dev/null << EOF
[Unit]
Description=AI Trading Bot Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/trading-bot/backend
Environment=PATH=/home/$USER/trading-bot/backend/venv/bin
ExecStart=/home/$USER/trading-bot/backend/venv/bin/python start_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
echo "▶️ Starting trading bot service..."
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot

# Setup monitoring
echo "📊 Setting up monitoring..."
cat > monitor_bot.sh << 'EOF'
#!/bin/bash
# Monitor script to check if bot is running and restart if needed

while true; do
    if ! pgrep -f "start_server.py" > /dev/null; then
        echo "$(date): Bot not running, restarting..."
        cd /home/$USER/trading-bot/backend
        source venv/bin/activate
        python start_server.py &
    fi
    sleep 60
done
EOF

chmod +x monitor_bot.sh

# Setup cron job for monitoring
echo "⏰ Setting up cron job for monitoring..."
(crontab -l ; echo "@reboot /home/$USER/trading-bot/monitor_bot.sh") | crontab -

# Setup log rotation
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/trading-bot > /dev/null << EOF
/home/$USER/trading-bot/backend/*.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 644 $USER $USER
}
EOF

echo "✅ VPS deployment completed!"
echo ""
echo "🎯 Next steps:"
echo "1. Configure your API keys in ~/trading-bot/backend/.env"
echo "2. Install MetaTrader 5 terminal using wine"
echo "3. Login to your broker account in MT5"
echo "4. Install PyTrader EA if using PyTrader"
echo "5. Test the bot: curl http://localhost:8000/docs"
echo ""
echo "🔍 Check status:"
echo "  sudo systemctl status trading-bot"
echo "  journalctl -u trading-bot -f"
echo ""
echo "Your AI trading bot is now running 24/7! 🚀"