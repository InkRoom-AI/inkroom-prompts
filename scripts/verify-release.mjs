import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
const root=fileURLToPath(new URL('../',import.meta.url));
const read=p=>readFileSync(resolve(root,p),'utf8');
const json=p=>JSON.parse(read(p));
const release=json('release.json'),v=release.version;
assert.match(v,/^\d+\.\d+\.\d+$/,'Stable version required');
assert.equal(json('package.json').version,v);
assert.equal(release.tag, `prompts-v${v}`);
for(const [k,name] of Object.entries(release.artifacts)){if(typeof name==='string')assert.ok(name.includes(v),k);}
assert.equal(release.artifacts.cursorPlugin.version,v);
const lock=json('package-lock.json');assert.equal(lock.version,v);assert.equal(lock.packages[''].version,v);
assert.ok(read('src/server.mjs').includes(`version:'${v}'`),'MCP initialize version');
const skill=read('skills/inkroom-prompts/SKILL.md');assert.ok(skill.startsWith(`---\nversion: ${v}\n`));
// Parent repository mirrors are validated in the canonical repository, not in this standalone export.
const provenance=json('SOURCE_MANIFEST.json');
assert.equal(provenance.version,v);
assert.equal(provenance.canonical.commit,'dd414737e193cacbc9d18ea86ec7d00f4460f543');
for (const file of provenance.files) {
 const bytes=readFileSync(resolve(root,file.destination));
 assert.equal(createHash('sha256').update(bytes).digest('hex'),file.distributionSha256,file.destination);
 if(file.policy==='exact') assert.equal(file.distributionSha256,file.canonicalSha256,file.destination);
}
const plugin=json('.cursor-plugin/plugin.json');assert.equal(plugin.version,v);assert.equal(plugin.name,release.product);
assert.equal(provenance.repositoryRole,'one-way-distribution');
assert.equal(read('LICENSE'),read('skills/inkroom-prompts/LICENSE'));
const url=`https://github.com/InkRoom-AI/inkroom-client/releases/download/prompts-v${v}/inkroom-prompts-${v}.tgz`;
assert.equal(plugin.mcpServers['inkroom-prompts'].args[2],url);
assert.equal(json('examples/mcp.json').mcpServers['inkroom-prompts'].args[2],url);
for(const f of ['README.md','README.zh-CN.md'])assert.ok(read(f).includes(url),f);
assert.ok(!plugin.variables&&!plugin.mcpServers['inkroom-prompts'].env&&!plugin.mcpServers['inkroom-prompts'].headers,'Keyless configuration');
console.log(`Release ${v}: package, lock, MCP, standalone provenance, licenses, Cursor and canonical install URLs consistent.`);

for (const file of provenance.additions) {
 assert.equal(createHash('sha256').update(readFileSync(resolve(root,file.path))).digest('hex'),file.sha256,file.path);
}
