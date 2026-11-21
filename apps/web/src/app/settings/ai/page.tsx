"use client";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

type Provider = "openai" | "gemini" | "claude";
type Config = {provider:Provider;model:string;endpoint:string;has_key:boolean;active:boolean;status:string;tested_at:string|null;latency_ms:number|null;error_code:string|null};
type Settings = {gateway_mode?:"live"|"mock";active_provider:Provider|null;configs:Config[];endpoints:Record<Provider,string>};
type Feedback = {request_id?:string;http_status?:number;upstream_status?:number|null;upstream_code?:string|null;upstream_request_id?:string|null;network_reason?:string|null;code?:string;reason?:string;impact?:string;solution?:string;message_vi?:string;next_action_vi?:string};
const labels:Record<Provider,string>={openai:"OpenAI",gemini:"Google Gemini",claude:"Anthropic Claude"};
export default function AISettingsPage(){
 const [data,setData]=useState<Settings|null>(null);
 const [provider,setProvider]=useState<Provider>("openai");
 const [model,setModel]=useState("");const [key,setKey]=useState("");
 const [consent,setConsent]=useState(false);const [busy,setBusy]=useState(false);
 const [error,setError]=useState<Feedback|null>(null);const [notice,setNotice]=useState("");
 const generation=useRef(0);
 const load=useCallback((preserveError=false)=>{
  const gen=++generation.current;
  return fetch('/api/v1/settings/ai',{cache:'no-store'}).then(async r=>{
   if(!r.ok)throw Error();return await r.json() as Settings;
  }).then(d=>{if(gen!==generation.current)return;setData(d);const p=d.active_provider||'openai';setProvider(p);setModel(d.configs.find(c=>c.provider===p)?.model||'');}).catch(()=>{if(gen===generation.current&&!preserveError)setError({reason:'Không đọc được cấu hình AI.',solution:'Kiểm tra backend và chạy migration rồi tải lại trang.'});});
 },[]);
 useEffect(()=>{void load();const lifecycle=generation;return()=>{lifecycle.current++;};},[load]);
 const current=data?.configs.find(c=>c.provider===provider);
 const dirty=model!==current?.model||!!key||provider!==data?.active_provider;
 function select(value:Provider){setProvider(value);setModel(data?.configs.find(c=>c.provider===value)?.model||'');setKey('');setConsent(false);setError(null);setNotice('');}
 async function action(kind:'save'|'test'|'remove'){
  if(kind==='remove'&&!window.confirm(`Xóa API key và cấu hình ${labels[provider]}?`))return;
  setBusy(true);setError(null);setNotice('');
  try{
   const url=kind==='test'?'/api/v1/settings/ai/test':kind==='remove'?`/api/v1/settings/ai/${provider}`:'/api/v1/settings/ai';
   const body=kind==='save'?{provider,model,...(key?{api_key:key}:{})}:kind==='test'?{consent}:undefined;
   const r=await fetch(url,{method:kind==='save'?'PUT':kind==='test'?'POST':'DELETE',headers:{'Content-Type':'application/json'},...(body?{body:JSON.stringify(body)}:{})});
   const result=await r.json();if(!r.ok){setError({...result.error,http_status:r.status,request_id:result.error?.request_id||r.headers.get('x-request-id')||undefined,...(!result.error?{reason:'Thao tác chưa hoàn tất.'}:{})});if(kind==='test')await load(true);return;}
   setData(result);setKey('');setNotice(kind==='save'?'Đã lưu cấu hình. Chưa kiểm tra kết nối.':kind==='remove'?'Đã xóa API key và metadata.':'Kết nối thành công bằng request thật tới provider.');
  }catch{setError({reason:'Không kết nối được backend local.',impact:'Chưa xác nhận thao tác thành công.',solution:'Kiểm tra FastAPI rồi thử lại.'});}
  finally{setBusy(false);}
 }
 return <main className="main-container" style={{maxWidth:850}}>
  <Link href="/projects">← Quay lại dự án</Link><h1 style={{marginTop:24}}>Cài đặt AI</h1>
  <p role="status">Gateway: {data?.gateway_mode||"live"}{data?.gateway_mode==="mock"?" — không gửi request thật":""}</p>
  <p className="page-description">Một provider/model dùng chung cho Topic Analyst và SEO Critic. Lưu cấu hình không tự gọi AI.</p>
  {error&&<div role="alert" className="error-panel"><div><strong>{error.code} {error.reason||error.message_vi}</strong>{error.impact&&<p>Ảnh hưởng: {error.impact}</p>}<p>Cách khắc phục: {error.solution||error.next_action_vi}</p>{error.request_id&&<p>Mã yêu cầu: <code>{error.request_id}</code></p>}{error.http_status&&<p>HTTP ứng dụng: {error.http_status}; HTTP provider: {error.upstream_status??"chưa nhận được"}</p>}{error.upstream_code&&<p>Mã lỗi provider: {error.upstream_code}</p>}{error.network_reason&&<p>Lỗi mạng: {error.network_reason}</p>}<button className="button button-secondary" disabled={busy} onClick={()=>void load()}>Tải lại cấu hình</button></div></div>}
  <p role="status" aria-live="polite" className="feedback">{busy?'Đang xử lý…':notice}</p>
  <form className="project-sidebar" onSubmit={e=>{e.preventDefault();void action('save');}}>
   <label htmlFor="provider">Nhà cung cấp</label><select id="provider" value={provider} disabled={busy||!data} onChange={e=>select(e.target.value as Provider)}>{Object.entries(labels).map(([value,label])=><option value={value} key={value}>{label}</option>)}</select>
   <p style={{margin:'12px 0',overflowWrap:'anywhere'}}>Endpoint cố định: <code>{data?.endpoints[provider]||'Đang tải…'}</code></p>
   <label htmlFor="model">Model ID cho Analyst và Critic</label><input id="model" required maxLength={160} pattern="[A-Za-z0-9][A-Za-z0-9._:/\-]*" value={model} onChange={e=>{setModel(e.target.value);setNotice('');}} disabled={busy} autoComplete="off"/>
   <p className="table-description">Nhập đúng Model ID trong tài khoản provider; quyền sử dụng được xác nhận khi Test Connection.</p>
   <label htmlFor="api-key">API key {current?.has_key?'(đã lưu; để trống để giữ key)':''}</label><input id="api-key" type="password" value={key} onChange={e=>setKey(e.target.value)} autoComplete="new-password" maxLength={4096} disabled={busy} />
   <p className="table-description">Key chỉ gửi đến backend local và lưu trong kho credentials của hệ điều hành. Không lưu vào trình duyệt hoặc SQLite.</p>
   <div style={{display:'flex',gap:12,flexWrap:'wrap',margin:'16px 0'}}><button type="submit" className="button button-primary" disabled={busy||!data||!model.trim()||(!key&&!current?.has_key)}>Save Settings</button><button type="button" className="button button-secondary" disabled={busy||!current?.has_key} onClick={()=>void action('remove')}>Remove Key</button></div>
   <label style={{display:'flex',gap:10,alignItems:'center'}}><input type="checkbox" style={{width:20,minHeight:20}} checked={consent} onChange={e=>setConsent(e.target.checked)} disabled={busy}/> Tôi đồng ý gửi lời nhắc kiểm tra ngắn tới provider; có thể phát sinh phí.</label>
   <p className="table-description">Test không gửi taxonomy, keyword, dữ liệu dự án hay file Semrush. Lưu cấu hình trước khi kiểm tra.</p>
   <button type="button" className="button button-primary" disabled={busy||!consent||dirty||!current?.has_key||data?.gateway_mode==="mock"} onClick={()=>void action('test')}>Test Connection</button>
  </form>
  <section className="project-sidebar" style={{marginTop:20}} aria-label="Trạng thái kết nối"><h2>Trạng thái {labels[provider]}</h2><dl><dt>Trạng thái</dt><dd>{current?.status||'AI_NOT_CONFIGURED'}{dirty?' — có thay đổi chưa lưu':''}</dd><dt>Model đã lưu</dt><dd>{current?.model||'Chưa có'}</dd><dt>Kiểm tra lúc</dt><dd>{current?.tested_at?new Date(current.tested_at).toLocaleString('vi-VN'):'Chưa kiểm tra'}</dd><dt>Thời gian phản hồi</dt><dd>{current?.latency_ms!=null?`${current.latency_ms} ms`:'Chưa có'}</dd></dl></section>
 </main>;
}
