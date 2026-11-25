# -*- coding: utf-8 -*-
"""Tests der Weboberfläche (Server-API).  Aufruf:  python3 -m unittest discover tests"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
os.environ["TABULARIUM_KONFIG"] = os.path.join(tempfile.gettempdir(), "tabularium-test-konfig.json")
import tabularium  # noqa: E402
import tabularium_web  # noqa: E402
from test_tabularium import FODS, entsperren  # noqa: E402


class TestWeb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp(prefix="tabularium-web-")
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), tabularium_web.Handler)
        port = cls.server.server_address[1]
        cls.z = tabularium_web.Zustand(os.path.join(cls.dir, "archiv"), port)
        tabularium_web.Handler.z = cls.z
        cls.basis = "http://127.0.0.1:%d" % port
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        entsperren(cls.dir)
        shutil.rmtree(cls.dir, ignore_errors=True)

    def anfrage(self, pfad, daten=None, token=True, kopf=None, roh=None):
        h = dict(kopf or {})
        if token:
            h["X-Tabularium-Token"] = self.z.token
        body = roh
        if daten is not None:
            body = json.dumps(daten).encode()
            h["Content-Type"] = "application/json"
        req = urllib.request.Request(self.basis + pfad, data=body, headers=h)
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def fods(self, name, b, s):
        p = os.path.join(self.dir, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(FODS.format(b=b, s=s, d="2026-11-25"))
        return p

    def test_1_startseite_mit_token(self):
        code, inhalt = self.anfrage("/", token=False)
        self.assertEqual(code, 200)
        self.assertIn(self.z.token, inhalt.decode())

    def test_2_ohne_token_abgewiesen(self):
        code, _ = self.anfrage("/api/status", token=False)
        self.assertEqual(code, 403)
        code, _ = self.anfrage("/api/einchecken", daten={"pfade": []}, token=False)
        self.assertEqual(code, 403)

    def test_3_fremder_host_abgewiesen(self):
        code, _ = self.anfrage("/api/status", kopf={"Host": "angreifer.example"})
        self.assertEqual(code, 403)

    def test_4_ablauf(self):
        p = self.fods("Liste.fods", 100, 120)
        code, r = self.anfrage("/api/einchecken", daten={"pfade": [p], "notiz": "eins"})
        self.assertEqual(code, 200, r)
        self.assertEqual(json.loads(r)["ergebnisse"][0]["version"], 1)
        self.fods("Liste.fods", 150, 170)
        status = json.loads(self.anfrage("/api/status")[1])
        self.assertEqual(status["dokumente"][0]["status"], "geaendert")
        v = json.loads(self.anfrage("/api/vergleich?name=Liste.fods&aktuell=1")[1])
        self.assertEqual(v["zaehlung"]["geaendert"], 2)
        self.anfrage("/api/einchecken", daten={"pfade": [p]})
        v = json.loads(self.anfrage("/api/vergleich?name=Liste.fods")[1])
        self.assertEqual((v["von"], v["bis"]), (1, 2))
        code, daten = self.anfrage("/api/datei?name=Liste.fods&version=1")
        self.assertEqual(code, 200)
        self.assertIn(b'office:value="100"', daten)
        code, bericht = self.anfrage("/api/bericht?name=Liste.fods")
        self.assertIn("Integritätsprüfung bestanden", bericht.decode())
        pr = json.loads(self.anfrage("/api/pruefen", daten={})[1])
        self.assertTrue(pr["ok"], pr)

    def test_5_upload(self):
        with open(self.fods("x.fods", 1, 2), "rb") as f:
            roh = f.read()
        code, r = self.anfrage("/api/hochladen", roh=roh, kopf={
            "X-Dateiname": "Gr%C3%BCn.fods", "Content-Type": "application/octet-stream"})
        self.assertEqual(code, 200, r)
        self.assertEqual(json.loads(r)["ergebnisse"][0]["datei"], "Grün.fods")
        code, r = self.anfrage("/api/hochladen", roh=b"x", kopf={"X-Dateiname": "boese.exe"})
        self.assertEqual(code, 400)

    def test_6_finder_nur_bekannte_pfade(self):
        code, _ = self.anfrage("/api/finder", daten={"pfad": "/etc/passwd"})
        self.assertEqual(code, 400)


if __name__ == "__main__":
    unittest.main()
