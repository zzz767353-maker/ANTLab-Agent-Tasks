# ANTLab Agent Tasks

文档阅读与信息核验方向 Agent 项目的应用层开发者招募考核：先完成基础题，再从进阶 A/B/C 中选择一套完成。

**截止时间：北京时间 2026 年 10 月 16 日 23:59（UTC+8）。**

## 从哪开始

1. 先读 [开始阅读.md](开始阅读.md)（总体规则、时间、提交方式）。
2. 基础题（必做）：[基础/README.md](基础/README.md) 与 基础/01_考核题目.md。
3. 进阶题（三选一）：[进阶/README.md](进阶/README.md)，在 A / B / C 中选一套。

## 目录结构

```text
开始阅读.md              入口：总体规则、截止时间、提交方式
基础/                    基础题：12 题（4 开发题有公开答案 + 8 评测题），
                         R0/R1/R2/K 四种输入组织条件；模型 API 自费，
                         主请求量与运行命令见 基础/README.md
进阶/                    进阶题（A/B/C 三选一）
├─ 01_A_研究机制迁移.md        A：主张→证据→支持状态机制迁移与对照
├─ 02_B_系统失效诊断.md        B：源码审查、故障归因与修复
├─ 03_C_产品假设验证.md        C：围绕自选用户任务的产品假设验证
├─ materials/                 两份 CC Attribution 公开论文（P1/P2）及抽取数据
├─ challenge_b/               B 题文档查证样机（30 行 Engine，含预埋故障）
└─ templates/                 声明与整合报告模板
```

## 运行与复算命令

**基础题**（真实 API 调用，会产生模型费用）：启动、请求链与复算命令见 `基础/README.md`；密钥与本地配置在 `基础/config.local.json`（勿提交）。

**进阶 B**（离线重放，无 API 费用，Python 3.10+，无第三方依赖）：

```bash
cd 进阶/challenge_b

# 1) 复现原始故障（baseline 引擎，含预埋 bug）
python run_cases.py --engine challenge:Engine --output runs/baseline.json

# 2) 最小修复后完整跑一遍（engine_fixed，只改了缓存 key）
python run_cases.py --engine engine_fixed:Engine --output runs/fixed.json

# 3) 测试 harness：复现 / 区分性干预 / 修复 / 2 回归 / 2 变体 / 1 边界（17 项断言）
python tests_b.py

# 4) 启动页面（展示当前请求、来源快照、证据与验证状态）
python server.py --engine engine_fixed:Engine   # 打开 http://127.0.0.1:8766
```

关键文件：`challenge.py`（原始 baseline，未改）、`engine_fixed.py`（最小修复）、`tests_b.py`（断言+预期依据）、`runs/`（原始结果）、`index.html`（增强页面）。

## 规则要点

- 准备时间为一周（包含基础题和进阶题）；模型调用使用自己的 API，费用自理；实验输入、原始响应、失败和前后对照须保留在仓库中。
- AI 可辅助阅读、实现和排错；需记录它对关键决定的影响、本人如何核验，以及实际完成和未完成的内容。
- 提交：把作品推送到自己的 GitHub 仓库，并在收集表登记仓库链接与最终 commit SHA；收集表地址与仓库评审账号见 Q 群公布（详见 进阶/05_提交与报告格式.md 与 进阶/06_收集表填写说明.md）。
- 本包不含评委参考答案、评测标签、内部开发教程或商业书籍全文。
- 文件完整性：`基础/文件校验.json` 与 `进阶/文件校验.json` 提供逐文件 SHA256，可自行校验。
