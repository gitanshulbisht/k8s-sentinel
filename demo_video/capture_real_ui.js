const puppeteer = require('puppeteer-core');
const fs = require('fs');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
    defaultViewport: { width: 1920, height: 1080 }
  });

  const page = await browser.newPage();
  
  // 1. Session view
  console.log("Loading session...");
  await page.goto('http://localhost:8790/sessions/01m1199y92m775hj5w89sezv0a', { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 2000));

  // Scroll to top of chat container
  await page.evaluate(() => {
    const scrollContainer = document.querySelector('div[class*="overflow-y-auto"]') || window;
    scrollContainer.scrollTo(0, 0);
  });
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: 'demo_video/tf_captures/real_session_top.png' });
  console.log("Captured real_session_top.png");

  // Scroll to middle (tool calls & diagnosis)
  await page.evaluate(() => {
    const scrollContainer = document.querySelector('div[class*="overflow-y-auto"]') || window;
    scrollContainer.scrollTo(0, 500);
  });
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: 'demo_video/tf_captures/real_session_diagnosis.png' });
  console.log("Captured real_session_diagnosis.png");

  // Scroll to bottom (recall & proposed fix)
  await page.evaluate(() => {
    const scrollContainer = document.querySelector('div[class*="overflow-y-auto"]') || window;
    scrollContainer.scrollTo(0, document.body.scrollHeight || 3000);
  });
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: 'demo_video/tf_captures/real_session_bottom.png' });
  console.log("Captured real_session_bottom.png");

  // 2. Agents Library View (click on Agents Library in sidebar if present)
  try {
    const agentsBtn = await page.$('button, a, div[role="button"]');
    await page.evaluate(() => {
      const items = Array.from(document.querySelectorAll('*'));
      const agentEl = items.find(el => el.textContent && el.textContent.includes('Agents Library'));
      if (agentEl) agentEl.click();
    });
    await new Promise(r => setTimeout(r, 1500));
    await page.screenshot({ path: 'demo_video/tf_captures/real_agents_library.png' });
    console.log("Captured real_agents_library.png");
  } catch(e) {
    console.log("Agents library error:", e.message);
  }

  // 3. Settings View
  try {
    await page.goto('http://localhost:8790/settings', { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 1500));
    await page.screenshot({ path: 'demo_video/tf_captures/real_settings.png' });
    console.log("Captured real_settings.png");
  } catch(e) {
    console.log("Settings error:", e.message);
  }

  await browser.close();
  console.log("All real UI captures completed!");
})();
