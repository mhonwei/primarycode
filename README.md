# Evolutionary Robot Generation System

通过进化算法自动生成机器人形态和控制器，在2D物理仿真环境中验证运动能力。

## 核心思路

```
随机基因组 → 物理机器人 → 仿真评估 → 自然选择 → 交叉变异 → 下一代
     ↑                                                          |
     └──────────────────────────────────────────────────────────┘
```

- **基因编码**: 树形结构描述机器人形态（躯干→肢体→关节），每个节点包含尺寸、连接角度、控制器参数
- **物理引擎**: 自研2D刚体物理（零外部依赖），支持碰撞检测、关节约束、摩擦力
- **控制器**: CPG (中枢模式发生器) + PD控制器，正弦波驱动关节周期运动
- **进化算法**: 遗传算法（锦标赛选择 + 插值交叉 + 参数/结构变异 + 精英保留）
- **适应度**: 移动距离(主) + 稳定性 + 站立高度 - 能耗

## 快速开始

```bash
# 安装依赖
pip install numpy matplotlib

# 快速演示 (10个体, 10代, ~30秒)
python -m robot_evolution --demo

# 正式运行
python -m robot_evolution --generations 50 --population 80

# 自定义参数
python -m robot_evolution -g 100 -p 100 --seed 42 -o results/
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--demo` | 快速演示模式 | - |
| `--generations, -g` | 进化代数 | 30 |
| `--population, -p` | 种群大小 | 50 |
| `--seed, -s` | 随机种子 | None |
| `--duration, -d` | 仿真时长(秒) | 10.0 |
| `--output, -o` | 输出目录 | output/ |
| `--no-viz` | 不生成可视化 | False |

## 输出文件

运行后在输出目录生成:
- `evolution_progress.png` - 适应度/距离/段数/耗时的进化曲线
- `best_robots.png` - 各代最佳机器人形态对比
- `best_robot_static.png` - 最终最佳机器人结构图
- `best_robot_simulation.png` - 最佳机器人运动过程(8帧)
- `evolution_info.json` - 进化结果数据

## 项目结构

```
robot_evolution/
├── config.py       # 所有可调参数 (物理/基因/控制器/进化/仿真)
├── genome.py       # 基因编码: 树形结构 + 随机生成 + 变异 + 交叉
├── physics.py      # 2D刚体物理引擎 (零依赖, 纯numpy)
├── controller.py   # CPG正弦波控制器 + PD跟踪
├── simulator.py    # 仿真运行 + 适应度评估
├── evolution.py    # 遗传算法引擎
├── visualizer.py   # matplotlib可视化
└── main.py         # CLI入口
```

## 设计亮点

1. **形态与控制器协同进化** - 不只进化结构，控制参数(振幅/频率/相位)也一起进化
2. **结构变异** - 可以增删肢体，不只是调整参数，能产生全新形态
3. **自研物理引擎** - 基于Baumgarte稳定化的关节约束求解，无需安装物理库
4. **渐进式设计** - 从简单2D开始，架构清晰，易于扩展到3D/更复杂的任务

## 后续扩展方向

- [ ] 集成PyBullet/MuJoCo实现3D仿真
- [ ] 添加神经网络控制器替代CPG
- [ ] 支持多任务优化（运动+抓取+避障）
- [ ] 增加材料属性进化（弹性/刚性/柔性）
- [ ] 导出为URDF/SDF格式供ROS使用
- [ ] Web界面实时可视化
