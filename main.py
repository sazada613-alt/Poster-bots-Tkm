import asyncio
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ── KEEP-ALIVE İÇİN GEREKLİ KISIM ──
from flask import Flask
from threading import Thread

app_web = Flask(__name__)

@app_web.route('/')
def index():
    return "🤖 Bot çalışıyor!"

def run():
    app_web.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ───────────────────────────────────

# 👤 ADMIN SAZLAMALARY
ADMIN_ID = 7394635812
RUGSAT_BERLEN_ULANYJYLAR = {ADMIN_ID}

# 🗂️ Sessiýa we meýilleşdirilen maglumatlar
ulanyja_sessiýalary = {}
garaşylýan = {}
meýilleşdirilen_postlar = []
öňki_habarlar = {}
duýuru_garaşylýar = False

# 🔧 Esasy menýu klawiaturasy
def esasy_menyu_klawiaturasy():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Reklama Goýmаk", callback_data='reklama')],
        [InlineKeyboardButton("📊 Statistika", callback_data='statistika')],
        [InlineKeyboardButton("📂 Postlarym", callback_data='postlarym')],
        [InlineKeyboardButton("👤 Admin Panel", callback_data='admin_panel')]
    ])

# Admin panel klawiaturasy
def admin_panel_klawiaturasy():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Ulanyja Goş", callback_data='ulanyja_gosh')],
        [InlineKeyboardButton("🗑 Ulanyja Aýyr", callback_data='ulanyja_ayyr')],
        [InlineKeyboardButton("👀 Ulanyjylary Gör", callback_data='ulanyjylary_gor')],
        [InlineKeyboardButton("📢 Ähli Kanallara Duýuru", callback_data='ahli_duyguru')],
        [InlineKeyboardButton("🔙 Yza", callback_data='yza')]
    ])

# 🚀 BaşlamakHandler
async def basla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in RUGSAT_BERLEN_ULANYJYLAR:
        await update.message.reply_text("❌ Bu boty ulanmak üçin rugsat ýok.")
        return

    await update.message.reply_text(
        "👋 Hoş geldiňiz! Aşakdaky menýulardan birini saýlaň:",
        reply_markup=esasy_menyu_klawiaturasy()
    )

# 🤖 Düwme Handler
async def duwme_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in RUGSAT_BERLEN_ULANYJYLAR:
        await query.edit_message_text("❌ Rugsat ýok.")
        return

    data = query.data
    global duýuru_garaşylýar

    # Admin panel funksiýalary
    if data == 'admin_panel':
        if user_id != ADMIN_ID:
            await query.edit_message_text("❌ Admin paneline diňe eýesi girip bilýär!")
            return
        await query.edit_message_text(
            "👑 Admin Panel\nNäme etjek bolýarsyňyz?",
            reply_markup=admin_panel_klawiaturasy()
        )

    elif data == 'ulanyja_gosh':
        if user_id != ADMIN_ID:
            await query.edit_message_text("❌ Rugsat ýok!")
            return
        garaşylýan[user_id] = 'ulanyja_gosh'
        await query.edit_message_text("👤 Goşjak ulanyjyňyzyň ID-sini giriziň:")

    elif data == 'ulanyja_ayyr':
        if user_id != ADMIN_ID:
            await query.edit_message_text("❌ Rugsat ýok!")
            return
        garaşylýan[user_id] = 'ulanyja_ayyr'
        await query.edit_message_text("🗑 Aýyrjak ulanyjyňyzyň ID-sini giriziň:")

    elif data == 'ulanyjylary_gor':
        if user_id != ADMIN_ID:
            await query.edit_message_text("❌ Rugsat ýok!")
            return
        ulanyja_sanaw = "\n".join([f"👤 {uid}" for uid in RUGSAT_BERLEN_ULANYJYLAR])
        await query.edit_message_text(f"👥 Rugsat berlen ulanyjylar:\n{ulanyja_sanaw}")

    elif data == 'ahli_duyguru':
        if user_id != ADMIN_ID:
            await query.edit_message_text("❌ Rugsat ýok!")
            return
        duýuru_garaşylýar = True
        garaşylýan[user_id] = 'duyguru_habary'
        await query.edit_message_text("📢 Ähli kanallara ugratjak duýuruňyzy giriziň:")

    elif data == 'yza':
        await query.edit_message_text(
            "👋 Hoş geldiňiz! Aşakdaky menýulardan birini saýlaň:",
            reply_markup=esasy_menyu_klawiaturasy()
        )

    # Öňki funksiýalar
    elif data == 'reklama':
        await query.edit_message_text(
            "📌 Post görnüşini saýlaň:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🖼 Surat", callback_data='surat'),
                InlineKeyboardButton("✏ Tekst", callback_data='tekst')
            ]])
        )

    elif data in ['surat', 'tekst']:
        ulanyja_sessiýalary[user_id] = {'type': data}
        garaşylýan[user_id] = 'photo' if data == 'surat' else 'text'
        prompt = "🖼 Surat ugradyň:" if data=='surat' else "✍ Tekst giriziň:"
        await query.edit_message_text(prompt)

    elif data == 'statistika':
        kanal_sany = len({p['channel'] for p in meýilleşdirilen_postlar})
        post_sany = len(meýilleşdirilen_postlar)
        await query.edit_message_text(f"📊 Statistika:\n📢 Kanallar: {kanal_sany}\n📬 Postlar: {post_sany}")

    elif data == 'postlarym':
        ulanyja_postlary = [p for p in meýilleşdirilen_postlar if p['user_id']==user_id]
        if not ulanyja_postlary:
            await query.edit_message_text("📭 Siziň postlaryňyz ýok.")
            return
        düwmeler = [
            [InlineKeyboardButton(
                f"{i+1}) {p['channel']} ({'⏸' if p.get('paused') else '▶'})", 
                callback_data=f"post_{i}"
            )] for i,p in enumerate(ulanyja_postlary)
        ]
        await query.edit_message_text("📂 Postlaryňyz:", reply_markup=InlineKeyboardMarkup(düwmeler))

    elif data.startswith('post_'):
        idx = int(data.split('_')[1])
        ulanyja_postlary = [p for p in meýilleşdirilen_postlar if p['user_id']==user_id]
        if idx >= len(ulanyja_postlary): return
        post = ulanyja_postlary[idx]
        hakyky_idx = meýilleşdirilen_postlar.index(post)
        ctrl = [
            InlineKeyboardButton(
                "🗑 Poz", callback_data=f"delete_{hakyky_idx}"
            ),
            InlineKeyboardButton(
                "▶ Dowam et" if post.get('paused') else "⏸ Duruз",
                callback_data=f"toggle_{hakyky_idx}"
            )
        ]
        await query.edit_message_text(
            f"📤 Kanal: {post['channel']}\n🕒 Minut: {post['minute']}\n📆 Gün: {post['day']}\n📮 Ugradylan: {post['sent_count']}\n🔁 Galan: {post['max_count']-post['sent_count']}",
            reply_markup=InlineKeyboardMarkup([ctrl])
        )

    elif data.startswith('delete_'):
        idx = int(data.split('_')[1])
        if idx < len(meýilleşdirilen_postlar):
            meýilleşdirilen_postlar.pop(idx)
        await query.edit_message_text("✅ Post pozuldy.")

    elif data.startswith('toggle_'):
        idx = int(data.split('_')[1])
        if idx < len(meýilleşdirilen_postlar):
            meýilleşdirilen_postlar[idx]['paused'] = not meýilleşdirilen_postlar[idx].get('paused', False)
        await query.edit_message_text("🔄 Ýagdaý üýtgedildi.")

# 💬 Habar Handler
async def habar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    global duýuru_garaşylýar
    
    if user_id not in RUGSAT_BERLEN_ULANYJYLAR: 
        return

    if user_id in garaşylýan:
        ädim = garaşylýan[user_id]

        # Admin funksiýalary
        if ädim == 'ulanyja_gosh':
            if user_id != ADMIN_ID:
                await update.message.reply_text("❌ Rugsat ýok!")
                return
            try:
                goşuljak_id = int(update.message.text.strip())
                RUGSAT_BERLEN_ULANYJYLAR.add(goşuljak_id)
                garaşylýan.pop(user_id)
                await update.message.reply_text(f"✅ Ulanyja {goşuljak_id} goşuldy!")
            except:
                await update.message.reply_text("⚠️ Nädogry ID! San bilen giriziň.")

        elif ädim == 'ulanyja_ayyr':
            if user_id != ADMIN_ID:
                await update.message.reply_text("❌ Rugsat ýok!")
                return
            try:
                aýrylјak_id = int(update.message.text.strip())
                if aýrylјak_id == ADMIN_ID:
                    await update.message.reply_text("❌ Admin özüni aýyryp bilmeýär!")
                    return
                if aýrylјak_id in RUGSAT_BERLEN_ULANYJYLAR:
                    RUGSAT_BERLEN_ULANYJYLAR.remove(aýrylјak_id)
                    await update.message.reply_text(f"✅ Ulanyja {aýrylјak_id} aýyryldy!")
                else:
                    await update.message.reply_text("❌ Bu ulanyja eýýäm ýok!")
                garaşylýan.pop(user_id)
            except:
                await update.message.reply_text("⚠️ Nädogry ID! San bilen giriziň.")

        elif ädim == 'duyguru_habary':
            if user_id != ADMIN_ID:
                await update.message.reply_text("❌ Rugsat ýok!")
                return
            duýuru_teksti = update.message.text
            garaşylýan.pop(user_id)
            duýuru_garaşylýar = False
            
            # Ähli ulanylýan kanallara duýuru ugrat
            kanallar = list(set([p['channel'] for p in meýilleşdirilen_postlar]))
            ugradylan = 0
            
            for kanal in kanallar:
                try:
                    await context.bot.send_message(kanal, f"📢 DUÝURU:\n\n{duýuru_teksti}")
                    ugradylan += 1
                except Exception as e:
                    print(f"Kanala duýuru ugradyp bolmady {kanal}: {e}")
            
            await update.message.reply_text(f"✅ Duýuru {ugradylan} kanala ugradyldy!")

        # Post döretmek üçin öňki funksiýalar
        else:
            sess = ulanyja_sessiýalary.get(user_id, {})
            
            if ädim == 'photo' and update.message.photo:
                sess['photo'] = update.message.photo[-1].file_id
                garaşylýan[user_id] = 'caption'
                await update.message.reply_text("📝 Surata caption giriziň:")

            elif ädim == 'text':
                sess['text'] = update.message.text
                garaşylýan[user_id] = 'minute'
                await update.message.reply_text("🕒 Her näçe minutda ugradylsyn? (mysal: 10)")

            elif ädim == 'caption':
                sess['caption'] = update.message.text
                garaşylýan[user_id] = 'minute'
                await update.message.reply_text("🕒 Her näçe minutda ugradylsyn? (mysal: 10)")

            elif ädim == 'minute':
                try:
                    sess['minute'] = int(update.message.text)
                    garaşylýan[user_id] = 'day'
                    await update.message.reply_text("📅 Näçe gün dowam etsin? (mysal: 2)")
                except:
                    await update.message.reply_text("⚠️ Minuty san bilen giriziň!")

            elif ädim == 'day':
                try:
                    sess['day'] = int(update.message.text)
                    garaşylýan[user_id] = 'channel'
                    await update.message.reply_text("📢 Haýsy kanal? (@username görnüşinde)")
                except:
                    await update.message.reply_text("⚠️ Günü san bilen giriziň!")

            elif ädim == 'channel':
                sess['channel'] = update.message.text.strip()
                garaşylýan.pop(user_id)

                # Post döret
                post = {
                    'user_id': user_id,
                    'type': sess['type'],
                    'minute': sess['minute'],
                    'day': sess['day'],
                    'channel': sess['channel'],
                    'next_time': time.time(),
                    'sent_count': 0,
                    'max_count': (sess['day']*24*60)//sess['minute']
                }
                if sess['type']=='surat':
                    post['photo'], post['caption'] = sess['photo'], sess['caption']
                else:
                    post['text'] = sess['text']
                meýilleşdirilen_postlar.append(post)
                await update.message.reply_text("✅ Post goşuldy, awtomatik ugradylar.")

# ⏰ Meýilleşdiriji
async def meýilleşdiriji(app):
    while True:
        häzirki_wagt = time.time()
        for post in meýilleşdirilen_postlar:
            if post.get('paused') or post['sent_count'] >= post['max_count']: 
                continue
            if häzirki_wagt >= post['next_time']:
                try:
                    if post['channel'] in öňki_habarlar:
                        try:
                            await app.bot.delete_message(post['channel'], öňki_habarlar[post['channel']])
                        except:
                            pass

                    if post['type']=='surat':
                        msg = await app.bot.send_photo(post['channel'], post['photo'], caption=post['caption'])
                    else:
                        msg = await app.bot.send_message(post['channel'], post['text'])

                    öňki_habarlar[post['channel']] = msg.message_id
                    post['sent_count'] += 1
                    post['next_time'] = häzirki_wagt + post['minute']*60
                except Exception as e:
                    print(f"Ugradyp bolmady: {e}")
        await asyncio.sleep(30)

# ✅ Esasy funksiýa
async def main():
    app = ApplicationBuilder().token("7859933993:AAEM7_UfgU1h7j3lEtLCx_f_xRx8Zor1JeU").build()
    app.add_handler(CommandHandler("start", basla))
    app.add_handler(CallbackQueryHandler(duwme_handler))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, habar_handler))
    asyncio.create_task(meýilleşdiriji(app))
    print("🤖 Bot işläp başlady...")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()

    keep_alive()  # web sunucusu başlat
    asyncio.get_event_loop().run_until_complete(main())
                    
