// Anfrageformular: baut eine E-Mail an Hinnerk zusammen (kein Server, keine Cookies).
(function () {
  var f = document.getElementById('anfrage-form');
  if (!f) return;
  f.addEventListener('submit', function (e) {
    e.preventDefault();
    var d = new FormData(f);
    var seite = f.getAttribute('data-seite') || 'Website';
    var betreff = 'Anfrage Entrümpelung – ' + (d.get('ort') || seite);
    var text = [
      'Hallo Hinnerk,',
      '',
      'ich komme von der Seite: ' + seite,
      'Was soll geräumt werden: ' + (d.get('was') || ''),
      'Ort / Stadtteil: ' + (d.get('ort') || ''),
      'Wunschtermin: ' + (d.get('termin') || ''),
      '',
      (d.get('nachricht') || ''),
      '',
      'Name: ' + (d.get('name') || ''),
      'Rückrufnummer: ' + (d.get('telefon') || '')
    ].join('\n');
    window.location.href = 'mailto:' + f.getAttribute('data-mail') +
      '?subject=' + encodeURIComponent(betreff) + '&body=' + encodeURIComponent(text);
  });
})();
