/**
 * Gira su Telegram le mail di riassortimento di Zalando (e di Restockalert).
 * Gira su Google Apps Script, ogni 5 minuti, anche col Mac spento.
 *
 * Impostazione: Impostazioni progetto -> Proprietà script, aggiungi
 *   TELEGRAM_TOKEN   = il token di BotFather
 *   TELEGRAM_CHAT_ID = il tuo chat ID
 * Poi esegui una volta "installa".
 */

// Quali mail girare. Modificabile: è una normale ricerca Gmail.
const RICERCA =
  '(from:zalando (disponibile OR "di nuovo" OR "torna" OR "back in stock" OR "taglia")) ' +
  'OR from:restockalert ' +
  'newer_than:2d -label:inviato-telegram';

const ETICHETTA = 'inviato-telegram';

function controllaMail() {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty('TELEGRAM_TOKEN');
  const chat = props.getProperty('TELEGRAM_CHAT_ID');
  if (!token || !chat) throw new Error('Mancano TELEGRAM_TOKEN o TELEGRAM_CHAT_ID nelle Proprietà script');

  const etichetta = GmailApp.getUserLabelByName(ETICHETTA) || GmailApp.createLabel(ETICHETTA);
  const thread = GmailApp.search(RICERCA, 0, 20);

  thread.forEach(function (t) {
    const m = t.getMessages().pop();
    const link = (m.getPlainBody().match(/https?:\/\/[^\s<>"]*zalando[^\s<>"]*/i) || [''])[0];
    const testo =
      '📧 <b>' + esc(m.getSubject()) + '</b>\n' +
      'da: ' + esc(m.getFrom()) + '\n' +
      esc(m.getPlainBody().replace(/\s+/g, ' ').slice(0, 300)) +
      (link ? '\n' + link : '');
    invia(token, chat, testo);
    t.addLabel(etichetta);
  });
}

function invia(token, chat, testo) {
  UrlFetchApp.fetch('https://api.telegram.org/bot' + token + '/sendMessage', {
    method: 'post',
    payload: { chat_id: chat, text: testo, parse_mode: 'HTML', disable_web_page_preview: 'true' },
  });
}

function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/** Esegui una volta: manda un messaggio di prova e attiva il controllo ogni 5 minuti. */
function installa() {
  ScriptApp.getProjectTriggers().forEach(function (tr) { ScriptApp.deleteTrigger(tr); });
  ScriptApp.newTrigger('controllaMail').timeBased().everyMinutes(5).create();
  const props = PropertiesService.getScriptProperties();
  invia(props.getProperty('TELEGRAM_TOKEN'), props.getProperty('TELEGRAM_CHAT_ID'),
    '📬 Avvisi da Gmail attivi: ti giro qui le mail di Zalando e Restockalert sui riassortimenti.');
}
