"""
进化机器人生成系统 - 主入口

用法:
  python -m robot_evolution                # 使用默认参数运行
  python -m robot_evolution --generations 50 --population 100
  python -m robot_evolution --demo         # 快速演示模式
  python -m robot_evolution --seed 42      # 可复现的运行
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from .config import Config
from .evolution import Evolution
from .genome import RobotGenome, random_genome
from .simulator import Simulator
from .visualizer import EvolutionVisualizer, RobotVisualizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="进化机器人生成系统 - 通过遗传算法进化出能运动的2D机器人",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                         默认参数运行进化
  %(prog)s --demo                  快速演示 (小种群, 少代数)
  %(prog)s --generations 50        运行50代进化
  %(prog)s --population 100        种群大小100
  %(prog)s --seed 42               设置随机种子
  %(prog)s --output results/       指定输出目录
        """,
    )
    parser.add_argument("--demo", action="store_true", help="快速演示模式 (10个体, 10代)")
    parser.add_argument("--generations", "-g", type=int, default=None, help="进化代数")
    parser.add_argument("--population", "-p", type=int, default=None, help="种群大小")
    parser.add_argument("--seed", "-s", type=int, default=None, help="随机种子")
    parser.add_argument("--output", "-o", type=str, default="output", help="输出目录")
    parser.add_argument("--no-viz", action="store_true", help="不生成可视化图片")
    parser.add_argument(
        "--duration", "-d", type=float, default=None, help="单次仿真时长 (秒)"
    )
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> Config:
    """根据命令行参数构建配置"""
    config = Config()

    if args.demo:
        config.evolution.population_size = 10
        config.evolution.generations = 10
        config.simulation.duration = 5.0
        config.seed = 42

    if args.generations is not None:
        config.evolution.generations = args.generations
    if args.population is not None:
        config.evolution.population_size = args.population
    if args.seed is not None:
        config.seed = args.seed
    if args.duration is not None:
        config.simulation.duration = args.duration

    return config


def run_evolution(config: Config, output_dir: Path, no_viz: bool = False):
    """运行进化并保存结果"""
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  进化机器人生成系统 v0.1")
    print("=" * 60)
    print(f"  种群大小:   {config.evolution.population_size}")
    print(f"  进化代数:   {config.evolution.generations}")
    print(f"  仿真时长:   {config.simulation.duration}s")
    print(f"  随机种子:   {config.seed}")
    print(f"  输出目录:   {output_dir}")
    print("=" * 60)
    print()

    # 运行进化
    evolution = Evolution(config)
    result = evolution.run()

    # 保存最佳基因组信息
    if result.best_genome:
        info = {
            "best_fitness": result.best_fitness,
            "total_segments": result.best_genome.total_segments,
            "total_joints": result.best_genome.total_joints,
            "total_time": result.total_time,
            "generations": config.evolution.generations,
            "population_size": config.evolution.population_size,
        }
        info_path = output_dir / "evolution_info.json"
        with open(info_path, "w") as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
        print(f"\n进化信息已保存: {info_path}")

    # 可视化
    if not no_viz:
        print("\n正在生成可视化...")

        try:
            # 进化曲线
            EvolutionVisualizer.plot_evolution_progress(
                result, save_path=str(output_dir / "evolution_progress.png")
            )

            # 各代最佳机器人
            EvolutionVisualizer.plot_best_robots(
                result, config, save_path=str(output_dir / "best_robots.png")
            )

            # 最佳机器人运动仿真
            if result.best_genome:
                viz = RobotVisualizer(config)
                viz.render_robot_static(
                    result.best_genome,
                    save_path=str(output_dir / "best_robot_static.png"),
                    title=f"Best Robot | Fitness: {result.best_fitness:.2f}",
                )
                viz.render_simulation(
                    result.best_genome,
                    save_path=str(output_dir / "best_robot_simulation.png"),
                    title=f"Best Robot Simulation | Fitness: {result.best_fitness:.2f}",
                )
        except ImportError as e:
            print(f"可视化跳过 (缺少依赖): {e}")
        except Exception as e:
            print(f"可视化生成失败: {e}")

    print("\n完成!")
    return result


def main():
    args = parse_args()
    config = build_config(args)
    output_dir = Path(args.output)
    run_evolution(config, output_dir, no_viz=args.no_viz)


if __name__ == "__main__":
    main()
