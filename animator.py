"""动画帧生成器 - 逐回合生成平滑过渡动画帧"""

from renderer import RaceRenderer
from race_data import WEATHER_CONFIG

# 技能效果中的减益类型（用于判断连线颜色）
DEBUFF_TYPES = {"backward", "pause", "silence", "prob_backward", "var_backward", "mark_target"}
BUFF_TYPES = {"forward", "prob_forward", "var_forward", "increment_var", "ub"}
REFLECT_TYPES = {"steel_plate_reflect"}
DEPLOY_TYPES = {"cannon_deploy"}


def _ease_in_out_cubic(t):
    """easeInOutCubic 缓动函数（与前端 animatePositions 一致）"""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2


def _build_skill_lines(events):
    """从事件中提取技能连线数据"""
    lines = []
    for ev in events:
        if ev.get("action") != "skill" or "effects" not in ev:
            continue
        source_track = ev.get("track")
        for eff in ev["effects"]:
            target_track = eff.get("track")
            # 如果目标赛道未指定，说明是自身效果
            if not target_track:
                target_track = source_track
            effect_type = eff.get("effect", eff.get("type", ""))
            line_type = None
            if effect_type in DEBUFF_TYPES:
                line_type = "debuff"
            elif effect_type in BUFF_TYPES:
                line_type = "buff"
            elif effect_type in REFLECT_TYPES:
                line_type = "reflect"
            elif effect_type in DEPLOY_TYPES:
                line_type = "deploy"
            if line_type:
                lines.append({
                    "from": source_track,
                    "to": target_track,
                    "type": line_type,
                    "isSelf": source_track == target_track,
                })
    return lines


def generate_frames(replay_data, speed=1.0, fps=15, max_turns=None, show_log=True,
                    progress_callback=None):
    """
    生成所有动画帧

    Args:
        replay_data: 加载后的回放数据
        speed: 播放速度倍率 (0.5/1.0/1.5/2.0/3.0)
        fps: 帧率
        max_turns: 最大渲染回合数（None=全部）
        show_log: 是否显示事件日志面板
        progress_callback: 进度回调函数 callback(current_frame, total_frames)

    Yields:
        PIL.Image 每一帧
    """
    track_length = replay_data["track_length"]
    characters = replay_data["characters"]
    turns = replay_data["turns"]
    terrains = replay_data["terrains"]
    terrain_fair = replay_data["terrain_fair"]
    num_tracks = len(characters)

    if max_turns:
        turns = turns[:max_turns]

    total_turns = len(turns)
    renderer = RaceRenderer()

    # 初始位置：所有角色在起点
    initial_positions = [track_length] * num_tracks

    # 每回合的帧数配置
    # 1x 速度：每回合约2秒
    base_duration = 2.0  # 秒
    move_ratio = 0.4     # 移动动画占总时长的比例
    stay_ratio = 0.6     # 停留（显示日志）占总时长的比例

    duration = base_duration / speed
    move_frames = max(4, int(fps * duration * move_ratio))
    stay_frames = max(2, int(fps * duration * stay_ratio))
    end_frames = int(fps * 2 / speed)

    # 计算总帧数（用于进度显示）
    total_frames = (1 + stay_frames) + total_turns * (move_frames + stay_frames) + end_frames
    frame_count = 0

    def _progress():
        nonlocal frame_count
        frame_count += 1
        if progress_callback:
            progress_callback(frame_count, total_frames)

    # ---- 初始帧：所有角色在起点 ----
    yield renderer.render_frame(
        characters=characters,
        track_length=track_length,
        positions=initial_positions,
        terrains=terrains,
        rankings=None,
        skill_lines=None,
        turn_number=0,
        total_turns=total_turns,
        events=None,
        terrain_fair=terrain_fair,
        char_vars=None,
    )
    _progress()
    # 初始帧多停留一会
    for _ in range(stay_frames):
        yield renderer.render_frame(
            characters=characters,
            track_length=track_length,
            positions=initial_positions,
            terrains=terrains,
            rankings=None,
            skill_lines=None,
            turn_number=0,
            total_turns=total_turns,
            events=None,
            terrain_fair=terrain_fair,
            char_vars=None,
        )
        _progress()

    # ---- 逐回合动画 ----
    prev_positions = initial_positions[:]

    for turn_idx, turn in enumerate(turns):
        turn_number = turn.get("turn", turn_idx + 1)
        new_positions = turn.get("positions", prev_positions[:])
        turn_terrains = turn.get("terrains", terrains)
        events = turn.get("events", [])
        rankings = turn.get("rankings")
        char_vars = turn.get("char_vars")
        skill_lines = _build_skill_lines(events)

        # 1) 平滑移动帧
        for frame_i in range(move_frames):
            t = frame_i / move_frames
            eased_t = _ease_in_out_cubic(t)

            # 插值位置
            interp_positions = [
                prev_positions[i] + (new_positions[i] - prev_positions[i]) * eased_t
                for i in range(num_tracks)
            ]

            # 技能连线在移动全程显示
            yield renderer.render_frame(
                characters=characters,
                track_length=track_length,
                positions=interp_positions,
                terrains=turn_terrains or terrains,
                rankings=rankings if (rankings and t > 0.8) else None,
                skill_lines=skill_lines,
                turn_number=turn_number,
                total_turns=total_turns,
                events=events if (show_log and t > 0.3) else None,
                terrain_fair=terrain_fair,
                char_vars=char_vars,
            )
            _progress()

        # 2) 停留帧（显示事件日志 + 技能连线）
        for _ in range(stay_frames):
            yield renderer.render_frame(
                characters=characters,
                track_length=track_length,
                positions=new_positions,
                terrains=turn_terrains or terrains,
                rankings=rankings,
                skill_lines=skill_lines,
                turn_number=turn_number,
                total_turns=total_turns,
                events=events if show_log else None,
                terrain_fair=terrain_fair,
                char_vars=char_vars,
            )
            _progress()

        prev_positions = new_positions[:]

    # ---- 结束帧：显示排名，多停留2秒 ----
    final_turn = turns[-1] if turns else {}
    final_positions = final_turn.get("positions", prev_positions[:])
    final_rankings = final_turn.get("rankings", [])
    final_events = final_turn.get("events", [])

    # 生成结束事件
    finish_events = list(final_events)
    if final_rankings:
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        names = []
        for r in final_rankings:
            if r["rank"] <= 3:
                char = next((c for c in characters if c["track"] == r["track"]), None)
                name = char["name"] if char else f"{r['track']}号"
                names.append(f"{medals.get(r['rank'], '')}{name}")
        finish_text = "🏁 比赛结束！ " + " ".join(names)
        finish_events.append({"action": "finish", "text": finish_text})

    end_frames = int(fps * 2 / speed)
    for _ in range(end_frames):
        yield renderer.render_frame(
            characters=characters,
            track_length=track_length,
            positions=final_positions,
            terrains=terrains,
            rankings=final_rankings,
            skill_lines=None,
            turn_number=turns[-1].get("turn", total_turns) if turns else total_turns,
            total_turns=total_turns,
            events=finish_events if show_log else None,
            terrain_fair=terrain_fair,
            char_vars=None,
        )
        _progress()
