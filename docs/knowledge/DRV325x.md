# DRV325x 知识卡片（DRV3255/3256-Q1）

> 知识卡片 = 结论与指针；原始文件在 Zotero，本地缓存不入 git。

## 是什么

TI 48V 轻混（Mild Hybrid）**电机驱动三相门极驱动器**：皮带式/集成式启发电机（BSG/ISG）、电机发电机。AEC-Q100 Grade 0（-40~150°C）。

## 关键规格

- 驱动能力：2A 峰值 source / 2.5A 峰值 sink；90V MOSFET 瞬态过压耐受
- 高效自举架构（降低损耗与自发热）；电荷泵支持 **100% PWM 占空比**
- **集成主动短路（ASC）**：高度可配置，故障时快速短路所选 MOSFET，省外部器件
- 三路/单路低边 shunt 放大器可选（电阻采样电流）
- SPI 配置；nASCIN/nSLEEP/nFAULT 硬件保护引脚
- 封装：HTQFP-64（10mm×10mm）

## 应用要点

- 库内有 Functional Safety Manual（2023），功能安全设计必读
- ASC 配置逻辑是保护策略核心：故障类型 → ASC 响应的映射要和系统 FMEA 对齐

## 资料位置

- **Zotero**：`FAE&Work/5 - Chasis`？→ 实际在 `BSM`/相关分类 → `DRV3255&3256` 条目组（DRV3255E SLVSGX9、DRV3256E SLVSGX8 datasheet、FS Manual）

## 整理记录

- 2026-09-05：Simon 建卡（首次全库学习）
