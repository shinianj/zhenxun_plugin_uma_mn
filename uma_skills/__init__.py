import os
import json

from nonebot import on_command
from utils.image_utils import BuildImage
from utils.message_builder import image
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import  GroupMessageEvent,Message,MessageEvent,MessageSegment
#from hoshino import Service, priv, R
from .update_skills import del_img, update_info, del_img
from .generate import get_skill_list, get_skill_info

__zx_plugin_name__="马娘技能查询"
__plugin_usage__="""
usage:
    指令：
    马娘技能帮助（请使用该指令查看完全使用方法）
    手动更新马娘技能（超级用户）
""".strip()
__plugin_des__ = "马娘技能查询"
__plugin_cmd__ = ["马娘技能查询"]
__plugin_type__ = ("群内功能",)
__plugin_version__ = 0.1
__plugin_author__ = "azmiao （原作者） 十年（真寻适配）"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["群内功能"]

}



current_dir = os.path.join(os.path.dirname(__file__), f'skills_config.json')

# 分类
rarity = ['普通', '传说', '独特', '普通·继承', '独特·继承', '剧情', '活动']
limit = ['通用', '短距离', '英里', '中距离', '长距离', '泥地', '逃马', '先行', '差行', '追马']
color = ['绿色', '紫色', '黄色', '蓝色', '红色']
skill_type = ['被动（速度）', '被动（耐力）', '被动（力量）', '被动（毅力）', '被动（智力）',
    '耐力恢复', '速度', '加速度', '出闸', '视野', '切换跑道',
    '妨害（速度）', '妨害（加速度）', '妨害（心态）', '妨害（智力）', '妨害（耐力恢复）', '妨害（视野）',
    '(未知)'
]
params = rarity + limit + color + skill_type

sv_help_ = on_command('马娘技能帮助',priority=5, block=True)
sv = on_command('查技能',priority=5, block=True)
update = on_command('手动更新马娘技能',priority=5, permission=SUPERUSER,block=True)

@sv_help_.handle()
async def get_help():
    img_path = os.path.join(os.path.dirname(__file__), f'uma_skills_help.png')
    sv_help = f'{os.path.abspath(img_path)}'
    async def n() -> str:
        sv = BuildImage(0,0,background=sv_help)
        return sv.pic2bs4() 
    await sv_help_.finish(image(b64=await n()))

@sv.handle()
async def check_skill(arg: Message = CommandArg()):
    alltext = arg.extract_plain_text().replace(')', '）').replace('(', '（')
    skill_list = alltext.split(' ')
    with open(current_dir, 'r', encoding='UTF-8') as f:
        f_data = json.load(f)
    if not skill_list:
        return
    elif len(skill_list) == 1 and not all(elem in params for elem in skill_list):
        # 按技能名查询
        skill_name = skill_list[0]
        msg = await get_skill_info(skill_name, f_data)
    else:
        # 多于一个参数或在参数列表中就按分类查询
        # 去重
        skill_list = list(set(skill_list))
        rarity_list, limit_list, color_list, skill_type_list = [], [], [], []
        for param in skill_list:
            if param in rarity:
                rarity_list.append(param)
            elif param in limit:
                limit_list.append(param)
            elif param in color:
                color_list.append(param)
            elif param in skill_type:
                skill_type_list.append(param)
        # 未识别出技能类型
        if not (rarity_list + limit_list + color_list + skill_type_list):
            await sv.finish(f'没有识别出任何检索条件呢')
        # 当 稀有度 或 条件限制 或 颜色 不止一个参数输入时，那返回必然无结果
        if len(rarity_list) > 1 or len(limit_list) > 1 or len(color_list) > 1:
            await sv.finish(f'没有搜索出任何马娘技能呢，请确保你输入的检索条件正确且无冲突！')
        msg = await get_skill_list(
            rarity_list[0] if rarity_list else '',
            limit_list[0] if limit_list else '',
            color_list[0] if color_list else '',
            skill_type_list,
            f_data
        )
    await sv.send(msg)

# 手动更新本地数据
@update.handle()
async def force_update():
    try:
        await update_info()
        await del_img(os.path.dirname(__file__))
        await update.send('马娘技能信息刷新完成')
    except Exception as e:
        await update.send(f'马娘技能信息刷新失败：{e}')