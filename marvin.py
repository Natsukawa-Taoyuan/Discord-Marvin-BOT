import os
import json
import discord
from discord.ext import commands
from discord import app_commands
import datetime
import random
from typing import Optional
from typing import Literal
import aiohttp
from dotenv import load_dotenv
import sys
from discord.ext import tasks  
import re
import time
import requests
from typing import Optional
from discord import app_commands
import marvin_tts 

print("--- 總監的除錯雷達已開啟！ ---")

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN') 


DEV_ID =

def is_owner_only_prefix():
    """給舊版 ! 指令用的開發者檢查 (例如 !sync)"""
    async def predicate(ctx):
        return ctx.author.id in DEV_ID
    return commands.check(predicate)

def is_owner_only_slash():
    """給新版 / 斜線指令用的開發者檢查"""
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id in DEV_ID
    return app_commands.check(predicate)


CONSOLE_CHANNEL_ID = 


UPTIME_KUMA_URL = ""
YT_API_KEYS = os.getenv('YT_API_KEYS', "").split(',')

TW_TIMEZONE = datetime.timezone(datetime.timedelta(hours=8))
current_key_index = 0  
log_buffer = ""


intents = discord.Intents.all()
intents.members = True          
intents.message_content = True  
intents.reactions = True       
intents.voice_states = True     


bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

bot.maintenance_mode = False 

DEFAULT_CONFIG = {
    "enable_role": True, "enable_verify": True, "enable_log": True, 
    "enable_help": True, "enable_welcome": True, "enable_egg": False, 
    "enable_bonk": False, "enable_roll": False, "enable_luck": False, 
    "enable_tag_reply": False, "enable_3am": False, "enable_tools": False, 
    "enable_link_check": False, "enable_photo": False, "enable_weather": False, 
    "enable_earthquake": False, "enable_announce": True, "enable_tips": True, 
    "enable_yt": True, "enable_stats": True, "enable_dynamic": True, "menus": {},
    "enable_antispam": False,
    "antispam_limit": 5,  
    "banned_words": ["free nitro", "discord.gift", "steamcommunity.link", "t.me"]
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")


def get_guild_config(guild_id: int) -> dict:
    """讀取指定伺服器的 settings.json 設定，若無則建立預設值"""
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
            
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = {}

    str_id = str(guild_id)
    if str_id not in data:
        data[str_id] = DEFAULT_CONFIG.copy()
    else:
        for key, value in DEFAULT_CONFIG.items():
            if key not in data[str_id]:
                data[str_id][key] = value
                
    return data[str_id]

def update_guild_config(guild_id: int, key: str, value):
    """更新伺服器的單一設定值並寫入硬碟"""
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = {}
        
    str_id = str(guild_id)
    if str_id not in data:
        data[str_id] = DEFAULT_CONFIG.copy()
    else:
        for k, v in DEFAULT_CONFIG.items():
            if k not in data[str_id]:
                data[str_id][k] = v
        
    data[str_id][key] = value
    
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


async def global_maintenance_check(interaction: discord.Interaction) -> bool:
    """在執行任何指令前，檢查維修狀態"""

    is_maintenance = getattr(bot, "maintenance_mode", False)
    if is_maintenance and interaction.user.id not in DEV_ID:
        await interaction.response.send_message("🛠️ **系統維修中！** 請稍後再試！", ephemeral=True)
        return False
    return True

bot.tree.interaction_check = global_maintenance_check

def is_owner_only_prefix():
    """自訂檢查器：確保只有 DEV_ID 的人能用這個隱藏後門"""
    async def predicate(ctx):
        if ctx.author.id in DEV_ID:
            return True
        return False 
    return commands.check(predicate)

@bot.command(name="resync")
async def resync_command(ctx):
    print(f">>> [系統] 總監 {ctx.author} 下達了強制同步指令！")
    msg = await ctx.send("🔄 正在強制同步斜線指令到本伺服器...")
    try:
        bot.tree.copy_global_to(guild=ctx.guild)
        synced = await bot.tree.sync(guild=ctx.guild)
        
        await msg.edit(content=f"✅ **同步成功！**\n目前伺服器已更新 **{len(synced)}** 個斜線指令。\n\n⚠️ **請現在按下 Ctrl + R 重整 Discord！**")
        print(f">>> [系統] 成功同步 {len(synced)} 個指令。")
    except Exception as e:
        print(f"❌ 同步出錯: {e}")
        await msg.edit(content=f"❌ 同步失敗，錯誤訊息：{e}")

ModuleChoices = Literal[
    "role", "verify", "log", "help", "welcome", 
    "tools", "link_check", "announce", "yt", "stats", "dynamic", "antispam"
]

@bot.tree.command(name="toggle", description="[管理員] 切換伺服器各項功能的開關")
@app_commands.default_permissions(administrator=True) 
async def toggle(interaction: discord.Interaction, module: ModuleChoices):
    mapping = {
        "role": "enable_role",
        "verify": "enable_verify",
        "log": "enable_log",
        "help": "enable_help",
        "welcome": "enable_welcome",
        "tools": "enable_tools",
        "link_check": "enable_link_check",
        "announce": "enable_announce",
        "yt": "enable_yt",
        "stats": "enable_stats",
        "dynamic": "enable_dynamic",
        "antispam": "enable_antispam" 
    }
    
    target_key = mapping.get(module)
    config = get_guild_config(interaction.guild_id)
    
    current_stat = config.get(target_key, DEFAULT_CONFIG.get(target_key, False))
    new_stat = not current_stat 
    
    update_guild_config(interaction.guild_id, target_key, new_stat)
    
    stat_text = "🟢 **已開啟**" if new_stat else "🔴 **已關閉**"
    await interaction.response.send_message(f"{stat_text}：`{module}` 模組功能！")


@bot.tree.command(name="status", description="[管理員] 顯示目前伺服器的功能開關狀態")
@app_commands.default_permissions(administrator=True)
async def status_command(interaction: discord.Interaction):
    config = get_guild_config(interaction.guild_id)
    
    def icon(key): 
        return "🟢" if config.get(key, False) else "🔴"

    embed = discord.Embed(
        title=f"📊 {interaction.guild.name} 系統儀表板", 
        description="輸入 `/toggle [模組名稱]` 來切換開關。",
        color=0xe74c3c  
    )
    
    embed.add_field(name="⚙️ 核心與驗證", value=(
        f"{icon('enable_verify')} **入群驗證** `verify`\n"
        f"{icon('enable_role')} **身分組領取** `role`\n"
        f"{icon('enable_welcome')} **歡迎訊息** `welcome`\n"
        f"{icon('enable_help')} **開放求助** `help`"
    ), inline=True)

    embed.add_field(name="📡 情報與頻道", value=(
        f"{icon('enable_announce')} **公告廣播** `announce`\n"
        f"{icon('enable_yt')} **YouTube通知** `yt`\n"
        f"{icon('enable_stats')} **人數統計** `stats`\n"
        f"{icon('enable_dynamic')} **動態語音** `dynamic`"
    ), inline=True)

    embed.add_field(name="🛡️ 安全與工具", value=(
        f"{icon('enable_log')} **日誌紀錄** `log`\n"
        f"{icon('enable_link_check')} **防禦連結** `link_check`\n"
        f"{icon('enable_antispam')} **防洗版/詐騙** `antispam`\n" 
        f"{icon('enable_tools')} **網站檢查** `tools`"
    ), inline=True)

    embed.set_footer(text=f"🤖 延遲: {round(bot.latency * 1000)}ms | 查詢: {interaction.user.display_name}")
    
    if interaction.guild.icon: 
        embed.set_thumbnail(url=interaction.guild.icon.url)
        
    await interaction.response.send_message(embed=embed)

def dev_only_slash():
    """自訂檢查器：只有 DEV_ID 清單裡的人能執行"""
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id in DEV_ID
    return app_commands.check(predicate)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """捕捉所有 Slash 指令的權限阻擋與錯誤"""
    if isinstance(error, app_commands.MissingPermissions):
        msg = "🔒 **存取被拒！** 朋友，這個開關只有 **伺服器管理員** 才能動喔！"
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
        return

    if isinstance(error, app_commands.CheckFailure):
        msg = "🚫 **權限不足！** 只有我的 **造物主 (開發者)** 才能執行這個指令，朋友！"
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
        return

    print(f"⚠️ [Error] Slash 指令發生未預期錯誤: {error}")
    error_msg = f"❌ 發生內部錯誤：`{error}`\n請通知開發者修復！"
    
    if not interaction.response.is_done():
        await interaction.response.send_message(error_msg, ephemeral=True)
    else:
        await interaction.followup.send(error_msg, ephemeral=True)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return 
    if isinstance(error, commands.CheckFailure):
        await ctx.send("🚫 **權限不足！** 只有造物主可以使用此指令。", delete_after=5)
        return
    print(f"⚠️ [Error] 前綴指令錯誤: {error}")

class ConsoleLogger(object):
    def __init__(self, original_stream):
        self.terminal = original_stream

    def write(self, message):
        global log_buffer
        self.terminal.write(message)
        if message.strip():
            log_buffer += message + "\n"

    def flush(self):
        self.terminal.flush()

sys.stdout = ConsoleLogger(sys.stdout)
sys.stderr = ConsoleLogger(sys.stderr)

class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    @discord.ui.button(label="點擊進行驗證", style=discord.ButtonStyle.green, custom_id="verify_button")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = get_guild_config(interaction.guild_id)
        
        if not config.get("enable_verify", False):
            return await interaction.response.send_message("🔴 驗證系統目前關閉中，請聯繫管理員。", ephemeral=True)

        role_id = config.get("verify_role_id", 0)

        if role_id == 0:
            return await interaction.response.send_message("⚠️ 本伺服器尚未設定驗證身分組，請通知管理員。", ephemeral=True)

        role = interaction.guild.get_role(role_id)
        if not role:
            return await interaction.response.send_message("❌ 找不到身分組 (可能已被刪除)，請通知管理員。", ephemeral=True)

        try:
            if role in interaction.user.roles:
                await interaction.response.send_message("✅ 你已經驗證過了！", ephemeral=True)
            else:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"🎉 驗證成功！已獲得 **{role.name}** 身分。", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ 機器人權限不足 (請檢查機器人身分組是否在「驗證身分組」之上)。", ephemeral=True)

@bot.tree.command(name="set_verify_role", description="[管理員] 設定驗證通過後給予的身分組")
@app_commands.default_permissions(administrator=True) 
async def set_verify_role(interaction: discord.Interaction, role: discord.Role):
    update_guild_config(interaction.guild_id, "verify_role_id", role.id)
    await interaction.response.send_message(f"✅ 已成功將驗證身分組設定為：{role.mention}", ephemeral=True)

@bot.tree.command(name="spawn_verify", description="[管理員] 在當前頻道生成驗證面板")
@app_commands.default_permissions(administrator=True) 
async def spawn_verify(interaction: discord.Interaction):
    config = get_guild_config(interaction.guild_id)
    
    if not config.get("enable_verify", False):
        return await interaction.response.send_message("🔴 請先開啟功能：`/toggle` 選擇 `verify`", ephemeral=True)

    role_id = config.get("verify_role_id")
    if not role_id:
        return await interaction.response.send_message("⚠️ **尚未設定驗證身分組！**\n無法生成面板，請先使用：`/set_verify_role`", ephemeral=True)

    role = interaction.guild.get_role(role_id)
    if not role:
        return await interaction.response.send_message("❌ **設定的身分組似乎不存在 (可能已被刪除)！**\n請重新設定：`/set_verify_role`", ephemeral=True)

    embed = discord.Embed(
        title="🔒 伺服器入群驗證", 
        description="點擊下方按鈕解鎖伺服器權限。", 
        color=0x00ff00
    )
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
        
    msg = await interaction.channel.send(embed=embed, view=VerifyView())
    update_guild_config(interaction.guild_id, "verify_msg_id", msg.id)
    
    await interaction.response.send_message("✅ 驗證面板已成功生成於此頻道！", ephemeral=True)

from typing import Optional
from discord import app_commands 

async def menu_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """動態抓取資料庫裡已經建立的面板名稱，變成下拉選單"""
    config = get_guild_config(interaction.guild_id)
    menus = config.get("menus", {})
    
    choices = [
        app_commands.Choice(name=name, value=name)
        for name in menus.keys() if current.lower() in name.lower()
    ]
    return choices[:25]

@bot.tree.command(name="role_add", description="[管理員] 新增身分組選項到指定面板")
@app_commands.default_permissions(administrator=True)
@app_commands.autocomplete(menu_name=menu_autocomplete) 
async def role_add(
    interaction: discord.Interaction, 
    menu_name: str, 
    emoji: str, 
    role: discord.Role, 
    label: Optional[str] = None
):
    """將身分組資料存入 JSON 設定檔"""
    config = get_guild_config(interaction.guild_id)
    
    if not config.get("enable_role", False):
        return await interaction.response.send_message("🔴 功能未開啟：請先使用 `/toggle` 開啟 `role`", ephemeral=True)

    menus = config.get("menus", {})
    if menu_name not in menus:
        menus[menu_name] = []
    
    display_label = label if label else role.name
    
    new_entry = {"emoji": emoji, "role_id": role.id, "label": display_label}
    
    menus[menu_name] = [item for item in menus[menu_name] if item['emoji'] != emoji]
    menus[menu_name].append(new_entry)
    
    update_guild_config(interaction.guild_id, "menus", menus)
    
    embed = discord.Embed(
        title="✅ 面板設定已更新", 
        description=f"面板：**{menu_name}**\n選項：{emoji} **{display_label}** -> {role.mention}", 
        color=0x00ff00
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="role_spawn", description="[管理員] 在當前頻道生成指定的領取面板")
@app_commands.default_permissions(administrator=True)
@app_commands.autocomplete(menu_name=menu_autocomplete) 
async def role_spawn(interaction: discord.Interaction, menu_name: str):
    """根據 JSON 資料生成按鈕並發送訊息"""
    config = get_guild_config(interaction.guild_id)
    
    if not config.get("enable_role", False):
        return await interaction.response.send_message("🔴 請先開啟功能：`/toggle` 選擇 `role`", ephemeral=True)

    menus = config.get("menus", {})
    role_list = menus.get(menu_name, [])
    
    if not role_list:
        return await interaction.response.send_message(f"⚠️ 面板 `{menu_name}` 裡沒有資料！請先用 `/role_add`。", ephemeral=True)

    view = discord.ui.View(timeout=None)
    desc_text = ""

    for item in role_list:
        rid = item["role_id"]
        lb = item["label"]
        ej = item["emoji"]
        
        desc_text += f"{ej} **{lb}**\n"
        
        button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label=lb,
            emoji=ej,
            custom_id=f"role_toggle:{rid}" 
        )
        view.add_item(button)

    embed = discord.Embed(
        title=f"🎭 身分組補給站 - {menu_name}", 
        description=f"點擊下方按鈕領取或移除身分：\n{'-'*30}\n{desc_text}", 
        color=0xf1c40f
    )
    
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message(f"✅ 已發送面板：**{menu_name}**", ephemeral=True)

@bot.tree.command(name="role_reset", description="[管理員] 清空特定的面板資料")
@app_commands.default_permissions(administrator=True)
@app_commands.autocomplete(menu_name=menu_autocomplete)
async def role_reset(interaction: discord.Interaction, menu_name: str):
    config = get_guild_config(interaction.guild_id)
    menus = config.get("menus", {})
    
    if menu_name in menus:
        del menus[menu_name]
        update_guild_config(interaction.guild_id, "menus", menus)
        await interaction.response.send_message(f"🗑️ 面板 `{menu_name}` 的設定已清除！", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ 找不到面板 `{menu_name}`。", ephemeral=True)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    """監聽所有元件互動 (按鈕、選單)"""
    
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get('custom_id', '')
        
        if custom_id.startswith('role_toggle:'):
            try:
                role_id = int(custom_id.split(':')[1])
                role = interaction.guild.get_role(role_id)
                
                if not role:
                    return await interaction.response.send_message("❌ 找不到該身分組 (可能已被刪除)", ephemeral=True)
                
                if role in interaction.user.roles:
                    await interaction.user.remove_roles(role)
                    await interaction.response.send_message(f"➖ 已移除身分：**{role.name}**", ephemeral=True)
                else:
                    await interaction.user.add_roles(role)
                    await interaction.response.send_message(f"➕ 已獲得身分：**{role.name}**", ephemeral=True)
            
            except discord.Forbidden:
                await interaction.response.send_message("❌ 機器人權限不足，請檢查身分組排序！", ephemeral=True)
            except Exception as e:
                print(f"⚠️ 身分組發放錯誤: {e}")

@bot.listen('on_message')  
async def tts_message_listener(message):  
    if message.author.bot: return

    if message.guild and message.guild.voice_client:
        vc = message.guild.voice_client
        if vc.is_connected() and message.author.voice and message.author.voice.channel == vc.channel:
            bot.loop.create_task(marvin_tts.process_and_play_tts(message, vc))

@bot.tree.command(name="join", description="召喚馬文進入您目前的語音頻道")
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        return await interaction.response.send_message("❌ 您必須先進入一個語音頻道！", ephemeral=True)
    
    await interaction.response.defer()
    
    try:
        channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client
        
        if voice_client: 
            await voice_client.move_to(channel)
        else: 
            await channel.connect()
            
        await interaction.followup.send(f"✅ 馬文已就位：`{channel.name}`。")
    except Exception as e:
        await interaction.followup.send(f"❌ 發生錯誤：{e}")

@bot.tree.command(name="leave", description="讓馬文退出語音頻道")
async def leave(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client:
        await voice_client.disconnect()
        await interaction.response.send_message("👋 播報結束。")
    else:
        await interaction.response.send_message("⚠️ 我不在語音頻道裡喔。", ephemeral=True)

import random
from typing import Optional

async def _send_welcome_card(guild: discord.Guild, member: discord.Member):
    """內部函數：執行歡迎卡片的發送動作"""
    config = get_guild_config(guild.id)
    
    if not config.get("enable_welcome", False):
        return False

    channel_id = config.get("welcome_channel")
    if not channel_id:
        return False

    channel = guild.get_channel(int(channel_id))
    if not channel:
        return False

    welcome_msgs = [
        f"歡迎來到 **{guild.name}**！",
        "野生的新成員出現了！",
        "這裡有一位新朋友！大家快出來接客！",
        "是誰？是誰？喔！原來是新朋友！",
        "好耶！我們又多了一位夥伴！"
    ]
    
    msg_text = random.choice(welcome_msgs)
    
    embed = discord.Embed(
        title=f"🎉 歡迎加入！ {member.display_name}",
        description=f"{msg_text}\n請記得去領取身分組，並詳閱版規喔！",
        color=0x00ff00
    )
    
    if member.display_avatar:
        embed.set_thumbnail(url=member.display_avatar.url)
    
    embed.set_footer(text=f"目前成員數: {len(guild.members)} | ID: {member.id}")
    
    try:
        await channel.send(content=f"嗨！ {member.mention} 👋", embed=embed)
        return True
    except discord.Forbidden:
        print(f"❌ 權限不足！無法在 {channel.name} 發送歡迎訊息。")
        return False

@bot.event
async def on_member_join(member: discord.Member):
    """當新成員加入時觸發"""
    print(f"👀 偵測到成員加入：{member.name}") 
    
    await _send_welcome_card(member.guild, member)

    config = get_guild_config(member.guild.id)
    if config.get("enable_log", False):
        log_channel_id = config.get("log_channel_id")
        if log_channel_id:
            log_channel = member.guild.get_channel(int(log_channel_id))
            if log_channel:
                embed = discord.Embed(
                    title="📥 成員加入", 
                    description=f"{member.mention} ({member.id})", 
                    color=0x2ecc71, 
                    timestamp=datetime.datetime.now(TW_TIMEZONE) 
                )
                if member.display_avatar:
                    embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"目前人數: {len(member.guild.members)}")
                
                try:
                    await log_channel.send(embed=embed)
                except discord.Forbidden:
                    pass 

@bot.tree.command(name="set_welcome", description="[管理員] 設定歡迎訊息發送的頻道")
@app_commands.default_permissions(administrator=True)
async def set_welcome(interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
    """設定歡迎頻道，若未指定則設為當前頻道"""
    target_channel = channel if channel else interaction.channel
    
    update_guild_config(interaction.guild_id, "welcome_channel", target_channel.id)
    update_guild_config(interaction.guild_id, "enable_welcome", True)

    await interaction.response.send_message(
        f"✅ **設定成功！**\n新成員加入時，我將會在 {target_channel.mention} 發送歡迎卡片。",
        ephemeral=True 
    )

@bot.tree.command(name="welcome_test", description="[管理員] 手動測試歡迎卡片發送效果")
@app_commands.default_permissions(administrator=True)
async def welcome_test(interaction: discord.Interaction):
    """測試目前設定的歡迎卡片"""
    success = await _send_welcome_card(interaction.guild, interaction.user)
    
    if success:
        await interaction.response.send_message("✅ 測試卡片已發送！請檢查設定的歡迎頻道。", ephemeral=True)
    else:
        await interaction.response.send_message(
            "❌ 發送失敗。請確認：\n1. 功能已開啟 `/toggle welcome` \n2. 已設定頻道 `/set_welcome` \n3. 機器人具備該頻道權限。", 
            ephemeral=True
        )

@bot.tree.command(name="set_log", description="[管理員] 設定系統日誌與攔截紀錄的發送頻道")
@app_commands.default_permissions(administrator=True)
async def set_log(interaction: discord.Interaction, channel: discord.TextChannel):
    update_guild_config(interaction.guild_id, "log_channel_id", channel.id)
    await interaction.response.send_message(f"✅ 系統日誌頻道已設定為：{channel.mention}", ephemeral=True)

@bot.tree.command(name="ban_word", description="[管理員] 新增伺服器違禁詞 (防詐騙/廣告)")
@app_commands.default_permissions(administrator=True)
async def ban_word(interaction: discord.Interaction, word: str):
    config = get_guild_config(interaction.guild_id)
    banned_list = config.get("banned_words", [])
    
    word_lower = word.lower()
    if word_lower in banned_list:
        return await interaction.response.send_message(f"⚠️ `{word}` 已經在黑名單中了。", ephemeral=True)
        
    banned_list.append(word_lower)
    update_guild_config(interaction.guild_id, "banned_words", banned_list)
    await interaction.response.send_message(f"🚫 已將 `{word}` 加入黑名單！\n(請確認 `/toggle antispam` 已開啟)", ephemeral=True)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return await bot.process_commands(message)

    config = get_guild_config(message.guild.id)
    
    if config.get("enable_antispam", False):
        banned_list = config.get("banned_words", [])
        content_lower = message.content.lower()
        content_cleaned = "".join(filter(str.isalnum, content_lower)) 
        
        trigger_word = next((w for w in banned_list if w in content_lower or w in content_cleaned), None)
        
        limit = config.get("antispam_limit", 0)
        mention_count = len(message.mentions)
        is_mass_mention = limit > 0 and mention_count > limit

        if trigger_word or is_mass_mention:
            try:
                await message.delete()
                reason = f"包含違禁詞 `{trigger_word}`" if trigger_word else f"大量標註 ({mention_count}人)"
                await message.channel.send(f"⚠️ {message.author.mention} 你的訊息已被攔截：{reason}", delete_after=5)
                
                if config.get("enable_log", False):
                    log_id = config.get("log_channel_id")
                    log_ch = message.guild.get_channel(int(log_id)) if log_id else None
                    if log_ch:
                        embed = discord.Embed(
                            title="🛡️ 安全攔截紀錄", 
                            color=0xff0000 if trigger_word else 0xe74c3c,
                            timestamp=datetime.datetime.now(TW_TIMEZONE)
                        )
                        embed.set_author(name=message.author, icon_url=message.author.display_avatar.url if message.author.display_avatar else None)
                        embed.add_field(name="原因", value=reason, inline=True)
                        embed.add_field(name="內容", value=message.content[:1000], inline=False)
                        embed.add_field(name="頻道", value=message.channel.mention, inline=False)
                        await log_ch.send(embed=embed)
            except discord.Forbidden:
                pass
            return

    if config.get("enable_link_check", False):
        if re.findall(r'(https?://[^\s]+)', message.content):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
                    async with session.head(re.findall(r'(https?://[^\s]+)', message.content)[0]) as resp: 
                        await message.add_reaction("✅" if resp.status < 400 else "❌")
            except: 
                await message.add_reaction("💀")

    await bot.process_commands(message)

import asyncio

@bot.tree.command(name="check_link", description="[工具] 檢查網站連結狀態與回應速度")
async def check_link(interaction: discord.Interaction, url: str):
    """(成員可用) 檢查網站連結狀態"""
    config = get_guild_config(interaction.guild_id)
    if not config.get("enable_tools", False): 
        return await interaction.response.send_message("🔒 工具模組未啟用。請請管理員使用 `/toggle tools` 開啟。", ephemeral=True)

    target_url = url if url.startswith("http") else f"http://{url}"
    
    await interaction.response.send_message(f"🔍 正在掃描目標：`{target_url}` ...")

    try:
        start_time = datetime.datetime.now()
        timeout = aiohttp.ClientTimeout(total=5)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(target_url) as resp:
                end_time = datetime.datetime.now()
                latency = (end_time - start_time).total_seconds() * 1000 
                status_code = resp.status
                
                if status_code == 200:
                    status_text, color, desc = "✅ 正常 (OK)", 0x2ecc71, "目標運作正常，訊號良好！"
                elif status_code == 404:
                    status_text, color, desc = "❌ 找不到網頁", 0xe74c3c, "目標已遺失，這可能是一個無效的連結。"
                elif status_code >= 500:
                    status_text, color, desc = "🔥 伺服器錯誤", 0xe67e22, "目標伺服器著火了，這不是你的問題。"
                else:
                    status_text, color, desc = f"⚠️ 其他狀態", 0xf1c40f, "收到非標準訊號，請小心操作。"

                embed = discord.Embed(title="🔗 連結連線測試報告", description=desc, color=color)
                embed.add_field(name="目標網址", value=f"[點擊前往]({target_url})", inline=False)
                embed.add_field(name="狀態碼", value=f"`{status_code} {status_text}`", inline=True)
                embed.add_field(name="回應延遲", value=f"`{latency:.0f} ms`", inline=True)
                embed.set_footer(text=f"測試者: {interaction.user.display_name}")
                
                await interaction.edit_original_response(content="", embed=embed)

    except asyncio.TimeoutError:
        await interaction.edit_original_response(content="❌ **連線超時！** 目標伺服器回應太慢或已離線。")
    except Exception as e:
        await interaction.edit_original_response(content=f"❌ **檢查失敗：** 網址格式錯誤或無法連線。\n錯誤訊息：`{e}`")

@bot.tree.command(name="set_stats", description="[管理員] 設定用於顯示伺服器人數的語音/文字頻道")
@app_commands.default_permissions(administrator=True)
async def set_stats(interaction: discord.Interaction, channel: discord.VoiceChannel): # 限制只能選語音頻道，通常統計都是用語音頻道改名
    """設定要當作「人數看板」的頻道"""
    update_guild_config(interaction.guild_id, "stats_channel_id", channel.id)
    update_guild_config(interaction.guild_id, "enable_stats", True)
    
    await interaction.response.send_message(f"✅ 已將 {channel.mention} 設為人數統計頻道！\n馬文稍後會自動幫它改名！", ephemeral=True)
    await update_guild_stats_channel(interaction.guild)

async def update_guild_stats_channel(guild: discord.Guild):
    """核心邏輯：讀取設定並更新該伺服器的頻道名稱"""
    config = get_guild_config(guild.id) 
    
    if not config.get("enable_stats", False):
        return

    channel_id = config.get("stats_channel_id", 0)
    if not channel_id:
        return

    target_channel = guild.get_channel(int(channel_id))
    
    if target_channel:
        new_name = f"📊 成員數: {guild.member_count}"
        
        if target_channel.name != new_name:
            try:
                await target_channel.edit(name=new_name)
                print(f"✅ [統計更新] {guild.name} 人數變更為: {guild.member_count}")
            except discord.Forbidden:
                print(f"❌ [統計錯誤] 權限不足：無法修改 {guild.name} 的頻道 (請給機器人 Manage Channels 權限)")
            except discord.HTTPException as e:
                if e.status == 429:
                    print(f"⏳ [統計限制] {guild.name} 更新太頻繁，Discord 暫時拒絕請求。")
                else:
                    print(f"⚠️ [統計失敗] {guild.name}: {e}")
    else:
        print(f"⚠️ [統計警告] 找不到頻道 ID {channel_id}，可能已被刪除")

@tasks.loop(minutes=10)
async def stats_tracker():
    """每 10 分鐘自動更新所有伺服器的人數看板"""
    await bot.wait_until_ready()
    
    for guild in bot.guilds:
        await update_guild_stats_channel(guild)
        await asyncio.sleep(1) 

async def _get_yt_subs(yt_channel_id: str):
    """內部函數：使用多金鑰輪替抓取訂閱數"""
    global current_key_index
    
    for _ in range(len(YT_API_KEYS)):
        api_key = YT_API_KEYS[current_key_index]
        url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={yt_channel_id}&key={api_key}"
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "items" in data and len(data["items"]) > 0:
                            return data["items"][0]["statistics"].get("subscriberCount", "0")
                        return None 
                    elif resp.status == 403: 
                        current_key_index = (current_key_index + 1) % len(YT_API_KEYS)
                        continue
                    else:
                        return None
        except:
            return None
    return None

@bot.tree.command(name="yt_add", description="[管理員] 新增 YouTube 頻道追蹤至語音頻道名稱")
@app_commands.default_permissions(administrator=True)
async def yt_add(interaction: discord.Interaction, yt_id: str, channel: discord.VoiceChannel):
    """[YT] 新增追蹤設定"""
    config = get_guild_config(interaction.guild_id)
    yt_list = config.get("yt_list", [])
    
    if any(item["yt_id"] == yt_id for item in yt_list):
        return await interaction.response.send_message("⚠️ 這個頻道已經在追蹤清單中了！", ephemeral=True)

    await interaction.response.defer(ephemeral=True) 
    sub_count = await _get_yt_subs(yt_id)
    if sub_count is None:
        return await interaction.followup.send("❌ 抓取失敗！請檢查 YouTube 頻道 ID 是否正確。")

    yt_list.append({"yt_id": yt_id, "vc_id": channel.id})
    update_guild_config(interaction.guild_id, "yt_list", yt_list)
    update_guild_config(interaction.guild_id, "enable_yt", True)

    try:
        formatted_count = "{:,}".format(int(sub_count))
        await channel.edit(name=f"🔴 訂閱: {formatted_count}")
        await interaction.followup.send(f"✅ **新增成功！**\n已開始追蹤 `{yt_id}` 並更新頻道：{channel.mention}")
    except discord.Forbidden:
        await interaction.followup.send(f"⚠️ 設定已儲存，但馬文權限不足，無法修改頻道名稱。")

@bot.tree.command(name="yt_list", description="[管理員] 查看目前的 YouTube 追蹤清單")
@app_commands.default_permissions(administrator=True)
async def yt_list(interaction: discord.Interaction):
    config = get_guild_config(interaction.guild_id)
    current_list = config.get("yt_list", [])

    if not current_list:
        return await interaction.response.send_message("📺 目前沒有追蹤任何 YouTube 頻道。", ephemeral=True)

    embed = discord.Embed(title="📋 YouTube 追蹤清單", color=0xff0000)
    for item in current_list:
        vc = interaction.guild.get_channel(item["vc_id"])
        vc_name = vc.name if vc else "❌ 已刪除的頻道"
        embed.add_field(name=f"頻道 ID: {item['yt_id']}", value=f"對應頻道: {vc_name}", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="yt_remove", description="[管理員] 移除 YouTube 頻道追蹤")
@app_commands.default_permissions(administrator=True)
async def yt_remove(interaction: discord.Interaction, yt_id: str):
    config = get_guild_config(interaction.guild_id)
    yt_list = config.get("yt_list", [])
    
    new_list = [item for item in yt_list if item["yt_id"] != yt_id]
    if len(new_list) == len(yt_list):
        return await interaction.response.send_message("⚠️ 找不到該 ID 的追蹤紀錄。", ephemeral=True)
        
    update_guild_config(interaction.guild_id, "yt_list", new_list)
    await interaction.response.send_message(f"🗑️ 已移除追蹤：`{yt_id}`", ephemeral=True)

@bot.event
async def on_message_delete(message: discord.Message):
    """監聽訊息刪除事件"""
    if message.author.bot or not message.guild:
        return

    config = get_guild_config(message.guild.id)
    if not config.get("enable_log", False):
        return

    log_id = config.get("log_channel_id")
    if not log_id:
        return

    log_channel = message.guild.get_channel(int(log_id))
    if not log_channel:
        return

    embed = discord.Embed(
        title="🗑️ 訊息被刪除",
        description=f"**發送者:** {message.author.mention}\n**頻道:** {message.channel.mention}",
        color=0xe74c3c, 
        timestamp=datetime.datetime.now(TW_TIMEZONE)
    )
    
    if message.author.display_avatar:
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
    else:
        embed.set_author(name=message.author.display_name)
    
    content = message.content if message.content else "(無文字內容，可能為圖片或附件)"
    embed.add_field(name="訊息內容", value=content[:1024], inline=False) 

    try:
        await log_channel.send(embed=embed)
    except Exception as e:
        print(f"❌ [日誌報錯] 無法發送刪除日誌：{e}")


@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    """監聽訊息編輯事件"""
    if before.author.bot or not before.guild:
        return
        
    if before.content == after.content:
        return

    config = get_guild_config(before.guild.id)
    if not config.get("enable_log", False):
        return

    log_id = config.get("log_channel_id")
    if not log_id:
        return

    log_channel = before.guild.get_channel(int(log_id))
    if not log_channel:
        return

    embed = discord.Embed(
        title="✏️ 訊息被編輯",
        description=f"**發送者:** {before.author.mention}\n**頻道:** {before.channel.mention}\n🔗 [點此跳轉至訊息]({after.jump_url})",
        color=0xf1c40f, 
        timestamp=datetime.datetime.now(TW_TIMEZONE)
    )
    
    if before.author.display_avatar:
        embed.set_author(name=before.author.display_name, icon_url=before.author.display_avatar.url)
    else:
        embed.set_author(name=before.author.display_name)
    
    before_content = before.content if before.content else "(無文字)"
    after_content = after.content if after.content else "(無文字)"
    
    embed.add_field(name="📝 編輯前", value=before_content[:1024], inline=False)
    embed.add_field(name="🆕 編輯後", value=after_content[:1024], inline=False)

    try:
        await log_channel.send(embed=embed)
    except Exception as e:
        print(f"❌ [日誌報錯] 無法發送編輯日誌：{e}")

@tasks.loop(hours=24) 
async def yt_tracker():
    """每 24 小時自動巡邏所有伺服器的 YouTube 訂閱數"""
    await bot.wait_until_ready()
    
    for guild in bot.guilds:
        config = get_guild_config(guild.id)
        if not config.get("enable_yt", False): continue
        
        yt_list = config.get("yt_list", [])
        for item in yt_list:
            sub_count = await _get_yt_subs(item["yt_id"])
            if sub_count:
                vc = guild.get_channel(item["vc_id"])
                if vc:
                    try:
                        formatted_count = "{:,}".format(int(sub_count))
                        new_name = f"🔴 訂閱: {formatted_count}"
                        if vc.name != new_name:
                            await vc.edit(name=new_name)
                            print(f"✅ [YT更新] {guild.name} -> {formatted_count}")
                    except: pass
            await asyncio.sleep(2) 

@stats_tracker.before_loop
async def before_stats():
    await bot.wait_until_ready()
    print("⏳ [系統] 人數統計排程準備就緒...")

@yt_tracker.before_loop
async def before_yt():
    await bot.wait_until_ready()
    print("⏳ [系統] YT 追蹤排程準備就緒...")

@bot.tree.command(name="set_hub", description="[管理員] 設定「創造語音」的大廳頻道")
@app_commands.default_permissions(administrator=True)
async def set_hub(interaction: discord.Interaction, channel: discord.VoiceChannel):
    """設定一個頻道，成員進入後會自動觸發建立新房間"""
    update_guild_config(interaction.guild_id, "dynamic_hub_id", channel.id)
    
    config = get_guild_config(interaction.guild_id)
    if "temp_channels" not in config:
        update_guild_config(interaction.guild_id, "temp_channels", [])
        
    await interaction.response.send_message(f"✅ 動態語音大廳已鎖定為：**{channel.name}**", ephemeral=True)

@bot.event
async def on_voice_state_update(member, before, after):
    voice_client = member.guild.voice_client
    if voice_client and voice_client.channel:
        alive_members = [m for m in voice_client.channel.members if not m.bot]
        
        if len(alive_members) == 0:
            print(f"👋 [語音] {voice_client.channel.name} 已經沒人了，馬文自動下線休息！")
            await voice_client.disconnect()

    if member.bot: return 

    guild_id = member.guild.id
    config = get_guild_config(guild_id)
    
    if config.get("enable_log", False) and before.channel != after.channel:
        log_id = config.get("log_channel_id")
        log_channel = member.guild.get_channel(int(log_id)) if log_id else None
        
        if log_channel:
            now = datetime.datetime.now(TW_TIMEZONE)
            embed = None
            
            if before.channel is None and after.channel is not None:
                embed = discord.Embed(title="🟢 加入語音", description=f"{member.mention} 進入了 **{after.channel.name}**", color=0x2ecc71, timestamp=now)
            elif before.channel is not None and after.channel is None:
                embed = discord.Embed(title="🔴 離開語音", description=f"{member.mention} 離開了 **{before.channel.name}**", color=0xe74c3c, timestamp=now)
            elif before.channel and after.channel and before.channel != after.channel:
                embed = discord.Embed(title="🔵 切換頻道", description=f"{member.mention} 移動：\n**{before.channel.name}** ➡️ **{after.channel.name}**", color=0x3498db, timestamp=now)
            
            if embed:
                embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
                try: await log_channel.send(embed=embed)
                except: pass

    if not config.get("enable_dynamic", False): return

    hub_id = config.get("dynamic_hub_id", 0)
    temp_channels = config.get("temp_channels", [])

    if after.channel and after.channel.id == hub_id:
        try:
            category = after.channel.category
            new_name = f"🔊 {member.display_name} 的房間"
            
            new_ch = await member.guild.create_voice_channel(name=new_name, category=category)
            await new_ch.set_permissions(member, connect=True, manage_channels=True)
            await member.move_to(new_ch)
            
            temp_channels.append(new_ch.id)
            update_guild_config(guild_id, "temp_channels", temp_channels)
            print(f"✨ [動態語音] 已為 {member.name} 建立專屬頻道")
        except Exception as e:
            print(f"❌ 動態語音建立失敗: {e}")

    if before.channel and before.channel.id in temp_channels:
        if len(before.channel.members) == 0:
            try:
                await before.channel.delete()
                temp_channels.remove(before.channel.id)
                update_guild_config(guild_id, "temp_channels", temp_channels)
                print(f"🗑️ [動態語音] 房間已空，自動回收：{before.channel.name}")
            except Exception as e:
                print(f"❌ 動態語音刪除失敗: {e}")

@bot.tree.command(name="set_announce", description="[管理員] 設定公告發布的目標頻道")
@app_commands.default_permissions(administrator=True)
async def set_announce(interaction: discord.Interaction, channel: discord.TextChannel):
    update_guild_config(interaction.guild_id, "announce_channel", channel.id)
    await interaction.response.send_message(f"✅ 公告頻道已鎖定：{channel.mention}", ephemeral=True)

@bot.tree.command(name="set_ping_role", description="[管理員] 設定公告時要自動標註的身分組")
@app_commands.default_permissions(administrator=True)
async def set_ping_role(interaction: discord.Interaction, role: discord.Role):
    update_guild_config(interaction.guild_id, "announce_role_id", role.id)
    await interaction.response.send_message(f"✅ 設定完成！以後公告將自動標註：**{role.name}**", ephemeral=True)

@bot.tree.command(name="announce", description="[管理員] 發送正式公告 (支援圖片)")
@app_commands.default_permissions(administrator=True)
async def announce(
    interaction: discord.Interaction, 
    content: str, 
    image: Optional[discord.Attachment] = None
):
    """發送帶有 Embed 的正式公告"""
    config = get_guild_config(interaction.guild_id)

    if not config.get("enable_announce", False):
        return await interaction.response.send_message("🔒 公告系統關閉中。請先使用 `/toggle announce` 開啟功能。", ephemeral=True)
    
    channel_id = config.get("announce_channel")
    if not channel_id:
        return await interaction.response.send_message("⚠️ 請先設定公告頻道：`/set_announce`", ephemeral=True)
    
    target_channel = interaction.guild.get_channel(int(channel_id))
    if not target_channel:
        return await interaction.response.send_message("❌ 找不到公告頻道！", ephemeral=True)

    ping_role_id = config.get("announce_role_id")
    ping_str = f"<@&{ping_role_id}>" if ping_role_id else ""

    embed = discord.Embed(
        title="📢 重要公告與活動通知",
        description=content.replace("\\n", "\n"), 
        color=0xe67e22,
        timestamp=datetime.datetime.now(TW_TIMEZONE)
    )
    embed.set_footer(text=f"發布者: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

    if image:
        embed.set_image(url=image.url)

    try:
        await target_channel.send(content=ping_str, embed=embed)
        await interaction.response.send_message(f"✅ 已發送公告至 {target_channel.mention}！", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ 發送失敗：{e}", ephemeral=True)

async def global_maintenance_check(interaction: discord.Interaction) -> bool:
    """在執行任何指令前，檢查維修狀態"""
    if getattr(bot, "maintenance_mode", False):
        if interaction.user.id not in DEV_ID:
            await interaction.response.send_message("🛠️ **系統維修中！** 馬文正在進行重要大腦升級，請稍後再試！", ephemeral=True)
            return False
    return True

bot.tree.interaction_check = global_maintenance_check

class MarvinDevConsole(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """安全檢查：指紋辨識"""
        if interaction.user.id not in DEV_ID:
            await interaction.response.send_message("⚠️ **權限拒絕！** 嗶嗶... 你不是總監，請把手從控制台上移開！", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="同步斜線指令", style=discord.ButtonStyle.green, emoji="🔄", custom_id="dev_btn_sync")
    async def btn_sync(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            synced = await bot.tree.sync()
            await interaction.followup.send(f"✅ **同步成功！** 馬文已向 Discord 總部註冊了 **{len(synced)}** 個指令！", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ 同步失敗：{e}", ephemeral=True)

    @discord.ui.button(label="維修模式", style=discord.ButtonStyle.gray, emoji="🛠️", custom_id="dev_btn_maint")
    async def btn_maint(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot.maintenance_mode = not getattr(bot, "maintenance_mode", False)
        if bot.maintenance_mode:
            button.style = discord.ButtonStyle.primary
            await bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name="🛠️ 系統升級維修中"))
            msg = "🟠 **維修模式已開啟！**\n目前已封鎖所有一般成員的指令請求。"
        else:
            button.style = discord.ButtonStyle.gray
            await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="等待指示 📡 | /help"))
            msg = "🟢 **維修模式已關閉！**\n防護罩已解除，系統恢復開放。"
        
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(msg, ephemeral=True)

    @discord.ui.button(label="深度診斷報告", style=discord.ButtonStyle.blurple, emoji="🔬", custom_id="dev_btn_diag")
    async def btn_diag(self, interaction: discord.Interaction, button: discord.ui.Button):
        import inspect
        
        try:
            source = inspect.getsource(get_guild_config)
            save_ver = "✅ JSON 版本" if "json.load" in source else "❌ 記憶體版本"
        except: save_ver = "⚠️ 無法讀取"

        intents_status = "✅ 正常" if bot.intents.members else "❌ 缺失 Member 權限"

        config = get_guild_config(interaction.guild_id)
        yt_count = len(config.get("yt_list", []))

        embed = discord.Embed(title="🔬 馬文核心診斷報告", color=0x3498db)
        embed.add_field(name="📥 存檔系統", value=save_ver, inline=True)
        embed.add_field(name="🛡️ Intents 狀態", value=intents_status, inline=True)
        embed.add_field(name="🤖 延遲 (Ping)", value=f"{round(bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="📺 YT 追蹤清單", value=f"{yt_count} 筆資料", inline=True)
        embed.add_field(name="🔑 API Key 庫", value=f"共 {len(YT_API_KEYS)} 把在輪替", inline=True)
        embed.add_field(name="維修模式", value="🟠 開啟中" if bot.maintenance_mode else "🟢 正常運作", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="路徑與權限測試", style=discord.ButtonStyle.secondary, emoji="📂", custom_id="dev_btn_path")
    async def btn_path(self, interaction: discord.Interaction, button: discord.ui.Button):
        test_file = os.path.join(BASE_DIR, "test_write.txt")
        write_status = "❌ 失敗"
        try:
            with open(test_file, "w", encoding="utf-8") as f: f.write("Marvin Test")
            write_status = "✅ 正常"
            os.remove(test_file)
        except: pass

        msg = (
            f"📂 **資料夾**: `{BASE_DIR}`\n"
            f"⚙️ **設定檔**: `settings.json` ({'✅' if os.path.exists(SETTINGS_FILE) else '❌'})\n"
            f"✍️ **硬碟寫入測試**: {write_status}"
        )
        await interaction.response.send_message(msg, ephemeral=True)

    @discord.ui.button(label="格式化本群設定", style=discord.ButtonStyle.danger, emoji="☢️", custom_id="dev_btn_reset")
    async def btn_reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"☢️ **危險操作確認**\n您確定要重置 **{interaction.guild.name}** 的所有設定嗎？\n請在 **15 秒內**於此頻道輸入 `YES` 執行！", 
            ephemeral=True
        )

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel and m.content == 'YES'

        try:
            msg = await interaction.client.wait_for('message', timeout=15.0, check=check)
            
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    all_data = json.load(f)
            except:
                all_data = {}
                
            all_data[str(interaction.guild_id)] = DEFAULT_CONFIG.copy()
            
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(all_data, f, indent=4, ensure_ascii=False)
            
            await msg.reply("💥 **轟！** 伺服器設定已全數格式化，恢復為原廠預設狀態。")
            
        except asyncio.TimeoutError:
            await interaction.followup.send("⏳ **操作超時！** 格式化程序已自動終止，設定安全無恙。", ephemeral=True)
            
@bot.tree.command(name="dev_panel", description="[開發者] 呼叫總監專屬終端控制台")
@dev_only_slash()
async def dev_panel(interaction: discord.Interaction):
    bot.maintenance_mode = getattr(bot, "maintenance_mode", False)
    embed = discord.Embed(
        title="⚙️ 馬文終端控制台",
        description="總監辛苦了！請選擇維護操作：\n\n🟢 `同步`: 更新 Slash 指令\n🔬 `診斷`: 檢查 Intents 與存檔\n📂 `路徑`: 測試寫入權限\n🛠️ `維修`: 切換全域鎖定",
        color=0x2b2d31
    )
    if bot.user.display_avatar:
        embed.set_thumbnail(url=bot.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed, view=MarvinDevConsole(), ephemeral=True)

@bot.tree.command(name="ping", description="[公用] 測試機器人連線延遲")
async def ping(interaction: discord.Interaction):
    """測試機器人延遲"""
    start = time.perf_counter()
    
    await interaction.response.send_message("🏓 測量中...", ephemeral=True) 
    end = time.perf_counter()
    
    api_lat = round(bot.latency * 1000)
    msg_lat = round((end - start) * 1000)
    
    embed = discord.Embed(title="🏓 Pong!", color=0x2ecc71 if api_lat < 100 else 0xe74c3c)
    embed.add_field(name="API 延遲", value=f"{api_lat} ms")
    embed.add_field(name="回應延遲", value=f"{msg_lat} ms")
    
    await interaction.edit_original_response(content=None, embed=embed)

@tasks.loop(seconds=5)
async def console_sender():
    await bot.wait_until_ready()
    global log_buffer
    if not log_buffer.strip(): return
    channel = bot.get_channel(CONSOLE_CHANNEL_ID)
    if not channel: return
    try:
        msg = f"```ansi\n{log_buffer[-1900:]}\n```"
        log_buffer = "" 
        await channel.send(msg)
    except: pass

@tasks.loop(seconds=60)
async def heartbeat_sender():
    await bot.wait_until_ready()
    if UPTIME_KUMA_URL and "http" in UPTIME_KUMA_URL:
        try: requests.get(UPTIME_KUMA_URL, timeout=10)
        except: pass

class AboutView(discord.ui.View):
    """關於馬文面板專用的超連結按鈕"""
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(label="開發者網頁", url="https://natsukawataoyuan.com/", emoji="🌐"))
        self.add_item(discord.ui.Button(label="伺服器狀態", url="https://status.natsukawataoyuan.com/status/mystatus", emoji="📊"))

@bot.tree.command(name="about", description="[公用] 查看馬文的詳細資訊與服務條款")
async def about(interaction: discord.Interaction):
    """關於馬文"""
    embed = discord.Embed(
        title="ℹ️ 關於馬文 (Marvin)", 
        description="您的 Discord 伺服器自動化戰術小幫手", 
        color=0x9b59b6
    )
    
    embed.add_field(name="👨‍💻 開發者", value="桃源三橘義 (natsukawa0707)", inline=False)
    
    tos = (
        "本機器人為非商業 Side Project，免費提供給有需要的群組使用，旨在提供自動化管理並減輕管理員的負擔。\n\n"
        "🖥️ **部署環境**\n"
        "部署於 Proxmox VE 私有雲環境，提供 24 小時不間斷的自動化服務。\n\n"
        "⚠️ **免責聲明**\n"
        "機器人由開發者單人維護及檢修，**不保證** 100% 穩定或長期提供服務。\n"
        "開發者保有修改功能、退出違規伺服器、發布公告或廣告之權利，恕不另行通知。\n\n"
        "🤝 **功能請求**\n"
        "若群主有功能需求，歡迎直接私訊說明，但開發者保有拒絕或排程之權利。\n\n"
        "✅ **同意條款**\n"
        "使用本機器人即表示同意以上條款，並理解開發者無法提供義務性支援。\n"
        "如有任何建議，歡迎聯絡我，謝謝您的理解及支持！"
    )
    
    embed.add_field(name="📜 服務說明與條款", value=tos, inline=False)
    
    if interaction.user.display_avatar:
        embed.set_footer(text=f"查詢者: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    else:
        embed.set_footer(text=f"查詢者: {interaction.user.display_name}")
        
    await interaction.response.send_message(embed=embed, view=AboutView())

class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="首頁 (Home)", description="回到說明書首頁", emoji="🏠", value="home"),
            discord.SelectOption(label="🎙️ 語音與 TTS", description="語音指令、自動辨識與特殊機制", emoji="🎙️", value="voice_tts"),
            discord.SelectOption(label="🛡️ 防護與權限", description="違禁詞、洗版防護、設定開關", emoji="🛡️", value="security"),
            discord.SelectOption(label="🎉 迎新與身分組", description="歡迎系統、身分組領取面板", emoji="🎉", value="welcome"),
            discord.SelectOption(label="🔊 動態語音系統", description="自動生成語音房間設定", emoji="🔊", value="dynamic_voice"),
            discord.SelectOption(label="📺 追蹤與統計", description="YouTube 通知、伺服器人數", emoji="📺", value="tracker"),
            discord.SelectOption(label="🛠️ 實用工具", description="連結檢查、公告發布、延遲測試", emoji="🛠️", value="tools")
        ]
        super().__init__(placeholder="請選擇您想了解的功能分類...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "home":
            embed = discord.Embed(
                title="📖 馬文 (Marvin) 管理員操作手冊", 
                description="總監/管理員您好！我是本伺服器的全自動戰術小幫手。\n請使用下方的選單來查看我的各項系統設定說明！", 
                color=0x3498db
            )
            embed.add_field(name="✨ 核心特色", value="支援各大廠牌 RAW 檔辨識、專案檔偵測、防洗版機制以及全自動語音報報。", inline=False)
            if bot.user.display_avatar:
                embed.set_thumbnail(url=bot.user.display_avatar.url)
        
        elif self.values[0] == "voice_tts":
            embed = discord.Embed(title="🎙️ 語音與 TTS 系統", color=0x1abc9c)
            embed.add_field(name="指令", value="`/join` - 召喚馬文進入語音頻道\n`/leave` - 讓馬文離開語音頻道", inline=False)
            embed.add_field(name="🔍 自動辨識功能", value=(
                "馬文會自動分析您傳送的附件並唸出類型：\n"
                "📸 **RAW 檔**：精準辨識 Canon, Sony, Nikon, 富士等廠牌\n"
                "🎨 **專案檔**：辨識 PS, PR, AE, Vegas, Blender 等工程檔\n"
                "💻 **程式碼**：辨識 Python, JS, JSON 等多種語言\n"
                "🎬 **多媒體**：自動區分圖片、影片與音檔"
            ), inline=False)
            embed.add_field(name="⚡ 特殊機制", value=(
                "🧤 **防洗版**：過長文字自動截斷並隨機吐槽\n"
                "💰 **炫富攔截**：偵測到電腦配備會觸發隱藏台詞\n"
                "🍃 **自動節能**：語音頻道沒活人時馬文會自動退群"
            ), inline=False)

        elif self.values[0] == "security":
            embed = discord.Embed(title="🛡️ 防護與權限指令", color=0xe74c3c)
            embed.add_field(name="`/toggle [功能]`", value="[管理員] 開啟或關閉伺服器的各項模組", inline=False)
            embed.add_field(name="`/set_log [頻道]`", value="[管理員] 設定系統日誌與攔截紀錄發送頻道", inline=False)
            embed.add_field(name="`/ban_word [詞彙]`", value="[管理員] 新增伺服器專屬的違禁詞", inline=False)

        elif self.values[0] == "welcome":
            embed = discord.Embed(title="🎉 迎新與身分組指令", color=0xf1c40f)
            embed.add_field(name="`/set_welcome [頻道]`", value="[管理員] 設定新成員加入時的歡迎頻道", inline=False)
            embed.add_field(name="`/role_spawn`", value="[管理員] 召喚身分組領取面板", inline=False)
            embed.add_field(name="`/spawn_verify`", value="[管理員] 召喚入群驗證按鈕", inline=False)

        elif self.values[0] == "dynamic_voice":
            embed = discord.Embed(title="🔊 動態語音系統", color=0x2ecc71)
            embed.add_field(name="`/set_hub [語音頻道]`", value="[管理員] 設定觸發動態語音的「大廳頻道」", inline=False)
            embed.add_field(name="💡 運作方式", value="成員進入大廳後，馬文會自動幫他創建專屬房間並賦予管理權，成員離開後房間會自動回收。", inline=False)

        elif self.values[0] == "tracker":
            embed = discord.Embed(title="📺 追蹤與統計指令", color=0x9b59b6)
            embed.add_field(name="`/yt_add [YT_ID] [語音頻道]`", value="[管理員] 將頻道名稱綁定 YouTube 訂閱數", inline=False)
            embed.add_field(name="`/yt_list`", value="[管理員] 查看目前的 YT 追蹤清單", inline=False)
            embed.add_field(name="`/set_stats [語音頻道]`", value="[管理員] 將頻道設為「伺服器總人數」看板", inline=False)

        elif self.values[0] == "tools":
            embed = discord.Embed(title="🛠️ 實用工具指令", color=0x34495e)
            embed.add_field(name="`/check_link [網址]`", value="檢查目標網站是否存活與連線速度", inline=False)
            embed.add_field(name="`/announce [內容] (圖片)`", value="[管理員] 發布帶有美觀排版的正式公告", inline=False)
            embed.add_field(name="`/ping`", value="查看機器人目前的連線延遲", inline=False)
            embed.add_field(name="`/about`", value="查看馬文的詳細資訊與服務條款", inline=False)

        await interaction.response.edit_message(embed=embed)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HelpSelect())

@bot.tree.command(name="help", description="查看馬文的操作手冊與指令列表")
async def help_command(interaction: discord.Interaction):
    """叫出動態說明面板 (依權限顯示不同內容)"""
    
    is_admin = isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator

    if is_admin:
        embed = discord.Embed(
            title="📖 馬文 (Marvin) 管理員操作手冊", 
            description="總監/管理員您好！我是本伺服器的全自動戰術小幫手。\n請使用下方的選單來查看我的各項系統設定說明！", 
            color=0x3498db
        )            
        await interaction.response.send_message(embed=embed, view=HelpView(), ephemeral=True)
        
    else:
        embed = discord.Embed(
            title="📖 馬文 (Marvin) 語音小幫手", 
            description="嗨！我是本伺服器的自動化精靈。\n以下是您可以使用的公開指令：", 
            color=0x1abc9c
        )
        embed.add_field(name="🎙️ 語音廣播 (TTS)", value="`/join` - 召喚我進入您所在的語音頻道\n`/leave` - 讓我下線休息", inline=False)
        embed.add_field(name="🛠️ 一般工具", value="`/ping` - 測試我的反應速度\n`/about` - 查看我的詳細資訊", inline=False)
        embed.add_field(name="✨ 隱藏技能", value="只要我在語音頻道裡，就會自動幫大家唸出聊天室的文字，還能精準辨識大家傳送的圖片、影片、**RAW 檔**與**設計專案檔**喔！", inline=False)
        
        if bot.user.display_avatar:
            embed.set_thumbnail(url=bot.user.display_avatar.url)
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """自動捕捉所有 Slash 指令的錯誤"""
    
    async def safe_reply(msg: str):
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    if isinstance(error, app_commands.MissingPermissions):
        await safe_reply("🔒 **存取被拒！** 朋友，這個開關只有 **伺服器管理員** 才能動喔！")
        return

    if isinstance(error, app_commands.CheckFailure):
        await safe_reply("🚫 **權限不足！** 只有我的 **造物主 (總監)** 才能執行這個指令，朋友！")
        return

    if isinstance(error, app_commands.TransformerError):
        await safe_reply("❌ **格式錯誤！** 朋友，請確認你輸入的參數格式是否正確。")
        return

    command_name = interaction.command.name if interaction.command else "未知指令"
    print(f"⚠️ [錯誤攔截] 執行 /{command_name} 時發生異常: {error}")
    
    import traceback
    traceback.print_exc() 
    
    await safe_reply("❌ **執行失敗！** 發生了未預期的系統錯誤，我已經將報錯紀錄提交給總監了！")

@bot.event
async def on_ready():
    bot.add_view(VerifyView())
    bot.add_view(MarvinDevConsole()) 
    
    if not console_sender.is_running(): console_sender.start()
    if not heartbeat_sender.is_running(): heartbeat_sender.start()
    if 'stats_tracker' in globals() and not stats_tracker.is_running(): stats_tracker.start() 
    if 'yt_tracker' in globals() and not yt_tracker.is_running(): yt_tracker.start()    
    
    print("🔄 正在向 Discord 總部同步斜線指令...")
    try:
        synced = await bot.tree.sync()
        print(f"✅ 同步成功！共計 {len(synced)} 個指令已上線。")
    except Exception as e:
        print(f"❌ 自動同步失敗: {e}")

    print("🔄 正在向 Discord 總部同步斜線指令...")
    try:
        synced = await bot.tree.sync()
        command_names = ", ".join([f"/{cmd.name}" for cmd in synced])
        print(f"✅ 同步成功！共計 {len(synced)} 個指令已上線：\n{command_names}")
    except Exception as e:
        print(f"❌ 自動同步失敗: {e}")

    print("==========================================")
    print(f"🚀 馬文 (Marvin) 核心系統已上線！")
    print(f"🤖 登入身分：{bot.user} (ID: {bot.user.id})")
    print(f"🛡️ 維修模式：{'🟠 開啟中' if getattr(bot, 'maintenance_mode', False) else '🟢 關閉中'}")
    print("==========================================")
    
    presence_text = "🛠️ 系統升級維修中" if getattr(bot, "maintenance_mode", False) else "等待指示 📡 | /help"
    presence_status = discord.Status.dnd if getattr(bot, "maintenance_mode", False) else discord.Status.online
    await bot.change_presence(status=presence_status, activity=discord.Activity(type=discord.ActivityType.listening, name=presence_text))
    
if __name__ == "__main__":
    if not TOKEN:
        print("❌ 嚴重錯誤：找不到 TOKEN！請檢查環境變數設定。")
    else:
        bot.run(TOKEN)