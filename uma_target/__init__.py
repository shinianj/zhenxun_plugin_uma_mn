import os
import json


from nonebot import on_command,on_regex
from utils.image_utils import BuildImage
from utils.message_builder import image
from nonebot.adapters.onebot.v11 import  GroupMessageEvent,Message,MessageEvent,MessageSegment
from nonebot.permission import SUPERUSER
from typing import Optional, Tuple, Any
from nonebot.params import CommandArg, ArgStr, RegexGroup

#from hoshino import Service
from .get_target import get_tar

__zx_plugin_name__="育成目标查询"
__plugin_usage__="""
usage:
    指令：
    育成目标帮助（请使用该指令查看完全使用方法）
""".strip()
__plugin_des__ = "育成目标查询"
__plugin_cmd__ = ["育成目标查询"]
__plugin_type__ = ("群内功能",)
__plugin_version__ = 0.1
__plugin_author__ = "azmiao （原作者） 十年（真寻适配）"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["群内功能"]

}

sv_help_ = on_command('育成目标帮助',priority=5, block=True)
sv = on_command('查目标',priority=5, block=True)

@sv_help_.handle()
async def get_help():
    img_path = os.path.join(os.path.dirname(__file__), f'uma_target_help.png')
    sv_help = f'{os.path.abspath(img_path)}'
    async def n() -> str:
        sv = BuildImage(0,0,background=sv_help)
        return sv.pic2bs4() 
    await sv_help_.finish(image(b64=await n()))

@sv.handle()
async def search_target(ev:Message = CommandArg()):
    uma_name_tmp = str(ev.extract_plain_text().strip()).replace('-f', '')
    is_force = True if str(ev.extract_plain_text().strip()).endswith('-f') else False
    current_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uma_info/config.json')
    with open(current_dir, 'r', encoding = 'UTF-8') as f:
        f_data = json.load(f)
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uma_info/replace_dict.json'), 'r', encoding = 'UTF-8') as af:
        replace_data = json.load(af)
    uma_target = ''
    name_list = list(f_data.keys())
    name_list.remove('current_chara')
    for uma_name in name_list:
        if f_data[uma_name]['category'] == 'umamusume':
            other_name_list = list(replace_data[uma_name])
            if f_data[uma_name]['cn_name']:
                cn_name = f_data[uma_name]['cn_name']
            else:
                continue
            if str(uma_name) == uma_name_tmp or str(cn_name) == uma_name_tmp or\
                str(f_data[uma_name]['jp_name']) == uma_name_tmp or str(uma_name_tmp) in other_name_list:
                try:
                    uma_target = await get_tar(cn_name, is_force)
                except:
                    await sv.finish(f'这只马娘不存在或暂时没有育成目标')
    if not uma_target:
        await sv.finish(f'这只马娘不存在或暂时没有育成目标')
    await sv.send(uma_target)