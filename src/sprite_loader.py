import pygame
import os

MARIO_FILE_MAP = {
    # === IDLE ===
    "animations/other_animations/mario_default_idle_left.png": "Mario - Idle",
    "animations/other_animations/mario_idle_version1/mario_idle_left(1),version(1).png": "Mario - Idle 1",
    "animations/other_animations/mario_idle_version1/mario_idle_left(2),version(1).png": "Mario - Idle 2",
    "animations/other_animations/mario_idle_version1/mario_idle_left(3),version(1).png": "Mario - Idle 3",
    "animations/other_animations/mario_idle_version1/mario_idle_left(4),version(1).png": "Mario - Idle 4",

    # === HURT / DEATH ===
    "animations/other_animations/mario_hurt_left.png": "Mario - Hurt",

    # === MOVEMENT ===
    "animations/movement_animations/mario_run/mario_run_left(1).png": "Mario - Run 1",
    "animations/movement_animations/mario_run/mario_run_left(2).png": "Mario - Run 2",
    "animations/movement_animations/mario_run/mario_run_left(3).png": "Mario - Run 3",
    "animations/movement_animations/mario_run/mario_run_left(4).png": "Mario - Run 4",
    "animations/movement_animations/mario_run/mario_run_left(5).png": "Mario - Run 5",
    "animations/movement_animations/mario_run/mario_run_left(6).png": "Mario - Run 6",
    "animations/movement_animations/mario_run/mario_run_left(7).png": "Mario - Run 7",
    "animations/movement_animations/mario_run/mario_run_left(8).png": "Mario - Run 8",

    "animations/movement_animations/mario_dash/mario_dash_left(1).png": "Mario - Dash 1",
    "animations/movement_animations/mario_dash/mario_dash_left(2).png": "Mario - Dash 2",
    "animations/movement_animations/mario_dash/mario_dash_left(3).png": "Mario - Dash 3",
    "animations/movement_animations/mario_dash/mario_dash_left(4).png": "Mario - Dash 4",
    "animations/movement_animations/mario_dash/mario_dash_left(5).png": "Mario - Dash 5",
    "animations/movement_animations/mario_dash/mario_dash_left(6).png": "Mario - Dash 6",
    "animations/movement_animations/mario_dash/mario_dash_left(7).png": "Mario - Dash 7",

    "animations/movement_animations/mario_jump/mario_jump_left(1).png": "Mario - Jump 1",
    "animations/movement_animations/mario_jump/mario_jump_left(2).png": "Mario - Jump 2",
    "animations/movement_animations/mario_jump/mario_jump_left(3).png": "Mario - Jump 3",
    "animations/movement_animations/mario_jump/mario_jump_left(4).png": "Mario - Jump 4",
    "animations/movement_animations/mario_jump/mario_fall_left.png": "Mario - Fall",
    "animations/movement_animations/mario_jump/mario_land_left(1).png": "Mario - Land 1",
    "animations/movement_animations/mario_jump/mario_land_left(2).png": "Mario - Land 2",

    # === LIGHT ATTACK COMBO (3 versions, 3 frames each) ===
    "animations/attack_animations/light_attack_combo/mario_light_attack_left(version1,(1)).png": "Mario - Light V1 1",
    "animations/attack_animations/light_attack_combo/mario_light_attack_left(version1,(2)).png": "Mario - Light V1 2",
    "animations/attack_animations/light_attack_combo/mario_light_attack_left(version1,(3)).png": "Mario - Light V1 3",
    "animations/attack_animations/light_attack_combo/mario_light_attack_left(version2,(1)).png": "Mario - Light V2 1",
    "animations/attack_animations/light_attack_combo/mario_light_attack_left(version2,(2)).png": "Mario - Light V2 2",
    "animations/attack_animations/light_attack_combo/mario_light_attack_left(version2,(3)).png": "Mario - Light V2 3",
    "animations/attack_animations/light_attack_combo/mario_light_attack_left(version3,(1)).png": "Mario - Light V3 1",
    "animations/attack_animations/light_attack_combo/mario_light_attack_left(version3,(2)).png": "Mario - Light V3 2",
    "animations/attack_animations/light_attack_combo/mario_light_attack_left(version3,(3)).png": "Mario - Light V3 3",

    # === HEAVY ATTACK COMBO (3 versions, 4 frames each) ===
    "animations/attack_animations/heavy_attack_combo/mario_heavy_left(version1,(1)).png": "Mario - Heavy V1 1",
    "animations/attack_animations/heavy_attack_combo/mario_heavy_left(version1,(2)).png": "Mario - Heavy V1 2",
    "animations/attack_animations/heavy_attack_combo/mario_heavy_left(version1,(3)).png": "Mario - Heavy V1 3",
    "animations/attack_animations/heavy_attack_combo/mario_heavy_left(version1,(4)).png": "Mario - Heavy V1 4",
    "animations/attack_animations/heavy_attack_combo/mario_heavy_left(version2,(1)).png": "Mario - Heavy V2 1",
    "animations/attack_animations/heavy_attack_combo/mario_heavy_left(version2,(2)).png": "Mario - Heavy V2 2",
    "animations/attack_animations/heavy_attack_combo/mario_heavy_left(version2,(3)).png": "Mario - Heavy V2 3",
    "animations/attack_animations/heavy_attack_combo/mario_heavy_left(version2,(4)).png": "Mario - Heavy V2 4",
    "animations/attack_animations/heavy_attack_combo/mario_heavy_left(version3,(1).png": "Mario - Heavy V3 1",
    "animations/attack_animations/heavy_attack_combo/mario_heavy_left(version3,(2).png": "Mario - Heavy V3 2",
    "animations/attack_animations/heavy_attack_combo/mario_heavy_left(version3,(3).png": "Mario - Heavy V3 3",
    "animations/attack_animations/heavy_attack_combo/mario_heavy_left(version3,(4).png": "Mario - Heavy V3 4",

    # === AIR ATTACKS ===
    "animations/attack_animations/air_attack_light/mario_light_attack_air_left(1).png": "Mario - Air Light 1",
    "animations/attack_animations/air_attack_light/mario_light_attack_air_left(2).png": "Mario - Air Light 2",
    "animations/attack_animations/air_attack_light/mario_light_attack_air_left(3).png": "Mario - Air Light 3",
    "animations/attack_animations/mario_heavy_air_attack/mario_heavy_air_attack_left(1).png": "Mario - Air Heavy 1",
    "animations/attack_animations/mario_heavy_air_attack/mario_heavy_air_attack_left(2).png": "Mario - Air Heavy 2",
    "animations/attack_animations/mario_heavy_air_attack/mario_heavy_air_attack_left(3).png": "Mario - Air Heavy 3",
    "animations/attack_animations/mario_heavy_air_attack/mario_heavy_air_attack_left(4).png": "Mario - Air Heavy 4",

    # === BLOCK ===
    "animations/attack_animations/mario_block/mario_block_left.png": "Mario - Block",

    # === HAMMER SPECIAL ===
    "animations/attack_animations/Hammer_special/mario_special_attack_hammer_left(1).png": "Mario - Hammer 1",
    "animations/attack_animations/Hammer_special/mario_special_attack_hammer_left(2).png": "Mario - Hammer 2",
    "animations/attack_animations/Hammer_special/mario_special_attack_hammer_left(3).png": "Mario - Hammer 3",
    "animations/attack_animations/Hammer_special/mario_special_attack_hammer_left(4).png": "Mario - Hammer 4",

    # === FIRE SPECIAL ===
    "animations/attack_animations/Fire_special/mario_special_fire_left(1).png": "Mario - Fire 1",
    "animations/attack_animations/Fire_special/mario_special_fire_left(2).png": "Mario - Fire 2",
    "animations/attack_animations/Fire_special/mario_special_fire_left(3).png": "Mario - Fire 3",
    "animations/attack_animations/Fire_special/mario_special_fire_left(4).png": "Mario - Fire 4",

    # === LEDGE GRAB ===
    "animations/movement_animations/mario_ledge_grab/mario_ledge_grab(1).png": "Mario - Ledge Grab 1",
    "animations/movement_animations/mario_ledge_grab/mario_ledge_grab(2).png": "Mario - Ledge Grab 2",
    "animations/movement_animations/mario_ledge_grab/mario_ledge_grab(3).png": "Mario - Ledge Grab 3",
}

LUIGI_FILE_MAP = {
    # === IDLE ===
    "animations/other_animations/idle_animation/luigi_idle_animation_left(1).png": "Luigi - Idle 1",
    "animations/other_animations/idle_animation/luigi_idle_animation_left(2).png": "Luigi - Idle 2",
    "animations/other_animations/idle_animation/luigi_idle_animation_left(3).png": "Luigi - Idle 3",
    "animations/other_animations/idle_animation/luigi_idle_animation_left(4).png": "Luigi - Idle 4",
    "animations/other_animations/luigi_idle_left_frame.png": "Luigi - Idle",

    # === HURT / DEATH ===
    "animations/other_animations/luigi_hurt_left.png": "Luigi - Hurt",

    # === MOVEMENT ===
    "animations/movement_animations/luigi_run/luigi_run_left(1).png": "Luigi - Run 1",
    "animations/movement_animations/luigi_run/luigi_run_left(2).png": "Luigi - Run 2",
    "animations/movement_animations/luigi_run/luigi_run_left(3).png": "Luigi - Run 3",
    "animations/movement_animations/luigi_run/luigi_run_left(4).png": "Luigi - Run 4",
    "animations/movement_animations/luigi_run/luigi_run_left(5).png": "Luigi - Run 5",
    "animations/movement_animations/luigi_run/luigi_run_left(6).png": "Luigi - Run 6",
    "animations/movement_animations/luigi_run/luigi_run_left(7).png": "Luigi - Run 7",
    "animations/movement_animations/luigi_run/luigi_run_left(8).png": "Luigi - Run 8",

    "animations/movement_animations/luigi_dash/luigi_dash_left(1).png": "Luigi - Dash 1",
    "animations/movement_animations/luigi_dash/luigi_dash_left(2).png": "Luigi - Dash 2",
    "animations/movement_animations/luigi_dash/luigi_dash_left(3).png": "Luigi - Dash 3",
    "animations/movement_animations/luigi_dash/luigi_dash_left(4).png": "Luigi - Dash 4",
    "animations/movement_animations/luigi_dash/luigi_dash_left(5).png": "Luigi - Dash 5",
    "animations/movement_animations/luigi_dash/luigi_dash_left(6).png": "Luigi - Dash 6",

    "animations/movement_animations/luigi_jump/luigi_jump_left(1).png": "Luigi - Jump 1",
    "animations/movement_animations/luigi_jump/luigi_jump_left(2).png": "Luigi - Jump 2",
    "animations/movement_animations/luigi_jump/luigi_jump_left(3).png": "Luigi - Jump 3",
    "animations/movement_animations/luigi_jump/luigi_jump_left(4).png": "Luigi - Jump 4",
    "animations/movement_animations/luigi_jump/luigi_fall_left.png": "Luigi - Fall",
    "animations/movement_animations/luigi_jump/luigi_land_left.png": "Luigi - Land",

    "animations/movement_animations/luigi_double_jump/luigi_double_jump_left(1).png": "Luigi - Double Jump 1",
    "animations/movement_animations/luigi_double_jump/luigi_double_jump_left(2).png": "Luigi - Double Jump 2",
    "animations/movement_animations/luigi_double_jump/luigi_double_jump_left(3).png": "Luigi - Double Jump 3",
    "animations/movement_animations/luigi_double_jump/luigi_double_jump_left(4).png": "Luigi - Double Jump 4",
    "animations/movement_animations/luigi_double_jump/luigi_double_jump_left(5).png": "Luigi - Double Jump 5",

    # === LIGHT ATTACK COMBO ===
    "animations/attack_animations/light_attack_combo/luigi_light_attack_left(version1,(1)).png": "Luigi - Light V1 1",
    "animations/attack_animations/light_attack_combo/luigi_light_attack_left(version1,(2)).png": "Luigi - Light V1 2",
    "animations/attack_animations/light_attack_combo/luigi_light_attack_left(version1,(3)).png": "Luigi - Light V1 3",
    "animations/attack_animations/light_attack_combo/luigi_light_attack_left(version2,(1)).png": "Luigi - Light V2 1",
    "animations/attack_animations/light_attack_combo/luigi_light_attack_left(version2,(2)).png": "Luigi - Light V2 2",
    "animations/attack_animations/light_attack_combo/luigi_light_attack_left(version2,(3)).png": "Luigi - Light V2 3",
    "animations/attack_animations/light_attack_combo/luigi_light_attack_left(version3,(1)).png": "Luigi - Light V3 1",
    "animations/attack_animations/light_attack_combo/luigi_light_attack_left(version3,(2)).png": "Luigi - Light V3 2",
    "animations/attack_animations/light_attack_combo/luigi_light_attack_left(version3,(3)).png": "Luigi - Light V3 3",
    "animations/attack_animations/light_attack_combo/luigi_light_attack_left(version3,(4)).png": "Luigi - Light V3 4",

    # === HEAVY ATTACK COMBO ===
    "animations/attack_animations/heavy_attack_combo/luigi_heavy_attack_left(version1,(1)).png": "Luigi - Heavy V1 1",
    "animations/attack_animations/heavy_attack_combo/luigi_heavy_attack_left(version1,(2)).png": "Luigi - Heavy V1 2",
    "animations/attack_animations/heavy_attack_combo/luigi_heavy_attack_left(version1,(3)).png": "Luigi - Heavy V1 3",
    "animations/attack_animations/heavy_attack_combo/luigi_heavy_attack_left(version1,(4)).png": "Luigi - Heavy V1 4",
    "animations/attack_animations/heavy_attack_combo/luigi_heavy_attack_left(version2,(1)).png": "Luigi - Heavy V2 1",
    "animations/attack_animations/heavy_attack_combo/luigi_heavy_attack_left(version2,(2)).png": "Luigi - Heavy V2 2",
    "animations/attack_animations/heavy_attack_combo/luigi_heavy_attack_left(version2,(3)).png": "Luigi - Heavy V2 3",
    "animations/attack_animations/heavy_attack_combo/luigi_heavy_attack_left(version2,(4)).png": "Luigi - Heavy V2 4",
    "animations/attack_animations/heavy_attack_combo/luigi_heavy_attack_left(version3,(1)).png": "Luigi - Heavy V3 1",
    "animations/attack_animations/heavy_attack_combo/luigi_heavy_attack_left(version3,(2)).png": "Luigi - Heavy V3 2",
    "animations/attack_animations/heavy_attack_combo/luigi_heavy_attack_left(version3,(3)).png": "Luigi - Heavy V3 3",
    "animations/attack_animations/heavy_attack_combo/luigi_heavy_attack_left(version3,(4)).png": "Luigi - Heavy V3 4",

    # === AIR ATTACKS ===
    "animations/attack_animations/air_attack_light/luigi_air_attack_light_left(1).png": "Luigi - Air Light 1",
    "animations/attack_animations/air_attack_light/luigi_air_attack_light_left(2).png": "Luigi - Air Light 2",
    "animations/attack_animations/air_attack_heavy/luigi_air_attack_heavy_left(1).png": "Luigi - Air Heavy 1",
    "animations/attack_animations/air_attack_heavy/luigi_air_attack_heavy_left(2).png": "Luigi - Air Heavy 2",
    "animations/attack_animations/air_attack_heavy/luigi_air_attack_heavy_left(3).png": "Luigi - Air Heavy 3",
    "animations/attack_animations/air_attack_heavy/luigi_air_attack_heavy_left(4).png": "Luigi - Air Heavy 4",

    # === BLOCK ===
    "animations/attack_animations/block&air_block/luigi_block_left(1).png": "Luigi - Block 1",
    "animations/attack_animations/block&air_block/luigi_block_left(2).png": "Luigi - Block 2",
    "animations/attack_animations/block&air_block/luigi_air_block_left(1).png": "Luigi - Air Block 1",
    "animations/attack_animations/block&air_block/luigi_air_block_left(2).png": "Luigi - Air Block 2",

    # === SPECIALS ===
    "animations/attack_animations/head_drill_special/luigi_head_drill_special_left(1).png": "Luigi - Head Drill 1",
    "animations/attack_animations/head_drill_special/luigi_head_drill_special_left(2).png": "Luigi - Head Drill 2",
    "animations/attack_animations/head_drill_special/luigi_head_drill_special_left(3).png": "Luigi - Head Drill 3",
    "animations/attack_animations/head_drill_special/luigi_head_drill_special_left(4).png": "Luigi - Head Drill 4",
    "animations/attack_animations/head_drill_special/luigi_head_drill_special_left(5).png": "Luigi - Head Drill 5",

    "animations/attack_animations/luigi_special_blastshot/luigi_air_shot_special_left_air(1).png": "Luigi - Air Shot Air 1",
    "animations/attack_animations/luigi_special_blastshot/luigi_air_shot_special_left_air(2).png": "Luigi - Air Shot Air 2",
    "animations/attack_animations/luigi_special_blastshot/luigi_air_shot_special_left_air(3).png": "Luigi - Air Shot Air 3",
    "animations/attack_animations/luigi_special_blastshot/luigi_air_shot_special_left_air(4).png": "Luigi - Air Shot Air 4",
    "animations/attack_animations/luigi_special_blastshot/luigi_air_shot_special_left_air(5).png": "Luigi - Air Shot Air 5",
    "animations/attack_animations/luigi_special_blastshot/luigi_air_shot_special_left_land(1).png": "Luigi - Air Shot Land 1",
    "animations/attack_animations/luigi_special_blastshot/luigi_air_shot_special_left_land(2).png": "Luigi - Air Shot Land 2",
    "animations/attack_animations/luigi_special_blastshot/luigi_air_shot_special_left_land(3).png": "Luigi - Air Shot Land 3",
    "animations/attack_animations/luigi_special_blastshot/luigi_air_shot_special_left_land(4).png": "Luigi - Air Shot Land 4",
    "animations/attack_animations/luigi_special_blastshot/luigi_air_shot_special_left_land(5).png": "Luigi - Air Shot Land 5",

    # === TAUNT ===
    "animations/other_animations/luigi_taunt/luigi_taunt(1).png": "Luigi - Taunt 1",
    "animations/other_animations/luigi_taunt/luigi_taunt(2).png": "Luigi - Taunt 2",
    "animations/other_animations/luigi_taunt/luigi_taunt(3).png": "Luigi - Taunt 3",
    "animations/other_animations/luigi_taunt/luigi_taunt(4).png": "Luigi - Taunt 4",
    "animations/other_animations/luigi_taunt/luigi_taunt(5).png": "Luigi - Taunt 5",
    "animations/other_animations/luigi_taunt/luigi_taunt(6).png": "Luigi - Taunt 6",
    "animations/other_animations/luigi_taunt/luigi_taunt(7).png": "Luigi - Taunt 7",

    # === LEDGE GRAB ===
    "animations/movement_animations/ledge_grab/luigi_ledge_grab(1).png": "Luigi - Ledge Grab 1",
    "animations/movement_animations/ledge_grab/luigi_ledge_grab(2).png": "Luigi - Ledge Grab 2",
    "animations/movement_animations/ledge_grab/luigi_ledge_grab(3).png": "Luigi - Ledge Grab 3",
}

YOSHI_FILE_MAP = {
    # === IDLE ===
    "animations/other_animations/idle_version_1/yoshi_idle_left(1,version1).png": "Yoshi - Idle 1",
    "animations/other_animations/idle_version_1/yoshi_idle_left(2,version1).png": "Yoshi - Idle 2",
    "animations/other_animations/idle_version_1/yoshi_idle_left(3,version1).png": "Yoshi - Idle 3",
    "animations/other_animations/idle_version_1/yoshi_idle_left(4,version1).png": "Yoshi - Idle 4",
    "animations/other_animations/idle_version_1/yoshi_idle_left(5,version1).png": "Yoshi - Idle 5",

    # === RUN ===
    "animations/movement_animations/yoshi_run/yoshi_run_left(1).png": "Yoshi - Run 1",
    "animations/movement_animations/yoshi_run/yoshi_run_left(2).png": "Yoshi - Run 2",
    "animations/movement_animations/yoshi_run/yoshi_run_left(3).png": "Yoshi - Run 3",
    "animations/movement_animations/yoshi_run/yoshi_run_left(4).png": "Yoshi - Run 4",
    "animations/movement_animations/yoshi_run/yoshi_run_left(5).png": "Yoshi - Run 5",
    "animations/movement_animations/yoshi_run/yoshi_run_left(6).png": "Yoshi - Run 6",
    "animations/movement_animations/yoshi_run/yoshi_run_left(7).png": "Yoshi - Run 7",
    "animations/movement_animations/yoshi_run/yoshi_run_left(8).png": "Yoshi - Run 8",

    # === DASH ===
    "animations/movement_animations/yoshi_dash/yoshi_dash_left(1).png": "Yoshi - Dash 1",
    "animations/movement_animations/yoshi_dash/yoshi_dash_left(2).png": "Yoshi - Dash 2",

    # === JUMP ===
    "animations/movement_animations/yoshi_jump&double_jump/yoshi_jump_left(1).png": "Yoshi - Jump 1",
    "animations/movement_animations/yoshi_jump&double_jump/yoshi_jump_left(2).png": "Yoshi - Jump 2",

    # === DOUBLE JUMP ===
    "animations/movement_animations/yoshi_jump&double_jump/yoshi_double_jump(1).png": "Yoshi - Double Jump 1",
    "animations/movement_animations/yoshi_jump&double_jump/yoshi_double_jump(2).png": "Yoshi - Double Jump 2",
    "animations/movement_animations/yoshi_jump&double_jump/yoshi_double_jump(3).png": "Yoshi - Double Jump 3",
    "animations/movement_animations/yoshi_jump&double_jump/yoshi_double_jump(4).png": "Yoshi - Double Jump 4",
    "animations/movement_animations/yoshi_jump&double_jump/yoshi_double_jump(5).png": "Yoshi - Double Jump 5",

    # === FALL ===
    "animations/movement_animations/yoshi_fall/yoshi_fall_left(1).png": "Yoshi - Fall 1",
    "animations/movement_animations/yoshi_fall/yoshi_fall_left(2).png": "Yoshi - Fall 2",

    # === LAND ===
    "animations/movement_animations/yoshi_land/yoshi_land_left(1).png": "Yoshi - Land 1",
    "animations/movement_animations/yoshi_land/yoshi_land_left(2).png": "Yoshi - Land 2",

    # === ROLL (slide) ===
    "animations/movement_animations/yoshi_roll/yoshi_roll_left(1).png": "Yoshi - Roll 1",
    "animations/movement_animations/yoshi_roll/yoshi_roll_left(2).png": "Yoshi - Roll 2",
    "animations/movement_animations/yoshi_roll/yoshi_roll_left(3).png": "Yoshi - Roll 3",
    "animations/movement_animations/yoshi_roll/yoshi_roll_left(4).png": "Yoshi - Roll 4",
    "animations/movement_animations/yoshi_roll/yoshi_roll_left(5).png": "Yoshi - Roll 5",
    "animations/movement_animations/yoshi_roll/yoshi_roll_left(6).png": "Yoshi - Roll 6",
    "animations/movement_animations/yoshi_roll/yoshi_roll_left(7).png": "Yoshi - Roll 7",
    "animations/movement_animations/yoshi_roll/yoshi_roll_left(8).png": "Yoshi - Roll 8",
    "animations/movement_animations/yoshi_roll/yoshi_roll_left(9).png": "Yoshi - Roll 9",

    # === HURT ===
    "animations/other_animations/yoshi_hurt/yoshi_hurt_left(1).png": "Yoshi - Hurt 1",
    "animations/other_animations/yoshi_hurt/yoshi_hurt_left(2).png": "Yoshi - Hurt 2",

    # === LIGHT ATTACK COMBO (3 versions × 4 frames) ===
    "animations/attack_animations/light_attack_combo/yoshi_light_attack,version1_left,(1).png": "Yoshi - Light V1 1",
    "animations/attack_animations/light_attack_combo/yoshi_light_attack,version1_left,(2).png": "Yoshi - Light V1 2",
    "animations/attack_animations/light_attack_combo/yoshi_light_attack,version1_left,(3).png": "Yoshi - Light V1 3",
    "animations/attack_animations/light_attack_combo/yoshi_light_attack,version1_left,(4).png": "Yoshi - Light V1 4",
    "animations/attack_animations/light_attack_combo/yoshi_light_attack,version2_left(1).png": "Yoshi - Light V2 1",
    "animations/attack_animations/light_attack_combo/yoshi_light_attack,version2_left(2).png": "Yoshi - Light V2 2",
    "animations/attack_animations/light_attack_combo/yoshi_light_attack,version2_left(3).png": "Yoshi - Light V2 3",
    "animations/attack_animations/light_attack_combo/yoshi_light_attack,version2_left(4).png": "Yoshi - Light V2 4",
    "animations/attack_animations/light_attack_combo/yoshi_light_attack,version3_left,(1).png": "Yoshi - Light V3 1",
    "animations/attack_animations/light_attack_combo/yoshi_light_attack,version3_left,(2).png": "Yoshi - Light V3 2",
    "animations/attack_animations/light_attack_combo/yoshi_light_attack,version3_left,(3).png": "Yoshi - Light V3 3",
    "animations/attack_animations/light_attack_combo/yoshi_light_attack,version3_left,(4).png": "Yoshi - Light V3 4",

    # === HEAVY ATTACK COMBO (3 versions) ===
    "animations/attack_animations/heavy_attack_combo/yoshi_heavy_attack,version1_left(1).png": "Yoshi - Heavy V1 1",
    "animations/attack_animations/heavy_attack_combo/yoshi_heavy_attack,version1_left(2).png": "Yoshi - Heavy V1 2",
    "animations/attack_animations/heavy_attack_combo/yoshi_heavy_attack,version1_left(3).png": "Yoshi - Heavy V1 3",
    "animations/attack_animations/heavy_attack_combo/yoshi_heavy_attack,version1_left(4).png": "Yoshi - Heavy V1 4",
    "animations/attack_animations/heavy_attack_combo/yoshi_heavy_attack,version1_left(5).png": "Yoshi - Heavy V1 5",
    "animations/attack_animations/heavy_attack_combo/yoshi_heavy_attack,version2_left(1).png": "Yoshi - Heavy V2 1",
    "animations/attack_animations/heavy_attack_combo/yoshi_heavy_attack,version2_left(2).png": "Yoshi - Heavy V2 2",
    "animations/attack_animations/heavy_attack_combo/yoshi_heavy_attack,version2_left(3).png": "Yoshi - Heavy V2 3",
    "animations/attack_animations/heavy_attack_combo/yoshi_heavy_attack,version2_left(4).png": "Yoshi - Heavy V2 4",
    "animations/attack_animations/heavy_attack_combo/yoshi_heavy_attack,version2_left(5).png": "Yoshi - Heavy V2 5",
    "animations/attack_animations/heavy_attack_combo/yoshi_heavy_attack,version3_left(1).png": "Yoshi - Heavy V3 1",
    "animations/attack_animations/heavy_attack_combo/yoshi_heavy_attack,version3_left(2).png": "Yoshi - Heavy V3 2",
    "animations/attack_animations/heavy_attack_combo/yoshi_heavy_attack,version3_left(3).png": "Yoshi - Heavy V3 3",
    "animations/attack_animations/heavy_attack_combo/yoshi_heavy_attack,version3_left(4).png": "Yoshi - Heavy V3 4",
    "animations/attack_animations/heavy_attack_combo/yoshi_heavy_attack,version3_left(5).png": "Yoshi - Heavy V3 5",
    "animations/attack_animations/heavy_attack_combo/yoshi_heavy_attack,version3_left(6).png": "Yoshi - Heavy V3 6",

    # === COMBO RESET FRAME ===
    "animations/attack_animations/yoshi_egg_shell_throw/yoshi_attack_combo_reset_frame_left.png": "Yoshi - Combo Reset",

    # === AIR ATTACKS ===
    "animations/attack_animations/air_attack_heavy&light/yoshi_air_attack_left_light(1).png": "Yoshi - Air Light 1",
    "animations/attack_animations/air_attack_heavy&light/yoshi_air_attack_left_light(2).png": "Yoshi - Air Light 2",
    "animations/attack_animations/air_attack_heavy&light/yoshi_air_attack_left_heavy(1).png": "Yoshi - Air Heavy 1",
    "animations/attack_animations/air_attack_heavy&light/yoshi_air_attack_left_heavy(2).png": "Yoshi - Air Heavy 2",

    # === AIR BLOCK (counter) ===
    "animations/attack_animations/yoshi_air_block/yoshi_air_block_left(1).png": "Yoshi - Air Block 1",
    "animations/attack_animations/yoshi_air_block/yoshi_air_block_left(2).png": "Yoshi - Air Block 2",

    # === EGG ROLL (Special E) ===
    "animations/attack_animations/Special_Move/yoshi_special_roll_left(1).png": "Yoshi - Egg Roll 1",
    "animations/attack_animations/Special_Move/yoshi_special_roll_left(2).png": "Yoshi - Egg Roll 2",
    "animations/attack_animations/Special_Move/yoshi_special_roll_left(3).png": "Yoshi - Egg Roll 3",
    "animations/attack_animations/Special_Move/yoshi_special_roll_left(4).png": "Yoshi - Egg Roll 4",
    "animations/attack_animations/Special_Move/yoshi_special_roll_left(5).png": "Yoshi - Egg Roll 5",
    "animations/attack_animations/Special_Move/yoshi_special_roll_left(6).png": "Yoshi - Egg Roll 6",
    "animations/attack_animations/Special_Move/yoshi_special_roll_left(7).png": "Yoshi - Egg Roll 7",
    "animations/attack_animations/Special_Move/yoshi_special_roll_left(8).png": "Yoshi - Egg Roll 8",

    # === EGG THROW (Special Q - ground) ===
    "animations/attack_animations/yoshi_egg_shell_throw/yoshi_egg_shell_throw_land_left(1).png": "Yoshi - Egg Throw G1",
    "animations/attack_animations/yoshi_egg_shell_throw/yoshi_egg_shell_throw_land_left(2).png": "Yoshi - Egg Throw G2",
    "animations/attack_animations/yoshi_egg_shell_throw/yoshi_egg_shell_throw_land_left(3).png": "Yoshi - Egg Throw G3",
    "animations/attack_animations/yoshi_egg_shell_throw/yoshi_egg_shell_throw_land_left(4).png": "Yoshi - Egg Throw G4",
    "animations/attack_animations/yoshi_egg_shell_throw/yoshi_egg_shell_throw_land_left(5).png": "Yoshi - Egg Throw G5",
    "animations/attack_animations/yoshi_egg_shell_throw/yoshi_egg_shell_throw_land_left(6).png": "Yoshi - Egg Throw G6",
    "animations/attack_animations/yoshi_egg_shell_throw/yoshi_egg_shell_throw_land_left(7).png": "Yoshi - Egg Throw G7",

    # === EGG THROW (Special Q - air) ===
    "animations/attack_animations/yoshi_egg_shell_throw/egg_shell_throw_air_left(1).png": "Yoshi - Egg Throw A1",
    "animations/attack_animations/yoshi_egg_shell_throw/egg_shell_throw_air_left(2).png": "Yoshi - Egg Throw A2",
    "animations/attack_animations/yoshi_egg_shell_throw/egg_shell_throw_air_left(3).png": "Yoshi - Egg Throw A3",
    "animations/attack_animations/yoshi_egg_shell_throw/egg_shell_throw_air_left(4).png": "Yoshi - Egg Throw A4",
    "animations/attack_animations/yoshi_egg_shell_throw/egg_shell_throw_air_left(5).png": "Yoshi - Egg Throw A5",
    "animations/attack_animations/yoshi_egg_shell_throw/egg_shell_throw_air_left(6).png": "Yoshi - Egg Throw A6",

    # === EGG PROJECTILE ===
    "animations/attack_animations/yoshi_egg_shell_throw/egg_shell_idle.png": "Yoshi - Egg Idle",
    "animations/attack_animations/yoshi_egg_shell_throw/egg_shell_left(1).png": "Yoshi - Egg Spin 1",
    "animations/attack_animations/yoshi_egg_shell_throw/egg_shell_left(2).png": "Yoshi - Egg Spin 2",
    "animations/attack_animations/yoshi_egg_shell_throw/egg_shell_left(3).png": "Yoshi - Egg Spin 3",
    "animations/attack_animations/yoshi_egg_shell_throw/egg_shell_left(4).png": "Yoshi - Egg Spin 4",

    # === EGG LAY (eat NPC → egg) ===
    "animations/attack_animations/yoshi_egg_lay/yoshi_egg_lay_left(1).png": "Yoshi - Egg Lay 1",
    "animations/attack_animations/yoshi_egg_lay/yoshi_egg_lay_left(2).png": "Yoshi - Egg Lay 2",
    "animations/attack_animations/yoshi_egg_lay/yoshi_egg_lay_left(3).png": "Yoshi - Egg Lay 3",
    "animations/attack_animations/yoshi_egg_lay/yoshi_egg_lay_left(4).png": "Yoshi - Egg Lay 4",
    "animations/attack_animations/yoshi_egg_lay/yoshi_egg_lay_left(5).png": "Yoshi - Egg Lay 5",
    "animations/attack_animations/yoshi_egg_lay/yoshi_egg_lay_left(6).png": "Yoshi - Egg Lay 6",
    "animations/attack_animations/yoshi_egg_lay/yoshi_egg_lay_left(7).png": "Yoshi - Egg Lay 7",
    "animations/attack_animations/yoshi_egg_lay/yoshi_egg_lay_left(8).png": "Yoshi - Egg Lay 8",
    "animations/attack_animations/yoshi_egg_lay/yoshi_egg_lay_left(9).png": "Yoshi - Egg Lay 9",

    # === PLAYER THROW (grab + hurl behind) ===
    "animations/attack_animations/yoshi_player_throw/yoshi_throw_left(1).png": "Yoshi - Throw 1",
    "animations/attack_animations/yoshi_player_throw/yoshi_throw_left(2).png": "Yoshi - Throw 2",
    "animations/attack_animations/yoshi_player_throw/yoshi_throw_left(3).png": "Yoshi - Throw 3",
    "animations/attack_animations/yoshi_player_throw/yoshi_throw_air_left(1).png": "Yoshi - Throw Air 1",
    "animations/attack_animations/yoshi_player_throw/yoshi_throw_air_left(2).png": "Yoshi - Throw Air 2",
    "animations/attack_animations/yoshi_player_throw/yoshi_throw_air_left(3).png": "Yoshi - Throw Air 3",

    # === LEDGE GRAB ===
    "animations/movement_animations/yoshi_ledge_grab/yoshi_ledge_grab(1).png": "Yoshi - Ledge Grab 1",
    "animations/movement_animations/yoshi_ledge_grab/yoshi_ledge_grab(2).png": "Yoshi - Ledge Grab 2",
}

DONKEY_KONG_FILE_MAP = {
    # === IDLE ===
    "sprites (1)/donkey_kong_idle.png": "DK - Idle",

    # === RUN ===
    "sprites (1)/donkey_kong_run(1).png": "DK - Run 1",
    "sprites (1)/donkey_kong_run(2).png": "DK - Run 2",
    "sprites (1)/donkey_kong_run(3).png": "DK - Run 3",
    "sprites (1)/donkey_kong_run(4).png": "DK - Run 4",
    "sprites (1)/donkey_kong_run(5).png": "DK - Run 5",

    # === ROLL (dash) ===
    "sprites (1)/donkey_kong_roll(1).png": "DK - Roll 1",
    "sprites (1)/donkey_kong_roll(2).png": "DK - Roll 2",
    "sprites (1)/donkey_kong_roll(3).png": "DK - Roll 3",
    "sprites (1)/donkey_kong_roll(4).png": "DK - Roll 4",
    "sprites (1)/donkey_kong_roll(5).png": "DK - Roll 5",
    "sprites (1)/donkey_kong_roll(6).png": "DK - Roll 6",
    "sprites (1)/donkey_kong_roll(7).png": "DK - Roll 7",

    # === JUMP ===
    "sprites (1)/donkey_kong_jump(1).png": "DK - Jump 1",
    "sprites (1)/donkey_kong_jump(2).png": "DK - Jump 2",
    "sprites (1)/donkey_kong_jump(3).png": "DK - Jump 3",

    # === FALL ===
    "sprites (1)/donkey_kong_fall.png": "DK - Fall",

    # === HURT ===
    "sprites (1)/donkey_kong_hurt_light(1).png": "DK - Hurt Light",
    "sprites (1)/donkey_kong_hurt_heavy(1).png": "DK - Hurt Heavy 1",
    "sprites (1)/donkey_kong_hurt_heavy(2).png": "DK - Hurt Heavy 2",

    # === BLOCK ===
    "sprites (1)/donkey_kong_block.png": "DK - Block",

    # === COMBO LIGHT ===
    "sprites (1)/donkey_kong_combo_light(version1,(1)).png": "DK - Light V1 1",
    "sprites (1)/donkey_kong_combo_light(version1,(2))-(impact_frame).png": "DK - Light V1 2",
    "sprites (1)/donkey_kong_combo_light(version1,(3)).png": "DK - Light V1 3",
    "sprites (1)/donkey_kong_combo_light(version1,(4)).png": "DK - Light V1 4",
    "sprites (1)/donkey_kong_combo_light(version1,(5))-(impact_frame).png": "DK - Light V1 5",
    "sprites (1)/donkey_kong_combo_light(version2,(1)).png": "DK - Light V2 1",
    "sprites (1)/donkey_kong_combo_light(version2,(2)).png": "DK - Light V2 2",
    "sprites (1)/donkey_kong_combo_light(version2,(3))-(impact_frame).png": "DK - Light V2 3",
    "sprites (1)/donkey_kong_combo_light(version2,(4)).png": "DK - Light V2 4",
    "sprites (1)/donkey_kong_combo_light(version2,(5)).png": "DK - Light V2 5",

    # === COMBO HEAVY ===
    "sprites (1)/donkey_kong_combo_heavy(version1,(1)).png": "DK - Heavy V1 1",
    "sprites (1)/donkey_kong_combo_heavy(version1,(2))-(impact_frame)).png": "DK - Heavy V1 2",
    "sprites (1)/donkey_kong_combo_heavy(version2,(1)).png": "DK - Heavy V2 1",
    "sprites (1)/donkey_kong_combo_heavy(version2,(2))-(impact_frame).png": "DK - Heavy V2 2",
    "sprites (1)/donkey_kong_combo_heavy(version2,(3)).png": "DK - Heavy V2 3",
    "sprites (1)/donkey_kong_combo_heavy(version3,(1)).png": "DK - Heavy V3 1",
    "sprites (1)/donkey_kong_combo_heavy(version3,(2))-(impact_frame).png": "DK - Heavy V3 2",

    # === SPECIAL SMASH (E - ground) ===
    "sprites (1)/donkey_kong_special_smash(1).png": "DK - Special Smash 1",
    "sprites (1)/donkey_kong_special_smash(2).png": "DK - Special Smash 2",
    "sprites (1)/donkey_kong_special_smash(3).png": "DK - Special Smash 3",
    "sprites (1)/donkey_kong_special_smash(4).png": "DK - Special Smash 4",
    "sprites (1)/donkey_kong_special_smash(5).png": "DK - Special Smash 5",

    # === BARREL THROW (Q - special) ===
    "sprites (1)/donkey_kong_barrel_throw(1).png": "DK - Barrel Throw 1",
    "sprites (1)/donkey_kong_barrel_throw(2).png": "DK - Barrel Throw 2",
    "sprites (1)/donkey_kong_barrel_throw(3).png": "DK - Barrel Throw 3",
    "sprites (1)/donkey_kong_barrel_throw(4).png": "DK - Barrel Throw 4",
    "sprites (1)/donkey_kong_barrel_throw(5).png": "DK - Barrel Throw 5",
    "sprites (1)/donkey_kong_barrel_throw(6).png": "DK - Barrel Throw 6",
    "sprites (1)/donkey_kong_barrel_throw(7).png": "DK - Barrel Throw 7",

    # === TAUNT ===
    "sprites (1)/donkey_kong_taunt(1).png": "DK - Taunt 1",
    "sprites (1)/donkey_kong_taunt(2).png": "DK - Taunt 2",
    "sprites (1)/donkey_kong_taunt(3).png": "DK - Taunt 3",
    "sprites (1)/donkey_kong_taunt(4).png": "DK - Taunt 4",
    "sprites (1)/donkey_kong_taunt(5).png": "DK - Taunt 5",
    "sprites (1)/donkey_kong_taunt(6).png": "DK - Taunt 6",
    "sprites (1)/donkey_kong_taunt(7).png": "DK - Taunt 7",

    # === LEDGE GRAB ===
    "sprites (1)/donkey_kong_ledge_grab(1).png": "DK - Ledge Grab 1",
    "sprites (1)/donkey_kong_ledge_grab(2).png": "DK - Ledge Grab 2",
    "sprites (1)/donkey_kong_ledge_grab(3).png": "DK - Ledge Grab 3",
}

class SpriteLoader:
    def __init__(self, directory: str, file_map: dict, scale: int = 3,
                 flip_x: bool = True, target_height: int = None,
                 max_width_ratio: float = None):
        self.scale = scale
        self._cache: dict[str, pygame.Surface] = {}

        for fname, key in file_map.items():
            path = os.path.join(directory, fname)
            if not os.path.exists(path):
                print(f"[WARNING] Missing sprite: {path}")
                continue

            raw = pygame.image.load(path)

            # ── Auto-detect whether the PNG uses real alpha transparency ──
            has_alpha = False
            if raw.get_bitsize() == 32:
                w, h = raw.get_size()
                step = max(1, min(w, h) // 5)
                for cx in range(0, w, step):
                    for cy in range(0, h, step):
                        if raw.get_at((cx, cy))[3] < 255:
                            has_alpha = True
                            break
                    if has_alpha:
                        break

            if has_alpha:
                surf = raw.convert_alpha()
            else:
                surf = raw.convert()
                surf.set_colorkey((0, 0, 0))
                alpha_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
                alpha_surf.blit(surf, (0, 0))
                surf = alpha_surf

            if flip_x:
                surf = pygame.transform.flip(surf, True, False)

            if target_height is not None:
                orig_w, orig_h = surf.get_size()
                if orig_h > 0:
                    ratio = target_height / orig_h
                    final_w = max(1, int(orig_w * ratio))
                    final_h = max(1, int(orig_h * ratio))
                    if max_width_ratio is not None and final_w > final_h * max_width_ratio:
                        final_w = max(1, int(final_h * max_width_ratio))
                    surf = pygame.transform.smoothscale(surf, (final_w, final_h))
            elif scale != 1:
                w = surf.get_width() * scale
                h = surf.get_height() * scale
                surf = pygame.transform.scale(surf, (w, h))
            self._cache[key] = surf

    def get(self, label: str) -> pygame.Surface:
        return self._cache.get(label)

    def get_flipped(self, label: str) -> pygame.Surface:
        surf = self.get(label)
        return pygame.transform.flip(surf, True, False) if surf else None


def load_grrrol_sprites(directory="Npc's/grrrol", scale=1):
    """Load grrrol rolling animation frames."""
    frames = []
    for i in range(1, 9):
        path = os.path.join(directory, f"grrrol_roll_right({i}).png")
        if os.path.exists(path):
            raw = pygame.image.load(path)
            has_alpha = False
            if raw.get_bitsize() == 32:
                w, h = raw.get_size()
                step = max(1, min(w, h) // 5)
                for cx in range(0, w, step):
                    for cy in range(0, h, step):
                        if raw.get_at((cx, cy))[3] < 255:
                            has_alpha = True
                            break
                    if has_alpha:
                        break
            if has_alpha:
                surf = raw.convert_alpha()
            else:
                surf = raw.convert()
                surf.set_colorkey((0, 0, 0))
                alpha_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
                alpha_surf.blit(surf, (0, 0))
                surf = alpha_surf
            if scale != 1:
                w = surf.get_width() * scale
                h = surf.get_height() * scale
                surf = pygame.transform.scale(surf, (w, h))
            frames.append(surf)
    return frames


def load_bobomb_sprites(directory="Npc's/para_bomb", target_height=42):
    """Load para-bomb sprites: fall, start-explode, and explosion frames."""
    sprites = {}

    def _load_img(path, th):
        raw = pygame.image.load(path)
        has_alpha = False
        if raw.get_bitsize() == 32:
            w, h = raw.get_size()
            step = max(1, min(w, h) // 5)
            for cx in range(0, w, step):
                for cy in range(0, h, step):
                    if raw.get_at((cx, cy))[3] < 255:
                        has_alpha = True
                        break
                if has_alpha:
                    break
        if has_alpha:
            surf = raw.convert_alpha()
        else:
            surf = raw.convert()
            surf.set_colorkey((0, 0, 0))
            alpha_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            alpha_surf.blit(surf, (0, 0))
            surf = alpha_surf
        orig_w, orig_h = surf.get_size()
        if orig_h > 0:
            ratio = th / orig_h
            new_w = max(1, int(orig_w * ratio))
            new_h = max(1, int(orig_h * ratio))
            surf = pygame.transform.smoothscale(surf, (new_w, new_h))
        return surf

    # Fall sprite
    fall_path = os.path.join(directory, "para_bomb_fall.png")
    if os.path.exists(fall_path):
        sprites["fall"] = _load_img(fall_path, target_height)

    # Glide sprites (left/right)
    for side in ("left", "right"):
        path = os.path.join(directory, f"para-bomb_glide_{side}.png")
        if os.path.exists(path):
            sprites[f"glide_{side}"] = _load_img(path, target_height)

    # About-to-land sprites (left/right)
    for side in ("left", "right"):
        path = os.path.join(directory, f"para_bomb_abouttoland_{side}.png")
        if os.path.exists(path):
            sprites[f"abouttoland_{side}"] = _load_img(path, target_height)

    # Start-explode frames
    sprites["start_explode"] = []
    for i in range(1, 3):
        path = os.path.join(directory, f"para_bomb_startexplode({i}).png")
        if os.path.exists(path):
            sprites["start_explode"].append(_load_img(path, target_height))

    # Explosion frames (larger)
    sprites["explosion"] = []
    for i in range(1, 5):
        path = os.path.join(directory, f"para_bomb_explosion({i}).png")
        if os.path.exists(path):
            sprites["explosion"].append(_load_img(path, 120))

    return sprites


def load_kamek_sprites(directory="Npc's/kamek", target_height=28):
    """Load Kamek sprites: fly, attack, ascending, magic projectile, magic explosion."""
    sprites = {}

    def _load_img(path, th):
        raw = pygame.image.load(path)
        has_alpha = False
        if raw.get_bitsize() == 32:
            w, h = raw.get_size()
            step = max(1, min(w, h) // 5)
            for cx in range(0, w, step):
                for cy in range(0, h, step):
                    if raw.get_at((cx, cy))[3] < 255:
                        has_alpha = True
                        break
                if has_alpha:
                    break
        if has_alpha:
            surf = raw.convert_alpha()
        else:
            surf = raw.convert()
            surf.set_colorkey((0, 0, 0))
            alpha_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            alpha_surf.blit(surf, (0, 0))
            surf = alpha_surf
        orig_w, orig_h = surf.get_size()
        if orig_h > 0:
            ratio = th / orig_h
            new_w = max(1, int(orig_w * ratio))
            new_h = max(1, int(orig_h * ratio))
            surf = pygame.transform.smoothscale(surf, (new_w, new_h))
        return surf

    sprites["fly_right"] = []
    for i in range(1, 3):
        path = os.path.join(directory, f"kamek_fly_right({i}).png")
        if os.path.exists(path):
            sprites["fly_right"].append(_load_img(path, target_height))
    sprites["fly_left"] = [pygame.transform.flip(f, True, False) for f in sprites["fly_right"]]

    sprites["fly_ascending_right"] = []
    for i in range(1, 3):
        path = os.path.join(directory, f"kamek_fly_ascending_right({i}).png")
        if os.path.exists(path):
            sprites["fly_ascending_right"].append(_load_img(path, target_height))
    sprites["fly_ascending_left"] = [pygame.transform.flip(f, True, False) for f in sprites["fly_ascending_right"]]

    sprites["attack_right"] = []
    for i in range(1, 3):
        path = os.path.join(directory, f"kamek_attack_right({i}).png")
        if os.path.exists(path):
            sprites["attack_right"].append(_load_img(path, target_height))
    sprites["attack_left"] = [pygame.transform.flip(f, True, False) for f in sprites["attack_right"]]

    sprites["magic"] = []
    for i in range(1, 6):
        path = os.path.join(directory, f"magic_leaving_wand({i}).png")
        if os.path.exists(path):
            sprites["magic"].append(_load_img(path, 16))

    sprites["magic_exploding"] = []
    for i in range(1, 5):
        path = os.path.join(directory, f"magic_exploding({i}).png")
        if os.path.exists(path):
            sprites["magic_exploding"].append(_load_img(path, 24))

    path = os.path.join(directory, "magic_exploded.png")
    if os.path.exists(path):
        sprites["magic_exploded"] = _load_img(path, 24)

    return sprites
