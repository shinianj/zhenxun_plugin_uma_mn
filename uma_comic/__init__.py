from asyncio.log import logger
import os

from nonebot import on_command
from utils.image_utils import BuildImage
from utils.message_builder import image
from nonebot.params import CommandArg
from utils.utils import scheduler
from nonebot.adapters.onebot.v11 import  GroupMessageEvent,Message,MessageEvent,MessageSegment
from nonebot.permission import SUPERUSER
#from hoshino import Service, priv
from .comic import update_info, get_comic_random, get_comic_id, get_comic_uma

__zx_plugin_name__="马娘漫画"
__plugin_usage__="""
usage:
    指令：
    马娘漫画帮助
    马娘漫画（随机给一个马娘漫画）
    马娘漫画+[数字id]
    示例：马娘漫画 1号
    马娘漫画+[马娘名称]
    示例：马娘漫画 特别周
    手动更新马娘漫画（超级用户）
""".strip()
__plugin_des__ = "马娘漫画"
__plugin_cmd__ = ["马娘漫画"]
__plugin_type__ = ("群内功能",)
__plugin_version__ = 0.1
__plugin_author__ = "azmiao （原作者） 十年（真寻适配）"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["群内功能"]

}

sv_help_ = on_command("马娘漫画帮助",priority=5, block=True)
sv = on_command("马娘漫画",priority=5, block=True)
update = on_command("手动更新马娘漫画",priority=5, permission=SUPERUSER,block=True)

@sv_help_.handle()
async def get_help():
    img_path = os.path.join(os.path.dirname(__file__), f'uma_comic_help.png')
    sv_help = f'{os.path.abspath(img_path)}'
    async def n() -> str:
        sv = BuildImage(0,0,background=sv_help)
        return sv.pic2bs4() 
    await sv_help_.finish(image(b64=await n()))

@sv.handle()
async def check_meanings(event: MessageEvent, arg: Message = CommandArg()):
    uma_name_tmp = arg.extract_plain_text().strip()
    if not uma_name_tmp:
        msg = await get_comic_random()
    elif uma_name_tmp.endswith('号'):
        try:
            id = int(uma_name_tmp.replace('号', ''))
        except:
            id = 0
            return
        msg = await get_comic_id(str(id))
    else:
        msg = await get_comic_uma(uma_name_tmp)
        if not msg:
            return
    await sv.send(msg)

# 手动更新，已存在图片的话会自动跳过
@update.handle()
async def force_update():
    await update_info()
    await update.send('马娘漫画更新完成')

#自动更新漫画
@scheduler.scheduled_job('cron', hour='0', minute='0')
async def update_comic():
    await update_info()
    await update.send('马娘漫画更新完成')
    logger.log('马娘漫画更新完毕')
