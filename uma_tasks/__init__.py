import os
import json


from nonebot import on_command,on_regex
from utils.image_utils import BuildImage
from utils.message_builder import image
from nonebot.adapters.onebot.v11 import  GroupMessageEvent,Message,MessageEvent,MessageSegment
from nonebot.permission import SUPERUSER
from typing import Optional, Tuple, Any
from nonebot.params import CommandArg, ArgStr, RegexGroup
#from hoshino import Service, priv, R
from .update_tasks import del_img, update_info, del_img
from .generate import get_title, get_task_info

__zx_plugin_name__="马娘限时任务"
__plugin_usage__="""
usage:
    指令：
    马娘限时任务帮助（请使用该指令查看完全使用方法）
""".strip()
__plugin_des__ = "马娘限时任务帮助"
__plugin_cmd__ = ["马娘限时任务帮助"]
__plugin_type__ = ("群内功能",)
__plugin_version__ = 0.1
__plugin_author__ = "azmiao （原作者） 十年（真寻适配）"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["群内功能"]

}

current_dir = os.path.join(os.path.dirname(__file__), f'tasks_config.json')

sv_help_ = on_command('马娘限时任务帮助',priority=5, block=True)
sv = on_regex(r'^限时任务(\S{1,3})$',priority=5, block=True)
update = on_command("手动更新限时任务",priority=5, permission=SUPERUSER,block=True)

@sv_help_.handle()
async def get_help():
    img_path = os.path.join(os.path.dirname(__file__), f'uma_tasks_help.png')
    sv_help = f'{os.path.abspath(img_path)}'
    async def n() -> str:
        sv = BuildImage(0,0,background=sv_help)
        return sv.pic2bs4() 
    await sv_help_.finish(image(b64=await n()))

@sv.handle()
async def check_meanings(ev: Tuple[Any, ...] = RegexGroup()):
    task_id = ev[0]
    with open(current_dir, 'r', encoding='UTF-8') as f:
        f_data = json.load(f)
    if task_id == '列表':
        task_list = []
        for task_id_tmp in list(f_data['tasks'].keys()):
            title = f_data['tasks'][task_id_tmp]['title']
            task_list.append(title)
        msg = await get_title(f_data)
        await sv.finish(msg)
    try:
        task_id = int(task_id)
    except:
        return
    number = int(f_data['number'])
    if task_id not in range(1, number+1):
        await sv.finish(ev, f'未找到此编号的限时任务：{task_id}\n目前支持 1-{number}')
    msg = await get_task_info(str(task_id), f_data)
    await sv.send(msg)

# 手动更新本地数据
@update.handle()
async def force_update():
    try:
        await update_info()
        await del_img(os.path.dirname(__file__))
        await update.send('限时任务信息刷新完成')
    except Exception as e:
        await update.send(f'限时任务信息刷新失败：{e}')