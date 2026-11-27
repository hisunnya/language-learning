# NCP-AAI · 智能体 AI


## 考纲要点


### NVIDIA Agentic AI 认证的先修知识


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `Prerequisite_Knowledge.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/Prerequisite_Knowledge.md) · 语言：英文原文 · 中译版



# NVIDIA Agentic AI 认证的先修知识

## 如何使用本指南

本文档列出你在开始学习本教材之前应当具备的基础知识。先修要求分为三个层级：

- **必备（Essential）** - 你必须理解这些概念，才能从本书中获益。不掌握它们，你会在最基础的内容上感到吃力。
- **推荐（Recommended）** - 扎实的理解能显著提升你的学习体验。没有它们你也可以学成，但预计会频繁查阅外部资料。
- **加分（Beneficial）** - 这些内容能加速学习、加深理解，但并非严格要求。

每一项先修知识都包含：
- **它是什么** - 清晰的定义
- **为什么重要** - 与教材内容的关联
- **自测问题** - 检验你的准备程度
- **如果不确定** - 用于补齐基础的资源

**学习时间预估**：如果你需要补齐基础，预计需要 10-40 小时，具体取决于你的自身背景。

---

## 第 1 部分：技术基础

### 必备（ESSENTIAL）：大语言模型（LLM）基础

**它是什么**：理解现代语言模型的工作原理——逐 token 生成、上下文窗口、提示词策略，以及基本能力与局限。

**为什么重要**：本书中的每一种智能体架构都以 LLM 作为推理引擎。你需要围绕上下文限制来做设计，为推理延迟做规划，并依据推理能力来选择模型。如果没有 LLM 基础，架构决策就会显得随意，而非有原则依据。

**自测**：
- 你能解释什么是 token，并估算某个提示词的 token 消耗量吗？
- 你理解贪心解码与核采样（nucleus sampling）的区别，以及各自适用的场景吗？
- 你能解释 temperature 控制什么、如何影响输出吗？
- 你能描述什么是上下文窗口，以及它为何会限制智能体的记忆吗？
- 你知道零样本（zero-shot）、少样本（few-shot）和思维链（chain-of-thought）提示的区别吗？

**如果不确定**：
- 复习："Attention Is All You Need"（Transformer 论文），掌握架构基础
- 完成：Andrew Ng 的 "ChatGPT Prompt Engineering for Developers" 课程（2 小时）
- 阅读：OpenAI 的 GPT-4 技术报告或 Anthropic 的 Claude 文档
- 所需时间：4-6 小时

**之所以关键**：全部 10 个部分都假定你理解 LLM 能做什么、不能做什么。第 1 部分讲授构建在 LLM 之上的智能体架构。第 5 部分讲授 Tree-of-Thought 等高级推理模式，而这些都依赖对 LLM 生成过程的理解。第 7 部分讲授 NVIDIA 平台优化，需要深入的 LLM 推理知识。

---

### 必备（ESSENTIAL）：Python 编程

**它是什么**：熟练掌握中级 Python，包括函数、类、字典、列表推导式、异常处理，以及阅读和修改已有代码的能力。

**为什么重要**：所有代码示例和实验都使用 Python。各个框架的实现（LangChain、LangGraph、AutoGen、CrewAI）都基于 Python。你需要阅读框架代码、实现智能体并调试故障。

**自测**：
- 你能写出一个接受关键字参数并返回字典的 Python 函数吗？
- 你能读懂基于类的代码，理解方法调用、继承和组合吗？
- 你理解 Python 的异常处理（`try`/`except`/`finally`）吗？
- 你能操作嵌套数据结构（字典中包含字典列表）吗？
- 你会使用列表推导式和字典推导式吗？

**如果不确定**：
- 完成：Python for Everybody 专项课程（Coursera，第 1-5 周）
- 阅读：《Fluent Python》第 1-4 章（函数与对象）
- 练习：实现 5-10 个操作数据结构的小程序
- 所需时间：若从零开始，15-25 小时

**之所以关键**：第 2 部分（框架）为每个概念提供 Python 代码示例。第 7 部分（NVIDIA 平台）包含优化技术的 Python 实现。第 8 部分（运维）包含 Python 探针代码。你无法通过抄写自己都不理解的代码来学会东西。

---

### 必备（ESSENTIAL）：RESTful API 与 HTTP 基础

**它是什么**：理解 HTTP 请求-响应模式、常见动词（GET、POST、PUT、DELETE）、状态码（200、404、500）、JSON 序列化，以及分布式系统如何通过 API 通信。

**为什么重要**：智能体通过 API 调用外部工具。多智能体通信使用的是 API 模式。部署架构依赖于对 API 设计、延迟和故障模式的理解。工具编排、智能体协同协议和生产部署全都以 API 熟练度为基础。

**自测**：
- 你能解释 GET 与 POST 请求的区别吗？
- 你理解 HTTP 状态码的含义吗（2xx 成功、4xx 客户端错误、5xx 服务端错误）？
- 你能为某个工具设计一个 REST 端点吗（用什么动词、什么参数、返回什么响应）？
- 你能解析 JSON 响应并处理嵌套对象吗？
- 你理解 API 超时是什么，以及它为什么重要吗？

**如果不确定**：
- 阅读：MDN 的 HTTP 指南（2-3 小时）
- 完成："REST API Best Practices" 教程
- 练习：用 Python 的 `requests` 库调用 3-5 个公开 API
- 所需时间：3-5 小时

**之所以关键**：第 1 部分第 1.2 章（架构模式）在假定你熟悉 API 的前提下介绍工具使用架构。第 2 部分第 2.3 章（工具集成）讲授基于框架的工具调用。第 4 部分（部署）面向通过 REST 通信的微服务架构。第 7 部分（NVIDIA 平台）把推理端点部署为 REST 服务。

---

### 推荐（RECOMMENDED）：软件架构模式

**它是什么**：识别常见的架构风格——客户端-服务器、微服务、发布-订阅消息、分层架构、事件驱动系统。理解关注点分离、松耦合，以及架构权衡（复杂度与可扩展性之间的关系）。

**为什么重要**：智能体编排模式（集中式、去中心化、分层式）与软件架构直接对应。第 1 部分第 1.5 章"编排模式"本质上是在问："这个多智能体问题适合哪种软件架构？"理解架构模式能加速模式识别和设计决策。

**自测**：
- 你能解释单体架构与微服务架构的区别吗？
- 你理解"松耦合"意味着什么，以及它为什么重要吗？
- 你能描述发布-订阅消息，以及它在何时适用吗？
- 对于一个由 200 个智能体协同处理仓库运营的系统，你会选择集中式还是去中心化编排？为什么？

**如果不确定**：
- 阅读：Len Bass 的《Software Architecture in Practice》（第 1-3 章）
- 复习：《System Design Interview》中的常见模式（负载均衡、缓存、复制）
- 学习：真实系统架构（Uber、Netflix、AWS）案例研究
- 所需时间：5-8 小时

**之所以推荐**：理解架构模式能让第 1 部分的编排模式（第 1.5 章）变得直观，而不是死记硬背。第 4 部分的部署模式直接应用软件架构原则。

---

### 推荐（RECOMMENDED）：数据库基础

**它是什么**：理解关系型数据库与非关系型数据库的区别、基础 SQL、索引策略、查询优化、ACID 保证与最终一致性的取舍，以及存储方面的权衡。

**为什么重要**：第 1 部分第 1.3 章（记忆系统）要求你理解持久化。长期记忆存放在数据库中——向量数据库用于语义搜索，关系型数据库用于结构化事实。第 6 部分（知识集成）把嵌入存入向量数据库。第 8 部分（运维）向数据库写日志以进行监控。

**自测**：
- 你能写出带 WHERE 和 JOIN 子句的基础 SQL SELECT 查询吗？
- 你理解数据库索引的作用，以及它们为何能提升查询性能吗？
- 你能解释 ACID 属性（原子性、一致性、隔离性、持久性）吗？
- 你能比较 SQL 数据库（PostgreSQL）、NoSQL（MongoDB）与向量数据库（Pinecone）吗？

**如果不确定**：
- 完成：SQL 基础教程（W3Schools 或 Mode Analytics，3-4 小时）
- 阅读：Martin Kleppmann 的《Designing Data-Intensive Applications》（第 1-3 章）
- 练习：搭建 PostgreSQL、创建表、执行查询
- 所需时间：6-10 小时

**之所以推荐**：第 1.3 部分（记忆系统）讲授需要数据库知识的记忆架构。第 6 部分（RAG 与知识集成）大量使用向量数据库。没有数据库基础，你只会把存储当成黑箱，而无法理解其中的设计权衡。

---

### 加分（BENEFICIAL）：分布式系统概念

**它是什么**：理解系统如何跨网络通信——消息传递、最终一致性、同步与异步通信、共识协议、网络故障，以及 CAP 定理基础。

**为什么重要**：第 1 部分第 1.4-1.5 章（多智能体协同与编排）围绕分布式多智能体系统展开，智能体运行在不同进程、服务器甚至不同组织中。理解分布式系统原则可以避免"假设消息瞬间送达或绝对有序"这类架构错误。

**自测**：
- 你能解释同步消息与异步消息的区别吗？
- 如果三个智能体在协同处理一项任务时网络中断 5 秒，系统应该如何恢复？
- 你理解"最终一致性"意味着什么，以及分布式系统为何接受它吗？
- 你能解释共识协议解决了什么问题（在较高层面上谈谈 Raft、Paxos）？

**如果不确定**：
- 阅读：Brendan Burns 的《Designing Distributed Systems》（第 1-4 章）
- 复习：MIT 6.824 分布式系统课程讲义（第 1-3 讲）
- 学习：CAP 定理及其影响
- 所需时间：8-12 小时

**之所以加分**：它对第 1.4-1.5 部分（多智能体协同）而言是必备的，但对更早的章节则没那么关键。如果你只构建单智能体系统，可以推迟再学。如果你正在设计多智能体系统或企业级部署，它就变成必备内容了。

---

## 第 2 部分：基础设施与工具

### 必备（ESSENTIAL）：命令行与 Shell 脚本

**它是什么**：能够使用 `cd`、`ls`、`pwd` 浏览文件系统；用 `ps`、`kill`、`top` 管理进程；用 `cat`、`grep`、`sed` 操作文件；能编写包含变量、循环和条件判断的基本 bash 脚本。

**为什么重要**：第 3 部分（部署）和第 4 部分（扩展）要求熟练使用命令行进行 SSH 访问、容器管理、Kubernetes 操作和基础设施自动化。每个部署步骤都涉及终端命令。不具备 CLI 能力，你在工具链上就会处处掣肘。

**自测**：
- 你能浏览 Linux 文件系统，并用 `find` 或 `grep` 查找文件吗？
- 你能写一个遍历文件并逐个处理的 bash 脚本吗？
- 你理解环境变量以及如何设置它们（`export`）吗？
- 你能管理后台进程并把输出重定向到文件吗？
- 你能用 `ssh` 连接远程服务器吗？

**如果不确定**：
- 阅读：William E. Shotts 的《The Linux Command Line》（前 10 章）
- 完成：Linux Command Line Basics 教程（2-3 小时）
- 练习：浏览你的文件系统，编写 3-5 个 bash 脚本
- 所需时间：4-6 小时

**之所以必备**：第 3.1 部分（部署基础）假定你具备 shell 能力。第 4 部分（扩展）涉及 Kubernetes CLI（`kubectl`）、Docker CLI 和基础设施脚本。第 8 部分（运维）使用命令行监控工具。

---

### 必备（ESSENTIAL）：Docker 与容器化基础

**它是什么**：理解容器是什么、它们与虚拟机的区别、基础 Dockerfile 语法、构建镜像、运行容器、挂载卷，以及网络基础。

**为什么重要**：第 3 部分讲授容器化以实现可复现的部署。第 4 部分使用 Kubernetes 扩展容器化的智能体。第 7 部分部署 NVIDIA NIM 容器。没有容器基础，你会把 Docker 当成魔法，而无法理解隔离、层和资源限制。

**自测**：
- 你能解释 Docker 镜像是什么，以及它与容器有何不同吗？
- 你能写一个包含 `FROM`、`COPY`、`RUN`、`CMD` 的基础 Dockerfile 吗？
- 你理解容器隔离提供了什么（文件系统、进程、网络）吗？
- 你能运行容器、映射端口、挂载卷并查看日志吗？
- 你理解容器化为何能解决"在我机器上能跑"的问题吗？

**如果不确定**：
- 完成：Docker 的 "Getting Started" 教程（2 小时）
- 阅读：Nigel Poulton 的《Docker Deep Dive》（第 1-5 章）
- 练习：编写 2-3 个 Dockerfile、运行容器、排查故障
- 所需时间：5-8 小时

**之所以必备**：第 3.1 部分立即讲授容器化。第 3.3 部分（容器编排）依赖对容器的理解。第 7 部分把推理服务器部署为容器。在生产部署章节中，你无法跳过 Docker 而取得成功。

---

### 推荐（RECOMMENDED）：Kubernetes 基础

**它是什么**：理解 Kubernetes 基础——Pod（最小单元）、Service（网络）、Deployment（副本管理）、Namespace、kubectl CLI，以及 Kubernetes 如何在集群间调度工作负载。

**为什么重要**：第 3.3 部分（容器编排）和第 4 部分（扩展）大量使用 Kubernetes。现代生产级智能体系统都部署到 Kubernetes 或同类编排器上。理解 Pod、Service 和 Deployment 能让你把智能体实例从 1 个扩展到 1000 个。

**自测**：
- 你能解释 Kubernetes Pod 是什么，以及它为何是最小可部署单元吗？
- 你理解 Kubernetes Service 如何把 Pod 暴露给网络吗？
- 你能描述 Deployment 如何管理副本数与滚动更新吗？
- 你能用 `kubectl` 查看 Pod、Service 和日志吗？
- 你理解资源请求与限制（CPU、内存）吗？

**如果不确定**：
- 完成：Kubernetes 官方教程 "Learn Kubernetes Basics"（3-4 小时）
- 阅读：Kelsey Hightower 的《Kubernetes Up & Running》（第 1-6 章）
- 练习：把一个简单应用部署到 Minikube，对它扩容并升级
- 所需时间：8-12 小时

**之所以推荐**：第 3.3 部分假定你已了解 Kubernetes 基础。第 4 部分在扩展模式中大量使用 Kubernetes。如果你是在使用 Kubernetes 的云平台上部署（EKS、GKE、AKS），它就由推荐升级为必备。

---

### 加分（BENEFICIAL）：GPU 架构与 CUDA 基础

**它是什么**：理解 GPU 与 CPU 的差异、并行处理概念、GPU 内存层级、基础 CUDA 编程模型（内核、线程、线程块）以及张量运算。

**为什么重要**：第 7 部分（NVIDIA 平台）在 GPU 上优化 LLM 推理。理解 GPU 架构能帮助你弄明白量化为何有效、批处理如何提升吞吐，以及 KV cache 优化能带来什么。第 4 部分使用 NVIDIA Nsight 分析 GPU 利用率。

**自测**：
- 你能解释 GPU 为何擅长矩阵乘法（LLM 的主要运算）吗？
- 你理解 GPU 内存与 CPU 内存的区别吗？
- 你能解释并行处理对批量推理意味着什么吗？
- 你知道 GPU 利用率百分比说明了什么吗？

**如果不确定**：
- 阅读：NVIDIA 的《CUDA C Programming Guide》（导论部分）
- 复习：Kirk 与 Hwu 的《Programming Massively Parallel Processors》（第 1 章）
- 观看：NVIDIA 的 GPU 架构概览视频
- 所需时间：4-6 小时

**之所以加分**：即使没有深厚的 GPU 知识，你也能学会第 7 部分的优化技术——书中会讲清你需要知道的内容。不过，GPU 基础能让这些优化从"照着配方操作"变成真正直观。

---

## 第 3 部分：领域知识

### 必备（ESSENTIAL）：机器学习基础

**它是什么**：理解监督学习与无监督学习、训练与推理、模型评估指标（准确率、精确率、召回率）、过拟合，以及嵌入/向量表示的概念。

**为什么重要**：第 6 部分（知识集成）为 RAG 使用嵌入与向量相似度。第 7 部分（NVIDIA 平台）优化推理。第 9 部分（安全）讨论算法偏见。你需要机器学习基础，才能理解智能体为何会表现出特定的行为。

**自测**：
- 你能解释训练一个模型与用它做推理的区别吗？
- 你理解嵌入是什么，以及语义相似度为何在向量空间中有效吗？
- 你能解释过拟合，以及它为何对泛化能力重要吗？
- 你知道精确率和召回率衡量的是什么吗？

**如果不确定**：
- 完成：Andrew Ng 的 "Machine Learning" 课程（Coursera，第 1-3 周）
- 阅读：Aurélien Géron 的《Hands-On Machine Learning》（第 1-2 章）
- 练习：训练一个简单的 scikit-learn 分类器并进行评估
- 所需时间：10-15 小时

**之所以必备**：第 6 部分大量使用嵌入和向量数据库。第 7 部分讨论模型量化与优化。第 9 部分分析机器学习系统中的偏见。没有机器学习基础，这些章节读起来就像咒语，而不像有原则的技术。

---

### 推荐（RECOMMENDED）：自然语言处理（NLP）基础

**它是什么**：理解分词、词嵌入、注意力机制、高层次上的 Transformer 架构，以及常见的 NLP 任务（分类、生成、问答）。

**为什么重要**：LLM 就是 NLP 模型。理解 Transformer 和注意力机制能帮助你弄懂上下文窗口、token 上限，以及某些架构决策为何存在。第 5 部分（认知）讲授建立在 Transformer 能力之上的高级推理模式。

**自测**：
- 你能解释分词做了什么，以及它为何重要吗？
- 你理解注意力机制计算的是什么（从高层次上说）吗？
- 你能描述 Transformer 架构（编码器-解码器、自注意力）吗？
- 你知道 Transformer 模型与 RNN 的区别在哪里吗？

**如果不确定**：
- 阅读："Attention Is All You Need" 论文（最初的 Transformer 论文）
- 完成：Hugging Face NLP 课程（第 1-2 章）
- 观看：斯坦福 CS224N 关于 Transformer 的讲座
- 所需时间：6-10 小时

**之所以推荐**：理解 Transformer 能加深你对 LLM 的理解（第 1 部分）。当你理解 Transformer 的工作机制后，第 5 部分的高级推理模式会更容易理解。第 7 部分的优化技术（量化、KV cache）直接针对 Transformer 的组件。

---

### 加分（BENEFICIAL）：提示工程技巧

**它是什么**：设计有效提示的实用技能——少样本示例、思维链提示、提示模板、系统消息、基于角色的提示，以及提示调试策略。

**为什么重要**：第 1 部分讲授使用提示的智能体架构。第 2 部分讲授带提示模板的框架。第 5 部分讲授需要精巧提示的高级推理。更好的提示技能能加速你的学习和实验成功。

**自测**：
- 你能写出一个向 LLM 演示任务的少样本提示吗？
- 你理解思维链提示，以及何时该使用它吗？
- 你能系统地调试一个失败的提示吗？
- 你知道系统消息与用户消息的区别吗？

**如果不确定**：
- 完成：DeepLearning.AI 的 "ChatGPT Prompt Engineering for Developers"（2 小时）
- 阅读：OpenAI 的提示工程指南
- 练习：为各种任务编写 10-15 个提示，并针对失败案例迭代
- 所需时间：3-5 小时

**之所以加分**：书在必要之处会讲授提示技巧，但扎实的提示技能会让实验更轻松。第 5 部分的 Tree-of-Thought 推理涉及复杂提示。第 7 部分的护栏机制也使用提示工程来实现安全防护。

---

## 第 4 部分：可选的加速项

### 加分（BENEFICIAL）：API 设计与 REST 原则

**它是什么**：理解 RESTful 设计原则、API 版本管理、认证（OAuth、JWT）、限流、分页和幂等性。

**为什么重要**：第 2 部分讲授使用 API 进行工具集成。第 4 部分用 REST 端点架构微服务。第 7 部分部署推理 API。扎实的 API 设计技能能帮助你设计更好的工具接口并调试集成故障。

**自测**：
- 你能按照最佳实践设计一个 RESTful API 吗？
- 你理解 API 的认证机制吗？
- 你能解释限流是什么，以及 API 为何要实现它吗？
- 你知道幂等性意味着什么，以及它为何重要吗？

**如果不确定**：
- 阅读：Leonard Richardson 的《RESTful Web APIs》
- 复习：Stripe、Twilio 或 GitHub API 文档中的最佳实践指南
- 练习：为 3-5 个智能体工具设计 API
- 所需时间：4-6 小时

**之所以加分**：书会讲授 REST 基础，但更高级的 API 设计在第 2 部分（工具集成）和第 4 部分（部署架构）中都有帮助。

---

### 加分（BENEFICIAL）：Python 异步编程

**它是什么**：理解 Python 的 `async`/`await` 语法、事件循环、并发执行，以及并行与并发的区别。

**为什么重要**：第 2 部分各框架使用异步模式实现并发工具执行。第 7 部分用异步处理优化吞吐。第 8 部分实现异步监控。如果你要自己实现智能体（而不只是配置框架），异步就是必备的。

**自测**：
- 你能写一个 `async` 函数并使用 `await` 吗？
- 你理解 `asyncio.gather()` 与顺序执行的区别吗？
- 你能说明异步在何时带来收益（I/O 密集型任务）吗？
- 你知道线程、进程和异步任务三者的区别吗？

**如果不确定**：
- 阅读：Matthew Fowler 的《Python Concurrency with asyncio》（第 1-4 章）
- 完成：Real Python 的 "Async IO in Python" 教程
- 练习：编写 3-5 个并发调用多个 API 的异步程序
- 所需时间：5-8 小时

**之所以加分**：如果你只是使用框架，异步是隐藏的。如果你要实现自定义智能体逻辑或优化性能，异步就变成必备。第 2.6 部分（高级工具集成）包含异步示例。

---

### 加分（BENEFICIAL）：CI/CD 与 DevOps 基础

**它是什么**：理解持续集成/持续部署流水线、自动化测试、基础设施即代码、版本控制（git），以及部署自动化（GitHub Actions、GitLab CI）。

**为什么重要**：第 4 部分讲授智能体系统的 CI/CD。第 8 部分（运维）在 CI/CD 流水线中实现监控。生产级智能体需要自动化测试、部署与回滚策略。

**自测**：
- 你能解释 CI/CD 达成什么，以及它为何重要吗？
- 你理解部署流水线中的自动化测试吗？
- 你能用 git 进行版本控制（提交、分支、合并）吗？
- 你能编写一个简单的 GitHub Actions 工作流吗？

**如果不确定**：
- 阅读：Jez Humble 的《Continuous Delivery》（第 1-3 章）
- 完成：GitHub Actions 教程（官方文档，2 小时）
- 练习：为一个简单的 Python 应用搭建 CI/CD 流水线
- 所需时间：6-10 小时

**之所以加分**：第 4 部分讲授 CI/CD 模式。如果你理解 DevOps 原则，实现流水线会更快；如果不理解，书也提供了足够的指引。

---

## 自测总结

在开始学习本教材之前，你应当能够对以下问题回答"是"：

**必备（必须全部满足）：**
- [ ] 我理解 LLM 的工作原理（token、上下文窗口、提示）
- [ ] 我能编写并调试中级 Python 代码
- [ ] 我理解 REST API 与 HTTP 基础
- [ ] 我能使用命令行界面并编写 bash 脚本
- [ ] 我理解 Docker 容器并能构建镜像

**推荐（应满足大部分）：**
- [ ] 我理解基本的软件架构模式
- [ ] 我了解数据库基础（SQL、索引、权衡）
- [ ] 我会使用 Kubernetes 基础（Pod、Service、Deployment）
- [ ] 我理解机器学习基础与嵌入

**加分（有帮助但非必需）：**
- [ ] 我理解分布式系统概念
- [ ] 我了解 GPU 架构与并行处理基础
- [ ] 我有提示工程方面的实践经验
- [ ] 我能编写异步 Python 代码
- [ ] 我理解 CI/CD 与 DevOps 原则

**如果你勾选的必备项少于 4/5**：开始之前投入 2-3 周补齐基础。现在投入的时间可以省去日后的挫败感。

**如果你勾选了 4-5 项必备内容和 2 项以上推荐内容**：你已经可以开始了。按需查阅外部资料即可。

**如果你勾选了大部分条目**：你的基础非常扎实，学习进度会很快。

---

## 推荐的准备路径

### 路径 1：最小准备（2-3 周，25-35 小时）

**重点**：只补第 1-2 部分所需的必备先修知识
1. 第 1 周：LLM 基础、Python 基础、REST API（12-15 小时）
2. 第 2 周：命令行、Docker 基础（10-12 小时）
3. 第 3 周：复习第 1 部分的前言，开始阅读正文（3-8 小时）

**结果**：可以开始第 1 部分，在第 3-4 部分会频繁查阅文档

---

### 路径 2：推荐准备（4-5 周，40-60 小时）

**重点**：必备 + 推荐先修知识
1. 第 1-2 周：路径 1 中的必备先修知识（25-30 小时）
2. 第 3 周：架构模式、数据库基础（10-15 小时）
3. 第 4 周：Kubernetes 基础、机器学习基础（12-18 小时）
4. 第 5 周：复习各部分前言，开始第 1 部分（3-8 小时）

**结果**：为全部 10 个部分打下坚实基础，学习推进顺畅

---

### 路径 3：全面准备（6-8 周，60-90 小时）

**重点**：必备 + 推荐 + 加分
1. 第 1-3 周：完成路径 2（45-60 小时）
2. 第 4 周：分布式系统、GPU 架构（10-15 小时）
3. 第 5 周：NLP 基础、提示工程（8-12 小时）
4. 第 6 周：异步 Python、CI/CD 基础（10-15 小时）
5. 第 7-8 周：复习、练习实验，开始第 1 部分（5-10 小时）

**结果**：全面的基础，在所有部分中都能快速推进

---

## 补齐基础的资源

### LLM 与机器学习基础
- **免费**：Andrew Ng 的 "Machine Learning"（Coursera）
- **免费**："ChatGPT Prompt Engineering for Developers"（DeepLearning.AI）
- **书籍**：Aurélien Géron 的《Hands-On Machine Learning》
- **论文**："Attention Is All You Need"（Transformer 架构）

### Python 编程
- **免费**：Python for Everybody（Coursera）
- **免费**：Real Python 教程
- **书籍**：Luciano Ramalho 的《Fluent Python》
- **练习**：LeetCode 简单难度题目（数据结构）

### 基础设施与工具
- **免费**：Docker "Getting Started" 教程
- **免费**：Kubernetes "Learn Kubernetes Basics"
- **书籍**：William E. Shotts 的《The Linux Command Line》
- **书籍**：Nigel Poulton 的《Docker Deep Dive》

### 软件工程
- **书籍**：Martin Kleppmann 的《Designing Data-Intensive Applications》
- **书籍**：Len Bass 的《Software Architecture in Practice》
- **免费**：系统设计面试资源（GitHub 仓库）

---

## 最后的建议

**面向在校学生**：你很可能已有扎实的机器学习/编程基础，但可能缺少基础设施经验。重点补 Docker、Kubernetes 和命令行技能（路径 2，第 3-4 周）。

**面向软件工程师**：你很可能已有扎实的基础设施经验，但可能缺少机器学习/LLM 经验。重点补 LLM 基础、嵌入与提示工程（路径 2，第 1-2 周）。

**面向机器学习从业者**：你很可能已有扎实的机器学习基础，但可能缺少生产部署经验。重点补 Docker、Kubernetes、CI/CD 与分布式系统（路径 3，第 4-6 周）。

**面向转行人士**：你可能需要在所有类别上做全面准备。系统地执行路径 3，在开始学习教材前投入 60-90 小时。

**关键洞见**：本教材全面讲授智能体化 AI，但它假定你已经具备基础知识。在先修知识上投入的时间不会白费——它会在 138-180 小时的教材学习中不断被放大。从扎实的基础起步，每一章都会变得更清晰、更快、也更有回报。

---


### NCP-AAI Agentic AI Professional 考纲逐条要点


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-aai/exam-objectives.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-aai/exam-objectives.md) · 语言：中文原文



# NCP-AAI Agentic AI Professional 考纲逐条要点

> 来源：英伟达官方考试页面 · [Agentic AI Professional](https://www.nvidia.cn/training/certification/agentic-ai-professional/)
>
> ⚠️ 版权归 NVIDIA 所有；本仓只整理覆盖度清单，不含 PDF 副本。

## 域 1 · 智能体架构和设计（考试权重 15%）

| # | 考点 | 状态 |
|---|---|---|
| 1.1 | 代理式 AI 系统的基础结构和设计，智能体在环境中进行交互、推理和沟通 | ⬜ |

## 域 2 · 智能体开发（考试权重 15%）

| # | 考点 | 状态 |
|---|---|---|
| 2.1 | 实际建构、集成和增强智能体 | ⬜ |

## 域 3 · 评估和调整（考试权重 13%）

| # | 考点 | 状态 |
|---|---|---|
| 3.1 | 衡量、比较和优化智能体性能 | ⬜ |

## 域 4 · 部署和扩展（考试权重 13%）

| # | 考点 | 状态 |
|---|---|---|
| 4.1 | 运行和扩展智能代理系统 | ⬜ |

## 域 5 · 认知、规划和记忆（考试权重 10%）

| # | 考点 | 状态 |
|---|---|---|
| 5.1 | 智能体行为底层的核心认知过程，包括推理策略、决策和内存管理 | ⬜ |

## 域 6 · 知识整合和数据处理（考试权重 10%）

| # | 考点 | 状态 |
|---|---|---|
| 6.1 | 整合外部知识以及管理各种类型的数据 | ⬜ |

## 域 7 · NVIDIA 平台部署（考试权重 7%）

| # | 考点 | 状态 |
|---|---|---|
| 7.1 | 充分利用 NVIDIA 面向代理式 AI 推出的 AI 硬件和软件平台 | ⬜ |

## 域 8 · 运行、监控和维护（考试权重 5%）

| # | 考点 | 状态 |
|---|---|---|
| 8.1 | 智能代理系统部署后的持续运行、监控和维护 | ⬜ |

## 域 9 · 安全、道德与合规（考试权重 5%）

| # | 考点 | 状态 |
|---|---|---|
| 9.1 | 确保代理式 AI 负责任地运行、恪守道德标准并遵守法律和监管框架 | ⬜ |

## 推荐阅读

- [NVIDIA 官方认证页](https://www.nvidia.cn/training/certification/agentic-ai-professional/)
- [NVIDIA NeMo](https://developer.nvidia.com/nemo)
- [NVIDIA Nemotron](https://developer.nvidia.com/nemotron)
- [NVIDIA AI Blueprint](https://developer.nvidia.com/ai-blueprint)

---


### NCP-AAI · Agentic AI Professional


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-aai/overview.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-aai/overview.md) · 语言：中文原文



# NCP-AAI · Agentic AI Professional

> [英伟达官方认证页](https://www.nvidia.cn/training/certification/agentic-ai-professional/)

## 考试基本信息

| 项目 | 详情 |
|---|---|
| 考试编号 | NCP-AAI |
| 等级 | Professional（专业级） |
| 考试时长 | 约 1 小时 |
| 题型 | 单选题 / 多选题 |
| 语言 | 中文 |
| 考试费用 | 见官网 |
| 证书有效期 | 见官网 |

## 面向人群

- AI 智能体 (Agent) 开发者、AI 应用架构师
- 研究 Agent / RAG / Tool-use 的工程师

## 考点权重

| 模块 | 权重 | 一句话抓总 |
|---|---|---|
| 智能体架构和设计 | 15% | 智能体结构与设计 |
| 智能体开发 | 15% | 构建、集成和增强智能体 |
| 评估和调整 | 13% | 衡量、比较和优化性能 |
| 部署和扩展 | 13% | 运行和扩展智能体系统 |
| 认知、规划和记忆 | 10% | 推理策略、决策和内存管理 |
| 知识整合和数据处理 | 10% | 外部知识与多模态数据 |
| NVIDIA 平台部署 | 7% | NVIDIA AI 硬件和软件平台 |
| 运行、监控和维护 | 5% | 部署后运维 |
| 安全、道德与合规 | 5% | 负责任 AI / 合规 |

> 完整考纲逐条见 [exam-objectives.md](./exam-objectives.md)。

---



## 速查表


### LLM 智能体的解剖学 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-aai/cheatsheets/chapter-01.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-aai/cheatsheets/chapter-01.md) · 语言：中文原文



# LLM 智能体的解剖学 — 速查表

## 控制模式对比

| 模式 | 机制 | 适用场景 |
|------|------|----------|
| ReAct | Thought → Action → Observation，动态分支 | 需基于中间结果决定下一步 |
| Plan-and-execute | 预生成完整计划后顺序执行 | 任务固定、无需动态调整 |
| Tree-of-thought | 并行探索多分支，评分+回溯 | 多解路径、需回溯的逻辑谜题 |

## 关键选择规则

| 场景 | 模式 | 原因 |
|------|------|------|
| 动态分支（库存缺货则升级非退款） | ReAct | 基于观察的动态决策 |
| 逻辑谜题多路径需回溯 | Tree-of-thought | 显式分支评估+回溯 |
| 固定顺序子任务 | Plan-and-execute | 预定义计划足够 |

:::info 记忆锚点
动态分支→ReAct；多解+回溯→ToT；固定计划→Plan-execute
:::

:::caution 高频陷阱
5 智能体架构不一定最优；ReAct ≠ Plan-and-execute（前者动态，后者静态）
:::

---


### 结构化推理与工具调用模式 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-aai/cheatsheets/chapter-02.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-aai/cheatsheets/chapter-02.md) · 语言：中文原文



# 结构化推理与工具调用模式 — 速查表

## 推理模式选择

| 模式 | 核心能力 | 考试要点 |
|------|----------|----------|
| ReAct | 对观察反应，无分支探索 | 顺序工具调用 |
| Tree-of-thought | 多分支评估+回溯 | 死胡同多的问题 |
| Chain-of-thought | 单一线性推理 | 无回溯需求 |

## 工具调用可靠性

| 技术 | 作用 | 确保 |
|------|------|------|
| JSON-schema 受限调用 | 显式类型+必填字段 | 格式正确、类型安全 |
| 参数校验 | 服务端 schema 校验 | 业务规则满足 |

:::info 记忆锚点
多路径+死胡同→ToT 回溯；可靠调用→JSON-schema；单路径→CoT/ReAct
:::

---


### 多智能体协作模式 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-aai/cheatsheets/chapter-03.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-aai/cheatsheets/chapter-03.md) · 语言：中文原文



# 多智能体协作模式 — 速查表

## 协调模式对比

| 模式 | 结构 | 特征 |
|------|------|------|
| Supervisor/worker | 中央 agent 路由+委派 | 专家不互通信 |
| 分层树 | 多级 manager 委派 | 中层管下层 |
| 协作辩论/评审 | agent 迭代挑战彼此 | 评审互动 |
| 顺序流水线 | 固定线性链 | 无条件路由 |
| 点对点 mesh | 无中央权威 | 全连接 |

## 选择规则

| 场景 | 模式 |
|------|------|
| 中央分类后派发给专家 | Supervisor/worker |
| 领域 manager→专门 worker | 分层树 |
| agent 互相评审改进 | 协作辩论 |
| 固定流程 | 顺序流水线 |

:::info 记忆锚点
中央路由→Supervisor；多级管理→分层树；互相评审→辩论
:::

---


### 编排框架与状态管理 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-aai/cheatsheets/chapter-04.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-aai/cheatsheets/chapter-04.md) · 语言：中文原文



# 编排框架与状态管理 — 速查表

## 框架对比

| 框架 | 核心模型 | 特点 |
|------|----------|------|
| LangGraph | StateGraph（节点+边+持久状态） | 条件分支+检查点+human-in-loop |
| AutoGen | GroupChat（对话驱动） | 自由对话、最小工作流结构 |
| CrewAI | Sequential/层次化 | 固定任务顺序 |
| NeMo AIQ | 框架无关包装器 | 编排+可观测性 |

## 关键选择

| 需求 | 框架 |
|------|------|
| 条件分支+检查点+HITL | LangGraph |
| 自由对话+最小结构 | AutoGen |
| 固定顺序多任务 | CrewAI |

:::info 记忆锚点
条件状态+恢复→LangGraph；自由对话→AutoGen；顺序→CrewAI
:::

---


### 任务分解与记忆系统 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-aai/cheatsheets/chapter-05.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-aai/cheatsheets/chapter-05.md) · 语言：中文原文



# 任务分解与记忆系统 — 速查表

## 记忆类型

| 类型 | 内容 | 场景 |
|------|------|------|
| 短期/工作记忆 | 当前会话上下文 | 即时推理 |
| 情景记忆 | 特定过去交互（3周前用户偏好）| 个性化服务 |
| 语义记忆 | 事实知识（巴黎是法国首都） | 知识检索 |
| Scratchpad/目标重述 | 每步重申原始目标 | 长视野任务防漂移 |

## 长任务防漂移技术

| 问题 | 解决方案 |
|------|----------|
| 40 步任务偏离原始目标 | 每步重新注入目标陈述 |
| 跨会话个性化 | 情景记忆存储用户偏好 |

:::info 记忆锚点
目标漂移→每步重述；特定过去→情景记忆；事实知识→语义记忆
:::

---


### 面向智能体的检索增强生成 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-aai/cheatsheets/chapter-06.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-aai/cheatsheets/chapter-06.md) · 语言：中文原文



# 面向智能体的检索增强生成 — 速查表

## 核心模式

| 步骤 | 操作 | 目的 |
|------|------|------|
| 分块 | 300-500 token/块 | 适合嵌入+检索 |
| 嵌入 | 向量表示 | 语义搜索 |
| 检索 | Top-k 相关块 | 候选获取 |
| 重排 | 交叉编码器精排 | 提升相关性 |
| 生成 | LLM 产出答案 | 引用源块 |

## 混合检索

| 方法 | 优势 |
|------|------|
| BM25/关键词 | 精确 ID 查找（"第 12.4(b) 节"） |
| 稠密嵌入 | 语义概念匹配 |
| 混合（BM25+稠密+重排） | 两者兼顾 |

:::info 记忆锚点
分块300-500；精确ID→BM25；语义→嵌入；最佳→混合+重排
:::

---


### 护栏、可观测性与扩展 — 速查表


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-aai/cheatsheets/chapter-09.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-aai/cheatsheets/chapter-09.md) · 语言：中文原文



# 护栏、可观测性与扩展 — 速查表

## NeMo Guardrails 配置

| Rail 类型 | 运行位置 | 处理内容 |
|-----------|----------|----------|
| 输入 rail | 用户消息到达 LLM 前 | prompt injection 拦截 |
| 输出 rail | 生成响应给用户前 | PII 脱敏 |

## 关键场景

| 威胁 | 防御位置 |
|------|----------|
| prompt injection | 输入 rail |
| PII 泄露 | 输出 rail |

:::info 记忆锚点
注入→输入rail；PII→输出rail；两者配置不可颠倒
:::

---



## 记忆卡


### Part 6, Chapter 6.6.3: "I Do" - Reranking Implementation


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/archive/Part_06_Chapter_6.6A_Reranking_Implementation.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/archive/Part_06_Chapter_6.6A_Reranking_Implementation.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Chapter 6, Section 6.6.4-6.6.6: Advanced Retrieval Practice


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/archive/Part_06_Chapter_6.6C_Advanced_Retrieval_Practice.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/archive/Part_06_Chapter_6.6C_Advanced_Retrieval_Practice.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### 46 门 AI 101 候选课程的评估与排名


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `supplemental_course/evaluation.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/supplemental_course/evaluation.md) · 语言：英文原文 · 中译版



# 46 门 AI 101 候选课程的评估与排名

日期：2026-07-16。输入：`course_inventory.csv`（46 门经 QA 核验的课程）、`courses.md`（完整条目）、`concepts.md`（C/O 锚点）。清单 CSV 现已按排名排序，并在 `rank`、`eval_score`、`o_count`、`c_count`、`score_cost`、`score_audience_fit`、`score_provider`、`score_quality`、`score_recency` 各列中记录各分项得分。

## 1. 方法论

综合得分 0–100 分，由七个分项构成。权重反映该数据集的用途：法定教育目标（O1–O3）占主导地位，其次是内容广度（C1–C6）；成本、受众契合度、机构实力、质量信号与时效性则用于微调排序。

| 分项 | 满分 | 评分方式 |
|---|---|---|
| 目标覆盖度（O1–O3） | 30 | 每满足一个目标得 10 分（依据经 QA 核验的 CSV 标记） |
| 内容覆盖度（C1–C6） | 20 | （覆盖的 C 领域数量 ÷ 6）× 20 |
| 成本 / 可及性 | 15 | 免费含证书 15 · 免费（免费或廉价证书）14 · 免费旁听（证书收费）12 · ≤$60 得 10 · ≤$150 得 9 · 仅限 Coursera Plus（约 $59/月）6；存在访问摩擦（申请批次、封闭版本、账号限制）扣 2 分 |
| 受众契合度 | 15 | 专为政府打造 15 · 面向普通职场人士的 AI 101 12 · 部分通用 / 小众定位 9–11 · 垂直领域（教育、营销、欧盟法律、仅智能体方向）7–8 · 研究生节奏 6 |
| 机构与讲师 | 10 | 点名的资深教授、顶尖机构 10 · 点名的教授、实力扎实的机构 8–9 · 可信的团队 / 实务专家主导 7–8 · 未点名的师资团队 6–7 |
| 质量信号 | 5 | 全州范围采用，或报名人数 >20k 且评分 ≥4.6 得 5 · 评分 / 报名表现稳健 3–4 · 太新 / 无信号 2 · 表现不一 1 |
| 时效性 | 5 | 2026 年 = 5 · 2025 年 = 4 · 2024 年 = 3 |

覆盖度分项是机械计算得出的（由经 QA 核验的 CSV 标记计算）；成本、契合度、机构与质量则由人工逐门课程梳理，并附一行理由说明（第 4 节）。评分是可复现的：脚本中内嵌了全部人工评分。

## 2. 排名

| # | 得分 | 课程 | 主办方 | O | C | 成本 | 契合 | 机构 | 质量 | 时效 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 95.0 | [The Science and Implications of Generative AI (open archive)](https://generative-ai-course.hks.harvard.edu/spring-2024) | Harvard Kennedy School | 3/3 | 6/6 | 14 | 15 | 10 | 3 | 3 |
| 2 | 94.0 | [AI Fundamentals for Public Servants](https://apolitical.co/microcourses/en/ai-fundamentals-for-public-servants-opportunities-risks-and-strategies/) | Stanford Online + Stanford HAI | 3/3 | 6/6 | 14 | 15 | 8 | 4 | 3 |
| 3 | 94.0 | [Responsible AI for Public Sector Legal Professionals](https://innovate-us.org/course/responsible-ai-for-public-sector-legal-professionals/) | InnovateUS | 3/3 | 6/6 | 15 | 13 | 9 | 3 | 4 |
| 4 | 93.7 | [Responsible AI for Public Organizations](https://innovate-us.org/course/responsible-ai-for-public-organizations/) | InnovateUS | 3/3 | 5/6 | 15 | 15 | 9 | 4 | 4 |
| 5 | 93.7 | [Responsible AI for Public Professionals](https://innovate-us.org/course/responsible-ai-for-public-professionals/) | InnovateUS | 3/3 | 5/6 | 15 | 15 | 9 | 5 | 3 |
| 6 | 92.7 | [AI and Digital Transformation in Government](https://www.sbs.ox.ac.uk/programmes/executive-education/online-learning/ai-and-digital-transformation-government) | Oxford Saïd + UNESCO | 3/3 | 5/6 | 15 | 15 | 7 | 5 | 4 |
| 7 | 91.0 | [Introduction to Artificial Intelligence (UIUC)](https://www.coursera.org/learn/intro-to-artificial-intelligence) | UIUC (Gies) | 3/3 | 6/6 | 12 | 12 | 9 | 4 | 4 |
| 8 | 89.7 | [AI Foundations for Business Professionals (specialization)](https://www.coursera.org/specializations/ai-foundations-business-professionals) | Oxford Saïd | 3/3 | 5/6 | 12 | 12 | 10 | 5 | 4 |
| 9 | 88.3 | [Free Online Certificate in AI and Career Empowerment](https://www.rhsmith.umd.edu/programs/executive-education/learning-opportunities-individuals/free-online-certificate-artificial-intelligence-and-career-empowerment) | UMD Smith | 3/3 | 4/6 | 15 | 13 | 9 | 4 | 4 |
| 10 | 88.0 | [AI Literacy for Everyone (specialization)](https://www.coursera.org/specializations/ai-literacy-for-everyone) | University of Michigan | 3/3 | 6/6 | 12 | 12 | 7 | 4 | 3 |
| 11 | 88.0 | [AI for Work and Life (UNF)](https://learn.getcertificate.online/courses/course-v1:UNF+AI101+2025_S/about) | University of North Florida | 3/3 | 6/6 | 12 | 12 | 8 | 2 | 4 |
| 12 | 86.7 | [Artificial Intelligence for Everyone](https://www.futurelearn.com/courses/artificial-intelligence-for-everyone) | Universiti Malaya | 3/3 | 5/6 | 14 | 12 | 8 | 2 | 4 |
| 13 | 85.3 | [AI Governance](https://www.coursera.org/learn/ai-governance) | Oxford Saïd | 3/3 | 4/6 | 12 | 12 | 10 | 4 | 4 |
| 14 | 83.3 | [Generative AI Cybersecurity & Privacy for Leaders](https://www.coursera.org/learn/generative-ai-security-privacy) | Vanderbilt | 3/3 | 4/6 | 12 | 11 | 9 | 4 | 4 |
| 15 | 81.7 | [AI Regulation: Navigating the EU AI Act](https://learningforlife.tudelft.nl/ai-regulation-navigating-the-eu-ai-act/) | TU Delft | 3/3 | 5/6 | 12 | 8 | 8 | 2 | 5 |
| 16 | 81.7 | [AI in National Security (SCSP)](https://www.coursera.org/learn/ai-national-security) | Special Competitive Studies Project | 2/3 | 5/6 | 14 | 15 | 8 | 4 | 4 |
| 17 | 78.7 | [AI in Education: Leveraging ChatGPT for Teaching](https://www.coursera.org/learn/ai-in-education-leveraging-chatgpt-for-teaching) | Wharton | 3/3 | 5/6 | 6 | 9 | 10 | 4 | 3 |
| 18 | 78.7 | [Unleash Your Potential: AI Fundamentals](https://www.futurelearn.com/courses/unleash-your-potential-ai-fundamentals) | University of Bristol | 2/3 | 5/6 | 14 | 12 | 9 | 2 | 5 |
| 19 | 77.3 | [Introduction to AI Literacy](https://explore.acadiau.ca/product?catalog=AI-Literacy) | Acadia University | 2/3 | 4/6 | 15 | 12 | 8 | 4 | 5 |
| 20 | 77.0 | [AI Ethics, Inclusion & Society](https://www.futurelearn.com/courses/ai-ethics-inclusion-and-society) | University of Glasgow | 2/3 | 6/6 | 14 | 10 | 7 | 2 | 4 |
| 21 | 76.7 | [Foundations of Generative AI](https://www.edx.org/learn/artificial-intelligence/the-georgia-institute-of-technology-introduction-to-genai) | Georgia Tech | 2/3 | 5/6 | 12 | 12 | 9 | 3 | 4 |
| 22 | 75.0 | [How to AI (Almost) Anything (MAS.S60)](https://ocw.mit.edu/courses/mas-s60-how-to-ai-almost-anything-spring-2025/) | MIT Media Arts and Sciences | 2/3 | 6/6 | 14 | 6 | 9 | 2 | 4 |
| 23 | 74.3 | [AI Literacy for Life & Work](https://www.gvsu.edu/computing/ai-community-coursecertificate-258) | Grand Valley State | 2/3 | 4/6 | 14 | 12 | 8 | 2 | 5 |
| 24 | 74.0 | [What Can AI Do for Marketing?](https://www.coursera.org/learn/whatcanaidoformarketing) | Emory (Goizueta) | 3/3 | 3/6 | 12 | 7 | 9 | 3 | 3 |
| 25 | 73.3 | [AI Fundamentals](https://www.futurelearn.com/courses/how-to-get-into-ai) | University of Leeds | 2/3 | 4/6 | 14 | 12 | 8 | 3 | 3 |
| 26 | 71.7 | [Generative AI in Education](https://www.coursera.org/learn/generative-ai-in-education) | University of Glasgow | 2/3 | 5/6 | 14 | 7 | 8 | 3 | 3 |
| 27 | 71.3 | [Artificial Intelligence in National Security](https://www.edx.org/learn/social-sciences/kings-college-london-artificial-intelligence-in-national-security) | King's College London | 2/3 | 4/6 | 12 | 10 | 9 | 3 | 4 |
| 28 | 70.7 | [The AI Awakening](https://www.coursera.org/learn/ai-awakening) | Stanford School of Engineering | 2/3 | 5/6 | 6 | 11 | 10 | 4 | 3 |
| 29 | 70.3 | [AI Safety, Ethics, and Society](https://www.aisafetybook.com/virtual-course) | Center for AI Safety | 2/3 | 4/6 | 12 | 10 | 9 | 3 | 3 |
| 30 | 70.3 | [Introduction to Generative AI (Duke)](https://www.coursera.org/learn/intro-gen-ai) | Duke University | 2/3 | 4/6 | 12 | 10 | 8 | 4 | 3 |
| 31 | 70.0 | [AI, Justice and Rule of Law](https://secure.sbs.ox.ac.uk/corporate/landingPage.do?method=load&corporateGroupId=7948447) | UNESCO + Oxford | 2/3 | 3/6 | 15 | 9 | 9 | 2 | 5 |
| 32 | 69.3 | [A Human Rights-Based Approach to AI](https://elearning.gchumanrights.org/courses/course-v1:gchumanrights+HRBAtoAI+2025/about) | Global Campus of Human Rights | 2/3 | 4/6 | 12 | 10 | 8 | 2 | 4 |
| 33 | 69.3 | [AI Policy and Governance](https://www.purdue.edu/online/artificial-intelligence-micro-credentials/) | Purdue University | 2/3 | 4/6 | 9 | 13 | 9 | 2 | 3 |
| 34 | 69.0 | [Agentic AI and AI Agents: A Primer for Leaders](https://www.coursera.org/learn/agentic-ai) | Vanderbilt | 2/3 | 3/6 | 12 | 9 | 9 | 5 | 4 |
| 35 | 69.0 | [Responsible AI Foundations (course series)](https://alltechishuman.org/rai-courses) | All Tech Is Human | 2/3 | 3/6 | 14 | 10 | 8 | 3 | 4 |
| 36 | 68.7 | [GenAI 101](https://kelley.iu.edu/learnAI) | Indiana University (Kelley) | 2/3 | 2/6 | 15 | 12 | 8 | 3 | 4 |
| 37 | 68.0 | [The Future of AI](https://bluedot.org/courses/future-of-ai) | BlueDot Impact | 2/3 | 3/6 | 14 | 10 | 7 | 3 | 4 |
| 38 | 67.7 | [AI Whisperer](https://www.usf.edu/innovative-education/usf-microcredentials/a-microcourse-in-crafting-prompts.aspx) | University of South Florida | 2/3 | 2/6 | 14 | 12 | 8 | 3 | 4 |
| 39 | 67.3 | [Demystifying AI, Understanding Risks...](https://www.purdue.edu/online/artificial-intelligence-micro-credentials/) | Purdue University | 2/3 | 4/6 | 9 | 12 | 8 | 2 | 3 |
| 40 | 67.0 | [It's Not Just Business](https://www.turing.ac.uk/courses/its-not-just-business-ai-risks-rewards-and-responsibilities) | The Alan Turing Institute | 2/3 | 3/6 | 14 | 10 | 8 | 2 | 3 |
| 41 | 67.0 | [Trustworthy AI: Managing Bias, Ethics, Accountability](https://www.coursera.org/learn/responsible-ai-and-ethics) | Johns Hopkins | 2/3 | 3/6 | 12 | 10 | 8 | 3 | 4 |
| 42 | 66.0 | [Generative AI: Governance, Policy, Emerging Regulation](https://www.coursera.org/learn/generative-ai-governance-policy-and-emerging-regulation) | University of Michigan | 2/3 | 3/6 | 12 | 9 | 9 | 3 | 3 |
| 43 | 64.3 | [Current Issues in Ethics and AI](https://www.coursera.org/learn/current-issues-in-ethics-and-ai) | CU Boulder | 2/3 | 4/6 | 6 | 10 | 9 | 2 | 4 |
| 44 | 64.0 | [AGI Strategy](https://bluedot.org/courses/agi-strategy) | BlueDot Impact | 2/3 | 3/6 | 12 | 9 | 7 | 2 | 4 |
| 45 | 61.7 | [Introduction to Generative AI (BUSAI X001)](https://reg-continuinged.osu.edu/search/publicCourseSearchDetails.do?method=load&courseId=1260877) | Ohio State | 2/3 | 2/6 | 10 | 11 | 8 | 2 | 4 |
| 46 | 56.0 | [Foundation Models and Generative AI (6.S087)](https://ocw.mit.edu/courses/6-s087-foundation-models-and-generative-ai-january-iap-2024/) | MIT OCW | 1/3 | 3/6 | 14 | 10 | 7 | 2 | 3 |

## 3. 分析

### 第 1 梯队 —— 核心推荐（第 1–7 名，得分 ≥ 91）

每门第 1 梯队课程都满足全部三个目标，免费（或可免费旁听），且七门中有五门是专为政府受众打造的。这就是联邦 AI 101 培养路径的候选清单：

- **Harvard Kennedy School — The Science and Implications of GenAI (#1)** 是最完整的一门：覆盖全部六个内容领域，三位点名的 HKS 教授，面向公共部门的定位，完全开放的 CC-BY 存档。它唯一的短板——没有证书、没有班级、2024 年的版本——已计入分数（质量 3，时效 3）。
- **Stanford HAI — AI Fundamentals for Public Servants (#2)** 在覆盖度上与之相当；排名靠后是因为讲师未点名，以及 Apolitical 的账号限制。
- **InnovateUS 三门课 (#3–5)** 是实操主干：免费并含证书，每六个月更新一次，已在多个州（NJ、NY、GA、DC）强制推行，并且是唯一直接面向政府人员讲授 NIST AI RMF 的免费课程。
- **Oxford/UNESCO (#6)** 是国际覆盖最广的公务员课程（3 万学习者、192 个国家）；因没有点名的首席教授而略被扣分。
- **UIUC (#7)** 是最好的*通用受众*大学导论课：唯一一门既覆盖全部六个 C 领域、又满足全部三个目标且可免费旁听的非政府专项课程。

### 第 2 梯队 —— 有力补充（第 8–16 名，80–90 分）

覆盖面广的通识课（Oxford 专项课程 #8、U-M #10、UNF #11、UMD #9——最后一项为转岗的联邦雇员打造），外加各方向最佳的专项支点：Oxford AI Governance (#13) 覆盖 C5，Vanderbilt Cyber & Privacy (#14) 覆盖合成媒体/安全风险，SCSP (#16) 覆盖国土安全与国家安全趋势（C6），TU Delft (#15) 覆盖比较监管。这些课程可以补齐任何第 1 梯队选择留下的空白。

### 第 3 梯队 —— 实用的专项课程（第 17–35 名，69–79 分）

质量可靠但受限：范围小众（KCL 国家安全、CAIS 安全、Glasgow 伦理、Purdue 政策）、领域定位（Wharton/Glasgow 教育、Emory 营销）、节奏偏快（MIT MAS.S60）、付费墙（Wharton、AI Awakening——仅限 Coursera Plus）或访问摩擦（CAIS/HRBA 批次制）。可按岗位作为选修课使用。

### 第 4 梯队 —— 就此目标而言边际（第 36–46 名，< 69 分）

这些课程本身并不弱，只是*契合度*弱：入门级的微缩课程（GenAI 101、AI Whisperer、OSU）、默认你已有基础铺垫的治理补充课（U-M Hickok、JHU、ATIH）、受 Coursera Plus 付费墙限制的 CU Boulder、需要申请才能参加的 AGI Strategy，以及 MIT 6.S087 (#46)——它是极好的 C1 材料，但只满足一个目标且完全没有 O2/O3 内容。

### 跨领域的观察

1. 专为政府打造的课程占据主导：前 7 名中有 6 门。差距分析（gap-analysis）环节贡献了前 7 名中的 2 门（#1、#2）和前 16 名中的 5 门——它实质性地改变了排名的头部，印证了这次修订的价值。
2. 目标 O3（治理/公民权利）是真正的分水岭：46 门中有 18 门未覆盖它，而排名 17 名之后且未覆盖 O3 的课程没有一门能突破 78 分。O1+O2 近乎标配；O3 的覆盖稀缺，且大多集中在政府专项与治理专项课程中。
3. Coursera Plus 付费墙实实在在地拉低了排名：Wharton (#17)、AI Awakening (#28) 和 CU Boulder (#43) 相比内容相近但可免费旁听的同类课程，各损失约 6–8 分。
4. 没有任何单一课程能把所有内容都讲好；下面的学习路径优于任何单个选择。

### 推荐学习路径（联邦 AI 101）

1. 基础（任选其一）：HKS #1（最丰富）或 InnovateUS Public Professionals #5（最短且有证书）或 UIUC #7（最系统）
2. 政府应用：Oxford/UNESCO #6 或 Stanford #2
3. 风险与治理：InnovateUS Public Organizations #4（NIST AI RMF）+ Oxford AI Governance #13
4. 趋势/安全选修：SCSP #16（国家安全）或 Vanderbilt #14（合成媒体/隐私）

## 4. 逐门课程的评分理由

1. HKS Science & Implications of GenAI —— 免费 CC-BY 存档，无证书；专为公共部门管理者打造；3 位点名的 HKS 教授；无外部评分。
2. Stanford AI Fundamentals for Public Servants —— 免费；专门打造（账号限制与受众相符，−1）；Stanford HAI 师资未点名；1.7k 政府学习者。
3. InnovateUS Legal Professionals —— 免费含证书 + CLE；面向政府但限定法律岗位；Noveck + 总检察长协会（AG-association）触达面。
4. InnovateUS Public Organizations —— 免费含证书；面向政府机构层面，含 NIST AI RMF；Noveck。
5. InnovateUS Public Professionals —— 免费含证书；专为公共部门打造；NJ/NY/GA/DC 全州强制采用。
6. Oxford/UNESCO Gov —— 免费含证书；专为公务员打造；师资团队未点名；30k / 192 个国家。
7. UIUC Intro to AI —— 可免费旁听；覆盖全部六个 C 领域的通用导论；Brunner；17.5k，4.7/5。
8. Oxford AI Foundations spec —— 可免费旁听；通用商务 AI-101；Holweg；21k+，4.8/5。
9. UMD AICE —— 免费含证书；为转岗的联邦雇员打造；Padmanabhan + 11 位师资；37k。
10. U-M AI Literacy spec —— 可免费旁听；通用 AI-101；师资团队未点名；4.7/539。
11. UNF AI for Work and Life —— 免费旁听（证书 $249）；明确按 AI-101 设计；新课，尚无信号。
12. Universiti Malaya —— 免费档 / $109；通用 AI-101；UM AI 系师资；报名人数少。
13. Oxford AI Governance —— 可免费旁听；面向普通职场人士的治理；Holweg；12k，4.8/5。
14. Vanderbilt Cyber & Privacy —— 可免费旁听；安全垂直方向、面向管理者；White；4.8/5。
15. TU Delft EU AI Act —— 可免费旁听（证书 $140）；面向美国受众的欧盟专项；全新上线。
16. SCSP AI in National Security —— 免费；专为联邦/国家安全打造；NSCAI 接班人式的实务专家（非教授）；6.9k，4.6/5；未覆盖 O2。
17. Wharton AI in Education —— 仅限 Coursera Plus；面向教育者；Mollick；4.8/303。
18. Bristol Unleash Your Potential —— 免费；通用导论；Bullock；太新，尚无信号。
19. Acadia Intro to AI Literacy —— 免费含证书；O2 角度较强；2 周内 5k 人；未覆盖 O3。
20. Glasgow AI Ethics, Inclusion & Society —— 免费档；伦理优先，O1 偏弱；学生共同创作（信号不一）。
21. Georgia Tech Foundations of GenAI —— 可免费旁听（证书 $90）；通用导论；Joyner；信号一般。
22. MIT MAS.S60 —— 免费 OCW；研究生节奏 + 研究环节；Liang。
23. GVSU AI Literacy for Life & Work —— 免费；通用；由院长牵头；全新上线。
24. Emory Marketing —— 可免费旁听；营销领域范围；Schweidel。
25. Leeds AI Fundamentals —— 免费 + 免费证书；通用导论；Wilson。
26. Glasgow GenAI in Education —— 免费报名；教育领域；9.5k，4.6/5。
27. KCL AI in National Security —— 可免费旁听（证书 $249）；国家安全垂直方向；Payne。
28. Stanford AI Awakening —— 仅限 Coursera Plus；经济/劳动力视角；Brynjolfsson；12k，4.7/5。
29. CAIS AI Safety, Ethics, and Society —— 免费但需申请批次（−2）；安全方向；Hendrycks + 配套教材。
30. Duke Intro to GenAI —— 可免费旁听；治理内容偏薄；Gift/Deza；30k，4.5/5。
31. AI, Justice and Rule of Law —— 免费；司法领域范围；Cofone；全新上线。
32. HRBA to AI —— 免费但 2025 版本已封闭（−2）；人权领域；QUB/DIHR/RWI。
33. Purdue AI Policy and Governance —— $99；面向政策制定者的治理；Schiff（GRAIL）。
34. Vanderbilt Agentic AI —— 可免费旁听；仅限智能体方向；White；118k，4.7/5。
35. ATIH Responsible AI Foundations —— 免费；面向治理实务者；Cummings（UVA）。
36. IU Kelley GenAI 101 —— 免费含徽章；通用职场技能，但仅覆盖 2/6 内容领域。
37. BlueDot Future of AI —— 免费含证书；2 小时的趋势/安全范围；团队主导。
38. USF AI Whisperer —— 免费（徽章 $39）；提示词范围较窄，是不错的入门台阶。
39. Purdue Demystifying AI —— $99；通用非技术向，含风险内容；ABET 认可系列。
40. Turing It's Not Just Business —— 免费 CC-BY；商业责任垂直方向。
41. JHU Trustworthy AI —— 可免费旁听；带中级标签的前提说明；McCulloh。
42. U-M GenAI Governance/Policy/Regulation —— 可免费旁听；治理专项 + 中级标签；Hickok。
43. CU Boulder Current Issues in Ethics and AI —— 仅限 Coursera Plus；以伦理/风险为核心；Schnabel。
44. BlueDot AGI Strategy —— 免费/凭券（PWYW）但需申请批次（−2）；AGI 战略垂直方向。
45. OSU Intro to GenAI —— $49；非技术向但仅覆盖 2/6 内容领域；新课。
46. MIT 6.S087 —— 免费，无证书；C1 深入但只满足 O1；研究者主导，而非教授。

## 5. 敏感性与局限性

- **权重敏感性。** 头部梯队是稳健的：七门第 1 梯队课程在目标权重与内容权重之间 ±10 分的浮动下仍占据前七位，因为它们在*两方面*都领先。并列时的次序（#2 与 #3、#4 与 #5）会因机构/质量的细微变化而翻转，不应过度解读。
- **如果要求必须有证书**，HKS (#1)、Stanford Awakening 以及 MIT 的条目会被剔除 —— 改用 InnovateUS 三门课、Oxford/UNESCO、UMD 和 UNF（旁听路径拿不到证书）。
- **如果要求只接受美国机构**，去掉 Oxford（与 ×3 相关）、Universiti Malaya、Glasgow、Bristol、Leeds、Acadia、TU Delft、KCL、Turing、Global Campus —— 第 1 梯队仍保留 HKS、Stanford、InnovateUS ×3 和 UIUC。
- **主观分项**（契合度、机构、质量）为人工评定；每一项都附有书面理由（第 4 节），因此任何有争议的分数都可以修正，并以机械方式重算综合得分。
- **时点数据。** Coursera 旁听可用性（三处仅限 Plus 的发现）、UNF 的免费证书窗口以及批次日程（CAIS、HRBA、BlueDot）变动频繁；分数反映的是 2026 年 7 月的 QA 核查结果。
- **C/O 标记是二元的。** 一门“涉及”C4 的课程与一门“以 C4 为核心”的课程得分相同；受众契合度分项可以部分弥补这一点，但按深度加权的标记将是自然的下一步改进方向。

---



## 易混考点


### NCP-AAI 备考：智能体 AI 7 个高频易混考点


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-aai/notes/01-exam-focus-guide.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-aai/notes/01-exam-focus-guide.md) · 语言：中文原文



# NCP-AAI 备考：智能体 AI 7 个高频易混考点

> ⚠️ 本文基于官方考纲整理，仅覆盖高频易混考点，**不能替代完整考试大纲**。

## 考点 1：四阶段智能体循环

| 阶段 | 发生什么 | 常见混淆 |
|---|---|---|
| **感知** | 摄取输入/观察（查询、工具输出、环境状态） | 易与行动混淆 |
| **推理** | 基于当前状态和目标决定下一步 | 易与反思混淆 |
| **行动** | 执行工具调用或产出输出 | — |
| **反思** | 评估动作与目标差距；修正方法 | 易与推理混淆 |

**考试要点**：推理是"决定做什么"，反思是"评估做得怎样"。两者不同！

## 考点 2：控制模式选择指南

| 模式 | 最适用 | 考试触发语 |
|---|---|---|
| **ReAct** | 下一步依赖实时结果 | "结果决定下一动作"、"先查 X 再决定" |
| **Plan-and-execute** | 步骤已知、可预测 | "理解透彻的工作流"、"步骤事先已知" |
| **CoT** | 单一线性推理 | 默认推理，无分支 |
| **ToT** | 需探索多个候选解 | "探索多种方法"、"比较备选" |

## 考点 3：单智能体 vs 多智能体决策

| 信号 | 选择 |
|---|---|
| 范围窄、工具少、一个知识库 | **单智能体** |
| 需要并行工作的不同专门角色 | **多智能体** |
| 冲突子目标需协商 | **多智能体** |
| 上下文/工具集超出单窗口 | **多智能体** |

## 考点 4：确定性边界 vs 自主区

| 概念 | 说明 | 考试触发语 |
|---|---|---|
| **确定性边界** | 特定高风险动作的硬编码门限（人工审批、白名单） | "X 之前必须获得审批" |
| **自主区** | 智能体无需门限即可执行的动作 | 内部消息、只读查询 |

**考试要点**：确定性边界仅限定**特定动作**，不意味着完全丧失自主性。

## 考点 5：系统提示设计铁律

1. 显式陈述安全和工具使用约束
2. 让约束**优先于**角色/语气指令
3. 角色塑造语气/风格，绝不能允许它覆盖硬性规则

**考试陷阱**：安全约束必须放在 prompt 前面，不能埋在背景故事之后。

## 考点 6：自反思风险 —— 无限循环

无界自反思可能导致：
- 无限循环
- 浪费延迟/成本
- 无质量保证

**修复方法**：限制迭代次数（较小的固定值）或使用显式的收敛/质量检查。

## 考点 7：快速决策清单

```
下一步依赖实时结果？ → ReAct
步骤完全事先已知？ → Plan-and-execute
需探索/比较多路径？ → ToT
任务窄 + 工具少？ → 单智能体
高风险动作？ → 加确定性审批门
```

---

## 速记总表

| 一句话考点 | 答案 |
|---|---|
| 推理 vs 反思？ | 推理 = 决定做什么；反思 = 评估做得怎样 |
| 实时依赖？ | **ReAct** |
| 步骤已知？ | **Plan-and-execute** |
| 高风险动作？ | **确定性审批门** |
| 安全约束放哪里？ | prompt **最前面** |
| 自反思无界风险？ | **无限循环** |
| 工具少+范围窄？ | **单智能体** |

---

> 📌 **完整速查表 + 知识卡片 + 模拟卷**：关注公众号「JunzeXuInfra」回复「NCP-AAI」领取 PDF 全家桶。

---



## 笔记


### 复杂度类别与相关章节


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `complexityCategories.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/complexityCategories.md) · 语言：英文原文 · 中译版



# 复杂度类别与相关章节

本文件把各章节映射到用于评估任意 Agentic AI 项目复杂度的类别

## 感知（Perception, Perc）

- 第 1.4 章：感知系统、多模态输入处理、时间同步
- 第 1.7A 章：实体识别、从非结构化文本中抽取关系
- 第 2.7 章：多模态 RAG 架构（视觉、音频、文本融合）
- 第 1.1B 章：可感知性——面向多样化输入需求的无障碍设计

感知涵盖智能体如何感知、获取并预处理来自环境的输入。这包括所处理的输入模态类型（文本、图像、音频、文档、传感器数据）、信号的质量与复杂度、实时处理要求，以及将原始输入转换为结构化、可执行表示的流水线的复杂程度。

## 记忆（Memory, Mem）

- 第 1.4 章：短期记忆、长期记忆、记忆管理、情景性/语义性/程序性分层
- 第 1.5A/1.5B 章：有状态编排中的状态管理
- 第 1.6 章：状态无限增长的陷阱、通向高级规划与记忆系统的构建
- 第 1.7A/1.7B 章：知识图谱作为结构化长期记忆；混合 RAG+KG
- 第 1.8 章：分布式缓存（Redis）、多层缓存、缓存失效
- 第 2.2 章：LangGraph 检查点——持久化状态、时间旅行调试
- 第 2.3 章：对话记忆（ConversationBufferMemory）、多轮会话状态
- 第 2.7 章：用于 RAG 检索的基于时间索引的音频分块（情景记忆模式）

记忆涵盖智能体如何跨时间、跨交互地存储、检索和管理信息。这包括短期工作上下文（会话内）、长期持久知识（跨会话）、过去事件的情景记录、语义知识库、程序性习得行为，以及任何用于维持一致性、防止数据陈旧、防范损坏的机制。

## 编排（Orchestration, Orch）

- 第 1.2 章：ReAct、Plan-and-Execute、Reflection 模式；工具使用架构
- 第 1.3 章：多智能体协作范式、通信机制、编排与控制模式、反模式
- 第 1.5A/1.5B 章：有状态编排——核心概念、逻辑树、故障恢复
- 第 1.6 章：编排陷阱（无状态误区、无限循环、并行化）
- 第 1.7B 章：混合架构模式；基于查询复杂度的路由
- 第 1.8 章：自动扩缩容模式、负载均衡、可扩展的智能体架构
- 第 2.1 章：以控制流为差异点的框架架构
- 第 2.2 章：LangGraph 状态图、条件边
- 第 2.3 章：AgentExecutor、智能体类型（零样本、对话式、函数式）
- 第 2.4 章：AutoGen（对话驱动）、CrewAI（基于角色）
- 第 2.5 章：Semantic Kernel —— 由 LLM 驱动的动态插件路由
- 第 2.6 章：工具链式调用、并行执行模式
- 第 2.9 章：流式输出——批处理式交付与渐进式交付的对比

编排涵盖智能体化系统如何协调工作——是靠单个智能体遵循固定流水线、多个专业化智能体协作、动态任务路由、分层的监督者与执行者，还是复杂涌现式多智能体行为。它包括智能体拓扑、控制流、任务分解、冲突消解，以及智能体组合与协调方式中的动态程度。

## 推理（Reasoning, Rsn）

- 第 1.2 章：ReAct（推理轨迹）、Plan-and-Execute（分层分解）、Reflection（自我批判与迭代精化）
- 第 1.3 章：竞争型多智能体——纳什均衡、博弈论式协调；群体智能的涌现
- 第 1.4 章：上下文管理、通过语义锚点进行的跨模态推理
- 第 1.7A 章：通过图遍历实现的多跳推理；知识图谱在何处能实现 RAG 无法实现的推理
- 第 1.7B 章：混合 RAG+KG——查询复杂度作为架构信号；四跳利益冲突遍历
- 第 2.2 章：自我纠错的代码智能体——带验证的迭代推理
- 第 2.3 章：零样本 ReAct、智能体类型及其推理模式
- 第 2.4 章：AutoGen 多智能体推理团队；CrewAI 结构化推理角色
- 第 2.7 章：跨模态 RAG——跨图像、音频与文本的推理

推理涵盖智能体如何处理信息以得出结论、做出决策、生成计划或产出输出。这包括推理链的深度、所需的推理类型（模式匹配、逻辑推断、因果、反事实、概率、博弈论）、规划视野、前提条件中所含的不确定性，以及推理是否需要整合多个异构知识源。

## 工具调用（Tool_calling, Tool）

- 第 1.2 章：工具使用架构——函数调用、工具注册表、工具使用陷阱（过载、安全性、幻觉参数）
- 第 1.3 章：基于 API 的通信（RESTful/gRPC）作为智能体间工具；MCP 作为标准化工具接入方式
- 第 1.7A 章：LangChain GraphCypherQAChain 作为图查询工具；NVIDIA NeMo 作为抽取工具
- 第 2.3 章：OpenAI Functions 智能体（结构化工具调用）、工具描述质量的关键性
- 第 2.4 章：AutoGen/CrewAI 智能体在工作流中调用工具
- 第 2.5 章：Semantic Kernel——语义函数 + 原生函数；由 LLM 执行的动态插件路由
- 第 2.6 章：函数调用深入解析——工具 schema 设计、工具链式调用、并行执行、NVIDIA NIM 集成
- 第 2.8 章：工具失败的错误处理（重试、降级、熔断器）

工具调用涵盖智能体如何调用外部能力——API、数据库、搜索引擎、代码执行环境、外部服务，或智能体内部语言模型之外的任何函数。这包括可用工具的数量与多样性、智能体如何选择工具（确定性选择还是由 LLM 驱动）、工具是否带有副作用、工具链式调用的复杂度，以及工具访问带来的安全/防护方面的影响。

## 集成（Integration, Integ）

- 第 1.3 章：ACP（工作流委派）、A2A（能力发现）、MCP（基础设施接入）——多智能体系统中的协议异构性；基于 API 的通信（REST/gRPC）
- 第 1.4 章：集成挑战——向量存储误区、跨模态集成、时间同步
- 第 1.5B 章：用于低延迟分类的 NVIDIA NIM 集成
- 第 1.7A 章：知识图谱与 LangChain 的集成；NVIDIA NeMo 模型集成
- 第 1.7B 章：把知识图谱接入智能体架构的集成模式；混合合规分析系统
- 第 1.8 章：与有状态编排、知识图谱、UI 的集成；Kubernetes 中的负载均衡
- 第 2.1 章：企业集成——Semantic Kernel 的插件架构
- 第 2.4 章：结合多智能体与单智能体框架的集成模式
- 第 2.5 章：企业 CRM 集成插件；依赖注入架构
- 第 2.6 章：作为集成契约的工具 schema 设计；并行工具执行
- 第 2.7 章：NVIDIA 多模态栈——五层集成；音频/视觉模型集成
- 第 2.8 章：跨 LangChain/LangGraph 的错误处理框架集成
- 第 2.9 章：LangServe 流式集成；SSE 与 WebSocket 的选型

集成涵盖智能体化系统如何与外部系统、数据库、服务及组织边界建立连接、交换数据并保持一致性。这包括外部系统的数量与异构性、涉及的协议与数据格式、一致性与同步要求、对数据流的监管合规约束，以及组织内或跨机构数据治理的复杂度。

## 错误处理（Error_handling, Err）

- 第 1.1A 章：原则 4——错误传递与恢复；工具超时、API 错误、幻觉；渐进式错误披露；优雅降级
- 第 1.1B 章：实时检测智能体错误的监控模式；升级交由人工处理
- 第 1.2 章：ReAct 的局限——错误传播、无限循环脆弱性；Plan-and-Execute——重新规划期间的级联失败；Reflection——收益递减、幻觉强化循环；工具使用陷阱——参数错误、集成脆弱性、提示注入
- 第 1.3 章：常见的协作系统故障（通信歧义 32%、冗余工作 50%、共识失败）；事件驱动——死信队列、幂等性；反模式——缺少故障隔离、缺少熔断器
- 第 1.6 章：无限循环与幻觉循环；无状态误区类错误
- 第 1.7B 章：知识图谱常见陷阱——数据质量、查询性能、维护开销
- 第 1.8 章：健康检查、成本护栏、竞价实例恢复、缓存失效
- 第 2.2 章：LangGraph 自我纠错代码智能体；用于恢复的检查点；"何时不该使用 LangGraph"
- 第 2.3 章：常见陷阱——工具描述质量、记忆累积
- 第 2.8 章：重试逻辑（指数退避 + 抖动）、降级链、优雅降级、熔断器；整章专门讲错误处理与韧性

错误处理涵盖智能体化系统如何检测、分类、响应故障、异常和意外状况，并从中恢复。这包括系统必须处理的错误类型的多样性（瞬时网络错误、永久性 API 错误、语义/幻觉错误、对抗性输入）、检测手段的成熟度（显式错误码 vs. 静默故障检测）、错误传播的范围（局部 vs. 跨智能体级联）、错误未被处理时后果的不可逆性，以及恢复策略的复杂度。

## 韧性（Resilience, Resil）

- 第 1.1B 章：用于监督的实时监控模式；紧急停止能力
- 第 1.2 章：ReAct——无限循环脆弱性、上下文耗尽；Plan-and-Execute——故障下的计划僵化；工具使用——以安全为先的设计，含限流与沙箱
- 第 1.3 章：可扩展性、去中心化与容错；Swarm——7 秒故障恢复；反模式——缺少故障隔离、缺少熔断器、缺少优雅降级；集中式 vs. 去中心化编排的韧性
- 第 1.6 章：状态无限增长 → 内存耗尽；循环检测；与可扩展性的关系
- 第 1.7B 章：生产级知识图谱的优化策略；运维监控与维护；熔断器、时间管理
- 第 1.8 章：自动扩缩容（Kubernetes HPA/VPA/KEDA）、竞价实例恢复、多层缓存、负载均衡、健康检查、成本护栏
- 第 2.2 章：LangGraph 检查点——状态持久化使崩溃后可恢复；时间旅行调试
- 第 2.8 章：优雅降级（核心服务 vs. 辅助服务）、熔断器（3 状态：Closed/Open/Half-Open）、高韧性多工具智能体示例；带指数退避 + 抖动的重试逻辑

韧性涵盖智能体化系统在面对故障、对抗性条件、资源约束、基础设施中断或异常输入模式时，被设计为维持功能（完全能力或降级能力）的程度。这包括冗余设计、优雅降级策略、故障隔离、恢复时间目标、自愈能力，以及系统在恶劣或不确定环境中无需人工干预即可运行的能力。

---


### 各章节测验链接


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `quizzes_ver20JUN26.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/quizzes_ver20JUN26.md) · 语言：英文原文 · 中译版



# 各章节测验链接

版本 20JUN26

分值：简单=1，中等=2，困难=3

任何拥有链接的人都可以参加测验。

| 章节 | 标题 | 题量 | 链接 |
|---------|-------|-----------|------|
| 1.1A | 设计直观的人机智能体交互界面... | 26Q (25R+1CB) | [参加测验](https://docs.google.com/forms/d/1XmM2qiJrFvJCOJXGFM_waJ-fDvNq7DCcjeHDUFo-J7w/viewform?usp=sharing) |
| 1.1B | 人在回路模式与无障碍设计 | 34Q (33R+1CB) | [参加测验](https://docs.google.com/forms/d/1wWQYe9nQOFHfVtHt8wCYysaIp_obXckibGoJgHB9p_Q/viewform?usp=sharing) |
| 1.2 | 核心智能体模式 | 30Q (29R+1CB) | [参加测验](https://docs.google.com/forms/d/1EsIlTzhOYvtV3RahqLJ3q5dW013TjVb0l0RWOu_N-Tg/viewform?usp=sharing) |
| 1.3 | 多智能体系统 | 42Q (40R+2CB) | [参加测验](https://docs.google.com/forms/d/1rGwHje49TRniIhG65hXRgmqXtHmy1xc5dv_zb2VmEMY/viewform?usp=sharing) |
| 1.4 | 记忆与感知系统 | 20Q (19R+1CB) | [参加测验](https://docs.google.com/forms/d/15U_a9_pc7gVkGTCNS-NG9K1sJwQWe5HGBaN6uMJBLVU/viewform?usp=sharing) |
| 1.5A | 有状态编排——入门与核心概念 | 27Q (26R+1CB) | [参加测验](https://docs.google.com/forms/d/109aLl62B5W3Nk4a34dI4fwTlgM6A01saKeAzZuZOtxw/viewform?usp=sharing) |
| 1.5B | 有状态编排——实例讲解 | 27Q (26R+1CB) | [参加测验](https://docs.google.com/forms/d/1jz2PVQHMS6ok1yD45OxRsVI7p8bL9r1IWhEGdicE6pE/viewform?usp=sharing) |
| 1.6 | 有状态编排——陷阱、集成与综... | 24Q (23R+1CB) | [参加测验](https://docs.google.com/forms/d/1Sy889rKbbJmXe6chqXD7gYnqLfgJtOYibvxTtE7PZuE/viewform?usp=sharing) |
| 1.7A | 基于知识图谱的关系推理——基础... | 41Q (39R+2CB) | [参加测验](https://docs.google.com/forms/d/11SNhGX9BGs58nqaICVAv4lmEN6G922_vjOu1DuctXPY/viewform?usp=sharing) |
| 1.7B | 基于知识图谱的关系推理——混合 RAG... | 25Q (24R+1CB) | [参加测验](https://docs.google.com/forms/d/1CjMbpAIwwGx_cse1y0Dh1hmjPZEU43LIDReJBJOTMtM/viewform?usp=sharing) |
| 1.8 | 可扩展性与生产部署 | 27Q (26R+1CB) | [参加测验](https://docs.google.com/forms/d/1uewv4-qyQz16HCz_0D5dUEhkv3wfsYfx9rphANqdBXI/viewform?usp=sharing) |
| 2.1 | 框架生态与选型 | 23Q (22R+1CB) | [参加测验](https://docs.google.com/forms/d/1jj55JTho9uPN2Mu7FwIpfc-mQe-L34q0cHoniRtOuOY/viewform?usp=sharing) |
| 2.2 | LangGraph | 25Q (24R+1CB) | [参加测验](https://docs.google.com/forms/d/1WyguE8MVLqdmWYRCy-0T_ZxX7B_Jcigt2r5jy80pmN0/viewform?usp=sharing) |
| 2.3 | LangChain 顺序式框架 | 23Q (22R+1CB) | [参加测验](https://docs.google.com/forms/d/13Ecjr24F4NqLB131JaVg36h0ExKPQiqkxTlYog6n7PM/viewform?usp=sharing) |
| 2.4 | 多智能体框架 | 33Q (32R+1CB) | [参加测验](https://docs.google.com/forms/d/1BwgT2tdhSe8Yv6NixzTpAbhGT2ksn5JG-10u-uEHUcQ/viewform?usp=sharing) |
| 2.5 | Semantic Kernel：企业级框架与插件架构... | 25Q (24R+1CB) | [参加测验](https://docs.google.com/forms/d/1qbm2AAl0XkPeTWvqInQZog1zRHNMblMmvSgbSQNLIDA/viewform?usp=sharing) |
| 2.6 | 工具集成与函数调用 | 26Q (25R+1CB) | [参加测验](https://docs.google.com/forms/d/1f_7aioG1-xWk0M2bAhihuJJOx9UK2nwaaWsjcevGTek/viewform?usp=sharing) |
| 2.7 | 多模态 RAG 方法 | 43Q (41R+2CB) | [参加测验](https://docs.google.com/forms/d/1yPrLfIsN_xeFWya-hQb0rla3c-A4I0gbbiZy_5wzQ-Y/viewform?usp=sharing) |
| 2.8 | 错误处理与韧性 | 28Q (27R+1CB) | [参加测验](https://docs.google.com/forms/d/1u4hzqjpzM3hRjso7YSN6Ay-j9MCsiCRzO-zFtvTV-MU/viewform?usp=sharing) |
| 2.9 | 流式输出与实时响应 | 27Q (26R+1CB) | [参加测验](https://docs.google.com/forms/d/1EVvuCnVelN44xHeVzolDx1MVwV3AJucqDsPeeHLP5DA/viewform?usp=sharing) |
| 3.1A | 实现评估流水线与任务基准测试 | 36Q (35R+1CB) | [参加测验](https://docs.google.com/forms/d/15iqCaPDaFXuBRjNGR643LmzxtZKWcDTXGI8VmkxYXew/viewform?usp=sharing) |
| 3.1B | 实现评估流水线与任务基准测试（指... | 28Q (27R+1CB) | [参加测验](https://docs.google.com/forms/d/1nyE8Blc4ZgqNV2ZBAD8pJbGBArv-sRDbAVv6oFWldPU/viewform?usp=sharing) |
| 3.1C | 实现评估流水线与任务基准测试（Ind... | 25Q (24R+1CB) | [参加测验](https://docs.google.com/forms/d/1OGa5ulPg3OvKKE6-TO3MfyONhmmn5dVX47TGUKa8EXk/viewform?usp=sharing) |
| 3.2 | 跨任务与数据集比较智能体性能 | 26Q (25R+1CB) | [参加测验](https://docs.google.com/forms/d/1cr_yfhb2zKPgxcGna1rjZUc0FJYGx7n18kLV3T_jPIw/viewform?usp=sharing) |
| 3.3 | 网页导航与交互基准测试 | 31Q (30R+1CB) | [参加测验](https://docs.google.com/forms/d/1KU6D0880znwHkFMab25JXaNJwQdtOt4z-sfaeWAcMN0/viewform?usp=sharing) |
| 3.4 | 调优模型参数以提升生产性能 | 25Q (24R+1CB) | [参加测验](https://docs.google.com/forms/d/1GmJu-NCaKyfixAg4HMtt9ReNxKkMXNDm52FtbIKUL50/viewform?usp=sharing) |
| 3.5 | 提示词优化技术与少样本学习策... | 27Q (26R+1CB) | [参加测验](https://docs.google.com/forms/d/1pVmk3BXqPnhzLGPfGNznt0LDY11gOcGKckXiAdAFCwA/viewform?usp=sharing) |
| 3.6 | 让智能体决策可见 | 28Q (27R+1CB) | [参加测验](https://docs.google.com/forms/d/1B4QIi-ZsCuJkL_DlOHcf5gy4MUhKqcRPwukx_p6yQqw/viewform?usp=sharing) |
| 3.7 | 工具使用审计 | 29Q (28R+1CB) | [参加测验](https://docs.google.com/forms/d/1TetLG6Fo7CnUyRHhjF5Ugbf0uCovGp0vCV23CZui-JA/viewform?usp=sharing) |
| 3.8 | 动作准确率指标 | 38Q (37R+1CB) | [参加测验](https://docs.google.com/forms/d/1lRlcnCStFuREtPdHk6b9Qxu69WKoglcrEKExiKIRlcQ/viewform?usp=sharing) |
| 3.9 | 推理质量 | 40Q (38R+2CB) | [参加测验](https://docs.google.com/forms/d/162oqrBfqthRmZNyU-74dOVIQr2KQ62ISMkS8dkMsfvw/viewform?usp=sharing) |
| 3.10 | 效率指标——平衡性能、成本与... | 42Q (40R+2CB) | [参加测验](https://docs.google.com/forms/d/1iZ1MjXJ_OPXboW9LVd-zzCzIh1y2ySzFZP1azKCdCCs/viewform?usp=sharing) |
| 4.1A | 面向 AI 智能体部署的微服务架构 | 27Q (26R+1CB) | [参加测验](https://docs.google.com/forms/d/1if2c8Qu-gzjVf7NkPtEV6hPmgCpQcGauEoaFp-zCoGs/viewform?usp=sharing) |
| 4.1B | 面向多智能体 AI 系统的 Kubernetes 编排 | 30Q (29R+1CB) | [参加测验](https://docs.google.com/forms/d/1AGZ2H6dIePFVzdv0nsS_wM0x6BjH6UhC8IdAh-Sp49A/viewform?usp=sharing) |
| 4.2A | NVIDIA NIM 与 Triton Inference Server | 42Q (40R+2CB) | [参加测验](https://docs.google.com/forms/d/11ATH7FGMjGK3nsRBhiFstDhmLZViqxrvPW1VM0ax5pc/viewform?usp=sharing) |
| 4.2B | TensorRT-LLM 与 NVIDIA Fleet Command | 40Q (38R+2CB) | [参加测验](https://docs.google.com/forms/d/1qPHp0ZxKB6ect5Of58tSlLwGGqSzQ7109LZ7jwCp-uE/viewform?usp=sharing) |
| 4.3 | 容器编排与边缘部署 | 31Q (30R+1CB) | [参加测验](https://docs.google.com/forms/d/1zf3fb2qlxLbs6Z6ARpbrcUdp-T5OE6hmEP9wMZC3bjw/viewform?usp=sharing) |
| 4.4 | 面向多智能体系统的生产基础设施 | 30Q (29R+1CB) | [参加测验](https://docs.google.com/forms/d/18t4_B1hDnAcH23xHZcoQxMI_C4GXx0gI5ST-SYdmFxs/viewform?usp=sharing) |
| 4.5 | NVIDIA NIM 与 Triton Inference Server | 26Q (25R+1CB) | [参加测验](https://docs.google.com/forms/d/1Z1xLfMAdzT0IJibUl0cGqfRD7Hh1Pb2CY2SCUcGJL6Q/viewform?usp=sharing) |
| 4.6 | TensorRT-LLM 与 NVIDIA Fleet Command | 29Q (28R+1CB) | [参加测验](https://docs.google.com/forms/d/1ak-7FD_KYAcAfbrWxUm_y2n3pyBXM0vvrnu5ZjYEkVE/viewform?usp=sharing) |
| 5.1 | 思维链（CoT）基础与集成 | 25Q (24R+1CB) | [参加测验](https://docs.google.com/forms/d/1z75RzeMlZKVckMfWuAszUoCAssGs2vqfq-YRncf2HHI/viewform?usp=sharing) |
| 5.2 | 思维树（ToT）基础与思维图... | 28Q (27R+1CB) | [参加测验](https://docs.google.com/forms/d/1hhvV97gVvKuxCSQ8f7Vhm7ipGrSf0nDeEvqUTzz4ciw/viewform?usp=sharing) |
| 5.3 | 自洽性基础 | 55Q (53R+2CB) | [参加测验](https://docs.google.com/forms/d/1sJG1qC1wUFkDaXt_3uLY3ulJXGTi34y4qi4NUq2q5bs/viewform?usp=sharing) |
| 5.4 | 分层规划基础与 HTN 形式化 | 28Q (27R+1CB) | [参加测验](https://docs.google.com/forms/d/1-ZY4GaQaWejGOa6TtuA1f6Msm9xLSKTII4ojrn_08Sw/viewform?usp=sharing) |
| 5.5 | 蒙特卡洛树搜索基础 | 33Q (32R+1CB) | [参加测验](https://docs.google.com/forms/d/1qDmgPgrrIKZoSTESd9Z-riUAac3kUkrLe1HdgSHUpa8/viewform?usp=sharing) |
| 5.6 | A* 搜索基础与实现 | 24Q (23R+1CB) | [参加测验](https://docs.google.com/forms/d/1yWaTgJIJcToZNaG58nq5HAokSfIMvrysr26tuN5xMSM/viewform?usp=sharing) |
| 5.8 | 语义记忆 | 33Q (32R+1CB) | [参加测验](https://docs.google.com/forms/d/1druUvn3qBIZn4A3O29sJpwO9PGEbH-2qC7zBv3muSk4/viewform?usp=sharing) |
| 5.9 | 工作记忆 | 29Q (28R+1CB) | [参加测验](https://docs.google.com/forms/d/1TyXSfcoxGHCr9QKNZ8OrYnKs14FBPtvoj_H_3SVdSyc/viewform?usp=sharing) |
| 5.10 | 基于效用决策基础 | 32Q (31R+1CB) | [参加测验](https://docs.google.com/forms/d/1bT6_8qN2j1GOUOGmtVgIVijEU7FWlbsc6_j5njKPfV8/viewform?usp=sharing) |
| 5.11 | 程序性记忆 | 26Q (25R+1CB) | [参加测验](https://docs.google.com/forms/d/1KLpFNjHOLGceEqyvbdXwj0lTVEiISK4Jon2uGrdd70g/viewform?usp=sharing) |
| 5.12 | 基于学习的决策基础 | 32Q (31R+1CB) | [参加测验](https://docs.google.com/forms/d/166c1B5zKyF6D_qePjAhlGh_YOAr_5e-74QxhhfVY-FA/viewform?usp=sharing) |
| 5.13 | 混合决策系统基础 | 38Q (37R+1CB) | [参加测验](https://docs.google.com/forms/d/1xyjiUDrzOfxbeixSAX08jC7rNL4HW99guwzyJDwuDSw/viewform?usp=sharing) |
| 5.14 | 基于学习的决策基础 | 28Q (27R+1CB) | [参加测验](https://docs.google.com/forms/d/1_cjJJEJgZBdIJdg-r2hIMqL7rDm9SEPWbxG3ojjCF1k/viewform?usp=sharing) |
| 5.15 | 混合决策系统基础 | 28Q (27R+1CB) | [参加测验](https://docs.google.com/forms/d/1-419Q5jTfru_79bt5TNuJpIFFmi-oZV_5qi_jzTTRDQ/viewform?usp=sharing) |
| 6.1 | 嵌入与 RAG 基础 | 72Q (69R+3CB) | [参加测验](https://docs.google.com/forms/d/1r3KyikJNqmj9EbsRjVmHk4SfZj5f74r3zKqOrEv3qF4/viewform?usp=sharing) |
| 6.2 | 向量数据库与相似度检索 | 67Q (64R+3CB) | [参加测验](https://docs.google.com/forms/d/1UJ1NjmCoN-R-qoCuPvvOWKeVFsdFLHElOLrxZ71LjV4/viewform?usp=sharing) |
| 6.3 | 构建 ETL 流水线以集成企业数据源... | 69Q (66R+3CB) | [参加测验](https://docs.google.com/forms/d/1W5uMtpzZbw_qfnl8aEibw2wlXsYV_CgczTUuPd2es34/viewform?usp=sharing) |
| 6.3C | ETL 实践、陷阱与资源 | 26Q (25R+1CB) | [参加测验](https://docs.google.com/forms/d/1HrfRMbzMQhgN1u_pEwAuUJ6II7e3OqY9iAUtyQpUIaY/viewform?usp=sharing) |
| 6.4 | 数据质量基础 | 60Q (57R+3CB) | [参加测验](https://docs.google.com/forms/d/1Yi5tTzZ56WYnOcHdVFO7Sgoyq1v_hh-n_iPK8QBz6iE/viewform?usp=sharing) |
| 6.5 | 生产级 RAG 系统 | 72Q (69R+3CB) | [参加测验](https://docs.google.com/forms/d/1mmle4Qng1tZMNURnsk90Gk_S-QT73P5eNnnthxY6qkE/viewform?usp=sharing) |
| 6.6 | 查询分解与自适应检索 | 64Q (64R+0CB) | [参加测验](https://docs.google.com/forms/d/1P99z62qsSnUuFiNeBoFhnDvm8ltVKBlnfMJU_eP-X4Q/viewform?usp=sharing) |
| 6.7 | 章节总结与综合 | 25Q (24R+1CB) | [参加测验](https://docs.google.com/forms/d/1kpdJP7Ibf3ciyYCQCJR3VzkY7N5tRibEdmyZlea8byo/viewform?usp=sharing) |
| 6.9B | 高级代码审查与应用题 | 35Q (34R+1CB) | [参加测验](https://docs.google.com/forms/d/1jkKJLEQqZnj-yCGJ7Gqe5OBwcmB_RF5EF8R2iB37JKk/viewform?usp=sharing) |
| 7.1A | NeMo 框架与六种 Rail 类型 | 26Q (25R+1CB) | [参加测验](https://docs.google.com/forms/d/1Fsc3F4S7qD_OVVNs-4r81DxzBNxef4b5KC2epFcQG_w/viewform?usp=sharing) |
| 7.1B | NVIDIA NIM 与 Colang | 25Q (24R+1CB) | [参加测验](https://docs.google.com/forms/d/1uFE6RZ9JRYVYVj-VQRiH_WME_1-vxC0Ee5-7fBape2M/viewform?usp=sharing) |
| 7.2A | 性能优化与生产监控——低... | 30Q (29R+1CB) | [参加测验](https://docs.google.com/forms/d/1U7d-6ReqiEqv3FqTsLwFAcI2XYEEdZaiwqmFSeQ18WE/viewform?usp=sharing) |
| 7.2B | 性能优化与生产监控 | 47Q (45R+2CB) | [参加测验](https://docs.google.com/forms/d/1u3x4JpR3MpV09bIVEDzXbXITqN_zKTGLJsC6V-Ne3N8/viewform?usp=sharing) |
| 7.3 | NeMo Agent Toolkit 性能剖析 | 26Q (25R+1CB) | [参加测验](https://docs.google.com/forms/d/1jRjKy9SG-CMOxUioHbsGR-OIXs3THpYzTqIU4ysVsMc/viewform?usp=sharing) |
| 7.4 | TensorRT-LLM 基础与量化 | 24Q (23R+1CB) | [参加测验](https://docs.google.com/forms/d/124BZB8in0oItPq4bJrRGv_WKock3WT_C7TEUd2cW0aY/viewform?usp=sharing) |
| 7.5 | NeMo Curator、Riva Speech AI 与多模态集成 | 49Q (47R+2CB) | [参加测验](https://docs.google.com/forms/d/1YvOLAjPOx0F-Rb44z6UwjSzxQiFSXuWdOrEfUDpPDW4/viewform?usp=sharing) |
| 7.6 | Multi-Instance GPU | 29Q (28R+1CB) | [参加测验](https://docs.google.com/forms/d/1io2Z9tCSlSIAPDXIdrVC1KsGJL3nA_5S_aLxCKj0M7s/viewform?usp=sharing) |
| 8.1 | 延迟指标 | 40Q (38R+2CB) | [参加测验](https://docs.google.com/forms/d/1c2DlRZhVBJvfB5OskMtG6lyOm9PSkcQl-nzg3u3LR4s/viewform?usp=sharing) |
| 8.2A | 错误分类法与 SLO 管理 | 26Q (25R+1CB) | [参加测验](https://docs.google.com/forms/d/13HhhUa2efm3tWRd5X6l3P1m7ht128IRee5R1C6IF7EI/viewform?usp=sharing) |
| 8.2B | NeMo Guardrails 集成 | 26Q (25R+1CB) | [参加测验](https://docs.google.com/forms/d/1fqOZUSK7ZEDr6V_4x7RmpumvkJyGD3DAhLeAvwglA6M/viewform?usp=sharing) |
| 8.3 | Token 经济性与架构 | 24Q (23R+1CB) | [参加测验](https://docs.google.com/forms/d/1BbZ7sbP0Fh_-NhvEvA0I9bL1gfLweEND5v9zLR8GJ_k/viewform?usp=sharing) |
| 8.4 | 成功指标与多维度度量 | 30Q (29R+1CB) | [参加测验](https://docs.google.com/forms/d/1xbI_UW3aLlDWQcQSJZ12GTkAz78PP0rMUouJLDfPIdU/viewform?usp=sharing) |
| 9.1 | 输出过滤与内容审核 | 32Q (31R+1CB) | [参加测验](https://docs.google.com/forms/d/1EljVTn1taC7T7mVsUz-NZKmLbf2E-Xp2e229yQTGl_w/viewform?usp=sharing) |
| 9.2 | 动作约束与权限模型 | 30Q (29R+1CB) | [参加测验](https://docs.google.com/forms/d/1q3QaLjLhBIFW4GDBWRdBICCz0RZl3wD6ZpjJLa74fkA/viewform?usp=sharing) |
| 9.3 | 沙箱与透明性基础 | 32Q (31R+1CB) | [参加测验](https://docs.google.com/forms/d/1VorINUF8J5w44kFKSzgEVaifGmX_ojvpW1ixHJkRKYo/viewform?usp=sharing) |
| 9.4 | 公平性与偏见缓解 | 32Q (32R+0CB) | [参加测验](https://docs.google.com/forms/d/17VfqM5o4CrRf0vXk-U9bWLZShS9LjnwXFQ3kypRScLo/viewform?usp=sharing) |
| 9.6A | 价值对齐框架（第一部分） | 24Q (23R+1CB) | [参加测验](https://docs.google.com/forms/d/1xjlhouAvPDHauiEAwRAk8a9F1YT-cJQ9qm_MAx6C90U/viewform?usp=sharing) |
| 9.6B | 价值对齐框架 | 32Q (32R+0CB) | [参加测验](https://docs.google.com/forms/d/1B5Nbm47QfdMqigaHZmTozYCgWTpcYwNs-0vJdRB8kpY/viewform?usp=sharing) |
| 9.7 | GDPR 与数据保护法规 | 30Q (29R+1CB) | [参加测验](https://docs.google.com/forms/d/1gtKkdyx3YcR8YOGC0ynEa0u7CdtC5A7eKC0tEzMnYhw/viewform?usp=sharing) |
| 9.8A | AI 治理的标准与框架 | 28Q (28R+0CB) | [参加测验](https://docs.google.com/forms/d/1bPR68UU_JtvSwapv2E6Trx85-0hxGHSqY0qm6u_UtMo/viewform?usp=sharing) |
| 9.8B | AI 治理的标准与框架 | 31Q (30R+1CB) | [参加测验](https://docs.google.com/forms/d/1OtUhvSYGqS6OiqH482WVkBjHTIu1rB1GJepYdzShctU/viewform?usp=sharing) |
| 9.9 | 价值对齐框架——构建真正理... | 32Q (31R+1CB) | [参加测验](https://docs.google.com/forms/d/1DOU4bbC2gaGPaj_CcgJIVKN_GWgn8CbqFxwMSZjSagI/viewform?usp=sharing) |
| 9.10 | GDPR 合规实践 | 28Q (27R+1CB) | [参加测验](https://docs.google.com/forms/d/1tr0N4p4yhnkWNoeIjY7ZwoQb4FT0h4UcpHEux51VgzE/viewform?usp=sharing) |
| 9.11 | AI 治理的标准与框架 | 32Q (31R+1CB) | [参加测验](https://docs.google.com/forms/d/1BZcNzB1DmOXwD3Aha0gKJalo2aNpLQoqrubV-dwZceQ/viewform?usp=sharing) |
| 9.16 | 章节总结与综合 | 48Q (46R+2CB) | [参加测验](https://docs.google.com/forms/d/1CPD-5S2dZGOYomwbzXhcrSc-dDpuBoHTXkFUjIny3AA/viewform?usp=sharing) |
| 9.17 | 章节总结与综合 | 32Q (31R+1CB) | [参加测验](https://docs.google.com/forms/d/19CQlkouCfWXofAvGk8PS_Wmaj7KnviEaA1kmD4okGrI/viewform?usp=sharing) |
| 10.1 | 对话式 UI | 35Q (34R+1CB) | [参加测验](https://docs.google.com/forms/d/13rN-HUmcylPaElvnlfOfjIFbUKKoY29F5wBykwKGvhY/viewform?usp=sharing) |
| 10.2 | 主动型智能体 | 31Q (30R+1CB) | [参加测验](https://docs.google.com/forms/d/1JfhTZi64odDKNg6bxGdDK6Tzke4LJ6H-l80zreuBmzw/viewform?usp=sharing) |
| 10.3 | RLHF 方法论 | 30Q (30R+0CB) | [参加测验](https://docs.google.com/forms/d/1kfKFluEL-PTpI3MlNeYHK6D6zJ2MF44TFe40gaS-EWA/viewform?usp=sharing) |
| 10.4 | 人在回路 | 30Q (29R+1CB) | [参加测验](https://docs.google.com/forms/d/1S9-1L6ueaO3E7ApGEXekHlKI74rXTce7v-P5TtQn_eI/viewform?usp=sharing) |
| 10.5 | 人在回路之上（Human-over-the-Loop） | 30Q (30R+0CB) | [参加测验](https://docs.google.com/forms/d/1ePcVBWqiyScIys77ZiU0F1OQaGRndloJJIZr30tM80Y/viewform?usp=sharing) |
| 10.6 | 主动学习 | 32Q (31R+1CB) | [参加测验](https://docs.google.com/forms/d/1DqC1GX5b_T6yULuxgc5deJP4HaWGCHJaQdFXw3YfkNg/viewform?usp=sharing) |

---


### 模拟测试链接


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `simulated_tests_ver20JUN26.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/simulated_tests_ver20JUN26.md) · 语言：英文原文 · 中译版



# 模拟测试链接

分值：简单=1，中等=2，困难=3

任何拥有链接的人都可以参加。

| 测试 | 标题 | 题量 | 链接 |
|------|-------|-----------|------|
| 测试 01 | NVIDIA NCP-AAI 模拟测试 1 | 70Q (67R+3CB) | [参加测试](https://docs.google.com/forms/d/1si4qX2qaX09zS7XUmZUcMoRU0LAeVTb-mWdLQwOWiFg/viewform?usp=sharing) |
| 测试 02 | NVIDIA NCP-AAI 模拟测试 2 | 70Q (67R+3CB) | [参加测试](https://docs.google.com/forms/d/10ykAbo8AwlsyFPrKCHx4D8OqNyUIu7dqn09BsOUcCXk/viewform?usp=sharing) |
| 测试 03 | NVIDIA NCP-AAI 模拟测试 3 | 70Q (69R+1CB) | [参加测试](https://docs.google.com/forms/d/1qt9R31-GuWnalv7y9oyKV-SjxLuq9v-OwMU62iFvmX4/viewform?usp=sharing) |
| 测试 04 | NVIDIA NCP-AAI 模拟测试 4 | 70Q (69R+1CB) | [参加测试](https://docs.google.com/forms/d/1EZwxxCVsUieRMRebMa_cMZuHsz0CCXwC6gPhdsxX7P8/viewform?usp=sharing) |
| 测试 05 | NVIDIA NCP-AAI 模拟测试 5 | 70Q (68R+2CB) | [参加测试](https://docs.google.com/forms/d/1nwj-8Oavejn4JVCEGp4xWc-FK0Yqt29x0uRh4Sc-k34/viewform?usp=sharing) |
| 测试 06 | NVIDIA NCP-AAI 模拟测试 6 | 70Q (69R+1CB) | [参加测试](https://docs.google.com/forms/d/18CEVZx6ao0AReKtMlhOG-TKAqwjgS24C1bGejbk3tiM/viewform?usp=sharing) |
| 测试 07 | NVIDIA NCP-AAI 模拟测试 7 | 70Q (68R+2CB) | [参加测试](https://docs.google.com/forms/d/1ZfOAz-jD9WJ3erws1rfvGpJUZKrWEX4I1-bnC_E-OWQ/viewform?usp=sharing) |
| 测试 08 | NVIDIA NCP-AAI 模拟测试 8 | 70Q (68R+2CB) | [参加测试](https://docs.google.com/forms/d/163Wg3lJTOUe0KFJteY3VxgwI3n_XMVmnTcs0Jj4_Cjg/viewform?usp=sharing) |
| 测试 09 | NVIDIA NCP-AAI 模拟测试 9 | 70Q (66R+4CB) | [参加测试](https://docs.google.com/forms/d/1v_6e-0fCNxpmzjJaoXl11sP0tj40_PiAkAVymo_Ngmo/viewform?usp=sharing) |
| 测试 10 | NVIDIA NCP-AAI 模拟测试 10 | 70Q (69R+1CB) | [参加测试](https://docs.google.com/forms/d/1gHKbf7XX8uLbm5rbxtbnsK47onfpHV1dvkg2L7mkBtY/viewform?usp=sharing) |

---


### AI 导师示例提示词


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `ai_tutor/example_prompts.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/ai_tutor/example_prompts.md) · 语言：英文原文 · 中译版



# AI 导师示例提示词

本文件展示如何为每一种辅导场景措写你的开场消息。有效的提示词会告诉导师三件事：你的水平、你想做什么，以及需要遵循哪些约束（只给提示、不给答案等）。

复制并改编这些提示词——把方括号中的占位符替换成你实际的主题、章节或代码片段。

---

## 目录

1. [开始一次会话](#开始一次会话)
2. [获得概念讲解（协议 A）](#获得概念讲解（协议-a）)
3. [打磨定义（协议 B）](#打磨定义（协议-b）)
4. [让导师质疑你的推理（协议 C）](#让导师质疑你的推理（协议-c）)
5. [探讨设计决策（协议 D）](#探讨设计决策（协议-d）)
6. [自我讲解解题过程（协议 E）](#自我讲解解题过程（协议-e）)
7. [学习新的流程（协议 F）](#学习新的流程（协议-f）)
8. [用提示解开卡点（协议 G）](#用提示解开卡点（协议-g）)
9. [用练习提升熟练度（协议 H）](#用练习提升熟练度（协议-h）)
10. [备考（协议 I）](#备考（协议-i）)
11. [复盘一次学习（协议 J）](#复盘一次学习（协议-j）)
12. [完成计分作业（协议 K）](#完成计分作业（协议-k）)
13. [诊断错误答案（协议 M）](#诊断错误答案（协议-m）)
14. [攻克新概念（协议 N）](#攻克新概念（协议-n）)
15. [当你感到卡住或沮丧时（协议 O）](#当你感到卡住或沮丧时（协议-o）)
16. [小组学习（协议 P）](#小组学习（协议-p）)
17. [在一次学习中串联多个协议](#在一次学习中串联多个协议)
18. [常见错误与应避免的做法](#常见错误与应避免的做法)

---

## 开始一次会话

每次开启新的对话时都使用它。填入你的水平和目标，让导师立即校准讲解方式。

```
I am an [beginner / intermediate / advanced] learner working through
"Mastering Agentic AI Systems." Today I want to [study Chapter 1.3 on
multi-agent systems / prepare for the NCP-AAI exam / debug my
understanding of LangGraph / practice with drills on Chapter 2.6].

Please start by asking me what I already know about the topic, then
choose the right teaching approach based on my answers.
```

---

## 获得概念讲解（协议 A）

**场景：** 你在章节中遇到某个术语或概念，想要一个清晰、有据可依的解释，然后再往深处学。

```
I am an intermediate learner on Chapter 1.4 (Memory and Perception Systems).
I just read about episodic memory but I'm not sure how it differs from
semantic memory in the context of agentic systems.

Please explain both terms using the chapter text as your source.
Give me a concrete example of each, then ask me to restate the
difference in my own words. After that, give me one application-level
check question.
```

```
I'm a beginner on Chapter 2.6 (Tool Integration and Function Calling).
What does it mean when the chapter says "LLMs never call functions
directly"? Explain it simply, without heavy notation, with one
example. Then ask me to explain it back to you.
```

---

## 打磨定义（协议 B）

**场景：** 你一直在使用某个术语，却意识到自己无法精确地定义它。在开始解题之前使用这个协议。

```
I want to use Socratic definition mode for the term "orchestration"
as used in Chapter 1.5A. I have a rough sense of what it means but
I cannot give a precise definition.

Ask me what I think it means first. Then ask me questions from
different angles — what it does, how it differs from "coordination,"
when you would use it — and offer examples and non-examples. Only
give me your synthesized definition after I have tried. At the end,
ask me to compare my initial and final definitions.
```

```
I keep confusing "stateless" and "stateful" agents. Use Socratic
definition mode to help me nail down both terms from Chapter 1.5A.
Start by asking me to define each one, probe the definitions with
edge cases, then give me your corrected version.
```

---

## 让导师质疑你的推理（协议 C）

**场景：** 你已经推导出一个解释、一套方案或一份设计，希望导师对它做压力测试，而不是直接认可它。

```
I will describe my understanding of how a multi-agent handoff works
in LangGraph (Chapter 2.2). Please use Socratic elenchus mode:
ask me to lay out my reasoning step by step, then question each
step for consistency with the chapter text. Use counter-examples
where my logic breaks down. Do not tell me the correct answer until
I have found the error myself.

Here is my reasoning: [paste your explanation]
```

```
I think I understand why progressive disclosure matters for agent UIs
(Chapter 1.1A). Challenge my reasoning — ask me to state my
assumptions, then probe them one by one. If my reasoning is
inconsistent with the chapter, help me discover it through questions,
not by correcting me directly.

My reasoning: [paste your explanation]
```

---

## 探讨设计决策（协议 D）

**场景：** 你正在不同架构、框架或设计模式之间做选择，并没有唯一正确的答案。你希望有人帮你理清各种取舍。

```
I am building a multi-agent system for document processing and I am
deciding between LangGraph (Chapter 2.2) and a sequential LangChain
approach (Chapter 2.3). Use Socratic dialectic mode.

Help me compare the two along key dimensions: complexity, state
management, fault tolerance, and scalability. Use "what if" scenarios
to challenge my assumptions — for example, what if my workflow needs
to branch based on document type, or what if I need to pause
mid-pipeline for human review? Ask me to argue against my preferred
option, then help me articulate a final justified choice.
```

```
I am an advanced learner on Chapter 1.7B (Hybrid RAG+KG). I need to
decide whether to use pure vector search or a hybrid RAG+Knowledge
Graph approach for a reasoning-heavy question-answering task.

Use counterfactual reasoning to stress-test my thinking: what if the
query requires multi-hop inference? What if the knowledge base changes
frequently? Help me explore the trade-offs, then ask me to commit to
a choice and defend it.
```

---

## 自我讲解解题过程（协议 E）

**场景：** 面前有一道解答或一个实例讲解，你想真正吃透它，而不只是读一遍。

```
I have this code example from Chapter 2.2 on LangGraph:
[paste code snippet]

Please use a self-explanation protocol. Walk me through it step by
step. At each key step, ask me to explain WHY it is correct or
necessary — not just what it does. Ask me what would happen if that
step were removed or changed. Only give your own explanation after
I have attempted mine. Close by asking me to state the general
principle the example illustrates.
```

```
I just read the trust equation explanation in Chapter 1.1A
(Trust = Transparency × Control). I think I understand it but
I want to make sure. Ask me to explain why the relationship is
multiplicative rather than additive, what would happen if control
were zero, and how this connects to UI design decisions. Challenge
any parts of my explanation that are incomplete.
```

---

## 学习新的流程（协议 F）

**场景：** 某个流程对你来说还很陌生——一次推导、一种编码模式、一套配置流程——你需要先完整看一遍别人怎么做，再自己尝试。

```
I am a beginner on Chapter 2.2 (LangGraph). I have never built a
stateful workflow with nodes and edges before.

Please use a worked example protocol. First, show me a fully worked
example of a simple LangGraph workflow — not the one in the chapter —
with numbered steps and a label for what each step accomplishes.
Then give me a similar but slightly different problem where some
steps are blank for me to fill in. Gradually reduce the scaffolding
until I attempt one mostly on my own.
```

```
I need to understand how to implement a retrieval-augmented generation
pipeline from Chapter 2.7 (Multimodal RAG). Show me a worked example
of a basic RAG pipeline first, then give me a version with missing
steps I need to complete. Highlight the general strategy at each
step, not just the specific code.
```

---

## 用提示解开卡点（协议 G）

**场景：** 你正在实际动手解题，已经有一些进展，但卡在了下一步。你想要的是最小限度的帮助，而不是答案。

```
I am working on understanding how context window limits affect
stateful orchestration (Chapter 1.5A). Here is as far as I have got:
[paste your current thinking or partial answer]

I am stuck on [describe exactly where you are stuck]. Please give me
only one small hint as a question — not the answer, not the next
step written out. After I respond, give me another small hint if I
need it. Escalate slowly.
```

```
I am trying to explain how LangGraph handles conditional branching
but I cannot work out how the router node decides which edge to take.
Here is what I have so far: [paste your work]

Use step-by-step hinting. Do not tell me — ask me a question that
helps me figure it out. Wait for my attempt before giving another hint.
```

---

## 用练习提升熟练度（协议 H）

**场景：** 你已经理解某个概念，但想用得更快、更有把握，就像你练习记忆卡片那样。

```
I understand the five agent memory types from Chapter 1.4 but I am
slow and unsure when asked to distinguish them in scenarios.

Give me one drill question at a time. I will answer from memory —
no peeking at notes. After each answer, tell me if I am correct and
explain briefly. Mix in different question types (identify the memory
type, predict the failure mode, compare two types). Occasionally
revisit questions I got wrong after a few more items. Increase
difficulty as I improve.
```

```
I want to drill on framework selection from Chapter 2.1. For each
scenario I describe, I will tell you which framework I would choose
and why. Tell me if I am right, explain any errors, and gradually
give me harder scenarios. Track which framework types I keep getting
wrong.
```

---

## 备考（协议 I）

**场景：** 你正在备考 NCP-AAI 考试或课程评估，希望进行有结构、带反馈的练习。

```
I am preparing for the NCP-AAI exam and I am weakest on Chapters
1.3 (Multi-Agent Systems) and 2.4 (Multi-Agent Frameworks).

Give me a short quiz of exam-style questions — a mix of
multiple-choice and short scenario questions at medium difficulty.
Show me one question at a time. Wait for my answer before telling
me if I am correct. After each question, explain what I got right
or wrong and which concept it tests. At the end, tell me which
topics I should prioritize and why.
```

```
I have studied all of Parts 1 and 2. I want a full mock exam session.
Generate 10 mixed-difficulty questions covering a spread of chapters.
Track my accuracy per topic. At the end, give me a prioritized study
plan for the week before the exam, sorted by my weakest areas.
```

---

## 复盘一次学习（协议 J）

**场景：** 你刚结束一次学习，想巩固所学内容、检验自我评估是否准确，并规划下一步。

```
We just finished working through Chapter 1.7A and 1.7B on Knowledge
Graphs. Please use a reflection protocol.

Ask me what I covered, what felt easy and what felt hard. Then ask me
to rate my confidence on each sub-topic we touched (1–5). Compare my
confidence ratings to how I actually performed in our session today.
Point out any topics where my confidence and performance diverge.
Finally, help me plan my next study session with specific goals,
resources, and a way to check my progress.
```

---

## 完成计分作业（协议 K）

**场景：** 你有一份作业或需要带回家完成的考核，希望得到导师的帮助，同时不越过学术诚信的底线。

```
I have a graded assignment on Chapter 2.6 (Tool Integration). I am
not asking for solutions — I know that is not allowed.

Please follow an integrity-preserving protocol. Help me understand
the concepts the assignment is testing, check whether my approach
is on the right track without doing the work for me, and give me
hints if I get stuck. Do not write any code I could submit directly.
```

```
I am working on a project that involves designing a multi-agent
workflow (Chapters 1.3 and 2.4). This is graded. I want to talk
through my architecture approach — please question my design choices,
point out gaps, and suggest things to consider, but let me make the
final design decisions myself.
```

---

## 诊断错误答案（协议 M）

**场景：** 你的答案错了，想弄清楚究竟错在哪里，而不是直接被告知正确答案。

```
I answered this question: "[paste the question]"
My answer was: "[paste your answer]"
I was told it was wrong.

Please diagnose my error. Tell me what type of mistake it is —
conceptual, procedural, factual, or careless. Ask me questions to
help me discover where my reasoning went wrong rather than just
telling me the right answer. After I correct my thinking, give me
a similar question to confirm I have fixed the misconception.
```

```
I thought the difference between in-context and external memory
(Chapter 1.4) was just about storage location. I was marked wrong.

Please use error diagnosis mode. What type of error is this? Walk
me through questions that reveal what I was missing, without just
stating the correct answer upfront.
```

---

## 攻克新概念（协议 N）

**场景：** 你即将学习新内容，希望在被讲授之前先自己动手过一遍——这就是「有成效的失败」方法。

```
I have not read Chapter 1.7A yet (Knowledge Graphs). I know about
vector databases and semantic search from earlier chapters.

Please use a productive failure protocol. Give me a problem that
requires knowledge graphs to solve well, but let me attempt it
first using only what I already know. Accept my attempts even if
they are wrong. After I have tried 2–3 approaches, show me the
canonical solution and explain how it relates to what I tried.
```

```
I understand basic RAG but I have not studied hybrid RAG+KG
(Chapter 1.7B). Before you explain it, give me a scenario where
basic RAG would fail, and let me try to figure out a solution.
After I have worked through it, teach me the hybrid approach and
connect it to my attempts.
```

---

## 当你感到卡住或沮丧时（协议 O）

**场景：** 你没有进展、感到迷失，或者正在失去动力。直接告诉导师，让它相应地调整。

```
I have been reading Chapter 1.5B (Stateful Orchestration Worked
Examples) for 30 minutes and I feel like I am going in circles.
I am frustrated and not sure what I do not understand.

Please slow down and help me identify exactly where I am getting
confused. Start with the most basic sub-question — do not assume
I know anything about this section. Give me one very small, concrete
thing to do and check in with me after.
```

```
I feel like the material on Chapter 2.5 (Semantic Kernel) is too
easy compared to what we did on LangGraph. I am bored and not
really engaging.

Please switch to a more challenging mode — give me a hard design
problem, a counter-intuitive scenario, or a debate question that
makes me actually think. Increase the difficulty and ask me to
defend my answers.
```

---

## 小组学习（协议 P）

**场景：** 你和几位同学一起学习，希望导师担任引导者而不是主导者。

```
There are three of us studying Chapter 1.3 (Multi-Agent Systems)
together. We are going to discuss the differences between
peer-to-peer and hierarchical multi-agent architectures.

Please act as a facilitator, not a lecturer. Monitor our discussion
and only interrupt if we get stuck, go off track, or leave someone
out. When you do intervene, use one short question — do not explain
or lecture. At the end of our discussion, help us reflect on what
we agreed on and what is still unresolved.
```

---

## 在一次学习中串联多个协议

下面的示例展示如何把多个协议串联成一条完整的学习路径。

**路径 1 — 第一次接触新概念**
```
Session goal: understand hybrid RAG+KG (Chapter 1.7B) from scratch.

Step 1 — I have not studied this yet. Use productive failure (Protocol N):
give me a problem and let me attempt it before you teach me.

[After the attempt:]
Step 2 — Now explain the canonical approach and compare it to my
attempts (Protocol A). Then walk me through the key steps of the
chapter's worked example and ask me to self-explain each one (Protocol E).

[After the explanation:]
Step 3 — Give me a drill on the key concepts from this chapter
(Protocol H) — 5 short questions, one at a time.

[At the end:]
Step 4 — Help me reflect on what I learned today and plan what to
review next (Protocol J).
```

**路径 2 — 针对薄弱主题备考**
```
I performed poorly on multi-agent coordination topics in practice.
Here is my plan for this session — please follow it:

1. Quiz me on Chapter 1.3 and 2.4 to see where my gaps are (Protocol I).
2. For each question I get wrong, diagnose my error type and help me
   self-correct through questions (Protocol M → C).
3. Give me a worked example on the topic I struggle with most (Protocol F).
4. Re-quiz me on those same topics to confirm improvement (Protocol I).
5. End with a reflection and a study plan for the next two days (Protocol J).
```

**路径 3 — 调试一个设计决策**
```
I am designing a production multi-agent pipeline and I think my
architecture is sound, but I want it stress-tested.

1. I will describe my architecture. Question my reasoning for
   correctness and consistency (Protocol C).
2. Then help me explore the alternatives I did not consider —
   use "what if" scenarios and trade-off questions (Protocol D).
3. If you find any significant errors in my reasoning, diagnose
   them and help me correct them through questions (Protocol M).
4. Once I have a refined design, ask me to self-explain why each
   component is the right choice (Protocol E).
```

---

## 常见错误与应避免的做法

**过于笼统：**
> "帮我学习第 1.3 章。"

导师不知道你的水平、你已经尝试过什么，也不知道你想要哪种帮助。要写得具体。

**一上来就要答案：**
> "这道题的正确答案是什么：[粘贴题目]"

导师会把你引回正轨。求助之前先展示你的尝试，哪怕只是一个粗略的猜测。

**在计分作业上跳过尝试：**
> "这是我的作业，帮我把代码写出来。"

这会触发协议 K。导师会拒绝，并改为帮助你理解问题、规划自己的解法。

**不说明自己的水平：**
> "讲解一下知识图谱。"

如果不知道你的水平，导师只能靠猜。面向中级水平的讲解，对初学者可能太快，对高级学习者又可能太慢。始终说明你的水平。

**粘贴正在进行的考试题目：**
> "这是我正在参加的开卷考试的第 4 题：……"

导师会拒绝，并提出在考试结束后再和你一起学习相关概念。

**询问第 1–2 部分之外的内容：**
> "讲解第 7.3 章 Agent Toolkits 的内容。"

导师无法访问第 3–10 部分的内容。它会告知这一点，并提出帮助它确实覆盖的部分。

---


### 测验与模拟考试


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `docs/practice.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/docs/practice.md) · 语言：英文原文 · 中译版



# 测验与模拟考试
{: .no_toc }

学习过程中的每一个阶段都可以用来自我评估。以下全部都是 Google 表单，任何拿到链接的人
都可以作答；表单本身并未存放在本仓库中。计分按题目难度加权：简单 = 1 分，中等 = 2 分，困难 = 3 分。

<details open markdown="block">
  <summary>本页目录</summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

## 全真模拟考试

10 套 NVIDIA NCP-AAI 模拟测试，每套 70 题。建议在
学完各章之后、临近考试时再做。

| 测试 | 标题 | 题量 | 链接 |
|---|---|---:|---|
| 测试 01 | NVIDIA NCP-AAI 模拟测试 1 | 70 | [开始作答](https://docs.google.com/forms/d/1si4qX2qaX09zS7XUmZUcMoRU0LAeVTb-mWdLQwOWiFg/viewform?usp=sharing) |
| 测试 02 | NVIDIA NCP-AAI 模拟测试 2 | 70 | [开始作答](https://docs.google.com/forms/d/10ykAbo8AwlsyFPrKCHx4D8OqNyUIu7dqn09BsOUcCXk/viewform?usp=sharing) |
| 测试 03 | NVIDIA NCP-AAI 模拟测试 3 | 70 | [开始作答](https://docs.google.com/forms/d/1qt9R31-GuWnalv7y9oyKV-SjxLuq9v-OwMU62iFvmX4/viewform?usp=sharing) |
| 测试 04 | NVIDIA NCP-AAI 模拟测试 4 | 70 | [开始作答](https://docs.google.com/forms/d/1EZwxxCVsUieRMRebMa_cMZuHsz0CCXwC6gPhdsxX7P8/viewform?usp=sharing) |
| 测试 05 | NVIDIA NCP-AAI 模拟测试 5 | 70 | [开始作答](https://docs.google.com/forms/d/1nwj-8Oavejn4JVCEGp4xWc-FK0Yqt29x0uRh4Sc-k34/viewform?usp=sharing) |
| 测试 06 | NVIDIA NCP-AAI 模拟测试 6 | 70 | [开始作答](https://docs.google.com/forms/d/18CEVZx6ao0AReKtMlhOG-TKAqwjgS24C1bGejbk3tiM/viewform?usp=sharing) |
| 测试 07 | NVIDIA NCP-AAI 模拟测试 7 | 70 | [开始作答](https://docs.google.com/forms/d/1ZfOAz-jD9WJ3erws1rfvGpJUZKrWEX4I1-bnC_E-OWQ/viewform?usp=sharing) |
| 测试 08 | NVIDIA NCP-AAI 模拟测试 8 | 70 | [开始作答](https://docs.google.com/forms/d/163Wg3lJTOUe0KFJteY3VxgwI3n_XMVmnTcs0Jj4_Cjg/viewform?usp=sharing) |
| 测试 09 | NVIDIA NCP-AAI 模拟测试 9 | 70 | [开始作答](https://docs.google.com/forms/d/1v_6e-0fCNxpmzjJaoXl11sP0tj40_PiAkAVymo_Ngmo/viewform?usp=sharing) |
| 测试 10 | NVIDIA NCP-AAI 模拟测试 10 | 70 | [开始作答](https://docs.google.com/forms/d/1gHKbf7XX8uLbm5rbxtbnsK47onfpHV1dvkg2L7mkBtY/viewform?usp=sharing) |

## 章节测验

共 96 套测验，下面按
[`quizzes_ver20JUN26.md`]({{ site.repo_blob }}/quizzes_ver20JUN26.md)（版本 20JUN26）中所用的编号列出，标题沿用该文件中的
写法（部分标题在源文件中已被截断）。

**编号提示。** 从第 4 部分起，测验列表使用的章节编号比学习计划、幻灯片和认证对照表中的章节编号
更旧：例如测验 5.11 是 *程序性记忆（Procedural Memory）*，而第 5.11 章是 *基于规则的决策（Rule-Based Decision Making）*；
测验 9.9–9.11 和 5.14–5.15 并没有对应编号的章节。请按**标题**而不是编号把测验与章节对应起来。
[各部分页面]({{ site.baseurl }}/curriculum/)只有在标题一致时才会把测验链接到对应章节。

### 第 1 部分 — 智能体基础

| 测验 | 标题 | 题量 | 链接 |
|---|---|---:|---|
| 1.1A | 为直观的人机智能体交互设计用户界面... | 26 | [开始作答](https://docs.google.com/forms/d/1XmM2qiJrFvJCOJXGFM_waJ-fDvNq7DCcjeHDUFo-J7w/viewform?usp=sharing) |
| 1.1B | 人在回路模式与无障碍设计 | 34 | [开始作答](https://docs.google.com/forms/d/1wWQYe9nQOFHfVtHt8wCYysaIp_obXckibGoJgHB9p_Q/viewform?usp=sharing) |
| 1.2 | 核心智能体模式 | 30 | [开始作答](https://docs.google.com/forms/d/1EsIlTzhOYvtV3RahqLJ3q5dW013TjVb0l0RWOu_N-Tg/viewform?usp=sharing) |
| 1.3 | 多智能体系统 | 42 | [开始作答](https://docs.google.com/forms/d/1rGwHje49TRniIhG65hXRgmqXtHmy1xc5dv_zb2VmEMY/viewform?usp=sharing) |
| 1.4 | 记忆与感知系统 | 20 | [开始作答](https://docs.google.com/forms/d/15U_a9_pc7gVkGTCNS-NG9K1sJwQWe5HGBaN6uMJBLVU/viewform?usp=sharing) |
| 1.5A | 有状态编排 - 简介与核心概念 | 27 | [开始作答](https://docs.google.com/forms/d/109aLl62B5W3Nk4a34dI4fwTlgM6A01saKeAzZuZOtxw/viewform?usp=sharing) |
| 1.5B | 有状态编排 - 示例详解 | 27 | [开始作答](https://docs.google.com/forms/d/1jz2PVQHMS6ok1yD45OxRsVI7p8bL9r1IWhEGdicE6pE/viewform?usp=sharing) |
| 1.6 | 有状态编排 - 陷阱、集成与同... | 24 | [开始作答](https://docs.google.com/forms/d/1Sy889rKbbJmXe6chqXD7gYnqLfgJtOYibvxTtE7PZuE/viewform?usp=sharing) |
| 1.7A | 基于知识图谱的关系推理 - 基础... | 41 | [开始作答](https://docs.google.com/forms/d/11SNhGX9BGs58nqaICVAv4lmEN6G922_vjOu1DuctXPY/viewform?usp=sharing) |
| 1.7B | 基于知识图谱的关系推理 - 混合 RAG... | 25 | [开始作答](https://docs.google.com/forms/d/1CjMbpAIwwGx_cse1y0Dh1hmjPZEU43LIDReJBJOTMtM/viewform?usp=sharing) |
| 1.8 | 可扩展性与生产部署 | 27 | [开始作答](https://docs.google.com/forms/d/1uewv4-qyQz16HCz_0D5dUEhkv3wfsYfx9rphANqdBXI/viewform?usp=sharing) |

### 第 2 部分 — 框架与工具集成

| 测验 | 标题 | 题量 | 链接 |
|---|---|---:|---|
| 2.1 | 框架全景与选型 | 23 | [开始作答](https://docs.google.com/forms/d/1jj55JTho9uPN2Mu7FwIpfc-mQe-L34q0cHoniRtOuOY/viewform?usp=sharing) |
| 2.2 | LangGraph | 25 | [开始作答](https://docs.google.com/forms/d/1WyguE8MVLqdmWYRCy-0T_ZxX7B_Jcigt2r5jy80pmN0/viewform?usp=sharing) |
| 2.3 | LangChain 顺序式框架 | 23 | [开始作答](https://docs.google.com/forms/d/13Ecjr24F4NqLB131JaVg36h0ExKPQiqkxTlYog6n7PM/viewform?usp=sharing) |
| 2.4 | 多智能体框架 | 33 | [开始作答](https://docs.google.com/forms/d/1BwgT2tdhSe8Yv6NixzTpAbhGT2ksn5JG-10u-uEHUcQ/viewform?usp=sharing) |
| 2.5 | Semantic Kernel：企业级框架与插件架构... | 25 | [开始作答](https://docs.google.com/forms/d/1qbm2AAl0XkPeTWvqInQZog1zRHNMblMmvSgbSQNLIDA/viewform?usp=sharing) |
| 2.6 | 工具集成与函数调用 | 26 | [开始作答](https://docs.google.com/forms/d/1f_7aioG1-xWk0M2bAhihuJJOx9UK2nwaaWsjcevGTek/viewform?usp=sharing) |
| 2.7 | 多模态 RAG 方案 | 43 | [开始作答](https://docs.google.com/forms/d/1yPrLfIsN_xeFWya-hQb0rla3c-A4I0gbbiZy_5wzQ-Y/viewform?usp=sharing) |
| 2.8 | 错误处理与韧性 | 28 | [开始作答](https://docs.google.com/forms/d/1u4hzqjpzM3hRjso7YSN6Ay-j9MCsiCRzO-zFtvTV-MU/viewform?usp=sharing) |
| 2.9 | 流式与实时响应 | 27 | [开始作答](https://docs.google.com/forms/d/1EVvuCnVelN44xHeVzolDx1MVwV3AJucqDsPeeHLP5DA/viewform?usp=sharing) |

### 第 3 部分 — 评估与优化

| 测验 | 标题 | 题量 | 链接 |
|---|---|---:|---|
| 3.1A | 实现评估流水线与任务基准测试 | 36 | [开始作答](https://docs.google.com/forms/d/15iqCaPDaFXuBRjNGR643LmzxtZKWcDTXGI8VmkxYXew/viewform?usp=sharing) |
| 3.1B | 实现评估流水线与任务基准测试（指... | 28 | [开始作答](https://docs.google.com/forms/d/1nyE8Blc4ZgqNV2ZBAD8pJbGBArv-sRDbAVv6oFWldPU/viewform?usp=sharing) |
| 3.1C | 实现评估流水线与任务基准测试（Ind... | 25 | [开始作答](https://docs.google.com/forms/d/1OGa5ulPg3OvKKE6-TO3MfyONhmmn5dVX47TGUKa8EXk/viewform?usp=sharing) |
| 3.2 | 跨任务与数据集比较智能体性能 | 26 | [开始作答](https://docs.google.com/forms/d/1cr_yfhb2zKPgxcGna1rjZUc0FJYGx7n18kLV3T_jPIw/viewform?usp=sharing) |
| 3.3 | 网页导航与交互基准测试 | 31 | [开始作答](https://docs.google.com/forms/d/1KU6D0880znwHkFMab25JXaNJwQdtOt4z-sfaeWAcMN0/viewform?usp=sharing) |
| 3.4 | 为生产性能调优模型参数 | 25 | [开始作答](https://docs.google.com/forms/d/1GmJu-NCaKyfixAg4HMtt9ReNxKkMXNDm52FtbIKUL50/viewform?usp=sharing) |
| 3.5 | 提示词优化技术与少样本学习策略... | 27 | [开始作答](https://docs.google.com/forms/d/1pVmk3BXqPnhzLGPfGNznt0LDY11gOcGKckXiAdAFCwA/viewform?usp=sharing) |
| 3.6 | 让智能体的决策可见 | 28 | [开始作答](https://docs.google.com/forms/d/1B4QIi-ZsCuJkL_DlOHcf5gy4MUhKqcRPwukx_p6yQqw/viewform?usp=sharing) |
| 3.7 | 工具使用审计 | 29 | [开始作答](https://docs.google.com/forms/d/1TetLG6Fo7CnUyRHhjF5Ugbf0uCovGp0vCV23CZui-JA/viewform?usp=sharing) |
| 3.8 | 动作准确率指标 | 38 | [开始作答](https://docs.google.com/forms/d/1lRlcnCStFuREtPdHk6b9Qxu69WKoglcrEKExiKIRlcQ/viewform?usp=sharing) |
| 3.9 | 推理质量 | 40 | [开始作答](https://docs.google.com/forms/d/162oqrBfqthRmZNyU-74dOVIQr2KQ62ISMkS8dkMsfvw/viewform?usp=sharing) |
| 3.10 | 效率指标 — 在性能、成本与风...之间取得平衡 | 42 | [开始作答](https://docs.google.com/forms/d/1iZ1MjXJ_OPXboW9LVd-zzCzIh1y2ySzFZP1azKCdCCs/viewform?usp=sharing) |

### 第 4 部分 — 生产部署与横向扩展

| 测验 | 标题 | 题量 | 链接 |
|---|---|---:|---|
| 4.1A | 面向 AI 智能体部署的微服务架构 | 27 | [开始作答](https://docs.google.com/forms/d/1if2c8Qu-gzjVf7NkPtEV6hPmgCpQcGauEoaFp-zCoGs/viewform?usp=sharing) |
| 4.1B | 面向多智能体 AI 系统的 Kubernetes 编排 | 30 | [开始作答](https://docs.google.com/forms/d/1AGZ2H6dIePFVzdv0nsS_wM0x6BjH6UhC8IdAh-Sp49A/viewform?usp=sharing) |
| 4.2A | NVIDIA NIM 与 Triton Inference Server | 42 | [开始作答](https://docs.google.com/forms/d/11ATH7FGMjGK3nsRBhiFstDhmLZViqxrvPW1VM0ax5pc/viewform?usp=sharing) |
| 4.2B | TensorRT-LLM 与 NVIDIA Fleet Command | 40 | [开始作答](https://docs.google.com/forms/d/1qPHp0ZxKB6ect5Of58tSlLwGGqSzQ7109LZ7jwCp-uE/viewform?usp=sharing) |
| 4.3 | 容器编排与边缘部署 | 31 | [开始作答](https://docs.google.com/forms/d/1zf3fb2qlxLbs6Z6ARpbrcUdp-T5OE6hmEP9wMZC3bjw/viewform?usp=sharing) |
| 4.4 | 面向多智能体系统的生产基础设施 | 30 | [开始作答](https://docs.google.com/forms/d/18t4_B1hDnAcH23xHZcoQxMI_C4GXx0gI5ST-SYdmFxs/viewform?usp=sharing) |
| 4.5 | NVIDIA NIM 与 Triton Inference Server | 26 | [开始作答](https://docs.google.com/forms/d/1Z1xLfMAdzT0IJibUl0cGqfRD7Hh1Pb2CY2SCUcGJL6Q/viewform?usp=sharing) |
| 4.6 | TensorRT-LLM 与 NVIDIA Fleet Command | 29 | [开始作答](https://docs.google.com/forms/d/1ak-7FD_KYAcAfbrWxUm_y2n3pyBXM0vvrnu5ZjYEkVE/viewform?usp=sharing) |

### 第 5 部分 — 高级推理与决策

| 测验 | 标题 | 题量 | 链接 |
|---|---|---:|---|
| 5.1 | 思维链（CoT）基础与集成 | 25 | [开始作答](https://docs.google.com/forms/d/1z75RzeMlZKVckMfWuAszUoCAssGs2vqfq-YRncf2HHI/viewform?usp=sharing) |
| 5.2 | 思维树（ToT）基础与思维图... | 28 | [开始作答](https://docs.google.com/forms/d/1hhvV97gVvKuxCSQ8f7Vhm7ipGrSf0nDeEvqUTzz4ciw/viewform?usp=sharing) |
| 5.3 | 自洽性基础 | 55 | [开始作答](https://docs.google.com/forms/d/1sJG1qC1wUFkDaXt_3uLY3ulJXGTi34y4qi4NUq2q5bs/viewform?usp=sharing) |
| 5.4 | 分层规划基础与 HTN 形式化 | 28 | [开始作答](https://docs.google.com/forms/d/1-ZY4GaQaWejGOa6TtuA1f6Msm9xLSKTII4ojrn_08Sw/viewform?usp=sharing) |
| 5.5 | 蒙特卡洛树搜索基础 | 33 | [开始作答](https://docs.google.com/forms/d/1qDmgPgrrIKZoSTESd9Z-riUAac3kUkrLe1HdgSHUpa8/viewform?usp=sharing) |
| 5.6 | A\* 搜索基础与实现 | 24 | [开始作答](https://docs.google.com/forms/d/1yWaTgJIJcToZNaG58nq5HAokSfIMvrysr26tuN5xMSM/viewform?usp=sharing) |
| 5.8 | 语义记忆 | 33 | [开始作答](https://docs.google.com/forms/d/1druUvn3qBIZn4A3O29sJpwO9PGEbH-2qC7zBv3muSk4/viewform?usp=sharing) |
| 5.9 | 工作记忆 | 29 | [开始作答](https://docs.google.com/forms/d/1TyXSfcoxGHCr9QKNZ8OrYnKs14FBPtvoj_H_3SVdSyc/viewform?usp=sharing) |
| 5.10 | 基于效用（Utility）的决策基础 | 32 | [开始作答](https://docs.google.com/forms/d/1bT6_8qN2j1GOUOGmtVgIVijEU7FWlbsc6_j5njKPfV8/viewform?usp=sharing) |
| 5.11 | 程序性记忆 | 26 | [开始作答](https://docs.google.com/forms/d/1KLpFNjHOLGceEqyvbdXwj0lTVEiISK4Jon2uGrdd70g/viewform?usp=sharing) |
| 5.12 | 基于学习的决策基础 | 32 | [开始作答](https://docs.google.com/forms/d/166c1B5zKyF6D_qePjAhlGh_YOAr_5e-74QxhhfVY-FA/viewform?usp=sharing) |
| 5.13 | 混合决策系统基础 | 38 | [开始作答](https://docs.google.com/forms/d/1xyjiUDrzOfxbeixSAX08jC7rNL4HW99guwzyJDwuDSw/viewform?usp=sharing) |
| 5.14 | 基于学习的决策基础 | 28 | [开始作答](https://docs.google.com/forms/d/1_cjJJEJgZBdIJdg-r2hIMqL7rDm9SEPWbxG3ojjCF1k/viewform?usp=sharing) |
| 5.15 | 混合决策系统基础 | 28 | [开始作答](https://docs.google.com/forms/d/1-419Q5jTfru_79bt5TNuJpIFFmi-oZV_5qi_jzTTRDQ/viewform?usp=sharing) |

### 第 6 部分 — 检索增强生成（RAG）

| 测验 | 标题 | 题量 | 链接 |
|---|---|---:|---|
| 6.1 | 嵌入与 RAG 基础 | 72 | [开始作答](https://docs.google.com/forms/d/1r3KyikJNqmj9EbsRjVmHk4SfZj5f74r3zKqOrEv3qF4/viewform?usp=sharing) |
| 6.2 | 向量数据库与相似性搜索 | 67 | [开始作答](https://docs.google.com/forms/d/1UJ1NjmCoN-R-qoCuPvvOWKeVFsdFLHElOLrxZ71LjV4/viewform?usp=sharing) |
| 6.3 | 构建 ETL 流水线以集成企业数据源... | 69 | [开始作答](https://docs.google.com/forms/d/1W5uMtpzZbw_qfnl8aEibw2wlXsYV_CgczTUuPd2es34/viewform?usp=sharing) |
| 6.3C | ETL 实操、陷阱与资源 | 26 | [开始作答](https://docs.google.com/forms/d/1HrfRMbzMQhgN1u_pEwAuUJ6II7e3OqY9iAUtyQpUIaY/viewform?usp=sharing) |
| 6.4 | 数据质量基础 | 60 | [开始作答](https://docs.google.com/forms/d/1Yi5tTzZ56WYnOcHdVFO7Sgoyq1v_hh-n_iPK8QBz6iE/viewform?usp=sharing) |
| 6.5 | 生产级 RAG 系统 | 72 | [开始作答](https://docs.google.com/forms/d/1mmle4Qng1tZMNURnsk90Gk_S-QT73P5eNnnthxY6qkE/viewform?usp=sharing) |
| 6.6 | 查询分解与自适应检索 | 64 | [开始作答](https://docs.google.com/forms/d/1P99z62qsSnUuFiNeBoFhnDvm8ltVKBlnfMJU_eP-X4Q/viewform?usp=sharing) |
| 6.7 | 本章小结与综合 | 25 | [开始作答](https://docs.google.com/forms/d/1kpdJP7Ibf3ciyYCQCJR3VzkY7N5tRibEdmyZlea8byo/viewform?usp=sharing) |
| 6.9B | 进阶代码审查与应用题 | 35 | [开始作答](https://docs.google.com/forms/d/1jkKJLEQqZnj-yCGJ7Gqe5OBwcmB_RF5EF8R2iB37JKk/viewform?usp=sharing) |

### 第 7 部分 — NVIDIA NeMo 框架与优化

| 测验 | 标题 | 题量 | 链接 |
|---|---|---:|---|
| 7.1A | NeMo 框架与六种 Rail 类型 | 26 | [开始作答](https://docs.google.com/forms/d/1Fsc3F4S7qD_OVVNs-4r81DxzBNxef4b5KC2epFcQG_w/viewform?usp=sharing) |
| 7.1B | NVIDIA NIM 与 Colang | 25 | [开始作答](https://docs.google.com/forms/d/1uFE6RZ9JRYVYVj-VQRiH_WME_1-vxC0Ee5-7fBape2M/viewform?usp=sharing) |
| 7.2A | 性能优化与生产监控 — Lo... | 30 | [开始作答](https://docs.google.com/forms/d/1U7d-6ReqiEqv3FqTsLwFAcI2XYEEdZaiwqmFSeQ18WE/viewform?usp=sharing) |
| 7.2B | 性能优化与生产监控 | 47 | [开始作答](https://docs.google.com/forms/d/1u3x4JpR3MpV09bIVEDzXbXITqN_zKTGLJsC6V-Ne3N8/viewform?usp=sharing) |
| 7.3 | NeMo Agent Toolkit 性能剖析 | 26 | [开始作答](https://docs.google.com/forms/d/1jRjKy9SG-CMOxUioHbsGR-OIXs3THpYzTqIU4ysVsMc/viewform?usp=sharing) |
| 7.4 | TensorRT-LLM 基础与量化 | 24 | [开始作答](https://docs.google.com/forms/d/124BZB8in0oItPq4bJrRGv_WKock3WT_C7TEUd2cW0aY/viewform?usp=sharing) |
| 7.5 | NeMo Curator、Riva Speech AI 与多模态集成 | 49 | [开始作答](https://docs.google.com/forms/d/1YvOLAjPOx0F-Rb44z6UwjSzxQiFSXuWdOrEfUDpPDW4/viewform?usp=sharing) |
| 7.6 | Multi-Instance GPU | 29 | [开始作答](https://docs.google.com/forms/d/1io2Z9tCSlSIAPDXIdrVC1KsGJL3nA_5S_aLxCKj0M7s/viewform?usp=sharing) |

### 第 8 部分 — 可靠性与成本管理

| 测验 | 标题 | 题量 | 链接 |
|---|---|---:|---|
| 8.1 | 延迟指标 | 40 | [开始作答](https://docs.google.com/forms/d/1c2DlRZhVBJvfB5OskMtG6lyOm9PSkcQl-nzg3u3LR4s/viewform?usp=sharing) |
| 8.2A | 错误分类法与 SLO 管理 | 26 | [开始作答](https://docs.google.com/forms/d/13HhhUa2efm3tWRd5X6l3P1m7ht128IRee5R1C6IF7EI/viewform?usp=sharing) |
| 8.2B | NeMo Guardrails 集成 | 26 | [开始作答](https://docs.google.com/forms/d/1fqOZUSK7ZEDr6V_4x7RmpumvkJyGD3DAhLeAvwglA6M/viewform?usp=sharing) |
| 8.3 | Token 经济性与架构 | 24 | [开始作答](https://docs.google.com/forms/d/1BbZ7sbP0Fh_-NhvEvA0I9bL1gfLweEND5v9zLR8GJ_k/viewform?usp=sharing) |
| 8.4 | 成功指标与多维度度量 | 30 | [开始作答](https://docs.google.com/forms/d/1xbI_UW3aLlDWQcQSJZ12GTkAz78PP0rMUouJLDfPIdU/viewform?usp=sharing) |

### 第 9 部分 — 安全与治理

| 测验 | 标题 | 题量 | 链接 |
|---|---|---:|---|
| 9.1 | 输出过滤与内容审核 | 32 | [开始作答](https://docs.google.com/forms/d/1EljVTn1taC7T7mVsUz-NZKmLbf2E-Xp2e229yQTGl_w/viewform?usp=sharing) |
| 9.2 | 动作约束与权限模型 | 30 | [开始作答](https://docs.google.com/forms/d/1q3QaLjLhBIFW4GDBWRdBICCz0RZl3wD6ZpjJLa74fkA/viewform?usp=sharing) |
| 9.3 | 沙箱与透明度基础 | 32 | [开始作答](https://docs.google.com/forms/d/1VorINUF8J5w44kFKSzgEVaifGmX_ojvpW1ixHJkRKYo/viewform?usp=sharing) |
| 9.4 | 公平性与偏见缓解 | 32 | [开始作答](https://docs.google.com/forms/d/17VfqM5o4CrRf0vXk-U9bWLZShS9LjnwXFQ3kypRScLo/viewform?usp=sharing) |
| 9.6A | 价值对齐框架（A 部分） | 24 | [开始作答](https://docs.google.com/forms/d/1xjlhouAvPDHauiEAwRAk8a9F1YT-cJQ9qm_MAx6C90U/viewform?usp=sharing) |
| 9.6B | 价值对齐框架 | 32 | [开始作答](https://docs.google.com/forms/d/1B5Nbm47QfdMqigaHZmTozYCgWTpcYwNs-0vJdRB8kpY/viewform?usp=sharing) |
| 9.7 | GDPR 与数据保护法规 | 30 | [开始作答](https://docs.google.com/forms/d/1gtKkdyx3YcR8YOGC0ynEa0u7CdtC5A7eKC0tEzMnYhw/viewform?usp=sharing) |
| 9.8A | AI 治理的标准与框架 | 28 | [开始作答](https://docs.google.com/forms/d/1bPR68UU_JtvSwapv2E6Trx85-0hxGHSqY0qm6u_UtMo/viewform?usp=sharing) |
| 9.8B | AI 治理的标准与框架 | 31 | [开始作答](https://docs.google.com/forms/d/1OtUhvSYGqS6OiqH482WVkBjHTIu1rB1GJepYdzShctU/viewform?usp=sharing) |
| 9.9 | 价值对齐框架 — 构建具备...能力的 AI 系统 | 32 | [开始作答](https://docs.google.com/forms/d/1DOU4bbC2gaGPaj_CcgJIVKN_GWgn8CbqFxwMSZjSagI/viewform?usp=sharing) |
| 9.10 | GDPR 合规实践 | 28 | [开始作答](https://docs.google.com/forms/d/1tr0N4p4yhnkWNoeIjY7ZwoQb4FT0h4UcpHEux51VgzE/viewform?usp=sharing) |
| 9.11 | AI 治理的标准与框架 | 32 | [开始作答](https://docs.google.com/forms/d/1BZcNzB1DmOXwD3Aha0gKJalo2aNpLQoqrubV-dwZceQ/viewform?usp=sharing) |
| 9.16 | 本章小结与综合 | 48 | [开始作答](https://docs.google.com/forms/d/1CPD-5S2dZGOYomwbzXhcrSc-dDpuBoHTXkFUjIny3AA/viewform?usp=sharing) |
| 9.17 | 本章小结与综合 | 32 | [开始作答](https://docs.google.com/forms/d/19CQlkouCfWXofAvGk8PS_Wmaj7KnviEaA1kmD4okGrI/viewform?usp=sharing) |

### 第 10 部分 — 人在回路与集成

| 测验 | 标题 | 题量 | 链接 |
|---|---|---:|---|
| 10.1 | 对话式 UI | 35 | [开始作答](https://docs.google.com/forms/d/13rN-HUmcylPaElvnlfOfjIFbUKKoY29F5wBykwKGvhY/viewform?usp=sharing) |
| 10.2 | 主动型智能体 | 31 | [开始作答](https://docs.google.com/forms/d/1JfhTZi64odDKNg6bxGdDK6Tzke4LJ6H-l80zreuBmzw/viewform?usp=sharing) |
| 10.3 | RLHF 方法论 | 30 | [开始作答](https://docs.google.com/forms/d/1kfKFluEL-PTpI3MlNeYHK6D6zJ2MF44TFe40gaS-EWA/viewform?usp=sharing) |
| 10.4 | 人在回路（Human-in-the-Loop） | 30 | [开始作答](https://docs.google.com/forms/d/1S9-1L6ueaO3E7ApGEXekHlKI74rXTce7v-P5TtQn_eI/viewform?usp=sharing) |
| 10.5 | Human-over-the-Loop（人在回路之上） | 30 | [开始作答](https://docs.google.com/forms/d/1ePcVBWqiyScIys77ZiU0F1OQaGRndloJJIZr30tM80Y/viewform?usp=sharing) |
| 10.6 | 主动学习 | 32 | [开始作答](https://docs.google.com/forms/d/1DqC1GX5b_T6yULuxgc5deJP4HaWGCHJaQdFXw3YfkNg/viewform?usp=sharing) |

## 学习计划中也有

[`Study_Plan.md`]({{ site.repo_blob }}/Study_Plan.md) 中的每个章节小节都以下列内容收尾：一组关键问题、
一个“做本章测验”的链接，以及一个供你用自己的话回答这些问题的表单。

## 如何高效使用

1. 读完一章后立即做该章测验，不要翻看笔记。
2. 在进入下一部分之前，把没通过的章节测验重新做一遍。
3. 在考试日期前大约两周做一套全真模拟考试，考试当周再做一套，把第二次当作一次彩排。
4. 使用 [AI 导师]({{ site.baseurl }}/ai-tutor/) 把做错的题目逐一弄明白。

---


### 有益的先修条件


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `docs/prerequisites/beneficial.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/docs/prerequisites/beneficial.md) · 语言：英文原文 · 中译版



# 有益的先修条件
{: .no_toc }

这些内容能加速学习、加深理解，但并非严格必需——本书会在你读到那里时解释你需要什么。
如果你构建的是多智能体系统或企业级系统，而不是单智能体系统，那么值得优先准备。
本层之上的级别请参见[必备]({{ site.baseurl }}/prerequisites/essential/)和
[推荐]({{ site.baseurl }}/prerequisites/recommended/)。

<details open markdown="block">
  <summary>本页内容</summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

## 分布式系统概念

[1.3]({{ site.baseurl }}/curriculum/part-01/)（多智能体系统）和
[1.5A–1.6]({{ site.baseurl }}/curriculum/part-01/)（有状态编排）的核心，都是跨进程、跨服务器、
跨组织的多智能体协同——这恰恰是那种一旦假定消息投递是瞬时的、完美有序的，就会引发
真实 bug 的场景。如果你只构建单智能体系统，这一层级可以完全推迟。

### 同步与异步消息，以及故障恢复

如果三个智能体正在协同完成一项任务，而网络中断了五秒，系统应该如何恢复？
你能解释同步消息与异步消息的区别吗？

<details markdown="block">
<summary>视频</summary>

<div style="margin:0 0 1.5rem 0">
<iframe src="https://www.youtube-nocookie.com/embed/videoseries?list=PLeKd45zvjcDFUEv_ohr_HdUFe97RItdiB" title="Distributed Systems lecture series" loading="lazy" style="width:100%;max-width:560px;aspect-ratio:16/9;border:0" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
<div><a href="https://www.youtube.com/playlist?list=PLeKd45zvjcDFUEv_ohr_HdUFe97RItdiB">Distributed Systems lecture series</a> &middot; Martin Kleppmann</div>
</div>

约 7 小时的播放列表；作者与《Designing Data-Intensive Applications》相同（该书在
[推荐 &gt; 数据库基础]({{ site.baseurl }}/prerequisites/recommended/#database-fundamentals)中被引用）。
前 2–3 讲覆盖本小节以及下一小节的内容。

</details>

### 最终一致性、CAP 定理与共识

你理解“最终一致性”意味着什么，以及分布式系统为何要接受它吗？
从高层次上说，Raft 或 Paxos 这类共识协议解决了什么问题？

- 继续观看上面的同一系列讲座，或阅读原始的
  [CAP Theorem](https://www.julianbrowne.com/article/brewers-cap-theorem)讲解以获得浓缩版本

---

## GPU 架构与 CUDA 基础

[第 7 部分]({{ site.baseurl }}/curriculum/part-07/)讲解了在 GPU 上优化 LLM 推理——量化、
批处理和 KV-cache 调优，只有在你明白 GPU 为何在 LLM 所需的运算上表现出色时才更有意义。
[4.4]({{ site.baseurl }}/curriculum/part-04/)则直接分析 GPU 利用率。没有这些背景你也能掌握
第 7 部分的技术——本书会解释你需要什么——但有了这些背景，学习会从照搬配方转为建立直觉。

### 为什么 GPU 在 LLM 工作负载上如此之快

你能解释 GPU 为何特别擅长矩阵乘法，以及 GPU 利用率百分比实际反映的是什么吗？

- [NVIDIA CUDA C++ Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html)
  的引言部分——读它是为了理解架构背后的原理，而不是为了成为 CUDA 程序员

### 在实践中分析 GPU 工作负载

在理解了“为什么”之后，你能否读懂 GPU profiler 的输出，
并判断某个内核是受内存限制还是受计算限制？

<details markdown="block">
<summary>视频</summary>

<div style="margin:0 0 1.5rem 0">
<iframe src="https://www.youtube-nocookie.com/embed/LuhJEEJQgUM" title="Lecture 1: How to profile CUDA kernels in PyTorch" loading="lazy" style="width:100%;max-width:560px;aspect-ratio:16/9;border:0" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
<div><a href="https://www.youtube.com/watch?v=LuhJEEJQgUM">Lecture 1: How to profile CUDA kernels in PyTorch</a> &middot; GPU MODE</div>
</div>

比纯粹的基础理论视频更偏动手实操——在上面“为什么”讲通之后才有用，
在那之前用处不大。

</details>

---

## Prompt Engineering 技术

[第 1 部分]({{ site.baseurl }}/curriculum/part-01/)以及[第 2 部分]({{ site.baseurl }}/curriculum/part-02/)
中的每个框架都会用到提示词；[5.2]({{ site.baseurl }}/curriculum/part-05/)的 Tree-of-Thought
推理依赖于精巧的提示词构造。更好的提示词技巧能让书中的每个实验都完成得更快。这扩展了
[必备 &gt; LLM 基础 &gt; 提示范式]({{ site.baseurl }}/prerequisites/essential/#large-language-model-llm-fundamentals)
中的简要提及。

### 零样本、少样本与思维链提示

你能写出一个向模型演示某项任务的少样本提示词，
并解释思维链提示何时值得付出额外的 token 成本吗？

<details markdown="block">
<summary>视频</summary>

<div style="margin:0 0 1.5rem 0">
<iframe src="https://www.youtube-nocookie.com/embed/b2t4pa9lOIc" title="Prompt Engineering Explained – Zero, Few, CoT, Self Consistency, Persona" loading="lazy" style="width:100%;max-width:560px;aspect-ratio:16/9;border:0" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
<div><a href="https://www.youtube.com/watch?v=b2t4pa9lOIc">Prompt Engineering Explained – Zero, Few, CoT, Self Consistency, Persona</a> &middot; Loop Kaka</div>
</div>

</details>

### 系统消息、模板与基于角色的提示

你知道系统消息与用户消息在实践中的区别吗？能否构建一个可复用的提示词模板？

- [OpenAI 的提示工程指南](https://platform.openai.com/docs/guides/prompt-engineering) &middot; 免费、官方、持续更新

### 调试失效的提示词

当提示词没有产生你预期的结果时，你是否有系统化的方法定位原因——
而不是随意猜测、反复改写措辞？

- 练习：跨不同任务挑选 10–15 个提示词，故意把每一个弄坏，
  先诊断原因，再动手修复

---

## Python 异步编程

如果你只是配置框架，异步始终隐藏在幕后。如果你要实现自定义的智能体逻辑，
它就是必不可少的：[2.9]({{ site.baseurl }}/curriculum/part-02/)（流式输出）使用异步模式
实现工具的并发执行，[第 7 部分]({{ site.baseurl }}/curriculum/part-07/)则用它来优化吞吐。

### `async`/`await` 与事件循环

你能编写 `async` 函数、使用 `await`，并解释当你的协程等待 I/O 时，
事件循环究竟在做什么吗？

<details markdown="block">
<summary>视频</summary>

<div style="margin:0 0 1.5rem 0">
<iframe src="https://www.youtube-nocookie.com/embed/ngXbyui-weA" title="Python Asynchronous Programming Tutorial: Asyncio, async &amp; await Explained" loading="lazy" style="width:100%;max-width:560px;aspect-ratio:16/9;border:0" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
<div><a href="https://www.youtube.com/watch?v=ngXbyui-weA">Python Asynchronous Programming Tutorial: Asyncio, async &amp; await Explained</a> &middot; Code with Josh</div>
</div>

</details>

### 并发执行，以及异步何时真正有用

你理解 `asyncio.gather()` 与顺序执行同样的调用之间的区别吗？
明白为什么异步对 I/O 密集型工作有帮助，却对 CPU 密集型工作没有帮助？

- 练习：写一个脚本，用 `asyncio.gather()` 并发调用 3–5 个 API，
  并与逐个串行调用做耗时对比

### 线程 vs. 进程 vs. 异步任务

你能解释在什么情况下该选线程、进程或异步任务，而不是彼此混用吗？

- [Real Python: Async IO in Python](https://realpython.com/async-io-python/)

---

## CI/CD 与 DevOps 基础

[第 4 部分]({{ site.baseurl }}/curriculum/part-04/)直接讲解智能体系统的 CI/CD，
[第 8 部分]({{ site.baseurl }}/curriculum/part-08/)则在这类流水线内部实现监控。
生产环境中的智能体需要自动化测试、部署和回滚——如果你对此完全陌生，
本书提供的指导已经足够，但把基础打好你会推进得更快。

### CI/CD 达成了什么

你能解释持续集成和持续交付各自解决了什么问题，
以及为什么自动化测试必须在部署之前而不是之后运行吗？

<details markdown="block">
<summary>视频</summary>

<div style="margin:0 0 1.5rem 0">
<iframe src="https://www.youtube-nocookie.com/embed/aZzV6X7XhyI" title="Automate your Docker Build/Test/Deploy pipelines!" loading="lazy" style="width:100%;max-width:560px;aspect-ratio:16/9;border:0" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
<div><a href="https://www.youtube.com/watch?v=aZzV6X7XhyI">Automate your Docker Build/Test/Deploy pipelines!</a> &middot; Bret Fisher</div>
</div>

这是一个具体的 build/test/deploy 流水线，而不只是理论——而且是容器化的，
这正是本书从[第 4 部分]({{ site.baseurl }}/curriculum/part-04/)起部署所有内容的方式。

</details>

### Git 版本控制

你能有信心地提交、分支和合并，包括解决一次真实的冲突，
而不是为了避免冲突干脆不用分支吗？

- [Git 官方文档](https://git-scm.com/doc) &middot; 官方资料，或任意一个交互式 git 分支教程

### 编写流水线

你能从零开始写一个简单的 GitHub Actions workflow 文件——而不是复制一份然后指望它能跑吗？

- [GitHub Actions 快速入门](https://docs.github.com/en/actions/quickstart) &middot; 官方文档，约 2 小时

---

返回[推荐]({{ site.baseurl }}/prerequisites/recommended/)、[必备]({{ site.baseurl }}/prerequisites/essential/)，
或[层级总览]({{ site.baseurl }}/prerequisites/)。

---


### 必备先修条件


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `docs/prerequisites/essential.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/docs/prerequisites/essential.md) · 语言：英文原文 · 中译版



# 必备先修条件
{: .no_toc }

开始之前，你必须熟练掌握以下六项。每一项都拆解为本书所依赖的具体子技能，
并给出一个自测问题和每项子技能一份资源——有合适短片的就用短片，
否则用课程、书籍或官方指南。本节是对
[`Prerequisite_Knowledge.md`]({{ site.repo_blob }}/Prerequisite_Knowledge.md)的展开；
层级总览和学习路径请参见[先修条件]({{ site.baseurl }}/prerequisites/)。

<details open markdown="block">
  <summary>本页内容</summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

## 大语言模型（LLM）基础

本书中的每一种智能体架构都以 LLM 作为推理引擎。你会围绕上下文限制进行设计、
为推理延迟做规划，并依据推理能力选择模型——而这一切都假定你已经知道 LLM
是如何生成文本的。这一节贯穿全书：解码参数（temperature、nucleus sampling）
在 [5.2]({{ site.baseurl }}/curriculum/part-05/)、[5.3]({{ site.baseurl }}/curriculum/part-05/)
和 [6.6]({{ site.baseurl }}/curriculum/part-06/) 中反复出现；上下文窗口与注意力机制出现在
[5.9]({{ site.baseurl }}/curriculum/part-05/)；而量化与精度则贯穿
[第 7 部分]({{ site.baseurl }}/curriculum/part-07/)，处处依赖 transformer 内部机制。

### 神经网络究竟是什么

你能用自己的话解释神经网络在计算什么，以及训练它与运行它有什么不同吗？

<details markdown="block">
<summary>视频</summary>

<div style="margin:0 0 1.5rem 0">
<iframe src="https://www.youtube-nocookie.com/embed/aircAruvnKk" title="But what is a neural network? | Deep learning chapter 1" loading="lazy" style="width:100%;max-width:560px;aspect-ratio:16/9;border:0" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
<div><a href="https://www.youtube.com/watch?v=aircAruvnKk">But what is a neural network? | Deep learning chapter 1</a> &middot; 3Blue1Brown</div>
</div>

</details>

### Transformer 架构

你能在框图层面勾勒出 transformer 如何把一个 token 序列变成对下一个 token 的预测吗？

<details markdown="block">
<summary>视频</summary>

<div style="margin:0 0 1.5rem 0">
<iframe src="https://www.youtube-nocookie.com/embed/wjZofJX0v4M" title="Transformers, the tech behind LLMs | Deep Learning Chapter 5" loading="lazy" style="width:100%;max-width:560px;aspect-ratio:16/9;border:0" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
<div><a href="https://www.youtube.com/watch?v=wjZofJX0v4M">Transformers, the tech behind LLMs | Deep Learning Chapter 5</a> &middot; 3Blue1Brown</div>
</div>

</details>

### 注意力机制与上下文窗口

你能解释注意力机制计算的是什么，以及为什么更长的上下文窗口会消耗更多算力吗？

<details markdown="block">
<summary>视频</summary>

<div style="margin:0 0 1.5rem 0">
<iframe src="https://www.youtube-nocookie.com/embed/eMlx5fFNoYc" title="Attention in transformers, step-by-step | Deep Learning Chapter 6" loading="lazy" style="width:100%;max-width:560px;aspect-ratio:16/9;border:0" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
<div><a href="https://www.youtube.com/watch?v=eMlx5fFNoYc">Attention in transformers, step-by-step | Deep Learning Chapter 6</a> &middot; 3Blue1Brown</div>
</div>

</details>

### 实践中的生成：解码、采样、能力与局限

你能解释贪心解码与 nucleus sampling 的区别以及各自适用的时机，
并说明 temperature 控制的是什么吗？

<details markdown="block">
<summary>视频</summary>

<div style="margin:0 0 1.5rem 0">
<iframe src="https://www.youtube-nocookie.com/embed/zjkBMFhNj_g" title="[1hr Talk] Intro to Large Language Models" loading="lazy" style="width:100%;max-width:560px;aspect-ratio:16/9;border:0" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
<div><a href="https://www.youtube.com/watch?v=zjkBMFhNj_g">[1hr Talk] Intro to Large Language Models</a> &middot; Andrej Karpathy</div>
</div>

</details>

### 提示范式

你知道零样本、少样本和思维链提示在实践中的区别，
以及何时值得为它们付出额外的 token 成本吗？（这方面的深入内容见下方
[Prompt Engineering]({{ site.baseurl }}/prerequisites/beneficial/#prompt-engineering-techniques)。）

- [ChatGPT Prompt Engineering for Developers](https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/) &middot; DeepLearning.AI，约 2 小时，免费

---

## Python 编程

书中的所有代码示例和每个框架（LangChain、LangGraph、AutoGen、CrewAI）都是 Python。
你要阅读框架内部实现、实现智能体并调试故障——复制那些你并不理解的代码，
无法让你走完[第 2 部分]({{ site.baseurl }}/curriculum/part-02/)、
[第 7 部分]({{ site.baseurl }}/curriculum/part-07/)或[第 8 部分]({{ site.baseurl }}/curriculum/part-08/)。

### 函数与关键字参数

你能写出一个接受关键字参数并返回字典的函数吗？

- [Python for Everybody](https://www.coursera.org/specializations/python) &middot; 密歇根大学（Coursera），第 1–3 周，可免费旁听

### 类与对象组合

你能读懂基于类的代码并跟踪方法调用、继承与组合，而不必先在调试器里逐行追踪吗？

- *Fluent Python*（Luciano Ramalho 著），第 1–4 章（函数与对象作为一等公民）

### 异常处理

你会自然而然地使用 `try`/`except`/`finally`，还是写出那种假定一切都不会失败的代码？

- [Python Exceptions: An Introduction](https://realpython.com/python-exceptions/) &middot; Real Python

### 嵌套数据结构与推导式

你能处理包含字典列表的字典，并写出列表推导式或字典推导式，而不必先写一个 `for` 循环吗？

- 练习：动手实现 5–10 个处理嵌套 JSON 形态数据的小程序
  （这正是框架配置和工具响应的形状）

---

## REST API、HTTP 与 API 设计

智能体通过 API 调用工具。多智能体通信、编排协议以及本书中的每一次生产部署，
都假定你熟悉 HTTP。这一节在[1.2]({{ site.baseurl }}/curriculum/part-01/)（工具调用架构）、
[2.6]({{ site.baseurl }}/curriculum/part-02/)（框架的工具调用）、
[第 4 部分]({{ site.baseurl }}/curriculum/part-04/)（微服务部署）和
[第 7 部分]({{ site.baseurl }}/curriculum/part-07/)（推理端点）中都至关重要。

**核心**——从第 1 部分起就需要：

### HTTP 动词与状态码

你能解释 GET 与 POST 的区别，以及 4xx 与 5xx 状态码分别说明问题出在谁身上吗？

- [MDN: An overview of HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview) &middot; 约 2–3 小时

### JSON 与端点设计

你能解析包含嵌套对象的 JSON 响应，并为某个工具设计 REST 端点——动词、参数、响应结构？

- 练习：用 Python 的 `requests` 库调用 3–5 个公开 API 并处理它们的响应

### 超时与故障模式

你理解 API 超时是什么、为什么它对调用工具的智能体很重要，以及超时时应该发生什么吗？

- 在[2.8：错误处理与弹性]({{ site.baseurl }}/curriculum/part-02/)中有实践讲解

**进阶深入**——当你开始设计工具接口或部署架构（而不只是调用现成的 API）时才重要
（第 2 部分工具集成、第 4 部分部署）：

### 认证与速率限制

你在概念层面理解 OAuth/JWT 吗？明白 API 为什么要强制速率限制吗？

- [Stripe API reference](https://docs.stripe.com/api)——把一个设计良好、文档完善的生产级 API 当作范例来读

### 幂等性与 API 网关

你知道幂等性是什么、为什么它对重试很重要，以及 API 网关在一组服务前面增加了什么吗？

<details markdown="block">
<summary>视频</summary>

<div style="margin:0 0 1.5rem 0">
<iframe src="https://www.youtube-nocookie.com/embed/20rOdqag4Dw" title="Kong Gateway Tutorial | API Gateway For Beginners" loading="lazy" style="width:100%;max-width:560px;aspect-ratio:16/9;border:0" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
<div><a href="https://www.youtube.com/watch?v=20rOdqag4Dw">Kong Gateway Tutorial | API Gateway For Beginners</a> &middot; Redhwan Nacef</div>
</div>

</details>

---

## 命令行与 shell 脚本

[第 4 部分]({{ site.baseurl }}/curriculum/part-04/)（部署与扩缩容）和
[第 8 部分]({{ site.baseurl }}/curriculum/part-08/)（运维）都假定你熟练使用终端进行
SSH 访问、容器管理、`kubectl` 和基础设施自动化。本书中的每一个部署步骤都离不开终端。

### 文件系统导航与搜索

你能不借助文件管理器，在 Linux 文件系统中导航并用 `find` 或 `grep` 定位文件吗？

- [The Linux Command Line](https://linuxcommand.org/tlcl.php)（William E. Shotts 著），第 1–10 章（免费 PDF）

### Bash 脚本

你能写出一个包含变量、循环和条件语句的 bash 脚本——比如逐个处理某个目录下的所有文件？

- 练习：针对你自己的文件系统写 3–5 个小型 bash 脚本

### 进程管理与环境变量

你能管理后台进程、把它的输出重定向到文件，并用 `export` 设置/读取环境变量吗？

- 与上面相同的资料，关于作业控制和环境的章节

### 远程访问

你能 `ssh` 登录到远程服务器，并在那里像在本地一样自如地工作吗？

- 练习：启动一台免费套餐云主机，通过 SSH 完成一天的工作

---

## Docker 与容器化基础

[4.1]({{ site.baseurl }}/curriculum/part-04/)直接讲解容器化，
[4.3]({{ site.baseurl }}/curriculum/part-04/)在其之上构建容器编排，而
[第 7 部分]({{ site.baseurl }}/curriculum/part-07/)把每个推理服务器都部署为容器。
这一节无法跳过，否则你无法跟上演示章节。

### 镜像、容器与隔离

你能解释 Docker 镜像与运行中的容器有何不同，以及容器实际上提供了哪些隔离
（文件系统、进程、网络）吗？

<details markdown="block">
<summary>视频</summary>

<div style="margin:0 0 1.5rem 0">
<iframe src="https://www.youtube-nocookie.com/embed/Wf2eSG3owoA" title="Docker and Kubernetes - Full Course for Beginners" loading="lazy" style="width:100%;max-width:560px;aspect-ratio:16/9;border:0" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
<div><a href="https://www.youtube.com/watch?v=Wf2eSG3owoA">Docker and Kubernetes - Full Course for Beginners</a> &middot; freeCodeCamp.org</div>
</div>

在进入 Kubernetes 之前先覆盖 Docker 基础——现在先把 Docker 部分看完，
等学到[Kubernetes 基础]({{ site.baseurl }}/prerequisites/recommended/#kubernetes-fundamentals)时再回来继续。

</details>

### 编写 Dockerfile

你能从一个空白文件出发，用 `FROM`、`COPY`、`RUN` 和 `CMD` 写出 Dockerfile，而不是复制一个现成的？

- [Docker: Getting Started](https://docs.docker.com/get-started/) &middot; 官方教程，约 2 小时

### 卷、网络与端口

你能运行一个容器、映射端口、挂载卷并查看它的日志吗？

- 练习：自己动手写 2–3 个 Dockerfile，运行它们，并故意弄坏一些东西来调试

---

## 机器学习基础

[第 6 部分]({{ site.baseurl }}/curriculum/part-06/)（RAG 与知识整合）建立在嵌入和向量相似度之上。
[第 7 部分]({{ site.baseurl }}/curriculum/part-07/)优化推理的方式，假定你明白模型输出的含义。
[第 9 部分]({{ site.baseurl }}/curriculum/part-09/)讨论算法偏见，这假定你具备评估指标的基本素养。

### 训练 vs. 推理，监督 vs. 无监督

你能解释训练一个模型与在它上面运行推理的区别，以及监督学习与无监督学习的区别吗？

- [Machine Learning Specialization](https://www.coursera.org/specializations/machine-learning-introduction)
  &middot; Andrew Ng（Coursera），前 1–2 周，可免费旁听

### 嵌入与向量相似度

你能解释为什么语义相似度可以作为向量空间中的距离计算来生效吗？

<details markdown="block">
<summary>视频</summary>

<div style="margin:0 0 1.5rem 0">
<iframe src="https://www.youtube-nocookie.com/embed/OATCgQtNX2o" title="Text embeddings &amp; semantic search" loading="lazy" style="width:100%;max-width:560px;aspect-ratio:16/9;border:0" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
<div><a href="https://www.youtube.com/watch?v=OATCgQtNX2o">Text embeddings &amp; semantic search</a> &middot; Hugging Face</div>
</div>

</details>

### 评估指标

你知道精确率（precision）和召回率（recall）各自度量的是什么吗？
明白为什么一个模型可以准确率很高却依然毫无用处吗？

- *Hands-On Machine Learning*（Aurélien Géron 著），第 3 章（分类与指标）

### 过拟合与泛化

你能解释过拟合吗？明白为什么一个在训练数据上得分完美的模型，在生产环境中仍然可能失败？

- *Hands-On Machine Learning*（Aurélien Géron 著），第 4 章；练习：训练一个 scikit-learn
  分类器，并刻意让它过拟合

---

接下来阅读[推荐]({{ site.baseurl }}/prerequisites/recommended/)或
[有益]({{ site.baseurl }}/prerequisites/beneficial/)先修条件，或返回
[层级总览]({{ site.baseurl }}/prerequisites/)。

---


### 先修条件


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `docs/prerequisites/index.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/docs/prerequisites/index.md) · 语言：英文原文 · 中译版



# 先修条件
{: .no_toc }

开始之前需要了解的内容，整理为三个层级，每个层级再拆分为若干主题，
每个主题进一步拆分为具体的子技能，并各配一个自测问题和一份精选资源——
有合适短片的就用短片，否则用课程、书籍或官方指南。本节是对
[`Prerequisite_Knowledge.md`]({{ site.repo_blob }}/Prerequisite_Knowledge.md)的展开，
后者包含完整的叙述版（逐章说明每个主题为何重要）；如果你想了解比这里这些
精简页面更多的背景信息，可以去读它。

<details open markdown="block">
  <summary>本页内容</summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

## 三个层级

浏览下面的层级、通过侧边栏浏览，或直接跳到某个主题——每个层级页面都有自己的目录。

| 层级 | 含义 | 主题 |
|---|---|---|
| [**必备**]({{ site.baseurl }}/prerequisites/essential/) | 你必须理解这些内容，才能从本书中获益 | LLM 基础、Python、REST API 与 API 设计、命令行与 Shell、Docker、机器学习基础 |
| [**推荐**]({{ site.baseurl }}/prerequisites/recommended/) | 没有它们你也能成功，但预计会经常需要查资料 | 软件架构模式、数据库基础、Kubernetes、NLP 基础 |
| [**有益**]({{ site.baseurl }}/prerequisites/beneficial/) | 能加速学习、加深理解，并非必需 | 分布式系统、GPU/CUDA 基础、Prompt Engineering、Python 异步、CI/CD |

与叙述版文档相比有一处调整：“RESTful APIs and HTTP Fundamentals”和
“API Design and REST Principles”在两个深度上覆盖的内容大体相同，因此合并为一个
必备主题——分为“核心”和“进阶深入”两组——而不是在两个层级中重复。

## 快速自评

开始之前，你应当能对以下五项全部回答“是”——如果做不到，每一项都链接到其完整的子主题：

- 我理解 LLM 的工作方式：token、上下文窗口、提示词（[必备 &gt; LLM 基础]({{ site.baseurl }}/prerequisites/essential/#large-language-model-llm-fundamentals)）
- 我能编写并调试中等难度的 Python 代码（[必备 &gt; Python]({{ site.baseurl }}/prerequisites/essential/#python-programming)）
- 我理解 REST API 与 HTTP 基础（[必备 &gt; REST API、HTTP 与 API 设计]({{ site.baseurl }}/prerequisites/essential/#rest-apis-http-and-api-design)）
- 我会使用命令行界面并编写 shell 脚本（[必备 &gt; 命令行]({{ site.baseurl }}/prerequisites/essential/#command-line-and-shell-scripting)）
- 我理解 Docker 容器并能构建镜像（[必备 &gt; Docker]({{ site.baseurl }}/prerequisites/essential/#docker-and-containerization-basics)）

如果这五项中至少四项无法确认，请在开始之前安排两到三周的补齐时间。

## 准备路径

| 路径 | 时长 | 投入 | 覆盖内容 |
|---|---|---|---|
| 最小化 | 2–3 周 | 25–35 小时 | 仅[必备]({{ site.baseurl }}/prerequisites/essential/)，足以开始第 1–2 部分 |
| 推荐 | 4–5 周 | 40–60 小时 | 必备加上[推荐]({{ site.baseurl }}/prerequisites/recommended/) |
| 全面 | 6–8 周 | 60–90 小时 | 必备、推荐以及[有益]({{ site.baseurl }}/prerequisites/beneficial/) |

按背景划分的具体建议（在校学生、软件工程师、ML 从业者、转行人士）位于
[`Prerequisite_Knowledge.md`]({{ site.repo_blob }}/Prerequisite_Knowledge.md#final-recommendations)的最后一节。

---


### 专家参与情况


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `docs/reports/expert-engagement.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/docs/reports/expert-engagement.md) · 语言：英文原文 · 中译版



# 专家参与情况
{: .no_toc }

截至 2026 年 11 月 16 日，共有 19 位受邀为课程做贡献的外部专家正在参与改进工作：其中 12 位已经发布了评审意见或贡献内容，其余的已在 GitHub 上认领了 issue 并正在处理。这些数字只统计上述这些专家。只有当至少 2 位专家共享同一家机构或同一个研究领域时，才会给出机构与研究领域的细分。最近的贡献机构列表只列出机构名称与日期，绝不出现个人姓名。

{::nomarkdown}
{% include nd/expert_engagement.html %}
{:/nomarkdown}

---


### Chapter 1.6C: Stateful Orchestration - Guided and Independent Practice


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/archive/Part_01_Chapter_1.6_Labs.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/archive/Part_01_Chapter_1.6_Labs.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Part 04 Chapter 4.1 Labs2


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/archive/Part_04_Chapter_4.1_Labs2.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/archive/Part_04_Chapter_4.1_Labs2.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Chapter 6, Section 6.3.4-6.3.9: ETL Practice, Pitfalls, and Resources


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/archive/Part_06_Chapter_6.3C_ETL_Practice.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/archive/Part_06_Chapter_6.3C_ETL_Practice.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Chapter 6, Section 6.4.4-6.4.6: Data Quality Practice and Integration


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/archive/Part_06_Chapter_6.4B_Data_Quality_Practice.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/archive/Part_06_Chapter_6.4B_Data_Quality_Practice.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Chapter 6, Section 6.5.4-6.5.6: Production RAG Practice and Monitoring


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/archive/Part_06_Chapter_6.5B_Production_RAG_Practice.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/archive/Part_06_Chapter_6.5B_Production_RAG_Practice.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Part 7 - Chapter 7.2: Local Development Setup and API Integration


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/archive/Part_07_Chapter_7.2A_Local_Development.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/archive/Part_07_Chapter_7.2A_Local_Development.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Simulated failing service


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/archive/Part_08_Chapter_8.2B_Labs.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/archive/Part_08_Chapter_8.2B_Labs.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### AI 101 课程候选清单 — 详细数据集


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `supplemental_course/courses.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/supplemental_course/courses.md) · 语言：英文原文 · 中译版



# AI 101 课程候选清单 — 详细数据集


根据 `plans/course_search_plan.md` 于 2026-07-16 汇编。第 1 轮：7 条
并行搜索线 → 37 条原始条目 → 经跨线去重 + 独立 QA（URL、学费、开课日
期、讲师）后得到 28 门唯一课程。第 2 轮（`plans/course_gap_plan.md`）：
针对第 1 轮覆盖不足的精英/旗舰大学开辟 6 条补缺搜索线 → 新增 18 门
经 QA 验证的课程（D 节）。合计：46 门课程。

入选资格：由大学教授主讲或由可信非营利机构开设；免费或 ≤ 约 $150；
2024 年及以后设立（优先 2025/2026）；入门级；能落实 O1–O3 中的一项
或多项；覆盖 C1–C6 中至少一项。机器可读映射：`course_inventory.csv`。

图例：C1 AI 科学 · C2 AI 系统特性 · C3 政府收益 · C4 风险（歧
视/隐私）· C5 风险缓解/可信 AI · C6 未来趋势/国家安全 · O1 在
岗位中应用 · O2 批判性评估/干预 · O3 治理（安全/隐私/公民权利）

---

## A. 大学课程


### AI Foundations for Business Professionals（面向业务专业人士的 AI 基础，3 门课程专项课程）

- 主办方：牛津大学 Saïd Business School（Coursera）| 类型：大学 | 项目：牛津 2025 年 Coursera/edX 上线项目（21 门课程）
- 讲师：Matthias Holweg 教授，运营管理学教授
- 学费：每门课可免费旁听；证书约 $49/月订阅，可申请助学 | 开设时间：2025 年（牛津 SBS 新闻：课程于 2025 年 6–7 月发布）| 时长：约 40 小时
- 形式：自主进度视频 + 评分作业 | URL: https://www.coursera.org/specializations/ai-foundations-business-professionals
- 覆盖：C1 ML/神经网络/深度学习基础；C2 生成式工具的任务化应用；C4 风险评估、偏见缓解；C5 可信 AI 治理框架；C6 智能体化 AI 的能力与风险 | 目标：O1 在岗位中驾驭 AI 创造价值；O2 评估风险，打造安全/公平/可问责的 AI；O3 治理、合规、数据伦理
- 备注：面向初学者，无需任何前置经验；已报名 2.1 万+，评分 4.8/5；包含下方那门可独立报名的 AI Governance 课程。

### AI Governance（AI 治理）

- 主办方：牛津大学 Saïd Business School（Coursera）| 类型：大学 | 项目：AI Foundations for Business Professionals 专项课程（可单独报名）
- 讲师：Matthias Holweg 教授
- 学费：可免费旁听；证书约 $49 | 开设时间：2025 年（archive.org 首次抓取于 2025-07-23；首批评价出现在 2025 年 11 月）| 时长：约 2 周
- 形式：自主进度视频 + 同行评审作业 | URL: https://www.coursera.org/learn/ai-governance
- 覆盖：C1 AI 系统为何失败/如何失败；C4 偏见、目标错位、过度依赖；C5 可信 AI 循环、风险管理、红队测试；C6 面向未来的落地实施策略 | 目标：O1 实施决策以及自建还是采购的判断；O2 失效模式与过度依赖；O3 AI 全生命周期中的问责
- 备注：面向初学者；已报名 1.2 万+，评分 4.8/5；在各大学 MOOC 条目中，对 C5 的单门课程处理最为出色。

### Foundations of Generative AI（生成式 AI 基础）

- 主办方：佐治亚理工学院（GTx，edX）| 类型：大学 | 项目：无
- 讲师：David Joyner 博士，在线教育执行主任兼 OMSCS 主任
- 学费：可免费旁听；认证证书 $90 | 开设时间：2025 年（edX 新闻稿，2025-10-16）| 时长：3 周，每周 2–3 小时
- 形式：自主进度视频 + 模块 | URL: https://www.edx.org/learn/artificial-intelligence/the-georgia-institute-of-technology-introduction-to-genai
- 覆盖：C1 AI 的历史、神经网络、transformers；C2 生成式 AI 是什么；C4 模型对齐的伦理；C5 生成式 AI 对齐模块；C6 生成式 AI 为何重要以及技术前沿现状 | 目标：O1 理解专业人士赖以工作的工具；O2 "驾照"式的 AI 素养——理解而不只是会用
- 备注：共 10 个模块，无需任何前置经验；对 C1 的概念覆盖干净利落。

### AI Literacy for Everyone（人人可用的 AI 素养，6 门课程专项课程）

- 主办方：密歇根大学（Coursera）| 类型：大学 | 项目：U-M Center for Academic Innovation 生成式 AI 系列（35+ 门课程）
- 讲师：U-M 多学科教师团队（法律、NLP、经济学、传播学）
- 学费：每门课可免费旁听；证书需约 $49/月订阅 | 开设时间：2024 年（U-M CAI：35+ 门生成式 AI 课程于 2024 年 7 月前上线）| 时长：约 30 小时
- 形式：自主进度视频 + 作业 | URL: https://www.coursera.org/specializations/ai-literacy-for-everyone
- 覆盖：C1 生成式 AI/ML 模型的工作原理；C2 生成式 AI 工具、提示词工程；C3 商业场景中的生成式 AI（可迁移到政府场景）；C4 伦理与法律影响；C5 负责任 AI 实践与监管；C6 劳动与工作的未来 | 目标：O1 将生成式 AI 融入日常工作；O2 用生成式 AI 做批判性思考；O3 伦理、署名、监管
- 备注：面向初学者；评分 4.7/5（539 条评价）；在所有单个候选中 C/O 覆盖最广；锚定课程日期为 2023 年 12 月——该专项课程才是 2024+ 的组成部分。

### Generative AI: Governance, Policy, and Emerging Regulation（生成式 AI：治理、政策与新兴监管）

- 主办方：密歇根大学（Coursera）| 类型：大学 | 项目：Responsible Generative AI 专项课程
- 讲师：Merve Hickok，密歇根大学信息学院讲师；Center for AI and Digital Policy 主席
- 学费：可免费旁听；证书约 $49 | 开设时间：2024 年（U-M CAI 2024 年上线；首批评价 2024 年 7 月）| 时长：约 3 小时
- 形式：自主进度视频 + 阅读材料 | URL: https://www.coursera.org/learn/generative-ai-governance-policy-and-emerging-regulation
- 覆盖：C4 风险与影响评估；C5 负责任 AI 原则、透明度；C6 美国/欧盟/G7 新兴监管 | 目标：O1 围绕 AI 采纳的治理决策；O3 政策、监管、问责
- 备注：需注意——Coursera 将其标注为"中级"（有一条搜索线据此将其排除），但内容简短、非技术化，且经评价确认易于上手；授课者是全国知名的 AI 政策专家。

### AI Fundamentals（AI 基础）

- 主办方：利兹大学（FutureLearn）| 类型：大学 | 项目：Click Start（Institute of Coding + Nominet）
- 讲师：Sam Wilson 博士，计算机科学学院副教授
- 学费：免费；通过 Click Start 可免费升级为数字证书（标准价 $54）| 开设时间：2024 年（archive.org 2024-09-19）| 时长：2 周，每周 4 小时
- 形式：自主进度视频 + 活动 + 测评 | URL: https://www.futurelearn.com/courses/how-to-get-into-ai
- 覆盖：C1 AI 从 1940 年代演进到 LLMs；C2 动手实操 AI 工具；C4 伦理/法律/社会挑战；C6 未来的影响 | 目标：O1 用 AI 提升职场生产力；O2 通过伦理活动实现负责任使用
- 备注：简短的非技术入门课；FutureLearn 上由非营利资金支持的免费证书路径十分罕见。

### Unleash Your Potential: AI Fundamentals（释放你的潜能：AI 基础）

- 主办方：布里斯托大学（FutureLearn）| 类型：大学 | 项目：AI for Collective Intelligence (AI4CI) 中心
- 讲师：Seth Bullock 教授（数据科学与 AI 领域 Toshiba 教席）；Genevieve Liveley 教授
- 学费：免费（免费升级为数字证书）| 开设时间：2026 年（布里斯托新闻，2026 年 2 月）| 时长：4 周，每周约 3 小时
- 形式：自主进度视频 + 案例研究 | URL: https://www.futurelearn.com/courses/unleash-your-potential-ai-fundamentals
- 覆盖：C1 基本概念、AI 的工作原理；C2 跨行业案例研究；C3 各行业的应用（间接）；C4 伦理、风险、偏见；C5 AI 安全、可持续性 | 目标：O1 在工作中使用 AI；O2 对 AI 能力进行批判性思考
- 备注：最新的英国条目（2026 年 2 月）；供稿人横跨法律、网络安全、医学、哲学等领域。

### Foundation Models and Generative AI (6.S087)（基础模型与生成式 AI）

- 主办方：MIT OpenCourseWare | 类型：大学 | 项目：MIT EECS / OCW
- 讲师：Rickard Brüel Gabrielsson，MIT EECS/CSAIL
- 学费：免费（不提供证书）| 开设时间：2024 年（IAP 2024；OCW 于 2024 年发布）| 时长：约 4 周的系列讲座
- 形式：自主进度讲座视频 | URL: https://ocw.mit.edu/courses/6-s087-foundation-models-and-generative-ai-january-iap-2024/
- 覆盖：C1 自监督学习 → 基础模型；C2 ChatGPT/DALL-E/Copilot 系统；C6 基础模型正在改变科学与商业 | 目标：O1 在业务/科学工作流中的应用
- 备注："非技术性的系列讲座……欢迎所有背景的学员"；在本数据集中 C1 深度最强。

### Free Online Certificate in Artificial Intelligence and Career Empowerment（人工智能与职业赋能免费在线证书）

- 主办方：马里兰大学 Robert H. Smith 商学院 | 类型：大学 | 项目：Smith Executive Education
- 讲师：Balaji Padmanabhan，决策、运营与 IT 领域院长级教授（另有 11 位 Smith 学院教师）
- 学费：免费，含证书 | 开设时间：2025 年 5 月 1 日（PRNewswire；Maryland Today）| 时长：10 个自主进度模块
- 形式：自主进度视频 + 行业专家访谈 | URL: https://www.rhsmith.umd.edu/programs/executive-education/learning-opportunities-individuals/free-online-certificate-artificial-intelligence-and-career-empowerment
- 覆盖：C1 AI 素养/能力；C2 AI 解决方案是如何构建的；C3 为联邦公务员转型而设计；C5 负责任 AI 模块 | 目标：O1 在各职能/职业中应用 AI；O2 在工作流中评估 AI；O3 组织内的负责任 AI
- 备注：明确面向处于职业转型期的联邦政府雇员；截至 2025 年 8 月已报名 37,000+ 人。

### GenAI 101（生成式 AI 101）

- 主办方：印第安纳大学 Kelley 商学院 | 类型：大学 | 项目：Kelley Learn AI 计划
- 讲师：Brian Williams，Sam Frumer 会计学教授
- 学费：免费，含数字徽章 | 开设时间：2025 年 8 月（IU）；2026 年 4 月面向全球（IU News）| 时长：8 个模块 / 16 节
- 形式：自主进度短视频 + 交互式 AI 导师 | URL: https://kelley.iu.edu/learnAI
- 覆盖：C2 跨 ChatGPT/Claude/Gemini 的提示词工程；C5 合乎伦理的 AI 使用 | 目标：O1 20 项职场可用的技能；O2 对 AI 生成内容进行事实核查
- 备注：无需技术背景；可分享的 LinkedIn 凭证。

### AI Whisperer: A Microcourse in Crafting Prompts for Generative AI（AI Whisperer：为生成式 AI 撰写提示词的微课程）

- 主办方：南佛罗里达大学 Bellini 人工智能、网络安全与计算学院 | 类型：大学 | 项目：USF 微证书
- 讲师：John Licato 副教授（与 Tempestt Neal、Sudeep Sarkar 教授共同授课）
- 学费：免费；可选 $39 数字徽章 | 开设时间：2025 年 10 月 28 日（USF 发布）| 时长：3–4 小时
- 形式：在 Canvas Network 上自主进度 | URL: https://www.usf.edu/innovative-education/usf-microcredentials/a-microcourse-in-crafting-prompts.aspx
- 覆盖：C1 ML/生成式 AI 基础单元；C2 工具选型 + 提示词工程 | 目标：O1 生成与岗位相关的报告/演示文稿；O2 判断输出质量
- 备注：本数据集中投入时间最少的课程；适合作为第一门课；同学院还配套有"GenAI in Action"微课程。

### Introduction to AI Literacy（AI 素养入门）

- 主办方：阿卡迪亚大学（Open Acadia）| 类型：大学 | 项目：Open Acadia 继续教育
- 讲师：Daniel Lametti 博士，心理学系
- 学费：免费，含证书 | 开设时间：2026 年初（阿卡迪亚新闻中心 2026-03-05；CBC）| 时长：约 2.5 小时
- 形式：自主进度模块（讲座、播客、论坛）| URL: https://explore.acadiau.ca/product?catalog=AI-Literacy
- 覆盖：C1 AI 是什么、如何工作；C2 ChatGPT/Claude 一类工具；C4 局限性与过度依赖风险；C5 负责任使用 | 目标：O1 何时以及如何在工作中使用 AI；O2 人与 AI 在思考方式上的差异
- 备注：认知科学视角直接支撑 O2；头两周报名 5,000+ 人。

### Trustworthy AI: Managing Bias, Ethics, and Accountability（可信 AI：管理偏见、伦理与问责）

- 主办方：约翰斯·霍普金斯大学（Coursera）| 类型：大学 | 项目：JHU AI 系列
- 讲师：Ian McCulloh，博士，JHU 高级科学家/讲师
- 学费：可免费旁听；证书约 $49 | 开设时间：2024 年末/2025 年 1 月（archive.org 2025-01-09）| 时长：约 2 周，4 个模块
- 形式：自主进度视频 + 9 项作业 | URL: https://www.coursera.org/learn/responsible-ai-and-ethics
- 覆盖：C1 人为偏见与机器偏见的机制差异；C4 算法偏见、隐私、漂移；C5 基于风险的负责任 AI、监管 | 目标：O2 对 AI 输出做更公平的风险评估；O3 偏见、隐私、监管、问责
- 备注：非技术、以案例驱动；虽标注为"中级"但无正式先修要求；对差别影响（disparate impact）这一锚点覆盖扎实。

### Artificial Intelligence in National Security（国家安全中的人工智能）

- 主办方：伦敦国王学院战争研究系（edX）| 类型：大学 | 项目：Grand Strategy 专业证书（可单独学习）
- 讲师：Kenneth Payne 教授，战略学教授
- 学费：可免费旁听；证书 $249（超出上限——走旁听路径即符合要求）| 开设时间：2025 年 7 月 3 日（KCL 课程目录；archive.org 2025-06-23）| 时长：5 小时
- 形式：自主进度在线短课程 | URL: https://www.edx.org/learn/social-sciences/kings-college-london-artificial-intelligence-in-national-security
- 覆盖：C2 自主性、数据、AI 决策系统；C3 国防/国家治理中的战略 AI；C4 伦理/法律挑战；C6 AI 军备竞赛、国家间竞争 | 目标：O2 人类决策与自主系统之比较；O3 AI 安全系统的伦理/法律/治理
- 备注：顶尖战争研究学者（《I, Warbot》作者）；直接覆盖自主系统与国家安全政策这两个概念锚点。

### Generative AI Cybersecurity & Privacy for Leaders: A Primer（面向领导者的生成式 AI 网络安全与隐私入门）

- 主办方：范德堡大学（Coursera）| 类型：大学 | 项目：GenAI Cybersecurity & Privacy for Leaders 专项课程
- 讲师：Jules White 博士，计算机科学教授兼副院长；Sam Hays 博士
- 学费：可免费旁听；付费证书可选 | 开设时间：2024 年 12 月–2025 年 1 月（archive.org 2025-01-17）| 时长：4 小时，5 个模块
- 形式：自主进度视频 + 提示词练习 | URL: https://www.coursera.org/learn/generative-ai-security-privacy
- 覆盖：C2 生成式 AI 特性、安全的提示词使用；C4 错误信息、深度伪造、网络钓鱼、隐私；C5 组织层面准备度、桌面推演；C6 深度伪造/舆论操纵威胁 | 目标：O1 在工作中安全地使用生成式 AI；O2 识别深度伪造与错误信息；O3 个人与组织层面的隐私/安全治理
- 备注：面向初学者，评分 4.8/5；对合成媒体这一锚点覆盖最强；面向非技术领导者设计。

### AI Literacy for Life & Work（生活与工作中的 AI 素养）

- 主办方：大谷州立大学计算机学院 | 类型：大学 | 项目：GVSU 社区课程/证书
- 讲师：Marouane Kessentini，计算机学院院长（另有 4 位教师）
- 学费：免费；付费数字证书/徽章可选 | 开设时间：2026 年 3 月 2 日（GVNext 2026-02-24）| 时长：7 个模块，8–10 小时
- 形式：自主进度视频 + 阅读材料 + 活动 | URL: https://www.gvsu.edu/computing/ai-community-coursecertificate-258
- 覆盖：C1 AI 系统如何运作；C2 核心概念、与 AI 沟通；C4 偏见、伦理/环境影响；C5 负责任使用 | 目标：O1 职场应用模块；O2 评估输出的准确性与偏见
- 备注：2026 年全新上线，有院长级别背书，无需写代码。

## B. 大学–非营利机构合作


### AI and Digital Transformation in Government（政府中的 AI 与数字化转型）

- 主办方：牛津大学 Saïd Business School + UNESCO（SPARK-AI Alliance）| 类型：大学/政府间组织 | 项目：Oxford Saïd Online / UNESCO AI for the Public Sector
- 讲师：牛津 Saïd 师资团队（项目负责人：Caroline Williams，Oxford Saïd Online 执行董事；无单一署名教授）
- 学费：免费（由 UNESCO 资助）；牛津/UNESCO 联合证书 | 开设时间：2025 年 11 月 10 日（UNESCO 公告）| 时长：约 12 小时
- 形式：自主进度在线课程；英语/西班牙语（后续会增加更多语种）| URL: https://www.sbs.ox.ac.uk/programmes/executive-education/online-learning/ai-and-digital-transformation-government
- 覆盖：C2 生成式 AI 工具实操；C3 政府服务供给、包容性设计；C4 AI 与人权模块；C5 伦理 + 数据治理模块；C6 数字化转型领导力 | 目标：O1 在公共部门工作中应用生成式 AI；O2 基于权利评估自动化决策；O3 人权、数据治理、包容性
- 备注：由 7 条搜索线中的 4 条独立检索到——本数据集中与公务员契合度最高的单项；到 2026 年中已有 192 个国家 30,000+ 学员；收益论述面向一般政府而非美国联邦政府。

### AI, Justice and Rule of Law（AI、正义与法治）

- 主办方：UNESCO + 牛津大学（Saïd、Blavatnik School、法学院）| 类型：大学/政府间组织 | 项目：UNESCO AI and Rule of Law 计划
- 讲师：Ignacio Cofone 教授，AI 法与监管学教授（学术负责人）
- 学费：免费 | 开设时间：2026 年 4 月 27 日（英文版；UNESCO / law.ox.ac.uk）| 时长：约 18 小时，6 个模块
- 形式：自主进度 MOOC | URL: https://secure.sbs.ox.ac.uk/corporate/landingPage.do?method=load&corporateGroupId=7948447 (公告：https://www.law.ox.ac.uk/content/news/faculty-law-co-creates-new-online-course-ai-justice-and-rule-law)
- 覆盖：C4 偏见、公平审判与 AI 证据风险；C5 保障措施、透明度、说理决定的权利；C6 未来司法体系中的 AI 决策支持 | 目标：O2 评估算法输出、防止过度依赖；O3 AI、法律与人权治理
- 备注：面向法官/律师/政策制定者，但向全球开放，无需技术背景；法语/西班牙语版于 2026 年 6 月推出。

## C. 非营利机构课程


### Responsible AI for Public Professionals（面向公共部门从业者的负责任 AI）

- 主办方：InnovateUS（Burnes Center for Social Change，东北大学 + The GovLab）| 类型：非营利 | 项目：InnovateUS 自定进度课程
- 讲师：项目由东北大学教授 Beth Simone Noveck 领衔，她同时担任新泽西州首席 AI 战略官（100+ 位专家供稿）
- 学费：免费，含证书 | 开设时间：2024 年 7 月（InnovateUS 上线公告，2024-07-11）| 时长：2 个部分，约 1 小时 45 分钟（24 段短视频）
- 形式：自主进度视频 + 生成式 AI 实操演示（与平台无关）| URL: https://innovate-us.org/course/responsible-ai-for-public-professionals/ （第 1 部分也可作为"Using Generative AI at Work"单独学习）
- 覆盖：C1 生成式 AI 是什么；C2 生成式 AI 工具与最佳实践；C3 日常政府工作；C4 风险、偏见、隐私、深度伪造；C5 负责任使用实践 | 目标：O1 为生成式 AI 挑选合适的工作任务；O2 保护敏感数据、核查输出；O3 安全、伦理、社会性挑战
- 备注：已被新泽西州、纽约州（10 万+ 雇员）、佐治亚州、华盛顿特区全州采用（DC 是首个强制负责任 AI 培训的城市）；每六个月刷新一次；符合 WCAG 2.1 无障碍标准。

### Responsible AI for Public Organizations（面向公共机构的负责任 AI）

- 主办方：InnovateUS（Burnes Center，东北大学）| 类型：非营利 | 项目：InnovateUS 自定进度课程
- 讲师：Burnes Center/GovLab 团队，由 Beth Simone Noveck 领衔
- 学费：免费，含证书 | 开设时间：2025 年（QA：未出现在 InnovateUS 2024 年 10 月的课程清单中；首次归档抓取于 2025 年 8 月）| 时长：2 个部分，约 2 小时
- 形式：自主进度视频 + 讲义 | URL: https://innovate-us.org/course/responsible-ai-for-public-organizations/
- 覆盖：C1 AI 方法概览；C2 AI 基础、数据质量；C3 发现/筛选本机构的 AI 项目；C4 生成式 AI 特有的风险；C5 NIST AI RMF、可信 AI 特征、伦理工具包 | 目标：O1 在所在机构设计/实施 AI 项目；O2 上线前套用风险框架；O3 治理、人才与伦理工具包
- 备注：极少数直接向政府职员讲授 NIST AI RMF 的免费课程之一；是面向个人层面的课程的机构级配套版本。

### Responsible AI for Public Sector Legal Professionals（面向公共部门法律专业人士的负责任 AI）

- 主办方：InnovateUS（联合 AI for Impact、Burnes Center、Reboot Democracy、GovLab）| 类型：非营利 | 项目：InnovateUS 自定进度课程
- 讲师：课程由 Burnes Center 团队（Beth Simone Noveck）主导；20+ 位公共部门资深法律顾问参与
- 学费：免费；在部分州可计入 CLE 学分 | 开设时间：2025 年夏季（rebootdemocracy.ai）| 时长：2 个部分，自主进度
- 形式：自主进度视频 + 实操活动 | URL: https://innovate-us.org/course/responsible-ai-for-public-sector-legal-professionals/
- 覆盖：C1 讲解生成式 AI 与 ML；C2 生成式 AI 日常演示；C3 政府法律实务中的 AI；C4 风险、敏感信息保护；C5 撰写 AI 治理政策；C6 社会性挑战 | 目标：O1 政府法律工作流中的生成式 AI；O2 负责任使用的关键问题；O3 数据治理、政策撰写
- 备注：通过全国州检察长协会（National Association of Attorneys General）推广；与自动化流程的人类监督直接相关。

### A Human Rights-Based Approach to AI（基于人权的 AI 方法论）

- 主办方：Global Campus of Human Rights（联合丹麦人权研究所、贝尔法斯特女王大学、Raoul Wallenberg Institute）| 类型：非营利 | 项目：GC 人权 MOOC 系列
- 讲师：Thérèse Murphy（QUB）、Line Gamrath Rasmussen（DIHR）、Sue Anne Teo（RWI）；包括 David Kaye（UC Irvine）
- 学费：免费（无费用）| 开设时间：首期 2025 年 2 月 17 日–3 月 23 日 | 时长：5 周，约 6 小时
- 形式：同期制 MOOC（材料在两期之间持续开放）| URL: https://elearning.gchumanrights.org/courses/course-v1:gchumanrights+HRBAtoAI+2025/about
- 覆盖：C2 生成式 AI 模块；C3 公共部门中的 AI 模块；C4 AI 造成的人权侵害；C5 基于权利的方法的实际应用 | 目标：O2 审视自动化系统对人权的影响；O3 公民权利、歧视、公共部门治理
- 备注：本数据集中公民权利框架最突出的一项；QA（2026 年 7 月）：2025 年期报名目前已关闭，2026 年期尚未发布——持续关注下一期。

### AI Safety, Ethics, and Society（AI 安全、伦理与社会）

- 主办方：Center for AI Safety (CAIS) | 类型：非营利 | 项目：《AI Safety, Ethics, and Society》教科书课程
- 讲师：Dan Hendrycks，CAIS 主任（教科书作者）；引导式讨论
- 费用：免费（按申请分班） | 开设时间：2024 年（首批学员为 2024 年 7 月—10 月，240 人） | 时长：约 13 周，每周约 5 小时
- 形式：线上分班；阅读材料 + 讲座 + 讨论 + 结业项目 | URL：https://www.aisafetybook.com/virtual-course
- 覆盖能力(Cs)：C1 AI 基础、深度学习、规模定律；C4 恶意滥用、偏见、失控 AI 风险；C5 安全工程、风险管理；C6 国家/国际/算力治理 | 覆盖目标(Os)：O2 监测、鲁棒性、人类控制；O3 企业/国家/国际治理
- 备注：面向非技术受众设计（含可选的基础入门周）；配套 Routledge 教科书；国家安全（natsec）框架特征鲜明。

### Responsible AI Foundations（负责任 AI 基础课程系列）

- 主办方：All Tech Is Human（在 LinkedIn Learning 上，已免费解锁） | 类型：非营利 | 项目：Responsible AI Foundations 专业证书
- 讲师：Renée Cummings，弗吉尼亚大学数据科学实践教授；Rebekah Tweed，ATIH 执行总监
- 费用：免费（由 Patrick J. McGovern Foundation 资助） | 开设时间：2025 年 10 月（5 门课程）；证书路径 2026 年 2 月 | 时长：数小时，4–5 门短课
- 形式：自主进度视频 | URL：https://alltechishuman.org/rai-courses
- 覆盖能力(Cs)：C4 识别/理解 AI 风险；C5 缓解风险、将治理落地；C6 治理智能体化 AI | 覆盖目标(Os)：O2 风险识别与缓解实践；O3 AI 治理格局与角色
- 备注：面向实践者，无先修要求；适合正在搭建治理体系的专业人士。

### AI in National Security: Integrating Artificial Intelligence into Public Sector Missions（国家安全中的 AI：将人工智能融入公共部门任务）

- 主办方：Special Competitive Studies Project (SCSP)（Coursera） | 类型：非营利 | 项目：AI + AGI in National Security 微证书（3 门免费课程）
- 讲师：Ylli Bajraktari（SCSP 总裁、前 NSCAI 执行主任）；Jack Shanahan 陆军中将（退役，首任 DoD JAIC 主任）
- 费用：免费 | 开设时间：2025 年 3 月（PRNewswire；archive.org 2025-03-11） | 时长：5 小时，4 个模块
- 形式：自主进度视频 + 实操练习 | URL：https://www.coursera.org/learn/ai-national-security
- 覆盖能力(Cs)：C1 在实际应用模块中界定 AI；C2 GenAI 工具演示；C3 公共部门任务应用、Agency AI Playbook；C5 负责任采用手册；C6 国家安全中的 AI 大趋势 | 覆盖目标(Os)：O1 为你的任务发挥 AI 工具的价值；O3 机构 AI 采用战略
- 备注：专为联邦/国家安全人员打造；NSCAI 的非营利继任者；报名 6.9k 人，评分 4.6/5；与 C6 要求最接近的单一匹配项。

### The Future of AI（AI 的未来）

- 主办方：BlueDot Impact | 类型：非营利 | 项目：BlueDot AI 安全课程体系
- 讲师：BlueDot Impact 课程团队
- 费用：免费（完成课程可获证书） | 开设时间：2025 年 3 月（发布公告；archive.org 2025-04-26） | 时长：约 2 小时，4 个单元
- 形式：自主进度，视频 + 交互式演示 | URL：https://bluedot.org/courses/future-of-ai
- 覆盖能力(Cs)：C1 当前 AI 能力；C4 AI 赋能的网络攻击、威权主义滥用；C6 未来十年的 AI 发展轨迹 | 覆盖目标(Os)：O2 批判性地权衡能力/风险主张；O3 社会韧性、政策参与
- 备注：为完全非专业背景者提供 2 小时的入门铺垫，之后再进入深入学习。

### AGI Strategy（AGI 战略）

- 主办方：BlueDot Impact | 类型：非营利 | 项目：BlueDot AI 安全课程体系
- 讲师：BlueDot 教学研究员（AI 安全/治理从业者；每班约 8 人）
- 费用：免费 / 自愿付费 | 开设时间：2025 年（archive.org 2025-08-25） | 时长：约 25 小时（5 周或 5 天密集班）
- 形式：分班学习 —— 阅读材料 + 每周引导式讨论 | URL：https://bluedot.org/courses/agi-strategy
- 覆盖能力(Cs)：C4 高级 AI 滥用的威胁分析；C5 战略性风险降低干预措施；C6 AGI 发展轨迹、实验室与国家的竞争 | 覆盖目标(Os)：O2 对 AI 发展主张做压力测试；O3 面向政策专业人员的治理/安全战略
- 备注：招收政策、安全、法律、情报领域专业人士；按申请排期；natsec 细分领域中最好的实时分班选项。

### It's Not Just Business – AI Risks, Rewards and Responsibilities（不只是商业 —— AI 的风险、回报与责任）

- 主办方：The Alan Turing Institute | 类型：非营利 | 项目：Turing Online Learning Platform（BridgeAI）
- 讲师：A.E. Jaques 博士与 Milo Phillips-Brown 博士（课程作者）
- 费用：免费（CC-BY-4.0 素材） | 开设时间：2024 年 11 月 13 日（Zenodo 记录 14137369） | 时长：1–5 小时
- 形式：线上自主进度 + 开放工作坊材料 | URL：https://www.turing.ac.uk/courses/its-not-just-business-ai-risks-rewards-and-responsibilities
- 覆盖能力(Cs)：C2 生成式 AI 的实操案例；C4 预判社会影响；C5 CAIR3 负责任设计-开发-部署框架 | 覆盖目标(Os)：O2 预先防范不可接受的部署风险；O3 社会/环境责任治理
- 备注：英国国家 AI 研究院；范围比完整的素养类课程更窄 —— 最适合作为治理方面的补充。

---

## 近似匹配项（已去重；恰好不满足一项标准）


开设时间（2024 年之前，且没有带日期的重开）：Elements of AI（Helsinki，2018）；Ethics of AI（Helsinki，2020）；AI: Ethics & Societal Challenges（Lund，约 2020）；AI Strategy and Governance（Wharton，2021）；Trustworthy Generative AI（Vanderbilt，2023 年 11 月）；Generative AI Essentials（U-M 独立课程，2023 年 12 月）；AI Ethics and Governance（Turing Commons，2022）；Media Literacy in the Age of Deepfakes（MIT，2021）；AI in Society（Helsinki/Una Europa，2022）；An Introduction to AI（OpenLearn，2022）；GenAI in Action v2.0（USF —— 未见重开记录）；AI Government Leadership Program（Partnership for Public Service，原版 2019）；AI for Everyone（Universiti Malaya —— 日期无法核实）。

费用：AI for Work and Life（北佛罗里达大学，现价 $249）；NACo AI Leadership Academy（约 $1,000）；AI for the Public Sector（Georgia Tech PE，$795）；AI Security XACS134（Stanford，$545）；HarvardX ML/AI with Python（证书 $299 + 先修要求）。

先修要求/难度：Responsible and Ethical AI（Northeastern，要求 Python）；Explainable AI Specialization（Duke，中级）；Frontier AI Governance（BlueDot，要求先修 AGI Strategy）；Intro to AI for Cybersecurity（JHU，中级）。

访问限制：AI Essentials（Holyoke CC，限马萨诸塞州居民）；Free Workforce AI（Mississippi Gulf Coast CC —— Intel 厂商课程体系）；GovEx AI Track（JHU，仅限指定城市）；FPF 培训（仅限会员）；CWCT AI Literacy（Purdue NW，资格受限）；Getting Started with GenAI（OU Click Start，英国 18–30 岁，已关闭）；NPS CHDS 自学（仅限政府关联人员）；Horizon AI Policy Workshop（需申请遴选）；Government AI Campus（Apolitical —— 营利性提供方）；AI Fluency（OpenLearn —— 内容由 Microsoft 撰写）。

---

## D. 差距分析补充项（2026-07-16，依据 plans/course_gap_plan.md）


6 条线索的差距扫描共发现 18 门课程（Stanford/Berkeley/CMU；Harvard/MIT；常春藤盟校及私立院校；
州立旗舰大学；国际精英院校；按平台最新优先的复查）。所有条目均经发现智能体实时抓取验证，
并由 2 个智能体的 QA 流程复核（截至 2026 年 7 月的费用/可报名情况）。注意：Coursera 已对部分
较新课程取消免费旁听 —— 下面三条属于 Coursera Plus/付费报名（约 $59/月，7 天免费试用），
并已作出相应标注。

### AI Fundamentals for Public Servants: Opportunities, Risks and Strategies（面向公务员的 AI 基础：机遇、风险与策略）

- 主办方：Stanford Online + Stanford HAI（通过 Apolitical 交付） | 类型：高校 | 项目：Stanford HAI Policymaker Education
- 讲师：Stanford HAI 的教师、讲师与研究员（公开页面未公布具体姓名）
- 费用：免费（免费名额，先到先得） | 开设时间：2024 年 8 月 12 日（Apolitical 新闻稿；archive.org 2024-09-05） | 时长：自主进度微课程
- 形式：自主进度视频（Apolitical 平台） | URL：https://apolitical.co/microcourses/en/ai-fundamentals-for-public-servants-opportunities-risks-and-strategies/
- 覆盖能力(Cs)：C1 AI 的工作原理；C2 能力/局限；C3 政府应用场景；C4 偏见、信任、风险；C5 以人为本的伦理框架；C6 未来的监管变化 | 覆盖目标(Os)：O1 在政府工作中发挥 AI 的价值；O2 理解局限与风险；O3 监管、偏见、伦理
- 备注：已有 1,700+ 名公务员报名（HAI 新闻，2025 年 1 月）。QA：需要一个免费的 Apolitical 账号，且账号限公务员/政策制定者使用 —— 契合本数据集的受众定位，但并非完全向公众开放。

### The AI Awakening: Implications for the Economy and Society（AI 的觉醒：对经济与社会的影响）

- 主办方：Stanford School of Engineering / Stanford Online（Coursera） | 类型：高校 | 项目：Stanford Online（SOE-YCS0028）
- 讲师：Erik Brynjolfsson，Stanford 教授；Stanford Digital Economy Lab 主任
- 费用：QA 修正 —— Coursera Plus/付费报名（约 $59/月，7 天免费试用）；已不再提供免费旁听 | 开设时间：2024 年（archive.org 2024-01-11） | 时长：约 4 小时，3 个模块
- 形式：自主进度视频 | URL：https://www.coursera.org/learn/ai-awakening
- 覆盖能力(Cs)：C1 生成式 AI 背后的技术；C2 数据与人在模型中的角色；C3（间接）经济/劳动力的政策洞见；C4 生成式 AI 的风险；C6 近未来的转型 | 覆盖目标(Os)：O1 组织如何使用 GenAI；O2 能力与边界
- 备注：报名 1.2 万人，评分 4.7/5；客座嘉宾包括 Eric Schmidt、Mira Murati；治理内容偏弱（无 C5/O3）。

### The Science and Implications of Generative AI（生成式 AI 的科学与影响，开放课程存档）

- 主办方：Harvard Kennedy School | 类型：高校 | 项目：DPI-681M 课程系列
- 讲师：Sharad Goel，公共政策教授；Dan Levy；Teddy Svoronos（均为 HKS）
- 费用：免费（CC BY 4.0 开放存档） | 开设时间：2024 年春季（HKS 新闻，2024 年 4 月 23 日） | 时长：11 次课，约 15.5 小时视频 + 材料
- 形式：自主进度的开放存档 —— 讲课视频、课前材料、从业者讨论 | URL：https://generative-ai-course.hks.harvard.edu/spring-2024
- 覆盖能力(Cs)：C1 LLM、深度神经网络；C2 提示词、RAG、微调；C3 面向政策制定者、公共部门案例；C4 滥用、错误信息、不平等；C5 对齐、缓解措施、版权；C6 社会性颠覆、工作的未来 | 覆盖目标(Os)：O1 提示词工程、何时该落地；O2 局限性与决策依据；O3 版权、政策、虚假信息治理
- 备注：差距扫描中最有力的发现 —— 由三位 HKS 教师专为非技术背景的公共部门领导者打造；静态存档（无分班/证书）；带实况互动的高管版售价 $1,995（属近似匹配项）。

### How to AI (Almost) Anything (MAS.S60)（如何用 AI 做（几乎）任何事）

- 主办方：MIT Media Arts and Sciences（通过 MIT OCW） | 类型：高校 | 项目：MIT OCW
- 讲师：Paul Liang 教授，MIT Media Lab
- 费用：免费（OCW，CC 授权） | 开设时间：2025 年春季（OCW 页面；公开课程网站 + 讲课视频） | 时长：完整学期，约 26 次课
- 形式：OCW 自主进度 —— 幻灯片、视频、阅读材料 | URL：https://ocw.mit.edu/courses/mas-s60-how-to-ai-almost-anything-spring-2025/
- 覆盖能力(Cs)：C1 深度学习与基础模型；C2 多模态 AI（语言、视觉、音频、传感器）；C3（间接）将 AI 应用于真实世界的数据；C4 奖励设定缺陷、越狱（jailbreak）；C5 安全与可靠性专题周；C6 前沿多模态/智能体化 AI | 覆盖目标(Os)：O1 将 AI 应用于自身领域/数据；O2 应用 AI 时的批判性思维
- 备注：注意 —— 按研究生节奏编排并含研究环节；无治理模块（缺少 O3）；最适合对技术有好奇心的专业人士，纯 AI 101 契合度较弱。

### AI in Education: Leveraging ChatGPT for Teaching（教育中的 AI：借助 ChatGPT 开展教学）

- 主办方：Wharton Online，宾夕法尼亚大学（Coursera） | 类型：高校 | 项目：无
- 讲师：Ethan Mollick，Wharton 副教授；Lilach Mollick 博士，Wharton Generative AI Labs
- 费用：QA 修正 —— Coursera Plus/付费报名（约 $59/月，7 天免费试用）；未确认免费旁听 | 开设时间：2024 年 11 月 21 日（Wharton 新闻稿） | 时长：约 6 小时，4 个模块
- 形式：自主进度视频，入门级 | URL：https://www.coursera.org/learn/ai-in-education-leveraging-chatgpt-for-teaching
- 覆盖能力(Cs)：C1 GenAI/LLM 基础；C2 ChatGPT 应用、自定义 GPT；C3（间接）公共教育者的技能提升；C4 伦理与隐私风险；C5 借助人的专业判断评估输出 | 覆盖目标(Os)：O1 将 AI 融入教学工作流；O2 借助专业能力评估 AI 输出；O3 隐私/伦理风险覆盖
- 备注：评分 4.8/5（303 条评价），报名 2.9 万人；以教育者为视角，但内容是通用 GenAI 素养；授课者是 AI 落地研究领域的权威学者。

### Introduction to Generative AI (Duke)（生成式 AI 入门，Duke）

- 主办方：Duke University（Coursera） | 类型：高校 | 项目：LLMOps Specialization，第 1 门课程
- 讲师：Noah Gift，Duke MIDS 驻校高管（Executive in Residence）；Alfredo Deza，兼职教授
- 费用：可免费旁听；付费证书可选 | 开设时间：2024 年（archive.org 2024-04-13） | 时长：约 4 周，自主进度
- 形式：自主进度视频，入门级，无需先修知识 | URL：https://www.coursera.org/learn/intro-gen-ai
- 覆盖能力(Cs)：C1 LLM/基础模型原理；C2 GenAI 系统类型（API、嵌入式）；C3（间接）劳动力生产率；C4 伦理板块 | 覆盖目标(Os)：O1 面向工作的有效提示词；O2 迭代改进输出
- 备注：评分 4.5/5，报名 3 万人；该专项后续课程偏开发者向；治理内容偏薄 —— 建议搭配一门治理课程。

### What Can AI Do for Marketing?（AI 能为营销做什么？）

- 主办方：Emory University，Goizueta Business School（Coursera） | 类型：高校 | 项目：AI for Marketing Specialization，第 1 门课程
- 讲师：David Schweidel，市场营销学教授
- 费用：可免费旁听；付费证书可选 | 开设时间：2024 年（archive.org 2024-09-12） | 时长：约 2 周，自主进度
- 形式：自主进度视频，入门级 | URL：https://www.coursera.org/learn/whatcanaidoformarketing
- 覆盖能力(Cs)：C2 客户旅程各环节的 AI；C3（间接）外联/传播职能；C4 “Bias in the Machine”模块 | 覆盖目标(Os)：O1 在传播工作流中应用 AI；O2 评估 AI 带来的影响；O3 偏见/公平性模块
- 备注：范围限定在营销领域 —— 可作为特定岗位的入门课，不宜当作通用 AI 101。

### Introduction to Artificial Intelligence (UIUC)（人工智能导论，UIUC）

- 主办方：University of Illinois Urbana-Champaign，Gies College of Business（Coursera） | 类型：高校 | 项目：Gies 开放课程
- 讲师：Robert J. Brunner，教授兼创新事务副院长
- 费用：可免费旁听；付费证书可选 | 开设时间：2025 年（archive.org 2025-03-15） | 时长：约 21 小时，4 个模块
- 形式：自主进度 MOOC，入门级，无先修要求 | URL：https://www.coursera.org/learn/intro-to-artificial-intelligence
- 覆盖能力(Cs)：C1 历史、ML/DL 基础；C2 神经网络、生成模型、数据；C3（间接）政策/社会影响模块；C4 偏见、数据伦理；C5 负责任 AI、监管、合规；C6 AGI、AI 安全、劳动力的未来 | 覆盖目标(Os)：O1 贯穿各类工作流的商业应用；O2 模型评估、输出评估；O3 监管、合规、数据伦理
- 备注：报名 1.75 万人，评分 4.7/5；在本次差距扫描中，六项 C 覆盖最全的一门。

### Introduction to Generative AI (BUSAI X001)（生成式 AI 入门，BUSAI X001）

- 主办方：The Ohio State University，Professional and Continuing Education | 类型：高校 | 项目：AI for Business Growth 证书方向（OSU AI Fluency Initiative）
- 讲师：Jeff Dotson 博士，Fisher College 市场营销学副教授
- 费用：$49 | 开设时间：2025 年（OSU News，2025-09-16） | 时长：约 10 小时，自主进度
- 形式：线上自主进度；OSU 结业证书 | URL：https://reg-continuinged.osu.edu/search/publicCourseSearchDetails.do?method=load&courseId=1260877
- 覆盖能力(Cs)：C1 用通俗语言讲解生成式 AI；C2 工具的能力与局限 | 覆盖目标(Os)：O1 将 AI 用于写作/规划/效率提升；O2 评估 AI 生成的内容
- 备注：面向非技术背景的成年学习者；开放报名（QA 确认 2026 年 6 月—9 月期开班）；C4/C5 需搭配治理类课程。

### Demystifying AI, Understanding Risks, and Shaping the Future（揭开 AI 的神秘面纱、理解风险并塑造未来）

- 主办方：Purdue University（Purdue Online） | 类型：高校 | 项目：Purdue AI Microcredentials，Foundational Non-Technical 组合
- 讲师：David Peterson 博士，社会学助理教授
- 费用：$99 | 开设时间：2024 年（项目页面存档 2024-07-11） | 时长：约 15 小时，4 个模块
- 形式：线上异步；证书 + Credly 徽章；获 ABET 认可 | URL：https://www.purdue.edu/online/artificial-intelligence-micro-credentials/
- 覆盖能力(Cs)：C1 AI 历史、深度学习基础；C2 系统设计、应用；C4 远期与即期的社会风险；C6 塑造 AI 的发展轨迹 | 覆盖目标(Os)：O1 任何背景都能上手的实操应用；O2 理解风险与局限
- 备注：首个获 ABET 认可的 AI 微证书系列；面向专业人士/政策制定者设计。

### AI Policy and Governance（AI 政策与治理）

- 主办方：Purdue University（Purdue Online） | 类型：高校 | 项目：Purdue AI Microcredentials，Foundational Non-Technical 组合
- 讲师：Daniel Schiff 博士，技术政策助理教授；GRAIL 实验室联合主任
- 费用：$99 | 开设时间：2024 年（项目页面存档 2024-07-11） | 时长：约 15 小时，5 个模块
- 形式：线上异步；证书 + Credly 徽章 | URL：https://www.purdue.edu/online/artificial-intelligence-micro-credentials/
- 覆盖能力(Cs)：C3 面向政府场景的 AI 公共政策；C4 伦理、公民社会关切；C5 治理策略、自我监管；C6 国际监管趋势 | 覆盖目标(Os)：O2 批判性评估社会风险；O3 治理、监管、负责任 AI 监督
- 备注：本次找到的最聚焦 O3 的高校课程；讲师曾任 JPMorgan 负责任 AI 负责人 —— 对政府受众高度契合。

### AI Ethics, Inclusion & Society（AI 伦理、包容与社会）

- 主办方：University of Glasgow（FutureLearn；平台上名为“Generative AI Ethics and Society”） | 类型：高校 | 项目：Glasgow 免费在线课程
- 讲师：Ciorsdaidh Watts 博士，高级讲师兼校级 AI Champion；Lydia Bach 博士
- 费用：免费层（限时访问；升级 $54） | 开设时间：2025 年（archive.org 2025-06-23） | 时长：3 周，每周 5 小时
- 形式：线上自主进度 | URL：https://www.futurelearn.com/courses/ai-ethics-inclusion-and-society
- 覆盖能力(Cs)：C1 AI 是什么、如何工作；C2 数据与算法；C3 AI 在学习/医疗/环境中的应用；C4 偏见、数字鸿沟、歧视；C5 治理与问责框架；C6 生存性风险、AI 的未来 | 覆盖目标(Os)：O2 批判性地审视 AI 部署；O3 治理、偏见、包容
- 备注：由两条差距线索独立发现；以伦理为先的定位，O1 偏弱；与学生共同创作（质量信号不一）。

### Generative AI in Education（教育中的生成式 AI）

- 主办方：University of Glasgow（Coursera） | 类型：高校 | 项目：无
- 讲师：Gabriella Rodolico 博士，科学教育高级讲师
- 费用：免费报名/限时内容；证书付费 | 开设时间：2024 年（archive.org 2024-04-21） | 时长：约 5 小时，4 个模块
- 形式：自主进度，入门级 | URL：https://www.coursera.org/learn/generative-ai-in-education
- 覆盖能力(Cs)：C1 生成式 AI 基础；C2 提示词工程、工具；C3（间接）公共教育工作者队伍；C4 错误信息、抄袭、版权；C5 负责任使用指引 | 覆盖目标(Os)：O1 把工具纳入工作流；O2 关键考量；O3 部分覆盖（版权/伦理）
- 备注：以教育为框架，但第 1–3 模块是通用 GenAI 入门；9.5k 名学习者，评分 4.6/5。

### AI Regulation: Navigating the EU AI Act（AI 监管：解读欧盟《人工智能法案》）

- 主办方：TU Delft（DelftX，edX） | 类型：高校 | 项目：Navigating AI and Online Platform Regulations
- 讲师：Marie-Therese Sekwenz，TU Delft（TPM）；Hannah Ruschemeier 教授
- 费用：可免费旁听；认证证书 $140 | 开设时间：2026 年（edX datePublished 2026-01-06；2026 年 6 月首期开课） | 时长：4 周，每周 2–4 小时
- 形式：自主进度 MOOC，无先修要求 | URL：https://learningforlife.tudelft.nl/ai-regulation-navigating-the-eu-ai-act/
- 覆盖能力(Cs)：C2 AI 价值链、GPAI 与 AI 系统的区别；C3（间接）面向公共管理受众；C4 禁止性实践、高风险危害；C5 可信 AI、人类监督、数据治理；C6 GPAI 系统性风险争论 | 覆盖目标(Os)：O1 将要求映射到 AI 工作流；O2 人类监督、透明度义务；O3 基于风险的监管、执法
- 备注：针对欧盟的法律 —— 对美国政府人员而言属于比较治理材料，而非通用 AI 101；QA 确认提供免费旁听通道。

### Artificial Intelligence for Everyone (Universiti Malaya)（人人可懂的人工智能，马来西亚大学）

- 主办方：Universiti Malaya（FutureLearn） | 类型：高校 | 项目：无
- 讲师：Norisma Idris，AI 系副教授（另有 4 位 UM AI 学院教师）
- 费用：免费层（8 周访问权限）或一次性 $109 | 开设时间：2025 年（archive.org 2025-04-06 —— 解决了此前 Track-1 日期存疑的问题） | 时长：8 周，每周 2 小时
- 形式：线上自主进度 | URL：https://www.futurelearn.com/courses/artificial-intelligence-for-everyone
- 覆盖能力(Cs)：C1 机器学习与深度学习基础；C2 NLP、计算机视觉、GenAI/LLM；C3（间接）跨领域应用；C4 伦理/治理考量；C5 应用的治理 | 覆盖目标(Os)：O1 将 AI 技术应用于具体场景；O2 批判性地分析应用；O3 伦理/治理覆盖
- 备注：此前因日期无法核实而列为 Track-1 的近似匹配项 —— 现已确认日期；由马来西亚顶级大学的 AI 系讲授。

### Agentic AI and AI Agents: A Primer for Leaders（智能体化 AI 与 AI 智能体：领导者入门）

- 主办方：Vanderbilt University（Coursera） | 类型：高校 | 项目：Agentic AI and AI Agents for Leaders Specialization，第 1 门课程
- 讲师：Jules White 博士，计算机科学教授兼副院长
- 费用：可免费旁听；证书付费 | 开设时间：2025 年 1 月（archive.org 2025-01-15） | 时长：约 6 小时，2 个模块
- 形式：自主进度视频 + 自定义 GPT 实操 | URL：https://www.coursera.org/learn/agentic-ai
- 覆盖能力(Cs)：C1 GenAI + 工具的运作方式；C2 智能体能力、自定义 GPT；C6 未来的工作中智能体的发展趋势 | 覆盖目标(Os)：O1 构建基础的工作自动化智能体；O2 区分创新与炒作
- 备注：报名 118k+，评分 4.7/5；范围专门聚焦智能体化 AI —— 是概念图中 AI 智能体锚点的有力补充。

### Current Issues in Ethics and AI（伦理与 AI 的当代议题）

- 主办方：University of Colorado Boulder（Coursera） | 类型：高校 | 项目：无
- 讲师：Bobby Schnabel，计算机科学教授；ACM 前 CEO
- 费用：QA 已更正 —— Coursera Plus/付费报名（约 $59/月，7 天免费试用）；免费旁听未确认 | 开设时间：2025 年（archive.org 2025-11-19） | 时长：3 周
- 形式：自主进度，5 个模块 | URL：https://www.coursera.org/learn/current-issues-in-ethics-and-ai
- 覆盖能力(Cs)：C3 对警务/司法/政府领域 AI 应用的批判性审视；C4 偏见、隐私、错误信息；C5 伦理框架、AI 监管；C6 AGI、自主战争、工作的未来 | 覆盖目标(Os)：O2 批判性地评估 AI 危害；O3 监管、隐私、公民权利（偏见、警务）
- 备注：讲师声望卓著；以伦理/风险为中心，兼有国家安全（natsec）主题（自主战争）。

### AI for Work and Life (UNF)（工作与生活领域的 AI，UNF）

- 主办方：University of North Florida（Open edX，经由 GetCertificate.Online） | 类型：高校 | 项目：UNF AI for Work and Life 证书
- 讲师：多讲师组合：Josh Gellers 博士、Suzanne Ehrlich 博士（UNF 教职）、Moez Limayem 博士（UNF 校长）、Reid Blackman 博士（伦理）
- 费用：QA 已澄清 —— 模块内容可免费旁听；可验证证书 $249（超出费用上限；旁听路径符合条件） | 开设时间：2025 年 9 月（UNF 新闻室；课程 id 为 UNF+AI101+2025） | 时长：8 个模块，约 10 小时 + 专家主持的在线场次
- 形式：线上随时学 + 专家实时场次；1 CEU | URL：https://learn.getcertificate.online/courses/course-v1:UNF+AI101+2025_S/about
- 覆盖能力(Cs)：C1 AI 基础与未来；C2 日常 AI 工具；C3（间接）AI 在法律/金融/医疗领域的应用；C4 AI in Society 模块；C5 负责任使用（Blackman 分节）；C6 未来趋势 | 覆盖目标(Os)：O1 提示词 + 将 AI 应用于自身岗位的结业项目；O2 提示词的艺术与科学；O3 AI in Society、伦理
- 备注：明确采用 "AI 101" 品牌；此前因费用问题属于 Track-2 近似匹配项 —— QA 已确认免费旁听路径依然存在（仅证书为 $249），恢复了入选资格。

### Gap-sweep near-misses (new, deduplicated)（缺口扫描得到的近似匹配项（新增，已去重））


费用：Future Proof with AI（Harvard Business School，$199）；HKS GenAI 高管版（$1,995）；Cambridge PACE Ethical AI（£415 起）；TU Delft AI in Public Service（€575 —— 其他方面都非常契合）；Penn State AI Literacy for Professionals（$525）；eCornell AI 证书（$3,750）；UChicago GenAI for Business（$2,800）；Kellogg 高管 AI 项目；Ohio State 同门系列课程（$279）；Imperial 面向政策制定者的 AI Fundamentals（£750，线下授课，仅限英国 —— 多项不符）。
开设时间：MITx Understanding the World Through Data（2023 年 10 月）；ASU AI Foundations 系列课程（2023）；Edinburgh Data Ethics/AI（2023）；TU Delft AI in Practice（2020）；Wharton AI For Business（2021）；RMIT GenAI for Business（2023）；UMD Cybersecurity in the AI Era（2022）；Vanderbilt GenAI Strategic Leader（含 2023 年开设的课程）。
先修要求/难度层级：Berkeley LLM Agents MOOC（需 ML/DL 基础）；Penn AI & ML Essentials with Python；MIT 6.S184（数学/PyTorch，学生主导）；CS50 AI with Python（无变化 —— 要求 CS50x/Python）。
提供方/获取方式：CMU OLI "AI for Learning"（由教职员工编写而非教授主讲；面向教育工作者 —— 经整合审查降级）；Glasgow GenAI in the Classroom for Educators（仅限教育工作者，AI-101 内容极少 —— 经整合审查降级）；MIT Horizon（仅限机构授权）；Stanford HAI/GSA 联邦系列课程（2023 年启动 + 仅限政府部门）；UGA AI Literacy for All（仅限 UGA 校友）；Purdue 校友免费层（仅限校友）；CSU 全系统 Canvas 课程（仅限 CSU）；UT Austin Essentials of AI（2023 + 仅限 UT）；HKS 免费网络研讨会（非结构化课程）；AI Literacy for Early Career Learners（EdTech 供应商）；KCL AI in Education（2024 年之前的旧版课程）。

### Unverified watch-list (could not confirm via live fetch — recheck later)（未经核实的观察清单（无法通过实时抓取确认 —— 后续复查））


CMU Heinz/OFAI "AI for Public Service" 开源课程体系（2024 年 10 月公布，尚无可报名页面）；CMU Heinz + NACD AI Oversight for Directors（2025 年 12 月公告）；UC Berkeley "AI-Forward Professional"（页面 404）；Harvard Data Science Initiative GenAI 强化课程（未标明费用）；Columbia Plus AI 系列课程（站点 403）；Cornell 夏季 AI 课程（未找到页面）；Emory ailearning 门户；Ohio State Agentic AI for Small Business（$79，日期/讲师未核实）；Penn State Berks Responsible AI（非学分，未标价）；Purdue Interdisciplinary AI Fundamentals（$99 —— 需核实讲师身份）；Glasgow 面向学生/医疗保健从业者的 GenAI 课程；LSE AI for Social Sciences（费用/资格不明）；Edinburgh AI for Leaders（页面 404）；Turing Institute 自主进度课程（日期未核实）；UW/Minnesota/Texas A&M/Princeton/Yale/NYU/Rice：未找到符合资格的公开课程（负面排查记录见 gap plan 缓存）。

---


### NCP-AAI 推荐培训课程


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-aai/dli-courses.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-aai/dli-courses.md) · 语言：中文原文



# NCP-AAI 推荐培训课程

> 来源：[英伟达官方认证页](https://www.nvidia.cn/training/certification/agentic-ai-professional/) · NVIDIA DLI 培训。

| 课程编号 | 课程名称 | 形式 | 时长 | 语言 | 参考费用 |
|---|---|---|---|---|---|
| — | 代理式 AI 专业级课程 | 讲师指导培训班 | 8 学时 | 中文 | 见官网 |

## 报名与购买

- [购买考试券（NVIDIA 官方）](https://www.nvidia.cn/training/certification/#book-cn-exam)
- [NVIDIA DLI 中文官网](https://www.nvidia.cn/training/)

---



## 学习指南


### 精通智能体化 AI 系统 - 学习计划


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `Study_Plan.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/Study_Plan.md) · 语言：英文原文 · 中译版



# 精通智能体化 AI 系统 - 学习计划


本学习计划为在 4 个月（120 天）的强化学习计划内掌握教材全部 86 个理论章节提供结构化指导。（另有 18 个实践章节在 labs/ 目录中单独提供。）每章包括：

---

## 目录


### 第 1 部分：智能体基础（11 章）

- [1.1A：UI 基础](#part-1-chapter-11a-ui-foundations)
- [1.1B：人在回路模式与无障碍设计](#part-1-chapter-11b-human-in-the-loop-patterns-and-accessible-design)
- [1.2：核心模式](#part-1-chapter-12-core-patterns)
- [1.3：多智能体系统](#part-1-chapter-13-multi-agent-systems)
- [1.4：记忆与感知](#part-1-chapter-14-memory--perception)
- [1.5A：有状态编排 - 基础](#part-1-chapter-15a-stateful-orchestration---foundations)
- [1.5B：有状态编排 - 实例详解](#part-1-chapter-15b-stateful-orchestration---worked-examples)
- [1.6：有状态编排 - 陷阱、集成与综合](#part-1-chapter-16-stateful-orchestration---pitfalls-integration-and-synthesis)
- [1.7A：基于知识图谱的关系推理](#part-1-chapter-17a-relational-reasoning-with-knowledge-graphs)
- [1.7B：基于知识图谱的关系推理 - RAG+KG 混合集成](#part-1-chapter-17b-relational-reasoning-with-knowledge-graphs---hybrid-ragkg-integration)
- [1.8：智能体韧性与综合](#part-1-chapter-18-agent-resilience-and-synthesis)

### 第 2 部分：框架与工具集成（9 章）

- [2.1：框架全景](#part-2-chapter-21-framework-landscape)
- [2.2：LangGraph](#part-2-chapter-22-langgraph)
- [2.3：LangChain](#part-2-chapter-23-langchain)
- [2.4：多智能体框架](#part-2-chapter-24-multiagent-frameworks)
- [2.5：Semantic Kernel - 企业级框架与插件架构](#part-2-chapter-25-semantic-kernel---enterprise-framework-and-plugin-architecture)
- [2.6：工具集成与函数调用](#part-2-chapter-26-tool-integration-and-function-calling)
- [2.7：多模态 RAG - 视觉、音频与文本的融合](#part-2-chapter-27-multimodal-rag---integration-of-vision-audio-and-text)
- [2.8：错误处理与韧性](#part-2-chapter-28-error-handling-and-resilience)
- [2.9：流式输出与实时响应](#part-2-chapter-29-streaming-and-real-time-responses)

### 第 3 部分：评估与优化（12 章）

- [3.1A：实现评估流水线与任务基准测试 - 引言、动机与核心概念](#part-3-chapter-31a-implement-evaluation-pipelines-and-task-benchmarks---introduction-motivation-and-core-concepts)
- [3.1B：实现评估流水线与任务基准测试 - 自定义指标与 CI/CD 集成](#part-3-chapter-31b-implement-evaluation-pipelines-and-task-benchmarks---custom-metrics-and-cicd-integration)
- [3.1C：实现评估流水线与任务基准测试 - 独立练习与综合系统设计](#part-3-chapter-31c-implement-evaluation-pipelines-and-task-benchmarks---independent-practice-and-comprehensive-system-design)
- [3.2：跨任务与数据集比较智能体性能 - 多基准测试评估与统计严谨性](#part-3-chapter-32-compare-agent-performance-across-tasks-and-datasets---multi-benchmark-evaluation-and-statistical-rigor)
- [3.3：网页导航与交互基准测试 - Web 智能体评估与多跳问答](#part-3-chapter-33-web-navigation-and-interaction-benchmarks---web-agent-evaluation-and-multi-hop-question-answering)
- [3.4：调优参数](#part-3-chapter-34-tune-parameters)
- [3.5：提示词优化、少样本学习、基于智能体轨迹的微调与奖励建模](#part-3-chapter-35-prompt-optimization-few-shot-learning-fine-tuning-with-agent-trajectories-and-reward-modeling)
- [3.6：轨迹分析与执行调试](#part-3-chapter-36-trace-analysis-and-execution-debugging)
- [3.7：工具审计与校验](#part-3-chapter-37-tool-auditing-and-validation)
- [3.8：动作准确率](#part-3-chapter-38-action-accuracy)
- [3.9：推理质量](#part-3-chapter-39-reasoning-quality)
- [3.10：效率指标](#part-3-chapter-310-efficiency-metrics)

### 第 4 部分：生产部署与扩缩容（7 章）

- [4.1：AI 智能体部署与扩缩容](#part-4-chapter-41-ai-agent-deployment-and-scaling)
- [4.2：部署与扩缩容](#part-4-chapter-42-deployment--scaling)
- [4.3：容器编排与边缘部署](#part-4-chapter-43-container-orchestration-and-edge-deployment)
- [4.4：性能剖析与优化](#part-4-chapter-44-performance-profiling-and-optimization)
- [4.5：NVIDIA NIM 与 Triton Inference Server](#part-4-chapter-45-nvidia-nim-and-triton-inference-server)
- [4.6：TensorRT-LLM 与 NVIDIA Fleet Command](#part-4-chapter-46-tensorrt-llm-and-nvidia-fleet-command)
- [4.7：扩缩容策略](#part-4-chapter-47-scaling-strategies)

### 第 5 部分：高级推理与决策（13 章）

- [5.1：思维链推理](#part-5-chapter-51-chain-of-thought-reasoning)
- [5.2：思维树（ToT）](#part-5-chapter-52-tree-of-thought-tot)
- [5.3：自洽性](#part-5-chapter-53-self-consistency)
- [5.4：分层规划](#part-5-chapter-54-hierarchical-planning)
- [5.5：蒙特卡洛树搜索（MCTS）](#part-5-chapter-55-monte-carlo-tree-search-mcts)
- [5.6：A* 搜索](#part-5-chapter-56-a-search)
- [5.7：情景记忆](#part-5-chapter-57-episodic-memory)
- [5.8：语义记忆](#part-5-chapter-58-semantic-memory)
- [5.9：工作记忆](#part-5-chapter-59-working-memory)
- [5.10：基于效用的决策](#part-5-chapter-510-utility-based-decision-making)
- [5.11：基于规则的决策](#part-5-chapter-511-rule-based-decision-making)
- [5.12：基于学习的决策](#part-5-chapter-512-learning-based-decision-making)
- [5.13：混合决策系统](#part-5-chapter-513-hybrid-decision-systems)

### 第 6 部分：检索增强生成（RAG）（9 章）

- [6.1A：RAG 分块与嵌入](#part-6-chapter-61a-rag-chunking-and-embeddings)
- [6.1C：RAG 实现](#part-6-chapter-61c-rag-implementation)
- [6.2A：向量数据库选型](#part-6-chapter-62a-vector-database-selection)
- [6.2B：生产级向量数据库部署](#part-6-chapter-62b-production-vector-database-deployment)
- [6.3A：ETL 基础](#part-6-chapter-63a-etl-fundamentals)
- [6.3B：ETL 加载与集成](#part-6-chapter-63b-etl-load-and-integration)
- [6.4：数据质量基础](#part-6-chapter-64-data-quality-fundamentals)
- [6.5：生产级 RAG 架构](#part-6-chapter-65-production-rag-architecture)
- [6.6：查询分解与自适应检索](#part-6-chapter-66-query-decomposition-and-adaptive-retrieval)

### 第 7 部分：NVIDIA NeMo 框架与优化（7 章）

- [7.1A：NVIDIA NeMo 框架与六种 Rail 类型](#part-7-chapter-71a-nvidia-nemo-framework-and-six-rail-types)
- [7.1B：Colang DSL、NIM 集成与常见误区](#part-7-chapter-71b-colang-dsl-nim-integration-and-misconceptions)
- [7.2：性能监控与优化](#part-7-chapter-72-performance-monitoring--optimization)
- [7.3：智能体工具包](#part-7-chapter-73-agent-toolkit)
- [7.4：量化基础](#part-7-chapter-74-quantization-fundamentals)
- [7.5：Curator、Riva 与多模态](#part-7-chapter-75-curator-riva-and-multimodal)
- [7.6：Multi-Instance GPU（MIG）与安全](#part-7-chapter-76-multi-instance-gpu-mig--security)

### 第 8 部分：可靠性与成本管理（5 章）

- [8.1：延迟基础](#part-8-chapter-81-latency-fundamentals)
- [8.2A：错误分类法与 SLO](#part-8-chapter-82a-error-taxonomy-and-slo)
- [8.2B：断路器与 NeMo 集成](#part-8-chapter-82b-circuit-breakers-and-nemo-integration)
- [8.3：Token 经济性](#part-8-chapter-83-token-economics)
- [8.4：成功指标](#part-8-chapter-84-success-metrics)

### 第 9 部分：安全与治理（8 章）

- [9.1：输出过滤](#part-9-chapter-91-output-filtering)
- [9.2：动作约束](#part-9-chapter-92-action-constraints)
- [9.3：沙箱与隔离](#part-9-chapter-93-sandboxing-and-isolation)
- [9.4：公平性基础](#part-9-chapter-94-fairness-foundations)
- [9.5：Constitutional AI 原则](#part-9-chapter-95-constitutional-ai-principles)
- [9.6：标准、认证与框架](#part-9-chapter-96-standards-certifications-and-frameworks)
- [9.7：GDPR 基础](#part-9-chapter-97-gdpr-foundations)
- [9.8：AI 治理的标准与框架](#part-9-chapter-98-standards-and-frameworks-for-ai-governance)

### 第 10 部分：人在回路与集成（5 章）

- [10.1：对话式 UI](#part-10-chapter-101-conversational-ui)
- [10.2：主动型智能体](#part-10-chapter-102-proactive-agents)
- [10.3A：RLHF 方法论](#part-10-chapter-103a-rlhf-methodology)
- [10.4：人在回路](#part-10-chapter-104-human-in-the-loop)
- [10.5：人在回路之上（Human-over-the-Loop）](#part-10-chapter-105-human-over-the-loop)

---

## 第 1 部分，第 1.1A 章：UI 基础


本章以智能体自主性为核心，阐明传统应用 UI 与智能体 UI 之间的根本差异。智能体会做出具有现实世界后果的独立决策，由此带来独特的设计挑战——用户需要从操作者转变为监督者。本章介绍了基础原则（渐进式披露、透明性、控制权、错误传达、上下文感知）以及 UI 模式（聊天、命令面板、审批工作流），这些内容构成了构建可信智能体界面的基础。

**每周学习安排**：阅读：3.36 小时 | 主动学习：1.44 小时
总计学时：4.8（3.36 小时阅读，1.44 小时主动学习）

**核心概念**：
- 自主性、透明性、人类监督、信任方程、决策审阅者角色
- 审批机制、认知局限、系统弃用
- 渐进式披露、认知过载、基础/展开/技术视图
- 可解释性、特征归因、置信度评分、反事实解释
- 用户控制权、控制光谱、置信度门控、基于风险的门控
- 审批疲劳、错误传达、瞬时错误、用户输入错误
- 能力边界、上下文感知、会话历史、会话持久化
- 参考链接、聊天界面模式、流式响应、反馈机制
- 快捷操作按钮、输入指示器、命令面板模式、模糊匹配
- 上下文分析、命令历史、审批工作流模式、决策请求标头
- AI 分析区块、支撑证据链接、多选项操作、审阅者评论
- SLA 计时器、审批路由、信息密度、视觉层级

**关键问题**：
1. 为什么智能体需要与传统应用不同的 UI 设计原则？
2. 解释"信任方程"，并说明为什么透明性与控制权缺一不可。
3. 什么是渐进式披露，它解决了什么问题？
4. 对于瞬时错误、用户输入错误、能力边界与策略违规，错误传达应有何不同？
5. 聊天界面模式为何有效，它的局限是什么？
6. 以客服退款智能体为例，说明渐进式披露中三种视图的区别。
7. 为什么置信度评分对用户信任很重要，应该如何传达？
8. 何时应使用审批工作流模式而非聊天界面？
9. 上下文感知如何提升用户信任智能体响应的能力？
10. 什么是"审批疲劳"，如何避免？

💭 [用自己的语言回答这些问题](https://docs.google.com/forms/d/1Vtz-NDYQN8m7EyvXgdAIgGgiME9lhT7xAI5vQpC58wI/viewform?usp=sharing)

**相关章节**：
- 1.1B（人在回路模式）
- 1.2+（工具使用与多智能体系统）
- 第 2 部分（框架实现）
- 第 3 部分（部署与基础设施）

**✅ [完成第 1.1A 章测验](https://docs.google.com/forms/d/e/1FAIpQLSfRpAEoQBYr8AT-YWuHvGzYyovoDzk_KI2lu69FfP1Z28e4rA/viewform?usp=sharing)**

---

[↑ 返回目录](#table-of-contents)

## 第 1 部分，第 1.1B 章：人在回路模式与无障碍设计


本章通过让人工干预程度与决策风险相匹配，来应对自主智能体系统的核心挑战。它建立了三种核心控制模式（通知、审批、监控）并将其分布在一条光谱上，为模式选择提供决策框架，同时引入基于 WCAG 的无障碍设计，确保所有用户都能有效地与审批工作流和智能体系统交互。

**每周学习安排**：阅读：1.26 小时 | 主动学习：0.54 小时
总计学时：1.8（1.26 小时阅读，0.54 小时主动学习）

**核心概念**：
- 控制光谱、通知模式、审批模式、监控模式
- 审批疲劳、置信度门控模式、风险量级
- 置信水平、可逆性、基于风险的门控、智能阈值
- 批处理、渐进式细节、键盘快捷键、基于时间的默认值
- 可感知性、替代文本、颜色对比度、超出颜色的视觉指示
- 面向无障碍的渐进式披露、标记中的语义含义
- 可操作性、完整的键盘访问、可见的焦点指示
- Tab 键顺序、模态管理、以通俗语言替代专业术语
- 可预测行为、错误预防与恢复、可操作的错误信息
- 备选方案、语义化 HTML、ARIA 属性
- 用于动态内容的实时区域、流式响应的无障碍支持
- 视觉隐藏内容、自动化工具、手动键盘测试
- 屏幕阅读器测试、响应式测试

**关键问题**：
1. 通知、审批与监控三种控制模式的主要区别是什么？
2. 置信度门控与基于风险的门控有何不同，二者能否协同工作？
3. 审批疲劳的成因是什么，五种具体的缓解策略如何应对它？
4. 本章为何强调无障碍改进对所有用户都有益？
5. 流式响应带来了哪些独特的无障碍挑战？
6. 在审批工作流的每一层渐进式披露中，应呈现哪些信息？
7. 如何设计能说明发生了什么、是否属永久性问题以及如何恢复的错误信息？
8. 为什么语义化 HTML 对无障碍和整体用户体验都很重要？
9. WCAG 的四条原则是什么，它们如何应用于智能体 UI？

💭 [用自己的语言回答这些问题](https://docs.google.com/forms/d/1tPuC_SNCaqDEZgX2802NJARqIlCh4JkzIf9FDpzoqdY/viewform?usp=sharing)

**相关章节**：
- 1.1A（UI 基础）
- 第 2 部分（实现过渡桥梁）
- 第 10 部分（生产级 HITL 系统）

**✅ [完成第 1.1B 章测验](https://docs.google.com/forms/d/e/1FAIpQLSd0-ms91kZKlPjrfIvjKYx6mKTiDSW96X5xUt_wlR4Nn9yXtQ/viewform?usp=sharing&ouid=116579026379007071084)**

---

[↑ 返回目录](#table-of-contents)

## 第 1 部分，第 1.2 章：核心模式


本章探讨四种基本的智能体推理模式——ReAct（推理 + 行动）、Plan-and-Execute（分层任务分解）、Reflection（自我批判与迭代改进）以及工具使用架构（Tool-Use Architecture）——考察它们的优势、局限与生产适用性。本章强调基于证据的模式选择而非想当然的做法，揭示常见误区，并就每种模式何时能优化性能、何时反而带来不必要的成本与复杂度给出清晰指导。

**每周学习安排**：阅读：2.52 小时 | 主动学习：1.08 小时
总计学时：3.6（2.52 小时阅读，1.08 小时主动学习）

**核心概念**：
- 思考阶段、行动阶段、观察阶段、显式推理轨迹
- 通过观察实现落地锚定、动态工具选择、适应性
- 示例-查询相似度、规划阶段、执行阶段、动态重规划
- 关注点分离、分层分解、成本效率
- 计划僵化脆弱性、规划瘫痪
- 生成-反思-精炼循环、自我反思阶段、迭代精炼
- 记忆整合、元推理能力、收益递减
- 幻觉循环、上下文窗口消耗
- 工具注册表与元数据、函数调用机制、动作层
- API 网关模式、Model Context Protocol、智能体化 RAG
- 无状态工具设计、微服务经验的应用
- 会议驱动的开发、过早优化
- 被忽视的基本功、数据质量的关键性、可观测性缺口

**关键问题**：
1. 对于生产环境的服务诊断智能体，何时该用 ReAct，何时该用 Plan-and-Execute？
2. 在生产系统中拉低 ReAct 性能的主要因素是什么？
3. 对于数据管道任务，为什么 Plan-and-Execute 优于 ReAct？
4. 在代码生成中实现 Reflection 时，最佳的停止条件是什么？
5. 为什么工具过载会在提供更多能力的同时反而降低智能体性能？
6. 工具描述应如何编写才能最大化 LLM 的理解效果？
7. 哪些策略可以防止 Reflection 中出现幻觉式推理？
8. 设计一个有效结合多种模式的客服退款智能体架构。

💭 [用自己的语言回答这些问题](https://docs.google.com/forms/d/1tfLakO_xSTnJkSjc2QmJix25sYrrSXY2vSN1EkaixaI/viewform?usp=sharing)

**相关章节**：
- 1.1A（UI 基础背景）
- 1.1B（控制机制）
- 第 2 部分（框架实现）
- 第 1.3 章（记忆与上下文）
- 第 10 部分（生产部署）

**✅ [完成第 1.2 章测验](https://docs.google.com/forms/d/e/1FAIpQLScbDCuwEEAPMITGgDm5QRvx2UIKTAJZHFiNTInBd3Upn8kCNA/viewform?usp=sharing&ouid=116579026379007071084)**

---

[↑ 返回目录](#table-of-contents)

## 第 1 部分，第 1.3 章：多智能体系统


本章针对协调多个自主智能体以达成共享或相互竞争目标这一核心难题展开。它考察了使用具有共享目标的专用智能体的协作范式、运用博弈论原理的竞争系统、从简单局部规则中涌现的群体智能、多种通信机制（消息传递、共享内存、事件驱动、基于 API）以及多种编排模式（集中式、去中心化、分层式、联邦式），并明确指出每种方案的失败模式与选择标准。

**每周学习安排**：阅读：5.11 小时 | 主动学习：2.19 小时
总计学时：7.3（5.11 小时阅读，2.19 小时主动学习）

**核心概念**：
- 智能体专业化、点对点交互、通信协议
- 智能体卡片、上下文移交、异构团队与同构团队
- 共享内存系统、共识协议
- 纳什均衡、非合作博弈、占优策略
- 有限理性、联盟形成、对抗性脆弱点
- 强化学习集成、冲突解决机制
- 涌现行为、局部规则与智能体、分离/对齐/凝聚
- 粒子群优化、自组织、去中心化的优势
- 涌现行为的不确定性、参数调优的关键性
- 消息传递、结构化消息、言语行为理论
- 同步请求-响应、显式通信轨迹、紧耦合
- 共享内存、隐式协调、时间与空间解耦
- 机会式问题求解、竞态条件、伪共享
- 事件驱动架构、异步发布、消息队列
- FIFO 缓冲、投递保证、幂等性、消息顺序
- 死信队列、关联 ID
- REST、无状态设计、人类可读的 JSON
- gRPC、Protocol Buffers、HTTP/2 多路复用、流式模式
- 类型安全、速率限制、断路器
- 集中式编排、去中心化编排
- 分层式编排、联邦式编排
- 过度工程、智能体单体、架构不匹配
- 缺乏故障隔离、可观测性不足、静态协议

**关键问题**：
1. 何时应采用多智能体架构而非单个能力更强的智能体？
2. 应如何在消息传递、共享内存、事件驱动与基于 API 的通信之间做选择？
3. 多智能体系统失败最常见的原因是什么？
4. 如何调试分布式多智能体系统？
5. 与集中式编排相比，分层式编排带来了什么？
6. 群体智能与竞争型多智能体系统同协作型系统有何不同？
7. 什么是 Protocol Buffers，为什么 gRPC 用它而不是 JSON？
8. 在事件驱动的多智能体系统中如何处理最终一致性？
9. 什么是断路器，为什么它在多智能体系统中至关重要？
10. 联邦式编排与分层式编排有何不同？

💭 [用自己的语言回答这些问题](https://docs.google.com/forms/d/1D6ORbJJbJGzyygA-fgn-TNFqpmhG4U_Wz1sgAIyrK_0/viewform?usp=sharing)

**相关章节**：
- 1.1A（UI 基础）
- 1.1B（智能体基础）
- 1.2（核心模式）
- 1.4（记忆与上下文）
- 1.5A/1.5B（工具集成）
- 第 2 部分（框架实现）

**✅ [完成第 1.3 章测验](https://docs.google.com/forms/d/e/1FAIpQLSfi2LfhCiYWhs02EEJgXpyYCRq3g0QNhUsfSqGxVEp5fe__nA/viewform?usp=sharing&ouid=116579026379007071084)**

---

[↑ 返回目录](#table-of-contents)

## 第 1 部分，第 1.4 章：记忆与感知

本章通过记忆系统与感知系统，为智能体认知确立架构基础。它区分了短期工作记忆（上下文窗口）与长期记忆系统（语义记忆、情景记忆、程序性记忆），介绍了感知流水线的各个阶段，并处理了若干关键的集成挑战，包括向量存储的常见误区、时间同步、上下文退化以及“迷失在中间”效应。本章强调，记忆与感知的正确集成能够实现具备上下文感知能力的智能体行为，而这正是生产级系统所必需的。

**每周时间分配**：阅读：0.7 小时 | 主动学习：0.3 小时
总计：1.0 小时（阅读 0.7 小时，主动学习 0.3 小时）

**核心概念**：
- 短期记忆、长期记忆、语义记忆
- 情景记忆、程序性记忆、向量数据库
- 记忆生命周期管理、分层记忆架构
- 知识图谱、多模态输入处理、传感器采集
- 信号处理、多模态融合、上下文解释
- 卷积神经网络、NLP 模型
- 强化学习适配、实体抽取
- 向量存储误区、混合记忆架构
- 感知-记忆校验门、时间同步
- 同步缓冲、上下文退化、“迷失在中间”效应
- 上下文污染、分层上下文管理
- 信息过滤

**关键问题**：
1. 为什么向量数据库无法满足 AI 智能体的全部记忆需求？
2. 如果感知输出未经校验就直接存入记忆，会带来什么问题？
3. 是什么导致了“迷失在中间”效应？它对记忆增强型智能体为何重要？
4. 多模态感知中的时间同步问题会造成哪些特定的失效模式？
5. 情景记忆、语义记忆与程序性记忆有何区别？这在架构上为何重要？
6. 校验门应如何既防止幻觉事实污染记忆，又允许知识更新？
7. 记忆与感知的集成如何让“同一个问题再次出现”得以解决？
8. 分层上下文管理如何避免上下文退化问题？

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/1FRP4086_QwTHPCIE60hjFuzTLidSSm1Yj-IAwOlE9yE/viewform?usp=sharing)

**相关章节**：
- 1.1A（用于展示记忆/感知的 UI 基础）
- 1.1B（HITL 校验模式）
- 1.2（依赖记忆的核心模式）
- 1.3（多智能体记忆集成）
- 1.5A/1.5B（有状态架构）
- 1.6（带记忆的编排）
- 1.7A/1.7B（知识图谱）

**✅ [参加第 1.4 章测验](https://docs.google.com/forms/d/e/1FAIpQLSdaLksbxBQ7MrW0iROXe7gK3rPa-A1XTChHBzGGPldirFbp4Q/viewform?usp=sharing&ouid=116579026379007071084)**

---

[↑ 返回目录](#table-of-contents)

## 第 1 部分，第 1.5A 章：有状态编排 —— 基础


本章通过定义若干核心概念来确立有状态编排的理论基础，包括作为决策路径结构的逻辑树（logic tree）、作为顺序编排模式的提示链（prompt chain），以及作为跨执行周期显式上下文管理的有状态编排。本章引入了有状态智能体编排模型（Stateful Agent Orchestration Model），该模型由状态存储（State Storage）、逻辑树求值（Logic Tree Evaluation）与执行引擎（Execution Engine）三个子系统组成；同时讲解了三条架构原则——状态与逻辑分离、显式转换与幂等操作，它们使系统具备生产级可靠性。

**每周时间分配**：阅读：1.54 小时 | 主动学习：0.66 小时
总计：2.2 小时（阅读 1.54 小时，主动学习 0.66 小时）

**核心概念**：
- 逻辑树（Logic Trees）
- 提示链（Prompt Chains）
- 有状态编排（Stateful Orchestration）
- 状态机（State Machines）
- ReAct 模式
- 状态存储（State Storage）
- 逻辑树求值（Logic Tree Evaluation）
- 执行引擎（Execution Engine）
- 记忆管理器（Memory Managers）
- 工具集成系统（Tool Integration Systems）
- 状态与逻辑分离（Separation of State and Logic）
- 显式转换（Explicit Transitions）
- 幂等操作（Idempotent Operations）

**关键问题**：
1. 为什么没有有状态编排时智能体无法完成多步骤工作流？它如何支持从工作流中途的故障中恢复？
2. ReAct 模式如何通过“推理-行动-观察”循环体现有状态编排的原则？
3. ReAct 在状态管理上的关键局限是什么，例如状态爆炸与上下文窗口耗尽？
4. 将状态与逻辑分离如何支持调试、回放/测试与并行执行等能力？
5. 为什么显式状态转换在可观测性与故障恢复方面比隐式状态变更更有价值？
6. 幂等操作如何在分布式系统中实现可靠的重试逻辑与崩溃恢复？
7. 在工作流控制方面，逻辑树与简单的 if-then-else 分支有何区别？
8. 状态机是如何在简单状态变量之外对工作流执行进行形式化的？

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/1UeodKYi-1ymUYEJPXKHjqHwo6006FRaADVtnWYr7h9s/viewform?usp=sharing)

**相关章节**：
- 第 1.1B 章（智能体基础 —— 记忆组件的形式化）
- 第 1.2 章（核心智能体模式 —— ReAct 与 Plan-and-Execute）
- 第 1.3 章（多智能体系统 —— 共享状态协调）
- 第 1.4 章（记忆与感知 —— 状态存储与持久化）
- 第 1.5B 章（实践示例 —— 实际实现）
- 第 1.6 章（高级模式 —— 在基础上的构建）

**✅ [参加第 1.5A 章测验](https://docs.google.com/forms/d/e/1FAIpQLSeolDH9wqfMzruX8okBPTB5E-jhtFdkdG5chPbZfDd39qI0sg/viewform?usp=sharing&ouid=116579026379007071084)**

---

[↑ 返回目录](#table-of-contents)

## 第 1 部分，第 1.5B 章：有状态编排 —— 实践示例


本章通过具体实现来演示有状态编排的原则，对比无状态与有状态智能体架构。书中使用多城市机票预订的示例来暴露无状态设计的失效模式（出错时上下文丢失、延迟成倍放大、可观测性缺口、无法并行化），并展示有状态编排如何逐一化解这些问题。一个客户支持路由示例则演示了使用 LangGraph 实现逻辑树：通过 TypedDict 状态模式与条件边，说明显式的图表示如何带来可视化能力、可修改性，以及借助 NVIDIA NIM 等基础设施选型实现的性能优化。

**每周时间分配**：阅读：0.98 小时 | 主动学习：0.42 小时
总计：1.4 小时（阅读 0.98 小时，主动学习 0.42 小时）

**核心概念**：
- 状态持久化（State Persistence）
- 从检查点恢复执行（Resumability from Checkpoints）
- 可观测性与链路追踪（Observability and Tracing）
- 并行化协调（Parallelization Coordination）
- 失效模式（Failure Mode）
- 条件路由逻辑（Conditional Routing Logic）
- 带注解的累加器（Annotated Accumulators）
- 纯状态变换函数（Pure State Transformation Functions）

**关键问题**：
1. 无状态架构有哪些具体的失效模式？有状态编排如何逐一应对？
2. 为什么本章选择对比无状态与有状态实现，而不是直接给出正确做法？
3. TypedDict 状态模式如何同时实现类型安全与显式的可观测性？
4. 请解释 `Annotated[List[dict], add]` 模式，以及它在机票预订中为何对并行执行至关重要。
5. LangGraph 中的条件边如何比过程式的 if-then-else 链更好地实现逻辑树路由？
6. 在支持路由示例中，对比 NVIDIA NIM 优化（延迟降低 3 倍）与算法改进？
7. 客户支持路由示例如何体现针对模糊分类的人在回路（human-in-the-loop）模式？
8. 为什么并行航班搜索能力需要显式的状态管理？你会如何实现它？

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/1qocOMGJsvuIgQNxYZpfavfVKSAp0zPJ91cq1ZEeMLDM/viewform?usp=sharing)

**相关章节**：
- 第 1.5A 章（有状态编排基础 —— 理论基础）
- 第 1.2 章（核心智能体模式 —— ReAct 与 Plan-and-Execute 基础）
- 第 1.1 章（智能体架构基础 —— 组件集成）
- 第 1.6 章（高级编排模式 —— 复杂场景）
- 第 1.7 章（知识图谱 —— 语义推理集成）

✅ 本章无测验！
---

[↑ 返回目录](#table-of-contents)

## 第 1 部分，第 1.6 章：有状态编排 —— 陷阱、集成与综合


本章讨论规模化实现有状态编排时出现的生产故障与集成模式。内容涵盖若干关键误区（LLM 看似能记住上下文，实则并无状态）、失效模式（状态无界增长、无限循环、把本可并行的操作串行执行），以及有状态编排如何实现第 1.2 章中的各类模式。本章展示编排基础如何支撑分层规划、持续重规划、协作式规划与记忆系统等高级能力。

**每周时间分配**：阅读：1.26 小时 | 主动学习：0.54 小时
总计：1.8 小时（阅读 1.26 小时，主动学习 0.54 小时）

**核心概念**：
- 上下文重建（Context Reconstruction）
- 状态无界增长（Unbounded State Growth）
- 滑动窗口裁剪（Sliding Window Pruning）
- 基于摘要的压缩（Summarization-Based Compression）
- 无限循环（Infinite Loops）
- 状态哈希（State Hashing）
- 动态批处理：NVIDIA NIM 优化，将并发请求分组以摊薄开销
- ReAct 依赖（ReAct Dependencies）
- Plan-and-Execute 状态
- 多智能体协调（Multi-Agent Coordination）
- 分布式状态持久化（Distributed State Persistence）
- 分层规划状态（Hierarchical Planning State）
- 持续重规划循环（Continual Replanning Loops）

**关键问题**：
1. 为什么开发者会直觉上却错误地认为 LLM 在多次调用之间具有隐式记忆？
2. 状态无界增长除了“变慢”之外，还会造成哪些具体的生产故障？
3. 无限循环与常规的迭代式智能体执行有何区别？为什么简单的迭代次数上限会失效？
4. 为什么并行执行在操作彼此独立时有时仍无法提升性能？
5. ReAct 模式的执行具体如何依赖状态管理？缺少状态管理时会发生什么？
6. 何时应选择有状态编排，而非更简单的无状态方案？
7. 第 1.6 章的状态管理与第 1.4 章的记忆系统之间有何关系？
8. 分布式状态管理（第 1.8 章）与本地状态有何本质区别？

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/1j2QqGnUlnkZKzRVhJFcssdOqmxzlt3_H3no8ESRoO5I/viewform?usp=sharing)

**相关章节**：
- 第 1.2 章（核心智能体模式 —— ReAct、Plan-and-Execute 基础）
- 第 1.3 章（多智能体系统 —— 共享状态协调模式）
- 第 1.4 章（记忆与感知 —— 短期与长期记忆概念）
- 第 1.5A 与 1.5B 章（有状态编排基础与示例）
- 第 1.7A 与 1.7B 章（知识图谱 —— 基于关系的推理）
- 第 1.8 章（部署与扩展 —— 分布式状态管理）

**✅ [参加第 1.6 章测验](https://docs.google.com/forms/d/e/1FAIpQLScGK3oH2vlJaJvt4DPkr0YKZAXaoRzCLZhBarVhIdyaR44nNQ/viewform?usp=sharing&ouid=116579026379007071084)**

---

[↑ 返回目录](#table-of-contents)

## 第 1 部分，第 1.7A 章：用知识图谱进行关系推理


本章介绍知识图谱——它以结构化方式表示实体、关系与属性——并指出基于向量的检索系统的局限：在这类系统中，关系只是隐含在嵌入之中。内容涵盖作为灵活知识表示模型的属性图（property graph）、用于模式匹配与多跳遍历的 Cypher 查询语言，以及通过 NER、实体消歧与关系抽取从非结构化文档构建知识图谱的方法。本章展示知识图谱如何与向量 RAG 互补，支撑那些需要显式关系遍历与多跳推理的问题。

**每周时间分配**：阅读：1.89 小时 | 主动学习：0.81 小时
总计：2.7 小时（阅读 1.89 小时，主动学习 0.81 小时）

**核心概念**：
- 实体节点（Entity Node）
- 属性（Property）
- 有向关系/边（Directed Relationship/Edge）
- 属性图模型（Property Graph Model）
- RDF 三元组存储（RDF Triple Store）
- 多跳遍历（Multi-Hop Traversal）
- 图遍历（Graph Traversal）
- 索引优化（Index Optimization）
- 查询参数化（Query Parameterization）
- 命名实体识别（Named Entity Recognition, NER）
- 实体消歧/链接（Entity Disambiguation/Linking）
- 实体类型归一化（Entity Type Normalization）
- NVIDIA NeMo 模型
- 流水线阶段（Pipeline Stages）

**关键问题**：
1. 为什么向量 RAG 难以应对需要关系遍历的多跳问题？
2. 在 Cypher 中 MERGE 与 CREATE 有何区别？这对生产系统为何重要？
3. 实体消歧与实体链接如何解决知识图谱构建中的重复实体问题？
4. 为什么队列-计算比（queue-to-compute ratio）比 CPU 或 GPU 利用率更适合衡量智能体系统的扩展性？
5. 相比 RDF 三元组存储，属性图在构建智能体系统上的主要优势是什么？
6. 模式匹配查询如何把一个推理问题转化为数据库问题？
7. 为什么 LangChain 的 GraphCypherQAChain 在生成查询时设置 temperature=0？
8. 在知识图谱水平扩展的语境下，“以无状态架构作为扩展的助推器”意味着什么？

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/1SUlPOKg3QO3-Kvq2g82e5yvlaQlmMzHwfF-NUe68yGQ/viewform?usp=sharing)

**相关章节**：
- 第 1.1A 章（核心智能体架构 —— 智能体为何需要知识图谱的背景）
- 第 1.2 章（核心模式 —— ReAct 从结构化知识中获益）
- 第 1.3 章（多智能体系统 —— 共享知识图谱的构建）
- 第 1.5 章（向量嵌入 —— 理解 RAG 的局限）
- 第 1.6 章（有状态编排 —— 与图遍历并行的状态机概念）
- 第 1.7B 章（混合检索系统 —— 集成模式）
- 第 1.8 章（扩展与性能 —— 规模化下的图优化）

**✅ [参加第 1.7A 章测验](https://docs.google.com/forms/d/e/1FAIpQLSd8YokYuK9mCMUjZNdVPFV0XuXVuNqN3o2GA6bUgum261Fxqg/viewform?usp=dialog)**

---

[↑ 返回目录](#table-of-contents)

## 第 1 部分，第 1.7B 章：用知识图谱进行关系推理 —— 混合 RAG+KG 集成


本章通过三种混合集成模式，讨论何时以及如何将向量 RAG 与知识图谱遍历结合起来。内容涵盖区分简单事实型查询（仅用 RAG）、多跳关系型查询（仅用图）以及同时需要两者的混合查询的决策准则。本章演示了将语义理解与关系校验相结合的合规分析系统，分析了性能权衡（混合方案带来 50% 的延迟额外开销），并介绍了生产部署模式，包括把知识图谱用作记忆后端、工具调用增强器以及多智能体协调基础设施。本章强调在规模化场景下保持系统健康所需的优化策略与运维纪律。

**每周时间分配**：阅读：1.19 小时 | 主动学习：0.51 小时
总计：1.7 小时（阅读 1.19 小时，主动学习 0.51 小时）

**核心概念**：
- 向量 RAG、图增强 RAG、检索增强知识图谱、向量存储、语义搜索
- 知识图谱遍历、知识图谱实体遍历、作为记忆后端的图、用于分析的图投影、时序图管理、图健康监控、无破坏性变更的 schema 演进、数据质量与实体对齐
- 查询复杂度分析、查询模式分析、简单事实型查询、多跳关系型查询、混合查询、并行查询
- 实体链接桥接、实体类型过滤、关系连接证明、结果合并与排序、策略规则理解
- 语义与关系优势匹配、合规领域要求、性能权衡、语义覆盖度、关系准确度、索引优化、扩展挑战
- 图增强的工具调用、通过知识图谱进行多智能体协调、ReAct 模式增强、Plan-and-Execute 的图优势
- 共享记忆互补、时序上下文、记忆分层、三层架构、以实体为中心的召回

**关键问题**：
1. 在实现欺诈检测系统时，应如何根据查询特征选择 RAG、知识图谱还是混合方案？
2. 某公司的图包含 5000 万节点与 5 亿条边，p95 延迟为 800 毫秒；可能的三个原因与对应的诊断方法是什么？
3. 对于客户服务聊天机器人，哪些指标能表明混合 RAG+KG 值得其复杂度？何时又应当放弃它？
4. 为数百万个抽取出的提及设计实体消歧系统，如何在自动化与人工审核之间取得权衡？
5. 在生产环境中实现一个查询，检测高管的家庭成员是否投资于竞争对手？
6. 针对研究文献分析，对比三种混合模式，找出论文、作者、方法与结论之间的关联？
7. 何时基于图的智能体协调相比基于消息的通信能降低开销？
8. 如何把查询需求转化为针对生产规模优化的显式 Cypher 模式？

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/1fDKOJe1V-ilTPEDz29FKqtfN4fwTxYF6IBc7o-_m_Uc/viewform?usp=sharing)

**相关章节**：
- 第 1.7A 章（知识图谱基础 —— 核心概念与构建）
- 第 1.2 章（核心模式 —— 以知识图谱作为工具的工具使用架构）
- 第 1.3 章（多智能体系统 —— 扩展到基于图的协调机制）
- 第 1.4 章（记忆与感知 —— 补全三层记忆架构）
- 第 1.6 章（有状态编排 —— 状态机扩展到基于图的状态）
- 第 1.8 章（可扩展性与生产部署 —— 有状态系统的扩展）

**✅ [参加第 1.7B 章测验](https://docs.google.com/forms/d/e/1FAIpQLSc9dfmZrsOYn-pFxnxE_1tkUpu2ENwxUxqa0B2-UlS2Pz_p1Q/viewform?usp=dialog)**

---

[↑ 返回目录](#table-of-contents)

## 第 2 部分，第 2.1 章：框架全景


本章提供一套系统化的决策框架，用于在五大主流智能体框架（LangGraph、LangChain、AutoGen、CrewAI、Semantic Kernel）之间做选择：分析各框架的控制流模型如何与工作流架构、状态管理需求以及协作模式相匹配。通过实例讲解与对比案例，本章引导读者以分析性方式而非流行度来评估框架，从而确保架构决策与系统的长期需求保持一致。

**每周时间分配**：阅读：1.89 小时 | 主动学习：0.81 小时
总计：2.7 小时（阅读 1.89 小时，主动学习 0.81 小时）

**核心概念**：
- 控制流模型、LangGraph 图架构、LangChain 线性执行
- 状态模式、条件路由、循环支持
- 对话驱动的协调、AssistantAgent、UserProxyAgent、非确定性
- 涌现行为、基于角色的层级、任务委派
- 插件架构、语义函数（semantic functions）、原生函数
- Kernel 编排器、动态插件路由、插件发现、依赖注入
- 控制流复杂度、状态管理需求、协作模式
- 部署场景、框架选择标准
- 混合工作流模式、复杂状态需求、多轮搜索迭代
- 用户反馈集成、过度工程、架构错配
- 确定性破坏、状态管理局限、合规要求
- 第 1 步：控制流映射、第 2 步：状态分析、第 3 步：协作评估
- 第 4 步：企业场景、第 5 步：非功能需求、验证策略

**关键问题**：
1. LangGraph 基于图的方法与 LangChain 线性执行模型之间，根本的架构差异是什么？
2. 在智能体项目中，何时应选择 LangGraph 而非 LangChain？
3. AutoGen 对话驱动的协调与 CrewAI 基于角色的层级组织有何不同？
4. AutoGen 非确定性对话方式的关键优势与劣势是什么？
5. 为什么 Semantic Kernel 被描述为企业级框架？其复杂度在何时是值得的？
6. 为新的智能体项目选择合适框架的五个系统化步骤是什么？
7. 如何识别框架选型造成架构错配、与工作流需求正面冲突的情形？
8. 是什么使 LangGraph 成为需要迭代与用户反馈集成的工作流的合适选择？
9. 为什么用 CrewAI 实现迭代式自我纠错工作流可能带来实现上的挑战？
10. 在金融服务这类对合规要求高的应用中，确定性在框架选型中扮演什么角色？

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/1sMNPc3ARkGr-pLP7nA51-S8Tn-OcAMjdQPxexAx1cZs/viewform?usp=sharing)

**相关章节**：
- 第 1 部分 第 1.2 章（核心模式基础）
- 第 1 部分 第 1.5A 章（无状态 vs 有状态模式）
- 第 1 部分 第 1.5B 章（状态与控制流机制）
- 第 1 部分 第 1.6 章（编排扩展原则）
- 第 2 部分 第 2.2 章（LangGraph 深入解析）
- 第 2 部分 第 2.3 章（LangChain 实现）
- 第 2 部分 第 2.4 章（多智能体框架模式）

**✅ [参加第 2.1 章测验](https://docs.google.com/forms/d/e/1FAIpQLSeNbhCnlqM2jNNjOGS-Fed32VepTbG6c39tF_jNmGvmq7vBXw/viewform?usp=sharing&ouid=116579026379007071084)**

---

[↑ 返回目录](#table-of-contents)

## 第 2 部分，第 2.2 章：LangGraph

LangGraph 是一个通过显式图架构来构建智能体化工作负载的框架，其中节点是计算单元，边是控制流通道，状态是共享上下文。本章探讨基于图的设计如何实现迭代式改进、条件路由与故障恢复，同时界定何时 LangGraph 的复杂特性是合理的，以及何时更简单的框架更贴合工作负载需求。

**每周投入分配**：阅读：1.12 小时 | 主动学习：0.48 小时
总计：1.6 小时（1.12 小时阅读，0.48 小时主动学习）

**核心概念**：
- 节点、边、状态、Reducer、循环
- 状态图、Thread ID、检查点保存器（Checkpointer）
- 路由函数、决策树、可测试性
- 状态快照、工作负载恢复、时间旅行调试
- 持久化后端、检查点开销

**核心问题**：
1. LangGraph 工作负载的三个基本组成部分是什么？它们如何交互以实现复杂的控制流？
2. 条件边如何实现迭代式改进模式？在顺序式框架中，这类模式只能依靠提示词工程的变通手段？
3. 静态边与条件边有什么区别？各自适用的场景是什么？
4. `add_messages` 之类的状态 Reducer 与默认的覆盖行为有何不同？它们支持哪些模式？
5. 与顺序式框架中的隐式状态相比，LangGraph 中显式的状态模式定义有什么优势？
6. 什么时候 LangGraph 的架构复杂度是合理的？什么时候它属于过早优化？
7. 检查点机制如何为长时间运行的工作负载提供生产级可靠性？其延迟代价是什么？
8. 在 LangGraph 与 LangChain 中实现迭代式代码改进，代码复杂度差异有多大？
9. 与顺序式框架中基于提示词的路由相比，路由函数在可测试性上有何优势？
10. 通过检查点进行时间旅行调试，能为分析和改进工作负载行为提供哪些能力？

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/18Pd0DgV6z8ubxm4t7FgMv5o-WTXyJWBc2n1LCkWbrOE/viewform?usp=sharing)

**相关章节**：
- 第 1 部分 第 1.1 章（基础智能体架构）
- 第 1 部分 第 1.2 章（核心模式）
- 第 1 部分 第 1.5A 章（有状态编排）
- 第 1 部分 第 1.5B 章（有状态编排）
- 第 2 部分 第 2.3 章（LangChain 顺序式框架）
- 第 2 部分 第 2.4 章（多智能体框架）
- 第 2 部分 第 2.5 章（Semantic Kernel）
- 第 2 部分 第 2.6 章（工具集成）
- 第 2 部分 第 2.7 章（多模态 RAG）

✅ [参加第 2.2 章测验](https://docs.google.com/forms/d/1vtYJ1nUdFWFCl9zY1no54tQYgI9XFPL816KTNwgekZQ/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 2 部分 第 2.3 章：LangChain


LangChain 的 AgentExecutor 实现了第 1 部分介绍的 ReAct 模式，无需手动管理循环，把 150–200 行精心编写的代码抽象为一个统一接口。本章涵盖智能体类型、工具集成模式，以及如何识别工作负载何时超出 LangChain 的线性模型、需要迁移到 LangGraph。

**每周投入分配**：阅读：0.98 小时 | 主动学习：0.42 小时
总计：1.4 小时（0.98 小时阅读，0.42 小时主动学习）

**核心概念**：
- AgentExecutor、ReAct 模式、智能体草稿本（Scratchpad）、工具抽象
- 零样本 ReAct 智能体、对话式 ReAct 智能体、面向对话优化的零样本智能体
- ConversationBufferMemory、OpenAI Functions 智能体、Function-Calling API
- 工具描述质量、优雅降级、迭代循环信号
- 复杂状态信号、条件分支信号、过度设计

**核心问题**：
1. 与手动构建 ReAct 循环相比，AgentExecutor 解决了什么问题？
2. 请结合具体示例说明零样本 ReAct 智能体与对话式 ReAct 智能体的区别。
3. 为什么工具描述的质量对智能体性能很重要？
4. AgentExecutor 的根本局限是什么？你如何识别自己已经超出了这一局限？
5. ConversationBufferMemory 如何支持追问？
6. 使用 OpenAI Functions 智能体会带来哪些权衡？
7. 为什么把 temperature 设为 0 对智能体调用工具很重要？
8. 工具中完善的错误处理如何避免智能体失败？
9. 对于一个简单的问答智能体，比较 LangChain 与 LangGraph 的开发负担。
10. 什么时候应该选择 LangChain 而不是 LangGraph？

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/1QCeo9aUUGxNr9NVpyJPYMLBv4hSZqVu7Ufn7aZv5Y7k/viewform?usp=sharing)

**相关章节**：
- 第 1 部分 第 1.1A 章（UI 基础）
- 第 1 部分 第 1.2 章（工具使用）
- 第 1 部分 第 1.3 章（记忆系统）
- 第 1 部分 第 1.4 章（ReAct 模式）
- 第 2 部分 第 2.1 章（框架全景）
- 第 2 部分 第 2.2 章（LangGraph）
- 第 2 部分 第 2.4 章（多智能体框架）

✅ [参加第 2.3 章测验](https://docs.google.com/forms/d/1s8K94UD7KQ7Z5dK7Hw6iq7HxNN4_4fFyFTCO2AAvJdU/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 2 部分 第 2.4 章：多智能体框架


本章探讨多智能体协同的两种根本不同的方法：AutoGen 基于消息驱动的对话式架构，以及 CrewAI 的组织结构模型。本章分析对话灵活性与可复现性之间的权衡，以及将多智能体系统与专用单智能体框架组合使用的模式。

**每周投入分配**：阅读：1.47 小时 | 主动学习：0.63 小时
总计：2.1 小时（1.47 小时阅读，0.63 小时主动学习）

**核心概念**：
- ConversableAgent、AssistantAgent、UserProxyAgent、消息驱动架构
- 回复函数、GroupChat、非确定性权衡、状态同步挑战
- 智能体角色定义、任务定义、Crew 编排、顺序流程
- 分层流程、委派机制、基于角色的抽象、质量门禁
- AutoGen 的优势与劣势、CrewAI 的优势与劣势、模式匹配准则
- 确定性 vs 灵活性权衡、混合架构模式、框架组合策略

**核心问题**：
1. 构建多智能体系统时，我应该在什么情况下使用 AutoGen 而不是 CrewAI？
2. AutoGen 的对话式协同与 CrewAI 的组织结构之间有哪些关键权衡？
3. 在多智能体系统中，我该如何处理状态管理与上下文传递？
4. 将多智能体框架与单智能体框架集成时，最常见的失败模式是什么？
5. 什么时候我应该使用 CrewAI 的分层流程而不是顺序流程？
6. AutoGen 的消息驱动架构如何实现单智能体框架无法实现的能力？
7. 对于多智能体系统，我应该实现哪些可观测性与调试策略？
8. 我应该如何组织 CrewAI 中的智能体角色与能力，以确保正确的委派？
9. 在生产系统中使用 AutoGen 时，我该如何处理确定性与可复现性？
10. 对于复杂的生产系统，我应该如何组合多智能体框架与单智能体框架？

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/1D9uH2BZHLmFzMVBCrwRwcYao9SIEE8enbr0YurbQhjY/viewform?usp=sharing)

**相关章节**：
- 第 1 部分 第 1.3 章（多智能体系统）
- 第 2 部分 第 2.1 章（框架全景）
- 第 2 部分 第 2.2 章（LangGraph）
- 第 2 部分 第 2.3 章（LangChain）
- 第 2 部分 第 2.5 章（Semantic Kernel）
- 第 3 部分 第 3 章（优化与评估）

✅ [参加第 2.4 章测验](https://docs.google.com/forms/d/1l9QELiqLpXgt_F2EspmqDzw7i9BcmoACJpxZi8WjtRg/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 2 部分 第 2.5 章：Semantic Kernel —— 企业级框架与插件架构


Semantic Kernel 提供了一个中心化的编排组件，通过依赖注入模式管理服务注册、插件发现与执行协调。该框架区分语义函数（由 LLM 驱动的推理）与原生函数（确定性代码），使插件能够将 AI 能力与可靠的系统集成相结合，同时支持通过 LLM 驱动的编排进行动态路由。

**每周投入分配**：阅读：1.2 小时 | 主动学习：0.5 小时
总计：1.7 小时（1.2 小时阅读，0.5 小时主动学习）

**核心概念**：
- 内核（Kernel）
- 服务注册
- 依赖注入
- 插件注册
- 编排器 LLM
- 语义函数
- 原生函数
- 函数组合
- 动态路由
- 函数选择行为（Function Choice Behavior）

**核心问题**：
1. 为什么 Semantic Kernel 要区分语义函数与原生函数？各自应该在什么时候使用？
2. 请解释内核的依赖注入模式如何让框架具备企业级的生产就绪能力。
3. 动态路由解决了什么问题？它又引入了哪些挑战？
4. 将 Semantic Kernel 的插件架构与 LangChain 的工具集成做比较，应该如何选择？
5. 为什么函数描述的质量对 Semantic Kernel 的路由可靠性至关重要？
6. 什么时候 Semantic Kernel 属于过度设计？有哪些更简单的替代方案更合适？
7. 插件在多个智能体之间复用，如何在企业环境中带来效率提升？
8. FunctionChoiceBehavior 是什么？它如何解决路由的非确定性？

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/19IY2XiDVAlbZQwlvoqH9D0fYaA3XBShjzPs5IT5L8X4/viewform?usp=sharing)

**相关章节**：
- 第 2.1 章（框架全景——作为选型替代方案）
- 第 2.2 章（LangGraph 对比）
- 第 2.3 章（LangChain 对比）
- 第 2.4 章（多智能体框架对比）
- 第 2.6 章（工具集成模式）
- 第 2.7 章（RAG 集成）

✅ [参加第 2.5 章测验](https://docs.google.com/forms/d/18KzsSdxbKRDJBiV68SQYE31Z4-GaKD6OvLWE4lZs3S8/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 2 部分 第 2.6 章：工具集成与函数调用


工具集成确立了语言模型如何通过结构化的函数调用请求外部工具执行：由应用程序负责解析 JSON、校验输入并管理执行。本章涵盖函数调用的机制、基于 JSON Schema 标准的模式设计、用于表达顺序依赖的工具链式调用、并行执行优化，以及包括错误处理与 NVIDIA NIM 优化在内的生产实践考量。

**每周投入分配**：阅读：2.8 小时 | 主动学习：1.2 小时
总计：4.0 小时（2.8 小时阅读，1.2 小时主动学习）

**核心概念**：
- 函数调用
- 函数模式
- JSON 输出生成
- 并行函数调用
- 工具链式调用
- 工具模式设计
- 面向模态的嵌入
- 并行执行模式
- NVIDIA NIM
- 函数描述质量

**核心问题**：
1. 请解释为什么 LLM 从不直接执行函数，以及这一区别对生产系统为何重要。
2. 是什么让函数描述对工具选择的准确性至关重要？糟糕的描述如何造成生产故障？
3. 比较顺序执行与并行工具执行。各自适用的场景是什么？风险又是什么？
4. 解释工具模式设计，并说明为何厂商特定的差异会造成跨厂商的可移植性挑战。
5. 工具链式调用解决了什么问题？其级联失败模式是什么？
6. 解释并行工具执行，并说明它何时能带来真正的价值、何时只会徒增复杂度。
7. 说明 NVIDIA NIM 与工具执行优化之间的关系。为什么 NIM 特别有利于工具密集型智能体？
8. 关于函数调用的哪些误解最容易导致生产故障？你该如何避免它们？
9. 你如何设计能够跨多个 LLM 厂商工作的工具模式？
10. 解释工具链式调用如何与状态管理挑战相连，以及有哪些策略可以应对这些挑战。

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/1-gbnIpSv2kFrPUEEFG8RmN_9wW3X_FtH7urOPEJcTuY/viewform?usp=sharing)

**相关章节**：
- 第 2.5 章（Semantic Kernel 插件函数）
- 第 2.2 章（LangGraph 节点实现）
- 第 2.3 章（LangChain 智能体执行）
- 第 2.4 章（多智能体工具协同）
- 第 2.7 章（多模态工具）
- 第 2.8 章（工具执行中的错误处理）
- 第 2.9 章（流式工具结果）

✅ [参加第 2.6 章测验](https://docs.google.com/forms/d/1GBnXoaDWStpAvBGOOT9ApCZLnTm7m8GRgegLAUN5kNg/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 2 部分 第 2.7 章：多模态 RAG —— 视觉、音频与文本的融合


多模态 RAG 把检索增强生成扩展到能够处理文本之外的视觉与音频内容，并通过三种架构方案解决语义对齐难题：使用 CLIP 的统一嵌入空间、用视觉-语言模型把所有模态落到文本、以及分库存储配合跨模态重排序。本章涵盖视觉模型专门化、图像路由逻辑、基于 Whisper 并带时间索引的音频转录，以及用于生产部署的 NVIDIA 多模态技术栈。

**每周投入分配**：阅读：3.7 小时 | 主动学习：1.6 小时
总计：5.3 小时（3.7 小时阅读，1.6 小时主动学习）

**核心概念**：
- 语义对齐
- 信息密集型可视化
- 多模态嵌入
- CLIP（对比式语言-图像预训练）
- 图像描述生成
- DePlot
- 统一向量空间
- 跨模态重排序
- NVIDIA NIM

**核心问题**：
1. 为什么传统的纯文本 RAG 系统在多模态文档上会失效？
2. CLIP 的统一嵌入方案与 DePlot 的结构化提取方案之间有哪些关键权衡？
3. "落到文本"（ground to text）方案如何在保持基于文本的检索效率的同时，保留信息密集型可视化的细节？
4. 为什么图像路由（决定每个图像由哪个视觉模型处理）对多模态 RAG 的效果至关重要？
5. "语义对齐"在多模态场景中意味着什么？为什么它对检索很重要？
6. Whisper 对音频做带时间索引的分块，与固定长度的文本分块有何不同？这种差异带来了什么优势？
7. 方案 1（统一嵌入）、方案 2（落到文本）与方案 3（分库存储加重排序）之间的功能差异是什么？
8. 为什么 NVIDIA 的 NIM 相比原生模型服务能带来显著的性能提升？这些提升依赖哪些技术？
9. Milvus 如何实现比基于 CPU 的向量数据库快 10–100 倍的向量检索？
10. 高效的多模态预处理流水线应遵循哪些关键设计原则？

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/1dZZIS9qrg0yokglW9vurYWoEmjoeyiebcpuIJMaahrw/viewform?usp=sharing)

**相关章节**：
- 第 2.6 章（工具集成基础）
- 第 2.5 章（面向模态处理的插件架构）
- 第 2.8 章（视觉流水线中的错误处理）
- 第 2.9 章（多模态结果流式输出）
- 第 3 部分（多模态系统的部署与扩展）

✅ [参加第 2.7 章测验](https://docs.google.com/forms/d/1uOVFi6y7U-vlQx6LVlkRdBBhJ0Xg2YW8V2nGtnnz0eU/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 2 部分 第 2.8 章：错误处理与韧性


错误处理模式通过分层防御建立生产级韧性：针对瞬时故障的重试逻辑、针对持续性故障的回退策略、保持部分可用性的优雅降级，以及防止多智能体系统中级联故障的熔断器。本章讨论与 LangChain 和 LangGraph 的框架集成，提供具备韧性的多工具智能体的实例，并解释如何通过全面应用这些模式达成 99.9% 的可用率。

**每周投入分配**：阅读：0.9 小时 | 主动学习：0.4 小时
总计：1.3 小时（0.9 小时阅读，0.4 小时主动学习）

**核心概念**：
- 瞬时故障
- 指数退避
- 抖动（Jitter）
- 重试预算
- 回退策略
- 模型路由
- 优雅降级
- 熔断器模式
- 关闭状态
- 半开状态

**核心问题**：
1. 什么时候应该采用重试逻辑，什么时候应该采用回退策略？
2. 优雅降级与回退策略之间的关键区别是什么？
3. 为什么在重试延迟中加入抖动能避免惊群（thundering herd）问题？
4. 熔断器如何在服务故障期间防止线程池耗尽？
5. 在多智能体系统中，熔断器与优雅降级之间是什么关系？
6. 为什么共享故障域对回退策略很危险？
7. 优雅降级与返回空结果或错误有什么不同？
8. 你如何监控重试逻辑是在正常工作，还是在白白消耗资源？
9. 为什么 LangGraph 基于条件边的错误处理方式优于 LangChain 的回调？
10. 99% 与 99.9% 的可用率目标在生产上有何差别？错误处理模式如何达成这些目标？

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/1dw5bhQ1ByWWPaVKHTraRKR5wGIXEapuq2bqdNnkKYgU/viewform?usp=sharing)

**相关章节**：
- 第 2.6 章（工具编排与 API 故障）
- 第 2.7 章（视觉流水线中的错误处理）
- 第 2.9 章（流式错误传递）
- 第 2.2 章（LangGraph 条件边）
- 第 2.3 章（LangChain 错误回调）
- 第 3 部分（生产部署与监控）

✅ [参加第 2.8 章测验](https://docs.google.com/forms/d/10KSLeNg8z7FgW7C5fmh0Zy75_0Rn1IpEK6TcQSLa5Kk/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 2 部分 第 2.9 章：流式输出与实时响应


流式输出把智能体的响应模式从"先累积后展示"重构为"边生成边流式发送"，以化解空白屏幕带来的心理效应和用户流失。本章涵盖感知延迟原则——亚秒级反馈比总延迟更重要——、首 token 时间（Time to First Token）优化、Server-Sent Events 与 WebSockets 之间的协议选择，以及用于生产级流式基础设施的 LangServe 集成。

**每周投入分配**：阅读：1.4 小时 | 主动学习：0.6 小时
总计：2.0 小时（1.4 小时阅读，0.6 小时主动学习）

**核心概念**：
- 感知延迟
- 首 token 时间（TTFT）
- 亚秒级反馈阈值
- 空白屏幕效应
- 逐 token 流式输出
- 异步生成器模式
- Server-Sent Events（SSE）
- WebSocket 双向性
- 检索延迟占主导
- 语义缓存

**核心问题**：
1. 为什么用户会觉得耗时 25 秒的流式响应比耗时 15 秒的批量响应更快？
2. 你正在实现一个带检索与生成的客户支持智能体。应该使用 SSE 还是 WebSockets？
3. 你的 TTFT 是 2.8 秒（1.2 秒检索、0.4 秒编码、1.2 秒排队等待）。哪项优化能带来最大影响？
4. 如果 WebSocket 连接在流式传输中途断开，会发生什么？SSE 在同样情形下有何不同？
5. LangServe 的自动流式与使用 FastAPI 手动构建流式端点有何不同？
6. 在一个复杂的多步骤智能体中（检索 3 秒、分析 5 秒、生成 5 秒），用户应该在什么时候看到首段输出？
7. 为什么语义缓存在客户支持场景中对流式 TTFT 优化尤其有效？
8. 你会如何实现流式错误处理，使用户能收到清晰的错误提示，而不是连接被突然中断？
9. TTFT 的关键组成部分有哪些？在 RAG 智能体中通常是哪一项占主导？
10. 提示词压缩如何解决编码延迟？能带来哪些吞吐提升？

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/11eHMRr-rKwryaHVflbmRTJz0E4Us2uRH6DJpAqKTVhs/viewform?usp=sharing)

**相关章节**：
- 第 2.1 章（框架对流式输出的支持）
- 第 2.2 章（LangGraph 流式输出多智能体结果）
- 第 2.3 章（LangChain 流式链）
- 第 2.6 章（工具结果流式输出）
- 第 2.8 章（流式错误处理）
- 第 3 部分（性能优化与扩展考量）

✅ [参加第 2.9 章测验](https://docs.google.com/forms/d/1_LJfwkS10MVPZgoJUMh6BFZrOFD-s2mtrdIcbVmhAhA/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 3 部分 第 3.1A 章：实现评估流水线与任务基准测试 —— 引言、动机与核心概念

本章是基础性章节，确立了系统性智能体评估所需的术语体系、概念框架与架构原则。它引入了评估金字塔（单元测试、离线评估、预发布环境、A/B 测试），区分了离线评估属于"预测"、在线评估属于"测量"，并展示了持续评估如何防止未来的变更造成回归、破坏原本正常工作的能力。

**每周投入**：阅读：2.1 小时 | 主动学习：0.9 小时
总时长：3.0 小时（阅读 2.1 小时，主动学习 0.9 小时）

**核心概念**：
- 评估流水线、任务成功率（TSR）、离线评估、在线评估、A/B 测试、真值标签
- 生产与测试的差距、单元测试、预发布环境、在线 A/B 测试、金字塔式故障模式分离
- 成本指数级增长、回归累积、左移测试、持续评估、均衡指标
- 单维度优化陷阱、隐性性能退化、以测量为驱动的信心
- 离线评估适用场景、在线 A/B 测试的必要性、测试数据集局限性、统计显著性要求
- 渐进式工作流模式、自动触发、测试数据集加载、指标计算、决策门禁强制执行
- 预发布验证、A/B 测试部署、自动回滚、审计轨迹生成
- 数据集准备、基线测量、变更实施、自动化评估、统计显著性分析
- 部署决策逻辑、迭代优化

**核心问题**：
1. 为什么离线评估被称为"预测"，而在线 A/B 测试被称为"测量"？两者的根本区别是什么？
2. 某团队运行离线评估显示准确率提升了 92%，却没有在向全部用户部署前运行 A/B 测试。这种做法会带来哪些风险？
3. 你正在为一个每天处理 100,000 次查询的客户支持智能体设计评估流水线。需要哪些流水线阶段，为什么？
4. 评估流水线阻止了部署，因为 P95 延迟增加了 0.5 秒，突破了 20% 的阈值。新模型将准确率提升了 4%。工程师是否应该覆盖该门禁？
5. 离线评估数据集中需要多少测试用例，才能可靠地预测生产环境中的表现？
6. 你的团队运行 A/B 测试比较新智能体与基线智能体。24 小时后，实验组的任务成功率为 87%，对照组为 86%。应该宣布测试获胜吗？
7. 当离线评估得到 92% 的准确率，而线上在任务完成率为 87% 的情况下仍出现 15% 的任务放弃率时，你该如何处理？
8. 对于一个新的智能体项目，你可以实现的最小可行评估流水线是什么，用来捕获明显的回归？

💭 [用自己的语言回答问题](https://docs.google.com/forms/d/18jaqGsULpEaGpx7NxPzclx_XsiOZfcVeareOozH5zXM/viewform?usp=sharing)

**相关章节**：
- 第 3.1B 章（自定义指标与 CI/CD 集成）
- 第 3.1C 章（指标
- 追踪
- 与监控）
- 第 3.2+ 章（高级评估技术）

✅ [参加第 3.1A 章测验](https://docs.google.com/forms/d/1KPObiIs-NsSrDIdWRpij_axE__ack1a2jDy4uLgOJ_A/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 3 部分，第 3.1B 章：实现评估流水线与任务基准测试 —— 自定义指标与 CI/CD 集成


本章是带指导的实践章节，在 3.1A 的评估流水线基础概念之上，讲解自定义领域专用指标与持续集成基础设施的落地实现。它展示了如何通过关键词匹配、LLM-as-judge 评分和基于规则的校验来衡量超越通用准确率与延迟的业务价值，随后把这些自定义指标集成到 GitHub Actions 工作流中，实现自动化质量保障。

**每周投入**：阅读：1.0 小时 | 主动学习：0.4 小时
总时长：1.4 小时（阅读 1.0 小时，主动学习 0.4 小时）

**核心概念**：
- 自定义指标、关键词匹配评分、LLM-as-Judge 评估、规则校验
- 共情评分、策略合规评分、工具效率评分、指标聚合
- MLflow 自定义指标集成、工作流触发器、评估执行脚本、PR 评论格式化
- 质量门禁、自动防护机制、统计比较逻辑、阈值配置
- 失败处理韧性、响应时间分段、策略限额校验、冗余检测
- 持续评估基础设施、人工评估的危险性、强制质量保障
- 基于路径的触发器、质量门禁强制执行、被阻断的合并、配置驱动的阈值
- 自动回滚、智能缓存、分阶段评估、冒烟测试、全面评估集

**核心问题**：
1. 你的客户支持智能体任务成功率达到 92%，但退款请求要花 30 秒，而账户咨询只要 5 秒。你会实现什么自定义指标来检测这一问题？
2. 共情评分如何应对机械式的重复作答——即为了抬高共情分而把"我理解"重复五次的回复？
3. 你的策略合规检查器需要检测诸如折扣优惠超过 15% 上限、或金额超过 $50 限额的违规行为。你会采用什么方法？
4. 你在 GitHub Actions 中实现了持续评估，但评估耗时 10 分钟，拖慢了开发者的反馈速度。你会如何优化？
5. 你如何判断评估指标上的回归是真正的质量问题，还是仅仅是随机波动？
6. 你的 GitHub Actions 评估工作流会发布各个 pull request 之间的对比结果，但它们的测试数据集各不相同。如何确保指标对比的公平性？
7. 你的持续评估发现新的提示词模板把准确率从 89% 提升到 92%，但同时把 P95 延迟从 2.0 秒推高到 3.5 秒。你应该接受还是阻断这个 PR？
8. 面对离线评估预测准确率 92%、而 A/B 测试只测得 87% 任务成功率这一问题，你该如何处理？

💭 [用自己的语言回答问题](https://docs.google.com/forms/d/16XDu67ICAelCAcPso3LCqnSPczWtDD5RiqKvXiTI2Vo/viewform?usp=sharing)

**相关章节**：
- 第 3.1A 章（基础）
- 第 3.1C 章（独立实践）
- 第 3.2 章及以后（性能对比）

✅ [参加第 3.1B 章测验](https://docs.google.com/forms/d/1fEhq0wN_qQrXTP7J39awodsskNKLVUe1FppPvvSk1fo/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 3 部分，第 3.2 章：跨任务与数据集比较智能体性能 —— 多基准测试评估与统计严谨性


本章把单一指标评估扩展为全面的多基准测试评估，揭示被聚合评分所掩盖的能力分布。它指出了基准测试认知误区的关键风险，讲解了可防止混淆变量的受控对比方法论，并展示了跨数据集泛化测试如何暴露脆弱性而非稳健推理。特别关注 AgentBench 的八环境框架，以及把离线评估连接到生产部署的持续反馈闭环。

**每周投入**：阅读：2.7 小时 | 主动学习：1.2 小时
总时长：3.9 小时（阅读 2.7 小时，主动学习 1.2 小时）

**核心概念**：
- 多维基准测试、能力分布、过拟合检测、泛化能力
- 架构对比、行业专用基准测试、基准测试套件构建、生产分布镜像
- 变量隔离、混淆变量、性能分布、置信区间、配对评估
- 统计显著性检验、实际显著性阈值、统计纪律
- 优雅降级、断崖式失败、域内数据集、域外数据集、时间偏移
- 多模态迁移、泛化差距、分布脆弱性
- 大样本局限、上下文相关阈值、McNemar 检验、置信区间计算
- 静态快照、可测性偏差、尾部案例代表不足、扭曲的优化激励
- 平均情形表现、定性因素缺失、三角验证策略、健康的怀疑态度
- AgentBench（8 个环境）、全新领域、标准化编译、操作系统环境
- 数据库环境、知识图谱环境、数字卡牌游戏环境、横向思维谜题
- 家务环境、网购环境、网页浏览环境
- 简单/中等/困难分层、能力下限、决策复杂度、长时程推理
- 强调多轮交互、上下文一致性、信息保留、自适应策略调整
- 推理失败、决策失败、指令遵循失败、规划失败
- 前沿模型差距、非确定性影响、工具选择优化
- 基线评估、分层评估策略、架构对比、全领域进展跟踪
- WebArena 框架、GAIA 基准测试、τ-Bench、AstaBench
- 显式反馈机制、隐式行为信号、选择偏差、响应时序偏差
- 放弃率、查询改写模式、交互时长离群值、下游动作跟踪
- 情感分类、基于方面的情感分析、主题提取、根因分析
- 优先级评分、优先级排序框架、严重程度加权
- 测试数据集增强、提示词优化、提示词校验、架构改进
- 护栏调整、持续改进飞轮、复利式改进、季度性改进

**核心问题**：
1. 为什么单一基准测试不足以充分评估智能体能力？依赖单一基准测试评估会带来哪些具体风险？
2. 受控对比方法论与朴素性能对比有何不同？为什么这种差异对部署决策很重要？
3. 跨数据集泛化测试中的哪些模式能够揭示智能体的脆弱性，而非稳健的推理能力？
4. 统计显著性阈值与实际显著性阈值如何协同指导部署决策？
5. 基准测试为什么会系统性地误导我们？有哪些评估策略可以弥补这些局限？
6. AgentBench 的八环境结构如何带来单环境基准测试无法揭示的洞见？
7. 显式反馈机制与隐式行为信号如何提供互补的洞见？
8. 持续改进飞轮如何把用户反馈转化为复利式的质量提升？

💭 [用自己的语言回答问题](https://docs.google.com/forms/d/17lHL7q_P4TvuHWnCcsnyXYvjdWI1nQfKROisDq-ESF0/viewform?usp=sharing)

**相关章节**：
- 第 3.1A-3.1C 章（单一指标基础）
- 第 1-2 部分（智能体基础与架构）
- 第 3.3 章（超参数调优与提示词优化）

✅ [参加第 3.2 章测验](https://docs.google.com/forms/d/1xIx6xl8c2kGfsV4qokwFpAM6gYj1oUdRI1PdOm0ckdE/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 3 部分，第 3.3 章：网页导航与交互基准测试 —— Web 智能体评估与多跳问答


本章专门讲解面向网页导航智能体与多跳推理任务的评估方法论，应对在动态、交互式环境中评估智能体的独特挑战。内容包括 Web 智能体基准测试（Mind2Web、WebArena、Web Bench）、用于捕捉关键中间动作的指标，以及离线静态基准测试与线上生产现实之间的关键差距——在生产环境中智能体会遇到 CAPTCHA、动态定价与身份认证。着重强调多跳问答的故障模式、非确定性的处理，以及领域专用基准测试的必要性。

**每周投入**：阅读：5.7 小时 | 主动学习：2.4 小时
总时长：8.1 小时（阅读 5.7 小时，主动学习 2.4 小时）

**核心概念**：
- Web 智能体基准测试、Mind2Web、WebArena、Online-Mind2Web、Web Bench
- ST-WebAgentBench、WebCanvas、τ-bench (TAU-Bench)、成功率、Pass@k 与 Pass^k 指标
- 基于里程碑的评分、动作推进指标、工具选择准确率、参数准确率
- 效率指标、幻觉率、行为一致性指标、冒烟测试策略
- 中等评估集、全面评估集、在线评估、隐式反馈机制
- 显式反馈、A/B 测试、影子测试、采样策略、评估飞轮
- LLM-as-a-Judge、WebJudge、泛化能力、RAGAS、LLM Guard、评估器被利用的风险
- 随机性挑战、轨迹匹配的局限、基于模拟的测试、环境多样性覆盖
- 可接受的降级模式、断崖式失败、人类在环测试
- 评估所需的上下文提供、结果校验范式
- 线下高成功率的误区、把成功率当作可靠性代理指标、面向非确定性系统的确定性指标
- 忽视边缘案例、混合难度层级、单轮评估假设
- 电商自动化、READ 与 WRITE 任务区分、单次交易成本、现实世界挑战
- 分阶段发布策略、客服自动化、企业 IT 自动化、策略遵循度指标
- 金融服务、研究与信息综合
- 多跳问答定义、单跳与多跳的区别、推理随机性、可分离但相互作用的维度
- HotpotQA、HotpotQA 设置、推理分类法、支撑事实评估、性能基线
- 2WikiMultiHopQA、MuSiQue、MultiHopRAG 与 LIMIT、MMInA
- 精确匹配（EM）、F1 分数、段落级检索指标、事实级指标、诊断能力
- 推理链指标、联合指标、支撑事实指标、实际含义
- 蝴蝶效应、故障模式区分、分层分析、推理链评估、错误模式分析
- 针对性干预、离线多跳评估、离线局限性、在线多跳评估
- 标签可靠性挑战、集成方法
- 答案准确率误区、数据集人工制品利用、段落级与事实级混淆、忽视错误传播
- 将联合指标作为次要指标、实际后果
- 科学研究综合、企业知识管理、医疗证据综合
- 冲突证据管理、持续改进飞轮
- 医疗与通用场景的误区、监管维度差距、数据特征差异
- 业务影响的不对称性、缺失集成上下文
- 真实问题收集、真实与合成数据的取舍、TAU-bench 混合方法
- 规避数据集人工制品、有状态评估、医疗基准测试、多模态集成
- 医疗合规性、工作流集成测试、金融基准测试、金融合规
- 风险不对称性、多智能体协同、法律领域基准测试、法律保密性、法律完备性指标
- 零售基准测试、零售满意度不对称性、制造领域基准测试

**核心问题**：
1. 为什么前沿智能体在离线 WebArena 上取得 60% 成功率，到了真实网站评估中却下降到 30%？
2. HotpotQA 的答案精确匹配（44%）与要求支撑事实的联合指标（11%）之间的差距，如何改变我们对基准测试表现的理解？
3. 为什么 Web 智能体在 READ 任务与 WRITE 任务上的失败方式不同，评估方式又该如何区别？
4. τ-bench 的 pass@k 指标从根本上如何改变我们对生产部署中智能体可靠性的认识？
5. 请解释为什么针对金融、医疗和法律应用的领域专用基准测试值得投入大量开发资源，而对客服自动化可能并不值得。
6. 评估飞轮如何把离线基准测试与生产监控连接起来，这种集成为性能带来哪些提升？
7. 为什么在多跳推理中，智能体在前几跳的失败比在后几跳的失败更为系统性？
8. 为什么生产环境下的多领域部署必须包含回退层级与跨领域一致性测试？

💭 [用自己的语言回答问题](https://docs.google.com/forms/d/1LuAa0-BTaiMWOQPXbsLPWTnRUWoICWcz25QMgKS-hvk/viewform?usp=sharing)

**相关章节**：
- 第 3.2 章（多基准测试评估）
- 第 3.1A-3.1C 章（基础评估基础设施）
- 第 3.4+ 章（高级技术）

✅ [参加第 3.3 章测验](https://docs.google.com/forms/d/10eGq1Q85Z70u3OPuxRZxJxkj3w5tDCL8xT_8mNExgso/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 3 部分，第 3.4 章：调优参数


系统化的参数调优要求理解配置变更如何通过准确率-延迟-成本的权衡空间同时影响多个性能维度。本章为生产环境下的智能体部署决策建立了多目标优化框架与 Pareto 前沿分析，从而避免单指标优化带来的病态问题。

**每周投入**：阅读：2.7 小时 | 主动学习：1.1 小时
总时长：3.8 小时（阅读 2.7 小时，主动学习 1.1 小时）

**核心概念**：
- 路由模型
- 温度参数
- Top-p 核采样
- 上下文窗口管理
- 迭代预算
- 工具配置
- Pareto 前沿
- 权衡空间
- 配置实验
- 质量优化配置
- 均衡性能配置
- 延迟优化配置
- 成本优化配置
- 延迟分解
- 量化
- 投机解码
- 提示词缓存
- 成本分解
- 推理链缓存
- 复杂度分级
- 批处理
- 响应缓存
- 多目标优化
- 代表性采样
- 基于约束的选择
- 基于偏好的排序
- 过拟合的表现
- 信息泄漏
- 留出验证
- 交叉验证
- 分布外验证
- 生产环境中的 A/B 测试

**核心问题**：
1. 为什么我们不能只优化准确率这类单一指标，而不同时考虑延迟与成本？
2. 我们如何确定温度参数取 0.2 还是 0.3 对我们的特定智能体才是最优的？
3. 我们的智能体每天处理 100 万次查询，当前成本为 $0.15/次（每天 $150K）。我们是否应该投入模型路由？
4. 我们如何知道参数调优是真正泛化到了生产环境，而不只是记住了测试集的偶然特征？
5. 我们对智能体做了性能剖析，发现工具执行占延迟的 60%，推理占 40%。我们应该推进模型优化还是工具优化？
6. 我们的离线基准测试显示准确率 92%，而生产环境显示 78%，这两者之间的差别在哪里？
7. 我们的 Pareto 前沿分析识别出四种满足约束的配置。我们该如何在它们之间做选择？
8. 我们正在考虑使用路由模型把查询分发到 GPT-3.5 或 GPT-4。最大的风险是什么？

💭 [用自己的语言回答问题](https://docs.google.com/forms/d/1YFDszYseCzx68rsjWeoW2GDjpu36ccjkP5u9QaAu1TY/viewform?usp=sharing)

**相关章节**：
- 3.1（评估流水线）
- 3.2（对比性能）
- 3.5（提示词优化）
- 3.6（轨迹分析）
- 3.7（工具审计）

✅ [参加第 3.4 章测验](https://docs.google.com/forms/d/1L8N0XfuZSeHCbccANkbSoBMuJdB-D40p_SSD8yLeuNw/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 3 部分，第 3.5 章：提示词优化、少样本学习、基于智能体轨迹的微调与奖励建模


提示词优化代表的是通过以测量为驱动的精炼来系统性地工程化智能体指令，其中的细微措辞变化会显著改变准确率（8-15 个百分点）。本章涵盖提示词优化、利用 2-5 个示例的少样本学习、结合人类专家经验与 LLM 生成变体的基于轨迹的微调，以及通过人类反馈强化学习（RLHF）进行的奖励建模。

**每周投入**：阅读：4.5 小时 | 主动学习：1.9 小时
总时长：6.4 小时（阅读 4.5 小时，主动学习 1.9 小时）

**核心概念**：

**核心问题**：
1. 为什么给提示词加一句澄清说明有时能让准确率提升 15 个百分点，而加上五句冗长的话却会让性能下降 8 个百分点？
2. 什么时候应该选择少样本学习而不是微调，这一选择在实际层面意味着什么？
3. 组织如何防止标注偏差污染奖励模型并损害智能体的对齐效果？
4. 请解释上下文学习（少样本）与微调作为两种根本不同的适配方式之间的区别，以及各自适用的场景。
5. RLHF 的三个顺序阶段是什么？为什么奖励模型质量是决定智能体对齐成败的关键瓶颈？
6. 与只做 SFT 相比，在监督微调（SFT）之前进行持续预训练（CPT）如何加快收敛并提升最终模型质量？
7. 在反馈校验中，请描述显式用户反馈（评分、打分、评论）与隐式信号（行为模式、查询改写）之间的区别。
8. 请解释拒绝采样微调（RFT）如何提升训练数据质量，并支持让改进不断累积的渐进式迭代循环。

💭 [用自己的语言回答问题](https://docs.google.com/forms/d/1UDQBEIAq_lkmUtMa5GZl-Q_0G7LFQgITV0WPNIaqBRU/viewform?usp=sharing)

**相关章节**：
- 3.1（评估）
- 3.2（对比测试）
- 3.4（参数调优）
- 3.6（轨迹分析）
- 3.7（工具审计）

✅ [参加第 3.5 章测验](https://docs.google.com/forms/d/11CPqSTsT2EOt6mSQqEx9RRIiQdZwW_CRlj5JCCJ8Qik/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 3 部分，第 3.6 章：轨迹分析与执行调试

追踪分析通过系统化的埋点、可视化和取证分析，将不透明的智能体故障转化为可执行的调试洞察。本章建立了用于调试非确定性概率推理的完整框架——在传统软件调试方法力有不逮的场景下，借助详尽的执行追踪让不可见的决策过程变得可观测。

**每周时间分配**：阅读：6.4 小时 | 主动学习：2.8 小时
总计：9.2 小时（阅读 6.4 小时，主动学习 2.8 小时）

**核心概念**：
- 追踪与埋点基础：Span、思考-行动-观察循环、OpenTelemetry 语义约定、层级化追踪结构
- 埋点层级：工作流级埋点、智能体级埋点、工具级埋点
- 数据采集与指标：时序数据、Token 消耗指标、状态转换、并发信息
- 可视化与分析工具：时间线视图、层级化探索、错误高亮、对比视图、过滤与搜索能力
- 故障类别：工具选择失败、参数生成失败、响应解析失败、状态管理失败、幻觉检测、预期内错误、意外错误、上下文窗口截断、时序与因果性问题、Token 优化权衡
- 调试方法论：根因分析、追踪优先的调试、全面埋点、系统化排查推进、事件响应模式、调试手册、逻辑错误分类体系
- 检查层级：步骤级检查、路径级检查、任务级检查、对比式检查
- 验证技术：带反向验证的正向推理、逐步自验证、一致性检查、置信度分数传播、步骤级验证器、形式化验证、自动推理集成、多模型验证集成
- 高级分析方法：子思维现象、子思维提取、一致性相关性分析、基于电路的推理验证、归因分析、特征激活监控
- 领域特定验证：数学推理检查、逻辑推理与谬误检测、知识图谱中的多跳推理、多智能体推理与协同
- 推理质量属性：忠实性、连贯性、有据性、路径效率、置信度校准
- 基础设施与采样：OpenTelemetry SDK、OpenTelemetry Collector、追踪采样、跨智能体追踪关联、历史追踪分析、自动告警
- 系统特征：非确定性推理

**关键问题**：
1. 追踪分析如何应对智能体化 AI 系统特有的调试挑战？
2. 三个埋点层级分别是什么？分层方法为何重要？
3. 在追踪分析中，预期内错误与意外错误有什么区别？
4. 上下文窗口截断如何表现为一项调试挑战？
5. 生产调试模式部分给出的六个关键洞察是什么？
6. "可能会出什么问题"（What Can Go Wrong）中的错误类别与调试有何关系？
7. 步骤级检查与路径级检查的关键差异是什么？
8. 关于推理检查的 15 种误解是如何阻碍有效验证的？

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/1S0DJHGhIlb9iihW-X8LNNaLLgzJc-Qh9HU8CgD7mEgI/viewform?usp=sharing)

**相关章节**：
- 3.1（评估设计）
- 3.2（对比基准测试）
- 3.4（参数调优）
- 3.5（提示词优化）
- 3.7（工具审计）
- 3.8（行动准确率）

✅ [参加第 3.6 章测验](https://docs.google.com/forms/d/1F9ZMB5Bl_av1VldP0kI4LLEQ9Je1E7NOwQtA06_0FEY/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 3 部分，第 3.7 章：工具审计与验证


工具审计通过函数调用和 API 调用揭示智能体实际执行的动作，与推理检查形成互补，对工具选择、参数生成和执行顺序进行全面监控。本章建立了正式的工具契约、区分语法错误与语义错误的验证框架、恢复机制以及生产监控模式。

**每周时间分配**：阅读：3.7 小时 | 主动学习：1.6 小时
总计：5.3 小时（阅读 3.7 小时，主动学习 1.6 小时）

**核心概念**：
- 工具契约与规约：工具契约、JSON Schema、规约完备性、参数错误率、工具边界对齐、文档质量差距
- 验证类型：语法验证、语义验证、Schema 验证成功率、幻觉检测、验证层级区分
- 预验证方法：错误预防层次体系、基于 Schema 的预验证、语义预验证、一致性检查、范围验证、前置条件检查、基于熵的幻觉检测、纵深防御
- 执行与监控：执行跟踪、分布式追踪、响应 Schema 验证、语义响应分析、延迟异常检测、错误分类、语义验证
- 错误恢复：指数退避、智能重试逻辑、回退工具链、优雅降级、人工介入升级、高风险领域处理、自动化与安全性的权衡
- 幻觉检测：幻影工具检测、参数幻觉、有据性验证、置信度校准
- 文档与质量：文档根因、文档优先级、双向关系、规约清晰度影响、参数文档、工具分类体系组织、标准化一致性
- 持续改进：审计数据驱动的改进、闭环落地
- 工作流验证：数据流验证、序列正确性、状态一致性、幂等性验证、竞态条件检测、依赖关系、多智能体同步
- 案例研究：初始失败率、根因、工作流级问题、方案实现、参数有据性问题、结果

**关键问题**：
1. 第 3.7 章为什么要单独区分语法验证与语义验证？
2. 电商案例研究表明系统中已有工具验证，但订单失败率仍达到 4.2%。关键缺口是什么？
3. 如果在没有有据性检查的情况下，智能体在 15–30% 的调用中会产生参数幻觉，为什么不是所有智能体都实现基于熵的检测？
4. 本章指出约 44% 的简单查询和 48% 的复杂查询包含参数错误。这些错误真的都源于文档质量吗？
5. 文档-准确率反馈回路在实践中如何运作？请给出一个具体示例。
6. 本章强调要通过幂等性验证来防止重复扣费。但验证器如何知道哪些工具调用是幂等的？
7. 如何在实施全面的执行前验证与延迟成本之间取得平衡？
8. 如果改进文档在减少幻觉方面如此有效，为什么在文档完善的系统中智能体仍会产生参数幻觉？

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/13TyeQff6TbjzXNFHgBLmErnakQ2Mh8inRReIVjTljvo/viewform?usp=sharing)

**相关章节**：
- 3.4（参数调优）
- 3.6（追踪分析）
- 3.8（行动准确率）
- 第 3 部分的前序章节

✅ [参加第 3.7 章测验](https://docs.google.com/forms/d/1rJ2Ghg9Ehrm2jf6foqfJP7Gx7n-u6VKWgML9v8Q-ru0/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 3 部分，第 3.8 章：行动准确率


行动准确率是对离散决策、工具选择、参数和执行步骤的细粒度评估，与仅衡量最终结果的任务级指标形成互补。本章建立了区分工具选择准确率与参数准确率的框架、轨迹评估指标，以及能够揭示智能体行为中隐藏问题的生产监控模式。

**每周时间分配**：阅读：3.2 小时 | 主动学习：1.3 小时
总计：4.5 小时（阅读 3.2 小时，主动学习 1.3 小时）

**核心概念**：
- 准确率类型：工具选择准确率、工具调用准确率、参数准确率、执行路径有效性、行动轨迹质量、任务成功指标
- 评估框架：离线评估框架、在线评估框架
- 评估方式：程序化评估、LLM-as-Judge 评估
- 验证类型：格式验证、参数验证、执行验证、行动验证、参数验证流水线
- 指标与测量：精确匹配指标、顺序匹配指标、会话级指标、节点级指标、Berkeley Function Calling Leaderboard（BFCL）指标、轨迹精确率、轨迹召回率、步骤效用得分、工具执行成功率
- 真值与参考：语义差距、参考轨迹
- 监控与埋点：行动日志记录
- 常见陷阱与谬误：单一指标谬误、精确匹配陷阱、缺乏语义依据的参数验证、平均抹平诊断信息、无视上下文依赖性、测试数据覆盖缺口、缺失生产监控、错误恢复盲区

**关键问题**：
1. 行动准确率与任务成功率有何不同，为什么要同时测量两者？
2. 何时应使用精确匹配、顺序匹配还是任意顺序匹配的轨迹评估？
3. 在参数幻觉影响 15–30% 调用的情况下，智能体如何实现高参数准确率？
4. 我的离线评估在测试数据上显示 92% 的行动准确率，但生产环境的 A/B 测试却表明用户很不满意。什么可以解释这种脱节？
5. 工具选择准确率与参数准确率之间是什么关系，我该如何诊断问题出在哪一方？
6. 对于工具输出会作为后续工具参数输入的多步任务，我该如何处理？
7. 我应该优先提升行动准确率还是错误恢复能力？
8. 如何避免"精确匹配陷阱"，即有效的替代行动序列被不当扣分？

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/13c2gdPWotS71qiZfoCGWAtzI4pWiadFNdr-9NIPCIdA/viewform?usp=sharing)

**相关章节**：
- 3.1（评估流水线）
- 3.2（对比性能）
- 3.6（追踪分析）
- 3.7（工具审计）
- 3.9（推理质量）
- 3.10（效率指标）

✅ [参加第 3.8 章测验](https://docs.google.com/forms/d/1MFoKgYBtljPsJ8H6EXeoxrOUJ6jQBRDjOFDYzPR5SUY/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 3 部分，第 3.9 章：推理质量


推理质量评估考察智能体如何通过逻辑连贯性、推理链有效性、透明度和信息量来驾驭决策路径——这些维度不同于任务成功率。本章建立了通过思维链分解、形式逻辑验证和评估指标来衡量多维推理质量的框架，使生产系统能在出现严重故障之前发现推理缺陷。

**每周时间分配**：阅读：5.6 小时 | 主动学习：2.4 小时
总计：8.0 小时（阅读 5.6 小时，主动学习 2.4 小时）

**核心概念**：
- 逻辑连贯性与推理链有效性
- 思维链（CoT）提示的双重作用
- 推理内容单元（RCU）与分解
- 步骤内正确性与步骤间正确性
- 用于一致性检查的自然语言推理（NLI）模型
- 面向形式化推理的 Logic Agent 框架
- 基于双遍架构的自评估
- 基于蕴含的评估与矛盾检测
- 信息增益度量与 RECEVAL 框架
- 带明确评分标准的 LLM-as-Judge 评估
- 离线推理评估流水线
- 追踪收集与参考数据集构建
- 带编号步骤的结构化 CoT 提示
- 分层推理验证与检查点
- 采用最小值聚合的复合质量指标

**关键问题**：
- 推理质量评估为何不同于任务成功度量，这一区分为何重要？
- 思维链提示如何同时提升智能体性能与评估能力？
- 将推理链分解为推理内容单元意味着什么，为什么这是必要的？
- Logic Agent 与基于 LLM 的推理有何不同，各自适用于什么场景？
- 步骤内正确性与步骤间正确性有何区别，为什么两者都必须评估？
- 双遍自评估如何提升推理质量，其局限是什么？
- 自动化推理评估指标与人类专家评估之间存在哪些权衡？
- 为什么最小值聚合比各分项得分求平均能提供更有用的整体推理质量分数？
- 团队如何避免"任务成功幻觉"，同时验证推理质量的改进确实转化为更好的结果？
- 推理轨迹本身存在哪些具体的幻觉风险，团队除了检查最终答案之外应如何应对？

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/128t6LAQ_P0jHdbtxTa-SrcXifmo6GJUN8aBKpEuQOOE/viewform?usp=sharing)

**相关章节**：
- 第 3.1 章（基础评估框架）
- 第 3.2 章（统计比较）
- 第 3.3 章（多跳推理模式）
- 第 3.4 章（参数调优）
- 第 3.5 章（提示技巧）
- 第 3.6 章（追踪分析）
- 第 3.7 章（工具审计）
- 第 3.8 章（行动准确率）
- 第 3.10 章（效率指标）
- 第 4 部分及以后（生产部署可靠性）

✅ [参加第 3.9 章测验](https://docs.google.com/forms/d/19ygg51eTO3Qt0YyX6skQExASouTaGV9AdXgwFJJowxY/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 3 部分，第 3.10 章：效率指标


效率指标衡量智能体利用计算资源、API 调用和执行步骤的有效程度，把技术层面的优化转化为对业务至关重要的指标。本章通过系统化测量 Token 消耗、步骤削减和成本归因，论证了无需牺牲准确率也能实现显著的效率提升——这对生产的可行性至关重要。

**每周时间分配**：阅读：7.1 小时 | 主动学习：3.1 小时
总计：10.2 小时（阅读 7.1 小时，主动学习 3.1 小时）

**核心概念**：
- 非对称定价下的 Token 用量（输出比输入多 1.5–3 倍）
- 步骤数与轨迹膨胀
- API 调用频率与网络开销
- 计算成本聚合
- 执行效率比率
- 用于减少 Token 的 AgentDiet 框架
- 输入与输出 Token 的成本经济性
- 最优 Token 密度与压缩
- KV Cache 优化与提示缓存
- 内存架构（分层存储）
- 顺序 vs 并行的智能体交接
- 智能路由优先设计配合模型扩缩
- 上下文精简与优雅降级
- 总 Token 消耗（TTC）指标
- Token 效率比计算
- 单次交互成本分析
- 步骤削减指标
- 延迟组件分解
- 离线效率剖析
- 轨迹分析与基线测量
- 面向效率的提示工程
- 示例优化与工具描述最小化
- 模型选择与路由策略
- 量化与压缩技术
- 智能批处理与工作流优化

**关键问题**：
- 某客服智能体在保持准确率的同时，将每次查询的 Token 消耗从 6,800 降到 2,100（减少 69%）。按每月 200 万次查询计算，年度成本节省是多少？
- 解释为什么某金融服务公司每年处理 500 万份贷款申请、每份申请消耗 8,500 个 Token，即使准确率达到 89% 也必须优化效率。
- 幻觉与其他故障模式之间的关键区别是什么，为什么这一区别会影响效率指标和优化策略？
- 在多智能体供应链系统中，单个智能体的幻觉率低于 5%，但系统级幻觉率却达到 14.2%。请解释这一差异。
- 某法律研究 AI 助手存在 28% 的引用幻觉率。为什么在其他指标良好的情况下这仍不可接受？应实施什么样的多层缓解架构？
- 你正在优化一个幻觉率为 11.4% 的电商商品推荐系统。为什么基准测试结果无法预测生产表现？应实施什么样的架构修复？
- 你发现某个智能体上线时每次交互使用 3,000 个 Token，六个月后却漂移到 4,500 个。请列出这一效率退化的三个可能原因。
- 在路由架构中针对特定任务类型选择小型语言模型还是前沿模型时，应考虑哪些因素？

💭 [用自己的话回答这些问题](https://docs.google.com/forms/d/1Pmjy7mSxNobu5oYN2s6aKhyHM2a5EtuTCvNv393dKrc/viewform?usp=sharing)

**相关章节**：
- 第 3.9 章（推理质量维护）
- 第 3.1–3.8 章（智能体设计基础）
- 第 2 部分（评估框架）
- 第 1 部分（核心原则）
- 第 4 部分（生产部署与扩展）

✅ [参加第 3.10 章测验](https://docs.google.com/forms/d/1gpzuiNKQSbBm6u68ff3BvACHF_Am-mYpU8PW_WsPI20/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 4 部分，第 4.1 章：AI 智能体部署与扩展

本章介绍了在生产环境中部署和扩展多智能体系统所需的关键基础设施与运维实践，涵盖消息队列架构、向量数据库选型、可观测性模式、API 网关实现、面向智能体系统的 MLOps，以及 CI/CD 流水线自动化。

**每周投入**：阅读：2.24 小时 | 主动学习：0.96 小时
总时长：3.2 小时（阅读 2.24 小时，主动学习 0.96 小时）

**核心概念**：
- 消息队列（RabbitMQ、Kafka）、异步通信、以 broker 为中心与分布式日志架构、交换机路由、消费者偏移量
- 向量数据库（Pinecone、Weaviate、Milvus）、语义相似性搜索、托管服务、HNSW 索引、混合搜索、元数据过滤、冷热分层存储
- 可观测性（Prometheus、Grafana）、基于拉取的指标架构、counter/gauge/histogram 指标、LLM 专用指标、告警配置、仪表盘
- API 网关（Kong、NGINX）、集中式入口、身份认证、速率限制、负载均衡、金丝雀部署、熔断器
- 面向智能体的 MLOps、组件版本管理、行为测试、蓝绿部署、功能开关、制品登记、持续改进循环
- CI/CD 流水线、持续集成、持续交付、代码质量检查、多阶段测试、Docker 多架构构建、容器安全扫描、渐进式发布

**关键问题**：
1. 在多智能体通信中，何时应选择 RabbitMQ 而非 Kafka？以 broker 为中心的架构与分布式日志方案之间存在哪些架构取舍？
2. 为什么智能体系统需要不同于传统机器学习模型的 MLOps 实践？组件版本管理如何应对这一挑战？
3. 在向量数据库选型中，Pinecone（托管）、Weaviate（开源）与 Milvus（高性能）之间的部署取舍是什么？
4. 与仅依赖容器镜像相比，在 CI/CD 流水线中于 MLflow 里进行全面的制品登记，如何实现可复现部署与即时回滚？
5. 行为测试在 CI/CD 质量门禁中具体发挥什么作用？它与传统面向智能体系统的单元测试有何不同？
6. 与一次性全量部署相比，渐进式部署策略（金丝雀发布、蓝绿部署）如何降低生产风险？
7. 除了传统应用监控（延迟、吞吐、错误）之外，哪些智能体专用的可观测性指标对于发现行为漂移与质量劣化至关重要？
8. 与在各智能体服务之间分散认证相比，集中式的 API 网关管控如何提升安全性与策略管理能力？
9. 为什么智能体系统除了基础设施指标之外，还需要 LLM 专用指标（token 用量、单次交互成本、会话轮次数）？
10. 哪些组织与技术基础（自动化、版本管理、测试、监控、安全回滚）能让团队安全地每天多次部署智能体系统？

💭 [用你自己的话回答这些问题](https://docs.google.com/forms/d/1reobzyiijjgzJZvvaMIVJV7cJyEr2Ve2w5AaGLf7Lhk/viewform?usp=sharing)

**相关章节**：
- 第 1 部分 第 1.1 章（智能体基础——需要部署基础设施作为支撑的基础架构与推理模式）
- 第 1 部分 第 1.3 章（多智能体协同——依赖消息队列架构的交互模式）
- 第 1 部分 第 1.7 章（记忆与知识系统——为向量数据库与状态管理设计提供依据的架构）
- 第 2 部分 第 2.1 章（框架全景——决定服务边界与编排需求的能力）
- 第 2 部分 第 2.6 章（工具集成——在智能体 MLOps 中需要做版本管理的配置与模式定义）
- 第 3 部分 第 3.1 章（评估框架——正在成为 CI/CD 流水线质量门禁的方法论）
- 第 3 部分 第 3.6 章（链路追踪分析与可观测性——监控基础设施的基础模式）
- 第 4 部分 第 4.2 章（部署与扩缩容——4.1 中引入的基础设施的详细实现模式）
- 第 4 部分 第 4.3 章（容器编排——依赖 4.1 基础的 Kubernetes 部署）
- 第 4 部分 第 4.4 章（性能剖析——基于 4.1 可观测性指标的优化）

---

[↑ 返回目录](#table-of-contents)

## 第 4 部分，第 4.2 章：部署与扩缩容


第 4.2 章详细讲解了智能体系统的部署模式，考察微服务与 serverless 方案、消息队列架构选型、向量数据库部署选项、可观测性落地实现以及 CI/CD 流水线构建。本章为在扩展系统规模的同时通过渐进式部署与全面监控保持可靠性，提供了可直接用于生产环境的指导。

**每周投入**：阅读：4.1 小时 | 主动学习：1.7 小时
总时长：5.8 小时（阅读 4.1 小时，主动学习 1.7 小时）

**核心概念**：
- 支持独立扩缩容的微服务架构
- 服务拆分（协调器、Worker、记忆服务）
- API 通信与异步消息队列
- 服务发现机制
- 网络隔离与安全区域
- serverless 部署与事件驱动计算
- 水平扩缩容与负载均衡
- 容错与优雅降级
- 使用 Terraform/CloudFormation 的基础设施即代码（IaC）
- RabbitMQ 与 Apache Kafka 对比
- 消费者组与基于主题的路由
- 确认语义（至多一次、至少一次、恰好一次）
- 分区策略与并行处理
- 语义搜索与向量嵌入
- 基于 HNSW 索引的快速相似性搜索
- 元数据过滤与混合搜索能力
- RAG 集成模式
- Pinecone 托管服务的取舍
- Weaviate 开源部署的灵活性
- Milvus 的高性能特性
- Prometheus 时间序列指标
- Grafana 可视化与仪表盘设计
- LLM 专用监控（token 用量、成本、延迟）
- 告警规则与阈值配置
- 具备插件生态的 Kong 网关
- NGINX 反向代理性能优化
- 速率限制与流量管理
- 请求转换与协议转换
- 面向智能体系统的 MLOps
- 行为测试方法论
- 通过 LLM-as-Judge 进行质量评估
- 模型注册表与制品管理
- 智能体系统版本管理（模型、提示词、工具、记忆）
- 蓝绿与金丝雀部署策略
- CI/CD 流水线阶段（代码质量 → 测试 → 部署）
- 安全扫描与漏洞检测
- 配合自动化监控的渐进式发布

**关键问题**：
- 对于智能体系统，团队何时应选择微服务部署而非 serverless 部署？两者之间的取舍是什么？
- 如何判断对多智能体系统而言，RabbitMQ 还是 Kafka 才是合适的消息队列架构？
- 像 Pinecone 这样的托管向量数据库方案与 Weaviate 这类开源方案之间的关键差异是什么？
- 团队应如何组织 CI/CD 流水线，才能在生产部署前验证智能体系统质量？
- 应监控哪些指标，以验证新部署的智能体系统版本维持了生产质量？
- 面向智能体 AI 系统的 MLOps 版本管理与传统 ML 模型版本管理有何不同？这一差异为何重要？
- Kong 与 NGINX API 网关之间是什么关系？团队应如何在两者之间做选择？
- 为什么行为测试对智能体 AI 系统至关重要？它与传统 ML 测试方法有何不同？
- 容器化以及 Kubernetes 这类编排平台如何支撑本章讨论的部署模式？

💭 [用你自己的话回答这些问题](https://docs.google.com/forms/d/12qABTv3UPfMa7lEVmrQ7JiS31biI5DwgMoQxY5aPdh8/viewform?usp=sharing)

**相关章节**：
- 第 4.1 章（基础设施基础）
- 第 3.1–3.8 章（智能体设计模式）
- 第 2 部分（框架实现）
- 第 3 部分（评估框架）
- 第 4.3 章（容器编排）
- 第 4.4 章（性能剖析）
- 第 4.5 章（分布式推理）
- 第 4.6 章（工作流扩缩容）
- 第 4.7 章（生产可靠性）

✅ [完成第 4.2 章测验](https://docs.google.com/forms/d/15AZa-h1gx97fnvqPz-MfpUVuPoMxIq7YlA9IlHHNAKg/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 4 部分，第 4.3 章：容器编排与边缘部署


第 4.3 章涵盖面向生产环境多智能体部署的 Kubernetes 编排，以及边缘模型优化策略。本章说明了 Kubernetes 如何自动化容器化智能体的部署、扩缩容与自愈，同时介绍使资源受限设备能够高效进行边缘部署的模型优化技术（量化、剪枝、蒸馏）。

**每周投入**：阅读：1.5 小时 | 主动学习：0.6 小时
总时长：2.1 小时（阅读 1.5 小时，主动学习 0.6 小时）

**核心概念**：
- Kubernetes 企业级编排框架
- 带副本数的 Deployment 资源
- 滚动更新策略（同时更新 vs 渐进式更新）
- 健康探针（就绪检查与存活检查）
- Pod 安全上下文与最小权限
- 面向有状态智能体的 StatefulSet
- 水平 Pod 自动扩缩容器（HPA）
- 基于 CPU 与内存的扩缩容
- 自定义指标（队列深度、请求延迟）
- 模型感知路由与 KV 缓存利用率
- 面向有状态工作负载的会话亲和性
- 服务网格（Istio、Linkerd、Consul）
- 配合渐进式流量切换的金丝雀部署
- 熔断器与故障检测
- 用于存储的持久卷声明（PersistentVolumeClaim）
- 资源限制与资源请求
- 网络策略与零信任通信
- 量化技术（PTQ 与 QAT）
- 训练后量化（PTQ）
- 量化感知训练（QAT）
- 通过结构化剪枝节省硬件资源
- 非结构化剪枝与稀疏内核
- 知识蒸馏（教师—学生模型）
- 神经架构搜索（NAS）
- 用于边缘优化的 TensorRT 框架
- Edge Impulse 平台
- NVIDIA Jetson 系列硬件
- 张量处理单元（TPU）
- 神经处理单元（NPU）
- 边缘部署平台（AWS Greengrass、Azure IoT）
- 面向隐私保护训练的联邦学习
- 跨分布式设备的版本控制
- 差分更新与二进制差异
- 面向硬件变体的配置管理
- 模型漂移检测
- 自动化回滚流程
- 隐私优先的数据处理与加密

**关键问题**：
- 何时应使用 Kubernetes Deployment 而非 StatefulSet？
- HPA 如何确定扩缩容决策？常见的错误配置模式有哪些？
- 为什么标准的 Kubernetes 负载均衡在推理工作负载下会失效？有哪些解决方案？
- 应采用哪种量化方案？边缘部署可接受多大程度的精度损失？
- 如何对大规模边缘设备集群进行版本控制与更新管理？
- 何时应选择边缘部署而非云端部署？两者的取舍是什么？
- 生产环境 Kubernetes 部署中最主要的运行故障成因是什么？如何加以预防？
- 联邦学习在边缘部署中扮演什么角色？如何改进系统？

💭 [用你自己的话回答这些问题](https://docs.google.com/forms/d/1KsS5CGcUpwBhTKitNLw4O5jrZvCQBmVAhqMeKL4nQB8/viewform?usp=sharing)

**相关章节**：
- 第 4.1 章（基础设施组件）
- 第 4.2 章（部署模式）
- 第 3 部分（智能体架构）
- 第 2 部分（LLM 基础）
- 第 1 部分（AI/ML 基础）
- 第 4.4 章（性能剖析）
- 第 4.5 章（分布式推理）
- 第 4.6 章（工作流扩缩容）
- 第 4.7 章（生产可靠性）

✅ [完成第 4.3 章测验](https://docs.google.com/forms/d/1doSFCcw7zjA8kMTJlZh3KkZpKEMwFYk96kBI0uSPC54/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 4 部分，第 4.4 章：性能剖析与优化


性能剖析是部署与生产稳定性之间一个关键但常被忽视的环节。与传统推理工作负载相比，AI 智能体系统带来了独特挑战，因为其多阶段执行模式会在各组件之间制造分布式瓶颈，而简单的指标无法揭示这些瓶颈。以测量驱动的优化把部署从一次性事件转变为持续改进的循环，用数据取代假设，从而把精力导向高影响力的优化点。

**每周投入**：阅读：4.2 小时 | 主动学习：1.8 小时
总时长：6.0 小时（阅读 4.2 小时，主动学习 1.8 小时）

**核心概念**：
- AI 智能体性能挑战、GPU 利用率间歇性波动、KV 缓存内存压力、CPU-GPU 同步开销、内核之间 GPU 空闲、GPU 利用率低于 50%、内存拷贝峰值、内核启动间隙、周期性停顿
- 服务级目标（SLO）、NVIDIA Nsight Systems、统一的 CPU-GPU 时间线、通用平台支持、基线测量、类生产工作负载
- 迭代式优化循环、先测量后优化、单变量分析
- TensorRT-LLM 性能分析、注意力内核优化、Paged Attention、投机解码
- 模型注册表、MLflow、语义化版本管理
- GitOps 部署、Kubernetes 清单（Manifest）、ArgoCD、蓝绿部署、金丝雀部署、回滚流程、自动化回滚、对比触发条件

**关键问题**：
1. 剖析如何通过定量数据揭示真实瓶颈，从而避免基础设施过度配置？
2. 受内存限制的性能瓶颈与受同步限制的性能瓶颈有何区别？剖析时间线如何区分两者？
3. 生产部署中，何时该使用自动化回滚而非手动回滚流程？
4. 如何在 Flash Attention、Paged Attention 与 Grouped-Query Attention 优化之间做选择？
5. 为什么对生成类工作负载而言，投机解码对吞吐的提升大于对延迟的改善？
6. 应优先优化什么：推理速度、批处理效率，还是 KV 缓存管理？
7. 如何在自动化回滚的安全性与其在生产系统中的误报风险之间取得平衡？
8. 与命令式部署流程相比，GitOps 为何能提升可靠性？
9. 为模型部署选错量化精度时会出现哪些失效模式？
10. 如何在部署之前而非事故发生时就设计好回滚策略？

💭 [用你自己的话回答这些问题](https://docs.google.com/forms/d/18QFKEW5wF2zl7ihQ4xulrfXl0E5GjJ4KIHFHtfHdqQc/viewform?usp=sharing)

**相关章节**：
- 第 4.3 章：容器编排与边缘部署（前置）
- 第 4.1 章：容器化与打包（前置）
- 第 4.2 章：推理基础设施与 API 网关模式（前置）
- 第 3 部分：评估框架（为优化决策提供依据）
- 第 2 部分：智能体架构与推理（确立需要剖析的复杂性）
- 第 4.5 章：持续监控与可观测性（延伸至生产监控）
- 第 4.6 章及以后：高级生产运维

✅ [完成第 4.4 章测验](https://docs.google.com/forms/d/1wMoYTDGgWJv6qkG1-84miLLcVV-2TRGnxnUSULKKsU8/viewform?usp=sharing)

---

[↑ 返回目录](#table-of-contents)

## 第 4 部分，第 4.5 章：NVIDIA NIM 与 Triton 推理服务器


NVIDIA NIM 通过预优化的容器化微服务，压缩了从"智能体在本地跑通"到"智能体承载生产流量"之间长达数月的落差，从而在 LLM 部署上带来范式转变。NIM 打包了完整的企业级推理栈，而 Triton 则作为统一的多框架服务化平台，让团队无需深厚的优化经验也能完成生产级部署。

**每周投入**：阅读：1.47 小时 | 主动学习：0.63 小时
总时长：2.1 小时（阅读 1.47 小时，主动学习 0.63 小时）

**核心概念**：
- NVIDIA NIM（推理微服务）、推理栈优化、性能基准测试、Profile 系统、运行时调优
- 张量并行、连续批处理（In-Flight Batching）、多 GPU 部署、FP8 量化
- Kubernetes NIM Operator、健康检查端点、NGC API 身份验证、GPU 资源需求、config.json 元数据、网络配置、Profile 兼容性、企业级安全
- NVIDIA Triton 推理服务器、多框架架构
- 动态批处理、首选批大小、最大队列延迟、队列属性、vLLM 后端连续批处理、后端维度不匹配
- Ensemble 配置、顺序模型流水线、推理编排、模型仓库
- 多实例 GPU（MIG）、水平 Pod 自动扩缩容

> （原文共 319963 字符，此处截断，完整内容见来源链接）

---


### 推荐先修知识


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `docs/prerequisites/recommended.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/docs/prerequisites/recommended.md) · 语言：英文原文 · 中译版



# 推荐先修知识
{: .no_toc }

没有这些内容你也可以学成，但如果跳过它们，你会频繁查阅外部资料。
关于必须先掌握的基础，请参阅 [必备（Essential）]({{ site.baseurl }}/prerequisites/essential/)，
关于各层级的总体概览，请参阅 [先修要求（Prerequisites）]({{ site.baseurl }}/prerequisites/)。

<details open markdown="block">
  <summary>本页内容</summary>
  {: .text-delta }
1. 目录
{:toc}
</details>

## 软件架构模式

[1.5A/1.5B]({{ site.baseurl }}/curriculum/part-01/) 中关于编排模式的内容，实质上是在问：
某个多智能体问题适合哪种软件架构。先认识这些模式，会让那一章读起来像是在应用你
已经掌握的知识，而不是在死记一套新的分类体系。

### 单体 vs. 微服务，以及松耦合
你能解释单体架构与微服务架构的区别，以及"松耦合"究竟能给你带来什么吗？

- [Software Architecture in Practice](https://www.oreilly.com/library/view/software-architecture-in/9780132942799/)，Len Bass 著，第 1–3 章

### 发布-订阅消息与事件驱动设计
你能描述发布-订阅消息机制，并判断什么时候它比直接调用更合适吗？

- [System Design Primer](https://github.com/donnemartin/system-design-primer) &middot; 免费、社区维护的参考资料，涵盖发布-订阅、负载均衡与复制

### 实践中的架构权衡
对于一个由 200 个智能体协同处理仓储作业的系统，你会选择集中式还是去中心化编排，为什么？真实案例比定义更能快速磨炼这种直觉。

- 阅读一个真实的架构案例研究（Uber、Netflix 或 AWS 的工程博客），并指出它实际使用了上面的哪些模式

---

## 数据库基础

[1.4]({{ site.baseurl }}/curriculum/part-01/)（记忆系统）要求你理解持久化，而
[第 6 部分]({{ site.baseurl }}/curriculum/part-06/)（RAG 与知识集成）则专门围绕向量
数据库展开 —— [6.2A]({{ site.baseurl }}/curriculum/part-06/) 假定你已经了解 SQL、
索引和 ACID，然后才解释为什么向量数据库会放宽其中的一些保证。

### SQL 基础
你能写出一条带 `WHERE` 子句和 `JOIN` 的 `SELECT` 查询吗？

- [SQL Tutorial](https://www.w3schools.com/sql/) &middot; W3Schools，约 3–4 小时，免费

### 索引与查询性能
你理解数据库索引做了什么，以及为什么它能加快某些查询却会拖慢写入吗？

- [Designing Data-Intensive Applications](https://dataintensive.net/)，Martin Kleppmann 著，第 1–3 章

### ACID vs. 最终一致性
你能说出 ACID 的四项属性，并解释为什么一个分布式系统可能有意放弃其中之一吗？

- 同上来源；实践方式是在本地搭建 PostgreSQL，并故意运行一个违反隔离级别的事务

### SQL vs. NoSQL vs. 向量数据库
你能就各自真正优化的目标，比较关系型数据库（PostgreSQL）、文档存储（MongoDB）和向量数据库（Pinecone）吗？

- 从 RAG 的角度已在 [6.2A: Vector Database Selection]({{ site.baseurl }}/curriculum/part-06/) 中覆盖

---

## Kubernetes 基础

[第 4 部分]({{ site.baseurl }}/curriculum/part-04/)（生产部署与扩缩容）全程建立在 Kubernetes
之上，尤其是 [4.3]({{ site.baseurl }}/curriculum/part-04/)（容器编排）。如果你要部署到托管的
Kubernetes 服务（EKS、GKE、AKS），这一项就从"推荐"变成了"必备"。

### Pod、Service 与 Deployment
你能解释什么是 Pod、为什么它是最小的可部署单元，以及 Service 如何把一组 Pod 暴露给网络吗？

<details markdown="block">
<summary>视频</summary>

<div style="margin:0 0 1.5rem 0">
<iframe src="https://www.youtube-nocookie.com/embed/X48VuDVv0do" title="Kubernetes Tutorial for Beginners [FULL COURSE in 4 Hours]" loading="lazy" style="width:100%;max-width:560px;aspect-ratio:16/9;border:0" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
<div><a href="https://www.youtube.com/watch?v=X48VuDVv0do">Kubernetes Tutorial for Beginners [FULL COURSE in 4 Hours]</a> &middot; TechWorld with Nana</div>
</div>

在 [必备 &gt; Docker]({{ site.baseurl }}/prerequisites/essential/#docker-and-containerization-basics)
中的 Docker 视频之后，自然的下一步就是它 —— 同样的频道风格，正好承接容器部分的内容。

</details>

### kubectl 与资源限制
你能用 `kubectl` 查看 Pod、Service 和日志，并解释 CPU/内存的 request 与 limit 各自有何作用吗？

- 练习：把一个简单应用部署到 Minikube，扩缩其副本数，并触发一次滚动更新

---

## 自然语言处理（NLP）基础

LLM 本质上就是 NLP 模型。[第 5 部分]({{ site.baseurl }}/curriculum/part-05/) 的高级推理
模式建立在 Transformer 机制之上，而 [第 7 部分]({{ site.baseurl }}/curriculum/part-07/) 的
优化技术（量化、KV cache）直接针对 Transformer 的组件。这一层级比
[必备 &gt; LLM 基础]({{ site.baseurl }}/prerequisites/essential/#large-language-model-llm-fundamentals) 更深一层 ——
请先读那部分。

### 分词（Tokenization）
你能解释分词做了什么、为什么一个词可能变成多个 token，以及这为什么对成本和上下文窗口预算很重要吗？

<details markdown="block">
<summary>视频</summary>

<div style="margin:0 0 1.5rem 0">
<iframe src="https://www.youtube-nocookie.com/embed/zduSFxRajkE" title="Let's build the GPT Tokenizer" loading="lazy" style="width:100%;max-width:560px;aspect-ratio:16/9;border:0" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
<div><a href="https://www.youtube.com/watch?v=zduSFxRajkE">Let's build the GPT Tokenizer</a> &middot; Andrej Karpathy</div>
</div>

动手且面向代码 —— 自己把其中的机制实现出来，而不是想当然地接受。关于注意力机制和完整的
Transformer 架构，请参阅
[必备 &gt; LLM 基础]({{ site.baseurl }}/prerequisites/essential/#large-language-model-llm-fundamentals)，
这里就不再重复那些视频了。

</details>

### 为什么 Transformer 取代了 RNN
你知道是什么让 Transformer 模型区别于 —— 并且通常优于 —— 它们之前的循环网络（RNN）吗？

- [Attention Is All You Need](https://arxiv.org/abs/1706.03762) —— 至少读一下引言和架构图；这篇论文奠定了整个论证的基础

### 常见的 NLP 任务类型
你能说出并区分几种标准的 NLP 任务形态 —— 分类、生成、问答 —— 并把"智能体工具调用"归入其中吗？

- [Hugging Face NLP Course](https://huggingface.co/learn/nlp-course)，第 1–2 章，免费

---

接下来可以阅读 [加分（Beneficial）]({{ site.baseurl }}/prerequisites/beneficial/) 先修要求，返回
[必备（Essential）]({{ site.baseurl }}/prerequisites/essential/)，或者回到
[层级概览]({{ site.baseurl }}/prerequisites/)。

---


### NCP-AAI 参考资料与官方直链


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `docs/ncp-aai/references.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/docs/ncp-aai/references.md) · 语言：中文原文



# NCP-AAI 参考资料与官方直链

| 资源 | 链接 |
|---|---|
| 考试报名页 | [NVIDIA 官方报名](https://www.nvidia.cn/training/certification/#book-cn-exam) |
| 官方认证页 | [Agentic AI Professional](https://www.nvidia.cn/training/certification/agentic-ai-professional/) |
| NVIDIA NeMo | [链接](https://developer.nvidia.com/nemo) |
| NVIDIA Nemotron | [链接](https://developer.nvidia.com/nemotron) |
| NVIDIA AI Blueprint | [链接](https://developer.nvidia.com/ai-blueprint) |

> ⚠️ 版权归 NVIDIA 所有；本仓只引用直链，不收录 PDF 副本。

---


### NCP-AAI 考试介绍（来源：英伟达官方科目解读 P13）


> 来源：`junze-xu/NVIDIA-AI-Certification-Notes` · `ncp-aai/overview.md` · [原文链接](https://github.com/junze-xu/NVIDIA-AI-Certification-Notes/blob/main/ncp-aai/overview.md) · 语言：中文原文



# NCP-AAI 考试介绍（来源：英伟达官方科目解读 P13）

> 原文出处：NVIDIA 官方《科目解读》第 13 页 · 2026 年整理

## 考试定位

NVIDIA-Certified Professional: Agentic AI (NCP-AAI) 认证，用于验证设计、开发、部署和管理先进的代理式 AI 解决方案，侧重于多代理交互、分布式推理、可扩展性和道德保障。

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
- AI 专家

## 推荐培训与课程

| 序号 | 课程名称 |
|---|---|
| 1 | 构建大语言模型 RAG 智能体 |
| 2 | 评估 RAG 和语义检索系统 |
| 3 | 使用大语言模型构建代理式 AI |
| 4 | 为大语言模型添加新知识 |
| 5 | 在生产环境大规模部署 RAG 工作流 |
| 6 | 考前学习指南 » |

---



## 实操


### 支持


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `SUPPORT.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/SUPPORT.md) · 语言：英文原文 · 中译版



# 支持

本仓库是书籍 *Mastering Agentic AI Systems: Guide for the NVIDIA NCP-AAI Exam* 的配套材料（实验、幻灯片、视频、测验和示例代码）。它是一个内容仓库，而非软件包，因此这里的"支持"主要是指把关于本材料的问题解答掉，以及修复内容缺失或错误。

## 在哪里提问

* **发现错误、无法运行的实验、过时的参考，或内容缺失？**
  请提交一个 [GitHub Issue](../../issues)。这是主要渠道，也是获得响应最快的方式。
* **关于如何使用本材料的一般性问题？** 目前也请使用
  [GitHub Issues](../../issues)。本仓库当前尚未启用 GitHub Discussions；如果将来有需求，可能会启用，但不要假定它今天就可用。
* **其他任何事情**（包括你不想公开提出的问题，或与某个具体 issue/PR 无关的事项）可以发送给 GSA
  项目联系人 [[邮箱已隐去]](mailto:[邮箱已隐去])。
* **安全方面的问题** 应按 [SECURITY.md](SECURITY.md) 中的流程处理，而不是提交普通 issue。

## 响应时间

我们的目标是在 **3 个工作日** 内对新 issue 和 pull request 给出首次响应。这只是首次响应，并不一定意味着问题
已经解决——某些内容修复耗时更长，尤其是较大的实验或
幻灯片。

## 提问之前

* 搜索已有的 [issues](../../issues)，看看你的问题是否已经被
  提出过。
* 如果你是在报告某个具体实验、幻灯片、视频或代码
  示例的问题，请附上文件路径，以便快速定位。

如何自行提交修改，请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

---


### 实验


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `docs/labs.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/docs/labs.md) · 语言：英文原文 · 中译版



# 实验
{: .no_toc }

动手练习是本项目最大的短板。每一章都需要一个真正的实验；目前只有一章有，而且它还是
一份草稿。

<details open markdown="block">
  <summary>本页目录</summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

## 目前已有哪些内容

| 内容 | 状态 |
|---|---|
| [实验 8.2B — 为不稳定的下游工具构建熔断器]({{ site.repo_blob }}/labs/8.2B_circuit_breaker/lab.md) | **草稿。** 按实验模板编写；维护者已运行过参考解答且测试通过；但尚未有外部学习者试做。大约 60–90 分钟；仅需 Python 3.10+ 标准库。 |
| [`labs/archive/`]({{ site.repo_tree }}/labs/archive) | 17 个旧版示例文件：从各章摘录的说明性文字，内嵌代码。它们**不是**实验，也不计入覆盖范围。 |
| [`LAB_TEMPLATE.md`]({{ site.repo_blob }}/labs/LAB_TEMPLATE.md) | 每个新实验所依据的标准模板。 |

参考实验的文件位于 [`labs/8.2B_circuit_breaker/`]({{ site.repo_tree }}/labs/8.2B_circuit_breaker)：`lab.md`、`starter.py`、
`solution.py`、`test_lab.py` 和 `requirements.txt`。用 `python3 test_lab.py` 运行自检。

## 一个完成的实验包含什么

按照 [`LAB_TEMPLATE.md`]({{ site.repo_blob }}/labs/LAB_TEMPLATE.md)，每个实验包含：**Objectives（学习目标）**、一个 **Scenario（场景）**、**Setup（环境准备）**、
一份有引导的 **We Do（一起做）** 演示、一个需要独立完成的 **You Do（自己动手）** 任务，以及 **Hint Ladder（提示阶梯）**（由浅入深、循序渐进、强力提示，最后给出
参考答案）、一个可运行的 **Self-Check（自检）**、**Key Points（关键要点）**，还有一张收尾的对照表，把每个学习目标追溯到讲授它的练习
和验证它的检查项。

## 质量评分标准

评审者对以下每一项都做是/否判定：

1. **引用具体的知识点**，要注明章节 ID 和具体说法，而不只是章节编号。
2. **学习者动手做**：*You Do* 部分要求编写或补全真实的代码。
3. **可独立完成**：不打开书中章节也能做完。
4. **起始代码按原样可运行**：它可能会通不过自己的测试，但导入或初始化时不得崩溃。
5. **参考解答可运行、依赖版本已锁定**：`solution.py` 能通过 `test_lab.py`；`requirements.txt` 固定了版本号。
6. **学习者可自行验证成败**：由测试套件或脚本给出通过/失败，而不是靠讲评式问答。
7. **场景真实**：是真实从业者可能遇到的处境，而不是玩具示例。

## 成熟度阶梯

| 阶段 | 含义 |
|---|---|
| `example` | 内嵌代码的说明性文字，未按模板编写。17 个归档文件处于这一级。 |
| `draft` | 已按模板编写，经检查符合评分标准；但尚未有其他人完整做过。 |
| `piloted` | 至少有作者之外的一个人完成过，并记录了遇到的问题。 |
| `stable` | 已试点、根据反馈修订，并重新验证了参考解答。 |

各章状态汇总表见 [`labs/README.md`]({{ site.repo_blob }}/labs/README.md)。

## 旧版示例文件

- [`Part_01_Chapter_1.1_Labs.md`]({{ site.repo_blob }}/labs/archive/Part_01_Chapter_1.1_Labs.md)
- [`Part_01_Chapter_1.6_Labs.md`]({{ site.repo_blob }}/labs/archive/Part_01_Chapter_1.6_Labs.md)
- [`Part_01_Chapter_1.7_Labs.md`]({{ site.repo_blob }}/labs/archive/Part_01_Chapter_1.7_Labs.md)
- [`Part_01_Chapter_1.8_Lab.md`]({{ site.repo_blob }}/labs/archive/Part_01_Chapter_1.8_Lab.md)
- [`Part_02_Chapter_2.10_Lab.md`]({{ site.repo_blob }}/labs/archive/Part_02_Chapter_2.10_Lab.md)
- [`Part_02_Chapter_2.7_Labs.md`]({{ site.repo_blob }}/labs/archive/Part_02_Chapter_2.7_Labs.md)
- [`Part_04_Chapter_4.1_Labs1.md`]({{ site.repo_blob }}/labs/archive/Part_04_Chapter_4.1_Labs1.md)
- [`Part_04_Chapter_4.1_Labs2.md`]({{ site.repo_blob }}/labs/archive/Part_04_Chapter_4.1_Labs2.md)
- [`Part_04_Chapter_4.6.md`]({{ site.repo_blob }}/labs/archive/Part_04_Chapter_4.6.md)
- [`Part_06_Chapter_6.3C_ETL_Practice.md`]({{ site.repo_blob }}/labs/archive/Part_06_Chapter_6.3C_ETL_Practice.md)
- [`Part_06_Chapter_6.4B_Data_Quality_Practice.md`]({{ site.repo_blob }}/labs/archive/Part_06_Chapter_6.4B_Data_Quality_Practice.md)
- [`Part_06_Chapter_6.5B_Production_RAG_Practice.md`]({{ site.repo_blob }}/labs/archive/Part_06_Chapter_6.5B_Production_RAG_Practice.md)
- [`Part_06_Chapter_6.6A_Reranking_Implementation.md`]({{ site.repo_blob }}/labs/archive/Part_06_Chapter_6.6A_Reranking_Implementation.md)
- [`Part_06_Chapter_6.6C_Advanced_Retrieval_Practice.md`]({{ site.repo_blob }}/labs/archive/Part_06_Chapter_6.6C_Advanced_Retrieval_Practice.md)
- [`Part_07_Chapter_7.2A_Local_Development.md`]({{ site.repo_blob }}/labs/archive/Part_07_Chapter_7.2A_Local_Development.md)
- [`Part_07_Chapter_7.7_Labs_Practice.md`]({{ site.repo_blob }}/labs/archive/Part_07_Chapter_7.7_Labs_Practice.md)
- [`Part_08_Chapter_8.2B_Labs.md`]({{ site.repo_blob }}/labs/archive/Part_08_Chapter_8.2B_Labs.md)

## 编写一个实验

实验是[征集协作者]({{ site.baseurl }}/contributing/)中的优先事项：挑选一章，设计一个真实的
场景，然后按模板把它写出来。一个自包含的算法类实验大约需要 4–12 小时，需要外部服务的实验则需要 12–20
小时，建议拆分成一系列小型 pull request 提交。

---


### [实验标题]


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/LAB_TEMPLATE.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/LAB_TEMPLATE.md) · 语言：英文原文 · 中译版



---

title: "[简短、具体的实验标题 —— 写出学习者要构建的产物，而不是主题。例如 'Build a Circuit Breaker for a Flaky Downstream API'，而不是 'Resilience Patterns']"
chapter: "[来自 cert_mapping/README.md 的规范章节 ID，例如 8.2B —— 必须是一个 ID，而不是一个区间。如果材料确实横跨多个章节，请选择本实验主要强化的那一章，其余的在 Prerequisites 中说明。]"
knowledge_items:
  
  - "[chapter-id: 具体的知识点表述，例如 '8.2B: circuit breaker state machine (CLOSED/OPEN/HALF_OPEN) and failure-threshold tuning']"
  - "[chapter-id: 当本实验覆盖不止一个知识点时的第二个知识点]"
prerequisites:
  - "[学习者应当已经完成的先前实验或章节；如果这是第一个实验则填 'None']"
  - "[所需的工具/账号/本地环境准备，例如 'Docker Desktop running locally'、'Python 3.11+']"
learning_objectives:
  
  - "[动词 + 具体结果，例如 'Implement a state machine that trips from CLOSED to OPEN after N consecutive failures']"
  - "[...]"
estimated_lab_time: "[具备先修条件的学习者所需的实际耗时，例如 '60-90 minutes'。这是学习者耗时，而不是你编写该实验所花费的精力。]"
frameworks:
  
  - "[library==X.Y.Z]"
maturity: "[example | draft | piloted | stable —— 参见 labs/README.md 中的成熟度阶梯。新实验最早也只能从 'draft' 起步，且需满足评分标准。]"
related_reference_lab: "labs/8.2B_circuit_breaker/lab.md"  
---

# [实验标题]

## 目标

完成本实验后，你将能够：
- [用面向学习者的语言重述 learning_objectives]

## 场景

[2-4 句话：学习者扮演什么角色、他们在做什么系统、哪里出了问题或需要构建什么、如果做错了会怎样。]

## 环境准备

```bash
[commands to clone/cd into the lab dir, create a venv, install pinned deps]
pip install -r requirements.txt
```

## 我们来做（引导式）

[引导步骤，每一步附有简短的"为什么采用这种做法"说明，以及学习者要运行的命令或代码参考。
请按函数/类名引用 starter.py 中的相关部分，而不是在此粘贴大段代码。]

**检查点：**[学习者可以运行或观察到的具体事项，用来确认引导部分已经奏效，例如 "running `pytest
test_lab.py::test_guided_example` passes"。]

## 你来做（独立完成）

### 任务

[精确的任务说明：学习者必须在 starter.py 中实现哪个函数/类/行为，以及它预期的输入/输出/边界情况。]

### 提示阶梯

**提示 1（温和 —— 引导你提出正确的问题）：**
[指出需要思考的概念或设计决策，但不要点明具体技法。]

**提示 2（适度 —— 收窄思路）：**
[点明要使用的模式/算法/API，但仍然不给出代码。]

**提示 3（强烈 —— 接近实现的指导）：**
[伪代码级别的细节、需要处理的关键边界情况，或部分代码骨架。学习者应当能从此处完成剩余工作。]

**参考答案：**
[指向 solution.py —— 不要在此 markdown 文件中内联完整答案。例如 "See solution.py for a complete reference implementation."]

## 自检

运行：
```bash
python3 test_lab.py
```

当你满足以下条件即视为成功：
- [ ] [具体、可观察的通过条件 #1，例如 "all tests in
      test_lab.py pass"]
- [ ] [具体、可观察的通过条件 #2，若自动化测试没有覆盖所有值得检查的点，例如 "manually triggering 5
      consecutive failures causes the breaker to log a state transition
      to OPEN"]

## 要点

- [把学习目标 1 重述为一个事实的要点]
- [把学习目标 2 重述为一个事实的要点]
- [...]

## 引用关系：目标 → 实践 → 检查

| 目标 | 章节知识点 | 练习位置 | 验证方式 |
|---|---|---|---|
| [目标 1，简要形式] | [对应的 knowledge_items 条目] | [We Do 步骤 / You Do 任务] | [Self-Check 条目] |
| [目标 2，简要形式] | [对应的 knowledge_items 条目] | [We Do 步骤 / You Do 任务] | [Self-Check 条目] |

---

---


### 实验 3.2：重复试验稳定性检查


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/3.2_repeated_trial_reliability/lab.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/3.2_repeated_trial_reliability/lab.md) · 语言：英文原文 · 中译版



# 实验 3.2：重复试验稳定性检查

## 目标

完成本实验后，你将能够：

1. 衡量当你重新运行完全相同的评测时，智能体的结果（以及单独来看，LLM 评判者的裁定）
   发生变化的频率。
2. 根据重复试验计算 pass^k，并解释为什么它低于单次运行的成功率。
3. 为"v2 减去 v1"构建配对自助法（bootstrap）置信区间，重采样的是条目而不是单次运行。
4. 算出每个条目需要多少次试验，裁定才会稳定下来。

## 场景

某公共福利热线使用一个助手，根据项目公开的规则告诉来电者是否符合某个项目的申请条件。
团队已经构建了 v2，并想知道它是否应该替换 v1。他们的离线测试集包含 200 个资格问题，
每个问题都有可核对的答案。每个问题运行一次，另外还有一个 LLM 评判者会就语气和完整性
对对话记录评分。

有人重新运行了完全相同的测试集，而部署门禁给出了不同的答案。这就是本实验要解决的
问题。在这里一旦答错，就会把本应享有福利的来电者打发走，因此团队需要的是在评测被重复
执行时依然站得住脚的结论，而不是取决于当天是哪一天跑出来的结果。

团队把全部内容重跑了 15 次。你手上有这些日志。它们是模拟生成的
（见 `trial_data.py`），这样每个人得到的数字都相同。

## 环境准备

除了 Python 本身之外无需安装任何东西。本实验没有第三方依赖
（见 `requirements.txt`）。

```bash
cd labs/3.2_repeated_trial_reliability
python3 --version    # 3.10 or newer
python3 starter.py   # prints the stability report; unfinished parts say TODO
python3 test_lab.py  # run the self-check now, before changing anything
```

## 我们来做：一次运行隐藏了什么

先打开 `trial_data.py`，快速浏览一下 `generate()`。它返回的每个列表都是
按 `[条目][试验]` 索引的：

- `data.v1` 和 `data.v2`：该版本在重跑第 `trial` 次时是否答对了第 `item` 个问题？
- `data.judge_regrades`：LLM 评判者在对*同一个* v2 对话记录再次评分时给出的通过/不通过
  裁定。输入每次都完全相同，因此任何变化都来自评判者本身。

现在打开 `starter.py`，读一读顶部提供的四个函数。

**步骤 1：`single_run_winner`。** 这就是团队原来的门禁：把测试集跑一次，比较两个成功率
（`single_run_success_rate`），发布更高的那个。运行 `python3 starter.py`，看看报告中
"One-run deploy gate" 那几行。把这个门禁重跑 15 次，结果是 v2 赢 12 次、v1 赢 3 次。
五次之中就有一次，完全相同的评测会反转部署决策。

**步骤 2：`flip_rate`。** 为什么会这样？看看 `flip_rate` 是怎么计算的。对于一个在 `n` 次试验中
通过了 `c` 次的条目，它统计的是试验"配对"中意见不一致的比例：`2c(n - c) / (n(n - 1))`。
这给出了同一条目两次重跑结果不一致的概率。我们采用配对而不是"是否有任何一次试验不一致"，
是因为后一种写法会随着试验记录的增多一路攀升到 100%，即使智能体本身毫无变化。

报告显示，对完全相同的输入，智能体结果两次重跑不一致的概率约为 18%，
评判者裁定两次重跑不一致的概率约为 12%。单次运行的比较会把这些噪声全部加到
两个版本上，而 v1 与 v2 之间真正的差距只有大约 2 个百分点。

**步骤 3：`per_item_rate`。** 下面每个 TODO 都从按条目的比率入手：
即某个条目的试验中通过的比例。先在*条目内部*对试验取平均，再去比较条目之间的差异，
这正是让分析保持配对的关键。

**检查点：** `python3 test_lab.py` 显示四个 `TestGuidedFunctions` 测试通过，
另外 12 个报告为 `ERROR` 且带有 `NotImplementedError`。这些错误就是你的待办清单。

## 你来做：三个函数

### 任务

实现 `starter.py` 中的三个 `TODO`。保持名称和签名不变：
`test_lab.py` 会直接调用它们。

- **TODO 1，`pass_hat_k(runs, k)`。** 估计 pass^k，即一个条目的 k 次独立试验
  *全部*通过的概率，再在条目之间取平均。使用来自 tau-bench 的无偏估计量：
  对于在 `n` 次试验中通过 `c` 次的条目，使用 `C(c, k) / C(n, k)`。若 `k < 1` 或 `k > n`，
  抛出 `ValueError`。
- **TODO 2，`paired_bootstrap_ci(v1_runs, v2_runs, n_boot, alpha, seed)`。**
  返回 (v2 比率 − v1 比率) 均值的百分位自助法区间。
  有放回地重采样*条目*，并让每个条目的两个比率始终绑定在一起。
  使用 `random.Random(seed)` 以保证结果可复现。若两个版本覆盖的条目数不同，
  抛出 `ValueError`。
- **TODO 3，`trials_needed(runs, target)`。** 返回最小的奇数 k，使得至少有 `target`
  比例的条目，其前 k 次试验的多数裁定与全部已记录试验的多数裁定一致。若记录的试验次数
  为偶数，抛出 `ValueError`。

### 提示阶梯

**提示 1（温和）：** 每个 TODO 都是对条目的循环。先确定单个条目贡献什么
（一个比例、一个差值、一个是否一致的布尔值），然后再取平均。

**提示 2（适度）：**
- TODO 1：计数交给 `math.comb`，而当 `c < k` 时 `math.comb(c, k)` 为 0，
  这正是我们想要的行为。
- TODO 2：先构建一个按条目的差值列表，然后重采样*那个列表*。
  差值本身已经是配对的。
- TODO 3：`majority()` 已经提供。在对 k 的循环之外，先把参考裁定算好。

**提示 3（强烈）：**
- TODO 1：`sum(math.comb(sum(t), k) / math.comb(len(t), k) for t in runs) / len(runs)`，
  再加上范围检查。
- TODO 2：`rng.randrange(n)` 抽取一个条目索引。一次自助法均值是
  `sum(diffs[rng.randrange(n)] for _ in range(n)) / n`。生成 `n_boot` 个这样的值，
  排序后读取下标 `floor(alpha / 2 * n_boot)` 和 `ceil((1 - alpha / 2) * n_boot) - 1`
  处的值。
- TODO 3：`for k in range(1, n + 1, 2):` 统计满足
  `majority(trials[:k]) == reference` 的条目数，一旦该比例达到 `target` 就立即返回 k。

**参考答案：** 完整的参考实现见 `solution.py`。请先尝试让自己的版本通过。

## 自检

运行：

```bash
python3 test_lab.py
```

当你满足以下条件即视为成功：

- [ ] 全部 16 个测试输出 `ok`，且未对 `test_lab.py` 做任何改动。
- [ ] `python3 starter.py` 打印出完整报告且没有任何 `TODO` 行，其中包括
      `pass^1 0.783   pass^5 0.555   pass^15 0.380`、一个不包含零的 v2 减 v1 区间，
      以及 `agent v2 5` 次试验即达到 95% 的稳定裁定。

失败的测试以其对应的 TODO 命名：`test_todo1_*` 检查 TODO 1，
`test_todo2_*` 检查 TODO 2，`test_todo3_*` 检查 TODO 3。

## 独立挑战（可选，不提供参考答案）

1. **更严格的参照。** `trials_needed` 把前 k 次试验与全部 15 次试验的多数结果作比较，
   而后者包含了同样的这 k 次试验。把试验拆分开，让参照只来自估计过程从未见过的试验，
   然后看看智能体和评判者的答案会发生多大变化。
2. **你自己的日志。** 在设置完全相同的条件下，对 20 到 50 个案例各运行五次真实的
   智能体或 LLM 评判者。把结果保存为 `[条目][试验]` 列表，并在其上运行你的三个函数。
   你测出的翻转率更接近智能体的 18%，还是评判者的 12%？

## 要点

- 重跑一次完全相同的评测，可能同时改变智能体的结果和 LLM 评判者的裁定，
  因此单次运行只是一个样本，而不是一次测量。
- pass^k 问的是某个条目是否*每一次*都通过。随着 k 增大它会迅速下降，
  而这种下降正是单一成功率所掩盖的可靠性差距。
- 比较两个版本应当是配对的：先在每个条目内部对试验取平均，再对条目重采样。
  这里，单次运行无法排除"没有差异"，而每条目 15 次试验可以。
- 你需要多少次试验取决于目标值。五次试验可以稳定 95% 的智能体裁定，
  但要达到 99% 需要九次。评判者要达到 99% 需要全部 15 次，
  因为它有些案例接近抛硬币。

## 引用关系：目标 → 实践 → 检查

| 目标 | 章节知识点 | 练习位置 | 验证方式 |
|---|---|---|---|
| 衡量智能体结果与评判者裁定在完全相同的重跑中变化的频率 | 3.2: non-determinism effects across identical re-runs | We Do，步骤 1 和 2 | `test_lab.py::TestGuidedFunctions`（`test_agent_and_judge_both_flip_on_identical_reruns`、`test_one_run_gate_disagrees_with_itself`） |
| 计算 pass^k 并解释它为何低于单次运行的成功率 | 3.2: tau-bench pass^k reliability versus single-run task success rate | You Do，TODO 1 | `test_lab.py::TestTodo1PassHatK`（`test_todo1_known_values`、`test_todo1_pass_hat_k_falls_as_k_grows`） |
| 构建 v2 减 v1 的配对自助法区间，重采样条目 | 3.2: paired evaluation of two agent versions with a confidence interval on the difference | You Do，TODO 2 | `test_lab.py::TestTodo2PairedBootstrap`（`test_todo2_constant_shift_is_recovered_exactly`、`test_todo2_one_run_is_inconclusive_but_fifteen_trials_are_not`） |
| 确定稳定裁定所需的每条目试验次数 | 3.2: non-determinism effects across identical re-runs | You Do，TODO 3 | `test_lab.py::TestTodo3TrialsNeeded`（`test_todo3_small_example_needs_three_trials`、`test_todo3_simulated_answers`） |

## 延伸阅读

- Yao, Shinn, Razavi 与 Narasimhan，"tau-bench: A Benchmark for Tool-Agent-User
  Interaction in Real-World Domains"，arXiv:2406.12045。pass^k 的来源。
- Miller，"Adding Error Bars to Evals: A Statistical Approach to Language Model
  Evaluations"，arXiv:2411.00640。配对差值、聚类标准误与答案重采样。
- Atil 等，"Non-Determinism of 'Deterministic' LLM Settings"，
  arXiv:2408.04667。固定种子、temperature 为 0 时的运行间波动。
- Yagubyan，"How Consistent Are LLM Agents? Measuring Behavioral Reproducibility
  in Multi-Step Tool-Calling Pipelines"，arXiv:2605.28840。
- Yagubyan，"The Coin Flip Judge? Reliability and Bias in LLM-as-a-Judge
  Evaluation"，arXiv:2606.13685。

---


### 实验 8.2B —— 面向智能体工具调用的熔断器


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/8.2B_circuit_breaker/lab.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/8.2B_circuit_breaker/lab.md) · 语言：英文原文 · 中译版



# 实验 8.2B —— 面向智能体工具调用的熔断器

## 目标

完成本实验后，你将能够：

1. 解释为什么在一个失败的工具调用外面套一层朴素的重试循环，会让智能体的可靠性问题
   变得更糟而不是更好。
2. 从零实现三态熔断器模式（CLOSED → OPEN → HALF_OPEN）。
3. 推演 `failure_threshold`/`window_size`（熔断器有多敏感）与 `recovery_timeout`
   （它保持谨慎多久）之间的权衡。
4. 用一个小型、确定性的测试套件来验证状态转移逻辑，而不是靠肉眼观察行为。

## 场景

TicketFlow 是一个客服智能体，它在处理退款请求时会调用 `verify_payment` 工具。在一次
例行部署中，支付验证服务开始间歇性失败 —— 不是宕机，只是又慢又不稳。TicketFlow 现有的
代码会把每次失败的调用最多重试 3 次。

在负载之下，这套重试逻辑会把局部故障放大成全面故障：TicketFlow 的 1,000 个并发会话中
每一个都可能对一个已经岌岌可危的服务额外发起最多 3 个请求，于是每个用户的
响应时间从 200ms 攀升到数秒 —— 包括那些本可以一次就成功的调用。这正是现有的
`Part_08_Chapter_8.2B_Labs.md` 示例文件所描述的场景；本实验要你从零构建这个修复方案，
而不是读一读就算了。

**熔断器（circuit breaker）** 包裹住这个有风险的调用，一旦失败次数越过阈值就停止发起调用，
而不是继续轰击它 —— 这正是你将在此实现的机制。

## 环境准备

除了 Python 本身之外无需安装任何东西 —— 本实验没有任何第三方依赖
（见 `requirements.txt`）。

```bash
cd labs/8.2B_circuit_breaker
python3 --version   # confirm 3.10 or newer
python3 test_lab.py # run the self-check now, before changing anything
```

## 我们来做 —— CLOSED 状态

打开 `starter.py`。`CircuitBreaker` 类是一个 `dataclass`，包含三个状态
（`CircuitState.CLOSED`、`OPEN`、`HALF_OPEN`），以及一个保存最近 `window_size` 次调用
结果的滚动窗口。

CLOSED 状态的路径已经为你实现好了 —— 在写任何代码之前，先读一读 `_call_closed`、
`_record_success`、`_record_failure`、`_should_trip` 和 `_trip`。跟着走一遍：

- `_call_closed` 运行 `fn()`。成功时记录一次成功；抛出异常时记录一次失败并重新抛出
  （调用方仍然会看到真实的错误）。
- `_record_failure` 把结果追加到 `_results`，把窗口裁剪为最后 `window_size` 条记录，
  然后检查 `_should_trip`。
- `_should_trip` 只在窗口已满（已发生 `window_size` 次调用）之后才评估，
  若该窗口内的失败率不低于 `failure_threshold` 就跳闸。
- `_trip` 把 `_state` 翻转为 `OPEN` 并记录 `_opened_at` —— 这个时间戳正是 OPEN 状态恢复
  逻辑要比对的东西，而你马上就要实现它了。

你在环境准备阶段已经跑过一次自检。在那次运行中，`TestClosedState` 的两个测试通过，
其余测试因 `NotImplementedError` 失败 —— 这是预期之中的。那些失败就是本实验余下部分的
待办清单。

## 你来做 —— OPEN 与 HALF_OPEN

实现 `starter.py` 中 `call()` 和 `_call_half_open()` 方法里的三个 `TODO`。不要改动任何
方法签名 —— `test_lab.py` 会直接调用它们。

**TODO 1（OPEN 状态）：** 当熔断器处于 OPEN 时，调用必须被拒绝，
且*不*调用被包裹的函数 —— 这正是熔断器的全部意义所在，好让已经岌岌可危的下游服务
不再被反复冲击。但如果已经过去足够长的时间（自 `self._opened_at` 起经过
`self.recovery_timeout` 秒），熔断器应当给下游服务一次试探性调用，而不是永远关着门。

**TODO 2（HALF_OPEN 分发）：** 在 `HALF_OPEN` 下，同一时刻只允许通过一次试探调用。
如果已有一轮试探正在进行（`_half_open_trial_in_flight` 为 `True`），第二个并发调用方
必须被拒绝，而不是排队等待或照常执行。

**TODO 3（试探调用本身，`_call_half_open`）：** 执行这次试探。成功时，熔断器应当
完全重置 —— 回到 `CLOSED`，并清空失败历史，这样一章内容的旧失败就不会残留下来
立刻再次触发跳闸。失败时，熔断器应当重新打开（并重启恢复计时），而不是卡在
`HALF_OPEN` 里出不来。

### 提示

**提示 1（温和）：** 看看 `_trip()` —— 它是一个两行的模式
（`self._state = ...`、`self._opened_at = ...`），你会在不止一处重用它。

**提示 2（适度）：** 对于 TODO 1，先计算
`elapsed = time.monotonic() - self._opened_at`，把它与
`self.recovery_timeout` 比较。如果恢复时间还没到，就抛出
`CircuitBreakerOpenError`，并在消息中写明还剩多少秒 —— 这个数字对正在调试线上故障的人
确实很有用。

**提示 3（强烈）：** `_call_half_open` 需要 `try`/`except`/`else`/`finally` 的结构：
在调用之前设置进行中标志，无论发生什么都在 `finally` 中清除它，把重置为 CLOSED 的逻辑
放在 `else` 中（只有没有抛出异常时才会执行），把重新打开的逻辑放在 `except` 中。

**参考答案：** 如果你想核对思路，或者已经彻底卡住了，`solution.py` 里有完整实现。
请先尝试让自己的版本通过 —— 本实验的重点是构建这个状态机，而不是读一个现成的。

## 自检

```
python3 test_lab.py
```

全部 7 个测试都应输出 `ok`。当这个文件在你没有改动它的前提下通过时，你就完成了。
如果有测试失败，它的名字会告诉你该回头看哪个 TODO：`TestOpenState` 下的测试考察 TODO 1；
`test_half_open_rejects_concurrent_trial` 考察 TODO 2；`TestHalfOpenState` 下的另外两个
测试考察 TODO 3。

## 独立挑战（可选，不提供参考答案）

上面的熔断器只跟踪一个下游依赖。而 TicketFlow 实际会调用三个工具
（`verify_payment`、`check_inventory`、`send_notification`）。扩展 `CircuitBreaker`
（或者在它外面包一层），让调用方可以按工具名各持有一个熔断器实例，并为每个工具配置
各自的 `failure_threshold`/`window_size`/`recovery_timeout`，同时提供一个方法来检查
是否*有任何*工具当前处于 OPEN 状态（这对于健康检查端点很有用）。本题没有答案文件 ——
请自行判断什么算"完成"，并以上面的目标为参考。

## 要点

- 熔断器的职责是停止调用一个正在失败的依赖，而不是让调用本身成功 —— 请在调用点
  为它搭配一个兜底方案或面向用户的降级模式，这属于与本实验所实现内容不同的另一件事。
- CLOSED → OPEN 的转换关注的是某个窗口内的*失败率*，而不是任何一次单点失败 ——
  正因如此，熔断器才不会因为一次倒霉的超时而跳闸。
- HALF_OPEN 的存在是为了让恢复成为一次可控的探测，而不是所有调用方在
  `recovery_timeout` 一到就一拥而上地重试。
- 快速拒绝（在 OPEN 状态下立即抛出）正是熔断器在负载之下的全部价值所在 ——
  缓慢的拒绝与它本想避免的故障几乎没有区别。

## 引用关系：目标 → 实践 → 检查

| 目标 | 章节知识点 | 练习位置 | 验证方式 |
|---|---|---|---|
| 解释朴素重试为何会放大下游故障 | 8.2B: circuit breaker state machine (CLOSED/OPEN/HALF_OPEN) and transition conditions | 场景 | 不适用 —— 概念性内容；在 We Do 的设计解读中继续沿用 |
| 实现 OPEN 状态的快速失败拒绝以及按时间转入 HALF_OPEN | 8.2B: circuit breaker state machine (CLOSED/OPEN/HALF_OPEN) and transition conditions | You Do，TODO 1 | `test_lab.py::TestOpenState` |
| 实现 HALF_OPEN 的单试探分发、成功时重置为 CLOSED、失败时重新打开 | 8.2B: failure-threshold and sliding-window tuning for trip/reset behavior | You Do，TODO 2-3 | `test_lab.py::TestHalfOpenState` |
| 用确定性测试套件验证状态转移逻辑 | 8.2B: circuit breaker state machine (CLOSED/OPEN/HALF_OPEN) and transition conditions | 自检 | 直接运行 `python3 test_lab.py` 并阅读其通过/失败输出 |

---


### Section 1.1 Part 3: UI Integration, Practice, and Resources


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/archive/Part_01_Chapter_1.1_Labs.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/archive/Part_01_Chapter_1.1_Labs.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Start Neo4j in Docker (if not already running)


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/archive/Part_01_Chapter_1.7_Labs.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/archive/Part_01_Chapter_1.7_Labs.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Apply the deployment and HPA


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/archive/Part_01_Chapter_1.8_Lab.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/archive/Part_01_Chapter_1.8_Lab.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Section 2.11: Hands-On Lab - Multi-Framework Comparison


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/archive/Part_02_Chapter_2.10_Lab.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/archive/Part_02_Chapter_2.10_Lab.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Chapter 2, Section 2.2.6-2.2.9: Multimodal Integration - Labs and Resources


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/archive/Part_02_Chapter_2.7_Labs.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/archive/Part_02_Chapter_2.7_Labs.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Part 04 Chapter 4.1 Labs1


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/archive/Part_04_Chapter_4.1_Labs1.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/archive/Part_04_Chapter_4.1_Labs1.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Part 4, Chapter 4.6B: Bottleneck Resolution and Hands-On Profiling Lab


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/archive/Part_04_Chapter_4.6.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/archive/Part_04_Chapter_4.6.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Part 7, Chapter 7.7: Hands-On Labs and Practice Questions


> 来源：`GSA/MasteringAgenticAISystems_supplementals` · `labs/archive/Part_07_Chapter_7.7_Labs_Practice.md` · [原文链接](https://github.com/GSA/MasteringAgenticAISystems_supplementals/blob/main/labs/archive/Part_07_Chapter_7.7_Labs_Practice.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


