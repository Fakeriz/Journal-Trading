import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define conversation states
PAIR, POSITION, ENTRY_PRICE, TAKE_PROFIT, STOP_LOSS, RISK_REWARD, RISK_AMOUNT, LOT_SIZE, DATE_TIME, SESSION, ANALYSIS = range(11)

# Mock database (replace with actual database in production)
trades = []

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_text(f'Hi {user.first_name}! Welcome to your Trading Journal Bot. '
                              f'Use /newentry to log a new trade, /history to view your trades, '
                              f'and /report to get a performance summary.')

def new_entry(update: Update, context: CallbackContext) -> int:
    """Start the new entry conversation."""
    update.message.reply_text('Let\'s log a new trade. What\'s the trading pair?')
    return PAIR

def pair(update: Update, context: CallbackContext) -> int:
    context.user_data['pair'] = update.message.text
    reply_keyboard = [['Long', 'Short']]
    update.message.reply_text('Is this a Long or Short position?',
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
    context.user_data['risk_reward'] = float(update.message.text.replace('$', '').strip())
    update.message.reply_text('How much are you risking?')
    return RISK_AMOUNT

def risk_amount(update: Update, context: CallbackContext) -> int:
    context.user_data['risk_amount'] = float(update.message.text)
    update.message.reply_text('What\'s the lot size?')
    return LOT_SIZE

def lot_size(update: Update, context: CallbackContext) -> int:
    context.user_data['lot_size'] = float(update.message.text)
    update.message.reply_text('What\'s the date and time of entry? (YYYY-MM-DD HH:MM)')
    return DATE_TIME

def date_time(update: Update, context: CallbackContext) -> int:
    context.user_data['date_time'] = update.message.text
    reply_keyboard = [['Asia', 'Europe', 'US']]
    update.message.reply_text('Which session is this trade in?',
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return SESSION

def session(update: Update, context: CallbackContext) -> int:
    context.user_data['session'] = update.message.text
    update.message.reply_text('Please provide a brief analysis for this trade.', reply_markup=ReplyKeyboardRemove())
    return ANALYSIS

def analysis(update: Update, context: CallbackContext) -> int:
    context.user_data['analysis'] = update.message.text
    
    # Save the trade to our mock database
    trades.append(context.user_data.copy())
    
    # Prepare a summary of the trade
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
    """Cancels and ends the conversation."""
    update.message.reply_text('Trade logging cancelled.', reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

def history(update: Update, context: CallbackContext) -> None:
    """Display trade history."""
    if not trades:
        update.message.reply_text('No trades logged yet.')
        return

    history_text = "Your Trade History:\n\n"
    for i, trade in enumerate(trades[-5:], 1):  # Show last 5 trades
        history_text += f"{i}. {trade['pair']} - {trade['position']} @ {trade['entry_price']}\n"
    
    update.message.reply_text(history_text)

def report(update: Update, context: CallbackContext) -> None:
    """Generate a simple performance report."""
    if not trades:
        update.message.reply_text('No trades logged yet.')
        return

    total_trades = len(trades)
    total_risk = sum(trade['risk_amount'] for trade in trades)
    
    report_text = f"Performance Report:\n\n" \
                  f"Total Trades: {total_trades}\n" \
                  f"Total Risk: ${total_risk}\n" \
                  f"Average Risk per Trade: ${total_risk / total_trades:.2f}"
    
    update.message.reply_text(report_text)

def main() -> None:
    """Run the bot."""
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    updater = Updater("7152456723:AAFBncqooKGVI8XUb2XarTvecOEDVX_yWtU")

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
            SESSION: [MessageHandler(Filters.regex('^(Asia|Europe|US)$'), session)],
            ANALYSIS: [MessageHandler(Filters.text & ~Filters.command, analysis)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("history", history))
    dp.add_handler(CommandHandler("report", report))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
