"""
2D 刚体物理引擎

简化但功能完整的2D物理仿真:
- 矩形刚体 (位置、角度、速度、角速度)
- 铰链关节 (revolute joint) 带电机扭矩
- 地面碰撞检测与响应
- 重力与摩擦力

设计原则: 零外部依赖, 仅使用 numpy
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

# 数值安全上限
MAX_VELOCITY = 50.0
MAX_OMEGA = 30.0
MAX_FORCE = 2000.0


def _safe(v: float) -> float:
    """NaN/Inf 保护"""
    if math.isnan(v) or math.isinf(v):
        return 0.0
    return v


def _clamp_vel(v: float, limit: float = MAX_VELOCITY) -> float:
    return max(-limit, min(limit, _safe(v)))


@dataclass
class Body:
    """2D 刚体"""
    x: float = 0.0
    y: float = 0.0
    angle: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    omega: float = 0.0

    width: float = 0.5
    height: float = 0.15
    mass: float = 1.0
    inertia: float = 1.0

    body_id: int = 0

    def __post_init__(self):
        self.mass = max(0.01, self.mass)
        self.inertia = max(0.001, self.mass * (self.width ** 2 + self.height ** 2) / 12.0)

    @property
    def position(self) -> np.ndarray:
        return np.array([self.x, self.y])

    @property
    def velocity(self) -> np.ndarray:
        return np.array([self.vx, self.vy])

    def local_to_world(self, local_point: np.ndarray) -> np.ndarray:
        c, s = math.cos(self.angle), math.sin(self.angle)
        rot = np.array([[c, -s], [s, c]])
        return rot @ local_point + np.array([self.x, self.y])

    def get_corners(self) -> np.ndarray:
        hw, hh = self.width / 2, self.height / 2
        local_corners = np.array([
            [-hw, -hh], [hw, -hh], [hw, hh], [-hw, hh],
        ])
        c, s = math.cos(self.angle), math.sin(self.angle)
        rot = np.array([[c, -s], [s, c]])
        return (local_corners @ rot.T) + np.array([self.x, self.y])

    def point_velocity(self, world_point: np.ndarray) -> np.ndarray:
        r = world_point - np.array([self.x, self.y])
        return np.array([
            self.vx - self.omega * r[1],
            self.vy + self.omega * r[0],
        ])

    def sanitize(self):
        """清理 NaN/Inf 并限制速度"""
        self.x = _safe(self.x)
        self.y = _safe(self.y)
        self.angle = _safe(self.angle)
        self.vx = _clamp_vel(self.vx)
        self.vy = _clamp_vel(self.vy)
        self.omega = _clamp_vel(self.omega, MAX_OMEGA)


@dataclass
class Joint:
    """铰链关节"""
    body_a: Body
    body_b: Body
    anchor_a_local: np.ndarray
    anchor_b_local: np.ndarray
    rest_angle: float = 0.0
    angle_min: float = -1.0
    angle_max: float = 1.0
    motor_torque: float = 0.0
    max_torque: float = 50.0
    joint_id: int = 0

    def current_angle(self) -> float:
        return self.body_b.angle - self.body_a.angle - self.rest_angle

    def set_motor(self, torque: float):
        t = max(-self.max_torque, min(self.max_torque, torque))
        self.motor_torque = _safe(t)


class PhysicsWorld:
    """2D 物理世界"""

    def __init__(
        self,
        gravity: float = -9.81,
        dt: float = 0.005,
        ground_y: float = 0.0,
        friction: float = 0.8,
        restitution: float = 0.2,
        damping: float = 0.98,
    ):
        self.gravity = gravity
        self.dt = dt
        self.ground_y = ground_y
        self.friction = friction
        self.restitution = restitution
        self.damping = damping

        self.bodies: list[Body] = []
        self.joints: list[Joint] = []
        self.time: float = 0.0
        self._next_body_id = 0
        self._next_joint_id = 0

    def add_body(self, body: Body) -> Body:
        body.body_id = self._next_body_id
        self._next_body_id += 1
        self.bodies.append(body)
        return body

    def add_joint(self, joint: Joint) -> Joint:
        joint.joint_id = self._next_joint_id
        self._next_joint_id += 1
        self.joints.append(joint)
        return joint

    def step(self):
        dt = self.dt

        # 1. 重力
        for body in self.bodies:
            body.vy += self.gravity * dt

        # 2. 关节约束 (多次迭代提高稳定性)
        for _ in range(4):
            self._solve_joints_position()

        # 3. 电机扭矩
        for joint in self.joints:
            if abs(joint.motor_torque) > 1e-6:
                torque = joint.motor_torque
                joint.body_a.omega -= torque / joint.body_a.inertia * dt
                joint.body_b.omega += torque / joint.body_b.inertia * dt

        # 4. 更新位置
        for body in self.bodies:
            body.vx *= self.damping
            body.vy *= self.damping
            body.omega *= self.damping

            body.sanitize()

            body.x += body.vx * dt
            body.y += body.vy * dt
            body.angle += body.omega * dt

        # 5. 地面碰撞
        self._solve_ground_collision()

        # 6. 关节角度限制
        self._enforce_joint_limits()

        # 7. 最终安全检查
        for body in self.bodies:
            body.sanitize()

        self.time += dt

    def _solve_joints_position(self):
        """基于位置的关节约束求解 (Baumgarte 稳定化)"""
        beta = 0.3  # 位置修正系数
        dt = self.dt

        for joint in self.joints:
            a, b = joint.body_a, joint.body_b

            anchor_a = a.local_to_world(joint.anchor_a_local)
            anchor_b = b.local_to_world(joint.anchor_b_local)

            delta = anchor_b - anchor_a
            dist = np.linalg.norm(delta)

            if dist < 1e-6:
                continue
            if dist > 10.0:  # 防止极端情况
                dist = 10.0

            direction = delta / dist

            # 位置修正: 直接移动物体使锚点靠近
            correction = delta * beta
            total_inv_mass = 1.0 / a.mass + 1.0 / b.mass
            if total_inv_mass < 1e-8:
                continue

            a.x += correction[0] * (1.0 / a.mass) / total_inv_mass
            a.y += correction[1] * (1.0 / a.mass) / total_inv_mass
            b.x -= correction[0] * (1.0 / b.mass) / total_inv_mass
            b.y -= correction[1] * (1.0 / b.mass) / total_inv_mass

            # 速度修正: 消除沿约束方向的相对速度
            vel_a = a.point_velocity(anchor_a)
            vel_b = b.point_velocity(anchor_b)
            rel_vel = np.dot(vel_b - vel_a, direction)

            impulse = rel_vel / total_inv_mass * 0.5
            impulse = max(-MAX_FORCE * dt, min(MAX_FORCE * dt, impulse))

            imp_vec = direction * impulse
            a.vx += imp_vec[0] / a.mass
            a.vy += imp_vec[1] / a.mass
            b.vx -= imp_vec[0] / b.mass
            b.vy -= imp_vec[1] / b.mass

    def _solve_ground_collision(self):
        for body in self.bodies:
            corners = body.get_corners()
            for corner in corners:
                penetration = self.ground_y - corner[1]
                if penetration > 0:
                    # 位置修正
                    body.y += penetration * 0.8

                    vel = body.point_velocity(corner)

                    # 法向响应
                    if vel[1] < 0:
                        r = corner - np.array([body.x, body.y])
                        r_cross_n = r[0]  # r × n, n = (0, 1)

                        # 有效质量
                        eff_mass = 1.0 / body.mass + r_cross_n ** 2 / body.inertia
                        if eff_mass < 1e-8:
                            continue
                        j_n = -(1 + self.restitution) * vel[1] / eff_mass
                        j_n = max(0, min(j_n, MAX_FORCE * self.dt))

                        body.vy += j_n / body.mass
                        body.omega += r_cross_n * j_n / body.inertia

                    # 摩擦
                    if abs(vel[0]) > 0.01:
                        friction_impulse = -self.friction * body.mass * abs(self.gravity) * self.dt * 0.25
                        if vel[0] > 0:
                            body.vx += friction_impulse / body.mass
                        else:
                            body.vx -= friction_impulse / body.mass

    def _enforce_joint_limits(self):
        for joint in self.joints:
            angle = joint.current_angle()
            if angle < joint.angle_min:
                correction = (joint.angle_min - angle) * 0.3
                joint.body_a.angle -= correction * 0.5
                joint.body_b.angle += correction * 0.5
                # 角速度也修正
                rel_omega = joint.body_b.omega - joint.body_a.omega
                if rel_omega < 0:
                    joint.body_b.omega += abs(rel_omega) * 0.3
                    joint.body_a.omega -= abs(rel_omega) * 0.3
            elif angle > joint.angle_max:
                correction = (angle - joint.angle_max) * 0.3
                joint.body_a.angle += correction * 0.5
                joint.body_b.angle -= correction * 0.5
                rel_omega = joint.body_b.omega - joint.body_a.omega
                if rel_omega > 0:
                    joint.body_b.omega -= abs(rel_omega) * 0.3
                    joint.body_a.omega += abs(rel_omega) * 0.3
