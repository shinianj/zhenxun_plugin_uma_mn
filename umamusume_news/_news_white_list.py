from tokenize import group
from services.db_context import db
from typing import List
from services.log import logger
from typing import Dict

class news(db.Model):
    __tablename__ = "news_white_list"
    id = db.Column(db.Integer(), primary_key=True)
    group_id =db.Column(db.TEXT(),nullable=False)  # 1
    group_ =db.Column(db.JSON(), nullable=False, default={})  # 是否开启

    _idx1 = db.Index("news_white_list_group_users_idx1", "group_id", unique=True)

    @classmethod
    async def add(cls,group_id:int):
        try:
            if not await cls.get_info(group_id = '1'):
                await cls.create(
                    group_id = '1',
                    group_ = {str(group_id):"True"}
                )
                return True
            else :
                query = cls.query.where((cls.group_id == '1'))
                query = query.with_for_update()
                user = await query.gino.first()
                if user:
                    p = user.group_
                    if p.get(str(group_id)) is None:
                        p[str(group_id)] = "True"
                        await user.update(group_=p).apply()
                        return True
                    else:
                        return False

        except Exception as e:
            logger.error(f" news_white_list_add 发生错误 {type(e)}：{e}")
        return False

    @classmethod
    async def delete(cls,group_id:int):
        try:
            if not await cls.get_info(group_id = '1'):
                return False
            else :
                query = (
                await cls.query.where((cls.group_id == '1'))
                .with_for_update()
                .gino.first()
            )
            user = query.group_
            if user[str(group_id)] == 'False':
                return False
            user[str(group_id)] = 'False'
            await query.update(group_=user).apply()
            return True

        except Exception as e:
            logger.error(f" news_white_list_delete 发生错误 {type(e)}：{e}")
        return False

    @classmethod
    async def on(cls,group_id:int):
        try:
            if not await cls.get_info(group_id = '1'):
                return False
            else :
                query = (
                await cls.query.where((cls.group_id == '1'))
                .with_for_update()
                .gino.first()
            )
            user = query.group_
            if user[str(group_id)] == 'True':
                return False
            user[str(group_id)] = 'True'
            await query.update(group_=user).apply()
            return True

        except Exception as e:
            logger.error(f" news_white_list_on 发生错误 {type(e)}：{e}")
        return False

    @classmethod
    async def get_info(cls, group_id: str = '1') -> Dict[str,str]:
        """
        说明：
            获取白名单
        参数：
            :param group_id: 群号
        """
        query = cls.query.where((cls.group_id == group_id))
        user = await query.gino.first()
        if user:
            return user.group_
        else:
            await cls.create(
                group_id = group_id,
            )
            return {}