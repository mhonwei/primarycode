"""
仿真器 - 将基因组实例化为物理机器人并运行仿真

流程:
1. 解析基因组 → 创建刚体和关节
2. 创建控制器
3. 运行物理仿真
4. 计算适应度 (移动距离、稳定性、能耗等)
"""

from __future__ import annotations

import math

import numpy as np

from .config import Config
from .controller import RobotController
from .genome import RobotGenome, SegmentGene
from .physics import Body, Joint, PhysicsWorld


class SimulationResult:
    """仿真结果"""

    def __init__(self):
        self.fitness: float = 0.0
        self.distance: float = 0.0
        self.max_height: float = 0.0
        self.stability: float = 0.0
        self.energy_used: float = 0.0
        self.alive: bool = True
        self.trajectory: list[tuple[float, float]] = []
        self.frames: list[list[np.ndarray]] = []


class RobotBuilder:
    """从基因组构建物理机器人"""

    def __init__(self, config: Config):
        self.config = config

    def build(
        self, genome: RobotGenome, world: PhysicsWorld
    ) -> tuple[list[Body], list[Joint], RobotController]:
        """将基因组实例化为物理实体"""
        bodies: list[Body] = []
        joints: list[Joint] = []
        controller = RobotController()

        # 先计算机器人大致尺寸, 确定起始高度
        total_reach = self._estimate_max_reach(genome.torso)
        start_y = total_reach + 1.0  # 足够高, 让机器人自由落到地面

        # 构建躯干 (水平放置)
        torso_gene = genome.torso
        torso = Body(
            x=0.0,
            y=start_y,
            angle=0.0,
            width=torso_gene.length,
            height=torso_gene.width,
            mass=max(0.1, torso_gene.length * torso_gene.width * self.config.genome.density),
        )
        world.add_body(torso)
        bodies.append(torso)

        # 递归构建子节点
        self._build_children(
            torso_gene, torso, bodies, joints, controller, world, depth=0
        )

        return bodies, joints, controller

    def _estimate_max_reach(self, seg: SegmentGene) -> float:
        """估算从根节点到最远端的最大距离"""
        if not seg.children:
            return seg.length
        child_reaches = [self._estimate_max_reach(c) + c.length for c in seg.children]
        return seg.length + max(child_reaches)

    def _build_children(
        self,
        parent_gene: SegmentGene,
        parent_body: Body,
        bodies: list[Body],
        joints: list[Joint],
        controller: RobotController,
        world: PhysicsWorld,
        depth: int,
    ):
        n_children = len(parent_gene.children)
        if n_children == 0:
            return

        for i, child_gene in enumerate(parent_gene.children):
            # 连接点分布: 单子节点在右端, 多子节点均匀分布
            if n_children == 1:
                attach_side = 1.0
            else:
                attach_side = -1.0 + 2.0 * i / (n_children - 1)

            anchor_local_parent = np.array([attach_side * parent_body.width / 2, 0.0])

            anchor_world = parent_body.local_to_world(anchor_local_parent)
            attach_angle = parent_body.angle + child_gene.attachment_angle

            child_cx = anchor_world[0] + math.cos(attach_angle) * child_gene.length / 2
            child_cy = anchor_world[1] + math.sin(attach_angle) * child_gene.length / 2

            child_body = Body(
                x=child_cx,
                y=child_cy,
                angle=attach_angle,
                width=child_gene.length,
                height=child_gene.width,
                mass=max(0.1, child_gene.length * child_gene.width * self.config.genome.density),
            )
            world.add_body(child_body)
            bodies.append(child_body)

            anchor_local_child = np.array([-child_gene.length / 2, 0.0])

            joint = Joint(
                body_a=parent_body,
                body_b=child_body,
                anchor_a_local=anchor_local_parent,
                anchor_b_local=anchor_local_child,
                rest_angle=child_gene.attachment_angle,
                angle_min=-child_gene.joint_range / 2,
                angle_max=child_gene.joint_range / 2,
                max_torque=self.config.physics.joint_max_torque,
            )
            world.add_joint(joint)
            joints.append(joint)

            controller.add_joint(joint.joint_id, child_gene.controller)

            self._build_children(
                child_gene, child_body, bodies, joints, controller, world, depth + 1
            )


class Simulator:
    """运行仿真并评估适应度"""

    def __init__(self, config: Config):
        self.config = config
        self.builder = RobotBuilder(config)

    def evaluate(
        self, genome: RobotGenome, record_frames: bool = False
    ) -> SimulationResult:
        result = SimulationResult()

        pcfg = self.config.physics
        world = PhysicsWorld(
            gravity=pcfg.gravity,
            dt=pcfg.dt,
            ground_y=pcfg.ground_y,
            friction=pcfg.friction,
            restitution=pcfg.restitution,
            damping=pcfg.damping,
        )

        bodies, joints, controller = self.builder.build(genome, world)
        if not bodies:
            return result

        scfg = self.config.simulation
        total_steps = int(scfg.duration / pcfg.dt)
        warmup_steps = int(scfg.warmup_time / pcfg.dt)
        frame_interval = max(1, total_steps // 200)

        # 热身阶段: 不开控制器, 让机器人自然落地稳定
        for step in range(warmup_steps):
            world.step()

        # 记录热身后的初始位置
        initial_cx = self._center_of_mass_x(bodies)
        if math.isnan(initial_cx):
            result.alive = False
            return result

        total_energy = 0.0
        min_torso_y = bodies[0].y
        max_torso_y = bodies[0].y
        eval_steps = total_steps - warmup_steps

        for step in range(eval_steps):
            controller.update(joints, world.time)
            world.step()

            # 能耗
            for joint in joints:
                total_energy += abs(joint.motor_torque) * pcfg.dt

            torso_y = bodies[0].y
            if not math.isnan(torso_y):
                min_torso_y = min(min_torso_y, torso_y)
                max_torso_y = max(max_torso_y, torso_y)

            # 记录帧
            if step % frame_interval == 0:
                cx = self._center_of_mass_x(bodies)
                cy = self._center_of_mass_y(bodies)
                if not (math.isnan(cx) or math.isnan(cy)):
                    result.trajectory.append((cx, cy))
                if record_frames:
                    frame = [body.get_corners() for body in bodies]
                    result.frames.append(frame)

            # 死亡检测
            if torso_y < pcfg.ground_y + 0.05 or math.isnan(torso_y):
                result.alive = False
                break

        # 计算结果
        final_cx = self._center_of_mass_x(bodies)
        if math.isnan(final_cx) or math.isnan(initial_cx):
            result.distance = 0.0
        else:
            result.distance = final_cx - initial_cx

        result.max_height = max_torso_y if not math.isnan(max_torso_y) else 0.0
        result.energy_used = total_energy if not math.isnan(total_energy) else 0.0

        height_range = max_torso_y - min_torso_y
        if math.isnan(height_range) or height_range < 0:
            height_range = 10.0
        result.stability = 1.0 / (1.0 + height_range)

        result.fitness = self._compute_fitness(result)
        return result

    def _compute_fitness(self, result: SimulationResult) -> float:
        if not result.alive:
            return max(0.0, result.distance * 0.1) if not math.isnan(result.distance) else 0.0

        fitness = 0.0

        # 移动距离 (核心指标)
        if not math.isnan(result.distance):
            fitness += result.distance * 10.0

        # 稳定性
        fitness += result.stability * 2.0

        # 能耗惩罚
        fitness -= result.energy_used * 0.001

        # 站立奖励
        if result.max_height > 0.3:
            fitness += 2.0

        return max(0.0, fitness)

    def _center_of_mass_x(self, bodies: list[Body]) -> float:
        total_mass = sum(b.mass for b in bodies)
        if total_mass < 1e-8:
            return 0.0
        return sum(b.x * b.mass for b in bodies) / total_mass

    def _center_of_mass_y(self, bodies: list[Body]) -> float:
        total_mass = sum(b.mass for b in bodies)
        if total_mass < 1e-8:
            return 0.0
        return sum(b.y * b.mass for b in bodies) / total_mass
