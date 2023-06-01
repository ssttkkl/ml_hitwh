from datetime import datetime
from io import StringIO

import tzlocal
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent

from .interceptor import handle_error
from .mapper.game_csv_mapper import write_games_csv
from .utils.dep import GroupDep, SeasonFromUnaryArgOrRunningSeason
from .utils.general_handlers import require_store_command_args, require_platform_group_id
from ..errors import BadRequestError
from ..model import Group, Season
from ..model.enums import SeasonState
from ..platform.upload_file import upload_file
from ..service.game_service import get_games
from ..utils.date import encode_date

# ========== 导出赛季对局 ==========
export_season_games_matcher = on_command("导出赛季对局", aliases={"导出对局"}, priority=5)

require_store_command_args(export_season_games_matcher)
require_platform_group_id(export_season_games_matcher)


@export_season_games_matcher.handle()
@handle_error()
async def export_season_games(bot: Bot, event: MessageEvent, group: Group = GroupDep(),
                              season: Season = SeasonFromUnaryArgOrRunningSeason()):
    games = await get_games(group_id=group.id, season_id=season.id)

    if games.total == 0:
        raise BadRequestError("本赛季还没有创建过对局")

    filename = f"赛季对局 {season.name}"
    if season.state == SeasonState.finished:
        filename += "（已结束）"
    else:
        now = datetime.now(tzlocal.get_localzone())
        filename += f"（截至{encode_date(now)}）"
    filename += ".csv"

    with StringIO() as sio:
        await write_games_csv(sio, games.data)

        data = sio.getvalue().encode("utf_8_sig")
        await upload_file(bot, event, filename, data)


# ========== 导出所有对局 ==========
export_group_games_matcher = on_command("导出所有对局", priority=5)

require_store_command_args(export_season_games_matcher)
require_platform_group_id(export_season_games_matcher)


@export_group_games_matcher.handle()
@handle_error()
async def export_group_games(bot: Bot, event: MessageEvent, group: Group = GroupDep()):
    games = await get_games(group.id)

    if games.total == 0:
        raise BadRequestError("本群还没有创建过对局")

    now = datetime.now(tzlocal.get_localzone())
    filename = f"所有对局（截至{encode_date(now)}）.csv"

    with StringIO() as sio:
        await write_games_csv(sio, games.data)

        data = sio.getvalue().encode("utf_8_sig")
        await upload_file(bot, event, filename, data)
