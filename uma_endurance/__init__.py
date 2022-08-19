import os

from nonebot import on_command
from utils.image_utils import BuildImage
from utils.message_builder import image
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import  GroupMessageEvent,Message,MessageEvent,MessageSegment
#from hoshino import Service
from .caculate import *

__zx_plugin_name__="马娘耐力查询"
__plugin_usage__="""
usage:
    指令：
    马娘耐力帮助（请使用该指令查看完全使用方法）
""".strip()
__plugin_des__ = "马娘耐力查询"
__plugin_cmd__ = ["马娘耐力查询"]
__plugin_type__ = ("群内功能",)
__plugin_version__ = 0.1
__plugin_author__ = "azmiao （原作者） 十年（真寻适配）"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["群内功能"]

}

sv_help_ = on_command('马娘耐力帮助',priority=5, block=True)
sv = on_command('算耐力',priority=5, block=True)

# 帮助界面
@sv_help_.handle()
async def help():
    img_path = os.path.join(os.path.dirname(__file__), f'uma_endurance_help.png')
    sv_help = f'{os.path.abspath(img_path)}'
    async def n() -> str:
        sv = BuildImage(0,0,background=sv_help)
        return sv.pic2bs4() 
    await sv_help_.finish(image(b64=await n()))

@sv.handle()
async def get_endurance(ev: Message = CommandArg()):
    ls = {}
    ls = ev.extract_plain_text().strip().split('\n')
    print(f'{ls}')
    sx = ls[0].split(':')[1]
    #sx = ls[0].split(":")
    print(sx)
    syx = ls[1].split(':')[1]
    print(syx)
    gj = ls[2].split(' ')[0].split(':')[1]
    print(gj)
    zt = ls[2].split(' ')[1].split(':')[1]
    print(zt)
    gh = ls[3].split(' ')[0].split(':')[1]
    print(gh)
    ph = ls[3].split(' ')[1].split(':')[1]
    print(ph)
    jh = ls[3].split(' ')[2].split(':')[1]
    print(ph)
    # 获取各个数据
    # 速度上限
    speed_limit = int(sx.strip().split()[0])
    # 耐力
    endurance_tmp = int(sx.strip().split()[1])
    # 力量
    power = int(sx.strip().split()[2])
    # 根性
    determination = int(sx.strip().split()[3])
    # 智力
    intelligence = int(sx.strip().split()[4].strip('\r'))
    # 跑法：逃马、先马、差马、追马
    run_type = syx.split(' ')[0].split('-')[0]
    # 跑法适应性：S, A, B, C, D, E, F, G
    run_adaptability = syx.split(' ')[0].split('-')[1]
    # 场地类型：芝、泥地
    site_type = syx.split(' ')[1].split('-')[0]
    # 场地适应性：S, A, B, C, D, E, F, G
    site_adaptability = syx.split(' ')[1].split('-')[1]
    # 跑道长度：1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2500, 3000, 3200, 3400, 3600
    track_length = int(syx.split(' ')[2].split('-')[0])
    # 跑道长度适应性：S, A, B, C, D, E, F, G
    track_adaptability =syx.split(' ')[2].split('-')[1].strip('\r')
    # 干劲：绝好调、好调、普通、不调、绝不掉
    feeling = gj
    # 场况：良、稍重、重、不良
    situation = zt.strip('\r')
    # 固有回体等级
    stable_recover_level = int(gh)
    # 普通回体个数
    common_recover_num = int(ph)
    # 金回体个数
    upper_recover_num = int(jh)

    # 开始计算
    # 速度上限补正
    speed_limit_patch = await judge_speed(speed_limit, site_type, feeling, situation)
    # 体力补正
    hp_bonus = await judge_hp_bonus(run_type)
    # 力量补正
    power_patch = await judge_power(power, site_type, feeling, situation)
    # 根性补正
    determination_patch = await judge_determination(determination, feeling)
    # 智力补正
    intelligence_patch = await judge_intelligence(intelligence, feeling, run_adaptability)
    # 基准速度
    speed_standard_patch = await speed_standard(track_length)
    # 终盘体力消耗比
    end_endurance_bonus = 1 + 200 / ((600 * determination_patch) ** 0.5)
    # 序盘体力需求
    endurance_begin, uniform_speed_begin = await cacul_begin_endurance(speed_standard_patch, run_type, intelligence_patch, power_patch, 
        site_adaptability, track_length, track_adaptability, site_type, situation)
    # 中盘体力需求
    endurance_middle, uniform_speed_middle = await cacul_middle_endurance(uniform_speed_begin, speed_standard_patch, run_type, 
        intelligence_patch, power_patch, site_adaptability, track_length, track_adaptability, site_type, situation)
    # 终盘体力需求
    endurance_end = await cacul_end_endurance(speed_limit_patch, uniform_speed_middle, speed_standard_patch, run_type, 
        intelligence_patch, power_patch, site_adaptability, track_length, track_adaptability, site_type, situation, end_endurance_bonus)
    # 理论总体力需求
    hp = endurance_begin + endurance_middle + endurance_end
    # 理论总耐力需求
    endurance = await cacul_endurance(endurance_begin, endurance_middle, endurance_end, track_length, run_type)
    # 理论
    # 理论体力
    theoretical_hp = await theoretical_endurance(track_length, endurance_tmp, run_type)
    # 回体技能折算耐力
    stable_recover_endu, common_recover_endu, upper_recover_endu = await cacul_skill_endu(stable_recover_level, hp, run_type)
    # 回体技能折算体力
    stable_recover, common_recover_single, common_recover, upper_recover_single, upper_recover = await cacul_skill(
        stable_recover_level, common_recover_num, upper_recover_num, theoretical_hp)
    # 算上技能后的总体力
    end_hp = theoretical_hp + stable_recover + common_recover + upper_recover
    # 算上技能后的总耐力
    end_endurance = await get_end_endurance(end_hp, track_length, run_type)
    msg = f'''
速度上限：{speed_limit}
耐力：{endurance_tmp}
力量：{power}
根性：{determination}
智力：{intelligence}
跑法：{run_type} - {run_adaptability}
跑场：{site_type} - {site_adaptability}
跑道：{track_length}米 - {track_adaptability}
天气：{situation} | 干劲：{feeling}

序盘体力需求：{round(endurance_begin, 1)}
中盘体力需求：{round(endurance_middle, 1)}
终盘体力需求：{round(endurance_end, 1)}

本次携带了：
    - {stable_recover_level}级的固有回体
    - {common_recover_num}个普通回体
    - {upper_recover_num}个金回体

其中：
-每个普通回体回复{round(common_recover_single, 1)}体力
    - 折合耐力：{round(common_recover_endu, 1)}
-每个金回体回复{round(upper_recover_single, 1)}体力
    - 折合耐力：{round(upper_recover_endu, 1)}
-固有体力回复{round(stable_recover, 1)}体力
    - 折合耐力：{round(stable_recover_endu, 1)}

汇总：
无回体技能的体力需求：{round(hp, 1)}
算上技能后的本马体力：{round(end_hp, 1)}

结论：
无回体技能的耐力需求：{round(endurance, 1)}
算上技能后的本马耐力：{round(end_endurance, 1)}

注：此数据取自根性下坡改版前的数据
实际需求比计算器结果要高不少，尤其是大赛
本计算器仅为能刚好正常跑完的耐力最低下限
数值为非常理想的情况，没有加速技能，因此仅供参考
'''.strip()
    await sv.send(msg)