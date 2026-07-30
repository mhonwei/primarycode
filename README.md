# primarycode
basiccodetraining

## HSCI · 人类生存危机指数可视化系统

基于《HSCI 设计方案（讨论稿 v1.0）》的完善性分析与 Phase 0 设计成果：

| 内容 | 位置 |
|---|---|
| 方案完善性分析（15 项缺口与补充方案） | [`docs/01-方案完善性分析.md`](docs/01-方案完善性分析.md) |
| 指数计算与指标体系规范（公式、掩码、权重、色带） | [`docs/02-指数计算与指标体系规范.md`](docs/02-指数计算与指标体系规范.md) |
| 数据管线设计（数据源分档、快照 schema、降级策略） | [`docs/03-数据管线设计.md`](docs/03-数据管线设计.md) |
| Phase 0 原型：热力矩阵 + 深时时间轴（静态单文件，浏览器直接打开） | [`prototype/index.html`](prototype/index.html) |

原型使用演示占位数据，双指数（HSCI-A / HSCI-E）由规范 02 的公式在页面内实时计算。
