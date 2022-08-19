import os
import asyncio
from socket import MsgFlag

from nonebot.adapters.onebot.v11 import GroupMessageEvent
from utils.message_builder import custom_forward_msg
from configs.config import NICKNAME, Config
from nonebot import on_command,on_regex
from utils.image_utils import BuildImage
from utils.message_builder import image
from nonebot.params import CommandArg
from utils.utils import scheduler,get_bot
from nonebot.adapters.onebot.v11 import  GroupMessageEvent,Message,MessageEvent,MessageSegment
from nonebot.permission import SUPERUSER
from services.log import logger
from utils.image_utils import text2image
from nonebot.adapters.onebot.v11 import Bot,ActionFailed
from typing import Optional, Tuple, Any
from nonebot.params import CommandArg, ArgStr, RegexGroup
#from hoshino import Service, priv
from ._news_white_list import news
from .news_spider import get_news, judge, news_broadcast, sort_news, translate_news
from .news_spider_tw import get_news_tw, judge_tw, news_broadcast_tw

__zx_plugin_name__="马娘新闻"
__plugin_usage__="""
usage:
    指令：
    马娘新闻帮助（请使用该指令查看完全使用方法）
    手动更新马娘漫画（超级用户）
    查看马娘新闻白名单
    (以下操作为当前群操作)
    添加马娘新闻白名单
    恢复马娘新闻白名单
    删除马娘新闻白名单
""".strip()
__plugin_des__ = "马娘新闻"
__plugin_cmd__ = ["马娘新闻"]
__plugin_type__ = ("群内功能",)
__plugin_version__ = 0.1
__plugin_author__ = "azmiao （原作者） 十年（真寻适配）"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["群内功能"]

}

Config.add_plugin_config(
        "MN_NEWS",
        "DEFAULT_MN_NEWS",
        False,
        help_="马娘新闻播报 开关",
        default_value=False,
    )

sv_help_ = on_command("马娘新闻帮助",priority=5, block=True)
sv = on_regex(r'^(台服)?马娘新闻$',priority=5, block=True)
sv_translator = on_command('新闻翻译',priority=5, block=True)
sv_translator_mode = on_command('马娘新闻翻译转发模式',priority=5, block=True)
white = on_command('添加马娘新闻白名单',permission=SUPERUSER,priority=5, block=True)
white_ = on_command('查看马娘新闻白名单',permission=SUPERUSER,priority=5, block=True)
white_del = on_command('删除马娘新闻白名单',permission=SUPERUSER,priority=5, block=True)
white_on = on_command('恢复马娘新闻白名单',permission=SUPERUSER,priority=5, block=True)

# 帮助界面
@sv_help_.handle()
async def help():
    img_path = os.path.join(os.path.dirname(__file__), f'umamusume_news_help.png')
    sv_help = f'{os.path.abspath(img_path)}'
    async def n() -> str:
        sv = BuildImage(0,0,background=sv_help)
        return sv.pic2bs4() 
    await sv_help_.finish(image(b64=await n()))

@white.handle()
async def _(event:GroupMessageEvent):
    if await news.add(event.group_id):
        await white.finish(f'已添加 {event.group_id} 至白名单中')
    await white.finish(f'{event.group_id} 添加至白名单失败,可能是群已存在或输入错误')

@white_del.handle()
async def _(event:GroupMessageEvent):
    if await news.delete(event.group_id):
        await white.finish(f'已删除 {event.group_id} 从白名单中')
    await white.finish(f'{event.group_id} 删除从白名单失败，可能是群未添加或已禁用')

@white_.handle()
async def _(event:GroupMessageEvent):
    w_list = await news.get_info()
    text = '当前马娘新闻白名单\n'
    for g in w_list.keys():
        text += f'{g} : {w_list[g]}\n'
    await white.finish(image(b64=(await text2image(text, color="#f9f6f2", padding=10)).pic2bs4()), at_sender=True)

@white_on.handle()
async def _(event:GroupMessageEvent):
    if await news.on(event.group_id):
        await white.finish(f'已将 {event.group_id} 恢复至白名单中')
    await white.finish(f'{event.group_id} 恢复至白名单失败,可能是群未添加或输入错误或已是开启状态')
    



# 主动获取新闻功能
@sv.handle()
async def uma_news(ev: Tuple[Any, ...] = RegexGroup()):
    try:
        if not ev[0]:
            msg = await get_news()
        else:
            msg = await get_news_tw()
    except:
        msg = '获取新闻失败，请等5分钟后再次尝试'
    await sv.send(msg)

# 马娘新闻播报
@scheduler.scheduled_job('cron', minute='*/5')
async def uma_news_poller():
    if Config.get_config("MN_NEWS", "DEFAULT_MN_NEWS"):
        try:
            flag = await judge()
            if flag:
                logger.info('检测到马娘新闻更新！')
                try:
                    bot = get_bot()
                    #gl = await bot.get_group_list()
                    w_list = await news.get_info()
                    for g in w_list.keys():
                        try:
                            await bot.send_group_msg(group_id=g, message=await news_broadcast())
                        except ActionFailed:
                            logger.warning(f"{g} 群被禁言中，无法发送马娘新闻")
                except Exception as e:
                    logger.error(f"马娘新闻播报错误 e:{e}")
            else:
                logger.info('暂未检测到马娘新闻更新')
                return
        except Exception as e:
            logger.info(f'马娘官网连接失败，具体原因：{e}')

# 台服马娘新闻播报
@scheduler.scheduled_job('cron', minute='*/5')
async def uma_news_poller_tw():
    if Config.get_config("MN_NEWS", "DEFAULT_MN_NEWS"):
        try:
            flag = await judge_tw()
            if flag:
                logger.info('检测到台服马娘新闻更新！')
                try:
                    bot = get_bot()
                    #gl = await bot.get_group_list()
                    #gl = [g["group_id"] for g in gl]
                    w_list = await news.get_info()
                    for g in w_list.keys():
                        try:
                            await bot.send_group_msg(group_id=g, message=await news_broadcast())
                        except ActionFailed:
                            logger.warning(f"{g} 群被禁言中，无法发送马娘新闻（台服）")
                except Exception as e:
                    logger.error(f"马娘新闻播报（台服）错误 e:{e}")
            else:
                logger.info('暂未检测到台服马娘新闻更新')
                return
        except Exception as e:
            logger.info(f'台服马娘官网连接失败，具体原因：{e}')

# 选择翻译新闻
@sv_translator.handle()
async def select_source(bot: Bot,event: GroupMessageEvent, ev: Message = CommandArg()):
    group_id = event.group_id
    self_id = event.user_id
    try:
        news_list = await sort_news()
    except Exception as e:
        msg = f'错误！马娘官网连接失败，原因：{e}'
        await sv_translator.send(msg)
        return
    num_i = 0
    msg_c = '马娘新闻列表：'
    for news in news_list:
        num_i += 1
        msg_c = msg_c + f'\n{num_i}. ' + news.news_title
    alltext = ev.extract_plain_text().strip()
    if alltext not in ['1', '2', '3', '4', '5']:
        msg = '新闻编号错误！(可选值有：1/2/3/4/5)' + '\n\n' + msg_c
        await sv_translator.send(msg)
        return
    news = news_list[int(alltext)-1]
    msg = '正在龟速翻译，请耐心等待...'
    await sv.send(msg)
    news_id = int(news.news_url.replace('▲https://umamusume.jp/news/detail.php?id=', ''))
    await asyncio.sleep(0.5)
    head_img, msg = await translate_news(news_id)
    if msg == '错误！马娘官网连接失败':
        await sv_translator.send('翻译失败，马娘官网连接失败')
        return
    current_dir = os.path.join(os.path.dirname(__file__), 'mode.txt')
    with open(current_dir, 'r', encoding='utf-8') as f:
        mode = f.read().strip()
    if mode == 'off':
        await sv_translator.send(ev, head_img + msg)
        return
    forward_msg = [
        {
            "type": "node",
            "data": {
                "name": "马娘新闻翻译",
                "uin": self_id,
                "content": f'标题：\n{news.news_title}'
            }
        }
    ]
    if head_img:
        forward_msg.append({
            "type": "node",
            "data": {
                "name": "马娘BOT",
                "uin": self_id,
                "content": head_img
            }
        })
    msg_list = [msg[i:i+1000].strip() for i in range(0, len(msg), 1000)]
    for msg_i in msg_list:
        forward_msg.append({
            "type": "node",
            "data": {
                "name": "马娘BOT",
                "uin": self_id,
                "content": msg_i
            }
        })
    await bot.send_group_forward_msg(
            group_id=event.group_id, messages=forward_msg)
        

# 选择模式
@sv_translator_mode.handle()
async def change_mode(ev: Message = CommandArg()):
    mode = ev.extract_plain_text().strip()
    current_dir = os.path.join(os.path.dirname(__file__), 'mode.txt')
    with open(current_dir, 'r', encoding='utf-8') as f:
        mode_tmp = f.read().strip()
    if mode not in ['on', 'off']:
        msg = f'模式选择错误(on/off)，默认on，当前{mode_tmp}'
        await sv_translator_mode.finish(ev, msg)
    with open(current_dir, 'w', encoding='utf-8') as f:
        f.write(mode)
    await sv_translator_mode.send(f'已更换转发模式为{mode}')