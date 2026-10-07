#!/usr/bin/env node
// Refresh literal source ranges using the same parser as the browser-test toolchain.
const fs=require('node:fs'),crypto=require('node:crypto'),path=require('node:path');
const {babelParse}=require(path.join(path.dirname(require.resolve(process.env.PLAYWRIGHT_MODULE || 'playwright')), 'lib/transform/babelBundle.js'));
const root=path.resolve(__dirname,'..');
const files={'app.js':'ui-app','memory-map.js':'ui-memory','surface-pages.js':'ui-surfaces','obsidian-setup.js':'ui-surfaces','data/system-examples.js':'scenarios','search-core.js':'search-core','data/atlas-tree.js':'demo-data','data/base-snapshot.js':'demo-data','data/library-snapshot.js':'demo-data','data/demo-flag.js':'demo-data','data/project-workspaces.js':'demo-data'};
const groups={},manifest={};
for(const [file,group] of Object.entries(files)){
 const source=fs.readFileSync(path.join(root,'docs/lab-showcase',file),'utf8');const ast=babelParse(source,file);const ranges=[];
 function walk(node,parent,preserve=false){
  if(!node||typeof node!=='object')return;
  if(file==='app.js'&&node.type==='VariableDeclarator'&&['LIB_SYN','stop','searchConcepts'].includes(node.id?.name))preserve=true;
  const value=node.type==='StringLiteral'?node.value:node.type==='TemplateElement'?node.value.cooked:null;
  if(typeof value==='string'&&/[А-Яа-яЁё]/.test(value)){
   const id=crypto.createHash('sha256').update(value).digest('hex').slice(0,12),entries=groups[group]||=(new Map());
   if(!entries.has(id))entries.set(id,{id,text:value,paths:[]});entries.get(id).paths.push(file+':'+node.loc.start.line);
   ranges.push({start:node.start,end:node.end,type:node.type,id,source:source.slice(node.start,node.end),...(preserve?{preserve:true}:{})});
  }
  for(const [key,child]of Object.entries(node)){if(['loc','start','end','extra','comments','tokens'].includes(key))continue;if(Array.isArray(child))child.forEach(x=>walk(x,node,preserve));else if(child&&typeof child==='object')walk(child,node,preserve)}
 }
 walk(ast,null);manifest[file]={group,sha256:crypto.createHash('sha256').update(source).digest('hex'),ranges};
}
for(const [group,entries]of Object.entries(groups)){
 fs.writeFileSync(path.join(root,'localization/source',group+'.json'),JSON.stringify({group,entries:[...entries.values()]},null,2)+'\n');
 console.log(group,entries.size,[...entries.values()].reduce((n,x)=>n+x.text.length,0));
}
fs.writeFileSync(path.join(root,'localization','ranges.json'),JSON.stringify(manifest,null,2)+'\n');
