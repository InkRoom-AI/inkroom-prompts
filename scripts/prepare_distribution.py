#!/usr/bin/env python3
"""Offline, fail-closed export of a reviewed canonical product snapshot. No Git/network writes."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import tarfile

PLAN = Path(__file__).resolve().parent.parent
COMMIT = 'dd414737e193cacbc9d18ea86ec7d00f4460f543'
TAG = 'prompts-v1.0.4'
SOURCE = 'https://github.com/InkRoom-AI/inkroom-client'
TARGET = 'https://github.com/InkRoom-AI/inkroom-prompts'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def prepare(archive, output):
    expected = json.loads((PLAN / 'canonical-files.json').read_text())
    wanted = {row['source']: row for row in expected}
    original = {}
    modes = {}
    with tarfile.open(archive) as tf:
        for member in tf.getmembers():
            path = Path(member.name)
            if '..' in path.parts or path.is_absolute():
                raise ValueError('Unsafe archive path')
            relative = '/'.join(path.parts[1:])
            if relative.startswith('prompts/') and not member.isdir() and relative not in wanted:
                raise ValueError('Unreviewed source member: ' + relative)
            if relative not in wanted:
                continue
            if not member.isfile() or relative in original:
                raise ValueError('Non-regular or duplicate source member')
            data = tf.extractfile(member).read()
            if digest(data) != wanted[relative]['sha256']:
                raise ValueError('Unreviewed source bytes: ' + relative)
            original[relative] = data
            modes[relative] = member.mode & 0o777
    if set(original) != set(wanted):
        raise ValueError('Missing reviewed source files')
    review = output.with_name(output.name + '-review')
    if output.exists() or review.exists():
        raise ValueError('Output already exists; never overwrite a prior candidate')
    output.mkdir(parents=True)
    review.mkdir(parents=True)
    for source, data in original.items():
        dest = output / wanted[source]['destination']
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        dest.chmod(modes[source])

    package = json.loads((output / 'package.json').read_text())
    package['repository'] = {'type': 'git', 'url': TARGET + '.git'}
    package['homepage'] = 'https://inkroom.ai/tools/prompts'
    package['files'] += ['SOURCE_MANIFEST.json', 'DISTRIBUTION.md']
    (output / 'package.json').write_text(json.dumps(package, indent=2) + '\n')
    banner_en = f'''\n> This is the standalone **InkRoom Prompts MCP** distribution, exported one way from the [official {TAG} source]({SOURCE}/tree/{COMMIT}/prompts). Runtime version: **1.0.4**. Runtime and license bytes are preserved; development stays in the canonical repository. See [source provenance, installation and update policy](DISTRIBUTION.md).\n'''
    banner_zh = f'''\n> 本仓为 **InkRoom 免费提示词 MCP** 的独立分发来源，从品牌主仓 [正式 {TAG} 源码]({SOURCE}/tree/{COMMIT}/prompts) 单向导出。运行版本 **1.0.4**，运行代码和许可保持原字节，业务开发统一在主源完成。见[来源、安装与同步规则](DISTRIBUTION.md)。\n'''
    for filename, banner in [('README.md', banner_en), ('README.zh-CN.md', banner_zh)]:
        text = (output / filename).read_text()
        first, rest = text.split('\n', 1)
        text = ('# InkRoom Prompts MCP\n' if filename == 'README.md' else '# InkRoom 免费提示词 MCP\n') + banner + rest
        text = text.replace('git clone https://github.com/InkRoom-AI/inkroom-client.git\ncd inkroom-client/prompts', 'git clone https://github.com/InkRoom-AI/inkroom-prompts.git\ncd inkroom-prompts')
        text = text.replace('Build from either public source repository:', 'Install from this product distribution repository:')
        text = text.replace('Alternatively clone `https://github.com/lijianhui1405/inkroom.git` and open its `prompts` directory. No `.env` or credentials are needed.', 'The canonical development source remains `InkRoom-AI/inkroom-client/prompts`. No `.env` or credentials are needed.')
        text = text.replace('也可使用原公开仓库 `https://github.com/lijianhui1405/inkroom.git` 下相同的 `prompts` 目录。无需填写任何密钥或准备 `.env`。', '统一开发主源仍为 `InkRoom-AI/inkroom-client/prompts`。无需填写任何密钥或准备 `.env`。')
        text = text.replace('`prompts/src/cli.mjs`', '`src/cli.mjs`')
        text = text.replace('预览版没有宣布已上线的官方公网 Remote MCP 地址。', '本地包没有宣布官方公网 Remote MCP 地址。')
        text = text.replace("The same Skill is also mirrored at each repository's top-level `skills/inkroom-prompts` for directories that discover Skills there. Both copies must remain identical.", 'The canonical repository also mirrors this Skill at its top-level `skills/inkroom-prompts`. This distribution retains the exact released Skill under the same relative path.')
        text = text.replace('The repository marketplace includes a separate', 'The canonical repository marketplace includes a separate')
        text = text.replace('| --- | --- | --- |\n| `search_prompts`', '| --- | --- | --- |\n| `help` | No parameters | Local capability and cost-boundary help; no network or model call |\n| `list_models` | No parameters | Public InkRoom model names, parameters and official sale prices; no account authorization implied |\n| `search_prompts`')
        text = text.replace('- Tools: `search_prompts` and `optimize_prompt`.', '- Tools: `help`, `list_models`, `search_prompts`, and `optimize_prompt`.')
        text = text.replace('| --- | --- | --- |\n| 查找提示词', '| --- | --- | --- |\n| `help`（能力说明） | 无参数 | 本地能力与费用边界；不联网、不调用模型 |\n| `list_models`（模型与价格） | 无参数 | 公开模型、参数和 InkRoom 官方售价；不代表账号已获生成权限 |\n| `search_prompts`（查找提示词）')
        text = text.replace('| 优化提示词 |', '| `optimize_prompt`（优化提示词） |')
        (output / filename).write_text(text)

    # The canonical test predates the two public read-only tools. Runtime is untouched.
    p = output / 'test/mcp.test.mjs'
    old = p.read_text()
    new = old.replace("['search_prompts','optimize_prompt']);", "['help','list_models','search_prompts','optimize_prompt']);")
    new = new.replace("(await client.listTools()).tools.length,2", "(await client.listTools()).tools.length,4")
    if new == old:
        raise ValueError('Expected stale test assertions not found')
    p.write_text(new)
    (review / 'upstream-test-fix.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile='a/prompts/test/mcp.test.mjs', tofile='b/prompts/test/mcp.test.mjs')))

    p = output / 'scripts/verify-release.mjs'
    text = p.read_text().replace("import assert from 'node:assert/strict';", "import assert from 'node:assert/strict';\nimport {createHash} from 'node:crypto';")
    text = text.replace("assert.equal(skill,read('../skills/inkroom-prompts/SKILL.md'),'Skill mirror');", "// Parent repository mirrors are validated in the canonical repository, not in this standalone export.\nconst provenance=json('SOURCE_MANIFEST.json');\nassert.equal(provenance.version,v);\nassert.equal(provenance.canonical.commit,'" + COMMIT + "');\nfor (const file of provenance.files) {\n const bytes=readFileSync(resolve(root,file.destination));\n assert.equal(createHash('sha256').update(bytes).digest('hex'),file.distributionSha256,file.destination);\n if(file.policy==='exact') assert.equal(file.distributionSha256,file.canonicalSha256,file.destination);\n}")
    text = text.replace("assert.equal(json('../.cursor-plugin/marketplace.json').plugins.find(p=>p.name===release.product).version,v);", "assert.equal(provenance.repositoryRole,'one-way-distribution');\nassert.equal(read('LICENSE'),read('skills/inkroom-prompts/LICENSE'));")
    text += "\nfor (const file of provenance.additions) {\n assert.equal(createHash('sha256').update(readFileSync(resolve(root,file.path))).digest('hex'),file.sha256,file.path);\n}\n"
    text = text.replace('Skill mirrors, Cursor and install URLs consistent.', 'standalone provenance, licenses, Cursor and canonical install URLs consistent.')
    p.write_text(text)
    template = PLAN / 'distribution-readme.md'
    if not template.exists():
        template = PLAN / 'DISTRIBUTION.md'
    (output / 'DISTRIBUTION.md').write_text(template.read_text())
    (output / 'scripts/prepare_distribution.py').write_bytes(Path(__file__).read_bytes())
    (output / 'canonical-files.json').write_bytes((PLAN / 'canonical-files.json').read_bytes())

    adapted = {'package.json', 'README.md', 'README.zh-CN.md', 'scripts/verify-release.mjs', 'test/mcp.test.mjs'}
    manifest = {'schemaVersion': 1, 'product': 'inkroom-prompts', 'version': '1.0.4', 'repositoryRole': 'one-way-distribution', 'distributionRepository': TARGET, 'canonical': {'repository': SOURCE, 'commit': COMMIT, 'tag': TAG, 'subdirectory': 'prompts'}, 'archiveSha256': digest(Path(archive).read_bytes()), 'files': []}
    for row in expected:
        name = row['destination']
        actual = digest((output / name).read_bytes())
        policy = 'adapter' if name in adapted else 'exact'
        if policy == 'exact' and actual != row['sha256']:
            raise ValueError('Protected file drift: ' + name)
        manifest['files'].append({'source': row['source'], 'destination': name, 'canonicalSha256': row['sha256'], 'distributionSha256': actual, 'policy': policy})
    # All additions are listed, while the manifest itself is covered by the external review receipt.
    manifest['additions'] = [{'path': name, 'sha256': digest((output / name).read_bytes())} for name in ['DISTRIBUTION.md', 'scripts/prepare_distribution.py', 'canonical-files.json']]
    (output / 'SOURCE_MANIFEST.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    patch = []
    for name in sorted(adapted):
        patch.extend(difflib.unified_diff(original['prompts/' + name].decode().splitlines(True), (output / name).read_text().splitlines(True), fromfile='a/' + name, tofile='b/' + name))
    (review / 'distribution-adapter.patch').write_text(''.join(patch))
    print(json.dumps({'files': len(expected), 'exactFiles': len(expected)-len(adapted), 'adapterFiles': len(adapted), 'runtimeChanged': False, 'output': str(output)}, ensure_ascii=False))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.archive, args.output)
