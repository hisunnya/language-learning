# NCP-OUSD · OpenUSD 开发


## 速查表


### 第 1 章速查表：阶段（Stage）、层（Layer）、图元（Prim）、属性（Property）


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `cheat-sheets/chapter-01-cheatsheet.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/cheat-sheets/chapter-01-cheatsheet.md) · 语言：英文原文 · 中译版



# 第 1 章速查表：阶段（Stage）、层（Layer）、图元（Prim）、属性（Property）

## Stage 与 Layer 的区别
| 概念 | 定义 |
|---|---|
| Layer | 基于文件的观点容器（.usda ASCII、.usdc 二进制 Crate、.usd 两者皆可） |
| Stage | 通过组合（composition）将一个或多个 Layer 组合后得到的内存中结果 |

**考试提示：** Layer 是*源*，Stage 是*组合输出*。绝不要混淆二者 —— Stage 从不直接保存，保存下来的只有它的 root layer。

## Root Layer 与 Session Layer
| | Root Layer | Session Layer |
|---|---|---|
| 持久性 | 保存到磁盘 | 临时存在，不随 root layer 一起保存 |
| 强度 | Stage 的基准 | 默认是叠加栈中最强的观点 |
| 使用场景 | 创作并共享的生产数据 | 本地临时覆盖（可见性、隔离） |

## Attribute 与 Relationship
| | Attribute（属性） | Relationship（关系） |
|---|---|---|
| 承载内容 | 带类型的值（int、float、asset 等） | 由 SdfPath 构成的目标列表 |
| 支持时间采样？ | 是，支持时间采样 + default | 否 |
| 示例用途 | points、displayColor、radius | material:binding、proxyPrim targets |

**考试提示：** 如果题目描述的是*两个图元之间的链接* → relationship。如果描述的是*会变化的数值* → attribute。

## 元数据层级
| 层级 | 示例 |
|---|---|
| Layer | defaultPrim、upAxis、metersPerUnit、startTimeCode、endTimeCode |
| Prim | kind、active、instanceable、specifier |
| Property | interpolation、custom、variability |

**考试提示：** 要清楚哪个字段属于哪一层 —— 考试最常见的陷阱就是把 upAxis/metersPerUnit 放到了错误的层级。

## SdfPath 语法
| 语法 | 含义 |
|---|---|
| `/World/Geo/Cube` | 绝对 prim 路径 |
| `Geo/Cube` 或 `../Sibling` | 相对路径 |
| `/World/Geo/Cube.size` | prim 上的属性（用点号分隔） |
| `/World/Geo/Cube.primvars:displayColor` | 带命名空间的属性（用冒号分隔） |
| `/World/Geo/Cube.size.timeSamples` | 非法语法 —— 时间采样通过 API 访问，而不是用路径字符串 |

**考试提示：** 点号（`.`）分隔 prim 与属性；冒号（`:`）在属性名内部划分命名空间。绝不要混淆二者。

## Prim（图元）
一个命名空间容器节点，承载属性、元数据和子图元 —— 也是由 SdfPath 寻址的基本层级构建单元。

## 常见易错点
- Stage ≠ 磁盘上的文件；只有 Layer 才是基于文件的。
- Session layer 的观点在关闭时消失，除非显式导出/合并。
- Relationship 从不携带时间采样 —— attribute 才携带。
- defaultPrim 必须指向*同一 Layer 中已存在*的 prim。

---


### 第 2 章速查表：Schema、时间采样、Primvar、Kind


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `cheat-sheets/chapter-02-cheatsheet.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/cheat-sheets/chapter-02-cheatsheet.md) · 语言：英文原文 · 中译版



## 第 2 章速查表：Schema、时间采样、Primvar、Kind

### IsA（Typed）Schema 与 API Schema
| | IsA Schema（类型化 Schema） | API Schema |
|---|---|---|
| 设置 prim 的 typeName | 是 | 否 |
| 每个 prim 的数量 | 恰好 1 个 | 0..N 个 |
| 示例 | UsdGeomMesh、UsdGeomXform | UsdPhysicsCollisionAPI、UsdCollectionAPI |
| 用途 | 定义 prim **是什么** | 增添能力/行为 |

### Single-Apply 与 Multi-Apply API Schema
| 类型 | 需要实例名？ | 示例 |
|---|---|---|
| Single-apply | 否 | UsdGeomModelAPI、UsdPhysicsMassAPI |
| Multi-apply | 是（`Schema:instanceName`） | UsdCollectionAPI、UsdShadeCoordSysAPI |

**自定义 schema 规则：** 只有在现有 UsdGeom/UsdShade/UsdLux/UsdSkel/UsdPhysics schema 都无法覆盖需求时，才自行创作自定义（类型化或 API）schema。优先复用。

### 数值解析（Value Resolution）：时间采样 vs Default
- 拥有**任意**观点（default **或**时间采样）的最强层赢得该属性。
- 如果该层包含时间采样，它的 **default 会被完全忽略**。
- 时间采样**绝不跨层合并** —— 只查阅最强层的完整时间采样集合。
- 查询时间落在已创作的时间采样范围之外时，会被**保持/钳制**在最近的边界采样上，而不是从较弱的层填充。

### Primvar 插值方式（粗 → 细）
| 插值方式 | 粒度 | 说明 |
|---|---|---|
| constant | 整个 prim 一个值 | 无变化 |
| uniform | 每个面一个值 | 逐面平直 |
| varying | 每个点一个值 | 跨面始终线性 |
| vertex | 每个点一个值 | 跟随曲面基（例：细分边界） |
| faceVarying | 每个面角一个值 | 唯一支持不连续的模式（UV 接缝） |

### Purpose
| Purpose | 默认参与渲染？ | 使用场景 |
|---|---|---|
| default | 是（交互与渲染皆然） | 标准几何体 |
| render | 仅渲染 | 最终高质量几何体 |
| proxy | 交互/包围盒，渲染需显式开启 | 轻量替代物 |
| guide | 否（从渲染和常规遍历中排除） | 绑定控制器、辅助对象 |

### Kind 与模型层级
- 取值：**component、group、assembly、subcomponent**
- **component** = 叶模型，不能包含子模型
- **group** = 其他模型的容器
- **assembly** = 通常由被引用的 component 组成的 group（例如一套资产）
- **subcomponent** = 在 component 命名空间内标记某个有意义的片段，同时不破坏其叶节点身份
- **连续性规则：** kind 血缘必须从根节点起一脉相承 —— 模型层级链中不允许出现断档。

### 关键 API 调用
- `prim.IsA(Usd.SchemaBase subtype)` —— 检查类型化 schema
- `prim.HasAPI(SchemaClass, instanceName=None)` —— 检查已应用的 API schema
- `Usd.ModelAPI(prim).GetKind()` —— 获取 kind 元数据

---


### 组合弧（Composition Arcs）速查表


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `cheat-sheets/chapter-03-cheatsheet.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/cheat-sheets/chapter-03-cheatsheet.md) · 语言：英文原文 · 中译版



# 组合弧（Composition Arcs）速查表

## LIVRPS 强度排序（最强 → 最弱）
| 顺序 | 弧 | 说明 |
|---|---|---|
|1|Local（sublayers）|subLayers 列表顶部 = 最强|
|2|Inherits|基于 class 的共享|
|3|Variants|所选变体的观点|
|4|References|可编辑列表，外部/内部内容|
|5|Payloads|Reference 式组合的延迟版本|
|6|Specializes|最弱 —— 可自定义的基类/回退观点|

## Sublayer vs Reference vs Payload
| 弧 | 用途 | 默认加载？ | 命名空间影响 | 排序规则 |
|---|---|---|---|---|
| Sublayer | 将图层合并进**同一个**层栈，共用同一 prim 命名空间 | 是，始终加载 | 同一命名空间，仅覆盖 | subLayers 列表顶部 = 最强 |
| Reference | 组合外部/内部内容（新的 prim/资产） | 是，除非位于未加载的 payload 内部 | 引入独立的层栈 | 列表可编辑；列表顺序 = 强度 |
| Payload | 与 Reference 用途相同，但延迟加载 | 否 —— 必须调用 stage.Load() | 引入独立的层栈 | 与 Reference 相同的列表编辑规则 |

## 什么是层栈（Layer Stack）？
一个 root layer，加上通过 sublayer 弧递归可达的所有层。References 和 Payloads 是把**独立的**层栈组合到一起 —— 它们不会直接合并进调用方的本地层栈。

## 运行时 Payload API（Python, Usd.Stage）
```
stage.Load(path)                          # load payload at/under path
stage.Unload(path)                        # unload payload at/under path
stage.LoadAndUnload(loadSet, unloadSet)   # batch load/unload
stage.GetLoadRules()                      # inspect current load rules
stage.Reload()                            # re-read layers from disk (not load state)
```

## 如何选择 Reference 还是 Payload
- 小型/轻量、总是需要的内容 → **Reference**
- 大型/重量级内容（高精度几何体、完整环境），仅偶尔需要 → **Payload**
- 同一重量级资产的多个独立变换实例 → 在每个实例位置使用 **Payload**
- 组装（kit-bashing）大型场景 → **Payload**（保持初始 stage 打开速度快）

## 常见考试陷阱
- 未加载的 payload 内部嵌套的 payload，即使父级加载后仍保持未加载状态，直到它自己被显式加载。
- Sublayer 强度 = 列表位置（顶部最强），**不是**按时间先后插入的顺序。
- 在 LIVRPS 排序中，Payload 比 Reference **更弱**，尽管其余行为相似。
- “层栈” ≠ 会话中的所有层；它只是 root + 递归的 sublayer —— references/payloads 会引入各自的独立层栈。

---


### 第 4 章速查表：LIVRPS 强度排序与列表编辑


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `cheat-sheets/chapter-04-cheatsheet.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/cheat-sheets/chapter-04-cheatsheet.md) · 语言：英文原文 · 中译版



## 第 4 章速查表 —— LIVRPS 强度排序与列表编辑

### LIVRPS 顺序（最强 → 最弱）

| 排名 | 弧 | 说明 |
|---|---|---|
| 1 | **L**ocal | 层栈中直接创作的观点；在其所属层级始终获胜 |
| 2 | **I**nherits | 基于 class 的、可实时传播的共享观点 |
| 3 | **V**ariantSets | 可切换的备选观点集合 |
| 4 | **R**eferences | 组合外部/内部资产数据 |
| 5 | **P**ayloads | references 的延迟加载版本（重量级数据） |
| 6 | **S**pecializes | 最弱；回退/默认观点，最容易被覆盖 |

**记忆口诀：** *"Little Idiots Value Rare Purple Socks"* —— L-I-V-R-P-S。

### 关键规则
- **递归应用：** 每条弧的目标层栈本身都会先在内部按 LIVRPS 解析，然后才以该弧的强度层级组合进外层栈。
- 在自己的层栈层级内，**Local 总是获胜**，无论其他地方存在看起来更强的弧。
- **Specializes 总是落败** —— 用于那些本就打算被覆盖的默认值。
- Reference vs Payload：列表编辑方面处于同一强度档，但 Payload 延迟加载（用于大型/重量级资产）；Reference 立即加载。

### 列表编辑操作（适用于 references、payloads、inherits、variantSets、specializes）

| 操作 | 效果 |
|---|---|
| `prepend` | 将条目添加到较弱观点的条目**之前**（未给出关键字时的默认行为） |
| `append` | 将条目添加到较弱观点的条目**之后** |
| `delete` | 从组合后的列表中移除指定条目 |
| `explicit` | **重置**列表 —— 丢弃所有较弱的观点，只使用本层的条目 |

### 常见考试陷阱
- 混淆弧的顺序 —— 记住 Inherits（排名 2）胜过 VariantSets、References **以及** Payloads。
- 以为 `append` 或 `delete` 会重置整个列表 —— 只有 `explicit` 才会。
- 忘记组合是**递归的**：被引用资产内部的 variants/references 会先各自经过一轮 LIVRPS 解析。
- 以为 references 总是胜过 variants —— 恰恰相反（VariantSets > References）。
- 以为不带关键字的列表编辑是 `explicit` —— 它们默认是 `prepend`。

### 预测获胜观点（多弧场景）
1. 判断所讨论的层级上是否存在 Local 观点 → 若有，则它获胜。
2. 若无 Local 观点，则沿 LIVRPS 顺序向下遍历：Inherits → VariantSets → References → Payloads → Specializes。
3. 对于嵌套弧，先解析嵌套层栈自身的 LIVRPS，再把扁平化后的结果视为该弧在外层解析中对应强度槽位的观点。

---


### 第 5 章速查表：变体集（Variant Sets）、Inherits、Specializes、覆盖


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `cheat-sheets/chapter-05-cheatsheet.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/cheat-sheets/chapter-05-cheatsheet.md) · 语言：英文原文 · 中译版



## 第 5 章速查表：变体集（Variant Sets）、Inherits、Specializes、覆盖

### LIVRPS 强度顺序（最强 → 最弱）
| 排名 | 弧 | 说明 |
|---|---|---|
| 1 | Local | 层栈中的直接观点（含 sublayers） |
| 2 | Inherits | 强 —— 胜过 References、Payloads、Specializes |
| 3 | Variants | 所选变体的观点 |
| 4 | References | 标准资产复用 |
| 5 | Payloads | 延迟加载的 references |
| 6 | Specializes | 最弱 —— 一切都会覆盖它 |

**考试口诀：** "L-I-V-R-P-S" → *Inherits Insists, Specializes Surrenders.*

### Inherits vs Specializes
| 方面 | Inherits | Specializes |
|---|---|---|
| 强度 | 强（高于 References） | 最弱（低于 Payloads） |
| 使用场景 | 必须胜出的共享 "class" 观点 | 实例可覆盖的回退默认值 |
| 典型目标 | 带 `class` specifier 的 prim | 任意 prim，常是库中的 "Base" prim |
| API | `prim.GetInherits().AddInherit(path)` | `prim.GetSpecializes().AddSpecialize(path)` |

### Prim Specifiers
| Specifier | 含义 | 遍历/渲染 |
|---|---|---|
| `def` | 定义 prim（类型 + 存在性） | 默认包含 |
| `over` | 只添加观点，不做类型/存在性断言 | 仅当其他地方有定义时才包含 |
| `class` | 抽象；继承目标 | 排除（IsAbstract） |

### 变体集（Variant Sets）
- 选择结果保存在 prim 的元数据字段 **`variants`** 中：`{variantSetName: selectedVariant}`。
- 创建：`vset = prim.GetVariantSets().AddVariantSet("look")`
- 添加变体：`vset.AddVariant("damaged")`
- 选择：`vset.SetVariantSelection("damaged")`
- 在变体内部编辑：`with vset.GetVariantEditContext(): ...`
- 在更强的层中覆盖选择是非破坏性的 —— 原有变体保持完整。

### 非破坏性编辑规则
- 在镜头/序列层中进行编辑时优先使用 **`over`**。
- 只有在最初创作某个资产自身的定义时才使用 **`def`**。
- 在没有任何 `def` 的路径上使用 `over`，在默认遍历中组合不出任何可见内容 —— 这是典型的静默失败陷阱。

### 选择正确的弧 —— 快速决策表
| 目标 | 弧 |
|---|---|
| 共享的基础观点必须胜过 references | Inherits |
| 弱回退默认值，可自由覆盖 | Specializes |
| 在互斥的已创作外观/配置之间切换 | 变体集（Variant Set） |
| 非破坏性的单实例微调 | `over` |
| 创作原始资产定义 | `def` |

### 常见考试陷阱
1. 混淆哪条弧更强 —— Inherits（强）与 Specializes（弱）经常被互换作为干扰项。
2. 忘记变体选择保存在元数据（`variants`）中，而不是属性。
3. 在镜头级别微调时使用 `def` 而不是 `over`，破坏了非破坏性工作流的预期。

---


### 第 6 章速查表：Component 与 Assembly 资产设计


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `cheat-sheets/chapter-06-cheatsheet.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/cheat-sheets/chapter-06-cheatsheet.md) · 语言：英文原文 · 中译版



# 第 6 章速查表：Component 与 Assembly 资产设计

## Kind 层级（默认注册表）
| Kind | 类型 | 说明 |
|---|---|---|
| component | model | 原子化、自包含的叶资产；不含嵌套的模型子级 |
| subcomponent | non-model | component 内部有意义的命名部分（不可独立引用） |
| group | model | 对模型的通用组织性聚合 |
| assembly | model（group 的子类型） | 对大量 component/group 引用的聚合，例如搭建好的场景或绑定 |

## Reference vs Payload
| 弧 | 默认加载？ | 使用场景 |
|---|---|---|
| reference | 是，立即加载 | 小型/轻量资产、总是需要的数据 |
| payload | 否 —— 需要 Load() | 大型 assembly 内的重量级 component，按需加载 |

## 资产接口层（Asset Interface Layer）模式
- 顶层（例如 Asset.usd）是使用方**唯一**引用的文件。
- 声明恰好一个 defaultPrim。
- 通过 payload/sublayer 弧在其下组合内部层（payload.usd、geom.usd、mtl.usd）。
- 对外暴露 variantSets、kind 元数据以及任何公开的 API 属性。
- 使用方绝不直接引用内部文件 —— 这就是封装。

## 封装规则
1. 绝不让下游场景直接引用内部的 geom/mtl 层。
2. 只要接口契约保持稳定，内部文件名/布局可以随意更改而不破坏使用方。
3. 通过深层路径覆盖“伸手进入”内部结构，是考试中常被点名的反模式。

## 避免命名空间冲突
- 在聚合的 assembly 下，为每个被引用/被 payload 的资产挂一个唯一命名的子 prim 作为根（绝不在同一路径上平铺合并）。
- Reference 弧在组合时会重新根植命名空间 —— 应当用它，而不是事后手动重命名。
- 按来源/供应商使用 Scope prim 作为组织容器。
- 避免两个外部资产在没有唯一父级 Scope 的情况下都在同一绝对路径定义 prim。

## Assembly 中的 Payload 使用
- 含有大量（数百个以上）component 的 assembly，为每个 component 引用使用 payload 弧。
- 可实现快速打开场景 —— 重量级几何体只在通过 Stage.Load()/Unload() 显式请求时才加载。
- Reference = 始终加载；Payload = 按需加载 —— 需要规模化时选择 payload。

## 常见考试陷阱
- 混淆 reference 与 payload 的加载时机行为。
- 给叶资产赋予 "assembly" kind，或给多部分聚合体赋予 "component"。
- 直接引用内部的 geom/mtl 层而非接口层（破坏封装）。
- 以为命名空间冲突在没有显式唯一父级 Scope 的情况下会自动解决。

---


### 第 7 章速查表：原生实例化与点实例化


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `cheat-sheets/chapter-07-cheatsheet.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/cheat-sheets/chapter-07-cheatsheet.md) · 语言：英文原文 · 中译版



## 原生实例化（Native Instancing）与点实例化（Point Instancing）

| | 原生（Prototype）实例化 | UsdGeomPointInstancer |
|---|---|---|
| 触发方式 | prim 上的 `instanceable = true` 元数据 | 创作一个 `PointInstancer` prim + `prototypes` 关系 |
| 规模目标 | 数十到低数千 | 数千到数百万 |
| 每实例身份 | 每个实例都是独立的场景图 prim | 实例是数组索引，不是独立的 prim |
| 每实例编辑 | 通过 instance proxy（受限）或对那一个 prim 取消实例化（`instanceable=false`） | 在数组中按索引创作数值（protoIndices/positions/orientations/scales） |
| 视口中单独拾取/选择 | 可以，会解析为 instance proxy 路径 | 不可以 —— 解析为 instancer + instance id，而非独立 prim |
| 内存开销 | 每个实例一个 prim 的额外开销；规模大时较重 | 扁平数组；每实例开销极低 |

### 原生实例化
- 在被引用/被继承的 prim 上设置 `instanceable = true`。
- USD 会把共享子树组合一次，生成一个隐藏的 **prototype**（路径形如 `/__Prototype_1`）。
- 在查看器中选择实例内部的 prim 会解析为 **instance proxy** 路径 —— 一个用于查看的替身。
- **你不能在 instance proxy 上创作新的观点（属性、诸如材质绑定之类的关系）。**
- 若要真正覆盖**某一个**实例：仅在该实例的 root prim 上设置 `instanceable = false` → 它会变成自己的 prototype → 直接创作覆盖内容。此时只有该实例的共享关系被打破。
- 直接编辑共享的 prototype prim = 改动会传播到**每一个**实例。这正是考试陷阱的答案。

### UsdGeomPointInstancer
关键属性/关系：
| 名称 | 类型 | 用途 |
|---|---|---|
| `prototypes` | rel | 待实例化的候选 prim |
| `protoIndices` | int[] | 每个实例使用哪个 prototype |
| `positions` | point3f[] | 每实例平移 |
| `orientations` | quath[] | 每实例旋转（半精度四元数） |
| `scales` | float3[] | 每实例非均匀缩放 |
| `ids` | int64[] | 稳定的每实例标识符 |
| `invisibleIds` | int64[] | 需要隐藏的 Id，不影响其他数组 |
| `velocities` / `angularVelocities` | vector3f[] | 支持运动模糊 |

### 决策规则（考试启发式）
- 需要成千上百万个副本，且不需要按实例编辑场景图 → **PointInstancer**。
- 需要按实例切换材质/变体、视口拾取，或数量适中 → **原生实例化**。
- 需要在众多共享实例中修正**某一个** → **对那一个 prim 取消实例化**，不要动 prototype，也不要试图在 instance proxy 上创作。

### 常见考试陷阱
1. 试图直接在 instance proxy 上绑定材质 → **无效**，必须取消实例化。
2. 编辑共享的 prototype 却以为只影响一个实例 → **会影响全部**。
3. 以为 PointInstancer 的实例可以像原生实例那样单独选择/编辑 → **不能**；应改用 ids/invisibleIds/数组创作。

---


### 第 8 章速查表：文件格式、USDZ 打包、资产解析


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `cheat-sheets/chapter-08-cheatsheet.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/cheat-sheets/chapter-08-cheatsheet.md) · 语言：英文原文 · 中译版



## 第 8 章：文件格式、USDZ 打包、资产解析
**考查范围：** 数据交换与互操作性（约 14%）

### 格式对比
| 格式 | 编码方式 | 人类可读 | 使用场景 |
|---|---|---|---|
| .usda | ASCII 文本 | 是 | 手工创作、覆盖、差异对比/版本控制 |
| .usdc | 二进制（Crate） | 否 | 生产场景、重量级 payload、快速加载 |
| .usd | 两者皆可（ASCII 或 Crate） | 视情况而定 | 与格式无关的容器；加载时通过内容嗅探判断 |
| .usdz | 打包（zip） | 否 | 自包含的跨应用/AR 分发 |

**考试陷阱：** `.usd` 扩展名**完全不能**说明编码方式 —— USD 会检查文件头/magic bytes 来判断是 ASCII 还是 Crate。

### USDZ 打包规则（硬性要求）
- 只能使用 **Store（不压缩）** 方式的 zip 压缩包 —— 不允许使用 Deflate。
- 条目必须按 **64 字节对齐**，以支持直接内存映射。
- **不允许加密**。
- 必须**完全自包含** —— 压缩包之外不得有任何外部文件引用。
- 所有内部引用必须使用**相对路径**。
- **默认根层**（通常是 .usdc）必须是压缩包中的**第一个条目**。

### 相对路径 vs 锚定路径
| 路径类型 | 相对于什么解析 | 可移植性 |
|---|---|---|
| 相对路径（`./tex.png`、`tex.png`） | 引用它的那一层所在位置 | 高 —— 随包移动依然安全 |
| 锚定/绝对路径（`/Users/...`、`C:\...`） | 固定的文件系统位置 | 低 —— 移动到另一台机器就会失效 |

**经验法则：** USDZ = 只用相对路径。锚定路径是包在不同机器/应用之间迁移时出现“贴图丢失”问题的头号原因。

### 资产解析（Asset Resolution）
- **AssetResolver**（`ArResolver` 接口、Ar 插件系统）把资产路径字符串转换为实际可解析的位置。
- 流水线可以实现**自定义解析器**，用于版本管理、搜索路径逻辑或对接资产管理系统。
- 组合（UsdStage）消费的是已经解析好的路径 —— 解析发生在组合之下，而不是组合的一部分。

### DCC 交换：无损 vs 有损
- 在纯 USD 工具链内部，原生 USD 往返转换通常**无损**。
- 通过 USD 导出器从 DCC 工具（Maya、Houdini、Blender 等）导出：当自定义节点类型/属性没有直接对应的 USD schema 时，往往**有损** —— 数据可能被丢弃或近似处理。
- 在假定 DCC 导出能保留 100% 保真度之前，务必先检查 schema 覆盖情况。

### 快速决策规则
- 需要**手工读取/对比/编辑** → `.usda`
- 需要**快速加载、占用空间小**的生产场景 → `.usdc`
- 需要**跨应用/AR 分发单个可移植的自包含包** → `.usdz`
- **移动文件后出现断链** → 检查是否为锚定/绝对路径，而不是相对路径

---


### 第 9 章速查表：用 Usd、Sdf、Gf、Vt 创作 Stage


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `cheat-sheets/chapter-09-cheatsheet.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/cheat-sheets/chapter-09-cheatsheet.md) · 语言：英文原文 · 中译版



## 第 9 章速查表：用 Usd、Sdf、Gf、Vt 创作 Stage

### Stage 的创建
| 调用 | 行为 |
|---|---|
| `Usd.Stage.CreateNew(path)` | 创建全新的根层，**覆盖**已有文件 |
| `Usd.Stage.Open(path)` | 打开已有文件，保留原有内容 |
| `Usd.Stage.CreateInMemory()` | 匿名 stage，不写入磁盘文件 |

### 定义 Prim
| 方法 | 返回值 | 说明 |
|---|---|---|
| `stage.DefinePrim(path, typeName)` | `Usd.Prim`（通用） | typeName 是字符串；没有内置的类型化访问器 |
| `UsdGeom.Xform.Define(stage, path)` | 类型化 schema 对象 | 设置 typeName 并返回便捷包装（`GetXform...Attr()`） |
| `UsdGeom.Sphere.Define(stage, path)` | `UsdGeom.Sphere` | 具备 `GetRadiusAttr()`、`CreateRadiusAttr()` 等方法 |

**考试要点：** 只要在创作时已知 schema 类型，类型化 `Define()` 就是首选／最佳实践答案。

### Sdf.Path 语法
| 写法 | 含义 |
|---|---|
| `/World/Cube` | 子 prim 路径（斜杠 = 命名空间子级） |
| `/World/Cube.size` | prim 上的属性／property（点号 = property） |
| `/World/Cube.size:custom` | 带命名空间的 property（冒号 = 子命名空间） |
| `World/Cube.size` | **无效的绝对路径** —— 缺少开头的斜杠 |

### Gf 数学类型
| 类型 | 精度 | 常见用途 |
|---|---|---|
| `Gf.Vec3f` | 单精度 | 点、法线、速度 |
| `Gf.Vec3d` | 双精度 | 高精度位置 |
| `Gf.Matrix4d` | 双精度 | `xformOp:transform` **必须**使用（此处 Matrix4f 无效） |

### Vt.Array
- `Vt.Vec3fArray`、`Vt.FloatArray`、`Vt.IntArray` 等。
- 任何数组值属性（`points`、`normals`、`faceVertexIndices`）所必需的存储类型。
- 在 `Set()` 时 Python 列表会自动转换为 `Vt.Array`，但 stage 中的存储类型始终是 `Vt.Array`。

### 属性创作：默认值 vs 时间采样
```python
attr.Set(value)              # authors DEFAULT (Usd.TimeCode.Default())
attr.Set(value, 24)          # authors TIME SAMPLE at frame 24
```
- 两种意见（opinion）可以共存于同一个属性上。
- 在第一个时间采样之前查询 → 返回**最早的时间采样**（保持／钳制），而不是默认值。
- 只有在查询 `Usd.TimeCode.Default()` 时才会返回默认值。

### 关系 vs 属性
| API | 存储内容 | 示例 |
|---|---|---|
| `prim.CreateAttribute(name, type)` | 带类型的数值 | `Sdf.ValueTypeNames.Float3` |
| `prim.CreateRelationship(name)` | `Sdf.Path` 目标 | `.SetTargets([path1, path2])` |

### 常见考试陷阱
1. 在已有路径上调用 `CreateNew()` 会静默覆盖 —— 不会抛出错误。
2. 混淆 `/A/B`（子 prim）与 `/A.B`（property）在 Sdf.Path 中的区别。
3. 以为通用的 `DefinePrim()` 会提供类型化属性访问器 —— 并不会。
4. 给 `xformOp:transform` 使用 `Matrix4f` —— 必须使用 `Matrix4d`。
5. 调用 `Set(value)` 两次并期待得到时间采样 —— 不带时间参数时始终写入默认值。

---


### 第 10 章速查表：遍历、组合编辑与 Hydra


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `cheat-sheets/chapter-10-cheatsheet.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/cheat-sheets/chapter-10-cheatsheet.md) · 语言：英文原文 · 中译版



## 第 10 章速查表：遍历、组合编辑与 Hydra

### 遍历
| API | 用途 | 考试提示 |
|---|---|---|
| `stage.Traverse()` | 使用 `UsdPrimDefaultPredicate`（Active && Defined && Loaded && !Abstract） | 非活动／未定义的 prim 会被静默跳过 |
| `Usd.PrimRange(prim)` | 控制更精细的迭代器 | 在当前 prim 上调用 `.PruneChildren()` 可跳过其子树 |
| `Usd.TraverseInstanceProxies()` | 用于下钻到实例化原型的谓词 | 实例代理（instance proxy）是只读的替身 |
| `range.IsPostVisit()` | 对某 prim 的第二次访问（后序）时为真 | 用于后序处理，与组合无关 |

### 用 Python 创作组合弧（composition arc）
| 任务 | 调用 |
|---|---|
| 添加 reference | `prim.GetReferences().AddReference(assetPath, primPath="")` |
| 添加 payload | `prim.GetPayloads().AddPayload(assetPath, primPath="")` |
| 创建 variant set | `vs = prim.GetVariantSets().AddVariantSet(name)` |
| 添加 variant 选项 | `vs.AddVariant(variantName)` |
| 选择 variant | `vs.SetVariantSelection(variantName)` |

**References vs Payloads：** Reference 总是参与组合；payload 支持 `stage.Load()` / `Unload()` 实现按需加载 —— 考试会考针对重型／可选资产选择 payload。

### EditTarget 与 Sdf.Layer
- `stage.SetEditTarget(Usd.EditTarget(layer))` —— 把之后所有的创作调用（`CreateAttribute().Set()`、variant 选择等）路由到 `layer`。
- `layer` 必须已经属于该 stage 的层栈（根层、sublayer，或可通过 reference/payload 弧的局部意见访问到的层）。
- 直接编辑 `Sdf.Layer`（在 layer 对象上创建 `Sdf.PrimSpec`/`Sdf.AttributeSpec`）会绕过 stage 层的 EditTarget 路由 —— 你编辑的是 layer 对象本身。
- 常见 bug：在一次限定范围的编辑之后忘记把 EditTarget 重置回根层。

### 检查组合
- `Usd.PrimCompositionQuery(prim).GetCompositionArcs()` → `UsdCompositionArc` 列表（弧类型、引入的层、目标路径）。
- 当你需要知道某个意见是*哪种弧类型*产生时，用它代替手动解析 `prim.GetPrimStack()`。

### Hydra —— 仅用于渲染的边界
| 组件 | 作用 |
|---|---|
| Scene delegate | 把 USD（或其他）场景数据转换为 Hydra 的渲染索引（`HdRenderIndex`） |
| Render index | 内存中的、与渲染器无关的场景表示 |
| Render delegate | 消费渲染索引进行渲染（Storm、Arnold、Karma 等） |

**核心考试点：** Hydra 没有回写到 USD 的创作路径。Scene delegate 与 render delegate 都无法修改 prim 意见、EditTarget 或层 —— 相对 stage 而言，渲染严格只读。

---


### 第 11 章速查表 —— usdview 调试与规模优化


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `cheat-sheets/chapter-11-cheatsheet.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/cheat-sheets/chapter-11-cheatsheet.md) · 语言：英文原文 · 中译版



## 第 11 章速查表 —— usdview 调试与规模优化

### usdview 面板
| 面板 | 用途 |
|---|---|
| Prim Browser | 组合后 prim 的树形视图；右键可 Load/Unload payload |
| Property Panel | 属性数值、元数据、authored 与 computed 的区分 |
| Layer Stack | 所有贡献意见的层，按强度顺序排列 |
| Composition Tab (Index) | 按弧分解的胜出意见；点击某个弧可检查源层 |

### LIVRPS 强度顺序（最强 → 最弱）
1. **L**ocal（层栈、sublayer 顺序）
2. **I**nherits
3. **V**ariants
4. **R**eferences
5. **P**ayloads
6. **S**pecializes

助记口诀：*Little Interns Value Real Paychecks Sometimes*

### Purpose 取值
| 取值 | 参与渲染？ | 视口中可见？ | 典型用途 |
|---|---|---|---|
| default | 继承父级 | 是 | 标准几何体 |
| render | 是 | 是 | 最终制作几何体 |
| proxy | **否** | 是 | 重型渲染几何体的轻量替身 |
| guide | **否** | 是（可选） | 绑定控制器、定位器、标注 |

考试陷阱：proxy/guide 几何体在 usdview 中可见，却在最终渲染中悄然消失 —— 遇到「渲染中缺失」类问题时，务必先检查 purpose。

### Payloads vs References
| 弧 | 默认参与组合？ | 使用场景 |
|---|---|---|
| Reference | 是，始终 | 小型／中型可复用资产 |
| Payload | **否** —— 延迟加载，必须 Load | 大型场景中的重型资产；主要的规模优化手段 |

### 命令
```
usdchecker --arkit asset.usdz      # ARKit/USDZ compliance validation
usdchecker asset.usda              # general compliance checks
usdview stage.usda                 # interactive inspection
```
Python：
```python
stage = Usd.Stage.Open(path, load=Usd.Stage.LoadNone)  # open without loading payloads
prim.Load()   # load a specific payload
prim.Unload() # unload it
```

### 规模优化优先级
1. **Payload 管理** —— 让不需要的分支保持未加载（对内存／加载时间的收益最大）
2. **实例化**（`instanceable=true`）—— 在 Pcp 中对相同的原型几何体去重
3. **Purpose 过滤** —— 用 proxy/guide 减少渲染时需要遍历的内容
4. **层结构** —— 尽量避免过深的 sublayer 栈和冗余覆盖；只在必要时展平

### 调试流程
1. 在 Prim Browser 中确认 prim 存在
2. 检查 Property 面板中是否有非预期的覆盖
3. 打开 Composition tab → Index，看哪个弧／层胜出
4. 显式检查 `purpose` 与 `visibility` 属性
5. 确认 payload 的加载状态（已加载还是未加载）
6. 交付前运行 `usdchecker`，排查 schema／合规问题

---


### 第 12 章速查表 —— 全真模拟考试与时间管理


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `cheat-sheets/chapter-12-cheatsheet.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/cheat-sheets/chapter-12-cheatsheet.md) · 语言：英文原文 · 中译版



## 第 12 章速查表 —— 全真模拟考试与时间管理

### 考试时间分配计算
| 总时长 | 复习缓冲 | 题量 | 每题时间（第一遍） |
|---|---|---|---|
| 90 分钟 | 15 分钟 | 65 | (90-15)/65 ≈ 1.15 分钟（约 69 秒） |
| 90 分钟 | 10 分钟 | 65 | (90-10)/65 ≈ 1.23 分钟（约 74 秒） |
| 90 分钟 | 20 分钟 | 60 | (90-20)/60 ≈ 1.17 分钟（约 70 秒） |

**经验法则：** 为标记题目预留 10-15 分钟。第一遍作答时，单题绝不超过 2 分钟 —— 标记后立即跳过。

### LIVRPS 组合强度（最强 → 最弱）
| 顺序 | 弧 | 说明 |
|---|---|---|
| 1 | Local | 在定义层栈中直接创作的意见 |
| 2 | Inherits | 基于 class 的共享意见 |
| 3 | VariantSets | 由选择驱动的意见 |
| 4 | References | 外部／内部组合，始终已加载 |
| 5 | Payloads | 类似 References，但默认延迟／未加载 |
| 6 | Specializes | 最弱 —— 后备／基础意见 |

**陷阱：** Local 意见总是胜过通过 References/Payloads 引入的意见，即使后者在被引用的层内部本身也是「local」的。

### 实例化／聚合决策表
| 需求 | 使用 |
|---|---|
| 数千个分散的相同资产，需要每实例的变换／属性数组 | UsdGeomPointInstancer |
| 对相同层级结构去重以节省内存，唯一的覆盖很少 | instanceable=true 的 reference |
| 大规模场景下每实例需要独特的材质／外观覆盖 | 避免 instanceable；改用 PointInstancer 或按实例键的组合 |

### Python 创作模式
| 任务 | API 调用 |
|---|---|
| 将 prim 标记为 instanceable | `prim.SetInstanceable(True)` |
| 批量执行多次编辑，避免逐次触发通知 | `with Sdf.ChangeBlock(): ...` |
| 添加 reference | `prim.GetReferences().AddReference(assetPath, primPath)` |

### 考试当天检查清单
- [ ] 准备好有效的带照片证件，供远程监考核查
- [ ] 清空桌面，完成摄像头房间扫描
- [ ] 手边没有笔记、第二显示器或手机
- [ ] 确认可以标记题目并返回之前的题目
- [ ] 做最后一次按知识域的回顾：组合、实例化／聚合、Python API，再加上官方考试指南中的另外三个知识域

### 最后一遍规则
只复习标记过的题目。不要重新打开那些已经自信作答过的题目 —— 在最终复习中反复怀疑自己本来确定的答案，是分数回退的首要原因。

---



## 记忆卡


### 第 1 章记忆卡：USD 对象模型——Stage、Layer、Prim 与 Property


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `flashcards/chapter-01-flashcards.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/flashcards/chapter-01-flashcards.md) · 语言：英文原文 · 中译版



## 第 1 章：USD 对象模型——Stage、Layer、Prim 与 Property——记忆卡

| # | 正面（问题） | 背面（答案） |
|---|-----------------|---------------|
| 1 | Stage 与 Layer 的区别是什么？ | Layer = 以文件为后端的意见容器（.usda/.usdc/.usd）。Stage = 一个或多个 Layer 组合之后的内存结果。应试提示：layer 是源数据，stage 是组合的输出。 |
| 2 | Attribute 与 Relationship 的关键区别？ | Attribute = 带类型的数值，可以有时间采样（可动画）。Relationship = 指向一个或多个其他 SdfPath，无类型，也没有时间采样。应试提示：材质绑定和着色器连接使用的是 relationship。 |
| 3 | .usda 与 .usdc 的区别是什么？ | .usda = 人类可读的 ASCII 文本层。.usdc = 二进制 'Crate' 格式，加载更快、体积更小。.usd = 两者皆可，打开时自动判定。应试提示：.usdc 是典型的制作环境格式。 |
| 4 | SdfPath 语法：如何寻址 prim /World/Geo/Cube 上的属性 'size'？ | /World/Geo/Cube.size —— 用点号分隔 prim 路径与属性名。应试提示：冒号（:）用于带命名空间的属性名，例如 primvars:displayColor，而不是 prim 与属性之间的分隔符。 |
| 5 | SdfPath 语法：绝对路径与相对路径的示例 | 绝对：/World/Geo/Cube（以 / 开头）。相对：Geo/Cube 或 ../Sibling（不以 / 开头）。应试提示：relationship 目标与 reference 路径通常是绝对路径。 |
| 6 | Session Layer 用来做什么？ | 一个临时的、非持久化的层，叠加在根层之上，保存局部覆盖（例如视口可见性开关）。应试提示：session layer 的意见默认最强，且不会随根层一起保存到磁盘。 |
| 7 | Root Layer 是什么？ | 传给 UsdStage::Open()/CreateNew() 的那个层，用作组合 stage 的锚点；sublayer 与 reference 都相对于它组合。应试提示：保存 stage 会把创作的意见持久化到这个层的文件中。 |
| 8 | 说出 USD 元数据可以被创作的三个层级 | Layer 级（defaultPrim、upAxis、metersPerUnit）、Prim 级（kind、active、instanceable）、Property 级（interpolation、custom）。应试提示：要知道哪个字段属于哪一层。 |
| 9 | USD 中的 Prim 是什么？ | 场景图中的命名空间容器节点，持有属性（attribute/relationship）、元数据和子 prim。应试提示：prim 是 stage 层级的基本构件，通过 SdfPath 寻址。 |
| 10 | defaultPrim 元数据——在哪里创作，作用是什么？ | 作为根层上的层元数据创作；它指定在不带显式 prim 路径引用该层时作为入口的 prim。应试提示：必须指向一个已存在的顶层 prim。 |
| 11 | Relationship 能像 Attribute 一样做时间采样吗？ | 不能。Relationship 存储目标路径列表，永远不做时间采样；只有 attribute 支持带时间采样的数值加上默认值。应试提示：这是常考的 attribute 与 relationship 之间的区别。 |
| 12 | upAxis 与 metersPerUnit 属于哪一层级的元数据？ | Layer 级元数据，通常创作在根层上，用于定义上轴约定（Y 或 Z）和单位比例。应试提示：除非创作在引用方 stage 自己的根层上，否则它们不会自动从被引用的层传播过来。 |

---


### 第 2 章记忆卡：Schema、时间采样、Primvars 与模型层级


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `flashcards/chapter-02-flashcards.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/flashcards/chapter-02-flashcards.md) · 语言：英文原文 · 中译版



## 第 2 章：Schema、时间采样、Primvars 与模型层级——记忆卡

| # | 正面（问题） | 背面（答案） |
|---|-----------------|---------------|
| 1 | IsA（类型化）schema 与 API schema 的核心区别？ | IsA schema 定义一个 prim 是什么（设置该 prim 的 typeName，例如 Mesh、Xform）—— 一个 prim 只有一个类型化 schema。API schema 在不改变 typeName 的前提下增加一组能力／属性；一个 prim 可以应用多个 API schema。应试提示：「定义类型」＝IsA；「增加行为」＝API。 |
| 2 | 单应用（single-apply）与多应用（multi-apply）API schema？ | 单应用：每个 prim 一个实例（例如 UsdGeomModelAPI、UsdPhysicsRigidBodyAPI）。多应用：每个 prim 多个具名实例，存储形式类似 apiSchemas = ["CollectionAPI:name"]（例如 UsdCollectionAPI、UsdShadeCoordSysAPI）。应试提示：多应用 schema 需要实例名。 |
| 3 | 什么时候应该创作自定义 USD schema？ | 只有当现有 schema（UsdGeom、UsdShade、UsdLux、UsdSkel、UsdPhysics、UsdVol）都无法覆盖需求时。优先复用／扩展标准 schema —— 自定义 schema 会破坏互操作性。应试提示：「先复用，再自建」是被考查的原则。 |
| 4 | 值解析：最强层对同一属性同时有默认值和时间采样，哪个胜出？ | 时间采样完全胜出；同一层中的默认值只要存在时间采样就会被忽略。应试提示：只有在解析出的意见中任何地方都不存在时间采样时，默认值才是真正的后备。 |
| 5 | 时间采样只存在于最强层的第 1-10 帧；查询时间 = 50 —— 返回什么值？ | 该值被保持（钳制）在最后一个可用的时间采样上（第 10 帧的值）—— 较弱层在第 50 帧的时间采样既不会被查询，也不会被合并进来。应试陷阱：时间采样绝不跨层合并；只使用最强层的完整采样集合。 |
| 6 | Primvar 插值：'vertex' 与 'varying' 的区别？ | 两者都是每个点存储一个值，但 'vertex' 使用曲面的基底进行插值（例如细分极限曲面），而 'varying' 无论曲面基底如何都只做线性插值。应试提示：需要跟随细分平滑的数值（例如法线）用 vertex，严格线性的属性用 varying。 |
| 7 | 带接缝的 UV 的 Primvar 插值（按角点不连续的值）？ | faceVarying —— 每个面－顶点（每个面的每个角点）一个值，允许接缝两侧取不同的值。应试提示：faceVarying 是唯一支持共享顶点处不连续的插值方式。 |
| 8 | 列出 UsdGeom 的全部 5 种 primvar 插值取值。 | constant、uniform、varying、vertex、faceVarying。应试提示：按从粗到细的粒度记住顺序：constant（整个 prim）→ uniform（每个面）→ varying/vertex（每个点）→ faceVarying（每个面－角点）。 |
| 9 | Purpose：proxy 与 guide 的区别？ | proxy = 轻量替身几何体，用于交互操作／包围盒计算，如果显式要求仍然可以被渲染（例如碰撞代理）。guide = 根本不用于渲染（绑定、辅助对象），默认同时被排除在渲染和播放之外。应试提示：proxy = 快速的替代渲染几何体；guide = 不可渲染的辅助对象。 |
| 10 | USD 模型层级中的 Kind 取值？ | component、group、assembly、subcomponent。应试提示：component = 叶子模型（不能再包含子模型）；group/assembly = 容器模型；subcomponent = 在不破坏叶子身份的前提下标记 component 命名空间内有意义的子部件。 |
| 11 | 模型层级的连续性规则？ | Kind 的继承链必须从伪根向下不断裂：如果某个 prim 有 kind，那么它到根的每一个祖先 prim 也必须有 kind（通常是 group 或 assembly）。component 不能有本身是 model 的后代。应试陷阱：kind 赋值出现断点会破坏基于模型的快速层级遍历（例如 Usd.PrimIsA/IsModel）。 |
| 12 | 命令／API：如何在 Python 中检查某个 prim 是否应用了 API schema？ | prim.HasAPI(SchemaClass)，例如 prim.HasAPI(UsdPhysics.CollisionAPI)；多应用时传入实例名：prim.HasAPI(UsdCollectionAPI, instanceName='myColl')。应试提示：HasAPI 是标准查询方式，而不是用字符串匹配 GetAppliedSchemas()。 |

---


### 第 3 章记忆卡：组合弧——Sublayer、Reference 与 Payload


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `flashcards/chapter-03-flashcards.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/flashcards/chapter-03-flashcards.md) · 语言：英文原文 · 中译版



## 第 3 章：组合弧——Sublayer、Reference 与 Payload——记忆卡

| # | 正面（问题） | 背面（答案） |
|---|-----------------|---------------|
| 1 | Sublayer 的强度顺序规则？ | subLayers 列表最顶部 = 最强的意见；顺序自上而下由强到弱。应试提示：重排 subLayers 会改变同一属性由哪个值胜出。 |
| 2 | Reference 与 Payload 的默认加载行为区别？ | Reference 在 stage 打开时自动加载（除非嵌套在未加载的 payload 内部）。Payload 默认不加载 —— 必须显式加载。应试提示：想延迟加载的重型资产就用 payload。 |
| 3 | 在已打开的 stage 上加载 payload 的 API 调用（Python）？ | stage.Load(path) —— 加载给定 prim 路径处／其下的 payload。配对使用：stage.Unload(path)。批量版本：stage.LoadAndUnload(loadSet, unloadSet)。 |
| 4 | 哪种弧能在跨层的同一个 prim 命名空间内合并意见（而非跨不同资产）？ | Sublayer 弧 —— 把各层组合进同一个层栈，作用于同一命名空间。应试提示：sublayer 不会引入别处的 prim，它是在已有路径上叠加意见。 |
| 5 | LIVRPS 强度顺序 —— 各个字母代表什么？ | Local、Inherits、Variants、References、Payloads、Specializes —— 从最强到最弱的组合弧顺序。应试提示：Reference 强于 Payload；Specializes 最弱。 |
| 6 | 什么构成一个「层栈」？ | 一个根层加上通过 sublayer 弧递归可达的所有层。应试提示：References／Payloads 是把彼此独立的层栈组合起来 —— 它们不会合并进调用方的本地层栈。 |
| 7 | 什么情况下该为资产选择 Payload 而不是 Reference？ | 对大型／重型资产（高分辨率几何体、完整环境）且并非总是需要时使用 Payload —— 可实现惰性加载和更快的 stage 打开速度。对轻量或始终需要的内容使用 Reference。 |
| 8 | 嵌套 payload 行为：位于未加载 payload 内部的 payload？ | 即使祖先已加载，它仍保持未加载，直到该嵌套 payload 本身也被显式加载。应试陷阱：很多人以为只要祖先路径存在就会自动加载。 |
| 9 | 从磁盘重新加载 stage 上所有层的命令？ | stage.Reload() —— 重新从磁盘读取层内容，但不改变 payload 的加载／未加载状态。与 Load/Unload 不同。 |
| 10 | Reference 弧是否像 sublayer 那样支持强度排序？ | 支持 —— Reference 列表可编辑；多个 reference 按列表顺序组合，靠前／前置的条目更强。Payloads 同样适用这套列表编辑模型。 |
| 11 | Specializes 弧与 Reference 相比的强度？ | 在 LIVRPS 中 Specializes 比 Reference 更弱。用于存放基础／后备意见，以便被本地覆盖。应试陷阱：初学者会以为它是强覆盖弧。 |
| 12 | 为什么在拼装（kit-bashing）／重型资产库中使用 Payload？ | 可以搭建引用数千个重型资产的巨型场景，同时保持初始 stage 打开迅速，只加载当前任务所需的内容。应试提示：这是实际工作中考查最多的用例。 |

---


### 第 4 章记忆卡：LIVRPS 强度排序与列表编辑操作


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `flashcards/chapter-04-flashcards.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/flashcards/chapter-04-flashcards.md) · 语言：英文原文 · 中译版



## 第 4 章：LIVRPS 强度排序与列表编辑操作——记忆卡

| # | 正面（问题） | 背面（答案） |
|---|-----------------|---------------|
| 1 | LIVRPS 代表什么？ | Local、Inherits、VariantSets、References、Payloads、Specializes。应试提示：顺序 = 由强到弱，必须准确背下来。 |
| 2 | LIVRPS 强度顺序 —— 从强到弱？ | Local > Inherits > VariantSets > References > Payloads > Specializes。应试提示：「Local 永远赢」和「Specializes 永远输」是首先要记住的两个锚点。 |
| 3 | LIVRPS 中最弱的组合弧是哪一种？ | Specializes。它专为后备／默认意见设计，这些意见应当能被其他一切轻松覆盖。 |
| 4 | 除 Local 之外，最强的组合弧是哪一种？ | Inherits。它紧邻 Local 之下，因此继承而来的 class 意见胜过 VariantSets、References、Payloads 和 Specializes。 |
| 5 | 列表编辑操作：append | 在组合列表中把条目添加到较弱意见已有条目之后。不会删除或重置已有条目。 |
| 6 | 列表编辑操作：prepend | 在组合列表中把条目添加到较弱意见已有条目之前。在 .usda 语法中未指定关键字时的默认行为。 |
| 7 | 列表编辑操作：explicit | 完全丢弃该字段所有较弱的组合条目，用本层指定的条目替换整个列表。 |
| 8 | 列表编辑操作：delete | 从组合列表中移除指定条目（来自较弱的意见），但不重置或替换整个列表。 |
| 9 | LIVRPS 强度排序只适用于顶层 stage，还是递归适用？ | 递归适用。由某个弧引入的每个层栈（例如被引用资产自身的内部层栈）都会先在内部按 LIVRPS 解析，然后再以该弧的强度级别参与外层组合。应试提示：这是重点考查的「多弧组合」场景。 |
| 10 | 在单个层栈层级内，哪个意见总是胜出？ | Local 意见 —— 它是 LIVRPS 中最强的位置，在同一层级内总是优先于 Inherits／VariantSets／References／Payloads／Specializes。 |
| 11 | 用例：让共享的基础属性在众多 prim 之间实时传播（类似 class 的共享） | 使用 Inherits，而不是 References。Inherits 强于 References／Payloads／VariantSets，并会把基础编辑自动传播给所有继承它的 prim。 |
| 12 | USD 组合中最终的「展平」结果是什么？ | 在应用 LIVRPS 强度排序（在嵌套层栈间递归进行）以及全部列表编辑操作之后产生的单一解析输出 —— 展平 stage 时导出的／烘焙的就是它。 |

---


### 第 5 章记忆卡：Variant Set、Inherits、Specializes 与非破坏性覆盖


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `flashcards/chapter-05-flashcards.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/flashcards/chapter-05-flashcards.md) · 语言：英文原文 · 中译版



## 第 5 章：Variant Set、Inherits、Specializes 与非破坏性覆盖——记忆卡

| # | 正面（问题） | 背面（答案） |
|---|-----------------|---------------|
| 1 | LIVRPS 强度顺序 —— 从强到弱列出全部六种弧类型 | Local、Inherits、Variants、References、Payloads、Specializes。应试提示：Inherits 胜过 References；Specializes 输给所有其他弧。 |
| 2 | Inherits 弧：常考的用例 | 共享的 'class' prim，其意见必须强于 reference（例如全工作室通用的绑定默认值，用来覆盖单个资产的意见）。强度关系：Inherits > Variants > References。 |
| 3 | Specializes 弧：常考的用例 | 弱的后备／默认意见（例如资产库默认值），实例级别和被引用的意见都可以随意覆盖它。Specializes 是 LIVRPS 中最弱的弧。 |
| 4 | Inherits 与 Specializes —— 一句话区分 | Inherits = 强覆盖（base 赢）。Specializes = 弱后备（base 输给其他一切）。应试记忆技巧：「Inherits Insists, Specializes Surrenders」（Inherits 坚持，Specializes 让步）。 |
| 5 | 可复用 inherit 目标的 prim specifier | 'class' —— 把该 prim 标记为抽象（IsAbstract=True）；默认的 UsdStage 遍历与渲染都会排除它。 |
| 6 | USD 中 variant 选择存储在哪里？ | 存储在 prim 的 'variants' 元数据字典中，以 variant set 名称为键，值为选中的 variant 名称。可以从任何更强的层非破坏性地覆盖。 |
| 7 | Python：添加 variant set 和 variant，然后在其中编辑 | vset = prim.GetVariantSets().AddVariantSet("look") vset.AddVariant("damaged") vset.SetVariantSelection("damaged") 配合 vset.GetVariantEditContext():     # 仅对该 variant 生效的意见 |
| 8 | Python：创作 inherits 弧 | prim.GetInherits().AddInherit(Sdf.Path("/World/Class/Base")) |
| 9 | Python：创作 specializes 弧 | prim.GetSpecializes().AddSpecialize(Sdf.Path("/World/Defaults/PropBase")) |
| 10 | 'over' 与 'def' 的核心区别 | 'def' 定义／创建一个 prim（断言其存在与类型）。'over' 只给别处已定义的 prim 添加意见 —— 非破坏性，不重新声明类型或存在性。 |
| 11 | 考试陷阱：如果组合层栈中任何位置都没有 'def'，却在某个 prim 路径上创作了 'over' 会怎样？ | 该 prim spec 会存在于层中，但组合出来的 prim 没有定义性 spec —— 它不会出现在默认的 UsdStage 遍历中（因为没有已定义的 prim），这是「意见悄然不起作用」的常见陷阱。 |
| 12 | 非破坏性编辑理念 —— 为什么在 shot／edit 层中优先使用 'over' | 保留原始资产定义，使编辑可逆／可移除，并允许多位协作者安全地叠加意见，而无需重新创建或破坏该 prim 的类型／身份。 |

---


### 第 6 章记忆卡：面向聚合的 Component 与 Assembly 资产设计


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `flashcards/chapter-06-flashcards.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/flashcards/chapter-06-flashcards.md) · 语言：英文原文 · 中译版



## 第 6 章：面向聚合的 Component 与 Assembly 资产设计——记忆卡

| # | 正面（问题） | 背面（答案） |
|---|-----------------|---------------|
| 1 | USD 默认 kind 注册表中有多少种基础 Kind 取值？ | 4 种 —— component、group、assembly、subcomponent。应试提示：assembly 是 group 的子类型；component 与 subcomponent 分别是非 group 模型／非模型 kind。 |
| 2 | 每个 USD 层允许声明多少个 defaultPrim？ | 恰好 1 个。可被 reference／payload 的层需要一个 defaultPrim，才能在不指定显式路径的情况下被引用。应试提示：缺少 defaultPrim 会导致不带路径的 reference 解析为空。 |
| 3 | Reference 与 Payload 的关键区别（聚合场景下）？ | 两者都会组合外部层，但 payload 数据默认不加载（在调用 Stage.Load() 之前被排除），而 reference 数据会立即加载。应试提示：大型 assembly 内的重型 component 资产用 payload。 |
| 4 | Component（原子）资产与 Assembly 资产有何不同？ | Component = 自包含的叶子资产，不含嵌套的模型子级。Assembly = 对许多 component／group reference 的 group kind 聚合。应试提示：component 不能包含更多 'model' kind 子级；assembly 可以嵌套很多。 |
| 5 | Subcomponent 与 Component kind 的区别？ | Component 是模型 kind（可独立引用的顶层资产）。Subcomponent 是非模型 kind，标记有意义的内部部件（例如汽车里的车门），它并不独立发布。应试提示：基于模型的遍历中，subcomponent 不计入 'model'。 |
| 6 | Asset Interface 层模式的目的？ | 提供一个稳定的顶层层（例如 Asset.usd），暴露一致的结构（defaultPrim、variantSets），同时隐藏内部的 geom／payload／material 层。应试提示：使用方只应引用接口层，绝不直接引用内部文件。 |
| 7 | Assembly 在聚合许多外部厂商来源时如何避免命名空间冲突？ | 每个被引用的 component 都嵌套在 assembly 下各自唯一命名的子 prim／scope 之下，而不是平铺合并到同一路径。应试提示：reference 弧在组合时会重新生根命名空间 —— 只有在不做唯一父 scope 就展平时才会产生冲突。 |
| 8 | 为什么要把内部资产结构封装在接口层之后？ | 即使内部文件布局（geom.usd、mtl.usd、payload.usd）发生变化，也不会破坏下游；使用方只依赖稳定的接口。应试提示：直接引用内部文件（「伸手进去」）是被考查的反模式。 |
| 9 | 用哪个 USD 元数据字段声明资产的 Kind？ | prim 上的 'kind' 元数据字段，例如 kind = "component"。应试提示：可直接在 .usda 中创作，或通过 UsdModelAPI.SetKind() 以编程方式设置。 |
| 10 | stage 已打开后加载 payload 的 Python API 调用？ | stage.Load(primPath)（或 GetPrimAtPath(path).Load()）。应试提示：除非 load 规则另有指定，stage 打开时 payload 默认处于未加载状态。 |
| 11 | Assembly 内部使用 payload 有助于哪些加载管理？ | 重型的 component 子级通过 payload 弧（而非普通 reference）引入，因此包含数百个 component 的场景也能快速打开；单个 component 按需加载。应试提示：reference = 始终加载；payload = 按需加载，对大型聚合至关重要。 |
| 12 | Reference 可以指向没有 defaultPrim 的层吗？ | 可以，但前提是该 reference 弧总是指定显式的目标 prim 路径。应试提示：defaultPrim 是给不带路径的 reference 提供的便利机制，并非硬性要求——只要调用方总是指定显式路径即可。 |

---


### 第 7 章记忆卡：原生（原型）实例化与点实例化


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `flashcards/chapter-07-flashcards.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/flashcards/chapter-07-flashcards.md) · 语言：英文原文 · 中译版



## 第 7 章：原生（原型）实例化与点实例化——记忆卡

| # | 正面（问题） | 背面（答案） |
|---|-----------------|---------------|
| 1 | 用哪个 USD 元数据字段为 prim 启用原生（原型）实例化？ | `instanceable = true`。应试提示：它是元数据而不是 schema 属性 —— 要看层的元数据块，而不是属性列表。 |
| 2 | 能否直接在实例代理（instance proxy）路径上创作新的材质绑定？ | 不能。实例代理用于检查／有限的覆盖；在其上创作新的 relationship／property 会报错。应试陷阱：学生会这么尝试，并把它当作「正确」答案。 |
| 3 | 如何只给某一个 instanceable prim 施加真正唯一的覆盖，而不影响共享同一原型的兄弟节点？ | 只在该 prim 上设置 instanceable=false，使其成为自己的原型，然后直接在其上创作覆盖。这样只打破该实例的共享。 |
| 4 | UsdGeomPointInstancer：用哪个属性把每个实例映射到要绘制的原型 prim？ | protoIndices（int[]）—— 每个条目索引到 `prototypes` relationship 中。 |
| 5 | UsdGeomPointInstancer：列出候选原型 prim 的 relationship？ | rel prototypes |
| 6 | PointInstancer.orientations 使用什么数据类型？ | quath[] —— 半精度四元数，在实例数量巨大时为节省内存而选用。 |
| 7 | 如何在不干扰其他数组的前提下永久隐藏 PointInstancer 中特定的实例 id？ | 创作 `invisibleIds` 属性并列出那些实例 id。不要用 scale=0 或 protoIndices=-1 这种取巧做法。 |
| 8 | 原生实例化与点实例化 —— 该如何选择？ | 原生实例化：实例数量较少（几十到几百／低千），需要逐个选择／编辑／按实例切换 variant。点实例化：数量巨大（数千到数百万），基于数组的变换，不需要逐实例的场景图编辑。 |
| 9 | USD 中的「实例代理」是什么？ | 一个合成的、非共享的路径（例如 /World/.../__Prototype_1/... 之下），表示某一个具体实例的组合结果，用于拾取／检查和有限的覆盖 —— 不适合任意创作。 |
| 10 | PointInstancer 中逐实例位置的属性？ | positions（point3f[]） |
| 11 | PointInstancer 中逐实例非均匀缩放的属性？ | scales（float3[]） |
| 12 | 为什么直接编辑共享的 PROTOTYPE prim 会影响所有实例？ | 原型是所有 instanceable prim 所引用的唯一组合源；在那里做的任何编辑都会传播到共享它的每一个实例。应试陷阱：当只有一个实例应当改变时，却选择「编辑原型」。 |

---


### 第 8 章记忆卡：文件格式、USDZ 打包与资产解析


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `flashcards/chapter-08-flashcards.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/flashcards/chapter-08-flashcards.md) · 语言：英文原文 · 中译版



## 第 8 章：文件格式、USDZ 打包与资产解析——记忆卡

| # | 正面（问题） | 背面（答案） |
|---|-----------------|---------------|
| 1 | 哪种 USD 文件格式是基于 ASCII 文本、人类可读的？ | .usda —— 人类可读的文本层，文件更大，可用任意文本编辑器编辑。应试提示：用于调试／手工创作，不用于运行时交付。 |
| 2 | 哪种 USD 文件格式是二进制并针对加载速度优化的？ | .usdc（Crate 二进制）—— 紧凑、解析快、不可读。应试提示：制作场景与管线的默认选择。 |
| 3 | 通用的 .usd 扩展名代表什么？ | 与格式无关 —— 文件内容可能是 ASCII（.usda），也可能是二进制 Crate（.usdc）；USD 通过检查文件头来判断实际格式。应试提示：永远不要以为 .usd = 文本。 |
| 4 | USDZ 包内的文件必须使用哪种压缩方式？ | Store（不压缩）—— zip 条目绝不能使用 deflate。应试提示：这样才能直接内存映射归档内容以提升性能。 |
| 5 | 打包进 USDZ 归档的文件有什么对齐要求？ | 64 字节对齐。应试提示：这是必需的，这样二进制 Crate 数据才能直接内存映射而无需拷贝。 |
| 6 | USDZ 包能否引用归档之外的文件？ | 不能 —— USDZ 必须完全自包含；所有被引用的资产（贴图、sublayer）都必须放在 zip 内部并使用相对路径。应试提示：绝对／外部引用会破坏可移植性，属于不被允许的做法。 |
| 7 | 相对资产路径与锚定（绝对）路径 —— 哪个在不同机器／管线之间更具可移植性？ | 相对路径 —— 相对于引用它的层来解析。应试提示：锚定／绝对路径在包或场景被移动到另一台机器时就会失效。 |
| 8 | 在 USD 中，哪个组件把资产路径（相对路径／搜索路径）解析为实际文件位置？ | AssetResolver（Ar 插件，ArResolver 接口）。应试提示：管线会实现自定义 resolver 来处理版本管理／搜索路径逻辑。 |
| 9 | 从 DCC 工具（例如 Maya、Houdini）导出到 USD 总是无损的吗？ | 不是 —— 往往有损。没有直接 USD schema 映射的自定义节点类型／属性可能被丢弃或近似处理。应试提示：把 DCC 到 USD 的转换当作无损之前，先确认 schema 覆盖率。 |
| 10 | USDZ 包中的哪个文件必须排在 zip 文件列表的第一位？ | 默认根层（通常是 .usdc 文件）—— 必须是归档中的第一个条目。应试提示：不保留条目顺序的重打包工具可能破坏 AR 查看器。 |
| 11 | USDZ 包中允许加密吗？ | 不允许 —— USDZ 的 zip 条目不得加密。应试提示：加密会破坏内存映射要求以及查看器兼容性。 |
| 12 | 对于纳入版本控制的小型配置／覆盖层，手工编辑的最佳格式选择？ | .usda —— 便于 diff、人类可读。应试提示：把 .usda 覆盖层与在其下被引用的、更重的 .usdc payload 层配对使用。 |

---


### 第 9 章记忆卡：用 Python 中的 Usd、Sdf、Gf、Vt 创作 Stage


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `flashcards/chapter-09-flashcards.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/flashcards/chapter-09-flashcards.md) · 语言：英文原文 · 中译版



## 第 9 章：用 Python 中的 Usd、Sdf、Gf、Vt 创作 Stage——记忆卡

| # | 正面（问题） | 背面（答案） |
|---|-----------------|---------------|
| 1 | Usd.Stage.CreateNew() 与 Usd.Stage.Open() 的关键区别？ | CreateNew() 创建一个全新的根层文件，覆盖该路径上的任何已有文件。Open() 加载已有文件而不修改它。应试提示：在已有路径上调用 CreateNew() 会悄然清空它。 |
| 2 | UsdGeom.Sphere.Define(stage, path) 的返回类型？ | 一个 UsdGeom.Sphere 类型化 schema 对象，带有 GetRadiusAttr() 等便捷访问器；底层 prim 的 typeName 被设为 'Sphere'。应试提示：类型化 Define() 一次调用同时设置 typeName 并返回包装对象。 |
| 3 | Sdf.Path 语法：子 prim 与 prim 上的属性？ | '/World/Cube' = 子 prim（斜杠分隔）。'/World/Cube.size' = prim 上的属性／property（点号分隔）。应试提示：点号始终表示命名空间 property，绝不表示子 prim。 |
| 4 | Stage.DefinePrim(path, typeName) 与 UsdGeom.Xform.Define(stage, path)？ | DefinePrim() 是通用的 —— 返回普通的 Usd.Prim；你必须手动创建／获取属性。Define() 既设置 typeName，又返回带内置访问器的类型化 schema 对象。应试提示：对于已知 schema，考试倾向把类型化 Define() 作为最佳实践。 |
| 5 | 如何用 Attribute API 创作带时间采样的数值？ | attr.Set(value, timeCode) —— 例如 attr.Set(5.0, 24)。省略时间参数则创作默认值（Usd.TimeCode.Default()）。应试提示：单独的 Set(value) ≠ 时间采样。 |
| 6 | Vt.Array 在 USD 中的用途？ | 一种带类型的、写时复制的数组容器（例如 Vt.Vec3fArray、Vt.FloatArray），是 points、normals、faceVertexIndices 等数组值属性所必需的。应试提示：Python 列表会自动转换，但存储类型始终是 Vt.Array。 |
| 7 | Gf.Vec3f 与 Gf.Vec3d —— 考试何时考查这一点？ | Vec3f = 单精度，用于点／法线／速度。Vec3d = 双精度，变换数学内部使用。应试提示：xformOp:transform 始终需要 Gf.Matrix4d，绝不用 Matrix4f。 |
| 8 | xformOp:transform 属性所需的值类型？ | 仅 Gf.Matrix4d —— UsdGeom 变换算子统一使用双精度 4x4 矩阵。应试提示：传入 Matrix4f 会导致类型不匹配错误。 |
| 9 | 如何用通用的 DefinePrim() 在 prim 上手动创建属性？ | prim.CreateAttribute('radius', Sdf.ValueTypeNames.Float) 然后 attr.Set(1.0)。之所以需要，是因为通用的 DefinePrim() 没有类型化访问器。应试提示：Sdf.ValueTypeNames 枚举了所有合法的属性值类型。 |
| 10 | 何时使用 Usd.Stage.CreateInMemory()？ | 创建一个匿名的内存 stage，磁盘上没有后端文件 —— 适用于不需要磁盘 I/O 的脚本／测试。应试提示：它不同于 CreateNew()，后者总是写入真实的文件路径。 |
| 11 | 创作 relationship 与创作 attribute —— API 区别？ | prim.CreateRelationship(name).SetTargets([path1, path2]) 指向其他 prim／属性（无值类型）。prim.CreateAttribute(name, type).Set(value) 存储带类型的数据。应试提示：relationship 存储 Sdf.Path 目标，而不是数值。 |
| 12 | 如果对早于第一个已创作时间采样的时间查询 attr.Get(time)，返回什么值？ | 最早已创作时间采样的数值（USD 在两端保持／钳制）—— 只要存在时间采样，就不会回退到默认值。应试提示：只有在查询 Usd.TimeCode.Default() 时才返回默认值。 |

---


### 第 10 章记忆卡：Stage 遍历、以编程方式编辑组合与 Hydra 基础


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `flashcards/chapter-10-flashcards.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/flashcards/chapter-10-flashcards.md) · 语言：英文原文 · 中译版



## 第 10 章：Stage 遍历、以编程方式编辑组合与 Hydra 基础——记忆卡

| # | 正面（问题） | 背面（答案） |
|---|-----------------|---------------|
| 1 | Usd.PrimRange.PruneChildren() 做什么？ | 阻止迭代器下钻到当前 prim 的子级 —— 必须在访问该 prim 时调用，而不是事后调用。应试提示：剪枝是按次迭代生效的，而不是预先过滤。 |
| 2 | 无参数调用 stage.Traverse() 时的默认谓词？ | UsdPrimDefaultPredicate = IsActive && IsDefined && IsLoaded && !IsAbstract。应试提示：非活动 prim 和仅含 'over' 的未定义 prim 会被静默跳过。 |
| 3 | 如何在遍历中包含实例化原型的内容？ | Usd.PrimRange(root, Usd.TraverseInstanceProxies()) —— 会就地呈现实例代理。应试提示：实例代理是只读替身，不能直接编辑。 |
| 4 | 给 prim 添加 reference 的 Python 调用？ | prim.GetReferences().AddReference(assetPath, primPath="")。应试提示：与 payload 是不同的弧类型 —— 总是参与组合，没有延迟加载。 |
| 5 | 给 prim 添加 payload 的 Python 调用？ | prim.GetPayloads().AddPayload(assetPath, primPath="")。应试提示：payload 支持显式加载／卸载以提升性能；reference 不支持。 |
| 6 | References 与 Payloads —— 考试中的关键区别？ | Reference 总是随 stage 组合进来；payload 可以通过 stage.Load()/Unload() 按需排除／加载，以优化大型场景的性能。 |
| 7 | 用代码创建并选择 variant 的步骤？ | vs = prim.GetVariantSets().AddVariantSet(name); vs.AddVariant(variantName); vs.SetVariantSelection(variantName)。应试提示：该选择本身就是一条已创作的意见，受当前 EditTarget 影响。 |
| 8 | 如何把之后的创作调用重定向到特定层？ | stage.SetEditTarget(Usd.EditTarget(layer))，其中 layer 必须已经属于该 stage 的层栈。应试提示：事后忘记把 EditTarget 重置回根层是常见 bug。 |
| 9 | 检查某个 prim 的胜出意见来自哪种弧的 API？ | Usd.PrimCompositionQuery(prim).GetCompositionArcs() —— 返回带弧类型、层和路径的 UsdCompositionArc 对象。应试提示：这是为此专用的 API，比手动解析 PrimStack 更好。 |
| 10 | Hydra scene delegate 的作用？ | 把 USD（或其他场景）数据转换为 Hydra 的渲染索引（HdRenderIndex），供 render delegate 消费。应试提示：scene delegate 只读，绝不回写 USD。 |
| 11 | Hydra render delegate 的作用？ | 消费渲染索引并产出渲染图像（例如 Storm、Arnold、Karma）。应试提示：Hydra 整体只用于渲染 —— 没有回写到 USD stage 的创作路径。 |
| 12 | GetVariantSets() 上的 GetVariantSet() 与 AddVariantSet()？ | GetVariantSet(name) 获取已有 set 的句柄而不创作它；AddVariantSet(name) 才会真正创作该 variantSet 的存在性 spec。应试提示：选择一个从未 AddVariantSet()／AddVariant() 过的 variant 将无法解析。 |

---


### 第 11 章 记忆卡片


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `flashcards/chapter-11-flashcards.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/flashcards/chapter-11-flashcards.md) · 语言：英文原文 · 中译版



## 第 11 章：使用 usdview 调试组合（Composition）与大规模场景优化 —— 记忆卡片

| # | 正面（问题） | 背面（答案） |
|---|-----------------|---------------|
| 1 | UsdGeomImageable 上有哪四个 purpose 值？ | default、render、proxy、guide。考试提示：render = 仅用于最终品质；proxy = 轻量级交互替身（渲染时隐藏）；guide = 交互辅助几何体（渲染时处处隐藏）；default = 继承父级行为。 |
| 2 | LIVRPS 组合强度顺序（由强到弱）？ | Local、Inherits、Variants、References、Payloads、Specializes。考试提示：用 'Little Interns Value Real Paychecks Sometimes' 来记忆。 |
| 3 | 校验 USDZ 资产是否符合 ARKit 规范的命令？ | usdchecker --arkit asset.usdz —— 检查 Apple AR 交付所要求的纹理格式、文件大小和结构规则。 |
| 4 | 如何在 usdview 中以交互方式卸载/加载 payload？ | 在 Prim Browser 中右键点击该 prim，选择 Load 或 Unload；也可以使用 Stage 菜单中的 'Load/Unload All Payloads'。 |
| 5 | 哪个 purpose 会在最终渲染中隐藏几何体，但保留其可见性以作为快速交互替身？ | proxy —— 在布局/动画工作中用于重型渲染几何体的简化表示。 |
| 6 | 哪个 purpose 用于不可渲染的辅助几何体，例如绑定控制器和定位器？ | guide —— 交互时可见，在 proxy 和 render 两种 purpose 遍历中都被排除。 |
| 7 | 在 prim 上设置 instanceable=true 能达到什么效果？ | 在 Pcp 中把相同的 prim 归组到共享的已组合原型下，使几何体/组合只计算和存储一次，而不是每个实例各算一次 —— 这是主要的规模化优化工具。 |
| 8 | usdview 中哪个面板会显示是哪个 layer/arc 为某个属性贡献了胜出的 opinion？ | Composition 选项卡的 Index 视图 —— 点击某个 arc 条目即可查看其来源 layer 和 LIVRPS 位置。 |
| 9 | 对于超大场景（数万个资产），主要的性能杠杆是什么？ | Payload 加载管理 —— 让远处/被遮挡/不需要的分支保持未加载状态，直到确有需要时再加载。 |
| 10 | reference arc 与 payload arc 有什么区别？ | Reference 总是会被组合进 stage；Payload 在被显式加载之前不参与组合。这种延迟加载行为正是 payload 的定义性特征。 |
| 11 | 在 usdview 的哪里可以检查某个属性在所有贡献 layer 中被创作的值？ | Property 面板的 value/metadata 视图，配合 Layer Stack 选项卡使用，后者会按强度顺序列出所有贡献 opinion 的 layer。 |
| 12 | 什么取代了临时脚本检查，成为可插拔、结构化的 USD 场景校验方案？ | UsdValidator / ValidationContext 框架 —— 一套基于插件的校验系统，可在 usdchecker 之外补充自定义、可注册的校验器。 |

---


### 第 12 章 记忆卡片


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `flashcards/chapter-12-flashcards.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/flashcards/chapter-12-flashcards.md) · 语言：英文原文 · 中译版



## 第 12 章：全真模拟考试与时间管理策略 —— 记忆卡片

| # | 正面（问题） | 背面（答案） |
|---|-----------------|---------------|
| 1 | LIVRPS 强度顺序（由强到弱）？ | Local、Inherits、VariantSets、References、Payloads、Specializes。考试提示：更强 arc 的 opinion 总是胜出，无论它是在较弱 arc 内部的哪个位置创作的。 |
| 2 | NCP-OUSD 考试形式：题目数量和时间限制？ | 约 60-70 题，90 分钟窗口。考试提示：根据你为复查预留多少缓冲，按每题约 1.15-1.4 分钟来安排时间。 |
| 3 | 带复查缓冲时，每题时间预算的公式？ | (总分钟数 − 复查缓冲) ÷ 题目数量。示例：(90-15)/65 ≈ 每题 1.15 分钟（约 69 秒）。 |
| 4 | Reference 与 Payload —— 关键的行为差异？ | 两者都像外部 arc 一样参与组合，但 Payload 默认不会加载，并且可以在运行时显式加载/卸载；Reference 总是加载。考试提示：Payload = 对沉重子树的性能控制手段。 |
| 5 | 哪种 UsdGeom schema 为大规模散布创作逐实例的位置/朝向/缩放/原型数组？ | UsdGeomPointInstancer —— 属性包括：positions、orientations、scales、protoIndices，以及一个 prototypes 关系。 |
| 6 | 如何把大量 Sdf 层的编辑批量处理，以避免每次编辑都触发重新组合通知？ | 在这些编辑外层使用 `with Sdf.ChangeBlock():`。考试提示：可避免每次创作调用都触发昂贵的通知/重新组合。 |
| 7 | 把 prim 标记为 instanceable 的正确 Python 调用？ | `prim.SetInstanceable(True)` —— 接受一个 Python 布尔值，调用对象是 Usd.Prim 而不是 Usd.Stage。 |
| 8 | 在被引用的资产中做出的 variant 选择，下游能否覆盖？ | 可以 —— 针对同一个 variantSet 选择的更强 layer opinion 总会覆盖被引用的默认值，遵循标准的 LIVRPS/opinion 强度规则。 |
| 9 | instanceable=true 的 reference 在逐实例覆盖方面有什么限制？ | Instanceable 的 prim 共享同一个原型；在实例根之下创作有分歧的逐实例覆盖（例如唯一的材质绑定）会破坏共享或使其实例化失效。考试提示：当需要逐实例唯一性时，请使用 PointInstancer 或实例级组合。 |
| 10 | 标记并回看策略 —— 应该标记多少道题？ | 第一遍作答时，标记的题目应不超过约 10-15%；标记绝大多数题目会破坏限时策略，也会导致复查时间不足。 |
| 11 | NVIDIA 远程监考当天的后勤要点有哪些？ | 核验有效的带照片身份证件、通过摄像头实时扫描房间以确认桌面整洁、不得有笔记/第二台显示器/手机、考试界面可导航返回已标记的题目。考试提示：在预定开始时间之前确认这些要求，避免延误侵蚀你的 90 分钟。 |
| 12 | 面对看似合理的干扰项，采用什么排除技巧？ | 立即剔除涉及已废弃/错误 schema 模式的选项，以及只解决场景部分问题的选项；先缩小到 2 个候选，再重新阅读场景约束。考试提示：在最后复查阶段，不要反复怀疑一个你有把握的排除结论。 |

---



## 易混考点


### 第 1 天 — USD 基础


> 来源：`sparsha-2011/physical-ai-learning-journey` · `02-openUSD-cert/notes/day-01-usd-foundations.md` · [原文链接](https://github.com/sparsha-2011/physical-ai-learning-journey/blob/main/02-openUSD-cert/notes/day-01-usd-foundations.md) · 语言：英文原文 · 中译版



# 第 1 天 — USD 基础


> **OpenUSD NCP 认证学习笔记**  
> _通用场景描述 — 核心架构_

---

## 目录


1. [三大核心库](#the-three-core-libraries)
2. [Stage（阶段）](#the-stage)
3. [Layer（层）](#layers)
4. [Prim（图元）— 场景图](#prims-the-scene-graph)
5. [属性 — Attribute 与 Relationship](#properties-attributes-and-relationships)
6. [SdfPath — 寻址场景](#sdfpath-addressing-the-scene)
7. [USD 文件格式](#usd-file-formats)
8. [元数据](#metadata)
9. [时间采样与动画](#time-samples-and-animation)
10. [三大核心库 — Gf、Sdf 与 Usd](#the-three-core-libraries-gf-sdf-and-usd)
11. [关键要点](#key-takeaways)

---

<a id="the-three-core-libraries"></a>

## 0. 三大核心库


每个 USD Python 脚本都以 `from pxr import ...` 开头。弄清楚每个库各自负责什么，就能避免在阅读 API 文档时产生混淆。

| 库 | 全称 | 职责 | 了解的内容 |
| ---------- | -------------------------------- | ------------------------------------------------------------------------------------------- | --------------------------------------------- |
| `Usd` | **Universal Scene Description**（通用场景描述） | 合成后的场景 —— 打开 Stage、遍历 Prim、在所有 arc 解析完毕后读取最终生效的值 | 全部内容 —— 合成、arc、layer、类型 |
| `Sdf` | **Scene Description Foundation**（场景描述基础） | 原始 layer 数据 —— 单个文件的意见，不做任何合成 | 一次只处理一个 layer，不解析 arc |
| `Gf` | **Graphics Foundational**（图形基础） | 仅包含数学类型 —— 向量、矩阵、四元数 | 与 USD 场景毫无关系 |
| `Vt` | **Value Types**（值类型） | 用于批量几何数据的数组容器 | 与 Gf 协同使用 |
| `UsdGeom` | **USD Geometry schemas**（USD 几何模式） | 面向网格、相机、xform、灯光的类型化模式 | 构建在 Usd 之上 |
| `UsdShade` | **USD Shading schemas**（USD 着色模式） | 材质、着色器、着色器网络 | 构建在 Usd 之上 |
| `UsdLux` | **USD Lighting schemas**（USD 光照模式） | 光源相关的模式 | 构建在 Usd 之上 |
| `UsdUtils` | **USD Utilities**（USD 工具集） | 辅助函数 —— 扁平化、复制 layer、校验 | 构建在 Usd 与 Sdf 之上 |

---

<a id="the-stage"></a>

## 1. Stage（阶段）


**Stage**（`Usd.Stage`）是表示整个 3D 场景的顶层内存容器。渲染器、视口以及各类工具都作用于它。所有的东西 —— 几何体、灯光、相机、材质 —— 都通过 Stage 来访问。

> **核心概念：** Stage _不是_ 文件。它是由一个或多个 **Layer** 组装而成的、活的内存合成结果。当你打开一个 USD 文件时，USD 会读取它、解析所有引用，并在内存中组装出一个合成后的 Stage。

```
                ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
                │ lighting.   │  │ layout.     │  │ models.     │
                │ usda        │  │ usda        │  │ usda        │
                └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
                       │                │                  │
                       └────────────────┴──────────────────┘
                                        │
                                        ▼
                             ┌──────────────────────┐
                             │   COMPOSED STAGE     │
                             │  (in-memory view)    │
                             └──────────────────────┘
```

### Python API —— `Usd.Stage`


```python
from pxr import Usd

# Create a new stage backed by a real file on disk
# The file is created immediately even before any content is added
stage = Usd.Stage.CreateNew("my_scene.usda")

# Open an existing USD file
# USD loads the file and all files it transitively references
stage = Usd.Stage.Open("my_scene.usda")

# Create an in-memory stage with no file backing
# Use for testing, temporary work, or before deciding on output path
stage = Usd.Stage.CreateInMemory()

# Save all changes back to the backing file(s)
stage.Save()

# Export the stage to a new path (optionally converting format)
# stage.Export() flattens ALL composition into a single layer
stage.Export("output.usdc")

# Inspect the stage as USDA text — invaluable for debugging
print(stage.ExportToString(addSourceFileComment=False))
```

| 方法 | 行为 |
| ------------------ | -------------------------------------------------------- |
| `CreateNew(path)` | 立即在磁盘上创建文件，返回可写的 stage |
| `Open(path)` | 打开已有文件，装配所有被引用的 layer |
| `CreateInMemory()` | 不落盘，全部驻留在 RAM 中 |
| `Save()` | 将被修改过的 layer 写回各自对应的文件 |
| `Export(path)` | 扁平化并写入 `path` 指定的新文件 |

---

<a id="layers"></a>

## 2. Layer（层）


**Layer**（`Sdf.Layer`）是包含场景描述的单个 USD 文件 —— 或内存缓冲区。它是存储的物理单元。Stage 由 layer 组装而成；真正存在于磁盘上的是 layer。

### Layer 栈


每个 Stage 都有一个 **root layer（根层）** 以及零个或多个 **sublayer（子层）**。sublayer 在根层的元数据中声明，并按顺序加载。顺序很重要 —— 越靠前的 sublayer **强度越高**（发生冲突时它们的意见胜出）。

```usda
#usda 1.0
(
    subLayers = [
        @./anim.usda@,       # strongest — loaded first
        @./layout.usda@,
        @./model.usda@       # weakest — loaded last
    ]
)
```

### Python API —— `Sdf.Layer`


```python
from pxr import Sdf, Usd

# Find a layer that is already loaded (by its identifier/path)
layer = Sdf.Layer.FindOrOpen("model.usda")

# Access the root layer of a stage
root_layer = stage.GetRootLayer()

# Access the session layer (in-memory, ephemeral, always strongest)
session_layer = stage.GetSessionLayer()

# Inspect all layers in the root layer stack, strongest → weakest
for layer in stage.GetLayerStack():
    print(layer.identifier)

# Add a sublayer programmatically
root_layer.subLayerPaths.append("./new_layer.usda")

# Read and write layer-level metadata
root_layer.customLayerData = {
    "pipeline:schemaVersion": "2.0",
    "pipeline:studio":        "AcmeStudios",
}
```

> **Session layer（会话层）** 是一个特殊的内存 layer，始终拥有最高强度。它记录交互式编辑（例如来自 usdview 的编辑）。`stage.Save()` **绝不会**把它保存到磁盘。请把它用于临时的、针对单次会话的覆盖值。

---

<a id="prims-the-scene-graph"></a>

## 3. Prim（图元）— 场景图


**Prim**（Primitive，图元）是场景图中的每一个独立节点。每一个网格、灯光、相机、材质，或空白的组织用容器，都是一个 prim。场景图就是一棵由 prim 构成的树。

```
/                             ← pseudo-root (always exists, invisible)
└── World  (Xform)            ← organising container
    ├── Geometry  (Scope)     ← namespace grouping (no transform)
    │   ├── Chair  (Mesh)     ← polygon geometry
    │   └── Table  (Mesh)
    ├── Lights  (Scope)
    │   └── KeyLight  (DistantLight)
    └── Materials  (Scope)
        └── WoodMat  (Material)
```

### Prim 说明符（Specifier）


USDA 文件中的每个 prim 都以三个 **specifier 关键字** 之一开头。理解它们是理解合成机制的基础。

| Specifier | 含义 | 使用场景 |
| --------- | ----------------------------------------------------------------------------- | ------------------------------------- |
| `def` | **Define（定义）** —— 创建一个新 prim 并完全拥有它 | 创作新内容 |
| `over` | **Override（覆盖）** —— 在_已有_ prim 上添加意见，但不取得所有权 | 在更强势的 layer 中覆盖数值 |
| `class` | **Class（类）** —— 抽象的模板 prim，绝不会被直接渲染 | 与 `inherits` arc 配合使用 |

```usda
# model.usda — defines the prim (weaker layer)
def Xform "Chair" {
    double3 xformOp:translate = (0, 0, 0)
}

# anim.usda — overrides the prim (stronger layer)
over "Chair" {
    # No type declaration — over doesn't claim ownership
    double3 xformOp:translate = (5, 0, 0)   # this wins
}
# Composed result: Chair is at (5, 0, 0)
```

> **重要提示：** 如果整个 layer 栈中都没有对应的 `def`，那么 `over` 不会产生任何效果，它会悄无声息地合成为空。这是“为什么我的改动没生效？”这类调试场景的常见原因。

### Python API —— `Usd.Prim`


```python
from pxr import Usd, UsdGeom

stage = Usd.Stage.CreateInMemory()

# Define a prim using the generic API
# Signature: stage.DefinePrim(path: str, typeName: str = "") -> Usd.Prim
chair = stage.DefinePrim("/World/Chair", "Xform")
# Produces: def Xform "Chair" { }

# Define a prim using the schema-specific API (preferred)
# This gives type-safe access to schema attributes
sphere = UsdGeom.Sphere.Define(stage, "/World/Ball")
sphere.GetRadiusAttr().Set(5.0)

# Retrieve a prim by path
prim = stage.GetPrimAtPath("/World/Chair")
# Returns an invalid prim (evaluates to False) if path does not exist
if not prim:
    print("Prim not found")

# Inspect prim properties
print(prim.GetPath())       # Sdf.Path("/World/Chair")
print(prim.GetTypeName())   # "Xform"
print(prim.IsValid())       # True
print(prim.IsDefined())     # True if at least one 'def' spec exists
print(prim.IsActive())      # True unless deactivated

# Navigate the hierarchy
for child in prim.GetChildren():
    print(child.GetPath())

# Type checking
print(prim.IsA(UsdGeom.Xform))     # True
print(prim.HasAPI(UsdGeom.MotionAPI)) # True/False
```

### 常见的 Prim 类型


| 模式类型 | 模块 | 用途 |
| ------------------------------------------------------- | ---------- | ---------------------------------------------------------------- |
| `Xform` | `UsdGeom` | 变换节点 —— 对子节点分组，应用平移/旋转/缩放 |
| `Scope` | `UsdGeom` | 命名空间容器 —— 不含变换 |
| `Mesh` | `UsdGeom` | 多边形几何体 |
| `Sphere`、`Cube`、`Cylinder` | `UsdGeom` | 参数化几何体 |
| `Camera` | `UsdGeom` | 带镜头属性的相机 |
| `DistantLight`、`SphereLight`、`RectLight`、`DomeLight` | `UsdLux` | 光源 |
| `Material` | `UsdShade` | 着色网络容器 |
| `Shader` | `UsdShade` | 单个着色节点 |

---

<a id="properties-attributes-and-relationships"></a>

## 4. 属性 — Attribute 与 Relationship


属性是**存储在 prim 上的数据**。它们恰好分为两类：

### Attribute（属性值）


attribute 存储**带类型的值** —— 数字、向量、颜色、字符串、数组、矩阵，或任何其他受支持的类型。真正的 3D 数据都存放在这里。

关于 attribute 的关键要点：

- 可以承载**简单类型**（int、float、bool、string），也可以承载**复杂类型**（数组、矩阵、结构体）
- 支持**时间采样数据** —— 随时间变化、可用于动画的值
- 支持**回退值（fallback values）** —— 当不存在被创作（authored）的值时返回 schema 定义的默认值
- 是**可变的** —— 创建之后可以修改或删除，无需重新创建 prim

```usda
double   radius = 5.0
float    intensity = 1000.0
bool     doubleSided = false
token    visibility = "inherited"
double3  xformOp:translate = (0, 5, 0)
color3f  inputs:diffuseColor = (0.8, 0.2, 0.1)
color3f[] primvars:displayColor = [(1, 0, 0)]
int[]    faceVertexCounts = [4, 4, 4]
matrix4d xformOp:transform = ( (1,0,0,0), (0,1,0,0), (0,0,1,0), (0,0,0,1) )
```

### Relationship（关系）


relationship 存储**指向其他 prim 的路径** —— 不存放数据值，只有连接关系。

关于 relationship 的关键要点：

- 只存储 **prim 路径** —— 不是任意数据值，也不是数字或字符串
- 可以是**多目标（multi-target）** —— 单个 relationship 可同时指向多个 prim
- **没有回退值** —— 与 attribute 不同，relationship 没有 schema 默认值，因为它是引用而非数据容器
- 用于材质绑定、骨骼关节、灯光链接、约束目标

```usda
rel material:binding = </World/Materials/WoodMat>         # single target
rel proxyPrim        = </World/Geometry/LowResMesh>       # single target
rel skel:joints      = [</Rig/Hip>, </Rig/Spine>, </Rig/Head>]  # multi-target
```

```python
# Reading a relationship's targets
rel = prim.GetRelationship("material:binding")
targets = rel.GetTargets()       # list of Sdf.Path objects
# targets = [Sdf.Path("/World/Materials/WoodMat")]

# Multi-target relationship
rel.AddTarget("/World/Materials/MetalMat")   # now has two targets
rel.GetTargets()   # [Sdf.Path("/World/Materials/WoodMat"), Sdf.Path("/World/Materials/MetalMat")]
```

### Attribute 与 Relationship 对比


| 对比项 | Attribute | Relationship |
| ----------------------- | ------------------------------------------------- | -------------------------------------------- |
| 存储内容 | 带类型的值（数字、字符串、数组、矩阵） | 仅 prim 路径 |
| 支持时间采样 | ✅ 是 —— 动画的核心机制 | ❌ 否 |
| 回退值 | ✅ 是 —— schema 定义默认值 | ❌ 否 —— 没有数据可以回退 |
| 多值 | 通过 `T[]` 类型实现的数组 | ✅ 多目标（多个路径） |
| 可变性 | ✅ 是 | ✅ 是 |
| 常见用途 | 几何体、变换、颜色、动画 | 材质绑定、关节目标、约束 |
| 沿层级向下继承 | 通过 primvars | ❌ 否 |

> **考试陷阱 —— Relationship 与回退值：** 只有 attribute 支持回退值。Relationship 存储的是引用（路径）而非数据 —— 根本不存在可以回退的东西。如果题目说“relationship 支持回退值” → 立刻排除。

> **考试陷阱 —— Relationship 与数据：** Relationship 绝不存储数值或字符串数据值，它们只存储 prim 路径。如果题目说“relationship 可以像 attribute 一样存储任意数据” → 立刻排除。

### 值类型速查表


| USDA 类型 | Python/Gf 等价物 | 说明 |
| ---------- | -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `double`   | `float`              | 64 位浮点数                                                                                                                                                                                                           |
| `float`    | `float`              | 32 位浮点数                                                                                                                                                                                                           |
| `int`      | `int`                | 32 位整数                                                                                                                                                                                                         |
| `bool`     | `bool`               | 布尔值                                                                                                                                                                                                                |
| `token`    | `str`                | **驻留字符串（interned string）** —— 不可变，针对快速比较和重复使用做了优化。用于标识符和类枚举值（例如 `"inherited"`、`"invisible"`、`"render"`）。不适合存放大段或频繁变化的文本。 |
| `string`   | `str`                | 任意可变字符串 —— 用于大段或经常变化的文本值                                                                                                                                                           |
| `double3`  | `Gf.Vec3d`           | 3 分量 double 向量                                                                                                                                                                                              |
| `float3`   | `Gf.Vec3f`           | 3 分量 float 向量                                                                                                                                                                                               |
| `color3f`  | `Gf.Vec3f`           | RGB 颜色                                                                                                                                                                                                             |
| `matrix4d` | `Gf.Matrix4d`        | 4×4 双精度变换矩阵 —— **可以**进行时间采样并制作动画                                                                                                                                           |
| `asset`    | `Sdf.AssetPath`      | 文件路径引用                                                                                                                                                                                                    |
| `T[]`      | `Vt.Array`           | 任意类型 `T` 的数组                                                                                                                                                                                                  |

### Token 与 String 的关键区别


`token` 和 `string` 都是文本，但用途完全不同：

```
token:   immutable interned string
         → stored once in a global table, all uses share the same memory
         → extremely fast comparison (pointer comparison, not character-by-character)
         → used for: enum-like values ("inherited", "render", "catmullClark")
         → NOT for: large text, frequently changing values, arbitrary content
         → examples: visibility, purpose, subdivisionScheme, projection

string:  arbitrary mutable string
         → standard heap-allocated string
         → slower comparison, more memory per unique value
         → used for: file paths, asset IDs, descriptions, any large/changing text
         → examples: asset:description, pipeline:comment
```

```python
# token — for identifiers and enum-like values
mesh.GetSubdivisionSchemeAttr().Set(UsdGeom.Tokens.catmullClark)  # token
imageable.GetVisibilityAttr().Set(UsdGeom.Tokens.inherited)       # token

# string — for arbitrary text content
prim.CreateAttribute("asset:id", Sdf.ValueTypeNames.String).Set("CHAIR_001_v3")  # string
```

> **考试陷阱 —— Token 的可变性：** Token 是**不可变的** —— 无法就地修改，也不适合承载大块或频繁变化的数据。如果题目说“token 是可变的，用于存放经常变化的大段文本数据” → 立刻排除。

### Python API —— `Usd.Attribute`

```python
from pxr import Usd, UsdGeom, Sdf, Gf, Vt

stage  = Usd.Stage.CreateInMemory()
sphere = UsdGeom.Sphere.Define(stage, "/World/Ball")

# --- Reading attributes ---

# Get the Attribute object (does not return the value)
attr = sphere.GetRadiusAttr()

# Get the composed value (default time)
value = attr.Get()              # returns 1.0 (schema fallback)

# Get the value at a specific time code
value_at_t = attr.Get(time=24)  # returns value at frame 24

# Check if this value was explicitly authored (vs schema fallback)
attr.HasAuthoredValue()         # True = explicitly Set(), False = fallback

# --- Writing attributes ---

sphere.GetRadiusAttr().Set(5.0)

# Set at a specific time code (creates a time sample = animation keyframe)
sphere.GetRadiusAttr().Set(5.0,  time=1)
sphere.GetRadiusAttr().Set(10.0, time=24)

# --- Creating custom attributes ---
# Signature: prim.CreateAttribute(name, typeName, custom=True) -> Usd.Attribute
prim = sphere.GetPrim()
custom_attr = prim.CreateAttribute(
    "pipeline:assetId",
    Sdf.ValueTypeNames.String
)
custom_attr.Set("CHAIR_001_v3")

# --- Primvars ---
# Primvars inherit down the hierarchy and are used by renderers
from pxr import UsdGeom
primvar = UsdGeom.PrimvarsAPI(sphere.GetPrim()).CreatePrimvar(
    "displayColor",
    Sdf.ValueTypeNames.Color3fArray,
    UsdGeom.Tokens.constant
)
primvar.Set(Vt.Vec3fArray([Gf.Vec3f(1.0, 0.0, 0.0)]))  # red
```

---

<a id="sdfpath-addressing-the-scene"></a>

## 5. SdfPath —— 定位场景


USD 场景中的每个 prim 和属性都有一个唯一的 **路径（path）** —— 一个字符串地址，用于标识它在场景图中的位置。路径由 `Sdf.Path` 对象表示。

```
/World/Chair/seat_geo.primvars:displayColor
│            │         │
│            │         └─ property name (with namespace)
│            └─────────── prim name (child of Chair)
└──────────────────────── root prim
```

### 路径语法规则


| 规则                                       | 示例                                       |
| ------------------------------------------ | ------------------------------------------ |
| 始终以 `/` 开头                           | `/World/Chair`                             |
| prim 名称之间用 `/` 分隔                  | `/World/Geometry/Mesh`                     |
| 属性与 prim 之间用 `.` 分隔                | `/World/Chair.visibility`                  |
| 名称中的冒号 `:` 表示命名空间              | `xformOp:translate`、`inputs:diffuseColor` |
| 路径中任何位置都不能出现空格              | `/World/My_Chair` ✅ `/World/My Chair` ❌  |
| 区分大小写                                 | `/World/Chair` ≠ `/World/chair`            |

```python
from pxr import Sdf

# Construct paths
prim_path = Sdf.Path("/World/Chair")
prop_path = Sdf.Path("/World/Chair.xformOp:translate")

# Navigate relative to an existing path
parent  = prim_path.GetParentPath()     # /World
name    = prim_path.name                # "Chair"
is_prop = prop_path.IsPropertyPath()   # True

# Get a child path
child = prim_path.AppendChild("Armrest")  # /World/Chair/Armrest
```

---

<a id="usd-file-formats"></a>

## 6. USD 文件格式


USD 支持四种文件扩展名。选择正确的格式是必考内容。

| 扩展名    | 格式                 | 人类可读   | 速度     | 自包含   | 使用场景                                      |
| --------- | -------------------- | ---------- | -------- | -------- | --------------------------------------------- |
| `.usda`   | ASCII 文本           | ✅ 是      | 慢       | ❌ 否    | 创作、调试、版本控制                          |
| `.usdc`   | 二进制 crate         | ❌ 否      | 非常快   | ❌ 否    | 生产管线、大规模几何体                        |
| `.usd`    | 二者皆可（自动检测） | 视情况而定 | 视情况而定 | ❌ 否  | 通用 —— USD 在加载时自动检测格式              |
| `.usdz`   | Zip 压缩包           | ❌ 否      | 快       | ✅ 是    | 交付给外部合作方、AR/VR 分发                 |

### 关键区别


**`.usd`** 是一个**通用扩展名** —— USD 会在加载时检查文件头，判断它是 ASCII 还是二进制格式。把 `.usda` 文件重命名为 `.usd` 是合法的，USD 会正确处理。把 `.usda` 重命名为 `.usdc` 则**不合法** —— 两者的内部格式不同。

**`.usdz`** 是一个 **zip 压缩包**，其中打包了根 USD 文件及其所有依赖项（贴图、sublayer、被引用文件）。它：

- 是将资产交付给外部工作室时应使用的格式
- 是进行 AR/VR 分发时应使用的格式（Apple RealityKit、用于 web 的 USDZ）
- 是只读的 —— 你无法从 `.usdz` 内部引用外部文件

### 命令行工具


```bash
# Convert between .usda and .usdc (format determined by output extension)
usdcat scene.usda -o scene.usdc

# Flatten all composition arcs into a single file
usdcat --flatten scene.usda -o flat.usda

# Print the composition arc graph for all prims
usdcat --print-composition scene.usda

# Create a .usdz package (bundles all dependencies)
usdzip -r delivery.usdz scene.usda

# List contents of a .usdz without extracting
usdzip -l delivery.usdz

# Validate a USD file against best practices
usdchecker scene.usda
```

---

<a id="metadata"></a>

## 7. 元数据


元数据是场景级或 prim 级的配置数据，**存储在 layer 头部或 prim 头部** —— 与 prim 属性相互独立。它不会被渲染、不会被动画化，其合成方式也与属性不同。

### Stage 级元数据


```usda
#usda 1.0
(
    upAxis = "Y"               # Y-up coordinate system (industry standard)
    metersPerUnit = 0.01       # 1 unit = 1 centimetre
    timeCodesPerSecond = 24    # 24 fps animation
    startTimeCode = 1
    endTimeCode = 240
    defaultPrim = "World"      # which prim references should target by default

    subLayers = [
        @./anim.usda@,
        @./layout.usda@
    ]
)
```

### Python API —— Stage 元数据


```python
from pxr import Usd, UsdGeom

stage = Usd.Stage.CreateInMemory()

# Coordinate system
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)    # Y-up
UsdGeom.SetStageMetersPerUnit(stage, 0.01)          # 1 unit = 1 cm

# Read coordinate system
up_axis = UsdGeom.GetStageUpAxis(stage)             # UsdGeom.Tokens.y
mpu     = UsdGeom.GetStageMetersPerUnit(stage)      # 0.01

# Animation range
stage.SetMetadata("timeCodesPerSecond", 24)
stage.SetMetadata("startTimeCode", 1)
stage.SetMetadata("endTimeCode", 240)

# defaultPrim — critical for references to work correctly
root_prim = stage.DefinePrim("/World", "Xform")
stage.SetDefaultPrim(root_prim)
# Now any file that references this asset will target /World automatically

# Custom pipeline metadata
stage.GetRootLayer().customLayerData = {
    "pipeline:schemaVersion": "2.0",
    "pipeline:studio":        "AcmeStudios",
    "pipeline:exportTool":    "MayaExporter_v2",
}

# Read custom metadata
custom  = stage.GetRootLayer().customLayerData
version = custom.get("pipeline:schemaVersion", "unknown")
```

> **`defaultPrim`** 是最常考的元数据字段之一。当资产 A 引用资产 B 时，USD 需要知道应当引入 B 中的哪个 prim。如果 B 上没有设置 `defaultPrim`，引用就会失败。务必为每一个发布的资产把 `defaultPrim` 设置为其根 prim。

---

<a id="time-samples-and-animation"></a>

## 8. 时间采样与动画


USD 通过**时间采样（time samples）** 表示动画 —— 这是一个把时间码（帧号）映射到具体值的字典。一个属性可以具有：

- 一个**默认值（default value）** —— 不关联任何时间的单一值，当不存在时间采样、或者请求 `Usd.TimeCode.Default()` 时返回
- **时间采样（time samples）** —— 以时间码为键的多个值，以稀疏字典的形式存储

### 关于时间采样的关键事实


**稀疏采样是合法的** —— 时间采样并不需要在每一帧上都存在。你只需要在重要的时间点上创作关键帧，USD 会在它们之间自动插值。

```usda
# Sparse — only 3 keyframes over 48 frames. Frames 2-23, 25-47 are interpolated.
def Xform "Ball" {
    double3 xformOp:translate.timeSamples = {
        1:  (0, 0, 0),    ← keyframe at frame 1
        24: (5, 0, 0),    ← keyframe at frame 24 (frames 2-23 interpolated)
        48: (10, 0, 0)    ← keyframe at frame 48 (frames 25-47 interpolated)
    }
    uniform token[] xformOpOrder = ["xformOp:translate"]
}
```

**任何类型的属性都可以做时间采样** —— 不只是数值类型。字符串属性、token 属性、bool 属性以及 matrix4d 属性都可以拥有时间采样：

```python
# String attribute with time samples — valid
name_attr = prim.CreateAttribute("char:name", Sdf.ValueTypeNames.String)
name_attr.Set("idle",    time=1)    # string time sample
name_attr.Set("running", time=24)   # string changes at frame 24

# matrix4d with time samples — valid and common for transforms
xform_attr = prim.CreateAttribute("xformOp:transform", Sdf.ValueTypeNames.Matrix4d)
xform_attr.Set(Gf.Matrix4d(1), time=1)
xform_attr.Set(rotated_matrix,  time=24)
```

**更新之前不要清空全部采样** —— `attr.Set(value, time=n)` 会新增或更新那个特定的时间码，而不会影响其它采样。先清空所有已有采样、再设置新采样既低效又没有必要。

```python
# WRONG — clears everything then re-adds all samples
attr.Clear()                        # ← unnecessary, loses existing samples
attr.Set(Gf.Vec3d(5,0,0), time=24)

# CORRECT — just set the specific time code you want to update
attr.Set(Gf.Vec3d(5,0,0), time=24)  # ← adds/updates only frame 24
# All other existing time samples are untouched
```

USD 会在时间采样之间自动**插值**。在第 1 帧到第 24 帧之间，小球会从 `(0,0,0)` 线性插值到 `(5,0,0)`。

### Python API —— 时间采样


```python
from pxr import Usd, UsdGeom, Gf

stage = Usd.Stage.CreateInMemory()
stage.SetMetadata("timeCodesPerSecond", 24)
stage.SetMetadata("startTimeCode", 1)
stage.SetMetadata("endTimeCode", 48)

ball = UsdGeom.Sphere.Define(stage, "/World/Ball")
attr = ball.GetPrim().CreateAttribute(
    "xformOp:translate", Sdf.ValueTypeNames.Double3
)

# Author time samples by passing `time=` to Set()
attr.Set(Gf.Vec3d(0, 0, 0),  time=1)
attr.Set(Gf.Vec3d(5, 0, 0),  time=24)
attr.Set(Gf.Vec3d(10, 0, 0), time=48)

# Read value at a specific time
value = attr.Get(time=24)    # Gf.Vec3d(5, 0, 0)

# Read default value (no time association)
default = attr.Get()                        # None if only time samples exist
default = attr.Get(Usd.TimeCode.Default())  # equivalent

# Inspect all time samples
samples = attr.GetTimeSamples()   # [1.0, 24.0, 48.0]

# Check authoring status
attr.HasAuthoredValue()    # True if any value (default or time sample) was Set()

# GetPropertyStack — find which layers contributed opinions at time=24
# Signature: attr.GetPropertyStack(timeCode: Usd.TimeCode) -> list[SdfPropertySpec]
# Parameter is REQUIRED — there is no default argument
stack = attr.GetPropertyStack(Usd.TimeCode(24))
# Note: Usd.TimeCode.Default() ≠ Usd.TimeCode(0)
# TimeCode.Default() = "the plain authored default" (no time association)
# TimeCode(0)        = "the value at frame 0" (a real point in time)
# Shorthand: attr.GetPropertyStack(24) == attr.GetPropertyStack(Usd.TimeCode(24))
```

### `Usd.TimeCode` —— 关键区别


| 表达式                            | 含义                                                    |
| --------------------------------- | ------------------------------------------------------- |
| `Usd.TimeCode.Default()`          | 普通的创作默认值 —— 不关联时间                           |
| `Usd.TimeCode(24)` 或直接写 `24`  | 时间码 24（第 24 帧）处的值                              |
| `Usd.TimeCode(0)` 或直接写 `0`    | 时间码 0 处的值 —— **与 Default() 并不相同**             |

`TimeCode.Default()` 没有数字简写形式 —— 必须始终完整书写。

---

<a id="the-three-core-libraries-gf-sdf-and-usd"></a>

## 9. 三大核心库 —— Gf、Sdf 和 Usd


USD Python 代码的每一行都会用到三个基础库中的一个或多个。知道该调用哪个库，是熟练阅读和编写 USD 代码的第一步。

<div align="center">

<img src="assets/gf-sdf-usd-api-reference.svg" width="700" alt="Gf、Sdf 和 Usd API 参考 —— 按库划分的关键类与方法"/>
</div>

| 库     | 全称                                  | 职责                                          | 了解合成吗？                        |
| ------ | ------------------------------------- | --------------------------------------------- | ----------------------------------- |
| `Gf`   | **Graphics Foundational**（图形基础库） | 仅数学类型 —— 向量、矩阵、四元数              | 否 —— 纯数学                        |
| `Vt`   | **Value Types**（值类型）              | Gf 类型的大批量数组容器                      | 否 —— 纯数据容器                    |
| `Sdf`  | **Scene Description Foundation**（场景描述基础库） | 原始 layer 数据 —— 每次只看一个文件的意见 | 否 —— 仅限单个 layer                |
| `Usd`  | **Universal Scene Description**（通用场景描述） | 合成后的场景 —— 所有 arc 已解析，是最终结果 | 是 —— 这正是合成本身                |

---

### Gf —— Graphics Foundational


`Gf` 是一个数学库。它没有场景、prim 或 layer 的概念。它提供的是 USD 属性所承载的数据类型。

```python
from pxr import Gf

# Vectors
Gf.Vec3f(1.0, 0.0, 0.0)      # 32-bit float 3-component vector
Gf.Vec3d(0.0, 5.0, 0.0)      # 64-bit double 3-component vector
Gf.Vec2f(0.5, 0.5)            # UV coordinate
Gf.Vec4f(1.0, 0.0, 0.0, 1.0) # RGBA colour

# Transforms
Gf.Matrix4d()                  # 4x4 double matrix — the standard transform type
Gf.Quatf(1.0, 0.0, 0.0, 0.0) # Quaternion — rotation
Gf.Rotation(Gf.Vec3d(0,1,0), 45.0)  # axis-angle rotation

# Ranges and bounds
Gf.Range3f(Gf.Vec3f(-1,-1,-1), Gf.Vec3f(1,1,1))  # 3D range
Gf.BBox3d()                   # bounding box
```

### Vt —— Value Types（批量数组）


`Vt` 提供 Gf 类型的数组容器版本。当属性需要承载多个值时就会用到它 —— 网格顶点、面索引、UV 坐标等。

```python
from pxr import Vt, Gf

Vt.Vec3fArray([Gf.Vec3f(0,0,0), Gf.Vec3f(1,0,0)])  # points array
Vt.IntArray([4, 4, 4, 4])                            # faceVertexCounts
Vt.Vec2fArray([Gf.Vec2f(0,0), Gf.Vec2f(1,0)])       # UV coordinates
Vt.FloatArray([0.5, 0.8, 0.3])                       # float array
Vt.TokenArray(["xformOp:translate"])                  # token array
```

---

### Sdf —— Scene Description Foundation


`Sdf` 操作的是单个 layer。它从不执行合成 —— 它告诉你的是某一个具体文件写了什么，而不是合成后的场景长什么样。

```python
from pxr import Sdf

# Layer — one USD file in memory
layer = Sdf.Layer.CreateNew("model.usda")
layer = Sdf.Layer.FindOrOpen("model.usda")
layer.Save()
layer.identifier          # file path string
layer.subLayerPaths       # list of sublayer paths
layer.customLayerData     # dict of pipeline metadata
layer.Clear()             # remove all opinions from this layer

# Spec — one entry in a layer for a specific path
prim_spec = Sdf.CreatePrimInLayer(layer, "/World/Chair")
prim_spec.specifier = Sdf.SpecifierDef    # def / over / class
prim_spec.typeName  = "Xform"

attr_spec = Sdf.AttributeSpec(prim_spec, "myAttr", Sdf.ValueTypeNames.Float)
attr_spec.default       = 5.0            # raw authored value
attr_spec.documentation = "My attribute"
attr_spec.GetInfo("timeSamples")         # {frame: value} dict

# Path — address of any prim or property
path = Sdf.Path("/World/Chair.xformOp:translate")
path.GetParentPath()     # /World/Chair
path.AppendChild("Leg")  # /World/Chair/Leg
path.IsPropertyPath()    # True
path.name                # "xformOp:translate"

# Utilities
Sdf.LayerOffset(offset=100.0, scale=2.0)      # time shift for references
Sdf.Reference("./asset.usda", "/Chair")        # reference arc definition
Sdf.ValueTypeNames.Float                       # type name constant
Sdf.ChangeBlock()                              # batch change notifications
```

---

### Usd —— Universal Scene Description


`Usd` 负责打开 stage、执行合成，并给出最终解析后的场景。你 90% 的时间都在使用这套 API。

```python
from pxr import Usd, UsdGeom

# Stage — fully composed scene
stage = Usd.Stage.Open("shot.usda")
stage = Usd.Stage.CreateNew("scene.usda")
stage = Usd.Stage.CreateInMemory()
stage.Save()
stage.Export("output.usda")           # flat resolved copy to any path
stage.Flatten()                       # returns new SdfLayer with all arcs resolved
stage.GetLayerStack()                 # all layers, strongest → weakest
stage.GetEditTarget()                 # which layer receives authoring
stage.SetEditTarget(layer)
stage.MuteLayer(layer.identifier)
stage.Traverse()                      # depth-first prim iterator
stage.GetCompositionErrors()

# Prim — composed node, all arcs resolved
prim = stage.GetPrimAtPath("/World/Chair")
prim = stage.DefinePrim("/World/Chair", "Xform")
prim.IsA(UsdGeom.Mesh)               # True/False — type check
prim.HasAPI(UsdGeom.MotionAPI)       # True/False — API schema check
prim.GetTypeName()                   # "Xform"
prim.GetChildren()                   # child prims
prim.GetPrimStack()                  # list[SdfPrimSpec] — no parameters
prim.IsActive()
prim.SetInstanceable(True)
prim.GetPrimIndex().DumpToString()   # full composition arc graph

# Attribute — composed value after all layers resolve
# Both attributes and relationships are accessed from the PRIM
attr = prim.GetAttribute("xformOp:translate")   # typed value
attr.Get()                           # composed value (default time)
attr.Get(time=24)                    # composed value at frame 24
attr.Set(Gf.Vec3d(5,0,0))           # author default value
attr.Set(Gf.Vec3d(5,0,0), time=24)  # author time sample
attr.GetTimeSamples()                # [1.0, 24.0, 48.0]
attr.HasAuthoredValue()              # True/False
attr.GetPropertyStack(Usd.TimeCode.Default())  # list[SdfPropertySpec]

# Relationship — prim paths (NOT data values) — also at prim level
rel = prim.GetRelationship("material:binding")  # prim path pointer
rel.GetTargets()                     # [Sdf.Path("/World/Looks/WoodMat")]
rel.AddTarget("/World/Looks/MetalMat")          # add another target
rel.SetTargets([Sdf.Path("/World/Looks/WoodMat")])  # replace all targets
rel.HasAuthoredTargets()             # True/False
# Relationships have NO fallback values and NO Get(timeCode)
# They store prim paths only — not typed data
```

---

### 同一把椅子 —— 两个不同的答案


```python
# Sdf sees what ONE LAYER says:
layer = Sdf.Layer.FindOrOpen("model.usda")
spec  = layer.GetAttributeAtPath("/World/Chair.xformOp:translate")
spec.default   # (0, 0, 0)  — model.usda authored this value

# Usd sees the COMPOSED RESULT after all layers resolve:
stage = Usd.Stage.Open("shot.usda")   # shot includes anim + model sublayers
attr  = stage.GetPrimAtPath("/World/Chair").GetAttribute("xformOp:translate")
attr.Get()     # (5, 0, 0)  — anim layer won, composition applied

# Same underlying file data. Completely different question being answered.
# Sdf: "what does this specific file say?"
# Usd: "what is the final truth after everything composes?"
```

---

<a id="key-takeaways"></a>

## 10. 关键要点

| 概念 | 需要记住的内容 |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **阶段（Stage）** | 各层的内存中组合。不是一个文件。 |
| **层（Layer）** | 一个物理 USD 文件，或内存中的缓冲区。 |
| **图元（Prim）** | 场景图中的每一个节点。拥有路径、类型和属性。 |
| **`def`** | 创建一个 prim。声明所有权。拥有类型。 |
| **`over`** | 覆盖已存在的 prim。没有类型。如果没有 `def` 则不产生任何效果。 |
| **`class`** | 抽象模板。与 `inherits` 一起使用。永不参与渲染。 |
| **属性（Attribute）** | 存储带类型的值。任意类型。可以进行时间采样。带有回退值。可变。 |
| **关系（Relationship）** | 仅存储 prim 路径。可以有多个目标。**没有**回退值。**不**用于存放数据。 |
| **属性回退值（Attribute fallbacks）** | 属性具有由 schema 定义的回退值。关系则**没有**。 |
| **时间采样（Time samples）** | 稀疏的 —— 只创作你需要的关键帧。任何类型都可以进行时间采样，包括字符串。 |
| **更新时间采样（Updating time samples）** | 只需 `Set(value, time=n)` —— 无需先清除已有的采样。 |
| **`token` 类型** | 不可变的驻留字符串（interned string）。比较速度快。用于标识符/枚举。**不**适合存放大段或频繁变化的文本。 |
| **`string` 类型** | 任意可变文本。用于文件路径、描述以及大段内容。 |
| **`matrix4d`** | 4×4 双精度矩阵。**可以**进行时间采样并参与动画。 |
| **Schema 校验（Schema validation）** | 内置 schema 定义了预期的结构，但**不会**在运行时自动执行校验。必须由工具或自定义代码来完成校验。 |
| **SdfPath** | 每个 prim 与属性的唯一地址。区分大小写。 |
| **`.usda`** | ASCII 文本 —— 人类可读，速度慢，适合调试 |
| **`.usdc`** | 二进制 crate —— 速度快，体积小，生产环境格式 |
| **`.usdz`** | Zip 归档 —— 自包含，用于交付以及 AR/VR |
| **`defaultPrim`** | 每个发布的资产都必须设置，引用才能生效 |
| **`upAxis`** | 始终要显式设置 —— DCC 用 `Y`，工程工具用 `Z` |
| **`metersPerUnit`** | 始终要显式设置 —— `0.01` = 厘米（DCC 中常见） |
| **时间采样（Time samples）** | 动画关键帧。`Set(value, time=n)` 会创建一个。 |
| **`TimeCode.Default()`** | 最普通的默认值 —— 与 `TimeCode(0)`（第 0 帧）不同 |

---

_下一节：[第 2 天 — 组合弧 第 1 部分](day-02-composition-arcs-part-1.md)_

---


### 第 2 天 — 组合弧（上）


> 来源：`sparsha-2011/physical-ai-learning-journey` · `02-openUSD-cert/notes/day-02-composition-arcs-part-1.md` · [原文链接](https://github.com/sparsha-2011/physical-ai-learning-journey/blob/main/02-openUSD-cert/notes/day-02-composition-arcs-part-1.md) · 语言：英文原文 · 中译版



# 第 2 天 — 组合弧（上）

> **OpenUSD NCP 认证学习笔记**  
> _子层、引用、载荷与值解析_

---

## 目录

1. [什么是组合？](#1-什么是组合)
2. [意见与值解析](#2-意见与值解析)
3. [LIVERPS — 强度顺序](#3-liverps--强度顺序)
4. [子层](#4-子层)
5. [引用](#5-引用)
6. [载荷](#6-载荷)
7. [层偏移与时间平移](#7-层偏移与时间平移)
8. [关键要点](#8-关键要点)

---

## 1. 什么是组合？

**组合（Composition）** 是 USD 把多层场景描述组装成一个统一的最终场景的过程。USD 场景并不采用单一的巨型文件，而是有意拆分到多个文件之中——每个文件由不同的部门或关注点负责——并在运行时组合到一起。

```
  model.usda        anim.usda        lighting.usda        fx.usda
  (geometry)        (keyframes)      (lights, sky)        (particles)
       │                 │                 │                   │
       └─────────────────┴─────────────────┴───────────────────┘
                                   │
                               shot_042.usda
                               (root layer)
                                   │
                                   ▼
                          ╔══════════════════╗
                          ║  COMPOSED STAGE  ║
                          ║  (in-memory)     ║
                          ╚══════════════════╝
```

连接各图层的机制称为 **组合弧（composition arc）**。USD 定义了六种弧类型，各自服务于不同用途。它们合在一起按强度排序，缩写为 **LIVERPS**。

---

## 2. 意见与值解析

存储在图层中的每一个值都称为一条 **意见（opinion）**。当多个图层对同一图元的同一属性各自持有意见时，USD 必须选出一个胜出者。这就是 **值解析（value resolution）**。

### 解析规则

**最强的图层**（位于层栈最顶端）对于同一属性总是胜出。如果最强图层对某属性没有意见，USD 就下沉到下一层，如此沿层栈逐层向下。如果没有任何图层持有意见，则返回 **schema 回退值**（即 schema 中定义的默认值）。

```
Layer Stack (strongest → weakest)       Translate on /Robot
───────────────────────────────────      ─────────────────────
[0] anim.usda         STRONGEST          (5, 0, 0)  ← WINS
[1] layout.usda                          (0, 0, 0)
[2] model.usda        WEAKEST            (0, 0, 0)

Composed result: Robot.translate = (5, 0, 0)
```

**非破坏性覆盖：** 这套机制意味着更强图层可以覆盖更弱图层，而无需修改它们。更弱的图层保持原样——只是由于存在更强的意见，它的值没有被采用而已。

### 按属性逐个解析

解析是逐属性进行的，而不是逐图元进行的。更强图层可以只覆盖 `translate`，同时更弱图层仍提供 `size`：

```
anim.usda:    over "Robot" { translate = (5,0,0) }   # only translate
model.usda:   def Xform "Robot" { size = (1,2,1), translate = (0,0,0) }

Composed Robot:
  translate = (5,0,0)   ← from anim.usda (stronger)
  size      = (1,2,1)   ← from model.usda (only layer with an opinion)
```

### Python API — 检查值解析

```python
from pxr import Usd

stage = Usd.Stage.Open("shot.usda")
prim  = stage.GetPrimAtPath("/World/Robot")
attr  = prim.GetAttribute("xformOp:translate")

# Read the composed (winning) value
value = attr.Get()
print(value)  # (5, 0, 0) — anim layer wins

# Inspect every layer that has an opinion on this attribute
# Signature: attr.GetPropertyStack(timeCode: Usd.TimeCode) -> list[SdfPropertySpec]
# timeCode is REQUIRED — there is no default argument
stack = attr.GetPropertyStack(Usd.TimeCode.Default())
for i, spec in enumerate(stack):
    print(f"[{i}] {spec.layer.identifier}  value={spec.default}")
# [0] anim.usda    value=(5,0,0)   ← winner
# [1] model.usda   value=(0,0,0)

# Check if the value was explicitly authored vs a schema fallback
print(attr.HasAuthoredValue())  # True = explicitly Set(), False = fallback
```

---

## 3. LIVERPS — 强度顺序

当同一图元由多个**不同来源**共同贡献时，哪个来源的意见胜出？USD 用一个固定优先级顺序来解决，记作缩写 **LIVERPS**：

```
L — Local          (opinions authored directly in the local layer)
I — Inherit
V — Variant
E — rEference  *note: the 'E' stands for the 'e' in reference
R — (Relocates in older USD literature — ignore for NCP-OUSD)
P — Payload
S — Specializes
```

该顺序是**固定的，不可更改**。本地意见始终胜过继承意见，继承意见始终胜过变体意见，依此类推。

| 位置          | 来源           | 强度         | 说明                                              |
| ------------- | -------------- | ------------ | ------------------------------------------------- |
| 1（最强）     | **Local**      | 最高         | 组合图层中直接撰写的意见                          |
| 2             | **Inherit**    | 高           | 通过 Inherit 弧从 class 图元继承而来              |
| 3             | **Variant**    | 中高         | 当前激活变体所携带的意见                          |
| 4             | **rEference**  | 中           | 通过 Reference 弧从被引用文件而来的意见            |
| 5             | **Payload**    | 中低         | 来自载荷弧的意见（延迟加载）                      |
| 6（最弱）     | **Specializes** | 最低        | 通过 Specialize 弧提供的回退默认值               |

> **Specializes 处于最弱位置。** 它提供任何其他来源都可以覆盖的回退默认值。它**不会**覆盖任何内容——这是常见的考试陷阱。

### 关键区别 — Variant 不是一种弧类型

这是 USD 术语中最精细的区别之一，也是考试中的直接考点：

**LIVERPS 描述意见强度** —— 一个值来自优先级队列的哪个位置。  
**弧类型描述组合关系** —— 连接图元或引入外部数据的结构性边。

二者相关，但**并不是同一回事**。Variant 在 LIVERPS 中占有一个位置，但它**不是**一种组合弧类型。

#### 真正的 4 种组合弧类型

```
Reference  → prepend references  = @./file.usda@     points to external file
Payload    → prepend payload     = @./heavy.usda@     points to external file (deferred)
Inherit    → prepend inherits    = </_ClassPrim>      points to another prim
Specialize → prepend specializes = </_BasePrim>       points to another prim
```

每一种真正的弧都使用**路径或文件引用**——它会创建一条指向外部对象的有向边。

#### Variant 为什么不同

变体集完全**存在于图元自身内部**。选择某个变体不会创建跨图元的连接——它只是切换当前生效的**本地意见块**：

```usda
def Xform "Chair" (
    variants = { string color = "red" }   ← no path, no external file
    prepend variantSets = "color"         ← activates a local block
) {
    variantSet "color" = {
        "red"  { color3f[] primvars:displayColor = [(0.8, 0.2, 0.2)] }
        "blue" { color3f[] primvars:displayColor = [(0.2, 0.4, 0.9)] }
    }
}
```

没有外部文件，也没有引用其他图元。变体只是切换图元**自身数据**中的哪一块处于激活状态。正因如此它不是组合弧——它并不从外部组合任何内容。

#### 典型的考题形式

| 题目问的是                                 | 包含 Variant 吗 |
| ------------------------------------------ | ---------------- |
| "哪些属于组合**弧类型**？"                | ❌ 不包含        |
| "哪些属于 **LIVERPS**？"                   | ✅ 包含          |
| "哪些影响**组合强度顺序**？"               | ✅ 包含          |
| "哪些在图元之间创建**有向边**？"           | ❌ 不包含        |
| "哪些会**引入外部数据**？"                 | ❌ 不包含        |

---

## 4. 子层

**子层（sublayer）** 会把某个图层的整个命名空间合并进组合用的层栈中。子层中的所有图元都出现在相同的路径上——不存在路径重映射。

```
shot.usda          anim.usda            Composed result
─────────────      ─────────────        ───────────────
subLayers = [      over "Robot" {       /Robot.translate = (5,0,0)  ← anim wins
  anim.usda,         translate=(5,0,0)  /Robot.size      = (1,2,1)  ← model provides
  model.usda       }
]
                   model.usda
                   def Xform "Robot" {
                     size = (1,2,1)
                     translate = (0,0,0)
                   }
```

### 何时使用子层

| ✅ 正确用法                                                    | ❌ 错误用法                                                 |
| ------------------------------------------------------------- | ---------------------------------------------------------- |
| 在同一场景中分离不同工作流（anim、layout、fx、lighting）       | 引入外部资产（应使用 Reference）                            |
| 对已有图元做非破坏性覆盖                                       | 多次引入同一资产（子层 = 一个实例）                         |
| 在一个镜头中按部门划分的图层                                   | 需要延迟加载的重几何体（应使用 Payload）                    |

> **关键区别 — 子层 vs 引用：**  
> 子层 = 合并整个命名空间（同一场景，不同关注点）  
> 引用 = 把另一个文件中的单个图元嫁接到指定路径（资产复用）

### USDA 语法

```usda
#usda 1.0
(
    subLayers = [
        @./anim.usda@,       # FIRST = STRONGEST — wins all conflicts
        @./layout.usda@,     # second strongest
        @./model.usda@       # LAST = WEAKEST
    ]
)
```

### Python API

```python
from pxr import Usd, Sdf

stage      = Usd.Stage.Open("shot.usda")
root_layer = stage.GetRootLayer()

# Inspect current sublayers (index 0 = strongest)
print(root_layer.subLayerPaths)
# ['./anim.usda', './layout.usda', './model.usda']

# Add a sublayer as the WEAKEST (append = last position)
root_layer.subLayerPaths.append("./fx.usda")

# Add a sublayer as the STRONGEST (insert at index 0)
root_layer.subLayerPaths.insert(0, "./director_overrides.usda")

# Iterate all layers in strength order
for layer in stage.GetLayerStack():
    print(layer.identifier)

# Mute a layer for debugging (temporarily removes its contributions)
stage.MuteLayer("./layout.usda")
# When wrong value disappears after muting → that layer is the source
stage.UnmuteLayer("./layout.usda")
```

---

## 5. 引用

**引用（Reference）** 会把另一个 USD 文件中的某个特定图元嫁接到你的场景中的指定路径上。它是**资产复用**的标准机制——同一个椅子资产可以被十个不同场景引用，每个场景都会得到一份自己的图元层级副本。

```
scene.usda                      chair_asset.usda
───────────                     ─────────────────
def Xform "World" {             def Xform "Chair" {   ← defaultPrim
  def Xform "ChairA" (              def Mesh "seat_geo" { ... }
    prepend references =            def Mesh "legs_geo" { ... }
      @./chair_asset.usda@      }
  ) { }
}

Composed result:
/World/ChairA/seat_geo
/World/ChairA/legs_geo
```

引用会向组合场景**添加新的图元**——被引用的图元层级会出现在引用路径之下，即使这些路径在根图层中根本不存在。

### `defaultPrim` — 至关重要

当你只写 `@./chair_asset.usda@` 而不带图元路径时，USD 会去查找被引用文件上的 `defaultPrim` 元数据，以确定要引入哪个图元。如果没有设置 `defaultPrim`，引用就会失败。

```python
# On the asset file — always set defaultPrim before publishing
asset_stage = Usd.Stage.Open("chair_asset.usda")
root_prim   = asset_stage.GetPrimAtPath("/Chair")
asset_stage.SetDefaultPrim(root_prim)
asset_stage.Save()
```

### `prepend` 与 `append` — 列表插入行为

这两个关键字决定了新弧相对于该图元上同类型既有弧插入的位置。

| 关键字      | 等价于                   | 位置         | 强度                       |
| ----------- | ------------------------ | ------------ | -------------------------- |
| `prepend`   | `list.insert(0, item)`   | 列表前端     | 比既有弧更强               |
| `append`    | `list.append(item)`      | 列表后端     | 比既有弧更弱               |

**多行独立的 `prepend` 表现得就像反复调用 `insert(0)`——最后写入的那一行最终位于索引 0：**

```usda
prepend references = @./base_geometry.usda@      # insert(0) → ["base_geometry"]
prepend references = @./material_override.usda@  # insert(0) → ["material_override", "base_geometry"]
#                                                               ↑ index 0 — WINS despite being written second
```

这一点违反直觉——文件中最后写入的弧反而最强。请使用单个列表来显式指定顺序：

```usda
def Xform "Chair" (
    prepend references = [
        @./material_override.usda@,   # index 0 — strongest
        @./base_geometry.usda@        # index 1 — weaker
    ]
) { }
```

**同一图元上混用 prepend 与 append：**
prepend 项 → 填充列表前端（最强）

append 项 → 填充列表后端（最弱）
最终顺序：[prepend[0], prepend[1], ..., append[0], append[1], ...]

**在一个尚无任何弧的全新图元上，`prepend` 与 `append` 的结果完全相同**——只有当图元上已经存在弧时，这一区分才有意义。

### 引用的组合规则

- 引用在 LIVERPS 中位于 **E** 位——弱于本地、继承和变体
- 引用图元上的本地意见**覆盖**来自引用的意见
- 引用可以指向文件内的特定图元路径：`@./asset.usda@</SpecificPrim>`
- 一个图元上可以叠加多个引用：`prepend references = [@./a.usda@, @./b.usda@]`

### USDA 语法

```usda
def Xform "ChairA" (
    prepend references = @./chair_asset.usda@
    # or with explicit target prim:
    # prepend references = @./chair_asset.usda@</Chair>
) {
    # Local opinions here override the reference
    double3 xformOp:translate = (5, 0, 0)
}
```

### Python API

```python
from pxr import Usd, UsdGeom, Sdf

stage = Usd.Stage.CreateNew("scene.usda")
world = UsdGeom.Xform.Define(stage, "/World")

# Define a prim and add a reference to it
chair_a = stage.DefinePrim("/World/ChairA")
chair_a.GetReferences().AddReference("./chair_asset.usda")

# Reference with an explicit target prim path
chair_b = stage.DefinePrim("/World/ChairB")
chair_b.GetReferences().AddReference("./chair_asset.usda", "/Chair")

# Reference with a layer offset (shifts the animation in time)
from pxr import Sdf
ref = Sdf.Reference(
    assetPath  = "./chair_asset.usda",
    primPath   = Sdf.Path("/Chair"),
    layerOffset = Sdf.LayerOffset(offset=100.0, scale=2.0)
)
chair_c = stage.DefinePrim("/World/ChairC")
chair_c.GetReferences().AddReference(ref)
```

---

## 6. 载荷

**载荷（Payload）** 在结构上与引用完全相同——它同样把另一个文件中的图元嫁接过来——但有一个关键区别：**载荷数据在被显式请求之前不会被加载**。

这是 USD 实现**延迟加载**的机制，使大型场景（例如拥有数千栋建筑的城市）能够快速打开，只显示轻量的代理几何体，而沉重的网格数据则按需加载。

```
scene.usda opens quickly:          After stage.Load("/World/City/BuildingA"):
───────────────────────────        ────────────────────────────────────────
/World/City                        /World/City
  /World/City/BuildingA (empty)      /World/City/BuildingA
  /World/City/BuildingB (empty)        /legs_geo (mesh, fully loaded)
  /World/City/BuildingC (empty)        /walls_geo (mesh, fully loaded)
```

### 显式图元路径 vs defaultPrim

在引用或载荷某个文件时，USD 需要知道该文件**内部是哪一个图元**要引入进来。有两种方式可以告诉它：

**不写显式路径——依赖 `defaultPrim`**

```usda
prepend references = @./chair_asset.usda@
prepend payload    = @./chair_asset.usda@
```

USD 打开文件并在元数据中查找 `defaultPrim`。如果没有设置——就会静默失败，得到空图元。

**写显式路径——完全绕过 `defaultPrim`**

```usda
prepend references = @./chair_asset.usda@</Chair>
prepend payload    = @./chair_asset.usda@</Chair>
```

`<>` 中 `@` 之后的路径会明确告诉 USD 要定位哪个图元。此时 `defaultPrim` 无关紧要。

### Payload vs Reference

| 属性           | Reference            | Payload                        |
| -------------- | -------------------- | ------------------------------ |
| 打开时是否加载 | ✅ 总是加载          | ❌ 仅在显式加载时加载          |
| LIVERPS 位置   | E（第 4 位）        | P（第 5 位，更弱）             |
| 适合场景       | 始终需要的资产       | 重量级数据、可选内容           |
| 典型内容       | 道具、角色、场景集   | 高精度几何体、缓存             |

### Python API

```python
from pxr import Usd, UsdGeom, Sdf

stage = Usd.Stage.Open("scene.usda", Usd.Stage.LoadNone)
# LoadNone = open the stage but don't load ANY payloads
# The stage opens instantly even for gigantic scenes

# Inspect what payloads exist without loading them
for prim in stage.Traverse():
    if prim.HasPayload():
        print(f"Payload available: {prim.GetPath()}")

# Load a specific payload on demand
stage.Load("/World/City/BuildingA")

# Unload it (frees memory, prim becomes empty again)
stage.Unload("/World/City/BuildingA")

# Check if a prim is currently loaded
prim = stage.GetPrimAtPath("/World/City/BuildingA")
print(prim.IsLoaded())   # True or False

# Author a payload in USDA syntax:
def Xform "BuildingA" (
    prepend payload = @./building_a_geo.usda@
) { }
```

### USDA 语法

```usda
def Xform "BuildingA" (
    prepend payload = @./building_a_geo.usda@
) {
    # This prim is visible on the stage but its children
    # are only populated when explicitly loaded
}
```

> **考试区别：** 载荷会**创建**一条新的组合弧（与引用一样）。子层**不会**创建新弧——它们直接合并进现有的层栈。

---

## 7. 层偏移与时间平移

**层偏移（layer offset）** 附着在引用弧或载荷弧上，会对该弧带来的所有时间采样数据施加一次时间变换。

变换公式为：

```
composed_time = (source_time × scale) + offset
```

### 示例

```usda
def Xform "Character" (
    prepend references = @./walk_cycle.usda@ (offset = 100, scale = 2.0)
) { }
```

`walk_cycle.usda` 中 `source_time = 10` 处的关键帧出现在：

```
composed_time = (10 × 2.0) + 100 = 120
```

### 为什么这在调试中很重要

如果动画出现在错误的时间码上，**请首先检查引用弧上的层偏移**。这是一个经常被忽略的调试步骤。

> **考试陷阱：** "层偏移不会影响组合结果，因此可以忽略"是**错误**的。层偏移会直接影响随时间变化的数据的组合。调试动画时序问题时，必须始终把它考虑在内。

### Python API

```python
from pxr import Sdf

ref = Sdf.Reference(
    assetPath   = "./walk_cycle.usda",
    primPath    = Sdf.Path("/Character"),
    layerOffset = Sdf.LayerOffset(offset=100.0, scale=2.0)
)
prim.GetReferences().AddReference(ref)
```

---

## 8. 关键要点

| 概念                 | 需要记住的内容                                                                                             |
| -------------------- | ------------------------------------------------------------------------------------------------------------ |
| **组合**             | USD 在运行时把多个图层组装成一个统一的 stage                                                              |
| **意见**             | 图层中为某个特定属性存储的任意值                                                                            |
| **值解析**           | 按属性逐个解析，最强图层（层栈首位）胜出                                                                    |
| **LIVERPS**          | Local → Inherit → Variant → rEference → Payload → Specializes                                                |
| **LIVERPS 中的 Variant** | 描述的是意见_强度_——而不是弧类型。变体切换的是本地数据块，而不是外部连接。                             |
| **4 种弧类型**       | Reference、Payload、Inherit、Specialize——它们创建指向外部文件或图元的结构性边                              |
| **Variant ≠ 弧**     | "哪些是弧类型？"→ 排除 Variant。"哪些属于 LIVERPS？"→ 包含 Variant。                                       |
| **Specializes**      | 最弱位置——提供回退默认值，**不会**覆盖                                                                      |
| **子层**             | 合并整个命名空间。图元相同，关注点不同。                                                                    |
| **引用**             | 把另一个文件中的单个图元嫁接到指定路径。用于资产复用。                                                     |
| **载荷**             | 类似引用但延迟加载——在调用 `stage.Load()` 之前不会加载                                                      |
| **defaultPrim**      | 每个发布的资产都必须设置，引用才能生效                                                                      |
| **层偏移**           | 对所有时间采样施加 `composed = source × scale + offset`                                                     |
| **非破坏性**         | 更强图层可以覆盖，而不影响更弱图层                                                                          |

---

_上一篇：[第 1 天 — USD 基础](day-01-usd-foundations.md)_  
_下一篇：[第 3 天 — 组合弧（下）](day-03-composition-arcs-part-2.md)_

---


### 第 3 天 — 组合弧（下）


> 来源：`sparsha-2011/physical-ai-learning-journey` · `02-openUSD-cert/notes/day-03-composition-arcs-part-2.md` · [原文链接](https://github.com/sparsha-2011/physical-ai-learning-journey/blob/main/02-openUSD-cert/notes/day-03-composition-arcs-part-2.md) · 语言：英文原文 · 中译版



# 第 3 天 — 组合弧（下）

> **OpenUSD NCP 认证学习笔记**  
> _变体、继承、特化与高级组合模式_

---

## 目录

1. [变体集](#1-变体集)
2. [变体回退选择](#2-变体回退选择)
3. [Inherits（继承）](#3-inherits继承)
4. [Specializes（特化）](#4-specializes特化)
5. [Inherits vs Specializes — 关键区别](#5-inherits-vs-specializes--关键区别)
6. [组合弧最佳实践](#6-组合弧最佳实践)
7. [关键要点](#7-关键要点)

---

## 1. 变体集

**变体集（variant set）** 是某个图元的一组具名的备选配置。每个配置称为一个**变体（variant）**。任意时刻只有一个变体处于激活状态——即被选中的变体。切换选择会改变该图元呈现出的数据。

```
def Xform "RaceCar"
├── variantSet "color"        variantSet "lod"
│   ├── "red"    → red paint      ├── "hero"   → 2M polygon mesh
│   ├── "blue"   → blue paint     ├── "medium" → 200K polygon mesh
│   └── "silver" → silver paint   └── "proxy"  → 500 polygon box
```

变体集就是 **LIVERPS 中的 V**——比引用和载荷更强，但弱于本地意见与继承。

### 为什么需要变体

如果不用变体，每一种组合都需要一个单独的文件：`car_red_hero.usda`、`car_red_medium.usda`、`car_blue_hero.usda`——组合爆炸。有了变体，一个文件就包含所有组合，选择在组合时完成，无需修改资产本身。

### USDA 语法

USD 文件中变体集的结构包含两个彼此独立的部分：

1. **元数据块 `()`** —— 声明该变体集的存在，以及当前选中的是哪个变体
2. **数据块 `{}`** —— 定义每个变体所承载的内容

```usda
#usda 1.0
(
    defaultPrim = "RaceCar"
)

def Xform "RaceCar" (
    # ── METADATA BLOCK ───────────────────────────────────────────────
    prepend variantSets = "color"          # declares the variant set exists
    variants = {
        string color = "red"               # currently selected variant
    }
) {
    # ── DATA BLOCK ────────────────────────────────────────────────────
    variantSet "color" = {
        "red" {
            # these opinions are ONLY active when color = "red"
            color3f[] primvars:displayColor = [(1, 0, 0)]
        }
        "blue" {
            color3f[] primvars:displayColor = [(0, 0, 1)]
        }
        "silver" {
            color3f[] primvars:displayColor = [(0.8, 0.8, 0.85)]
        }
    }
}
```

### 从外部覆盖变体选择

引用方场景可以选择不同的变体，而**不必修改资产文件**。之所以可行，是因为 LIVERPS 中的 V 意味着更强图层中的本地意见（包括变体选择）会覆盖资产中的默认选择。

```usda
# scene.usda — the referencing scene
def Xform "World" {
    def Xform "MyCar" (
        prepend references = @./car_asset.usda@
        variants = {
            string color = "blue"   # overrides the asset's default "red"
        }
    ) { }
}
```

### Python API — `Usd.VariantSets`

```python
from pxr import Usd, UsdGeom

stage = Usd.Stage.CreateNew("car_asset.usda")
car   = UsdGeom.Xform.Define(stage, "/RaceCar")
prim  = car.GetPrim()

# Create a variant set on the prim
vset = prim.GetVariantSets().AddVariantSet("color")

# Add variants and author content into each one
vset.AddVariant("red")
vset.SetVariantSelection("red")
with vset.GetVariantEditContext():
    # Anything authored here is scoped to the "red" variant
    prim.CreateAttribute(
        "primvars:displayColor",
        Sdf.ValueTypeNames.Color3fArray
    ).Set([(1, 0, 0)])

vset.AddVariant("blue")
vset.SetVariantSelection("blue")
with vset.GetVariantEditContext():
    prim.CreateAttribute(
        "primvars:displayColor",
        Sdf.ValueTypeNames.Color3fArray
    ).Set([(0, 0, 1)])

# Set the default selection in the asset
vset.SetVariantSelection("red")

# --- In the referencing scene, override the selection ---
scene = Usd.Stage.CreateNew("scene.usda")
my_car = scene.DefinePrim("/World/MyCar")
my_car.GetReferences().AddReference("./car_asset.usda")

# Override variant selection
my_car.GetVariantSets().GetVariantSet("color").SetVariantSelection("blue")
```

---

## 2. 变体回退选择

**变体回退选择（variant fallback selections）** 定义当请求的变体在某个资产中并不存在时，USD 应该使用什么。它们可以避免管线环境请求了未撰写的变体时所导致的硬失败。

### 三个听起来相似但彼此不同的概念

在介绍具体做法之前，必须先弄清楚三个容易混淆的概念：

```
1. Default variant selection on the prim
   variants = { string lod = "high" }    ← in the prim definition
   "if nobody overrides this, use high"
   → VALID and standard practice

2. variantFallbacks in layer metadata header
   #usda 1.0
   (
       variantFallbacks = { string[] "lod" = ["high", "medium"] }
   )
   → VALID — stage-wide policy in the layer header

3. variantFallbacks in PRIM metadata
   def Xform "Chair" (
       variantFallbacks = { ... }    ← inside a prim block
   ) { }
   → WRONG — has no effect, not standard practice
```

> 考试专门考查 (1) 与 (3) 之间的区别。在**图元上**设置默认选择是正确做法，也正是"在图元定义层上定义回退变体"的含义。把 `variantFallbacks` 写在**图元元数据**里则是错误的，没有任何效果。

---

### 做法 1 — 图元上的默认变体选择（资产级）

直接在变体集定义中设置默认选择。这是基准方案——如果没有任何更强的图层覆盖它，USD 就使用该选择。

```usda
def Xform "Chair" (
    prepend variantSets = "lod"
    variants = { string lod = "high" }   ← default selection on the prim
) {
    variantSet "lod" = {
        "high"   { ... }
        "medium" { ... }
        "low"    { ... }
    }
}
```

- 位于资产文件自身之中
- 当没有其他图层覆盖该选择时生效
- 这就是考试语言中"在图元定义层上定义回退变体"的含义

---

### 做法 2 — 根图层元数据中的 `variantFallbacks`

面向整个 stage 的回退策略。必须写在**根图层元数据头部**——也就是与 `upAxis`、`metersPerUnit`、`subLayers` 相同的那一块。绝不能写在任何图元定义里。

```usda
#usda 1.0
(
    upAxis = "Y"
    variantFallbacks = {        ← layer metadata header — correct placement
        string[] "lod"   = ["high", "medium", "low"]
        string[] "color" = ["default"]
    }
    subLayers = [
        @./anim.usda@,
        @./layout.usda@
    ]
)
```

- 被固化到磁盘上的文件中
- 只要该文件作为根图层被打开就会生效
- 自动跨会话持久化
- 与做法 3 等价，只是用 USDA 而不是 Python 撰写
  > 做法 2 与做法 3 是**等价的**——策略相同，接口不同。做法 2 写在文件里，做法 3 写在 Python 代码里。二者设置的是同一个面向全 stage 的回退。

---

### 做法 3 — `Usd.Stage.SetGlobalVariantFallbacks()`（Python）

必须在 `Usd.Stage.Open()` **之前**调用。对已经打开的 stage 无效。

```python
from pxr import Usd

# Call BEFORE opening — has no effect on already-open stages
Usd.Stage.SetGlobalVariantFallbacks({
    "lod":   ["high", "medium", "low"],
    "color": ["default"],
})

stage = Usd.Stage.Open("scene.usda")   # fallbacks apply here
```

- 必须在打开 stage 之前调用
- 不会持久化——每个新进程都要重新设置
- 适合在启动时做环境相关或工具相关的覆盖

---

### 做法 4 — 会话层（运行时变更）

会话层始终是最强的图层，并且永远不会保存到磁盘。用它来做**运行时变更**——即 stage 已经打开之后——而无需改动任何共享文件。

```python
stage   = Usd.Stage.Open("shot.usda")
session = stage.GetSessionLayer()
stage.SetEditTarget(session)

# Override variant selection at runtime
prim = stage.GetPrimAtPath("/World/Car")
prim.GetVariantSets().GetVariantSet("lod").SetVariantSelection("proxy")
# Takes effect immediately — no file change, no reopen needed

# Clear when done
stage.GetSessionLayer().Clear()
```

- 最强图层——覆盖其他所有内容
- 仅存在于内存中——`stage.Save()` 永远不会把它写入磁盘
- 进程结束时被丢弃
- 运行时变更变体的正确机制——而不是"避免运行时变更"
  > **考试陷阱：** "只在 stage 组合期间使用回退选择，避免运行时变更"是**错误**的。会话层正是为支持运行时变体变更而存在的。

---

### 做法 5 — 每个引用图层各自的 `variantFallbacks`

为了在各部门之间保持一致，可以在每个引用该资产的图层中撰写 `variantFallbacks`：

```usda
# department_anim.usda
#usda 1.0
(
    variantFallbacks = {
        string[] "lod" = ["high", "medium", "low"]
    }
)
```

- 无论用哪个工具打开 stage，都能保证回退行为一致
- 避免某个工具的环境与资产默认设置不一致时导致的失败

---

### 对比表

| 做法                             | 撰写位置                             | 是否持久化       | 生效时机                       | 使用场景                     |
| -------------------------------- | ------------------------------------ | ---------------- | ------------------------------ | ---------------------------- |
| 图元上的默认选择                 | 资产文件的图元定义内部               | 是——写盘        | 不存在更强覆盖时               | 资产级基准                   |
| 根图层中的 `variantFallbacks`    | 根图层元数据头部 `()`                | 是——写盘        | stage 组合时                   | 共享的管线默认值             |
| `SetGlobalVariantFallbacks()`    | `Stage.Open()` 之前的 Python 代码    | 否——按进程      | stage 组合时                   | 工具/环境启动                |
| 会话层                           | 内存中，永不保存                     | 否——按会话      | 运行时，stage 打开之后        | 交互式覆盖、调试             |
| 每个引用图层各自设置             | 各子层元数据头部                     | 是——写盘        | 逐层组合时                     | 部门一致性                   |

---

### 错误做法

| 错误做法                                   | 原因                                                                       |
| ------------------------------------------ | -------------------------------------------------------------------------- |
| 把 `variantFallbacks` 写在**图元元数据**中 | 图元元数据对回退没有任何作用——必须写在图层元数据头部                       |
| 只依赖图元上的默认选择                     | 无法覆盖"请求的变体根本不存在"的情况                                         |
| 只依赖会话层                               | 会话层可以覆盖选择，但并不定义回退逻辑                                       |
| 用不同的变体集复制出多个图元               | 增加复杂度——`variantFallbacks` 才是正确机制                                  |
| 假定 USD 会自动按字母序选择                 | USD **不会**自动选择变体——回退必须显式定义                                  |
| 避免运行时变更                             | 错误——会话层正是为运行时变体变更而存在的                                     |

---

## 3. Inherits（继承）

**Inherits（继承）** 把 `class` 图元的意见传播给场景中多个 `def` 图元。它是 **LIVERPS 中的 I**——强度第二的弧。

```
class "_PineTree"           ← template, never rendered
  height = 5.0
  displayColor = green

def "PineTree_A" (inherits = </_PineTree>)  → height=5.0, green
def "PineTree_B" (inherits = </_PineTree>)  → height=5.0, green
def "PineTree_C" (inherits = </_PineTree>)  → height=5.0, green
  height = 8.0  ← local override               (height=8.0 WINS, still green)
```

**继承的强大之处：** 把 `_PineTree.height` 改成 `6.0`，所有继承它的树都会自动更新——除了那些带有本地覆盖的树。

### 继承的关键属性

- Inherits 使用**图元路径**，而不是文件路径：是 `</_PineTree>`，不是 `@./file.usda@`
- class 图元必须存在于**组合后 stage 的命名空间**中的某处
- class 图元使用 `class` 说明符——默认的遍历和渲染器会跳过它们
- 继承图元上的本地意见胜过继承而来的意见（LIVERPS 中 L 在 I 之前）
- 对 class 图元的修改会**实时**传播到所有继承它的图元

### USDA 语法

```usda
# Define the class (template)
class Xform "_PineTree" {
    double height = 5.0
    color3f[] primvars:displayColor = [(0.1, 0.5, 0.1)]
}

# Inherit from the class
def Xform "Forest" {
    def Xform "PineTree_A" (
        prepend inherits = </_PineTree>
        # Uses angle brackets <> for prim paths — not @ signs for files
    ) {
        # No local overrides — gets everything from _PineTree
    }

    def Xform "PineTree_C" (
        prepend inherits = </_PineTree>
    ) {
        double height = 8.0
        # Local opinion overrides the inherited height=5.0
        # displayColor still inherited from _PineTree
    }
}
```

### Python API — `Usd.Inherits`

```python
from pxr import Usd, UsdGeom, Sdf

stage = Usd.Stage.CreateNew("forest.usda")

# Create the class prim using CreateClassPrim()
# Signature: stage.CreateClassPrim(path: str) -> Usd.Prim
class_prim = stage.CreateClassPrim("/_PineTree")
class_prim.CreateAttribute("height", Sdf.ValueTypeNames.Double).Set(5.0)

# Create a prim that inherits from the class
tree_a = UsdGeom.Xform.Define(stage, "/Forest/PineTree_A")

# Access the inherits manager and add the arc
# Signature: prim.GetInherits() -> Usd.Inherits
inherits = tree_a.GetPrim().GetInherits()
inherits.AddInherit(Sdf.Path("/_PineTree"))

# Verify the inherited value
tree_a_prim = stage.GetPrimAtPath("/Forest/PineTree_A")
print(tree_a_prim.GetAttribute("height").Get())  # 5.0 — inherited

# Add a local override (beats the inherit)
tree_a_prim.GetAttribute("height").Set(8.0)
print(tree_a_prim.GetAttribute("height").Get())  # 8.0 — local wins
```

---

## 4. Specializes（特化）

**Specializes（特化）** 是 LIVERPS 中最弱的组合弧——排在最后的那一个 S。与 Inherits 一样，它把意见从一个图元传播到另一个图元。与 Inherits 不同的是，被传播的意见是**回退默认值**，任何其他弧都可以胜过它们。

> **关键区别：** Inherits 的意见是强的（LIVERPS 中排第二）。Specializes 的意见是弱的（LIVERPS 中排最后）。只有当没有任何其他弧对该属性持有意见时，特化值才会生效。

### 经典用例 — 材质库

```
class "_BasePlastic"
    roughness = 0.2    (smooth)
    metallic  = 0.0

def "RoughPlastic" (specializes = </_BasePlastic>)
    roughness = 0.8    ← LOCAL opinion beats specializes → 0.8 applies
    metallic is not set → falls back to specializes → 0.0 applies
```

### USDA 语法

```usda
class "_BasePlastic" {
    float inputs:roughness = 0.2   # smooth plastic default
    float inputs:metallic  = 0.0
    color3f inputs:diffuseColor = (0.8, 0.8, 0.8)
}

def Material "RoughPlastic" (
    prepend specializes = </_BasePlastic>
) {
    float inputs:roughness = 0.8
    # Local roughness (0.8) overrides the specialized value (0.2)
    # metallic and diffuseColor fall back to _BasePlastic values
}
```

### Python API — `Usd.Specializes`

```python
from pxr import Usd, Sdf

stage = Usd.Stage.CreateNew("materials.usda")

# Create the base class
base = stage.CreateClassPrim("/_BasePlastic")
base.CreateAttribute("inputs:roughness", Sdf.ValueTypeNames.Float).Set(0.2)
base.CreateAttribute("inputs:metallic",  Sdf.ValueTypeNames.Float).Set(0.0)

# Create a specialization
rough = stage.DefinePrim("/RoughPlastic", "Material")

# Signature: prim.GetSpecializes() -> Usd.Specializes
specializes = rough.GetSpecializes()
specializes.AddSpecialize(Sdf.Path("/_BasePlastic"))

# Override roughness locally (local beats specializes)
rough.GetAttribute("inputs:roughness").Set(0.8)

stage.Save()
```

---

## 5. Inherits vs Specializes — 关键区别

这一区别是认证考试中最常被考查的主题之一。

| 属性           | Inherits                                        | Specializes                           |
| -------------- | ----------------------------------------------- | ------------------------------------- |
| LIVERPS 位置   | **I** —— 第二强                                  | **S** —— 最弱（最后一位）             |
| 意见强度       | 强——胜过变体、引用、载荷                          | 弱——被其他一切胜过                   |
| 用途           | 把属性广播到多个图元                              | 提供回退默认值                        |
| 典型用途       | 共享属性（可见性、缩放约定等）                    | 材质基类、默认设置                    |
| 关键字         | `prepend inherits = <path>`                       | `prepend specializes = <path>`        |

### 心智模型

```
Inherits:     "I AM a PineTree — I should have all its properties unless I say otherwise"
              The class's opinions flow DOWN as STRONG opinions

Specializes:  "I am a SPECIALIZATION of BasePlastic — use its values as my fallback"
              The class's opinions flow DOWN as WEAK fallbacks
```

> **考试陷阱：** "Specializes 弧会覆盖图元的整个组合结果，取代来自更弱弧的所有意见。"——这是**错误**的。Specializes 是**最弱**的弧。它提供回退默认值，其他一切都胜过它。

---

## 6. 组合弧最佳实践

### 应该做的

| 实践                                                       | 弧类型     | 原因                                                             |
| ---------------------------------------------------------- | ---------- | ---------------------------------------------------------------- |
| 使用**引用**引入外部资产                                   | Reference  | 嫁接图元层级，同时不会在根图层中创建新的组合弧                 |
| 对不需要立即加载的重资产使用**载荷**                       | Payload    | 会创建弧但延迟加载——在模块化与性能之间取得平衡                 |
| 使用**变体集**在不同资产配置之间切换                       | Variant    | 在受控的组合范围内实现灵活的场景变化                           |
| 使用**子层**分离不同工作流的关注点（anim、fx、lighting）    | Sublayer   | 同一命名空间，不同关注点——规范的团队协作模式                 |

### 不应该做的

| 反模式                                       | 为什么不对                                                                 |
| -------------------------------------------- | -------------------------------------------------------------------------- |
| 把大量无关的小改动过度使用子层来组织         | 让组合变得不可预测，难以调试                                                |
| 在根图层中直接编辑被载荷引用的资产           | 破坏封装性，可能损坏组合弧                                                  |
| 在载荷内部嵌套引用                           | 技术上可行，但会造成复杂且不可预测的组合——生产环境中应避免                |
| 假定 specializes 会覆盖更弱的弧               | Specializes **就是**最弱的弧——它只提供回退                                |

---

## 7. 关键要点

| 概念                          | 需要记住的内容                                                                    |
| ----------------------------- | --------------------------------------------------------------------------------- |
| **变体集**                    | 具名的备选集合。同一时刻只有一个激活。LIVERPS 中的 V。                            |
| **变体选择**                  | 哪个变体处于激活状态。可以被更强的图层覆盖。                                      |
| **`GetVariantEditContext()`** | 用于向特定变体中撰写内容的上下文管理器                                            |
| **变体回退**                  | `SetGlobalVariantFallbacks()` 或会话层——用于请求的变体不存在时                    |
| **Inherits**                 | 以**强**意见传播 class 意见。I = LIVERPS 中第 2 位。                             |
| **`class` 说明符**            | 模板图元。被遍历和渲染器跳过。与 inherits 配合使用。                              |
| **Specializes**              | 以**弱**回退传播 class 意见。S = LIVERPS 中最后一位。                             |
| **Inherits vs Specializes**  | Inherits = 强广播。Specializes = 弱回退。                                         |
| **弧的路径语法**              | Inherits/Specializes 使用 `<prim path>`。References/Payloads 使用 `@file path@`。  |
| **完整的 LIVERPS**            | Local → Inherit → Variant → rEference → Payload → Specializes                     |

---

_上一篇：[第 2 天 — 组合弧（上）](day-02-composition-arcs-part-1.md)_  
_下一篇：[第 4 天 — 高级组合](day-04-advanced-composition.md)_

---


### 第 4 天 — 高级合成概念


> 来源：`sparsha-2011/physical-ai-learning-journey` · `02-openUSD-cert/notes/day-04-advanced-composition.md` · [原文链接](https://github.com/sparsha-2011/physical-ai-learning-journey/blob/main/02-openUSD-cert/notes/day-04-advanced-composition.md) · 语言：英文原文 · 中译版



# 第 4 天 — 高级合成概念

> **OpenUSD NCP 认证学习笔记**  
> _编辑目标、会话层、稀疏覆盖、展平与资产结构_

---

## 目录

1. [编辑目标](#1-编辑目标)
2. [会话层](#2-会话层)
3. [稀疏覆盖](#3-稀疏覆盖)
4. [移除与清除属性](#4-移除与清除属性)
5. [展平 — 烘焙合成](#4-展平-烘焙合成)
6. [封装 — 资产结构原则](#5-封装-资产结构原则)
7. [变更处理与 SdfChangeBlock](#6-变更处理与-sdfchangeblock)
8. [直接操作层](#7-直接操作层)
9. [完整的合成心智模型](#8-完整的合成心智模型)
10. [关键要点](#9-关键要点)

---

## 1. 编辑目标

**编辑目标**决定所有创作操作会被写入哪一层。当你调用 `Set()`、`DefinePrim()` 或任何其他创作 API 时，产生的 spec 只会写入恰好一层——也就是当前的编辑目标。

默认情况下，编辑目标是 stage 的**根层**。你可以随时把它切换到层栈中的任意一层。

```
Stage (shot.usda)
├── root_layer.usda   ← edit target (default)
├── anim.usda
└── lighting.usda

prim.GetAttribute("translate").Set((5,0,0))
→ writes ONLY to root_layer.usda
→ anim.usda and lighting.usda are untouched
```

> **USD 流水线中最常见的 bug：** 把创作操作写入了错误的编辑目标。该操作会静默成功——不会抛出任何错误——但意见却落到了错误的层上。在多图层流水线中，创作之前务必检查 `stage.GetEditTarget()`。

### Python API

```python
from pxr import Usd, Sdf

stage = Usd.Stage.Open("shot.usda")

# Check the current edit target
current = stage.GetEditTarget()
print(current.GetLayer().identifier)  # current layer receiving edits

# Switch edit target to a specific layer
anim_layer = Sdf.Layer.FindOrOpen("./anim.usda")
stage.SetEditTarget(anim_layer)
# Now ALL edits go to anim.usda

# Safe pattern — save and restore
previous = stage.GetEditTarget()
try:
    stage.SetEditTarget(anim_layer)
    prim.GetAttribute("xformOp:translate").Set((5, 0, 0))
finally:
    stage.SetEditTarget(previous)  # always restore
```

---

## 2. 会话层

**会话层**是一个特殊的内存层，它始终是 stage 中**最强**的层。`stage.Save()` 永远不会把它保存到磁盘。

```
Strength order when session layer is involved:
[0] session layer     ← STRONGEST (in-memory, never saved)
[1] root_layer.usda   ← default edit target
[2] anim.usda
[3] model.usda        ← weakest
```

### 会话层的用途

- 保存临时的交互式覆盖（例如 usdview 中的编辑）
- 做单次会话的定制，而不影响共享文件
- 存放会话结束后不应保留的临时覆盖

### 它不是什么

会话层**并不**等同于你自己创建并命名为 `"session.usda"` 的子层。它是 USD 内置的内存层，通过 `stage.GetSessionLayer()` 获取。

```python
# Access the session layer
session = stage.GetSessionLayer()

# Author into the session layer
stage.SetEditTarget(session)
prim.GetAttribute("visibility").Set("invisible")
# This override exists only in this session — not saved to disk

# Clear all session layer opinions
stage.GetSessionLayer().Clear()
# Removes ALL interactive edits made this session
```

> **重要：** `stage.Save()` 永远不会触碰会话层。如果你需要某个覆盖长期生效，请把它创作到真实的、基于文件的层中。

---

## 3. 稀疏覆盖

**稀疏覆盖**使用 `over` spec，只修改由其他层所拥有的 prim 上的特定属性。覆盖层中只包含它需要改动的属性——其余所有属性都从原始层原样流入。

```
model.usda (weaker — owns the prim):          anim.usda (stronger — sparse override):
def Xform "Chair" {                           over "Chair" {
    double3 xformOp:translate = (0,0,0)           double3 xformOp:translate = (5,0,0)
    double3 xformOp:scale = (1,1,1)               # scale NOT mentioned — flows from model
    token visibility = "inherited"                # visibility NOT mentioned — flows through
}                                             }

Composed result:
    translate = (5,0,0)  ← from anim (stronger)
    scale     = (1,1,1)  ← from model (anim has no opinion)
    visibility = "inherited" ← from model (anim has no opinion)
```

这就是 USD 的**非破坏性覆盖**机制。更强的层保持最小化——只包含它所改动的内容。

```python
from pxr import Usd, Sdf

stage      = Usd.Stage.Open("shot.usda")
anim_layer = Sdf.Layer.FindOrOpen("./anim.usda")

# Switch to the override layer
stage.SetEditTarget(anim_layer)

# Override ONLY translate — nothing else is touched
prim = stage.GetPrimAtPath("/World/Chair")
prim.GetAttribute("xformOp:translate").Set((5, 0, 0))
# anim.usda now contains an 'over "Chair"' with only translate
# model.usda is completely unchanged
```

---

## 4. 移除与清除属性

### 为什么需要这些操作

稀疏覆盖让你可以**新增**或**修改**意见。但有时你需要反方向操作——**移除**某个意见，或者**阻断**某个属性从更弱的层流入。这是一种独立的创作操作，考试会专门考查它；而且根据你的目标不同（移除数值、移除某个时间采样，还是让属性彻底不出现），它的行为也不相同。

### 三种场景

```
Scenario 1 — Remove an authored value
  A layer Set() a value on an attribute.
  You want to undo that — go back to schema fallback.
  Use: attr.Clear()

Scenario 2 — Remove a specific time sample
  An animated attribute has a keyframe you want to delete.
  Use: attr.ClearAtTime(frame)

Scenario 3 — Remove the property entirely from the layer
  The property spec itself should not exist in this layer at all.
  Use: prim.RemoveProperty("name")
```

### 场景 1 — 清除已创作的值

`Clear()` 从当前编辑目标层中移除已创作的意见。属性依然存在——如果存在 schema 默认值就会回退到该默认值，否则变为未创作状态。

```python
from pxr import Usd, UsdGeom

stage = Usd.Stage.Open("scene.usda")
prim  = stage.GetPrimAtPath("/World/Chair")
attr  = prim.GetAttribute("xformOp:translate")

# Before clear
attr.Get()              # (5, 0, 0) — authored value
attr.HasAuthoredValue() # True

# Clear the authored opinion from the current edit target
attr.Clear()

# After clear
attr.Get()              # (0, 0, 0) — schema fallback, or None if no fallback
attr.HasAuthoredValue() # False
```

> **`Clear()` 并不会删除属性。** 它移除的是当前编辑目标层中的已创作值意见。该属性 spec 可能仍存在于更弱的层中——它们的值现在会流入。

### 场景 2 — 清除某个特定的时间采样

如果你只想删除某个带动画属性上的一个关键帧，而不影响其余动画：

```python
attr = prim.GetAttribute("xformOp:translate")

# Before — time samples at frames 1, 12, 24, 48
attr.GetTimeSamples()   # [1.0, 12.0, 24.0, 48.0]

# Remove only frame 12
attr.ClearAtTime(12)

# After
attr.GetTimeSamples()   # [1.0, 24.0, 48.0] — frame 12 gone
attr.Get(time=12)       # interpolated between 1 and 24
```

### 场景 3 — 彻底移除属性

`RemoveProperty()` 会从当前编辑目标层中该 prim 上删除属性 spec。当这个属性根本不该存在于该层中时使用它——它不只是没有值，而是连 spec 都不该存在。

```python
# Remove a primvar that should not be on this prim
prim.RemoveProperty("primvars:displayColor")

# Remove a relationship
prim.RemoveProperty("material:binding")

# The property is gone from this layer
# If a weaker layer has it, that opinion now flows through
```

### 生产环境中什么时候会用到？

**从装配 stage 中被实例化的组件 prim 上移除属性**

最常见的考试场景。一个资产被引用到场景中，装配层需要从合成后的 prim 上剥离某个属性——例如在交付前移除一个调试用 primvar，或移除材质绑定以便让镜头级别的绑定干净地接管。

```python
# Asset has a default red displayColor
# Shot layer wants to remove it so the shot material controls colour

stage      = Usd.Stage.Open("shot.usda")
shot_layer = stage.GetRootLayer()

# Switch to shot layer as edit target
stage.SetEditTarget(shot_layer)

chair = stage.GetPrimAtPath("/World/Chair")

# Remove the colour primvar from the shot layer's opinion
# This blocks the asset's red from showing through
chair.RemoveProperty("primvars:displayColor")
```

**在流水线处理过程中清除时间采样**

当下游流水线步骤需要在交付前对资产进行烘焙或剥离动画时：

```python
# Remove all time samples from an attribute
attr = prim.GetAttribute("xformOp:translate")
attr.Clear()   # removes all time samples AND default value

# Or selectively remove frames in a range
for frame in range(1, 25):
    attr.ClearAtTime(frame)
```

### Clear 与 RemoveProperty 对照表

| 操作 | 作用 | 属性是否仍然存在？ | 更弱的层是否会流入？ |
| ----------------------------- | --------------------------------------- | ------------------------------ | --------------------------- |
| `attr.Clear()` | 从编辑目标中移除已创作的值 | 是——spec 仍保留 | 是 |
| `attr.ClearAtTime(n)` | 移除某一个时间采样 | 是——spec 仍保留 | 该时间点会流入 |
| `prim.RemoveProperty("name")` | 从编辑目标中删除属性 spec | 否——spec 从该层消失 | 是 |

> **关键洞察：** 这三种操作都只影响当前编辑目标层，不会触碰其他层。如果更弱的层对该属性有意见，移除之后它就会流入——这可能正是你想要的，也可能不是。使用带 `Block` 的 `over` spec 可以显式阻止更弱的意见流入。

### 阻断来自更弱层的属性

如果你想彻底阻止更弱层的意见流入——而不只是移除自己的意见——使用 `Block()`：

```python
# Block() sets the value to the type's "blocked" sentinel
# telling composition to stop resolving this property
attr.Block()

# After Block():
attr.Get()              # None — blocked, not the weaker layer's value
attr.HasAuthoredValue() # True — the block IS an authored opinion
```

---

## 4. 展平 — 烘焙合成

**展平**会解析所有合成弧，产出一个只包含胜出值的单一层。这是一个单向操作——原始源文件不受影响，但合成结构（引用、变体、子层）在输出中被永久丢弃。

```
Before flatten:                    After flatten:
shot.usda                          flat_delivery.usda
├── anim.usda                      (one layer, no arcs)
├── layout.usda                    /World/Chair.translate = (5,0,0)
└── model.usda                     /World/Chair.size = (1,2,1)
    └── ref → chair_asset.usda     ...all winning values baked in
```

### 展平保留什么、丢弃什么

| 保留 | 丢弃 |
| ------------------------------ | ------------------------------------------- |
| ✅ 所有胜出的属性值 | ❌ 合成弧（引用、子层） |
| ✅ 动画时间采样 | ❌ 变体集（折叠为被选中的那一个） |
| ✅ 完整的 prim 层级 | ❌ 层栈结构 |
| ✅ 几何体类型 | ❌ payload 惰性加载 |

> **时间采样会被保留。** 展平**不会**把动画烘焙成静态数值。那是另一个独立且需要刻意执行的操作。

### `stage.Flatten()` 与 `UsdUtils.FlattenLayerStack()` 对比

两种方法都会在内存中返回一个全新的 `SdfLayer`。原始 stage 及其所有源文件**绝不会被修改**。可以把两者都理解为在那一刻给 stage 拍了一张照片——场景本身未被触碰。

### 各自解析什么

| 方法 | 子层 | 引用 | Payload | 变体 | 时间采样 |
| ------------------------------ | --------- | ----------- | ----------- | --------------------- | ------------ |
| `UsdUtils.FlattenLayerStack()` | 合并 | 保持完整 | 保持完整 | 保持完整 | 保留 |
| `stage.Flatten()` | 合并 | 已解析 | 已解析 | 折叠为选中的那一个 | 保留 |
| `usdcat --flatten` | 合并 | 已解析 | 已解析 | 折叠为选中的那一个 | 保留 |

> 两种方法都**始终保留**时间采样。它们都不会把动画展平成静态值。

---

### 真正的区别 —— 输出的 SdfLayer 长什么样

假设你有这样一个 stage：

```
shot.usda
  ├── anim.usda          (sublayer — translate keyframes)
  └── layout.usda        (sublayer — base positions)
      /World/Chair       (has reference → chair_asset.usda)
      /World/Chair       (has variantSet "color", selection = "red")
```

**执行 `UsdUtils.FlattenLayerStack(stage)` 之后：**

```usda
#usda 1.0
(
    # sublayers are GONE — merged into one layer
    # but arcs are PRESERVED exactly as authored
)

def Xform "Chair" (
    prepend references = @./chair_asset.usda@   ← reference STILL HERE
    variants = { string color = "red" }          ← variant set STILL HERE
    prepend variantSets = "color"
) {
    double3 xformOp:translate.timeSamples = {    ← anim + layout merged
        1:  (0, 0, 0),
        24: (5, 0, 0),
    }
}
```

对 `chair_asset.usda` 的引用仍然存在。变体集依然存在，依然可以切换。来自 `anim.usda` 和 `layout.usda` 的子层意见被合并进一层，但合成结构被保留下来。

**执行 `stage.Flatten()` 之后：**

```usda
#usda 1.0
(
    # everything resolved — no arcs, no sublayers
)

def Xform "Chair" {
    # reference is GONE — geometry inlined from chair_asset.usda
    def Mesh "seat_geo" {
        point3f[] points = [(-1,0,-1), (1,0,-1), ...]  ← geometry inlined
        int[] faceVertexCounts = [4, 4, 4, ...]
    }
    def Mesh "legs_geo" { ... }

    # variant set is GONE — only the selected variant's data remains
    color3f[] primvars:displayColor = [(0.8, 0.2, 0.2)]  ← "red" baked in
    # cannot switch to "blue" anymore — that data is gone

    double3 xformOp:translate.timeSamples = {    ← time samples preserved
        1:  (0, 0, 0),
        24: (5, 0, 0),
    }
}
```

引用消失了——来自 `chair_asset.usda` 的几何体被直接内联进来。变体集消失了——只剩下当前选中变体的数据。在完全展平的文件上，你无法再切换变体。

### 各自的使用时机

**使用 `UsdUtils.FlattenLayerStack()` 的场景：**

- 你想调试子层冲突——在多个文件的干扰之外看清合并后的层长什么样
- 你需要交付文件，但希望接收方保留完整的引用与变体
- 你要把各部门层（anim + layout + fx）合并成一个文件，同时保持资产的模块化

**使用 `stage.Flatten()` 的场景：**

- 你要向外部方交付一个完全自包含、不依赖任何外部内容的文件
- 你需要把当前确切状态的快照烘焙下来用于归档
- 你要把内容交给不支持 USD 合成的渲染器或工具

### 代码

```python
from pxr import Usd, UsdUtils

stage = Usd.Stage.Open("shot.usda")

# Sublayer-only flatten — references and variants preserved
flat_sublayers = UsdUtils.FlattenLayerStack(stage)
flat_stage     = Usd.Stage.Open(flat_sublayers)

# Confirm reference still exists
chair = flat_stage.GetPrimAtPath("/World/Chair")
print(chair.GetMetadata("references"))   # still has reference arc

# Confirm variant set still exists
print(chair.GetVariantSets().GetNames()) # ["color"] — still switchable

# Full flatten — resolves everything
flat_full = stage.Flatten()
flat_stage_b = Usd.Stage.Open(flat_full)

chair_b = flat_stage_b.GetPrimAtPath("/World/Chair")
print(chair_b.GetMetadata("references"))     # None — reference gone
print(chair_b.GetVariantSets().GetNames())   # [] — variant set gone
print(chair_b.GetChildren())                 # [seat_geo, legs_geo] — inlined

# Save flat result to disk for delivery
flat_full.Export("delivery.usda")
# Original shot.usda completely untouched
```

### 关键心智模型

```
UsdUtils.FlattenLayerStack()
  "Merge the filing cabinet drawers into one drawer
   but keep all the folder tabs and references intact"

stage.Flatten()
  "Photocopy every single document in the cabinet
   into one pile — no folders, no tabs, just the final content"
```

> **用于调试时调用展平是安全的**——`stage.Flatten()` 返回的是一个**全新的** `SdfLayer` 对象，它绝不会修改原始 stage。你可以检查展平后的层，用完即弃。用于交付时，请对结果调用 `.Export()`。

---

## 5. 封装 — 资产结构原则

**封装**意味着资产把所需的全部 prim 都放在自己的层级之内。没有任何东西会伸到根 prim 之外去访问引用方场景中的数据。

### 为什么重要

当资产被引用进场景时，只有被引用 prim 之下的层级才会被带入。如果资产在该层级之外还有 prim——比如材质在 `/Looks/WoodMat` 而几何体在 `/Chair`——那么材质不会随引用一起被带入。

```
❌ Unencapsulated asset (broken):
/Chair                    ← referenced in
  /seat_geo  (Mesh)       ✅ brought in
/Looks                    ← NOT brought in (outside /Chair)
  /WoodMat   (Material)   ← geometry can't find its material!

✅ Encapsulated asset (correct):
/Chair                    ← referenced in
  /seat_geo  (Mesh)       ✅ brought in
  /Looks                  ✅ brought in (inside /Chair)
    /WoodMat (Material)   ✅ found correctly
```

### 资产结构规则

1. **设置 `defaultPrim`**——每个发布的资产都必须把 `defaultPrim` 设为其根 prim
2. **把材质留在资产根节点内**——用 `/Asset/Looks/`，而不是根部的 `/Looks/`
3. **使用相对路径**——用 `./textures/wood.png`，而不是 `C:/studio/textures/wood.png`
4. **只有一个根 prim**——`defaultPrim` 是引用的唯一入口

---

## 6. 变更处理与 SdfChangeBlock

每当你在 USD stage 上修改任何内容——设置属性值、添加 prim、更改变体选择——USD 都会立即向所有监听该 stage 的系统广播一条**变更通知**。

**谁在监听这些通知：**

- **Hydra**——渲染器。每条通知都会触发一次视口重绘。
- **场景图面板**——usdview 更新它的 prim 树。
- **资产管理系统**——把层标记为脏，需要保存。
- **自定义回调**——任何注册在 `stage.GetObjectsChangedNotice()` 上的东西。

对少量交互式编辑来说这没问题。一次平移改动 → 一次重绘 → 即时完成。问题出现在批量创作时：

```python
# Importing a 500-frame animation cache WITHOUT SdfChangeBlock
for frame in range(500):
    attr.Set(positions[frame], time=frame)
    # notification fires here — Hydra tries to redraw
    # notification fires here — Hydra tries to redraw
    # ... 500 times
    # UI freezes, import takes 10x longer than it should
```

每次 `Set()` 调用都会触发一条通知。Hydra 收到 500 次彼此独立的重绘请求。视口卡顿，导入过程拖沓，而中间 499 次重绘完全是白做的功。

### `Sdf.ChangeBlock` —— 把所有改动批处理成一条通知

`Sdf.ChangeBlock` 会把所有通知排队缓存，直到代码块退出，然后发送**一条合并后的通知**，覆盖块内发生的一切变更。

```python
from pxr import Sdf

# WITH SdfChangeBlock — one notification, one redraw
with Sdf.ChangeBlock():
    for frame in range(500):
        attr.Set(positions[frame], time=frame)
# ONE notification sent here — Hydra redraws once
# Import completes instantly
```

在代码块内部，数据依然会实时写入层——只有通知被延迟。因此不存在状态不一致的风险。

### 生产示例 —— 导入点缓存

```python
# Loading 240 frames of simulation data
with Sdf.ChangeBlock():
    for frame, frame_points in cache_data.items():
        points.Set(Vt.Vec3fArray(frame_points), time=frame)
# 240 frames written, 1 notification sent, viewport updates once
```

### 何时使用

| 场景 | 需要用 SdfChangeBlock 吗？ |
| ------------------------------------------------------- | ----------------------------- |
| UI 交互中的单次属性编辑 | 不需要——一条通知就够了 |
| 在循环中写入时间采样 | 需要——把整个循环包起来 |
| 导入仿真缓存 | 需要 |
| 用上千个位置填充 PointInstancer | 需要 |
| 以编程方式构建大型 prim 层级 | 需要 |

> **经验法则：** 只要你在 `for` 循环里进行创作，就把它包在 `Sdf.ChangeBlock()` 中。

### Stage 缓存（`UsdStageCache`）—— 避免重复合成

打开一个 USD stage 是很昂贵的操作——从磁盘读取所有层，并在数百个引用和子层上执行合成，可能要花上几秒钟。`UsdStageCache` 会在内存中保存已打开过的 stage 对象，因此第二次打开同一个文件时会立刻返回缓存的 stage，而不会重新执行合成。

```python
from pxr import Usd

cache = Usd.StageCache()

with Usd.StageCacheContext(cache):
    # First open — reads from disk, runs composition, stored in cache
    stage = Usd.Stage.Open("scene.usda")

    # Second open of the same file — returns cached stage instantly
    stage2 = Usd.Stage.Open("scene.usda")

    print(stage is stage2)   # True — exact same object
```

### 会看到过期/陈旧的输出吗？

不会——缓存保存的是对**活的 Stage 对象**的引用，而不是冻结的快照。缓存之后对 stage 所做的任何编辑，在从缓存中取回它时都会立刻可见。你始终看到的是当前状态。

唯一会看到陈旧数据的场景是：在 stage 被缓存之后，**磁盘上的文件被外部修改**了：

```python
stage = Usd.Stage.Open("scene.usda")   # reads disk at this moment
# someone edits scene.usda externally on disk
stage2 = Usd.Stage.Open("scene.usda")  # returns cached stage — disk changes NOT picked up

# To pick up external changes:
stage.Reload()   # re-reads all layers from disk
```

### 缓存能做和不能做的事

| | 行为 |
| ------------------------------ | ----------------------------------------------------------- |
| 存储 | 对活的 Stage 对象的引用——而不是副本 |
| 返回 | 同一个 Stage 对象——各处都能看到编辑 |
| 跨进程持久化 | 否——存在于内存中，进程结束即消失 |
| 感知外部磁盘改动 | 否——需要调用 `stage.Reload()` 重新从磁盘读取 |
| 缓存不同路径字符串 | 否——`"scene.usda"` 与 `"./scene.usda"` 是不同的键 |

### 它在生产环境中的价值

```python
# Render manager opens the same shot for 10 render passes
# Without cache: 10 composition runs x 3 seconds = 30 seconds
# With cache:    1 composition run + 9 instant lookups = 3 seconds
```

> **经验法则：** 只要同一个 stage 文件在单个进程中被打开超过一次，就使用 `UsdStageCache`——渲染管理器、带多个面板的流水线工具、批处理处理器。

---

## 7. 直接操作层

大多数 USD 创作都通过高层 `Usd` API 完成——`stage.DefinePrim()`、`attr.Set()`、`UsdGeom.Mesh.Define()`。它们是 schema 感知的，会自动处理合成、类型校验和回退值。

有时你需要绕过这些，直接操作原始的层数据。这就是 **Sdf 层**——你在手工构造层 spec，没有任何 schema 安全网。

### 两个层次的对照

```python
# HIGH-LEVEL — schema-aware, goes through Usd API
# USD handles type validation, composition, and fallbacks
stage = Usd.Stage.CreateNew("model.usda")
mesh  = UsdGeom.Mesh.Define(stage, "/World/Chair")
mesh.GetPointsAttr().Set(Vt.Vec3fArray([...]))

# LOW-LEVEL — raw layer data, goes through Sdf directly
# No schema awareness — you describe the structure manually
layer     = Sdf.Layer.CreateNew("model.usda")
prim_spec = Sdf.CreatePrimInLayer(layer, "/World/Chair")
prim_spec.specifier = Sdf.SpecifierDef
prim_spec.typeName  = "Mesh"

attr_spec = Sdf.AttributeSpec(
    prim_spec,
    "points",
    Sdf.ValueTypeNames.Point3fArray
)
attr_spec.default       = Vt.Vec3fArray([...])
attr_spec.documentation = "Mesh vertex positions."
```

两者产出的 USDA 输出完全相同。高层路径更安全，编写也更快。Sdf 路径则让你能精确控制写入层的内容。

### SdfPrimSpec —— 在层中定义一个 prim

```python
from pxr import Sdf

layer = Sdf.Layer.CreateNew("scene.usda")

# Define a prim directly in the layer
prim_spec = Sdf.CreatePrimInLayer(layer, "/World/Chair")
prim_spec.specifier = Sdf.SpecifierDef    # def / over / class
prim_spec.typeName  = "Xform"             # the schema type

# Read what was authored
print(prim_spec.specifier)   # Sdf.SpecifierDef
print(prim_spec.typeName)    # "Xform"
print(prim_spec.path)        # Sdf.Path("/World/Chair")
```

### SdfAttributeSpec（SdfPropertySpec 的子类）—— 在层中定义一个属性

```python
# Define an attribute on the prim spec
attr_spec = Sdf.AttributeSpec(
    prim_spec,                          # parent prim spec
    "sensor:temperature",               # attribute name
    Sdf.ValueTypeNames.Float            # value type
)

# Set schema-level properties on the attribute
attr_spec.default       = 20.0                    # fallback value
attr_spec.variability   = Sdf.VariabilityVarying  # animated or static
attr_spec.documentation = "Temperature in Celsius."

# Read back what was authored in this layer
print(attr_spec.default)        # 20.0
print(attr_spec.typeName)       # Sdf.ValueTypeNames.Float
print(attr_spec.documentation)  # "Temperature in Celsius."
```

### 你实际会在什么时候用它

| 场景 | 为什么用 Sdf 层 |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| 编写流水线校验器 | 需要检查原始层内容，而不是合成结果 |
| 不打开 stage 就构建一个层 | 程序化生成、测试夹具 |
| 在 usdGenSchema 生成的代码内部 | 生成的 C++ 内部使用 SdfPropertySpec 来注册 schema 属性 |
| 调试 PropertyStack 与 PrimStack | `GetPropertyStack()` 和 `GetPrimStack()` 返回的是 `SdfPropertySpec` 和 `SdfPrimSpec` 对象——理解它们有助于读懂输出 |

> **关键区别：** 高层 API（`attr.Set()`、`UsdGeom.Mesh.Define()`）是 schema 感知的——它了解类型、回退值和合成。Sdf 层是原始层数据——你是在没有任何 schema 校验的情况下直接写入某个文件的 spec 列表。两者在磁盘上产出的结果相同。

---

## 8. 完整的合成心智模型

当 USD 合成一个 prim 时，它会收集所有对该 prim 有意见的层中的 **PrimSpec**，按 LIVERPS 强度排序，然后合并出胜出的值：

```
1. Collect all PrimSpecs for /World/Chair across all layers
   (from sublayers, references, inherits, variants, specializes)

2. Order by LIVERPS strength:
   [Local opinions in root layer]           strength 1
   [Inherited from class prim]              strength 2
   [Active variant content]                 strength 3
   [Referenced asset opinions]              strength 4
   [Payload opinions]                       strength 5
   [Specialized class opinions]             strength 6 (weakest)

3. For each property: take the value from the strongest spec that has an opinion
   If no spec has an opinion → use schema fallback value

4. Result: the composed prim with its final resolved values
```

---

## 9. 关键要点

| 概念 | 需要记住的内容 |
| -------------------------- | ---------------------------------------------------------------------------- |
| **编辑目标** | 决定所有创作操作写入哪一层 |
| **默认编辑目标** | 根层——在多图层 stage 中创作前务必检查 |
| **会话层** | 始终最强。内存中。永不保存。`stage.GetSessionLayer()` |
| **稀疏覆盖** | `over` spec 只改动特定属性。非破坏性。 |
| **`stage.Flatten()`** | 返回解析了全部合成的新 `SdfLayer`。绝不修改源文件。 |
| **`FlattenLayerStack()`** | 只合并子层。引用与变体保持完整。 |
| **时间采样被保留** | 展平**不会**把动画烘焙成静态数值 |
| **变体被折叠** | 展平会把变体集折叠为当前选中的变体 |
| **封装** | 材质和所有 prim 都要放在资产根 prim 之内。使用相对路径。 |
| **defaultPrim** | 每个发布的资产都必须设置 |
| **SdfChangeBlock** | 把大量编辑批处理成一条通知——对性能至关重要 |
| **UsdStageCache** | 缓存已打开的 stage，避免重复的重新合成 |

---

_上一篇：[第 3 天 — 合成弧（第二部分）](day-03-composition-arcs-part-2.md)_  
_下一篇：[第 5 天 — Schema 与数据建模](day-05-schemas-and-data-modeling.md)_

---


### 第 5 天 — Schema 与数据建模


> 来源：`sparsha-2011/physical-ai-learning-journey` · `02-openUSD-cert/notes/day-05-schemas-and-data-modeling.md` · [原文链接](https://github.com/sparsha-2011/physical-ai-learning-journey/blob/main/02-openUSD-cert/notes/day-05-schemas-and-data-modeling.md) · 语言：英文原文 · 中译版



# 第 5 天 — Schema 与数据建模


> **OpenUSD NCP 认证学习笔记**  
> _USD Schema、Schema 类型、usdGenSchema、自定义 Schema、SdfFileFormat_

---

## 目录


1. [什么是 Schema？](#1-what-is-a-schema)
2. [IsA Schema 与 API Schema](#2-isa-schemas-vs-api-schemas)
3. [Schema 继承层次结构](#3-schema-inheritance-hierarchy)
4. [创建自定义 Schema](#4-creating-custom-schemas)
5. [usdGenSchema 工作流程](#5-the-usdgenschema-workflow)
6. [TfType 注册](#6-tftype-registration)
7. [自定义文件格式插件 — SdfFileFormat](#7-custom-file-format-plugins-sdffileformat)
8. [Model Kind — 按流水线角色对 Prim 分类](#8-model-kinds-classifying-prims-by-pipeline-role)
9. [自定义 Model Kind — UsdModelKindRegistry](#9-custom-model-kinds-usdmodelkindregistry)
10. [考试模式识别 — 排除法指南](#10-exam-pattern-recognition-elimination-guide)
11. [关键要点](#11-key-takeaways)

---

## 1. 什么是 Schema？


**Schema** 是对某类 prim 类型的正式定义 —— 它有哪些属性、这些属性的类型和默认值是什么，以及它如何参与 USD 的类型系统。正是 Schema 让 `UsdGeom.Sphere` 成为球体、让 `UsdLux.DistantLight` 成为平行光。

USD 自带面向常见 3D 概念（`Mesh`、`Camera`、`Material`、`DistantLight`）的内置 Schema。当你的流水线需要 USD 中不存在的类型 —— 一个 `TemperatureSensor`、一条 `ConveyorBelt`、一台 `ShotCamera` —— 你就要创建一个**自定义 Schema**。

---

## 2. IsA Schema 与 API Schema


USD 有两种本质不同的 Schema 类型：

### IsA Schema（有类型的 Schema）


IsA Schema **定义一个 prim 的类型**。它设置 `typeName` 元数据。一个 prim 恰好拥有**一个** IsA Schema —— 它要么是 Mesh，要么是 Sphere，不可能是两者。

```usda
def Mesh "Chair" {     # typeName = "Mesh" — this prim IS a Mesh
    ...
}
```

```python
prim.IsA(UsdGeom.Mesh)       # True — prim is of type Mesh
prim.GetTypeName()            # "Mesh"
```

### API Schema


API Schema **为 prim 增补**额外的属性和行为，而不改变它的类型。一个 prim 可以同时应用**多个** API Schema，它们会列在 `apiSchemas` 元数据中。

```usda
def Mesh "Character" (
    prepend apiSchemas = ["PhysicsRigidBodyAPI", "MotionAPI"]
    # Still a Mesh — but with physics and motion APIs applied
) { }
```

```python
prim.HasAPI(UsdPhysics.RigidBodyAPI)   # True
prim.IsA(UsdGeom.Mesh)                 # Still True
```

| 属性                | IsA Schema            | API Schema                   |
| ------------------- | --------------------- | ---------------------------- |
| 设置 `typeName`     | ✅ 是                 | ❌ 否                        |
| 每个 prim 的数量    | 恰好 1 个             | 多个                        |
| 检查方式            | `prim.IsA()`          | `prim.HasAPI()`              |
| USDA 中的声明形式   | `def TypeName "name"` | `prepend apiSchemas = [...]` |

---

## 3. Schema 继承层次结构


所有 USD Schema 最终都继承自 `UsdSchemaBase`。这个层次结构决定了一个 Schema 能继承到哪些能力。

```
UsdSchemaBase                    ← 所有 schema 的根
├── UsdTyped                     ← 所有 IsA（typed）schema 的基类
│   ├── UsdGeomImageable         ← 所有可渲染 prim（visibility、purpose）
│   │   ├── UsdGeomXformable     ← 所有可变换 prim
│   │   │   ├── UsdGeomGprim     ← 所有几何图元
│   │   │   │   ├── UsdGeomMesh
│   │   │   │   ├── UsdGeomSphere
│   │   │   │   └── ...
│   │   │   ├── UsdGeomCamera
│   │   │   └── UsdLuxLight      ← 所有灯光
│   │   └── ...
│   └── UsdShadeMaterial
└── UsdAPISchemaBase             ← 所有 API schema 的基类
    ├── UsdGeomMotionAPI
    ├── UsdPhysicsRigidBodyAPI
    └── ...
```

### 为自定义 Schema 选择正确的基类


| 基类                | 何时使用                                                     |
| ------------------ | ------------------------------------------------------------ |
| `UsdSchemaBase`    | ❌ 几乎从不使用 —— 需要手动实现全部内容                       |
| `UsdTyped`         | ✅ 作为新 prim 类型的标准 IsA Schema                          |
| `UsdGeomImageable` | ✅ 需要 visibility 和 purpose 的自定义可渲染对象               |
| `UsdGeomXformable` | ✅ 需要变换能力的自定义对象                                   |

> **考试陷阱：**"直接继承 UsdSchemaBase" 通常是错误答案。正确的基类是 `UsdTyped`（用于标准的自定义 IsA Schema）；如果该 Schema 是可渲染对象，则为 `UsdGeomImageable`。

---

## 4. 创建自定义 Schema


USD 自带面向常见 3D 概念的 Schema —— `Mesh`、`Sphere`、`Material`、`DistantLight`。这些覆盖了通用场景。但一家工厂自动化公司需要 `TemperatureSensor` 和 `ConveyorBelt` 这样的 prim，一家影视工作室则需要 `ShotCamera` 和 `CharacterRig`。这些在 USD 中开箱即用并不存在。

自定义 Schema 让你可以把新的 prim 类型加入进来，成为**USD 的正式一分子** —— 享有与内置 Schema 相同的类型安全、API 生成、schema fallback 以及工具集成能力。

### 普通属性与自定义 Schema 的对比


| 能力                        | 普通自定义属性              | 自定义 Schema                   |
| --------------------------- | --------------------------- | ------------------------------- |
| `prim.IsA(TemperatureSensor)` | ❌ 无类型检查            | ✅ 工作正常                     |
| Schema fallback 值          | ❌ 未设置时返回 `None`      | ✅ 返回定义的默认值             |
| 生成的 Python/C++ API       | ❌ 手动 `GetAttribute("name")` | ✅ `sensor.GetTemperatureAttr()` |
| usdview 内省                | ❌ 任意数据，没有 schema 信息 | ✅ 带类型的完整属性列表        |
| 创作期校验                  | ❌ 静默错误                 | ✅ 在定义时即做类型检查          |
| 继承链已知                  | ❌ 否                       | ✅ `IsA(UsdGeomXform)` 同样有效  |

### 何时使用


| ✅ 应当使用自定义 Schema 的情形        | ❌ 不适用自定义 Schema 的情形      |
| ------------------------------------- | -------------------------------- |
| 跨团队共享的标准类型                  | 临时的一次性流水线属性           |
| `prim.IsA()` 和 `prim.HasAPI()` 必须可用 | 不在工具之间共享的数据           |
| 需要 schema fallback 值               | 快速原型开发（先用普通属性）     |
| 需要完整的 C++ 与 Python API          | 一次性迁移脚本                   |

自定义 Schema 定义在 `schema.usda` 文件中，该文件描述这个 Schema 的类、它继承自什么，以及它提供哪些属性及其类型和默认值。

### `schema.usda` 文件结构


```usda
#usda 1.0
(
    subLayers = [
        @usd/schema.usda@       # inherit from base USD schemas
    ]
)
#usdGenSchema config describing how to name the generated code it has no runtime existence
over "GLOBAL" (
    customData = {
        string libraryName   = "acmeSensors"    # library name
        string libraryPrefix = "AcmeSensor"     # C++ class prefix
    }
) {}

# Custom IsA schema — inherits from Xform (which is a UsdTyped)

class Xform "TemperatureSensor" (
    customData = {
        string className = "TemperatureSensor"
    }
    doc = """A prim representing a physical temperature sensor."""
    inherits = </Xform>
) {
    float  sensor:temperature = 20.0      # default = 20°C
    float  sensor:minRange    = -40.0
    float  sensor:maxRange    = 125.0
    string sensor:serialNumber = ""
}
```

---

## 5. usdGenSchema 工作流程


`usdGenSchema` 是代码生成工具，它把 `schema.usda` 定义转换为可编译的 C++ 代码和 Python 绑定。理解 TfType 在每一步中处于什么位置至关重要 —— 这能解释每一步为什么存在，以及跳过其中任何一步会带来什么问题。

```
STEP 1  编写 schema.usda
        ─────────────────────────────────────────────────────
        定义 Schema 类、基类以及属性。
        这是你的唯一事实来源 —— 人类可读的意图。

        class Xform "TemperatureSensor" (
                ↑           ↑
            基类         Schema 类（你正在创建的新类型）
            inherits = </Xform>
        ) {
            float sensor:temperature = 20.0
        }

        TfType 相关性：NONE YET（尚不存在）
        该类型在运行时的任何地方都不存在。
        它只是写在一个文本文件里的意图。

        ↓

STEP 2  运行 usdGenSchema schema.usda
        ─────────────────────────────────────────────────────
        usdGenSchema 读取 schema.usda 并生成：

          acmeSensors.h           ← C++ 类声明
          acmeSensors.cpp         ← C++ 实现
                                     内含 TF_REGISTRY_FUNCTION  ← 关键产物
          wrapAcmeSensors.cpp     ← Python 绑定
          plugInfo.json           ← 包含插件发现元数据的清单文件

        TfType 相关性：TF_REGISTRY_FUNCTION 在这里生成
        usdGenSchema 会自动写出注册宏。
        你永远不需要手写 TF_REGISTRY_FUNCTION。
        它会在下一步被编译进库中。

        生成的源码中 TF_REGISTRY_FUNCTION 的样子：

          TF_REGISTRY_FUNCTION(TfType) {
              TfType::Define<AcmeSensors_TemperatureSensor,
                             TfType::Bases<UsdGeomXform>>();
          }

        ↓

STEP 3  将 C++ 编译为共享库
        ─────────────────────────────────────────────────────
        cmake + make → acmeSensors.so (Linux) / acmeSensors.dll (Windows)

        TfType 相关性：TF_REGISTRY_FUNCTION 现在已在二进制中
        该宏被编译进 .so 文件。
        它存在于磁盘上，但尚未运行。
        TfType 注册表中该类型仍为空。

        ↓

STEP 4  部署插件
        ─────────────────────────────────────────────────────
        把 acmeSensors.so + plugInfo.json 放到某个目录中。
        /path/to/acmeSensors/
          ├── acmeSensors.so       ← 编译好的库（内含 TF_REGISTRY_FUNCTION）
          └── plugInfo.json        ← 发现元数据（告诉 USD 这个库存在）

        设置 PXR_PLUGINPATH_NAME=/path/to/acmeSensors/

        TfType 相关性：发现已启用，注册仍未完成
        USD 现在知道去哪里找这个库（plugInfo.json）。
        但 TF_REGISTRY_FUNCTION 仍然没有运行。
        注册表中 TemperatureSensor 仍为空。
        这正是"只提供清单文件"是错误做法的原因 —— 发现 ≠ 注册。

        ↓

STEP 5  在运行中的进程里首次使用该类型
        ─────────────────────────────────────────────────────
        首次调用 prim.IsA(TemperatureSensor)。
        USD 检查注册表 → 未找到 → 加载 acmeSensors.so。
        加载 .so 会触发 TF_REGISTRY_FUNCTION 运行。

        TfType 相关性：注册就发生在此时
        TF_REGISTRY_FUNCTION 执行：
          创建注册表条目：
          TemperatureSensor → Xform → Xformable → Imageable → Typed → SchemaBase

        从此刻直到进程结束：
          prim.IsA(TemperatureSensor)         → True
          prim.IsA(UsdGeom.Xform)             → True
          sensor.GetTemperatureAttr().Get()   → 20.0
          usdview 显示全部 schema 属性 → True

        进程结束 → 注册表消失。
        下次进程启动时又从第 4 步开始。
```

### 这三种方式为何会存在


核心问题是：**一个正在运行的进程如何知道你的自定义 Schema？**

TfType 注册表在每次进程启动时都会重新构建。必须有某种东西告诉 USD"这个自定义类型存在，这是它的继承链"。这三种方式就是针对不同环境控制者的三种不同答案。

### 方法 1 — 通过 PXR_PLUGINPATH_NAME 部署独立插件


**背景：** 你是一家工作室或流水线团队。你构建了一个自定义 Schema。你并不拥有美术师所使用的那些应用 —— Maya、Houdini、usdview、自定义渲染器。你无法重新编译其中任何一个。你只希望自己的 Schema 在各处都能正常工作。

**工作原理：**

```
你构建：   acmeSensors.so + plugInfo.json
           放在 /studio/plugins/acmeSensors/

每台机器上运行：
  export PXR_PLUGINPATH_NAME=/studio/plugins/acmeSensors/

进程启动时：
  USD 扫描 PXR_PLUGINPATH_NAME
  找到 plugInfo.json
  记录下这个库存在
  首次使用 TemperatureSensor 时 -> 加载 acmeSensors.so
  TF_REGISTRY_FUNCTION 运行 -> 类型完成注册
```

**你会使用它的原因：**

```
你希望在不触碰任何应用的前提下更新 Schema
  -> 只需在共享盘上替换 acmeSensors.so
  -> 所有进程在下次启动时都会加载它

你使用许多不同的应用（Maya、Houdini、usdview、自定义工具）
  -> 每台机器设置一次 PXR_PLUGINPATH_NAME
  -> 在所有这些应用中同时生效

你希望有部门专属的 Schema
  -> /studio/plugins/vfx/   给 VFX 团队
  -> /studio/plugins/anim/  给动画团队
  -> PXR_PLUGINPATH_NAME 按环境指向对应的目录
```

**权衡取舍：**

```
必须在每一个环境中都正确设置 PXR_PLUGINPATH_NAME
  -> 渲染农场节点
  -> 美术师工作站
  -> CI/CD 流水线
  -> 客户交付机器

如果没有设置 -> Schema 未知 -> IsA() 返回 False
                                   -> fallback 返回 None
                                   -> 静默失败
```

### 方法 2 — 直接链接进应用


**背景：** 你正在构建一个应用 —— 一个 Maya 插件、一个 Houdini HDA、一个自定义流水线工具、一个游戏引擎插件。你掌控构建流程。这个 Schema 不是可选的 —— 它本身就是应用的一部分。没有它，这个应用就不成立。

**工作原理：**

```
构建时：
  acmeSensors.cpp 被直接编译进 MyApp 二进制

不存在单独的 .so 文件。
不需要 plugInfo.json 来做发现。
当 MyApp 进程启动时：
  TF_REGISTRY_FUNCTION 作为应用启动流程的一部分运行
  在任何 USD stage 打开之前 Schema 就已注册
  始终可用 —— 不可能缺失
```

**你会使用它的原因：**

```
游戏工作室的 Maya 插件：
  插件就是 Schema —— 两者不可分割
  美术师安装 Maya 插件 -> Schema 始终存在
  不需要环境变量 -> 不可能出现配置错误

机器人流水线的 Houdini HDA：
  HDA 中包含传感器 Schema
  美术师安装 HDA -> Schema 正常工作
  没有单独的部署步骤

自定义流水线应用：
  该应用就是专门为这个 Schema 编写的
  发布应用 -> Schema 随应用一起发布
  没有外部依赖

DCC 工具厂商（Autodesk、SideFX）：
  他们把 USD 支持 + 常见 Schema 编译进自己的工具
  你安装 Maya -> UsdGeom、UsdShade 已经注册好
  内置 Schema 不需要 PXR_PLUGINPATH_NAME
```

**权衡取舍：**

```
不重新构建并重新分发应用就无法更新 Schema
  -> schema v1.2 需要发布 MyApp 的新版本
  -> 对于快速迭代不够灵活

美术师必须升级应用才能拿到新 Schema
  -> 版本管理变成应用版本管理问题
```

### 方法 3 — 直接编译进 USD 自身的构建


**背景：** 你是一家大型工作室，维护着 **USD 的自定义分支（fork）**。工作室里的每个工具都是针对你的自定义 USD 构建的 —— 而不是 Pixar 的原版 USD。这个 Schema 对你的流水线如此基础，以至于它应该属于 USD 的基础部分，而不是某个插件或某个应用。

**工作原理：**

```
你 fork USD 仓库
把 Schema 源文件加入 USD 构建系统
用内置你的 Schema 的方式构建 USD 本身

每个针对你的 USD 构建的工具都自动拥有该 Schema
  -> 不需要 plugInfo.json
  -> 不需要 PXR_PLUGINPATH_NAME
  -> 不需要应用级链接
  -> Schema 就像 UsdGeom 属于 USD 一样属于 USD
```

**你会使用它的原因：**

```
你有一个如此基础的 Schema，它就像内置 Schema 一样
  -> 每个工具都需要它
  -> 把它当作插件处理会带来不必要的复杂度

你掌控整条工具链
  -> 你针对你的 USD 构建 Maya 的 USD 插件
  -> 你针对你的 USD 构建 Houdini 的 USD 插件
  -> 你针对你的 USD 构建渲染器
  -> 它们全都免费获得该 Schema

示例：某大型工作室创建了一个 "StudioPrim" 基础 Schema
  -> 工作室里的每个 prim 都带有流水线元数据
  -> 把它作为独立插件部署是荒谬的
  -> 它应该属于基础部分

Pixar 自己也用这种方式实现内部 Schema
  -> 有些 Schema 只存在于 Pixar 的 USD 构建中
  -> 从不出现在开源发行版里
```

**权衡取舍：**

```
需要维护一个 USD 分支
  -> 每次 Pixar 发布新的 USD 版本
  -> 你都必须把自己的改动合并进新版本
  -> 工程成本高昂

灵活性最低：
  -> 更新 Schema = 重建整个 USD
  -> 重建 USD = 重建所有链接它的工具
  -> 无法在生产环境中给 Schema 打补丁

只适合非常稳定、非常基础的 Schema
  -> 不适合经常变动的 Schema
```

### 并排对比 — 该用哪一种


```
要问的问题：                              答案 -> 方法

"我拥有这些应用吗？"
  不拥有 —— 我用第三方工具              -> 方法 1（插件）
  拥有 —— 我自己构建应用                 -> 方法 2（链接进应用）
  拥有 —— 我自己构建 USD                 -> 方法 3（USD 分支）

"Schema 多久变一次？"
  频繁 —— 快速迭代                      -> 方法 1（直接替换 .so）
  偶尔 —— 与应用发布绑定                -> 方法 2（发布新应用版本）
  很少 —— 非常稳定的基础                -> 方法 3（USD 分支）

"谁掌控环境？"
  许多机器、许多团队                    -> 方法 1（环境变量方案）
  由应用安装控制                        -> 方法 2（内置）
  工作室掌控整条工具链                  -> 方法 3（USD 分支）

"部署单元是什么？"
  共享盘上的插件文件                    -> 方法 1
  应用安装包                            -> 方法 2
  完整的 USD 构建                       -> 方法 3
```

### 真实世界示例


```
方法 1 - 多数工作室
  流水线 TD 构建 TemperatureSensor Schema
  把 .so 放到 NFS 共享盘上
  在工作室环境中设置 PXR_PLUGINPATH_NAME
  在 Maya、Houdini、usdview、渲染器中同时生效
  更新 Schema = 替换 .so 文件 = 完成

方法 2 - DCC 插件开发者
  Autodesk 构建 Maya 的 USD 支持
  UsdGeom、UsdShade、UsdLux 被编译进 Maya USD 插件
  你安装 Maya -> 这些 Schema 始终可用
  它们不需要 PXR_PLUGINPATH_NAME

  某游戏工作室构建自定义的 Unreal Engine USD 导入器
  其游戏专用 Schema 被编译进插件
  美术师安装插件 -> 在 Unreal 中即可使用这些 Schema

方法 3 - 拥有 USD 分支的大型影视工作室
  Disney/ILM/Pixar 维护自己的 USD 构建
  全工作室范围的元数据 Schema 被内置进他们的 USD
  每个针对其 USD 构建的工具都自动拥有它
  该 Schema 与 UsdGeom 本身一样基础
```

### 每种方式的一句话总结


```
方法 1 - "我不拥有这些应用，设个环境变量就行"
          最灵活、最常见，在设置了 PXR_PLUGINPATH_NAME 的地方都能工作

方法 2 - "Schema 随我的应用一起发布"
          无需部署步骤，始终存在，更新需要发布新应用版本

方法 3 - "对我们来说 Schema 就是 USD 的一部分"
          最透明，维护成本最高，只适合非常稳定的 Schema
```

> **考试陷阱：**"把自定义 Schema 编译成独立插件供 USD 运行时加载" 被判为错误，并不是因为独立插件是错的 —— 它们是有效且常见的 —— 而是因为这种说法暗示它是**唯一**的部署方式。正确的表述是：Schema 可以作为独立插件部署、直接链接进应用，或编译进 USD 构建。独立插件方案并非必需。

### TfType 全景视图


```
schema.usda          →   usdGenSchema   →   acmeSensors.so    →   运行中的进程
(文本文件)               (代码生成)         (二进制)               (内存中的注册表)

"TemperatureSensor       TF_REGISTRY_      TF_REGISTRY_           TemperatureSensor
 继承 Xform"          →   FUNCTION         FUNCTION             → Xform
                        写在       →      编译进       →        → Xformable
                        .cpp            .so                   → Imageable
                                        (休眠状态)             → Typed
                                                                 → SchemaBase
                    [意图]          [已生成]         [在磁盘上]  [在内存中生效]
```

### 为什么不只用 Python？


Python 没有机制来运行 `TF_REGISTRY_FUNCTION`。没有 `.so` 二进制文件、没有编译好的宏，也没有任何东西会在加载时写入 TfType 注册表。类型名以字符串形式存在，但注册表永远不会被填充。

| 能力                              | 仅用 Python               | 通过 usdGenSchema 使用完整 C++ |
| --------------------------------- | ------------------------- | ------------------------------ |
| 二进制中的 `TF_REGISTRY_FUNCTION` | 无                        | 第 2 步自动生成                |
| `prim.IsA()`                     | False 或报错              | 正常工作 —— 注册表已填充        |
| 继承链已知                        | 否                        | 注册表中有完整链条             |
| Schema fallback 值                | `Get()` 返回 None         | 返回 schema 默认值             |
| 生成的访问器方法                  | 手动 `GetAttribute("name")`| `GetTemperatureAttr()`         |
| 适用场景                          | 仅用于原型开发            | 生产流水线                    |

---

## 6. TfType 注册


### TfType 解决什么问题

当 USD 读取一个包含 `def TemperatureSensor "Sensor_001"` 的文件时，它看到的只是一个字符串。如果没有某个东西告诉 USD 这个字符串的含义，它就无法回答：

- 这个 prim 有哪些属性？
- 它继承自什么？
- 适用哪些回退值（fallback）？
- `prim.IsA(UsdGeom.Xform)` 是否返回 True？

那个"东西"就是 **TfType 注册表（registry）** —— USD 的运行时类型标识系统。注册正是把一个字符串变成有意义的关键：它带来完整的继承链、回退值以及自动生成的 API。

> **TfType 在工作流程中的位置：** 见上文第 5 节。`TF_REGISTRY_FUNCTION` 在第 2 步（由 usdGenSchema）生成，在第 3 步编译，在第 4 步部署，并最终在第 5 步该类型首次被使用时**运行**。注册表只在第 5 步被填充。

> **类比 —— 移民数据库**
>
> 把 USD 想象成一个边境查验系统。护照上写着 "citizen of AcmeSensors Corp."（AcmeSensors 公司的公民）。
> 在边境系统到某个注册表里查证之前，这个字符串毫无意义——
> 而那个注册表知道：这位公民拥有哪些权利、会说哪些语言？
>
> TfType 注册表就是那个数据库。没有它，`TemperatureSensor` 就是一本
> 系统从未听说过的国家签发的护照——字符串确实存在，
> 却不携带任何含义。有了它，USD 才知道完整的档案信息。
>
> `schema.usda` 是护照申请表。`usdGenSchema` 是打印护照的工序。
> `TF_REGISTRY_FUNCTION` 是护照被盖章并录入数据库的那一刻。
> `plugInfo.json` 则是护照签发机构所在的地址。

### 未注册 与 已注册 的对比


```
WITHOUT TfType registration          WITH TfType registration
────────────────────────────────     ────────────────────────────────
prim.GetTypeName()                   prim.GetTypeName()
→ "TemperatureSensor"                → "TemperatureSensor"
  (just a string, no meaning)          (meaningful — registry knows it)

prim.IsA(TemperatureSensor)          prim.IsA(TemperatureSensor)
→ False or AttributeError            → True

prim.IsA(UsdGeom.Xform)             prim.IsA(UsdGeom.Xform)
→ False (ancestry unknown)           → True (ancestry chain known)

sensor.GetTemperatureAttr().Get()    sensor.GetTemperatureAttr().Get()
→ None (no schema fallback)          → 20.0 (schema fallback works)

usdview:                             usdview:
→ "unknown schema type"              → all attributes listed with types
→ no attribute listing               → schema documentation visible
```

同一个 USD 文件。同一个 prim。区别完全在于本进程中注册表是否已被填充。

### usdGenSchema 内部用到了什么 —— SdfPropertySpec


当 `usdGenSchema` 生成用于注册你的 schema 的 C++ 代码时，它还会生成使用 `SdfPropertySpec` 和 `SdfPrimSpec` 的代码，用来描述该 schema 类型拥有哪些属性 —— 它们的名称、类型、默认值以及文档说明。

这正是为什么即使从未调用过 `Set()`，`sensor.GetTemperatureAttr().Get()` 也会返回 `20.0` —— 生成的代码在 schema 定义阶段就用 `SdfAttributeSpec` 注册了该默认值，而不是在创作（authoring）阶段。

你会在以下情形直接与 `SdfPropertySpec` 打交道：

- 读取 `GetPropertyStack()` 或 `GetPrimStack()` 的结果 —— 两者都返回 Sdf spec 对象
- 编写需要检查图层原始内容的流水线校验器
- 不依赖完整 stage，直接向图层中创作内容

> **完整解释与代码示例：** [第 4 天 第 3b 节 —— 直接操作图层](day-04-advanced-composition.md#3b-working-directly-with-layers--sdfprimspec-and-sdfpropertyspec)

---

### 两个组成部分 —— 两者缺一不可


注册恰好需要两样东西协同工作，单独任何一样都不够。

**组成部分 1 —— `plugInfo.json`（发现）**

这个文件告诉 USD："这里有一个插件，当有人需要 `TemperatureSensor` 时就去加载它。"它是该库的_地址_，本身并不执行注册。

```json
{
  "Plugins": [
    {
      "Name": "acmeSensors",
      "LibraryPath": "acmeSensors.so",
      "Types": {
        "AcmeSensors_TemperatureSensor": {
          "bases": ["UsdGeomXform"],
          "alias": { "UsdSchemaBase": "TemperatureSensor" }
        }
      }
    }
  ]
}
```

**组成部分 2 —— `TF_REGISTRY_FUNCTION`（真正的注册）**

这个 C++ 宏由 `usdGenSchema` 在生成的源码中产生。它在共享库被加载进内存时运行，把该类型写入 TfType 注册表。

```cpp
// Generated by usdGenSchema — do not write manually
// Runs when acmeSensors.so is loaded into the process

TF_REGISTRY_FUNCTION(TfType)
{
    TfType::Define<AcmeSensors_TemperatureSensor,
                   TfType::Bases<UsdGeomXform>>();
    // After this line:
    // Registry knows: TemperatureSensor → Xform → Xformable → Imageable → Typed → SchemaBase
}
```

> **类比 —— 门牌地址 vs 本人到场**
>
> `plugInfo.json` 就像把自己的地址登记在通讯录上 —— 它告诉别人
> 去哪里找你。但在你开门自我介绍之前，
> 你并没有在这个社区登记备案。
>
> `TF_REGISTRY_FUNCTION` 就是"本人到场"的那一刻。地址（manifest）
> 和自我介绍（macro）两者都要有，缺一则毫无作用。

> **考试陷阱 —— 只靠 manifest 文件：**"通过继承 UsdGeomImageable 实现 schema
> 并**仅**通过插件 manifest 文件注册它"是**错误**的。
> manifest 只让类型能够被**发现**。C++ 源码中的 `TF_REGISTRY_FUNCTION`
> 才执行真正的注册。两者都需要。

---

### 注册何时运行 —— 按进程计算，而非永久有效


这是最常被误解的方面。注册**不会**在进程之间持久化，也从不写入磁盘。每个新进程都会通过加载插件来重建注册表。

```
Process lifecycle for a custom schema type:

  Process starts
       |
       v
  USD scans PXR_PLUGINPATH_NAME
  Reads all plugInfo.json files
  Notes which plugins exist — does NOT load them yet
       |
       v
  Someone calls prim.IsA(TemperatureSensor)
       |
       v
  Registry check: "do I know TemperatureSensor?"
  Answer: No → "plugInfo.json says there's a library for this"
       |
       v
  acmeSensors.so loads into memory
  TF_REGISTRY_FUNCTION runs
  Type written into registry
       |
       v
  IsA(), fallbacks, API all work
  (for the lifetime of THIS process only)
       |
       v
  Process ends → registry gone from memory
  Next process starts from zero
```

> **类比 —— 场地的签到名单**
>
> 每当一场新活动开始（一个新进程），场地都会准备一份全新的签到名单。
> 插件库就像一位客人，活动每开一次都必须在门口签到。
> 签到之后，他在整场活动中都可以自由走动。
> 活动结束，名单就被丢弃 —— 下一场活动还得重新签到。
>
> 这正是为什么每一个使用你的自定义 schema 的环境都必须设置
> `PXR_PLUGINPATH_NAME` —— 每一个渲染农场节点、每一台美术师工作站、每一个 CI runner。
> 每个新进程都需要找到该插件并重新完成注册。

### 未部署插件时会发生什么


如果同事的 `PXR_PLUGINPATH_NAME` 中没有该插件就打开你的 USD 文件：

```python
# The raw data is still readable — the file is not corrupted
prim.GetTypeName()                             # "TemperatureSensor" — string is there
prim.GetAttribute("sensor:temperature").Get()  # 23.5 — raw value readable

# But schema knowledge is gone
prim.IsA(TemperatureSensor)                    # False — type unknown
prim.IsA(UsdGeom.Xform)                        # False — ancestry unknown
sensor.GetTemperatureAttr()                    # AttributeError — API not available
sensor.GetTemperatureAttr().Get()              # None — no fallback
```

文件并没有损坏，原始数据依然可读。但没有插件，USD 就无法解释这个类型 —— 没有继承、没有回退值、没有生成的 API。在注册表被填充之前，类型名只是一串字符串。

---

### TfType 考试陷阱汇总


| Option phrasing                                               | Verdict | Why                                                          |
| ------------------------------------------------------------- | ------- | ------------------------------------------------------------ |
| "仅通过插件 manifest 文件注册"                               | 错误    | 还需要 C++ 源码中的 `TF_REGISTRY_FUNCTION`                  |
| "纯 Python 的 schema"                                        | 错误    | 没有 `TF_REGISTRY_FUNCTION` —— `IsA()` 和回退值都无法工作  |
| "只做 Token 注册而不与 schema 关联"                          | 错误    | 仅靠 Token = 没有继承、没有回退值、没有 API                 |
| "修改 USD 核心源码来添加该类型"                              | 错误    | 插件系统的存在正是为了完全避免改动核心                     |
| "用 UsdSchemaRegistry 动态加载而无需重新编译"                | 错误    | 仍需要插件机制或编译期注册                                  |
| "用 TfType 注册并通过 PXR_PLUGINPATH_NAME 部署"               | 正确    | 两个组成部分都必需                                          |
| "继承 UsdSchemaBase 或它的派生类"                            | 正确    | UsdTyped 和 UsdGeomImageable 正是从 UsdSchemaBase 派生而来 |

---

## 7. 自定义文件格式插件 —— SdfFileFormat


**文件格式插件**教会 USD 读写一种新的文件类型（`.abc`、`.fbx`、`.myformat`）。它与自定义 schema 完全独立 —— schema 定义 prim 类型的含义；文件格式插件定义数据如何从文件中读出和写入。

```
UsdSchema   = defines what scene data IS (prim types, attributes, meaning)
SdfFileFormat = defines how data is READ and WRITTEN to/from a file format
```

### 实现步骤


```
1. Create a C++ class inheriting from SdfFileFormat
   class MyFormatPlugin : public SdfFileFormat { ... }

2. Implement required methods:
   bool Read(SdfLayer*, const string& resolvedPath, bool metadataOnly)
   bool WriteToFile(const SdfLayer&, const string& filePath, ...)

3. Register with TfType:
   TF_REGISTRY_FUNCTION(TfType) {
       TfType::Define<MyFormatPlugin,
                      TfType::Bases<SdfFileFormat>>();
   }

4. Declare in plugInfo.json for automatic discovery

5. When USD opens a .myformat file:
   → Looks up registered SdfFileFormat plugins
   → Finds MyFormatPlugin (registered for .myformat)
   → Calls MyFormatPlugin.Read() to translate to SdfLayer
   → Stage composes normally from that point
```

插件部署可以使用[这里](#why-these-three-methods-exist-at-all)提到的任意一种方式来完成。

### ArResolver —— 在文件 I/O 期间处理外部引用


当你的文件格式包含**对外部资产的引用**（贴图、子文件、被引用的图层）时，插件必须与 USD 的资产解析系统 **`ArResolver`** 集成，才能正确定位这些文件。

```
Without ArResolver integration:
  MyFormat file contains: texture = "textures/wood.png"
  Plugin reads raw string "textures/wood.png" — but WHERE is it?
  Relative to what? The answer depends on the resolver context.

With ArResolver integration:
  Plugin calls ArResolver to resolve "textures/wood.png"
  → Resolver applies search paths, asset remapping, version pinning
  → Returns the actual absolute path to the correct file
  → File loading works correctly in all deployment environments
```

```cpp
// Inside your SdfFileFormat::Read() implementation:
ArResolver& resolver = ArGetResolver();
ArResolverContext ctx = resolver.GetCurrentContext();

// Resolve asset paths from the file using the resolver
std::string resolved = resolver.Resolve("textures/wood.png");
// resolved = "/project/assets/textures/wood.png"
```

> **注意 1：**"通过实现自定义锁机制来确保线程安全"是**错误**的。并发访问由 USD 核心管理 —— 文件格式插件不实现自己的锁。这是多余的，已经在更高层级处理。

> **注意 2：**"在插件中嵌入自定义的 USD stage 缓存"是**错误**的。Stage 缓存由 USD 核心和客户端管理，而不是放在文件格式插件内部。嵌入一个会造成不一致。

### 错误做法


| Wrong approach                                 | Why it's wrong                                                                                               |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| 重写 `UsdStage::Open()`                       | 静态方法，本就不是为重写而设计的。文件加载发生在 `SdfLayer` 层，而非 `Stage` 层。                         |
| 修改 USD 核心源码                             | USD 的设计初衷就是通过插件实现可扩展。改动核心会破坏兼容性。                                               |
| 为文件格式创建 `UsdSchema`                    | Schema 定义的是场景描述类型，并不控制文件 I/O。                                                            |
| 在 Read/Write 中实现自定义线程锁              | 并发访问由 USD 核心管理 —— 插件不需要自定义锁                                                               |
| 在插件内部嵌入 stage 缓存                     | Stage 缓存属于 USD 核心/客户端层级 —— 不该放在文件格式插件内部                                             |
| 仅用 `UsdUtils` 解析该格式                    | UsdUtils 提供的是工具函数，并**不能**替代实现 `SdfFileFormat` 方法                                        |
| 为该格式实现 `UsdStage` 子类                  | UsdStage 与格式无关 —— 文件格式 I/O 是 `SdfFileFormat` 的职责                                              |

---

## 8. Model Kind —— 按流水线角色对 Prim 分类


**model kind**（模型种类）是 prim 上的一个元数据标签，用来描述它的
**在流水线中的角色** —— 不是它几何上长什么样，
而是它在场景装配层次结构中承担什么职能。

```python
from pxr import Usd

model_api = Usd.ModelAPI(prim)
model_api.SetKind("component")   # tag this prim with its role
print(model_api.GetKind())       # "component"
```

Schema 类型回答："这个 prim **是什么**？"（Mesh、Sphere、Light）
Model kind 回答："这个 prim **扮演什么角色**？"（assembly、component）

---

### 四个内置 Kind


```
assembly
  └── group
        └── component
              └── subcomponent
```

#### assembly


```
assembly                                    group
----------------------------------------    ----------------------------------------
Standalone deliverable                      Organisational container
Has its own USD file                        No own USD file - content inline
Gets referenced independently               Never referenced independently
Other scenes depend on it                   Only exists inside a parent scene
Removing it breaks other scenes             Removing it and hoisting children = same result

def Xform "CityBlock" (                     def Xform "Streets" {
    prepend references =                        def Xform "MainSt" { }
        @./city_block.usda@                     def Xform "Alley"  { }
) { }                                       }
```

---

### 唯一的问题


> 其他场景是否曾经会直接引用这个 prim？

```
Yes -> assembly   (give it its own file, it is a deliverable)
No  -> group      (it is just a folder, no own file needed)
```

#### group


assembly 内部的一种组织性容器。group 是为了可读性和层次结构而存在的
结构性文件夹，而不是可独立发布的资产。

#### component


叶子节点的可复用资产 —— 被引用进场景的内容的基本单元。
component 是自包含的，拥有 `defaultPrim`，
并且可以被独立引用。

```
/CityBlock/Buildings/BuildingA   kind = component  ← one reusable building
/CityBlock/Buildings/BuildingB   kind = component  ← another building
/CityBlock/Props/Bench_001       kind = component  ← a bench asset
/CityBlock/Props/Lamppost_003    kind = component  ← a lamppost asset
```

**真实示例：** 单个椅子资产。它有自己的 USD 文件、
自己的材质、自己的 LOD 变体。它是能够被独立发布、版本化和引用的
最小单元。

```python
chair = stage.DefinePrim("/World/Chair", "Xform")
Usd.ModelAPI(chair).SetKind("component")
```

**component 必须满足：**

- 在其 USD 文件上设置 `defaultPrim`
- 自包含（所有材质都位于根 prim 内部）
- 可被独立引用

#### subcomponent


component 内部重要的具名节点。subcomponent 不能被独立复用 ——
它们只存在于 component 内部，
并通过打标签来表明其在结构上具有重要意义。

```
/Chair                    kind = component
  /Chair/SeatGeo          kind = subcomponent  ← significant internal part
  /Chair/BackGeo          kind = subcomponent  ← significant internal part
  /Chair/LegFL            kind = subcomponent  ← front-left leg
  /Chair/LegFR            kind = subcomponent
```

**真实示例：** 在一个角色 component 内部，头部、躯干和四肢
都是 subcomponent —— 它们是重要的具名部件，
工具可能需要单独引用它们（例如用于挂载配饰
或施加定向特效），
但它们并不是可独立发布的资产。

```python
seat = stage.DefinePrim("/Chair/SeatGeo", "Mesh")
Usd.ModelAPI(seat).SetKind("subcomponent")
```

### 真实场景中的完整层次结构


```
/Shot_042                                   assembly  <- shots reference this
  /Shot_042/Environment                     assembly  <- env team references this independently
    /Shot_042/Environment/CityBlock         assembly  <- lighting references this alone
      /Shot_042/.../Buildings               group     <- nobody references just Buildings
        /Shot_042/.../TowerA                component <- asset team publishes this
      /Shot_042/.../Streets                 group     <- nobody references just Streets
        /Shot_042/.../MainSt                component <- asset team publishes this
  /Shot_042/Characters                      group     <- nobody references just Characters
    /Shot_042/.../Hero                      assembly  <- anim team references Hero alone
      /Shot_042/.../Hero/Body               group     <- nobody references just Body
        /Shot_042/.../Torso                 component <- asset team publishes this
```

每个 assembly 都有一条 `@./its_own_file.usda@` 引用弧。每个 group 都只有内联子节点，没有引用弧。

### Model Kind 在实际工作中的意义


**资产管理工具**利用 model kind 遍历场景、
找出所有 component —— 无需了解具体的
路径或类型：

```python
from pxr import Usd

# Find all component-level assets in the scene
for prim in stage.Traverse():
    kind = Usd.ModelAPI(prim).GetKind()
    if kind == "component":
        print(f"Component asset: {prim.GetPath()}")
        # → can now check version, load payload, apply overrides
```

**渲染器和流水线工具**利用 model kind 来决定加载什么、
在资产浏览器中展示什么、以及把什么纳入
渲染提交 —— 无需为每个项目编写定制逻辑。

### Kind 与 Schema Type 的关键区别


```
Schema type  answers: WHAT IS IT?
  prim.GetTypeName() → "Mesh", "Sphere", "Xform"
  Describes the geometric or functional type

Model kind   answers: WHAT ROLE DOES IT PLAY?
  Usd.ModelAPI(prim).GetKind() → "component", "assembly"
  Describes the pipeline and organisational role

A prim can be both:
  typeName = "Xform"      ← it IS an Xform (schema type)
  kind     = "component"  ← it PLAYS THE ROLE of a component (model kind)
```

### 快速参考


| Kind           | Role                                     | Reusable?                         | Example                               |
| -------------- | ---------------------------------------- | --------------------------------- | ------------------------------------- |
| `assembly`     | 顶层完整场景或交付物                     | 是 —— 已发布                      | 完整城市街区、完整镜头                 |
| `group`        | 场景内的组织性容器                       | 否 —— 仅承担结构                  | `/Buildings`、`/Props`、`/Characters` |
| `component`    | 叶子可复用资产 —— 基本单元               | 是 —— 可被独立引用                | 椅子、建筑、角色                       |
| `subcomponent` | component 内部的重要部件                 | 否 —— 只存在于 component 内部     | 头部、座面、立面面板                   |

---

## 9. 自定义 Model Kind —— UsdModelKindRegistry


USD 内置了一套 **model kind** 层次结构，用于按 prim 在场景中的角色进行分类：

```
assembly       ← top-level published collection of assets
  group        ← organisational container
    component  ← leaf reusable asset (a chair, a tree, a building)
      subcomponent ← important internal node within a component
```

### 创建自定义 Model Kind

要在此层次结构中新增一种 kind（`factory_unit`）：

**步骤 1 —— 使用 `UsdModelKindRegistry` 定义并注册**

该 kind 必须注册到注册表中，这样 USD 才会将其识别为合法类型。

```python
from pxr import Usd

registry = Usd.ModelKindRegistry.GetInstance()

registry.Register(
    "factory_unit",   # new kind name
    "component",      # parent kind — places it under component in hierarchy
)

# USD hierarchy after registration:
# assembly → group → component → factory_unit
```

**步骤 2 —— 使用 `Usd.ModelAPI` 在 prim 上设置 kind**

```python
from pxr import Usd

prim = stage.DefinePrim("/Factory/Unit_A", "Xform")

# Set the kind using UsdModelAPI
model_api = Usd.ModelAPI(prim)
model_api.SetKind("factory_unit")

# Read the kind
print(model_api.GetKind())   # "factory_unit"
```

**步骤 3 —— 实现一个继承（而非覆盖）UsdModelAPI 的 schema 插件**

```
EXTEND UsdModelAPI   ← adds behaviour for the new kind

What you write manually:
  FactoryUnitAPI.h          ← C++ header declaring your class
  FactoryUnitAPI.cpp        ← C++ implementation
                               contains TF_REGISTRY_FUNCTION (written manually)
  plugInfo.json             ← manifest file (written manually)
```

#### 代码片段：


```python
# In C++ — your schema plugin adds behaviour without replacing existing
#
# class FactoryUnitAPI : public UsdModelAPI {   ← EXTENDS UsdModelAPI
# public:
#
#     // Add new behaviour specific to factory_unit
#     bool GetFacilityId(std::string* facilityId) const;
#     bool SetFacilityId(const std::string& facilityId);
#
#     // Original UsdModelAPI methods still work unchanged:
#     // GetKind(), SetKind(), IsModel(), IsGroup() etc.
#     // Nothing is replaced — only added
# };
#
# In Python after the plugin is deployed:
factory_api = FactoryUnitAPI(prim)
factory_api.GetFacilityId()   # new method you added
factory_api.GetKind()         # original UsdModelAPI method still works
```

plugInfo.json

```python
{
  "Plugins": [{
    "Name": "factoryUnit",
    "LibraryPath": "factoryUnit.so",
    "Types": {
      "FactoryUnitAPI": {
        "bases": ["UsdModelAPI"]
      }
    }
  }]
}
```

```
What you run:
cmake + make ← compiles your C++ into factoryUnit.so

What you deploy:
factoryUnit.so
plugInfo.json
→ both placed in a directory
→ PXR_PLUGINPATH_NAME points to that directory
```

部署可以使用[此处](#why-these-three-methods-exist-at-all)提到的任意一种方式进行。

**步骤 4 —— 扩展 `Validate()` 方法以加入领域特定的规则**

自定义校验可确保 `factory_unit` prim 始终具备所需的结构。

```python
# In C++ — override Validate() to add factory_unit specific checks
#
# bool FactoryUnitAPI::Validate(std::string* reason) const {
#
#     // First run the parent validation — do NOT skip this
#     if (!UsdModelAPI::Validate(reason)) {
#         return false;   // fails standard component rules → reject
#     }
#
#     // Now add factory_unit specific rules on top
#     UsdPrim prim = GetPrim();
#
#     // Rule 1: must have pipeline:facilityId metadata
#     std::string facilityId;
#     if (!GetFacilityId(&facilityId) || facilityId.empty()) {
#         *reason = "factory_unit must have pipeline:facilityId set";
#         return false;
#     }
#
#     // Rule 2: must have at least one TemperatureSensor child
#     bool hasSensor = false;
#     for (const auto& child : prim.GetChildren()) {
#         if (child.IsA<AcmeSensors_TemperatureSensor>()) {
#             hasSensor = true;
#             break;
#         }
#     }
#     if (!hasSensor) {
#         *reason = "factory_unit must contain at least one TemperatureSensor";
#         return false;
#     }
#
#     return true;   // passes all rules
# }
#
# In Python after the plugin is deployed:
factory_api = FactoryUnitAPI(prim)
is_valid, reason = factory_api.Validate()
if not is_valid:
    print(f"Invalid factory_unit: {reason}")
    # "factory_unit must have pipeline:facilityId set"
```

### 错误做法


| 错误做法 | 原因 |
| ----------------------------------------------- | ------------------------------------------------------------------------------ |
| 覆盖（而非扩展）UsdModelAPI | 会替换已有行为 —— 破坏标准 kind |
| 在 TfType 中注册 token 但不建立 schema 关联 | 只提供了一个名字，没有行为、API 或校验 |
| 在 model kind 内部使用变体（variants） | 变体 = 内容变化。Model kind = 分类。两者关注点不同。 |
| 修改 USD 核心源码 | USD 的插件与注册表系统正是为了避免这样做而存在 |

---

## 10. 考试模式识别 —— 排除指南


### 模式 1 —— “如何创建自定义 schema？”（"How do you create a custom schema?"）


**正确答案框架：**

1. 编写 `schema.usda`
2. 继承自 **`UsdTyped`** 或 **`UsdGeomImageable`**（不要直接继承 `UsdSchemaBase`）
3. 运行 **`usdGenSchema`** 生成 C++ 和 Python 代码
4. 通过 `plugInfo.json` 注册到 **TfType 系统**
5. 通过 `PXR_PLUGINPATH_NAME` 作为插件部署

### 模式 2 —— “如何新增一种文件格式？”（"How do you add a new file format?"）


**正确答案框架：**
实现 **`SdfFileFormat` 接口** + 注册到 **TfType 系统** + 在 `plugInfo.json` 中声明

### 模式 3 —— “如何创建自定义 model kind？”（"How do you create custom model kinds?"）


**正确答案框架：**
唯一的 token + **`UsdModelKindRegistry`** + 通过 **`Usd.ModelAPI`** 在根 prim 上设置 `kind` 元数据 + 继承（扩展而非覆盖）`UsdModelAPI` 的 schema 插件 + 扩展后的 `Validate()` 方法

### 模式 4 —— “扩展还是覆盖”（"Extend vs Override"）


> 任何声称要“**覆盖**”（**override**）已有 schema、API 或核心系统的选项 = **错误**。USD 永远只做扩展，绝不覆盖。覆盖会破坏该 schema 所有用户已有的功能。扩展（继承自它、向它添加）能在增加新能力的同时保持向后兼容。

### 可立即排除的表述


遇到包含以下表述的**任何选项**，立即排除：

| 选项中的表述 | 排除原因 |
| --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `"Modify the core USD source code"`（“修改 USD 核心源代码”） | USD 使用插件 —— 绝不修改核心代码 |
| `"Python-only schema"` 或 `"subclassing Usd.Schema in Python"`（“仅 Python 的 schema”或“在 Python 中继承 Usd.Schema”） | 完整 schema 需要 C++ + usdGenSchema |
| `"Overriding"` 任何已有的 schema、API 或方法（“覆盖”） | 始终是扩展（EXTEND）—— 绝不覆盖 |
| `"Override UsdStage::Open()"`（“覆盖 UsdStage::Open()”） | 文件格式使用 `SdfFileFormat`，而不是 Stage::Open |
| `"Register token in TfType WITHOUT schema or API linkage"`（“在 TfType 中注册 token 但没有 schema 或 API 关联”） | 仅靠 token 不够 —— 需要完整的 schema 支持 |
| `"Define schema in a .usd file at runtime"`（“在运行时于 .usd 文件中定义 schema”） | Schema 在 `schema.usda` 中定义 + 离线编译 |
| `"Create new UsdSchema to control file format I/O"`（“创建新的 UsdSchema 来控制文件格式 I/O”） | Schema ≠ 文件 I/O —— 应使用 `SdfFileFormat` |
| `"Embed fallback variant selections in prim metadata"`（“在 prim 元数据中嵌入 fallback 变体选择”） | Fallback 属于 stage/layer 层级，而不是 prim 元数据 |
| 仅以 `"Plugin manifest file only"`（“只有插件清单文件”）注册 schema | 同样需要 C++ 源码中的 `TF_REGISTRY_FUNCTION` 宏 —— 只有清单文件是不够的 |
| 对文件格式插件使用 `"Custom locking in Read/Write"`（“在 Read/Write 中自定义加锁”） | USD 核心负责并发管理 —— 插件不需要实现加锁 |
| `"Embed stage cache in file format plugin"`（“在文件格式插件中嵌入 stage 缓存”） | Stage 缓存属于 USD 核心/客户端层级，而不是插件 |
| `"Implement UsdStage subclass for new file format"`（“为新文件格式实现 UsdStage 子类”） | UsdStage 与格式无关 —— 应使用 `SdfFileFormat` |
| `"USD auto-selects variants alphabetically"`（“USD 按字母顺序自动选择变体”） | USD 并不会自动选择变体 —— 必须显式定义 fallback |
| `"UsdSchemaRegistry for dynamic loading without recompilation"`（“用 UsdSchemaRegistry 实现免重编译的动态加载”） | 自定义 schema 需要插件机制或编译期注册 —— 不支持动态运行时加载 |
| `"Using UsdUtils exclusively to parse custom format"`（“完全使用 UsdUtils 解析自定义格式”） | UsdUtils 提供工具函数，但无法替代实现 `SdfFileFormat` 方法 |

---

## 11. 关键要点


| 概念 | 需要记住的内容 |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **IsA schema**（IsA 类 schema） | 定义 prim 类型。设置 `typeName`。每个 prim 只有一个。用 `prim.IsA()` 检查 |
| **API schema**（API 类 schema） | 增强 prim。没有 `typeName`。每个 prim 可以有多个。用 `prim.HasAPI()` 检查 |
| **Custom schema base**（自定义 schema 基类） | 标准 schema 用 `UsdTyped`。可渲染的用 `UsdGeomImageable`。不要直接用 `UsdSchemaBase` |
| **usdGenSchema** | 从 `schema.usda` 生成 C++ 和 Python 代码。完整集成所必需 |
| **TfType = runtime type registry**（TfType = 运行时类型注册表） | 把类型名字符串转换为带有完整继承链、fallback 和 API 的实际类型 |
| **Two components required**（两个必需组件） | `plugInfo.json`（发现入口）+ C++ 中的 `TF_REGISTRY_FUNCTION`（真正的注册）。缺一不可。 |
| **`TF_REGISTRY_FUNCTION`** | 由 `usdGenSchema` 生成的 C++ 宏。在库加载进内存时执行。把类型写入注册表。 |
| **Registration is per-process**（注册是按进程进行的） | 注册表只存在于内存中。每个新进程都会重新加载插件并重新注册。绝不写入磁盘。 |
| **Without plugin deployed**（未部署插件时） | 原始数据仍可读取。但 `IsA()` = False，fallback = None，API = AttributeError。文件并未损坏。 |
| **`PXR_PLUGINPATH_NAME`** | 必须在每个环境中设置 —— 渲染农场、美术工作站、CI。每个新进程都需要能找到插件。 |
| **Python-only schemas**（仅 Python 的 schema） | 不会生成 `TF_REGISTRY_FUNCTION` —— `IsA()` 和 fallback 都无法工作。只适合原型阶段，不适合生产环境。 |
| **SdfFileFormat** | 用于教会 USD 读写新的文件格式。与 schema 相互独立 |
| **UsdModelKindRegistry** | 在这里注册自定义 model kind。使用 `Usd.ModelAPI.SetKind()` 来应用 |
| **Extend vs Override**（扩展还是覆盖） | 始终扩展 UsdModelAPI —— 绝不覆盖。覆盖会破坏已有的 kind |
| **Schema file format separation**（schema 与文件格式分离） | Schema = 数据是什么。SdfFileFormat = 数据如何存储。两者相互独立。 |

---

_上一篇：[第 4 天 —— 高级组合概念](day-04-advanced-composition.md)
_下一篇：[第 6 天 —— 可视化](day-06-visualization.md)

---


### 第 6 天 — 可视化


> 来源：`sparsha-2011/physical-ai-learning-journey` · `02-openUSD-cert/notes/day-06-visualization.md` · [原文链接](https://github.com/sparsha-2011/physical-ai-learning-journey/blob/main/02-openUSD-cert/notes/day-06-visualization.md) · 语言：英文原文 · 中译版



# 第 6 天 — 可视化


> **OpenUSD NCP 认证学习笔记**  
> _UsdGeomMesh, UsdGeomCamera, UsdShadeMaterial, 灯光, Primvars, 可见性_

---

## 目录


1. [UsdGeomImageable — 可见性与用途](#1-usdgeomimageable-visibility-and-purpose)
2. [UsdGeomMesh — 多边形几何体](#2-usdgeommesh-polygon-geometry)
3. [Primvars — 逐元素数据](#3-primvars-per-element-data)
4. [UsdShadeMaterial 与 UsdShadeShader](#usdshadematerial-and-usdshadeshader)
5. [UsdPreviewSurface 与纹理链路](#5-usdpreviewsurface-and-the-texture-chain)
6. [UsdLux — 灯光](#6-usdlux-lights)
7. [UsdGeomCamera — 完整参考](#7-usdgeomcamera-complete-reference)
8. [关键要点](#8-key-takeaways)

---

## 1. UsdGeomImageable — 可见性与用途


`UsdGeomImageable` 是 USD 中**所有可渲染图元**的基类。它恰好提供两样东西——仅此而已：

1. `visibility` —— 该图元是否被渲染
2. `purpose` —— 该图元出现在哪种渲染上下文中

### 可见性


```python
from pxr import UsdGeom

imageable = UsdGeom.Imageable(prim)

# Make invisible
imageable.MakeInvisible()
# Sets visibility = "invisible" on this prim

# Make visible
imageable.MakeVisible()
# Sets visibility = "inherited" on this prim

# Compute resolved visibility (walks up hierarchy)
computed = imageable.ComputeVisibility()
# Returns "inherited" or "invisible"
# A parent set to invisible makes ALL children invisible
# regardless of their own visibility setting
```

> **可见性沿层级向下继承。** 如果父图元不可见，那么它的所有子图元都不可见，即使它们设置了 `visibility = "inherited"`。`ComputeVisibility()` 会沿图元层级向上遍历来解析出最终结果。

### purpose 为何存在 —— 现实中的问题


想象一个拥有 200 万个多边形的机器人主角角色。每当动画师拖动时间线，视口就不得不渲染这 200 万个多边形，仅仅是为了让角色稍微动一下。视口会卡得几乎停滞。

解决方案：同一个角色在 USD 文件中存在**三次**，每个版本都打上了不同的 purpose 标签：

```
/World/Robot
  ├── /World/Robot/HeroGeo      purpose = "render"   ← 2M polygons, full detail
  ├── /World/Robot/ProxyGeo     purpose = "proxy"    ← 500 polygon box
  └── /World/Robot/RigControls  purpose = "guide"    ← circles and arrows for animators
```

每个工具只加载它自己需要的内容：

```
usdview (viewport):        shows → proxy      fast lightweight stand-in
                           hides → render     too heavy for interactive use
                           hides → guide      rig controls not needed here

Final renderer:            shows → render     the real 2M polygon geometry
                           hides → proxy      don't render the low-res box
                           hides → guide      NEVER appears in a render

Rigging / animation tool:  shows → guide      the circles animators grab to pose
                           shows → proxy      so animators can see roughly where the robot is
                           hides → render     too heavy for the rig context
```

**一个 USD 文件。三类受众。零重复。无需手动隐藏。**

### 什么是绑定工具（rigging tool）？


**绑定工具**（Maya、Houdini、Blender）是用来构建让角色动起来的控制系统的软件。未经处理的网格只是一袋静态的多边形——绑定会在此基础上增加：

- 网格内部的**骨架**（关节/骨骼）
- 动画师可以直接抓取操作的**控制曲线**（圆形和箭头）
- 把控制曲线 → 关节 → 网格形变连接起来的**规则**

这些控制曲线正是在 USD 中被打上 `guide` purpose 标签的部分。它们存在的唯一目的就是让动画师能够为角色摆姿势——它们在最终渲染图像中没有视觉意义，**绝不**能出现在成片渲染中。

```
Animator grabs the circle (guide prim) → joint rotates → mesh deforms → arm lifts
         ↑ visible in rig tool                          ↑ visible in final render
         ↑ NEVER in final render                        ↑ NEVER in rig tool
```

### Purpose 取值


| Purpose     | 谁会看到它                                    | 现实中的例子                                |
| ----------- | ---------------------------------------------- | ------------------------------------------------- |
| `"render"`  | 仅最终渲染通道                                 | 200 万多边形的主角几何体                          |
| `"proxy"`   | 视口 / 交互式工具                              | 500 多边形的包围盒替身                           |
| `"guide"`   | 绑定 / 动画工具——**绝不渲染**                   | IK 控制曲线、关节显示、辅助几何体                 |
| `"default"` | 所有上下文（回退值）                            | 无需区分轻重量的简单道具                        |

> **`guide` 是最难理解的**——它并不像可见性那样是关于"隐藏"。它讲的是处于一个完全独立的渲染上下文中，而该上下文永远不会是最终渲染。一个图元可以是 `guide` purpose，同时又是 `visibility = inherited`——它依然不会被渲染。这是两条彼此独立的轴。

```python
imageable.GetPurposeAttr().Set(UsdGeom.Tokens.render)
imageable.GetPurposeAttr().Set(UsdGeom.Tokens.proxy)
imageable.GetPurposeAttr().Set(UsdGeom.Tokens.guide)
imageable.GetPurposeAttr().Set(UsdGeom.Tokens.default_)

# Compute resolved purpose (inherits from parents)
purpose = imageable.ComputePurpose()
```

### 在 usdview 中


usdview 的工具栏上有 **Purposes** 切换按钮——分别是 render、proxy 和 guide 的图标。把 render 按钮关掉，200 万多边形的几何体就消失了，只剩下代理盒。这就是 purpose 在实时生效。这也正是 `viz_visibility_and_purpose.py` 这个练习会导出全部四个 purpose 取值的原因——在 usdview 中打开它，逐一切换每个 purpose 按钮，就能确切看到哪些图元出现、哪些图元消失。

---

## 2. UsdGeomMesh — 多边形几何体


`UsdGeomMesh` 是多边形几何体所使用的 schema。USD 场景中的每一个 3D 网格都由三个协同工作的必需属性表示。

### 三个必需属性


**`points`** —— 每个顶点的 3D 位置，处于图元的局部坐标系中：

```usda
point3f[] points = [(0,0,0), (1,0,0), (1,1,0), (0,1,0)]
#                   corner 0  corner 1  corner 2  corner 3
```

**`faceVertexCounts`** —— 每个面拥有多少个顶点：

```usda
int[] faceVertexCounts = [4, 4, 3]
#                          ↑    ↑   ↑
#                         quad quad triangle  (3 faces)
```

**`faceVertexIndices`** —— 哪些顶点（按 `points` 中的索引计）构成各个面，所有面依次拼接在一起：

```usda
int[] faceVertexIndices = [0,1,2,3,  4,5,6,7,  0,1,5]
#                          face 0    face 1     face 2
```

> **关键：** `faceVertexIndices.length` = **faceVertexCounts 之和**。不是点的数量，也不是面的数量。
>
> 对上面的例子：`4 + 4 + 3 = 11`——索引数组中有 11 个元素。

### 其它网格属性


| 属性                | 类型          | 说明                                                             |
| ------------------- | ----------- | -------------------------------------------------------------------- |
| `subdivisionScheme` | `token`     | `"none"`（平面着色）、`"catmullClark"`（平滑）、`"loop"`、`"bilinear"` |
| `holeIndices`       | `int[]`     | 视作孔洞的面索引——几何体存在但**不**被渲染                          |
| `doubleSided`       | `bool`      | 是否渲染背面                                                        |
| `extent`            | `float3[2]` | 轴对齐包围盒——视口正确显示所必需                                    |

### Python API


```python
from pxr import UsdGeom, Vt, Gf

stage = Usd.Stage.CreateInMemory()
mesh  = UsdGeom.Mesh.Define(stage, "/World/Chair")

# Set geometry
mesh.GetPointsAttr().Set(Vt.Vec3fArray([
    Gf.Vec3f(-1, 0, -1), Gf.Vec3f(1, 0, -1),
    Gf.Vec3f(1, 0, 1),   Gf.Vec3f(-1, 0, 1),
]))

mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray([4]))
mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray([0, 1, 2, 3]))

# Subdivision
mesh.GetSubdivisionSchemeAttr().Set(UsdGeom.Tokens.catmullClark)

# Holes — face index 2 is a hole (exists in topology, not rendered)
mesh.GetHoleIndicesAttr().Set(Vt.IntArray([2]))

# Extent — required for viewport correctness
mesh.GetExtentAttr().Set(Vt.Vec3fArray([
    Gf.Vec3f(-1, 0, -1), Gf.Vec3f(1, 0, 1)
]))
```

### extent 属性 —— 它是什么，以及为什么你必须更新它


`extent` 是网格的轴对齐包围盒——一对 Vec3f 值，表示包含所有顶点的那个盒子的最小角点与最大角点。

```text
extent = [min_corner, max_corner]
= [(x_min, y_min, z_min), (x_max, y_max, z_max)]

Example: a unit cube sitting on the origin
extent = [(-0.5, 0.0, -0.5), (0.5, 1.0, 0.5)]
```

**它为何存在：** USD 渲染器和视口系统使用 `extent` 进行视锥剔除——在做任何实际工作之前，它们会先检查包围盒，以判断该图元对相机而言是否可见。如果包围盒显示该图元位于视野之外，渲染器就会完全跳过它。对于大型场景来说，这是一项重要的性能优化。

**为什么你必须手动更新它：** 当你修改 `points` 时，USD **不会**自动重新计算 `extent`。它是一个缓存值，你需要自己负责让它保持同步。如果你修改了几何体却忘了更新 `extent`，渲染器就会基于过期的包围盒继续工作。

extent 过期的后果：

- 图元在错误的相机角度下消失（渲染器以为它在视锥之外，其实并不在）
- 图元在某些渲染器中完全不被渲染
- 视口中的包围盒显示不正确
- BBoxCache 查询返回错误结果

这绝不是表面问题——它会直接破坏渲染。

**考试规则：** 每当你修改 `points` 时，下一步的必需动作就是更新 `extent`。两者永远成对出现。

```python
from pxr import Usd, UsdGeom, Vt, Gf

stage = Usd.Stage.CreateInMemory()
mesh  = UsdGeom.Mesh.Define(stage, "/World/Chair")

new_points = Vt.Vec3fArray([
    Gf.Vec3f(-1, 0, -1), Gf.Vec3f(1, 0, -1),
    Gf.Vec3f(1,  2, -1), Gf.Vec3f(-1, 2, -1),
    Gf.Vec3f(-1, 0,  1), Gf.Vec3f(1, 0,  1),
    Gf.Vec3f(1,  2,  1), Gf.Vec3f(-1, 2,  1),
])

# Step 1 — set the new points
mesh.GetPointsAttr().Set(new_points)

# Step 2 — recompute and update extent
# Method A: let USD compute it from the points array
extent = UsdGeom.PointBased(mesh).ComputeExtent(new_points)
# returns Vt.Vec3fArray([min_corner, max_corner])
mesh.GetExtentAttr().Set(extent)

# Method B: set manually if you know the exact bounds
mesh.GetExtentAttr().Set(Vt.Vec3fArray([
    Gf.Vec3f(-1, 0, -1),   # minimum corner
    Gf.Vec3f( 1, 2,  1),   # maximum corner
]))

# Method C: use BBoxCache for the whole stage (more expensive)
bbox_cache = UsdGeom.BBoxCache(
    Usd.TimeCode.Default(),
    includedPurposes=["default"]
)
world_bound = bbox_cache.ComputeWorldBound(mesh.GetPrim())
bbox_range  = world_bound.GetRange()
mesh.GetExtentAttr().Set(Vt.Vec3fArray([
    Gf.Vec3f(bbox_range.GetMin()),
    Gf.Vec3f(bbox_range.GetMax())
]))
```

**方法签名：**

```python
# UsdGeom.PointBased.ComputeExtent(points) -> Vt.Vec3fArray
UsdGeom.PointBased(mesh).ComputeExtent(points_array)
# points_array: Vt.Vec3fArray
# returns:      Vt.Vec3fArray with two elements [min, max]

# UsdGeomMesh.GetExtentAttr() -> UsdAttribute
mesh.GetExtentAttr().Set(Vt.Vec3fArray([min_vec, max_vec]))
# value type: float3[2] — exactly two Vec3f values

# UsdGeom.BBoxCache(timeCode, includedPurposes)
bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ["default"])
# ComputeWorldBound(prim) -> UsdGeom.BBox3d
# .GetRange() -> Gf.Range3d
# .GetMin()   -> Gf.Vec3d
# .GetMax()   -> Gf.Vec3d
```

> **不要把 extent 和法线（normals）搞混。** 法线描述表面的朝向，用于光照计算。extent 描述包围盒，用于剔除。两者都是附加的网格属性，但用途完全不同。

> **UV 永远不会被自动生成。** UV 坐标必须显式编写为 `primvars:st`。考试会专门考查这一点。

---

## 3. Primvars — 逐元素数据


**Primvars**（Primitive Variables，图元变量）是 `primvars:` 命名空间下的属性，用于承载逐元素的数据——颜色、UV、法线——并把它们从几何体传递给着色器。

### 插值模式


图元变量上的 `interpolation` 元数据决定了需要多少个数值，以及这些数值如何映射到几何体：

| 插值方式        | 需要的数值数量    | 映射到                                          |
| ------------- | ----------------- | --------------------------------------------------- |
| `constant`    | 1                 | 整个图元——所有部分共用一个值                        |
| `uniform`     | 每个面 1 个         | 每个面都有自己独立的值                              |
| `vertex`      | 每个点 1 个         | 每个顶点都有值，并在各面之间插值                      |
| `faceVarying` | 每个面-顶点 1 个   | 最精细——`faceVertexIndices` 中的每一项各一个          |

> **UV 使用 `faceVarying`**，因为同一个 3D 顶点在不同的面上可以拥有不同的 UV 坐标（在接缝处）。`faceVarying` 数量 = `faceVertexIndices.length` = `faceVertexCounts` 之和。

### Primvar 关键事实


- Primvars **并非**总是 uniform 插值——它们有四种不同的模式
- Primvars 编写在特定的图元上——**不**需要放在根图元上
- 采用 `constant` 插值的 Primvars 会沿层级向下继承
- Primvars **没有内置的回退值机制**
- Primvars **可以**带时间采样（动画 UV、动画颜色）
- `"indexed"` **不是**一种插值类型——primvars 可以被索引，但插值与索引是两个彼此独立的概念

### Python API — `UsdGeom.PrimvarsAPI`


```python
from pxr import UsdGeom, Sdf, Vt, Gf

primvar_api = UsdGeom.PrimvarsAPI(mesh.GetPrim())

# Create a UV primvar (faceVarying — most common for UVs)
st = primvar_api.CreatePrimvar(
    "st",
    Sdf.ValueTypeNames.TexCoord2fArray,
    UsdGeom.Tokens.faceVarying
)
st.Set(Vt.Vec2fArray([
    Gf.Vec2f(0, 0), Gf.Vec2f(1, 0),
    Gf.Vec2f(1, 1), Gf.Vec2f(0, 1),
]))

# Create a displayColor primvar (constant — whole prim is red)
color = primvar_api.CreatePrimvar(
    "displayColor",
    Sdf.ValueTypeNames.Color3fArray,
    UsdGeom.Tokens.constant
)
color.Set(Vt.Vec3fArray([Gf.Vec3f(1.0, 0.0, 0.0)]))
```

---

<a id="usdshadematerial-and-usdshadeshader"></a>

## 4. UsdShadeMaterial 与 UsdShadeShader


### 材质层级


```
/World/Looks/WoodMat                ← UsdShadeMaterial (the CONTAINER)
  └── /World/Looks/WoodMat/Shader   ← UsdShadeShader (the computation node)
```

**材质**（Material）是一个容器，负责向渲染器暴露输出。**着色器**（Shader）节点则执行真正的着色计算。两者通过输出相互连接。

### `inputs:` 与 `outputs:`


每个 `UsdShadeShader` 都有：

- **`inputs:`** —— 着色器**接受**的参数（颜色、粗糙度、纹理坐标等）
- **`outputs:`** —— 着色器**产生**的数据（表面结果、颜色值等）

```
geometry.primvars:st
        ↓
PrimvarReader.inputs:varname = "st"
PrimvarReader.outputs:result (float2)
        ↓
UVTexture.inputs:st ← connected from PrimvarReader.outputs:result
UVTexture.inputs:file = "./textures/wood.png"
UVTexture.outputs:rgb (color3f)
        ↓
PreviewSurface.inputs:diffuseColor ← connected from UVTexture.outputs:rgb
PreviewSurface.inputs:roughness = 0.5
PreviewSurface.outputs:surface (token)
        ↓
Material.outputs:surface ← connected from PreviewSurface.outputs:surface
```

> **考试陷阱：**
>
> - `inputs:` 和 `outputs:` **并非**已废弃——它们是 UsdShade 的根基
> - `inputs:` 可以承载任何数据类型——不只是纹理
> - Shader **不**包含 Material——恰恰相反：是 Material 包含 Shader
> - Shader 参数**必须**使用 `UsdShadeInput`/`UsdShadeOutput` 对象来定义——在没有它们的情况下给 shader 设置任意属性会破坏 schema 兼容性，并阻止着色网络的连接
> - 纹理文件路径不能直接赋值到 `UsdShadeMaterial` 上——纹理必须经由着色器节点（`UsdUVTexture`）传递

### 材质级输入 —— 外部参数化


一个 `UsdShadeMaterial` 图元可以在**材质层级**上暴露 `UsdShadeInput` 对象——而不只是在它内部的着色器节点上。这让外部系统无需了解其内部着色网络，就能设置材质上的参数。

```python
# Expose a parameter at the material level
mat = UsdShade.Material.Define(stage, "/Looks/WoodMat")

# UsdShadeInput on the MATERIAL PRIM — accepts external parameters
mat_color_input = mat.CreateInput(
    "baseColor", Sdf.ValueTypeNames.Color3f)
mat_color_input.Set(Gf.Vec3f(0.6, 0.4, 0.2))

# Connect material input → shader input
shader = UsdShade.Shader.Define(stage, "/Looks/WoodMat/Shader")
shader.CreateIdAttr("UsdPreviewSurface")
shader_diff = shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f)
shader_diff.ConnectToSource(mat_color_input)
# Now the material's baseColor drives the shader's diffuseColor
# External tools can set mat.GetInput("baseColor") without touching the shader
```

### 位移输出


`UsdShadeMaterial` 有**两个与表面相关的输出**——而不止一个：

```python
# Surface output — connects the main shading network
mat.CreateSurfaceOutput().ConnectToSource(surface_shader_out)

# Displacement output — connects displacement shaders
# Displacement shaders modify the geometry's surface POSITIONS during rendering
# (pushes vertices in/out based on a texture — creates real geometric detail)
mat.CreateDisplacementOutput().ConnectToSource(displacement_shader_out)
```

| 输出                   | 用途                                              |
| ---------------------- | ----------------------------------------------------------------- |
| `outputs:surface`      | 主着色——颜色、粗糙度、金属度、反射                 |
| `outputs:displacement` | 几何体修改——在渲染过程中推移表面位置               |

> 位移不同于法线贴图——法线贴图是伪造光照效果，位移则是真正地移动几何体。

### Python API


```python
from pxr import UsdShade, Sdf

stage = Usd.Stage.CreateInMemory()

# Create the Material container
mat    = UsdShade.Material.Define(stage, "/World/Looks/WoodMat")

# Create the Shader node inside it
shader = UsdShade.Shader.Define(stage, "/World/Looks/WoodMat/Shader")
shader.CreateIdAttr("UsdPreviewSurface")

# Author inputs (parameters going IN)
shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f
).Set(Gf.Vec3f(0.6, 0.4, 0.2))
shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.5)

# Create the surface output (data coming OUT)
surf_out = shader.CreateOutput("surface", Sdf.ValueTypeNames.Token)

# Connect Material output → Shader output
mat.CreateSurfaceOutput().ConnectToSource(surf_out)

# Bind the material to a mesh
# MaterialBindingAPI must be Applied BEFORE Bind() is called
binding_api = UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim())
binding_api.Bind(mat)
```

### UsdGeomSubset — 逐面材质绑定

**它是什么：** `UsdGeomSubset` 在网格上定义了一组命名的面索引。它是网格的一个子 prim，持有一个面索引列表和一个材质绑定。网格本身仍然是单个 prim —— 这些 subset 只是其部分面集合的视图。

**为什么需要它：** 直接调用 `MaterialBindingAPI.Bind()` 会把一种材质应用到整个网格上。在生产环境中，单个网格往往有多个材质区域 —— 汽车车身同时有喷漆金属、橡胶轮胎、玻璃车窗和镀铬饰条。如果没有 GeomSubset，你就得为每个材质区域把网格拆成独立的 prim，这既开销高昂，又会破坏艺术家的工作流。

```text
Without GeomSubset:
/Car/Body     -> one material (wrong — body has paint, rubber, glass)
OR
/Car/Body/Paint   -> split into 4 separate prims
/Car/Body/Rubber
/Car/Body/Glass
/Car/Body/Chrome  <- more complex hierarchy, harder to rig/animate

With GeomSubset:
/Car/Body           -> one mesh, full topology intact
/Car/Body/Paint   -> subset, faces [0-120]   -> paint_mat
/Car/Body/Rubber  -> subset, faces [121-160] -> rubber_mat
/Car/Body/Glass   -> subset, faces [161-200] -> glass_mat
/Car/Body/Chrome  -> subset, faces [201-240] -> chrome_mat
```

**方法签名：**

```python
# UsdGeom.Subset.Define(stage, path) -> UsdGeom.Subset
subset = UsdGeom.Subset.Define(stage, "/World/Mesh/ZoneName")

# CreateElementTypeAttr(value) -> UsdAttribute
# value must be UsdGeom.Tokens.face for material binding
subset.CreateElementTypeAttr(UsdGeom.Tokens.face)

# CreateIndicesAttr(value) -> UsdAttribute
# value: Vt.IntArray of face indices from the parent mesh
subset.CreateIndicesAttr(Vt.IntArray([0, 1, 2, 3]))

# UsdShade.MaterialBindingAPI.Apply(prim) -> MaterialBindingAPI
# Apply on the SUBSET prim, not the mesh
binding = UsdShade.MaterialBindingAPI.Apply(subset.GetPrim())
binding.Bind(material)
```

**完整示例：**

```python
from pxr import Usd, UsdGeom, UsdShade, Vt, Gf, Sdf

stage = Usd.Stage.CreateInMemory()

# Define the mesh — 12 faces total
mesh = UsdGeom.Mesh.Define(stage, "/World/Chair/Body")
mesh.GetPointsAttr().Set(Vt.Vec3fArray([...]))
mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray([4]*12))
mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray([...]))

# Define materials
fabric_mat = UsdShade.Material.Define(stage, "/Looks/Fabric")
metal_mat  = UsdShade.Material.Define(stage, "/Looks/Metal")
# ... (set up shader networks on each material)

# Subset 1 — seat cushion faces
fabric_subset = UsdGeom.Subset.Define(
    stage, "/World/Chair/Body/FabricZone"
)
fabric_subset.CreateElementTypeAttr(UsdGeom.Tokens.face)
fabric_subset.CreateIndicesAttr(Vt.IntArray([0,1,2,3,4,5,6,7]))
UsdShade.MaterialBindingAPI.Apply(
    fabric_subset.GetPrim()
).Bind(fabric_mat)

# Subset 2 — metal frame faces
metal_subset = UsdGeom.Subset.Define(
    stage, "/World/Chair/Body/MetalZone"
)
metal_subset.CreateElementTypeAttr(UsdGeom.Tokens.face)
metal_subset.CreateIndicesAttr(Vt.IntArray([8,9,10,11]))
UsdShade.MaterialBindingAPI.Apply(
    metal_subset.GetPrim()
).Bind(metal_mat)
```

**关键规则：**

- `elementType` 必须是 `UsdGeom.Tokens.face` —— 材质绑定只在面 subset 上生效
- subset prim 必须是网格 prim 的**直接子级**
- 面索引对应 `faceVertexCounts` 中各个面的顺序 —— 面 0 是第一项，面 1 是第二项，依此类推
- 一个面只能属于一个材质 subset —— 索引重叠会导致未定义行为
- `MaterialBindingAPI` 应用在 **subset prim** 上，而不是网格 prim 上

### 基于 Collection 的材质绑定


**它是什么：** 基于 Collection 的绑定使用 `Usd.CollectionAPI` 定义一组命名的 prim，这些 prim 可以来自场景层级的任意位置，然后用一次操作把材质绑定到该集合上。Collection 定义在单个根 prim 上，但可以包含 stage 中任意路径的 target。

**为什么需要它：** 直接绑定和 GeomSubset 绑定每次只能影响一个 prim。在大型场景中，可能有几十个 prim 需要同一种材质 —— 每一颗金属螺栓、每一块玻璃面板、每一个橡胶密封件，散落在数百个资产中。逐个更新既昂贵又容易出错。Collection 绑定让你只声明一次分组、只绑定一次。

```text
Direct binding:                      Collection binding:
/Building/Floor/Tile_001.Bind()      collection "marble_surfaces" includes:
/Building/Floor/Tile_002.Bind()        /Building/Floor/Tile_001
/Building/Floor/Tile_003.Bind()        /Building/Floor/Tile_002
... 500 more calls                     /Building/Floor/Tile_003
... 500 more entries
root.Bind(marble_mat, "marble_surfaces")
<- one bind call covers all 500
```

**何时使用它：**

- 层级结构中分散的许多 prim 共用同一种材质
- 你希望在场景级别、而非按单个资产管理材质分配
- 资产是实例化的 —— 无法直接在每个实例上绑定

**方法签名：**

```python
# Usd.CollectionAPI.Apply(prim, collectionName) -> CollectionAPI
# Apply to any prim that will own the collection definition
collection = Usd.CollectionAPI.Apply(root_prim, "collection_name")

# CreateIncludesRel() -> UsdRelationship
# Add target paths to include in the collection
collection.CreateIncludesRel().AddTarget(Sdf.Path("/World/Chair/Legs"))

# CreateExcludesRel() -> UsdRelationship
# Optionally exclude specific paths from an include-all collection
collection.CreateExcludesRel().AddTarget(Sdf.Path("/World/Chair/Legs/LeftFront"))

# UsdShade.MaterialBindingAPI.Bind(material, strength, collectionName)
# strength: UsdShade.Tokens.strongerThanDescendants
#           UsdShade.Tokens.weakerThanDescendants
binding_api.Bind(
    material,
    UsdShade.Tokens.strongerThanDescendants,
    "collection_name"
)
```

```
strongerThanDescendants - parent wins, overrides children

    /World  ->  metal_mat  (stronger)
        /Chair  ->  wood_mat

    Result:  /World = metal   /Chair = metal  <- parent wins

weakerThanDescendants - children win, parent is just a fallback

    /World  ->  metal_mat  (weaker)
        /Chair  ->  wood_mat

    Result:  /World = metal   /Chair = wood   <- child keeps its own
```

> stronger = 把该材质强制应用到其下的一切
> weaker = 只在没有任何其他设置的地方使用该材质

**完整示例：**

```python
from pxr import Usd, UsdShade, Sdf

stage = Usd.Stage.Open("building.usda")

root      = stage.GetPrimAtPath("/Building")
metal_mat = UsdShade.Material.Get(stage, "/Looks/Metal")

# Define a collection called "structural_metal"
# that includes all metal structural prims
collection = Usd.CollectionAPI.Apply(root, "structural_metal")
includes   = collection.CreateIncludesRel()
includes.AddTarget(Sdf.Path("/Building/Floor_01/Beams"))
includes.AddTarget(Sdf.Path("/Building/Floor_02/Beams"))
includes.AddTarget(Sdf.Path("/Building/Facade/Frame"))
includes.AddTarget(Sdf.Path("/Building/Roof/Trusses"))

# Bind the material to the whole collection in one call
binding_api = UsdShade.MaterialBindingAPI.Apply(root)
binding_api.Bind(
    metal_mat,
    UsdShade.Tokens.strongerThanDescendants,
    "structural_metal"
)
# All four paths now use metal_mat
# If new paths are added to the collection later,
# they automatically inherit the binding
```

**三层绑定方式总结：**

| 层级       | 机制                                          | 作用范围                      | 适用场景                                        |
| ---------- | --------------------------------------------- | ----------------------------- | ----------------------------------------------- |
| 直接绑定   | `MaterialBindingAPI.Bind(mat)`                | 单个 prim                     | 简单的单一材质资产                              |
| GeomSubset | 在 subset 上调用 `MaterialBindingAPI.Bind(mat)` | 同一网格内的面分组            | 单网格多材质                                    |
| Collection | `CollectionAPI` + `Bind(mat, strength, name)` | 层级结构中任意一组 prim       | 大型场景、分散的 prim、实例化资产               |

---

## 5. UsdPreviewSurface 与纹理链路


`UsdPreviewSurface` 是 USD 内置的标准基于物理的着色器。它可以在所有符合 USD 规范的渲染器中工作。

### 关键输入


| 输入             | 类型        | 描述                         |
| --------------- | ---------- | ---------------------------- |
| `diffuseColor`  | `color3f`  | 基础表面颜色                 |
| `roughness`     | `float`    | 0 = 镜面光滑，1 = 完全粗糙   |
| `metallic`      | `float`    | 0 = 绝缘体，1 = 纯金属       |
| `opacity`       | `float`    | 1 = 不透明，0 = 透明         |
| `normal`        | `normal3f` | 法线贴图（切线空间）         |
| `emissiveColor` | `color3f`  | 自发光颜色                   |

### 读取纹理 —— 三节点链路


```python
# Node 1 — UsdPrimvarReader_float2
# Reads the UV primvar (primvars:st) from the mesh geometry
reader = UsdShade.Shader.Define(stage, "/Looks/Mat/Reader")
reader.CreateIdAttr("UsdPrimvarReader_float2")
reader.CreateInput("varname", Sdf.ValueTypeNames.Token).Set("st")
# "st" — NOT "primvars:st" — the primvars: prefix is OMITTED in varname
reader_out = reader.CreateOutput("result", Sdf.ValueTypeNames.Float2)

# Node 2 — UsdUVTexture
# Samples an image texture using the UV coordinates
tex = UsdShade.Shader.Define(stage, "/Looks/Mat/Texture")
tex.CreateIdAttr("UsdUVTexture")
tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set("./wood.png")
tex_st = tex.CreateInput("st", Sdf.ValueTypeNames.Float2)
tex_st.ConnectToSource(reader_out)     # connect UV from reader
tex_rgb = tex.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)

# Node 3 — UsdPreviewSurface
# Uses the texture colour as diffuseColor
surface = UsdShade.Shader.Define(stage, "/Looks/Mat/Surface")
surface.CreateIdAttr("UsdPreviewSurface")
diff_in = surface.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f)
diff_in.ConnectToSource(tex_rgb)       # connect texture to diffuseColor
surf_out = surface.CreateOutput("surface", Sdf.ValueTypeNames.Token)

# Wire Material
mat.CreateSurfaceOutput().ConnectToSource(surf_out)
```

---

## 6. UsdLux —— 灯光


所有 UsdLux 灯光都继承自 `UsdGeomXformable` —— 它们像其他任何 prim 一样**可变换、可做动画**。

### 所有灯光共有的属性


| 属性               | 类型       | 描述                                                                                                             |
| ------------------ | ---------- | ---------------------------------------------------------------------------------------------------------------- |
| `intensity`        | `float`    | 亮度 —— 根据灯光类型，以**坎德拉（cd）**或**每球面度瓦特数**计量。**不是流明。**                                  |
| `exposure`         | `float`    | 以摄影级数（stop）为单位的指数亮度缩放：`final = intensity × 2^exposure`。每增加一个单位，亮度**翻倍**。         |
| `color`            | `color3f`  | 发出光的光谱色调 —— 直接影响渲染场景中的色相                                                                   |
| `colorTemperature` | `float`    | 以开尔文（Kelvin）表示的色温（例如 6500K = 日光，3200K = 钨丝灯）                                                |
| `falloffRadius`    | `float`    | 灯光影响的最大距离 —— 超出该半径的几何体不会获得任何光贡献                                                     |
| `enableShadows`    | `bool`     | **显式开启/关闭阴影投射** —— 在某些渲染器中默认为 False                                                         |

> **`intensity` 的单位 —— 常见的考试陷阱：** 之前的笔记写的是"流明" —— 这是**错的**。  
> `intensity` = **坎德拉（cd）**或**每球面度瓦特数**（辐射强度），而不是流明（光通量）。  
> 流明衡量的是所有方向上的总光输出。坎德拉衡量的是某一特定方向上的光强。

> **`falloffRadius` 限制了灯光的有效范围** —— 超出该半径的几何体不会获得任何光贡献。可通过剔除远处的光照计算来优化渲染。

### 阴影并非自动开启


投射阴影需要**显式配置**。使用 `enableShadows = true` 为某个特定灯光开启阴影：

```python
# Shadows are NOT on by default — must explicitly enable
light = UsdLux.SphereLight.Define(stage, "/World/Key")
light.CreateIntensityAttr(500.0)

# Enable shadows via the shadow API
shadow_api = UsdLux.ShadowAPI.Apply(light.GetPrim())
shadow_api.CreateShadowEnableAttr(True)
# OR set directly:
light.GetPrim().CreateAttribute(
    "inputs:enableShadows", Sdf.ValueTypeNames.Bool
).Set(True)
```

### 体积散射并非自带特性


UsdLux 灯光**不会**自动产生体积散射（雾、体积光、participating media）。这需要额外的体积着色器或特定渲染器的设置。考试中这会作为干扰项出现 —— 凡是说 UsdLux 灯光"天然支持"或"自动模拟"体积效果的选项，都应排除。

### 灯光类型


| Schema               | 类比                 | 关键属性                                     |
| -------------------- | -------------------- | -------------------------------------------- |
| `UsdLuxDistantLight` | 平行光（太阳）       | `angle`（太阳圆盘的角尺寸）                  |
| `UsdLuxSphereLight`  | 带尺寸的点光源       | `radius` —— 控制阴影柔和度                  |
| `UsdLuxRectLight`    | 影棚柔光箱           | `width`、`height`                            |
| `UsdLuxDomeLight`    | HDRI 环境光          | `textureFile`（.exr/.hdr 的路径）            |
| `UsdLuxConeLight`    | 聚光灯               | `shaping:cone:angle`、`shaping:cone:softness` |

### SphereLight 的 radius —— 重点考试主题


`UsdLuxSphereLight` 上的 `radius` 控制的是**角度扩散范围和阴影柔和度**，而不是亮度。

```
Small radius → small light source → hard sharp shadows
Large radius → large light source → soft diffuse shadows

intensity  = brightness (lumens)
exposure   = brightness adjustment in photographic stops
radius     = shadow softness and light spread (SphereLight only)
color      = colour tint of emitted light
```

---

## 7. UsdGeomCamera —— 完整参考


`UsdGeomCamera` 表示 USD 中的相机。它是 **Xformable** —— 使用 xformOp 变换来定位、旋转和制作动画。动画需要**显式的时间采样** —— 不会自动更新。

### 投影类型 —— 仅有两种


```python
camera.GetProjectionAttr().Set(UsdGeom.Tokens.perspective)
camera.GetProjectionAttr().Set(UsdGeom.Tokens.orthographic)
# No fisheye, cylindrical, or spherical — only these two exist
```

| 投影类型         | 行为                           | 使用场景                     |
| --------------- | ------------------------------ | ---------------------------- |
| `perspective`   | 越远的物体看起来越小             | 影视、游戏、可视化           |
| `orthographic`  | 任意距离的物体大小都相同         | CAD、技术制图、等轴测         |

### 完整属性参考


| 属性                     | 类型      | 默认值         | 描述                                       |
| ------------------------ | --------- | -------------- | ------------------------------------------ |
| `projection`             | `token`   | `"perspective"` | 只能是 `perspective` 或 `orthographic`    |
| `focalLength`            | `float`   | `50.0 mm`      | 镜头到像平面的距离。控制 FOV（视场角）。   |
| `horizontalAperture`     | `float`   | `20.955 mm`    | 传感器宽度，**单位是毫米**（不是英寸）     |
| `verticalAperture`       | `float`   | `15.291 mm`    | 传感器高度，单位为毫米                     |
| `horizontalApertureOffset` | `float` | `0.0`          | 水平镜头偏移（移轴效果）                   |
| `verticalApertureOffset` | `float`   | `0.0`          | 垂直镜头偏移                               |
| `clippingRange`          | `float2`  | `(1, 1000000)` | 近远裁剪平面 **—— 确实在 schema 中**       |
| `fStop`                  | `float`   | `0.0`          | 光圈 f 值 —— 控制景深                     |
| `focusDistance`          | `float`   | `0.0`          | 对焦平面的距离                             |

### 焦距与视场角


焦距与光圈**共同**决定视场角：

```
FOV = 2 × atan(horizontalAperture / (2 × focalLength))

18mm focal length + 24mm sensor → wide angle ~67° FOV
85mm focal length + 24mm sensor → telephoto ~16° FOV
```

### Python API


```python
from pxr import UsdGeom, Gf

camera = UsdGeom.Camera.Define(stage, "/World/MainCamera")

# Position using xformOp (camera is Xformable)
UsdGeom.XformCommonAPI(camera).SetTranslate(Gf.Vec3d(0, 5, 20))
UsdGeom.XformCommonAPI(camera).SetRotate(Gf.Vec3f(-15, 0, 0))

# Lens properties
camera.GetProjectionAttr().Set(UsdGeom.Tokens.perspective)
camera.GetFocalLengthAttr().Set(35.0)
camera.GetHorizontalApertureAttr().Set(24.0)    # mm, not inches
camera.GetVerticalApertureAttr().Set(13.5)      # 16:9 aspect ratio

# Clipping (IS in the schema — not handled externally)
camera.GetClippingRangeAttr().Set(Gf.Vec2f(0.1, 10000))

# Depth of field
camera.GetFocusDistanceAttr().Set(8.0)   # focus at 8 units
camera.GetFStopAttr().Set(2.8)           # shallow DOF

# Animate the camera — EXPLICIT time samples required
UsdGeom.XformCommonAPI(camera).SetTranslate(Gf.Vec3d(0, 5, 20), time=1)
UsdGeom.XformCommonAPI(camera).SetTranslate(Gf.Vec3d(10, 5, 15), time=48)
```

### 考试陷阱


| 错误说法                                       | 正确事实                                |
| --------------------------------------------- | --------------------------------------- |
| "传感器尺寸以英寸计"                          | 传感器尺寸以**毫米**计                 |
| "clippingRange 由渲染器在外部处理"            | `clippingRange` 确实在 schema 中       |
| "fStop 控制曝光时间"                          | `fStop` 只控制**景深**                 |
| "相机会从动画片段自动更新"                    | 需要**显式的时间采样**                 |
| "只支持 perspective"                          | **perspective 和 orthographic 两者都存在** |

---

## 8. 关键要点

| 概念 | 需要记住的内容 |
| ---------------------------- | ------------------------------------------------------------------------ |
| **UsdGeomImageable** | 所有可渲染图元的基类。**仅**提供 visibility 与 purpose。 |
| **Purpose tokens**（Purpose 取值） | render、proxy、guide、default。Guide = **绝不**渲染。 |
| **Visibility inheritance**（可见性继承） | 父级不可见 → 所有子级都不可见，无论它们各自的设置是什么 |
| **faceVertexIndices length** | = faceVertexCounts 之和。**不是**点的数量，也**不是**面的数量。 |
| **holeIndices** | 标记某些面为孔洞 —— 它们存在于拓扑中，但**不**被渲染 |
| **UVs not auto-generated**（UV 不会自动生成） | 必须显式编写 `primvars:st` |
| **Primvar interpolation**（Primvar 插值） | constant、uniform、vertex、faceVarying。**不是** "indexed"。 |
| **inputs: and outputs:** | **并未**废弃。inputs = 输入数据。outputs = 输出数据。任意类型。 |
| **MaterialBindingAPI** | 必须先 `Apply()` 再 `Bind()` —— 两个步骤都不能少 |
| **`outputs:displacement`** | 材质的第二个输出 —— 连接用于移动几何体位置的位移着色器 |
| **Material-level inputs**（材质层级的输入） | Material 图元上的 `UsdShadeInput` 暴露外部参数 —— 而不只是在着色器上 |
| **Arbitrary attrs on shader**（在着色器上随意加属性） | ❌ 错误 —— 着色器参数**必须**使用 `UsdShadeInput`/`UsdShadeOutput` 对象 |
| **Texture on Material directly**（直接给 Material 加纹理） | ❌ 错误 —— 纹理必须经过着色器节点（`UsdUVTexture`），**不**能直接放在 Material 图元上 |
| **`intensity` units**（`intensity` 的单位） | **坎德拉（cd）或瓦特每球面度** —— **不是**流明。这是直接的考试陷阱。 |
| **`exposure`** | 指数缩放 —— 每增加一个单位，亮度**翻倍**。`final = intensity × 2^exposure` |
| **`enableShadows`** | 用于显式开关阴影投射的布尔属性。**不是**自动的。 |
| **`colorTemperature`** | 灯光上的开尔文色温属性 |
| **falloffRadius** | 控制灯光的最大作用范围。**不是**亮度。 |
| **SphereLight radius**（SphereLight 的半径） | 控制阴影的柔和度与扩散范围。**不是**亮度。 |
| **Shadows not automatic**（阴影不是自动的） | 需要 `enableShashes = true` —— 默认不开启 |
| **Volumetric scattering**（体积散射） | **不是** UsdLux 的固有特性 —— 需要额外的体积着色器。在考试中永远是错误答案。 |
| **Camera projections**（相机投影） | 只有 `perspective` 和 `orthographic`。**没有**其他。 |
| **Sensor size**（传感器尺寸） | 始终以毫米为单位。**绝不**是英寸。 |
| **clippingRange** | **就在** UsdGeomCamera schema 里。**不是**由外部处理的。 |
| **fStop** | 只控制景深。**不是**曝光时间。 |

---

_上一篇：[第 5 天 —— Schema 与数据建模](day-05-schemas-and-data-modeling.md)_  
_下一篇：[第 7 天 —— 流水线开发与数据交换](day-07-pipeline-and-data-exchange.md)_

---


### 第 7 天 —— 流水线开发与数据交换


> 来源：`sparsha-2011/physical-ai-learning-journey` · `02-openUSD-cert/notes/day-07-pipeline-and-data-exchange.md` · [原文链接](https://github.com/sparsha-2011/physical-ai-learning-journey/blob/main/02-openUSD-cert/notes/day-07-pipeline-and-data-exchange.md) · 语言：英文原文 · 中译版



# 第 7 天 —— 流水线开发与数据交换


> **OpenUSD NCP 认证学习笔记**  
> _文件格式、导出器、导入器、验证器、数据交换、流水线工具_

---

## 目录


1. [USD 文件格式的取舍](#1-usd-file-format-trade-offs)
2. [命令行工具](#2-command-line-tools)
3. [Stage 遍历](#3-stage-traversal)
4. [编写 USD 导出器](#4-writing-a-usd-exporter)
5. [资产验证器 —— usdchecker](#5-asset-validators-usdchecker)
6. [导出器钩子 —— 导出前/导出后](#6-exporter-hooks-prepost-export)
7. [移除专有依赖](#7-removing-proprietary-dependencies)
8. [流水线文档标准](#8-pipeline-documentation-standards)
9. [USD 流水线的 UI/UX 原则](#9-uiux-principles-for-usd-pipelines)
10. [构建配置管理](#10-build-configuration-management)
11. [概念性数据映射文档](#11-conceptual-data-mapping-documents)
12. [自定义导出器与导入器](#12-custom-exporters-and-importers)
13. [12b. 拆分单体资产以支持多用户协作](#12b-splitting-monolithic-assets-for-multi-user-collaboration)
14. [12c. 往返流水线 —— 导出 → DCC → 导回](#12c-round-trip-pipelines-export-dcc-import-back)
15. [数据交换脚本最佳实践](#13-data-interchange-script-best-practices)
16. [关键要点](#14-key-takeaways)

---

## 1. USD 文件格式的取舍


| 扩展名 | 格式        | 可读     | 速度     | 自包含 | 最适合                       |
| --------- | ------------- | -------- | --------- | -------------- | ------------------------------ |
| `.usda`   | ASCII 文本    | ✅ 是   | 慢      | ❌ 否          | 创作、调试、版本控制          |
| `.usdc`   | 二进制 crate  | ❌ 否    | 非常快 | ❌ 否          | 生产流水线、大体量数据               |
| `.usd`    | 自动检测 | 视情况而定  | 视情况而定   | ❌ 否          | 通用 —— USD 读取文件头来确定格式 |
| `.usdz`   | Zip 归档   | ❌ 否    | 快      | ✅ 是         | 对外交付、AR/VR 分发          |

### 重命名规则


把 `.usda` 重命名为 `.usd` 是**有效的** —— USD 会根据文件头判断出这是 ASCII 内容。  
把 `.usda` 重命名为 `.usdc` 是**无效的** —— 二者的内部二进制格式完全不同。

---

## 2. 命令行工具


### `usdcat` —— 格式转换与检查


```bash
# Convert ASCII to binary

usdcat scene.usda -o scene.usdc

# Flatten ALL composition into a single file

usdcat --flatten scene.usda -o flat.usda

# Print composition arc graph for all prims

usdcat --print-composition scene.usda
```

### `usdzip` —— 打包 .usdz 归档


```bash
# Package a USD file and ALL its dependencies into .usdz

usdzip -r delivery.usdz scene.usda

# List contents without extracting

usdzip -l delivery.usdz
```

> `usdcat` 负责格式转换和扁平化，`usdzip` 负责 `.usdz` 打包。这是两个用途各异的独立工具。

### `usdchecker` —— 资产验证


```bash
# Validate a USD file against best practices

usdchecker scene.usda

# Validate a .usdz package

usdchecker delivery.usdz
```

`usdchecker` 只做**验证** —— 它不会自动修复问题。

### `usddiff` —— 比较两个 USD 文件


```bash
usddiff scene_v1.usda scene_v2.usda
```

---

## 3. Stage 遍历


`stage.Traverse()` 会以深度优先顺序访问场景图中的所有图元（prim）。谓词（predicate）用于过滤遍历结果。

```python
from pxr import Usd, UsdGeom

stage = Usd.Stage.Open("scene.usda")

# Traverse ALL active, defined prims

for prim in stage.Traverse():
    print(prim.GetPath(), prim.GetTypeName())

# Traverse only loaded prims (excludes unloaded payloads)

predicate = Usd.TraverseInstanceProxies(
    Usd.PrimIsActive & Usd.PrimIsDefined & Usd.PrimIsLoaded
)
for prim in stage.TraverseAll():
    if predicate(prim):
        print(prim.GetPath())

# Find all meshes

for prim in stage.Traverse():
    if prim.IsA(UsdGeom.Mesh):
        mesh = UsdGeom.Mesh(prim)
        print(f"Mesh found: {prim.GetPath()}")
```

---

## 4. 编写 USD 导出器


USD 导出器把数据从专有格式转换为 USD 场景描述。正确的做法是使用 USD API —— 绝不手写 ASCII。

### 导出器模式


```python
from pxr import Usd, UsdGeom, UsdShade, Sdf, Vt, Gf

def export_scene(source_data: dict, output_path: str):
    # 1. Create the stage
    stage = Usd.Stage.CreateNew(output_path)

    # 2. Set stage metadata — always set these
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)
    stage.SetMetadata("timeCodesPerSecond", 24)

    # 3. Create root prim and set as defaultPrim
    root = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(root.GetPrim())

    # 4. Export geometry using USD API (not hand-written ASCII)
    for mesh_data in source_data["meshes"]:
        mesh = UsdGeom.Mesh.Define(stage, f"/World/{mesh_data['name']}")
        mesh.GetPointsAttr().Set(Vt.Vec3fArray(mesh_data["points"]))
        mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray(mesh_data["face_counts"]))
        mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray(mesh_data["indices"]))

    # 5. Export animation using time samples
    for frame, transform in source_data["animation"].items():
        prim.GetAttribute("xformOp:translate").Set(
            Gf.Vec3d(*transform), time=frame
        )

    # 6. Save
    stage.Save()
```

### 导出器关键规则


| ✅ 应当 | ❌ 不应 |
| ------------------------------------------------------- | ------------------------------------- |
| 使用 USD Python API 创建带 schema 的 UsdPrim      | 手写原始 USD ASCII           |
| 所有 reference 使用相对路径                   | 使用绝对路径                    |
| 在根图元上设置 `defaultPrim`                      | 让 `defaultPrim` 保持未设置             |
| 动画数据使用时间采样                      | 动画只使用默认值 |
| 专有数据使用已注册的 schema 或 metadata | 嵌入未注册的字符串 blob       |
| 使用 USD 的分层模型                                | 把所有内容扁平化到一个文件      |

---

## 5. 资产验证器 —— usdchecker


`usdchecker` 依据一组既定规则验证 USD 文件或包，这些规则旨在确保资产对下游工具而言是**可互操作且可渲染**的。

### usdchecker —— 何时使用


`usdchecker` 验证的是**文件正确性与 schema 兼容性**。它只回答一个问题：

> "这个文件的格式是否正确？"

它不会调试组合行为 —— 一个文件可以通过 usdchecker 检查，但组合结果依然是错的。

### 它检查什么


```
Schema compliance     attributes have correct types, required attributes present
File structure        USDA syntax valid, USDC not corrupted, asset paths resolvable
Best practices        defaultPrim set, upAxis set, kinds correct
```

### 什么时候该用


```
After exporting from a DCC          verify the export is schema-valid
After writing a custom exporter     confirm output before publishing
As a publish gate in CI             every asset must pass before it ships
A renderer refuses to open a file   first diagnostic - is the file valid at all?
```

### 不要用它做什么


```
Wrong opinion winning in composition   -> GetPropertyStack()
Reference not loading                  -> usdview composition query
Variant not selecting correctly        -> prim.GetPrimIndex().DumpToString()
Performance problems                   -> UsdUtils.ComputeAllDependencies
```

### 命令


```bash
usdchecker asset.usda           # basic check
usdchecker --strict asset.usda  # includes best practices
usdchecker asset.usdz           # checks all files in a package
```

`usdchecker` 常见的检查项：

- `defaultPrim` 已设置
- 所有网格都有 `extent` 属性
- 所有材质绑定都能解析到有效的图元
- 被 reference 的文件存在且可访问
- schema 版本兼容性
- `.usdz` 包的完整性

```python
# Programmatic validation using UsdUtils

from pxr import UsdUtils

errors = UsdUtils.ComplianceChecker.GetErrors(stage)
for error in errors:
    print(error)
```

> `usdchecker` 只做验证，不会自动修复。它是交付前的 QA 工具，而不是修复工具。

---

## 6. 导出器钩子 —— 导出前/导出后


### 问题所在


你们工作室有一个由流水线团队构建并维护的 Maya 转 USD 导出器。它负责处理几何体、材质、灯光和相机。每个部门都依赖它。

你的部门需要在此之上添加自定义行为 —— 给导出的网格打上 `pipeline:assetId` 标签、自动运行 `usdchecker`、把导出文件登记到资产数据库中。你有两个选择：

```
Option A — Modify the core exporter directly
  Open the pipeline team's exporter source code
  Add your custom logic inside it
  → Your version now diverges from the maintained version
  → Pipeline team releases a bug fix → you have to merge manually
  → Your change runs for every department's export → risk of breaking FX, lighting etc.
  → Hard to roll back if something breaks in production

Option B — Use hooks
  The exporter provides designated extension points
  You register your function into those points
  → Core exporter is never touched
  → Pipeline team updates their exporter → your hooks still work automatically
  → Your hook only runs when you register it → other departments unaffected
  → Remove your hook in one line if something breaks
```

钩子的存在，正是为了让你永远可以选择方案 B。

### 钩子究竟是什么


钩子就是一个**保存函数的变量**。默认情况下，它保存的是一个什么都不做的空函数 —— 一个接收参数并立即返回空值的 lambda。导出器会在工作流的指定时刻调用该变量中存放的任何东西。

在 Python 中，函数是一等对象 —— 它们可以像其他任何值一样被赋值给变量：

```python
# Assign a function to a variable — no () because you are not calling it

# you are pointing the variable at the function object

def my_function(x):
    print(x)

hook = my_function   # hook now holds the function
hook("hello")        # calls my_function("hello") → prints "hello"

# Reassign it to a different function

hook = lambda x: None   # now hook does nothing
hook("hello")            # nothing happens
```

整个机制就是这些。没有继承，没有类系统，只是一个保存可调用对象的变量。

### 核心导出器内部


这就是核心导出器内部的样子 —— 你永远看不到它，也不需要修改它：

```python
# Core exporter — owned by pipeline team, never touched by you


# Default hooks — empty lambdas that do nothing

pre_export_hook  = lambda stage, options: None
post_export_hook = lambda stage, path:    None

def run_export(maya_scene, output_path, options):
    stage = create_usd_stage()

    pre_export_hook(stage, options)    # calls whatever is in this variable
                                       # default = does nothing

    export_geometry(maya_scene, stage)
    export_materials(maya_scene, stage)
    export_lights(maya_scene, stage)
    stage.Export(output_path)

    post_export_hook(stage, output_path)  # calls whatever is in this variable
                                           # default = does nothing
```

当没有人注册钩子时，导出器调用的就是那个空 lambda —— 整个导出过程与根本没有那行钩子调用完全一样。

### 你该怎么用


你定义自己的函数，然后重新赋值这些钩子变量。你的代码完全存放在自己部门的仓库里 —— 与核心导出器彻底分离：

```python
# YOUR code — your department's repo, not the core exporter


# Pre-export hook — runs BEFORE the core export starts

def my_pre_hook(stage, options):
    # Set pipeline metadata on the stage before export
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    stage.GetRootLayer().customLayerData = {
        "pipeline:schemaVersion": "2.0",
        "pipeline:studio":        "AcmeStudios",
        "pipeline:assetId":       options["assetId"],
    }
    # Validate required data is present before export runs
    if not options.get("assetId"):
        raise ValueError("assetId must be set before exporting")

# Post-export hook — runs AFTER the core export completes

def my_post_hook(stage, output_path):
    # Add pipeline attributes to every exported mesh
    for prim in stage.Traverse():
        if prim.IsA(UsdGeom.Mesh):
            prim.CreateAttribute(
                "pipeline:exportVersion",
                Sdf.ValueTypeNames.String
            ).Set("2.0")
    # Run usdchecker automatically
    errors = UsdUtils.ComplianceChecker.GetErrors(stage)
    if errors:
        raise RuntimeError(f"Export validation failed: {errors}")
    # Register in asset database
    asset_db.register(output_path, {"department": "modeling"})

# Reassign the hook variables — your function replaces the empty lambda

exporter.pre_export_hook  = my_pre_hook
exporter.post_export_hook = my_post_hook

# Run the export — your hooks fire automatically at the right moments

exporter.run_export(maya_scene, "/output/chair_v003.usda", options)
```

### 导出前钩子 —— 在核心导出开始之前运行


- 设置 stage 元数据（`upAxis`、`metersPerUnit`、流水线版本）
- 校验必需数据是否齐备 —— 在做任何工作之前尽早失败
- 根据环境配置导出设置（渲染农场还是美术师工作站）
- 在开始创作之前，把 edit target 设置到正确的 layer
- 用 `customLayerData` 给根 layer 打标签（工作室名称、schema 版本、导出工具）

### 导出后钩子 —— 在核心导出完成之后运行


- 给导出的图元添加流水线专用属性（资产 ID、部门标签）
- 自动运行 `usdchecker` —— 在交付之前发现问题
- 把导出的文件路径登记到资产管理数据库
- 通知下游部门有新的版本可用
- 写出导出日志或审计轨迹，便于流水线追踪
- 校验输出是否符合预期（图元数量、文件大小检查）

> **经验法则：** 导出前 = 设置并校验输入。导出后 = 验证并记录输出。

### 逐步会发生什么


```
1. exporter.pre_export_hook  = my_pre_hook
   → variable now holds your function instead of the empty lambda

2. exporter.run_export() is called

3. Core exporter calls pre_export_hook(stage, options)
   → your my_pre_hook runs
   → metadata written, validation passes

4. Core export logic runs unchanged
   → geometry, materials, lights exported normally

5. Core exporter calls post_export_hook(stage, output_path)
   → your my_post_hook runs
   → pipeline attributes added, usdchecker runs, asset registered

6. Export complete
```

核心导出器的代码完全没有变化。改变的只是那两个变量中保存的值。

### 多个部门 —— 钩子列表


真实的导出器会保存一个函数**列表**，这样多个部门就能各自注册自己的钩子，而不会互相覆盖：

```python
# Inside the core exporter

pre_export_hooks = []   # empty list by default

def run_export(maya_scene, output_path, options):
    stage = create_usd_stage()

    for hook in pre_export_hooks:   # calls every registered hook in order
        hook(stage, options)

    # core export...

# Modeling department registers their hook

pre_export_hooks.append(modeling_pre_hook)

# FX department registers their hook independently

pre_export_hooks.append(fx_pre_hook)

# Both run in order — neither overwrites the other

```

### 钩子如何解决各个问题


| 没有钩子时的问题 | 钩子如何解决 |
| ------------------------------------- | --------------------------------------------------------------------------------- |
| 改动会影响每个部门 | 只有你注册时钩子才会运行 —— 其他部门不受影响 |
| fork 会与维护中的版本分叉 | 核心导出器会自动获得更新 —— 你的钩子文件完全不受影响 |
| 出问题后难以回滚 | 一行代码即可取消注册钩子 —— 导出照旧运行 |
| 归属不清晰 | 导出器由流水线团队统一拥有 —— 你的新增内容只由你自己负责 |

### 错误的做法


| 错误做法 | 原因 |
| --------------------------------------------------- | ---------------------------------------------------------- |
| 覆盖主导出函数 | 核心逻辑的维护责任转移到你身上 —— 你必须永远维护它 |
| 导出后再去修改磁盘上的 USD 文件 | 绕过流水线管控，容易出错，有损坏文件的风险 |
| 为自定义需求另建一个生成器 | 重复劳动，破坏流水线一致性 |

### 什么时候该用钩子


```
Use hooks when:
  Adding pipeline metadata to every exported asset
  Running usdchecker automatically after every export
  Registering assets in a pipeline database
  Applying custom schema attributes post-export
  Setting environment-specific stage configuration pre-export

Not needed for:
  One-off manual exports with no pipeline integration
  Simple test exports where the core exporter handles everything
```

---

## 7. 移除专有依赖


USD 资产中的专有着色器、文件格式、SDK 和 API 会造成**厂商锁定** —— 这些资产只能在支持该专有技术的工具中使用。移除这些依赖，可以让流水线变得可移植、可维护，并且面向未来。

### 五种正确的策略


**1. 用 USD 原生着色器替换专有着色器**

把专有的、面向特定渲染器的着色器重构为 UsdPreviewSurface 或 MaterialX —— 两者都是开放标准，任何符合 USD 规范的渲染器都能读取。

```
Before (proprietary — Arnold only):           After (USD native — any renderer):
def Shader "Mat" {                            def Shader "Mat" {
    token info:id = "ArnoldStandardSurface"       token info:id = "UsdPreviewSurface"
    float inputs:base = 0.8                       color3f inputs:diffuseColor = (0.8,0.8,0.8)
}                                                 float inputs:roughness = 0.3
                                              }
```

**2. 用 USD 原生格式替换专有文件格式**

把 `.abc`、`.fbx`、`.obj` 等其他专有交换格式转换为 `.usda`、`.usdc` 或 `.usdz`。原生 USD 格式不依赖任何外部格式 —— 任何 USD 工具都能直接读取。

**3. 用开源插件替代专有 SDK**

用开源的 USD 插件或标准 USD API 替换厂商专用 SDK（例如某个专有的网格处理库）。开源插件是可审查的、可移植的，并且由社区维护。

```
Proprietary SDK:   import VendorMeshSDK        # vendor lock-in
USD native:        from pxr import UsdGeom     # open standard
```

**4. 实现自定义 USD schema，而不是专有扩展**

当流水线需要新的数据类型时，应当构建符合 **USD 规范**的自定义 schema（通过 `usdGenSchema`），而不是去创建专有扩展。自定义 USD schema 可以移植到任何加载了该 schema 插件的工具中 —— 专有扩展则不行。

```
Proprietary extension:  custom:vendor:property = ...  # only works with vendor tool
Custom USD schema:      sensor:temperature = 20.0     # works anywhere with schema plugin
```

**5. 把专有动画数据转换为 USD 动画 schema**

存储在专有绑定、自定义骨骼格式或厂商专用动作格式中的动画，应当转换为 USD 的开放动画 schema —— 骨骼动画使用 `UsdSkel`，变换动画使用带时间采样的 `xformOp` 属性。这样就消除了播放时对源 DCC 工具的依赖。

```python
# Convert proprietary animation → USD time samples

for frame, transform in proprietary_animation.items():
    prim.GetAttribute("xformOp:translate").Set(
        Gf.Vec3d(*transform), time=frame
    )
# Now any USD tool can play back the animation with no proprietary dependency

```

### 错误的做法


| 错误做法 | 为什么错 |
| -------------------------------------------------- | ----------------------------------------------------------------- |
| 把专有着色器直接嵌入 USD 文件 | 加剧锁定 —— 资产从此必须依赖特定的渲染器 |
| 引用专有文件却不做转换 | 依赖依然存在 —— 只是推迟到了加载时 |
| 用厂商专用 API 进行 USD stage 组合 | 在处理层面引入了专有依赖 |
| 只做封装而不做转换 | 长期维护问题 —— 依赖依然存在于内部 |
| 用专有格式替换 USD | 依赖反而增加，违背了使用 USD 的初衷 |

### 在真实流水线中是什么样

```
PROPRIETARY (before):               USD-NATIVE (after):
─────────────────────               ────────────────────────────
ArnoldStandardSurface  →            UsdPreviewSurface / MaterialX
.fbx geometry files    →            .usdc geometry
VendorRig format       →            UsdSkel + xformOp time samples
ProprietaryShadowAPI   →            UsdLux shadow attributes
VendorMeshSDK          →            pxr.UsdGeom Python API
Proprietary extensions →            Custom USD schemas (usdGenSchema)
```

目标：生态系统中任何支持 OpenUSD 的工具，都应当能够打开、读取并渲染该资产，而**无需安装任何厂商专有软件**。

---

## 8. 管线文档标准


优秀的 USD 管线文档必须包含足够的技术细节，使开发者能够实现并维护该管线。

### 必需内容


- 每个管线节点上的 USD **schema 类型**
- **Stage 分层结构** —— 哪些层以何种方式组合
- 节点之间的**数据流** —— 每个 Stage 的输入与输出
- **组合弧标注** —— 哪些弧连接了哪些资产
- **依赖关系映射** —— 明确列出每个 Stage 依赖于什么

### 不足之处


- 缺乏 USD 专属细节的通用框图
- 只有代码片段而没有可视化示意图
- 面向技术工作的高层业务流程图

---

## 9. USD 管线的 UI/UX 原则


USD 的组合模型是一张图 —— 层引用层，资产引用资产，变体分支并合。USD 管线工具的 UI 应当反映这一底层结构，而不是在其之上强加线性或模态的工作流。

### 核心原则


**1. 基于节点的可视化编辑器**

USD 组合是一张有向图。UI 应当以有向图的形式来呈现它 —— 用节点表示 layer 与 asset，用连线表示弧（references、sublayers、payloads）。线性列表或顺序步骤向导会错误地呈现 USD 实际的组合方式。

```
shot.usda ──────────────────────────────── [Shot Node]
               ↑             ↑                  ↑
          [Anim Node]  [Layout Node]      [Asset Node]
          anim.usda    layout.usda        chair_asset.usda

Each arrow = a composition arc
Each node  = a layer or asset
```

**2. 实时反馈**

USD 的变更通知系统会在每次编辑时立即触发。UI 应当在组合错误、校验警告和加载状态一出现的当下就把它们呈现出来 —— 而不是等到点击模态的“应用”或“提交”按钮之后。

**3. 上下文相关的帮助与工具提示**

每个节点和连线都应带有内联文档，说明它表示的是哪一种弧、prim 使用什么 schema 类型、以及有哪些可用的属性。来自 `plugInfo.json` 和 `schema.usda` 的 schema 定义中包含这些文档 —— 应当把它们呈现在 UI 中。

**4. 支持分支与合并**

USD 的 sublayers 和 references 以非线性的方式分支与合并。强制单一线性流程的管线工具会错误地呈现组合模型。UI 必须支持每个节点有多个输入和输出 —— 就如同 USD 组合本身一样。

**5. 配置不使用模态对话框**

USD 的编辑是实时的 —— `attr.Set()` 会立即生效。UI 中的配置变更应当是非阻塞的。那种必须先点“应用”或“确定”才生效的模态对话框，对 USD 管线工具来说在架构上是错误的。

**6. 可扩展性 —— 惰性呈现**

大型场景包含数千个 prim 和数十个 layer。UI 应当体现 USD 的 payload 延迟加载模型 —— 在节点被显式展开之前只显示节点本身，而不加载其完整内容，这与 `Usd.Stage.LoadNone` + 显式 `Load()` 的做法一致。

### 错误模式


| 反模式 | 为什么是错的 |
| -------------------------------------------- | --------------------------------------------------------------- |
| 每一次配置变更都使用模态对话框 | 阻塞工作流，错误地呈现 USD 的实时编辑模型 |
| 仅支持线性的管线流程 | USD 会分支与合并 —— 线性流程在结构上是错误的 |
| 没有定制选项 | USD 管线因工作室而异 —— 不存在通吃一切的标准方案 |
| 编辑前先做扁平化 | 抵消了 USD 原本要提供的组合优势 |
| 直到最终提交前都没有错误反馈 | USD 会立即呈现组合错误 —— UI 也应当如此 |
| 启动时完整加载所有节点 | 忽略了 USD 的 payload 延迟加载设计 |

### 为什么基于节点是正确的思维模型


```
USD asks:   "what layers compose this prim?"
Node UI answers visually:
  [chair_asset.usda] ──reference──> [ChairA in shot.usda]
                                         ↑
                               [anim.usda override]

Linear UI fails to represent:
  - which layer is strongest
  - where overrides come from
  - how arcs stack and resolve
```

> **规则：** 如果底层的 USD 数据结构是一张图，那么 UI 也必须是图。任何把这种结构扁平化为顺序列表的工具，都在隐藏艺术家理解与调试组合时所需的信息。

---

## 10. 构建配置管理


USD 管线要求环境变量、插件版本和 schema 部署在**每一个环境中都完全一致** —— 艺术家工作站、渲染农场、CI/CD 流水线和客户交付环境皆是如此。构建配置管理正是确保这种一致性的实践。

### 为什么需要它


若不这样做，同一个 `.usda` 文件在不同机器上的行为会不同：

```
Artist machine:   USD 23.08  acmeSensors.so v1.2  Python 3.10
Render farm:      USD 22.11  acmeSensors.so v1.0  Python 3.9

Same file. Different results.
Renders differ from viewport.
Schema attributes resolve incorrectly.
No crash — silent wrong output.
```

USD 插件版本不匹配导致的是**静默数据损坏**，而不是报错。插件版本之间某个属性被重命名，意味着 `attr.Get()` 会返回 `None` 而不是抛出异常 —— 管线看起来能正常工作，却产出了错误的结果。

### 核心原则


**1. 在受版本控制的配置文件中显式声明构建变体**

每个环境的精确依赖版本都声明在一个提交到仓库的配置文件里 —— 而不是靠假设或逐台机器手动设置：

```yaml
# build_config.yaml — committed to source control
usd_version: "23.08"
python_version: "3.10"
plugins:
  acmeSensors: "1.2.0"
pxr_plugin_path: "/studio/plugins/23.08/v1.2/"
```

**2. 集中式配置 —— 单一事实来源**

一个配置文件驱动所有环境。升级插件版本只需修改一个文件并提交 —— 任何拉取该仓库的环境都会自动获得相同的版本。

**3. 针对不同平台的条件逻辑**

```yaml
platforms:
  linux: { library_ext: ".so", plugin_path: "/studio/plugins/" }
  windows: { library_ext: ".dll", plugin_path: "C:/studio/plugins/" }
```

**4. 绝不要忽略构建缓存**

构建缓存（cmake、ninja）只会重新编译发生变化的部分。忽略缓存会强制全量重建 —— 对于可能需要数十分钟才能编译完成的大型 USD schema 库来说是一种浪费。

```bash
cmake --build .              # correct — uses cache
cmake --build . --clean-first  # wrong — discards cache, full rebuild
```

**5. 记录所有环境变量**

每一个影响构建或运行时的变量都必须被明确记录，并由配置系统统一设置 —— 而不是留给每位艺术家手动配置：

```
PXR_PLUGINPATH_NAME   path to custom schema plugins
USD_INSTALL_ROOT      path to USD installation
PYTHONPATH            path to USD Python bindings
TF_DEBUG              debug symbol flags
```

### 错误做法


| 反模式 | 为什么不行 |
| ---------------------------------- | ------------------------------------------------------------------------ |
| 未记录的环境变量 | 艺术家手动配置 → 环境不一致 |
| 构建脚本中硬编码路径 | 在不同机器、操作系统或目录结构下会失效 |
| 忽略构建缓存 | 不必要的全量重建 —— 在大型插件库上浪费大量时间 |
| 没有版本锁定 | 插件更新会在各环境中悄无声息地改变行为 |
| 每台机器手动配置 | 不可复现 —— “在我机器上能跑” 不是管线 |

> **核心规则：** 如果管线中任意两台机器的 `PXR_PLUGINPATH_NAME`、`USD_INSTALL_ROOT` 或插件版本不同 —— 那么你的管线就不在配置管理之下，静默错误将会发生。

---

## 11. 概念性数据映射文档


概念性数据映射文档是一份**逻辑蓝图**，用于在编写任何代码之前明确源 schema 属性如何映射到目标 USD schema 属性。

### 必需内容


- **Schema 对应关系** —— 源 prim 类型与目标 USD prim 类型之间的显式映射（例如 `FBXMesh` → `UsdGeomMesh`）
- **属性对应关系** —— 源属性名 → 目标属性名、数据类型、单位（例如 `diffuseColor` 映射为 `color3f` 类型的 `inputs:diffuseColor`）
- **转换规则** —— 复杂转换如何处理：单位缩放、轴向翻转、坐标系转换
- **必填字段与可选字段** —— 哪些属性必须存在才能构成一次有效交换，哪些可以省略
- **元数据继承映射** —— 源元数据如何映射到 USD 的 layer/prim 元数据，以及哪些元数据会沿层级向上传递
- **变体集映射策略** —— 源资产的各种变化（LOD 层级、材质替换、配置选项）如何映射到 USD 变体集

### 不应出现在映射文档中的内容


以下内容属于**其它**文档 —— 不应出现在概念性映射文档中：

| 内容 | 应当放在哪里 |
| ------------------------------------------- | ----------------------------------- |
| 运行时性能优化技术 | 实现文档或优化文档 |
| USD API 使用示例与代码片段 | 技术实现文档 |
| 错误处理与校验流程 | 技术文档或运维文档 |
| 源/目标 schema 的版本历史 | Schema 管理文档 |
| 物理存储格式细节 | 实现文档 |
| 含实际数据的示例载荷 | 测试文档 |

> **考试规律：** 如果某个选项在映射文档类问题的语境下提到“API 示例”、“错误处理”、“运行时性能”或“存储格式” —— 那就是错的。映射文档讲的是_数据关系_，而不是_实现细节_。

---

## 12. 自定义导出器与导入器


### 根本区别


```
EXPORTER                              IMPORTER
────────────────────────────          ────────────────────────────
Reads:   proprietary format           Reads:   USD
Writes:  USD                          Writes:  proprietary format

Source:  Maya, Houdini, simulation,   Source:  USD stage
         legacy pipeline data
Target:  USD stage                    Target:  game engine, renderer,
                                               legacy tool, DCC

Purpose: bring data INTO USD world    Purpose: take data OUT of USD world
```

### 自定义导出器


#### 它做什么


从专有格式或 DCC 格式读取数据，并将其写出为
USD stage。导出器负责把每一个源概念翻译成
正确的 USD schema。

```
Maya mesh node          →   UsdGeom.Mesh
Maya joint hierarchy    →   UsdSkel.Skeleton
Maya material           →   UsdShade.Material
Maya keyframes          →   xformOp time samples
Maya lights             →   UsdLux.SphereLight
```

#### 正确模式 —— 两遍处理


```python
# PASS 1 — read and validate the SOURCE (proprietary format)
# All unit conversion, type conversion, and validation happens here
# before any USD state is created
intermediate = {
    "meshes":    parse_source_geometry("scene.ma"),   # convert units here
    "materials": parse_source_materials("scene.ma"),  # validate types here
    "animation": parse_source_animation("scene.ma"),  # convert euler→quat here
}

# PASS 2 — write to USD using clean validated intermediate data
stage = Usd.Stage.CreateNew("output.usda")
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
stage.SetDefaultPrim(UsdGeom.Xform.Define(stage, "/World").GetPrim())

with Sdf.ChangeBlock():                               # batch notifications
    for mesh_data in intermediate["meshes"]:
        mesh = UsdGeom.Mesh.Define(stage, mesh_data["path"])
        mesh.GetPointsAttr().Set(mesh_data["points"])
        mesh.GetFaceVertexCountsAttr().Set(mesh_data["face_counts"])
        mesh.GetFaceVertexIndicesAttr().Set(mesh_data["indices"])

stage.Export("output.usda")                           # not stage.Save()
```

#### 通过 pre/post 钩子扩展


绝不要覆盖主导出函数。请使用钩子来扩展它：

```python
def pre_export_hook(stage):
    # runs BEFORE core export logic
    # use for: setting stage metadata, upAxis, metersPerUnit
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    stage.GetRootLayer().customLayerData = {
        "pipeline:version":    "2.0",
        "pipeline:exportTool": "MayaExporter",
    }

def post_export_hook(stage):
    # runs AFTER core export logic
    # use for: adding pipeline attributes, running usdchecker, registering asset
    for prim in stage.Traverse():
        if prim.IsA(UsdGeom.Mesh):
            prim.CreateAttribute(
                "pipeline:exported",
                Sdf.ValueTypeNames.Bool
            ).Set(True)
```

#### 导出器关键规则


- **继承 UsdGeom 类** —— 自动获得内置的 schema 校验
- **使用 `stage.Export(path)`** —— 将扁平化解析后的副本写入任意路径
- **不要使用 `stage.Save()`** —— 它只会写入 root layer 自身的底层文件
- **设置 `defaultPrim`** —— 每个发布的资产都必须设置它
- **注册自定义 schema** —— 导出自定义属性之前必须先注册 TfType
- **使用相对路径** —— 绝不要硬编码绝对路径
- **把批量创作包裹在 `Sdf.ChangeBlock()` 中** —— 这对性能至关重要

### 自定义导入器


#### 它做什么


读取 USD stage 并将其翻译为另一种格式。
导入器负责把 USD 概念映射回目标系统中
的等价物。

```
UsdGeom.Mesh            →   game_mesh_t struct
UsdSkel.Skeleton        →   game_skeleton_t struct
UsdShade.Material       →   game_material_t struct
xformOp time samples    →   game_animation_t keyframes
UsdLux.SphereLight      →   game_light_t struct
```

#### 正确模式 —— 两遍处理


```python
# PASS 1 — read and validate the SOURCE (USD)
# Traverse the stage and extract data into intermediate representation
# All validation, unit conversion, and error handling happens here
stage = Usd.Stage.Open("character.usda")
intermediate = {"meshes": [], "materials": [], "lights": []}

for prim in stage.Traverse():
    if prim.IsA(UsdGeom.Mesh):
        mesh = UsdGeom.Mesh(prim)
        intermediate["meshes"].append({
            "path":        str(prim.GetPath()),
            "points":      mesh.GetPointsAttr().Get(),
            "face_counts": mesh.GetFaceVertexCountsAttr().Get(),
            "indices":     mesh.GetFaceVertexIndicesAttr().Get(),
        })
    elif prim.IsA(UsdLux.SphereLight):
        light = UsdLux.SphereLight(prim)
        intermediate["lights"].append({
            "path":      str(prim.GetPath()),
            "intensity": light.GetIntensityAttr().Get(),
            "radius":    light.GetRadiusAttr().Get(),
        })

# PASS 2 — write to the target format from clean intermediate data
write_game_binary("character.gamebin", intermediate)
```

#### 导入器关键规则


- **绝不要把 USD 读取与目标格式写入交错进行** —— 始终采用两遍处理
- **使用 `Usd.Stage.Open()` 并做好错误处理** —— 处理文件缺失与组合错误
- **在合并来自多个 USD 来源的数据时使用 `UsdUtils.CopyLayer()`**
- **检查 `attr.HasAuthoredValue()`** —— 区分显式赋值与 schema 回退值
- **显式加载 payload** —— 当需要大量几何数据时使用 `stage.Load(path)`
- **导入时不要要求必须存在自定义 schema** —— 自定义 schema 是对 USD 数据类型的扩展，读取 USD 并不需要它们

### 并排对比


```
                    EXPORTER                    IMPORTER
                    ────────────────────        ────────────────────
Pass 1 reads:       proprietary format          USD stage
Pass 1 validates:   source data                 USD attribute values
Pass 2 writes:      USD (UsdGeom, UsdShade)     target format
Serialise with:     stage.Export(path)          write_target_format()
Key API:            UsdGeom.Mesh.Define()       prim.GetAttribute().Get()
Extend via:         pre/post hooks              pre/post hooks
```

### 错误做法


| 错误做法 | 为什么不行 |
| ------------------------------------ | --------------------------------------------------------------- |
| 直接把原始二进制写入 USD | 绕过 USD 序列化 —— 会损坏文件 |
| 手写 USD ASCII | 绕过 schema 校验和类型检查 |
| 覆盖主导出函数 | 应使用 pre/post 钩子 —— 覆盖会丢失内置功能 |
| 把解析与 USD 创作交错进行 | 难以调试、无法独立测试、非常脆弱 |
| 导出时忽略变体集 | 配置会丢失 —— 数据保真度被破坏 |
| 为追求速度而跳过 schema 校验 | 静默损坏 —— 校验能尽早发现类型不匹配 |
| 使用绝对文件路径 | 在其他任何机器上都会失效 |
| 导入时要求必须存在自定义 schema | 自定义 schema 用于扩展数据类型 —— 读取 USD 并不需要 |
| 交付时使用 `stage.Save()` | 只会写入底层文件 —— 应使用 `stage.Export()` |

### 考试规律识别


| 题目问的是 | 正确答案 |
| -------------------------------------------- | ---------------------------------------------------------- |
| 如何在导出器中确保 schema 合规 | 继承 UsdGeom 类 |
| 如何序列化完整场景用于交付 | 用 `stage.Export(path)` 而不是 `stage.Save()` |
| 如何扩展导出器 | pre/post 钩子 —— 绝不覆盖主函数 |
| 如何组织导入器 | 两遍处理：先中间表示，再写入目标 |
| 用什么校验导出结果 | `usdchecker` —— 只做校验，不会自动修复 |
| 导入是否需要自定义 schema | 不需要 —— 自定义 schema 用于扩展类型，读取时并不需要 |
| 导入时如何合并 layer | `UsdUtils.CopyLayer()` |

---

## 12b. 拆分单体资产以支持多用户协作


### 它是什么


**单体资产**是指一个包含全部内容的 USD 文件 —— 几何、材质着色、动画和绑定全部由一个人在同一个 layer 中创作完成。这对个人独立工作还算可行，但在生产环境中就难以为继，因为多个部门会同时负责同一资产的不同部分。

**拆分**是指把那个单一文件分解成多个由各部门拥有的 layer，并通过 sublayers 或 references 重新组合到一起。每个部门只拥有并编辑属于自己的 layer —— 没有人会覆盖他人的工作。

### 为什么需要它


```
Monolithic (one file, one owner at a time):
character.usda
/Character/Mesh          ← modeling owns this
/Character/Rig            ← rigging owns this
/Character/Materials      ← look dev owns this
/Character/Anim           ← animation owns this

Problem:
Only one person can edit the file at a time
File locking blocks other departments
A rigging change overwrites an animation edit
Cannot render partially complete work
Version conflicts are constant
```

```
Split (multiple files, one owner each):
character_geo.usda        ← modeling owns, edits freely
character_rig.usda        ← rigging owns, edits freely
character_look.usda       ← look dev owns, edits freely
character_anim.usda       ← animation owns, edits freely
character_shot.usda       ← sublayers all four, nobody edits directly

Benefits:
Each department works in parallel with no conflicts
Partial completion is renderable at any time
One department’s change never touches another’s file
LIVRPS resolves any opinion conflicts cleanly
```

### 分层策略


shot 文件按 LIVRPS 顺序把所有部门文件都作为 sublayer —— 最强的 layer 在冲突中胜出：

```usda
#usda 1.0
(
    subLayers = [
        @./character_anim.usda@,    # strongest — animation overrides everything
        @./character_look.usda@,    # look dev overrides geo and rig
        @./character_rig.usda@,     # rig overrides base geo
        @./character_geo.usda@      # weakest — base geometry
    ]
)
```

### Python 实现

```python
from pxr import Usd, UsdGeom, UsdShade, Sdf

# --- Step 1: Create department-owned layers ---

# Modeling layer — owns base geometry
geo_stage = Usd.Stage.CreateNew("character_geo.usda")
mesh = UsdGeom.Mesh.Define(geo_stage, "/Character/Body")
mesh.GetPointsAttr().Set(base_points)
mesh.GetFaceVertexCountsAttr().Set(face_counts)
mesh.GetFaceVertexIndicesAttr().Set(face_indices)
geo_stage.Save()

# Look dev layer — owns materials only
look_stage = Usd.Stage.CreateNew("character_look.usda")
# over “Character” — sparse override, does not redefine geometry
look_root = look_stage.OverridePrim("/Character")
UsdShade.MaterialBindingAPI.Apply(
    look_stage.OverridePrim("/Character/Body")
).Bind(UsdShade.Material.Define(look_stage, "/Looks/Skin"))
look_stage.Save()

# Animation layer — owns transforms only
anim_stage = Usd.Stage.CreateNew("character_anim.usda")
anim_prim  = anim_stage.OverridePrim("/Character")
xform      = UsdGeom.Xformable(anim_prim)
# Author time samples on the override — geo layer untouched
for frame, pos in animation_data.items():
    anim_prim.GetAttribute("xformOp:translate").Set(pos, time=frame)
anim_stage.Save()

# --- Step 2: Create the shot file that composes all layers ---
shot_stage = Usd.Stage.CreateNew("character_shot.usda")
root_layer = shot_stage.GetRootLayer()

# Add department layers as sublayers — strongest first
root_layer.subLayerPaths = [
    "./character_anim.usda",   # strongest
    "./character_look.usda",
    "./character_rig.usda",
    "./character_geo.usda",    # weakest
]
shot_stage.Save()
# character_shot.usda composes all four — full character visible
# each department can keep editing their own file independently
```
### 关键规则


- 每个部门图层使用 **`over`**（稀疏覆盖，sparse override）而不是 **`def`** —— 只在几何图层中定义图元，在其他所有图层中对它进行覆盖
- 镜头文件只负责管理子图层的顺序 —— 各部门从不直接编辑镜头文件
- 冲突由 LIVRPS 裁决 —— 动画层的意见胜过 look dev 层，look dev 层胜过 rig 层，rig 层胜过几何层
- 每个图层都可以独立提交到版本控制系统 —— 部门之间不会产生合并冲突

> **考试关联：**“把整体式资产拆分为多个可协作的工作流”被列为 Composition 与 Pipeline 两个领域下的一项实测技能。答案始终是采用子图层 + 部门自有图层 + 稀疏覆盖 —— 而不是在文件之间复制数据，也不是用 variant set 来做协作。

---

## 12c. 往返管线 —— 导出 → DCC → 导回


**它是什么：** 往返管线把数据从 USD 移入外部 DCC 工具（Maya、Houdini、Blender），允许美术师在该工具中工作，然后再把修改后的数据带回 USD —— 全程保留原有的结构、元数据和自定义属性。

**为什么需要它：** USD 是中枢，但美术师是在 DCC 工具里干活的。一个在 USD 中建模的角色需要送到 Maya 做绑定，再带着完好的 rig 回到 USD。一个 USD 模拟需要送到 Houdini 做特效，再把烘焙好的模拟带回来。如果没有往返策略，数据会在每一次往返中丢失或被破坏。

**核心挑战：** DCC 工具无法理解自定义 USD schema、带命名空间的属性、关系以及 USD 元数据。粗暴的导出会把这些统统剥掉，粗暴的导入会覆盖原始文件。稳健的往返流程会保留 DCC 无法理解的内容，并且只合并真正发生变化的部分。

```
Round-trip without strategy (data loss):
USD stage              →   Export to Maya    →   Maya modifies mesh
/Chair/Seat               .fbx or .ma            (rig is added)
- custom:pipeline:id         ← lost               ← lost in .ma
- material bindings          ← lost               ← gone
- variant sets               ← lost               ← gone
←   Import back      ←   Re-import
overwrites original   all metadata gone
```
```
Round-trip with strategy (data preserved):
USD stage              →   Export to Maya    →   Maya modifies mesh
/Chair/Seat               custom exporter         (rig is added)
- custom:pipeline:id         ← preserved in sidecar
- material bindings          ← preserved in sidecar
- variant sets               ← preserved in sidecar
←   Import back      ←   Two-pass importer
merges Maya data      restores sidecar data
into original         + applies Maya changes
USD layer             on top
```

**sidecar 模式 —— 保留 DCC 无法处理的内容：**

```python
from pxr import Usd, UsdUtils, UsdGeom, Sdf

# --- EXPORT PHASE ---

def export_to_dcc(usd_path: str, dcc_path: str, sidecar_path: str):
    stage = Usd.Stage.Open(usd_path)

    # Step 1: Save everything the DCC cannot understand into a sidecar USD file
    sidecar = Sdf.Layer.CreateNew(sidecar_path)
    # Copy custom metadata, variant sets, relationships
    # into the sidecar before the DCC strips them
    UsdUtils.CopyLayer(stage.GetRootLayer(), sidecar)
    sidecar.Save()

    # Step 2: Export only DCC-compatible data
    # (geometry, transforms, basic materials)
    export_geometry_to_dcc(stage, dcc_path)
    # DCC file does not contain USD-specific data
    # but sidecar preserves everything

# --- IMPORT PHASE (after DCC work is done) ---

def import_from_dcc(dcc_path: str, sidecar_path: str, output_usd: str):

    # Pass 1 — parse DCC file into intermediate
    dcc_data = parse_dcc_file(dcc_path)
    # validate, convert units, extract what changed

    # Pass 2 — build USD from intermediate
    stage = Usd.Stage.CreateNew(output_usd)

    # Restore preserved data from sidecar
    stage.GetRootLayer().subLayerPaths.append(sidecar_path)
    # sidecar is weaker — DCC changes override it

    # Apply DCC changes on top as stronger layer
    stage.SetEditTarget(stage.GetRootLayer())
    for mesh_data in dcc_data["meshes"]:
        mesh = UsdGeom.Mesh.Get(stage, mesh_data["path"])
        # Apply only what the DCC changed — not a full rewrite
        if mesh_data.get("points_changed"):
            mesh.GetPointsAttr().Set(mesh_data["points"])

    stage.Save()
    # Result: USD file with DCC changes on top + all original metadata preserved
```

**往返必须保留的内容：**

| 数据类型                      | DCC 能理解吗？ | 往返策略                             |
| ----------------------------- | -------------- | ------------------------------------ |
| 几何体（点、面）              | 是             | 直接导出后再导回                     |
| 变换                          | 是             | 直接导出后再导回                     |
| 基础材质                      | 部分能         | 导出近似结果，再从 sidecar 恢复      |
| 自定义 schema 属性            | 否             | 保存在 sidecar 中，导入时恢复        |
| Variant set                  | 否             | 保存在 sidecar 中，导入时恢复        |
| USD 关系                      | 否             | 保存在 sidecar 中，导入时恢复        |
| 管线元数据                    | 否             | 保存在 sidecar 中，导入时恢复        |
| 时间采样 / 动画               | 部分能         | 导出为 DCC 关键帧，导回为时间采样    |

> **往返 = 导出 + sidecar + 两遍导入。** sidecar 模式正是生产级往返流程与粗糙做法之间的分水岭。没有 sidecar，每一次 DCC 往返都会永久性地丢失 USD 特有数据。

> **考试关联：**“在 DCC 与 USD 之间实现往返管线”被列为 Data Exchange 与 Pipeline 两个领域下的一项实测技能。正确的答案模式始终围绕着“保留 DCC 无法理解的内容，并在导入时进行合并”，而不是覆盖原始 USD 文件。

---

## 13. 数据交换脚本最佳实践


### `UsdUtils.CopyLayer` —— 为合并而复制图层


当从多个 USD 源合并数据时，`UsdUtils.CopyLayer` 是推荐的工具函数，可在合并前准确地复制整个图层。

```python
from pxr import UsdUtils, Sdf

# CopyLayer duplicates an entire SdfLayer cleanly
# Signature: UsdUtils.CopyLayer(source: SdfLayer, dest: SdfLayer) -> bool
source_layer = Sdf.Layer.FindOrOpen("department_anim.usda")
dest_layer   = Sdf.Layer.CreateAnonymous("merged.usda")

success = UsdUtils.CopyLayer(source_layer, dest_layer)
# dest_layer now contains all specs from source_layer
# source_layer is unchanged

# Use when: merging department layers, combining asset versions,
#           duplicating a layer before modifying it (preserve original)
```

> **为什么用 CopyLayer 而不是手动复制：** 用 Python 循环遍历 specs 来手动复制图层容易出错，并且可能遗漏嵌套的 specs、元数据、关系以及组合弧数据。`UsdUtils.CopyLayer` 能够正确处理完整的图层 spec 图。

### 完整最佳实践清单


| ✅ 始终要做                                                | ❌ 绝不要做                            |
| ---------------------------------------------------------- | -------------------------------------- |
| 使用 `Usd.Stage` API 并做恰当的错误处理                    | 把 USD 文件当作纯文本直接编辑          |
| 使用 `UsdUtils.CopyLayer` 复制图层以便合并                 | 手动遍历 specs 来复制图层              |
| 使用 USD 的分层与组合来合并各个源                          | 在脚本中手动合并数据                   |
| 使用 USD Python API 配合 schema 创建带 schema 的 UsdPrim   | 手写 USD ASCII                         |
| 使用相对路径或资产解析器                                   | 使用绝对文件路径                       |
| 为专有元数据使用恰当的 schema                              | 嵌入未注册的字符串数据块               |
| 对动画数据使用时间采样                                     | 对动画使用静态默认值                   |
| 全程保持 schema 校验                                       | 为了加快脚本速度而跳过校验             |

---

## 14. 关键要点


| 概念                                       | 需要记住的内容                                                                                                                                                 |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `.usd` 扩展名                             | 通用格式 —— USD 会根据文件头自动识别 ASCII 还是二进制                                                                                                          |
| 将 `.usda` 重命名为 `.usdc`                | 无效 —— 两者是不同的二进制格式                                                                                                                                |
| `usdcat`                                  | 格式转换与扁平化。打包 `.usdz` 则使用 `usdzip`                                                                                                                |
| `usdchecker`                              | 做校验。不会自动修复。                                                                                                                                          |
| 导出器钩子                                | 前置/后置钩子用于扩展导出。绝不要覆盖主导出函数                                                                                                                |
| 专有依赖                                  | 5 种策略：替换着色器、文件格式、SDK、专有扩展、动画格式                                                                                                        |
| 开源插件                                  | 用来替代专有 SDK —— 可移植、易维护、没有厂商锁定                                                                                                              |
| 自定义 schema 与专有扩展                   | 自定义 USD schema（usdGenSchema）具有可移植性。专有扩展则需要厂商工具。                                                                                        |
| 专有动画 → USD                            | 转换为 `UsdSkel` 或 `xformOp` 时间采样 —— 消除对 DCC 的依赖                                                                                                    |
| 在组合中使用厂商专用 API                   | ❌ 错误 —— 在处理层面引入了专有依赖                                                                                                                             |
| 在 USD 中嵌入专有着色器                    | ❌ 错误 —— 加重了锁定，而不是消除锁定                                                                                                                         |
| 映射文档包含                              | schema 对应关系、属性对应关系、转换规则、必填/选填字段、**元数据继承映射**、**variant set 映射策略**                                                          |
| 映射文档不包含                            | API 使用示例、错误处理、运行时性能、存储格式细节、示例 payload —— 这些属于实现/技术文档                                                                        |
| 导入器模式                                | 先解析到中间表示，然后再填充 USD                                                                                                                              |
| 导入用的自定义 schema                     | 导入时**不需要** —— 只有在扩展 USD 数据类型时才需要                                                                                                            |
| 自定义导出器 —— 继承自 UsdGeom             | 自动获得内置的 schema 校验 —— 正确做法                                                                                                                        |
| `stage.Export(path)`                      | 标准序列化方法 —— 把完整解析后的场景写入任意路径                                                                                                              |
| 把原始二进制写入 USD 文件                 | ❌ 错误 —— 会损坏文件，绕过 USD 序列化                                                                                                                         |
| 把外部引用作为原始数据嵌入                | ❌ 错误 —— 破坏模块性，增大文件体积                                                                                                                            |
| `UsdUtils.CopyLayer(src, dest)`           | 合并数据时复制图层的正确工具 —— 能处理完整的 spec 图                                                                                                          |
| 手动复制 spec                             | ❌ 错误 —— 容易出错，遗漏嵌套的 specs 和元数据                                                                                                                |
| Stage 缓存                                | `UsdStageCache` —— 避免重复的重新组合                                                                                                                         |
| `SdfChangeBlock`                          | 批量发送变更通知 —— 对批量创作的性能至关重要                                                                                                                  |
| 扁平化保留                                | 时间采样（动画）、几何体类型                                                                                                                                   |
| 扁平化丢弃                                | Variant set（被折叠）、组合弧                                                                                                                                   |

---

_上一篇：[第 6 天 — 可视化](day-06-visualization.md)_  
_下一篇：[第 8 天 — 内容聚合](day-08-content-aggregation.md)_

---


### 第 8 天 — 内容聚合


> 来源：`sparsha-2011/physical-ai-learning-journey` · `02-openUSD-cert/notes/day-08-content-aggregation.md` · [原文链接](https://github.com/sparsha-2011/physical-ai-learning-journey/blob/main/02-openUSD-cert/notes/day-08-content-aggregation.md) · 语言：英文原文 · 中译版



# 第 8 天 — 内容聚合

> **OpenUSD NCP 认证学习笔记**  
> _实例化、PointInstancer、资产管理、场景图最佳实践_

---

## 目录

1. [实例化 — USD 原生实例化](#1-实例化-usd-原生实例化)
2. [点实例化 — UsdGeomPointInstancer](#2-点实例化-usdgeompointinstancer)
3. [逐实例覆盖](#3-逐实例覆盖)
4. [3b. Payload 剪枝 — 优化场景聚合](#3b-payload-剪枝-优化场景聚合)
5. [3c. 接口 Schema — 可组合组件的松耦合](#3c-接口-schema-可组合组件的松耦合)
6. [3d. 协作式聚合 — 合成弧 vs 文件锁](#3d-协作式聚合-合成弧-vs-文件锁)
7. [资产版本控制与管理](#4-资产版本控制与管理)
8. [场景图组织模式](#5-场景图组织模式)
9. [关键要点](#6-关键要点)

---

## 1. 实例化 — USD 原生实例化

**实例化**允许多个 prim 共享同一份底层数据（**原型**），而不在内存中复制它。所有实例都引用同一个原型，从而大幅降低重复对象带来的内存占用。

```python
from pxr import Usd, UsdGeom

stage = Usd.Stage.Open("scene.usda")

# Make a prim instanceable
tree_prim = stage.GetPrimAtPath("/World/Tree_001")
tree_prim.SetInstanceable(True)
# USD now treats this prim as an instance that shares a prototype

# Check instancing status
print(tree_prim.IsInstanceable())   # True
print(tree_prim.IsInstance())       # True — if USD has promoted to instance
print(tree_prim.IsPrototype())      # True — if this prim IS the prototype
```

### 原生实例化的规则

- 当某个 prim 的元数据中设置了 `instanceable = True` 时，它就变成**可实例化的**
- USD 会自动创建一个**原型**（即共享的数据）
- 所有引用同一数据的可实例化 prim 都会成为该原型的实例
- 实例之间共享几何体数据——内存占用只对应一个原型，而不是 N 份副本
- **实例代理（instance proxy）**——在实例上读取属性会返回原型的值；要直接写入实例的子级，必须先调用 `SetInstanceable(False)`

```usda
def Xform "Tree_001" (
    instanceable = true
    prepend references = @./tree_asset.usda@
) { }

def Xform "Tree_002" (
    instanceable = true
    prepend references = @./tree_asset.usda@
) { }
# Both trees share one prototype — memory for one tree
```

---

## 2. 点实例化 — UsdGeomPointInstancer

`UsdGeomPointInstancer` 按照数组所定义的位置，放置一个或多个原型 prim 的许多实例。它是 USD 中性能最高的实例化机制——专为森林、人群、粒子系统以及任何包含数千到数百万个重复对象的场景而设计。

```
UsdGeomPointInstancer (/World/Forest)
├── prototypes (hidden):
│   └── /World/Forest/Protos/Tree (Mesh — the shared geometry)
├── protoIndices  = [0, 0, 0, 0, ...]  # which prototype each instance uses
├── positions     = [(x,y,z), ...]      # where each instance is placed
├── orientations  = [(quat), ...]       # rotation of each instance
└── scales        = [(sx,sy,sz), ...]   # scale of each instance
```

### Python API — `UsdGeom.PointInstancer`

```python
from pxr import UsdGeom, Vt, Gf, Usd

stage      = Usd.Stage.CreateInMemory()
instancer  = UsdGeom.PointInstancer.Define(stage, "/World/Forest")

# 1. Define the prototype (the shared geometry)
proto_root = stage.DefinePrim("/World/Forest/Protos")
tree_proto = UsdGeom.Sphere.Define(stage, "/World/Forest/Protos/Tree")
tree_proto.GetRadiusAttr().Set(0.5)

# 2. Point instancer to the prototypes
instancer.GetPrototypesRel().AddTarget("/World/Forest/Protos/Tree")

# 3. Define per-instance arrays
num_instances = 1000
import random

positions = Vt.Vec3fArray([
    Gf.Vec3f(random.uniform(-50, 50), 0, random.uniform(-50, 50))
    for _ in range(num_instances)
])
proto_indices = Vt.IntArray([0] * num_instances)  # all use prototype 0

instancer.GetPositionsAttr().Set(positions)
instancer.GetProtoIndicesAttr().Set(proto_indices)
```

### 逐实例定制

点实例化通过逐实例数组支持逐实例的变化：

| 数组 | 类型 | 控制内容 |
| -------------- | ----------- | ---------------------------------------------------- |
| `positions` | `point3f[]` | 每个实例的世界位置 |
| `orientations` | `quath[]` | 每个实例的旋转（四元数） |
| `scales` | `float3[]` | 每个实例的缩放 |
| `protoIndices` | `int[]` | 每个实例使用哪个原型（从而实现多样性） |
| `invisibleIds` | `int64[]` | 需要隐藏的实例 ID |

### 动态向 PointInstancer 添加新原型

**它是什么：** 一个 `UsdGeomPointInstancer` 可以同时引用多个原型 prim。每个实例通过 `protoIndices` 数组选择自己使用的原型。添加一个新原型，意味着要把一个新的 prim 注册到 instancer 的 `prototypes` 关系上，并更新 `protoIndices` 去引用它。

**为什么需要它：** 在生产环境中，场景是逐步搭建的。一个森林场景可能最初只有一种树，之后需要橡树、松树和桦树的变体。人群仿真也可能在制作中途加入一种新的角色类型。动态添加原型——而无需重建整个 instancer——才是正确的生产模式。

```
Before adding:                    After adding Oak:
prototypes rel:                   prototypes rel:
[0] /Forest/Protos/Pine           [0] /Forest/Protos/Pine
                                  [1] /Forest/Protos/Oak   ← new

protoIndices = [0,0,0,0,0]        protoIndices = [0,1,0,1,0]
(all Pine)                         (alternating Pine and Oak)
```

**如果做错了会出什么问题：** `protoIndices` 数组必须始终有效——每个索引都必须对应一个已存在的原型。如果你添加了原型却忘了在关系中注册它，或者设置了一个越界索引，instancer 会静默地无法渲染那些实例。

**方法签名：**

```python
# UsdGeomPointInstancer.GetPrototypesRel() -> UsdRelationship
# The relationship holding all registered prototype paths
instancer.GetPrototypesRel()

# UsdRelationship.AddTarget(path) -> bool
# Register a new prototype path — appends to the list
# The index of the new prototype = len(existing_targets) before adding
instancer.GetPrototypesRel().AddTarget(Sdf.Path("/Forest/Protos/Oak"))

# UsdRelationship.GetTargets() -> list[Sdf.Path]
# Check current registered prototypes and their indices
targets = instancer.GetPrototypesRel().GetTargets()
# targets[0] = first prototype (index 0)
# targets[1] = second prototype (index 1)

# UsdGeomPointInstancer.GetProtoIndicesAttr() -> UsdAttribute
# Must update after adding prototype to use the new index
instancer.GetProtoIndicesAttr().Set(Vt.IntArray([...]))
```

**完整示例：**

```python
from pxr import Usd, UsdGeom, Vt, Gf, Sdf

stage     = Usd.Stage.Open("scene.usda")
instancer = UsdGeom.PointInstancer.Get(stage, "/World/Forest")

# --- Check existing prototypes and their indices ---
targets = instancer.GetPrototypesRel().GetTargets()
# targets = [Sdf.Path("/World/Forest/Protos/Pine")]
# Pine is at index 0

# --- Step 1: Define the new prototype prim ---
oak_proto = UsdGeom.Mesh.Define(
    stage, "/World/Forest/Protos/Oak"
)
# ... set up oak geometry ...

# --- Step 2: Register with the instancer ---
# AddTarget appends — Oak will be at index 1
instancer.GetPrototypesRel().AddTarget(
    Sdf.Path("/World/Forest/Protos/Oak")
)

# Verify indices
targets = instancer.GetPrototypesRel().GetTargets()
# targets[0] = Pine   ← index 0
# targets[1] = Oak    ← index 1

# --- Step 3: Update protoIndices to use the new prototype ---
# Existing instances still use 0 (Pine)
# New instances use 1 (Oak)
current_indices = list(instancer.GetProtoIndicesAttr().Get())
# Add 200 new Oak instances
new_indices = current_indices + [1] * 200
instancer.GetProtoIndicesAttr().Set(Vt.IntArray(new_indices))

# --- Step 4: Add positions for the new instances ---
current_positions = list(instancer.GetPositionsAttr().Get())
import random
new_positions = [
    Gf.Vec3f(random.uniform(-100, 100), 0, random.uniform(-100, 100))
    for _ in range(200)
]
instancer.GetPositionsAttr().Set(
    Vt.Vec3fArray(current_positions + new_positions)
)
```

> **索引顺序就是关系中的原型顺序。** 第一个加入的 target = 索引 0，第二个 = 索引 1，依此类推。如果你需要移除某个原型，那么所有引用它的既有 `protoIndices` 以及列表中位于其后的内容都必须更新——这就是为什么移除原型很少发生，而添加原型才是标准操作。

---

## 3. 逐实例覆盖

点实例化支持逐实例的属性变化。每个实例都可以有各自不同的颜色、材质或自定义属性，这些可以通过 PointInstancer 上的 primvar 驱动，或者把 shader 输入连接到逐实例的 primvar 上实现。

### 正确的覆盖方式

| 方式 | 具体做法 | 适用场景 |
| ------------------------------- | ----------------------------------------------------------- | -------------------------------- |
| 逐实例变换 | `positions`、`orientations`、`scales` 数组 | 每个实例的位置不同 |
| 逐实例材质变化 | 把 `UsdShade` 输入连接到 primvar | 每个实例的颜色不同 |
| 带 payload 的 `UsdReferences` | 在不同路径上引用资产并做选择性覆盖 | 针对特定属性的覆盖 |

### 在被实例化的 prim 上覆盖变体集

要在不触碰源资产的前提下覆盖**某个特定实例**上的属性，可以在实例的 prim 路径上应用一个变体选择覆盖：

```usda
# The asset defines two color variants in chair_asset.usda
# In the scene, ChairA gets the default "brown" variant
# ChairB gets a "blue" variant override — locally, without editing the source

def Xform "ChairA" (
    prepend references = @./chair_asset.usda@
) { }   # uses default variant from asset

def Xform "ChairB" (
    prepend references = @./chair_asset.usda@
    variants = { string color = "blue" }   # ← local override on this instance
) { }   # only this instance uses blue — asset unchanged
```

```python
# Python equivalent — override variant on one instance
chair_b = stage.GetPrimAtPath("/World/ChairB")
chair_b.GetVariantSets().GetVariantSet("color").SetVariantSelection("blue")
# ChairA is unaffected — still uses the default from the asset
```

当资产已经为你想改动的属性定义了变体集时，这就是实现逐实例定制的正确模式。

### 错误的方式

| 错误做法 | 为什么是错的 |
| ----------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| 直接修改原型 prim | 会改变**所有**实例——这不是逐实例覆盖 |
| 为每个实例复制整个原型 | 破坏了实例化的效率——完全违背了初衷 |
| 在**原型**上使用 `variantSets` 来实现逐实例变化 | 原型上的变体会全局影响**所有**实例 |
| 用 payload 覆盖来修改实例属性 | payload 是用于延迟加载的——不是用来做属性覆盖的 |
| 新建一个"继承"自被实例化 prim 的 prim | USD 的 prim 之间不存在面向对象意义上的派生——请使用引用与覆盖 |

> **点实例化确实支持逐实例的材质变化。** 这是考试中常见的陷阱——那个错误说法是"点实例化不支持逐实例材质变化"。事实并非如此。逐实例材质通过 primvar 驱动的 shader 输入来实现。

### 实例代理 —— 在不破坏实例化的前提下读取与覆盖

**它是什么：** 当一个 prim 设置了 `instanceable = True` 时，USD 会创建一个共享的原型，并让该 prim 成为它的实例。你无法直接在可实例化 prim 的子级上创作意见——那样做会破坏原型共享，因为 USD 需要把数据分叉出去。**实例代理**是 USD 提供给你的只读句柄，用来检视这些子级。若要进行创作式的覆盖，你应当操作实例根节点本身——而不是它的子级。

**为什么需要它：** 被实例化的资产在大场景中非常普遍——成千上万的树、人群、道具。你经常需要定制单个实例（这棵树枯死了、这个角色受伤了），同时又不破坏其他所有实例的实例化，更不想复制整份资产。理解正确的覆盖模式可以避免一个常见的生产 bug：写入实例子级并静默地破坏实例化。

```
Instanceable prim:
/World/Tree_042  (instanceable = True)
← prototype is shared with all other Tree instances

What you can do:
Read:    stage.GetPrimAtPath("/World/Tree_042/Trunk")
→ returns instance proxy — readable, not writable
Override: stage.OverridePrim("/World/Tree_042")
→ override on the INSTANCE ROOT — this is valid
→ author sparse opinions here without breaking instancing

What breaks instancing:
stage.GetPrimAtPath("/World/Tree_042").SetInstanceable(False)
→ now this tree is NOT an instance — it gets its own copy
→ memory efficiency lost for this prim
```

**三种模式 —— 读取、覆盖与破坏：**

```python
from pxr import Usd, UsdGeom, UsdShade, Sdf

stage = Usd.Stage.Open("scene.usda")

# --- Pattern 1: READ via instance proxy (always safe) ---
trunk_proxy = stage.GetPrimAtPath("/World/Tree_042/Trunk")
# trunk_proxy IS an instance proxy — you can read from it
print(trunk_proxy.IsInstanceProxy())           # True
print(trunk_proxy.GetAttribute("radius").Get()) # reads prototype value

# You CANNOT author on an instance proxy child
# trunk_proxy.GetAttribute("radius").Set(2.0)  ← WRONG — no effect or error

# --- Pattern 2: OVERRIDE on the instance root (correct) ---
# Author a sparse override on the instance root prim
# This is the correct way to customise one instance
stage.SetEditTarget(stage.GetRootLayer())
over = stage.OverridePrim("/World/Tree_042")

# Override a property at the instance root level
UsdGeom.Imageable(over).GetVisibilityAttr().Set(
    UsdGeom.Tokens.invisible
)
# Only Tree_042 becomes invisible — all other trees unchanged
# Instancing is preserved — prototype is still shared

# Override material binding on the instance root
binding = UsdShade.MaterialBindingAPI.Apply(over)
binding.Bind(dead_tree_mat)
# Only Tree_042 uses dead_tree_mat — prototype unchanged

# --- Pattern 3: BREAK instancing (use only when necessary) ---
# If you need to author on a specific child prim,
# you must turn off instanceable for that prim
tree_prim = stage.GetPrimAtPath("/World/Tree_042")
tree_prim.SetInstanceable(False)
# Now Tree_042 is NOT an instance — it gets its own copy of the prototype
# You can now author on /World/Tree_042/Trunk directly
# BUT: this tree no longer shares the prototype — memory cost increases
trunk = stage.GetPrimAtPath("/World/Tree_042/Trunk")
trunk.GetAttribute("radius").Set(2.0)   # now valid
```

**方法签名：**

```python
# UsdPrim.IsInstanceProxy() -> bool
# True if this prim is a child accessed through an instance
prim.IsInstanceProxy()

# UsdPrim.IsInstance() -> bool
# True if this prim IS an instance (the root, not a child)
prim.IsInstance()

# UsdPrim.IsPrototype() -> bool
# True if this prim IS the prototype (the shared template)
prim.IsPrototype()

# UsdPrim.SetInstanceable(bool) -> None
# True = share prototype with matching instances
# False = this prim gets its own copy — breaks sharing for this prim only
prim.SetInstanceable(False)

# Usd.Stage.OverridePrim(path) -> UsdPrim
# Creates an over spec at path for sparse authoring
# Safe to use on instance roots — does not break instancing
stage.OverridePrim("/World/Tree_042")
```

**关键规则：**

- 实例代理的子级是**只读**的——读取总是安全的，创作则不行
- 在**实例根节点**（即可实例化的 prim 本身）上做覆盖——而不是在它的子级上
- 通过 `stage.OverridePrim()` 在实例根节点上覆盖是安全的，不会破坏实例化
- `SetInstanceable(False)` 会破坏该 prim 的原型共享——只在确实需要让几何体分叉时才使用
- 在实例根节点上做可见性、材质绑定、变换覆盖都能正确工作，并且保留实例化

> **考试表述：** "在不破坏实例化状态的前提下编辑 instanceProxy 网格的属性" → 答案是用 `stage.OverridePrim()` 在实例根节点上覆盖，而不是在代理子级上。代理子级是只读的。

### 决策树 —— 编辑单个实例（`/World/Tree_042`）

```
I want to change something on Tree_042 only:
    |
    v
Does the change target /World/Tree_042 itself?
    |
   YES  ->  OverridePrim("/World/Tree_042")
       author the opinion there
       instancing preserved
    |
   NO (needs a child path like /Trunk, /Leaves)
    |
    v
Does the prototype expose this as an interface attribute at the root?
    |
   YES  ->  override the interface attribute on the root
       instancing preserved
    |
   NO
    |
    v
Does the prototype have a variant set for this property?
    |
   YES  ->  set variant selection on the root
       instancing preserved
    |
   NO
    |
    v
SetInstanceable(False) on Tree_042
author on the child path directly
instancing broken for this one tree
(all other trees still share prototype)
```

> **一句话总结：** 只有当你需要在某个子级 prim 路径上创作意见时，实例化才会被破坏。凡是在实例根节点本身上创作的内容——可见性、变换、材质绑定、变体选择、自定义属性——都会让实例化保持完好。原型为所有实例处理子级数据，而实例根节点可以在其之上承载逐实例覆盖，而不打扰原型共享。

---

## 3b. Payload 剪枝 — 优化场景聚合

当一个场景包含大量 payload 时，一次性全部加载会带来不必要的开销。**Payload 剪枝**会在聚合过程中排除未被使用或无关的 payload，从而降低加载时间与内存占用。

```python
from pxr import Usd

# Open with LoadNone — no payloads loaded
stage = Usd.Stage.Open("scene.usda", Usd.Stage.LoadNone)

# Prune: only load payloads within a specific part of the scene
# Everything outside /World/ActiveSets is never loaded
stage.LoadAndUnload(
    loadSet   = {"/World/ActiveSets"},   # load these subtrees
    unloadSet = {}                        # unload nothing extra
)

# Check which payloads are loaded
for prim in stage.Traverse():
    if prim.HasPayload():
        print(f"{prim.GetPath()}  loaded={prim.IsLoaded()}")
```

> **Payload 剪枝 vs 提高粒度：** 更多更小的 payload = 更精细的编辑控制 BUT 聚合期间的开销也更大。更少且剪枝得当的 payload = 更快的聚合。正确的优化策略是剪枝，而不是添加更细粒度的 payload。

| 策略 | 对聚合的影响 |
| ---------------------------------- | ---------------------------------------------------------- |
| Payload 剪枝 | ✅ 缩短加载时间——只加载真正需要的内容 |
| 更细粒度的 payload | ❌ 增加开销——即使用不到也要加载更多文件 |
| 把所有资产嵌入根层 | ❌ 丧失模块化，增加初始加载量 |
| 禁用实例化 | ❌ 复制数据——增加内存与聚合成本 |

---

## 3c. 接口 Schema — 可组合组件的松耦合

### 没有接口 Schema 时的问题

你有一个椅子资产，场景想改变它的颜色。如果没有接口，场景就必须知道确切的内部路径：

```python
# Scene has to reach deep inside the asset to change colour
# It must know:
#   - the exact path to the shader: /Chair/Looks/WoodMat/PBRShader
#   - the exact attribute name: inputs:diffuseColor

shader = stage.GetPrimAtPath("/Chair/Looks/WoodMat/PBRShader")
shader.GetAttribute("inputs:diffuseColor").Set(Gf.Vec3f(0.8, 0.2, 0.2))
```

这样能一直工作，直到资产团队重命名了 shader、重构了 Looks 文件夹，或者改动了材质网络。于是场景就坏了——而且没有人告诉过场景团队它要变了。

```
Scene knows about:          Asset changes internally:
/Chair/Looks/WoodMat    ->  /Chair/Materials/Wood      <- renamed
    /PBRShader            ->    /SurfaceShader            <- renamed
        inputs:diffuseColor ->      inputs:baseColor        <- renamed

Scene breaks silently - wrong path, no error until render time
```

### 解决方案 —— 在根节点上定义接口属性

与其让场景伸进资产内部，不如由资产在自己的根 prim 上暴露一个公开属性。这就是接口。场景永远只与根节点打交道——绝不接触内部路径。

```
/Chair                     <- ROOT - public interface lives here
    chair:color = (0.6,0.4,0.2)   <- public attribute - the interface

    /Chair/Looks             <- INTERNAL - scene never touches this
        /Chair/Looks/WoodMat
            /Chair/Looks/WoodMat/Shader
                inputs:diffuseColor  <- wired internally to read from chair:color
```

```python
# -- ASSET SIDE (done once by the asset team) ----------------------

stage = Usd.Stage.Open("chair_asset.usda")
chair_root = stage.GetPrimAtPath("/Chair")

# Step 1 - create the public interface attribute on the root
chair_root.CreateAttribute(
        "chair:color",
        Sdf.ValueTypeNames.Color3f
).Set(Gf.Vec3f(0.6, 0.4, 0.2))   # default brown

# Step 2 - wire the internal shader to READ from the interface
# This happens inside the asset - the scene never sees this
shader = stage.GetPrimAtPath("/Chair/Looks/WoodMat/Shader")
shader_input = UsdShade.Shader(shader).CreateInput(
        "diffuseColor", Sdf.ValueTypeNames.Color3f
)
# Connect shader input -> interface attribute on root
shader_input.ConnectToSource(
        UsdShade.ConnectionSourceInfo(
                UsdShade.Material.Get(stage, "/Chair/Looks/WoodMat"),
                "chair:color",
                UsdShade.AttributeType.Input
        )
)
stage.Save()
```

### 现在场景完全解耦了

```python
# -- SCENE SIDE (done by the scene/shot team) ----------------------

stage = Usd.Stage.Open("shot.usda")

# Reference the chair - scene knows nothing about its internals
chair = stage.OverridePrim("/World/Chair")
# (chair_asset.usda is referenced in shot.usda)

# Change the colour by talking to the PUBLIC interface only
# The scene does not know or care about the internal shader path
chair.GetAttribute("chair:color").Set(Gf.Vec3f(0.8, 0.1, 0.1))  # red chair

# The internal shader reads from chair:color automatically
# The scene team never needs to know about /Chair/Looks/WoodMat/Shader
```

现在资产团队可以任意重构整个内部 shader 网络——重命名 shader、添加图层、改变材质层级——而场景依然照常工作，因为接口（根节点上的 `chair:color`）从未改变。

### 可组合性带来的好处 —— 替换资产

由于两个资产实现了同一个接口，场景可以自由地替换它们：

```python
# ChairA and ChairB both expose "chair:color" on their root
# The scene treats them identically

for chair_path in ["/World/ChairA", "/World/ChairB", "/World/ChairC"]:
        prim = stage.GetPrimAtPath(chair_path)
        prim.GetAttribute("chair:color").Set(Gf.Vec3f(0.1, 0.1, 0.8))  # all blue
        # Works regardless of which chair asset is referenced
        # as long as they all implement the chair:color interface
```

如果没有接口，场景就必须分别了解每个椅子模型的内部结构——每一个都可能使用不同的内部 shader 路径。

### 全景图

```
WITHOUT interface:
    Shot team knows:   /Chair/Looks/WoodMat/Shader.inputs:diffuseColor
    Asset team changes: internal structure
    Result:            scene breaks - tight coupling

    Shot team knows:   /TableA/Mat/Surface.inputs:baseColor
                                         /TableB/Shading/PBR.inputs:albedo     <- different path!
    Result:            different code for every asset - unmaintainable

WITH interface:
    Shot team knows:   chair:color on root    <- same for every chair
                                         table:color on root    <- same for every table
    Asset team changes: internal structure freely
    Result:            scene never breaks - loose coupling

    Any asset that exposes chair:color is a valid chair
    Can swap ChairA for ChairB - scene code unchanged
```

### 一句话总结

> 接口 schema 就是资产根 prim 上的一个公开属性，场景通过它与资产交互，而不是伸进资产内部。内部连线负责把这个公开属性接到真正的 shader/绑定/几何体上。场景与内部实现解耦——它只了解契约，而不了解实现。这与软件工程中的公开 API 完全是同一个原则：只要公开接口保持不变，就可以自由地改变实现。

---

## 3d. 协作式聚合 — 合成弧 vs 文件锁

USD 的合成系统是实现协作式资产聚合的**正确**机制。多位美术师各自贡献到不同的文件，这些文件再以非破坏性的方式合到一起。

```
Artist A → anim.usda          ┐
Artist B → layout.usda        ├── composition arcs → shot_042.usda
Artist C → fx.usda            ┘

Each artist works in their own file.
No file locking needed.
No overwriting.
Composition resolves conflicts using LIVERPS.
```

| 机制 | 适合协作吗？ | 原因 |
| --------------------------------------- | -------------------------- | ------------------------------------------------------------------------ |
| 合成弧（references、payloads） | ✅ 是 | 每位贡献者都有自己的文件，以非破坏性的方式合成 |
| 文件锁 | ❌ 否 | 不可扩展，无法发挥 USD 合成的优势，还会阻塞其他美术师 |
| 单一扁平 USD 文件 | ❌ 否 | 所有改动都被串行化进一个文件——无法并发编辑 |
| 用变体集处理并发编辑 | ❌ 否 | 变体集 = 资产变体，而不是并发协作机制 |

---

## 4. 资产版本控制与管理

### 引用 —— 单一事实来源

使用引用而不是复制数据，意味着每个资产只有一份权威副本。更新资产文件后，所有引用它的场景都会自动看到这次更新。

```python
# Instead of duplicating chair geometry into every scene:
# scene_A.usda, scene_B.usda, scene_C.usda all reference:
chair = stage.DefinePrim("/World/ChairA")
chair.GetReferences().AddReference("./assets/chair_v003.usda")
# Update chair_v003.usda → all three scenes update automatically
```

### 用变体集做版本管理

变体集可以在同一个文件内表示同一资产的不同版本或不同配置：

```usda
def Xform "Chair" (
    prepend variantSets = "version"
    variants = { string version = "v003" }
) {
    variantSet "version" = {
        "v001" { prepend references = @./chair_v001.usda@ }
        "v002" { prepend references = @./chair_v002.usda@ }
        "v003" { prepend references = @./chair_v003.usda@ }
    }
}
```

### 用 Payload 提升性能

把大型资产以 payload 的方式引用，这样即使场景中有许多重型资产也能快速打开：

```python
# Heavy asset referenced as payload — not loaded until explicitly requested
heavy_prim = stage.DefinePrim("/World/HighResCity")
heavy_prim.GetPayloads().AddPayload("./city_highres.usda")

# Open stage without loading any payloads — instant open
stage = Usd.Stage.Open("scene.usda", Usd.Stage.LoadNone)

# Load only the assets you need
stage.Load("/World/HighResCity")
```

### 版本控制的最佳实践

| ✅ 应该做 | ❌ 不应该做 |
| --------------------------------------------------- | -------------------------------------- |
| 引用资产——保持单一事实来源 | 把所有数据嵌入每一个 stage |
| 用变体集来切换版本 | 只依赖文件命名约定 |
| 交付带版本号的文件（`v001`、`v002`） | 直接覆盖原始 USD 文件 |
| 把源合成文件纳入版本控制 | 直接编辑展平后的交付文件 |

---

## 5. 场景图组织模式

### 标准层级约定

```
/World                              ← Xform — root of the scene
├── /World/Geometry  (Scope)        ← all renderable geometry
│   ├── /World/Geometry/Chair (Mesh)
│   └── /World/Geometry/Table (Mesh)
├── /World/Lights    (Scope)        ← all lights
│   └── /World/Lights/KeyLight
├── /World/Looks     (Scope)        ← all materials
│   └── /World/Looks/WoodMat
└── /World/Cameras   (Scope)
    └── /World/Cameras/MainCam
```

### `UsdGeomScope` 与 `UsdGeomXform` 的区别

| Schema | 有变换吗？ | 适用场景 |
| -------------- | ---------- | --------------------------------------------------- |
| `UsdGeomXform` | ✅ 有 | 需要整体移动的分组 prim |
| `UsdGeomScope` | ❌ 没有 | 仅用于命名空间组织——没有变换带来的开销 |

对于 `/World/Looks/`、`/World/Lights/` 这类只需要分组、不需要变换的容器，使用 `Scope`；当这个组本身需要定位或动画时，使用 `Xform`。

---

## 6. 关键要点

| 概念 | 需要记住的内容 |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **原生实例化** | `SetInstanceable(True)`——共享原型数据，减少内存占用 |
| **PointInstancer** | 性能最高——适合森林、人群、粒子。逐实例变换且不复制几何体。 |
| **`positions`、`protoIndices`** | PointInstancer 上最核心的逐实例数组 |
| **逐实例材质** | 通过 primvar 驱动的 shader 输入即可支持——并不是被禁用的 |
| **修改原型 = 全局改动** | 会影响**所有**实例——不是逐实例覆盖 |
| **在实例上覆盖变体集** | 在实例的 prim 路径上覆盖变体选择——是正确的逐实例覆盖机制 |
| **Payload 覆盖 ≠ 属性覆盖** | Payload = 延迟加载。**不是**用来覆盖实例属性的。 |
| **Payload 剪枝** | 在聚合期间排除未使用的 payload——降低加载时间与内存占用 |
| **更细粒度的 payload** | ❌ 增加开销——正确的优化手段是剪枝，而不是更多 payload |
| **接口 schema** | 为组件定义公开 API——实现松耦合与可替换资产 |
| **协作 = 合成弧** | 每位美术师贡献自己的文件。文件锁 = 错误。单一扁平文件 = 错误。 |
| **变体集 ≠ 协作** | 变体集 = 资产变体。**不是**用来管理多位美术师的并发编辑的。 |
| **引用 = 单一事实来源** | 更新资产文件 → 所有引用它的场景随之更新 |
| **用 Payload 承载重型资产** | `Stage.LoadNone` + 显式 `Load()`——对大型场景最理想 |
| **UsdGeomScope** | 命名空间分组，无变换。适用于 `/Looks/`、`/Lights/` |
| **UsdGeomXform** | 变换容器。适用于需要整体移动的组。 |
| **不要覆盖原始文件** | 交付带版本号的副本（`v001`、`v002`），绝不覆盖源文件 |

---

_上一篇：[第 7 天 — 流水线开发与数据交换](day-07-pipeline-and-data-exchange.md)_  
_下一篇：[第 9 天 — 调试与故障排查](day-09-debugging-and-troubleshooting.md)_

---


### Day 9 — 调试与故障排查


> 来源：`sparsha-2011/physical-ai-learning-journey` · `02-openUSD-cert/notes/day-09-debugging-and-troubleshooting.md` · [原文链接](https://github.com/sparsha-2011/physical-ai-learning-journey/blob/main/02-openUSD-cert/notes/day-09-debugging-and-troubleshooting.md) · 语言：英文原文 · 中译版



# Day 9 — 调试与故障排查

> **OpenUSD NCP 认证学习笔记**  
> _PrimStack、PropertyStack、TfDebug、MuteLayer、Flattening、Composition Errors、Schema Versions_

---

## 目录

1. [调试思维 — 根因](#1-调试思维--根因)
2. [完整的调试工具箱](#2-完整的调试工具箱)
3. [PrimStack — 检查 Prim 的贡献](#3-primstack--检查-prim-的贡献)
4. [PropertyStack — 找出获胜的图层](#4-propertystack--找出获胜的图层)
5. [HasAuthoredValue — 已创作值与 Schema 回退值](#5-hasauthoredvalue--已创作值与-schema-回退值)
6. [编辑目标 — 最常见的静默 Bug](#6-编辑目标--最常见的静默-bug)
7. [MuteLayer — 系统化隔离](#7-mutelayer--系统化隔离)
8. [GetCompositionErrors — 断开的引用](#8-getcompositionerrors--断开的引用)
9. [把 Flattening 当作调试工具](#9-把-flattening-当作调试工具)
10. [命名空间与路径冲突调试](#10-命名空间与路径冲突调试)
11. [TfDebug — 详尽的内部日志](#11-tfdebug--详尽的内部日志)
12. [11b. SdfLayer 弧检查 — GetCompositionArcInfo](#11b-sdflayer-弧检查--getcompositionarcinfo)
13. [11c. usdrecord — 它是什么，以及为什么它不是调试工具](#11c-usdrecord--它是什么以及为什么它不是调试工具)
14. [组合弧检查](#12-组合弧检查)
15. [Schema 版本校验](#13-schema-版本校验)
16. [图层偏移与动画时间](#14-图层偏移与动画时间)
17. [usdview 调试面板](#15-usdview-调试面板)
18. [常见 Bug 速查](#16-常见-bug-速查)
19. [考试陷阱排除指南](#17-考试陷阱排除指南)

---

## 1. 调试思维 — 根因

几乎每一个 USD 调试场景最终都可归结为六种根因之一：

| 根因 | 症状 | 主要工具 |
| --- | --- | --- |
| **错误的值胜出** | 属性显示的值不正确 | `GetPropertyStack()` |
| **结构错误 / 缺少 prim** | 源码里明明存在，prim 却缺失 | `GetPrimStack()`、composition 选项卡 |
| **错误的编辑目标** | 值已写入，文件却看起来没变 | 检查 `GetEditTarget()` |
| **组合弧冲突** | 出现意外的覆盖或数据缺失 | `GetCompositionErrors()`、PrintComposition |
| **Schema 版本不匹配** | 跨图层出现意外的属性行为 | 检查 `customLayerData`、`usdchecker` |
| **性能 / 加载问题** | 打开 stage 缓慢，视口卡顿 | `TfDebug`、检查 payload 加载 |

> **创作质量不佳（无效引用或命名空间问题）最可靠的症状：** prim 明明存在于源图层中，却从 stage 中消失。这直接说明组合弧已损坏 — 要么是无效引用，要么是缺少 `defaultPrim`，要么是命名空间冲突。

---

## 2. 完整的调试工具箱

| 工具 / 方法 | 作用 | 使用场景 |
| --- | --- | --- |
| `prim.GetPrimStack()` | 该 prim 的全部 SdfPrimSpec，从最强到最弱 | prim 类型错误、prim 缺失、specifier 异常 |
| `attr.GetPropertyStack(timeCode)` | 该属性的全部属性 spec，从最强到最弱 | 属性值错误 |
| `Usd.Debug.PrintComposition(prim)` | 以文本形式给出完整的组合弧拆解 | 最细致的弧调试（仅源码构建可用） |
| `prim.GetPrimIndex().DumpToString()` | 以文本形式给出完整的组合图 | 同上 — 所有 USD 构建都可用 |
| `SdfLayer.GetCompositionArcInfo(path)` | 指定路径上某条弧的详细元数据 | 弧类型、弧强度、目标文件/prim — 用于定向弧检查 |
| `UsdUtils.FlattenLayerStack(stage)` | 仅合并 sublayer — 保留引用/variant | 调试 sublayer 冲突 |
| `stage.Flatten()` | 解析所有弧 — 完整组合后的场景 | 查看最终场景的真实样貌 |
| `usdcat --flatten` | `stage.Flatten()` 的 CLI 等价物 | 快速 CLI 检查 |
| `usdcat --print-composition` | CLI 组合弧图 | PrintComposition 的 CLI 替代 |
| `stage.GetLayerStack()` | 所有图层，从最强到最弱 | 理解加载了哪些图层 |
| `stage.GetRootLayer()` | 组合前的根图层 | 查看基础场景描述 |
| `stage.GetSessionLayer()` | 临时的内存内覆盖 | 检查交互式修改 |
| `stage.MuteLayer(id)` | 在不移除图层的前提下让它静音 | 隔离出是哪个图层引发了问题 |
| `stage.GetCompositionErrors()` | stage 上所有组合错误 | 断开的引用、无效路径 |
| `usdchecker scene.usda` | 按最佳实践校验文件 | 交付前 QA |
| `Tf.Debug.SetDebugSymbolsByName()` | 打开详尽的内部日志 | stage 打开问题、路径解析 |

---

## 3. PrimStack — 检查 Prim 的贡献

`prim.GetPrimStack()` 返回一组 `SdfPrimSpec` 对象 — 每个对该 prim 的存在或类型有任何贡献的图层对应一个。结果按**从最强到最弱**排序。

### 函数签名

```
prim.GetPrimStack() → list[SdfPrimSpec]
```

- **调用对象：** 一个 prim（`Usd.Prim`）
- **参数：** **无** — 完全不接受任何参数
- **为什么没有 TimeCode：** prim 要么存在于某个图层，要么不存在。不存在"这个 prim 在什么时刻存在"这种概念 — prim 的存在与时间无关。

### `SdfPrimSpec` 字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `spec.layer` | `SdfLayer` | 包含该 spec 的图层对象 |
| `spec.layer.identifier` | `str` | 该图层的文件路径 |
| `spec.specifier` | `Sdf.Specifier` | `Sdf.SpecifierDef`、`Sdf.SpecifierOver`、`Sdf.SpecifierClass` |
| `spec.typeName` | `str` | 类型，例如 `"Xform"`、`"Mesh"`，`over` 则为 `""` |
| `spec.path` | `Sdf.Path` | prim 路径 |
| `spec.attributes.keys()` | `list[str]` | 该图层在此 prim 上创作的所有属性名 |

### Python API

```python
from pxr import Usd
import os

stage = Usd.Stage.Open("scene.usda")
prim  = stage.GetPrimAtPath("/World/Chair")

# GetPrimStack — no parameters
for i, spec in enumerate(prim.GetPrimStack()):
    layer_name = os.path.basename(spec.layer.identifier)
    print(f"[{i}] {layer_name}")
    print(f"     specifier: {spec.specifier}")   # def / over / class
    print(f"     typeName:  '{spec.typeName}'")  # "Xform", "Mesh", ""
    # Index 0 = strongest spec
```

### 该看什么

| 观察到的现象 | 含义 |
| --- | --- |
| 栈中出现两个互不相关的资产图层 | 命名空间冲突 — 两个资产定义了同一路径 |
| 索引 0 处 `specifier=over`、`typeName=''` | 稀疏覆盖 — 该图层并不拥有这个 prim |
| 索引 0 处 `specifier=def`、`typeName='Mesh'` | 该图层拥有此 prim 及其类型 |
| 只有 `over` spec，没有 `def` spec | 该 prim 并没有真正被定义 — `IsDefined()` 将返回 False |

---

## 4. PropertyStack — 找出获胜的图层

`attr.GetPropertyStack(timeCode)` 返回一组 `SdfPropertySpec` 对象 — 每个在给定时间对该具体属性有意见的图层对应一个。结果按**从最强到最弱**排序。

### 函数签名

```
attr.GetPropertyStack(timeCode: Usd.TimeCode) -> list[SdfPropertySpec]
```

- **调用对象：** 一个具体属性（`Usd.Attribute`）— 必须先调用 `prim.GetAttribute("name")`
- **参数：** `timeCode` — **必填**。没有默认值。省略它会抛出 `TypeError`。
- **返回：** 在 `timeCode` 时对该属性有意见的所有图层，按从强到弱排序

### TimeCode 参数 — 关键区别

| 写法 | 含义 |
| --- | --- |
| `Usd.TimeCode.Default()` | **纯粹的已创作默认值** — 没有时间关联。用于非动画属性。 |
| `Usd.TimeCode(24)` 或 `24` | **第 24 帧**的值。用于动画属性。 |
| `Usd.TimeCode(0)` 或 `0` | **第 0 帧**的值 — 一个真实的时间点。**与 `Default()` 不等价** |

`TimeCode.Default()` 没有数字简写 — 必须始终完整写出。`0` 表示第 0 帧，与默认值不同。

### `SdfPropertySpec` 字段

| 字段 | 说明 |
| --- | --- |
| `spec.layer` | `SdfLayer` 对象 |
| `spec.layer.identifier` | 该图层的文件路径 |
| `spec.default` | 纯粹的已创作值（若仅有时间采样则为 None） |
| `spec.GetInfo("timeSamples")` | 时间采样属性的 `{frame: value}` 字典 |
| `spec.typeName` | 值类型（例如 `"Float"`、`"Double3"`） |

### Python API

```python
from pxr import Usd
import os

prim  = stage.GetPrimAtPath("/World/Chair")
attr  = prim.GetAttribute("chair:brightness")

# Non-animated attribute — use TimeCode.Default()
stack = attr.GetPropertyStack(Usd.TimeCode.Default())

print(f"Number of specs: {len(stack)}")
for i, spec in enumerate(stack):
    layer_name = os.path.basename(spec.layer.identifier)
    note = "<── WINNER" if i == 0 else ""

    # spec.default = plain value. None if time-sampled.
    value = spec.default
    if value is None:
        ts = spec.GetInfo("timeSamples")
        value = ts  # {frame: value} dict

    print(f"[{i}] {layer_name:<35} value={value} {note}")

# Animated attribute — use a specific frame
stack_animated = attr.GetPropertyStack(Usd.TimeCode(24))
# Only layers that have an opinion at frame 24 appear in this stack
```

---

## 5. HasAuthoredValue — 已创作值与 Schema 回退值

`attr.HasAuthoredValue()` 在任何图层显式对该属性调用过 `Set()` 时返回 `True`；如果你从 `Get()` 看到的值仅仅是 schema 回退的默认值，则返回 `False`。

```python
attr = sphere.GetRadiusAttr()

# Both return 1.0 from Get()
# but only one was explicitly Set():
print(attr.Get())              # 1.0 (either way)
print(attr.HasAuthoredValue()) # True = explicitly Set()  False = schema fallback

# Critical use case: "is this 0.0 because someone set it to 0,
# or is 0.0 just the schema default?"
# Get() cannot distinguish these — HasAuthoredValue() can.
```

---

## 6. 编辑目标 — 最常见的静默 Bug

当你在错误的编辑目标上创作值时：

- 不会抛出任何错误
- 值会被成功写入 — 只是写进了错误的图层
- 你正在查看的组合结果中，那个错误的图层可能根本不可见

```python
stage = Usd.Stage.Open("shot.usda")
# Default edit target = root layer (shot.usda)

# THE BUG: forgot to switch edit target before authoring
prim.GetAttribute("xformOp:translate").Set((5, 0, 0))
# → went to shot.usda (root), not anim.usda

# DETECT: always check before authoring
current = stage.GetEditTarget().GetLayer()
print(f"Writing to: {current.identifier}")

# FIX: save previous target, set correct one, restore
previous = stage.GetEditTarget()
stage.SetEditTarget(anim_layer)
prim.GetAttribute("xformOp:translate").Set((5, 0, 0))
stage.SetEditTarget(previous)  # restore
```

### Session Layer 陷阱

`stage.GetSessionLayer().Clear()` 清除的是 USD **内置的** session layer。这与你恰好命名为 `"session.usda"` 的 sublayer 完全不同。内置的 session layer 正是 usdview 交互式编辑写入的位置 — 而且 `stage.Save()` **永远不会把它保存到磁盘**。

---

## 7. MuteLayer — 系统化隔离

当某个属性的值不对、而你不知道是哪个图层造成的时，逐个静音候选图层。当错误值消失时，那个图层就是元凶。

```python
candidates = [layer_fx, layer_director, layer_layout]

for layer in candidates:
    stage.MuteLayer(layer.identifier)
    val = attr.Get()

    if val_is_correct(val):
        print(f"CULPRIT: {layer.identifier}")
        # This layer was causing the wrong value

    stage.UnmuteLayer(layer.identifier)  # always restore before trying next

# API reference
stage.GetMutedLayers()           # list of currently muted layer identifiers
stage.IsLayerMuted(identifier)   # True/False
```

### 静音规则

| 可以安全静音 | 绝不要静音 |
| --- | --- |
| 任何 sublayer | 被引用资产的根图层 — 会导致组合错误 |
| session layer | — |
| 任何 payload 图层 | — |

> 静音**引用的根图层**会导致组合错误 — USD 会把它当成被引用的文件根本不存在。

---

## 8. GetCompositionErrors — 断开的引用

```python
stage = Usd.Stage.Open("scene.usda")

# Get all composition errors
errors = stage.GetCompositionErrors()
print(f"Total errors: {len(errors)}")

for err in errors:
    print(str(err))

# Common error types:
# PcpErrorType_InvalidAssetPath   → file not found
# PcpErrorType_InvalidPrimPath    → file found but prim path doesn't exist
#                                   (usually: defaultPrim not set on asset)
# PcpErrorType_ArcCycle           → circular reference A→B→A
```

| 错误类型 | 原因 | 修复方法 |
| --- | --- | --- |
| `InvalidAssetPath` | 被引用的文件不存在 | 确保文件存在于该相对路径下 |
| `InvalidPrimPath` | 文件找到了，但 prim 路径不存在 | 在被引用的资产上设置 `defaultPrim` |
| `ArcCycle` | A 引用 B，而 B 又引用 A | 打破循环依赖 |

---

## 9. 把 Flattening 当作调试工具

Flattening 会创建一个用于检查的临时快照。原始 stage **永远不会被修改**。

```python
from pxr import Usd, UsdUtils

stage = Usd.Stage.Open("scene.usda")

# FlattenLayerStack — sublayers only, references and variants preserved
flat_layer = UsdUtils.FlattenLayerStack(stage)
flat_stage_a = Usd.Stage.Open(flat_layer)
# Inspect sublayer conflicts here
# Discard when done — original stage untouched

# stage.Flatten() — resolves EVERYTHING
flat_layer_full = stage.Flatten()
flat_stage_b = Usd.Stage.Open(flat_layer_full)
# Inspect fully composed scene here
# Discard when done — original stage untouched

# For delivery (not just debugging): save to disk
flat_layer_full.Export("delivery.usda")
```

### FlattenLayerStack 与 stage.Flatten() 对比

| 特性 | `UsdUtils.FlattenLayerStack()` | `stage.Flatten()` |
| --- | --- | --- |
| 合并 sublayer | ✅ 是 | ✅ 是 |
| 解析引用 | ❌ 否 — 原样保留 | ✅ 是 |
| 保留 variant | ✅ 是 | ❌ 否 — 折叠为选中项 |
| 保留时间采样 | ✅ 是 | ✅ 是 |
| 适用场景 | 调试 sublayer 冲突 | 查看完整组合后的场景 |

---

## 10. 命名空间与路径冲突调试

当两个互不相关的资产在同一图层栈中都定义了同一路径上的 prim 时，就发生了命名空间冲突。更强的图层会静默胜出 — 不会抛出任何错误。

```python
# SYMPTOM: wrong attributes on a prim, or data from one asset
# appearing on what should be a different prim

# DETECT using GetPrimStack
for spec in prim.GetPrimStack():
    print(spec.layer.identifier)
# RED FLAG: two unrelated asset layers both appearing for one prim

# FIX: reference each asset at a DIFFERENT namespace path
# Instead of: /World/Chair (both assets land here)
# Use:        /World/OfficeArea/Chair   ← from office_chair.usda
#             /World/DiningArea/Chair   ← from dining_chair.usda
```

### 路径大小写敏感性

USD 路径是**大小写敏感**的：

```python
stage.GetPrimAtPath("/World/Chair").IsValid()   # True
stage.GetPrimAtPath("/World/chair").IsValid()   # False — different path!
```

针对 `/World/chair` 的覆盖永远不会作用到 `/World/Chair`。这是最隐蔽、也最常见的路径不匹配类 Bug 之一。

---

## 11. TfDebug — 详尽的内部日志

`Tf.Debug` 可以打开 USD 内部子系统的详尽日志。输出会写到 stderr。

```python
from pxr import Tf

# Enable a debug symbol before opening the stage
Tf.Debug.SetDebugSymbolsByName("USD_STAGE_OPEN", True)
stage = Usd.Stage.Open("scene.usda")   # verbose output printed to stderr
Tf.Debug.SetDebugSymbolsByName("USD_STAGE_OPEN", False)

# List all available symbols
all_symbols = Tf.Debug.GetDebugSymbolNames()

# Check if a symbol is enabled
Tf.Debug.IsDebugSymbolNameEnabled("USD_COMPOSITION")  # True/False
```

### 关键调试符号

| 符号 | 使用场景 |
| --- | --- |
| `USD_STAGE_OPEN` | stage 能打开，但 prim 不对或缺失 |
| `USD_COMPOSITION` | 引用或 variant 没有按预期解析 |
| `AR_RESOLVER_INIT` | 资产路径无法解析为文件 |
| `USD_PAYLOADS` | payload 几何体没有出现 |
| `USD_CHANGES` | 变更通知过多 — 性能问题 |
| `USD_INSTANCING` | 实例化没有正确共享原型 |

### CLI 替代方案

```bash
# Windows
set TF_DEBUG=USD_STAGE_OPEN AR_RESOLVER_INIT

# Linux / macOS
export TF_DEBUG=USD_STAGE_OPEN AR_RESOLVER_INIT

# Wildcard — enables ALL USD_ symbols at once
set TF_DEBUG=USD*
```

---

## 11b. SdfLayer 弧检查 — GetCompositionArcInfo

`SdfLayer.GetCompositionArcInfo(path)` 会检索某个图层内指定 prim 路径上某条组合弧的详细元数据。与把整个图以文本形式倾倒出来的 `DumpToString()` 不同，该方法给出结构化的弧元数据，便于做定向检查。

```python
from pxr import Sdf

layer = Sdf.Layer.FindOrOpen("scene.usda")

# Retrieve arc info at a specific path
# Returns a list of arc info objects for arcs authored at that path
arc_infos = layer.GetCompositionArcInfo(Sdf.Path("/World/Chair"))

for arc in arc_infos:
    print(arc)
    # Each arc info contains:
    # - arc type (reference, payload, inherit, specialize)
    # - target file path or prim path
    # - layer offset if present
```

> **何时使用：** 当你需要精确查看**某一个图层**在某个特定路径上创作了**哪些**弧时 — 而不是完整的组合结果，只是那一个图层的贡献。适合用于检查资产是否具备预期弧结构的流水线校验脚本。

| 工具 | 它能看到什么 |
| --- | --- |
| `GetCompositionArcInfo(path)` | 单个图层、单个路径上创作的弧 — 结构化元数据 |
| `prim.GetPrimIndex().DumpToString()` | 跨所有图层的完整组合图 — 文本格式 |
| usdview 的 Composition 选项卡 | 完整组合图 — 可视化格式 |

---

## 11c. usdrecord — 它是什么，以及为什么它不是调试工具

`usdrecord` 是一个无头渲染工具 — 它把 USD stage 渲染为图像文件，而不会打开交互式查看器。它**不是**组合调试工具。

```bash
# What usdrecord actually does — renders frames to images
usdrecord scene.usda output.png              # render frame 0
usdrecord --frame 24 scene.usda frame24.png  # render specific frame
usdrecord --frames 1:48 scene.usda out.####.png  # render frame range
```

它使用 Hydra 流水线（与 usdview 相同），但没有 GUI。适合自动化渲染流水线和 CI/CD 校验 — 不适合检查组合。

### 为什么它会在考试中作为干扰项出现

关于组合调试的考试题经常把 `usdrecord` 列为错误答案。需要识别的模式：

```
"usdrecord captures composition changes during runtime"  → WRONG
"usdrecord records arc evaluation for debugging"         → WRONG
"usdrecord shows composition arc strength"               → WRONG

usdrecord = headless renderer = outputs IMAGES
It has no composition inspection capability whatsoever.
```

在看到涉及组合调试的题目中出现 `usdrecord` 时，直接排除它。

---

## 12. 组合弧检查

### `prim.GetPrimIndex().DumpToString()`

在**所有** USD 构建中都能用，包括 `pip install usd-core`：

```python
index = prim.GetPrimIndex()
dump  = index.DumpToString()
print(dump)
# Shows full composition arc graph:
# "root node" = local opinions (strongest)
# "reference" = reference arc and its contributing layers
# "inherit"   = inherit arc
# Error annotations for broken arcs
```

### `Usd.Debug.PrintComposition(prim)`

仅在**完整源码构建**中可用 — 在 `pip install usd-core` 中会抛出 `AttributeError`：

```python
# Check availability before using
if hasattr(Usd, 'Debug') and hasattr(Usd.Debug, 'PrintComposition'):
    Usd.Debug.PrintComposition(prim)
else:
    # Use DumpToString instead — always available
    print(prim.GetPrimIndex().DumpToString())
```

### 可用性汇总

| 方法 | pip usd-core | 源码构建 | CLI |
| --- | --- | --- | --- |
| `prim.GetPrimIndex().DumpToString()` | ✅ | ✅ | — |
| `Usd.Debug.PrintComposition(prim)` | ❌ `AttributeError` | ✅ | — |
| `usdcat --print-composition` | ✅ | ✅ | ✅ |

---

## 13. Schema 版本校验

当以不同 Schema 版本创作的图层组合在一起时，属性名在版本之间可能不同 — 这会导致细微的组合失败：同一个概念存在两份意见，但名称不同。

```
old_layer (v1.0):  "shader:roughness" = 0.3
new_layer (v2.0):  "inputs:roughness" = 0.5

Composed result: BOTH attributes exist on the prim simultaneously
The renderer uses "inputs:roughness" = 0.5
The old "shader:roughness" = 0.3 has no effect — silently wrong
```

### 预防 — 为每个图层打上版本元数据标签

```python
# When authoring any layer
stage.GetRootLayer().customLayerData = {
    "pipeline:schemaVersion": "2.0",
    "pipeline:studio":        "AcmeStudios",
    "pipeline:exportTool":    "MayaExporter_v2",
}

# When reading layers to validate compatibility
for layer in stage.GetLayerStack():
    custom  = layer.customLayerData   # returns {} if not set
    version = custom.get("pipeline:schemaVersion", "NOT SET")
    print(f"{layer.identifier}: version={version}")
    # "NOT SET" = old layer predating version tagging
    # → inspect attribute names manually for old naming conventions
```

> `customLayerData` 是存储在图层元数据头部的普通 Python 字典。用 `.get(key, default)` 安全读取 — 对没有元数据的旧图层永远不会抛出 `KeyError`。

---

## 14. 图层偏移与动画时间

图层偏移会对引用弧或 payload 弧带来的所有时间采样数据施加一次时间变换。

```
composed_time = (source_time × scale) + offset
```

```python
# Reference with offset=100, scale=2.0
# Source keyframe at time=10 appears at:
# composed = (10 × 2.0) + 100 = 120

ref = Sdf.Reference(
    assetPath   = "./walk_cycle.usda",
    primPath    = Sdf.Path("/Character"),
    layerOffset = Sdf.LayerOffset(offset=100.0, scale=2.0)
)
```

> **如果动画出现在错误的时间码上 — 先检查图层偏移。** 这是一个经常被忽略的调试步骤。"图层偏移不影响组合结果所以可以忽略"是**错误**的 — 图层偏移直接影响所有随时间变化的数据。

---

## 15. usdview 调试面板

### Composition 选项卡

`Metadata/Composition 面板 → Composition 选项卡` 会显示所选 prim 的完整组合弧图 — 这是 `prim.GetPrimIndex().DumpToString()` 的可视化等价物。用它来理解哪些弧作出了贡献、顺序如何。

### LayerStack 选项卡

`Metadata/Composition 面板 → LayerStack 选项卡` 会显示对所选 prim 有贡献的所有图层，以及每个属性的已创作值。这是 `GetPropertyStack()` 的可视化等价物 — 最强的图层排在最前。

### Layers 面板

`View → Layers`（取决于 USD 版本，也可能是 `Windows → Layers`）列出 stage 中的所有图层。取消勾选/静音某个图层，即可在 Properties 面板中实时看到属性值变化。这是 `stage.MuteLayer()` 的可视化等价物。

### Properties 面板

在 Properties 面板中点击任意属性：

- **灰显/变暗的值** = schema 回退值 — 没有人对该属性调用过 `Set()`
- **正常/明亮的值** = 显式创作的值

这是 `HasAuthoredValue()` 的可视化等价物。

---

## 16. 常见 Bug 速查

| Bug | 症状 | 修复方法 |
| --- | --- | --- |
| 编辑目标错误 | 值已写入，文件却没变化。无报错。 | 每次 Set() 前检查 `GetEditTarget()` |
| 缺少 defaultPrim | 引用失败，prim 为空 | `stage.SetDefaultPrim(root_prim)` |
| session layer 未保存 | 下次打开时值回退 | 把 SetEditTarget 指向一个落盘的文件图层 |
| 在已存在文件上调用 `CreateNew()` | 输出文件只有 `#usda 1.0` | 先删除文件，或使用 `CreateInMemory()` + Export |
| 命名空间冲突 | prim 上带着错误的属性 | 每个资产使用唯一路径 |
| 路径大小写不匹配 | 覆盖永远不生效 | 大小写完全一致 — 用 `/World/Chair` 而不是 `/World/chair` |
| Schema 版本不匹配 | 属性重复，值不正确 | 用 `customLayerData` 中的版本信息标记图层 |
| 图层偏移被忽略 | 动画出现在错误的时间码 | 检查引用弧上的 `Sdf.LayerOffset` |

---

## 17. 考试陷阱排除指南

排除任何包含以下模式的选项：

| 选项中的模式 | 为什么总是错的 |
| --- | --- |
| "直接编辑组合后 stage 的内存表示" | 组合后的 stage 是只读的 |
| "清除 USD 缓存以重置组合" | USD 组合是确定性的 — 缓存只影响性能 |
| "手动编辑根图层以移除所有引用" | 破坏性操作，且没有触及根因 |
| "删除所有 payload 并重新加载" | 破坏性操作，且不能解决组合冲突 |
| "修改 USD schema 以强制特定的意见" | Schema 定义结构，而不是组合行为 |
| "图层偏移不影响组合所以可以忽略" | 图层偏移**确实**影响随时间变化的数据 |
| "usdchecker 会自动修复组合问题" | usdchecker 只做**校验** — 绝不自动修复 |
| "usdrecord 在运行时捕获/记录组合变化" | usdrecord 是一个输出图像的**无头渲染器** — 完全不具备组合调试能力 |
| `"prim.GetCompositionArcs()"` | 该方法在 USD Python API 中**并不存在** — 会抛出 AttributeError。请改用 `prim.GetPrimIndex().DumpToString()` |
| "完全依赖 GetSessionLayer() 来做所有组合调试" | session layer 只包含临时覆盖 |
| "把 stage flatten 以降低图层组合开销" | Flattening 会**增加**内存占用并失去分层带来的好处 |
| "GetPrimAtPath() 会忽略组合弧来获取 prim" | 返回的是**完整组合后**的 prim — 所有弧都已生效 |

---

_上一篇：[Day 8 — 内容聚合](day-08-content-aggregation.md)_  
_返回开头：[Day 1 — USD 基础](day-01-usd-foundations.md)_

---



## 笔记


### 第 2 章 练习题


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `practice-questions/chapter-02-questions.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/practice-questions/chapter-02-questions.md) · 语言：英文原文 · 中译版



## 第 2 章：Schema、时间采样、Primvar 与模型层级 —— 练习题

**Q1.** 某工作室需要为已有的 UsdGeomMesh prim 添加物理碰撞行为，同时不改变该 prim 的底层类型。哪种做法是正确的？

A) 把该 prim 的类型从 Mesh 改为 Physics
B) 把单应用（single-apply）的 API schema（如 UsdPhysicsCollisionAPI）应用到已有的 Mesh prim 上
C) 删除该 prim，并重新创建为 UsdPhysicsCollisionAPI 类型化 prim
D) 添加一个名为 "collision" 的多应用（multi-apply）CollectionAPI 实例

<details>
<summary>答案</summary>

**正确答案：B**

API schema 可以在不改变 prim 的 typeName 的前提下增加能力/属性；UsdPhysicsCollisionAPI 正是为这种场景设计的单应用 applied API schema。

**其他选项错误的原因：**
- 修改 typeName 会破坏 Mesh 的 IsA schema 身份，而且这并不是在 USD 中添加能力的方式。
- UsdPhysicsCollisionAPI 不是类型化（IsA）schema —— 它不能作为 prim 的类型，只能作为 applied API。
- CollectionAPI 出于其他目的（例如选择集、绑定）把 prim 分组进具名集合 —— 它不会添加碰撞行为。

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

**Q2.** 以下哪个是 multi-apply API schema，应用时需要提供实例名称？

A) UsdGeomModelAPI
B) UsdCollectionAPI
C) UsdPhysicsMassAPI
D) UsdGeomVisibilityAPI

<details>
<summary>答案</summary>

**正确答案：B**

UsdCollectionAPI 的设计目标就是在同一个 prim 上多次应用，每次使用唯一的实例名称（例如 apiSchemas = ["CollectionAPI:renderSet"]）。

**其他选项错误的原因：**
- UsdGeomModelAPI 是非应用的便捷 API，而不是 multi-apply schema。
- UsdPhysicsMassAPI 是单应用的 —— 每个 prim 只能有一个质量定义。
- UsdGeomVisibilityAPI 是一组与可见性相关的属性，属于单应用。

</details>

---

**Q3.** 在最强的贡献 layer 中，某个属性同时创作了默认值和时间采样。针对某个具体 time code 查询时，USD 的值解析会返回什么？

A) 默认值，因为默认值总是优先
B) 默认值与最近时间采样的平均值
C) 报错，因为两者不能同时创作
D) 时间采样的值；同一 layer 中的默认值被忽略

<details>
<summary>答案</summary>

**正确答案：D**

只要胜出的 layer 中该属性带有时间采样，USD 值解析就只使用时间采样；默认值仅在解析出的 opinion 中完全没有时间采样时才作为兜底生效。

**其他选项错误的原因：**
- 存在时间采样时，默认值是兜底而非优先。
- USD 从不对默认值和时间采样值取平均。
- 两者同时创作是合法且常见的（默认值可供不支持时间的消费方使用，或用于播放范围之前）。

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

**Q4.** Layer A（更强）只为某个属性在第 1 到第 10 帧创作了时间采样。Layer B（更弱）为同一属性在第 1 到第 100 帧创作了时间采样。当客户端在第 50 帧查询该属性时返回什么值？

A) Layer A 在第 10 帧最后一个采样的保持（钳制）值
B) Layer B 在第 50 帧附近采样的插值结果
C) Layer A 与 Layer B 最近采样的混合结果
D) 默认值，因为两个 layer 在第 50 帧都没有精确采样

<details>
<summary>答案</summary>

**正确答案：A**

一旦值解析为某个属性选定了最强 layer 的 opinion，就只会使用该 layer 的时间采样 —— 如果查询时间落在创作范围之外，则在边界采样处做钳制/保持。Layer B 的采样永远不会被查询。

**其他选项错误的原因：**
- 一旦更强的 layer 为该属性提供了任何时间采样，更弱 layer 的时间采样就再也不会被合并进来。
- USD 不会跨 layer 混合采样。
- 这里默认值无关紧要，因为最强 layer 已经有时间采样了。

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

**Q5.** 某个 mesh 需要 UV 坐标在 UV 接缝处可以不连续，即在同一个共享顶点的两侧取不同的值。必须使用哪种 primvar 插值方式？

A) constant
B) vertex
C) uniform
D) faceVarying

<details>
<summary>答案</summary>

**正确答案：D**

faceVarying 为每个面角（每个面上每个顶点）存储一个值，是唯一支持在共享拓扑顶点处取不连续值的插值模式。

**其他选项错误的原因：**
- constant 对整个 prim 只有一个值 —— 它根本无法变化。
- vertex 为每个点存储一个值，并由曲面基函数平滑插值 —— 它无法在顶点处不连续。
- uniform 为每个面存储一个值而非每个面角，因此无法表达逐面角的 UV 差异。

</details>

---

**Q6.** 绑定控制几何体不应出现在最终渲染中，甚至不应出现在标准播放中，但仍然需要在查看器中可检视。这类几何体应赋予哪个 purpose 值？

A) guide
B) render
C) proxy
D) default

<details>
<summary>答案</summary>

**正确答案：A**

guide purpose 将几何体标记为仅供辅助使用的内容（绑定控制器、标注），默认会被排除在 render 和标准遍历之外。

**其他选项错误的原因：**
- render purpose 面向专门用于渲染的最终高品质几何体 —— 意图正好相反。
- proxy purpose 是用于代表可渲染/可交互几何体的轻量替身，而不是永久性的不可渲染辅助几何体。
- default purpose 意味着该 prim 正常参与交互和渲染两种上下文 —— 并非对两者都隐藏。

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

**Q7.** 关于 USD 的 'kind' 与模型层级，下列哪项说法是正确的？

A) 模型层级必须是连续的 —— 如果某个 prim 有 kind，那么它到根之间的所有祖先也必须都有 kind
B) stage 中的每个 prim 都必须有 kind
C) kind 为 'component' 的 prim 可以包含本身也是模型（group/assembly）的子 prim
D) 'subcomponent' kind 会破坏其父 component 的叶子状态

<details>
<summary>答案</summary>

**正确答案：A**

模型层级依赖从根开始不间断的 kind 世系，这样快速遍历 API（例如 IsModel）才能短路返回；一旦出现断层，该分支的层级即视为无效。

**其他选项错误的原因：**
- Kind 是可选元数据；只有参与模型层级的 prim 才需要它。
- 按照约定，component 是叶子模型 —— 它不应包含嵌套的模型。
- subcomponent 的存在目的正是标记 component 命名空间中某个特殊部分，而不会让该 component 变成非叶子模型。

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

**Q8.** 某团队正在建模标准几何体、材质和灯光，这些内容已完全被 UsdGeom、UsdShade 和 UsdLux 覆盖。他们正在考虑为 'ConfigurableProp' 这一概念编写自定义的类型化 schema。按照 OpenUSD 最佳实践，推荐的做法是什么？

A) 对任何工作室特有的概念都一律编写自定义 schema，无论现有 schema 是否已覆盖
B) 只使用 API schema，绝不编写自定义类型化 schema
C) 一律使用无代码（codeless）schema，完全不考虑编译型 C++ schema
D) 复用并组合现有的标准 schema；只有在没有任何现有 schema 覆盖该需求时才编写自定义 schema

<details>
<summary>答案</summary>

**正确答案：D**

OpenUSD 最佳实践首先强调复用与互操作性 —— 自定义 schema 应作为最后手段，以避免生态碎片化和工具不兼容。

**其他选项错误的原因：**
- 一味自定义会忽视已有的标准覆盖，并损害互操作性。
- 仅靠 API schema 无法定义 prim 的基础类型；类型化 schema 仍然有其正当用途。
- 无代码还是编译型是一种实现选择，而不是可以跳过评估现有 schema 覆盖情况的规则。

</details>

---

---


### 第 08 章 练习题


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `practice-questions/chapter-08-questions.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/practice-questions/chapter-08-questions.md) · 语言：英文原文 · 中译版



## 第 8 章：文件格式、USDZ 打包与资产解析 — 练习题

**Q1.** 某流水线工程师需要手工创作一个小的覆盖图层，以便在 Git 中做差异对比，并让美术能在纯文本编辑器中审阅。应当使用哪种格式？

A) .usdc
B) .usda
C) .usdz
D) 压缩后的 .usd

<details>
<summary>答案</summary>

**正确答案：B**

.usda 是 ASCII 文本格式，完全可读，并且在版本控制中便于做差异对比。

**其他选项错误的原因：**
- .usdc 是二进制的 Crate 格式——无法以文本方式读取，产生的差异对比也不可读。
- .usdz 是打包归档格式，不是可直接编辑的原始图层。
- 并不存在 'compressed .usd' 这一变体；.usd 与格式无关（可以是 ASCII 或 Crate），它不是一种压缩选项。

</details>

---

**Q2.** 某个生产场景包含数百万个图元，必须在运行时以尽可能快的速度加载，同时占用尽可能小的磁盘空间。哪种格式最佳？

A) .usda
B) .usdz
C) .usdc
D) 纯文本 .usd

<details>
<summary>答案</summary>

**正确答案：C**

.usdc（Crate 二进制）体积紧凑，针对快速解析/加载做了优化，非常适合重型生产场景。

**其他选项错误的原因：**
- .usda 是基于文本的，体积更大，在大规模场景中解析更慢。
- .usdz 是分发打包格式，并未被设计用作流水线场景的主要创作/运行时图层格式。
- 纯文本 .usd 文件的行为与 .usda 一样——体积大、加载慢，对数百万图元而言并不理想。

> ⚠️ 考试中经常被忽略——请仔细阅读选项。

</details>

---

**Q3.** 某开发者为 AR Quick Look 打包了一个 USDZ 文件。包内某个材质使用了绝对路径 "/Users/artist/textures/wood.png" 而不是相对路径来引用纹理。当该包在另一台设备上打开时会发生什么？

A) 纹理能正确解析，因为 USDZ 总是会自动把路径转换为相对路径
B) 查看器会通过网络从原美术的机器上下载该纹理
C) 纹理无法解析，因为 USDZ 要求所有内部引用都必须是相对路径且自包含
D) USDZ 完全忽略材质，因此这没有任何影响

<details>
<summary>答案</summary>

**正确答案：C**

USDZ 包必须完全自包含并使用相对内部路径；指向特定机器位置的绝对路径会破坏可移植性，在其他地方无法解析。

**其他选项错误的原因：**
- 打包时 USD 不会自动把绝对路径改写为相对路径——这必须在创作/导出阶段正确完成。
- USDZ 没有为缺失资源提供网络拉取机制；它是静态的、封闭的归档。
- USDZ 完全支持材质与纹理绑定；忽略材质并不是它的行为。

> ⚠️ 考试中经常被忽略——请仔细阅读选项。

</details>

---

**Q4.** 对于打包进有效 USDZ 包内的文件，哪一项 zip 归档要求是强制性的？

A) 以最高级别进行 Deflate 压缩，以获得最小的文件体积
B) 文件以未压缩（Store 方法）存储，并按 64 字节对齐
C) 使用 AES-256 加密以保护专有几何体
D) 使用带密码保护的 Deflate 压缩

<details>
<summary>答案</summary>

**正确答案：B**

USDZ 要求 zip 条目以未压缩（Store）方式存储并按 64 字节边界对齐，这样归档内容就能直接做内存映射，无需解压。

**其他选项错误的原因：**
- Deflate 压缩被明确禁止，因为它会妨碍直接进行内存映射。
- USDZ 不支持加密，而且加密会破坏与 AR 查看器的兼容性。
- 把压缩与加密结合起来，会把两种被禁止的行为叠加在一起。

> ⚠️ 考试中经常被忽略——请仔细阅读选项。

</details>

---

**Q5.** 通用的 .usd 扩展名与明确的 .usdc 扩展名之间的关键区别是什么？

A) .usd 始终是 ASCII，而 .usdc 始终是二进制
B) .usd 与格式无关，可以包含 ASCII 或 Crate 二进制内容，而 .usdc 明确表示 Crate 二进制
C) .usd 是打包格式，而 .usdc 是单个图层
D) .usdc 已被废弃，建议改用 .usd

<details>
<summary>答案</summary>

**正确答案：B**

.usd 扩展名并不指示编码方式——USD 通过检查文件的 magic bytes/头部信息来判断实际格式（ASCII 还是 Crate）。.usdc 则明确标识为 Crate 二进制。

**其他选项错误的原因：**
- .usd 可以包含两种编码中的任意一种，它并非始终是 ASCII。
- 打包格式是 .usdz，而不是 .usd 或 .usdc。
- .usdc 是正在积极使用、并未废弃的显式二进制扩展名。

> ⚠️ 考试中经常被忽略——请仔细阅读选项。

</details>

---

**Q6.** 某美术使用 DCC 工具自带的 USD 导出器导出一个绑定了骨骼的资产。其中若干自定义程序化节点属性没有对应的 USD schema 表示。哪种描述最能概括这次导出？

A) 无损转换，因为 USD 支持所有 DCC 数据类型
B) 有损转换，因为未映射的自定义数据可能被丢弃或近似处理
C) 无效转换，导出一定会失败
D) 只要保存为 .usdc 就是无损转换

<details>
<summary>答案</summary>

**正确答案：B**

当 DCC 专有属性没有直接的 USD schema 映射时，导出器通常会丢弃或近似处理它们，这使得往返转换成为有损的。

**其他选项错误的原因：**
- USD 并不保证完全覆盖每个 DCC 的专有数据类型。
- 导出通常会成功，只是保真度有所下降，而不是直接失败。
- 文件格式（.usdc 与 .usda）影响的是编码，而不是转换过程中的 schema/数据保真度。

</details>

---

**Q7.** OpenUSD 架构中，哪个组件负责把资产路径字符串转换成实际可解析的文件位置，并且可以按流水线进行定制？

A) Hydra 渲染委托
B) AssetResolver（Ar 插件 / ArResolver）
C) SdfLayer 缓存
D) UsdStage 组合引擎

<details>
<summary>答案</summary>

**正确答案：B**

AssetResolver（ArResolver 接口）负责把资产路径字符串解析为实际文件位置，并且可以替换为定制的、面向特定流水线的解析器（例如用于版本管理或搜索路径）。

**其他选项错误的原因：**
- Hydra 渲染委托负责场景渲染，而不是资产路径解析。
- SdfLayer 缓存管理已加载的图层数据，而不是路径到位置的解析逻辑。
- UsdStage 组合使用已经解析好的路径来组装图层；它依赖解析器，而不是自己执行解析。

> ⚠️ 考试中经常被忽略——请仔细阅读选项。

</details>

---

**Q8.** 某工作室需要把一个完全自包含的资产（网格体、材质、纹理）发送给外部合作方，对方使用不同操作系统上的不同应用，且绝不能出现文件链接失效的风险。哪种交付策略最佳？

A) 发送一个 .usda 图层，其中使用锚定到工作室资产服务器的绝对路径
B) 发送一个 .usdc 图层，并附带一个单独存放零散纹理的 zip 包
C) 发送一个 USDZ 包，其中包含所有被引用的资产以及相对内部路径
D) 发送一个 .usd 文件，通过网络共享路径引用纹理

<details>
<summary>答案</summary>

**正确答案：C**

USDZ 把图层和所有被引用的资产打包进一个使用相对路径、未压缩的自包含归档，从而保证在不同机器和应用之间的可移植性。

**其他选项错误的原因：**
- 锚定到内部服务器的绝对路径在工作室网络/文件系统之外无法解析。
- 把纹理与图层分开放在零散 zip 中会重新引入手动重链接的风险，并破坏自包含性。
- 网络共享路径本质上不可移植，无法在原始网络之外使用。

> ⚠️ 考试中经常被忽略——请仔细阅读选项。

</details>

---

---


### 第 9 章练习题


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `practice-questions/chapter-09-questions.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/practice-questions/chapter-09-questions.md) · 语言：英文原文 · 中译版



## 第 9 章：使用 Usd、Sdf、Gf 和 Vt 在 Python 中创作 Stage — 练习题

**Q1.** 某个流程脚本必须在 /World/Ball 处创建一个 Sphere prim，并从第 1 帧到第 24 帧对其 radius 进行时间采样，以实现脉冲式动画效果。哪种做法最能满足这一需求？

A) stage.DefinePrim('/World/Ball', 'Sphere'); prim.GetAttribute('radius').Set(radius_at(1))
B) sphere = UsdGeom.Sphere.Define(stage, '/World/Ball'); for f in range(1,25): sphere.GetRadiusAttr().Set(radius_at(f), f)
C) sphere = UsdGeom.Sphere.Define(stage, '/World/Ball'); sphere.GetRadiusAttr().Set(radius_at(12))
D) prim = stage.DefinePrim('/World/Ball'); prim.CreateRelationship('radius').SetTargets(['/World/RadiusCurve'])

<details>
<summary>答案</summary>

**正确答案：B**

Define() 会返回一个带类型的 UsdGeom.Sphere 对象，并自带开箱即用的 GetRadiusAttr() 访问器；对每一帧调用 Set(value, time)，即可在所需区间内创作出真正的时间采样数据。

**其他选项错误的原因：**
- 以字符串 typeName 调用通用的 DefinePrim()，返回的是普通的 Usd.Prim，不会自动创建任何 schema 专属属性；radius 属性甚至都不存在，除非另行创建。
- 只用一个时间值调用 Set()，只会创作出一个时间采样，而不是覆盖第 1–24 帧的动画区间。
- Relationship 存储的是指向其他对象的 Sdf.Path 目标，而不是标量动画值；radius 必须是被创作的属性，而不是 relationship。

> ⚠️ 考试中经常出错——请仔细阅读各选项。

</details>

---

**Q2.** 哪个 Sdf.Path 字符串能正确寻址在 prim /World/Cube 上创作的 'size' 属性？

A) Sdf.Path('/World/Cube.size')
B) Sdf.Path('/World/Cube/size')
C) Sdf.Path('/World.Cube.size')
D) Sdf.Path('World/Cube.size')

<details>
<summary>答案</summary>

**正确答案：A**

在 Sdf.Path 语法中，点号（'.'）用于分隔 prim 路径与属性（attribute 或 relationship）名称；斜杠只用于分隔命名空间（子 prim）片段。

**其他选项错误的原因：**
- 在 'size' 前使用斜杠会把它当作命名空间下的子 prim，而不是属性——对于寻址属性来说无效。
- 把点号放在 'World' 之后，会错误地把 'Cube' 当成 World 的属性，而不是子 prim。
- 省略前导斜杠会使其成为相对路径，无法直接寻址 Stage 中的绝对位置。

> ⚠️ 考试中经常出错——请仔细阅读各选项。

</details>

---

**Q3.** 某个流程工具需要完全在内存中构建并校验一个临时的 USD stage，全程不向磁盘写入任何文件。它应该使用哪个调用？

A) Usd.Stage.CreateNew('/dev/null')
B) Usd.Stage.Open(None)
C) Usd.Stage.CreateInMemory()
D) Sdf.Layer.CreateAnonymous()

<details>
<summary>答案</summary>

**正确答案：C**

Usd.Stage.CreateInMemory() 会创建一个匿名且功能完整的 stage，在磁盘上没有对应的文件，非常适合脚本化校验或测试。

**其他选项错误的原因：**
- 使用空设备路径调用 CreateNew() 并非受支持或可移植的 USD 用法，而且它依然隐含基于文件的语义。
- Open(None) 不是 Usd.Stage.Open 的有效调用签名，会抛出错误。
- Sdf.Layer.CreateAnonymous() 创建的是匿名 layer，而不是 Usd.Stage，因此缺少 stage 级别的 API（例如遍历和 prim 定义辅助函数）。

</details>

---

**Q4.** 你正在为一个包含数千个顶点位置的 UsdGeomMesh prim 创作 'points' 属性。应该向 Attribute.Set() 传入哪种值类型？

A) 一个由 Gf.Vec3f 值构成的 Vt.Vec3fArray
B) 单个 Gf.Vec3f 值
C) 一个由「索引到位置」键值对构成的 Python 字典
D) 一个表示全部位置的 Gf.Matrix4d

<details>
<summary>答案</summary>

**正确答案：A**

USD 中数组值的属性在内部以带类型的 Vt.Array 容器存储；对于 'points' 这类 point3f[] 属性，正确的构造方式是由 Gf.Vec3f 元素填充的 Vt.Vec3fArray。

**其他选项错误的原因：**
- 单个 Vec3f 只能表示一个点，而不是一组顶点位置数组。
- USD 属性不接受任意字典——schema 要求传入与该属性声明的 Sdf.ValueTypeName 相匹配的强类型数组。
- Matrix4d 表示的是 4x4 变换矩阵，而不是点位置数组，形状完全不对。

</details>

---

**Q5.** 带类型的 schema Define() 辅助函数（例如 UsdGeom.Xform.Define）与通用的 Stage.DefinePrim() 之间的关键功能差异是什么？

A) Define() 只适用于 Xform prim，而 DefinePrim() 支持所有类型
B) 两者行为完全相同；Define() 只是 DefinePrim() 已废弃的旧别名
C) DefinePrim() 根本无法设置 typeName，只有 Define() 才能指定
D) Define() 会设置 typeName，并返回一个内置属性访问器的带类型 schema 对象；DefinePrim() 需要传入 typeName 字符串，并返回一个通用的 Usd.Prim

<details>
<summary>答案</summary>

**正确答案：D**

每个核心 schema（Xform、Sphere、Mesh 等）都有对应的带类型 Define() 辅助函数，它们各自设置 typeName，并返回一个暴露 schema 专属 Get/Create*Attr() 方法的便捷包装对象；DefinePrim() 与 schema 无关，返回的是裸的 Usd.Prim。

**其他选项错误的原因：**
- 每个核心 UsdGeom/UsdShade schema 类都有自己的 Define() 辅助函数，不只是 Xform。
- 两者不是可以互相替换的别名；Define() 提供了 DefinePrim() 所没有的 schema 专属便捷方法。
- DefinePrim() 接受可选的 typeName 参数（例如 stage.DefinePrim(path, 'Sphere')），完全可以设置，只是没有带类型的包装对象。

> ⚠️ 考试中经常出错——请仔细阅读各选项。

</details>

---

**Q6.** 一名技术美术希望属性 'displayColor' 始终拥有一个默认值，同时在第 10 帧还有一个特定的覆盖值。哪段代码能正确地同时实现两者？

A) attr.Set(default_val, Usd.TimeCode.Default()); attr.Set(frame10_val, Usd.TimeCode.Default())
B) 只调用 attr.Set(frame10_val, 10)，不创作任何默认值
C) attr.Set(default_val); attr.Set(frame10_val, 10)
D) prim.CreateRelationship('displayColor').SetTargets(['/World/Frame10Color'])

<details>
<summary>答案</summary>

**正确答案：C**

不带时间参数调用 Set(value) 创作的是 DEFAULT 意见（等价于 Usd.TimeCode.Default()）；另行调用 Set(value, time) 则会在该帧创作一个动画时间采样——两种意见可以共存于同一个属性上。

**其他选项错误的原因：**
- 两次都以 Usd.TimeCode.Default() 调用 Set()，只会创作默认值——第二次调用只是覆盖第一次，永远不会产生第 10 帧的时间采样。
- 只创作时间采样而不创作默认值，会使该属性的默认时间查询（Usd.TimeCode.Default()）无法解析，只能回退到 schema 的 fallback，而不是期望的默认值。
- Relationship 存储的是 Sdf.Path 目标，而不是颜色值，无法表示随时间变化的标量/向量属性。

> ⚠️ 考试中经常出错——请仔细阅读各选项。

</details>

---

**Q7.** 在 UsdGeomXformable prim 上创作 xformOp:transform 属性时，需要使用哪种 Gf 值类型？

A) Gf.Matrix4f
B) Gf.Vec3d
C) Gf.Matrix4d
D) Vt.Matrix4dArray

<details>
<summary>答案</summary>

**正确答案：C**

UsdGeom 将所有 xformOp:transform 值统一为双精度的 Gf.Matrix4d；创作该属性时传入其他任何类型都会触发值类型不匹配错误。

**其他选项错误的原因：**
- Gf.Matrix4f 是有效的 GfMath 类型，但并不是 schema 为 xformOp:transform 声明的值类型，后者始终是 matrix4d。
- Vec3d 表示单个三分量向量（例如平移/缩放），而不是完整的 4x4 变换矩阵。
- Vt.Matrix4dArray 是容纳多个矩阵的数组容器；xformOp:transform 是单个标量 matrix4d 属性，而不是数组。

</details>

---

**Q8.** 一名开发者本想打开一个已有的 stage 文件进行编辑，却误在同一个文件路径上调用了 Usd.Stage.CreateNew() 而不是 Usd.Stage.Open()。会发生什么？

A) USD 会报错，因为该文件已经存在
B) USD 会静默地把该调用当作 Open() 处理，并保留已有内容
C) USD 会把新的空 stage 作为 sublayer 追加到已有内容之下
D) 已有文件的内容被覆盖/重置，丢失此前创作的所有数据

<details>
<summary>答案</summary>

**正确答案：D**

CreateNew() 始终在给定路径上创建一个全新的 root layer，覆盖任何已有文件——它既不检查也不保留原有内容，因此是流程中常见的破坏性错误。

**其他选项错误的原因：**
- 默认情况下 CreateNew() 不会因路径已存在而报错；它会静默替换文件，这正是它常成为考试陷阱的原因。
- CreateNew() 与 Open() 语义不同；CreateNew() 绝不会保留已有内容。
- CreateNew() 不会执行任何 sublayer 组合——它只是在该路径上创建一个全新且独立的 root layer。

> ⚠️ 考试中经常出错——请仔细阅读各选项。

</details>

---

---



## 学习指南


### 第 1 章 练习题


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `practice-questions/chapter-01-questions.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/practice-questions/chapter-01-questions.md) · 语言：英文原文 · 中译版



## 第 1 章：USD 对象模型：Stage、Layer、Prim 与属性 —— 练习题

**Q1.** 团队需要一种在本地视口测试中切换 prim 可见性的方法，且在把 .usda 文件共享给他人时不能影响已保存的文件。哪种做法最符合这一要求？

A) 在 session layer 中添加 override
B) 在 root layer 中添加 override（"over"）
C) 直接在被引用的 layer 上编辑该属性
D) 在 LayerStack 底部的 sublayer 中创建一个新的 prim spec

<details>
<summary>答案</summary>

**正确答案：A**

session layer 在 layer stack 中位于 root layer 之上，用来存放临时性 override，这些 override 绝不会随 root layer 文件一起保存到磁盘，因此非常适合本地的、非持久化的开关操作。

**其他选项错误的原因：**
- root layer 中的编辑会在保存 stage 时被保存，违背了'不影响已保存文件'的要求
- 直接编辑被引用的 layer 会对其他用户依赖的共享数据造成破坏
- 位于栈底部的 sublayer 在保存时同样会持久化到磁盘，并且贡献的是较弱的 opinion，而非临时/暂存的 opinion

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

**Q2.** 你需要在 prim 上存储一个随动画逐帧变化的值。这个值应该放在哪种 USD 对象中？

A) Attribute（属性）
B) Relationship（关系）
C) Prim metadata（Prim 元数据）
D) VariantSet（变体集）

<details>
<summary>答案</summary>

**正确答案：A**

Attribute 是带类型的值，除默认值之外还支持时间采样（time-sampled）数据，因此它是承载动画数据的正确对象。

**其他选项错误的原因：**
- Relationship 指向其他 SdfPath，不是带类型、可动画的值
- Metadata 是静态配置数据，不是按帧采样的值
- VariantSet 用于在离散的数据配置之间切换，而不是连续的动画值

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

**Q3.** 以下哪个是引用 prim /World/Geo/Cube 上 'size' 属性的合法 SdfPath 语法？

A) /World/Geo/Cube:size
B) /World/Geo/Cube.size
C) /World/Geo/Cube->size
D) /World/Geo/Cube#size

<details>
<summary>答案</summary>

**正确答案：B**

在 SdfPath 语法中，用点号分隔 prim 路径与属性名。

**其他选项错误的原因：**
- 冒号语法用于带命名空间的属性名（例如 primvars:displayColor），而不是用于分隔 prim 路径与属性名
- SdfPath 中不存在箭头语法
- 井号不是 SdfPath 中的合法标点

</details>

---

**Q4.** USD Stage 与 USD Layer 的主要区别是什么？

A) Stage 会保存到磁盘，而 Layer 只存在于内存中
B) Stage 是一个或多个 layer 组合后在内存中的结果；Layer 是以文件为后端、承载 opinion 的容器
C) Layer 可以包含 prim，而 Stage 只能包含属性
D) Stage 与 Layer 是可互换的同义词

<details>
<summary>答案</summary>

**正确答案：B**

这是最基础的区别：layer 是以文件为后端（.usda/.usdc）的 opinion 来源，而 stage 是由它们推导出的运行时组合结果。

**其他选项错误的原因：**
- 这颠倒了两者的关系 —— 有文件后端的是 layer，stage 是内存中的组合结果
- Stage 与 Layer 最终都与 prim 相关；layer 承载 prim spec，stage 则表示组合后的 prim
- 这是两个含义不同、且被高频考查的概念，不是同义词

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

**Q5.** 一个基础几何 layer 和一个灯光 layer 都在某个 prim 的 displayColor 属性上创作了 opinion。二者都是同一 root layer 的 sublayer，且灯光 layer 在 subLayerPaths 中排在前面（更强）。在组合后的 stage 中哪个 opinion 胜出？

A) 无论顺序如何，基础几何 layer 的 opinion 总是胜出
B) 灯光 layer 的 opinion 胜出，因为它在 layer stack 中排在前面，因此更强
C) 两个 opinion 会合并为平均值
D) 由于 session layer 是隐式存在的，它的 opinion 总是覆盖两者

<details>
<summary>答案</summary>

**正确答案：B**

在 subLayerPaths 列表中，排在前面的 layer 是最强的 opinion 来源；组合时它的值胜出。

**其他选项错误的原因：**
- Sublayer 的强度由列表顺序决定，而不是由部门或角色决定
- USD 组合会解析出唯一最强的值 opinion；它不会对冲突的值取平均
- 除非在所讨论的 layer stack 中被显式包含，否则 session layer 不属于本题场景

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

**Q6.** 要建模两个 prim 之间的非层级链接（例如从 mesh 到 shader network 的材质绑定），应该使用哪种 USD 对象类型？

A) Relationship（关系）
B) Attribute（属性）
C) Reference（引用）
D) VariantSet（变体集）

<details>
<summary>答案</summary>

**正确答案：A**

Relationship 指向一个或多个其他 SdfPath，正是 prim 之间诸如材质绑定这类链接所使用的机制。

**其他选项错误的原因：**
- Attribute 承载的是带类型的值，而不是指向其他 prim 的路径目标
- Reference 是把外部 layer 内容引入进来的组合 arc，而不是已有 prim 之间的逐 prim 链接
- VariantSet 用于在离散的数据变体之间切换，而不是基于路径的链接

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

**Q7.** 在 layer 上设置时，必须指向一个已存在的 prim 路径，并决定该 layer 在其他地方被引用且未指定 prim 路径时使用哪个 prim 作为默认入口的元数据字段是哪个？

A) upAxis
B) defaultPrim
C) startTimeCode
D) kind

<details>
<summary>答案</summary>

**正确答案：B**

defaultPrim 是 layer 元数据，用于指定顶层 prim；当该 layer 在未显式给出 prim 路径的情况下被引用时，该 prim 就作为入口点。

**其他选项错误的原因：**
- upAxis 设置的是向上轴的约定（Y 或 Z），与引用入口点无关
- startTimeCode 定义的是动画时间范围的起点，而不是入口点 prim
- kind 是 prim 级元数据，用于分类 prim 的角色（例如 group、component、assembly），而不是 layer 级的默认入口

</details>

---

**Q8.** 某条流水线要求：直接打开一个 .usda 文件时，总是能生成带有布局部门所创作的正确向上轴和单位约定的 stage，无论该文件之后如何被其他 layer 引用。为了保证这一点，upAxis 和 metersPerUnit 应当创作在哪里？

A) 作为创作该文件的 root layer 上的 layer 元数据
B) 在使用方的 stage 的 session layer 上
C) 作为 defaultPrim 上的 prim 级元数据
D) 作为每个 Xform 属性上的属性元数据

<details>
<summary>答案</summary>

**正确答案：A**

upAxis 和 metersPerUnit 属于 layer 级（stage）元数据，把它们创作在该文件的 root layer 上，可以确保它们随文件一同传递，并在任何时候打开该文件时都被采纳。

**其他选项错误的原因：**
- session layer 是临时的、仅属于某个 stage 的，且绝不会随文件保存，因此无法保证其他人打开该文件时的行为
- upAxis 和 metersPerUnit 是 layer 级元数据，而不是 prim 级
- 它们是 layer 元数据，而不是各个属性上的属性级元数据

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

---


### 第 3 章 练习题


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `practice-questions/chapter-03-questions.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/practice-questions/chapter-03-questions.md) · 语言：英文原文 · 中译版



## 第 3 章：组合 Arc：Sublayer、Reference 与 Payload —— 练习题

**Q1.** 某工作室有一个 500GB 的城市环境资产，只出现在 10% 的镜头中。美术师需要其余 90% 镜头拥有快速的 stage 打开时间。应该用哪种组合 arc 来引用该资产，使其在不需要时不会产生内存/加载开销？

A) Reference
B) Sublayer
C) Inherit
D) Payload

<details>
<summary>答案</summary>

**正确答案：D**

stage 打开时，payload 默认不会被加载 —— 内容会被推迟，直到通过 stage.Load() 显式请求，从而让沉重、只是偶尔需要的资产也能快速打开。

**其他选项错误的原因：**
- Reference 在 stage 打开时总是会加载其目标（除非嵌套在未加载的 payload 中），因此并不能节省加载开销。
- Sublayer 把 opinion 合并到同一个 layer stack/命名空间中 —— 它并不是用来以延迟加载方式引入独立外部资产的。
- Inherit 共享基于 class 的 opinion，但不会延迟加载沉重的几何体数据。

</details>

---

**Q2.** 在 root layer 的 subLayers 列表中，当两个 sublayer 对同一属性都创作了 opinion 时，哪个 layer 贡献的 opinion 最强？

A) 列表顶部的 layer
B) 列表底部的 layer
C) 最近添加的 layer，与位置无关
D) 按文件名字母序排在最前的 layer

<details>
<summary>答案</summary>

**正确答案：A**

USD sublayer 的强度完全由列表位置决定 —— subLayers 列表顶部最强，底部最弱。

**其他选项错误的原因：**
- 列表底部是最弱的 layer，与正确答案恰好相反。
- 插入时间与强度无关 —— 只有列表中当前的顺序才重要。
- 文件名或字母序对组合强度没有任何影响。

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

**Q3.** 在 USD 中，技术上构成 'layer stack' 的是什么？

A) 当前会话中任何位置加载的所有 layer
B) 仅指单个 root layer，不考虑其 sublayer
C) root layer 加上通过 sublayer arc 递归到达的所有 layer
D) 通过任意组合 arc（包括 reference 和 payload）可达的所有 layer

<details>
<summary>答案</summary>

**正确答案：C**

layer stack 被定义为一个 layer 及其 sublayer，被递归组合成一个有序、扁平化的命名空间。Reference/payload 会引入并组合独立的 layer stack，它们不会合并进调用方的本地 layer stack。

**其他选项错误的原因：**
- 这描述的是整个组合后的场景图，而不是规范中专门使用的 'layer stack' 术语。
- 忽略 sublayer 是不正确的 —— 它们正是构成 layer stack 的定义性成员。
- Reference 和 payload 引入各自独立的 layer stack 并一起组合，而不是折叠进本地的那个。

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

**Q4.** 你需要在已有环境 layer 之上添加少量 override opinion（例如调整后的灯光强度），目标是完全相同的 prim 路径，既不引入别处的新 prim 层级，也不影响 reference/inherit 语义。哪种 arc 是合适的？

A) Reference
B) Sublayer
C) Payload
D) Specializes

<details>
<summary>答案</summary>

**正确答案：B**

Sublayer 把多个 layer 组合到同一个 layer stack 中、作用于相同的 prim 命名空间 —— 这非常适合像灯光微调这类只含 override、且不引入新资产的 layer。

**其他选项错误的原因：**
- Reference 的用途是组合引入外部/内部内容和新的 prim 层级，而不是简单的同命名空间 override。
- Payload 的行为类似 reference，但支持延迟加载 —— 它同样用于引入独立内容，而不是命名空间内的 override。
- Specializes 用于较弱的、可定制的基础 opinion，而不是同一命名空间上的强 override。

</details>

---

**Q5.** 某条流水线需要引入一个非常大的角色绑定资产，该资产在 stage 打开时不应自动加载，以保证初始场景加载足够快。哪种 arc 能满足这一要求？

A) Sublayer
B) Inherit
C) Reference
D) Payload

<details>
<summary>答案</summary>

**正确答案：D**

Payload arc 明确就是为沉重内容的延迟/惰性加载而设计的 —— 在客户端调用 stage.Load() 之前不会被加载。

**其他选项错误的原因：**
- Sublayer 不用于引入独立的外部资产 —— 它把 layer 合并到同一命名空间中。
- Inherit 用于基于 class 的共享 opinion，并不控制加载行为。
- Reference 在 stage 打开时会自动加载其内容，不满足延迟加载的要求。

</details>

---

**Q6.** 在已经打开的 UsdStage 上，哪个 Python API 调用可以在给定 prim 路径处卸载 payload？

A) stage.Reload()
B) stage.RemovePrim(path)
C) stage.Unload(path)
D) stage.Export()

<details>
<summary>答案</summary>

**正确答案：C**

stage.Unload(path) 会把给定路径处或其下方的 payload 标记为未加载，从而在组合后的 stage 中移除其贡献，而不会从磁盘上删除任何内容。

**其他选项错误的原因：**
- stage.Reload() 会从磁盘重新读取 layer 内容；它并不改变 payload 的加载状态。
- stage.RemovePrim() 会彻底删除 prim spec —— 这是破坏性的创作操作，而不是加载状态开关。
- stage.Export() 会把当前 stage 写入文件；它与 payload 的加载状态无关。

</details>

---

**Q7.** 某个 prim 的 payload（Payload B）嵌套在另一个 prim 之下，而后者的 payload（Payload A）当前处于未加载状态。Payload B 的内容会怎样？

A) 无论 Payload A 的状态如何，它都会自动加载
B) 在 Payload A 被加载、且 Payload B 本身也被显式加载之前，它始终保持未加载
C) 由于这种嵌套，USD 会抛出组合错误
D) 由于嵌套在 payload 中的 payload 行为类似 reference，它默认处于已加载状态

<details>
<summary>答案</summary>

**正确答案：B**

嵌套的 payload 要求每一层都被显式加载 —— 未加载的祖先 payload 会让位于其下的所有内容（包括嵌套的 payload）保持未加载，直到祖先与嵌套 payload 都被加载为止。

**其他选项错误的原因：**
- 无论祖先状态如何都自动加载，与 payload 的延迟加载设计相矛盾。
- 这是合法且受支持的组合方式 —— 嵌套 payload 是合法的，不会抛出错误。
- 嵌套 payload 不会继承类似 reference 的自动加载行为；在每一层它们都仍然受 payload 加载规则约束。

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

**Q8.** 某 root layer 的 subLayers 列表中，'anim.usda' 排在 'layout.usda' 之上。两者都对 /World/Cube.radius 创作了 opinion。哪个值会被组合到 stage 上？

A) layout.usda 的值，因为靠后的列表条目会胜出
B) anim.usda 的值，因为它在 subLayers 列表中位置更高，因此更强
C) 两个值会合并为平均结果
D) 无论 sublayer 顺序如何，最强的活跃 variant set 的值都会覆盖两者

<details>
<summary>答案</summary>

**正确答案：B**

Sublayer 的强度由其在 subLayers 列表中的位置决定，最顶部的条目最强 —— 因此 anim.usda 胜出。

**其他选项错误的原因：**
- 决定强度的是列表位置而非插入顺序；排在第二并不会让 layout.usda 更强。
- USD 组合从不对数值 opinion 取平均或混合 —— 最强的 opinion 直接胜出。
- 本场景中并不存在 variant set；即便存在，在本地 layer stack 内依然是 sublayer 顺序决定哪个 sublayer 的 opinion 可见。

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

---


### 第 4 章 练习题


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `practice-questions/chapter-04-questions.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/practice-questions/chapter-04-questions.md) · 语言：英文原文 · 中译版



## 第 4 章：LIVRPS 强度顺序与列表编辑操作 —— 练习题

**Q1.** 某个 prim 既在 variant set 中有 opinion，又来自一个 reference。两者都为同一属性提供了值，且不存在本地 opinion。哪个 opinion 胜出？

A) reference 的 opinion，因为 reference 是最后组合的
B) 文件中创作时间最新的那个 opinion
C) variant set 的 opinion，因为在 LIVRPS 中 VariantSets 比 References 更强
D) 各个 opinion 合并为平均值

<details>
<summary>答案</summary>

**正确答案：C**

LIVRPS 顺序（由强到弱）为 Local、Inherits、VariantSets、References、Payloads、Specializes。VariantSets 的强度高于 References，因此 variant 的 opinion 胜出。

**其他选项错误的原因：**
- Reference 比 VariantSets 更弱，并不是以某种'最后组合'的方式取胜
- USD 组合强度由 arc 类型和 layer stack 中的位置决定，而不是由创作时间戳决定
- USD 从不跨 arc 对值取平均；它选择最强的 opinion

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

**Q2.** 你需要给某个已经通过 reference 创作了三盏灯的 prim 再添加一盏强调光，同时不扰动被引用的灯光，也不改变它们的顺序。应该使用哪种列表编辑操作？

A) explicit
B) delete
C) 先 prepend，再删除现有的三盏灯并重新添加
D) append

<details>
<summary>答案</summary>

**正确答案：D**

Append 会把新项添加到较弱的（已经组合进来的）项之后，从而保留现有的被引用项及其顺序。

**其他选项错误的原因：**
- Explicit 会丢弃三盏被引用的灯并整体替换该列表
- Delete 是移除项，而不是添加新的灯
- 相比简单的 append，这种做法既具破坏性又属于无谓的反复折腾

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

**Q3.** 某个 stage 中：最强 layer 为 /Prim 上的 'color' 创作了一个本地 opinion；一个更弱的 layer（由 /Prim 引用）也为 'color' 创作了 opinion。'color' 最终的扁平化数值由什么决定？

A) 本地 opinion，因为在 LIVRPS 中 Local 是最强的位置，在其 layer stack 层级内总是胜出
B) 更弱的被引用 layer 的值，因为 reference 总是覆盖本地编辑
C) USD 抛出组合错误，需要人工解决
D) 该值按 layer 名称的字母序优先级来解析

<details>
<summary>答案</summary>

**正确答案：A**

本地 opinion 在 LIVRPS 排序中处于最强的位置，在同一 layer stack 范围内总是优先于 reference 这类较弱的 arc。

**其他选项错误的原因：**
- Reference 比本地 opinion 更弱，而不是更强 —— 这颠倒了实际顺序
- USD 在这里不会报错；它通过强度排序确定性地解析结果
- Layer 名称对组合强度没有任何影响

</details>

---

**Q4.** 你希望某个 prim 从同一场景中的另一个 prim 那里继承一组基础属性，而不复制数据；同时希望基 prim 后续的编辑能自动传播。哪种组合 arc 是正确选择？

A) Payload
B) Inherit
C) Reference
D) VariantSet

<details>
<summary>答案</summary>

**正确答案：B**

Inherits 正是为基于 class 的共享而设计的：基 prim 的 opinion 会实时传播给所有继承它的 prim，并且在强度顺序中比 References/Payloads/VariantSets 更强。

**其他选项错误的原因：**
- Payload 用于延迟加载沉重的场景数据，而不是轻量的 class 实时传播
- Reference 组合外部或内部的场景数据，但它比 Inherits 弱，通常用于资产组合而非类似 class 的共享
- VariantSet 用于可切换的替代方案，而不是共享一组基础属性

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

**Q5.** 哪一种列表编辑操作会完全丢弃某个可列表编辑字段（例如 references）的所有较弱 opinion，只用该 layer 上指定的项来替换它们？

A) append
B) prepend
C) explicit
D) delete

<details>
<summary>答案</summary>

**正确答案：C**

Explicit 会重置组合后的列表，忽略所有较弱的 opinion，只使用该 layer 中指定的项。

**其他选项错误的原因：**
- Append 把项添加到较弱 opinion 的项之后，并不会丢弃它们
- Prepend 把项添加到较弱 opinion 的项之前，并不会丢弃它们
- Delete 从组合后的列表中移除指定的项，但不会重置整个列表

</details>

---

**Q6.** 在 USD 的 .usda 文件中，某个 references 字段没有使用 prepend/append/delete 关键字，只写了一个裸的引用路径。在现代 USD 中，这种列表编辑默认是如何处理的？

A) 视为 explicit，丢弃所有较弱的已组合 reference
B) 视为 append，把该项添加到较弱 opinion 之后
C) 视为错误，必须显式给出关键字
D) 视为 prepend，把该项添加到较弱 opinion 之前

<details>
<summary>答案</summary>

**正确答案：D**

当文件语法中未指定列表编辑关键字时，USD 默认将该操作视为 prepend。

**其他选项错误的原因：**
- Explicit 需要 explicit 关键字；它不是默认行为
- 默认不是 append，而是 prepend
- USD 并不要求显式关键字 —— 它会回退为 prepend

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

**Q7.** 被引用的资产本身在其自己的 layer stack 内部还包含自己的组合 arc（variant 和嵌套 reference）。当该资产通过外层 stage 上的一个 reference 被引入时，LIVRPS 强度排序是如何适用的？

A) LIVRPS 只适用于最外层的 stage layer stack；被引用资产内部的嵌套 arc 会被任意扁平化
B) reference 内部的嵌套组合 arc 会被完全忽略
C) 嵌套 arc 会按 LIVRPS 的逆序解析以避免冲突
D) LIVRPS 排序是递归应用的 —— 被引用资产自己的 layer stack 会先在内部按 LIVRPS 解析，然后才被组合进外层 stack

<details>
<summary>答案</summary>

**正确答案：D**

强度排序是递归的：由某个 arc（如 reference）引入的每个 layer stack 都会先在内部按 LIVRPS 解析，得到的扁平化 opinion 再以该 arc 在外层 stack 中的强度层级参与组合。

**其他选项错误的原因：**
- LIVRPS 并不局限于最外层的 stack —— 它适用于每一个嵌套的 layer stack
- 嵌套 arc 会被完整解析，而不是被忽略
- 不存在'逆序'；递归应用的仍是同一套 LIVRPS 顺序

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

**Q8.** 哪个序列正确地按由强到弱列出了 LIVRPS 组合 arc？

A) Local, References, Inherits, VariantSets, Payloads, Specializes
B) Specializes, Payloads, References, VariantSets, Inherits, Local
C) Local, Inherits, VariantSets, References, Payloads, Specializes
D) Local, VariantSets, Inherits, Payloads, References, Specializes

<details>
<summary>答案</summary>

**正确答案：C**

LIVRPS 代表 Local、Inherits、VariantSets、References、Payloads、Specializes —— 正是由强到弱的强度顺序。

**其他选项错误的原因：**
- 这打乱了 Inherits 与 References 的顺序
- 这是正确的列表，但被颠倒了（由弱到强），与题目要求恰好相反
- 这打乱了 VariantSets、Inherits 以及 Payloads/References 的顺序

> ⚠️ 考试中经常出错 —— 请仔细阅读选项。

</details>

---

---


### 第 05 章 练习题


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `practice-questions/chapter-05-questions.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/practice-questions/chapter-05-questions.md) · 语言：英文原文 · 中译版



## 第 5 章：变体集、Inherits、Specializes 与非破坏性覆盖 — 练习题

**Q1.** 某工作室拥有 500 个主角角色资产。每个角色都引用了一个共享的 'CharacterBase' 图元，该图元定义了一个绑定控制器显示属性。绑定 TD 需要每个角色都能自动获得对该基础属性的更新，而且基础意见必须胜出，甚至要压过被引用角色资产自身的本地意见。应当使用哪种组合弧把角色连接到 CharacterBase？

A) Specializes 弧，因为它让基础意见仍然可以被覆盖
B) Inherits 弧，因为继承而来的意见比引用更强，能够覆盖引用
C) Payload 弧，因为它能对基础图元实现延迟加载
D) 在多种基础配置之间切换的变体集

<details>
<summary>答案</summary>

**正确答案：B**

在 LIVRPS 强度顺序（Local, Inherits, Variants, References, Payloads, Specializes）中，Inherits 位于 References 之上，因此来自被继承的 'class' 图元的意见会胜过通过引用带入的意见——这正是让共享基础属性占据优先地位所需要的行为。

**其他选项错误的原因：**
- Specializes 的强度弱于引用，因此胜出的会是被引用资产的意见而不是基础——与需求正好相反。
- Payload 只控制某个子树是否被加载进内存；它与相对于引用的意见强度无关。
- 变体集只是在已创作的不同变体之间切换，并不会与被引用内容建立优先级关系。

> ⚠️ 考试中经常被忽略——请仔细阅读选项。

</details>

---

**Q2.** 某资产库团队希望每个道具资产都具有合理的默认碰撞属性与物理属性，并且这些属性只需在一个共享的 'PropDefaults' 图元上定义一次。各个镜头必须能够在特定的道具实例上自由覆盖这些默认值——即便道具是通过引用引入的——而且默认值的弧不能与之争夺优先级。哪种弧能满足这一需求？

A) Inherits，这样默认值总是占据优先地位
B) References，让每个道具直接指向 PropDefaults
C) Specializes，让 PropDefaults 充当位于实例意见与引用意见之下的弱回退
D) Sublayers，让 PropDefaults 在根层栈处组合

<details>
<summary>答案</summary>

**正确答案：C**

Specializes 是 LIVRPS 强度顺序中最弱的弧，排在 References 和 Payloads 之下。这使它非常适合承载基础/默认意见：来自引用、变体或实例上本地覆盖的任何意见都会胜过 specialize 的目标，从而满足“可自由覆盖的回退”这一需求。

**其他选项错误的原因：**
- Inherits 的强度强于引用，因此会强制默认值压过镜头级覆盖——与需求正好相反。
- 用普通引用指向 defaults 图元并不会与道具图元本身建立回退关系；它只会把默认值复制成一个独立的图元。
- Sublayers 在层栈根部以很高的强度（local）组合，会让默认值几乎无法按实例覆盖。

> ⚠️ 考试中经常被忽略——请仔细阅读选项。

</details>

---

**Q3.** 你需要在某个镜头中为一个被引用的树木资产的单个实例着色，既不改变树的类型，也不影响流水线其他位置同一资产的其他实例。哪种创作方式是正确的？

A) 在镜头层中以相同的 typeName 在树图元上创作一个 'def'，然后设置 displayColor
B) 在镜头层中在树图元上创作一个 'over'，只设置 displayColor 属性
C) 删除被引用的树图元，并用 'def' 在本地重新定义
D) 为树资产添加一个新的变体集，并全局选择一个 'red' 变体

<details>
<summary>答案</summary>

**正确答案：B**

'over' 会在已定义的图元上创作一条非破坏性意见，无需重新指定其类型或存在性。它会组合进该图元已有的意见栈中，只改变被请求的属性（displayColor），而底层定义、其他属性以及所有其他实例都保持不变。

**其他选项错误的原因：**
- 以相同的 typeName 重新声明 'def' 既没有必要也不符合惯用做法；即使可行，也有意外重置其他回退值的风险，并非考试所期望的非破坏性惯例。
- 删除并重新定义图元会破坏来自引用的组合弧，丢失全部上游资产意见——与非破坏性编辑正好相反。
- 变体集会跨越整个变体弧改变已创作的选择，对单个镜头中一次性的、针对单个实例的颜色微调来说既过度又非局部。

</details>

---

**Q4.** 哪种 specifier 用于纯作为继承目标的图元，使其被排除在默认阶段遍历和渲染之外？

A) class
B) over
C) def
D) payload

<details>
<summary>答案</summary>

**正确答案：A**

使用 'class' specifier 声明的图元是抽象的。在组合后的 UsdPrim 上它们会被标记为 IsAbstract，并被排除在默认的 UsdStage 遍历（例如带默认 predicate 的 UsdPrimRange）和渲染之外，这正是可复用继承目标所期望的行为。

**其他选项错误的原因：**
- 'over' 只是给已存在的已定义图元追加意见；它不会创建抽象的、被排除遍历的图元。
- 'def' 定义的是具体图元，会被包含在默认遍历与渲染之中——不适合作为隐藏的、仅供继承的目标。
- 'payload' 是用于延迟加载的组合弧，而不是图元 specifier。

> ⚠️ 考试中经常被忽略——请仔细阅读选项。

</details>

---

**Q5.** 在 USD 层中，变体集当前创作的选择存储在哪里？

A) 在图元的 'variants' 元数据字典中，以变体集名称为键
B) 在一个以变体集命名的专用子层中
C) 作为图元默认属性上名为 'variantSelection' 的属性
D) 在根层的 'defaultPrim' 元数据字段中

<details>
<summary>答案</summary>

**正确答案：A**

变体选择以列表形式可编辑的元数据存储在图元上，即 'variants' 字典字段，把每个变体集名称映射到所选变体的名称。这正是 UsdVariantSet.SetVariantSelection 所写入的内容，也是任何更强的层都能非破坏性覆盖的内容。

**其他选项错误的原因：**
- USD 不会自动为每个变体集创建单独的子层；子层是一种手动、文件级的组合机制，与变体的存储无关。
- 不存在名为 'variantSelection' 的标准图元属性；选择属于图元元数据，而不是属性命名空间中的属性。
- 'defaultPrim' 元数据用于标识一个层中在被引用时充当入口的图元，与变体选择毫无关系。

> ⚠️ 考试中经常被忽略——请仔细阅读选项。

</details>

---

**Q6.** 在 LIVRPS 组合强度顺序中，哪种弧整体最弱，即它的意见可以被引用、载荷、继承、变体和本地意见覆盖？

A) Inherits
B) Payloads
C) References
D) Specializes

<details>
<summary>答案</summary>

**正确答案：D**

LIVRPS 助记法（Local, Inherits, Variants, References, Payloads, Specializes）按从强到弱排列各类弧。Specializes 排在最后，因此是最弱的弧——其他所有弧类型的意见都优先于 specialize 目标上的意见。

**其他选项错误的原因：**
- Inherits 是强度第二强的弧，排在 Variants、References、Payloads 和 Specializes 之上。
- 在该顺序中 Payloads 排在 Specializes 之上；只有 Specializes 更弱。
- References 排在 Payloads 和 Specializes 之上，因此不是最弱的弧。

> ⚠️ 考试中经常被忽略——请仔细阅读选项。

</details>

---

**Q7.** 某灯光美术希望针对不同镜头，非破坏性地在一个道具的 'clean' 与 'damaged' 表面外观之间切换，并且这个选择要能按镜头层轻松更改、在 USD 文本文件中易于查看。哪种方式最符合这一需求？

A) 创作两个独立的 'def' 图元，每种外观一个，并切换它们的可见性
B) 创建一个变体集（例如 'lookVariant'），包含 'clean' 和 'damaged' 变体，并按镜头覆盖变体选择
C) 使用 inherits 弧，根据镜头指向 'clean' 或 'damaged' 的 class 图元
D) 根据镜头在 clean 或 damaged 的几何文件之间选择使用 payload

<details>
<summary>答案</summary>

**正确答案：B**

变体集正是为这一用例而设计的：它们把互斥的已创作变体封装在一个图元之下，把当前选择存为简单的元数据，并允许任何更强的层（例如镜头层）非破坏性地覆盖 'variants' 选择，而无需改动底层的图元定义。

**其他选项错误的原因：**
- 在重复的 'def' 图元之间切换可见性是破坏性的，会让创作数据翻倍，而且并不是考试所期望的互斥外观建模方式。
- Inherits 用于共享的 class 级意见并具有很强的优先级，而不是用于按镜头在互斥的外观状态之间切换。
- Payload 出于性能原因控制子树的加载/卸载，而不是在已创作的外观变体之间做选择；按镜头切换 payload 目标也不是惯用机制。

</details>

---

**Q8.** 在 USD 流水线中，于更强（例如镜头级）的层里做编辑时优先使用 'over' 而非 'def'，其背后的核心理念是什么？

A) 因为只要编辑被引用的图元，'over' 就是必需的语法
B) 因为 'over' 意见在运行时比 'def' 意见加载得更快
C) 因为 'def' 不能用在引用弧或载荷弧之内
D) 因为 'over' 会把额外的意见非破坏性地组合到已有图元上，保留原始定义，并支持安全、可逆的图层叠加

<details>
<summary>答案</summary>

**正确答案：D**

USD 的非破坏性编辑理念倾向于使用 'over'，因为它在不重新声明图元类型或存在性的情况下，把额外的意见叠加到已有定义之上，从而让原始创作保持完整、可逆，并能在大型流水线的众多层之间安全地组合。

**其他选项错误的原因：**
- 'over' 是一种强烈的惯例，而不是硬性的语法要求——技术上你确实可以重新创作 'def'，但不推荐，而且行为并不等价。
- 'over' 与 'def' 在运行时没有有意义的性能差异；这一区别关乎组合语义，而非速度。
- 'def' 在被引用或被载荷的层中完全合法——事实上，资产自身的层通常就是用 'def' 最初定义该图元，之后再由其他层覆盖。

</details>

---

---


### 第 06 章 练习题


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `practice-questions/chapter-06-questions.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/practice-questions/chapter-06-questions.md) · 语言：英文原文 · 中译版



## 第 6 章：用于聚合的组件与装配资产设计 — 练习题

**Q1.** 某工作室把 200 个外部供应商的 USD 资产聚合进一个装配体中。多个供应商各自把资产根创作在路径 '/Geom' 上，组合时产生了命名空间冲突。哪种结构上的修复方案最佳？

A) 把每个供应商的资产引用到装配体下各自唯一命名的子图元之下，而不是合并到同一路径上
B) 在组合之后手动展平阶段，并手工重命名每一个发生冲突的图元
C) 在发生冲突的图元之上添加覆盖意见以掩盖重复
D) 把每个供应商引用转换为载荷弧，让命名空间自动合并

<details>
<summary>答案</summary>

**正确答案：A**

引用弧会在组合时重新确定命名空间的根。把每个供应商资产嵌套在一个唯一命名的子图元之下，可以在结构上避免冲突，无需事后编辑。

**其他选项错误的原因：**
- 事后手工重命名无法规模化，而且每次源资产更新都会失效
- 覆盖意见只是在某个组合阶段上掩盖症状；潜在的冲突风险对任何其他使用者依然存在
- 载荷弧控制加载时机，而不是命名空间合并行为——改用载荷弧对解决路径冲突毫无帮助

> ⚠️ 考试中经常被忽略——请仔细阅读选项。

</details>

---

**Q2.** 某装配体聚合了 300 个高面数的组件资产，必须能快速打开以进行 lookdev 评审，并且只按需加载几何体。组件引用应当使用哪种组合弧？

A) Sublayer
B) Reference
C) Inherit
D) Payload

<details>
<summary>答案</summary>

**正确答案：D**

载荷弧默认被排除在组合后的阶段之外，只有通过 Load() 显式请求时才会加载，因此在大规模场景下延迟加载重型组件时，载荷弧是正确选择。

**其他选项错误的原因：**
- 子层用于在同一层栈内合并意见以实现覆盖，而不是用于聚合外部重型资产
- 引用弧会立即且无条件地加载，与快速打开场景的目标背道而驰
- 继承用于共享的 class 级覆盖，而不是引入重型外部几何体

> ⚠️ 考试中经常被忽略——请仔细阅读选项。

</details>

---

**Q3.** 某团队要发布一个新的组件资产。使用者只应与一个稳定的顶层图层交互，该图层暴露出始终一致的 defaultPrim 和变体集，而永远不需要了解内部的 geom/material 文件布局。哪种模式满足这一要求？

A) 一个把全部几何体、材质和元数据都内联包含进来的单体 .usda 文件
B) 在引用时把所有内部图层展平进使用方场景
C) Asset Interface 图层模式，把内部图层组合在一个稳定的顶层入口之下
D) 直接引用内部的 geom.usd 文件，绕过任何顶层图层

<details>
<summary>答案</summary>

**正确答案：C**

Asset Interface 图层模式提供了一个供使用者引用的单一稳定入口，把内部结构封装起来，使其可以变化而不会破坏下游场景。

**其他选项错误的原因：**
- 单体文件没有任何封装能力，也无法实现按需选择性地加载载荷或日后替换内部实现
- 展平会破坏实现选择性加载和变体切换所需的组合弧
- 直接引用内部文件正是考试明确要考查的封装反模式

</details>

---

**Q4.** 对于自包含、不可再分解的叶子资产（例如没有嵌套模型子项的单个道具模型），应当赋予哪个 Kind 值？

A) group
B) assembly
C) subcomponent
D) component

<details>
<summary>答案</summary>

**正确答案：D**

component 是保留给原子的、可独立引用的叶子资产的 model kind，这类资产不包含任何更细分的 model kind 子项。

**其他选项错误的原因：**
- group 是对多个模型的通用组织性聚合，而不是叶子资产
- assembly 是 group 的子类型，用于对组件的更大规模聚合，而不是单个叶子
- subcomponent 是用于组件内部有意义部件的非 model kind，而不是顶层资产本身

</details>

---

**Q5.** 哪种 Kind 表示对多个 component 或 group 模型的聚合，例如由车轮、车身和引擎组件构成的一辆完整装配车辆？

A) assembly
B) component
C) subcomponent
D) undefined

<details>
<summary>答案</summary>

**正确答案：A**

assembly 是一种专门用来表示把多个 component 或 group 模型聚合为单一更高层级组合资产的 model kind。

**其他选项错误的原因：**
- component 描述的是原子的叶子资产，而不是其他模型的聚合
- subcomponent 是用于内部子部件的非 model kind，而不是顶层聚合资产
- undefined/无 kind 会让资产无法分类，也无法被基于 kind 的工具遍历；当有具体 kind 可用时，这绝不是正确答案

> ⚠️ 考试中经常被忽略——请仔细阅读选项。

</details>

---

**Q6.** 为组件创作 Asset Interface 图层时，应当用哪种组合弧引入几何体载荷文件，以便使用者可以自行选择是否加载重型几何体？

A) Sublayer
B) Inherit
C) Payload
D) Specialize

<details>
<summary>答案</summary>

**正确答案：C**

标准的 OpenUSD 资产结构中，接口图层通过载荷弧引入一个 payload.usd 文件，让使用者可以延迟加载重型几何体，同时立即暴露出轻量的接口。

**其他选项错误的原因：**
- 子层在同一层栈内合并意见，并不提供按需加载的行为
- 继承用于共享的 class 级覆盖，而不是引入重型几何体载荷
- 特化用于更弱的回退覆盖，而不是在延迟加载的同时组合外部重型数据

</details>

---

**Q7.** 两个被引用的装配体各自定义了一个名为 /World 的根图元，聚合时发生冲突。最稳健的结构性修复方案是什么？

A) 把每个被引用的资产封装在各自唯一命名的子 scope 图元之下，使 /World 永远不会在聚合根处出现两次
B) 在聚合之后手工为每一处 /World 添加覆盖意见以消除歧义
C) 使用 specializes 弧合并两个 /World 图元
D) 把两个引用都转换成载荷，使同一时间只加载一个

<details>
<summary>答案</summary>

**正确答案：A**

把每个被引用的资产嵌套在一个唯一命名的子 scope 之下会重新确定其命名空间的根，从结构上防止冲突，无论源资产内部创作了什么。

**其他选项错误的原因：**
- 覆盖意见只是按阶段处理症状，必须为每个使用者重复一遍，无法规模化
- Specializes 弧用于回退覆盖关系，而不是解决重复的命名空间路径
- 载荷只控制加载时机；只要两个 /World 图元恰好同时被加载，仍然会冲突

> ⚠️ 考试中经常被忽略——请仔细阅读选项。

</details>

---

**Q8.** 在 OpenUSD 资产结构中，Asset Interface 图层模式的首要目的是什么？

A) 提供一个稳定、一致的顶层入口，封装内部文件布局，使使用者永远不需要引用内部结构
B) 在路径追踪期间直接提升渲染性能
C) 直接存储全部几何数据，以获得尽可能快的磁盘访问
D) 取代已发布资产上对 Kind 元数据的需求

<details>
<summary>答案</summary>

**正确答案：A**

接口图层的核心目的在于封装：提供一个单一稳定的引用目标，把内部的 geom/material/payload 文件组织对使用者隐藏起来。

**其他选项错误的原因：**
- 渲染性能与图层结构无关；它取决于几何体复杂度和着色，而不是接口模式
- 接口图层有意保持轻量，通常不会内联存储几何体——几何体存放在被组合的内部图层中
- Kind 元数据与接口图层模式是互补关系，而不是可以互相替代的关系

</details>

---

---


### 第 07 章 练习题


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `practice-questions/chapter-07-questions.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/practice-questions/chapter-07-questions.md) · 语言：英文原文 · 中译版



## 第 7 章：原生（原型）实例化与点实例化 — 练习题

**Q1.** 某工作室需要在场景中填充 200 万棵树。单棵树从来不需要唯一的材质覆盖，只需要偶尔隐藏特定的树来做相机视锥剔除测试。哪种方式最符合这一需求？

A) 使用带 protoIndices 和 positions 的 UsdGeomPointInstancer，并用 invisibleIds 驱动被隐藏的树
B) 把每个树图元标记为 instanceable=true，使它们共享同一个原型
C) 不做任何实例化，把树资产引用 200 万次
D) 把每个树的变体放进原型图元上的一个变体集里

<details>
<summary>答案</summary>

**正确答案：A**

PointInstancer 借助扁平数组（protoIndices、positions）扩展到数百万实例，而 invisibleIds 是 schema 原生的机制，可以在不触及每个实例的场景图元的前提下隐藏指定的实例 id。

**其他选项错误的原因：**
- 原生实例化仍然会为每个实例创建一个场景图元；在 200 万实例的规模下，相比基于数组的点实例化，它会显著抬高内存占用和阶段填充时间。
- 不做实例化的引用会为每一份拷贝重复完整的原型组合——在这一规模下是最差的内存/性能选项。
- 原型上的变体集会一次性改变所有实例共享的定义；它们并不提供按实例剔除的能力。

> ⚠️ 考试中经常被忽略——请仔细阅读选项。

</details>

---

**Q2.** 50 个汽车图元都设置了 instanceable=true 并引用同一个原型资产。你必须给其中恰好 5 个赋予唯一的车漆材质，而另外 45 个继续共享原型的渲染数据。正确的工作流是什么？

A) 直接在这 5 辆车的实例代理路径上创作材质绑定
B) 在共享的原型图元上编辑材质绑定
C) 只对这 5 个图元设置 instanceable=false，让它们各自成为自己的原型，然后在其上创作唯一的材质绑定
D) 给原型添加变体集，并为每个实例代理选择不同的变体

<details>
<summary>答案</summary>

**正确答案：C**

你不能在实例代理上创作新的意见（比如材质绑定关系）。对这 5 个例外者取消实例化只会打破它们自己的共享，把每一个变成各自独立的组合原型，在那里进行真实的材质覆盖才是合法的。

**其他选项错误的原因：**
- 实例代理是用于查看组合结果的读取/检查路径；在其上创作关系或新属性会报错——这是考试中的头号陷阱。
- 直接编辑共享原型会改变全部 50 个实例的材质，而不只是目标中的那 5 辆车。
- 变体选择是按原型解析一次的组合弧；你无法为同一个共享原型的不同实例代理选择不同的变体。

> ⚠️ 考试中经常被忽略——请仔细阅读选项。

</details>

---

**Q3.** 当在引用方图元上设置为 true 时，哪个元数据字段会让 USD 通过原型与其他相同实例共享组合结果？

A) instanceable = true
B) instance = true
C) isPrototype = true
D) shared = true

<details>
<summary>答案</summary>

**正确答案：A**

`instanceable` 正是定义在 UsdPrim 上的布尔元数据字段，用于让图元选择加入原生实例化/原型共享。

**其他选项错误的原因：**
- "instance" 并不是用于此目的的真实 USD 元数据键。
- "isPrototype" 并不存在这种可创作的元数据——原型是内部计算出来的，并通过保留路径 /__Prototype_N 暴露。
- "shared" 不是 USD 元数据字段；它是考试中编造的干扰项。

</details>

---

**Q4.** UsdGeomPointInstancer 的 `orientations` 属性使用什么数据类型来存储每个实例的旋转？

A) matrix4d[]
B) float3[] 欧拉角
C) quath[]（半精度四元数数组）
D) 仅 quatf[]，不支持 quath

<details>
<summary>答案</summary>

**正确答案：C**

PointInstancer.orientations 以 quath[]（半精度四元数）的形式创作，正是为了在海量实例数量下减少内存占用。

**其他选项错误的原因：**
- matrix4d[] 每实例的体积要比四元数大得多，而且它不是该 schema 的属性类型。
- 该 schema 不使用欧拉角；四元数可以避免万向节锁并且插值平滑。
- quath 正是 schema 的默认类型；quatf 不是 PointInstancer 的标准 orientations 类型。

> ⚠️ 考试中经常被忽略——请仔细阅读选项。

</details>

---

**Q5.** 某可视化项目需要 300 个各自不同的建筑模块，其中 40 个必须显示与其余不同的屋顶颜色变体选择，而且美术经常要在视口中拾取单栋建筑进行调整。哪种实例化策略最佳？

A) 带 variant-index primvar 的 UsdGeomPointInstancer
B) 一个烘焙了几何体变化、完全不做实例化的单一网格
C) 使用 instanceable=true 的原生（原型）实例化，使每栋建筑仍然是可单独选中、可寻址的图元
D) 使用 PointInstancer，让 protoIndices 指向 40 个作为独立原型烘焙的不同原型变体，忽略选择需求

<details>
<summary>答案</summary>

**正确答案：C**

在几百个实例这种规模下，若需要逐实例选择、变体切换和视口拾取，原生实例化会让每个实例在层级中保持为可单独寻址的图元，而 PointInstancer 的实例不具备这一点。

**其他选项错误的原因：**
- PointInstancer 的实例默认不是可单独选中的场景图元——它们只是索引/数组条目，这让逐实例的变体工作流和视口拾取都很别扭。
- 把变化烘焙进单一网格会彻底消除复用和逐实例可编辑性，作为可维护的流水线也无法扩展。
- 通过 protoIndices 来满足变体需求在技术上能实现多样性，但仍然牺牲了场景明确要求的单个图元可选择性。

</details>

---

**Q6.** 美术在视口中选中一个被实例化的图元时，解析出的路径是 /World/Set/Buildings/__Prototype_1/Geom/Mesh 之类，而不是引用方实例自身的路径。这种解析路径叫什么？

A) 原型覆盖
B) 组合弧目标
C) 实例代理
D) 共享引用别名

<details>
<summary>答案</summary>

**正确答案：C**

实例代理（instance proxy）是 USD 合成出来的、看起来并非实例但可寻址的路径，使工具能够在不复制共享原型数据的前提下，检查（并在有限程度上覆盖）某个具体实例的组合结果。

**其他选项错误的原因：**
- "原型覆盖"不是标准的 USD 术语。
- 组合弧目标是引用/载荷/继承的目的地，而不是逐实例的检查路径。
- "共享引用别名"是杜撰出来的术语，USD 文档和考试中都没有使用。

</details>

---

**Q7.** UsdGeomPointInstancer 上的哪个关系指定了实例所依据的源图元集合？

A) rel targets
B) rel prototypes
C) rel sourcePrims
D) rel instanceSources

<details>
<summary>答案</summary>

**正确答案：B**

`prototypes` 正是 UsdGeomPointInstancer 上的关系名称，列出 protoIndices 中每个条目所索引的候选图元。

**其他选项错误的原因：**
- "targets" 是通用的关系术语，不是 schema 定义的名称。
- "sourcePrims" 不是该 schema 的属性名称。
- "instanceSources" 听起来合理，但它是错误的干扰项名称。

</details>

---

**Q8.** 某流水线需要在 500,000 个点实例化的岩石中永久隐藏实例 id 12、45 和 88，同时不改动其余所有实例的 positions 或 protoIndices 数组。应当创作哪个属性？

A) protoIndices，把对应条目设为 -1
B) scales，把这三个索引设为 0
C) invisibleIds，列出 12、45 和 88
D) positions，把这三个索引移到屏幕外

<details>
<summary>答案</summary>

**正确答案：C**

invisibleIds 是 schema 专门提供的属性，用于把实例 id 标记为隐藏，而不会扰动其余的逐实例数组。

**其他选项错误的原因：**
- 在该 schema 中 protoIndices 不支持把 -1 作为合法的 'hide' 哨兵值，那样会破坏数组索引对齐的预期。
- 缩放为 0 在视觉上可行，但那是一种手动变通做法，而且实例对于边界/碰撞等计算仍然是 'active' 的，这不同于专用的 invisibleIds 机制。
- 把 positions 移到屏幕外是一种绕行方案，而不是 schema 所期望、且为考试所考察的解决方案，还会浪费渲染/边界计算。

> ⚠️ 考试中经常被忽略——请仔细阅读选项。

</details>

---

---


### 第 10 章练习题


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `practice-questions/chapter-10-questions.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/practice-questions/chapter-10-questions.md) · 语言：英文原文 · 中译版



## 第 10 章：Stage 遍历、以编程方式编辑组合，以及 Hydra 基础 — 练习题

**Q1.** 你需要遍历一个 stage，并跳过所有以 kind 为 "group" 的 prim 为根的整个子树，以加快处理速度，且不访问它们的后代。哪种做法是正确的？

A) 使用 stage.Traverse() 并递归调用 prim.GetChildren()，手动检查 kind
B) 使用 Usd.PrimRange(stage.GetPseudoRoot(), Usd.TraverseInstanceProxies())，并在每个 prim 上继续
C) 使用 stage.TraverseAll()，之后再用列表推导式过滤结果
D) 使用 Usd.PrimRange(prim)，并在迭代器位于 kind 为 "group" 的 prim 上时调用 range.PruneChildren()

<details>
<summary>答案</summary>

**正确答案：D**

Usd.PrimRange 提供了 PruneChildren()，必须在迭代器定位到当前 prim 时调用它，才能在同一次遍历中停止下降到该 prim 的子节点——这正是预期的剪枝机制。

**其他选项错误的原因：**
- 可行，但手动重新实现了遍历，而没有使用考试考察的内置且更高效的 PrimRange 剪枝 API
- TraverseInstanceProxies() 改变的是访问哪些实例内容，与按 kind 剪枝子树无关
- TraverseAll() 还会访问 inactive/undefined/abstract 的 prim，而事后过滤并不能避免访问被剪枝子树的代价

> ⚠️ 考试中经常出错——请仔细阅读各选项。

</details>

---

**Q2.** 在 Python 中，哪个调用能正确地在某个 prim 上添加对外部资产的引用？

A) prim.GetReferences().AddReference("/path/to/asset.usd")
B) prim.GetPayloads().AddPayload("/path/to/asset.usd")
C) prim.AddReference("/path/to/asset.usd")
D) Sdf.Reference(prim, "/path/to/asset.usd")

<details>
<summary>答案</summary>

**正确答案：A**

GetReferences() 返回一个 Usd.References 对象，其 AddReference(assetPath, primPath="") 方法会在该 prim 上创作一条引用弧（reference arc）。

**其他选项错误的原因：**
- AddPayload 创作的是 payload 弧，其按需加载语义不同——对于该需求来说弧类型不对
- Prim 本身没有 AddReference 方法；引用必须通过 GetReferences() 来创作
- Sdf.Reference 只是描述引用目标的普通数据结构，并不是能向 prim 创作任何内容的方法

</details>

---

**Q3.** 哪段代码能正确地创作名为 "shadingVariant" 的 variant set，其中包含名为 "red" 的 variant，并将其选中？

A) vs = prim.GetVariantSet("shadingVariant"); vs.AddVariant("red"); vs.SetVariantSelection("red")
B) prim.GetVariantSets().SetVariantSelection("shadingVariant", "red")
C) vs = prim.GetVariantSets().GetVariantSet("shadingVariant"); vs.SetVariantSelection("red")
D) vs = prim.GetVariantSets().AddVariantSet("shadingVariant"); vs.AddVariant("red"); vs.SetVariantSelection("red")

<details>
<summary>答案</summary>

**正确答案：D**

AddVariantSet() 创作该 variantSet 的存在，AddVariant() 创作一个可选项，SetVariantSelection() 在当前 EditTarget 上创作选择意见——这才是正确的调用顺序。

**其他选项错误的原因：**
- Prim 没有单独的 GetVariantSet 方法；variant set 需要通过 GetVariantSets() 访问
- GetVariantSets() 没有 SetVariantSelection(setName, variantName) 这种组合签名
- GetVariantSet 只能获取已存在的 variant set 的句柄，而此处从未调用 AddVariant，因此 "red" 这个 variant 并不存在，选择也无法解析出任何意见

> ⚠️ 考试中经常出错——请仔细阅读各选项。

</details>

---

**Q4.** 哪项陈述正确描述了 Hydra 在 USD 流程中的角色？

A) Hydra 的 scene delegate 会在渲染过程中把编辑回写到 stage 的 session layer
B) Storm 或 Arnold 等 Hydra render delegate 可以修改当前 EditTarget 中的 prim 意见
C) UsdImagingGL 要求在每次渲染调用前都先调用 stage.SetEditTarget()
D) scene delegate 把 USD 场景数据转换为 Hydra render index，render delegate 再消费该 index 完成渲染，并不存在回写到 USD 的路径

<details>
<summary>答案</summary>

**正确答案：D**

Hydra 严格来说只是一个只用于渲染的抽象层：scene delegate 向 render index 供给数据，render delegate 基于它进行光栅化/渲染，两者都不会回写 USD stage。

**其他选项错误的原因：**
- scene delegate 只为渲染读取场景数据，绝不会向任何 layer 创作编辑
- render delegate 只是 render index 的消费方，仅用于渲染，并没有通向 USD 的创作 API
- 通过 Hydra 渲染根本不需要也不会使用 SetEditTarget——EditTarget 关注的是创作，而不是渲染

> ⚠️ 考试中经常出错——请仔细阅读各选项。

</details>

---

**Q5.** 某个 stage 中包含 instanceable 引用。部分用于交叉引用（例如材质绑定）的 prim 位于被实例化的 prototype 内部，默认的 stage.Traverse() 不会访问到它们。怎样才能把它们作为 instance proxy 一起遍历出来？

A) 第二次调用 stage.Traverse()
B) 在遍历之前对每个 prim 调用 prim.SetInstanceable(False)
C) 使用 Usd.PrimCompositionQuery 代替 PrimRange
D) 使用 Usd.PrimRange(stage.GetPseudoRoot(), Usd.TraverseInstanceProxies())

<details>
<summary>答案</summary>

**正确答案：D**

Usd.TraverseInstanceProxies() 是一个谓词，它允许 PrimRange 进入被实例化的 prototype，并在遍历中把其中内容呈现为 instance proxy prim。

**其他选项错误的原因：**
- 用同样的谓词重复调用同一个遍历，仍然只会得到相同的过滤结果
- 把每个 prim 都去实例化既违背了实例化的初衷，在大规模场景中也具破坏性且代价高昂，对只读检查而言完全没必要
- PrimCompositionQuery 用于检查单个 prim 的组合弧，并不是面向整个 stage 的遍历机制

> ⚠️ 考试中经常出错——请仔细阅读各选项。

</details>

---

**Q6.** 某个 stage 中有 root.usd（最强）以及一个较弱的 sublayer override.usd。你希望后续的创作调用（例如 prim.CreateAttribute().Set()）写入 override.usd。哪个调用可以实现这一点？

A) stage.GetRootLayer().SetSubLayerPaths(["override.usd"])
B) stage.SetEditTarget(Usd.EditTarget(overrideLayer))
C) prim.GetPrimStack()[-1].layer = overrideLayer
D) Sdf.Layer.FindOrOpen("override.usd").SetDefaultPrim(...)

<details>
<summary>答案</summary>

**正确答案：B**

用 stage 的 layer 栈中已有的 layer 构造 Usd.EditTarget(layer)，再传给 stage.SetEditTarget()，即可把所有后续的创作调用都导向该 layer。

**其他选项错误的原因：**
- SetSubLayerPaths 只会改变包含哪些 layer 以及它们的强度顺序，并不能指定新的创作目标
- GetPrimStack() 返回的 PrimStack 条目是只读的检查用对象，无法通过重新赋值来改变创作去向
- SetDefaultPrim 只用于标记该 layer 的 default prim，对 edit target 没有任何影响

</details>

---

**Q7.** 你需要以编程方式判断某个 prim 胜出的意见究竟来自引用弧还是来自本地 layer 的直接覆盖，以便排查异常值。哪个 API 是专为此设计的？

A) 仅使用 prim.GetPrimStack()，不做进一步处理
B) Usd.PrimCompositionQuery(prim).GetCompositionArcs()
C) stage.GetEditTarget().GetLayer()
D) Usd.PrimRange(prim).IsPostVisit()

<details>
<summary>答案</summary>

**正确答案：B**

Usd.PrimCompositionQuery(prim).GetCompositionArcs() 返回 UsdCompositionArc 对象，明确描述每个参与贡献的弧的类型（reference、payload、inherit、variant、specialize 等）以及来源 layer/路径——这正是完成该检查的正确工具。

**其他选项错误的原因：**
- PrimStack 给出的是有序的 PrimSpec 列表，但若不做额外交叉比对，就无法标明每个条目来自哪种弧
- GetEditTarget().GetLayer() 只能揭示新的创作会写到哪里，而无法说明已有意见来自何处
- IsPostVisit() 是 PrimRange 的迭代顺序标志，与组合弧检查无关

</details>

---

**Q8.** 默认情况下，不带参数调用 stage.Traverse() 会跳过下列哪一项？

A) kind 为 "component" 的 prim
B) 身上创作了 variant set 的 prim
C) inactive 的 prim，以及纯粹是 "over" 的 prim（未定义，没有任何 defining spec）
D) 带有 payload 弧的 prim

<details>
<summary>答案</summary>

**正确答案：C**

默认谓词（UsdPrimDefaultPredicate）要求 IsActive && IsDefined && IsLoaded && !IsAbstract，因此 inactive 的 prim 和只有 "over" 而未定义的 prim 会被默认遍历排除。

**其他选项错误的原因：**
- kind 元数据与默认遍历谓词无关
- 是否创作了 variant set 不影响 prim 能否通过默认谓词
- 仅仅存在 payload 弧本身并不会排除某个 prim；排除与否取决于加载状态，而不是是否存在 payload

> ⚠️ 考试中经常出错——请仔细阅读各选项。

</details>

---

---


### 第 11 章练习题


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `practice-questions/chapter-11-questions.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/practice-questions/chapter-11-questions.md) · 语言：英文原文 · 中译版



## 第 11 章：使用 usdview 调试组合，以及大规模场景优化 — 练习题

**Q1.** 在 usdview 中，一个在交互式视口里显示正常的 mesh 却从最终的生产渲染中消失了。Composition 标签页确认该 prim 在整个 layer 栈中既未被覆盖也未被隐藏。最可能的原因是什么？

A) 该 prim 的 purpose 属性被设为 proxy
B) 该 prim 位于未加载的 payload 内部
C) 该 prim 的 visibility 属性被设为 invisible
D) 该 prim 拥有一个没有选中项的 variant set

<details>
<summary>答案</summary>

**正确答案：A**

purpose=proxy 意味着该 prim 是用作轻量级交互替身；生产渲染器使用的 render purpose 遍历会完全跳过它，而 usdview 的默认视口默认同时显示 render 和 proxy 两种 purpose。

**其他选项错误的原因：**
- 未加载的 payload 会让该 prim 在 usdview 中同样不可见，而不仅仅是渲染中缺失
- visibility 为 invisible 会在包括视口在内的所有地方隐藏该 prim，与题述场景矛盾
- 没有选中项的 variant set 通常会回退到默认值，不会只在渲染时选择性地隐藏几何体

> ⚠️ 考试中经常出错——请仔细阅读各选项。

</details>

---

**Q2.** 某个 stage 中有一个 prim，其同一属性上同时有引用弧和 inherit 弧贡献意见。使用组合检查器的 Index 视图时，按默认的 LIVRPS 顺序，哪条弧的意见胜出？

A) 引用弧胜出，因为引用比继承更强
B) 继承弧总是胜出，因为继承是基于 class 的
C) 在 layer 中最后加入的那条弧胜出
D) specializes 弧胜出，因为它最先被求值

<details>
<summary>答案</summary>

**正确答案：A**

LIVRPS 强度顺序（Local、Inherits、Variants、References、Payloads、Specializes）中 References 强于 Inherits，因此来自引用的直接意见胜过通过继承提供的意见。

**其他选项错误的原因：**
- 在 LIVRPS 中 Inherits 比 References 弱而不是强，尽管它基于 class
- 组合强度由弧类型的顺序（LIVRPS）决定，而不是单个 prim spec 内的插入顺序
- Specializes 是 LIVRPS 中最弱的弧，而且根本不在本场景中

> ⚠️ 考试中经常出错——请仔细阅读各选项。

</details>

---

**Q3.** 某个镜头中有 50,000 个相同的铆钉道具散布在船体网格上，导致 stage 加载缓慢并占用过多内存。哪种优化策略最好？

A) 把铆钉拆成 50,000 个独立的 USD 文件，通过各自的引用加载
B) 把所有铆钉的 purpose 设为 guide，让 usdview 跳过它们
C) 在共享的 prototype 上设置 instanceable=true，把每个铆钉 prim 转换为原生实例
D) 把所有铆钉的意见移入一个最强的 sublayer

<details>
<summary>答案</summary>

**正确答案：C**

原生实例化让 Pcp 在所有实例之间共享同一个组合后的 prototype index，因此相同几何体在内存中只计算并存储一次，而不是 50,000 次——这是与 payload 并列的主要规模化手段。

**其他选项错误的原因：**
- 拆分成上千个独立文件会增加文件 I/O 和组合开销，却没有对内存做去重
- 把 purpose 设为 guide 改变的是渲染/显示可见性，而不是内存占用或加载性能，而且会错误地把铆钉从渲染中隐藏掉
- Sublayer 顺序只影响意见强度，不影响相同几何体被组合和存储的次数

</details>

---

**Q4.** 在交付之前，你需要依据 Pixar 的 ARKit 兼容 USDZ 合规规则校验交付资产。应该使用哪个工具和调用方式？

A) usdview --validate asset.usdz
B) Usd.Stage.Open(asset.usdz, validate=True)
C) usdcat --check asset.usdz
D) usdchecker --arkit asset.usdz

<details>
<summary>答案</summary>

**正确答案：D**

usdchecker 是命令行校验工具，--arkit 标志会运行 ARKit 专用的合规规则集，这是 USDZ 在 Apple 平台上交付所必需的。

**其他选项错误的原因：**
- usdview 没有 --validate 标志；它是交互式查看器，而不是校验器
- Usd.Stage.Open 不接受用于合规检查的 validate 关键字参数
- usdcat 用于以文本形式打印/转换 layer 内容，并没有 --check 合规选项

</details>

---

**Q5.** 对于动画师需要在视口中查看和选择、但绝不能出现在任何渲染输出中的绑定控制器手柄和定位器，应该赋予哪个 purpose 值？

A) default
B) guide
C) proxy
D) render

<details>
<summary>答案</summary>

**正确答案：B**

guide purpose 专用于绑定控制器、gizmo 和标注等辅助几何体——交互工作中可见，但会被生产渲染器使用的 proxy 与 render purpose 遍历双双排除。

**其他选项错误的原因：**
- default 沿用常规可见性行为，仍然会被 render purpose 遍历选中
- proxy 的用途是为繁重的渲染几何体提供轻量替身，而不是充当不可渲染的辅助对象
- render purpose 明确用于最终的高质量渲染几何体，与此处需求正好相反

> ⚠️ 考试中经常出错——请仔细阅读各选项。

</details>

---

**Q6.** 在 usdview 的 Composition 标签页中，点击 Index 里的某一条弧条目，主要能让你检查什么？

A) 该 prim 上创作的动画曲线
B) 当前渲染器中应用于该 prim 的渲染设置
C) 用于创作该 stage 的 USD schema 版本
D) 贡献意见的具体 layer 与弧，以及它在 LIVRPS 强度顺序中的位置

<details>
<summary>答案</summary>

**正确答案：D**

Index 面板会枚举对某个 prim 有贡献的每一条组合弧，你可以选中其中一条来查看其来源 layer、弧类型和强度位置——这是追踪某条意见为何胜出的核心机制。

**其他选项错误的原因：**
- 动画曲线要在 Property/Value 面板或图编辑器中查看，而不是在组合弧索引中
- 渲染设置位于 render delegate/RenderSettings prim 上，与组合弧检查无关
- Schema 版本是 stage 级别的元数据，会在其他位置显示，不是逐弧的组合细节

</details>

---

**Q7.** 某工作室希望完整的城市环境 stage 保持轻量、易于打开，只为当前处于相机视野内的街区拉取高分辨率的建筑几何体。对于这一工作流，哪个机制是主要杠杆？

A) 在 LOD 表示之间切换的 variant set
B) 覆盖建筑材质的 specializes 弧
C) 用于隐藏远处建筑的 sublayer 顺序
D) Payload，使不需要的建筑街区在被显式请求之前保持未加载

<details>
<summary>答案</summary>

**正确答案：D**

Payload 明确就是为延迟加载而设计的机制：它们的内容在被加载之前不参与组合，因此成为在规模化场景中控制哪些数据被拉入内存的主要工具。

**其他选项错误的原因：**
- Variant set 改变的是选中了哪一种表示，但并不像 payload 对整个分支那样天然地延迟未选中变体的加载
- Specializes 影响的是覆盖的意见强度，而不是数据是否被加载进内存
- Sublayer 顺序只改变意见强度，并不控制某个分支的数据是否被组合或常驻内存

</details>

---

**Q8.** 在 USD 组合中，引用弧与 payload 弧的根本区别是什么？

A) 引用只支持 .usda 文件，而 payload 只支持 .usd 二进制文件
B) Payload 支持 variant set，而引用不支持
C) Payload 在被显式加载之前不参与组合，而引用始终会被组合进 stage
D) 引用可以指向多个 prim，而 payload 只能指向一个 prim

<details>
<summary>答案</summary>

**正确答案：C**

决定性的行为差异在于可加载性：payload 的目标被延迟，必须显式加载（通过 Stage.Load 或 usdview 的 Load/Unload），而被引用的内容始终是组合后 stage 的一部分。

**其他选项错误的原因：**
- 两种弧类型都与文件格式无关（.usda、.usd、.usdc）
- Variant set 既可以出现在引用引入的内容下，也可以出现在 payload 引入的内容下；这不是区分点
- 根据创作方式，两种弧都可以指向单个或多个 prim/layer；目标数量并非核心区别

> ⚠️ 考试中经常出错——请仔细阅读各选项。

</details>

---

---


### 第 12 章练习题


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `practice-questions/chapter-12-questions.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/practice-questions/chapter-12-questions.md) · 语言：英文原文 · 中译版



## 第 12 章：完整模拟考试与时间管理策略 — 练习题

**Q1.** 某个 prim 有三条影响其显示颜色的意见：在最强 layer 中直接创作在 prim 上的本地意见（红色）、继承自 class 的意见（绿色），以及通过引用某个资产引入的意见——其中被引用的 layer 局部设置了颜色（蓝色）。组合后的 stage 显示什么颜色？

A) 红色
B) 蓝色
C) 绿色
D) 与弧类型无关，最后创作的那条意见

<details>
<summary>答案</summary>

**正确答案：A**

LIVRPS 强度顺序把 Local 意见排在 Inherits、Variants、References、Payloads 和 Specializes 之上。直接创作的本地意见永远胜过任何通过更弱的弧到达的意见，无论它在那条弧内部何处被创作。

**其他选项错误的原因：**
- 蓝色是引用的意见——按 LIVRPS，引用弱于本地意见，因此永远不会覆盖更强的本地意见
- 绿色来自 Inherits，它弱于 Local 但强于 References/Payloads/Specializes——但仍然输给本地意见
- 实际创作的时间顺序与组合无关；起决定作用的只有弧在 LIVRPS 强度顺序中的位置

> ⚠️ 考试中经常出错——请仔细阅读各选项。

</details>

---

**Q2.** 你需要用 50,000 棵树填充一片森林环境，它们共享相同的几何体，但每一棵都需要独特的位置、旋转、缩放以及按实例区分的生长阶段索引。哪种做法最符合这一需求？

A) 创作 50,000 个各自带有独立几何体的唯一 prim
B) 通过各自的引用把每个树 prim 单独标记为 instanceable=true
C) 为每棵树使用一个 VariantSet 来切换生长阶段
D) 使用一个引用了少量 prototype prim 的 UsdGeomPointInstancer，并通过其数组驱动 positions/orientations/scales/protoIndices

<details>
<summary>答案</summary>

**正确答案：D**

UsdGeomPointInstancer 专为大规模点云式实例化而设计，暴露 positions、orientations、scales 和 protoIndices 数组，以便在规模化场景中高效地按实例创作。

**其他选项错误的原因：**
- 每棵树一个唯一 prim 会毁掉实例化在内存和创作上的优势，也无法扩展到 50,000 个实例
- Instanceable 引用在层级去重方面很高效，但不像 PointInstancer 那样原生提供按实例的变换/属性数组
- VariantSet 用于在离散资产/外观之间切换，而不是按实例创作变换

</details>

---

**Q3.** 某资产被引用的 layer 定义了名为 'material' 的 variantSet，默认选中 'chrome'。组合中更强的一个下游 layer 为同一个 variantSet 创作了显式的变体选择意见 'rust'。最终组合出的材质变体是什么？

A) Chrome，因为引用定义了默认值
B) 这是组合错误，需要手动解决
C) Rust，因为更强 layer 的意见覆盖了被引用的默认选择
D) 取决于运行时 layer 的加载顺序

<details>
<summary>答案</summary>

**正确答案：C**

变体选择就是普通意见，遵循标准的强度顺序：在更强 layer 中创作的意见总会覆盖更弱的意见，包括被引用资产内部设置的默认值。

**其他选项错误的原因：**
- Chrome 只是没有更强意见时的回退项——而这里存在更强的意见
- 这是标准且定义明确的组合行为，而不是需要手动解决的冲突
- 磁盘上文件的加载顺序不会影响 LIVRPS 强度顺序，后者由弧类型和 layer 栈中的位置决定

> ⚠️ 考试中经常出错——请仔细阅读各选项。

</details>

---

**Q4.** 哪个 UsdGeom schema 是专为大规模、非层级的实例化设计的，其中每个点的缩放、朝向和 prototype 选择必须以数组形式创作？

A) UsdGeomXform
B) UsdGeomScope
C) UsdGeomModelAPI
D) UsdGeomPointInstancer

<details>
<summary>答案</summary>

**正确答案：D**

UsdGeomPointInstancer 把 positions、orientations、scales 和 protoIndices 暴露为数组属性，专为高效散布大量实例而设计。

**其他选项错误的原因：**
- UsdGeomXform 只定义一个可变换的分组 prim；它没有与实例化相关的属性
- UsdGeomScope 是不可变换的分组构造，不带任何实例化语义
- UsdGeomModelAPI 应用 model kind 元数据（component/group/assembly），与点实例化无关

</details>

---

**Q5.** 你正在编写一个 Python 脚本，要在许多 prim 上创作成千上万条属性值覆盖，并且希望避免每次编辑都触发一次 stage 的重新组合通知。哪种写法是正确的？

A) 每次 SetAttribute 调用后都调用 stage.Save()
B) 通过 Usd API 创作时，把这批编辑包在 `with Sdf.ChangeBlock():` 上下文里
C) 在紧凑循环中调用 Usd.Prim.GetAttribute，不做任何批处理
D) 完全不涉及 Usd.Stage，直接在新建的 Sdf.Layer 上创作每一处编辑

<details>
<summary>答案</summary>

**正确答案：B**

Sdf.ChangeBlock 会把组合变更通知推迟到代码块退出时，让大量通过 Usd API 的编辑作为一次批量通知被高效创作，而不是每次编辑都通知一次。

**其他选项错误的原因：**
- 每次编辑后都保存是代价高昂的 I/O 操作，对批处理内存中的重新组合通知毫无帮助
- 循环中不做批处理的编辑每次调用都会触发完整的通知/重新组合周期，这正是 ChangeBlock 要避免的效率问题
- 绕过 Usd.Stage 会失去 schema 感知的校验和便捷性，而考试期望你在创作流程中使用它们

</details>

---

**Q6.** 在给某个 prim 添加了对资产的引用之后，哪个 Python 调用能正确地将其标记为 instanceable？

A) stage.SetInstanceable(prim, True)
B) prim.SetInstanceable("true")
C) prim.SetInstanceable(True)
D) prim.GetVariantSets().SetInstanceable(True)

<details>
<summary>答案</summary>

**正确答案：C**

Usd.Prim.SetInstanceable(bool) 是 prim 对象自身的正确方法，接受一个 Python 布尔值。

**其他选项错误的原因：**
- Usd.Stage 没有 SetInstanceable 方法——instanceable 是设置在 Usd.Prim 上的元数据
- 该方法期望的是 Python bool，而不是字符串 "true"；传入字符串是常见的脚本错误，会悄无声息地行为异常
- VariantSet 与 instanceable 标志毫无关系；后者是 prim 上的元数据字段，而不是变体机制

> ⚠️ 考试中经常出错——请仔细阅读各选项。

</details>

---

**Q7.** 考试共有 65 道题、限时 90 分钟，你希望最后预留 15 分钟用于复查标记过的题目。第一遍作答时，每道题大致应分配多少时间？

A) 约 69 秒
B) 约 50 秒
C) 约 90 秒
D) 约 120 秒

<details>
<summary>答案</summary>

**正确答案：A**

（90 − 15）分钟 ÷ 65 题 = 75 ÷ 65 ≈ 1.15 分钟 ≈ 第一遍作答时每题约 69 秒。

**其他选项错误的原因：**
- 50 秒分配的时间偏少，并且假设预留了比 15 分钟更长的复查缓冲
- 90 秒忽略了 15 分钟的复查缓冲，仅第一遍就会用完整个时间窗口
- 每题 120 秒意味着 65 道题大约需要 130 分钟，远远超出 90 分钟的时间窗口

> ⚠️ 考试中经常出错——请仔细阅读各选项。

</details>

---

**Q8.** 哪项陈述正确区分了 USD payload 与 USD reference？

A) 在组合强度顺序中，payload 比 reference 更强
B) payload 与 reference 之间没有功能差异
C) payload 只能指向同一 layer 内的 prim，而 reference 可以指向外部文件
D) payload 的行为类似 reference，但被排除在默认加载集合之外，并且可以在运行时显式加载/卸载以提升性能

<details>
<summary>答案</summary>

**正确答案：D**

Payload 的组合方式与 reference 相同，但默认被延迟处理，让工具可以在运行时选择性地加载/卸载重量级子树——这是大型场景的关键性能机制。

**其他选项错误的原因：**
- 在 LIVRPS 顺序中，References 比 Payloads 更强，而不是相反
- 两者在默认加载行为和运行时控制上有着实质差异，这正是两种弧都存在的原因
- 两种弧都可以指向外部文件或同一 layer 内的 prim；区分点在于加载集合行为，而不是目标范围

</details>

---

---


### 答案解析 —— 模拟测试 1


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `practice-tests/answer-key-1.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/practice-tests/answer-key-1.md) · 语言：英文原文 · 中译版



# 答案解析 —— 模拟测试 1

**Q1. 正确答案：A**

LIVRPS 代表 Local、Inherits、VariantSets、References、Payload、Specializes，按强度递减排列。Inherits 位于 Local 与 VariantSets 之间，因此它的意见（opinion）胜过变体集的意见，但弱于本地的意见。

---

**Q2. 正确答案：B**

关系（relationship）是 USD 中表达图元（prim）之间（以及属性之间）定向链接的原生机制，而材质绑定（通过 UsdShadeMaterialBindingAPI）正是实现为一条指向 Material 图元路径的关系，从而支持高效的图遍历以及感知合成（composition-aware）的解析。

---

**Q3. 正确答案：C**

USD 默认的时间采样行为是：对于早于第一个采样或晚于最后一个采样的时刻，保持最近一个已创作（authored）采样的值——它从不做外推。因此在第 5 帧查询（早于第 10 帧的第一个采样）时，会原样返回第 10 帧的值。

---

**Q4. 正确答案：B**

Primvar（primitive variable，图元变量）是具有特殊命名空间和继承语义的属性：在祖先图元上创作的 primvar，会被那些未创作自身意见的后代 gprim 继承，因此非常适合用于层叠的着色与几何变量，例如 displayColor 或 displayOpacity。

---

**Q5. 正确答案：A**

USD 的模型类型（model kind）层级约定把 'component' 视为叶子级的模型类型——component 表示自包含的资产，不应再有下级的模型类型子节点。带有自身模型几何体的嵌套子节点通常会被赋予诸如 'subcomponent' 这样的非模型类型，以表明它属于该 component 的内部结构，而本身并不是层级中独立的模型。

---

**Q6. 正确答案：D**

UsdCollectionAPI 正是为这种用例设计的：它是一种多重应用（multi-apply）的 API schema，可以非破坏性地应用到任意图元上，定义一个或多个具名集合，并通过 includes/excludes 规则引用任意目标图元（任何类型均可）——而不改变这些目标图元自身的类型。

---

**Q7. 正确答案：A**

在 LIVRPS 合成强度排序中，图元上的 Local 意见始终最强，其后依次是 Inherits、VariantSets、References、Payloads 和 Specializes。引用层中直接的本地覆盖（override）总会胜过经由引用弧（reference arc）传来的意见，与创作顺序无关。

---

**Q8. 正确答案：C**

'faceVarying' 插值会为每个面的每个顶点存储一个值，从而允许同一个网格顶点根据所属面不同而取不同值——这正是硬边、按面-顶点法线所需要的。

---

**Q9. 正确答案：D**

LIVRPS 排序把 Local 意见置于强度层级的顶端——直接创作在图元自身层栈（layer stack）中的意见，总胜过经由任何弧（inherits、variants、references、payloads、specializes）传来的意见。

---

**Q10. 正确答案：D**

变体集（variant set）正是为这种用例设计的：它们定义具名且互斥的意见块（变体），下游层可以通过变体选择以非破坏性方式从中挑选，无需改动原始资产。

---

**Q11. 正确答案：A**

LIVRPS 代表 Local、Inherits、Variants、References、Payloads、Specializes——Specializes 排在最后，是最弱的弧，通常用于创作基础的「资产结构」层级，其意见设计成可被引用或本地编辑轻松覆盖。

---

**Q12. 正确答案：B**

Payload 正是为延迟加载而显式设计的弧——重型资产可以在结构层面被合成进 stage，但保持未加载状态，直到艺术家或某个流水线步骤显式请求加载；这对于包含上亿多边形的场景至关重要。

---

**Q13. 正确答案：B**

Inherits 是基于类的合成弧，在 LIVRPS 中位置接近顶端（强于 variants、references、payloads 和 specializes），意味着继承而来的类意见可以覆盖经由引用传来的意见，这正符合绑定师（rigger）的需求。

---

**Q14. 正确答案：A**

「显式（explicit）」的列表编辑操作会在层栈的该位置完全替换合成后的列表——它不会与更弱层针对同一列表的 add/prepend/append/delete 操作合并，这不同于 prepend 或 append，后两者会与更弱的意见以相加方式合成。

---

**Q15. 正确答案：C**

LIVRPS 代表 Local、Inherits、VariantSets、References、Payloads、Specializes——顺序即为强度顺序。在不存在本地意见的情况下，inherits 弧（来自 /_class_Robot）的强度高于 reference 弧，因此继承而来的红色值胜出。

---

**Q16. 正确答案：A**

变体集是专门为暴露少量具名、互斥的替代方案（例如 LOD 层级）而打造的，下游消费者只需借助一小段元数据即可完成选择，而无需改动源资产。

---

**Q17. 正确答案：B**

列表编辑会把 prepend 的条目合成在原有显式条目之前，把 append 的条目合成在其之后：prepend 项（assetB）在前，然后是原有的显式列表（assetA），最后是 append 项（assetC）——最终得到 assetB、assetA、assetC。

---

**Q18. 正确答案：D**

PointInstancer 专为大量共享几何体的实例而设计，把逐实例的变换、缩放和朝向以紧凑数组的形式存放在单个图元上，从而带来极低的逐实例开销以及该规模下的快速加载。

---

**Q19. 正确答案：C**

当 instanceable=true 时，被实例化子树下的图元是只读的实例代理（instance proxy）；在该特定图元上设置 instanceable=false 会将其从原型共享中移除，使其成为唯一且可直接编辑的图元，从而可以创作覆盖（override）。

---

**Q20. 正确答案：B**

把资产的内部内容封装在单个 defaultPrim 之下，可以提供稳定、无歧义的引用目标和干净的接口，使外部层只覆盖暴露出来的属性和变体，而不必触碰内部结构。

---

**Q21. 正确答案：B**

'instanceable' 是触发原生实例化的布尔图元元数据；当它为 true 且该图元的合成弧与另一个可实例化图元相匹配时，USD 会把它们聚合到同一个由内部管理的共享原型之下。

---

**Q22. 正确答案：D**

当引用省略了显式的图元路径时，USD 会将其解析到该资产创作出的 defaultPrim，从而让流水线仅凭资产路径就能聚合资产，而不受各供应商内部根图元命名方式的影响。

---

**Q23. 正确答案：A**

原生实例化把每个实例保留为层级中的完整图元，可针对个别编辑选择退出共享（instanceable=false）；而 PointInstancer 则把实例表示为数组驱动的点（位置、朝向、缩放、id），没有可寻址的逐实例图元层级——这是以可编辑性换取规模。

---

**Q24. 正确答案：B**

实例代理仅用于读取访问（遍历、查询），不能直接接收创作的意见。若要让某个被实例化的图元拥有独有属性，就必须在该图元上设置 instanceable = false，将其从实例池中移除；这样它可以合成自己的本地意见（例如材质覆盖），而其他实例继续不受影响地共享原型。

---

**Q25. 正确答案：B**

.usdz 是一种未压缩（zip-stored）的归档格式，专门用于把一个 USD stage 及其引用的全部纹理和依赖打包进单个可移植、自包含的文件，这正是 AR Quick Look 等平台所要求的。

---

**Q26. 正确答案：D**

缺少显式锚定（"./"、"../" 或绝对路径）的路径，会被 USD 的资产解析系统视作搜索路径，并通过可插拔的 Asset Resolver（Ar）进行解析；它会先查阅搜索路径规则，然后才回退到锚定层所在的目录。

---

**Q27. 正确答案：C**

Alembic 是专为烘焙几何缓存打造的，USD 的 Alembic 插件能够以很高的保真度引用 .abc 的点/拓扑数据；不过 Alembic 不携带 USD 风格的程序化着色网络，这与题目所述可接受有损着色的前提相符。

---

**Q28. 正确答案：A**

USDZ 被设计为完全自包含的可移植归档；其中每一个资产引用都必须是相对路径，且能解析到同一包内捆绑的文件，因此无论机器或文件系统如何都能一致工作。

---

**Q29. 正确答案：D**

.usd 有意保持格式无关——其底层数据既可以是文本（ASCII），也可以是二进制（crate）；而 .usda 和 .usdc 则是明确固定为 ASCII 或 crate 编码的扩展名。

---

**Q30. 正确答案：C**

Omniverse Connectors 可插入各类 DCC 应用，并与 Nucleus 服务器的 Live Session 功能配合，在已连接的客户端之间提供 USD 编辑的实时双向同步。

---

**Q31. 正确答案：C**

Stage.Traverse() 默认使用 Usd.PrimDefaultPredicate，它已经排除了 inactive、undefined、unloaded 和 abstract 图元，同时仍包含通过 references/payloads 合成进来的图元——这正是题目所描述的过滤行为。

---

**Q32. 正确答案：D**

OverridePrim() 会在当前编辑目标（edit target）上创建一个无类型的 'over' 图元规格（prim spec），这是在不声明具体类型的前提下添加覆盖意见（例如 visibility）的正确创作模式。

---

**Q33. 正确答案：C**

传入显式的数值 Usd.TimeCode(24.0) 会在第 24 帧创作一个时间采样，而不会触碰已有的默认值（在 Usd.TimeCode.Default() 处创作的）。

---

**Q34. 正确答案：B**

SetTargets() 会在当前编辑目标上创作一个显式的目标列表，替换掉合成后的目标列表，使最终只剩新的材质路径，满足「完全替换」的要求。

---

**Q35. 正确答案：D**

层（Layer）保存原始的、未合成的意见，并直接对应文件（.usda/.usdc/.usd）；而 Stage 由 USD 的合成引擎构建，把根层以及任何子层、引用、payload 等组合成单一可查询的、已合成的图元与属性视图。

---

**Q36. 正确答案：C**

渲染委托（Render Delegate，例如 HdStorm，或自定义的 HdRenderDelegate 插件）会取出 Hydra 渲染索引中保存的、与渲染器无关的场景数据，并将其转换为面向特定渲染后端（如 RTX 或 OpenGL 渲染器）的绘制调用/资源。

---

**Q37. 正确答案：B**

Sdf.ChangeBlock 会把全部变更通知推迟到退出该代码块时，并合并处理，因此监听者收到的是一次批量通知，而不是每次编辑各收到一次——这是官方文档中用于提升 Sdf 层批量创作性能的模式。

---

**Q38. 正确答案：A**

Usd.TraverseInstanceProxies() 是指示遍历进入可实例化子树、并在其真实 stage 路径上产出实例代理图元的谓词，这是检查逐实例创作意见所必需的。

---

**Q39. 正确答案：C**

可实例化图元为效率共享同一个合成后的原型，因此 USD 合成会丢弃直接创作在实例命名空间路径（即实例代理）上、否则会导致各实例相异的意见；变更必须针对共享原型进行，或者必须先将该图元去实例化。

---

**Q40. 正确答案：D**

Payload 专门用于延迟加载重型场景描述；以未加载方式打开 stage（或使用 population mask 限定哪些图元会被加载）可保持启动速度，而图元可以在用户导航到它们时按需加载。

---

**Q41. 正确答案：C**

'proxy' 用途是为简化的替身几何体准备的，例如碰撞网格或低分辨率表示体，用于交互式操作与操控，但会被排除在最终成图渲染之外。

---

**Q42. 正确答案：A**

UsdGeomPointInstancer 专为通过紧凑的逐实例属性数组（位置、朝向、缩放、原型索引）高效渲染海量实例而打造，因此它是诸如散布植被等场景下的标准可扩展方案。

---

**Q43. 正确答案：D**

'guide' 用途专留给辅助性或示意性的几何体，用来帮助艺术家（例如相机视锥或操纵器控件），默认既不参与交互显示也不参与渲染，除非在查看器中显式开启。

---

**Q44. 正确答案：A**

在 USD 中，相对资产路径会由资产解析算法锚定到创作它们的层上；若移动根层时未保持相对目录结构，这种锚定就会失效，因此修复办法是纠正相对路径，或改用不依赖层物理位置的、基于 resolver（解析器）的方案。

---

---


### 答案解析 — 模拟测试 2


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `practice-tests/answer-key-2.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/practice-tests/answer-key-2.md) · 语言：英文原文 · 中译版



# 答案解析 — 模拟测试 2

**Q1. 正确答案：D**

USD 的值解析（value resolution）会在整个 layer stack（层栈）中挑出为该属性创作了任何 opinion（default 或 time samples）的最强 layer；如果这个最强 layer 拥有 time samples，就会使用它们（并进行插值），而较弱 layer 的默认值会被完全忽略，而不是与之合并。

---

**Q2. 正确答案：B**

LIVRPS 代表 Local、Inherits、VariantSets、References、Payloads、Specializes，按强度从高到低排列，因此 Payloads 正好位于 References 与 Specializes 之间。

---

**Q3. 正确答案：A**

faceVarying 插值为每个面-顶点（每个面的每个角）创作一个值，使共享拓扑顶点的相邻面可以拥有各自独立的值 —— 这是硬边法线（hard-edged normals）所必需的。

---

**Q4. 正确答案：B**

USD 的模型层级约定把 component 视为叶子级的 model kind，代表不可再分的资产；component 之下不应再包含 group/component 结构，因此把 group 嵌套在 component 之下违反了该层级约定。

---

**Q5. 正确答案：B**

UsdCollectionAPI 是一个 multi-apply API schema，这意味着只要每次 apply 都通过 apiSchemas listOp metadata 中唯一的 instance name 区分开，它就可以在同一个 prim（图元）上被 apply 多次。

---

**Q6. 正确答案：C**

relationship 是无类型、非随时间变化的命名空间对象，用于引用场景图中的其它对象（例如材质绑定）；而 connection 是类型化属性上的 metadata，把该属性的值解析重定向到另一个属性，常用于着色网络（shading networks）。

---

**Q7. 正确答案：C**

USD 的值解析严格遵循「layer 强度优先」原则：它会找到为该属性创作了任何 opinion（default 或 time samples）的最强 layer，并只使用该 opinion。如果这个最强 layer 的 opinion 只是一个普通 default，那么所有时间都返回该默认值，较弱 layer 的 time samples 永远不会被查询，哪怕它们确实随时间变化。

---

**Q8. 正确答案：B**

multi-apply API schema 会以 '<SchemaName>:<instanceName>' 的格式记录在 apiSchemas listOp 中，例如 'CollectionAPI:renderLights'。这个 instance name 同时用作该 schema 属性（property）的命名空间前缀（例如 collection:renderLights:includes），从而使同一 API schema 的多个独立实例可以共存于一个 prim 上。

---

**Q9. 正确答案：C**

LIVRPS 按强度从高到低把 arc 排列为 Local、Inherits、Variants、References、Payloads、Specializes。由于两个 layer 都没有直接在 Chair 自身上创作 local opinion，继承而来的 opinion（5.0）仅因为 Inherits 排在 References 之前，就胜过被引用而来的 opinion（2.0）。

---

**Q10. 正确答案：D**

普通的（无 op 的）列表赋值会被视为该 layer stack 中此位置上的一个 explicit 列表；更强的 layer 仍可以在它之前 prepend 或在它之后 append。prepend 项按强度顺序插入到 explicit 基础列表之前，得到 [C.usd, A.usd, B.usd]，并保留较弱 layer 自身的内部顺序。

---

**Q11. 正确答案：A**

在 LIVRPS 中，References 的强度高于 Payloads（Local、Inherits、Variants、References、Payloads、Specializes）。无论加载时机如何，一旦两者都被加载，reference 的 opinion（8）就仅凭 arc 类型强度胜过 payload 的 opinion（6）。

---

**Q12. 正确答案：A**

Specializes 是 LIVRPS 中最弱的 arc —— 比 References 和 Payloads 都弱 —— 因此来自这些 arc 的任何 opinion 总会覆盖它，这正是题目所要求的行为。与 inherits 一样，它仍然会实时组合来自目标 prim 的 opinions（而不是静态拷贝），因此它是回退基线／默认模式（fallback base/default patterns）的正确选择。

---

**Q13. 正确答案：D**

variant selection 只是普通的 metadata opinion，遵循常规的 LIVRPS／local layer-stack 强度规则。session layer 位于 root layer 之上、是最强的 sublayer，因此它的选择（"damaged"）胜过 root layer 的默认选择（"pristine"）。

---

**Q14. 正确答案：D**

Payloads 会推迟整个目标子树的组合。在未加载期间，该子树中的任何内容 —— 包括 Building reference 这类嵌套的组合 arc —— 都不会被组合到 stage 上。只有当 payload arc 本身被加载时，才会真正发生加载。

---

**Q15. 正确答案：C**

USD 的 LIVRPS 强度排序为 Local > Inherits > VariantSets > References > Payloads > Specializes。由于不存在 local opinion，接下来最强的 arc 是 Inherits，因此 class prim 上的红色 opinion 胜过 variant、reference 和 payload 的 opinions。

---

**Q16. 正确答案：C**

当 layer stack 中的多个 layer 都对同一个列表（例如 references）prepend 项目时，USD 会组合该列表，使最强 layer prepend 的项目最靠近最终列表的前端。root layer 比 sublayer 更强，因此 assetX（root 的 prepend）排在 assetY（sublayer 的 prepend）之前，得到 [assetX, assetY]。

---

**Q17. 正确答案：B**

Payloads 正是为延迟加载而专门设计的 arc —— 组合后的资产会保持未加载状态，直到客户端显式发出 Load，从而满足需求 1。把用于照明的 variant set 嵌套在该 payload 资产内部，则允许下游使用者在自己 layer 中创作非破坏性的 variant selection opinion 来选择 'Day' 或 'Night'，而无需编辑源文件，从而满足需求 2。

---

**Q18. 正确答案：C**

instance proxy 在内存中共享同一个组合后的 prototype；若要让某个实例创作的意见（例如独特的 shader 颜色）产生差异，必须在其引用 prim 上设置 instanceable=false，把该 prim 排除在 instanceable 分组之外。这样仅为该实例创建出一棵唯一、可独立编辑的子树，而其它实例继续共享 prototype 及其 GPU／内存收益。

---

**Q19. 正确答案：C**

标准的 OpenUSD 资产接口模式把轻量、始终加载的接口意见（kind、variantSets、purpose）保留在资产根 prim 上，同时把昂贵的几何体 payload 推迟到 payload arc 之后。使用者可以打开资产、检查／切换变体、并理解其接口，而完全不必加载被 payload 的网格 —— 这对大规模装配体的扩展至关重要。

---

**Q20. 正确答案：B**

PointInstancer 上每一个逐实例数组（positions、orientations、scales、protoIndices、ids，以及存在时的 velocities）都必须与实例总数等长，并按下标一一对应。protoIndices 的值用于索引（数量少得多的）prototypes relationship，以决定 200,000 个实例各自使用 4 个 prototype 中的哪一个；scales 则提供每个实例各自的非均匀缩放系数。

---

**Q21. 正确答案：A**

class prim 与 'inherits' 组合 arc 配合使用，是在众多 prim 之间共享同一组 override opinions 的 USD 标准机制。只需编辑一次 class prim，改动就会立即传播到每一个继承它的建筑上，既没有重复数据，也只有一个集中可编辑的唯一真源。

---

**Q22. 正确答案：A**

PointInstancer 专门用于通过紧凑的索引数组来处理海量重复几何体，而不是为每个实例在场景图中生成一个 prim。这样可以避免原生（prototype）instancing 在每个被实例化 reference 上仍然要付出的逐实例 prim／遍历开销，因此在数千万实例的规模上，point instancing 是正确的选择。

---

**Q23. 正确答案：D**

USD 通过比较每个 instanceable prim 的完整组合结果来确定 prototype 分组。在每个实例根上创作不同的 variantSelection 是一种普通的、持久的 opinion（并不限于 session layer），会让 USD 自动把这 10,000 辆车按唯一车漆颜色的数量划分成对应数量的不同 prototype —— 同色车辆之间依然共享几何体，而不必强制完全解除实例化。

---

**Q24. 正确答案：A**

PointInstancer 定义了 invisibleIds 属性，专门用于按索引抑制单个实例的渲染，无需改动 positions、orientations、scales 或 protoIndices 数组，也不会破坏实例化或需要修改 prototype。它是官方认可的非破坏性逐实例可见性控制机制。

---

**Q25. 正确答案：D**

USDZ 要求每个被引用的文件都解析为相对于包的路径，不能有绝对路径，也不能有位于归档之外的内容。像 Alembic cache 这类非 USD 的外部引用，必须本地化／转换成 USD 内容并打包进归档内部，而不能留作外部依赖。

---

**Q26. 正确答案：A**

.usd 是通用的、与格式无关的扩展名。读取器通过嗅探文件的 magic bytes/header 来判断内容是文本（usda 风格）还是二进制 crate（usdc 风格）；.usda 和 .usdc 扩展名只是让人和工具能明确看出编码方式。

---

**Q27. 正确答案：C**

UsdSkel 捕捉的是绑定（rigging）的烘焙结果 —— 骨架层级、蒙皮权重、混合形状 —— 但不会捕捉 DCC 的专有过程／构建历史图谱。通过 USD 交换创作期的绑定数据时，这类信息丢失是根本性且可预期的。

---

**Q28. 正确答案：B**

Omniverse Connectors 使用 USD layer arc，把 DCC 的编辑实时同步到 Nucleus live session 中，使多位美术的编辑能在近实时的情况下以非破坏性方式合并 —— 这正是题目所描述的协作式低延迟场景。

---

**Q29. 正确答案：D**

以 ./ 或 ../ 开头的路径是锚定相对路径。默认的 ArResolver 会把它们锚定到包含该 reference 的 layer 所在目录，因此来自 /project/shots/010/ 的 ../../assets/props/chair.usd 能正确解析为 /project/assets/props/chair.usd。

---

**Q30. 正确答案：D**

USDZ 规范要求所有包内条目都必须以未压缩方式存储（不允许 DEFLATE），并对齐到固定的字节边界，这样符合规范的读取器才能直接把文件从归档中做内存映射，而无需解压或拷贝步骤。违反其中任何一条规则，即使 USD 内容本身有效，也会让符合规范的读取器无法打开。

---

**Q31. 正确答案：D**

Usd.NamespaceEditor 是专门为重命名／重新定父级／删除打造的高级、感知 stage 的 API；它会检查完整的组合后 stage，在每一个参与贡献的 layer 中编辑相关 opinions，并自动修正场景中任何引用被移动路径的 relationship 目标和属性 connection。

---

**Q32. 正确答案：D**

UsdGeom.XformCommonAPI 强制执行唯一规范的 op 排序（translate、pivot、rotateXYZ、scale、inverse-pivot），每一个符合 USD 规范的 DCC 和 Hydra 成像插件都必须能够识别它，从而保证各工具之间的解释保持一致。

---

**Q33. 正确答案：B**

调用 Set() 时不传 UsdTimeCode 参数，创作的是该属性的 *default* opinion（等价于 UsdTimeCode.Default()）。当存在 time samples 时，任何非 default 的时间查询都以 time samples 为准；默认值只有在不存在 time samples 或显式查询 Default 时间时才会返回，因此第 12 帧仍然会从 1-24 的采样区间中解析。

---

**Q34. 正确答案：C**

Usd.PrimDefaultPredicate 正是 stage.Traverse() 默认在内部应用的组合后判定条件（active && defined && loaded && !abstract），因此把它显式传给 Usd.PrimRange 会得到完全相同的遍历集合。

---

**Q35. 正确答案：B**

直接用 Sdf.Layer.FindOrOpen 打开该 layer 并查询 GetAttributeAtPath，只是操作该 layer 的原始 specs，显示的正是 contents.usda 中创作的内容，没有应用任何组合 —— 这正是孤立检查单个 layer 的意见所需要的。

---

**Q36. 正确答案：A**

由 UsdImagingDelegate 实现的 Scene Delegate 会遍历组合后的 USD stage，并使用 prim adapter 把每种受支持的 prim 类型转换成 Hydra 的 Rprim/Sprim/Bprim，再将它们填充到 render index 中，供任何 render delegate 消费。

---

**Q37. 正确答案：B**

把 Usd.EditContext 当作 Python 上下文管理器使用时，它只会在 'with' 代码块期间临时把 stage 的编辑目标切换为给定的 Sdf.Layer。块内通过 stage API 发起的所有创作调用（DefinePrim、GetAttribute().Set() 等）都会把 opinions 路由到该特定 sublayer，而在代码块退出的一刻 stage 原本的编辑目标会被自动恢复 —— 即使过程中抛出异常也是如此。这是管线工具中进行作用域化创作（scoped authoring）的惯用且异常安全的写法。

---

**Q38. 正确答案：A**

UsdGeom.PrimvarsAPI.CreatePrimvar 会在必需的 'primvars:' 命名空间下创作该属性，并允许你显式声明插值 token。UsdGeom.Tokens.faceVarying 正确表示每个面-顶点一个值，与题述的数据布局一致；而没有指定 elementSize 的普通 FloatArray 会按预期为每个元素提供一个标量 float —— 这正是 Hydra render delegate 读取索引化／插值 primvar 数据时所期望的。

---

**Q39. 正确答案：C**

LIVRPS 强度排序把 Local opinion 放在最强位置，先于 Inherits、Variants、References、Payloads 和 Specializes 求值；因此无论那些 arc 包含什么，local layer stack 中直接创作在该 prim 上的 opinion 总是胜过通过 inherits、references 或 specializes arc 传入的 opinions。

---

**Q40. 正确答案：A**

Purpose 只是一个过滤提示；具体纳入哪些 purpose，由消费该数据的渲染通道／渲染设置在计算要绘制哪些 imageable prim 时指定。渲染通道通常默认为 [default, render]；如果该列表中包含 guide（或 proxy）purpose，guide/proxy 几何体就会被合成进最终图像。

---

**Q41. 正确答案：B**

Payloads 正是为延迟／可选加载而设计的组合 arc —— 与 references 不同，打开 stage 时 payload 目标默认不会被加载，并且可以按 prim 或通过 UsdStagePopulationMask/load rules 加载／卸载。把大型可选资产从 references 改为 payloads，意味着 stage 打开很快，只有需要时才按需加载相应子树。

---

**Q42. 正确答案：C**

variant selection 会作为实例组合过程的一部分被解析，早于 instancing key 的计算，因此在其它方面完全相同的 instanceable prim 上设置不同的 variant selection，USD 仍能把解析后选择相同的实例归组到共同的 prototype —— 既实现了逐实例的变化，又保持了实例化的效率。

---

**Q43. 正确答案：A**

UsdStagePopulationMask 限制组合过程中被填充的 prim 路径 —— 掩码之外的一切（且不是被掩码路径的祖先）根本不会被组合。这是收窄超大 stage 范围最高效的方式，并且与 load rules（管辖已填充 prim 下的 payload 加载）和 layer muting（影响哪些 opinions 参与贡献，而非哪些 prim 被填充）不同。

---

---


### 模拟测试 1：NCP-OUSD：NVIDIA OpenUSD 开发认证备考


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `practice-tests/practice-test-1.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/practice-tests/practice-test-1.md) · 语言：英文原文 · 中译版



# 模拟测试 1：NCP-OUSD：NVIDIA OpenUSD 开发认证备考

- **题目数量：** 44
- **时间限制：** 90 分钟
- **及格分数：** 70%%

> 答案位于 `answer-key-1.md`。请在 `score-tracker.md` 中记录成绩。

---

**Q1.** 根据 USD 的 LIVRPS 组合强度排序，哪条 arc 产生的 opinions 强于 Variant Sets，但弱于 Local（直接）opinions？

A) Inherits
B) References
C) Payload
D) Specializes

---

**Q2.** 你需要把一个 Mesh prim 绑定到一个 Material prim，使目标可以指向场景图中其它位置的任意 prim 路径，并且渲染器能够高效地解析该绑定。应该用哪种 USD 结构来创作这个绑定？

A) 一个自定义 string 属性，以文本形式保存 material 的路径
B) Mesh 上的一个 relationship，指向 Material prim 的路径
C) 一个在硬编码的 material prim 之间切换的 variant set
D) 一个名为 'material' 的 prim metadata 字段，设置为目标路径

---

**Q3.** 一个 double 类型的属性只在第 10 帧和第 20 帧创作了 time samples，并且没有配置外推。当在第 5 帧查询该属性时，USD 返回什么值？

A) 基于第 10 帧与第 20 帧之间斜率线性外推得到的值
B) 属性的默认值与第 10 帧采样之间插值得到的混合值
C) 第 10 帧创作的值（保持/钳制，因为 USD 默认不做外推）
D) 不返回任何值，因为第 5 帧超出了已创作的采样范围

---

**Q4.** 哪条陈述正确描述了 OpenUSD 中 primvars 的行为？

A) Primvars 只能在 Xform prim 上创作，在 Mesh 或 Sphere 之类的 Gprim 上无效。
B) 在某个 prim 上创作的 Primvars 会被命名空间下的后代几何体继承（除非被覆盖），使 displayColor 之类的值能够向下级联。
C) Primvars 必须始终使用 'constant' 插值，不能按顶点或按面变化。
D) Primvars 是一种专门的关系类型，仅用于纹理绑定。

---

**Q5.** 在正确创作的 USD 资产中，发现某个 kind 为 'component' 的 prim 下还有一个同样被指定为 'component' 的子 prim。这说明了什么？该子 prim 的 kind 通常应该是什么？

A) 这违反了模型层级约定，因为 component 本应是叶子模型；该子 prim 通常应使用非模型的 kind，例如 'subcomponent'，而不是 'component'。
B) 这是有效的；component 的设计初衷就是可以任意深度地嵌套，以表示子装配体。
C) 这仅违反命名约定；该子 prim 应当改为指定 kind 'assembly'，以反映它位于 component 之下的位置。
D) Kind metadata 对模型层级的有效性没有任何影响，因此没有违反任何规则。

---

**Q6.** 某条流水线需要把 prim 的任意组合——网格、灯光和相机——归入命名集合，以便在下游工具中进行选择性禁用，而不改变其中任何 prim 的底层类型。哪种 schema 方案正确满足了这一需求？

A) 在每个参与的 prim 上直接创作一个名为 'collectionMembers' 的自定义属性。
B) 定义一个新的类型化 schema，例如 'CollectionMesh'，并要求每个参与的 prim 都重新定型为它。
C) 在每个参与的 prim 上使用 VariantSet，表示它是否属于该集合。
D) 应用 UsdCollectionAPI——一个 multi-apply API schema——在 prim 上定义命名集合，按路径包含或排除其它 prim，而不改变它们的类型。

---

**Q7.** 某个 stage 的 root layer 中包含一个 prim /Asset，其 local opinion 把属性 'displayColor' 设为 (1,0,0)。同一个 prim 还从一个 referenced layer 组合进来，后者把 'displayColor' 设为 (0,1,0)。没有 variant sets、specializes 或 inherits 参与。在组合后的 stage 上，值解析为 'displayColor' 报告哪种颜色？

A) (1,0,0)，因为 referencing layer 中的 local opinion 总是强于来自 referenced layer 的 opinion
B) (0,1,0)，因为 references 总是优先于引入它们的 layer
C) 混合值 (0.5,0.5,0.5)，因为 USD 会对来自不同 arc 的冲突 opinion 取平均
D) (0,1,0)，因为 referenced layer 先被创作，先创作的 opinion 获胜

---

**Q8.** 某位技术美术需要在多边形网格上创作按面-顶点的法线，使每个面的每个顶点都能拥有彼此不同的法线值，即使这些面之间共享顶点。该属性应使用哪种 primvar 插值设置？

A) constant
B) uniform
C) faceVarying
D) vertex

---

**Q9.** prim /World/Robot 在 stage 的 root layer 中直接创作了 local opinion，把 'primvars:displayColor' 设为红色。同一个 prim 还具有指向某个资产 layer 的 reference arc，该 layer 把 displayColor 设为蓝色。stage 组合时使用哪个值？

A) 蓝色，因为来自 referenced layer 的 opinion 总是覆盖 referencing layer 中的 opinion
B) 按墙上时钟时间最后创作的那个 opinion
C) 渲染器会把红色和蓝色混合成一种合成颜色，因为两者都是有效的 opinion
D) 红色，因为该 prim 自身 layer 的 layer stack 中的 local opinion 强于任何组合 arc，包括 references

---

**Q10.** 资产团队希望美术能够非破坏性地在资产的三种备选 LOD 网格表示（高、中、低）之间切换，且绝不编辑原始资产文件。哪种组合 arc 是专为此类可选备选方案而设计的？

A) Payloads，因为它们控制几何体是否加载
B) Sublayers，因为它们把多个 layer 合并为一个 opinion 集合
C) Specializes，因为它提供一组可被覆盖的弱 opinions
D) Variant sets，因为它们让使用者可以在若干互斥的命名 opinion 集合之间选择

---

**Q11.** 在 USD 使用的 LIVRPS 组合强度排序中，哪条 arc 最弱，其用途是提供可被覆盖的 'default' opinions，任何更强的 arc（例如 reference）都能轻松覆盖它们？

A) Specializes
B) Inherits
C) Variants
D) Payloads

---

**Q12.** 某个生产 stage 需要引入一个庞大的城市街区资产（5 亿个多边形），以便布局美术在几何体默认不加载的情况下也能处理场景，只在需要打光或渲染时显式加载。应该使用哪种组合 arc 来引入该资产？

A) reference，因为 references 总是立即加载且无法延后
B) payload，因为 payloads 可以从初始加载中排除并按需加载
C) variant set，因为它让你切换几何体细节级别
D) sublayer，因为 sublayers 合并 opinions 但不引入新的 prim scope

---

**Q13.** 某位绑定师创作了一个基础 prim /_class_BipedRig，定义了共享的关节属性。多个角色 prim 需要继承这些属性，使得对 /_class_BipedRig 的任何后续编辑都能自动传播到每一个角色，并且这种继承而来的 opinion 仍强于来自被引用角色资产的 opinions。绑定师应该使用哪条 arc？

A) Specializes
B) Inherits
C) Payloads
D) Variants

---

**Q14.** 某个 stage layer 使用 'explicit' 列表编辑操作，而不是 'prepend' 或 'append'，来创作它的 reference list-op。这对同一 prim 在更弱 layer 中创作的任何 reference opinions 有什么影响？

A) 更弱 layer 的 reference 条目被完全丢弃，由 explicit 列表取代
B) 更弱 layer 的 reference 条目被追加到 explicit 列表之后
C) 更弱 layer 的 reference 条目被合并进来，并去除重复项
D) explicit 操作对强度没有任何影响；只有 prepend 和 append 会影响排序

---

**Q15.** 名为 /Robot 的 prim 在 root layer 中对其 'displayColor' 属性没有任何 local opinions。它继承自一个将 displayColor 设为 (1,0,0) 红色的 class prim /_class_Robot，同时它还引用了一个外部资产，该资产的根 prim 把 displayColor 设为 (0,1,0) 绿色。按照 LIVRPS 强度排序，为 /Robot 解析出的颜色是什么？

A) 绿色，因为 references 先于 inherits 被组合
B) 错误，因为 inherits 和 references 不能作用于同一个属性
C) 红色，因为在 LIVRPS 顺序中 inherits arc 强于 references
D) 绿色，因为被引用资产的 root layer 总是最强的

---

**Q16.** 某工作室交付一个跨多个镜头使用的角色资产。绑定师需要让灯光美术在 stage 级别通过单一命名选择，在三套预制的 LOD 几何体（高、中、低）之间切换，而不编辑角色的源 layer。哪种组合 arc 最能实现这一点？

A) variant set，使用者通过设置 variant selection metadata 来选择 LOD
B) payload，这样每个 LOD 在 stage 打开时独立加载
C) 一个指向三个同级 prim（每个 LOD 一个）的 specializes arc
D) 三个独立的 references，每个 LOD 追加一个，这样三个都会同时加载

---

**Q17.** 在某个 stage 的 layer stack 中最弱的 layer 里，某个 prim 的 reference list op 是一个 explicit 列表：references = [assetA.usda]。一个更强的 layer 在同一 prim 上添加了 prependReferences = [assetB.usda] 和 appendReferences = [assetC.usda]。最终的组合引用顺序是什么（按从强到弱列出）？

A) assetC.usda, assetA.usda, assetB.usda
B) assetB.usda, assetA.usda, assetC.usda
C) assetA.usda, assetB.usda, assetC.usda
D) assetB.usda, assetC.usda, assetA.usda

---

**Q18.** 一个数字孪生场景包含 40,000 个几乎完全相同的运输箱，每个只需要唯一的位置、旋转和缩放。哪种做法最能最小化内存占用和加载时间？

A) 把箱子资产作为独立 prim 引用 40,000 次
B) 使用原生（prototype）instancing，为每个箱子创作一个唯一的 instanceable prim
C) 把所有箱子展平为单个网格并烘焙变换
D) 使用 PointInstancer prototype，带有逐实例的 transform、scale 和 orientation 数组

---

**Q19.** 某位灯光美术需要只改变通过原生（prototype）instancing 创建的 500 个实例中某一个箱子的自发光颜色，而不影响其余 499 个。该美术首先必须做什么？

A) 在 stage 中直接于该实例的 prim 路径上创作 property override
B) 编辑共享 prototype prim 的自发光颜色属性
C) 在该特定箱子 prim 上设置 instanceable = false，然后创作 override
D) 为 prototype 添加一个新的 variant set，并按实例进行切换

---

**Q20.** 为构建具有明确定义的外部接口的"原子化"可复用 USD 组件资产，推荐采用哪种结构模式？

A) 把所有几何体、材质和物理直接烘焙进引用方场景中，且不带 defaultPrim
B) 创作一个顶层的 defaultPrim，将几何体、材质和 variants 封装其中，仅暴露必要的属性供外部覆盖
C) 把资产存储为多个同级的根 prim 且不带 defaultPrim，由使用者手动挑选
D) 只使用 payload arc，完全避免 variant sets，以降低复杂度

---

**Q21.** 为了让一个 prim 在 USD 中具备参与原生（prototype）instancing 的资格，必须在它上面创作值为 true 的哪个 metadata 字段？

A) kind = "component"
B) instanceable
C) active = true
D) specializesInstancing

---

**Q22.** 多个供应商交付的 USD 资产文件各自定义了使用不同供应商专有名称的根 prim（例如 /Vendor_A_Root、/Vendor_B_Root）。某条流水线需要把数百个这类资产引用到一个聚合场景中，而不能硬编码每个供应商的根 prim 名称。该流水线应该依赖什么？

A) 要求每个供应商文件都使用完全相同的根 prim 名称 /Root
B) 在引用之前先把每个供应商文件展平进聚合 layer
C) 使用 sublayers 而非 references，这样根 prim 名称就不重要了
D) 每个供应商资产所创作的 defaultPrim metadata，只按资产路径进行引用

---

**Q23.** 在 OpenUSD 中，原生（prototype）instancing 与基于 PointInstancer 的 instancing 之间的关键架构权衡是什么？

A) 原生 instancing 保留逐实例的 prim 层级，并允许通过关闭 instanceable 让单个实例变为可编辑；而 PointInstancer 实例则表示为轻量级的索引点，没有各自可编辑的 prim 层级
B) 原生 instancing 支持带逐点数组的数百万实例，而 PointInstancer 只支持少数几个实例
C) PointInstancer 要求每个实例共享完全相同的材质，而原生 instancing 允许逐实例的材质变化且没有额外开销
D) 原生 instancing 和 PointInstancer 在功能上完全相同，仅 XML schema 语法有所不同

---

**Q24.** 某场景包含 5,000 个 'Tree' 资产的原生可实例化引用，全部共享同一个 prototype。灯光美术需要给恰好一个特定树实例一个独特的材质色调，而不影响其余 4,999 个实例，也不重构整个层级。在 USD 中哪种做法正确实现了这一点？

A) 在那棵树的 instance proxy 路径上直接创作一个 over，并在那里添加材质绑定 override
B) 直接在那一个树 prim 上设置 instanceable = false，使其被排除在 instancing 之外，并让它接收自己独有的 opinions
C) 编辑共享 prototype prim 的材质绑定，然后用 variant selection 隔离那一个实例
D) 把整个 Tree 层级从原生 instancing 转换为 PointInstancer，以便获得逐点的材质 override 能力

---

**Q25.** 某团队需要交付一个单一、自包含的 3D 资产（几何体、材质和贴图），用于在 iOS 设备上的 Apple AR Quick Look 中查看，并且在加载时没有任何外部文件依赖。他们应该导出为哪种格式？

A) .usda
B) .usdz
C) .usdc
D) .usd

---

**Q26.** 某个 layer 包含资产路径引用 "textures/wood.png"，前面既没有 "./" 也没有 "../"。USD 的资产解析会如何处理这个路径？

A) 它总是被解析为绝对路径，完全忽略当前 layer 的位置
B) 除非用显式的 "./" 前缀重写，否则解析失败
C) 它相对于 USD 进程启动时操作系统的当前工作目录解析
D) 它被视为搜索路径，使用所配置 Asset Resolver 的搜索规则解析，而不是纯粹作为锚定相对路径

---

**Q27.** 某工作室需要把从 Maya 导出的已烘焙、逐帧点缓存变形网格引入 USD stage，并尽量减少几何保真度损失，但保留程序化着色网络不是必需条件。哪种交换方式最合适？

A) 导出 FBX，并通过通用的 FBX-to-USD 导入器转换
B) 在 .usda 文本 layer 中手工创作逐帧的点位置
C) 导出 Alembic (.abc)，并通过 USD 的 Alembic 插件 (UsdAbc) 引用它，因为点缓存几何体几乎无损地转换，而着色网络不会被带过来
D) 直接把 Maya 场景文件打包为 USDZ 而不做转换

---

**Q28.** 你正在准备一个 USDZ 包，它必须在不同的工作室和不同的机器上都能正确加载，不出现任何文件缺失错误。所有内部资产引用都必须满足哪项要求？

A) 所有引用必须是相对路径，且只能解析到包归档内部所包含的文件
B) 所有引用必须使用绝对文件系统路径，以便解析器可靠地找到归档根目录
C) 引用可以指向任何路径类型，因为 USDZ 总是会在解析发生前解压到临时目录
D) 应使用外部的 http:// 贴图 URL 来减小包的体积

---

**Q29.** 哪条陈述正确区分了 .usd 文件扩展名与 .usda 和 .usdc？

A) .usd 总是编码为二进制 crate 数据，而 .usda 和 .usdc 都是 ASCII 变体
B) .usd 文件无法被 DCC 工具或 Omniverse 打开，只有 .usda 和 .usdc 文件可以
C) .usd 专用于 USDZ 包，而 .usda 和 .usdc 仅用于独立的 stage
D) .usd 是一个通用的、与格式无关的扩展名，其内容可以是 ASCII 编码也可以是二进制（crate）编码；而 .usda 明确表示 ASCII 文本，.usdc 明确表示 crate 二进制编码

---

**Q30.** 多位美术需要在 DCC 应用（如 Maya）与基于 Omniverse 的审阅场景之间工作时，实时看到彼此的编辑。应该使用哪种机制？

A) 每位美术完成一次编辑会话后，手动重新导出并重新导入 USD 文件
B) 每次会话后通过电子邮件或文件传输共享 USDZ 包形式的场景
C) 使用 DCC 应用的 Omniverse Connector，并连接到 Nucleus 服务器的 Live Session，以实现实时的同步编辑
D) 把 DCC 场景转换为 FBX，并定期在 Omniverse 中引用更新后的 FBX 文件

---

**Q31.** 某个流水线工具必须遍历一个 stage 并处理每一个处于 active、defined、loaded 状态且不是 class definition 的 prim，同时还要访问通过 references 和 payloads 引入的 prim。不需要任何自定义 predicate 逻辑。哪个调用能用最少的代码完成这一目标？

A) stage.TraverseAll()
B) Usd.PrimRange.Stage(stage, Usd.PrimIsAbstract)
C) stage.Traverse()
D) stage.GetPseudoRoot().GetAllChildren()

---

**Q32.** 某工作室的流水线脚本需要在一个已经通过 reference 存在于组合后 stage 中的 prim 上添加纯 override——一个 visibility opinion——同时不声明也不改变该 prim 在当前 edit target 的 layer 上的类型。哪个调用是正确的？

A) stage.DefinePrim(path, 'Xform')
B) Sdf.CreatePrimInLayer(layer, path)
C) stage.GetPrimAtPath(path).SetTypeName('')
D) stage.OverridePrim(path)

---

**Q33.** 某绑定工具需要在第 24 帧为某个 prim 的 xformOp:translate 属性创作一个带关键帧的平移值，同时不干扰该属性上已创作的任何默认（与时间无关）值。哪一行是正确的？

A) attr.Set(Gf.Vec3d(1,2,3), Usd.TimeCode.Default())
B) attr.Set(Gf.Vec3d(1,2,3))
C) attr.Set(Gf.Vec3d(1,2,3), Usd.TimeCode(24.0))
D) attr.SetDefault(Gf.Vec3d(1,2,3))

---

**Q34.** 某个迁移脚本必须更新材质绑定关系，使每个 mesh prim 精确指向一个新的材质路径，完全替换此前由其它 layer 或先前流水线运行所创作的任何目标。应使用哪个 relationship 调用？

A) rel.AppendTarget(newMaterialPath)
B) rel.SetTargets([newMaterialPath])
C) rel.AddTarget(newMaterialPath)
D) rel.GetTargets().append(newMaterialPath)

---

**Q35.** 就底层数据模型而言，Sdf.Layer 与 Usd.Stage 之间的根本区别是什么？

A) Sdf.Layer 只存储几何体数据，而 Usd.Stage 存储所有非几何体的 metadata
B) Usd.Stage 可以保存到磁盘，而 Sdf.Layer 在会话期间只存在于内存中
C) 在 USD API 中，Sdf.Layer 和 Usd.Stage 只是同一个对象的两种可互换术语
D) Sdf.Layer 是由文件支撑的、存放场景描述 opinions 的原始容器；Usd.Stage 则是通过组合 arc 把一个或多个 layer 组合起来的内存中的组合结果

---

**Q36.** 某团队正在使用 Hydra，把一个自定义视口渲染器集成到基于 Omniverse 的工具中。哪个组件负责消费 Hydra 的 scene index/render index 数据，并为该特定渲染器发出实际的图形 API 绘制调用？

A) The Scene Delegate
B) The Usd.Stage 组合引擎
C) The Render Delegate
D) The Sdf.Layer 栈

---

**Q37.** 某个流水线脚本在紧凑循环中直接调用 Sdf.AttributeSpec 和 Sdf.PrimSpec 构造函数，在一个 Sdf.Layer 上创作了数千个属性值。该脚本运行极慢，因为每次单独的编辑都会触发一次完整的变更通知流程，而其它工具（例如视口监听器）会对其作出响应。哪项变更最能解决性能问题，同时保持相同的底层 Sdf 创作调用？

A) 在循环之前调用 `stage.SetEditTarget()`，指向一个全新的内存 session layer
B) 把整个创作循环包裹在 `with Sdf.ChangeBlock():` 上下文管理器中
C) 只在循环完成后调用一次 `stage.Save()`，而不是每次编辑之后都调用
D) 把循环替换为 `Usd.PrimRange(stage.GetPseudoRoot(), Usd.TraverseInstanceProxies())`

---

**Q38.** 某个校验工具必须遍历一个 stage 并检查位于 instanceable 引用之下的 prim 上的属性值，但默认的 UsdStage.Traverse() 调用不会下降到那些被实例化的子树中，只显示实例 prim 本身。哪个调用能在遍历时正确地把被实例化的后代暴露为 instance proxies？

A) stage.Traverse(Usd.TraverseInstanceProxies())
B) stage.TraverseAll()
C) 使用默认 predicate 的 Usd.PrimRange.Stage(stage)
D) 遍历 stage.GetPrototypes() 并访问每个 prototype prim 的子节点

---

**Q39.** 名为 </World/Rock_01> 的 prim 把 'instanceable' 属性设为 true，以减少跨数千个副本的内存占用。某位美术在 root layer 上创作了一个 override，只为这一个实例修改 displayColor，但即使完全重新加载，该变更在 usdview 中也从未出现。最可能的原因是什么？

A) usdview 缓存了 displayColor 的值，需要重启进程而不只是重新加载
B) 一旦为该 prim 加载了 payload，displayColor 就无法被覆盖
C) Instanceable prim 共享其共享 prototype 的组合 opinions，因此在组合过程中，针对 instance proxy 的逐实例 override 会被裁剪掉，除非把该 prim 设为非 instanceable，或把 override 应用到 prototype/class 上
D) 该 override 被创作在错误的 variant set 中，需要匹配相应的 variant selection

---

**Q40.** 某个大型环境 stage 在 usdview 中打开要花超过一分钟，因为它会急切地加载数千个通过 payload 引入的 hero assets，其中大多数都在当前相机视野之外。哪种做法最能减少初始打开时间，同时仍允许按需获取完整细节？

A) 在打开之前把整个 stage 展平为单个 layer
B) 把所有 payload 转回 references，让组合解析得更快
C) 把每个资产 prim 标记为 instanceable，让 usdview 只组合一份拷贝
D) 让资产保持在 payload 之后，并使用选择性加载（例如 stage population mask，或在打开时取消勾选 'Load Payloads'，然后只交互式地加载所需的 prim）

---

**Q41.** 某物理团队需要为每个 hero asset 准备一个低模碰撞网格，它应当在交互式视口中可见且可选中以便操作，但绝不能出现在最终的生产渲染中。应该给这些碰撞网格分配哪个 UsdGeomImageable purpose 值？

A) guide
B) default
C) proxy
D) render

---

**Q42.** 某场景需要绘制 500,000 棵树，而这些树只来自 5 个独特的树 prototype 模型，每个实例需要唯一的位置、旋转和缩放，并以高效的内存使用为优先考虑。哪种 USD 机制是最合适的选择？

A) 一个引用这 5 个 prototype 的 UsdGeomPointInstancer，带有逐实例的 position、orientation 和 scale 数组
B) 原生 instanceable references，为每棵树创作一个 instanceable reference
C) 一个在 stage 根节点处于 5 个树模型之间切换的 VariantSet
D) 基于 class 的 inherits，为每个树实例创作一个 inherited override

---

**Q43.** 四个标准 UsdGeomImageable purpose 值中，哪一个用于非几何体的辅助可视化，例如相机视锥、灯光操纵器或绑定控制器形状，并且除非用户显式启用否则在视口中隐藏？

A) proxy
B) default
C) render
D) guide

---

**Q44.** 某个 USD root layer 使用相对路径 './props/chair.usd' 引用了一个资产。在 root layer 被移动到新目录、却没有同时移动被引用资产之后，usdview 报告该引用无法解析。最可能的正确修复方式是什么？

A) 对相对路径进行锚定或更新，使其能相对于新的 layer 位置正确解析，或者改用与 layer 目录解耦的、基于搜索路径/asset-resolver 的路径
B) 增加 asset resolver 的缓存超时时间，让该引用有更多时间完成解析
C) 把该引用包裹在 variant set 中，让组合能够自动重试解析
D) 把该引用转换为 payload，让未解析的资产被静默跳过

---

---


### 模拟测试 2：NCP-OUSD：NVIDIA OpenUSD 开发认证备考


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `practice-tests/practice-test-2.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/practice-tests/practice-test-2.md) · 语言：英文原文 · 中译版



# 模拟测试 2：NCP-OUSD：NVIDIA OpenUSD 开发认证备考

- **题目数量：** 43
- **时间限制：** 90 分钟
- **及格分数：** 70%%

> 答案位于 `answer-key-2.md`。请在 `score-tracker.md` 中记录成绩。

---

**Q1.** 某个 prim 的 Radius 属性在一个较弱的 sublayer 中创作了默认值 1.0，并在同一个 stage 中一个更强的 sublayer 中创作了完整的一组 time samples（第 1-48 帧）。在第 24 帧查询 stage 上的该属性时，USD 的值解析（value resolution）会返回什么值？

A) 1.0，因为无论 layer 强度如何，已创作的默认值总是优先于 time samples
B) USD 抛出解析错误，因为同一属性的 default 与 time-sampled opinions 不能跨 layer 共存
C) 默认值与第 24 帧 time-sampled 值的平均值
D) 更强 layer 在第 24 帧插值得到的 time-sample 值，因为只要某个 layer 为该属性贡献了任何 opinion，最强 layer 就完全胜出，并使用它的 time samples 进行插值

---

**Q2.** 在 USD 的 LIVRPS 组合强度排序中，哪条 arc 解析时的强度弱于 References 但强于 Specializes？

A) Inherits
B) Payloads
C) VariantSets
D) Local opinions

---

**Q3.** 某位建模美术需要网格上的逐面-顶点法线，使共享顶点的各个面各自拥有不同的法线值，从而在接缝处形成视觉上的硬边。为法线 primvar 应创作哪种 primvar 插值？

A) faceVarying
B) uniform
C) vertex
D) constant

---

**Q4.** 在一个 stage 上，某个 prim 以 kind = component 创作，而同一个 prim 之下还有以 kind = group 创作的子 prim。当用 USD 的模型层级约定检查该 stage 时，结果是什么？

A) 校验通过，因为 component prim 可以包含任意深度的 group 和 component 后代
B) 层级无效，因为 component 在模型层级中本应是叶子级的 kind，其下不应再有 group 或 component 后代
C) 加载时会自动把这些子 prim 重新归类为 subcomponent kind，以满足层级规则
D) 只有当该 component prim 同时被标记为 instanceable 时，层级才无效

---

**Q5.** 某个 prim 需要两个独立的集合，分别名为 'render' 和 'proxy'，二者都用 UsdCollectionAPI 构建。在该 prim 的 apiSchemas metadata 中，正确的创作方式是什么？

A) 只 apply 一次 UsdCollectionAPI；两个集合名会依据该 prim 的下游消费者自动推断出来
B) 用不同的 instance name apply 两次 UsdCollectionAPI，例如 CollectionAPI:render 和 CollectionAPI:proxy，因为它是一个 multi-apply API schema
C) 创建两个独立的 prim，因为单个 prim 不能承载多个已 apply 的 API schema 实例
D) 创作两个名为 UsdRenderCollectionAPI 和 UsdProxyCollectionAPI 的 single-apply schema

---

**Q6.** 哪条陈述正确区分了 USD relationship 与 attribute connection？

A) connection 与 relationship 是同一底层场景描述构造的可互换序列化形式
B) relationship 和 connection 都只能指向其它属性，永远不能直接指向 prim
C) relationship 指向一个或多个 prim、property 或其它 relationship，本身不携带类型化的、随时间变化的值；而 connection 是属性上的 metadata，指向其它属性以为该属性取值
D) relationship 可以携带已创作的 time samples，而 connection 只能限定为单个默认值

---

**Q7.** 某个 stage 中针对 </World/Robot.driveSpeed> 的 layer stack 组合如下：最强 layer（root.usda）只创作了默认值 5.0，没有任何 time samples；较弱的 sublayer（anim.usda）创作了 time samples，在第 1-24 帧把该属性从 0.0 动画到 10.0。在第 12 帧，USD 的值解析为 driveSpeed 返回什么值？

A) anim.usda 在第 12 帧插值得到的 time-sample 值，因为无论 layer 强度如何，time samples 总是优先于默认值
B) 0.0，因为当最强 layer 缺少 time samples 时，USD 会回退到第一个已创作的 time sample
C) 5.0，因为拥有任何 opinion 的最强 layer 直接胜出，而它的 opinion 是默认值，所以较弱的 time samples 被完全忽略
D) 报错，因为同一属性在一个 layer 中用 default、在另一个 layer 中用 time samples 属于无效组合

---

**Q8.** 某位管线 TD 需要把 multi-apply 的 CollectionAPI schema 在同一个 prim 上 apply 两次：一次定义名为 'renderLights' 的集合，一次定义 'shadowLinks'，使两个集合能在同一个 prim 上独立共存。哪一对 token 能正确表示这两个已 apply 的 schema 实例（写在 prim 的 'apiSchemas' listOp metadata 中）？

A) CollectionAPI(renderLights) 和 CollectionAPI(shadowLinks)
B) CollectionAPI:renderLights 和 CollectionAPI:shadowLinks
C) renderLights:CollectionAPI 和 shadowLinks:CollectionAPI
D) CollectionAPI 和 CollectionAPI，由 USD 在加载时自动消歧

---

**Q9.** 在该 stage 上，/World/Props/Chair 继承自 /World/_class_/BaseChair，后者在它的一个 Sphere 子 prim 上创作了 radius = 5.0。Chair 还有一条指向外部 layer Sphere_ext.usd 的 reference arc，该 layer 在同一个子 prim 上创作了 radius = 2.0；两个 layer 都没有直接在 Chair 自身上创作 radius。组合后 radius 的值是什么？

A) 2.0，因为在 LIVRPS 中 references 总是强于 inherits
B) 抛出错误，因为 inherits 和 references 不能作用于重叠的 opinions
C) 5.0，因为在 LIVRPS 强度排序中 Inherits 强于 References
D) 2.0，因为该 reference 在 layer 中创作得较晚，最后创作的获胜

---

**Q10.** layer stack 中最强的 layer 创作了：references.prepend = ["C.usd"]。较弱的 sublayer 创作了：references = ["A.usd", "B.usd"]（普通的、无 op 赋值）。最终组合出的 reference 列表是什么（按从强到弱排列）？

A) [C.usd] —— 一旦更强的 layer 编辑了该列表，较弱 layer 的 explicit 列表就被完全丢弃
B) [A.usd, B.usd, C.usd]
C) [C.usd, B.usd, A.usd]
D) [C.usd, A.usd, B.usd]

---

**Q11.** /World/Robot 在同一个 prim 上同时带有 payload（robot_payload.usd，设置 jointCount = 6）和 reference（robot_ref.usd，设置 jointCount = 8），且没有直接在 Robot 上创作 local opinion。两条 arc 当前都已加载。jointCount 解析出的值是什么？

A) 8，因为在 LIVRPS 强度排序中 References 强于 Payloads
B) 6，因为 payload 总是晚于 reference 加载，其 late-binding opinion 获胜
C) 未定义，因为 references 和 payloads 不能在同一个 prim 上共存
D) 取决于哪条 arc 先出现在该 prim 的 metadata 列表中

---

**Q12.** 你正在设计一个着色库：下游 prim 应当能够从共享的 base prim 拾取通用的默认 shader 参数，但这些下游 prim 上**任何**后续通过 reference 或 payload 引入的 opinion 都必须始终胜过 base 的默认值 —— 同时，如果 base prim 之后被修改，它仍要能实时传播这些修改。应该用哪条组合 arc 把下游 prim 链接到共享 base？

A) Specializes
B) Inherits
C) 一条 reference
D) 一个 variant set

---

**Q13.** 某个 stage 的 session layer 为 /World/Prop 上的 "shadingVariant" variant set 创作了 variantSelection = "damaged"。root layer（在 layer stack 中较弱）为同一个 variant set 创作了 variantSelection = "pristine"，作为它的默认选择。哪一个变体会被组合到该 prim 上？

A) "pristine"，因为创作在 variant set 所属 prim 上的默认选择总是优先
B) 两者都不是 —— 当两个 layer 对 variant selection 存在分歧时，USD 会抛出组合错误
C) 两个变体都会被组合，并合并成一个综合结果
D) "damaged"，因为 session layer 是 local layer stack 中最强的 sublayer

---

**Q14.** /World/City 带有一个指向 City_payload.usd 的 payload。在该 payload layer 内部，prim /World/City/Building 自己还有一条指向 Building_lib.usd 的 reference arc，用于提供精细几何体。如果打开 stage 时 City 的 payload 保持未加载，Building_lib.usd 中的内容会怎样？

A) 会引发组合错误，因为 payload 目标内部不允许嵌套 arc
B) 只有 reference 的 default prim metadata 被加载，几何体本身仍然保持延迟
C) 它仍会正常组合，因为 references 总是优先于未加载的 payload
D) 它根本不会被组合 —— 未加载 payload 子树内的任何内容都不会被求值，包括其中嵌套的任何 arc

---

**Q15.** prim /World/Robot 在 root layer 中对 'displayColor' 属性没有任何 local opinion。该 prim 继承自一个把 displayColor 设为红色的 class prim /_class_Robot；它还有一个 variant set 'look'（被选中的变体把 displayColor 设为蓝色）、一个指向把 displayColor 设为绿色的外部资产的 reference，以及一个把 displayColor 设为黄色的 payload。该 prim 最终解析为哪种颜色？

A) 绿色，因为 references 引入主要的资产数据，优先于 variants 和 inherits
B) 蓝色，因为 variant selection 总是覆盖继承而来的 class opinions
C) 红色，因为在 LIVRPS 强度排序中 Inherits 强于 VariantSets、References 和 Payloads
D) 黄色，因为 payloads 最后被组合，因此拥有最强的 opinion

---

**Q16.** Layer stack（从强到弱）：root.usda，然后是 sublayer.usda。root.usda 包含 'prepend references = @assetX.usda@'。sublayer.usda 包含 'prepend references = @assetY.usda@'。两个 layer 都没有删除任何 references。该 prim 上 references 列表最终组合出的顺序是什么？

A) [assetY, assetX] —— 由于 sublayer 先被求值，sublayer 的 prepend 先于 root layer 的 prepend 生效
B) 只有 [assetX] —— root layer 的 prepend 操作会悄无声息地丢弃 sublayer 的列表内容
C) [assetX, assetY] —— 更强 layer prepend 的项目比更弱 layer prepend 的项目更靠近组合列表的前端
D) [assetY, assetX]，其中 assetX 作为重复项被移除 —— USD 的列表编辑总是让最弱的 opinion 赢得平局

---

**Q17.** 某工作室正在构建一个大型环境资产。他们需要：(1) 沉重的底层几何体在用户明确需要查看或渲染之前一直不加载到内存中；(2) 下游用户能够非破坏性地在 'Day' 与 'Night' 两套照明方案之间切换，而不编辑源 layer。哪种组合策略最能同时满足这两项要求？

A) 把几何体直接 reference 进 stage，再用 inherits arc 处理 Day/Night 的照明变化
B) 用 payload 推迟环境资产的加载，并在被 payload 的资产内部为照明创作一个 variant set，供下游选择
C) 把 Day 与 Night 的照明文件与被引用的几何体一起直接 sublayer 到 root layer 中
D) 用一个 variant set 在两套完整的 Day 与 Night 环境资产之间切换，不使用 payload

---

**Q18.** 某工作室对一个英雄树资产使用原生（prototype）instancing，在一片森林场景中散布了 5,000 个相同的 instanceable references。一位灯光美术需要只改变其中某一个特定树实例的叶子颜色，不影响其余 4,999 个实例，也不破坏其余部分的 GPU instancing。哪种做法能正确实现这一点？

A) 直接在 prototype prim 上创作新的颜色值，使其传播到每个实例，然后再手动把其余 4,999 个实例上的值改回去
B) 在视口中选中那一棵单独的树的 instance proxy 路径，直接在该 proxy prim 上创作颜色属性 override
C) 在那棵特定树的引用 prim 上设置 instanceable = false，把它排除在共享 prototype 之外，从而可以在它自己的子树上创作唯一的 opinions，而其余 4,999 个保持实例化
D) 在 PointInstancer 的 prototypes relationship 上添加一个 variant set，并只针对该实例的 point index 切换变体

---

**Q19.** 某位管线架构师正在按照资产接口模式设计一个原子化 component 资产（单把椅子）。该资产必须暴露一小套稳定的公共 API —— kind metadata、为 LOD 和材质定义的 variantSets —— 让其他部门能够廉价地引用它，而不必每次打开资产都加载完整的渲染几何体。哪种结构最能满足这一要求？

A) 把整个资产 —— 接口 metadata 与完整渲染几何体 —— 摊平进单个不带 arc 的 .usd 文件，这样只需管理一个文件
B) 直接 reference 渲染网格几何体（不用 payload），并与接口 metadata 放在一起，使所有内容在一次组合中一起加载
C) 定义资产的 root prim，把所有接口 metadata（kind、variantSets、purpose）直接创作在它上面，然后通过指向独立几何体 layer 的 payload arc 引入沉重的渲染网格
D) 把接口 metadata 存在被引用几何体之上的 session layer 中，因为 session layer 是唯一适合定义公共资产接口的 arc 类型

---

**Q20.** 你正在创作一个 UsdGeomPointInstancer，用它散布 200,000 个岩石实例，从 4 个不同的 prototype 网格中随机选择，并为每块岩石施加非均匀的逐实例缩放。哪种配置是正确的？

A) protoIndices 的长度应为 4（每个 prototype 一项），而 positions 的长度为 200,000，因为 protoIndices 只需要描述 prototype 集合
B) protoIndices 必须是长度为 200,000、取值范围为 [0,3] 的 int 数组，用于索引 prototypes relationship；scales 也必须是长度为 200,000 的数组，并与 positions 逐下标对齐
C) 只需要创作 positions 和 orientations —— scale 会自动从被引用的 prototype 几何体继承，无法逐实例变化
D) prototypes relationship 必须把同一个 prototype 路径列出 200,000 次，这样每个实例都有自己专属的 relationship 目标

---

**Q21.** 某位环境美术把 300 个建筑资产聚合进一个主城市 stage。其中许多建筑需要应用完全相同的 override 编辑 —— 例如在其碰撞网格上禁用碰撞并设置 purpose='proxy'。把同样的 override opinions 复制粘贴到 root layer 中全部 300 个 prim 上虽然可行，但一旦这些共享 override 需要修改，就会变成维护噩梦。哪种组合技术最能消除这种重复，同时保留单一可编辑的真源？

A) 在一个专用的 class prim（例如 /_class_NoCollision）上创作一次共享 override，并从这 300 个建筑 prim 各加一条指向该 class prim 的 'inherits' arc
B) 写一个脚本，在每次 stage 组合时把相同的 override opinion 重新注入全部 300 个 prim specs 中，从而使文本保持同步
C) 把这 300 个建筑从 references 改为 payloads，因为 payload arc 会自动去重引用 prim 上创作的任何 override opinions
D) 创建 300 个独立的 variant set，每个建筑一个，每个只含一个 'collision-off' 变体，且必须在每栋建筑上手动选择

---

**Q22.** 对于一个大型开放世界场景，需要渲染约 5,000 万根草叶，而几何体只有 3 种不同的变化。哪种陈述正确描述了在这一规模下原生（prototype）instancing 与 point instancing 之间的取舍？

A) Point instancing 正是为这种场景量身打造的：3 个 prototype 只存储一次，用紧凑的 position/orientation/scale/protoIndex 数组高效描述数百万个实例；而原生 instancing 会产生逐实例的场景图/prim 开销，在数千万实例的规模下扩展性很差
B) 应当优先使用原生 instancing，因为它支持任意的逐实例材质 override，而 point instancing 完全不支持任何逐实例变化
C) 原生 instancing 与 point instancing 的逐实例场景图开销完全相同，因此选择纯粹取决于团队偏好，对性能没有任何影响
D) 在这一规模下根本不需要任何显式 instancing，因为 USD 在打开 stage 时会自动对所有被引用的 prim 去重相同的网格数据，无需额外创作

---

**Q23.** 某个团队需要让 10,000 个原生可实例化汽车 prim（全部引用同一个汽车资产）各自独立地为创作在汽车资产 root prim 上的 'paint' variantSet 选择不同的值，同时尽可能多地共享网格 instancing 以节省 GPU 内存。哪种创作方式能正确实现这一点？

A) VariantSet 的选择永远不能在 instanceable prim 之间产生分歧 —— 在进行任何逐车 variant 选择之前，整个车队都必须设置为 instanceable=false
B) 必须用 point instancing 代替原生 instancing，因为只有 PointInstancer 才支持通过索引 primvar 实现逐实例的 variantSet 选择
C) 为每辆车创作一个独立的 session layer（共 10,000 个），各自 override 该车的 variantSelection，因为 session layer 是唯一能让实例之间 variant 选择产生分歧的机制
D) 直接在这 10,000 个汽车实例的 root prim 上分别创作 'paint' variantSet 的不同 variantSelection opinion（仍然以 instanceable=true 引用同一个资产）；USD 会自动把组合结果匹配的实例按唯一的 variant 选择归组为不同的 prototype，同一颜色组内仍然共享几何体

---

**Q24.** 某个 PointInstancer prim 使用单个 prototype 在地形上散布了 50,000 个岩石实例。在美术评审期间，灯光团队要求隐藏 12 个特定实例（按索引标识），因为它们穿透了地形几何体，同时既不能禁用 instancing，也不能重构 prototype 层级。在 USD 中哪种做法能正确实现这一点？

A) 在 PointInstancer prim 上创作 invisibleIds 属性，列出要隐藏的实例索引
B) 在 prototype prim 上设置 instanceable=false，并从生成的层级中手动删除不需要的实例 prim
C) 在 session layer 中添加 override，把 PointInstancer 下各实例 prim 路径上的 visibility 设为 invisible
D) 从 protoIndices 数组中那些索引位置移除对应条目

---

**Q25.** 某工作室正在准备一个混合现实产品配置器，要交付给只接受 USDZ 的合作伙伴移动 AR 查看器。源资产通过绝对文件系统路径引用了若干贴图文件（例如 "C:/textures/diffuse.png"），并包含一个 payload，而这个 payload 自身又引用了项目目录之外的外部 Alembic cache。在打包之前，必须采取什么操作才能确保 USDZ 在合作伙伴的查看器中正确打开？

A) 保持绝对路径不变，因为 USDZ 会在打包时自动重写它们
B) 用 sublayer arc 替换 payload，因为 USDZ 不支持 payload
C) 在引用之前用 DEFLATE 压缩所有贴图文件，以减小包体积
D) 把所有绝对路径转换为相对于包的锚定路径，并在压缩之前把外部 Alembic reference 摊平/本地化进 payload 中

---

**Q26.** 某位管线工程师写了一个 `.usd` 扩展名的文件，内容是纯 ASCII 文本，随后又在不重命名文件的情况下，通过 USD 的二进制 Crate writer 重新保存了同样的内容。哪种陈述正确描述了这种情形？

A) .usd 扩展名是一个通用容器；实际编码由文件内部的 magic bytes/header 决定，而不是由扩展名决定，因此文本内容或二进制 crate 内容都是合法的
B) 这会失败，因为 .usd 扩展名被专门保留给基于文本的 ASCII layer
C) 这会失败，因为 .usd 扩展名被专门保留给二进制 crate 编码的 layer
D) 转换为 crate 之后必须把文件重命名为 .usdc，否则下游消费者会误解它

---

**Q27.** 某位技术美术使用标准场景导出功能把一个绑定好的角色从 DCC 应用导出到 USD，打算之后重新导入该 DCC 以继续编辑绑定。在这种情形下，关于通过 USD 往返（round-trip）的说法，哪一项是正确的？

A) USD 原生存储 DCC 专有的依赖图节点，因此往返之后仍能完整保留非破坏性的绑定可编辑性
B) USD 的 UsdSkel schema 记录了完整的 DCC 构建历史，因此导入后仍可编辑构建节点
C) 构建历史和非破坏性的过程化绑定节点在 USD 导出/导入中通常不会保留；只有最终得到的关节层级、蒙皮权重和烘焙后的变形数据会被保留
D) 由于 USD 是所有 DCC 原生数据模型的超集，往返在设计上就是无损的

---

**Q28.** 某工作室把某个 DCC 应用作为上游创作工具，希望美术在工作时就能看到托管于 Omniverse Nucleus 的场景的实时更新，并且多位美术的编辑能以非破坏性方式合并。哪种交付方式最能满足这一要求？

A) 定期把场景导出为单个 .usdc 文件，并在每位美术完成后手动重新上传到 Nucleus
B) 为该 DCC 使用 Omniverse Connector，直接创作到 Nucleus 上的 live session，利用 USD 的非破坏性分层实现并发编辑
C) 从 DCC 导出 FBX，再用批处理离线转换脚本转换成 USD
D) 每次会话结束后把场景打包成 USDZ，并通过共享网络驱动器分发

---

**Q29.** 位于 `/project/shots/010/anim.usda` 的 layer 中包含一个 reference `@../../assets/props/chair.usd@`。当使用默认 resolver 直接打开该 layer 时，该 reference 路径是如何解析的？

A) 作为 search-path（非锚定）reference 解析，需要 ArResolver 的 search-path 列表才能在磁盘任意位置定位 chair.usd
B) 如果没有针对该 pipeline 的专用资产 resolver 插件就无法解析，因为默认 resolver 不支持相对路径
C) 作为从文件系统根开始的绝对路径解析，导致 resolver 去查找 `/../../assets/props/chair.usd`
D) 作为锚定相对路径解析，相对于包含 anim.usda 的目录，得到 `/project/assets/props/chair.usd`

---

**Q30.** 在 QA 期间，由自定义打包脚本创建的 USDZ 包在多个符合 USDZ 规范的查看器中都无法打开，尽管同样的 USD 内容以散装文件形式可以正常打开。检查发现该 zip 归档使用了 DEFLATE 压缩，且第一个条目在归档中的字节偏移没有按 64 字节对齐。在多个符合规范的查看器中都失败，最可能的原因是什么？

A) USDZ 查看器会忽略 zip 的对齐与压缩，因此失败与之无关，很可能是缺少 default prim 导致的
B) USDZ 支持 DEFLATE 压缩，但只用于贴图文件而非 USD layer，因此只需让 layer 文件的偏移避免错位
C) 64 字节对齐要求只适用于包内嵌的音频和视频资源，而不适用于 USD layer
D) USDZ 要求 zip 条目以未压缩方式存储并对齐到特定字节边界，以便查看器直接对内容做内存映射；违反这一点就会让符合规范的读取器失效

---

**Q31.** 某个管线工具需要在一个由多个 sublayer 组合而成的 stage 上，把 prim 从 /World/Geo/OldName 重命名为 /World/Geo/NewName，并且 stage 中任何指向 /World/Geo/OldName（或其后代）的 relationship 目标或属性 connection，都必须自动更新到新路径并跨所有参与的 layer 生效。应该选择哪个 API？

A) 在 stage 的 root layer 上调用一次 Sdf.Layer.Apply(SdfBatchNamespaceEdit)
B) 对 stage.GetPrimAtPath() 返回的 prim 调用 Usd.Prim.SetName()
C) 用 Usd.EditContext 设置编辑目标，然后用 Sdf.CopySpec 把 prim spec 复制到新路径
D) Usd.NamespaceEditor，先调用 RenamePrim()，再调用 ApplyEdits()

---

**Q32.** 你正在用 Python 创作某个绑定的局部变换，希望 Maya、Houdini 和 Omniverse Kit 都能以完全相同的方式解释 pivot、rotation 和 scale，而没有任何 DCC 特有的重新解释。哪种创作方式能保证这种规范的、跨应用兼容的 xformOpOrder？

A) 按你希望的求值顺序调用 UsdGeom.Xformable(prim).AddRotateXYZOp() 和 AddScaleOp()
B) 直接把 'xformOpOrder' 属性创作为 Vt.TokenArray，按任何方便的顺序列出各个 op
C) 在同一个 prim 上分别创作 xformOp:translate 与 xformOp:transform（4x4 矩阵）op，并让 USD 自行解析优先级
D) 使用 UsdGeom.XformCommonAPI(prim).SetXformVectors() 来设置 translation、rotation、scale 和 pivot

---

**Q33.** 属性 'points' 已经在第 1 到 24 帧创作了 time samples。在之后的某个管线环节中你运行了：attr.Set(Vt.Vec3fArray([...]))，没有传时间参数。随后在 UsdTimeCode(12) 处查询 stage，UsdAttribute.Get() 返回什么值？

A) 后来那次 Set() 调用传入的值，因为最近创作的 opinion 总是获胜，与时间无关
B) 来自第 1-24 帧已有 time samples 的插值值，不受后来那次调用的影响，因为那次调用只创作了默认值
C) 报错，因为不能在已经有 time samples 的属性上创作默认值
D) 默认值与第 12 帧插值 time-sample 值的平均值

---

**Q34.** 某个管线校验脚本需要遍历 stage，并访问每一个 prim —— 与 stage.Traverse() 的默认行为一致：跳过 inactive prim、undefined overs、abstract 类以及未加载的 payload —— 但作者希望把判定条件显式写在代码里以提高清晰度。哪种调用与 stage.Traverse() 的默认行为等价？

A) stage.TraverseAll()
B) Usd.PrimRange.Stage(stage, Usd.TraverseInstanceProxies())
C) Usd.PrimRange(stage.GetPseudoRoot(), Usd.PrimDefaultPredicate)
D) stage.Traverse(Usd.PrimIsActive)

---

**Q35.** 你需要确定属性 'displayColor' 是否在某个特定 sublayer（contents.usda）中被直接创作了 opinion，与其它 sublayer 或 session layer 中更强的 opinion 无关。哪种做法能正确回答这个问题？

A) 把编辑目标设为 contents.usda 之后，调用 stage.GetEditTarget().GetLayer().GetAttributeAtPath(path)
B) 把 contents.usda 直接作为 Sdf.Layer 打开，并调用 layer.GetAttributeAtPath(path) 检查它的 spec
C) prim.GetAttribute('displayColor').Get()，因为 GetAttribute() 返回从该 layer 可见的值
D) stage.GetPrimAtPath(primPath).GetAttribute('displayColor').HasAuthoredValue()

---

**Q36.** 在 UsdImagingGLEngine 使用的 Hydra 渲染架构中，哪个组件负责把组合后的 USD prim 转换成 Hydra 内部的 Rprim/Sprim 表示，并注册到 render index 中？

A) Scene Delegate（UsdImagingDelegate）
B) Render Delegate（例如 HdStormRendererPlugin）
C) Render Index
D) Hydra Engine（UsdImagingGLEngine）

---

**Q37.** 某个管线工具必须把 look-dev 的 override opinions 创作到某个特定 sublayer 'look_overrides.usda' 中，该 sublayer 是 stage root layer 的 subLayerPaths 所列的若干 sublayer 之一。工具在这一段代码运行结束后，不得永久改变同一脚本中后续无关代码的创作位置。哪种代码能正确地把创作限定在该 sublayer 上，且仅限于这段编辑期间？

A) sublayer = Sdf.Layer.FindOrOpen(sublayer_path)
stage.SetEditTarget(Usd.EditTarget(sublayer))
prim = stage.DefinePrim('/World/Mesh')
prim.GetAttribute('displayColor').Set(color_val)
B) sublayer = Sdf.Layer.FindOrOpen(sublayer_path)
with Usd.EditContext(stage, Usd.EditTarget(sublayer)):
    prim = stage.DefinePrim('/World/Mesh')
    prim.GetAttribute('displayColor').Set(color_val)
C) sublayer = Sdf.Layer.FindOrOpen(sublayer_path)
prim_spec = Sdf.CreatePrimInLayer(sublayer, '/World/Mesh')
prim_spec.specifier = Sdf.SpecifierDef
attr_spec = Sdf.AttributeSpec(prim_spec, 'displayColor', Sdf.ValueTypeNames.Color3fArray)
attr_spec.default = color_val
D) root_layer = stage.GetRootLayer()
root_layer.subLayerPaths.append(sublayer_path)
prim = stage.DefinePrim('/World/Mesh')
prim.GetAttribute('displayColor').Set(color_val)

---

**Q38.** 在数字孪生流水线中，你必须创作一个自定义的逐面-顶点 primvar，名为 'temperature'（在 UsdGeom.Mesh 的每个面-顶点上采样一个 float 值），以便 Hydra render delegate 在渲染时能够正确消费它。哪种代码能正确创建并填充这个 primvar？

A) primvarsAPI = UsdGeom.PrimvarsAPI(mesh)
pv = primvarsAPI.CreatePrimvar('temperature', Sdf.ValueTypeNames.FloatArray, UsdGeom.Tokens.faceVarying)
pv.Set(temp_values)
B) primvarsAPI = UsdGeom.PrimvarsAPI(mesh)
pv = primvarsAPI.CreatePrimvar('temperature', Sdf.ValueTypeNames.FloatArray, UsdGeom.Tokens.constant)
pv.Set(temp_values)
C) attr = mesh.GetPrim().CreateAttribute('temperature', Sdf.ValueTypeNames.FloatArray)
attr.Set(temp_values)
D) primvarsAPI = UsdGeom.PrimvarsAPI(mesh)
pv = primvarsAPI.CreatePrimvar('temperature', Sdf.ValueTypeNames.FloatArray, UsdGeom.Tokens.faceVarying, elementSize=3)
pv.Set(temp_values)

---

**Q39.** 在一个 USD stage 中，某个 prim 的 diffuseColor 属性有创作于以下四处的直接 opinions：(1) stage 的 root layer 中直接创作在该 prim 上的 local opinion，(2) 通过 'inherits' arc 引用的 class prim，(3) 被引用资产的 layer，(4) 一个 'specializes' arc 的目标。不存在 variant 或 session layer opinions。按照 LIVRPS 组合强度排序，哪一个 opinion 决定最终的组合值？

A) specializes arc 目标上的 opinion，因为 specializes 总是覆盖共享库资产的本地编辑
B) 被引用资产 layer 上的 opinion，因为 references 在本地编辑生效之前就被解析
C) 直接创作在 local layer stack 中该 prim 自身上的 opinion
D) 通过 inherits arc 从 class prim 继承而来的 opinion，因为 class 的用途就是强制全工作室范围的默认值

---

**Q40.** 某位 lookdev 美术在 stage 上使用 purpose="guide" 创作了不可渲染的绑定辅助几何体。在使用 Hydra render delegate 进行最终批量渲染时，guide 几何体却意外出现在了渲染帧中。最可能的原因是什么，正确修复方法又是什么？

A) 渲染通道的 included-purposes 列表被配置成了 ["default", "render", "proxy", "guide"]，而不是典型的 ["default", "render"]；修复方法是从渲染设置的 includedPurposes 中移除 guide（以及 proxy）
B) guide purpose 在当前的 USD 版本中已被弃用；该美术本应改用 purpose="proxy"，后者总是会被排除在渲染之外
C) guide 会在导出时被烘焙进几何体，无法在渲染时过滤；修复需要把 guide prim 重新创作为 visibility="invisible"
D) 必须把 stage 的 defaultPrim 设置为排除任何包含 guide-purpose prim 的子树，因为 purpose 只在 defaultPrim 之下才生效

---

**Q41.** 某个城市级数字孪生 stage 在 usdview 中打开要花掉超过一分钟，而美术只想查看一栋建筑。所有大型环境资产（道路、植被、背景建筑）都是通过普通 reference arc 引入的。哪种改动最能缩短该工作流的 stage 打开时间？

A) 把所有背景资产的 opinions 移入 session layer，使它们只在内存中求值，而不从磁盘读取
B) 把大型背景资产上的 reference arc 换成 payload arc，使这些子树默认处于未加载状态，并可按需加载
C) 把背景资产转换为 instanceable prim，使 USD 在打开 stage 前对其场景图去重
D) 提高 SdfLayer 文件格式的二进制 crate 版本，让 layer 在打开时解析得更快

---

**Q42.** 某个场景中有 5,000 个 instanceable prim 引用同一个树木资产。美术总监希望每个实例展示四种不同树皮颜色变化中的一种，同时仍能享受 USD 的 instancing 优化（共享 prototype master）。直接在某个实例子树内的后代 mesh 上创作带颜色 opinion 的 'over' 没有任何效果。哪种做法可以在不失去 instancing 的情况下实现逐实例变化？

A) 在每个树木 prim 上设置 instanceable=false，使后代 mesh 上的逐实例 override 生效，并接受相应的内存开销
B) 把颜色 override 移入 session layer，因为 session layer opinions 不受阻止编辑后代 prim 的 instancing 限制
C) 把这四种树皮颜色变化创作为 instanceable prim 上的 variant set，并为每个实例设置不同的 variant selection；选择相同的实例仍然共享同一个 prototype
D) 在指向每个实例的 'specializes' arc 上创作颜色 override，因为 specializes arc 是按实例而不是按 prototype 求值的

---

**Q43.** 某个 stage 包含数百万个 prim。一位管线工程师需要在脚本中打开该 stage，并且只组合 /World/Vehicles/Car_042（及其祖先）这一棵子树，以便做一次快速调试，既不修改磁盘上的任何 layer 文件，也完全不组合无关的 prim。哪种做法是正确的？

A) 用限制到 /World/Vehicles/Car_042 的 UsdStagePopulationMask，通过 UsdStage.OpenMasked()（或 Open() 配合 SetPopulationMask()）打开 stage，使组合过程本身就仅限于该路径及其祖先
B) 正常调用 UsdStage.Open()，然后对每个兄弟 prim 调用 UsdPrim.Unload()，事后把它们从内存中移除
C) 对除包含 Car_042 的 layer 之外的每个 layer 调用 UsdStage.MuteLayer()，把其它 layer 全部 mute
D) 把 UsdStage 的默认 load rules 设置为 UsdStageLoadRules.NoneRule()，然后只对 Car_042 的 payload 手动调用 Load()

---

---



## 实操


### Chapter 1 Lab: The USD Object Model: Stages, Layers, Prims, and Properties


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `labs/chapter-01-lab.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/labs/chapter-01-lab.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Chapter 2 Lab: Schemas, Time Samples, Primvars, and Model Hierarchy


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `labs/chapter-02-lab.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/labs/chapter-02-lab.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Chapter 3 Lab: Composition Arcs: Sublayers, References, and Payloads


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `labs/chapter-03-lab.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/labs/chapter-03-lab.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Chapter 4 Lab: LIVRPS Strength Ordering and List-Editing Operations


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `labs/chapter-04-lab.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/labs/chapter-04-lab.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Chapter 5 Lab: Variant Sets, Inherits, Specializes, and Non-Destructive Overrides


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `labs/chapter-05-lab.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/labs/chapter-05-lab.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Chapter 6 Lab: Component and Assembly Asset Design for Aggregation


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `labs/chapter-06-lab.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/labs/chapter-06-lab.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Chapter 7 Lab: Native (Prototype) Instancing and Point Instancing


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `labs/chapter-07-lab.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/labs/chapter-07-lab.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Chapter 8 Lab: File Formats, USDZ Packaging, and Asset Resolution


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `labs/chapter-08-lab.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/labs/chapter-08-lab.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Chapter 9 Lab: Authoring Stages with Usd, Sdf, Gf, and Vt in Python


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `labs/chapter-09-lab.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/labs/chapter-09-lab.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Chapter 10 Lab: Stage Traversal, Programmatic Composition Editing, and Hydra Basics


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `labs/chapter-10-lab.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/labs/chapter-10-lab.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Chapter 11 Lab: Debugging Composition with usdview and Optimizing Scenes at Scale


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `labs/chapter-11-lab.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/labs/chapter-11-lab.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


### Chapter 12 Lab: Full Practice Exam Simulation and Time-Management Strategy


> 来源：`aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026` · `labs/chapter-12-lab.md` · [原文链接](https://github.com/aseemmankotia/course-nvidia-ncp-ousd-openusd-development-2026/blob/main/labs/chapter-12-lab.md) · 语言：英文原文（未中译）



> ⚠️ 本篇为英文原文，未做中译（代码占比高，属动手实操材料）。请通过上方原文链接查看完整内容。

---


