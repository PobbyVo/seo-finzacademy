import {test,expect} from '@playwright/test';
const endpoints={openai:'https://api.openai.com/v1/responses',gemini:'https://generativelanguage.googleapis.com/v1beta/interactions',claude:'https://api.anthropic.com/v1/messages'};
test('settings UI saves, tests only after consent, reloads metadata and removes key',async({page})=>{
 let config:Record<string,unknown>|null=null;let calls=0;
 await page.route('**/api/v1/settings/ai**',async route=>{
  const req=route.request();
  if(req.method()==='PUT'){const b=req.postDataJSON();config={provider:b.provider,model:b.model,endpoint:endpoints[b.provider as keyof typeof endpoints],has_key:true,active:true,status:'NOT_TESTED',tested_at:null,latency_ms:null,error_code:null};}
  if(req.url().endsWith('/test')){calls++;expect(req.postDataJSON()).toEqual({consent:true});config={...config,status:'CONNECTED',tested_at:'2026-11-21T08:00:00Z',latency_ms:125};}
  if(req.method()==='DELETE')config=null;
  await route.fulfill({json:{active_provider:config?.provider||null,configs:config?[config]:[],endpoints}});
 });
 await page.goto('/projects');await page.getByRole('link',{name:'Cài đặt',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Cài đặt AI'})).toBeVisible();
 await page.getByLabel('Nhà cung cấp').selectOption('gemini');await page.getByLabel('Model ID cho Analyst và Critic').fill('user-model');
 await page.getByLabel(/^API key/).fill('fake-browser-key');
 await page.getByRole('button',{name:'Save Settings'}).click();
 await expect(page.getByLabel(/^API key/)).toHaveValue('');expect(calls).toBe(0);
 await expect(page.getByRole('button',{name:'Test Connection'})).toBeDisabled();
 await page.getByRole('checkbox').check();await page.getByRole('button',{name:'Test Connection'}).click();
 await expect(page.getByText('CONNECTED',{exact:true})).toBeVisible();await expect(page.getByText('125 ms',{exact:true})).toBeVisible();
 await page.reload();await expect(page.getByLabel('Model ID cho Analyst và Critic')).toHaveValue('user-model');expect(calls).toBe(1);
 expect(await page.evaluate(()=>JSON.stringify({...localStorage}))).not.toContain('fake-browser-key');
 page.on('dialog',d=>d.accept());await page.getByRole('button',{name:'Remove Key'}).click();await expect(page.getByText(/^AI_NOT_CONFIGURED/)).toBeVisible();
});
test('real API exposes only metadata and UI explains provider failure',async({page,request})=>{
 const r=await request.get('/api/v1/settings/ai');expect(r.status()).toBe(200);expect((await r.json()).active_provider).toBeNull();
 await page.route('**/api/v1/settings/ai**',async route=>{
  if(route.request().url().endsWith('/test')){await route.fulfill({status:401,json:{error:{code:'API_KEY_INVALID',reason:'API key không hợp lệ.',impact:'Chưa xác nhận kết nối.',solution:'Thay API key.'}}});return;}
  await route.fulfill({json:{active_provider:'openai',endpoints,configs:[{provider:'openai',model:'user-model',has_key:true,active:true,status:'NOT_TESTED',tested_at:null,latency_ms:null}]}});
 });
 await page.goto('/settings/ai');await page.getByRole('checkbox').check();await page.getByRole('button',{name:'Test Connection'}).click();
 await expect(page.locator('main').getByRole('alert')).toContainText('API_KEY_INVALID');await expect(page.locator('main').getByRole('alert')).toContainText('Thay API key');
 await expect(page.getByText('CONNECTED',{exact:true})).toHaveCount(0);
});
test('upstream diagnostics survive a failed metadata refresh',async({page})=>{
 let tested=false;
 await page.route('**/api/v1/settings/ai**',async route=>{
  if(route.request().url().endsWith('/test')){
   tested=true;await route.fulfill({status:503,json:{error:{code:'PROVIDER_UNAVAILABLE',reason:'Provider đang không sẵn sàng.',solution:'Thử lại sau.',request_id:'ui-correlation-503',upstream_status:503,upstream_code:'service_unavailable'}}});return;
  }
  if(tested){await route.fulfill({status:500,json:{error:{message_vi:'Không đọc metadata'}}});return;}
  await route.fulfill({json:{active_provider:'gemini',endpoints,configs:[{provider:'gemini',model:'user-model',has_key:true,active:true,status:'NOT_TESTED',tested_at:null,latency_ms:null}]}});
 });
 await page.goto('/settings/ai');await page.getByRole('checkbox').check();await page.getByRole('button',{name:'Test Connection'}).click();
 const alert=page.locator('main').getByRole('alert');
 await expect(alert).toContainText('ui-correlation-503');await expect(alert).toContainText('service_unavailable');await expect(alert).toContainText('HTTP provider: 503');
 await expect(alert).not.toContainText('Không đọc được cấu hình');
});
