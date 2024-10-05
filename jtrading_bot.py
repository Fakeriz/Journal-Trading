import os
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# Token Telegram
TOKEN = os.getenv('7152456723:AAFBncqooKGVI8XUb2XarTvecOEDVX_yWtU')

# Konfigurasi Google Sheets API
# scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
# client = gspread.authorize(creds)

# ID Spreadsheet yang sudah dibuat (ambil dari URL Google Sheets)
# SPREADSHEET_ID = 'your_spreadsheet_id'

# Step untuk conversation
TRADE_ENTRY, EXPORT_CHOICE = range(2)

# Data jurnal trading akan disimpan sementara di sini
journal_data = []

# Fungsi untuk memulai bot
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Selamat datang di Trading Journal Bot.\nKetik /add untuk menambahkan jurnal trading baru."
    )

# Fungsi untuk memulai penambahan entri trading
def add_entry(update: Update, context: CallbackContext):
    update.message.reply_text("Silakan masukkan data trading Anda dalam format: Pair, Entry, Exit, Profit/Loss")
    return TRADE_ENTRY

# Fungsi untuk menerima data trading
def receive_entry(update: Update, context: CallbackContext):
    user_input = update.message.text
    try:
        pair, entry, exit, profit_loss = user_input.split(',')
        entry_data = {
            'Pair': pair.strip(),
            'Entry': float(entry.strip()),
            'Exit': float(exit.strip()),
            'Profit/Loss': float(profit_loss.strip())
        }
        journal_data.append(entry_data)
        update.message.reply_text(f"Data trading berhasil ditambahkan: {entry_data}")
        
        # Tawarkan opsi export
        reply_keyboard = [['CSV', 'Google Spreadsheet(MT)']]
        update.message.reply_text(
            "Data trading Anda sudah tersimpan. Bagaimana Anda ingin mengekspornya?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return EXPORT_CHOICE

    except ValueError:
        update.message.reply_text("Format salah. Pastikan Anda memasukkan data dalam format: Pair, Entry, Exit, Profit/Loss")
        return TRADE_ENTRY

# Fungsi untuk mengekspor data ke CSV atau Google Sheets
def export_choice(update: Update, context: CallbackContext):
    choice = update.message.text
    if choice == 'CSV':
        # Export to CSV
        df = pd.DataFrame(journal_data)
        csv_file = 'trading_journal.csv'
        df.to_csv(csv_file, index=False)
        update.message.reply_document(open(csv_file, 'rb'))
        os.remove(csv_file)  # Hapus file CSV setelah dikirim
    elif choice == 'Google Spreadsheet':
        # Export to Google Sheets
        df = pd.DataFrame(journal_data)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        sheet.clear()  # Bersihkan isi sheet
        sheet.update([df.columns.values.tolist()] + df.values.tolist())  # Update sheet
        update.message.reply_text(f"Data telah diekspor ke Google Spreadsheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
    else:
        update.message.reply_text("Pilihan tidak valid.")
    
    return ConversationHandler.END

# Fungsi untuk membatalkan proses
def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Proses dibatalkan.")
    return ConversationHandler.END

# Fungsi utama untuk menjalankan bot
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Conversation handler untuk menambahkan entri dan ekspor data
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add_entry)],
        states={
            TRADE_ENTRY: [MessageHandler(Filters.text & ~Filters.command, receive_entry)],
            EXPORT_CHOICE: [MessageHandler(Filters.text & ~Filters.command, export_choice)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler('start', start))

    # Mulai bot
    updater.start_polling()
    updater.idle()

if name == 'main':
    main()