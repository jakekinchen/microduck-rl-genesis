"use strict";
const $ = id => document.getElementById(id);
const colors = {a: "#355fca", b: "#a67a0a", target: "#b33e38"};
let snapshot, primary, comparison, currentCase = "", time = 0, playing = false, lastTick = 0, lastDraw = 0, requestVersion = 0;
const svgNS = "http://www.w3.org/2000/svg";
function node(tag, text, cls) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if(cls)n.className=cls;return n; }
function svgNode(tag, attrs={}, text) { const n=document.createElementNS(svgNS,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;return n; }
async function get(url) { const response=await fetch(url);const result=await response.json();if(!response.ok)throw new Error(result.error||`Request failed (${response.status})`);return result; }
function number(n, digits=2) { return Number.isFinite(n) ? n.toFixed(digits) : "—"; }
function list(dl, items) { dl.replaceChildren();for(const [key,value] of items){dl.append(node("dt",key),node("dd",String(value??"—")));} }
function error(message) { $("error").textContent=message;$("error").hidden=!message; }
function points(run) { return run?.trajectories?.[currentCase] || []; }
function duration() { return Math.max(0,...[primary,comparison].flatMap(r=>points(r).map(p=>p.time_s||0))); }
function sample(run) { const rows=points(run);if(!rows.length)return null;return rows.reduce((a,b)=>Math.abs(b.time_s-time)<Math.abs(a.time_s-time)?b:a); }
function chart(id, series, {xLabel="Seconds", yLabel="", height=270, width=520, cursor=true, equal=false}={}) {
  const svg=$(id);svg.replaceChildren();svg.setAttribute("viewBox",`0 0 ${width} ${height}`);
  const valid=series.map(s=>({...s,values:s.values.filter(p=>p.length===2&&p.every(Number.isFinite))}));
  const all=valid.flatMap(s=>s.values);
  if(!all.length){svg.append(svgNode("text",{x:24,y:60},"No recorded data for this view."));return;}
  let xmin=Math.min(0,...all.map(p=>p[0])),xmax=Math.max(.1,...all.map(p=>p[0]));
  let ymin=Math.min(0,...all.map(p=>p[1])),ymax=Math.max(.1,...all.map(p=>p[1]));
  const L=48,R=18,T=17,B=36,pw=width-L-R,ph=height-T-B;
  if(equal){const unit=Math.max((xmax-xmin)/pw,(ymax-ymin)/ph)*1.15;const mx=(xmin+xmax)/2,my=(ymin+ymax)/2;xmin=mx-unit*pw/2;xmax=mx+unit*pw/2;ymin=my-unit*ph/2;ymax=my+unit*ph/2;}
  else {ymax+=(ymax-ymin)*.09;}
  const x=v=>L+(v-xmin)/(xmax-xmin)*pw,y=v=>T+ph-(v-ymin)/(ymax-ymin)*ph;
  for(let i=0;i<=4;i++){
    const xx=xmin+(xmax-xmin)*i/4,yy=ymin+(ymax-ymin)*i/4;
    svg.append(svgNode("line",{x1:L,y1:y(yy),x2:width-R,y2:y(yy),class:"axis"}),svgNode("text",{x:L-7,y:y(yy)+4,"text-anchor":"end"},number(yy,2)),svgNode("text",{x:x(xx),y:height-15,"text-anchor":"middle"},number(xx,1)));
  }
  svg.append(svgNode("text",{x:width-R,y:height-1,"text-anchor":"end"},xLabel),svgNode("text",{x:L,y:11},yLabel));
  for(const s of valid){if(!s.values.length)continue;
    const path=s.values.map((p,i)=>`${i?"L":"M"}${x(p[0]).toFixed(2)},${y(p[1]).toFixed(2)}`).join(" ");
    svg.append(svgNode("path",{d:path,fill:"none",stroke:s.color,"stroke-width":2,"stroke-dasharray":s.dashed?"5 4":"none"}));
    const point=s.current;
    if(point?.every(Number.isFinite))svg.append(svgNode("circle",{cx:x(point[0]),cy:y(point[1]),r:5,fill:s.color,stroke:"white","stroke-width":2}));
  }
  if(cursor && time<=xmax)svg.append(svgNode("line",{x1:x(time),y1:T,x2:x(time),y2:height-B,class:"cursor"}));
}
function draw() {
  const a=points(primary),b=points(comparison),sa=sample(primary),sb=sample(comparison);
  chart("path-plot",[
    {values:a.map(p=>p.robot_xyz_m?.slice(0,2)||[]),color:colors.a,current:sa?.robot_xyz_m?.slice(0,2)},
    {values:b.map(p=>p.robot_xyz_m?.slice(0,2)||[]),color:colors.b,current:sb?.robot_xyz_m?.slice(0,2)},
    {values:a.filter(p=>p.visible).map(p=>p.target_xy_m||[]),color:colors.target,dashed:true,current:sa?.visible?sa?.target_xy_m:null}
  ],{xLabel:"World X (m)",yLabel:"World Y (m)",equal:true,cursor:false});
  chart("distance-plot",[{values:a.map(p=>[p.time_s,p.distance_m]),color:colors.a},{values:b.map(p=>[p.time_s,p.distance_m]),color:colors.b}],{yLabel:"Metres"});
  chart("speed-plot",[{values:a.map(p=>[p.time_s,p.speed_m_s]),color:colors.a},{values:b.map(p=>[p.time_s,p.speed_m_s]),color:colors.b},{values:a.map(p=>[p.time_s,p.command?.[0]]),color:colors.a,dashed:true}],{height:240,yLabel:"m/s (dashed: requested forward speed)"});
  list($("moment"),[["Snapshot time",`${number(sa?.time_s)} s`],["Gap to target",`${number(sa?.distance_m)} m`],["Speed",`${number(sa?.speed_m_s,3)} m/s`],["Target available",sa?(sa.visible?"Yes":"No"):"—"],["Target",sa?.target_label||"Recorded target"],["Command vx, vy, yaw",sa?.command?.map(v=>number(v)).join(", ")||"—"],["Tilt",`${number(sa?.tilt_deg)}°`],["Policy inference",`${number(sa?.latency_ms,3)} ms`],["Fall",sa?(sa.fell?"Yes":"No"):"—"]]);
  $("timeline").value=time;$("time").textContent=`${number(time)} s`;
}
function syncVideos(force=false){for(const [id,run] of [["video-a",primary],["video-b",comparison]]){const v=$(id);if(!v.getAttribute("src"))continue;const mediaTime=Math.max(0,time-(run?.video_time_origins_s?.[currentCase]||0));const target=Math.min(mediaTime,Number.isFinite(v.duration)?Math.max(0,v.duration-.01):mediaTime);if(force||Math.abs(v.currentTime-target)>.10)v.currentTime=target;v.playbackRate=Number($("speed").value);}}
function pause(){playing=false;$("play").textContent="Play";$("video-a").pause();$("video-b").pause();}
function tick(stamp){if(!playing)return;time=Math.min(duration(),time+(stamp-lastTick)/1000*Number($("speed").value));lastTick=stamp;syncVideos();if(stamp-lastDraw>=100||time>=duration()){draw();lastDraw=stamp;}if(time>=duration())pause();else requestAnimationFrame(tick);}
function setVideo(id,missing,run){const video=$(id),url=run?.artifacts?.[`${currentCase}.mp4`];video.pause();if(url){video.src=url;video.hidden=false;$(missing).hidden=true;}else{video.removeAttribute("src");video.load();video.hidden=true;$(missing).hidden=false;}}
function setCase(value){pause();currentCase=value;$("case").value=value;time=0;$("timeline").max=duration();setVideo("video-a","missing-a",primary);setVideo("video-b","missing-b",comparison);const fall=points(primary).find(p=>p.fell===true);$("first-fall").hidden=!fall;$("first-fall").textContent=fall?`First fall · ${number(fall.time_s)} s`:"First fall";const c=primary?.cases.find(c=>c.case_id===value);$("case-details-label").textContent=c?.gait?"Gait rejection details":"Recorded domain for this case";$("case-domain").textContent=c?.gait?JSON.stringify({target_passed:c.target?.passed,composite_passed:c.passed,failures:c.failures,gait:c.gait},null,2):c?.domain?JSON.stringify(c.domain,null,2):"No randomized domain parameters were recorded for this case.";draw();}
function renderDetail(){
  const cases=primary?.cases||[];$("case").replaceChildren(...cases.map(c=>{const o=node("option",c.case_id);o.value=c.case_id;return o;}));
  $("inspection").hidden=!cases.length;$("empty").hidden=!!cases.length;
  if(!cases.length){$("empty").textContent="No supported behavior recordings yet. New development receipts appear after refresh.";return;}
  $("comparison-figure").hidden=!comparison;$("videos").classList.toggle("comparing",!!comparison);
  $("primary-caption").textContent=primary.name;$("comparison-caption").textContent=comparison?.name||"";
  $("evidence-label").textContent=`${primary.passed}/${primary.total} ${primary.schema==="microduck.laser-gait-evaluation/v3"?"composite":"visible"} development cases · ${primary.engine}`;
  const integrity=primary.integrity.status;$("integrity").textContent=integrity==="manifest_verified"?`${primary.integrity.files} manifest entries verified`:integrity;
  $("integrity").parentElement.classList.toggle("invalid",integrity!=="manifest_verified");
  $("boundary").textContent=typeof primary.boundary==="string"?primary.boundary:JSON.stringify(primary.boundary);
  if(comparison && comparison.integrity.status!=="manifest_verified")$("boundary").append(` Comparison integrity: ${comparison.integrity.status}.`);
  if(comparison && primary.suite_sha256!==comparison.suite_sha256)$("boundary").append(" These runs use different suites; case scores are not a controlled comparison.");
  $("case-results").replaceChildren();
  $("gap-heading").textContent=primary.schema!=="microduck.laser-evaluation/v1"?"Mean visible gap":"Final gap";
  for(const c of cases){const other=comparison?.cases.find(x=>x.case_id===c.case_id);const row=node("tr");const name=node("td"),button=node("button",c.case_id);button.onclick=()=>setCase(c.case_id);name.append(button);row.append(name,node("td",c.passed?"Pass":"Fail",c.passed?"pass":"fail"),node("td",other?(other.passed?"Pass":"Fail"):"—",other?(other.passed?"pass":"fail"):""),node("td",`${number(c.final_distance_m??c.mean_visible_distance_m,3)} m`),node("td",c.fell?"Yes":"No"),node("td",String(c.inference_deadline_misses??c.deadline_misses??"—")));$("case-results").append(row);}
  list($("provenance"),[["Policy SHA-256",primary.policy_sha256],["Suite SHA-256",primary.suite_sha256],["Steering adapter",primary.steering?.id||"See evaluation.json"],["Target input",primary.target_source],["Evidence",primary.proof_class],["Held-out", "No"],["Receipt",primary.id]]);
  $("artifact-links").replaceChildren();for(const [name,url] of Object.entries(primary.artifacts)){const link=node("a",name);link.href=url;link.target="_blank";link.rel="noopener";$("artifact-links").append(link);}
  chart("learning-plot",[{values:(primary.learning_curve||[]).map(p=>[p.iteration,p.mean_reward]),color:colors.a}],{width:1000,height:230,xLabel:"PPO iteration",yLabel:"Mean reward",cursor:false});
  const active=snapshot.active_focus;const focused=active?.status==="verified"&&active.primary===primary.id?active.case_id:null;
  setCase(cases.some(c=>c.case_id===currentCase)?currentCase:cases.find(c=>c.case_id===focused)?.case_id||cases.find(c=>c.case_id==="moving")?.case_id||cases[0].case_id);
}
async function selectRuns(){const version=++requestVersion;pause();$("inspection").hidden=true;$("empty").hidden=false;$("empty").textContent="Reading selected development evidence…";try{const [a,b]=await Promise.all([$("primary").value?get(`/api/run?id=${encodeURIComponent($("primary").value)}`):null,$("comparison").value?get(`/api/run?id=${encodeURIComponent($("comparison").value)}`):null]);if(version!==requestVersion)return;primary=a;comparison=b;renderDetail();error("");}catch(e){if(version===requestVersion)error(e.message);}}
function renderWorkspace(){
  $("mission").textContent=snapshot.goal["Current Milestone"]||"Read GOAL.md";$("current-status").textContent=snapshot.goal["Current Status"]||"No current status section.";
  $("queue-list").replaceChildren(...snapshot.queue.map(q=>{const row=node("div");row.append(node("strong",q.title),node("span",`${q.checked}/${q.total} implementation checkboxes. ${q.next?`Next: ${q.next}`:"Read exit gate in the task list."}`));return row;}));
  $("training-list").replaceChildren(...snapshot.training.map(r=>{const row=node("div");const telemetry=r.telemetry?.status==="recorded"?` Last logged iteration: ${r.telemetry.last_iteration}; reward ${number(r.telemetry.latest_reward)}; ${new Date(r.telemetry.last_wall_time*1000).toLocaleString()}.`:"";row.append(node("strong",r.id),node("span",`${r.recorded_status}; ${r.transitions?.toLocaleString()||"unknown"} planned transitions${r.elapsed_s?`; ${(r.elapsed_s/60).toFixed(1)} min recorded`:""}. ${r.checkpoint?`Checkpoint: ${r.checkpoint}`:"No completed checkpoint recorded."}${telemetry}`));return row;}));
  $("inspection-errors").replaceChildren(...snapshot.errors.map(e=>node("p",`${e.path}: ${e.error}`)));
  const focus=snapshot.active_focus;$("active-question").textContent=focus?.status==="verified"?focus.question:focus?.error||"No source-checked active experiment is configured.";
}
async function refresh(){try{const prior=$("primary").value,priorCompare=$("comparison").value;snapshot=await get("/api/snapshot");$("checkout").textContent=`${snapshot.root}\n${snapshot.branch} @ ${snapshot.head.slice(0,12)}${snapshot.dirty?" (working changes)":""}`;$("freshness").textContent=`Snapshot ${new Date(snapshot.generated_at).toLocaleTimeString()} · ${snapshot.evaluations.length} development reports`;
  const runs=snapshot.evaluations.filter(r=>r.cases.length);const option=r=>{const o=node("option",r.name);o.value=r.id;return o;};$("primary").replaceChildren(...runs.map(option));$("comparison").replaceChildren(node("option","No comparison"),...runs.map(option));$("comparison").firstChild.value="";
  const focus=snapshot.active_focus?.status==="verified"?snapshot.active_focus:null;
  $("primary").value=runs.some(r=>r.id===prior)?prior:focus?.primary||runs.find(r=>r.name==="20260904-v2-steering")?.id||runs.at(-1)?.id||"";
  $("comparison").value=runs.some(r=>r.id===priorCompare)?priorCompare:(!prior?focus?.comparison||runs.find(r=>r.name==="20260904-v1-baseline")?.id||"":"");
  renderWorkspace();await selectRuns();
}catch(e){error(`Cannot read workspace: ${e.message}. Check that ./scripts/duck studio is running.`);}}
$("primary").onchange=selectRuns;$("comparison").onchange=selectRuns;$("case").onchange=()=>setCase($("case").value);$("refresh").onclick=refresh;
$("timeline").oninput=()=>{pause();time=Number($("timeline").value);syncVideos(true);draw();};
$("first-fall").onclick=()=>{const fall=points(primary).find(p=>p.fell===true);if(!fall)return;pause();time=fall.time_s;syncVideos(true);draw();};
$("speed").onchange=()=>syncVideos();
$("play").onclick=()=>{if(playing){pause();return;}if(time>=duration())time=0;playing=true;lastTick=performance.now();$("play").textContent="Pause";syncVideos(true);for(const v of [$("video-a"),$("video-b")])if(v.getAttribute("src"))v.play().catch(()=>{});requestAnimationFrame(tick);};
for(const button of document.querySelectorAll("[data-view]"))button.onclick=()=>{pause();for(const section of document.querySelectorAll(".view"))section.hidden=section.id!==button.dataset.view;for(const b of document.querySelectorAll("[data-view]"))b.classList.toggle("selected",b===button);$("page-title").textContent=button.textContent;};
refresh();
setInterval(async()=>{if(document.hidden||$("workspace").hidden)return;try{snapshot=await get("/api/snapshot");renderWorkspace();$("freshness").textContent=`Snapshot ${new Date(snapshot.generated_at).toLocaleTimeString()} · ${snapshot.evaluations.length} development reports`;}catch(e){error(e.message);}},15000);
