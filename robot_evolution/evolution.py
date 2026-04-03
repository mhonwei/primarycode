"""
进化算法 - 遗传算法驱动机器人形态和控制器的协同进化

流程:
1. 初始化随机种群
2. 评估每个个体的适应度 (通过仿真)
3. 选择 (锦标赛选择)
4. 交叉 + 变异 → 产生下一代
5. 精英保留
6. 重复直到达到代数上限
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

from .config import Config
from .genome import RobotGenome, crossover, mutate_genome, random_genome
from .simulator import SimulationResult, Simulator


@dataclass
class GenerationStats:
    """每一代的统计信息"""
    generation: int = 0
    best_fitness: float = 0.0
    avg_fitness: float = 0.0
    worst_fitness: float = 0.0
    best_distance: float = 0.0
    avg_segments: float = 0.0
    elapsed_time: float = 0.0
    best_genome: RobotGenome | None = None


@dataclass
class EvolutionResult:
    """进化运行的完整结果"""
    generations: list[GenerationStats] = field(default_factory=list)
    best_genome: RobotGenome | None = None
    best_fitness: float = 0.0
    total_time: float = 0.0


class Evolution:
    """遗传算法引擎"""

    def __init__(self, config: Config):
        self.config = config
        self.simulator = Simulator(config)
        self._genome_counter = 0

    def run(self, callback=None) -> EvolutionResult:
        """
        运行进化过程

        Args:
            callback: 每代结束时调用的回调函数, 签名: callback(gen_stats, population)
        """
        ecfg = self.config.evolution
        result = EvolutionResult()
        start_time = time.time()

        if self.config.seed is not None:
            random.seed(self.config.seed)

        # 1. 初始化种群
        population = self._init_population(ecfg.population_size)
        print(f"初始化种群: {ecfg.population_size} 个个体")

        for gen in range(ecfg.generations):
            gen_start = time.time()

            # 2. 评估适应度
            eval_results = self._evaluate_population(population)

            # 更新个体适应度
            for genome, sim_result in zip(population, eval_results):
                genome.fitness = sim_result.fitness
                genome.generation = gen

            # 排序 (适应度从高到低)
            population.sort(key=lambda g: g.fitness, reverse=True)

            # 3. 统计
            stats = self._compute_stats(gen, population, eval_results, time.time() - gen_start)
            result.generations.append(stats)

            # 更新全局最佳
            if stats.best_fitness > result.best_fitness:
                result.best_fitness = stats.best_fitness
                result.best_genome = stats.best_genome.copy()

            # 打印进度
            print(
                f"第 {gen + 1:3d}/{ecfg.generations} 代 | "
                f"最佳: {stats.best_fitness:8.2f} | "
                f"平均: {stats.avg_fitness:8.2f} | "
                f"距离: {stats.best_distance:6.2f}m | "
                f"段数: {stats.avg_segments:.1f} | "
                f"耗时: {stats.elapsed_time:.1f}s"
            )

            if callback:
                callback(stats, population)

            # 4. 生成下一代
            if gen < ecfg.generations - 1:
                population = self._next_generation(population)

        result.total_time = time.time() - start_time
        print(f"\n进化完成! 总耗时: {result.total_time:.1f}s")
        print(f"最佳适应度: {result.best_fitness:.2f}")

        return result

    def _init_population(self, size: int) -> list[RobotGenome]:
        """初始化随机种群"""
        population = []
        for _ in range(size):
            genome = random_genome(self.config, genome_id=self._genome_counter)
            self._genome_counter += 1
            population.append(genome)
        return population

    def _evaluate_population(
        self, population: list[RobotGenome]
    ) -> list[SimulationResult]:
        """评估种群中所有个体"""
        results = []
        for genome in population:
            result = self.simulator.evaluate(genome)
            results.append(result)
        return results

    def _next_generation(self, population: list[RobotGenome]) -> list[RobotGenome]:
        """生成下一代"""
        ecfg = self.config.evolution
        new_population: list[RobotGenome] = []

        # 精英保留
        for i in range(ecfg.elitism_count):
            elite = population[i].copy()
            elite.genome_id = self._genome_counter
            self._genome_counter += 1
            new_population.append(elite)

        # 生成剩余个体
        while len(new_population) < ecfg.population_size:
            if random.random() < ecfg.crossover_rate:
                # 交叉
                parent_a = self._tournament_select(population)
                parent_b = self._tournament_select(population)
                child = crossover(parent_a, parent_b, self.config)
            else:
                # 直接复制
                parent = self._tournament_select(population)
                child = parent.copy()

            # 变异
            child = mutate_genome(child, self.config)
            child.genome_id = self._genome_counter
            self._genome_counter += 1
            new_population.append(child)

        return new_population[:ecfg.population_size]

    def _tournament_select(self, population: list[RobotGenome]) -> RobotGenome:
        """锦标赛选择"""
        k = min(self.config.evolution.tournament_size, len(population))
        candidates = random.sample(population, k)
        return max(candidates, key=lambda g: g.fitness)

    def _compute_stats(
        self,
        gen: int,
        population: list[RobotGenome],
        eval_results: list[SimulationResult],
        elapsed: float,
    ) -> GenerationStats:
        """计算每代统计信息"""
        fitnesses = [g.fitness for g in population]
        best_idx = 0
        best_result = eval_results[0] if eval_results else None

        # 找到最佳个体对应的仿真结果
        for i, g in enumerate(population):
            if g.fitness == max(fitnesses):
                best_idx = i
                break
        best_result = eval_results[best_idx] if eval_results else None

        return GenerationStats(
            generation=gen,
            best_fitness=max(fitnesses),
            avg_fitness=sum(fitnesses) / len(fitnesses),
            worst_fitness=min(fitnesses),
            best_distance=best_result.distance if best_result else 0.0,
            avg_segments=sum(g.total_segments for g in population) / len(population),
            elapsed_time=elapsed,
            best_genome=population[0].copy(),
        )
