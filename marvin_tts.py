import re
import os
import random
import asyncio
import discord
from gtts import gTTS

PLATFORM_MAP = {
    'youtube.com': 'YouTube影片', 'youtu.be': 'YouTube影片',
    'twitter.com': '推特貼文', 'x.com': 'X平台貼文',
    'instagram.com': 'IG貼文', 'facebook.com': '臉書貼文',
    'fb.watch': '臉書影片', 'tiktok.com': '抖音影片',
    'threads.net': 'Threads貼文', 'twitch.tv': 'Twitch實況',
    'bilibili.com': 'B站影片', 'b23.tv': 'B站影片',
    'forum.gamer.com.tw': '巴哈姆特文章'
}

FILE_TYPE_MAP = {
    '.psd': 'Photoshop專案檔', '.prproj': 'Premiere專案檔', '.aep': 'After Effects專案檔',
    '.ai': 'Illustrator專案檔', '.xd': 'Adobe XD專案檔', '.fig': 'Figma專案檔',
    '.drp': 'DaVinci Resolve專案檔', '.blend': 'Blender專案檔', '.c4d': 'Cinema 4D專案檔',
    '.veg': 'Vegas專案檔', '.lrcat': 'lightroom編目檔', '.xmp': 'lightroom調色檔',
    '.doc': 'Word檔案', '.docx': 'Word檔案', '.rtf': 'Word檔案',
    '.xls': 'Excel檔案', '.xlsx': 'Excel檔案', '.csv': 'CSV表格檔',
    '.ppt': 'PowerPoint簡報', '.pptx': 'PowerPoint簡報', '.pdf': 'PDF文件', '.txt': '文字檔',
    '.py': 'Python程式碼', '.js': 'JavaScript程式碼', '.json': 'JSON設定檔',
    '.html': '網頁檔案', '.css': 'CSS樣式表', '.cpp': 'C++程式碼',
    '.c': 'C語言程式碼', '.cs': 'C#程式碼', '.java': 'Java程式碼',
    '.php': 'PHP程式碼', '.ts': 'TypeScript程式碼', '.sh': 'Shell腳本',
    '.sql': 'SQL檔案', '.bat': '批次檔', '.cmd': '命令腳本', '.ps1': 'PowerShell腳本',
    '.exe': 'Windows執行檔', '.msi': 'Windows安裝檔', '.apk': '安卓安裝檔', 
    '.dmg': 'MacOS安裝檔', '.ipk': 'IOS安裝檔', '.jar': 'Java執行檔'
}

RAW_CAMERA_MAP = {
    '.cr2': 'Canon RAW檔', '.cr3': 'Canon RAW檔', '.crw': 'Canon RAW檔',
    '.nef': 'Nikon RAW檔', '.nrw': 'Nikon RAW檔', '.arw': 'Sony RAW檔', 
    '.srf': 'Sony RAW檔', '.sr2': 'Sony RAW檔', '.raf': '富士 RAW檔',
    '.orf': 'Olympus RAW檔', '.ori': 'Olympus RAW檔', '.rw2': 'Panasonic RAW檔',
    '.pef': 'Pentax RAW檔', '.ptx': 'Pentax RAW檔', '.x3f': 'Sigma RAW檔',
    '.3fr': '哈蘇 RAW檔', '.fff': '哈蘇 RAW檔', '.iiq': 'Phase One RAW檔',
    '.srw': '三星 RAW檔', '.raw': '徠卡或Panasonic RAW檔', '.rwl': '徠卡 RAW檔', 
    '.dng': '通用 DNG RAW檔'
}

PC_KEYWORDS = ['cpu', '主機板', '記憶體', '顯示卡', 'ssd', '硬碟', '電供', '機殼', '水冷', '風冷', 'ram', 'vga']

async def process_and_play_tts(message, voice_client):
    """處理訊息並產生語音播放"""
    try:
        clean_text = re.sub(r'http\S+', '', message.content).strip()
        clean_text = discord.utils.remove_markdown(clean_text).replace("~", "")
        user_name = message.author.display_name 

        is_pc_spec, clean_text = _handle_pc_specs_and_spam(clean_text, user_name)

        url_text = _detect_urls(message.content)

        attachment_text = _analyze_attachments(message.attachments)

        has_special = bool(url_text or attachment_text)
        if is_pc_spec:
            read_text = f"{clean_text} {url_text} {attachment_text}"
        elif has_special:
            read_text = f"{user_name} {clean_text} {url_text} {attachment_text}"
        else:
            read_text = f"{user_name} 說：{clean_text}" if clean_text else ""

        read_text = re.sub(r'\s+', ' ', read_text).strip()

        if read_text:
            print(f"🎙️ 正在產生語音: {read_text}")
            filename = f"tts_{message.id}.mp3"
            
            await asyncio.to_thread(lambda: gTTS(text=read_text, lang='zh-TW').save(filename))
            
            while voice_client.is_playing():
                await asyncio.sleep(0.5)
                
            voice_client.play(
                discord.FFmpegPCMAudio(filename), 
                after=lambda e: os.remove(filename) if os.path.exists(filename) else None
            )

    except Exception as e:
        print(f"⚠️ TTS 發生錯誤: {e}")

def _handle_pc_specs_and_spam(text, user_name):
    """處理炫富偵測與過長文字截斷"""
    lower_text = text.lower()
    matched_count = sum(1 for kw in PC_KEYWORDS if kw in lower_text)
    
    if matched_count >= 3:
        replies = [
            f"ㄟ幹，{user_name}又在炫富",
            f"大家快看，{user_name}又在貼電腦配備，是有多有錢啦",
            f"貼這什麼土豪配備，真想拔走{user_name}的顯卡",
            f"{user_name}的規格太亮了，我的眼睛好痛"
        ]
        return True, random.choice(replies)
        
    if len(text) > 50:
        replies = [
            "⋯⋯字太多了，懶得唸。", "⋯⋯剩下的太長了，我快沒氣了！",
            "⋯⋯後面還有很多字，自己看畫面啦！", "⋯⋯講了一大堆，我不想唸了！",
            "⋯⋯太長不看。", "⋯⋯好了可以了，字太多了。", "⋯⋯後面還有八百字，我先下班囉。"
        ]
        return False, text[:50] + random.choice(replies)
        
    return False, text

def _detect_urls(content):
    """偵測訊息中的網址並回傳播報文字"""
    urls = re.findall(r'http\S+', content)
    if not urls: return ""
    
    detected_platforms = set()
    for url in urls:
        url_lower = url.lower()
        matched = False
        for domain, name in PLATFORM_MAP.items():
            if domain in url_lower:
                detected_platforms.add(name)
                matched = True
                break 
        if not matched: detected_platforms.add("網址")
        
    return "分享了" + "和".join(detected_platforms)

def _analyze_attachments(attachments):
    """分析附件類型並回傳播報文字"""
    if not attachments: return ""
    
    image_exts = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.tiff', '.tif', '.heic', '.heif', '.avif')
    video_exts = ('.mp4', '.mov', '.mkv', '.avi', '.webm', '.mxf', '.flv')
    audio_exts = ('.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac', '.wma') 
    
    has_image = has_video = has_audio = has_file = False
    detected_raws = set()     
    detected_projects = set() 
    detected_codes = set()    
    
    for att in attachments:
        filename = att.filename.lower()
        ext = os.path.splitext(filename)[1]
        
        if ext in RAW_CAMERA_MAP: detected_raws.add(RAW_CAMERA_MAP[ext])
        elif ext in FILE_TYPE_MAP:
             detected_projects.add(FILE_TYPE_MAP[ext])
        elif (att.content_type and 'image/' in att.content_type) or filename.endswith(image_exts): has_image = True
        elif (att.content_type and 'video/' in att.content_type) or filename.endswith(video_exts): has_video = True
        elif (att.content_type and 'audio/' in att.content_type) or filename.endswith(audio_exts): has_audio = True 
        else: has_file = True
        
    actions = []
    for raw_cam in detected_raws: actions.append(f"傳送了{raw_cam}")
    for proj_type in detected_projects: actions.append(f"傳送了{proj_type}")
    for code_lang in detected_codes: actions.append(f"傳送了{code_lang}")
        
    if has_image: actions.append("傳送了圖片")
    if has_video: actions.append("傳送了影片")
    if has_audio: actions.append("傳送了音檔") 
    if has_file: actions.append("傳送了檔案")
    
    return "和".join(actions)