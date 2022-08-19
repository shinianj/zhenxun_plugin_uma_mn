import os
import datetime
import json
import nonebot
import httpx

#from .spider import uma_update
from utils.message_builder import record
from .adaptability import get_adaptability
from nonebot.params import CommandArg
from nonebot import on_command,Driver
from nonebot.permission import SUPERUSER
from configs.config import NICKNAME, Config
from utils.message_builder import image
from nonebot.adapters.onebot.v11 import  GroupMessageEvent,Message,MessageEvent,MessageSegment
from utils.utils import scheduler,get_bot
from PIL import Image, ImageDraw, ImageFont, ImageColor
from utils.image_utils import BuildImage
from nonebot.adapters.onebot.v11 import ActionFailed
from services.log import logger
from pathlib import Path
#from hoshino import Service, priv, R
#from hoshino.util import pic2b64

__zx_plugin_name__="马娘数据"
__plugin_usage__="""
usage:
    指令：
    马娘数据帮助
    查今天生日马娘
    查马娘生日+[马娘名称]
    示例：查马娘生日 特别周
    查生日马娘+[日期(月\日)]
    示例：查生日马娘 5-2(即5月2日 特别周生日)
    查角色+id/日文名/ 中文名/英文名/分类/语音/头像/cv/身高/体重/三围/适应性/详细信息/原案/决胜服/制服+[马娘名称]
    示例:查角色 中文名 无声铃鹿
    示例:查角色 英文名 无声铃鹿
    示例:查角色 CV 无声铃鹿
""".strip()
__plugin_des__ = "马娘数据"
__plugin_cmd__ = ["马娘数据"]
__plugin_type__ = ("群内功能",)
__plugin_version__ = 0.1
__plugin_author__ = "azmiao （原作者） 十年（真寻适配）"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["群内功能"]

}
driver: Driver = nonebot.get_driver()

Config.add_plugin_config(
        "_task",
        "DEFAULT_MN",
        True,
        help_="马娘数据 开关，使用请前往config.py中填写对应的URL地址(127.0.0.1:8080中的8080）",
        default_value=True,
    )

from ._R import pic2b64,ResImg
from .detail_info import get_detail

current_dir = os.path.join(os.path.dirname(__file__), 'config.json')

sv_help_ = on_command('马娘数据帮助',aliases={'马娘数据'},priority=5, block=True)
sv_today_bir = on_command('查今天生日马娘',priority=5, block=True)
sv_search_name = on_command('查马娘生日',priority=5, block=True)
sv_search_date = on_command('查生日马娘',priority=5, block=True)
sv_search_horse = on_command('查角色',aliases={'查马娘'},priority=5, block=True)
update = on_command('手动更新马娘数据',priority=5, permission=SUPERUSER,block=True)

@sv_help_.handle()
async def get_help():
    img_path = os.path.join(os.path.dirname(__file__), f'uma_info_help.png')
    sv_help = f'{os.path.abspath(img_path)}'
    async def n() -> str:
        sv = BuildImage(0,0,background=sv_help)
        return sv.pic2bs4() 
    await sv_help_.finish(image(b64=await n()))

@sv_today_bir.handle()
async def get_tod():
    with open(current_dir, 'r', encoding = 'UTF-8') as f:
        f_data = json.load(f)
    rep_dir = os.path.join(os.path.dirname(__file__), 'replace_dict.json')
    with open(rep_dir, 'r', encoding = 'UTF-8') as f:
        rep_data = json.load(f)
    tod = datetime.datetime.now().strftime('%m-%d')
    tod_list = tod.split('-', 1)
    tod = '-'.join(str(int(tod_num, 10)) for tod_num in tod_list)
    tod_list = []
    name_list = list(f_data.keys())
    name_list.remove('current_chara')
    for uma_name in name_list:
        if f_data[uma_name]['category'] == 'umamusume':
            if str(f_data[uma_name]['bir']) == str(tod):
                cn_name = f_data[uma_name]['cn_name'] if f_data[uma_name]['cn_name'] else rep_data[uma_name][0]
                tod_list.append(cn_name)
    if not tod_list:
        msg = f'今天没有马娘生日哟'
        await sv_today_bir.finish(f'{msg}',at_sender = True)
    msg = '今天生日的马娘有：\n' + ' | '.join(tod_list)
    await sv_today_bir.finish(f'{msg}',at_sender = True)

@sv_search_name.handle()
async def search_bir(event: MessageEvent, arg: Message = CommandArg()):
    uma_name_tmp = arg.extract_plain_text().strip()
    with open(current_dir, 'r', encoding = 'UTF-8') as f:
        f_data = json.load(f)
        f.close()
    with open(os.path.join(os.path.dirname(__file__), 'replace_dict.json'), 'r', encoding = 'UTF-8') as af:
        replace_data = json.load(af)
        af.close()
    uma_bir = ''
    name_list = list(f_data.keys())
    name_list.remove('current_chara')
    for uma_name in name_list:
        if f_data[uma_name]['category'] == 'umamusume':
            other_name_list = list(replace_data[uma_name])
            cn_name = f_data[uma_name]['cn_name'] if f_data[uma_name]['cn_name'] else f_data[uma_name]['jp_name']
            if str(uma_name) == str(uma_name_tmp) or str(cn_name) == str(uma_name_tmp) or str(uma_name_tmp) in other_name_list:
                cn_name_tmp = cn_name
                uma_bir = f_data[uma_name]['bir']
    if not uma_bir:
        msg = f'这只马娘不存在或没有生日数据'
        await sv_search_name.finish(msg)
    msg = f'{cn_name_tmp}的生日是：{uma_bir}'
    await sv_search_name.finish(msg)

@sv_search_date.handle()
async def search_uma(arg: Message = CommandArg()):
    uma_bir_tmp = arg.extract_plain_text().strip()
    with open(current_dir, 'r', encoding = 'UTF-8') as f:
        f_data = json.load(f)
    rep_dir = os.path.join(os.path.dirname(__file__), 'replace_dict.json')
    with open(rep_dir, 'r', encoding = 'UTF-8') as f:
        rep_data = json.load(f)
    uma_list = []
    name_list = list(f_data.keys())
    name_list.remove('current_chara')
    for uma_name in name_list:
        if f_data[uma_name]['category'] == 'umamusume':
            if str(f_data[uma_name]['bir']) == str(uma_bir_tmp):
                cn_name = f_data[uma_name]['cn_name'] if f_data[uma_name]['cn_name'] else rep_data[uma_name][0]
                uma_list.append(cn_name)
    if not uma_list:
        msg = f'这天没有马娘生日哟'
        await sv_search_date.finish(msg)
    msg = f'{uma_bir_tmp}生日的马娘有：\n' + ' | '.join(uma_list)
    await sv_search_date.finish( msg)

@scheduler.scheduled_job('cron', hour='8', minute='31')
async def push_bir():
    with open(current_dir, 'r', encoding = 'UTF-8') as f:
        f_data = json.load(f)
    rep_dir = os.path.join(os.path.dirname(__file__), 'replace_dict.json')
    with open(rep_dir, 'r', encoding = 'UTF-8') as f:
        rep_data = json.load(f)
    tod = datetime.datetime.now().strftime('%m-%d')
    tod_list = tod.split('-', 1)
    tod = '-'.join(str(int(tod_num, 10)) for tod_num in tod_list)
    tod_list = []
    name_list = list(f_data.keys())
    name_list.remove('current_chara')
    for uma_name in name_list:
        if f_data[uma_name]['category'] == 'umamusume':
            if f_data[uma_name]['bir'] == str(tod):
                cn_name = f_data[uma_name]['cn_name'] if f_data[uma_name]['cn_name'] else rep_data[uma_name][0]
                tod_list.append(cn_name)
    if not tod_list:
        await logger.info(f'今天没有马娘生日哟')
        return
    msg = '今天生日的马娘有：\n' + ' | '.join(tod_list)
    try:
        bot = get_bot()
        gl = await bot.get_group_list()
        gl = [g["group_id"] for g in gl]
        for g in gl:
            try:
                await bot.send_group_msg(
                    group_id=g, message= msg
                )
            except ActionFailed:
                logger.warning(f"{g} 群被禁言中，无法发送今日马娘生日推送")
    except Exception as e:
        logger.error(f"今日马娘生日推送错误 e:{e}")

@sv_search_horse.handle()
async def get_single_info(event: MessageEvent, arg: Message = CommandArg()):
    alltext = arg.extract_plain_text().strip()
    try:
        text_list = alltext.split(' ', 1)
    except:
        msg = f'命令格式输入错误，请参考“马娘数据帮助”发送命令！'
        await sv_search_horse.finish(msg)
    info_type = text_list[0]
    if info_type not in ['id', '日文名', '中文名', '英文名', '分类', '语音', '头像', 'cv', '身高', '体重', '三围', '适应性', '详细信息', \
        '原案', '决胜服', '制服']:
        return
    uma_name_tmp = text_list[1]
    with open(current_dir, 'r', encoding = 'UTF-8') as f:
        f_data = json.load(f)
        f.close()
    with open(os.path.join(os.path.dirname(__file__), 'replace_dict.json'), 'r', encoding = 'UTF-8') as af:
        replace_data = json.load(af)
        af.close()
    name_list = list(f_data.keys())
    name_list.remove('current_chara')
    msg = ''
    for uma_name in name_list:
        other_name_list = list(replace_data[uma_name])
        cn_name = f_data[uma_name]['cn_name'] if f_data[uma_name]['cn_name'] else f_data[uma_name]['jp_name']
        if str(uma_name) == str(uma_name_tmp) or str(cn_name) == str(uma_name_tmp) or str(uma_name_tmp) in other_name_list:
            if info_type == 'id':
                id = f_data[uma_name]['id']
                msg = f'{uma_name_tmp}的角色id为{id}'
            elif info_type == '日文名':
                jp_name = f_data[uma_name]['jp_name']
                msg = f'{uma_name_tmp}的日文名为{jp_name}'
            elif info_type == '中文名':
                cn_name = f_data[uma_name]['cn_name']
                if not cn_name:
                    msg = f'{uma_name_tmp}暂时还没有中文名哟'
                    await sv_search_horse.finish(msg)
                msg = f'{uma_name_tmp}的中文名为{cn_name}'
            elif info_type == '英文名':
                en_name = str(uma_name)
                msg = f'{uma_name_tmp}的英文名为{en_name}'
            elif info_type == '分类':
                category_tmp = str(f_data[uma_name]['category'])
                category = '赛马娘' if category_tmp == 'umamusume' else '学园关系角色'
                msg = f'{uma_name_tmp}的角色分类为{category}'
            elif info_type == '语音':
                voice = f_data[uma_name]['voice']
                if not voice:
                    msg = f'{uma_name_tmp}暂时还没有语音哟'
                    await sv_search_horse.finish(msg)
                save_path = os.path.join(os.path.dirname(__file__), f'res/base_data/voice_data')
                mp3_name = uma_name + '.mp3'
                msg = record(mp3_name, save_path)
                #msg = f'[CQ:record,file=file:///{os.path.abspath(voice_file)}]'
            elif info_type == '头像':
                sns_icon = f_data[uma_name]['sns_icon']
                save_path = os.path.join(os.path.dirname(__file__), f'res/base_data/sns_icon/{uma_name}.png')
                async def _():
                    response = httpx.get(sns_icon, timeout=10)
                    with open(save_path,  mode='wb') as f:
                        f.write(response.read())
                await _()
                sv_help = f'{os.path.abspath(save_path)}'
                async def n() -> str:
                        sv = BuildImage(0,0,background=sv_help)
                        return sv.pic2bs4() 
                cn_name = f_data[uma_name]['cn_name']
                msg = f'{cn_name} 的头像'
                msg += image(b64=await n())
            elif info_type == 'cv':
                cv = f_data[uma_name]['cv']
                if not cv:
                    msg = f'{uma_name_tmp}暂时还没公布cv哟'
                    await sv_search_horse.finish(msg)
                msg = f'{uma_name_tmp}的cv是:\n{cv}'
            elif info_type == '身高':
                height = f_data[uma_name]['height']
                if not height:
                    msg = f'{uma_name_tmp}暂时还没公布身高哟'
                    await sv_search_horse.finish(msg)
                msg = f'{uma_name_tmp}的身高是:\n{height}cm'
            elif info_type == '体重':
                weight = f_data[uma_name]['weight']
                if not weight:
                    msg = f'{uma_name_tmp}暂时还没公布体重哟'
                    await sv_search_horse.finish(msg)
                msg = f'{uma_name_tmp}的体重是:\n{weight}'
            elif info_type == '三围':
                measurements = f_data[uma_name]['measurements']
                if not measurements:
                    msg = f'{uma_name_tmp}暂时还没公布三围哟'
                    await sv_search_horse.finish(msg)
                msg = f'{uma_name_tmp}的三围是:\n{measurements}'
            elif info_type == '制服':
                uniform_img = f_data[uma_name]['uniform_img']
                if not uniform_img:
                    msg = f'{uma_name_tmp}暂时还没公布制服哟'
                    await sv_search_horse.finish(msg)
                save_path = os.path.join(os.path.dirname(__file__), f'res/extra_data/uma_uniform/{uma_name}.png')
                sv_help = f'{os.path.abspath(save_path)}'
                async def n() -> str:
                        sv = BuildImage(0,0,background=sv_help)
                        return sv.pic2bs4() 
                cn_name = f_data[uma_name]['cn_name']
                msg = f'{cn_name} 的制服'
                msg += image(b64=await n())
            elif info_type == '决胜服':
                winning_suit_img = f_data[uma_name]['winning_suit_img']
                save_path = os.path.join(os.path.dirname(__file__), f'res/extra_data/uma_uniform/{uma_name}_winning_suit_img.png')
                if not winning_suit_img:
                    msg = f'{uma_name_tmp}暂时还没公布决胜服哟'
                    await sv_search_horse.finish(msg)
                async def _():
                    response = httpx.get(winning_suit_img, timeout=10)
                    with open(save_path,  mode='wb') as f:
                        f.write(response.read())
                await _()
                sv_help = f'{os.path.abspath(save_path)}'
                async def n() -> str:
                        sv = BuildImage(0,0,background=sv_help)
                        return sv.pic2bs4() 
                cn_name = f_data[uma_name]['cn_name']
                msg = f'{cn_name} 的决胜服'
                msg += image(b64=await n())
            elif info_type == '原案':
                original_img = f_data[uma_name]['original_img']
                save_path = os.path.join(os.path.dirname(__file__), f'res/extra_data/uma_uniform/{uma_name}_original_img.png')
                if not original_img:
                    msg = f'{uma_name_tmp}暂时还没公布原案哟'
                    await sv_search_horse.finish(msg)
                async def _():
                    response = httpx.get(original_img, timeout=10)
                    with open(save_path,  mode='wb') as f:
                        f.write(response.read())
                await _()
                sv_help = f'{os.path.abspath(save_path)}'
                async def n() -> str:
                        sv = BuildImage(0,0,background=sv_help)
                        return sv.pic2bs4() 
                cn_name = f_data[uma_name]['cn_name']
                msg = f'{cn_name} 的原案'
                msg += image(b64=await n())
            elif info_type == '适应性':
                img_tmp = await get_adaptability(uma_name, f_data)
                img = pic2b64(img_tmp)
                if not img:
                    msg = f'{uma_name_tmp}暂时还没有适应性数据哟'
                    await sv_search_horse.finish(msg)
                cn_name = f_data[uma_name]['cn_name']
                msg = f'{cn_name} 的适应性数据'
                msg += image(b64=img)
            elif info_type == '详细信息':
                img_tmp = await get_detail(uma_name, f_data)
                img = pic2b64(img_tmp)
                if not img:
                    msg = f'出现错误！未获取到详细信息！请到Github仓库反馈！'
                    await sv_search_horse.finish(msg)
                cn_name = f_data[uma_name]['cn_name']
                msg = f'{cn_name} 的详细信息'
                msg += image(b64=img)
    if not msg:
        msg = f'这个角色可能不存在或者角色名称对不上'
    await sv_search_horse.send(msg)


# @update.handle()
# async def update_info():
#      await update.send('正在更新数据，请耐心等待...')
#      try:
#          await uma_update(current_dir)
#          msg = '马娘数据更新完成'
#      except Exception as e:
#          msg = f'马娘数据更新失败{e}'
#      await update.send(msg)