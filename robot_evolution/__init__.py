"""
进化机器人生成系统 (Evolutionary Robot Generation System)

通过进化算法自动生成机器人形态和控制器，在2D物理仿真环境中验证运动能力。

核心模块:
- genome: 基因编码 (树形结构描述机器人形态)
- physics: 2D刚体物理引擎
- controller: 关节控制器 (CPG/正弦波)
- simulator: 仿真运行与适应度评估
- evolution: 遗传算法 (选择、交叉、变异)
- visualizer: 可视化渲染
"""

__version__ = "0.1.0"
