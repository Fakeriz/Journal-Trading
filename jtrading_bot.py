import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, CallbackQueryHandler
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import hashlib
import os

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define conversation states
PAIR, POSITION, ENTRY_PRICE, TAKE_PROFIT, STOP_LOSS, RISK_REWARD, RISK_AMOUNT, LOT_SIZE, DATE_TIME, SESSION, ANALYSIS = range(11)
UPDATE_CHOICE, UPDATE_VALUE = range(2)
AUTH_USERNAME, AUTH_PASSWORD = range(2)

# Database setup
def setup_database():
    conn = sqlite3.connect('trading_journal.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS trades
                 (id INTEGER PRIMARY KEY, pair TEXT, position TEXT, entry_price REAL, 
                 take_profit REAL, stop_loss REAL, risk_reward REAL, risk_amount REAL, 
                 lot_size REAL, date_time TEXT, session TEXT, analysis TEXT, profit_loss REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, 
                 telegram_id INTEGER UNIQUE)''')
    conn.commit()
    conn.close()

setup_database()

# User Authentication
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Let's register you. Please enter a username:")
    return AUTH_USERNAME

def get_username(update: Update, context: CallbackContext) -> int:
    context.user_data['username'] = update.message.text
    update.message.reply_text("Now, please enter a password:")
    return AUTH_PASSWORD

def get_password(update: Update, context: CallbackContext) -> int:
    password = hash_password(update.message.text)
    conn = sqlite3.connect('trading_journal.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, telegram_id) VALUES (?, ?, ?)",
                  (context.user_data['username'], password, update.effective_user.id))
        conn.commit()
        update.message.reply_text("Registration successful! You can now use the bot.")
    except sqlite3.IntegrityError:
        update.message.reply_text("Username already exists. Please try again with a different username.")
    finally:
        conn.close()
    return ConversationHandler.END

def is_authenticated(update: Update):
    conn = sqlite3.connect('trading_journal.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (update.effective_user.id,))
    user = c.fetchone()
    conn.close()
    return user is not None

def authenticate(func):
    def wrapper(update: Update, context: CallbackContext):
        if is_authenticated(update):
            return func(update, context)
        else:
            update.message.reply_text("You need to register first. Use /register to create an account.")
    return wrapper

@authenticate
def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_text(f'Welcome to your Forex Trading Journal Bot, {user.first_name}!\n\n'
                              f'Commands:\n'
                              f'/newentry - Log a new trade\n'
                              f'/updatetrade - Update an existing trade\n'
                              f'/deletetrade - Delete a trade\n'
                              f'/history - View your trade history\n'
                              f'/report - Get a performance report\n'
                              f'/chart - View performance charts\n'
                              f'/export - Export your trade data\n'
                              f'/setreminder - Set a reminder for updating trades')

@authenticate
def new_entry(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Let\'s log a new trade. What\'s the trading pair?')
    return PAIR

# ... (include all other conversation handlers from pair to analysis) ...

@authenticate
def update_trade(update: Update, context: CallbackContext) -> int:
    conn = sqlite3.connect('trading_journal.db')
    df = pd.read_sql_query("SELECT id, pair, date_time FROM trades ORDER BY date_time DESC LIMIT 5", conn)
    conn.close()

    if df.empty:
        update.message.reply_text('No trades to update.')
        return ConversationHandler.END

    context.user_data['trades'] = df.to_dict('records')
    keyboard = [[InlineKeyboardButton(f"{trade['pair']} - {trade['date_time']}", callback_data=str(trade['id']))] 
                for trade in context.user_data['trades']]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Select a trade to update:', reply_markup=reply_markup)
    return UPDATE_CHOICE

def update_trade_choice(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    trade_id = int(query.data)
    context.user_data['current_trade'] = trade_id

    keyboard = [
        [InlineKeyboardButton("Take Profit", callback_data='take_profit'),
         InlineKeyboardButton("Stop Loss", callback_data='stop_loss')],
        [InlineKeyboardButton("Profit/Loss", callback_data='profit_loss')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="What would you like to update?", reply_markup=reply_markup)
    return UPDATE_VALUE

def update_trade_value(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    field = query.data
    context.user_data['update_field'] = field
    query.edit_message_text(text=f"Please enter the new value for {field}:")
    return ConversationHandler.END

def save_update(update: Update, context: CallbackContext) -> int:
    new_value = update.message.text
    trade_id = context.user_data['current_trade']
    field = context.user_data['update_field']

    conn = sqlite3.connect('trading_journal.db')
    c = conn.cursor()
    c.execute(f"UPDATE trades SET {field} = ? WHERE id = ?", (new_value, trade_id))
    conn.commit()
    conn.close()

    update.message.reply_text(f"Trade updated successfully. {field} set to {new_value}")
    return ConversationHandler.END

@authenticate
def delete_trade(update: Update, context: CallbackContext) -> int:
    conn = sqlite3.connect('trading_journal.db')
    df = pd.read_sql_query("SELECT id, pair, date_time FROM trades ORDER BY date_time DESC LIMIT 5", conn)
    conn.close()

    if df.empty:
        update.message.reply_text('No trades to delete.')
        return ConversationHandler.END

    context.user_data['trades'] = df.to_dict('records')
    keyboard = [[InlineKeyboardButton(f"{trade['pair']} - {trade['date_time']}", callback_data=str(trade['id']))] 
                for trade in context.user_data['trades']]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Select a trade to delete:', reply_markup=reply_markup)
    return ConversationHandler.END

def confirm_delete(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    trade_id = int(query.data)

    conn = sqlite3.connect('trading_journal.db')
    c = conn.cursor()
    c.execute("DELETE FROM trades WHERE id = ?", (trade_id,))
    conn.commit()
    conn.close()

    query.edit_message_text(text="Trade deleted successfully.")
    return ConversationHandler.END

@authenticate
def set_reminder(update: Update, context: CallbackContext) -> None:
    # Schedule a job to send a reminder after 24 hours
    context.job_queue.run_once(send_reminder, timedelta(hours=24), context=update.message.chat_id)
    update.message.reply_text('Reminder set! I\'ll remind you to update your trades in 24 hours.')

def send_reminder(context: CallbackContext) -> None:
    job = context.job
    context.bot.send_message(job.context, text='Don\'t forget to update your trades!')

@authenticate
def advanced_report(update: Update, context: CallbackContext) -> None:
    conn = sqlite3.connect('trading_journal.db')
    df = pd.read_sql_query("SELECT * FROM trades", conn)
    conn.close()

    if df.empty:
        update.message.reply_text('No trades logged yet.')
        return

    total_trades = len(df)
    winning_trades = df[df['profit_loss'] > 0]
    losing_trades = df[df['profit_loss'] < 0]
    win_rate = len(winning_trades) / total_trades * 100
    average_win = winning_trades['profit_loss'].mean() if not winning_trades.empty else 0
    average_loss = abs(losing_trades['profit_loss'].mean()) if not losing_trades.empty else 0
    profit_factor = abs(winning_trades['profit_loss'].sum() / losing_trades['profit_loss'].sum()) if not losing_trades.empty else float('inf')
    
    report_text = f"Advanced Performance Report:\n\n" \
                  f"Total Trades: {total_trades}\n" \
                  f"Win Rate: {win_rate:.2f}%\n" \
                  f"Average Win: ${average_win:.2f}\n" \
                  f"Average Loss: ${average_loss:.2f}\n" \
                  f"Profit Factor: {profit_factor:.2f}\n" \
                  f"Total Profit/Loss: ${df['profit_loss'].sum():.2f}"
    
    update.message.reply_text(report_text)

def main() -> None:
    updater = Updater("7152456723:AAFBncqooKGVI8XUb2XarTvecOEDVX_yWtU")

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('newentry', new_entry)],
        states={
            PAIR: [MessageHandler(Filters.text & ~Filters.command, pair)],
            POSITION: [MessageHandler(Filters.regex('^(Long|Short)$'), position)],
            # ... (include all other states)
            ANALYSIS: [MessageHandler(Filters.text & ~Filters.command, analysis)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    update_handler = ConversationHandler(
        entry_points=[CommandHandler('updatetrade', update_trade)],
        states={
            UPDATE_CHOICE: [CallbackQueryHandler(update_trade_choice)],
            UPDATE_VALUE: [CallbackQueryHandler(update_trade_value)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=True  # Ensure this is set to True if you need to track each message
    )

    auth_handler = ConversationHandler(
        entry_points=[CommandHandler('register', register_user)],
        states={
            AUTH_USERNAME: [MessageHandler(Filters.text & ~Filters.command, get_username)],
            AUTH_PASSWORD: [MessageHandler(Filters.text & ~Filters.command, get_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

#
def pair(update: Update, context: CallbackContext) -> int:
    context.user_data['pair'] = update.message.text
    reply_keyboard = [['Long', 'Short']]
    update.message.reply_text('Is this a Long or Short position?',
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return POSITION

def position(update, context):
    user_choice = update.message.text
    if user_choice == "Long":
        update.message.reply_text("Anda memilih posisi Long. Silakan masukkan data trade.")
    elif user_choice == "Short":
        update.message.reply_text("Anda memilih posisi Short. Silakan masukkan data trade.")
    else:
        update.message.reply_text("Posisi tidak valid. Harap pilih antara Long atau Short.")

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

    dp.add_handler(MessageHandler(Filters.regex("^(Long|Short)$"), position))
#

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(conv_handler)
    dp.add_handler(update_handler)
    dp.add_handler(auth_handler)
    dp.add_handler(CommandHandler("history", history))
    dp.add_handler(CommandHandler("report", report))
    dp.add_handler(CommandHandler("advancedreport", advanced_report))
    dp.add_handler(CommandHandler("chart", chart))
    dp.add_handler(CommandHandler("export", export_data))
    dp.add_handler(CommandHandler("deletetrade", delete_trade))
    dp.add_handler(CommandHandler("setreminder", set_reminder))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()