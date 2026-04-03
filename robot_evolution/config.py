"""全局配置参数"""

import dataclasses


@dataclasses.dataclass
class PhysicsConfig:
    """物理引擎配置"""
    gravity: float = -9.81          # 重力加速度 (m/s^2)
    dt: float = 0.005               # 仿真时间步长 (s)
    ground_y: float = 0.0           # 地面高度
    friction: float = 0.8           # 地面摩擦系数
    restitution: float = 0.2        # 碰撞恢复系数
    damping: float = 0.999          # 速度衰减系数 (每步)
    joint_max_torque: float = 100.0 # 关节最大扭矩 (N·m)


@dataclasses.dataclass
class GenomeConfig:
    """基因编码配置"""
    max_depth: int = 3              # 机器人结构树最大深度
    max_children: int = 3           # 每个节点最大子节点数
    min_segment_length: float = 0.3 # 最小肢体长度 (m)
    max_segment_length: float = 1.5 # 最大肢体长度 (m)
    min_segment_width: float = 0.08 # 最小肢体宽度 (m)
    max_segment_width: float = 0.3  # 最大肢体宽度 (m)
    min_joint_range: float = 0.3    # 最小关节活动范围 (rad)
    max_joint_range: float = 2.5    # 最大关节活动范围 (rad)
    density: float = 2.0            # 肢体密度 (kg/m^2, 2D)


@dataclasses.dataclass
class ControllerConfig:
    """控制器配置"""
    min_amplitude: float = 0.1      # 最小振幅
    max_amplitude: float = 1.0      # 最大振幅
    min_frequency: float = 0.5      # 最小频率 (Hz)
    max_frequency: float = 3.0      # 最大频率 (Hz)
    min_phase: float = 0.0          # 最小相位
    max_phase: float = 6.2832       # 最大相位 (2π)


@dataclasses.dataclass
class EvolutionConfig:
    """进化算法配置"""
    population_size: int = 50       # 种群大小
    generations: int = 30           # 进化代数
    tournament_size: int = 5        # 锦标赛选择大小
    crossover_rate: float = 0.7     # 交叉概率
    mutation_rate: float = 0.3      # 变异概率
    structure_mutation_rate: float = 0.1  # 结构变异概率 (增删肢体)
    elitism_count: int = 2          # 精英保留数量


@dataclasses.dataclass
class SimulationConfig:
    """仿真配置"""
    duration: float = 10.0          # 单次仿真时长 (s)
    warmup_time: float = 1.0        # 热身时间 (不计入评估)


@dataclasses.dataclass
class Config:
    """总配置"""
    physics: PhysicsConfig = dataclasses.field(default_factory=PhysicsConfig)
    genome: GenomeConfig = dataclasses.field(default_factory=GenomeConfig)
    controller: ControllerConfig = dataclasses.field(default_factory=ControllerConfig)
    evolution: EvolutionConfig = dataclasses.field(default_factory=EvolutionConfig)
    simulation: SimulationConfig = dataclasses.field(default_factory=SimulationConfig)
    seed: int | None = None         # 随机种子
