from typing import TextIO

from nonebot import Bot
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ml_hitwh.controller.mapper.enums_mapper import player_and_wind_mapping, game_state_mapping
from ml_hitwh.controller.utils import get_user_name
from ml_hitwh.model.enums import GameState
from ml_hitwh.model.orm import data_source
from ml_hitwh.model.orm.game import GameOrm, GameRecordOrm


async def map_game(io: TextIO, game: GameOrm, bot: Bot, *, map_promoter: bool = False):
    session = data_source.session()

    stmt = select(GameOrm).where(GameOrm.id == game.id).limit(1).options(
        selectinload(GameOrm.season),
        selectinload(GameOrm.promoter),
        selectinload(GameOrm.group),
        selectinload(GameOrm.records).joinedload(GameRecordOrm.user)
    )
    game: GameOrm = (await session.execute(stmt)).scalar_one_or_none()

    # 对局22090901  四人南
    io.write('对局')
    io.write(str(game.code))
    io.write('  ')
    io.write(player_and_wind_mapping[game.player_and_wind])
    io.write('\n')

    # 所属赛季：Season Name
    io.write('所属赛季：')
    if game.season_id is None:
        io.write('无')
    else:
        # season = await session.get(SeasonOrm, game.season_id)
        io.write(game.season.name)
    io.write('\n')

    # 状态：未完成
    io.write('状态：')
    io.write(game_state_mapping[GameState(game.state)])
    io.write('\n')

    if map_promoter:
        # promoter = await session.get(UserOrm, game.promoter_user_id)
        io.write('创建者：')
        io.write(game.promoter.nickname or
                 await get_user_name(game.promoter.binding_qq, game.group.binding_qq, bot))
        io.write('\n')

    if len(game.records) > 0:
        # [空行]
        io.write('\n')

        # #1  Player Name    10000  (+5)
        # [...]
        for i, r in enumerate(sorted(game.records, key=lambda r: r.point, reverse=True)):
            # user = await session.get(UserOrm, r.user_id)
            name = r.user.nickname or await get_user_name(r.user.binding_qq, game.group.binding_qq, bot)
            io.write('#')
            io.write(str(i + 1))
            io.write('  ')
            io.write(name)
            io.write('    ')
            io.write(str(r.score))

            if game.state == GameState.completed:
                io.write('  (')
                if r.point > 0:
                    io.write('+')
                elif r.point == 0:
                    io.write('±')
                io.write(str(r.point))
                io.write(')')

            io.write('\n')
