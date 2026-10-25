const PRICES = { standard: 180, comfort: 250, vip: 350 };

const LAYOUT = [
  { row: 1, seats: 18, zone: 'standard' },
  { row: 2, seats: 18, zone: 'standard' },
  { row: 3, seats: 18, zone: 'standard' },
  { row: 4, seats: 19, zone: 'comfort' },
  { row: 5, seats: 19, zone: 'comfort' },
  { row: 6, seats: 19, zone: 'comfort' },
  { row: 7, seats: 19, zone: 'comfort' },
  { row: 8, seats: 19, zone: 'comfort' },
  { row: 9, seats: 14, zone: 'vip' },
  { row: 10, seats: 14, zone: 'vip' },
  { row: 11, seats: 14, zone: 'vip' },
  { row: 12, seats: 14, zone: 'vip' }
];

const map = document.getElementById('seat-map');
const countEl = document.getElementById('count');
const sumEl = document.getElementById('sum');
const buyBtn = document.getElementById('buy-btn');
const seatsInput = document.getElementById('seats-input');
const totalInput = document.getElementById('total-input');
const form = document.getElementById('booking-form');

if (map) {
  const taken = new Set(JSON.parse(map.dataset.taken || '[]'));
  const selected = new Map();

  LAYOUT.forEach(({ row, seats, zone }) => {
    const rowEl = document.createElement('div');
    rowEl.className = 'seat-row';

    const label = document.createElement('span');
    label.className = 'row-label';
    label.textContent = row;
    rowEl.appendChild(label);

    for (let s = 1; s <= seats; s++) {
      const id = row + '-' + s;
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'seat ' + zone;
      btn.textContent = s;

      if (taken.has(id)) {
        btn.classList.add('taken');
        btn.disabled = true;
      } else {
        btn.addEventListener('click', () => toggleSeat(btn, id, PRICES[zone]));
      }
      rowEl.appendChild(btn);
    }

    rowEl.appendChild(label.cloneNode(true));
    map.appendChild(rowEl);
  });

  function toggleSeat(btn, id, price) {
    if (selected.has(id)) {
      selected.delete(id);
      btn.classList.remove('selected');
    } else {
      selected.set(id, price);
      btn.classList.add('selected');
    }
    updateSummary();
  }

  function calcTotal() {
    let total = 0;
    selected.forEach((p) => { total += p; });
    return total;
  }

  function updateSummary() {
    countEl.textContent = selected.size;
    sumEl.textContent = calcTotal();
    buyBtn.disabled = selected.size === 0;
  }

  form.addEventListener('submit', (e) => {
    if (selected.size === 0) {
      e.preventDefault();
      return;
    }
    seatsInput.value = [...selected.keys()].join(',');
    totalInput.value = calcTotal();
  });
}
const sessionInputs = document.querySelectorAll(
  '#booking-form select[name="movie"], #booking-form input[name="date"], #booking-form select[name="time"]'
);
sessionInputs.forEach((el) => {
  el.addEventListener('change', () => {
    const params = new URLSearchParams();
    sessionInputs.forEach((input) => {
      if (input.value) params.set(input.name, input.value);
    });
    window.location.search = params.toString();
  });
});