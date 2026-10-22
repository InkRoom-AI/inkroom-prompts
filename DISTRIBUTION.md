# InkRoom Prompts MCP — 来源、安装与同步

`InkRoom-AI/inkroom-prompts` 是免费提示词 MCP 的独立产品分发仓库；它与图片 MCP `inkroom` 分开维护市场身份，共享品牌主源的正式版本。

唯一主源：`InkRoom-AI/inkroom-client/prompts`；正式标签 `prompts-v1.0.4`，固定提交 `dd414737e193cacbc9d18ea86ec7d00f4460f543`。运行时、依赖锁、Skill、许可、Docker 与后端附带源码均保留原字节。`SOURCE_MANIFEST.json` 逐文件记录主源与分发 SHA256。分发只调整仓库身份、说明和独立目录的验证路径，另附主源两处过期工具数量断言的修复补丁。

## 本地验证与安装

需要 Node.js 20.3+，先进入本目录；不使用 `.env`、Key、Token 或账号。

```sh
npm ci --ignore-scripts --no-audit --no-fund
npm test
node scripts/verify-release.mjs
node src/cli.mjs --help
npm pack --dry-run
```

客户端使用本地实际路径：

```json
{"mcpServers":{"inkroom-prompts":{"command":"node","args":["/ABSOLUTE/PATH/inkroom-prompts/src/cli.mjs"]}}}
```

`/ABSOLUTE/PATH` 必须替换为本机目录。已存在的品牌正式发行包安装链接继续使用，不声明 npm Registry 已发布，也不构造新仓下载链接。

工具名称固定为 `help`、`list_models`、`search_prompts`、`optimize_prompt`。前三项只读；优化使用现有免费服务配额，可能消耗平台模型资金，离线验收仅使用 mock，不调用真实优化或生图。无公共 Remote MCP 地址；不得填写虚构 `cloudEndpoint`。

## 单向更新规则

1. 业务修改、测试、版本与许可先在品牌主源完成；不在分发仓单独改运行时，不反向同步。
2. 固定一个已审核的正式 tag、commit 和完整文件 SHA 清单，使用离线导出脚本生成全新目录。脚本无网络/Git 写入且拒绝覆盖已有目录。后续版本须审核更新固定来源与清单，不能直接读取浮动 main。
3. 仅允许声明过的 metadata/layout 适配，保留原安装来源、许可、免费 Skill、官网锚点与既有待审包；同一产品各分发载体运行版本一致。
4. 每次分发更新提交来源清单、adapter 差异、测试结果和固定用户手册更新；市场任务复核后再合并推送。不得自动发布、自动重投待审条目或覆盖图片 MCP `inkroom`。
5. 市场 MCP 显示名用 `InkRoom Prompts MCP`，中文 `InkRoom 免费提示词 MCP`，稳定 identifier 保持 `inkroom-prompts`。免费 Skill 仍是独立市场实体，不批量更名或重建现有条目。

长期维护材料随源码保存在 `scripts/prepare_distribution.py`、`canonical-files.json`、`SOURCE_MANIFEST.json` 与本文件。已保存主源归档后，在本仓根目录执行一条离线命令：

```sh
python3 scripts/prepare_distribution.py --archive /ABSOLUTE/PATH/canonical-tag.tar.gz --output /ABSOLUTE/PATH/new-distribution
```

输出为全新的目录和同级 `new-distribution-review` 审查目录；已有目录不会覆盖。当前脚本只接受本次审核的 1.0.4 文件 SHA，拒绝字节变化、遗漏或重复文件。下次正式版本先审核并更新来源 commit/tag、完整 SHA 清单及适配规则，再重新执行；此命令不下载来源、不提交、不推送、不创建仓库、不发布市场，也不触发模型调用。

MIT 许可完整保留；第三方提示词与示例图不随代码许可转授。分发源码不包含生产配置、凭据或服务数据库。源码和本地测试记录不代表市场受理、公开、安装验收或网站 sameAs 上线。
