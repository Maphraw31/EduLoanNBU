import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
from datetime import datetime, timedelta

TOKEN = "MTM1NjY1MTM4MzI1NTk5MDQ5NA.Gbcrz_.W8n8fjLwU4hCupKvNHQn62y21MMwOJstT6fgjs"
CHANNEL_ID = 1356918369026048091  # ใส่ Channel ID ที่ต้องการให้บอทส่งแจ้งเตือน

# สร้างไฟล์ฐานข้อมูลถ้ายังไม่มี
db_file = "loan_data.json"
if not os.path.exists(db_file):
    with open(db_file, "w") as f:
        json.dump({}, f)

bot = commands.Bot(command_prefix="!")

# โหลดข้อมูลจากไฟล์
def load_data():
    with open(db_file, "r") as f:
        return json.load(f)

# บันทึกข้อมูลลงไฟล์
def save_data(data):
    with open(db_file, "w") as f:
        json.dump(data, f, indent=4)

# 📌 คำนวณดอกเบี้ย (0.52% ต่อสัปดาห์)
def calculate_interest(amount, weeks):
    return round(amount * (0.52 / 100) * weeks, 2)

# 📌 คำสั่งขอกู้เงิน
@bot.command()
async def loan(ctx, amount: int):
    user_id = str(ctx.author.id)
    data = load_data()
    
    if user_id not in data:
        data[user_id] = {"loan": 0, "due_date": None}
    
    data[user_id]["loan"] += amount
    data[user_id]["due_date"] = (datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d")
    save_data(data)
    
    await ctx.send(f"✅ {ctx.author.mention} ได้ทำการกู้เงิน {amount} เครดิต สำเร็จ! (ชำระคืนภายใน 1 สัปดาห์)")

# 📌 คำสั่งคืนเงิน
@bot.command()
async def pay(ctx, amount: int):
    user_id = str(ctx.author.id)
    data = load_data()
    
    if user_id not in data or data[user_id]["loan"] == 0:
        await ctx.send("❌ คุณไม่มีหนี้ที่ต้องชำระ!")
        return
    
    data[user_id]["loan"] -= amount
    if data[user_id]["loan"] <= 0:
        data[user_id]["loan"] = 0
        data[user_id]["due_date"] = None
    save_data(data)
    
    await ctx.send(f"💰 {ctx.author.mention} ได้ชำระเงิน {amount} เครดิต! ยอดคงเหลือ: {data[user_id]['loan']} เครดิต")

# 📌 คำสั่งเช็กยอดหนี้
@bot.command()
async def debt(ctx):
    user_id = str(ctx.author.id)
    data = load_data()
    
    if user_id not in data or data[user_id]["loan"] == 0:
        await ctx.send("✅ คุณไม่มีหนี้ค้างชำระ!")
        return
    
    loan_amount = data[user_id]["loan"]
    due_date = data[user_id]["due_date"]
    await ctx.send(f"📌 {ctx.author.mention} คุณมีหนี้ค้างชำระ {loan_amount} เครดิต (ครบกำหนดวันที่ {due_date})")

# 📌 แจ้งเตือนหนี้ทุกวันอาทิตย์
@tasks.loop(hours=168)  # 168 ชั่วโมง = 7 วัน
async def debt_reminder():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        data = load_data()
        for user_id, info in data.items():
            if info["loan"] > 0:
                user = await bot.fetch_user(int(user_id))
                if user:
                    weeks = (datetime.now() - datetime.strptime(info["due_date"], "%Y-%m-%d")).days // 7
                    interest = calculate_interest(info["loan"], weeks)
                    total_due = info["loan"] + interest
                    await channel.send(f"⏳ {user.mention} กรุณาชำระหนี้ {total_due} เครดิต รวมดอกเบี้ย {interest} เครดิต!")

@bot.event
async def on_ready():
    print(f"✅ บอทออนไลน์: {bot.user}")
    debt_reminder.start()

bot.run(os.getenv('TOKEN'))
