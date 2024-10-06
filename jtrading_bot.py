import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, CallbackQueryHandler, ContextTypes
from datetime import datetime
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import json
import asyncio
from io import BytesIO

TOKEN = '7152456723:AAFBncqooKGVI8XUb2XarTvecOEDVX_yWtU'

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Menus side panel
async def start(update: Update, context) -> None:
    if not await authenticate(update, context):
        return
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
        [InlineKeyboardButton("Add new trade", callback_data='new_trade')],
        [InlineKeyboardButton("Update trade", callback_data='update_trade')],
        [InlineKeyboardButton("Delete trade", callback_data='delete_trade')],
        [InlineKeyboardButton("View trades", callback_data='view_trades')],
        [InlineKeyboardButton("Analyze performance", callback_data='analyze')],
        [InlineKeyboardButton("Set reminder", callback_data='set_reminder')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Welcome to the Trading Bot! Please choose an option:', reply_markup=reply_markup)

async def button(update: Update, context) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data == 'new_trade':
        await query.edit_message_text(text="Please enter trade details in the format: symbol,entry_price,quantity")
        context.user_data['next_handler'] = 'add_trade'
    elif query.data == 'update_trade':
        await query.edit_message_text(text="Please enter trade ID and updated details: trade_id,exit_price,exit_date")
        context.user_data['next_handler'] = 'update_trade'
    elif query.data == 'delete_trade':
        await query.edit_message_text(text="Please enter the trade ID to delete")
        context.user_data['next_handler'] = 'delete_trade'
    elif query.data == 'view_trades':
        await view_trades(update, context)
    elif query.data == 'analyze':
        await analyze_performance(update, context)
    elif query.data == 'set_reminder':
        await query.edit_message_text(text="Please enter reminder details: symbol,target_price")
        context.user_data['next_handler'] = 'set_reminder'

async def handle_message(update: Update, context) -> None:
    if not await authenticate(update, context):
        return
    next_handler = context.user_data.get('next_handler')
    if next_handler == 'add_trade':
        await add_trade(update, context)
    elif next_handler == 'update_trade':
        await update_trade(update, context)
    elif next_handler == 'delete_trade':
        await delete_trade(update, context)
    elif next_handler == 'set_reminder':
        await set_reminder(update, context)
    else:
        await update.message.reply_text("I'm not sure what you want to do. Please use the menu options.")

# ... (other functions like add_trade, update_trade, delete_trade, view_trades, analyze_performance remain the same)

# Define conversation states
PAIR, POSITION, ENTRY_PRICE, TAKE_PROFIT, STOP_LOSS, RISK_REWARD, RISK_AMOUNT, LOT_SIZE, DATE_TIME, SESSION, ANALYSIS = range(11)

# User authentication
async def authenticate(update: Update, context) -> bool:
    user_id = update.effective_user.id
    conn = sqlite3.connect('trading_bot.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return True
    else:
        await update.message.reply_text("Please register first using /register command.")
        return False

async def register(update: Update, context) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username
    conn = sqlite3.connect('trading_bot.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()
    await update.message.reply_text("Registration successful!")

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
    update.message.reply_text(f'Let\'s log a new trade. What\'s the trading pair?\n\n'
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

# Update 1.0
async def add_trade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    trade_data = update.message.text.split(',')
    if len(trade_data) != 3:
        await update.message.reply_text("Invalid format. Please use: symbol,entry_price,quantity")
        return
    symbol, entry_price, quantity = trade_data
    entry_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect('trading_bot.db')
    c = conn.cursor()
    c.execute("INSERT INTO trades (user_id, symbol, entry_price, quantity, entry_date) VALUES (?, ?, ?, ?, ?)",
              (user_id, symbol, float(entry_price), float(quantity), entry_date))
    conn.commit()
    conn.close()
    await update.message.reply_text("Trade added successfully!")

async def update_trade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    trade_data = update.message.text.split(',')
    if len(trade_data) != 3:
        await update.message.reply_text("Invalid format. Please use: trade_id,exit_price,exit_date")
        return
    trade_id, exit_price, exit_date = trade_data
    conn = sqlite3.connect('trading_bot.db')
    c = conn.cursor()
    c.execute("UPDATE trades SET exit_price = ?, exit_date = ? WHERE id = ? AND user_id = ?",
              (float(exit_price), exit_date, int(trade_id), user_id))
    conn.commit()
    conn.close()
    await update.message.reply_text("Trade updated successfully!")

async def delete_trade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    trade_id = update.message.text.strip()
    conn = sqlite3.connect('trading_bot.db')
    c = conn.cursor()
    c.execute("DELETE FROM trades WHERE id = ? AND user_id = ?", (int(trade_id), user_id))
    conn.commit()
    conn.close()
    await update.message.reply_text("Trade deleted successfully!")

async def view_trades(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    conn = sqlite3.connect('trading_bot.db')
    c = conn.cursor()
    c.execute("SELECT * FROM trades WHERE user_id = ?", (user_id,))
    trades = c.fetchall()
    conn.close()
    if trades:
        trade_list = "\n".join([f"ID: {trade[0]}, Symbol: {trade[2]}, Entry: {trade[3]}, Exit: {trade[4]}" for trade in trades])
        await update.callback_query.edit_message_text(f"Your trades:\n{trade_list}")
    else:
        await update.callback_query.edit_message_text("You have no trades recorded.")

async def analyze_performance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    conn = sqlite3.connect('trading_bot.db')
    c = conn.cursor()
    c.execute("SELECT * FROM trades WHERE user_id = ? AND exit_price IS NOT NULL", (user_id,))
    closed_trades = c.fetchall()
    conn.close()
    
    if not closed_trades:
        await update.callback_query.edit_message_text("No closed trades to analyze.")
        return
    
    total_profit = sum((trade[4] - trade[3]) * trade[5] for trade in closed_trades)
    win_count = sum(1 for trade in closed_trades if trade[4] > trade[3])
    loss_count = len(closed_trades) - win_count
    win_rate = win_count / len(closed_trades) * 100
    
    analysis = f"Total Profit: ${total_profit:.2f}\n"
    analysis += f"Win Rate: {win_rate:.2f}%\n"
    analysis += f"Total Trades: {len(closed_trades)}\n"
    analysis += f"Wins: {win_count}\n"
    analysis += f"Losses: {loss_count}"
    
    await update.callback_query.edit_message_text(f"Performance Analysis:\n\n{analysis}")

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reminder_data = update.message.text.split(',')
    if len(reminder_data) != 2:
        await update.message.reply_text("Invalid format. Please use: symbol,target_price")
        return
    symbol, target_price = reminder_data
    context.job_queue.run_repeating(check_price, interval=300, first=10,
                                    context={'chat_id': update.effective_chat.id, 'symbol': symbol, 'target_price': float(target_price)})
    await update.message.reply_text(f"Reminder set for {symbol} at ${target_price}")

async def check_price(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    symbol = job.context['symbol']
    target_price = job.context['target_price']
    chat_id = job.context['chat_id']
    
    # Here you would typically fetch the current price from an API
    current_price = 100  # Placeholder value
    
    if current_price >= target_price:
        await context.bot.send_message(chat_id=chat_id, text=f"Alert! {symbol} has reached ${current_price}")
        job.schedule_removal()

#
def main() -> None:
    updater = Updater(TOKEN)

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
    dp.add_handler(CommandHandler("register", register))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()