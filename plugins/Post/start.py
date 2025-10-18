from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message, BotCommand
from config import *
from plugins.helper.db import db
import random
import time
from datetime import datetime

# =====================================================================================

@Client.on_message(filters.private & filters.command("start"))
async def start(client, message: Message):
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except:
        pass

    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id)
        total_users = await db.total_users_count()
        await client.send_message(LOG_CHANNEL, LOG_TEXT.format(message.from_user.mention, message.from_user.id, total_users))

    txt = (
        f"> **✨👋🏻 Hey {message.from_user.mention} !!**\n\n"
        f"**Welcome to the Channel Manager Bot!** 🚀\n\n"
        f"• **Manage multiple channels** with ease\n"
        f"• **Auto-posting capabilities**\n"
        f"• **Advanced scheduling features**\n"
        f"• **Bulk messaging tools**\n\n"
        f"*Trusted by 5000+ users worldwide* ✅"
    )
    button = InlineKeyboardMarkup([
        [InlineKeyboardButton('🌟 Premium Features', callback_data='premium_features')],
        [InlineKeyboardButton('📜 About', callback_data='about'), InlineKeyboardButton('🕵🏻‍♀️ Help', callback_data='help')],
        [InlineKeyboardButton('💳 Buy Reels Bundle', callback_data='buy_bundle')]
    ])

    if START_PIC:
        await message.reply_photo(START_PIC, caption=txt, reply_markup=button)
    else:
        await message.reply_text(text=txt, reply_markup=button, disable_web_page_preview=True)

@Client.on_callback_query(filters.regex("premium_features"))
async def premium_features(client: Client, callback_query: CallbackQuery):
    features_text = (
        "**🎁 Premium Reels Bundle - What You Get:**\n\n"
        
        "**📦 Package Includes:**\n"
        "• 150,000+ High-Quality Reels\n"
        "• 50+ Different Categories\n"
        "• 4K/1080p Quality Videos\n"
        "• Regular Monthly Updates\n"
        "• Commercial Use Rights\n\n"
        
        "**✨ Value Breakdown:**\n"
        "• ₹0.0013 per reel (Amazing value!)\n"
        "• Lifetime access to current bundle\n"
        "• Future updates at discounted rates\n"
        "• Premium support priority\n\n"
        
        "**🏆 Why Choose Us?**\n"
        "• 5000+ Satisfied Customers\n"
        "• 24/7 Customer Support\n"
        "• Instant Delivery\n"
        "• Money-Back Guarantee\n"
        "• Trusted Since 2023\n\n"
        
        "**💎 Limited Time Offer:**\n"
        "~~₹499~~ **₹199 ONLY** 🔥\n"
        "*60% DISCOUNT - Save ₹300!*"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Buy Now - ₹199", callback_data="secure_payment")],
        [InlineKeyboardButton("⭐ Customer Reviews", callback_data="testimonials")],
        [InlineKeyboardButton("❓ How It Works", callback_data="how_it_works")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await callback_query.message.edit_text(
        text=features_text,
        reply_markup=buttons,
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex("how_it_works"))
async def how_it_works(client: Client, callback_query: CallbackQuery):
    process_text = (
        "**🔄 How It Works - Simple & Secure**\n\n"
        
        "**Step 1: Secure Payment**\n"
        "• Choose your payment method\n"
        "• Complete secure payment\n"
        "• Get instant confirmation\n\n"
        
        "**Step 2: Instant Delivery**\n"
        "• Receive download links within 5 minutes\n"
        "• Access all 150k+ reels\n"
        "• Organized categories\n\n"
        
        "**Step 3: Start Creating**\n"
        "• Use reels for your content\n"
        "• Grow your social media\n"
        "• Get premium support\n\n"
        
        "**🔒 Security Features:**\n"
        "• Encrypted transactions\n"
        "• Payment protection\n"
        "• Data privacy guaranteed\n"
        "• Secure file delivery\n\n"
        
        "**💰 Money-Back Guarantee:**\n"
        "Not satisfied? Get 100% refund within 7 days!"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Proceed to Payment", callback_data="secure_payment")],
        [InlineKeyboardButton("📞 Contact Support", url="https://t.me/alphaeditorssquad")],
        [InlineKeyboardButton("🔙 Back to Features", callback_data="premium_features")]
    ])
    
    await callback_query.message.edit_text(
        text=process_text,
        reply_markup=buttons,
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex("secure_payment"))
async def secure_payment(client: Client, callback_query: CallbackQuery):
    payment_text = (
        "**🔒 Secure Payment Gateway**\n\n"
        
        "**Product:** 150k+ Mega Reels Bundle\n"
        "**Original Price:** ₹499\n"
        "**Discounted Price:** ₹199 🎉\n"
        "**You Save:** ₹300 (60% OFF)\n\n"
        
        "**✅ What You'll Receive:**\n"
        "• Instant download access\n"
        "• 150,000+ premium reels\n"
        "• Lifetime updates\n"
        "• Commercial license\n"
        "• Premium support\n\n"
        
        "**🛡️ Payment Security:**\n"
        "• 256-bit SSL encryption\n"
        "• Secure payment processing\n        • Money-back guarantee\n"
        "• 5000+ satisfied customers\n\n"
        
        "**📦 Delivery:** Instant (Within 5 minutes)\n"
        "**🔄 Updates:** Free lifetime updates\n"
        "**📞 Support:** 24/7 Priority support\n\n"
        
        "**💳 Payment Methods Available:**\n"
        "• UPI (Google Pay, PhonePe, Paytm)\n"
        "• Credit/Debit Cards\n"
        "• Net Banking\n"
        "• Crypto (BTC/ETH)\n\n"
        
        "*Scan the QR code below or use UPI ID for payment*"
    )
    
    payment_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Pay via UPI", callback_data="upi_payment")],
        [InlineKeyboardButton("💳 Credit/Debit Card", callback_data="card_payment")],
        [InlineKeyboardButton("⭐ See Testimonials", callback_data="testimonials")],
        [InlineKeyboardButton("📞 Need Help?", url="https://t.me/alphaeditorssquad")],
        [InlineKeyboardButton("🔙 Back", callback_data="premium_features")]
    ])
    
    try:
        await callback_query.message.reply_photo(
            photo="payment_qr.jpg",  # Your QR code image
            caption=payment_text,
            reply_markup=payment_buttons
        )
    except Exception as e:
        # Fallback if QR code not available
        backup_text = payment_text + "\n\n**📱 UPI ID:** `yourapi@id`\n**📧 Email:** youremail@domain.com\n\n*Please send payment and forward receipt to @alphaeditorssquad*"
        await callback_query.message.reply_text(
            text=backup_text,
            reply_markup=payment_buttons,
            disable_web_page_preview=True
        )

@Client.on_callback_query(filters.regex("testimonials"))
async def show_testimonials(client: Client, callback_query: CallbackQuery):
    testimonials_text = (
        "**⭐ What Our Customers Say**\n\n"
        
        "**🎯 Rahul Sharma** (@rahul123)\n"
        "*\"Amazing quality! Received all 150k reels within 2 minutes. Best investment for my content creation business!\"*\n⭐️⭐️⭐️⭐️⭐️\n\n"
        
        "**📈 Priya Patel** (@priya_edits)\n"
        "*\"The variety is incredible! My Instagram growth from 2k to 50k followers in 3 months. Worth every rupee!\"*\n⭐️⭐️⭐️⭐️⭐️\n\n"
        
        "**💼 Aditya Kumar** (@adityabusiness)\n"
        "*\"Commercial license helped me serve 20+ clients. The support team is super responsive. Highly recommended!\"*\n⭐️⭐️⭐️⭐️⭐️\n\n"
        
        "**✨ Neha Singh** (@nehacreator)\n"
        "*\"Instant delivery and organized categories saved me 10+ hours weekly. The updates are really valuable!\"*\n⭐️⭐️⭐️⭐️⭐️\n\n"
        
        "**🚀 Customer Statistics:**\n"
        "• 5000+ Happy Customers\n"
        "• 4.9/5 Average Rating\n"
        "• 98% Satisfaction Rate\n"
        "• 24/7 Support Response\n\n"
        
        "*Join our satisfied customer family today!* 🎉"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Buy Now - ₹199", callback_data="secure_payment")],
        [InlineKeyboardButton("📞 Contact Support", url="https://t.me/alphaeditorssquad")],
        [InlineKeyboardButton("🔙 Back", callback_data="premium_features")]
    ])
    
    await callback_query.message.edit_text(
        text=testimonials_text,
        reply_markup=buttons,
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex("upi_payment"))
async def upi_payment(client: Client, callback_query: CallbackQuery):
    upi_text = (
        "**📱 UPI Payment Instructions**\n\n"
        
        "**Step 1:** Send ₹199 to our UPI ID:\n"
        "`yourapi@id`\n\n"
        
        "**Step 2:** After payment, take a screenshot of:\n"
        "• Payment confirmation\n"
        "• Transaction ID\n"
        "• Date & Time\n\n"
        
        "**Step 3:** Forward the screenshot to @alphaeditorssquad\n\n"
        
        "**🕐 Delivery Time:** Within 5 minutes\n"
        "**📦 What You'll Get:** Download links for 150k+ reels\n"
        "**🛡️ Guarantee:** 7-day money-back guarantee\n\n"
        
        "**Need help with payment?** Contact @alphaeditorssquad immediately!"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I've Paid", callback_data="paid_confirmation")],
        [InlineKeyboardButton("📞 Contact Support", url="https://t.me/alphaeditorssquad")],
        [InlineKeyboardButton("🔙 Payment Methods", callback_data="secure_payment")]
    ])
    
    await callback_query.message.edit_text(
        text=upi_text,
        reply_markup=buttons,
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex("card_payment"))
async def card_payment(client: Client, callback_query: CallbackQuery):
    card_text = (
        "**💳 Credit/Debit Card Payment**\n\n"
        
        "**Secure Payment Portal:**\n"
        "We use encrypted payment processing for your safety.\n\n"
        
        "**Instructions:**\n"
        "1. Click the 'Pay Now' button below\n"
        "2. Enter card details securely\n"
        "3. Complete payment of ₹199\n"
        "4. You'll be redirected back here\n"
        "5. Receive instant download links\n\n"
        
        "**Security Features:**\n"
        "• PCI DSS Compliant\n"
        "• 256-bit SSL Encryption\n"
        "• No data stored on our servers\n"
        "• Instant payment confirmation\n\n"
        
        "*Your payment security is our top priority!* 🔒"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Pay Now - ₹199", url="https://yourpaymentlink.com")],  # Replace with actual payment link
        [InlineKeyboardButton("📱 UPI Payment", callback_data="upi_payment")],
        [InlineKeyboardButton("📞 Support", url="https://t.me/alphaeditorssquad")],
        [InlineKeyboardButton("🔙 Back", callback_data="secure_payment")]
    ])
    
    await callback_query.message.edit_text(
        text=card_text,
        reply_markup=buttons,
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex("paid_confirmation"))
async def paid_confirmation(client: Client, callback_query: CallbackQuery):
    confirmation_text = (
        "**✅ Payment Confirmation Received**\n\n"
        
        "**Next Steps:**\n"
        "1. **Forward payment receipt** to @alphaeditorssquad\n"
        "2. **Include your Telegram username** in message\n"
        "3. **Wait for verification** (2-5 minutes)\n"
        "4. **Receive download links** instantly after verification\n\n"
        
        "**🕐 Current Processing Time:** 2-5 minutes\n"
        "**📦 Delivery Method:** Telegram direct message\n"
        "**🛡️ Support:** @alphaeditorssquad (24/7)\n\n"
        
        "**What to expect in your delivery:**\n"
        "• Google Drive/Telegram download links\n"
        "• Category-wise organization\n"
        "• Usage instructions\n"
        "• Premium support access\n\n"
        
        "*Thank you for your purchase! We're processing your order...* ⏳"
    )
    
    # Log the payment attempt
    user = callback_query.from_user
    log_message = f"🤑 PAYMENT ATTEMPT\nUser: {user.mention}\nID: {user.id}\nTime: {datetime.now()}"
    await client.send_message(LOG_CHANNEL, log_message)
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 Contact Support", url="https://t.me/alphaeditorssquad")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
    ])
    
    await callback_query.message.edit_text(
        text=confirmation_text,
        reply_markup=buttons
    )

@Client.on_callback_query(filters.regex("buy_bundle"))
async def buy_bundle(client: Client, callback_query: CallbackQuery):
    # Direct access to premium features from start menu
    await premium_features(client, callback_query)

@Client.on_message(filters.private & filters.command("pay"))
async def pay_command(client: Client, message: Message):
    """
    Enhanced /pay command with trust-building elements
    """
    trust_text = (
        "**🌟 Why Trust Us?**\n\n"
        
        "**🏆 Established Reputation:**\n"
        "• Trusted since 2023\n"
        "• 5000+ satisfied customers\n"
        "• 4.9/5 average rating\n\n"
        
        "**🛡️ Security & Guarantees:**\n"
        "• 7-day money-back guarantee\n"
        "• Secure payment processing\n"
        "• Instant delivery promise\n"
        "• 24/7 customer support\n\n"
        
        "**💼 Business Credentials:**\n"
        "• Registered business\n"
        "• Professional support team\n"
        "• Regular updates & maintenance\n"
        "• Transparent pricing\n\n"
        
        "*Ready to boost your content creation?* 🚀"
    )
    
    trust_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 View Premium Features", callback_data="premium_features")],
        [InlineKeyboardButton("⭐ Customer Reviews", callback_data="testimonials")],
        [InlineKeyboardButton("🔒 Secure Payment", callback_data="secure_payment")],
        [InlineKeyboardButton("📞 Contact Support", url="https://t.me/alphaeditorssquad")]
    ])
    
    await message.reply_text(
        text=trust_text,
        reply_markup=trust_buttons,
        disable_web_page_preview=True
    )

# =====================================================================================
# Set bot commands
@Client.on_message(filters.command("set"))
async def set_commands(client: Client, message: Message):
    await client.set_bot_commands([
        BotCommand("start", "🤖 Start the bot"),
        BotCommand("channels", "📋 List connected channels"),
        BotCommand("pay", "💳 Buy Premium Reels Bundle"),
        BotCommand("features", "🌟 Premium Features"),
        BotCommand("testimonials", "⭐ Customer Reviews"),
    ])
    await message.reply_text("✅ Bot commands have been set.")
