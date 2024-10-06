import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, CallbackQueryHandler, ContextTypes
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO

TOKEN = '7152456723:AAFBncqooKGVI8XUb2XarTvecOEDVX_yWtU'

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Menus side panel
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    keyboard = [
        [InlineKeyboardButton("Memulai bot dan menampilkan menu utama", callback_data='start')],
        [InlineKeyboardButton("Mendaftarkan pengguna baru", callback_data='registry')],
        [InlineKeyboardButton("Memulai proses pencatatan trade baru", callback_data='newentry')],
        [InlineKeyboardButton("Menghasilkan laporan kerja", callback_data='report')],
        [InlineKeyboardButton("Menampilkan opsi untuk melihat chart", callback_data='chart')],
        [InlineKeyboardButton("Mengekspor data trading ke CSV dan Excel", callback_data='export')],
        [InlineKeyboardButton("Memperbarui trade yang ada", callback_data='updatetrade')],
        [InlineKeyboardButton("Menghapus trade", callback_data='deletetrade')],
        [InlineKeyboardButton("Menampilkan riwayat trading terbaru", callback_data='history')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose an option:', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    await query.answer()

    if query.data == 'start':
        await query.edit_message_text(text="Memulai bot dan menampilkan menu utama.")
    elif query.data == 'registry':
        await query.edit_message_text(text="Mendaftarkan pengguna baru.")
    elif query.data == 'newentry':
        await query.edit_message_text(text="Memulai proses pencatatan trade baru.")
    elif query.data == 'report':
        await query.edit_message_text(text="Menghasilkan laporan kerja.")
    elif query.data == 'chart':
        await query.edit_message_text(text="Menampilkan opsi untuk melihat chart.")
    elif query.data == 'export':
        await query.edit_message_text(text="Mengekspor data trading ke CSV dan Excel.")
    elif query.data == 'updatetrade':
        await query.edit_message_text(text="Memperbarui trade yang ada.")
    elif query.data == 'history':
        await query.edit_message_text(text="Menampilkan riwayat trading terbaru.")

# Define conversation states
PAIR, POSITION, ENTRY_PRICE, TAKE_PROFIT, STOP_LOSS, RISK_REWARD, RISK_AMOUNT, LOT_SIZE, DATE_TIME, SESSION, ANALYSIS = range(11)

# Database setup
def setup_database():
    conn = sqlite3.connect('trading_journal.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS trades
                 (id INTEGER PRIMARY KEY, pair TEXT, position TEXT, entry_price REAL, 
                 take_profit REAL, stop_loss REAL, risk_reward REAL, risk_amount REAL, 
                 lot_size REAL, date_time TEXT, session TEXT, analysis TEXT, profit_loss REAL)''')
    conn.commit()
    conn.close()

setup_database()

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_text(f'Welcome to your Forex Trading Journal Bot, {user.first_name}!\n\n'
                              f'Commands:\n'
                              f'/newentry - Log a new trade\n'
                              f'/history - View your trade history\n'
                              f'/report - Get a performance report\n'
                              f'/chart - View performance charts\n'
                              f'/export - Export your trade data')

def new_entry(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(f'Let\'s log a new trade. What\'s the trading pair?'
                              f'XAUUSD\n'
                              f'BTCUSD\n'
                              f'USOIL\n'
                              f'EURUSD, etc\n')
    return PAIR

def pair(update: Update, context: CallbackContext) -> int:
    context.user_data['pair'] = update.message.text
    reply_keyboard = [['Long', 'Short']]
    update.message.reply_text('Is this a Long (Buy) or Short (Sell) position?',
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return POSITION

def position(update: Update, context: CallbackContext) -> int:
    context.user_data['position'] = update.message.text
    update.message.reply_text('What\'s the entry price?', reply_markup=ReplyKeyboardRemove())
    return ENTRY_PRICE

def entry_price(update: Update, context: CallbackContext) -> int:
    context.user_data['entry_price'] = float(update.message.text)
    update.message.reply_text('What\'s your Take Profit price?')
    return TAKE_PROFIT

def take_profit(update: Update, context: CallbackContext) -> int:
    context.user_data['take_profit'] = float(update.message.text)
    update.message.reply_text('What\'s your Stop Loss price?')
    return STOP_LOSS

def stop_loss(update: Update, context: CallbackContext) -> int:
    context.user_data['stop_loss'] = float(update.message.text)
    update.message.reply_text('What\'s the Risk/Reward ratio?')
    return RISK_REWARD

def risk_reward(update: Update, context: CallbackContext) -> int:
    context.user_data['risk_reward'] = update.message.text
    update.message.reply_text('How much are you risking? (in USD)')
    return RISK_AMOUNT

def risk_amount(update: Update, context: CallbackContext) -> int:
    context.user_data['risk_amount'] = update.message.text
    update.message.reply_text('What\'s the lot size?')
    return LOT_SIZE

def lot_size(update: Update, context: CallbackContext) -> int:
    context.user_data['lot_size'] = float(update.message.text)
    update.message.reply_text('What\'s the date and time of entry? (YYYY-MM-DD HH:MM)')
    return DATE_TIME

def date_time(update: Update, context: CallbackContext) -> int:
    context.user_data['date_time'] = update.message.text
    reply_keyboard = [['Asia', 'London', 'NY am', 'NY pm']]
    update.message.reply_text('Which session is this trade in?',
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return SESSION

def session(update: Update, context: CallbackContext) -> int:
    context.user_data['session'] = update.message.text
    update.message.reply_text('Please provide a brief analysis for this trade.', reply_markup=ReplyKeyboardRemove())
    return ANALYSIS
# ... (include all other conversation handlers from POSITION to ANALYSIS) ...

def save_trade(context: CallbackContext):
    conn = sqlite3.connect('trading_journal.db')
    c = conn.cursor()
    c.execute('''INSERT INTO trades (pair, position, entry_price, take_profit, stop_loss, 
                 risk_reward, risk_amount, lot_size, date_time, session, analysis)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (context.user_data['pair'], context.user_data['position'], context.user_data['entry_price'],
               context.user_data['take_profit'], context.user_data['stop_loss'], context.user_data['risk_reward'],
               context.user_data['risk_amount'], context.user_data['lot_size'], context.user_data['date_time'],
               context.user_data['session'], context.user_data['analysis']))
    conn.commit()
    conn.close()

def analysis(update: Update, context: CallbackContext) -> int:
    context.user_data['analysis'] = update.message.text
    save_trade(context)
    
    summary = f"Trade logged successfully!\n\n" \
              f"Pair: {context.user_data['pair']}\n" \
              f"Position: {context.user_data['position']}\n" \
              f"Entry Price: {context.user_data['entry_price']}\n" \
              f"Take Profit: {context.user_data['take_profit']}\n" \
              f"Stop Loss: {context.user_data['stop_loss']}\n" \
              f"Risk/Reward: {context.user_data['risk_reward']}\n" \
              f"Risk Amount: ${context.user_data['risk_amount']}\n" \
              f"Lot Size: {context.user_data['lot_size']}\n" \
              f"Date/Time: {context.user_data['date_time']}\n" \
              f"Session: {context.user_data['session']}\n" \
              f"Analysis: {context.user_data['analysis']}"
    
    update.message.reply_text(summary)
    context.user_data.clear()
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Trade logging cancelled.', reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

def history(update: Update, context: CallbackContext) -> None:
    conn = sqlite3.connect('trading_journal.db')
    df = pd.read_sql_query("SELECT * FROM trades ORDER BY date_time DESC LIMIT 5", conn)
    conn.close()

    if df.empty:
        update.message.reply_text('No trades logged yet.')
        return

    history_text = "Your Recent Trade History:\n\n"
    for _, trade in df.iterrows():
        history_text += f"{trade['pair']} - {trade['position']} @ {trade['entry_price']}\n" \
                        f"Date: {trade['date_time']}\n" \
                        f"R/R: {trade['risk_reward']}, Risk: ${trade['risk_amount']}\n\n"
    
    update.message.reply_text(history_text)

def report(update: Update, context: CallbackContext) -> None:
    conn = sqlite3.connect('trading_journal.db')
    df = pd.read_sql_query("SELECT * FROM trades", conn)
    conn.close()

    if df.empty:
        update.message.reply_text('No trades logged yet.')
        return

    total_trades = len(df)
    total_risk = df['risk_amount'].sum()
    avg_rr = df['risk_reward'].mean()
    
    report_text = f"Performance Report:\n\n" \
                  f"Total Trades: {total_trades}\n" \
                  f"Total Risk: ${total_risk:.2f}\n" \
                  f"Average Risk per Trade: ${total_risk / total_trades:.2f}\n" \
                  f"Average Risk/Reward: {avg_rr:.2f}"
    
    update.message.reply_text(report_text)

def create_bar_chart():
    conn = sqlite3.connect('trading_journal.db')
    df = pd.read_sql_query("SELECT pair, COUNT(*) as count FROM trades GROUP BY pair", conn)
    conn.close()

    plt.figure(figsize=(10, 6))
    plt.bar(df['pair'], df['count'])
    plt.title('Number of Trades per Currency Pair')
    plt.xlabel('Currency Pair')
    plt.ylabel('Number of Trades')
    plt.xticks(rotation=45)
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    
    return buffer

def create_pie_chart():
    conn = sqlite3.connect('trading_journal.db')
    df = pd.read_sql_query("SELECT session, COUNT(*) as count FROM trades GROUP BY session", conn)
    conn.close()

    plt.figure(figsize=(8, 8))
    plt.pie(df['count'], labels=df['session'], autopct='%1.1f%%')
    plt.title('Distribution of Trades by Session')
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    
    return buffer

def chart(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Bar Chart", callback_data='bar'),
         InlineKeyboardButton("Pie Chart", callback_data='pie')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Choose a chart type:', reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'bar':
        chart_buffer = create_bar_chart()
        query.message.reply_photo(photo=chart_buffer, caption="Number of Trades per Currency Pair")
    elif query.data == 'pie':
        chart_buffer = create_pie_chart()
        query.message.reply_photo(photo=chart_buffer, caption="Distribution of Trades by Session")

def export_data(update: Update, context: CallbackContext) -> None:
    conn = sqlite3.connect('trading_journal.db')
    df = pd.read_sql_query("SELECT * FROM trades", conn)
    conn.close()

    if df.empty:
        update.message.reply_text('No trades to export.')
        return

    # Export to CSV
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    update.message.reply_document(document=csv_buffer, filename='trading_journal.csv',
                                  caption='Your trading journal data in CSV format')

    # Export to Excel
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Trades', index=False)
    excel_buffer.seek(0)
    update.message.reply_document(document=excel_buffer, filename='trading_journal.xlsx',
                                  caption='Your trading journal data in Excel format')

def main() -> None:
    updater = Updater(TOKEN)

    """Run the bot."""
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('newentry', new_entry)],
        states={
            PAIR: [MessageHandler(Filters.text & ~Filters.command, pair)],
            POSITION: [MessageHandler(Filters.regex('^(Long|Short)$'), position)],
            ENTRY_PRICE: [MessageHandler(Filters.text & ~Filters.command, entry_price)],
            TAKE_PROFIT: [MessageHandler(Filters.text & ~Filters.command, take_profit)],
            STOP_LOSS: [MessageHandler(Filters.text & ~Filters.command, stop_loss)],
            RISK_REWARD: [MessageHandler(Filters.text & ~Filters.command, risk_reward)],
            RISK_AMOUNT: [MessageHandler(Filters.text & ~Filters.command, risk_amount)],
            LOT_SIZE: [MessageHandler(Filters.text & ~Filters.command, lot_size)],
            DATE_TIME: [MessageHandler(Filters.text & ~Filters.command, date_time)],
            SESSION: [MessageHandler(Filters.regex('^(Asia|London|NY am|NY pm)$'), session)],
            ANALYSIS: [MessageHandler(Filters.text & ~Filters.command, analysis)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("history", history))
    dp.add_handler(CommandHandler("report", report))
    dp.add_handler(CommandHandler("chart", chart))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(CommandHandler("export", export_data))
    dp.add_handler(MessageHandler(Filters.regex("^(Long|Short)$"), position))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()