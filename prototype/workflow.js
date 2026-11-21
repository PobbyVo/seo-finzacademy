'use strict';
// Presentation only: completion requires an acknowledged SQLite save, never inferred SEO approval.
let runningStep=null;
let projectEpoch=0, validationIssues=[], completionTimer=null, completionDialog=null;
const FEEDBACK={
 PROJECT_MISSING:['Chưa lưu dự án','Chưa có nguồn dự án trong SQLite.','Không có taxonomy để đối chiếu.','Nhập và lưu thông tin dự án.','setup'],
 TOPIC_SCOPE_INVALID:['Phạm vi cần xem xét','Có ứng viên giao thoa hoặc chưa xác minh mã nguồn.','Không thể chốt mapping cho nhánh này.','Đối chiếu taxonomy và quyết định chuyển nhóm.','topic'],
 AI_NOT_CONFIGURED:['Chưa cấu hình AI','Chưa có model và endpoint hợp lệ.','Không thể chạy Analyst/Critic thật.','Xem hướng dẫn AI_PROVIDER, AI_BASE_URL, AI_MODEL; khởi động lại server.','topic'],
 FILE_NOT_SELECTED:['Chưa chọn file','Chưa có file preview cho yêu cầu.','Không thể xác nhận import.','Chọn CSV/XLSX đã xuất từ Semrush.','upload'],
 UNSUPPORTED_FILE:['Định dạng chưa hỗ trợ','File không phải CSV hoặc XLSX.','Không đọc được bảng dữ liệu.','Chọn lại file CSV/XLSX.','upload'],
 COLUMN_MAPPING_INVALID:['Ghép cột chưa hợp lệ','Cột Keyword thiếu hoặc không tồn tại.','Không thể gắn các dòng với keyword nguồn.','Chọn đúng cột Keyword trong bảng ánh xạ.','upload'],
 VOLUME_MISSING:['Thiếu Volume','Một số keyword thiếu hoặc sai định dạng Volume.','Không thể dùng Volume để đánh giá nhu cầu.','Xuất báo cáo bổ sung có Volume; null không phải 0.','requests'],
 KD_MISSING:['Thiếu Keyword Difficulty','Một số keyword chưa có KD hợp lệ.','Chưa thể đánh giá cạnh tranh theo KD.','Xuất Keyword Overview có KD rồi tải file bổ sung.','requests'],
 INTENT_MISSING:['Thiếu nhãn Intent','Báo cáo chưa có nhãn Intent cho một số keyword.','Không có nhãn tham khảo từ Semrush; funnel không thay thế Intent.','Xuất báo cáo bổ sung có Intent.','requests'],
 LOCALE_AMBIGUOUS:['Định dạng số mơ hồ','Dấu chấm/phẩy không phù hợp locale được chọn.','Không thể dùng số này làm căn cứ.','Kiểm tra locale vi-VN/en-US ở bảng ánh xạ rồi nhập lại.','upload'],
 DUPLICATE_KEYWORD:['Keyword trùng lặp','Có nhiều dòng cùng keyword trong file.','Không được cộng Volume giữa các dòng trùng.','Xem nguồn và giữ các quan sát riêng khi đối chiếu.','analysis'],
 SERP_NOT_VERIFIED:['SERP chưa được xác minh','Chưa có parser và quality gate xác minh SERP.','Chưa kết luận intent, dạng trang hoặc gộp/tách bài; chưa đủ điều kiện brief.','Tiếp tục xem kế hoạch dự thảo với giới hạn bằng chứng.','plan'],
 APPROVAL_REQUIRED:['Cần phê duyệt','Có quyết định quan trọng đang chờ người dùng.','Không được thay keyword nguồn hoặc chốt kế hoạch.','Xem và quyết định từng đề xuất.','approvals'],
 DB_SAVE_FAILED:['Chưa lưu được SQLite','Server chưa xác nhận giao dịch lưu thành công.','Dữ liệu hiện tại chỉ là bản nháp; không tự chuyển bước.','Kiểm tra server và thử lưu lại.','setup'],
 LLM_REQUEST_FAILED:['Tác vụ AI chưa hoàn tất','Model không trả kết quả hợp lệ hoặc kết nối thất bại.','Không có kết quả AI mới được xác nhận.','Kiểm tra cấu hình AI và thử lại tác vụ.','topic']
};
function normalizeRoute(id){return id==='serp'?(state.analysis?'plan':'analysis'):id;}
function makeFeedback(code,detail,decision='view'){
 const [title,reason,impact,solution,target]=FEEDBACK[code]||FEEDBACK.DB_SAVE_FAILED;
 return {code,severity:['SERP_NOT_VERIFIED','DUPLICATE_KEYWORD','VOLUME_MISSING','KD_MISSING','INTENT_MISSING','LOCALE_AMBIGUOUS','TOPIC_SCOPE_INVALID','APPROVAL_REQUIRED'].includes(code)?'WARNING':'ERROR',title,reason:detail||reason,impact,solution,next_action:{label:code==='DB_SAVE_FAILED'?'Thử lưu lại':`Mở ${target}`,target},blocking:decision==='brief'||['PROJECT_MISSING','COLUMN_MAPPING_INVALID','DB_SAVE_FAILED','LLM_REQUEST_FAILED'].includes(code),source_ref:null};
}
function currentFeedback(){
 const out=[];if(!state.project)out.push(makeFeedback('PROJECT_MISSING'));
 if(state.active==='topic'&&!aiStatus.configured)out.push(makeFeedback('AI_NOT_CONFIGURED'));
 if(['overview','analysis','plan','brief'].includes(state.active)){
  out.push(makeFeedback('SERP_NOT_VERIFIED',null,state.active==='brief'?'brief':'view'));
  if(state.approvals.some(a=>a.status==='PENDING'))out.push(makeFeedback('APPROVAL_REQUIRED',null,'brief'));
  if(state.groups.some(g=>g.kind==='BOUNDARY'||g.review_status==='UNCERTAIN'))out.push(makeFeedback('TOPIC_SCOPE_INVALID',null,'brief'));
  const flags={};for(const batch of state.imports){for(const [key,value]of Object.entries(batch.backendStats||{})){if(typeof value==='number')flags[key]=(flags[key]||0)+value;}}
  const count=countColumns();
  for(const [code,keys,fallback]of [['KD_MISSING',['MISSING_KD','MISSING_KD_COLUMN','INVALID_KD','KD_OUT_OF_RANGE'],count.missingKd],['VOLUME_MISSING',['MISSING_VOLUME','MISSING_VOLUME_COLUMN','INVALID_VOLUME'],count.missingVolume],['INTENT_MISSING',['MISSING_INTENT'],count.missingIntent],['LOCALE_AMBIGUOUS',['AMBIGUOUS_VOLUME_LOCALE'],count.invalidVolume],['DUPLICATE_KEYWORD',['DUPLICATE_KEYWORD_IN_FILE'],0]]){
   const n=keys.reduce((a,k)=>a+(flags[k]||0),0)||fallback;
   if(n)out.push(makeFeedback(code,`${n} dòng ${Object.keys(flags).length?'trong toàn bộ file':'trong mẫu dữ liệu'}: ${FEEDBACK[code][1]}`));
  }
 }
 return [...validationIssues,...out].filter((x,i,a)=>a.findIndex(y=>y.code===x.code)===i);
}
function ValidationFeedback(issue){return `<section class="validation-card" data-code="${e(issue.code)}" role="status"><strong>${e(issue.title)}</strong> ${chip(issue.code,'review')}<p><b>Nguyên nhân:</b> ${e(issue.reason)}</p><p><b>Ảnh hưởng:</b> ${e(issue.impact)}</p><p><b>Giải pháp:</b> ${e(issue.solution)}</p><small>${issue.blocking?'HOLD — chặn quyết định liên quan':'Cảnh báo — vẫn xem được dữ liệu và dự thảo'}</small><br><button type="button" class="button outline small" data-feedback="${e(issue.code)}">${e(issue.next_action.label)}</button></section>`;}
function renderValidation(){let root=document.getElementById('validationSummary');if(!root){root=document.createElement('div');root.id='validationSummary';document.getElementById('pageBody').prepend(root);}root.innerHTML=currentFeedback().map(ValidationFeedback).join('');}
function showValidation(code,detail){validationIssues=[makeFeedback(code,detail)];renderValidation();const target=code==='COLUMN_MAPPING_INVALID'?document.getElementById('map-keyword'):null;if(target){target.setAttribute('aria-invalid','true');target.setAttribute('aria-describedby','mappingError');let msg=document.getElementById('mappingError');if(!msg){msg=document.createElement('p');msg.id='mappingError';msg.className='inline-error';target.after(msg);}msg.textContent=FEEDBACK.COLUMN_MAPPING_INVALID[1];target.focus();}document.getElementById('validationSummary')?.scrollIntoView({block:'start'});}
function navigationEligible(target){if(!target||!state.project||state.preview)return false;if(state.approvals.some(x=>x.status==='PENDING'))return false;if(state.aiCritique&&state.aiCritique.verdict!=='READY_FOR_SERP')return false;const needed={topic:'setup',analysis:'upload',plan:'analysis'}[target];return !!needed&&state.workflow?.[needed]?.status==='PROCESS_COMPLETED';}
function closeCompletion(){clearTimeout(completionTimer);completionTimer=null;if(completionDialog){completionDialog.close();completionDialog.remove();completionDialog=null;}}
function handleStepCompletion(title,target,epoch){
 closeCompletion();if(epoch!==projectEpoch)return;
 const eligible=navigationEligible(target);const origin=state.active;const projectId=state.project.id;
 const dialog=document.createElement('dialog');completionDialog=dialog;dialog.className='completion-modal';dialog.setAttribute('role','dialog');dialog.setAttribute('aria-labelledby','completionTitle');
 dialog.innerHTML=`<div class="completion-check" aria-hidden="true">✓</div><h2 id="completionTitle">${e(title)}</h2><p>PROCESS_COMPLETED — thao tác đã lưu SQLite. Không đồng nghĩa QUALITY_APPROVED.</p><p>${eligible?`Bước tiếp theo: ${e(NAV.find(n=>n.id===target)?.label)}. Tự chuyển sau 2 giây.`:'Chưa đủ điều kiện tự chuyển. Hãy xem cảnh báo trên màn hình.'}</p>${eligible?'<div class="completion-countdown" aria-hidden="true"></div><button class="button primary" id="completionNext">Đi tiếp ngay</button>':''}<button class="button outline" id="completionStay" autofocus>Ở lại bước này</button>`;
 document.body.append(dialog);dialog.addEventListener('cancel',()=>closeCompletion());dialog.addEventListener('close',()=>{clearTimeout(completionTimer);});dialog.querySelector('#completionStay').onclick=closeCompletion;
 const advance=()=>{if(epoch===projectEpoch&&state.project?.id===projectId&&state.active===origin&&navigationEligible(target)){closeCompletion();go(target);}else closeCompletion();};
 if(eligible){dialog.querySelector('#completionNext').onclick=advance;completionTimer=setTimeout(advance,2000);}dialog.showModal();
}
async function commitStep(step,title,target){
 const epoch=projectEpoch;const previous=state.workflow?.[step];state.workflow={...state.workflow,[step]:{status:'PROCESS_COMPLETED',at:new Date().toISOString()}};
 setBusy('Đang lưu kết quả vào SQLite…','Chỉ thông báo thành công sau khi server xác nhận',step);
 try{await persistServerState();if(epoch!==projectEpoch)return;saveLocalSnapshot();validationIssues=[];render();handleStepCompletion(title,target,epoch);}
 catch(err){if(epoch!==projectEpoch)return;state.workflow={...state.workflow,[step]:previous||{status:'ERROR'}};saveLocalSnapshot();render();showValidation(err.code||'DB_SAVE_FAILED',err.message);}
 finally{if(epoch===projectEpoch)setBusy(null);}
}
function saveLocalSnapshot(){try{localStorage.setItem(STORAGE_KEY,JSON.stringify({...state,preview:null}));}catch{}}
document.addEventListener('click',event=>{const button=event.target.closest('[data-feedback]');if(!button)return;const code=button.dataset.feedback;if(code==='DB_SAVE_FAILED'){commitStep(state.active==='setup'?'setup':state.active,'Đã lưu lại dữ liệu',null);return;}if(code==='COLUMN_MAPPING_INVALID'&&document.getElementById('map-keyword')){document.getElementById('map-keyword').focus();return;}if(code==='FILE_NOT_SELECTED'||code==='UNSUPPORTED_FILE'){handleAction('choose-file');return;}const target=FEEDBACK[code]?.[4];if(target){go(target);if(code==='AI_NOT_CONFIGURED')document.querySelector('[data-action="run-ai-topic"]')?.closest('section')?.scrollIntoView({block:'start'});}});
document.addEventListener('invalid',event=>{if(event.target.closest('#projectForm')){event.target.setAttribute('aria-invalid','true');let msg=event.target.parentElement.querySelector('.inline-error');if(!msg){msg=document.createElement('p');msg.className='inline-error';event.target.after(msg);}msg.textContent='Trường này cần giá trị hợp lệ để lưu và đối chiếu taxonomy.';}},true);
document.addEventListener('input',event=>{if(event.target.closest('#projectForm'))projectEpoch++;if(event.target.validity?.valid){event.target.removeAttribute('aria-invalid');event.target.parentElement?.querySelector('.inline-error')?.remove();}});

window.addEventListener('pagehide',closeCompletion);
