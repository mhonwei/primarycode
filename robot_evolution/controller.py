"""
机器人控制器 - 基于中枢模式发生器 (CPG) 的关节控制

每个关节使用正弦波控制信号:
  target_angle = amplitude * sin(2π * frequency * t + phase_offset)

电机扭矩通过 PD 控制器驱动关节跟踪目标角度:
  torque = Kp * (target - current) + Kd * (0 - angular_velocity)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .genome import ControllerGene
from .physics import Joint


@dataclass
class JointController:
    """单个关节的控制器"""
    amplitude: float      # 振幅 (rad)
    frequency: float      # 频率 (Hz)
    phase_offset: float   # 相位偏移 (rad)
    kp: float = 200.0     # 比例增益
    kd: float = 20.0      # 微分增益

    def compute_torque(self, joint: Joint, time: float) -> float:
        """计算当前时刻的电机扭矩"""
        # 目标角度 (正弦波)
        target = self.amplitude * math.sin(
            2.0 * math.pi * self.frequency * time + self.phase_offset
        )

        # 限制在关节范围内
        target = max(joint.angle_min, min(joint.angle_max, target))

        # 当前角度和角速度
        current_angle = joint.current_angle()
        angular_vel = joint.body_b.omega - joint.body_a.omega

        # PD 控制
        error = target - current_angle
        torque = self.kp * error - self.kd * angular_vel

        return torque


class RobotController:
    """机器人整体控制器 (管理所有关节)"""

    def __init__(self):
        self.joint_controllers: dict[int, JointController] = {}

    def add_joint(self, joint_id: int, gene: ControllerGene):
        """为关节添加控制器"""
        self.joint_controllers[joint_id] = JointController(
            amplitude=gene.amplitude,
            frequency=gene.frequency,
            phase_offset=gene.phase_offset,
        )

    def update(self, joints: list[Joint], time: float):
        """更新所有关节的控制信号"""
        for joint in joints:
            ctrl = self.joint_controllers.get(joint.joint_id)
            if ctrl is not None:
                torque = ctrl.compute_torque(joint, time)
                joint.set_motor(torque)
