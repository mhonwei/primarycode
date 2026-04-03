"""
可视化模块 - 渲染机器人和进化过程

功能:
1. 渲染单个机器人的静态结构
2. 动画播放机器人运动
3. 进化过程统计图表
4. 保存为图片/GIF
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")  # 非交互后端, 支持无显示器环境
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.collections import PatchCollection
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from .config import Config
from .genome import RobotGenome
from .simulator import SimulationResult, Simulator
from .evolution import EvolutionResult, GenerationStats


# 配色方案
COLORS = {
    "background": "#1a1a2e",
    "ground": "#16213e",
    "ground_line": "#0f3460",
    "torso": "#e94560",
    "limb": "#533483",
    "limb_alt": "#0f3460",
    "joint": "#e94560",
    "trajectory": "#00d2ff",
    "text": "#ffffff",
    "grid": "#333366",
}


def check_matplotlib():
    if not HAS_MATPLOTLIB:
        raise ImportError(
            "matplotlib 未安装。请运行: pip install matplotlib"
        )


class RobotVisualizer:
    """机器人可视化"""

    def __init__(self, config: Config):
        self.config = config
        self.simulator = Simulator(config)

    def render_robot_static(
        self,
        genome: RobotGenome,
        save_path: str | None = None,
        title: str | None = None,
    ) -> None:
        """渲染机器人的静态结构图"""
        check_matplotlib()

        # 运行短暂仿真获取稳定姿态
        result = self.simulator.evaluate(genome, record_frames=True)

        if not result.frames:
            print("无法渲染: 仿真未产生帧数据")
            return

        # 取第一帧 (初始姿态)
        frame = result.frames[0]

        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        ax.set_facecolor(COLORS["background"])
        fig.set_facecolor(COLORS["background"])

        self._draw_ground(ax)
        self._draw_frame(ax, frame)

        ax.set_aspect("equal")
        ax.set_xlim(-3, 3)
        ax.set_ylim(-0.5, 4)
        ax.set_xlabel("X (m)", color=COLORS["text"])
        ax.set_ylabel("Y (m)", color=COLORS["text"])
        ax.tick_params(colors=COLORS["text"])

        title_text = title or f"Robot Structure (segments: {genome.total_segments}, joints: {genome.total_joints})"
        ax.set_title(title_text, color=COLORS["text"], fontsize=14)

        plt.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=150, facecolor=fig.get_facecolor())
            print(f"Static image saved: {save_path}")
        plt.close(fig)

    def render_simulation(
        self,
        genome: RobotGenome,
        save_path: str | None = None,
        title: str | None = None,
    ) -> SimulationResult:
        """渲染机器人运动过程 (多帧拼图)"""
        check_matplotlib()

        result = self.simulator.evaluate(genome, record_frames=True)
        n_frames = len(result.frames)

        if n_frames == 0:
            print("无法渲染: 仿真未产生帧数据")
            return result

        # 选择关键帧
        n_show = min(8, n_frames)
        indices = [int(i * (n_frames - 1) / (n_show - 1)) for i in range(n_show)]

        fig, axes = plt.subplots(2, 4, figsize=(20, 8))
        fig.set_facecolor(COLORS["background"])

        for idx, ax in zip(indices, axes.flat):
            ax.set_facecolor(COLORS["background"])
            self._draw_ground(ax)
            self._draw_frame(ax, result.frames[idx])
            ax.set_aspect("equal")

            # 动态调整视窗
            all_x = []
            all_y = []
            for corners in result.frames[idx]:
                all_x.extend(corners[:, 0])
                all_y.extend(corners[:, 1])
            if all_x:
                cx = (min(all_x) + max(all_x)) / 2
                ax.set_xlim(cx - 3, cx + 3)
            ax.set_ylim(-0.5, 4)

            t = idx / max(1, n_frames - 1) * self.config.simulation.duration
            ax.set_title(f"t = {t:.1f}s", color=COLORS["text"], fontsize=10)
            ax.tick_params(colors=COLORS["text"], labelsize=7)

        title_text = title or f"Simulation | Fitness: {result.fitness:.2f} | Distance: {result.distance:.2f}m"
        fig.suptitle(title_text, color=COLORS["text"], fontsize=16)
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=150, facecolor=fig.get_facecolor())
            print(f"Simulation image saved: {save_path}")
        plt.close(fig)

        return result

    def _draw_ground(self, ax):
        """绘制地面"""
        ax.axhline(y=0, color=COLORS["ground_line"], linewidth=2)
        ax.fill_between([-50, 50], -1, 0, color=COLORS["ground"], alpha=0.5)

    def _draw_frame(self, ax, frame: list[np.ndarray]):
        """绘制一帧中的所有刚体"""
        for i, corners in enumerate(frame):
            color = COLORS["torso"] if i == 0 else COLORS["limb"]
            alpha = 0.9 if i == 0 else 0.7

            polygon = plt.Polygon(corners, closed=True, facecolor=color, edgecolor="white",
                                  linewidth=1.5, alpha=alpha)
            ax.add_patch(polygon)

            # 绘制关节点 (各段的第一个角和最后一个角的中点)
            if i > 0:
                joint_pos = (corners[0] + corners[3]) / 2
                ax.plot(joint_pos[0], joint_pos[1], "o",
                        color=COLORS["joint"], markersize=4, zorder=5)


class EvolutionVisualizer:
    """进化过程可视化"""

    @staticmethod
    def plot_evolution_progress(
        result: EvolutionResult,
        save_path: str | None = None,
    ) -> None:
        """绘制进化过程的适应度曲线"""
        check_matplotlib()

        gens = [s.generation + 1 for s in result.generations]
        best = [s.best_fitness for s in result.generations]
        avg = [s.avg_fitness for s in result.generations]
        worst = [s.worst_fitness for s in result.generations]
        distances = [s.best_distance for s in result.generations]
        segments = [s.avg_segments for s in result.generations]

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.set_facecolor(COLORS["background"])

        for ax in axes.flat:
            ax.set_facecolor(COLORS["background"])
            ax.tick_params(colors=COLORS["text"])
            ax.xaxis.label.set_color(COLORS["text"])
            ax.yaxis.label.set_color(COLORS["text"])
            ax.title.set_color(COLORS["text"])
            for spine in ax.spines.values():
                spine.set_color(COLORS["grid"])

        # 适应度曲线
        ax = axes[0, 0]
        ax.fill_between(gens, worst, best, alpha=0.2, color=COLORS["trajectory"])
        ax.plot(gens, best, "-o", color=COLORS["torso"], label="Best", markersize=3)
        ax.plot(gens, avg, "-s", color=COLORS["trajectory"], label="Average", markersize=3)
        ax.set_xlabel("Generation")
        ax.set_ylabel("Fitness")
        ax.set_title("Fitness Evolution")
        ax.legend(facecolor=COLORS["background"], edgecolor=COLORS["grid"],
                  labelcolor=COLORS["text"])

        # Distance
        ax = axes[0, 1]
        ax.plot(gens, distances, "-o", color="#00ff88", markersize=3)
        ax.set_xlabel("Generation")
        ax.set_ylabel("Distance (m)")
        ax.set_title("Best Individual Distance")

        # Segment count
        ax = axes[1, 0]
        ax.plot(gens, segments, "-o", color="#ff8800", markersize=3)
        ax.set_xlabel("Generation")
        ax.set_ylabel("Segments")
        ax.set_title("Avg Body Segments")

        # Time per generation
        times = [s.elapsed_time for s in result.generations]
        ax = axes[1, 1]
        ax.bar(gens, times, color=COLORS["limb"], alpha=0.7)
        ax.set_xlabel("Generation")
        ax.set_ylabel("Time (s)")
        ax.set_title("Evaluation Time")

        fig.suptitle(
            f"Evolution Result | Best Fitness: {result.best_fitness:.2f} | Total: {result.total_time:.1f}s",
            color=COLORS["text"], fontsize=16,
        )
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=150, facecolor=fig.get_facecolor())
            print(f"Evolution progress saved: {save_path}")
        plt.close(fig)

    @staticmethod
    def plot_best_robots(
        result: EvolutionResult,
        config: Config,
        save_path: str | None = None,
        n_show: int = 6,
    ) -> None:
        """展示进化过程中各代最佳机器人"""
        check_matplotlib()

        stats = result.generations
        n_gens = len(stats)
        if n_gens == 0:
            return

        # 选择要展示的代数
        n_show = min(n_show, n_gens)
        indices = [int(i * (n_gens - 1) / (n_show - 1)) for i in range(n_show)]

        cols = min(3, n_show)
        rows = math.ceil(n_show / cols)

        fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 5 * rows))
        fig.set_facecolor(COLORS["background"])

        if n_show == 1:
            axes = np.array([axes])
        axes = np.atleast_2d(axes)

        simulator = Simulator(config)
        vis = RobotVisualizer(config)

        for plot_idx, gen_idx in enumerate(indices):
            row, col = divmod(plot_idx, cols)
            ax = axes[row, col]
            ax.set_facecolor(COLORS["background"])

            gen_stat = stats[gen_idx]
            genome = gen_stat.best_genome
            if genome is None:
                continue

            sim_result = simulator.evaluate(genome, record_frames=True)
            if sim_result.frames:
                vis._draw_ground(ax)
                vis._draw_frame(ax, sim_result.frames[0])

            ax.set_aspect("equal")
            ax.set_xlim(-3, 3)
            ax.set_ylim(-0.5, 4)
            ax.set_title(
                f"Gen {gen_idx + 1} | Fitness: {gen_stat.best_fitness:.1f}",
                color=COLORS["text"], fontsize=11,
            )
            ax.tick_params(colors=COLORS["text"], labelsize=7)

        # 隐藏多余的子图
        for plot_idx in range(n_show, rows * cols):
            row, col = divmod(plot_idx, cols)
            axes[row, col].set_visible(False)

        fig.suptitle("Best Robots Across Generations", color=COLORS["text"], fontsize=16)
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=150, facecolor=fig.get_facecolor())
            print(f"Best robots saved: {save_path}")
        plt.close(fig)
