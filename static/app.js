const money = n => new Intl.NumberFormat('es-MX',{style:'currency',currency:'MXN',maximumFractionDigits:0}).format(n);
async function load(){
  const [props, appts, health] = await Promise.all([
    fetch('/api/properties').then(r=>r.json()),
    fetch('/api/appointments').then(r=>r.json()),
    fetch('/api/health').then(r=>r.json()),
  ]);
  document.getElementById('statusText').textContent = health.status === 'online' ? 'Servicios en línea' : 'Sin conexión';
  document.getElementById('properties').innerHTML = props.map(p=>`<div class="property"><strong>${p.title}</strong><span>${p.location}</span><span class="pill">${p.operation}</span><span class="price">${money(p.price)}</span></div>`).join('');
  document.getElementById('appointments').innerHTML = appts.map(a=>`<div class="event"><strong>${a.client_name}</strong><span>Propiedad #${a.property_id} · ${a.date} · ${a.time} · ${a.status}</span></div>`).join('');
}
document.getElementById('reload').addEventListener('click', load); load();
