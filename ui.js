const $ = selector => document.querySelector(selector);
const grid = $('#product-grid');
const modes = [...document.querySelectorAll('.mode')];
let activeMode = 'text';

async function requestJson(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Không thể kết nối đến ứng dụng Python.');
  return data;
}

const ShopClient = {
  allProducts: () => requestJson('/api/products'),
  product: id => requestJson(`/api/products/${encodeURIComponent(id)}`),
  order: id => requestJson(`/api/orders/${encodeURIComponent(id.trim())}`),
  search: (mode, value) => requestJson('/api/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode, value })
  }),
  searchImageFile: file => requestJson('/api/search/image', {
    method: 'POST',
    headers: { 'Content-Type': file.type || 'application/octet-stream' },
    body: file
  })
};

const palette = {
  Black: { fill: '#303432', bg: '#e7e9e3', detail: '#59615c' },
  White: { fill: '#f7f8ef', bg: '#e8eddc', detail: '#b4c3a0' },
  Blue: { fill: '#4b7390', bg: '#e2edf0', detail: '#acc9d3' },
  Brown: { fill: '#9b6847', bg: '#f0e7dd', detail: '#c99b78' },
  Red: { fill: '#d66e5d', bg: '#f5e7df', detail: '#ecaa92' },
  Grey: { fill: '#919894', bg: '#ebece8', detail: '#bdc4bf' }
};

function productArt(product, withPill = true) {
  const { fill, bg, detail } = palette[product.color];
  const shapes = {
    shoe: `<path d="M22 87c15 1 25-8 35-29l18 5c5 13 18 18 32 23 16 6 28 11 45 12l12 6c5 3 8 8 8 15v6H23c-9 0-15-6-15-14V99c0-7 5-12 14-12Z" fill="${fill}" stroke="#242925" stroke-width="2"/><path d="M10 113h161v13H23c-7 0-12-4-13-13Z" fill="#fafbf4" stroke="#242925" stroke-width="2"/><path d="m61 76 28 10m-17-18 26 11m-14-14 23 9" stroke="${detail}" stroke-width="4" stroke-linecap="round"/><path d="M114 94c11 6 21 9 40 9" fill="none" stroke="${detail}" stroke-width="5" stroke-linecap="round"/>`,
    backpack: `<path d="M61 42V32c0-14 11-24 29-24s29 10 29 24v10" fill="none" stroke="${detail}" stroke-width="9"/><rect x="42" y="34" width="96" height="112" rx="27" fill="${fill}" stroke="#20241f" stroke-width="2"/><path d="M48 78c-13 1-18 12-18 22v33m103-55c14 1 18 12 18 22v33" fill="none" stroke="${detail}" stroke-width="10" stroke-linecap="round"/><rect x="62" y="86" width="56" height="39" rx="9" fill="${detail}" stroke="#20241f" stroke-width="2"/><path d="M76 43h28" stroke="${detail}" stroke-width="4"/>`,
    bag: `<path d="M37 72h106l9 69H28z" fill="${fill}" stroke="#392d28" stroke-width="2"/><path d="M62 76V55c0-17 11-30 28-30s28 13 28 30v21" fill="none" stroke="${detail}" stroke-width="8"/><path d="M31 104h118" stroke="${detail}" stroke-width="5"/><rect x="77" y="100" width="27" height="20" rx="4" fill="${detail}"/>`,
    shirt: `<path d="m54 31 19-11h34l19 11 31 22-18 32-18-11v71H59V74L41 85 23 53z" fill="${fill}" stroke="#704844" stroke-width="2"/><path d="M73 20c1 12 6 20 17 20s16-8 17-20" fill="none" stroke="${detail}" stroke-width="5"/><path d="M60 91h60" stroke="${detail}" stroke-width="4" opacity=".7"/>`,
    shorts: `<path d="M43 29h94l8 110-49 7-6-51-6 51-49-7z" fill="${fill}" stroke="#20241f" stroke-width="2"/><path d="M42 53h96M90 54v41" stroke="${detail}" stroke-width="5"/><path d="M51 68h24m30 0h24" stroke="${detail}" stroke-width="3"/>`,
    hoodie: `<path d="M65 28c-9-5-15-3-22 4L20 67l18 16 18-17v80h68V66l18 17 18-16-23-35c-7-7-13-9-22-4" fill="${fill}" stroke="#606864" stroke-width="2"/><path d="M65 28c-2 31 13 44 25 44s27-13 25-44c-9-11-17-16-25-16S74 17 65 28Z" fill="${detail}" stroke="#606864" stroke-width="2"/><path d="M81 71v28m18-28v28" stroke="#f4f5ee" stroke-width="3"/><path d="M72 113h36" stroke="${detail}" stroke-width="4"/>`,
    wallet: `<rect x="23" y="48" width="134" height="88" rx="11" fill="${fill}" stroke="#20241f" stroke-width="2"/><path d="M24 67h132" stroke="${detail}" stroke-width="5"/><rect x="90" y="82" width="67" height="39" rx="8" fill="${detail}" stroke="#20241f" stroke-width="2"/><circle cx="113" cy="102" r="5" fill="#d9f36a"/>`
  };
  return `<div class="product-art" style="--art-bg:${bg}">${withPill ? `<span class="pill">${product.id}</span>` : ''}<svg viewBox="0 0 180 165" role="img" aria-label="Minh họa ${product.name}">${shapes[product.art]}</svg></div>`;
}

function renderProducts(items) {
  grid.innerHTML = items.length ? items.map(({ product, score }) => `<article class="product-card">${productArt(product)}<div class="product-body"><div class="product-category">${product.category}</div><div class="product-name">${product.name}</div><div class="product-meta"><span>Màu: ${product.color}</span><span>${score === null ? `Kho: ${product.stock}` : `Điểm: ${score.toFixed(score % 1 ? 3 : 0)}`}</span></div><div class="product-bottom"><span class="product-price">$${product.price}</span><button class="detail-button" type="button" data-product="${product.id}" aria-label="Xem chi tiết ${product.name}">Xem chi tiết ↗</button></div></div></article>`).join('') : `<div class="empty-state"><div class="empty-icon">⌕</div><strong>Chưa tìm thấy sản phẩm</strong><span>Hãy thử từ khóa hoặc vector khác.</span></div>`;
}

async function showAll() {
  try {
    const all = await ShopClient.allProducts();
    renderProducts(all);
    $('#results-title').innerHTML = `Khám phá sản phẩm <span id="result-count">${all.length}</span>`;
    $('#result-description').textContent = 'Mười sản phẩm mẫu từ tài liệu, sẵn sàng để tìm kiếm.';
    $('#query-summary').classList.add('hidden');
    $('#reset-button').classList.add('hidden');
  } catch (error) {
    showError('#search-error', error.message);
  }
}

function showError(selector, message) {
  const element = $(selector);
  element.textContent = message;
  element.classList.toggle('hidden', !message);
}

function setMode(mode) {
  activeMode = mode;
  modes.forEach(button => {
    const selected = button.dataset.mode === mode;
    button.classList.toggle('active', selected);
    button.setAttribute('aria-selected', selected);
  });
  for (const name of ['text', 'voice', 'image']) $(`#${name}-input-panel`).classList.toggle('hidden', name !== mode);
  showError('#search-error', '');
}

function setSurface(surface) {
  const order = surface === 'order';
  $('#product-tab').classList.toggle('selected', !order);
  $('#order-tab').classList.toggle('selected', order);
  $('#product-tab').setAttribute('aria-selected', String(!order));
  $('#order-tab').setAttribute('aria-selected', String(order));
  $('#product-panel').classList.toggle('hidden', order);
  $('#order-panel').classList.toggle('hidden', !order);
  $('#results-section').classList.toggle('hidden', order);
  $('#nav-products').classList.toggle('active', !order);
  $('#nav-orders').classList.toggle('active', order);
}

modes.forEach(button => button.addEventListener('click', () => setMode(button.dataset.mode)));
$('#product-tab').addEventListener('click', () => setSurface('product'));
$('#order-tab').addEventListener('click', () => setSurface('order'));
$('#nav-products').addEventListener('click', () => setSurface('product'));
$('#nav-orders').addEventListener('click', () => setSurface('order'));
$('#reset-button').addEventListener('click', showAll);

let imagePreviewUrl = null;
$('#image-file').addEventListener('change', () => {
  if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
  const file = $('#image-file').files[0];
  $('#image-file-name').textContent = file ? file.name : 'JPG, PNG hoặc WebP · tối đa 5 MB';
  $('#image-preview').classList.toggle('hidden', !file);
  if (file) {
    imagePreviewUrl = URL.createObjectURL(file);
    $('#image-preview').src = imagePreviewUrl;
  } else {
    imagePreviewUrl = null;
    $('#image-preview').removeAttribute('src');
  }
  showError('#search-error', '');
});

$('#search-form').addEventListener('submit', async event => {
  event.preventDefault();
  showError('#search-error', '');
  try {
    let output;
    if (activeMode === 'text') output = await ShopClient.search('text', $('#keyword').value);
    else if (activeMode === 'voice') output = await ShopClient.search('voice', $('#transcript').value);
    else {
      const file = $('#image-file').files[0];
      if (!file) throw new Error('Hãy chọn một ảnh sản phẩm.');
      if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) throw new Error('Chỉ hỗ trợ ảnh JPG, PNG hoặc WebP.');
      if (file.size > 5_000_000) throw new Error('Ảnh quá lớn. Hãy chọn ảnh dưới 5 MB.');
      output = await ShopClient.searchImageFile(file);
    }
    renderProducts(output.results);
    $('#results-title').innerHTML = `Kết quả tìm kiếm <span id="result-count">${output.results.length}</span>`;
    $('#result-description').textContent = output.results.length ? 'Sắp xếp theo điểm phù hợp, cùng điểm thì theo mã sản phẩm.' : 'Không có kết quả phù hợp với truy vấn này.';
    const summary = $('#query-summary');
    summary.textContent = `${activeMode === 'text' ? 'Từ khóa' : activeMode === 'voice' ? 'Bản ghi lời nói' : 'Ảnh tải lên'}: ${activeMode === 'image' ? $('#image-file').files[0].name : output.query.interpreted} · ${output.results.length} kết quả`;
    summary.classList.remove('hidden');
    $('#reset-button').classList.remove('hidden');
    $('#results-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) { showError('#search-error', error.message); }
});

$('#order-form').addEventListener('submit', async event => {
  event.preventDefault();
  showError('#order-error', '');
  $('#order-result').innerHTML = '';
  try {
    const order = await ShopClient.order($('#order-id').value);
    const date = new Date(`${order.date}T00:00:00`).toLocaleDateString('vi-VN');
    $('#order-result').innerHTML = `<article class="order-card"><div class="order-top"><div><div class="section-kicker">THÔNG TIN ĐƠN HÀNG</div><h3>${order.id}</h3></div><span class="status-pill">${order.status}</span></div><div class="order-facts"><div><span>Ngày đặt</span><strong>${date}</strong></div><div><span>Khách hàng</span><strong>${order.customer}</strong></div><div><span>Số mặt hàng</span><strong>${order.items.length}</strong></div></div><div class="order-items">${order.items.map(item => `<div class="order-item"><span>${item.product.name} × ${item.quantity}</span><strong>$${item.unitPrice * item.quantity}</strong></div>`).join('')}</div><div class="order-total"><span>Tổng đơn hàng</span><span>$${order.total}</span></div></article>`;
  } catch (error) { showError('#order-error', error.message); }
});

grid.addEventListener('click', async event => {
  const button = event.target.closest('[data-product]');
  if (!button) return;
  let product;
  try { product = await ShopClient.product(button.dataset.product); }
  catch (error) { showError('#search-error', error.message); return; }
  $('#dialog-content').innerHTML = `<div class="dialog-layout">${productArt(product, false)}<div class="dialog-info"><span class="section-kicker">${product.id} / ${product.category}</span><h2 id="dialog-title">${product.name}</h2><p>${product.description}</p><div class="dialog-data"><div><span>Màu sắc</span><strong>${product.color}</strong></div><div><span>Trong kho</span><strong>${product.stock} sản phẩm</strong></div></div><div class="dialog-price">$${product.price}</div></div></div>`;
  $('#product-dialog').showModal();
});
$('#dialog-close').addEventListener('click', () => $('#product-dialog').close());
$('#product-dialog').addEventListener('click', event => { if (event.target === $('#product-dialog')) $('#product-dialog').close(); });

$('#mic-button').addEventListener('click', () => {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) { showError('#search-error', 'Trình duyệt này chưa hỗ trợ nhận dạng giọng nói. Bạn có thể nhập bản ghi lời nói vào ô bên trên.'); return; }
  const recognition = new Recognition();
  recognition.lang = 'en-US';
  recognition.onresult = event => { $('#transcript').value = event.results[0][0].transcript; $('#mic-button').classList.remove('listening'); };
  recognition.onerror = () => { $('#mic-button').classList.remove('listening'); showError('#search-error', 'Không ghi nhận được giọng nói. Hãy thử lại hoặc nhập bản ghi lời nói.'); };
  recognition.onend = () => $('#mic-button').classList.remove('listening');
  $('#mic-button').classList.add('listening');
  recognition.start();
});

showAll();
