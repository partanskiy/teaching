/* Static catalogue: local data, relative PDF links, no network requests. */
'use strict';
(() => {
  const bank = window.BANK;
  const byId = new Map(bank.tasks.map(t => [t.id, t]));
  const normalizedIds = new Set(bank.tasks.map(t => t.id.toLocaleLowerCase('ru')));
  const docById = new Map(bank.documents.map(d => [d.id, d]));
  const $ = id => document.getElementById(id);
  const roles = {tasks:'Условия',solutions:'Решения',combined:'Условия и решения',criteria:'Критерии',requirements:'Требования',regulations:'Распорядительный документ',methodology:'Методические рекомендации',shared_statement:'Общее условие для нескольких классов'};
  const stages = {regional:'ВсОШ: региональный',municipal:'ВсОШ: муниципальный',main:'МОШ: основной тур'};
  const reviews = {automatic:'Предварительная разметка',statement_reviewed:'Условие прочитано',solution_reviewed:'Условие и решение сверены'};
  const provenance = {organizer:'Организатор или составители',federal_publisher:'Федеральная публикация',archive_mirror:'Архивная копия официального материала'};
  const el = (tag, cls, text) => {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const link = (text, href) => {
    const a = el('a', '', text); a.href = href; return a;
  };
  function options(id, values, all) {
    const select = $(id);
    select.replaceChildren(el('option','',all));
    select.firstChild.value = '';
    values.forEach(([value, name]) => {
      const option = el('option','',name); option.value = value; select.append(option);
    });
  }
  const unique = values => [...new Set(values)].filter(v => v !== null && v !== undefined);
  options('stage', Object.entries(stages), 'Все этапы');
  options('season', unique(bank.tasks.map(t => t.academic_year)).sort().reverse().map(v => [v,v]), 'Все годы');
  options('region', unique(bank.tasks.map(t => t.region)).sort((a,b) => a.localeCompare(b,'ru')).map(v => [v,v]), 'Все регионы');
  options('topic', [...Object.entries(bank.topics),['unclassified','Тема пока не определена']], 'Все темы');
  options('method', Object.entries(bank.methods), 'Все приемы');
  options('form', Object.entries(bank.forms), 'Все формы');
  options('variant', [['none','Без номера варианта'], ...unique(bank.tasks.map(t => t.variant)).sort().map(v => [v,'Вариант '+v])], 'Все варианты');
  options('drole', Object.entries(roles).filter(([k]) => k!=='shared_statement'), 'Все роли');
  const dayLabel = el('label','','День регионального этапа');
  const daySelect = el('select'); daySelect.id = 'day'; dayLabel.append(daySelect);
  $('tasks').querySelector('.filters').append(dayLabel);
  options('day', [['1','Первый день'],['2','Второй день']], 'Все дни');
  const stats = bank.statistics;
  [[stats.documents,'документов'],[stats.regional_tasks+stats.mosh_tasks,'задач исследованного ядра'],[stats.municipal_regions,'регионов муниципального банка'],[stats.lessons,'занятия по 90 минут']].forEach(([value,label]) => {
    const item = el('div','stat'); item.append(el('strong','',String(value)),el('span','',label)); $('stats').append(item);
  });
  let limit = 100;
  let currentTab = 'tasks';
  function tab(name) {
    currentTab = name;
    ['tasks','documents','lessons'].forEach(key => $(key).hidden = key!==name);
    document.querySelectorAll('nav button').forEach(button => button.classList.toggle('active',button.dataset.tab===name));
  }
  document.querySelectorAll('nav button').forEach(button => button.addEventListener('click',() => tab(button.dataset.tab)));
  function sourceFor(t, solution=false) {
    const priorities = solution ? ['solutions','combined','criteria'] : ['shared_statement','tasks','combined'];
    return priorities.map(role => t.sources.find(s => s.role===role)).find(Boolean) || t.sources[0];
  }
  function pdf(text, source) {return link(text,source.path+'#page='+source.page);}
  function taskCard(t) {
    const card = el('article','card');
    card.append(el('div','meta',t.id+' / '+stages[t.stage]));
    card.append(el('h2','',t.summary || 'Задача '+t.number+'. Условие в оригинальном PDF'));
    const variant = t.variant ? ' / вариант '+t.variant : '';
    const day = t.day && t.stage==='regional' ? ' / день '+t.day : '';
    card.append(el('p','meta',t.academic_year+' / '+t.region+day+variant));
    const tags = el('div','tags');
    t.topics.forEach(topic => tags.append(el('span','tag topic',bank.topics[topic] || 'Тема не определена')));
    t.methods.forEach(method => tags.append(el('span','tag',bank.methods[method] || method)));
    if(t.reserve) tags.append(el('span','tag reserve','Контрольный резерв'));
    card.append(tags);
    card.append(el('p','meta',reviews[t.review_status]+' / '+bank.forms[t.form]+(t.difficulty ? ' / учебный уровень '+t.difficulty : '')));
    if(t.lessons.length) card.append(el('p','meta','Занятия: '+t.lessons.map(l => l.lesson+(l.role==='homework' ? ' (дома)' : ' (класс)')).join(', ')));
    const actions = el('div','actions');
    actions.append(pdf('Условие PDF',sourceFor(t)));
    if(t.sources.some(s => ['solutions','combined','criteria'].includes(s.role))) actions.append(pdf('Решение или критерии PDF',sourceFor(t,true)));
    card.append(actions);
    const details = el('details'); details.append(el('summary','','Публикации и исходные ссылки ('+t.sources.length+')'));
    const list = el('ul','source-list');
    t.sources.forEach(s => {
      const row = el('li');
      const d = docById.get(s.document_id);
      row.append(pdf(roles[s.role] || s.role,s),document.createTextNode(' / стр. '+s.page+' / '+s.region+' / '),link('Источник',s.url));
      if(d) row.append(el('span','',' / '+(provenance[d.provenance] || d.provenance)));
      list.append(row);
    });
    details.append(list); card.append(details); return card;
  }
  function matches(t) {
    const q = $('q').value.trim().toLocaleLowerCase('ru');
    const text = [t.id,t.summary,t.region,...t.topics.map(k => bank.topics[k] || k),...t.methods.map(k => bank.methods[k] || k)].join(' ').toLocaleLowerCase('ru');
    if(normalizedIds.has(q) && t.id.toLocaleLowerCase('ru')!==q) return false;
    if(q && !text.includes(q)) return false;
    for(const [id,key] of [['stage','stage'],['season','academic_year'],['region','region'],['form','form']]) if($(id).value && $(id).value!==t[key]) return false;
    if($('day').value && (t.stage!=='regional' || String(t.day)!==$('day').value)) return false;
    if($('topic').value && !t.topics.includes($('topic').value)) return false;
    if($('method').value && !t.methods.includes($('method').value)) return false;
    const review = $('review').value;
    if(review && (review==='reviewed' ? t.review_status==='automatic' : t.review_status!==review)) return false;
    const variant = $('variant').value;
    if(variant && (variant==='none' ? t.variant!==null : String(t.variant)!==variant)) return false;
    if($('use').value==='course' && !t.lessons.length) return false;
    if(t.reserve && !$('reserve').checked) return false;
    return true;
  }
  function renderTasks() {
    const tasks = bank.tasks.filter(matches);
    $('count').textContent = 'Найдено '+tasks.length+' задач. Показано '+Math.min(limit,tasks.length)+'.';
    $('cards').replaceChildren(...tasks.slice(0,limit).map(taskCard));
    if(!tasks.length) $('cards').append(el('p','empty','Под эти фильтры задач нет. Измените фильтры или включите контрольный резерв.'));
    $('more').hidden = tasks.length<=limit;
  }
  ['q','stage','season','region','topic','method','form','review','variant','use','day','reserve'].forEach(id => $(id).addEventListener(id==='q' ? 'input' : 'change',() => {limit=100;renderTasks();}));
  $('more').addEventListener('click',() => {limit+=100;renderTasks();});
  function renderFiles() {
    const q = $('dq').value.trim().toLocaleLowerCase('ru');
    const docs = bank.documents.filter(d => (!$('drole').value || d.role===$('drole').value) && (!q || [d.path,d.academic_year,d.region,roles[d.role]].join(' ').toLocaleLowerCase('ru').includes(q)));
    $('dcount').textContent = 'Найдено '+docs.length+' файлов.';
    $('files').replaceChildren(...docs.map(d => {
      const row = el('article','file'); row.append(el('h3','',d.path.split('/').at(-1).replace(/^[a-f0-9]{14}_/,'')));
      row.append(el('p','meta',d.academic_year+' / '+d.region+' / '+(stages[d.stage]||d.stage)+' / '+(roles[d.role]||d.role)+' / классы '+d.grade_scope.join(', ')+(d.days.length ? ' / дни для 10 класса: '+d.days.join(', ') : '')));
      row.append(el('p','meta',(provenance[d.provenance]||d.provenance)+' / '+(d.bytes/1024).toFixed(0)+' KiB / SHA256 '+d.sha256));
      const actions = el('div','actions'); actions.append(link('Открыть файл',d.path),link('Исходный файл',d.url));
      if(d.source_page) actions.append(link('Страница публикации',d.source_page));
      if(d.extraction_status!=='text') actions.append(el('span','','Требуется чтение PDF вручную'));
      row.append(actions); return row;
    }));
  }
  $('dq').addEventListener('input',renderFiles); $('drole').addEventListener('change',renderFiles);
  function jump(id) {
    ['q','stage','season','region','topic','method','form','review','variant','use','day'].forEach(key => $(key).value='');
    $('q').value=id; $('reserve').checked=Boolean(byId.get(id).reserve);limit=100;
    tab('tasks');renderTasks();$('count').scrollIntoView({behavior:'smooth',block:'start'});
  }
  bank.lessons.forEach(l => {
    const article=el('article','lesson');
    article.append(el('div','meta',l.month+' / 90 минут / '+bank.blocks[l.block]),el('h2','',l.number+'. '+l.title),el('p','',l.goal));
    [['classroom','В классе'],['homework','Дома']].forEach(([key,title]) => {
      if(!l[key].length)return;
      article.append(el('p','',title+':'));const list=el('ul');
      l[key].forEach(id => {
        const task=byId.get(id); const row=el('li'); const button=el('button','task-jump',id);button.type='button';button.addEventListener('click',() => jump(id));
        row.append(button,document.createTextNode(': '+(task.summary||'Условие в PDF')));list.append(row);
      });article.append(list);
    });article.append(el('p','note',l.notes));$('lesson-list').append(article);
  });
  renderTasks();renderFiles();
})();
