#!/bin/bash
# Installa il bot Zalando sul Mac: controlla ogni 15 minuti e avvisa su Telegram.
set -e
DIR="$HOME/zalando-bot"
REPO="https://raw.githubusercontent.com/fabianoleo/zalando-bot/main"
PLIST="$HOME/Library/LaunchAgents/com.zalandobot.plist"

echo "== Installo il bot Zalando in $DIR =="
if ! /usr/bin/python3 -c "import sys" >/dev/null 2>&1; then
  echo "Serve Python 3: si apre una finestra per installare gli 'Strumenti da riga di comando'."
  echo "Installali, poi rilancia lo stesso comando."
  xcode-select --install || true
  exit 1
fi

mkdir -p "$DIR"
cd "$DIR"
for f in check.py config.json requirements.txt; do
  curl -fsSL "$REPO/$f?$(date +%s)" -o "$f"
done
[ -f state.json ] || echo '{}' > state.json

echo "== Preparo Python (1-2 minuti) =="
/usr/bin/python3 -m venv venv
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q -r requirements.txt

if [ ! -f .env ]; then
  echo
  read -r -s -p "Incolla il token del bot Telegram (non si vede mentre scrivi) e premi Invio: " TOKEN < /dev/tty
  echo
  read -r -p "Il tuo chat ID Telegram: " CHAT < /dev/tty
  printf 'export TELEGRAM_TOKEN=%q\nexport TELEGRAM_CHAT_ID=%q\n' "$TOKEN" "$CHAT" > .env
  chmod 600 .env
fi

cat > run.sh <<'RUN'
#!/bin/bash
cd "$(dirname "$0")"
source .env
curl -fsSL "https://raw.githubusercontent.com/fabianoleo/zalando-bot/main/config.json?$(date +%s)" -o config.json.new 2>/dev/null && mv config.json.new config.json
./venv/bin/python check.py "$@"
RUN
chmod +x run.sh

mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.zalandobot</string>
  <key>ProgramArguments</key><array><string>$DIR/run.sh</string></array>
  <key>StartInterval</key><integer>900</integer>
  <key>RunAtLoad</key><false/>
  <key>StandardOutPath</key><string>$DIR/log.txt</string>
  <key>StandardErrorPath</key><string>$DIR/log.txt</string>
</dict></plist>
PL
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo
echo "== Prova: dovrebbe arrivarti un messaggio su Telegram =="
./run.sh --test
echo
echo "Fatto. Il bot controlla ogni 15 minuti finché il Mac è acceso."
echo "Per toglierlo:  launchctl unload $PLIST && rm -rf $DIR $PLIST"
