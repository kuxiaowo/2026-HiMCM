/* Export Q4/Q5 synchronized Markdown using Chromium and MathJax SVG.
 * This is a PDF reading copy, not a claim that the .tex compiled successfully.
 * Only document rendering uses the bundled Node runtime; modelling uses conda.
 */
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const { createRequire } = require('module');
const root = path.resolve(__dirname, '../..');
const deps = process.env.CODEX_NODE_MODULES || path.join(process.env.USERPROFILE,
  '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const runtimeRequire = createRequire(path.join(deps, 'playwright/package.json'));
const { chromium } = runtimeRequire('playwright');
const chapter = Number(process.argv[2]);
if (![4,5].includes(chapter)) throw Error('Expected chapter 4 or 5');
const stem = chapter===4?'question4_sensitivity':'question5_evaluation';
const source = path.join(root, 'docs/paper/'+stem+'.md');
const temporary = path.join(root, 'tmp/question45_pdf');
const output = path.join(root, 'output/pdf/'+stem+'.pdf');
const mathjax = path.join(temporary, 'mathjax-3.2.2-tex-svg.js');
fs.mkdirSync(temporary, {recursive:true});
fs.mkdirSync(path.dirname(output), {recursive:true});

function escape(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function inline(s) {
  return escape(s).replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
}
function parse(md) {
  const lines=md.split(/\r?\n/); const parts=[];
  for(let i=0;i<lines.length;i++) {
    const line=lines[i].trim();if(!line||/^# 第[四五]题正式正文$/.test(line)||line.startsWith('计算附件：'))continue;
    if(line==='\\[') {
      const block=[];while(++i<lines.length&&lines[i].trim()!=='\\]')block.push(lines[i]);
      parts.push('<div class="math-block">'+escape('\\[\n'+block.join('\n')+'\n\\]')+'</div>');continue;
    }
    let m=line.match(/^(#{1,3}) (.+)$/);
    if(m){const n=m[1].length;parts.push(`<h${n}>${inline(m[2])}</h${n}>`);continue;}
    m=line.match(/^!\[(.*)\]\((.*)\)$/);
    if(m){
      const absolute=path.resolve(path.dirname(source),m[2]);
      const uri='data:image/png;base64,'+fs.readFileSync(absolute).toString('base64');
      while(i+1<lines.length&&!lines[i+1].trim())i++;
      const caption=lines[i+1]?.trim().startsWith('图'+chapter+'-')?lines[++i].trim():m[1];
      parts.push(`<figure><img src="${uri}"/><figcaption>${inline(caption)}</figcaption></figure>`);continue;
    }
    if(new RegExp('^表'+chapter+'-\\d+：').test(line)) {
      parts.push(`<p class="table-caption">${inline(line)}</p>`);continue;
    }
    if(line.startsWith('|')) {
      const rows=[];do {const r=lines[i].trim();if(!/^\|\s*---/.test(r))rows.push(r.slice(1,-1).split('|').map(s=>s.trim()));i++;}while(i<lines.length&&lines[i].trim().startsWith('|'));i--;
      parts.push('<table><thead><tr>'+rows[0].map(s=>'<th>'+inline(s)+'</th>').join('')+'</tr></thead><tbody>'+rows.slice(1).map(r=>'<tr>'+r.map(s=>'<td>'+inline(s)+'</td>').join('')+'</tr>').join('')+'</tbody></table>');continue;
    }
    if(line.startsWith('- ')) {
      const rows=[];do {rows.push(lines[i].trim().slice(2));i++;}while(i<lines.length&&lines[i].trim().startsWith('- '));i--;
      parts.push('<ul class="references">'+rows.map(s=>'<li>'+inline(s)+'</li>').join('')+'</ul>');continue;
    }
    parts.push('<p'+(line.startsWith('注：')?' class="note"':'')+'>'+inline(line)+'</p>');
  }
  let content=parts.join('\n');
  content=content.replace(/(<p class="table-caption">.*?<\/p>)\s*(<table>.*?<\/table>)\s*(<p class="note">.*?<\/p>)/gs,
    '<div class="table-block">$1$2$3</div>');
  content=content.replace(/(<p><strong>本部分资料与图表设计参考<\/strong><\/p>)([\s\S]*)$/,
    '<aside class="reference-block">$1$2</aside>');
  return content;
}

const style=`
@page{size:A4;margin:20mm 20mm 20mm 20mm;}
body{font-family:"SimSun","Microsoft YaHei",serif;font-size:12pt;line-height:1.5;color:#17242e;margin:0;width:170mm;}
h1{font-size:18pt;margin:0 0 18pt;line-height:1.35;color:#263746;}
h2{font-size:15pt;margin:20pt 0 9pt;line-height:1.3;}
h3{font-size:12.5pt;margin:15pt 0 7pt;line-height:1.3;}
h1,h2,h3{break-after:avoid;font-family:"Microsoft YaHei",sans-serif;}
p{margin:7pt 0;text-align:justify;orphans:3;widows:3;}
.math-block{break-inside:avoid;page-break-inside:avoid;margin:10pt 0;font-size:12pt;padding:3pt 0;}
.math-equation{display:block;width:100%;height:auto;break-inside:avoid;}
mjx-container[display="true"]{margin:.7em 0 !important;}
figure{margin:14pt 0;break-inside:avoid;}
figure img{display:block;width:100%;height:auto;}
figcaption{font-size:10pt;line-height:1.45;margin:6pt 0 0;color:#334650;text-align:justify;}
table{border-collapse:collapse;width:100%;font-size:10.5pt;line-height:1.4;break-inside:avoid;margin:4pt 0 6pt;}
th{border-top:1.3pt solid #263746;border-bottom:.7pt solid #263746;font-weight:600;text-align:left;padding:6pt;}
td{padding:5pt 6pt;vertical-align:top;}
tbody tr:last-child td{border-bottom:1.2pt solid #263746;}
thead{display:table-header-group;}
.table-caption{break-after:avoid;font-size:11pt;text-align:center;font-weight:600;margin:12pt 0 4pt;}
.table-block,.reference-block{break-inside:avoid;}
.note{font-size:10pt;line-height:1.4;margin:5pt 0 10pt;}
.references{font-size:10.5pt;line-height:1.45;padding-left:15pt;}
.references li{margin-bottom:6pt;overflow-wrap:anywhere;}
a{color:inherit;text-decoration:none;}
`;

(async()=>{
  if(!fs.existsSync(mathjax))throw Error('Download pinned MathJax 3.2.2 to '+mathjax+' before rendering.');
  const html=path.join(temporary,stem+'_print.html');
  const title=chapter===4?'第四部分：敏感性与情景分析':'第五部分：模型评价';
  fs.writeFileSync(html,'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>'+title+'</title><style>'+style+'</style></head><body>'+parse(fs.readFileSync(source,'utf8'))+'</body></html>');
  const available=[chromium.executablePath(), 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    'C:/Program Files/Google/Chrome/Application/chrome.exe'].find(p=>fs.existsSync(p));
  if(!available)throw Error('No installed Chromium browser is available for PDF rendering.');
  const browser=await chromium.launch({headless:true,executablePath:available});
  try {
    const page=await browser.newPage({viewport:{width:1000,height:1400}});
    await page.goto(pathToFileURL(html).href,{waitUntil:'load'});
    await page.evaluate(()=>{window.MathJax={tex:{inlineMath:[['\\(','\\)']],displayMath:[['\\[','\\]']],tags:'none'},svg:{fontCache:'local'},startup:{typeset:false}};});
    await page.addScriptTag({path:mathjax});
    await page.evaluate(async()=>{await MathJax.startup.promise;await MathJax.typesetPromise();await document.fonts.ready;});
    await page.emulateMedia({media:'print'});
    // Replace display SVG containers with indivisible vector images. Chromium
    // can fragment MathJax containers across print pages despite break-inside.
    const mathErrors=await page.evaluate(()=>[...document.querySelectorAll('mjx-merror,[data-mml-node="merror"]')].map(n=>n.textContent));
    await page.evaluate(()=>{
      for(const container of document.querySelectorAll('.math-block mjx-container')) {
        const svg=container.querySelector('svg').cloneNode(true);
        const box=container.querySelector('svg').getBoundingClientRect();
        svg.setAttribute('xmlns','http://www.w3.org/2000/svg');
        svg.setAttribute('xmlns:xlink','http://www.w3.org/1999/xlink');
        svg.setAttribute('width',box.width+'px');svg.setAttribute('height',box.height+'px');
        svg.style.fontFamily='SimSun, serif';svg.style.verticalAlign='';
        const img=document.createElement('img');img.className='math-equation';
        img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(new XMLSerializer().serializeToString(svg));
        container.replaceWith(img);
      }
    });
    await page.evaluate(async()=>{await Promise.all([...document.images].map(i=>i.decode()));});
    const audit=await page.evaluate(()=>({
      display_equations:document.querySelectorAll('.math-equation').length,
      figures:document.querySelectorAll('figure').length,tables:document.querySelectorAll('table').length,
      broken_images:[...document.images].filter(i=>!i.complete||!i.naturalWidth).length,
      horizontal_overflow:[...document.querySelectorAll('.math-block,table,figure')].map(n=>({tag:n.tagName,width:n.scrollWidth,available:n.clientWidth})).filter(r=>r.width>r.available+3)
    }));
    audit.math_errors=mathErrors;
    if(audit.math_errors.length||audit.broken_images||audit.horizontal_overflow.length||audit.display_equations!==(chapter===4?3:0)||audit.figures!==(chapter===4?2:0)||audit.tables!==(chapter===4?4:0))throw Error(JSON.stringify(audit));
    await page.pdf({path:output,format:'A4',printBackground:true,preferCSSPageSize:true,displayHeaderFooter:true,
      headerTemplate:'<span></span>',footerTemplate:'<div style="font-family:Arial;font-size:9px;color:#64717b;width:100%;text-align:center;"><span class="pageNumber"></span> / <span class="totalPages"></span></div>'});
    fs.writeFileSync(path.join(root,'output/question4/q'+chapter+'_pdf_render_audit.json'),JSON.stringify({method:'Chromium + MathJax 3.2.2 SVG from synchronized Markdown',latex_compiler_status:'platform_error',...audit},null,2)+'\n');
    console.log(JSON.stringify({pdf:output,...audit}));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
