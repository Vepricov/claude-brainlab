"use strict";
const assert = require("node:assert/strict");
const vm = require("node:vm");
const { replaceRanges } = require("../scripts/build_showcase_locales.cjs");
// Unicode offsets and embedded expressions must survive the build exactly.
const source = 'const emoji="🌟"; const text=`До ${name} после`;';
const before = source.indexOf("До "), after = source.indexOf(" после");
const result = replaceRanges(source, [
  {start:before,end:before+3,source:"До ",type:"TemplateElement",id:"before"},
  {start:after,end:after+6,source:" после",type:"TemplateElement",id:"after"},
], key => key === "before" ? "Before " : " after `code` ${literal}");
assert.equal(vm.runInNewContext(`${result}; text`, {name:"Hermes"}), "Before Hermes after `code` ${literal}");
assert.throws(() => replaceRanges(source, [{start:0,end:3,source:"bad",id:"stale"}], () => "x"), /Invalid/);
console.log("PASS: locale compiler preserves expressions and rejects stale ranges");
