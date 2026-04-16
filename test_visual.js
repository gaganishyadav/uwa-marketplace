const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const BASE = 'http://127.0.0.1:5001';

  // 1. Landing page
  await page.goto(BASE + '/');
  await page.screenshot({ path: 'screenshots/01_landing.png', fullPage: true });
  console.log('✓ Landing page');

  // 2. Register
  await page.goto(BASE + '/register');
  await page.screenshot({ path: 'screenshots/02_register.png', fullPage: true });
  console.log('✓ Register page');

  // 3. Create a test user
  await page.fill('input[name="username"]', 'testuser');
  await page.fill('input[name="email"]', 'test@uwa.edu.au');
  await page.fill('input[name="password"]', 'Testpass123!');
  await page.fill('input[name="confirm_password"]', 'Testpass123!');
  await page.click('button[type="submit"]');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: 'screenshots/03_after_register.png', fullPage: true });
  console.log('✓ After register:', await page.url());

  // 4. Login page
  await page.goto(BASE + '/login');
  await page.screenshot({ path: 'screenshots/04_login.png', fullPage: true });
  console.log('✓ Login page');

  // 5. Login
  await page.fill('input[name="email"]', 'test@uwa.edu.au');
  await page.fill('input[name="password"]', 'Testpass123!');
  await page.click('button[type="submit"]');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: 'screenshots/05_after_login.png', fullPage: true });
  console.log('✓ After login:', await page.url());

  // 6. Dashboard
  await page.goto(BASE + '/dashboard');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: 'screenshots/06_dashboard.png', fullPage: true });
  console.log('✓ Dashboard');

  // 7. Gallery
  await page.goto(BASE + '/gallery');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: 'screenshots/07_gallery.png', fullPage: true });
  console.log('✓ Gallery');

  // 8. Create a listing
  await page.goto(BASE + '/create');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: 'screenshots/08_create_listing.png', fullPage: true });
  console.log('✓ Create listing page');

  // Fill the listing form
  const titleInput = await page.$('input[name="title"]');
  if (titleInput) {
    await page.fill('input[name="title"]', 'Calculus Textbook');
    await page.fill('textarea[name="description"]', 'First year calculus textbook in great condition. No highlights or notes.');
    await page.fill('input[name="price"]', '25');
    await page.selectOption('select[name="category"]', 'Textbooks');
    await page.selectOption('select[name="condition"]', 'Good');
    await page.selectOption('select[name="meetup_location"]', 'Reid Library');
    await page.screenshot({ path: 'screenshots/09_create_filled.png', fullPage: true });
    console.log('✓ Create listing form filled');

    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/10_after_create.png', fullPage: true });
    console.log('✓ After creating listing:', await page.url());
  }

  // 11. Gallery with listing
  await page.goto(BASE + '/gallery');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: 'screenshots/11_gallery_with_listing.png', fullPage: true });
  console.log('✓ Gallery with listing');

  // 12. Listing detail
  const listingLink = await page.$('a[href*="/listing/"]');
  if (listingLink) {
    await listingLink.click();
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/12_listing_detail.png', fullPage: true });
    console.log('✓ Listing detail:', await page.url());
  }

  // 13. Dashboard with listing
  await page.goto(BASE + '/dashboard');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: 'screenshots/13_dashboard_with_listing.png', fullPage: true });
  console.log('✓ Dashboard with listing');

  await browser.close();
  console.log('\nAll screenshots saved to screenshots/');
})();
