import os

from nonebot import on_command,on_regex
from utils.image_utils import BuildImage
from utils.message_builder import image
from nonebot.adapters.onebot.v11 import  GroupMessageEvent,Message,MessageEvent,MessageSegment
from nonebot.permission import SUPERUSER
from typing import Optional, Tuple, Any
from nonebot.params import CommandArg, ArgStr, RegexGroup

from .get_url import generate_img
from .get_url_tw import generate_img_tw
#from hoshino import Service

__zx_plugin_name__="支援卡节奏榜"
__plugin_usage__="""
usage:
    指令：
    支援卡节奏榜帮助（请使用该指令查看完全使用方法）
""".strip()
__plugin_des__ = "支援卡节奏榜"
__plugin_cmd__ = ["支援卡节奏榜"]
__plugin_type__ = ("群内功能",)
__plugin_version__ = 0.1
__plugin_author__ = "azmiao （原作者） 十年（真寻适配）"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["群内功能"]

}

sv_help_ = on_command('支援卡节奏榜帮助',priority=5, block=True)
sv = on_regex(r'^(台服)?(\S{1,2})卡节奏榜$',priority=5, block=True)

# 帮助界面
@sv_help_.handle()
async def help():
    img_path = os.path.join(os.path.dirname(__file__), f'uma_support_chart_help.png')
    sv_help = f'{os.path.abspath(img_path)}'
    async def n() -> str:
        sv = BuildImage(0,0,background=sv_help)
        return sv.pic2bs4() 
    await sv_help_.finish(image(b64=await n()))

@sv.handle()
async def SSR_speed_chart(ev: Tuple[Any, ...] = RegexGroup()):
    sup_type = ev[1]
    if sup_type not in ['速', '耐', '力', '根', '智', '友人']:
        return
    if not ev[0]:
        msg = await generate_img(sup_type)
    else:
        msg = await generate_img_tw(sup_type)
    await sv.send(msg)