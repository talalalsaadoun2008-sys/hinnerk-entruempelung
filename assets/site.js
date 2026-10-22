// Hinnerk – kleine Skripte. Ohne Skript funktioniert alles weiter (alles sichtbar, Links statt Knöpfe).
(function () {
  document.documentElement.classList.add('js');

  // Auftritte: Teile jedes Abschnitts nacheinander, einmal.
  var ziele = document.querySelectorAll('[data-auf], .bogen');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('da'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    ziele.forEach(function (el) { io.observe(el); });
  } else {
    ziele.forEach(function (el) { el.classList.add('da'); });
  }

  // Ablauf-Akkordeon
  document.querySelectorAll('.akk').forEach(function (akk) {
    var li = akk.querySelectorAll('li');
    li.forEach(function (x) {
      var b = x.querySelector('button');
      if (!b) return;
      b.addEventListener('click', function () {
        li.forEach(function (y) { y.classList.remove('offen'); var bb = y.querySelector('button'); if (bb) bb.setAttribute('aria-expanded', 'false'); });
        x.classList.add('offen'); b.setAttribute('aria-expanded', 'true');
      });
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
      if (!o) { out.innerHTML = ''; return; }
      var mail = 'mailto:' + f.getAttribute('data-mail') + '?subject=' + encodeURIComponent('Entrümpelung in ' + sel.value) +
        '&body=' + encodeURIComponent('Moin Hinnerk,\n\nich möchte eine kostenlose Besichtigung in ' + sel.value + '.\nWas soll geräumt werden: \nWunschtermin: \nRückrufnummer: \n');
      out.innerHTML = '';
      var b = document.createElement('b'); b.textContent = sel.value + ' · Bezirk ' + o.b; out.appendChild(b);
      var p = document.createElement('p'); p.textContent = 'Recyclinghof in der Nähe: ' + o.r; out.appendChild(p);
      var a1 = document.createElement('a'); a1.href = o.s + '.html'; a1.textContent = 'Mehr zu ' + sel.value; out.appendChild(a1);
      out.appendChild(document.createElement('br'));
      var a2 = document.createElement('a'); a2.className = 'knopf knopf-blau'; a2.href = mail; a2.textContent = 'Besichtigung in ' + sel.value + ' anfragen'; out.appendChild(a2);
    }
    sel.addEventListener('change', zeigen);
    if (sel.value) zeigen();
  }

  // Anfrageformular (Unterseiten): baut eine E-Mail, speichert nichts.
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
})();
