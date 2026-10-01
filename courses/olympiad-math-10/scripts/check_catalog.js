/* Exercise offline catalogue rendering and filters against the delivered data. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname,'..');
const nodes = new Map();
class Element {
  constructor(tag) {this.tagName=tag;this.children=[];this.listeners={};this.value='';this.checked=false;this.hidden=false;this.dataset={};this.classList={toggle(){}};this.textContent='';}
  set id(value) {this._id=value;nodes.set(value,this);}
  get id() {return this._id;}
  get firstChild() {return this.children[0];}
  append(...items) {this.children.push(...items);}
  replaceChildren(...items) {this.children=[...items];}
  addEventListener(name,handler) {this.listeners[name]=handler;}
  querySelector(selector) {assert.equal(selector,'.filters');return new Element('div');}
  scrollIntoView() {}
  fire(name) {assert.ok(this.listeners[name],`Missing ${name} listener`);this.listeners[name]();}
}
for(const id of ['tasks','documents','lessons','q','stage','season','region','topic','method','form','review','variant','use','reserve','dq','drole','stats','count','cards','more','dcount','files','lesson-list']){
  const element=new Element('div');element.id=id;
}
const buttons=['tasks','documents','lessons'].map(tab => {const b=new Element('button');b.dataset.tab=tab;return b;});
const document={
  getElementById:id=>nodes.get(id),
  createElement:tag=>new Element(tag),
  createTextNode:text=>({textContent:text}),
  querySelectorAll:selector=>{assert.equal(selector,'nav button');return buttons;}
};
const context=vm.createContext({window:{},document});
vm.runInContext(fs.readFileSync(path.join(root,'site/data.js'),'utf8'),context);
vm.runInContext(fs.readFileSync(path.join(root,'site/app.js'),'utf8'),context);
const get=id=>nodes.get(id);
const bank=context.window.BANK;
assert.equal(get('cards').children.length,100);
assert.equal(get('files').children.length,bank.documents.length);
assert.equal(get('lesson-list').children.length,34);
get('q').value='R-2026-10.1';get('q').fire('input');
assert.match(get('count').textContent,/Найдено 0 задач/);
get('reserve').checked=true;get('reserve').fire('change');
assert.equal(get('cards').children.length,1);
get('q').value='';get('q').fire('input');get('stage').value='regional';get('stage').fire('change');
assert.match(get('count').textContent,/Найдено 154 задач/);
get('day').value='2';get('day').fire('change');
assert.match(get('count').textContent,/Найдено 77 задач/);
get('day').value='';get('day').fire('change');get('stage').value='';get('stage').fire('change');
get('use').value='course';get('use').fire('change');
assert.match(get('count').textContent,/Найдено 101 задач/);
get('drole').value='methodology';get('drole').fire('change');assert.equal(get('files').children.length,1);
buttons[2].fire('click');assert.equal(get('lessons').hidden,false);assert.equal(get('tasks').hidden,true);
console.log('Offline catalogue passed: rendering, reserve, exact ID, day, course and document filters.');
