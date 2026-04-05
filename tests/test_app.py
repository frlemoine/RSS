import unittest

import app


SAMPLE_INDEX = """
<html>
  <body>
    <a href="JADE_20260401-215458.tar.gz">JADE_20260401-215458.tar.gz</a>
    <a href="JADE_20260402-215758.tar.gz">JADE_20260402-215758.tar.gz</a>
    <a href="JADE_20260403-221345.tar.gz">JADE_20260403-221345.tar.gz</a>
  </body>
</html>
"""

SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<TEXTE_JURI_ADMIN>
  <META>
    <META_COMMUN>
      <ID>CETATEXT000053742045</ID>
      <URL>texte/juri/admin/CETA/TEXT/00/00/53/74/20/CETATEXT000053742045.xml</URL>
      <NATURE>Texte</NATURE>
    </META_COMMUN>
    <META_SPEC>
      <META_JURI>
        <TITRE>CAA de BORDEAUX, 2ème chambre, 26/03/2026, 24BX00910, Inédit au recueil Lebon</TITRE>
        <DATE_DEC>2026-03-26</DATE_DEC>
        <JURIDICTION>CAA de BORDEAUX</JURIDICTION>
        <NUMERO>24BX00910</NUMERO>
      </META_JURI>
      <META_JURI_ADMIN>
        <FORMATION>2ème chambre</FORMATION>
        <PUBLI_RECUEIL>C</PUBLI_RECUEIL>
      </META_JURI_ADMIN>
    </META_SPEC>
  </META>
  <TEXTE>
    <BLOC_TEXTUEL>
      <CONTENU>Vu la procédure suivante :<br/>La requête est rejetée.<br/>Article 1er : Rejet.</CONTENU>
    </BLOC_TEXTUEL>
  </TEXTE>
</TEXTE_JURI_ADMIN>
"""


class AppTestCase(unittest.TestCase):
    def test_parse_archive_listing(self) -> None:
        archives = app.parse_archive_listing(SAMPLE_INDEX)
        self.assertEqual(len(archives), 3)
        self.assertEqual(archives[-1]["name"], "JADE_20260403-221345.tar.gz")
        self.assertEqual(archives[-1]["timestamp"], "2026-04-03T22:13:45+02:00")

    def test_parse_decision_xml(self) -> None:
        archive = {
            "name": "JADE_20260403-221345.tar.gz",
            "timestamp": "2026-04-03T22:13:45+02:00",
            "url": "https://example.test/JADE_20260403-221345.tar.gz",
        }
        decision = app.parse_decision_xml(SAMPLE_XML.encode("utf-8"), archive)
        self.assertEqual(decision["id"], "CETATEXT000053742045")
        self.assertEqual(decision["jurisdiction"], "CAA de BORDEAUX")
        self.assertEqual(decision["number"], "24BX00910")
        self.assertIn("Vu la procédure suivante", decision["summary"])
        self.assertTrue(decision["page_path"].endswith("CETATEXT000053742045.html"))

    def test_pick_archives_to_process_bootstrap(self) -> None:
        archives = app.parse_archive_listing(SAMPLE_INDEX)
        selected = app.pick_archives_to_process(archives, [])
        self.assertEqual(len(selected), 3)


if __name__ == "__main__":
    unittest.main()
