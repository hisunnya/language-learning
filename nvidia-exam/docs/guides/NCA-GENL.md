# NCA-GENL · 生成式 AI 大语言模型


## 考纲要点


### NCA-GENL 官方考试大纲（2026-09-02）


> 来源：`cterpening/certification-study-library` · `data/objective-snapshots/nca-genl-2026-09-02-official-objectives.txt` · [原文链接](https://github.com/cterpening/certification-study-library/blob/main/data/objective-snapshots/nca-genl-2026-09-02-official-objectives.txt) · 语言：英文原文 · 中译版



NVIDIA-Certified Associate  
Generative AI LLMs  
(NCA-GENL)

## 考试大纲

请查阅下表。该表按主题及其权重组织，用以说明每个科目在考试中所占的比例。这些主题与 NVIDIA Training 的课程和工作坊一一对应，可用于备考。

### Recommended Training（推荐培训）

#### Content Breakdown（内容分布）

| 内容分布 | 占考试比例 |
|---|---|
| Core Machine Learning and AI Knowledge（核心机器学习与 AI 知识） | 30% |
| Software Development（软件开发） | 24% |
| Experimentation（实验） | 22% |
| Data Analysis and Visualization（数据分析与可视化） | 14% |
| Trustworthy AI（可信 AI） | 10% |

#### 推荐课程

| Recommended Training（课程） | Type of course（课程类型） | Duration（时长） | Cost（费用） |
|---|---|---|---|
| **You can take one of these courses（您可以选修以下课程之一）：** | | | |
| Getting Started With Deep Learning | Self-paced | 8 hours | $90 |
| Fundamentals of Deep Learning | Workshop | 8 hours | $500 |
| See Details（查看详情） | | | |
| **You can take one of these courses（您可以选修以下课程之一）：** | | | |
| Accelerating End-to-End Data Science Workflows | Self-paced | 8 hours | $90 |
| Fundamentals of Accelerated Data Science | Workshop | 8 hours | $500 |
| See Details（查看详情） | | | |
| **You can take one of these courses（您可以选修以下课程之一）：** | | | |
| Introduction to Transformer-Based Natural Language Processing | Self-paced | 6 hours | $30 |
| Building Transformer-Based Natural Language Processing Applications | Workshop | 8 hours | $500 |
| See Details（查看详情） | | | |
| **You can take one of these courses（您可以选修以下课程之一）：** | | | |
| Building LLM Applications with Prompt Engineering | Self-paced | 8 hours | $90 |
| Building LLM Applications with Prompt Engineering | Workshop | 8 hours | $500 |
| See Details（查看详情） | | | |
| **You can take one of these courses（您可以选修以下课程之一）：** | | | |
| Rapid Application Development With Large Language Models (LLMs) | Self-paced | 8 hours | $90 |
| Rapid Application Development With Large Language Models (LLMs) | Workshop | 8 hours | $500 |
| See Details（查看详情） | | | |

### Review These Additional Materials（复习这些补充材料）

- Getting Started With Large Language Models for Enterprise Solutions（博客，20 分钟）
- The Fast Path to Developing With LLMs（点播视频，50 分钟）
- Running Your Own LLM（点播视频，40 分钟）
- What Is Retrieval-Augmented Generation, aka RAG?（博客，15 分钟）
- Trustworthy AI（网页）

---


### NVIDIA 认证专家（NVIDIA-Certified Associate）：生成式 AI LLM（NCA-GENL）学习指南


> 来源：`cterpening/certification-study-library` · `guides/NCA-GENL-nvidia-generative-ai-llms-associate.md` · [原文链接](https://github.com/cterpening/certification-study-library/blob/main/guides/NCA-GENL-nvidia-generative-ai-llms-associate.md) · 语言：英文原文 · 中译版



# NVIDIA 认证专家（NVIDIA-Certified Associate）：生成式 AI LLM（NCA-GENL）学习指南


> **独立 AI 辅助资源 —— 已核对来源与目标；人工复核待完成。** 已于 2026 年 9 月 29 日核查最新的加权考试大纲、交付约定、链接以及考试诚信边界。本次评审将 33 条公开的详细主题要点逐一对应，并执行了 23 项本地 NumPy 校验；独立人工复核以及 GPU/LLM 基础设施相关实践仍在进行中。参见[覆盖记录](../docs/SOURCE-VALIDATION.md#nca-genl-coverage-record)。

**当前基线 —— 采用当前考试大纲：** NCA-GENL 仍是一项在售的专家级考试。当前详情面板列出：考试语言为英语、50–60 道单项选择题、时长一小时、费用 125 美元。该页面现列出五个加权领域下的 33 条详细主题要点；此前开头部分“50 道题”的表述不一致问题已不复存在。页面改版未提供单独的生效日期。<br>
**即将到来的变更：** 截至 2026 年 9 月 29 日，所核查的页面上没有修订或停考公告。<br>
**先修条件：** NVIDIA 列出的是对生成式 AI 与 LLM 的基础理解，而非必须具备的前置证书。<br>
**有效期：** NVIDIA 表示该证书有效期为两年，可通过重新参加考试进行续期。购买前请重新核对政策与价格。

**请核对最新信息：** [项目 FAQ 与政策](https://www.nvidia.com/en-us/learn/certification/)说明：只公布通过/未通过结果而不报告分数；重考需间隔 14 天；自首次购买起 12 个月内最多尝试五次。远程考试不允许中途休息。取消/改期通常需至少提前 24 小时操作，且改期后的考试须在付款后两个月内进行。付款前请核实你自己的实际预约与无障碍安排；本次评审未进行任何预约、账户创建或安全浏览器安装。

当前的备考页面推荐公开的[深度学习基础（Fundamentals of Deep Learning）材料](https://github.com/NVDLI/fundamentals-of-deep-learning)以及 Rapid Application Development with LLMs 课程。当相关公开入口仅返回空白模板或维护提示时，此处不将以往的课程价格与运行时长作为当前事实复述。

## 如何使用本指南


学习一条完整贯通的生命周期：定义一个已获授权的使用场景与成功标准 → 检查/准备受治理的数据 → 选择模型/适配方式/检索方案与提示词 → 实现一个小规模应用 → 对照带版本管理的基线进行评估 → 在资源/延迟/安全控制下部署 → 监控质量、安全性、漂移与成本。使用合成数据或已授权数据。绝不要把机密内容上传到未经批准的模型，不要复制私有题库，也不要把流畅的输出当作事实成立的证据。

> **关于“相关条目”：** `Related item:` 提示框用于补充先修条件、架构或运维方面的背景信息。它对主题起补充作用，但并不表示 NVIDIA 在公开考试大纲中使用了这一表述。

## 考试大纲映射


| 主题领域 | 权重 | 需要产出的证据 |
|---|---:|---|
| 核心机器学习与 AI 知识 | 30% | 问题/模型/数据映射；训练与推理的区分以及 transformer/token/embedding 推理；适配与 RAG 的选型 |
| 软件开发 | 24% | 小规模且经过测试的 Python LLM 应用、明确的 API/数据契约、安全集成、带版本的部署与遥测 |
| 实验 | 22% | 假设、基线、受控变体、数据切分/指标、可复现的运行记录以及基于错误的决策 |
| 数据分析 | 14% | 数据质量/画像证据、恰当的转换/特征、诚实的图表/切片以及已沟通的局限 |
| 可信 AI | 10% | 风险/影响记录、隐私/安全/安全性/偏差/透明度控制、评估、责任归属与应对措施 |

---

## 1. 核心机器学习与 AI 知识 —— 30%


AI 是宏观领域；机器学习从数据中学习模式；深度学习使用多层神经网络。监督学习使用带标注的目标，无监督学习在没有标注的情况下寻找结构，强化学习则通过交互从奖励中学习。模型利用学到的参数把输入映射到输出。训练过程计算预测、损失与梯度，再由优化器更新参数；验证集用于指导模型/超参数的选择；留出的测试集用于估计最终的泛化能力。推理则是把冻结或已部署的模型应用到新输入上。

神经网络把加权变换与非线性激活结合起来。深度与表示学习能够支撑复杂特征，但也会带来数据、算力、优化和可解释性方面的挑战。需要理解参数与超参数的区别、epoch 与 batch/step 的区别、欠拟合与过拟合的区别，以及正则化/数据增强/早停。GPU 的并行能力可以加速矩阵/张量密集型的训练与推理；只有当工作负载、数据搬运、批处理方式和内存使用方式与硬件相匹配时，加速才真正有效。

语言模型用于估计 token 序列。分词（tokenization）把文本映射到 token ID；嵌入（embedding）把 token 或其他对象表示为向量。Transformer 使用注意力机制建立位置之间的关联，并结合前馈层、归一化、残差连接和位置信息。编码器风格的模型侧重表示/理解；解码器风格的自回归模型用于生成下一个 token；编码器—解码器模型用于转换序列。上下文窗口、词表、参数量、精度以及解码设置都会影响能力、延迟、内存、一致性与成本。

基础模型/预训练模型从大规模数据中学习广泛模式。提示工程（prompting）在不改变权重的前提下对行为进行条件约束。零样本（zero-shot）只给出指令；单样本/少样本（one/few-shot）会补充示例；结构化提示则会明确角色、任务、数据边界、输出模式与约束条件。Temperature/top-p 等解码设置在确定性的集中程度与多样性之间做取舍。不要暴露隐藏的思维链（chain-of-thought），也不要依赖缺乏支撑的推理能力宣称；应评估答案本身及其相关证据。

需要在提示/上下文工程、检索增强生成（RAG）和微调之间做选择。RAG 在推理阶段检索受治理的外部证据并提供给模型，从而在检索有效的前提下提升信息的时效性与可溯源性。微调使用精心筛选的示例改变模型行为/权重；参数高效方法只改变规模较小的适配器参数集合。预训练/领域适配的资源消耗要高得多。对齐方法以及人工/偏好反馈旨在让行为更有帮助、更安全，但并不保证事实性或无害性。

要按职责来理解 NVIDIA 的生态体系，而不是死记产品名称：GPU 与 CUDA 加速计算；RAPIDS 加速数据科学；NeMo 提供生成式 AI 的开发/定制/护栏能力；NIM 打包受支持的推理微服务；TensorRT/TensorRT-LLM 优化推理；Triton 提供模型服务；NGC 分发经过策展的容器/模型/资源。产品 API 与打包形式会变化，因此要核对当前文档，并区分开发、训练、优化、服务与治理各层。

**相关条目：** 嵌入支持相似性搜索，但它是有损的模型输出，并非语义层面的真理。向量数据库负责为向量/元数据建立索引；RAG 仍然需要受治理的数据摄取、分块、过滤、重排序、引用生成以及端到端评估。

---

### 学习模型、适配模型与检索证据


**实践深度：** 拟合得到的参数来自数据；超参数则控制拟合过程或模型族。最小二乘模型无需神经网络反向传播也能学出系数。下面基于 CPU 的工作簿展示了一次真实的拟合、留出集预测与指标计算，但它并不训练 LLM。

NVIDIA 的[提示工程与 P-tuning 入门文章](https://developer.nvidia.com/blog/an-introduction-to-large-language-models-prompt-engineering-and-p-tuning/)区分了普通提示示例与学习得到的虚拟提示 token。少样本示例在不更新模型权重的前提下对请求进行条件约束。参数高效调优训练的是一个适配组件；全量微调则会改变更大范围的参数集合。该文章发布于 2023 年 4 月：其中关于早期访问服务和耗时的示例属于历史信息，并非当前的购买建议或性能承诺。应当评估答案及其支撑证据，而不是假定一段书面解释就揭示了忠实的内部推理过程。

[NVIDIA 的 RAG 解析文章](https://blogs.nvidia.com/blog/what-is-retrieval-augmented-generation/)把检索描述为外部上下文的来源。嵌入模型、索引、重排序器和生成器各自承担不同角色。新文档在摄取/索引更新成功之前无法被检索到，而检索到最新内容本身并不能证明权限、正确性或引用支持。应把厂商演示中的加速效果视为特定工作负载下的证据，而不是针对你所用硬件的性能预测。

当前主题清单明确包含阅读研究文献的要求。在比较一篇论文或模型卡时，应记录任务、数据/切分、基线、指标、算力、失败案例以及可复现性限制。不要把在某个基准上测得的改进未经该服务验证就移植到不相关的服务上。

## 2. 软件开发 —— 24%


从一份书面契约开始：用户与所需决策、允许使用的数据、模型/供应商、延迟/成本目标、安全边界、输出模式、证据/引用、失败时的行为以及负责人。构建最小可用的流水线：校验输入 → 检索或构建上下文 → 调用模型 → 校验输出 → 应用人工/工具策略 → 记录安全的元数据/结果。将配置与代码分离，并锁定兼容的模型、提示词、库、容器与 API 版本。

Python 很常见，因为 NumPy/pandas 或其 GPU 等价物负责处理数据，PyTorch 及相关框架负责处理张量/模型，而 Transformers 风格的库则提供分词器/模型/流水线。理解数组/张量、形状/dtype/设备、批处理、dataset/dataloader、模型评估模式以及无梯度推理。框架的便利并不能消除内存、序列化、依赖或不可信模型代码带来的风险。

提示词是应用资产，需要进行版本管理。使用清晰的分隔符、可信的 system/developer 指令、类型化输入以及受约束/结构化的输出。把模型输出视为不可信：按模式（schema）进行校验，对每一个下游动作做授权检查，针对其接收端做转义/参数化，限制时间/大小/重试次数，并对有实质影响的效果要求人工审批。提示注入是一个信任边界问题；仅仅告诉模型“忽略攻击”并不构成充分防护。

对于 RAG，应解析并规范化已批准的文档，保留来源/负责人/版本/ACL 元数据，按语义和检索需求进行分块，做嵌入/建索引，按权限进行过滤，执行检索/重排序并组织引用。检索的召回率/精确率/相关性应与基于证据的生成分开评估。删除操作与权限变更必须贯穿数据源、索引、缓存、上下文和日志。

部署方式可以是本地部署、托管 API、NIM/容器、Triton 或其他服务系统。以可复现的方式打包；依据质量要求和 SLO 选择 GPU/精度/量化/批大小/并发度；暴露健康检查与就绪检查；保护身份/网络/密钥；实施限流与预算控制；记录 trace/request/model/prompt 版本信息且不包含敏感内容。适用时采用金丝雀/影子/A-B 模式，并保留回滚能力。

测试内容包括针对预处理/模式/策略的确定性单元测试、模拟 API 故障、检索测试、模型评估集、对抗性/安全检查、负载/延迟/资源测试以及端到端的用户结果验证。CI 流程不应泄露数据或密钥。应监控输入/输出分布、拒答/事实依据/任务质量、延迟/错误、token 与 GPU 使用情况以及安全事件。

**相关条目：** 编排框架可以简化链路和智能体，但每一层抽象仍然隐含数据、身份、重试、状态、工具、可观测性和版本契约。在投入生产使用之前，要清楚框架隐藏了哪些细节。

---

### 当前服务文档改变了版本假设


**请核对最新信息 / 实践深度：** 当前的 [NIM LLM 与 VLM 概览](https://docs.nvidia.com/nim/large-language-models/latest/about-nim-llm/overview.html)描述的是 2.x 架构，每个镜像配备一个推理引擎，即 vLLM 或 SGLang。请确认你所部署的模型镜像对应的引擎及受支持特性。不要假定所有 NIM 都是较早的多后端架构，也不要认为 NIM 与 Triton 只是同一事物的不同名称。[Triton 快速入门](https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/getting_started/quickstart.html)则带你走完模型仓库、服务器/模型就绪状态以及一次推理请求的全过程。Triton 提供 CPU 执行路径，但仅因为服务器在没有 GPU 访问的情况下启动成功，并不会让一个要求 GPU 的模型配置加载成功。

[NIM 各类版本说明](https://docs.nvidia.com/nim/large-language-models/latest/about-nim-llm/nim-offerings.html)区分了快速获取模型与 NIM Certified 分支验证及支持。免费容器并不自动等同于企业级支持权益。应当将版本类型、镜像标签、模型/配置文件、GPU、驱动、API 行为、许可与运维支持作为一个整体来核验。

所核查的 [2.0.13 发行说明](https://docs.nvidia.com/nim/large-language-models/latest/about-nim-llm/release-notes.html)给出了一个具体的回归案例：某个有文档记载的模型现在会拒绝超过四个 stop 字符串，而此前版本可以接受。这说明需要为请求契约编写带版本的测试；它并非适用于所有服务器或模型的普遍限制。发行说明还区分了容器包更新与宿主机驱动修复。本次评审未运行任何 NIM/Triton 镜像、模型或 API。

## 3. 实验 —— 22%


在改动系统之前，先写出可证伪的假设和主要成功指标。保留一个简单的基线——规则、更小的模型、当前提示词或不做检索的情形。明确数据集总体范围、采样方式、标签/评分标准、训练/验证/测试切分、各切片以及不可接受的性能退化。避免训练—测试污染，以及来自重复样本、时间/未来信息、在全部数据上拟合的预处理，或提示/训练中出现基准答案所导致的数据泄露。

数据预处理包括校验、去重、缺失值/异常值处理、在适用场景下做归一化/标准化、分词/截断/填充、类别平衡以及隐私/许可审查。特征工程要编码有用的信号而不泄露目标变量。对语言类应用而言，示例、分块方式、元数据、嵌入模型和提示上下文同样属于实验变量。

当因果理解很重要时，一次只改动一个受控因素。记录代码/数据/模型/提示词/配置的版本、随机种子、硬件/软件环境、参数/超参数、运行 ID、时间、指标定义、结果与产出物。固定随机种子有助于提升可重复性，但 GPU 内核、分布式执行和外部 API 仍可能存在非确定性；应记录多次重复运行之间的不确定性。

选择与任务相匹配的指标。分类任务使用精确率、召回率、F1、ROC/PR 以及结合类别/基准率背景的混淆矩阵。回归任务使用 MAE/RMSE 和误差分布。生成任务可使用精确匹配/语义/任务专属指标，再加上事实依据、事实性、相关性、完整性、风格、拒答以及人工评分标准。单靠困惑度或词面重合度并不能证明用户价值。RAG 需要检索与生成两方面的度量；生产环境还需纳入延迟、吞吐、错误和成本。

利用错误分析按输入、用户、语言、来源、长度、风险或阶段对失败进行归类。适当时用置信区间/显著性检验或实际效应量来比较各变体；不要仅凭一个挑选出来的微小平均值就推广某个方案。A/B 测试需要伦理审批、分流分配和护栏措施。要记录负面结果与停止条件。选择满足质量、安全、运维和成本约束的最简变体。

**相关条目：** 离线基准测试用于在固定样本上估计行为；在线实验用于测量真实交互；生产监控用于在发布后发现变化。它们回答的是不同的问题，应当共同构成一条完整的证据链。

---

### 评估必须保持数据与决策边界完好


所选取的 [scikit-learn 常见陷阱指南](https://scikit-learn.org/stable/common_pitfalls.html)区分了“拟合一个转换”与“应用这个转换”。应当从训练数据上估计预处理参数，再把同一个转换应用到留出数据上。对依赖于数据的预处理，必须在交叉验证的每个训练折内部进行拟合。当出现重复的人员/文档或未来信息可能渗入估计时，应按实体或时间进行切分。Scikit-learn 在此仅作为参考使用，此处并未安装或执行。

在评估之前先选定指标和分母。[指标参考](https://scikit-learn.org/stable/modules/model_evaluation.html)区分了平均绝对误差与均方误差；平方会让大误差获得更大权重并改变单位。对检索而言，精确率衡量返回内容中有多少是相关的，召回率衡量相关内容被返回了多少。针对已授权的、当前版本的源数据来定义相关性。这两个指标都无法衡量生成的答案是否正确地使用了证据。

在原始工作簿中，模型对四行训练数据实现了精确拟合，但两行留出数据中有一行的误差为 12。平均误差有参考价值，却无法解释这一失败。该两行样本在设计上有意过小，不足以支撑泛化结论、公平性评估或部署决策。应为调优保留独立的验证流程，并为评估保留一份未被触碰的最终测试集；该示例是固定其模型，而不是依据测试结果挑选新模型。

## 4. 数据分析 —— 14%


从数据来源、许可/授权同意、负责人、预期用途、总体范围和敏感度入手。对结构/类型、计数、缺失情况、重复项、标签一致性、取值范围/分布、类别不平衡、语言/长度、时间覆盖度和数据泄露进行画像分析。要区分结构化表格、半结构化事件/文档与非结构化的文本/图像/音频；每一类都需要不同的校验与预处理方式。

使用 dataframe 操作来可复现地完成过滤、连接、聚合和转换。CPU 版 pandas 可能足以处理中等规模数据；cuDF/RAPIDS 和分布式工具可以加速兼容的更大规模操作，但格式转换/数据传输以及不受支持的操作都可能抵消这些收益。要测量端到端效果，而不是某一个内核。保留稳定的 ID 和血缘关系，以便在追踪错误时能回溯到数据源，同时不暴露个人数据。

可视化应当回答某个具体问题。分布情况用直方图/密度图，离散程度与异常值用箱线图/小提琴图，类别比较用条形图，时间序列用折线图，关系用散点图，模型行为用混淆矩阵图/校准图/误差图。坐标轴起点要如实设置，标明单位/样本量/不确定性，避免误导性的双坐标轴和 3-D 装饰，并且要检查各切片，而不只是看总体均值。嵌入的降维图属于探索性分析，对方法和参数十分敏感；二维图上位置接近并不能证明语义上属于同一组。

要说明数据排除了什么、施加了哪种转换，以及该图表支持了什么决策。仪表盘的数据新鲜度和查询定义也是证据的一部分。绝不要把敏感的逐行示例放进截图或公开的实验跟踪工具中。

**相关条目：** 数据质量是指针对某个特定用途的适用性，而非普遍的“干净”。针对某一地区、语言或时间段具有代表性的数据集，在别处可能极不具代表性。

---

### 数据形状与数据血缘会影响结果


[NumPy 快速入门](https://numpy.org/doc/stable/user/quickstart.html)介绍了轴、shape、dtype 以及数组操作。要明确写出特征顺序与单位。一个以文档为行、以特征为列的矩阵，在处理查询时必须沿用相同的列含义。形状兼容仍可能编码了错误的含义。归一化零向量需要明确的结果；该工作簿返回“无匹配”，而不是除以零。

制作图表时，要写明总体范围、样本量、单位、排除项和不确定性。折线图适合有序的时间序列；直方图用于描述分布；混淆矩阵用于描述类别错误。只展示一个看起来有利的均值，或者在不同变体之间改变 y 轴刻度，都可能掩盖运维层面的性能退化。当可用的观测值很少时，用表格比用图表更清楚。

## 5. 可信 AI —— 10%

NVIDIA 公开的原则强调隐私、安全性/安全防护、透明度/问责以及不歧视。将这些原则转化为具体要求、明确的负责人、风险分级、评估、发布门禁、监控和响应。在模型卡/系统卡中记录预期用途、禁止/超出范围的用途、训练/评估数据、模型/版本、局限性以及人工监督机制。

隐私控制包括目的限定、最小化、同意/合法性依据、保留/删除、访问控制、加密以及防止记忆/推断。安全威胁建模需要覆盖数据投毒、供应链/模型代码、模型窃取、提示注入、敏感信息披露、不安全的输出处理、拒绝服务/钱包耗尽以及过度的工具授权。应落实最小权限、来源溯源、沙箱隔离、输出校验、动作审批、速率/预算限制和日志记录。

安全评估考察有害内容以及特定领域中的物理/财务/法律后果。护栏（guardrails）可以对输入/输出和工具进行过滤或引导，但也可能失效或过度拒绝；应测试绕过方式及其运营影响。基于依据的锚定/引用（grounding/citations）可降低部分幻觉风险，但被引用的文本本身可能有误或被误用。对于高影响的决策，应采用校准后的不确定性表达、弃答/升级机制以及由具备资质的人员进行的复核。

公平性分析需要与领域利益相关方共同界定受影响的群体，以及合适的成果/机会/错误指标。仅靠数据集平衡并不能确保公平；应比较各数据切片以及交叉群体上的表现与危害，调查代理变量（proxy）并记录权衡取舍。透明度应说明系统用途、AI 的参与程度、相关证据和局限，同时不得泄露机密或助长滥用。在影响达到一定程度时，应提供反馈/申诉渠道。

监控漂移、质量、滥用、安全事件、投诉以及不平等的结果。建立停止/回滚、通知、事件调查和补救机制。合规性取决于具体用途和司法辖区；应咨询具备资质的治理/法务/隐私团队。

**相关条目：** 模型在技术上可能准确，却仍可能不安全、不公平、存在安全风险，或不适合用于相应的业务决策。可信性是端到端的系统属性，而不是单个模型的评分。

---

### 框架指引与产品声明需要各自独立的证据支撑


[NIST AI RMF 门户](https://www.nist.gov/itl/ai-risk-management-framework)介绍了一个自愿性框架及其生成式 AI 配置文件。它同时指出 AI RMF 1.0 正在修订，并提到一份 2026 年 4 月的关键基础设施概念说明（concept note）。概念说明或修订工作并不等于一份新近最终定稿的替代基线。应与具备资质的利益相关方共同确定适用的义务要求，而不是把某个框架或产品标签当作合规证书。

将 NVIDIA 的[可信 AI 原则](https://www.nvidia.com/en-us/ai-trust-center/trustworthy-ai/)转化为证据：针对隐私的数据权限与删除测试；针对安全性/安全防护的未授权动作与滥用测试；针对透明度的可理解的用途与局限性说明；以及针对不歧视的任务特定成果/错误分析。空结果可能是正确且已获授权的响应。不要把禁止访问的文档暴露给模型，然后指望用一句指令来修补这次泄露。

## 综合场景


以下原创的推理案例不是考试题目。

1. **受治理的支持助手。** 在检索之前定义角色、来源所有者和当前版本。在选出排名靠前的结果之前先过滤资格条件，引用所选版本并提供弃答路径。分别评估检索与生成，然后测试权限变更、来源删除和回滚。未授权的首位命中结果并不是披露它的理由。
2. **存在重复客户的分类器。** 按预期的部署边界进行切分，仅在训练折上拟合预处理，并与简单基线进行比较。检查少数群体切片和高代价错误，而不是仅凭准确率就判定通过。记录预期用途、不确定的结果以及人工复核的职责。
3. **摘要器升级。** 冻结任务/评分标准，在有充分依据的评估集上比较质量、隐私、延迟和成本。重新检查候选服务版本的请求契约和受支持的配置文件。供应商宣称的吞吐量不能替代你自己的测量；应保留回滚方案和明确的否决标准。

## 已执行的本地 NumPy 工作簿


**实践深度 —— 使用合成数据的真实 CPU 计算。** 该代码在 Python 3.13.14 和已安装的 NumPy 2.5.2 下运行：**23 项检查全部通过**。它使用了真实的[最小二乘拟合](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html)和[向量范数](https://numpy.org/doc/stable/reference/generated/numpy.linalg.norm.html)，随后基于可信的权限/版本固定数据执行词法余弦检索。它不执行文件写入、网络调用、安装、账户操作、GPU 推理或模型下载。

回归数据是无量纲的教学数值，而不是实测的延迟、成本或客户指标。它在训练集上的精确拟合并不能预测留出集上的质量。固定词表的计数向量并不是学习得到的语义嵌入，也不存在任何文本生成器或 LLM。检索部分只是组件层面的演示，而不是完整的 RAG 实现或经过认证的授权服务。操作者/角色/租户/清单（manifest）的固定数据必须被信任；在这个极小的示例中，除显式版本之外，文档 ID 在全局范围内是唯一的。真实系统需要权威身份、带作用域的 ID、摄取/删除的传播、缓存失效以及并发控制。

将代码复制到具备上述 NumPy 依赖的环境中。在扩展该示例之前，先解释成功结果以及刻意演示出来的失败。

```python
# Original synthetic CPU computation. Requires NumPy 2.5.2; no model download.

import json
import numpy as np

checks = []

def check(name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append(name)

# Fit preprocessing and two linear coefficients on training data only.

train_x = np.array([1., 2., 3., 4.])
train_y = np.array([4., 6., 8., 10.])
test_x = np.array([7., 8.])
test_y = np.array([16., 30.])
center, scale = train_x.mean(), train_x.std()

def design(x):
    return np.column_stack((np.ones(len(x)), (x - center) / scale))

coefficients, residuals, rank, singular_values = np.linalg.lstsq(
    design(train_x), train_y, rcond=None)
predictions = design(test_x) @ coefficients
errors = predictions - test_y
baseline = np.full_like(test_y, train_y.mean())
check("training-only center", center == 2.5)
check("test-inclusive center would differ", np.concatenate((train_x, test_x)).mean() != center)
check("full-rank two-parameter fit", rank == 2)
check("training fit", np.allclose(design(train_x) @ coefficients, train_y))
check("held-out predictions", np.allclose(predictions, [16, 18]))
check("held-out MAE six", np.isclose(np.abs(errors).mean(), 6))
check("held-out MSE seventy-two", np.isclose(np.square(errors).mean(), 72))
check("better than fixed training-mean baseline",
      np.square(errors).mean() < np.square(baseline - test_y).mean())
check("one held-out slice still has large error", np.isclose(abs(errors[1]), 12))
# An empty solver residual array can reflect matrix dimensions, not perfect fit.

_, under_residuals, _, _ = np.linalg.lstsq(np.array([[1., 2.]]), np.array([3.]), rcond=None)
check("underdetermined residual output is empty", under_residuals.size == 0)

# A fixed vocabulary is a lexical representation, not a learned embedding model.

vocabulary = ("refund", "policy", "days", "delivery", "invoice")
documents = [
    dict(id="private", version=1, tenant="A", roles={"finance"}, text="refund policy days"),
    dict(id="policy", version=1, tenant="A", roles={"support"}, text="refund policy days"),
    dict(id="policy", version=2, tenant="A", roles={"support"}, text="refund policy days invoice"),
    dict(id="other-tenant", version=1, tenant="B", roles={"support"}, text="refund policy days"),
    dict(id="shipping", version=1, tenant="A", roles={"support"}, text="delivery days"),
]
current = {"private": 1, "policy": 2, "other-tenant": 1, "shipping": 1}

def vector(text):
    tokens = text.casefold().split()
    return np.array([tokens.count(term) for term in vocabulary], dtype=float)

def cosine(query, document):
    denominator = np.linalg.norm(query) * np.linalg.norm(document)
    return float(query @ document / denominator) if denominator else 0.0

def retrieve(query, *, tenant, role, manifest, k=1):
    # tenant/role/manifest are trusted fixtures, not values authenticated here.
    if type(k) is not int or k < 1:
        raise ValueError("k must be a positive integer")
    eligible = [d for d in documents
                if d["tenant"] == tenant and role in d["roles"]
                and manifest.get(d["id"]) == d["version"]]
    q = vector(query)
    ranked = [(cosine(q, vector(d["text"])), d) for d in eligible]
    ranked.sort(key=lambda pair: (-pair[0], pair[1]["id"]))
    return [(d["id"], d["version"]) for score, d in ranked[:k] if score > 0]

context = dict(tenant="A", role="support", manifest=current)
result = retrieve("refund policy days", **context)
check("authorized current version retrieved", result == [("policy", 2)])
check("unknown vocabulary yields abstention", retrieve("unicorn", **context) == [])
check("unknown tenant denied", retrieve("refund", **(context | {"tenant": "C"})) == [])
check("unknown role denied", retrieve("refund", **(context | {"role": "visitor"})) == [])
check("current-manifest removal takes effect",
      retrieve("refund", **(context | {"manifest": {"shipping": 1}})) == [])
check("query magnitude does not change cosine ranking",
      retrieve("refund policy days refund policy days", **context) == result)
check("zero vector is explicitly handled", cosine(vector("?"), vector("refund")) == 0)
unsafe = max(documents, key=lambda d: cosine(vector("refund policy days"), vector(d["text"])))
check("unfiltered top result exposes a forbidden record", unsafe["id"] == "private")
check("post-filtering only the top hit loses an eligible result",
      "support" not in unsafe["roles"] and bool(result))
try:
    retrieve("refund", **context, k=True)
except ValueError:
    check("boolean k rejected", True)
else:
    raise AssertionError("boolean k accepted")

# Retrieval evaluation uses relevant authorized current (id, version) pairs.

relevant = {("policy", 2)}
returned = set(retrieve("refund days", **context, k=2))
precision = len(returned & relevant) / len(returned)
recall = len(returned & relevant) / len(relevant)
check("retrieval precision one-half", precision == 0.5)
check("retrieval recall one", recall == 1.0)
check("stale citation is not current evidence", ("policy", 1) not in relevant)
metrics = dict(numpy=np.__version__, test_mae=float(np.abs(errors).mean()),
               test_mse=float(np.square(errors).mean()),
               held_out_predictions=predictions.round(6).tolist(),
               retrieval_precision=precision, retrieval_recall=recall)
print(json.dumps(dict(metrics=metrics, checks=checks)))
print(f"{len(checks)} local NumPy checks passed")
```

预期的最后一行输出：`23 local NumPy checks passed`。

| 观察项 | 实际结果 | 含义与局限 |
|---|---|---|
| 留出集预测 | 对目标值 16 和 30，预测为 16 和 18 | 尽管在训练集上完全拟合，仍有一行测试数据失败。两行数据不足以证明泛化能力。 |
| MAE / MSE | 6 / 72 | 不同的损失函数和量纲；两者都不能取代误差分析。 |
| 未过滤时的首位文档 | 一条被禁止访问的财务记录 | 相似度并不等同于权限。 |
| 排序前的资格过滤 | 当前的 support 策略版本 2 | 可信的固定数据规则会拒绝旧版本、其他租户以及不被允许的角色。 |
| 返回两个结果时的精确率/召回率 | 0.5 / 1.0 | 唯一相关的文档被找到了，同时还返回了一个无关但符合资格的文档。未计算基于答案依据的评分。 |

`lstsq` 返回的残差数组为空，可能源于秩或矩阵维度；它本身并不能证明预测误差为零。同样，成功检索到某个来源也不能证明生成的主张得到了该来源的支持。

## 实践证据实验


以下八项活动仍属于建议性质。请使用获得授权的一次性（可丢弃）环境以及合成数据或已获得适当许可的数据。保留版本信息、预期/实际结果、失败情况、清理过程和局限性。

| 活动 | 需要产出的证据 | 需要排查的失败场景 |
|---|---|---|
| 1. 传统 ML 基线 | 用仅在训练集上拟合的变换训练一个小型模型；比较验证/测试损失与简单基线。 | 引入重复实体或未来信息，并说明为什么此时切分已无法回答部署问题。 |
| 2. Transformer 检视 | 记录分词器/模型版本、token ID、长度、截断、张量形状和任务适配度。 | 测试过长、空和多语言输入；解释截断行为与模型局限，且不臆测其内部推理过程。 |
| 3. 提示契约 | 对指令、示例、输入/输出模式、允许的工具和评估评分标准进行版本管理。 | 测试含糊请求、注入、拒答和非法输出；并验证这些约束确实在模型之外强制执行。 |
| 4. 受治理的检索 | 梳理已获授权的来源、ID/版本、权限、分块、嵌入和引用关系。 | 撤销访问权限或删除某个来源，然后检查索引、检索、上下文和缓存；把检索指标与答案指标分开衡量。 |
| 5. 受控实验 | 明确假设、基线、采样、指标、随机种子/配置和验收标准。 | 纳入一个负面结果、一个有害切片和一次资源消耗回退；不要在最终测试集上调参。 |
| 6. 数据分析 | 剖析数据来源、缺失、重复、不平衡和时间覆盖情况；产出有依据的图表或表格。 | 改变聚合方式或坐标轴刻度，并解释为什么表面上的结论会随之改变。 |
| 7. 服务与升级 | 核实镜像/模型/配置文件/硬件/API 的精确兼容性、健康状态、负载和回滚。 | 在已批准的环境中触发非法请求、模型加载失败或 OOM；区分服务器就绪与有用的推理。 |
| 8. 信任证据 | 撰写系统卡、风险记录、数据/权限图谱和运营升级计划。 | 与合适的利益相关方共同评估隐私/安全/偏见/安全性的失败场景；记录不确定性和停止标准。 |

## 准备度检查


以下原创的带解答提示用于备考；它们并不等同于考试，也不保证通过。

### 机器学习与 AI 基础


1. **AI、ML、深度学习和生成式 AI 之间是什么关系？** AI 是宏观领域；ML 从数据中学习；深度学习使用多层模型；生成式系统生成内容。它们的作用范围彼此交叉，但这并不意味着每个 AI 系统都是 LLM。
2. **训练与推理有什么区别？** 训练利用数据和目标函数改变被学习的参数。推理把选定的模型应用到新输入上；部署仍需要经过验证的数据和运营层面的控制措施。
3. **参数与超参数有什么区别？** 系数或权重是学习得到的参数。模型族、正则化和学习率是人为选定的设置；应通过合适的验证流程对它们进行调优。
4. **为什么 GPU 带来的收益会有差异？** 并行计算、显存、批处理和数据搬运必须与工作负载相匹配。应在实际配置上比较完整的任务耗时和质量。
5. **Token、嵌入和注意力分别是什么？** Token 把输入编码为离散单元；嵌入把单元/条目表示为向量；注意力组合依赖上下文的信息。向量相似并不足以证明内容为真。
6. **该用提示、检索还是微调？** 提示用于任务条件化，检索用于获取外部证据，微调用于有充分依据的行为/领域适配需求。分别评估各自的数据权利、成本、质量和运营负担。
7. **少样本提示会训练权重吗？** 普通的上下文示例不会更新权重。学习得到的虚拟提示/适配器需要经过训练流程，并且要有自己的版本和评估证据。
8. **应如何评估一项研究结论？** 检查任务、数据集/切分、基线、指标、算力和不确定性；在可行的情况下复现相关结果，并说明哪些结论无法迁移到你的使用场景。

### 软件开发


9. **应用契约应包含哪些内容？** 输入/输出模式、用户/任务、允许的数据/动作、模型与提示版本、延迟/成本限制、失败行为以及可问责的负责人。
10. **为什么 dtype、形状和特征顺序很重要？** 它们决定了数值的表示方式与解释方式。维度正确无法弥补列顺序错乱或嵌入空间不兼容的问题。
11. **合法的 JSON 就是安全的模型输出吗？** 不是。必须校验语义和授权，然后针对目标做参数化或编码处理。限制措施和审批要求应在模型之外施加。
12. **检索权限应在哪个环节生效？** 使用可信的身份和来源规则，在排序和构建上下文之前确定资格。对少量的 top-k 结果做事后过滤，可能会丢失有价值的合规证据。
13. **NIM 和 Triton 有什么区别？** 它们是打包方式和部署契约各不相同的推理服务产品。当前的 NIM LLM/VLM 2.x 架构以及 Triton 的仓库/后端行为，必须按确切版本来核查。
14. **用什么证明推理服务系统已经就绪？** 服务器与模型的就绪状态、一次有效且有代表性的推理、受保护的访问以及达到要求的性能/质量。仅有一个正在运行的容器是不够的。
15. **升级应验证哪些内容？** 镜像/模型/配置文件/硬件与驱动器的兼容性、API 行为、质量/安全性、可观测性和回滚。特定版本的发布说明会指出需要测试的场景。
16. **免费提供是否包含企业级支持？** 并非自动包含。请核实所提供的产品、分支、许可证和订阅要求；当前的 NIM 与 NIM Certified 的支持条件并不相同。

### 实验


17. **什么样的假设才有用？** 它应当是与任务、总体、基线、指标以及可接受的回退限度相绑定且可被证伪的预期。在查看结果之前就要确定评估方法。
18. **预处理应在哪里拟合？** 只能在训练分区上拟合，包括在每个交叉验证折内部。其学到的变换要应用到验证/测试数据上，而不要在那里重新拟合。
19. **随机按行切分在什么时候会产生误导？** 重复出现的人员/文档、时间依赖性或未来特征都会造成信息泄漏。切分方式应与预期的部署总体和时间边界相匹配。
20. **完美的训练分数能证明泛化能力吗？** 不能。本地模型在训练集上完全拟合，但在留出集上有一个目标值偏差达 12。应评估有代表性的未见数据和失败切片。
21. **MAE 与 MSE 有什么区别？** MAE 以目标单位计算平均绝对误差；MSE 计算平方误差的平均值，会更强调较大的偏差。应依据后果来选择，而不是看哪个数值看起来更好。
22. **检索精确率与召回率有什么区别？** 精确率是"返回内容中相关内容的数量除以返回内容的总数量"；召回率是"返回内容中相关内容的数量除以既定资格/版本范围内全部相关内容的数量"。
23. **设置随机种子能让每次运行完全一致吗？** 它有助于可复现性，但硬件内核、分布式执行和远程服务仍可能存在差异。应记录版本/配置，并在相关时测量重复运行之间的波动。
24. **人工反馈需要哪些条件？** 需要知情同意和恰当的数据处理、合格且清晰的指示/评分标准、有代表性的评分者以及对分歧的分析。人工标注是带有局限性的证据，并非绝对可靠的真理。

### 数据分析


25. **数据剖析应从哪里开始？** 从来源、权利/同意、用途、总体和敏感性入手，随后再检查类型、缺失、重复、取值范围、标签、不平衡以及时间覆盖。
26. **干净的数据也可能不适用？** 是的。它可能排除了实际部署中的用户或场景条件，编码了有偏的标签，或缺少必要的授权许可。
27. **特征变换需要保留什么？** 保留含义、单位、列顺序、标识符和数据血缘，并界定可复现的"拟合/应用"边界。不要把留出集信息带入学习到的预处理中。
28. **GPU 数据处理在什么时候有帮助？** 当受支持的操作和问题规模足以抵消传输与转换成本时。要衡量整条流水线，包括回退到不受支持操作的部分。
29. **应该选择哪种图表？** 取决于问题本身：分布、时间趋势、类别对比还是关系。要标明样本量、单位、排除项和不确定性。
30. **平均值会掩盖有害的切片吗？** 会。应按相关群体/条件拆分误差并检查绝对影响；良好的汇总指标可能与严重失败同时存在。
31. **二维嵌入图能确立语义分组吗？** 不能。投影方法和参数会改变显示结果。应把它当作探索性手段，并单独验证预期关系。
32. **分析师应沟通什么？** 说明测量了什么、做了哪些变换、总体的局限、不确定性以及所支持的决策。避免在报告或追踪记录中暴露敏感数据行。

### 可信 AI

33. **隐私与安全有何区别？** 隐私关注数据的适当使用与个人利益；安全关注防范未经授权的访问或中断。一个安全的系统仍可能以不当方式处理数据。
34. **安全性与事实准确性有何不同？** 事实上准确的答案仍可能促成伤害或超出许可的使用范围。除正确性之外，还要评估后果、上下文与人工监督。
35. **引用能否证明内容有据可依？** 只有当所引用的授权来源确实支持该论断，且针对当前任务仍然有效时才可以。检索成功与答案受到支持的程度需要分别评估。
36. **护栏能否保证防护？** 不能。需要测试绕过手段、过度拒绝与集成失败；应独立执行数据/操作权限控制，并维持事件响应机制。
37. **应如何评估偏见？** 与利益相关方共同界定受影响的群体、任务特定的危害以及合适的度量指标；检查各数据切片与代理变量，并记录权衡取舍。仅凭类别计数均衡并不足够。
38. **系统卡应包含哪些内容？** 用途、用户、数据/模型版本、评估范围、已知局限、责任负责人、禁止用途，以及运行监控与升级机制。
39. **采用框架就等于合规吗？** 不等于。NIST AI RMF 是自愿性指南；适用的法律/合同义务以及实际控制证据需要单独评估。
40. **系统何时应当弃答或停止？** 当证据、权限、质量或安全要求未得到满足时。在投入生产之前定义阈值、人工升级、回滚与复审触发条件。

就绪意味着能够解释一项决策、实现相关组件、评估其失败情形，并说明证据未能证明的内容。

## 更新检查 — 2026 年 10 月 29 日


当前的 NCA-GENL 页面继续界定考试约定与公开的备考主题；本次更新未发现修订后的目标权重或考试版本。作为当前模型开发的背景信息，NVIDIA 10 月 15 日的技术博客介绍了 Nemotron 3.5 Super VL 这一多模态开放模型，并说明了使用 NeMo 进行定制的方法。当前的 NeMo Framework 文档涵盖自定义语言、多模态、视觉与语音模型的工作流。可将它们作为比较模态、提示词、适配、评估与部署选型的可选示例；博客中的性能结论由厂商自行报告，这两个来源都未增加考试要求。[Nemotron 3.5 Super VL 公告](https://developer.nvidia.com/blog/nvidia-nemotron-3-5-super-vl-powers-specialized-agents-with-multimodal-reasoning/) · [NeMo Framework 文档](https://docs.nvidia.com/nemo-framework/)

## 学习资源


以下并非完整清单。先从当前的主题列表和一条教学路径入手，再有针对性地选择练习。公开可获取性已于 2026 年 9 月 29 日核查。规划耗时为原创建议；链接可达并不能证明其课程元数据或付费内容可以访问。

| 资源 | 获取方式 | 预计耗时 |
|---|---|---|
| [NCA-GENL certification and preparation topics](https://www.nvidia.com/en-us/learn/certification/generative-ai-llm-associate/)：权威来源的五个权重与 33 条详细条目。 | 公开 | 3–5 小时（映射/复习的估算）。 |
| [Fundamentals of Deep Learning public materials](https://github.com/NVDLI/fundamentals-of-deep-learning)：列出的六个模块，涵盖神经网络、CNN、数据增强、迁移学习以及高级架构/NLP。 | 公开仓库；算力/依赖需另行准备 | 所查阅的 README 未给出固定时长；请按模块估算时间。已审阅 README，未运行 notebook。 |
| [Rapid Application Development with LLMs](https://learn.nvidia.com/courses/course-detail?course_id=course-v1:DLI+S-FX-26+V1)：当前备考页面仍列出该课程。 | 课程端点返回空的元数据模板；课程访问权限未经验证 | 此前的 8 小时/时长/价格未复核；请通过当前目录确认。 |
| [Getting Started with Deep Learning](https://learn.nvidia.com/courses/course-detail?course_id=course-v1:DLI+S-FX-01+V1)：此前的推荐内容。 | 公开课程模板为空 | 此前的 8 小时未复核；当前蓝图改为链接开放材料。 |
| [Accelerating End-to-End Data Science](https://learn.nvidia.com/courses/course-detail?course_id=course-v1:DLI+S-DS-01+V2)：此前的补充学习路径。 | 公开课程模板为空 | 此前的 8 小时未复核。 |
| [Introduction to Transformer-Based NLP](https://courses.nvidia.com/courses/course-v1:DLI+S-FX-08+V1/)：较早的端点。 | 显示维护/迁移通知 | 此前的 6 小时未复核；未查阅当前课程内部内容。 |
| [Building LLM Applications with Prompt Engineering](https://learn.nvidia.com/courses/course-detail?course_id=course-v1:DLI+S-FX-12+V2)：此前的补充学习路径。 | 公开课程模板为空 | 此前的 8 小时未复核。 |
| [NumPy quickstart](https://numpy.org/doc/stable/user/quickstart.html) 与本地工作簿：数组、拟合与检索相关组件。 | 公开；执行需安装 NumPy 依赖 | 2–4 小时（选读与工作簿的估算）；不涉及 LLM/GPU 执行。 |
| [scikit-learn pitfalls](https://scikit-learn.org/stable/common_pitfalls.html) 与 [metrics](https://scikit-learn.org/stable/modules/model_evaluation.html)：评估参考资料。 | 公开文档 | 2–4 小时（选读的估算）；本次评审未运行该库。 |
| [NVIDIA Trustworthy AI](https://www.nvidia.com/en-us/ai-trust-center/trustworthy-ai/) 与 [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework)：原则与风险背景。 | 公开 | 2–4 小时（选读/情景推演的估算）；不构成完整的合规评估。 |
| [Udemy NCA-GENL specialization](https://www.udemy.com/course/nca-genl-nvidia-certified-generative-ai-llms-specialization/)：HTTP 403。 | 付费目录访问被拦截 | 此前 2026 年 3 月/1 小时 48 分的元数据未经验证；未对当前内容或质量做出评估。 |

使用能够解释决策与失败情形的原创练习。避免依赖记忆的题目、试题集和保过题库；完成一门课程或一个很小的本地示例，并不能证明已具备考试或生产环境就绪能力。

---


### NCA-GENL 考纲逐条要点


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/exam-objectives.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/exam-objectives.md) · 语言：中文原文



# NCA-GENL 考纲逐条要点

> 来源：英伟达官方考试页面 · [Generative AI LLMs Associate](https://www.nvidia.cn/training/certification/generative-ai-llm-associate/)
>
> ⚠️ 版权归 NVIDIA 所有；本仓只整理覆盖度清单，不含 PDF 副本。

## 域 1 · 核心机器学习和 AI 知识（考试权重 30%）

| # | 考点 | 状态 |
|---|---|---|
| 1.1 | 理解机器学习基础原理（监督/非监督/强化学习） | ⬜ |
| 1.2 | 区分深度学习与传统机器学习方法 | ⬜ |
| 1.3 | 描述神经网络基本结构与训练流程 | ⬜ |

## 域 2 · 软件开发（考试权重 24%）

| # | 考点 | 状态 |
|---|---|---|
| 2.1 | 使用 Python 开发 AI 应用 | ⬜ |
| 2.2 | 集成 NVIDIA SDK/API 到应用工作流 | ⬜ |
| 2.3 | 实现 RAG 流水线（检索增强生成） | ⬜ |

## 域 3 · 实验（考试权重 22%）

| # | 考点 | 状态 |
|---|---|---|
| 3.1 | 设计并执行 AI 模型实验 | ⬜ |
| 3.2 | 使用 NVIDIA工具进行模型评估与比较 | ⬜ |

## 域 4 · 数据分析和可视化（考试权重 14%）

| # | 考点 | 状态 |
|---|---|---|
| 4.1 | 执行探索性数据分析 (EDA) | ⬜ |
| 4.2 | 可视化模型结果与数据分布 | ⬜ |

## 域 5 · 可信 AI（考试权重 10%）

| # | 考点 | 状态 |
|---|---|---|
| 5.1 | 描述可信赖 AI 的道德原则 | ⬜ |
| 5.2 | 描述数据隐私与数据同意之间的平衡 | ⬜ |

## 推荐阅读

- 官方 Study Guide（中文版，Web PDF）：[直链](https://images.nvidia.cn/aem-dam/zh_cn/Solutions/training/certification/nvt-certification-exam-study-guide-genl-web-zhcn.pdf)
- [NVIDIA 官方认证页](https://www.nvidia.cn/training/certification/generative-ai-llm-associate/)

---


### NCA-GENL · Generative AI LLMs Associate


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/overview.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/overview.md) · 语言：中文原文



# NCA-GENL · Generative AI LLMs Associate

> [英伟达官方认证页](https://www.nvidia.cn/training/certification/generative-ai-llm-associate/)

## 考试基本信息

| 项目 | 详情 |
|---|---|
| 考试编号 | NCA-GENL |
| 等级 | Associate（初级） |
| 考试时长 | 约 1 小时 |
| 题型 | 单选题 / 多选题 |
| 语言 | 中文 |
| 考试费用 | 见官网 |
| 证书有效期 | 2 年 |

## 面向人群

- 生成式 AI 应用开发者、数据科学家
- 希望转向 LLM / RAG 工程的软件工程师

## 考点权重

| 模块 | 权重 | 一句话抓总 |
|---|---|---|
| 机器学习和人工智能核心知识 | 30% | 监督/非监督/强化学习 + 深度学习基础 |
| 软件开发 | 24% | Python + NVIDIA SDK 集成 + RAG |
| 实验 | 22% | 模型训练与评估实验设计 |
| 数据分析和可视化 | 14% | EDA + 结果可视化 |
| 可信 AI | 10% | 道德原则 + 数据隐私 |

> 完整考纲逐条见 [exam-objectives.md](./exam-objectives.md)。

## 官方 Study Guide

[中文版 Web PDF](https://images.nvidia.cn/aem-dam/zh_cn/Solutions/training/certification/nvt-certification-exam-study-guide-genl-web-zhcn.pdf)

---


### NCP-GENL Generative AI LLMs Professional 考纲逐条要点


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/exam-objectives.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/exam-objectives.md) · 语言：中文原文



# NCP-GENL Generative AI LLMs Professional 考纲逐条要点

> 来源：英伟达官方考试页面 · [Generative AI LLMs Professional](https://www.nvidia.cn/training/certification/generative-ai-llm-professional/)
>
> ⚠️ 版权归 NVIDIA 所有；本仓只整理覆盖度清单，不含 PDF 副本。

## 域 1 · LLM 架构（考试权重 6%）

| # | 考点 | 状态 |
|---|---|---|
| 1.1 | 理解和应用 LLM 基础架构和机制 | ⬜ |

## 域 2 · 提示工程（考试权重 13%）

| # | 考点 | 状态 |
|---|---|---|
| 2.1 | 通过提示工程、思维链 (CoT)、领域适应、Zero/One/Few-shot 学习以及输出控制，使 LLM 适应新领域 | ⬜ |

## 域 3 · 数据准备（考试权重 9%）

| # | 考点 | 状态 |
|---|---|---|
| 3.1 | 通过清理/管护/分析/组织数据集、Token 化和词表管理，为预训练、微调或推理准备数据 | ⬜ |

## 域 4 · 模型优化（考试权重 17%）

| # | 考点 | 状态 |
|---|---|---|
| 4.1 | 在生产环境中部署 LLM：构建容器化推理工作流、配置模型服务和编排 | ⬜ |
| 4.2 | 实施实时监控、优化部署以缩短延迟并提升吞吐量 | ⬜ |
| 4.3 | 管理模型更新 | ⬜ |

## 域 5 · 微调（考试权重 13%）

| # | 考点 | 状态 |
|---|---|---|
| 5.1 | 创建概念性数据映射文档、自定义导入器、导出和脚本 | ⬜ |

## 域 6 · 评估（考试权重 7%）

| # | 考点 | 状态 |
|---|---|---|
| 6.1 | 通过定量和定性指标、框架设计、基准测试、错误分析和可扩展评估，评估 LLM | ⬜ |

## 域 7 · GPU 加速和优化（考试权重 14%）

| # | 考点 | 状态 |
|---|---|---|
| 7.1 | 在 GPU 硬件上扩展和优化 LLM 训练/推理 | ⬜ |
| 7.2 | 涉及多 GPU/分布式设置、并行技术、故障排查、内存和批处理优化、性能分析 | ⬜ |

## 域 8 · 模型部署（考试权重 9%）

| # | 考点 | 状态 |
|---|---|---|
| 8.1 | 通过容器化工作流、可扩展编排、高效批处理/模型服务以及实时监控，在生产环境部署 LLM | ⬜ |

## 域 9 · 生产监控与可靠性（考试权重 7%）

| # | 考点 | 状态 |
|---|---|---|
| 9.1 | 建立监控仪表板和可靠性指标，跟踪日志和异常，进行根因分析 | ⬜ |
| 9.2 | 实施自动化微调、重新训练和版本管理 | ⬜ |

## 推荐阅读

- [NVIDIA 官方认证页](https://www.nvidia.cn/training/certification/generative-ai-llm-professional/)
- [NVIDIA NeMo](https://developer.nvidia.com/nemo)
- [NVIDIA Triton](https://developer.nvidia.com/triton-inference-server)
- [NVIDIA NIM](https://developer.nvidia.com/nim)

---


### NCP-GENL · Generative AI LLMs Professional


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/overview.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/overview.md) · 语言：中文原文



# NCP-GENL · Generative AI LLMs Professional

> [英伟达官方认证页](https://www.nvidia.cn/training/certification/generative-ai-llm-professional/)

## 考试基本信息

| 项目 | 详情 |
|---|---|
| 考试编号 | NCP-GENL |
| 等级 | Professional（专业级） |
| 考试时长 | 约 1 小时 |
| 题型 | 单选题 / 多选题 |
| 语言 | 中文 |
| 考试费用 | 见官网 |
| 证书有效期 | 见官网 |

## 面向人群

- LLM 应用工程师、AI 平台开发者、NLP 工程师

## 考点权重

| 模块 | 权重 | 一句话抓总 |
|---|---|---|
| LLM 架构 | 6% | Transformer + 核心机制 |
| 提示工程 | 13% | CoT/少样本/领域适应 |
| 数据准备 | 9% | Tokenization + 词表 |
| 模型优化 | 17% | 容器化推理 + Triton |
| 微调 | 13% | LoRA/QLoRA/PEFT |
| 评估 | 7% | 定量/定性指标 |
| GPU 加速和优化 | 14% | 多 GPU/并行/内存优化 |
| 模型部署 | 9% | 批处理/服务/实时监控 |
| 生产监控与可靠性 | 7% | 监控仪表板/版本管理 |

> 完整考纲逐条见 [exam-objectives.md](./exam-objectives.md)。

---


### NCA-GENL 考纲逐条要点（来源：英伟达官方 Study Guide）


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `nca-genl/exam-objectives.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/nca-genl/exam-objectives.md) · 语言：中文原文



# NCA-GENL 考纲逐条要点（来源：英伟达官方 Study Guide）

> 原文出处：NVIDIA NCA-GENL Study Guide (中文版) · 8 页 · 2024.06 版本

---

## 域 1 · 核心机器学习和 AI 知识（考试权重 30%）

| # | 考点 | 覆盖 |
|---|---|---|
| 1.1 | 在高级团队成员的监督下协助部署和评估模型的可扩展性、性能和可靠性 | ⬜ |
| 1.2 | 了解使用数据挖掘和可视化技术从大型数据集提取见解的过程 | ⬜ |
| 1.3 | 构建 LLM 用例（RAG、聊天机器人、摘要器） | ⬜ |
| 1.4 | 为 RAG 策划和嵌入内容数据集 | ⬜ |
| 1.5 | 熟悉机器学习基础（特征工程、模型比较、交叉验证） | ⬜ |
| 1.6 | 熟悉 Python NLP 包功能（spaCy、NumPy、矢量数据库） | ⬜ |
| 1.7 | 阅读研究论文以确定新兴 LLM 趋势和技术 | ⬜ |
| 1.8 | 选择并使用模型创建文本嵌入 | ⬜ |
| 1.9 | 使用提示工程原理创建提示以实现所需结果 | ⬜ |
| 1.10 | 使用 Python 包实现传统机器学习分析 | ⬜ |

**推荐课程**：深度学习新手入门（S-FX-01）· Transformer NLP 入门（S-FX-08）· 加速数据科学工作流（S-DS-01）· 提示工程 LLM 应用（S-FX-12）· LLM 应用开发（S-FX-26）

**推荐阅读**：
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- [End-to-End AI — NVIDIA Blog](https://blogs.nvidia.com/)
- [Generative AI — What Is It?](https://www.nvidia.com/)
- [Activation Function — Wikipedia](https://en.wikipedia.org/)
- [Autoregressive Model — Wikipedia](https://en.wikipedia.org/)
- [What Are Foundation Models? — NVIDIA Blog](https://blogs.nvidia.com/)
- [LoRA: Low-Rank Adaptation](https://arxiv.org/abs/2106.09685)
- [Demystifying Diffusion Models — NVIDIA Blog](https://blogs.nvidia.com/)

---

## 域 2 · 数据分析（考试权重 14%）

| # | 考点 | 覆盖 |
|---|---|---|
| 2.1 | 了解使用数据挖掘和可视化技术从数据集提取见解 | ⬜ |
| 2.2 | 使用统计性能指标（损失函数 / 解释方差比例）比较模型 | ⬜ |
| 2.3 | 在高级团队成员指导下进行数据分析 | ⬜ |
| 2.4 | 使用专门软件创建图形/图表传达数据分析结果 | ⬜ |
| 2.5 | 识别关系、趋势和研究影响因素 | ⬜ |

**推荐阅读**：[RAPIDS](https://rapids.ai/) · [cuML 文档](https://docs.rapids.ai/) · [GPU Accelerated Data Science](https://www.nvidia.com/)

---

## 域 3 · 实验（考试权重 22%）

| # | 考点 | 覆盖 |
|---|---|---|
| 3.1 | 了解数据挖掘和可视化提取见解的过程 | ⬜ |
| 3.2 | 使用统计性能指标比较模型 | ⬜ |
| 3.3 | 在指导下进行数据分析 | ⬜ |
| 3.4 | 使用软件可视化传达分析结果 | ⬜ |
| 3.5 | 识别关系、趋势和研究影响因素 | ⬜ |

**推荐阅读**：
- [A/B Testing in ML](https://en.wikipedia.org/)
- [Inference Optimization](https://developer.nvidia.com/)
- [Zero-Shot Testing](https://arxiv.org/)
- [Hallucinations in LLMs](https://arxiv.org/)
- [Evaluating RAG Applications](https://arxiv.org/)
- [Cross-Validation in ML](https://scikit-learn.org/)

---

## 域 4 · 软件开发（考试权重 24%）

| # | 考点 | 覆盖 |
|---|---|---|
| 4.1 | 协助部署和评估模型可扩展性、性能、可靠性 | ⬜ |
| 4.2 | 构建 LLM 用例（RAG、聊天机器人、摘要器） | ⬜ |
| 4.3 | 熟悉 Python NLP 包功能 | ⬜ |
| 4.4 | 确定满足用户需求所需的系统数据/硬件/软件组件 | ⬜ |
| 4.5 | 监控数据收集、实验和其他软件流程的运行 | ⬜ |
| 4.6 | 使用 Python 包实现传统机器学习分析 | ⬜ |
| 4.7 | 在指导下编写软件组件或脚本 | ⬜ |

**推荐阅读**：
- [TensorRT — Get Started](https://developer.nvidia.com/)
- [Best Practices — NVIDIA NeMo](https://developer.nvidia.com/)
- [Mastering LLM Customization — NVIDIA Blog](https://blogs.nvidia.com/)
- [NCCL: Multi-GPU Communications](https://developer.nvidia.com/)
- [BERT: Pretraining of Bidirectional Transformers](https://arxiv.org/abs/1810.04805)

---

## 域 5 · 值得信赖的 AI（考试权重 10%）

| # | 考点 | 覆盖 |
|---|---|---|
| 5.1 | 描述可信赖 AI 的道德原则 | ⬜ |
| 5.2 | 描述数据隐私与数据同意重要性之间的平衡 | ⬜ |
| 5.3 | 描述如何使用 NVIDIA 和其他技术提高 AI 可信度 | ⬜ |
| 5.4 | 描述如何最大限度减少 AI 系统中的偏见 | ⬜ |

**推荐阅读**：
- [Trustworthy AI for A Better World — NVIDIA](https://www.nvidia.com/)
- [What Is Trustworthy AI? — NVIDIA Blog](https://blogs.nvidia.com/)
- [What Is RAG? — NVIDIA Blog](https://blogs.nvidia.com/)

---

## 推荐具备的知识和经验

1. 会用 Python、C 和 AI 框架（PyTorch、TensorFlow 等）
2. 深刻理解神经网络和深度学习模型
3. 理工科背景（计算机科学、软件工程、AI 等）

## 岗位关键职责

1. 与 AI 开发团队协作设计、编码、测试、调试和记录编程应用
2. 执行系统分析以确保软件和系统符合规格
3. 将新的 AI 语言模型集成到现有系统
4. 协助评估和解决应用和系统性能问题
5. 保持了解新的 AI 模型与语言模型发展
6. 参与制作技术文档和手册
7. 在指导下进行软件编程和文档开发
8. 执行提示工程
9. 协助模型选择过程
10. 定义、策划、标记和注释 LLM 数据集
11. 执行实验（A/B 测试、提示评估、模型评估、POC）

---



## 速查表


### ML 与神经网络基础 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/cheatsheets/chapter-01.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/cheatsheets/chapter-01.md) · 语言：中文原文



# ML 与神经网络基础 — 速查表

## 学习范式

| 范式 | 数据类型 | 目标 | 典型用例 |
|------|----------|------|----------|
| 监督 | 有标签（输入 + 输出） | 从输入预测输出 | 垃圾邮件检测、图像分类 |
| 无监督 | 无标签（仅输入） | 发现隐藏模式 | 客户分群、异常检测 |
| 强化 | 智能体 + 环境 + 奖励 | 学习最优动作 | 机器人、游戏 AI |

**考试陷阱：** "无标签" → 无监督。"智能体获得奖励" → 强化。

---

## 过拟合 vs 欠拟合

| 状态 | 训练损失 | 验证损失 | 原因 | 解决方案 |
|------|----------|----------|------|----------|
| 过拟合 | 很低 | 高 | 模型记忆训练数据 | L1/L2、dropout、更多数据 |
| 欠拟合 | 高 | 高 | 模型太简单 | 增加容量、加特征 |
| 良好拟合 | 低 | 同样低 | 平衡 | 无需行动 |

**考试场景：** 训练准确率 95% 但验证 72% → 过拟合。

---

## 正则化技术

| 技术 | 工作方式 | 效果 | 何时使用 |
|------|----------|------|----------|
| L1（Lasso） | 加入 Σ\|权重\| | 稀疏权重（许多 → 0） | 特征选择 |
| L2（Ridge） | 加入 Σ(权重²) | 小权重 | 通用防过拟合（最常见） |
| Dropout | 训练时随机停用神经元 | 强制冗余 | 深度神经网络 |

**推理时的 Dropout：** 关闭（rate = 0）。所有神经元激活。考试会考。

---

## 激活函数

| 函数 | 公式 | 范围 | 用例 |
|------|------|------|------|
| ReLU | max(0, x) | [0, ∞) | 隐藏层 |
| Sigmoid | 1/(1+e⁻ˣ) | (0, 1) | 二分类输出 |
| Tanh | (eˣ - e⁻ˣ)/(eˣ + e⁻ˣ) | (-1, 1) | 隐藏层 |
| Softmax | eˣⁱ / Σeˣʲ | (0, 1)，和为 1 | 多分类输出 |

---

## 损失函数

| 损失 | 用例 | 输出类型 |
|------|------|----------|
| 交叉熵 | 分类 | 概率 |
| 均方误差（MSE） | 回归 | 连续值 |
| 平均绝对误差（MAE） | 回归（对异常值稳健） | 连续值 |

**考试陷阱：** 分类用 MSE 或回归用交叉熵都是错的。

---

## 嵌入

| 模型 | 嵌入维度 | 用例 |
|------|----------|------|
| BERT-base | 768 | 通用 NLP |
| BERT-large | 1024 | 更高准确率 NLP |
| Sentence Transformers | 384-768 | 语义搜索 |
| GPT-3 | 12288 | 大规模语言生成 |

**考试要点：** 高余弦相似度 = 词在相似上下文中使用。

---

## 梯度下降

- 太高学习率 → 训练不稳定、损失震荡
- 太低学习率 → 训练很慢
- 典型范围：0.001 - 0.01
- **Adam 优化器最常用（自适应学习率）**

---


### Transformer 架构与 LLM — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/cheatsheets/chapter-02.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/cheatsheets/chapter-02.md) · 语言：中文原文



# Transformer 架构与 LLM — 速查表

## 核心架构组件

| 组件 | 用途 | 考试陷阱 |
|------|------|----------|
| 自注意力 | 计算序列中 token 对之间的关系 | 不除以 sqrt(d_k) 缩放，softmax 会饱和 |
| 多头注意力 | 不同学习模式的并行注意力 | 每个头维度 = embedding_dim ÷ num_heads |
| 位置编码 | 注入序列顺序信息 | 没有它是置换不变的 |
| 前馈网络 | 对每个 token 独立施加非线性 | 通常比嵌入维度大 4× |

## 注意力数学

```
Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) × V
```

- **Q（query）**：token 在寻找什么
- **K（key）**：token 提供的内容
- **V（value）**：要检索的实际内容
- **d_k**：key 维度（必须缩放防饱和）

**多头示例：** 12 头，embedding_dim=768 → 每个头 64 维。

---

## 架构模式

| 架构 | 组件 | 用例 | 预训练目标 |
|------|------|------|-----------|
| Encoder-only | 仅编码器 | 分类、NER、句子任务 | 掩码语言建模 |
| Decoder-only | 仅解码器 | 文本生成 | 下一 token 预测 |
| Encoder-Decoder | 编码 + 解码 | 翻译、摘要 | seq2seq |

**考试规则：**
- 分类/嵌入 → Encoder-only（BERT）
- 文本生成 → Decoder-only（GPT、Llama）
- 翻译/摘要 → Encoder-Decoder（T5）

---


### 提示工程 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/cheatsheets/chapter-03.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/cheatsheets/chapter-03.md) · 语言：中文原文



# 提示工程 — 速查表

## 提示策略

| 策略 | 何时使用 | 示例短语 | 准确率影响 |
|------|----------|----------|-----------|
| **Zero-shot** | 任务直接，模型可能已知 | "Classify this review" | 适合常见任务 |
| **Few-shot** | 任务细微，需特定格式 | 在任务前加 1-5 个示例 | +10-30% 准确率 |
| **思维链（CoT）** | 复杂推理、数学、分析 | "Let's think step by step" | 推理 +20-40% |

---

## 温度与采样参数

| 参数 | 范围 | 效果 | 用例 |
|------|------|------|------|
| **Temperature** | 0 | 确定性（相同输入→相同输出） | 客服、数据提取 |
| | 0.3-0.4 | 多数一致，轻微变化 | 代码生成、事实问答 |
| | 0.7-0.9 | 创意但连贯 | 内容写作、头脑风暴 |
| | 1.0+ | 高度随机 | 仅实验 |
| **Top-p** | 0.1 | 非常聚焦（前 10% 概率） | 需技术准确性 |
| | 0.9 | 平衡多样性 | 通用 |
| | 1.0 | 考虑所有 token | 最大创意 |
| **Max_tokens** | 50-100 | 短响应 | 摘要 |
| | 500-1000 | 中等内容 | 段落 |
| | 2000+ | 长篇 | 文章 |

---

## 提示类型

| 类型 | 用途 | 优先级 |
|------|------|--------|
| 系统提示 | 设定角色、行为、约束 | 较低（用户可覆盖） |
| 用户提示 | 任务/指令 | 高 |

---

## 最佳实践

- 用分隔符/标签区分上下文与指令
- 复杂任务拆分为子任务
- 避免双重否定
- 期望输出 JSON 时指定键和类型
- "You are a..." 比祈使句更有效

---


### 对齐、安全与负责任 AI — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/cheatsheets/chapter-04.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/cheatsheets/chapter-04.md) · 语言：中文原文



# 对齐、安全与负责任 AI — 速查表

## RLHF 训练流水线（重点考察）

| 阶段 | 发生什么 | 输出 |
|------|----------|------|
| 1. 监督微调（SFT） | 在遵循指令的示例上训练基础模型 | 指令微调模型 |
| 2. 奖励模型训练 | 在人类偏好比较（A vs B）上训练分类器 | 奖励模型 |
| 3. RL 优化 | 用 PPO 借助奖励模型反馈优化策略 | 对齐模型 |

**考试陷阱：** 奖励模型必须在 RL 阶段之前训练。顺序很重要。

---

## 幻觉（重点考察）

**定义：** 模型生成看似合理但事实上不正确/不可验证的信息。

**原因：**
- 模型在下一 token 预测上训练，而非真实验证
- 置信度得分反映 token 概率，而非事实准确性
- 知识截止：训练后的事件无信息
- 模式补全：用看似合理的编造填补空白

**缓解技术：**

| 技术 | 工作方式 | 有效性 |
|------|----------|--------|
| **RAG（接地）** | 检索已验证文档，指示引用来源 | **最佳** — 架构级约束 |
| 引用验证 | 后处理验证引用存在于数据库 | 高 |
| 降低温度 | 减少随机性（0.0-0.3） | 中等 — 减少但不消除 |
| 提示指令 | 告诉模型说"我不知道" | 低 |

**考试陷阱：** Temperature 0.0 使输出确定但并不能防止幻觉。

---

## 负责任 AI 原则

- 公平性：避免偏见
- 可解释性：决策可追溯
- 隐私：数据保护
- 安全性：防止有害输出

---


### 数据预处理与特征工程 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/cheatsheets/chapter-05.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/cheatsheets/chapter-05.md) · 语言：中文原文



# 数据预处理与特征工程 — 速查表

## 文本清理优先顺序

1. 移除 HTML/XML 标签
2. 移除 URL
3. 处理 emoji（移除或转为文本）
4. 小写化（除非大小写重要）
5. Unicode 归一化 → **ML 用 NFKC，保真用 NFC**
6. 移除多余空白

**不要应用：** 词干化/词形归并（transformer 自学形态）。

---

## Unicode 归一化形式

| 形式 | 用例 | 效果 |
|------|------|------|
| **NFC** | 正式文档，保真 | 组合字符 |
| **NFD** | 语言学分析 | 分离基字符 + 变音 |
| **NFKC** | **NLP/ML（推荐）** | 兼容性 + 组合 |
| **NFKD** | 极少使用 | 兼容性 + 分解 |

---

## 分词对比

| 类型 | 词汇量 | 序列长度 | [UNK] 率 | 最适合 |
|------|--------|----------|----------|--------|
| Word-level | 50K-100K+ | 最短（1x） | 高 | 简单任务 |
| **BPE/WordPiece** | 32K-50K | 中等（1.5-2x） | **零** | **多数 LLM** |
| Character-level | 256-500 | 最长（10-20x） | 零 | 嘈杂文本 |

**考试选择：** 未知领域选 BPE（无 [UNK]，长度合理）。

---

## 注意力掩码与填充

**规则：** 1 = 真实 token（关注），0 = padding（忽略）

---

## 内存扩展（Transformer）

| 序列长度 | 注意力内存 | 总内存 |
|----------|-----------|--------|
| 512 tokens | 1x | 1x |
| 1024 tokens | 4x | ~2x |
| 2048 tokens | 16x | ~4-8x |

**公式：** 注意力 = O(n²)，长度翻倍 = 4× 内存。

---


### 实验与评估 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/cheatsheets/chapter-06.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/cheatsheets/chapter-06.md) · 语言：中文原文



# 实验与评估 — 速查表

## 评估指标对比

| 指标 | 用例 | 范围 | 方向 | 关键焦点 |
|------|------|------|------|----------|
| **困惑度** | 语言建模 | 1 到 ∞ | 越低越好 | 下一 token 预测质量 |
| **BLEU** | 翻译/生成 | 0.0 - 1.0 | 越高越好 | n-gram 精确率 |
| **ROUGE-1** | 摘要 | 0.0 - 1.0 | 越高越好 | unigram 召回率 |
| **ROUGE-2** | 摘要 | 0.0 - 1.0 | 越高越好 | bigram 召回率 |
| **ROUGE-L** | 摘要 | 0.0 - 1.0 | 越高越好 | 最长公共子序列 |
| **人工评估** | 开放式任务 | 1-5 或 1-7 | 越高越好 | 流畅度、连贯性 |

**考试规则：**
- 翻译 → BLEU（精确率）
- 摘要 → ROUGE（召回率）
- 语言模型质量 → 困惑度（越低越好）

---

## 困惑度快速参考

```
困惑度 = exp(交叉熵损失)
困惑度越低 = 模型对数据越"不惊讶" = 越好
```

---

## 数据增强质量排序

1. **回译**（最佳多样性，保持含义）
2. **上下文替换**（BERT MLM，替换最多 15% token）
3. **同义词替换**（WordNet，10-15% 替换率）
4. **随机删除**（最差，仅用于鲁棒性测试）

---


### LLM 集成与部署 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/cheatsheets/chapter-07.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/cheatsheets/chapter-07.md) · 语言：中文原文



# LLM 集成与部署 — 速查表

## RAG（检索增强生成）

**架构：** 查询 → 嵌入 → 向量搜索 → 检索 Top-K 块 → 注入提示 → LLM 生成

| 用途 | 何时使用 |
|------|----------|
| RAG | 私有/领域数据、减少幻觉、引用来源 |
| 微调 | 永久改变风格/格式/领域 |
| 提示工程 | 少量示例、无需数据存储 |

---

## 向量数据库与搜索

| 数据库 | 类型 | 最适合 |
|--------|------|--------|
| FAISS | 库（本地） | 原型、低于 1000 万向量 |
| Pinecone | 托管服务 | 生产 |
| Weaviate | 自托管/托管 | GraphQL 查询、混合搜索 |
| Milvus | 自托管 | 大规模、本地部署 |

---

## 决策矩阵：微调 vs 提示工程 vs RAG

| 标准 | 提示工程 | RAG | 微调 |
|------|----------|-----|------|
| 所需数据 | 0-10 示例 | 知识库 | 超过 1000 标注示例 |
| 部署时间 | 数小时-数天 | 数天-数周 | 数周-数月 |
| 成本 | 低 | 中 | 高 |
| 质量上限 | 60-80% | 70-85% | 85-95% |
| 考试提示 | 低于 500 示例的默认选择 | 适合事实/检索任务 | 任务模式必须学习时使用 |

---


### NVIDIA 软件栈 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/cheatsheets/chapter-08.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/cheatsheets/chapter-08.md) · 语言：中文原文



# NVIDIA 软件栈 — 速查表

## 框架对比

| 工具 | 用途 | 关键特性 | 何时使用 |
|------|------|----------|----------|
| **NVIDIA NeMo** | 训练/微调 LLM | 数据预处理、模型训练、RLHF | 从头构建自定义模型 |
| **NVIDIA NIM** | 部署优化 LLM | 预构建容器、自动批处理 | 快速生产部署 |
| **TensorRT-LLM** | 优化推理 | 量化（INT4/8、FP8）、内核融合 | 最大性能 |
| **Triton Inference Server** | 服务多模型 | 动态批处理、并发执行 | 多模型部署 |

**考试规则：**
- 训练框架 → NeMo
- 部署微服务 → NIM
- 语音（ASR/TTS）→ Riva
- 大规模 RAG → NeMo Retriever

---

## NeMo 模块化流水线

1. 数据预处理：分词、数据清理、格式转换
2. 模型训练：分布式训练、检查点、混合精度
3. 提示学习：P-tuning、prompt tuning、适配器
4. RLHF：奖励建模、PPO 训练、安全对齐

---

## NIM 关键优势

- 预构建容器，最少配置
- 自动批处理、GPU 内存优化
- 快速生产部署

---


### 真实世界 LLM 应用架构 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/cheatsheets/chapter-09.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/cheatsheets/chapter-09.md) · 语言：中文原文



# 真实世界 LLM 应用架构 — 速查表

## 模型大小权衡（单块 A100 GPU）

| 模型大小 | 内存 | 延迟（P50） | 吞吐 | 用例 |
|----------|------|-------------|------|------|
| 1.3B（蒸馏） | 3GB | 20ms | 5,000 tok/sec | 分类、抽取 |
| 7B | 14GB | 50ms | 2,000 tok/sec | 通用任务、低延迟 |
| 13B | 26GB | 100ms | 1,000 tok/sec | 复杂推理 |
| 70B | 140GB | 更高 | 更低 | 最高质量 |

---

## 批处理策略

| 策略 | 适用 | 效果 |
|------|------|------|
| 动态批处理 | 在线请求 | 提高吞吐 |
| 连续批处理 | 不定长请求 | 最大化 GPU 利用率 |
| 静态批处理 | 离线任务 | 固定 batch 处理 |

---

## 评估指标复习

| 指标 | 用例 | 方向 |
|------|------|------|
| BLEU | 翻译 | 越高越好 |
| ROUGE | 摘要 | 越高越好 |
| 困惑度 | 语言模型 | 越低越好 |
| 准确率 | 分类 | 越高越好 |

---


### 考试策略模拟 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/cheatsheets/chapter-10.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/cheatsheets/chapter-10.md) · 语言：中文原文



# 考试策略模拟 — 速查表

## 考试格式

| 参数 | 值 |
|------|-----|
| 题数 | 50-51 道多选题 |
| 时长 | 60 分钟 |
| 及格分 | 约 70%（约答对 36 题） |
| 每题时间 | 平均 1.2 分钟（目标 1 分钟） |

---

## 时间管理策略

1. **第一遍（40 分钟）：** 立即回答所有会的题
2. **标记难题：** 超过 90 秒标记并跳过
3. **第二遍（15 分钟）：** 处理被标记的题
4. **最终复查（5 分钟）：** 检查标记题

---

## 常见考试陷阱

| 陷阱 | 如何避免 |
|------|----------|
| Decoder-only vs encoder-decoder | 生成用 Decoder，翻译用 encoder-decoder |
| RLHF vs 监督微调 | RLHF = 3 步流程带奖励模型 |
| Temperature vs top-p | Temperature 标准多样性；top-p 替代采样 |
| NeMo vs NIM | NeMo = 训练框架；NIM = 部署微服务 |
| BLEU vs ROUGE | BLEU = 翻译（精确率）；ROUGE = 摘要（召回率） |
| ASR vs TTS | ASR = 语音→文本；TTS = 文本→语音 |

---

## 领域权重回顾

| 领域 | 权重 |
|------|------|
| 生成式 AI 基础 | 20-25% |
| NVIDIA AI 平台 | 20-25% |
| 模型训练 | 20-25% |
| 推理与部署 | 15-20% |
| 评估 | 10-15% |

---

## 心理准备

- 注意 NOT、BEST、MOST、LEAST
- 相信你的准备
- 别反复纠结：第一直觉通常正确
- 保持冷静：60 分钟足够

---


### Transformer 内部机制 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/cheatsheets/chapter-01.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/cheatsheets/chapter-01.md) · 语言：中文原文



# Transformer 内部机制 — 速查表

## 注意力机制对比

| 变体 | KV 头数量 | KV 缓存相对大小 | 质量 |
|------|-----------|----------------|------|
| MHA | = 查询头数 | 最大（基准） | 最高 |
| GQA | 分组共享 | 缩减（1/group_size） | 接近 MHA |
| MQA | 1（全部共享） | 最小 | 有适度损失 |

## GQA 缩减计算

- 公式：KV 头数 = 查询头数 ÷ 组大小
- 示例：32 查询头 + 组大小 4 = 8 KV 头 → KV 缓存为 MHA 的 1/4

## FlashAttention 核心原理

| 要素 | 说明 |
|------|------|
| 机制 | IO 感知精确算法，分块保留在 SRAM |
| 避免 | 在 HBM 中实例化完整 N×N 注意力矩阵 |
| 结果 | 内存带宽优化（非近似），从 memory-bound 转向 compute-bound |
| 数学上 | **精确**——不是近似 |

## 位置编码对比

| 方法 | 外推能力 | 说明 |
|------|----------|------|
| 可学习绝对嵌入 | 差 | 固定长度表格，无法表示更长位置 |
| 正弦绝对编码 | 差 | 未训练长度性能显著下降 |
| ALiBi | 好 | 线性偏置直接加到注意力分数，无需重训练即可外推 |
| RoPE + 高 theta | 好 | 增大基频让旋转更慢，支持更长上下文 |

## 编码器-解码器 vs 仅解码器

| 维度 | 编码器-解码器 | 仅解码器 |
|------|--------------|----------|
| 注意力类型 | 双向自注意力 + 交叉注意力 | 统一因果注意力 |
| 适用任务 | 翻译、摘要（seq2seq） | 开放式生成、通用 LLM |

---


### 缩放定律、分词与上下文窗口 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/cheatsheets/chapter-02.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/cheatsheets/chapter-02.md) · 语言：中文原文



# 缩放定律、分词与上下文窗口 — 速查表

## Chinchilla 计算最优

| 规则 | 说明 |
|------|------|
| 参数-Token 比 | 约 20:1（每参数约 20 个训练 token） |
| 示例 | 70B 参数 → 约 1.4 万亿 token |
| 均衡扩展 | 参数与 token 数应大致同步扩展 |

## RoPE 上下文扩展方法

| 方法 | 是否需要微调 | 原理 |
|------|-------------|------|
| 位置插值（PI） | 是（需要） | 将位置插值到训练长度内 |
| NTK-aware 缩放 | 否（免训练） | 非均匀调整旋转频率 |
| 增大 theta（基频） | 否/少 | 让旋转更慢（10000 → 500000），支持更长距离 |

## 分词器对比

| 维度 | BPE | SentencePiece |
|------|-----|---------------|
| 预分词 | 通常按空白符预切分 | 直接处理原始字节流 |
| 空白符处理 | 切分前驱步骤 | 视为普通符号 |
| 多语言友好 | 差（对 CJK 失效） | 好（无需空白符边界） |

## 词表大小影响

| 效果 | 大词表 | 小词表 |
|------|--------|--------|
| 嵌入表 | 更大 | 更小 |
| 序列长度 | 更短（更多常见词=单 token） | 更长 |
| 稀有 token | 仍可能出现 | 更频繁 |

## MoE vs 稠密模型

| 维度 | MoE | 稠密 |
|------|-----|------|
| 总参数量 | 可非常大 | 受算力预算限制 |
| 每 token 激活 | 仅 top-k 专家 | 全部参数 |
| 适用场景 | 大容量 + 低算力预算 | 简单直接 |

---


### 高级提示词 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/cheatsheets/chapter-03.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/cheatsheets/chapter-03.md) · 语言：中文原文



# 高级提示词 — 速查表

## 提示模式对比

| 模式 | 特点 | 适用场景 |
|------|------|----------|
| 零样本 | 仅指令，无示例 | 简单任务 |
| 少样本 | 多个输入/输出示例 | 格式引导 |
| CoT（思维链） | 展示分步推理 | 多步推理、数学 |
| ReAct | Thought-Action-Observation 循环 | 需要外部工具/信息 |
| 自洽性 | CoT + 多次采样投票 | 推理准确率优先 |

## 自洽性关键配置

| 要素 | 要求 |
|------|------|
| 温度 | > 0（通常 ~0.7） |
| 采样次数 | 5-10 次独立路径 |
| 决策方式 | 多数投票选出最终答案 |
| 成本 | 约为单次推理的 5-10 倍 |

## ReAct 循环结构

```
Thought → Action（工具调用）→ Observation → Thought → ... → Final Answer
```

## 受限解码

| 能力 | 说明 |
|------|------|
| 机制 | 在 token 级别屏蔽无效 token |
| 适用 | JSON schema、枚举值、正则约束 |
| 优势 | 100% 语法保证（vs 提示/CoT 无保证） |

## 各模式成本/收益快速判断

| 场景 | 推荐 | 不推荐 |
|------|------|--------|
| 严格 JSON 输出 | 受限解码 | CoT（增加冗余文本） |
| 多步推理 + 准确率优先 | CoT + 自洽性 | 零样本 |
| 实时信息查询 | ReAct | 自洽性（无工具调用） |
| 简单分类 | 单次提示 | CoT + 自洽性（开销浪费） |

---


### RAG 与适配策略 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/cheatsheets/chapter-04.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/cheatsheets/chapter-04.md) · 语言：中文原文



# RAG 与适配策略 — 速查表

## 三策略决策框架

| 策略 | 适用场景 | 不适用 |
|------|----------|--------|
| 提示词工程 | 通用能力、静态 FAQ（少量） | 私有/动态知识 |
| RAG | 动态/每日更新知识、低训练预算 | 行为/风格一致性 |
| 微调（SFT） | 严格风格/语气、稳定任务、格式遵循 | 知识频繁变化 |

## RAG 流水线组件

| 组件 | 顺序 | 功能 |
|------|------|------|
| 分块/切分器 | 1 | 将长文档切成可检索单元 |
| 嵌入模型 | 2 | 将分块转为向量 |
| 向量存储 | 3 | 索引和检索相似向量 |
| 检索器 | 4 | 初始 top-k 相似度搜索 |
| 重排序器 | 5 | 对初始结果重新打分精炼 |
| 生成 LLM | 6 | 用检索到的上下文生成答案 |

## RAG vs 微调成本/延迟权衡

| 维度 | RAG | 微调 |
|------|-----|------|
| 前期成本 | 低 | 高（GPU 训练） |
| 运行时延迟 | 增加（检索步骤） | 低（直接推理） |
| 知识更新 | 重新索引文档 | 重新训练 |
| 每查询基础设施 | 有（检索+向量库） | 无 |

## 混合策略示例

| 需求 | 最佳方案 |
|------|----------|
| 领域术语检索 | 微调嵌入模型 + RAG |
| 严格品牌语气 | SFT 微调 |
| 每日更新 + 最新知识 | RAG |
| 20 条静态 FAQ | 直接放入系统提示 |

---


### 数据集整理与清洗 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/cheatsheets/chapter-05.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/cheatsheets/chapter-05.md) · 语言：中文原文



# 数据集整理与清洗 — 速查表

## 去重方法

| 方法 | 捕获类型 | 实现 |
|------|----------|------|
| 精确去重 | 字节级相同（或归一化后相同） | SHA-256 哈希 |
| 近重复/模糊去重 | 高度重叠但不完全相同 | MinHash + LSH |

## MinHash LSH 调参

| 参数变化 | 效果 |
|----------|------|
| band 数↑ / 每 band 行数↓ | 召回率↑ 精确率↓ |
| band 数↓ / 每 band 行数↑ | 召回率↓ 精确率↑ |

## 质量过滤双管齐下

| 方法 | 示例 |
|------|------|
| 分类器打分 | fastText 分类器丢弃最低分文档 |
| 启发式规则 | 符号-词比例过高、重复 n-gram 过多 |

## 数据治理要求

| 要求 | 说明 |
|------|------|
| 许可核实 | 确认商业使用许可、署名、禁止演绎 |
| PII 处理 | 删除或脱敏个人可识别信息 |

## 灾难性 Forgotten

| 原因 | 缓解 |
|------|------|
| 微调数据混合严重偏离预训练分布 | 保持领域比例平衡 |
| 示例 | 预训练 15% 代码 → 微调几乎无代码 → 代码能力退化 |

## 指令微调数据一致性

| 操作 | 必要性 |
|------|--------|
| 统一模板 | system/user/assistant 角色、分隔符 |
| 删除离群样本 | 避免冲突的提示/响应结构 |

---


### 定制化策略 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/cheatsheets/chapter-06.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/cheatsheets/chapter-06.md) · 语言：中文原文



# 定制化策略 — 速查表

## PEFT 方法对比

| 方法 | 可训练参数 | 基座权重 | 内存节省机制 |
|------|-----------|----------|-------------|
| LoRA | 低秩矩阵 | 冻结 | 仅训练适配器 |
| QLoRA | 低秩矩阵 | 4-bit 量化冻结 | NF4 量化 + 双重量化 |
| P-tuning | 虚拟 token 嵌入 | 冻结 | 仅训练前缀 token |
| 适配器 | 瓶颈前馈层 | 冻结 | 仅训练小型层 |

## LoRA/QLoRA 内存对比

| 参数规模 | FP16 内存 | QLoRA 大约 |
|----------|-----------|-----------|
| 70B | ~140GB | ~35GB（4-bit） |

## RLHF vs DPO

| 维度 | RLHF | DPO |
|------|------|-----|
| 奖励模型 | 需要单独训练 | 不需要 |
| 优化算法 | PPO（强化学习） | 闭式损失 |
| 稳定性 | 较不稳定 | 更简单、更稳定 |
| 适用场景 | 偏好对齐 | 偏好对齐 |

## NeMo 组件对照

| 组件 | 用途 |
|------|------|
| NeMo Curator | 数据整理、过滤、去重 |
| NeMo Aligner | 偏好对齐（RLHF/DPO） |
| NeMo Guardrails | 运行时安全护栏 |
| Framework Launcher | 通用训练编排（SFT/PEFT） |

## NeMo PEFT 配置

| 配置键 | 作用 |
|--------|------|
| model.peft.peft_scheme | 选择 lora/ptuning/adapter/ia3 |
| trainer.precision | 数值精度（bf16/fp16/32） |
| model.optim.name | 优化器选择 |

---


### 分布式训练：数据、张量、流水线与序列并行 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/cheatsheets/chapter-07.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/cheatsheets/chapter-07.md) · 语言：中文原文



# 分布式训练：数据、张量、流水线与序列并行 — 速查表

## 四大并行策略对比

| 策略 | 切分对象 | 通信模式 | 适用场景 |
|------|----------|----------|----------|
| 数据并行 (DDP) | 数据批次 | all-reduce 梯度 | 模型能放入单 GPU |
| 张量并行 (TP) | 权重矩阵（单层内） | all-reduce 激活 | 单层过大，节点内 NVLink |
| 流水线并行 (PP) | 层（stage 间） | P2P send/recv 激活 | 多层模型，跨 GPU 分配 |
| 序列并行 (SP) | 序列维度（非张量部分） | all-reduce | 长上下文训练（64K+ token） |

## 关键选择规则

| 场景 | 首选策略 | 原因 |
|------|----------|------|
| 单层权重 + 微批=1 也装不下 | 张量并行 | 把权重矩阵切分到多 GPU |
| 模型能放下但想加速训练 | 数据并行 | 每 GPU 复制完整模型，分数据 |
| 节点内 8 GPU 训练大模型 | TP + PP 组合 | TP 节内高带宽，PP 跨节点 |
| 长序列 64K+ 激活内存瓶颈 | 序列并行 + TP | 切分非张量维度的激活 |

## 通信带宽需求

| 策略 | 最低要求 | 最优 |
|------|----------|------|
| 张量并行 | NVLink（节点内 900GB/s） | 不可跨节点 |
| 流水线并行 | InfiniBand / RoCE | 跨节点可接受 |
| 数据并行 | all-reduce（带宽/N） | NVLink + IB |

:::info 本章记忆锚点
张量并行切权重（节点内 NVLink）；流水线并行切层（可跨节点）；数据并行切数据（最简单）。单层装不下 → TP；模型能放下 → DDP。
:::

:::caution 高频陷阱
梯度检查点减少的是**激活内存**而非参数内存；数据并行**无法解决单层过大**问题（每 GPU 仍是完整模型）。
:::

---


### 推理加速：TensorRT-LLM、量化与投机解码 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/cheatsheets/chapter-08.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/cheatsheets/chapter-08.md) · 语言：中文原文



# 推理加速：TensorRT-LLM、量化与投机解码 — 速查表

## 量化方法对比

| 方法 | 精度 | 校准需求 | 特点 |
|------|------|----------|------|
| AWQ（激活感知权重量化） | INT4 | 校准数据集 | 保护显著权重通道，接近 FP16 精度 |
| GPTQ | INT4/INT8 | 校准数据集 | 逐层权重重建，Hessian 误差最小化 |
| FP8（H100/B200 原生） | FP8 | 无需/可选 | 硬件原生支持，精度损失最小 |
| INT8 训练后量化 | INT8 | 无校准 | 朴素方法，离群值上精度显著下降 |

## 关键选择规则

| 场景 | 最佳选择 | 原因 |
|------|----------|------|
| 70B 模型，内存受限，最小进度损失 | INT4 AWQ | 内存减至 ~1/4，精度接近 FP16 |
| H100/B200 GPU 部署 | FP8 | 硬件原生，最高吞吐 |
| 快速部署，无需重新训练 | 训练后量化（PTQ） | 无需训练循环，校准即可 |
| 内存极度受限（如单 GPU 70B） | GPTQ INT4 | 最小内存占用 |

## 投机解码（Speculative Decoding）

| 要素 | 说明 |
|------|------|
| 机制 | 小模型（draft）快速生成候选 token → 大模型并行验证 |
| 加速原理 | 单步内验证多个 token，利用验证比生成快 |
| 条件 | 小模型与大模型同分布前缀 |
| 加速比 | 通常 2–3×（取决于 draft 模型质量） |

## TensorRT-LLM 核心

| 特性 | 说明 |
|------|------|
| 本质 | NVIDIA 的 LLM 推理优化引擎 |
| 量化 | 支持 INT4/INT8/FP8 |
| KV Cache | PagedAttention 式管理 |
| 并行 | 张量并行 + 流水线并行 |
| NIM 底层 | NIM = TensorRT-LLM + Triton + 容器化 |

:::info 本章记忆锚点
AWQ = 激活感知保护显著权重；GPTQ = Hessian 逐层重建；投机解码 = 小模型猜 + 大模型验；TensorRT-LLM 是 NIM 的核心引擎。
:::

:::caution 高频陷阱
减少批大小解决不了**每权重内存**问题（模型本身太大）；FP8 需要 H100/B200+ 硬件原生支持；朴素 INT8 无校准在离群值上精度损失严重。
:::

---


### LLM 服务化：NVIDIA NIM、Triton Inference Server 与模型仓库 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/cheatsheets/chapter-09.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/cheatsheets/chapter-09.md) · 语言：中文原文



# LLM 服务化：NVIDIA NIM、Triton Inference Server 与模型仓库 — 速查表

## NIM vs Triton 选型

| 维度 | NVIDIA NIM | Triton Inference Server |
|------|------------|------------------------|
| 定位 | 预优化的 LLM 推理微服务 | 通用模型服务平台 |
| 部署速度 | 最快（分钟级，预构建） | 需配置（小时-天级） |
| API | OpenAI 兼容，标准化 | 自定义/多协议 |
| 支持模型 | 预定义模型目录 | 任意模型（PyTorch/ONNX/TensorRT） |
| 复杂流水线 | 不支持 ensemble | 支持 ensemble 多模型链 |
| 批处理 | 内置 continuous batching | 需配置 |
| 典型场景 | 快速上线标准 LLM | 多后端、ensemble、生产平台 |

## NGC 目录

| 内容 | 说明 |
|------|------|
| 模型 | 预训练 + 优化模型检查点 |
| 容器 | NIM、RAPIDS、DeepStream 等 |
| Helm Charts | Kubernetes 部署配置 |
| 角色 | AI 工作流组件的一站式注册中心 |

## NIM 核心特性

| 特性 | 说明 |
|------|------|
| 底层引擎 | TensorRT-LLM |
| 服务层 | Triton Inference Server |
| API | OpenAI 兼容（/v1/chat/completions） |
| 优化 | 量化、KV Cache、continuous batching |
| 部署 | 容器化，一行命令启动 |

:::info 本章记忆锚点
NIM = 优化好的 LLM 开箱即用（标准化）；Triton = 自定义/多后端/ensemble（灵活性）。快速上线选 NIM；复杂流水线选 Triton ensemble。
:::

:::caution 高频陷阱
NIM 不支持任意 ensemble 流水线（那是 Triton 的领域）；自定义 Triton 后端需要大量工程但不适用快速单模型部署；Flask 封装缺少生产级批处理和扩展。
:::

---


### 自动扩缩容、发布上线与 LLM MLOps 生命周期监控 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/cheatsheets/chapter-10.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/cheatsheets/chapter-10.md) · 语言：中文原文



# 自动扩缩容、发布上线与 LLM MLOps 生命周期监控 — 速查表

## 扩缩容信号

| 信号 | 适用场景 | 局限性 |
|------|----------|--------|
| GPU 利用率 | 稳态计算密集型任务 | LLM 推理中可能误导（利用率中等但队列积压） |
| 队列深度 + 延迟 SLO | **LLM 推理首选** | 需要良好的监控基础设施 |
| 请求速率 | 突发流量检测 | 不反映单请求处理成本 |
| 生成长度 | 自适应批处理预测 | 需历史数据训练 |

:::warning LLM 服务扩容黄金规则
队列深度加延迟 SLO 违约是面向用户体验的**先行指标**。GPU 利用率在 LLM 推理中是**滞后/误导性信号**（可变生成长度导致利用率中等但请求排队）。
:::

## 发布策略对比

| 策略 | 机制 | 适用场景 |
|------|------|----------|
| 金丝雀发布 | 5% 流量导新版本，渐进扩大 | 标准无状态模型更新 |
| 蓝绿部署 | 两套环境并行，瞬时切换 | 需快速回滚的关键服务 |
| 影子流量 | 新版本处理副本流量，不影响用户 | 验证新模型行为 |
| A/B 测试 | 同时运行两个版本对比指标 | 模型效果对比评估 |

## 向后不兼容变更处理

| 变更类型 | 正确做法 |
|----------|----------|
| 分词器改动（缓存不兼容） | 蓝绿部署，切换需清空旧缓存提示 |
| 模型架构变化 | 金丝雀 + 完整回滚计划 |
| prompt/schema 变更 | 验证所有下游消费者 |

## MLOps 监控指标

| 层级 | 关键指标 | 告警阈值依据 |
|------|----------|-------------|
| 基础设施 | GPU 显存、温度、功耗 | 硬件规格 |
| 服务 | p50/p99 延迟、吞吐、队列深度 | SLO 定义 |
| 业务 | 用户满意度、token 成本 | 业务目标 |

:::info 本章记忆锚点
LLM 扩容看队列+延迟（非 GPU 利用率）；标准更新用金丝雀；不兼容变更用蓝绿部署。
:::

:::caution 高频陷阱
GPU 利用率在 LLM 推理中是误导性扩容信号；分词器改动若不向后兼容必须蓝绿部署而非金丝雀。
:::

---


### 生产监控与可靠性 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/cheatsheets/chapter-11.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/cheatsheets/chapter-11.md) · 语言：中文原文



# 生产监控与可靠性 — 速查表

## 监控仪表板设计

| 层级 | 关键指标 | 数据源 |
|------|----------|--------|
| 硬件基础设施 | GPU 显存利用率、温度、功耗、NVLink 带宽 | DCGM + Prometheus |
| 模型服务 | p50/p99 延迟、token/s、队列深度、错误率 | Triton metrics / NIM telemetry |
| 数据质量 | 输入分布漂移、异常 token 占比 | 自定义 metric exporter |
| 业务运营 | 用户满意度、每百万 token 成本 | 应用埋点 + 计费日志 |

## 异常检测与告警

| 异常类型 | 检测方法 | 响应 |
|----------|----------|------|
| 分布漂移（输入） | KL 散度 / PSI 统计量 | 触发自动重训管道 |
| 输出质量下降 | 自动 rouge/bleu 监控 + 用户反馈回路 | 降级到旧模型版本 |
| 服务降级 | p99 延迟超 SLO 阈值 | 自动扩容 + 告警值班 |
| 硬件故障 | DCGM ECC 错误 + XID 事件 | 自动从服务池隔离节点 |

## 根因分析（RCA）流程

| 步骤 | 操作 |
|------|------|
| 1. 确认告警 | 区分真警 vs 误警（阈值合理性） |
| 2. 关联变更 | 检查最近的模型版本/配置变更 |
| 3. 分层排查 | 硬件 → 网络 → 模型服务 → 应用 |
| 4. 数据取证 | 拉取 trace/log/metric 分布对比 |
| 5. 修复 + 复发预防 | 修复根因 + 增加自动化检测 |

## 自动化微调与重训触发

| 触发条件 | 管道动作 |
|----------|----------|
| 新标注数据累计到阈值 | 启动 LoRA 增量微调 |
| 输入分布漂移超过 PSI > 0.2 | 全量数据 + 微调启动 |
| 定期（周/月） | 数据质量审核 + 可选重训 |

## 版本管理与回滚

| 工具 | 用途 |
|------|------|
| MLflow / Weights & Biases | 实验跟踪 + 指标对比 |
| DVC（Data Version Control） | 数据集版本化 |
| NGC Registry / Harbor | 模型镜像版本管理 |
| Kubernetes Rollout | Deployment 版本历史 + 一键回滚 |

:::info 记忆锚点
监控层级=硬件→服务→数据→业务；异常检测=漂移+质量+硬件；RCA=确认→关联变更→分层排查；重训触发=新数据+漂移+周期；MLflow=DVC+版本回滚。
:::

---


### 考试策略与全真模拟 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/cheatsheets/chapter-12.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/cheatsheets/chapter-12.md) · 语言：中文原文



# 考试策略与全真模拟 — 速查表

## 域权重与备考优先级

| 域 | 权重 | 备考优先级 |
|----|------|-----------|
| 4 · 模型优化 | 17% | ★★★★★ |
| 7 · GPU 加速和优化 | 14% | ★★★★★ |
| 2 · 提示工程 | 13% | ★★★★ |
| 5 · 微调 | 13% | ★★★★ |
| 3 · 数据准备 | 9% | ★★★ |
| 8 · 模型部署 | 9% | ★★★ |
| 6 · 评估 | 7% | ★★★ |
| 9 · 生产监控与可靠性 | 7% | ★★★ |
| 1 · LLM 架构 | 6% | ★★ |

## 考试节奏

| 部分 | 时间 | 策略 |
|------|------|------|
| ~55 道选择题 | 120 分钟 | 每题约 2.2 分钟；超过 3 分钟标记跳过 |
| 无动手实验 | — | 全部是选择题（可能含拖拽/连线） |

## 高频陷阱速查

| 陷阱 | 正确理解 |
|------|----------|
| GPU 利用率 = 扩容信号 | LLM 推理中应是队列深度 + 延迟 SLO |
| 分词器改动可热更新 | 不向后兼容时必须蓝绿部署 |
| 所有场景都适合 RAG | 单文档大模型足够时 RAG 反增成本 |
| LoRA 对所有层有效 | LoRA 通常作用于 attention 层 |

## 跨域综合场景推理

| 场景 | 关键推理 |
|------|----------|
| 推理延迟高但 GPU 利用率低 | → 瓶颈在 CPU post-processing 或 IO；非 GPU 不足 |
| 微调后效果反而下降 | → 过拟合小数据集；需回退+增加正则 |
| 部署新模型后错误率上升 | → 输入分布不一致；需 shadow traffic 验证 |
| 多 GPU 训练速度未线性扩展 | → 通信瓶颈；检查 NCCL/IB 配置 |

:::info 记忆锚点
域权重排序：模型优化(17%)>GPU加速(14%)>提示(13%)=微调(13%)>数据=部署(9%)>评估=监控(7%)>架构(6%)；扩容看队列非利用率；分词器不兼容需蓝绿。
:::

---



## 记忆卡


### ML 与神经网络基础 — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/flashcards/chapter-01.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/flashcards/chapter-01.md) · 语言：中文原文



# ML 与神经网络基础 — 知识卡片

## 卡片 1

**Q：如何快速判断题目描述的是无监督学习？**

A：关键词"无标签数据"或"发现隐藏模式" → 无监督学习。"智能体获得奖励" → 强化学习。

---

## 卡片 2

**Q：过拟合和欠拟合的核心区别是什么？**

A：
- 过拟合：训练损失**很低**但验证损失**很高**（模型记忆了训练数据）
- 欠拟合：训练和验证损失**都高**（模型太简单）

---

## 卡片 3

**Q：为什么推理时要关闭 Dropout？**

A：推理时使用所有神经元获得完整模型容量。训练时 Dropout 用于防过拟合，推理时 rate = 0。考试常考。

---

## 卡片 4

**Q：分类问题的损失函数为什么不能用 MSE？**

A：分类任务的输出是概率分布，应用交叉熵损失。回归任务输出连续值，才用 MSE。交叉使用是考试陷阱。

---

## 卡片 5

**Q：L1 和 L2 正则化的区别？**

A：
- L1（Lasso）：产生稀疏权重（许多 → 0），用于特征选择
- L2（Ridge）：产生小权重（极少为 0），通用防过拟合最常见

---


### Transformer 架构与 LLM — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/flashcards/chapter-02.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/flashcards/chapter-02.md) · 语言：中文原文



# Transformer 架构与 LLM — 知识卡片

## 卡片 1

**Q：注意力计算中为什么要除以 sqrt(d_k)？**

A：防止点积过大导致 softmax 饱和。不缩放上层的梯度会消失。

---

## 卡片 2

**Q：多头注意力的维度如何计算？**

A：每个头维度 = embedding_dim ÷ num_heads。例：12 头 × 64 维 = 768 维嵌入。

---

## 卡片 3

**Q：Encoder-only、Decoder-only、Encoder-Decoder 各自适合什么任务？**

A：
- Encoder-only（BERT）：分类、NER、句子任务
- Decoder-only（GPT）：文本生成
- Encoder-Decoder（T5）：翻译、摘要

---

## 卡片 4

**Q：为什么需要位置编码？**

A：没有它，自注意力是置换不变的（顺序无关）。位置编码注入 token 的序列位置信息。

---

## 卡片 5

**Q：注意力计算的三个矩阵 Q、K、V 分别代表什么？**

A：
- Q（query）：token 在寻找什么
- K（key）：token 提供的内容
- V（value）：要检索的实际内容

---


### 提示工程 — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/flashcards/chapter-03.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/flashcards/chapter-03.md) · 语言：中文原文



# 提示工程 — 知识卡片

## 卡片 1

**Q：Few-shot 提示的示例数量范围？**

A：1-5 个示例。加入示例可提高 10-30% 准确率。

---

## 卡片 2

**Q：思维链（CoT）提示的正确触发短语？**

A："Let's think step by step" — 推理准确率提升 20-40%。

---

## 卡片 3

**Q：Temperature = 0 的效果是什么？**

A：确定性输出（相同输入 → 相同输出）。不会防止幻觉，但输出稳定。

---

## 卡片 4

**Q：Top-p = 0.1 意味着什么？**

A：仅考虑前 10% 概率的 token — 非常聚焦。适合需技术准确性的任务。

---

## 卡片 5

**Q：复杂任务的最佳分解策略是什么？**

A：拆分为子任务，分别给出指令。比单一复杂提示效果好得多。

---


### 对齐、安全与负责任 AI — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/flashcards/chapter-04.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/flashcards/chapter-04.md) · 语言：中文原文



# 对齐、安全与负责任 AI — 知识卡片

## 卡片 1

**Q：RLHF 流水线的三个阶段按顺序是什么？**

A：1. 监督微调（SFT）→ 2. 奖励模型训练 → 3. RL 优化（PPO）。顺序不可颠倒。

---

## 卡片 2

**Q：幻觉的根本原因是什么？**

A：模型在下一 token 预测上训练，而非真实验证。置信度得分反映 token 概率，而非事实准确性。

---

## 卡片 3

**Q：为什么 Temperature 0.0 不能防止幻觉？**

A：Temperature 0.0 仅使输出确定（选择概率最高的 token），但模型仍会"自信地"生成事实错误。

---

## 卡片 4

**Q：缓解幻觉最有效的技术是什么？**

A：**RAG（检索增强生成）** — 架构级约束，检索已验证文档并指示引用来源。

---

## 卡片 5

**Q：奖励模型的训练数据是什么？**

A：人类偏好比较（A vs B）。分类器学习预测人类偏好的回复。

---


### 数据预处理与特征工程 — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/flashcards/chapter-05.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/flashcards/chapter-05.md) · 语言：中文原文



# 数据预处理与特征工程 — 知识卡片

## 卡片 1

**Q：NLP/ML 任务推荐使用哪种 Unicode 归一化？**

A：**NFKC** — 兼容性归一化 + 组合，减少词汇量。人类文本用 NFC。

---

## 卡片 2

**Q：BPE/WordPiece 分词的主要优势是什么？**

A：零 [UNK] 率 + 合理的序列长度。多数 LLM 的首选分词方案。

---

## 卡片 3

**Q：Transformer 注意力内存的扩展规律？**

A：O(n²) — 序列长度翻倍 = 4× 内存。2048 tokens 需要约 4-8× 512 tokens 的内存。

---

## 卡片 4

**Q：注意力掩码中 1 和 0 分别代表什么？**

A：1 = 真实 token（关注），0 = padding（忽略）。

---


### LLM 集成与部署 — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/flashcards/chapter-07.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/flashcards/chapter-07.md) · 语言：中文原文



# LLM 集成与部署 — 知识卡片

## 卡片 1

**Q：RAG 架构的正确流程？**

A：查询 → 嵌入 → 向量搜索 → 检索 Top-K 块 → 注入提示 → LLM 生成。

---

## 卡片 2

**Q：低于 500 个训练示例时，默认选择什么方案？**

A：**提示工程 / RAG** — 微调需要超过 1000 标注示例才能有效。

---

## 卡片 3

**Q：FAISS 和 Milvus 的区别是什么？**

A：
- FAISS：本地库，适合原型（低于 1000 万向量）
- Milvus：自托管，适合大规模生产

---

## 卡片 4

**Q：什么时候应该选择微调而不是 RAG？**

A：需要永久改变风格/格式/领域，且有超过 1000 标注示例时。动态知识/新鲜度需求选 RAG。

---


### NVIDIA 软件栈 — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/flashcards/chapter-08.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/flashcards/chapter-08.md) · 语言：中文原文



# NVIDIA 软件栈 — 知识卡片

## 卡片 1

**Q：NeMo 和 NIM 的核心区别？**

A：
- NeMo：训练/微调框架（LLM 开发）
- NIM：部署微服务（LLM 生产部署）

---

## 卡片 2

**Q：TensorRT-LLM 的主要优化手段？**

A：量化（INT4/INT8/FP8）、内核融合、多 GPU 并行。用于自定义优化流水线和最大性能。

---

## 卡片 3

**Q：Triton Inference Server 适合什么场景？**

A：多模型部署、生产监控。支持动态批处理、并发执行、版本控制、健康检查。

---

## 卡片 4

**Q：NVIDIA Riva 用于什么任务？**

A：语音 AI — ASR（语音→文本）和 TTS（文本→语音）。

---


### 考试策略 — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/flashcards/chapter-10.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/flashcards/chapter-10.md) · 语言：中文原文



# 考试策略 — 知识卡片

## 卡片 1

**Q：NCA-GENL 考试的通过标准约是多少？**

A：约 70%（50-51 题中答对约 36 题）。60 分钟完成。

---

## 卡片 2

**Q：超过多少秒未解应标记跳过？**

A：90 秒。标记并跳过，最后用 5 分钟缓冲时间处理标记题。

---

## 卡片 3

**Q：RLHF 和 SFT 的关键区别？**

A：RLHF = 3 步流程（SFT + 奖励模型 + PPO）；SFT = 直接示例学习。

---

## 卡片 4

**Q：翻译任务和摘要任务分别用什么评估指标？**

A：翻译 → BLEU（精确率）；摘要 → ROUGE（召回率）。

---


### Transformer 内部机制 — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/flashcards/chapter-01.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/flashcards/chapter-01.md) · 语言：中文原文



# Transformer 内部机制 — 知识卡片

## 卡片 1

**Q：GQA 与 MHA 的核心区别是什么？对 KV 缓存有什么影响？**

A：GQA 让多个查询头共享一个 KV 头（如组大小 4 → 32 查询头配 8 KV 头），KV 缓存为 MHA 的 1/4。考试提示：当题干要求"长上下文、内存受限"时选 GQA。

---

## 卡片 2

**Q：MQA 与 GQA 的区别？何时选 MQA 而非 GQA？**

A：MQA 让所有查询头共享单个 KV 头（最小 KV 缓存），代价是有适度质量损失。当需要"绝对最小 KV 缓存且可容忍质量下降"时选 MQA。考试提示：题干出现"最高吞吐推理+可接受质量损失"选 MQA。

---

## 卡片 3

**Q：FlashAttention 的数学本质是什么？为什么它比标准注意力更快？**

A：FlashAttention 是 IO 感知的分块精确算法——数学上**精确**（非近似），把 Q/K/V 块保留在 SRAM 中处理，避免在 HBM 中实例化 N×N 矩阵。考试提示：关键词"避免 HBM 中完整矩阵"= FlashAttention。

---

## 卡片 4

**Q：位置编码外推能力最好的方法是哪种？**

A：ALiBi（线性偏置直接加到注意力分数）和 RoPE + 高 theta。可学习绝对嵌入和正弦绝对编码外推能力差。考试提示：题干要求"不做微调、超出训练长度的稳定性能"→ ALiBi。

---

## 卡片 5

**Q：编码器-解码器 vs 仅解码器的关键区别？各自适用场景？**

A：编码器-解码器：双向自注意力+交叉注意力，适合翻译/摘要（seq2seq）。仅解码器：统一因果注意力，适合开放式生成/通用 LLM。考试提示：现代通用 LLM 几乎都是仅解码器。

---


### 缩放定律、分词与上下文窗口机制 — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/flashcards/chapter-02.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/flashcards/chapter-02.md) · 语言：中文原文



# 缩放定律、分词与上下文窗口机制 — 知识卡片

## 卡片 1

**Q：Chinchilla 计算的 token-参数比是多少？70B 模型需要多少训练 token？**

A：约 20 token/参数。70B × 20 ≈ 1400 亿 token。考试提示：记住"每参数约 20 个 token"。

---

## 卡片 2

**Q：SentencePiece 与经典 BPE 的关键结构差异是什么？**

A：经典 BPE 先按空白符预切分再合并字节对；SentencePiece 把输入视为原始字符/字节流，空白符当普通符号处理。考试提示：CJK 语言（无空白符边界）→ 选 SentencePiece。

---

## 卡片 3

**Q：免训练扩展 RoPE 上下文长度的最佳方法是哪种？**

A：NTK-aware RoPE 缩放（非均匀调整旋转频率）。位置插值(PI)需要微调才能恢复质量，违反免训练约束。考试提示：题干强调"不做额外微调"→ NTK-aware。

---

## 卡片 4

**Q：增大 RoPE theta（如 10000→500000）对上下文扩展的原理是？**

A：增大 theta 减慢旋转频率 → 相位回绕前可表示更长的相对距离 → 支持更长上下文。考试提示：Llama 3/Code Llama 使用此技术。

---

## 卡片 5

**Q：MoE 架构的核心优势是什么？**

A：总参数量大（高容量）但每个 token 只激活 top-k 专家 → 每 token 算力接近小稠密模型。考试提示："总参数大但每 token FLOPs 低"= MoE。

---


### 高级提示词：思维链、ReAct 与受限解码 — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/flashcards/chapter-03.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/flashcards/chapter-03.md) · 语言：中文原文



# 高级提示词：思维链、ReAct 与受限解码 — 知识卡片

## 卡片 1

**Q：受限解码的核心机制是什么？适用什么场景？**

A：在生成时**屏蔽无效 token**，保证输出针对 schema 的语法有效性。适用：JSON schema 强制、枚举值约束（如 APPROVED/REJECTED/PENDING）。考试提示：题干要求"零容忍格式错误"+ "严格 schema"→ 受限解码。

---

## 卡片 2

**Q：ReAct 模式的步骤序列是什么？适用什么场景？**

A：Thought → Action（工具调用）→ Observation → 重复直到 Final Answer。适用：需要外部实时信息的场景（如查询股价后推理）。考试提示：题干有"通过 API 实时查询"+ "基于结果推理下一步"→ ReAct。

---

## 卡片 3

**Q：自洽性（self-consistency）的工作原理和前提条件？**

A：温度>0 下采样多条不同 CoT 路径 → 多数投票选最终答案。前提：需要 temperature>0 产生多样性。考试提示：CoT+自洽性= 成本换准确率，延迟/成本不受限时最佳。

---

## 卡片 4

**Q：零样本、单样本、少样本提示的定义分别是什么？**

A：零样本=仅指令无示例；单样本=恰好 1 个示例；少样本=多个示例。考试提示：区分 one-shot 和 few-shot 的确切定义。

---

## 卡片 5

**Q：何时不应使用 CoT+自洽性？**

A：简单二分类任务——成本增至三倍但准确率提升有限。应把 CoT+自洽性留给需要多步推理的任务。考试提示：不要一刀切地应用高级提示技术。

---


### RAG 作为适配手段：提示词 vs RAG vs 微调的决策框架 — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/flashcards/chapter-04.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/flashcards/chapter-04.md) · 语言：中文原文



# RAG 作为适配手段：提示词 vs RAG vs 微调的决策框架 — 知识卡片

## 卡片 1

**Q：RAG、微调、提示词三种适配策略的核心权衡是什么？**

A：RAG：训练成本≈0 但运行时检索延迟+基础设施成本；微调：前期训练成本高但每次查询延迟低/开销低；提示词：零成本但受限于上下文窗口和知识时效性。考试提示：每日更新+有限算力 → RAG（知识时效性与模型解耦）。

---

## 卡片 2

**Q：小规模静态 FAQ（20 条）最简单的适配方法是什么？**

A：直接放进系统提示/上下文窗口，无需 RAG 或微调。考试提示：20 条静态内容 = 直接塞提示；只有大规模/动态知识才需要 RAG。

---

## 卡片 3

**Q：RAG 中重排序器的作用是什么？运行在哪个阶段？**

A：在检索器返回初始 top-k 后、生成器之前，用更精确方法（如交叉编码器）重新打分和精炼结果。考试提示：重排序器在**检索之后、生成之前**运行。

---

## 卡片 4

**Q：过大的分块对 RAG 检索质量有什么负面影响？**

A：多个主题混入单个向量 → 稀释相关性信号 → 检索精确度下降 + 可能超出上下文窗口。考试提示：分块过大 ≠ 好，通常 300-500 token/块是合理范围。

---

## 卡片 5

**Q：需要严格品牌口吻+低延迟的生产环境应选什么适配策略？**

A：在品牌语气示例上**微调**——把行为模式直接固化进权重，不增加运行时检索延迟。考试提示：一致的风格/行为 → 微调；外部知识注入 → RAG。

---


### 数据集整理、清洗与指令微调数据设计 — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/flashcards/chapter-05.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/flashcards/chapter-05.md) · 语言：中文原文



# 数据集整理、清洗与指令微调数据设计 — 知识卡片

## 卡片 1

**Q：MinHash + LSH 做近似去重的原理是什么？**

A：MinHash 近似 shingle 集合间的 Jaccard 相似度，LSH 把相似签名分同一桶 → 只比较同桶候选对，避免 O(n²) 全量比较。考试提示：大规模语料 85% 相似度去重 → MinHash+LSH。

---

## 卡片 2

**Q：增加 LSH band 数（每个 band 行数减少）对去重结果有什么影响？**

A：召回率上升（更多对被标记为候选）、精确率下降（误报增多）。考试提示：band 更多、每 band 行数更少 → 降低碰撞阈值 → 召回↑ 精确↓。

---

## 卡片 3

**Q：指令微调前对格式不一致的训练数据必须做什么？**

A：归一化到单一一致的提示模板（system/user/assistant 角色、分隔符），删除或标准化离群样本。考试提示：格式不一致会教模型互相冲突的结构 → 必须统一。

---

## 卡片 4

**Q：微调数据混合与预训练分布严重偏离的后果是什么？**

A：灾难性forgeting——模型参数偏离先前学到的能力（如几乎不加代码 → 编码能力下降）。考试提示：微调数据混合失衡 → 灾难性遗忘非均匀领域能力。

---

## 卡片 5

**Q：精确去重与近重复去重的本质区别是什么？**

A：精确去重匹配字节级相同（或归一化后相同）的内容；近重复去重用相似度估计捕获大幅重叠但不完全相同的文档。考试提示：近重复去重的删除集合**包含**精确重复的超集。

---


### 定制化策略：LoRA/QLoRA、RLHF vs DPO 与 NVIDIA NeMo — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/flashcards/chapter-06.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/flashcards/chapter-06.md) · 语言：中文原文



# 定制化策略：LoRA/QLoRA、RLHF vs DPO 与 NVIDIA NeMo — 知识卡片

## 卡片 1

**Q：QLoRA 如何将 70B 模型放进单张 80GB GPU？**

A：把冻结基座权重量化为 4-bit NF4（70B 从 ~140GB 降至 ~35GB），只训练小型 LoRA 适配器。考试提示：单 GPU 大模型微调 → QLoRA。

---

## 卡片 2

**Q：DPO 与 RLHF 的核心概念区别是什么？**

A：RLHF 训练单独奖励模型 + PPO RL 循环；DPO 用闭式损失直接在偏好对上优化策略，无需奖励模型或 RL 循环。考试提示：更简单+更稳定 → DPO；需要显式奖励解释性 → RLHF。

---

## 卡片 3

**Q：NeMo Aligner 与 NeMo Curator 的区别是什么？**

A：NeMo Aligner = 偏好对齐（奖励模型 + PPO + DPO）；NeMo Curator = 数据整理（过滤+去重）。考试提示：Aligner 对齐；Curator 整理——功能完全不同。

---

## 卡片 4

**Q：P-tuning 与 LoRA 的机制区别是什么？**

A：P-tuning：在输入前附加可训练虚拟 token 嵌入，基座模型完全冻结；LoRA：向现有权重层注入可训练低秩矩阵。考试提示：虚拟 token → P-tuning；低秩矩阵注入 → LoRA。

---

## 卡片 5

**Q：无标注 50GB 法律文档想让模型先内化风格，应先做什么？**

A：在语料上做**继续预训练**（领域自适应预训练），适配词汇和风格，后续再做任务微调。考试提示：无标注领域文本 → 继续预训练；有标注指令对 → LoRA/DPO。

---


### 分布式训练：数据、张量、流水线与序列并行 — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/flashcards/chapter-07.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/flashcards/chapter-07.md) · 语言：中文原文



# 分布式训练：数据、张量、流水线与序列并行 — 知识卡片

## 卡片 1

**Q：单层权重过大装不下时应选哪种并行策略？为什么？**

A：张量并行——把权重矩阵切分到多 GPU，直接解决单层过大。数据并行每 GPU 复制完整模型无效；流水线并行每 GPU 仍需容纳完整一层。考试提示：单层装不下 → 张量并行（需节点内 NVLink）。

---

## 卡片 2

**Q：长序列 64K token 训练时激活内存瓶颈的专属解决方案是什么？**

A：序列并行——与张量并行结合，切分非张量维度的序列部分，专门解决长序列激活内存主导问题。考试提示：长上下文训练 + 激活内存瓶颈 → 序列并行。

---

## 卡片 3

**Q：张量并行为何不能跨节点？**

A：张量并行需要极高的通信带宽和极低延迟（每次前向/反向都需 all-reduce），只有节点内 NVLink（900GB/s）能满足。跨节点 IB 带宽不够。考试提示：TP 限于节点内；PP/DDP 可跨节点。

---

## 卡片 4

**Q：微批大小=1 仍装不下前馈层时，梯度检查点有帮助吗？**

A：无——梯度检查点减少的是**激活内存**（前向中间结果），不减少参数内存。超大单层属于参数内存问题。考试提示：区分"参数内存"vs"激活内存"的优化手段。

---

## 卡片 5

**Q：64 GPU 集群训练大模型，节点内 8 GPU + NVLink，应如何组合并行策略？**

A：节点内用张量并行（8 路 TP），节点间用数据并行或流水线并行。典型方案：TP(8) + PP(跨节点) + DDP。考试提示：节点内高带宽 → TP；跨节点 → PP/DDP。

---


### 推理加速：TensorRT-LLM、量化与投机解码 — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/flashcards/chapter-08.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/flashcards/chapter-08.md) · 语言：中文原文



# 推理加速：TensorRT-LLM、量化与投机解码 — 知识卡片

## 卡片 1

**Q：内存受限场景下部署 70B 模型，最优量化方法是？**

A：INT4 AWQ——通过激活统计量保护显著权重通道，在 INT4 内存下接近 FP16 精度。考试提示：INT4 AWQ = 内存受限大模型推理首选。

---

## 卡片 2

**Q：GPTQ 与 AWQ 的区别是什么？**

A：GPTQ 使用逐层权重重建 + Hessian 误差最小化（二阶信息）；AWQ 通过激活分布保护显著权重通道。两者都是 INT4 量化但校准机制不同。考试提示：Hessian/逐层重建 → GPTQ。

---

## 卡片 3

**Q：投机解码的加速原理是什么？**

A：小模型（draft）快速生成候选 token → 大模型并行验证（逐步验证比逐步生成快）→ 单步产出多个 token。加速比通常 2–3×。考试提示：投机解码 = 小猜大验。

---

## 卡片 4

**Q：H100/H200 GPU 上最佳的推理精度/吞吐权衡是什么？**

A：FP8 推理——H100/B200 硬件原生支持 FP8，精度损失最小且吞吐极高。考试提示：新一代 GPU（H100+）推理 → FP8 最优。

---

## 卡片 5

**Q：TensorRT-LLM 与 NIM 的关系是什么？**

A：NIM 微服务底层使用 TensorRT-LLM 做推理优化 + Triton Inference Server 做服务层 + 容器化封装。NIM = TensorRT-LLM + Triton + 容器。考试提示：NIM 是"打包好的" TensorRT-LLM。

---


### LLM 服务化：NVIDIA NIM、Triton Inference Server 与模型仓库 — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/flashcards/chapter-09.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/flashcards/chapter-09.md) · 语言：中文原文



# LLM 服务化：NVIDIA NIM、Triton Inference Server 与模型仓库 — 知识卡片

## 卡片 1

**Q：两天内部署 Llama 3 70B 暴露 OpenAI API，应选什么方案？**

A：从 NVIDIA NIM（NGC 目录）部署——预打包+GPU 优化+标准化 OpenAI 兼容 API，几分钟即可部署。考试提示：快速标准化部署 → NIM。

---

## 卡片 2

**Q：需要 ensemble 流水线（预处理 Python + TensorRT LLM + 重排序）时应选什么方案？**

A：自定义 Triton Inference Server 部署——NIM 不支持任意 ensemble，Triton 原生支持多后端 ensemble 链。考试提示：复杂/自定义流水线 → Triton。

---

## 卡片 3

**Q：NIM 不支持的功能是什么？此时应选什么？**

A：NIM 不支持任意 ensemble 流水线和多后端链。需选 Triton Inference Server（自定义部署）。考试提示：需要 ensemble → Triton；快速单模型 → NIM。

---

## 卡片 4

**Q：NGC 目录提供哪些类型的资源？**

A：预训练/优化模型检查点、容器（NIM/RAPIDS 等）、Helm Charts、AI 工作流组件。考试提示：NVIDIA 的模型+容器一站式注册中心。

---

## 卡片 5

**Q：PyTorch、ONNX、TensorRT 三后端模型 + ensemble 共享 GPU 基础选什么？**

A：NVIDIA Triton Inference Server——原生支持多后端 + ensemble 调度。考试提示：多后端/多框架 → Triton 独有优势。

---


### 自动扩缩容、发布上线与 LLM MLOps 生命周期监控 — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/flashcards/chapter-10.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/flashcards/chapter-10.md) · 语言：中文原文



# 自动扩缩容、发布上线与 LLM MLOps 生命周期监控 — 知识卡片

## 卡片 1

**Q：LLM 推理场景中仅看 GPU 利用率做扩容决策为什么是误导性的？**

A：可变生成长度导致利用率看似正常但请求在排队。队列深度+延迟 SLO 违约才是用户体验劣化的先行指标。考试提示：LLM 扩容 → 队列深度 + 延迟 SLO，**而非 GPU 利用率**。

---

## 卡片 2

**Q：分词器改动导致向后不兼容时，应使用哪种发布策略？**

A：蓝绿部署——两套环境并行，瞬时切换+可瞬时回滚（而非渐进金丝雀）。考试提示：不兼容变更 → 蓝绿；无状态渐进 → 金丝雀。

---

## 卡片 3

**Q：金丝雀发布的标准操作是什么？**

A：新版本先接 5% 流量 → 观察指标 → 渐进扩大至 100%。考试提示：金丝雀 = 渐进流量切换；蓝绿 = 瞬时两环境切换。

---

## 卡片 4

**Q：LLM 服务化的 MLOps 关键监控指标有哪些？**

A：p50/p99 延迟、吞吐（tokens/sec）、队列深度、GPU 显存利用率、每 token 成本。考试提示：服务级别指标面向用户体验+成本。

---

## 卡片 5

**Q：收到人类偏好对齐需求但要求最简单稳定的训练流水线应选什么？**

A：DPO（直接偏好优化）——比 RLHF 更简单、更稳定，无需单独奖励模型。考试提示：偏好数据+简单稳定 → DPO。

---


### 第 11 章：生产监控与可靠性 — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/flashcards/chapter-11.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/flashcards/chapter-11.md) · 语言：中文原文



# 第 11 章：生产监控与可靠性 — 知识卡片

## 卡片 1

**Q：LLM 生产监控的四层架构？**

A：1. 硬件基础设施（GPU 显存/温度/功耗/DCGM）→ 2. 模型服务（p50/p99 延迟、token/s、队列深度）→ 3. 数据质量（输入分布漂移、异常 token 占比）→ 4. 业务运营（用户满意度、token 成本）。考试：四层缺一不可。

---

## 卡片 2

**Q：分布漂移如何检测和响应？**

A：计算输入数据的 KL 散度或 PSI（Population Stability Index）→ 超过阈值（PSI > 0.2）触发自动重训管道。考试：PSI > 0.2 = 显著漂移阈值。

---

## 卡片 3

**Q：根因分析（RCA）的标准流程？**

A：1. 确认告警（真警/误警）→ 2. 关联变更（最近部署/配置）→ 3. 分层排查（硬件→网络→服务→应用）→ 4. 取证（trace/log/metric）→ 5. 修复 + 复发预防。考试：第一件事是确认不是误警。

---

## 卡片 4

**Q：版本管理工具链各负责什么？**

A：MLflow = 实验跟踪+指标；DVC = 数据集版本；NGC/Harbor = 模型镜像仓库；K8s Rollout = 部署版本回滚。考试：分工明确，互不替代。

---


### 第 12 章：考试策略与模拟 — 知识卡片


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/flashcards/chapter-12.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/flashcards/chapter-12.md) · 语言：中文原文



# 第 12 章：考试策略与模拟 — 知识卡片

## 卡片 1

**Q：NCP-GENL 哪些域权重最高？**

A：模型优化 17%（最高）→ GPU 加速 14% → 提示工程 13% = 微调 13% → 数据准备 9% = 模型部署 9% → 评估 7% = 生产监控 7% → LLM 架构 6%（最低）。考试：重点复习前三（合计 44%）。

---

## 卡片 2

**Q：考试题型和时间分配？**

A：约 55 道选择题，120 分钟，无动手实验。每题约 2.2 分钟；超过 3 分钟标记跳过。考试：全部是选择题，节奏紧张。

---

## 卡片 3

**Q：四个高频考试陷阱？**

A：1. GPU 利用率 ≠ LLM 扩容信号（队列深度+延迟SLO才是）；2. 分词器不兼容时需蓝绿部署；3. RAG 非万能（单文档大模型足够时 RAG 反增成本）；4. LoRA 通常只作用于 attention 层。

---

## 卡片 4

**Q：推理延迟高但 GPU 利用率低，瓶颈在哪？**

A：CPU post-processing 或 IO 瓶颈，而非 GPU 不足。排查方向：CPU 利用率、网络带宽、存储 IOPS。考试：GPU 利用率低 + 延迟高 = 非 GPU 瓶颈。

---



## 易混考点


### NCA-GENL 备考：LLM 基础 7 个高频易混考点


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/notes/01-exam-focus-guide.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/notes/01-exam-focus-guide.md) · 语言：中文原文



# NCA-GENL 备考：LLM 基础 7 个高频易混考点

> ⚠️ 本文基于官方考纲整理，仅覆盖高频易混考点，**不能替代完整考试大纲**。

## 考点 1：过拟合 vs 欠拟合 —— 损失值对比

| 状态 | 训练损失 | 验证损失 | 诊断 | 解决方案 |
|---|---|---|---|---|
| **过拟合** | 很低（0.02） | 高（0.18） | 模型记忆训练数据 | L1/L2 正则化、Dropout、更多数据 |
| **欠拟合** | 高（0.65） | 高（0.68） | 模型太简单 | 增加容量、加特征、训练更久 |
| **良好拟合** | 低（0.12） | 同样低（0.15） | 平衡 | 无需行动 |

**考试情境**：训练准确率 95% + 验证 72% = 过拟合（差距 23 个百分点）。

## 考点 2：Dropout 在推理时关闭

- **训练时**：随机停用神经元（rate = 0.2~0.5）
- **推理时**：Dropout **关闭**（rate = 0），所有神经元激活

**考试必考**：推理时不用 Dropout，这是为了防止预测的随机性。

## 考点 3：损失函数配对 —— 不能乱用

| 场景 | 正确损失 | 错误搭配 |
|---|---|---|
| 分类（情感分析、图像分类） | **交叉熵** | ❌ MSE |
| 回归（房价预测、温度） | **MSE 或 MAE** | ❌ 交叉熵 |

**考试陷阱**：题目问"分类用什么损失"，正确答案是交叉熵，不是 MSE。

## 考点 4：激活函数速查

| 函数 | 适用范围 | 用途 |
|---|---|---|
| **ReLU** | [0, +∞) | 隐藏层默认（快速、减少梯度消失） |
| **Sigmoid** | (0, 1) | 二分类输出（概率解释） |
| **Softmax** | (0,1)，和为 1 | 多分类输出（概率分布） |
| **GELU** | 平滑变体 | Transformer（BERT/GPT 默认） |

**考试规则**：隐藏层用 ReLU，二分类输出用 Sigmoid，多分类输出用 Softmax。

## 考点 5：嵌入（Embedding）的余弦相似度

- 嵌入间**余弦相似度 > 0.85** = 语义高度相似
- 支持迁移学习：预训练嵌入 → 下游任务
- 「king」-「man」+「woman」≈「queen」

**考试要点**：高余弦相似度 = 词在相似上下文中使用。

## 考点 6：学习率症状

| 学习率 | 现象 | 典型范围 |
|---|---|---|
| 过高 | 损失爆炸、震荡、发散 | — |
| 适中 | 稳定收敛 | 0.0001 ~ 0.01 |
| 过低 | 训练极慢、陷入局部最优 | — |

**考试要点**：Adam 优化器最常用（自适应学习率）。

## 考点 7：数据集划分黄金法则

| 集合 | 用途 | 大小 |
|---|---|---|
| **训练集** | 学习权重 | 60-80% |
| **验证集** | 调优超参数、检测过拟合 | 10-20% |
| **测试集** | **仅最终评估**，训练期间绝不触碰 | 10-20% |

**考试规则**：测试集提前使用 → 结果作废。

---

## 速记总表

| 一句话考点 | 答案 |
|---|---|
| 训练 95%、验证 72%？ | **过拟合** |
| 推理时 Dropout？ | **关闭** |
| 分类用什么损失？ | **交叉熵** |
| 多分类输出层激活？ | **Softmax** |
| 余弦相似度 > 0.85？ | **语义高度相似** |
| Adam 是什么？ | **自适应学习率优化器** |
| 测试集能提前用吗？ | **绝对不能** |

---

> 📌 **完整速查表 + 知识卡片 + 模拟卷**：关注公众号「JunzeXuInfra」回复「NCA-GENL」领取 PDF 全家桶。

---


### NCP-GENL 备考：高级 LLM 机制 7 个高频易混考点


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/notes/01-exam-focus-guide.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/notes/01-exam-focus-guide.md) · 语言：中文原文



# NCP-GENL 备考：高级 LLM 机制 7 个高频易混考点

> ⚠️ 本文基于官方考纲整理，仅覆盖高频易混考点，**不能替代完整考试大纲**。

## 考点 1：KV 缓存三变体

| 变体 | KV 头数 | KV 缓存大小 | 代表使用者 |
|---|---|---|---|
| **MHA** | = 查询头数 | 最大 | 原始 Transformer |
| **GQA** | 分组（子集） | 中等（MHA 的 1/4–1/8） | Llama 2/3、Mistral |
| **MQA** | 1（全体共享） | 最小 | PaLM、Falcon |

**KV 缓存公式**：缓存大小 ∝ num_layers × num_kv_heads × head_dim × 2(K 和 V) × bytes/param

**考试要点**：GQA 的 KV 头数 = num_query_heads / group_size

## 考点 2：FlashAttention —— 精确算法，非近似

| 特性 | 说明 |
|---|---|
| **精确性** | 精确算法，**不是近似** |
| 切块技术 | Q/K/V 切成 SRAM 大小的块 + 在线 softmax |
| 内存 | **O(N)** vs 标准 O(N²) |
| FLOPs | 仍为 O(N²)（未减少计算） |
| 解决什么 | **内存带宽瓶颈**，非算力瓶颈 |

**考试陷阱**：FlashAttention 是精确的，不要误以为是低精度/近似算法。

## 考点 3：混合专家（MoE）稀疏激活

| 概念 | 事实 |
|---|---|
| **路由** | 门控网络给专家打分；每个 token 激活 top-k（通常 1 或 2） |
| **稀疏激活** | 总参数随专家数扩展；**活跃 FLOPs 随 k 扩展，而非随专家总数** |
| 示例 | Mixtral 8x7B：8 专家 top-2，约 13B 激活 / 约 47B 总参数 |

**考试要点**：MoE 的"稀疏"指的是**激活**稀疏，不是注意力稀疏。机制完全不同！

## 考点 4：位置编码外推性

| 类型 | 外推性 | 代表模型 |
|---|---|---|
| 绝对（正弦/可学习） | ❌ 差 | 原始 Transformer、GPT-2 |
| RoPE | ⚠️ 需缩放（NTK/YaRN） | Llama、GPT-NeoX |
| ALiBi | ✅ 原生 | BLOOM、MPT |

**考试陷阱**：RoPE 单独使用**不能**良好外推，需要额外缩放。ALiBi 是唯一原生支持的。

## 考点 5：编码器-解码器 vs 仅解码器

| 方面 | 编码器-解码器 | 仅解码器 |
|---|---|---|
| 注意力 | 双向编码器 + 因果解码器 + 交叉注意力 | 仅因果自注意力 |
| 最适合 | 翻译、摘要（seq2seq） | 开放式生成、通用 LLM |
| 示例 | T5、BART | GPT、Llama、Mistral |

## 考点 6：GELU 是 Transformer 默认激活

| 函数 | 常见用途 |
|---|---|
| **GELU** | Transformer FFN 层（BERT、GPT 默认） |
| ReLU | 经典深度网络 |
| Softmax | 注意力分数、输出分布 |

**考试要点**：不要用 ReLU 回答 Transformer 激活函数——现代 Transformer 默认 GELU。

## 考点 7：架构决策矩阵

```
需要翻译/摘要？ → 编码器-解码器
需要开放式生成？ → 仅解码器
需要分类/嵌入？ → 仅编码器
需要省 KV 缓存？ → GQA 或 MQA
需要外推长度？ → ALiBi（或 RoPE + 缩放）
```

---

## 速记总表

| 一句话考点 | 答案 |
|---|---|
| FlashAttention 近似吗？ | **不是**，精确算法 |
| FlashAttention 解决什么？ | 内存**带宽**瓶颈 |
| MoE 稀疏什么？ | 激活稀疏（非注意力稀疏） |
| GQA KV 头怎么算？ | query_heads / group_size |
| RoPE 能外推吗？ | 需缩放，单独不行 |
| ALiBi 能外推吗？ | **原生可以** |
| Transformer FFN 用什么激活？ | **GELU** |

---

> 📌 **完整速查表 + 知识卡片 + 模拟卷**：关注公众号「JunzeXuInfra」回复「NCP-GENL」领取 PDF 全家桶。

---



## 笔记


### NCA-GENL 官方考试大纲


> 来源：`cterpening/certification-study-library` · `data/objective-snapshots/nca-genl-official-objectives.txt` · [原文链接](https://github.com/cterpening/certification-study-library/blob/main/data/objective-snapshots/nca-genl-official-objectives.txt) · 语言：英文原文 · 中译版



NVIDIA-Certified Associate
NVIDIA 生成式 AI 大语言模型认证考试
(NCA-GENL)
NCA-GENL 考试备考主题与推荐阅读
以下信息旨在帮助你准备本场考试。
下面列出了所涵盖的主题、每个主题的权重、推荐培训以及补充阅读材料。
核心机器学习与 AI 知识
数据分析
实验
软件开发
可信 AI
核心机器学习与 AI 知识
理解相关算法、约定与技术，使计算机能够从数据中学习，并基于数据进行预测或决策。
考试主题：
在高级团队成员的指导下，协助部署并评估模型的可扩展性、性能与可靠性。
了解使用数据挖掘、数据可视化及类似技术从大型数据集中提取洞察的过程。
构建 LLM 用例，例如检索增强生成 (RAG)、聊天机器人与摘要器。
为 RAG 精选并嵌入内容数据集。
熟悉机器学习的基本原理（例如特征工程、模型比较、交叉验证）。
熟悉 Python 自然语言处理包（spaCy、NumPy、向量数据库等）的能力。
阅读研究论文（文章、会议论文等），以识别新兴的 LLM 趋势与技术。
选择并使用模型来创建文本嵌入。
使用提示工程原则编写提示词，以达到期望结果。
使用 Python 包（spaCy、NumPy、Keras 等）实现特定的传统机器学习分析。
30%
考试权重
推荐培训与建议阅读：
推荐培训
《深度学习基础》— 开源课程材料
《使用大语言模型 (LLM) 进行快速应用开发》
建议阅读
《提示工程指南》
《大语言模型导论：提示工程与 P-Tuning》
《Attention Is All You Need》
《面向 NVIDIA 架构 PC 的端到端 AI：使用 ONNX 转换 AI 模型》
《生成式 AI —— 它是什么，如何工作？》
《什么是基础模型？》— NVIDIA 博客
《LoRA：大语言模型的低秩自适应》
《生成式 AI 研究聚焦：深入解析基于扩散的模型》
scikit-learn 用户指南
《什么是 Milvus》
《什么是检索增强生成（又称 RAG）？》— NVIDIA 博客
Hugging Face LLM 课程 —— 数据集
数据分析
检查、清洗、转换数据并对其进行建模，以发现有用的信息、支撑结论并辅助决策。
考试主题：
了解使用数据挖掘、数据可视化及类似技术从大型数据集中提取洞察的过程。
使用统计性能指标（例如损失函数或被解释方差比例）比较模型。
在高级团队成员的指导下开展数据分析。
使用专业软件创建图表、图形或其他可视化内容，以呈现数据分析的结果。
识别关系与趋势，或任何可能影响研究结果的因素。
14%
考试权重
推荐培训与建议阅读：
推荐培训
《深度学习基础》— 开源课程材料
《使用大语言模型 (LLM) 进行快速应用开发》
建议阅读
cuML 文档
《开始使用 GPU 加速数据科学》
Matplotlib 教程
《Python 数据科学手册》（免费）
RAPIDS cuDF 用户指南
scikit-learn —— 指标与评分
实验
执行、评估并解读实验，包括 AI 模型评估，以及在标注或基于人类反馈的强化学习 (RLHF) 中使用人类被试。
考试主题：
在高级团队成员的指导下，协助进行模型训练与训练优化。
协助为预训练、微调和 RLHF 准备（例如抓取、分词）大型数据集。
协助设计并执行 LLM 应用的硬件或软件测试。
协助评估当前或新兴技术，需考虑成本、可移植性、兼容性或易用性等因素。
了解并/或参与来自人类被试的数据收集（例如 RLHF）。
评估并改进现有模型 / 基准测试。
执行实验以评估模型与流水线。
22%
考试权重
推荐培训与建议阅读：
推荐培训
《深度学习基础》— 开源课程材料
《使用大语言模型 (LLM) 进行快速应用开发》
建议阅读
Hugging Face LLM 课程 —— 微调 LLM
《掌握 LLM 技术：推理优化》
《语音与语言处理》— Jurafsky & Martin（免费）
Hugging Face LLM 课程 —— 分词器
Weights & Biases 快速入门
《基于人类反馈的强化学习 (RLHF) 图解》
LM Evaluation Harness
软件开发
创建、维护并测试软件。
考试主题：
在高级团队成员的指导下，协助部署并评估模型的可扩展性、性能与可靠性。
构建 LLM 用例，例如 RAG、聊天机器人与摘要器。
熟悉 Python 自然语言处理包（spaCy、NumPy、向量数据库等）的能力。
确定满足用户需求所需的系统数据、硬件或软件组件。
监控数据收集、实验及其他软件流程的运行状况。
使用 Python 包（spaCy、NumPy、Keras 等）实现特定的传统机器学习分析。
在高级团队成员的指导下编写软件组件或脚本。
24%
考试权重
推荐培训与建议阅读：
推荐培训
《深度学习基础》— 开源课程材料
《使用大语言模型 (LLM) 进行快速应用开发》
建议阅读
NVIDIA 生成式 AI 示例
TensorRT —— 入门
最佳实践 —— NVIDIA NeMo
《掌握 LLM 技术：定制化》
《大数据？用数据集来拯救！》— HuggingFace NLP 课程
《BERT：深度双向 Transformer 的预训练》
NVIDIA Triton Inference Server 快速入门
spaCy 文档
scikit-learn 用户指南
可信 AI
创建并评估合乎伦理、注重节能且可靠的人工智能系统，使其能够解释并整合各种形式的数据，确保其设计和应用方式是透明、公平且可验证的。
考试主题：
描述可信 AI 的伦理原则。
描述数据隐私与数据知情同意重要性之间的平衡。
描述如何使用 NVIDIA 及其他技术来提升 AI 的可信度。
描述如何将 AI 系统中的偏差降至最低。
10%
考试权重
推荐培训与建议阅读：
推荐培训
《使用大语言模型 (LLM) 进行快速应用开发》
建议阅读
《为更美好的世界打造可信 AI》— NVIDIA
《什么是可信 AI？》— NVIDIA 博客
NIST 人工智能风险管理框架
Google 负责任 AI 实践

---


### NCP-GENL 推荐培训课程


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/dli-courses.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/dli-courses.md) · 语言：中文原文



# NCP-GENL 推荐培训课程

> 来源：[英伟达官方认证页](https://www.nvidia.cn/training/certification/generative-ai-llm-professional/) · NVIDIA DLI 培训。

| 课程编号 | 课程名称 | 形式 | 时长 | 语言 | 参考费用 |
|---|---|---|---|---|---|
| — | 生成式 AI / LLM 专业级课程 | 讲师指导培训班 | 8 学时 | 中文 | 见官网 |

## 报名与购买

- [购买考试券（NVIDIA 官方）](https://www.nvidia.cn/training/certification/#book-cn-exam)
- [NVIDIA DLI 中文官网](https://www.nvidia.cn/training/)

---



## 学习指南


### NCA-GENL 推荐培训课程


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/dli-courses.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/dli-courses.md) · 语言：中文原文



# NCA-GENL 推荐培训课程

> 来源：[英伟达官方认证页](https://www.nvidia.cn/training/certification/generative-ai-llm-associate/) · NVIDIA DLI 培训。以下课程来自 DLI 中文官网（费用/时长实时更新）。

## 推荐培训

| 课程名称 | 形式 | 时长 | 语言 | 参考费用 |
|---|---|---|---|---|
| 您可任选一门：深度学习新手入门 | 在线自主培训 | 8 学时 | 中文 | 90 美元 |
| 深度学习基础——理论与实践入门 | 讲师指导的培训班 | 8 学时 | 中文 | 3500 元 |
| 加速端到端的数据科学工作流 | 在线自主培训 | 6 学时 | 中文 | 90 美元 |
| 您可任选一门：基于 Transformer 的自然语言处理入门 | 在线自主培训 | 6 学时 | 中文 | 30 美元 |
| 构建基于 Transformer 的自然语言处理应用 | 讲师指导的培训班 | 8 学时 | 中文 | 3500 元 |
| 您可任选一门：开发基于提示工程的大语言模型 (LLM) 应用 | 在线自主培训 | 8 学时 | 中文 | 90 美元 |
| 利用提示工程构建大语言模型 (LLM) 应用 | 讲师指导的培训班 | 8 学时 | 中文 | 3500 元 |
| 您可任选一门：快速搭建大语言模型 (LLM) 应用 | 在线自主培训 | 8 学时 | 中文 | 90 美元 |
| 构建基于大语言模型 (LLM) 的应用 | 讲师指导的培训班 | 8 学时 | 中文 | 3500 元 |

## 报名与购买

- [购买考试券（NVIDIA 官方）](https://www.nvidia.cn/training/certification/#book-cn-exam)
- [NVIDIA DLI 中文官网](https://www.nvidia.cn/training/)
- [点此查看课程表](https://www.nvidia.cn/training/)
- [点此购买](https://learn.nvidia.com/)

> 注：NVIDIA 培训由 DLI 团队运营，具体费用、课时请以其官网实时信息为准。

---


### NCA-GENL 参考资料与官方直链


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/references.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/references.md) · 语言：中文原文



# NCA-GENL 参考资料与官方直链

## 官方文件

| 资源 | 链接 |
|---|---|
| 考试报名页 | [NVIDIA 官方报名](https://www.nvidia.cn/training/certification/#book-cn-exam) |
| Study Guide（中文版，Web PDF） | [直链](https://images.nvidia.cn/aem-dam/zh_cn/Solutions/training/certification/nvt-certification-exam-study-guide-genl-web-zhcn.pdf) |
| NVIDIA DLI 中文官网 | [链接](https://www.nvidia.cn/training/) |

## 延伸参考

- [NVIDIA NeMo](https://developer.nvidia.com/nemo)
- [NVIDIA Triton Inference Server](https://developer.nvidia.com/triton-inference-server)
- [NVIDIA TensorRT-LLM](https://developer.nvidia.com/tensorrt)
- [Hugging Face](https://huggingface.co/)
- [LangChain](https://www.langchain.com/)

> ⚠️ 版权归 NVIDIA 所有；本仓只引用直链，不收录 PDF 副本。

---


### NCP-GENL 参考资料与官方直链


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/references.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/references.md) · 语言：中文原文



# NCP-GENL 参考资料与官方直链

| 资源 | 链接 |
|---|---|
| 考试报名页 | [NVIDIA 官方报名](https://www.nvidia.cn/training/certification/#book-cn-exam) |
| 官方认证页 | [Generative AI LLMs Professional](https://www.nvidia.cn/training/certification/generative-ai-llm-professional/) |
| NVIDIA NeMo | [链接](https://developer.nvidia.com/nemo) |
| NVIDIA Triton | [链接](https://developer.nvidia.com/triton-inference-server) |
| NVIDIA NIM | [链接](https://developer.nvidia.com/nim) |

> ⚠️ 版权归 NVIDIA 所有；本仓只引用直链，不收录 PDF 副本。

---


### NCA-GENL · DLI 免费课程清单


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `nca-genl/dli-courses.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/nca-genl/dli-courses.md) · 语言：中文原文



# NCA-GENL · DLI 免费课程清单

> NVIDIA Deep Learning Institute (DLI)，登录 https://learn.nvidia.com 后免费学习。

---

## 本门核心课程（5 门）

| # | 课程名称 | course_id | 类型 | 链接 |
|---|---|---|---|---|
| 1 | 深度学习新手入门 | `course-v1:DLI+S-FX-01+V1-ZH` | 自主学习 | [打开课程](https://learn.nvidia.com/courses/course-detail?course_id=course-v1:DLI+S-FX-01+V1-ZH) |
| 2 | 加速端到端的数据科学工作流 | `course-v1:DLI+S-DS-01+V2-ZH` | 自主学习 | [打开课程](https://learn.nvidia.com/courses/course-detail?course_id=course-v1:DLI+S-DS-01+V2-ZH) |
| 3 | 基于 Transformer 的自然语言处理入门 | `course-v1:DLI+S-FX-08+V1-ZH` | 自主学习 | [打开课程](https://learn.nvidia.com/courses/course-detail?course_id=course-v1:DLI+S-FX-08+V1-ZH) |
| 4 | 开发基于提示工程的大语言模型（LLM）应用 | `course-v1:DLI+S-FX-12+V2-ZH` | 自主学习 | [打开课程](https://learn.nvidia.com/courses/course-detail?course_id=course-v1:DLI+S-FX-12+V2-ZH) |
| 5 | 快速搭建大语言模型（LLM）应用 | `course-v1:DLI+S-FX-26+V1-ZH` | 自主学习 | [打开课程](https://learn.nvidia.com/courses/course-detail?course_id=course-v1:DLI+S-FX-26+V1-ZH) |

---

## 课程与考点对应关系

| 课程模块 | 对应考试模块 | 权重 |
|---|---|---|
| S-FX-01 深度学习基础 + 神经网络 | 核心机器学习和 AI 知识 | 30% |
| S-FX-08 Transformer / NLP 入门 | 核心机器学习和 AI 知识（注意力 / Transformer） | 30% |
| S-FX-12 LLM 提示工程 + S-FX-26 LLM 应用搭建 | 软件开发（RAG / API / Triton / NeMo） | 24% |
| S-DS-01 数据科学工作流 | 实验（数据集 / 评估指标） | 22% |
| S-FX-01 可信 AI 模块 | 可信 AI（偏见 / 隐私 / 伦理） | 10% |

---

## 其他推荐官方免费资源

- **NeMo 官方文档**：https://docs.nvidia.com/nemo/
- **Triton 推理服务器文档**：https://docs.nvidia.com/deeplearning/triton-inference-server/
- **TensorRT 文档**：https://developer.nvidia.com/tensorrt
- **Hugging Face 文档**（答题时的延伸参考）：https://huggingface.co/docs

---


### NCA-GENL 考试介绍与培训指引（来源：英伟达官方科目解读）


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `nca-genl/overview.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/nca-genl/overview.md) · 语言：中文原文



# NCA-GENL 考试介绍与培训指引（来源：英伟达官方科目解读）

> 原文出处：NVIDIA 官方《科目解读》第 1 页 · 2026 年整理

## 考试定位

NVIDIA-Certified Associate: Generative AI LLMs (NCA-GENL) 认证，用于验证结合 NVIDIA 解决方案的**生成式 AI 和大语言模型 (LLM) 开发、集成和维护 AI 应用程序**的基本技能。

## 考试参数

| 项目 | 数值 |
|---|---|
| 考试时长 | 60 分钟 |
| 考试费用 | 960 元 |
| 题目数量 | 50–60 道选择题 |

## 面向人群

本考试不要求有工作经验，适合以下角色参加：

- 软件开发者
- 软件工程师
- 解决方案架构师
- 机器学习工程师
- 数据科学家
- AI 策略师
- 生成式 AI 专家

## 官方推荐培训与课程

| 序号 | 课程名称 | 类型 |
|---|---|---|
| 1 | 深度学习基础——理论与实践入门 | DLI 自主 |
| 2 | 加速数据科学基础 | DLI 自主 |
| 3 | 构建基于 Transformer 的自然语言处理应用 | DLI 自主 |
| 4 | 利用提示工程构建大语言模型（LLM）应用 | DLI 自主 |
| 5 | 构建基于大语言模型 (LLM) 的应用 | DLI 自主 |
| 6 | 考前学习指南 | NVIDIA 官方 |

> ⚠️ 推荐课程详见 [dli-courses.md](dli-courses.md) 的精确匹配。考前学习指南由 NVIDIA 官方提供（随报名邮件发送或在学员账户内下载）。

## 考点权重（详见 [README.md](README.md)）

本考试覆盖五大模块，核心 ML 知识占 30%、软件开发 24%、实验 22%、数据分析 14%、可信 AI 10%。完整拆解与逐条覆盖度对照见根目录 README。

---


### NCA-GENL 参考资料与官方直链


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `nca-genl/references.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/nca-genl/references.md) · 语言：中文原文



# NCA-GENL 参考资料与官方直链

> 本页汇总英伟达官方考试资源的直接链接。

## 官方 Study Guide（直链，不入仓）

| 资源 | 链接 |
|---|---|
| Study Guide（中文版，Web PDF） | [nvt-certification-exam-study-guide-genl-web-zhcn.pdf](https://images.nvidia.cn/aem-dam/zh_cn/Solutions/training/certification/nvt-certification-exam-study-guide-genl-web-zhcn.pdf) |

---

## 推荐阅读材料

### 核心 ML 知识（30%）

| 材料 | 链接 |
|---|---|
| Attention Is All You Need | [arXiv:1706.03762](https://arxiv.org/abs/1706.03762) |
| End-to-End AI for NVIDIA-Based PCs — ONNX | [NVIDIA Blog](https://blogs.nvidia.com/) |
| Generative AI — What Is It? | [NVIDIA](https://www.nvidia.com/) |
| LoRA: Low-Rank Adaptation | [arXiv:2106.09685](https://arxiv.org/abs/2106.09685) |
| Demystifying Diffusion Models | [NVIDIA Blog](https://blogs.nvidia.com/) |
| What Are Foundation Models? | [NVIDIA Blog](https://blogs.nvidia.com/) |

### 数据分析（14%）

| 材料 | 链接 |
|---|---|
| RAPIDS | [rapids.ai](https://rapids.ai/) |
| GPU Accelerated Data Science With RAPIDS | [NVIDIA](https://www.nvidia.com/) |

### 实验（22%）

| 材料 | 链接 |
|---|---|
| Hallucinations in LLMs | [arXiv](https://arxiv.org/) |
| Evaluating RAG Applications | [arXiv](https://arxiv.org/) |
| Cross-Validation in ML | [scikit-learn](https://scikit-learn.org/) |

### 软件开发（24%）

| 材料 | 链接 |
|---|---|
| TensorRT | [NVIDIA Developer](https://developer.nvidia.com/) |
| NVIDIA NeMo Best Practices | [NVIDIA Developer](https://developer.nvidia.com/) |
| Mastering LLM Customization | [NVIDIA Blog](https://blogs.nvidia.com/) |
| NCCL: Multi-GPU Communications | [NVIDIA Developer](https://developer.nvidia.com/) |
| BERT: Pretraining of Bidirectional Transformers | [arXiv:1810.04805](https://arxiv.org/abs/1810.04805) |

### 可信 AI（10%）

| 材料 | 链接 |
|---|---|
| Trustworthy AI for A Better World | [NVIDIA](https://www.nvidia.com/) |
| What Is Trustworthy AI? | [NVIDIA Blog](https://blogs.nvidia.com/) |
| What Is RAG? | [NVIDIA Blog](https://blogs.nvidia.com/) |

---


### NCP-GENL 考试介绍（来源：英伟达官方科目解读 P12）


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `ncp-genl/overview.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/ncp-genl/overview.md) · 语言：中文原文



# NCP-GENL 考试介绍（来源：英伟达官方科目解读 P12）

> 原文出处：NVIDIA 官方《科目解读》第 12 页 · 2026 年整理

## 考试定位

NVIDIA-Certified Professional: Generative AI LLMs (NCP-GENL) 认证，用于验证使用先进的分布式训练技术和优化策略，设计、训练和微调前沿的大语言模型 (LLM)，交付高性能的 AI 解决方案的中级技能。

## 考试参数

| 项目 | 数值 |
|---|---|
| 考试时长 | 120 分钟 |
| 考试费用 | 1580 元 |
| 题目数量 | 60–70 道选择题 |

## 面向人群

- 软件开发者
- 软件工程师
- 解决方案架构师
- 机器学习工程师
- 数据科学家
- AI 策略师
- 生成式 AI 专家

## 推荐培训与课程

| 序号 | 课程名称 |
|---|---|
| 1 | 构建大语言模型 RAG 智能体 |
| 2 | 为大语言模型添加新知识 |
| 3 | 模型并行 —— 构建和部署大型神经网络 |
| 4 | 在生产环境大规模部署 RAG 工作流 |
| 5 | 使用 Nsight 分析工具优化 CUDA 机器学习代码 |
| 6 | 考前学习指南 » |

---



## 实操


### 实验：ML 与神经网络基础


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/labs/chapter-01.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/labs/chapter-01.md) · 语言：中文原文



# 实验：ML 与神经网络基础

:::note 预计用时
20 分钟
:::

## 实验目标

- 能诊断过拟合和欠拟合
- 掌握 L1/L2 正则化和 Dropout 的实现
- 理解不同激活函数的效果

## 练习 1：过拟合诊断

```python
import torch
import torch.nn as nn

# 训练损失很低但验证损失很高 → 过拟合
train_loss = 0.02
val_loss = 0.18

if train_loss < 0.05 and val_loss > 0.15:
    print("诊断：过拟合")
    print("解决方案：L2 正则化、Dropout、增加训练数据")
```

## 练习 2：Dropout 实现

```python
model = nn.Sequential(
    nn.Linear(768, 256),
    nn.ReLU(),
    nn.Dropout(0.3),  # 训练时 30% 神经元停用
    nn.Linear(256, 10)
)

model.eval()  # 推理时 Dropout 自动关闭
```

:::tip
`model.eval()` 关闭 Dropout 和 BatchNorm 的训练行为。
:::

## 练习 3：激活函数对比

| 激活函数 | 用途 | 特点 |
|----------|------|------|
| ReLU | 隐藏层 | 减少梯度消失 |
| Sigmoid | 二分类输出 | 输出概率 |
| Softmax | 多分类输出 | 概率分布 |

## 关键要点

:::info 本章记忆锚点
过拟合：训练损失很低但验证损失高。推理时 Dropout 关闭。分类用交叉熵，回归用 MSE。
:::

---


### 实验：Transformer 架构


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/labs/chapter-02.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/labs/chapter-02.md) · 语言：中文原文



# 实验：Transformer 架构

:::note 预计用时
18 分钟
:::

## 实验目标

- 理解 QKV 矩阵的计算
- 掌握多头注意力的维度计算
- 能区分三种架构模式

## 练习 1：注意力计算

```python
import torch
import torch.nn.functional as F

d_k = 64
Q = torch.randn(1, 10, d_k)  # batch, seq_len, d_k
K = torch.randn(1, 10, d_k)
V = torch.randn(1, 10, d_k)

# 注意力 = softmax(QK^T / sqrt(d_k)) × V
scores = torch.matmul(Q, K.transpose(-2, -1)) / (d_k ** 0.5)
attention = F.softmax(scores, dim=-1)
output = torch.matmul(attention, V)
```

:::caution
不除以 sqrt(d_k) → 点积过大 → softmax 饱和 → 梯度消失。
:::

## 练习 2：多头注意力维度

```python
embedding_dim = 768
num_heads = 12
head_dim = embedding_dim // num_heads  # 64
print(f"每个头 {head_dim} 维 × {num_heads} 头 = {embedding_dim}")
```

## 练习 3：架构模式匹配

| 任务 | 正确架构 |
|------|----------|
| 文本分类 | Encoder-only（BERT） |
| 文本生成 | Decoder-only（GPT） |
| 翻译 | Encoder-Decoder（T5） |

## 关键要点

:::info 本章记忆锚点
注意力必须缩放。Encoder-only 做分类，Decoder-only 做生成，Encoder-Decoder 做翻译/摘要。
:::

---


### 实验：提示工程


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/labs/chapter-03.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/labs/chapter-03.md) · 语言：中文原文



# 实验：提示工程

:::note 预计用时
15 分钟
:::

## 实验目标

- 掌握不同提示策略的使用场景
- 理解温度参数对输出的影响
- 能设计有效的提示

## 练习 1：Few-shot 提示

```python
prompt = """将以下评论分类为积极/消极。

评论：这家餐厅太棒了！ → 积极
评论：服务很糟糕。 → 消极
评论：食物还可以，但等待时间太长。 →"""
```

## 练习 2：思维链提示

```python
cot_prompt = "一个水池有 3 个进水管。第一个 6 小时注满，第二个 8 小时注满，第三个 12 小时注满。如果三个管道同时打开，几小时注满？ Let's think step by step。"
```

:::tip
"Let's think step by step" 提升推理准确率 20-40%。
:::

## 练习 3：温度对比

```python
# Temperature = 0：确定性输出
# Temperature = 0.3-0.4：事实问答
# Temperature = 0.7-0.9：创意写作
# Temperature = 1.0+：高度随机（仅实验）
```

## 关键要点

:::info 本章记忆锚点
Few-shot 用 1-5 个示例。CoT 用 "step by step"。温度越高越创意，温度越低越确定。
:::

---


### 实验：对齐与安全


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/labs/chapter-04.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/labs/chapter-04.md) · 语言：中文原文



# 实验：对齐与安全

:::note 预计用时
15 分钟
:::

## 实验目标

- 掌握 RLHF 的三阶段流程
- 能识别和缓解幻觉
- 理解 RAG 的架构优势

## 练习 1：RLHF 流程排序

```python
# 正确的 RLHF 顺序：
stages = [
    "1. SFT：在指令示例上微调基础模型",
    "2. 奖励模型：在人类偏好比较上训练",
    "3. PPO：借助奖励模型反馈优化"
]
# 考试陷阱：奖励模型必须在 RL 阶段之前训练！
```

## 练习 2：幻觉检测

```python
response = "莎士比亚于 1605 年写了《哈姆雷特》"
# 事实核查：《哈姆雷特》约 1599-1601 写成
# → 幻觉！模型生成了看似合理但错误的信息
```

## 练习 3：RAG 缓解幻觉

```python
# RAG 接地示例
query = "什么是 CUDA？"
retrieved_docs = ["CUDA 是 NVIDIA 的并行计算平台..."]
prompt = f"根据以下文档回答：{retrieved_docs}\n问题：{query}"
```

:::tip
RAG 是最有效的幻觉缓解技术 — 架构级约束。
:::

## 关键要点

:::info 本章记忆锚点
RLHF 顺序不可颠倒。Temperature 0.0 不能防幻觉。RAG 是最佳幻觉缓解。
:::

---


### 实验：数据预处理


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/labs/chapter-05.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/labs/chapter-05.md) · 语言：中文原文



# 实验：数据预处理

:::note 预计用时
15 分钟
:::

## 实验目标

- 掌握 NFKC Unicode 归一化
- 理解 BPE 分词的优势
- 能正确实现填充和注意力掩码

## 练习 1：Unicode 归一化

```python
import unicodedata

text = "ＡＢＣ１２３"  # 全角字符
normalized = unicodedata.normalize('NFKC', text)
print(normalized)  # "ABC123" — 转为半角
```

:::note
ML 用 NFKC 减少词汇量，NFC 用于正式文档。
:::

## 练习 2：分词对比

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
tokens = tokenizer.encode("Hello world")
# BPE 分词无 [UNK] — 稀有词拆分为子词
```

## 练习 3：填充与注意力掩码

```python
# padding: 短序列填充到 batch 内最大长度
# attention_mask: 1 = 真实 token, 0 = padding
inputs = tokenizer(["Hello", "Hi world"], padding=True, return_tensors="pt")
# input_ids:      [[101, 7592, 102, 0], [101, 7632, 2088, 102]]
# attention_mask: [[1, 1, 1, 0], [1, 1, 1, 1]]
```

## 关键要点

:::info 本章记忆锚点
ML 用 NFKC。BPE 无 [UNK]。attention_mask 1 = 真实，0 = padding。
:::

---


### 实验：实验与评估


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/labs/chapter-06.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/labs/chapter-06.md) · 语言：中文原文



# 实验：实验与评估

:::note 预计用时
15 分钟
:::

## 实验目标

- 能根据任务选择正确的评估指标
- 掌握 BLEU 和 ROUGE 的区别
- 理解困惑度的含义

## 练习 1：指标选择

| 任务 | 正确指标 |
|------|----------|
| 机器翻译 | BLEU（精确率） |
| 文本摘要 | ROUGE（召回率） |
| 语言模型质量 | 困惑度（越低越好） |

## 练习 2：BLEU 计算

```python
from nltk.translate.bleu_score import sentence_bleu

reference = [['this', 'is', 'a', 'test']]
candidate = ['this', 'is', 'a', 'test']
score = sentence_bleu(reference, candidate)
print(f"BLEU: {score:.4f}")  # 完全匹配 = 1.0
```

## 练习 3：困惑度

```python
import math
cross_entropy_loss = 2.303
perplexity = math.exp(cross_entropy_loss)
print(f"困惑度: {perplexity:.2f}")  # 越低越好
```

:::tip
困惑度 = exp(交叉熵损失)。越低越好 — 模型对数据越不惊讶。
:::

## 关键要点

:::info 本章记忆锚点
翻译用 BLEU，摘要用 ROUGE，困惑度越低越好。不同任务需要不同指标。
:::

---


### 实验：LLM 集成与部署


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/labs/chapter-07.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/labs/chapter-07.md) · 语言：中文原文



# 实验：LLM 集成与部署

:::note 预计用时
20 分钟
:::

## 实验目标

- 能构建完整的 RAG 流水线
- 掌握 FAISS 向量搜索
- 理解微调 vs RAG vs 提示工程的取舍

## 练习 1：构建 RAG 流水线

```python
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# 嵌入模型
encoder = SentenceTransformer('all-MiniLM-L6-v2')

# 知识库
documents = ["CUDA 是 NVIDIA 的并行计算平台", "cuDF 是 GPU 加速的 DataFrame"]
doc_embeddings = encoder.encode(documents)

# 构建 FAISS 索引
index = faiss.IndexFlatL2(doc_embeddings.shape[1])
index.add(doc_embeddings.astype('float32'))

# 查询
query = "什么是 CUDA？"
query_embedding = encoder.encode([query]).astype('float32')
D, I = index.search(query_embedding, k=2)
print(f"最相似文档: {[documents[i] for i in I[0]]}")
```

## 练习 2：决策矩阵

| 场景 | 正确方案 |
|------|----------|
| 低于 500 示例 | 提示工程/RAG |
| 动态知识/新鲜度 | RAG |
| 永久改变风格 | 微调 |

## 关键要点

:::info 本章记忆锚点
RAG 架构：查询→嵌入→搜索→检索→注入→生成。FAISS 用于原型。低于 500 示例选提示工程/RAG。
:::

---


### 实验：NVIDIA 软件栈


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/labs/chapter-08.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/labs/chapter-08.md) · 语言：中文原文



# 实验：NVIDIA 软件栈

:::note 预计用时
12 分钟
:::

## 实验目标

- 掌握 NeMo 训练流水线
- 理解 NIM 部署流程
- 能区分各工具的适用场景

## 练习 1：工具匹配

| 场景 | 正确工具 |
|------|----------|
| 训练 LLM | NeMo |
| 部署 LLM 微服务 | NIM |
| 多模型部署 | Triton |
| 语音 ASR/TTS | Riva |
| 大规模 RAG | NeMo Retriever |

## 练习 2：NIM 部署

```bash
# NIM 预构建容器快速部署
docker run --gpus all -e NGC_API_KEY nvcr.io/nim/meta/llama3-8b-instruct:1.0.0
```

:::tip
NIM = 最少配置的快速生产部署。NeMo = 从头训练自定义模型。
:::

## 关键要点

:::info 本章记忆锚点
训练用 NeMo，部署用 NIM，多模型用 Triton。NeMo ≠ NIM（训练 vs 部署）。
:::

---


### 实验：真实世界 LLM 应用


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/labs/chapter-09.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/labs/chapter-09.md) · 语言：中文原文



# 实验：真实世界 LLM 应用

:::note 预计用时
12 分钟
:::

## 实验目标

- 能根据用例选择合适大小的模型
- 理解批处理策略的取舍
- 掌握延迟 vs 吞吐 vs 质量的权衡

## 练习 1：模型选择决策

| 用例 | 推荐模型大小 | 原因 |
|------|-------------|------|
| 文本分类/抽取 | 1.3B（蒸馏） | 低延迟、低成本 |
| 通用任务 | 7B | 平衡 |
| 复杂推理 | 13B+ | 高质量 |

## 练习 2：批处理策略

```python
# 动态批处理 — 在线请求组合
# 连续批处理 — 不定长请求最大 GPU 利用率
# 静态批处理 — 离线固定 batch
```

:::caution
模型越大 → 延迟更高、吞吐更低、质量更高。根据 SLA 权衡。
:::

## 关键要点

:::info 本章记忆锚点
分类用小模型（1.3B），通用用 7B，推理用 13B+。动态批处理提高在线吞吐。
:::

---


### 实验：全真模拟与策略


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/nca-genl/labs/chapter-10.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/nca-genl/labs/chapter-10.md) · 语言：中文原文



# 实验：全真模拟与策略

:::note 预计用时
60 分钟
:::

## 实验目标

- 体验完整的 60 分钟考试节奏
- 练习关键词驱动的答题策略
- 识别知识盲点

## 练习 1：关键词解码

匹配关键词和优先考虑因素：

| 关键词 | 优先考虑 |
|--------|----------|
| BEST | 综合最优 |
| FASTEST | 速度优先 |
| MOST memory-efficient | 内存优先 |
| MOST scalable | 可扩展性 |

## 练习 2：排除法练习

**以下哪种情况应该选择微调？**

A. 有 50 个标注示例，需要快速部署
B. 有 5000 个标注示例，需要永久改变模型行为
C. 需要动态知识更新
D. 预算有限

<details>
<summary>答案</summary>

**B** — 微调需要超过 1000 示例。A 选提示工程，C 选 RAG，D 选提示工程。

</details>

## 练习 3：术语配对

| 任务 | 正确工具/指标 |
|------|--------------|
| 训练自定义 LLM | NeMo |
| 翻译评估 | BLEU |
| 摘要评估 | ROUGE |
| 部署微服务 | NIM |

## 关键要点

:::info 本章记忆锚点
先读关键词，再排除错误工具-规模匹配。时间分配：90 秒标记阈值，最后 5 分钟处理标记题。相信你的准备！
:::

---


### 实验：注意力机制变体选型


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/labs/chapter-01.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/labs/chapter-01.md) · 语言：中文原文



# 实验：注意力机制变体选型

:::note 预计用时 20 分钟 :::

## 实验目标
- 选择正确的注意力变体（GQA/MQA/MHA）
- 理解 FlashAttention 的数学精确性
- 区分外推能力不同的位置编码

## 练习 1：注意力变体选择
| 场景 | 最佳选择 | 理由 |
|------|----------|------|
| 70B 实时聊天，内存受限 | GQA | KV 缓存缩减 4-8 倍，保质量 |
| 最高吞吐推理，可容忍质量损失 | MQA | 单 KV 头，缓存最小 |
| 小规模高质量编码器 | MHA | 全 KV 头 |

## 练习 2：KV 缓存计算
32 查询头 + 组大小 4 的 GQA → KV 头数 = 32/4 = 8 → 缓存为 MHA 的 1/4

## 练习 3：位置编码外推
| 编码方式 | 可外推？ |
|----------|----------|
| 可学习绝对嵌入 | 否 |
| ALiBi | 是 |
| RoPE + 高 theta | 是 |

:::info 记忆锚点
GQA=分组共享；FlashAttention=精确IO感知；ALiBi=最佳外推
:::

---


### 实验：分词与上下文扩展


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/labs/chapter-02.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/labs/chapter-02.md) · 语言：中文原文



# 实验：分词与上下文扩展

:::note 预计用时 15 分钟 :::

## 练习 1：Chinchilla 计算
70B 模型：每参数 20 token → 70B x 20 = 1400 亿 token 为计算最优点

## 练习 2：分词方法选择
| 语言类型 | 最佳分词 | 原因 |
|----------|----------|------|
| 英文（有空白符） | BPE / SentencePiece 均可 | 两者适用 |
| 中文/日文/韩文 | SentencePiece | 无需按空白符预切分 |

## 练习 3：RoPE 扩展
| 技术 | 需要微调？ | 原理 |
|------|-----------|------|
| NTK-aware 缩放 | 否 | 非均匀调频率 |
| 位置插值 (PI) | 是 | 插值位置索引 |
| theta = 500000 | 否 | 减慢旋转 |

:::info 记忆锚点
Chinchilla 20:1；CJK→SentencePiece；免训练→NTK-aware
:::

---


### 实验：高级提示与解码


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/labs/chapter-03.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/labs/chapter-03.md) · 语言：中文原文



# 实验：高级提示与解码

:::note 预计用时 20 分钟 :::

## 练习 1：受限解码场景
需要输出严格 JSON/枚举值 → 受限解码（token 级屏蔽无效输出）

## 练习 2：ReAct 序列
正确步骤：Thought → Action → Observation → 重复 → Final Answer

## 练习 3：自洽性配置
温度 > 0（如 0.7）+ 多次采样（5-10 次）+ 多数投票

## 练习 4：零样本 vs 少样本
零样本=仅指令无示例；少样本=多个输入/输出示例

:::info 记忆锚点
受限解码=格式保证；ReAct=交错推理+工具；自洽=温度>0+投票
:::

---


### 实验：适配策略决策


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/labs/chapter-04.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/labs/chapter-04.md) · 语言：中文原文



# 实验：适配策略决策

:::note 预计用时 20 分钟 :::

## 练习 1：策略选择
| 场景 | 最佳策略 | 原因 |
|------|----------|------|
| 每日更新内部文档 | RAG | 知识时效性与模型解耦 |
| 严格品牌口吻+低延迟 | 微调 | 行为模式固化进权重 |
| 20 条静态 FAQ | 直接放提示 | 无需基础设施 |
| 超出上下文的大语料 | RAG | 分块检索 |

## 练习 2：RAG 组件
分块器 → 嵌入模型 → 向量存储 → 检索器 → 重排序器 → 生成器

## 练习 3：分块过大后果
主题混杂 → 稀释相关性信号 → 检索精确度下降 + 可能超出上下文

:::info 记忆锚点
动态知识→RAG；风格固化→微调；小静态→直接提示
:::

---


### 实验：数据集整理


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/labs/chapter-05.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/labs/chapter-05.md) · 语言：中文原文



# 实验：数据集整理

:::note 预计用时 15 分钟 :::

## 练习 1：去重方法
| 场景 | 方法 | 原理 |
|------|------|------|
| 大规模近似去重(85%相似) | MinHash + LSH | 近似 Jaccard，同桶比较 |
| 精确去重 | SHA-256 哈希 | 字节级相同 |

## 练习 2：LSH band 数增加效果
band 更多 + 每 band 行数更少 → 召回率上升、精确率下降

## 练习 3：灾难性遗忘
微调数据混合中代码几乎为 0 → 预训练学到的编码能力退化

:::info 记忆锚点
MinHash+LSH=近似去重；格式统一=微调前提；分布失衡=灾难性遗忘
:::

---


### 实验：定制化策略


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/labs/chapter-06.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/labs/chapter-06.md) · 语言：中文原文



# 实验：定制化策略

:::note 预计用时 20 分钟 :::

## 练习 1：内存计算
QLoRA 70B：4-bit NF4 量化基座 ~35GB + LoRA 适配器 → 单张 80GB GPU 可运行

## 练习 2：DPO vs RLHF
| 维度 | DPO | RLHF |
|------|-----|------|
| 需要奖励模型 | 否 | 是 |
| 训练稳定性 | 高 | 较低 |
| 复杂度 | 简单 | 复杂 |

## 练习 3：组件分工
NeMo Curator=数据整理；NeMo Aligner=偏好对齐（DPO/PPO）

## 练习 4：领域自适应步骤
无标注法律文本 → 继续预训练（领域自适应）→ 指令微调 → DPO 对齐

:::info 记忆锚点
QLoRA=4-bit基座+LoRA；DPO=免奖励模型；Curator整理，Aligner对齐
:::

---


### 实验：分布式训练并行策略


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/labs/chapter-07.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/labs/chapter-07.md) · 语言：中文原文



# 实验：分布式训练并行策略

:::note 预计用时 20 分钟 :::

## 练习 1：选择策略
| 场景 | 首选 | 原因 |
|------|------|------|
| 单层过大装不下 | 张量并行 | 切权重矩阵 |
| 模型能放下要加速 | 数据并行 | 复制模型分数据 |
| 节点内 8 GPU | TP | NVLink 高带宽 |
| 长序列 64K+ | 序列并行 | 切激活序列维度 |

## 练习 2：张量并行限制
不能跨节点——需要节点内 NVLink 900GB/s 带宽

## 练习 3：组合方案
64 GPU 4 节点：TP(8, 节点内) + PP(跨节点) + DDP

:::info 记忆锚点
大单层→TP；能放下→DDP；节点内→TP；长序列→SP
:::

---


### 实验：推理加速量化


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/labs/chapter-08.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/labs/chapter-08.md) · 语言：中文原文



# 实验：推理加速量化

:::note 预计用时 15 分钟 :::

## 练习 1：量化方法选择
| 场景 | 最佳方法 | 原因 |
|------|----------|------|
| 内存受限 70B | AWQ INT4 | 接近 FP16 精度，内存 1/4 |
| H100 GPU | FP8 | 硬件原生，最高吞吐 |
| 精度敏感 | FP16/FP8 | 避免量化损失 |

## 练习 2：投机解码原理
小模型 draft 猜多个 token → 大模型并行验证 → 单步多 token → 2-3x 加速

:::info 记忆锚点
AWQ=激活感知保护；FP8=H100原生；投机=小猜大验
:::

---


### 实验：LLM 服务化选型


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/labs/chapter-09.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/labs/chapter-09.md) · 语言：中文原文



# 实验：LLM 服务化选型

:::note 预计用时 15 分钟 :::

## 练习 1：选型决策
| 场景 | 最佳选择 | 原因 |
|------|----------|------|
| 两天内部署 70B OpenAI API | NIM | 预打包分钟级 |
| 多后端 ensemble 流水线 | Triton | NIM 不支持 ensemble |

## 练习 2：NIM 架构
NIM = TensorRT-LLM（引擎）+ Triton（服务层）+ 容器化

:::info 记忆锚点
快速标准→NIM；灵活/ensemble→Triton；NIM底层=TensorRT-LLM
:::

---


### 实验：生产监控与可靠性


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/labs/chapter-11.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/labs/chapter-11.md) · 语言：中文原文



# 实验：生产监控与可靠性

:::note 预计用时 25 分钟 :::

## 实验目标

- 搭建 LLM 监控仪表板
- 实现漂移检测 + 告警
- 完成一次完整的根因分析

## 练习 1：监控仪表板搭建

```bash
# 1. 部署 DCGM Exporter
helm install dcgm-exporter nvidia/dcgm-exporter -n monitoring

# 2. 部署 Prometheus + Grafana
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring

# 3. 导入 LLM 监控模板 (Grafana Dashboard ID: 1860 + 自定义 LLM 面板)
# 面板包含：GPU 显存、p99 延迟、token/s、队列深度
```

## 练习 2：漂移检测验证

```python
from scipy import stats
import numpy as np

# 1. 计算 PSI
def calc_psi(expected, actual, bins=10):
    breakpoints = np.linspace(0, 1, bins + 1)
    expected_pct = np.histogram(expected, bins=breakpoints)[0] / len(expected)
    actual_pct = np.histogram(actual, bins=breakpoints)[0] / len(actual)
    psi = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return psi

# 2. PSI > 0.2 触发告警
psi = calc_psi(baseline_data, current_data)
print(f"PSI = {psi:.3f}")  # > 0.2 → 触发重训管道
```

## 练习 3：根因分析模拟

**场景：部署新模型后 p99 延迟从 200ms 飙升至 800ms**

| 排查步骤 | 操作 | 发现 |
|----------|------|------|
| 1. 确认告警 | Grafana 面板确认 p99 飙升 | 确认真警 |
| 2. 关联变更 | 检查最近 K8s Rollout | 2 小时前部署新模型 |
| 3. 分层排查 | DCGM 看 GPU 正常；看 CPU post-processing | CPU 利用率 95% |
| 4. 取证 | trace 分析显示 preprocessing 耗时占 70% | 新模型 token 数翻倍 |
| 5. 修复 | 优化 preprocessing 流水线 + 扩容 CPU 节点 | p99 恢复 180ms |

## 关键要点

:::info 本章记忆锚点
监控四层=硬件→服务→数据→业务；PSI>0.2=漂移；RCA=确认→关联→分层→取证→修复；DCGM+Prometheus+Grafana=标准监控栈。
:::

---


### 实验：全真模拟与策略


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-genl/labs/chapter-12.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-genl/labs/chapter-12.md) · 语言：中文原文



# 实验：全真模拟与策略

:::note 预计用时
120 分钟
:::

## 实验目标

- 体验完整 NCP-GENL 考试节奏
- 练习跨域综合推理
- 巩固高频陷阱识别

## 练习 1：综合推理题

**Q1. 某电商平台部署 LLM 客服，高峰时段延迟从 300ms 飙升至 1200ms，但 GPU 仅 40% 利用率。首选扩容策略？**

A. 增加 GPU 节点
B. 扩容 CPU + 优化 post-processing
C. 切换至更大模型
D. 减少并发连接

<details>
<summary>答案</summary>

**B** — GPU 利用率低 + 延迟高 → 瓶颈在 CPU/IO。扩容 CPU + 优化 preprocessing 是正确方向。

</details>

**Q2. 微调后模型在验证集上 loss 下降但线上用户投诉增加，最可能原因？**

A. 欠拟合
B. 过拟合验证集分布
C. 提示词工程不当
D. GPU 显存不足

<details>
<summary>答案</summary>

**B** — 验证集 loss 降但线上退化 = 过拟合验证集分布；需增加数据多样性 + 正则。

</details>

**Q3. 以下哪种分词器变更必须使用蓝绿部署而非金丝雀？**

A. 增加新 token 但保留旧 token ID
B. 完全替换词表（旧 token ID 不再有效）
C. 仅调整 BPE merge 顺序
D. 增加 special token

<details>
<summary>答案</summary>

**B** — 完全替换词表 = 向后不兼容 → 必须蓝绿部署清缓存。

</details>

## 关键要点

:::info 本章记忆锚点
GPU利用低+延迟高=非GPU瓶颈；验证集loss降但线上退化=过拟合；分词器不兼容=蓝绿部署；域权重前三合计44%（模型优化+GPU加速+提示/微调）。
:::

---


