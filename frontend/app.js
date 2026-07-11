const state = { role: null, page: 'home', overview: null, detections: [], alerts: [], chat: [] };
const api = async (path, options = {}) => {
  const response = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
  return response.json();
};
const userNav = [['home','个性化首页'],['monitor','实时监测'],['alerts','我的预警'],['history','历史与统计'],['agent','AI 助手']];
const adminNav = [['home','全局仪表盘'],['users','用户管理'],['devices','设备管理'],['alerts','预警中心'],['history','全局统计'],['agent','管理员助手']];
const titleMap = {home:'个性化首页',monitor:'实时监测',alerts:'预警中心',history:'历史与统计',agent:'AI 助手',users:'用户管理',devices:'设备管理'};
const byId = (id) => document.getElementById(id);
const fmt = (value) => new Date(value).toLocaleString('zh-CN', {month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
const badge = (status) => `<span class="badge ${status === 'safe' ? 'safe' : status === 'high' ? 'high' : 'warning'}">${status === 'safe' ? '安全' : status === 'high' ? '高风险' : status === 'acknowledged' ? '已确认' : '待确认'}</span>`;

function toast(text) { const el = byId('toast'); el.textContent = text; el.classList.remove('hidden'); setTimeout(() => el.classList.add('hidden'), 2600); }
function navigation() {
  const items = state.role === 'admin' ? adminNav : userNav;
  byId('nav').innerHTML = items.map(([page,label]) => `<button class="nav-item ${state.page === page ? 'active' : ''}" data-page="${page}">${label}</button>`).join('');
  document.querySelectorAll('.nav-item').forEach(el => el.onclick = () => { state.page = el.dataset.page; render(); });
}
async function loadData() {
  const role = state.role;
  const [overview, detections, alerts] = await Promise.all([api(`/api/overview?role=${role}`), api(`/api/detections?role=${role}`), api(`/api/alerts?role=${role}`)]);
  state.overview = overview.data; state.detections = detections.data; state.alerts = alerts.data;
}
function metric(label, value, note) { return `<article class="card"><div class="metric-label">${label}</div><div class="metric-value">${value}</div><div class="metric-note">${note}</div></article>`; }
function bars(values) { const max = Math.max(...values); return `<div class="chart">${values.map(v => `<div class="bar" style="height:${Math.max(16, v/max*100)}%"></div>`).join('')}</div>`; }
function detectionRows(records) { return records.map(r => `<tr><td>${fmt(r.created_at)}</td><td><b>${r.gas_type}</b><br><small>${r.device_id}</small></td><td>${r.concentration_ppm} ppm</td><td>${Math.round(r.confidence*100)}%</td><td>${badge(r.status)}</td></tr>`).join(''); }

async function home() {
  const o = state.overview; const recs = (await api('/api/recommendations')).data;
  const intro = state.role === 'admin' ? '管理员工作台' : '根据你的关注气体与最近行为生成';
  return `<div class="page-top"><div><p class="metric-label">${intro}</p></div>${state.role === 'user' ? '<button class="primary" data-go="monitor">开始一次模拟检测</button>' : ''}</div>
  <div class="metric-grid">${metric('检测记录',o.total_detections,'当前可见范围')}${metric('触发预警',o.warning_count,'由后端统一判定')}${metric('待确认预警',o.open_alert_count,'需要优先处理')}${metric('在线设备',o.online_devices,'设备状态模拟')}</div>
  <div class="grid-two"><article class="card"><h3>浓度趋势 · 最近 7 个时段</h3>${bars(o.trend)}<div class="metric-note">第 6 个时段出现峰值，建议持续观察</div></article>
  <article class="card"><h3>${state.role === 'admin' ? '全局气体分布' : '为你推荐'}</h3>${state.role === 'admin' ? `<div class="list"><div class="list-row"><span>NH3 识别次数</span><b>${o.gas_counts.NH3}</b></div><div class="list-row"><span>甲苯识别次数</span><b>${o.gas_counts.Toluene}</b></div><div class="list-row"><span>低置信度样本</span><b>1</b></div></div>` : recs.map(r => `<div class="recommend"><b>${r.title}</b><span>${r.reason}</span></div>`).join('')}</article></div>`;
}
function monitor() {
  return `<div class="grid-two"><article class="card"><h3>模拟实时检测</h3><p class="metric-label">Demo 使用固定演示曲线。后续由算法组替换为真实推理接口。</p><div class="form-grid"><div class="field"><label>设备</label><select id="detect-device"><option value="dev-01">ZnO-200-A</option><option value="dev-02">ZnO-200-B</option></select></div><div class="field"><label>模拟气体</label><select id="detect-gas"><option>NH3</option><option>Toluene</option></select></div></div><div class="button-row" style="margin-top:18px"><button class="primary" id="simulate">开始模拟检测</button></div><div id="detect-result" style="margin-top:18px"></div></article><article class="card"><h3>算法链路（当前基线）</h3><div class="list"><div class="list-row"><span>输入</span><b>时间序列电信号</b></div><div class="list-row"><span>处理</span><b>滤波 · 基线 · 特征</b></div><div class="list-row"><span>输出</span><b>类别 · 浓度 · 置信度</b></div><div class="list-row"><span>版本</span><b>baseline-v0</b></div></div></article></div>`;
}
function alerts() {
  return `<article class="card"><div class="page-top"><h3>${state.role === 'admin' ? '全局预警事件' : '我的预警'}</h3>${state.role === 'admin' ? '<button class="primary" id="edit-rules">编辑阈值</button>' : ''}</div><table class="table"><thead><tr><th>发生时间</th><th>气体 / 设备</th><th>浓度</th><th>等级</th><th>状态</th><th></th></tr></thead><tbody>${state.alerts.map(a => `<tr><td>${fmt(a.created_at)}</td><td><b>${a.gas_type}</b><br><small>${a.device_id}</small></td><td>${a.concentration_ppm} ppm</td><td>${badge(a.severity)}</td><td>${badge(a.status)}</td><td>${a.status === 'open' ? `<button class="ghost ack" data-id="${a.id}">确认</button>` : ''}</td></tr>`).join('')}</tbody></table></article>`;
}
function history() {
  return `<div class="grid-two"><article class="card"><h3>检测记录</h3><table class="table"><thead><tr><th>时间</th><th>气体 / 设备</th><th>浓度</th><th>置信度</th><th>状态</th></tr></thead><tbody>${detectionRows(state.detections)}</tbody></table></article><article class="card"><h3>模型质量（Demo）</h3><div class="list"><div class="list-row"><span>分类 F1</span><b>待训练</b></div><div class="list-row"><span>浓度 MAE</span><b>待训练</b></div><div class="list-row"><span>数据集</span><b>NH3 / 甲苯梯度实验</b></div><div class="list-row"><span>划分策略</span><b>按实验批次</b></div></div></article></div>`;
}
async function users() { const data = (await api('/api/admin/users')).data; return `<article class="card"><h3>用户与设备授权</h3><table class="table"><thead><tr><th>姓名</th><th>角色</th><th>可访问设备</th><th>状态</th></tr></thead><tbody>${data.map(u=>`<tr><td><b>${u.name}</b><br><small>${u.id}</small></td><td>${u.role === 'admin'?'管理员':'普通用户'}</td><td>${u.devices.join(', ')}</td><td>${badge('safe')}</td></tr>`).join('')}</tbody></table></article>`; }
async function devices() { const data = (await api('/api/admin/devices')).data; return `<article class="card"><h3>设备状态</h3><table class="table"><thead><tr><th>设备</th><th>材料</th><th>地点</th><th>状态</th></tr></thead><tbody>${data.map(d=>`<tr><td><b>${d.name}</b><br><small>${d.id}</small></td><td>${d.material}</td><td>${d.location}</td><td>${badge(d.status === 'online'?'safe':'warning')}</td></tr>`).join('')}</tbody></table></article>`; }
function agent() { const bubbles = state.chat.length ? state.chat.map(m=>`<div class="bubble ${m.type}">${m.text}${m.tools?`<br><small>调用工具：${m.tools.join(', ')} · ${m.range}</small>`:''}</div>`).join('') : '<div class="bubble bot">你好，我是气体监测助手。你可以问“当前有几条预警？”、“浓度趋势如何？”或“设备状态怎么样？”。</div>'; return `<article class="card"><h3>${state.role === 'admin'?'管理员':'用户'} AI 助手</h3><div class="chat" id="chat">${bubbles}</div><form class="chat-form" id="chat-form"><input id="chat-input" placeholder="输入问题，例如：当前有哪些待确认预警？"/><button class="primary">发送</button></form></article>`; }

async function render() {
  navigation(); byId('page-title').textContent = titleMap[state.page] || '工作台'; byId('page-kicker').textContent = state.role === 'admin' ? 'ADMIN CONSOLE' : 'USER CONSOLE';
  const pages = {home,monitor,alerts,history,agent,users,devices};
  byId('content').innerHTML = await pages[state.page](); bindPage();
}
function bindPage() {
  document.querySelectorAll('[data-go]').forEach(el=>el.onclick=()=>{state.page=el.dataset.go;render();});
  const sim = byId('simulate'); if(sim) sim.onclick = async()=>{ sim.disabled=true; sim.textContent='处理中…'; const result=await api('/api/detections/simulate',{method:'POST',body:JSON.stringify({gas_type:byId('detect-gas').value,device_id:byId('detect-device').value})}); await loadData(); const d=result.data; byId('detect-result').innerHTML=`<div class="recommend"><b>${d.gas_type} · ${d.concentration_ppm} ppm · ${Math.round(d.confidence*100)}% 置信度</b><span>算法 ${d.algorithm_version}；${d.status==='warning'?'已由后端创建预警':'未触发预警'}</span></div>`; toast('模拟检测完成，历史记录已更新'); };
  document.querySelectorAll('.ack').forEach(el=>el.onclick=async()=>{await api(`/api/alerts/${el.dataset.id}/acknowledge`,{method:'POST'});await loadData();render();toast('预警已确认');});
  const rules = byId('edit-rules'); if(rules) rules.onclick=()=>toast('Demo 中阈值编辑接口已预留：PUT /api/admin/alert-rules');
  const form=byId('chat-form'); if(form) form.onsubmit=async(e)=>{e.preventDefault();const input=byId('chat-input');if(!input.value.trim())return;const message=input.value.trim();state.chat.push({type:'user',text:message});input.value='';render();const r=await api('/api/agent/chat',{method:'POST',body:JSON.stringify({role:state.role,message})});state.chat.push({type:'bot',text:r.data.answer,tools:r.data.tools,range:r.data.data_range});render();};
}
async function enter(role) { state.role=role; state.page='home'; const r=await api('/api/demo/login',{method:'POST',body:JSON.stringify({role})});byId('identity').innerHTML=`<b>${r.user.name}</b><small>${role==='admin'?'管理员 · 全局权限':'普通用户 · 授权设备'}</small>`;byId('login-screen').classList.add('hidden');byId('app').classList.remove('hidden');await loadData();render(); }
document.querySelectorAll('.role-card').forEach(el=>el.onclick=()=>enter(el.dataset.role));
byId('switch-role').onclick=()=>{byId('app').classList.add('hidden');byId('login-screen').classList.remove('hidden');state.chat=[];};
