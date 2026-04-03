"""
基因编码模块 - 用树形结构描述机器人形态

机器人基因由一棵树表示:
- 根节点 = 躯干 (torso)
- 子节点 = 肢体 (limb)
- 每条边 = 关节 (joint), 带有连接角度和控制参数

每个节点(肢体段)包含:
- length: 长度
- width: 宽度
- attachment_angle: 连接到父节点的角度 (相对于父节点末端法线)
- joint_range: 关节活动范围
- controller_params: 控制器参数 (amplitude, frequency, phase_offset)
"""

from __future__ import annotations

import copy
import math
import random
from dataclasses import dataclass, field

from .config import Config, GenomeConfig, ControllerConfig


@dataclass
class ControllerGene:
    """关节控制器基因 (正弦波参数)"""
    amplitude: float = 0.5    # 振幅
    frequency: float = 1.0    # 频率 (Hz)
    phase_offset: float = 0.0 # 相位偏移 (rad)

    def copy(self) -> ControllerGene:
        return ControllerGene(self.amplitude, self.frequency, self.phase_offset)


@dataclass
class SegmentGene:
    """肢体段基因"""
    length: float = 0.5           # 长度 (m)
    width: float = 0.15           # 宽度 (m)
    attachment_angle: float = 0.0 # 连接角度 (rad), 相对于父节点
    joint_range: float = 1.0      # 关节活动范围 (rad)
    controller: ControllerGene = field(default_factory=ControllerGene)
    children: list[SegmentGene] = field(default_factory=list)

    @property
    def depth(self) -> int:
        """计算子树深度"""
        if not self.children:
            return 0
        return 1 + max(c.depth for c in self.children)

    @property
    def total_segments(self) -> int:
        """计算总肢体段数"""
        return 1 + sum(c.total_segments for c in self.children)

    def copy(self) -> SegmentGene:
        return SegmentGene(
            length=self.length,
            width=self.width,
            attachment_angle=self.attachment_angle,
            joint_range=self.joint_range,
            controller=self.controller.copy(),
            children=[c.copy() for c in self.children],
        )

    def all_segments(self) -> list[SegmentGene]:
        """返回所有肢体段的扁平列表"""
        result = [self]
        for child in self.children:
            result.extend(child.all_segments())
        return result


@dataclass
class RobotGenome:
    """完整的机器人基因组"""
    torso: SegmentGene  # 躯干 (根节点, 不含关节)
    genome_id: int = 0
    fitness: float = 0.0
    generation: int = 0

    @property
    def total_segments(self) -> int:
        return self.torso.total_segments

    @property
    def total_joints(self) -> int:
        return self.torso.total_segments - 1  # 关节数 = 段数 - 1

    def copy(self) -> RobotGenome:
        return RobotGenome(
            torso=self.torso.copy(),
            genome_id=self.genome_id,
            fitness=self.fitness,
            generation=self.generation,
        )


# ---------------------------------------------------------------------------
# 随机生成
# ---------------------------------------------------------------------------

def random_controller(cfg: ControllerConfig) -> ControllerGene:
    """随机生成控制器基因"""
    return ControllerGene(
        amplitude=random.uniform(cfg.min_amplitude, cfg.max_amplitude),
        frequency=random.uniform(cfg.min_frequency, cfg.max_frequency),
        phase_offset=random.uniform(cfg.min_phase, cfg.max_phase),
    )


def random_segment(
    gcfg: GenomeConfig,
    ccfg: ControllerConfig,
    current_depth: int = 0,
    is_root: bool = False,
) -> SegmentGene:
    """随机生成一个肢体段(可递归生成子节点)"""
    seg = SegmentGene(
        length=random.uniform(gcfg.min_segment_length, gcfg.max_segment_length),
        width=random.uniform(gcfg.min_segment_width, gcfg.max_segment_width),
        attachment_angle=0.0 if is_root else random.uniform(-math.pi * 0.8, math.pi * 0.8),
        joint_range=random.uniform(gcfg.min_joint_range, gcfg.max_joint_range),
        controller=random_controller(ccfg),
    )

    # 递归生成子节点
    if current_depth < gcfg.max_depth:
        # 越深越不容易产生子节点
        branch_prob = 0.8 * (1.0 - current_depth / (gcfg.max_depth + 1))
        n_children = 0
        for _ in range(gcfg.max_children):
            if random.random() < branch_prob:
                n_children += 1
        for _ in range(n_children):
            child = random_segment(gcfg, ccfg, current_depth + 1)
            seg.children.append(child)

    return seg


def random_genome(config: Config, genome_id: int = 0) -> RobotGenome:
    """随机生成一个完整的机器人基因组"""
    torso = random_segment(config.genome, config.controller, current_depth=0, is_root=True)

    # 确保至少有一个子节点 (至少有一条腿)
    if not torso.children:
        child = random_segment(config.genome, config.controller, current_depth=1)
        torso.children.append(child)

    return RobotGenome(torso=torso, genome_id=genome_id)


# ---------------------------------------------------------------------------
# 变异操作
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def mutate_controller(ctrl: ControllerGene, ccfg: ControllerConfig, strength: float = 0.3):
    """变异控制器参数"""
    ctrl.amplitude = _clamp(
        ctrl.amplitude + random.gauss(0, strength * (ccfg.max_amplitude - ccfg.min_amplitude)),
        ccfg.min_amplitude, ccfg.max_amplitude,
    )
    ctrl.frequency = _clamp(
        ctrl.frequency + random.gauss(0, strength * (ccfg.max_frequency - ccfg.min_frequency)),
        ccfg.min_frequency, ccfg.max_frequency,
    )
    ctrl.phase_offset = (ctrl.phase_offset + random.gauss(0, strength * math.pi)) % (2 * math.pi)


def mutate_segment(seg: SegmentGene, gcfg: GenomeConfig, ccfg: ControllerConfig, strength: float = 0.3):
    """变异单个肢体段"""
    seg.length = _clamp(
        seg.length + random.gauss(0, strength * (gcfg.max_segment_length - gcfg.min_segment_length)),
        gcfg.min_segment_length, gcfg.max_segment_length,
    )
    seg.width = _clamp(
        seg.width + random.gauss(0, strength * (gcfg.max_segment_width - gcfg.min_segment_width)),
        gcfg.min_segment_width, gcfg.max_segment_width,
    )
    seg.attachment_angle = _clamp(
        seg.attachment_angle + random.gauss(0, strength * 0.5),
        -math.pi * 0.8, math.pi * 0.8,
    )
    seg.joint_range = _clamp(
        seg.joint_range + random.gauss(0, strength * 0.3),
        gcfg.min_joint_range, gcfg.max_joint_range,
    )
    mutate_controller(seg.controller, ccfg, strength)


def mutate_structure(seg: SegmentGene, gcfg: GenomeConfig, ccfg: ControllerConfig, current_depth: int = 0):
    """结构变异: 增删肢体"""
    # 尝试添加新肢体
    if current_depth < gcfg.max_depth and len(seg.children) < gcfg.max_children:
        if random.random() < 0.3:
            new_child = random_segment(gcfg, ccfg, current_depth + 1)
            new_child.children = []  # 新增肢体不带子节点
            seg.children.append(new_child)

    # 尝试删除肢体 (保留至少一个)
    if len(seg.children) > 1 and random.random() < 0.2:
        idx = random.randrange(len(seg.children))
        seg.children.pop(idx)

    # 递归对子节点进行结构变异
    for child in seg.children:
        if random.random() < 0.3:
            mutate_structure(child, gcfg, ccfg, current_depth + 1)


def mutate_genome(genome: RobotGenome, config: Config) -> RobotGenome:
    """变异整个基因组"""
    child = genome.copy()
    gcfg = config.genome
    ccfg = config.controller
    ecfg = config.evolution

    # 参数变异
    if random.random() < ecfg.mutation_rate:
        segments = child.torso.all_segments()
        # 选择一些段进行变异
        for seg in segments:
            if random.random() < 0.5:
                mutate_segment(seg, gcfg, ccfg)

    # 结构变异
    if random.random() < ecfg.structure_mutation_rate:
        mutate_structure(child.torso, gcfg, ccfg)

    return child


# ---------------------------------------------------------------------------
# 交叉操作
# ---------------------------------------------------------------------------

def crossover_segments(seg_a: SegmentGene, seg_b: SegmentGene) -> SegmentGene:
    """对两个肢体段进行交叉"""
    # 参数插值交叉
    t = random.random()
    new_seg = SegmentGene(
        length=seg_a.length * t + seg_b.length * (1 - t),
        width=seg_a.width * t + seg_b.width * (1 - t),
        attachment_angle=seg_a.attachment_angle * t + seg_b.attachment_angle * (1 - t),
        joint_range=seg_a.joint_range * t + seg_b.joint_range * (1 - t),
        controller=ControllerGene(
            amplitude=seg_a.controller.amplitude * t + seg_b.controller.amplitude * (1 - t),
            frequency=seg_a.controller.frequency * t + seg_b.controller.frequency * (1 - t),
            phase_offset=seg_a.controller.phase_offset * t + seg_b.controller.phase_offset * (1 - t),
        ),
    )

    # 子节点交叉: 随机从两个父代选取子节点
    max_children = max(len(seg_a.children), len(seg_b.children))
    for i in range(max_children):
        if i < len(seg_a.children) and i < len(seg_b.children):
            child = crossover_segments(seg_a.children[i], seg_b.children[i])
            new_seg.children.append(child)
        elif i < len(seg_a.children):
            if random.random() < 0.5:
                new_seg.children.append(seg_a.children[i].copy())
        else:
            if random.random() < 0.5:
                new_seg.children.append(seg_b.children[i].copy())

    return new_seg


def crossover(parent_a: RobotGenome, parent_b: RobotGenome, config: Config) -> RobotGenome:
    """交叉两个机器人基因组"""
    new_torso = crossover_segments(parent_a.torso, parent_b.torso)

    # 确保至少有一个子节点
    if not new_torso.children:
        donor = parent_a if parent_a.fitness >= parent_b.fitness else parent_b
        if donor.torso.children:
            new_torso.children.append(donor.torso.children[0].copy())
        else:
            new_torso.children.append(
                random_segment(config.genome, config.controller, current_depth=1)
            )

    return RobotGenome(torso=new_torso)
