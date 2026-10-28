// Hinnerk – kleine Skripte. Ohne Skript funktioniert alles weiter.
(function () {
  document.documentElement.classList.add('js');

  // Auftritte beim Scrollen, einmal.
  var ziele = document.querySelectorAll('[data-auf]');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('da'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -6% 0px' });
    ziele.forEach(function (el) { io.observe(el); });
  } else {
    ziele.forEach(function (el) { el.classList.add('da'); });
  }

  // Kopfzeile bekommt beim Scrollen eine Linie.
  var kopf = document.querySelector('.kopf');
  if (kopf) {
    var setz = function () { kopf.classList.toggle('gescrollt', window.scrollY > 40); };
    window.addEventListener('scroll', setz, { passive: true }); setz();
  }

  // Menü schließt nach Klick auf einen Link.
  document.querySelectorAll('.menue nav a').forEach(function (a) {
    a.addEventListener('click', function () { a.closest('details').removeAttribute('open'); });
  });

  // Kartenreihe mit Pfeilen.
  document.querySelectorAll('[data-schieb]').forEach(function (b) {
    b.addEventListener('click', function () {
      var r = b.closest('section').querySelector('[data-reihe]');
      if (r) r.scrollBy({ left: Number(b.getAttribute('data-schieb')) * 316, behavior: 'smooth' });
    });
  });

  // Stadtteil-Finder
  var f = document.getElementById('finder');
  var daten = document.getElementById('finder-daten');
  if (f && daten) {
    var orte = JSON.parse(daten.textContent);
    var sel = f.querySelector('select');
    var out = f.querySelector('.ergebnis');
    function zeigen() {
      var o = orte[sel.value];
      out.innerHTML = '';
      if (!o) return;
      var mail = 'mailto:' + f.getAttribute('data-mail') + '?subject=' + encodeURIComponent('Entrümpelung in ' + sel.value) +
        '&body=' + encodeURIComponent('Moin Hinnerk,\n\nich möchte eine kostenlose Besichtigung in ' + sel.value + '.\nWas soll geräumt werden: \nWunschtermin: \nRückrufnummer: \n');
      var b = document.createElement('b'); b.textContent = sel.value + ' · Bezirk ' + o.b; out.appendChild(b);
      var p = document.createElement('p'); p.textContent = 'Recyclinghof in der Nähe: ' + o.r; out.appendChild(p);
      var a1 = document.createElement('a'); a1.href = o.s + '.html'; a1.textContent = 'Mehr zu ' + sel.value; out.appendChild(a1);
      out.appendChild(document.createElement('br'));
      var a2 = document.createElement('a'); a2.className = 'knopf'; a2.href = mail; a2.textContent = 'Besichtigung in ' + sel.value + ' anfragen'; out.appendChild(a2);
    }
    sel.addEventListener('change', zeigen);
    if (sel.value) zeigen();
  }

  // Anfrageformular: baut eine E-Mail, speichert nichts.
  var form = document.getElementById('anfrage-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var d = new FormData(form);
      var seite = form.getAttribute('data-seite') || 'Website';
      var text = ['Moin Hinnerk,', '', 'ich komme von der Seite: ' + seite,
        'Was soll geräumt werden: ' + (d.get('was') || ''), 'Ort / Stadtteil: ' + (d.get('ort') || ''),
        'Wunschtermin: ' + (d.get('termin') || ''), '', (d.get('nachricht') || ''), '',
        'Name: ' + (d.get('name') || ''), 'Rückrufnummer: ' + (d.get('telefon') || '')].join('\n');
      window.location.href = 'mailto:' + form.getAttribute('data-mail') + '?subject=' +
        encodeURIComponent('Anfrage Entrümpelung – ' + (d.get('ort') || seite)) + '&body=' + encodeURIComponent(text);
    });
  }
  // Kostenrechner (nur Richtwert)
  var rb = document.querySelector('[data-rechner]');
  if (rb) {
    var cfg = JSON.parse(rb.getAttribute('data-rechner'));
    var rf = rb.querySelector('form');
    var out = rb.querySelector('.rechner-ergebnis');
    var knopf = rb.querySelector('.rechner-knopf');
    var euro = function (n) { return n.toLocaleString('de-DE') + ' €'; };
    var rechne = function () {
      var qm = Math.max(10, Math.min(400, Number(rf.qm.value) || 0));
      var f = rf.querySelector('input[name="fuell"]:checked');
      var satz = f ? Number(f.value) : cfg.fuell[1][1];
      var et = Number(rf.etage.value) || 0;
      var preis = qm * satz * (1 + et * cfg.etage_prozent / 100) + (rf.extra.checked ? cfg.extra_raum : 0);
      preis = Math.max(cfg.minimum, preis);
      var von = Math.max(cfg.minimum, Math.round(preis * (1 - cfg.spanne) / 10) * 10);
      var bis = Math.round(preis * (1 + cfg.spanne) / 10) * 10;
      out.innerHTML = '';
      out.appendChild(document.createTextNode('Richtwert für ' + qm + ' m²:'));
      var b = document.createElement('b'); b.textContent = 'ca. ' + euro(von) + ' – ' + euro(bis); out.appendChild(b);
      var art = f ? f.parentNode.textContent.trim() : '';
      var text = 'Moin Hinnerk,\n\nich möchte einen Festpreis für eine Entrümpelung.\nWohnfläche: ' + qm + ' m²\nFüllgrad: ' + art +
        '\nStockwerk: ' + rf.etage.options[rf.etage.selectedIndex].text + (rf.extra.checked ? '\nKeller oder Dachboden kommt dazu' : '') +
        '\nRichtwert laut Rechner: ' + euro(von) + ' – ' + euro(bis) + '\n\nStadtteil: \nWunschtermin: \nRückrufnummer: \n';
      knopf.href = 'mailto:' + rb.getAttribute('data-mail') + '?subject=' + encodeURIComponent('Festpreis-Anfrage Entrümpelung') + '&body=' + encodeURIComponent(text);
    };
    rf.addEventListener('input', rechne); rf.addEventListener('change', rechne); rechne();
  }
})();
