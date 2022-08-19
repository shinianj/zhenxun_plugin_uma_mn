import shutil
import os

from nonebot.adapters.onebot.v11 import  GroupMessageEvent,Message
from nonebot.params import CommandArg
from utils.utils import scheduler
from nonebot import on_command
from .get_all_info import judge, get_msg, get_almanac_info

__zx_plugin_name__="马娘签到"
__plugin_usage__="""
usage:
    指令：
    马娘签到
""".strip()
__plugin_des__ = "马娘签到"
__plugin_cmd__ = ["马娘签到"]
__plugin_type__ = ("群内功能",)
__plugin_version__ = 0.1
__plugin_author__ = "azmiao （原作者） 十年（真寻适配）"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["群内功能"]

}


sv = on_command('马娘签到',priority=5, block=True)

@sv.handle()
async def get_calendar(event: GroupMessageEvent):
    user_id = event.user_id
    group_id = event.group_id
    is_get = await judge(group_id, user_id)
    if is_get:
        msg = await get_almanac_info(group_id, user_id)
    else:
        msg = await get_msg(group_id, user_id)
    await sv.send(msg,at_sender = True)

# 独立于主服务的自动任务
@scheduler.scheduled_job(
    "cron",
    hour=0,
    minute=0,
)
async def clean_dir():
    current_dir = os.path.join(os.path.dirname(__file__), f'data')
    if os.path.exists(current_dir):
        shutil.rmtree(current_dir)  #删除目录，包括目录下的所有文件
        os.mkdir(current_dir)
    else:
        os.mkdir(current_dir)