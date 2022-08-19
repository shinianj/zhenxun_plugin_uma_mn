import os

from nonebot import on_command,on_regex
from utils.image_utils import BuildImage
from utils.message_builder import image
from nonebot.adapters.onebot.v11 import  GroupMessageEvent,Message,MessageEvent,MessageSegment
from nonebot.permission import SUPERUSER
from typing import Optional, Tuple, Any
from nonebot.params import CommandArg, ArgStr, RegexGroup
#from hoshino import Service, priv
from .face import update_info, get_face_uma, get_face_id, get_face_random, get_mean_id, get_mean_uma

__zx_plugin_name__="马娘表情包"
__plugin_usage__="""
usage:
    指令：
    马娘表情包帮助（请使用该指令查看完全使用方法）
    手动更新马娘表情包(超级用户)
""".strip()
__plugin_des__ = "马娘表情包"
__plugin_cmd__ = ["马娘表情包"]
__plugin_type__ = ("群内功能",)
__plugin_version__ = 0.1
__plugin_author__ = "azmiao （原作者） 十年（真寻适配）"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["群内功能"]

}

sv_help_ = on_command('马娘表情包帮助',priority=5, block=True)
sv = on_regex(r'^(\S{1,10})表情包$',priority=5, block=True)
sv_search = on_command('查表情包含义',aliases={'查表情包含义'},priority=5, block=True)
update = on_command('手动更新马娘表情包',priority=5, permission=SUPERUSER,block=True)

@sv_help_.handle()
async def get_help():
    img_path = os.path.join(os.path.dirname(__file__), f'uma_face_help.png')
    sv_help = f'{os.path.abspath(img_path)}'
    async def n() -> str:
        sv = BuildImage(0,0,background=sv_help)
        return sv.pic2bs4() 
    await sv_help_.finish(image(b64=await n()))

# 支持1到10个字符的马娘名字
@sv.handle()
async def get_umaface(ev: Tuple[Any, ...] = RegexGroup()):
    uma_name_tmp = ev[0]
    if uma_name_tmp == '马娘':
        msg = await get_face_random()
    elif uma_name_tmp.endswith('号'):
        try:
            id = int(uma_name_tmp.replace('号', ''))
        except:
            id = 0
            return
        msg = await get_face_id(str(id+100000))
    else:
        msg = await get_face_uma(uma_name_tmp)
        if not msg:
            return
    await sv.send(msg)

@sv_search.handle()
async def check_meanings(ev: Message = CommandArg()):
    uma_name_tmp = ev.extract_plain_text().strip()
    if uma_name_tmp.endswith('号'):
        try:
            id = int(uma_name_tmp.replace('号', ''))
        except:
            id = 0
            return
        msg = await get_mean_id(str(id+100000))
    else:
        msg = await get_mean_uma(uma_name_tmp)
        if not msg:
            return
    await sv_search.send(msg)

# 手动更新，已存在图片的话会自动跳过
@update.handle()
async def force_update():
    await update_info()
    await update.send('马娘表情包更新完成')