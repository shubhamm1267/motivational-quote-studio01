import test from 'node:test';
import assert from 'node:assert/strict';
import {TEMPLATES,chooseTemplate,templateFormat,enrichLocalPost,VALID_TEMPLATES} from '../backend/templates.mjs';
import {getSeed,localPost,CATEGORIES} from '../backend/facts.mjs';
test('18 distinct editorial templates plus legacy dark style and Auto',()=>{
 assert.equal(TEMPLATES.length,18);
 assert.equal(new Set(TEMPLATES.map(t=>t.id)).size,18);
 for(const t of TEMPLATES)assert.ok(VALID_TEMPLATES.has(t.id));
 assert.ok(VALID_TEMPLATES.has('classic_dark'));
});
test('Auto template choices are grounded in the requested category',()=>{
 for(let i=0;i<20;i++){
  const t=chooseTemplate('auto','relationships');
  assert.ok(['ghosted','heart','expectations','dialogue'].includes(t));
 }
});
test('local fallback enriches reference formats without a Gemini key',()=>{
 const src=localPost(getSeed('life'),'en');
 const post=enrichLocalPost(src,'life','underrated','en');
 assert.ok(post.headline.length>8);
 assert.ok(post.items.length>=8);
 assert.ok(post.highlights.length>0);
 assert.equal(post.template,'underrated');
 assert.equal(templateFormat('underrated'),'numbered');
});
test('new categories contain fallback seeds',()=>{
 for(const cat of ['gratitude','maturity','boundaries','reality','affirmation','positivity']){
  assert.ok(CATEGORIES.some(c=>c.id===cat));
  assert.ok(getSeed(cat));
 }
});
