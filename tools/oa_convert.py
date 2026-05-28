#!/usr/bin/env python3
"""
EZproxy / OpenAthens URL Converter
University of Waikato Library

Reads a plain text or CSV file of URLs (one per line, or first column of CSV),
converts each to an OpenAthens redirector link, and writes a 4-column CSV:
  source_url, converted_url, status, notes

Usage:
  python3 oa_convert.py input.csv output.csv
  python3 oa_convert.py input.txt output.csv

Options:
  --plain   Convert plain URLs to OpenAthens without EZproxy cleaning
            (default is EZproxy cleaning mode)
  --repair  Diagnose and repair broken OpenAthens URLs

Conversion modes
----------------
EZproxy mode (default):
  Strips EZproxy proxy layers, resolves vendor domain, looks up confirmed
  entry point in the vendor table, and wraps in the OA redirector.

Plain mode (--plain):
  Wraps plain vendor URLs in the OA redirector, substituting confirmed entry
  points from the vendor table where a match is found.

Repair mode (--repair):
  Accepts broken go.openathens.net or proxy.openathens.net URLs and attempts
  to diagnose and correct common faults: double-encoding, wrong institution
  scope, malformed url= parameter, old-style proxy subdomains. Also accepts
  plain vendor URLs and converts them.

Status values in output CSV
---------------------------
  confirmed  Vendor matched in the confirmed entry point table
  ok         Converted cleanly without table match
  warn       Converted but with unusual conditions noted
  repaired   Repaired broken OA URL (repair mode)
  skip       Could not convert — see notes column
"""

import sys
import re
import csv
import argparse
from pathlib import Path
from urllib.parse import unquote, quote

OA_PREFIX = "https://go.openathens.net/redirector/waikato.ac.nz?url="
OA_SCOPE = "waikato.ac.nz"
EZPROXY_HOST = "ezproxy.waikato.ac.nz"


# ---------------------------------------------------------------------------
# Confirmed vendor entry point table
# University of Waikato — confirmed and tested
# Each entry: (domains_list, vendor_name, confirmed_oa_url)
# More specific domains must appear before broader ones in each entry's list.
# Lookup sorts by domain length descending so plants.jstor.org beats jstor.org.
# ---------------------------------------------------------------------------
VENDOR_TABLE = [
    (["acm.org"], "ACM Digital Library",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.acm.org%2Fdl%2F"),
    (["science.org", "sciencemag.org"], "AAAS / Science.org",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.science.org%2F"),
    (["pubs.acs.org"], "ACS Publications",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fpubs.acs.org%2Fsearch%2Fadvanced"),
    (["pubs.aip.org"], "AIP Publishing",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fpubs.aip.org%2Fpages%2Fjournals"),
    (["amdigital.co.uk"], "Adam Matthew Digital",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.firstworldwar.amdigital.co.uk"),
    (["aeaweb.org"], "American Economic Association",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.aeaweb.org%2Fjournals"),
    (["journals.physiology.org"], "American Physiological Society",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fjournals.physiology.org"),
    (["psycnet.apa.org"], "APA / PsycNET",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fpsycnet.apa.org%2F"),
    (["ascelibrary.org"], "ASCE",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fascelibrary.org%2Fjournals"),
    (["mathscinet.ams.org"], "AMS MathSciNet",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fmathscinet.ams.org%2Fmathscinet"),
    (["annualreviews.org"], "Annual Reviews",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.annualreviews.org%2F"),
    (["journals.aps.org"], "APS Journals",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fjournals.aps.org%2Farchive%2F"),
    (["journals.asm.org"], "ASM Journals",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fjournals.asm.org"),
    (["asmedigitalcollection.asme.org"], "ASME Digital Collection",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fasmedigitalcollection.asme.org%2Fjournals"),
    (["compass.astm.org", "astm.org"], "ASTM Compass",
     "https://iam.astm.org/sso/saml2/0oaupiq0svm9luOS84x7?fromURI=https://compass.astm.org"),
    (["asia-studies.com"], "Asia Studies Full-Text Online",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=http%3A%2F%2Fasia-studies.com%2F"),
    (["bloomsburycollections.com"], "Bloomsbury Digital Resources",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.bloomsburycollections.com%2Fhome"),
    (["bwb.co.nz"], "Bridget Williams e-Books",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fbwbtextscollection.bwb.co.nz"),
    (["brill.com"], "Brill Online",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fbrill.com"),
    (["browzine.com"], "BrowZine",
     "https://browzine.com/libraries/463/subjects"),
    (["cabells.com"], "Cabells Journalytics",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fcabells.com"),
    (["cambridge.org"], "Cambridge Core",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.cambridge.org%2Fcore"),
    (["energynews.co.nz"], "Capital Letter / Energy News",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fenergynews.co.nz"),
    (["scifinder-n.cas.org", "cas.org"], "CAS SciFinder",
     "https://sso.cas.org/sp/startSSO.ping?PartnerIdpId=https%3A%2F%2Fidp.waikato.ac.nz%2Fentity&TargetResource=https%3A%2F%2Fscifinder-n.cas.org%2F"),
    (["link.gale.com", "gale.com"], "Cengage / Gale",
     "https://link.gale.com/apps/AONE?u=waikato"),
    (["chicagomanualofstyle.org"], "Chicago Manual of Style Online",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.chicagomanualofstyle.org"),
    (["journals.uchicago.edu"], "Chicago Journals",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.journals.uchicago.edu%2F"),
    (["clinicalkey.com"], "ClinicalKey Student",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.clinicalkey.com%2Fstudent%2Fnursing"),
    (["credoreference.com"], "Credo Reference",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fsearch.credoreference.com"),
    (["connectsci.au"], "CSIRO / ConnectSci",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fconnectsci.au%2Fwr"),
    (["datanalysis.morningstar", "morningstar.com.au"], "DatAnalysis",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fdatanalysis.morningstar.com.au%2Faf%2Fdathome%3Fxtm-licensee%3Ddatpremium"),
    (["degruyterbrill.com", "degruyter.com"], "De Gruyter / De Gruyter Brill",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fdegruyterbrill.com"),
    (["digitaltheatreplus.com"], "Digital Theatre Plus",
     "https://auth.digitaltheatreplus.com/sso/saml2/0oavwa66z2j634owi4x7"),
    (["docuseek2.com"], "Docuseek",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fdocuseek2.com"),
    (["dukeupress.edu"], "Duke University Press",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fread.dukeupress.edu"),
    (["ebookcentral.proquest.com"], "EBookCentral (ProQuest)",
     "https://ebookcentral.proquest.com/lib/waikato/"),
    (["research.ebsco.com"], "EBSCO / Research EBSCO",
     "https://research.ebsco.com/c/fu2ghl"),
    (["ebscohost.com"], "EBSCO DynaMed",
     "https://search.ebscohost.com/login.aspx?authtype=ip,sso&custid=s4804380&groupid=main&profid=dmp"),
    (["euppublishing.com"], "Edinburgh University Press",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.euppublishing.com%2Fdoi%2F10.3366%2Fircl.2025.0638"),
    (["elgaronline.com"], "ElgarOnline",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Felgaronline.com"),
    (["emerald.com"], "Emerald Insight",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.emerald.com%2Finsight"),
    (["academic.eb.com", "britannica.com"], "Encyclopaedia Britannica Academic",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Facademic.eb.com"),
    (["etv.org.nz"], "ETV",
     "https://login.etv.org.nz/etv/login?sso_domain=waikato.ac.nz"),
    (["euromonitor.com"], "Euromonitor",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Feuromonitor.com"),
    (["exacteditions.com"], "Exact Editions",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fexacteditions.com"),
    (["ft.com"], "Financial Times",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fft.com"),
    (["pubs.geoscienceworld.org", "geoscienceworld.org"], "GeoScienceWorld",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fpubs.geoscienceworld.org"),
    (["guilfordjournals.com"], "Guilford Periodicals Online",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fguilfordjournals.com"),
    (["heinonline.org"], "HeinOnline",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fheinonline.org%2FHOL%2FWelcome"),
    (["hstalks.com"], "Henry Stewart Talks",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fhstalks.com"),
    (["humankinetics.com"], "Human Kinetics",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fjournals.humankinetics.com"),
    (["iclr.co.uk"], "ICLR",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Ficlr.co.uk"),
    (["ieeexplore.ieee.org"], "IEEE Xplore",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fieeexplore.ieee.org"),
    (["igi-global.com"], "IGI Global",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.igi-global.com"),
    (["impan.pl"], "IMPAN",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.impan.pl%2Fen%2Fpublishing-house%2Fjournals-and-series%2Facta-arithmetica%2Fall%2F207%2F1"),
    (["inderscienceonline.com"], "Inderscience Online",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Finderscienceonline.com"),
    (["informit.org"], "Informit",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Finformit.org"),
    (["intellectdiscover.com"], "Intellect Discover / Ingenta Connect",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fintellectdiscover.com%2F"),
    (["int-res.com"], "Inter-Research Science Center",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fint-res.com"),
    (["iopscience.iop.org"], "IOPscience",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fiopscience.iop.org"),
    (["ipasource.com"], "IPA Source",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.ipasource.com%2Flogin%2Funiversity-of-waikato%2F"),
    (["plants.jstor.org"], "JSTOR Global Plants",
     "https://proxy.openathens.net/login?qurl=https%3A%2F%2Fplants.jstor.org%2F&entityID=https%3A%2F%2Fidp.waikato.ac.nz%2Fentity"),
    (["jstor.org"], "JSTOR",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.jstor.org%2F"),
    (["jusp.jisc.ac.uk"], "JUSP",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fjusp.jisc.ac.uk%2Flogin%2F"),
    (["kanopy.com"], "Kanopy",
     "https://waikato.kanopy.com/"),
    (["knowledge-basket.co.nz"], "Knowledge Basket",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.knowledge-basket.co.nz%2Fdatabases%2Fnewztext-uni%2Fsearch-newztext%2F"),
    (["lexis.com", "lexisnexis.com"], "LexisNexis Advance",
     "https://advance.lexis.com/nz?federationidp=HC3SRN51745"),
    (["procedures.lww.com"], "Lippincott Procedures",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fprocedures.lww.com%2Flnp%2Fid%2FNZ"),
    (["advisor.lww.com"], "Lippincott Solutions",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fadvisor.lww.com%2Flna%2Fid%2FUOW"),
    (["liverpooluniversitypress.co.uk"], "Liverpool University Press",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.liverpooluniversitypress.co.uk%2Floi%2Fwhpeh%2Fgroup%2Fd2020.y2023"),
    (["lrb.co.uk"], "London Review of Books",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.lrb.co.uk"),
    (["magpies.net.au"], "Magpies",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fmagpies.net.au"),
    (["maorilawreview.co.nz"], "Maori Law Review",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fmaorilawreview.co.nz"),
    (["advantage.marketline.com"], "MarketLine Advantage",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fadvantage.marketline.com%2F"),
    (["accesspharmacy.mhmedical.com"], "McGraw-Hill AccessPharmacy",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Faccesspharmacy.mhmedical.com%2F"),
    (["microbiologyresearch.org"], "Microbiology Society",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.microbiologyresearch.org%2Fcontent%2Fjournal%2Fijsem%2F76%2F1"),
    (["direct.mit.edu"], "MIT Press Direct",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fdirect.mit.edu"),
    (["nature.com"], "Nature",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.nature.com%2F"),
    (["nber.org"], "NBER",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.nber.org%2Fpapers%2F"),
    (["pubs.nctm.org"], "NCTM",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fpubs.nctm.org"),
    (["naxosmusiclibrary.com"], "Naxos Music Library",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwaikato.naxosmusiclibrary.com"),
    (["newleftreview.org"], "New Left Review",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fnewleftreview.org"),
    (["nzgeo.com"], "New Zealand Geographic",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.nzgeo.com"),
    (["companyresearch.nzx.com"], "NZX",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fcompanyresearch.nzx.com%2Fdeep_ar%2F"),
    (["noids.nz"], "Notes on Injectable Drugs",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.noids.nz"),
    (["cdnsciencepub.com"], "NRC Research Press / Canadian Science Publishing",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fcdnsciencepub.com"),
    (["nzcer.org.nz"], "NZCER",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.nzcer.org.nz%2Fjournals%2F"),
    (["oece.nz"], "NZ Int. Research in Early Childhood Education",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Foece.nz%2Fmembers%2Fresearch%2F2019-nzirece-journal-issue-1%2Findigenous-early-childhood-education%2F"),
    (["account.worldcat.org", "worldcat.org"], "OCLC WorldCat",
     "https://waikatouni.account.worldcat.org/account"),
    (["openbookpublishers.com"], "Open Book Publishers",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.openbookpublishers.com%2Fbooks"),
    (["ovidsp.ovid.com", "ovid.com"], "Ovid Technologies",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fovidsp.ovid.com%2Fovidweb.cgi%3FT%3DJS%26NEWS%3Dn%26CSC%3DY%26PAGE%3Dmain%26D%3Doemezd"),
    (["academic.oup.com"], "Oxford Academic",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Facademic.oup.com%2Fageing%2Fissue"),
    (["oxfordartonline.com"], "Oxford Art Online",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.oxfordartonline.com%2F"),
    (["opil.ouplaw.com"], "Oxford Law (OPIL)",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fopil.ouplaw.com%2Fhome%2FOHT"),
    (["oxfordmusiconline.com"], "Oxford Music Online",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.oxfordmusiconline.com%2F"),
    (["oxfordreference.com"], "Oxford Reference",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.oxfordreference.com%2F"),
    (["oxfordscholarlyeditions.com"], "Oxford Scholarly Editions",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.oxfordscholarlyeditions.com"),
    (["veryshortintroductions.com"], "Oxford Very Short Introductions",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fveryshortintroductions.com"),
    (["oed.com"], "Oxford English Dictionary",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.oed.com%2F"),
    (["philpapers.org"], "PhilPapers",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fphilpapers.org"),
    (["pdcnet.org"], "Philosophy Documentation Center",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fpdcnet.org"),
    (["philosophynow.org"], "Philosophy Now",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fphilosophynow.org"),
    (["pnas.org"], "PNAS",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fpnas.org"),
    (["thepolynesiansociety.org"], "The Polynesian Society",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fthepolynesiansociety.org"),
    (["portlandpress.com"], "Portland Press",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fportlandpress.com"),
    (["pressreader.com"], "PressReader",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.pressreader.com"),
    (["muse.jhu.edu"], "Project MUSE",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fmuse.jhu.edu"),
    (["proquest.com"], "ProQuest / Alexander Street",
     "https://www.proquest.com/anznews/fromDatabasesLayer?accountid=17287"),
    (["psychiatryonline.org"], "PsychiatryOnline",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fpsychiatryonline.org%2F"),
    (["jove.com"], "JoVE",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fjove.com"),
    (["pubs.rsc.org"], "Royal Society of Chemistry",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fpubs.rsc.org%2Fen%2Fjournals"),
    (["royalsocietypublishing.org"], "Royal Society Publishing",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Froyalsocietypublishing.org"),
    (["journals.sagepub.com"], "SAGE Journals",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fjournals.sagepub.com"),
    (["methods.sagepub.com"], "Sage Research Methods",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fmethods.sagepub.com%2F"),
    (["scopus.com"], "Scopus",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.scopus.com%2F"),
    (["sciencedirect.com"], "ScienceDirect",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.sciencedirect.com%2F"),
    (["scival.com"], "SciVal",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.scival.com"),
    (["scientificamerican.com"], "Scientific American",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fscientificamerican.com"),
    (["spiedigitallibrary.org"], "SPIE Digital Library",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fspiedigitallibrary.org"),
    (["link.springer.com", "springer.com"], "Springer Nature Link",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Flink.springer.com%2F"),
    (["standards.govt.nz"], "Standards New Zealand",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fstandards.govt.nz%2Fip-check"),
    (["tandfonline.com"], "Taylor & Francis Online",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.tandfonline.com%2F"),
    (["taylorfrancis.com"], "Taylor & Francis Books",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.taylorfrancis.com%2F"),
    (["chronicle.com"], "The Chronicle of Higher Education",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.chronicle.com"),
    (["ucpress.edu"], "University of California Press",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fucpress.edu"),
    (["vitalsource.com"], "VitalSource",
     "https://bc.vitalsource.com/tenants/openathens/bookshelf"),
    (["warc.com"], "WARC",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.warc.com"),
    (["wheelers.co"], "Wheelers ePlatform",
     "https://waikatolibrary.wheelers.co/"),
    (["onlinelibrary.wiley.com", "wiley.com"], "Wiley Online Library",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fonlinelibrary.wiley.com%2F"),
    (["iknowconnect.cch.com"], "Wolters Kluwer / iKnowConnect",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fiknowconnect.cch.com"),
    (["reotupu.co.nz"], "Wordstream / ReoTupu",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.reotupu.co.nz%2Fwslivewakareo%2FDefault.aspx"),
    (["worldscientific.com"], "World Scientific Publishing",
     "https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fworldscientific.com"),
]

# Pre-sort by longest domain first so specific subdomains beat broad domains
_SORTED_TABLE = sorted(
    VENDOR_TABLE,
    key=lambda e: max(len(d) for d in e[0]),
    reverse=True
)


# ---------------------------------------------------------------------------
# Vendors that must NOT be converted to OpenAthens.
# These remain on their existing SSO or other access mechanisms.
# Each entry: (domains_list, vendor_name, reason)
# ---------------------------------------------------------------------------
SKIP_VENDORS = [
    (
        ["westlaw.com", "westlaw.co.nz", "nzlaw.thomsonreuters.com", "signon.thomsonreuters.com"],
        "Westlaw (Thomson Reuters)",
        "Custom SAML via REANZ Tuakiri SSO — not managed via OpenAthens"
    ),
    (
        ["timeshighereducation.com"],
        "Times Higher Education",
        "Incompatible vendor — access via email domain registration only"
    ),
    (
        ["journalsurf.co.nz"],
        "Learning Focus / Journal Surf",
        "Incompatible vendor — shared username/password only"
    ),
    (
        ["antarcticsociety.org.nz"],
        "NZ Antarctic Society",
        "Incompatible vendor — shared username/password only"
    ),
    (
        ["nbr.co.nz"],
        "National Business Review",
        "Incompatible vendor — student domain access, staff individual licences"
    ),
    (
        ["app.disabilitybusters.com"],
        "Disability Busters",
        "Not required — domain account self-registration only"
    ),
    (
        ["pocketmags.com"],
        "Pocketmags",
        "Not required — current access via username/password"
    ),
    (
        ["journals.aom.org", "aom.org"],
        "Academy of Management",
        "Not required — OpenAthens setup incomplete"
    ),
    (
        ["tradelawguide.com"],
        "Trade Law Guide",
        "Not required — vendor must add OA proxy IP before activation"
    ),
]

_SORTED_SKIP = sorted(
    SKIP_VENDORS,
    key=lambda e: max(len(d) for d in e[0]),
    reverse=True
)


def lookup_skip_vendor(url: str) -> tuple[str, str] | None:
    """
    Match a URL against the skip-vendor table.
    Returns (vendor_name, reason) or None.
    """
    lower = url.lower()
    for domains, name, reason in _SORTED_SKIP:
        for domain in domains:
            if domain.lower() in lower:
                return (name, reason)
    return None


def lookup_vendor(url: str) -> tuple[str, str] | None:
    """
    Match a URL against the vendor table.
    Returns (vendor_name, confirmed_oa_url) or None.
    """
    lower = url.lower()
    for domains, name, oa_url in _SORTED_TABLE:
        for domain in domains:
            if domain.lower() in lower:
                return (name, oa_url)
    return None


# ---------------------------------------------------------------------------
# URL conversion helpers
# ---------------------------------------------------------------------------

def to_openathens(url: str) -> str:
    return OA_PREFIX + quote(url, safe="")


def clean_ezproxy_url(raw: str) -> tuple[str, list[str]]:
    """
    Clean an EZproxy URL down to the plain target URL.
    Returns (cleaned_url, notes).
    Raises ValueError with a reason if the URL is unresolvable.
    """
    url = raw.strip()
    notes = []

    # 1. Decode HTML-encoded ampersands
    if "&amp;" in url or url.endswith("&amp"):
        url = url.replace("&amp;", "&").replace("&amp", "&")
        notes.append("HTML-encoded ampersands decoded (&amp; to &)")

    # 2. Handle Google redirect wrapper
    if re.match(r"^https?://(?:www\.)?google\.com/url\?", url, re.IGNORECASE):
        q_match = re.search(r"[?&]q=([^&]+)", url)
        if q_match:
            url = unquote(q_match.group(1))
            notes.append("Extracted from Google redirect wrapper")

    # 3. Detect broken inputs
    if re.search(r"location\.href", url, re.IGNORECASE) or \
       re.search(r"javascript:", url, re.IGNORECASE):
        raise ValueError("JavaScript fragment — not a real URL")
    if not re.match(r"^https?://", url, re.IGNORECASE):
        raise ValueError("Does not start with http:// or https://")

    # 4. Strip EZproxy login wrapper — up to 2 layers
    for _ in range(2):
        login_match = re.match(
            r"^https?://ezproxy\.waikato\.ac\.nz/login\?q?url=(.+)$",
            url, re.IGNORECASE
        )
        if login_match:
            target = login_match.group(1)
            try:
                target = unquote(target)
            except Exception:
                pass
            notes.append("EZproxy login wrapper stripped")
            url = target
        else:
            break

    # 5. Convert proxied hostname
    proxy_match = re.match(
        r"^(https?://)((?:[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?\.)*(?:[a-z0-9\-]+))"
        r"\.ezproxy\.waikato\.ac\.nz(/.*)?$",
        url, re.IGNORECASE
    )
    if proxy_match:
        scheme = proxy_match.group(1)
        proxied_host = proxy_match.group(2)
        rest = proxy_match.group(3) or ""
        real_host = proxied_host.replace("-", ".")
        url = scheme + real_host + rest
        if proxied_host != real_host:
            notes.append(f"Proxied hostname restored: {proxied_host} -> {real_host}")

    # 6. Handle old-style OpenAthens proxy subdomain:
    #    vendor-host.ap1.proxy.openathens.net -> vendor.host
    oa_proxy_match = re.match(
        r"^(https?://)([\w\-]+)\.ap\d*\.proxy\.openathens\.net(/.*)?$",
        url, re.IGNORECASE
    )
    if oa_proxy_match:
        proxied_host = oa_proxy_match.group(2)
        path = oa_proxy_match.group(3) or "/"
        real_host = proxied_host.replace("-", ".")
        url = "https://" + real_host + path
        notes.append(f"OA proxy subdomain stripped: {proxied_host} -> {real_host}")

    # 7. Bare DOI
    if re.match(r"^10\.\d{4,}/", url):
        url = "https://doi.org/" + url
        notes.append("Bare DOI — prefixed with https://doi.org/")

    # 8. Final sanity check
    if not re.match(r"^https?://[a-z0-9]", url, re.IGNORECASE):
        raise ValueError("Could not extract a valid URL after processing")

    return url, notes


def repair_oa_url(raw: str) -> tuple[str, str, list[str]]:
    """
    Diagnose and repair a broken OpenAthens URL.
    Returns (status, repaired_url_or_empty, notes).
    """
    url = raw.strip()
    notes = []

    is_oa_redirector = bool(re.match(
        r"^https?://go\.openathens\.net/redirector/", url, re.IGNORECASE))
    is_oa_proxy = bool(re.match(
        r"^https?://proxy\.openathens\.net/", url, re.IGNORECASE))
    is_oa_proxy_subdomain = bool(re.search(
        r"\.ap\d*\.proxy\.openathens\.net", url, re.IGNORECASE))

    # Old-style OA proxy subdomain: vendor.ap1.proxy.openathens.net/path
    if is_oa_proxy_subdomain:
        proxy_match = re.match(
            r"^(https?://)([\w\-]+)\.ap\d*\.proxy\.openathens\.net(/.*)?$",
            url, re.IGNORECASE
        )
        if proxy_match:
            proxied_host = proxy_match.group(2)
            path = proxy_match.group(3) or "/"
            real_host = proxied_host.replace("-", ".")
            vendor_url = "https://" + real_host + path
            notes.append(
                f"Old-style OA proxy subdomain — vendor host restored: "
                f"{proxied_host} -> {real_host}"
            )
            skip_match = lookup_skip_vendor(vendor_url)
            if skip_match:
                name, reason = skip_match
                notes.append(f"{name}: {reason}")
                return ("skip", "", notes)
            match = lookup_vendor(vendor_url)
            if match:
                name, oa_url = match
                notes.append(f"Vendor recognised: {name} — confirmed entry point substituted")
                return ("repaired", oa_url, notes)
            else:
                notes.append("Vendor not in confirmed table — standard redirector URL constructed")
                return ("repaired", to_openathens(vendor_url), notes)

    if is_oa_redirector or is_oa_proxy:
        # Extract the url= parameter
        url_param_match = re.search(r"[?&]q?url=(.+?)(?:&[a-zA-Z]|$)", url, re.IGNORECASE)
        if not url_param_match:
            notes.append("No url= parameter found in OpenAthens URL — cannot repair")
            return ("skip", "", notes)

        raw_param = url_param_match.group(1)

        # Detect and correct double-encoding (%253A, %252F etc.)
        if re.search(r"%25[0-9a-fA-F]{2}", raw_param):
            raw_param = unquote(raw_param)
            notes.append("Double-encoded URL parameter corrected (%25xx -> %xx)")

        try:
            url_param = unquote(raw_param)
        except Exception:
            url_param = raw_param

        if not re.match(r"^https?://", url_param, re.IGNORECASE):
            notes.append(f"url= parameter does not contain a valid URL: {url_param}")
            return ("skip", "", notes)

        # Check if the extracted vendor URL is on the skip list
        skip_match = lookup_skip_vendor(url_param)
        if skip_match:
            name, reason = skip_match
            notes.append(f"{name}: {reason}")
            return ("skip", "", notes)

        # Check institution scope
        scope_match = re.search(r"redirector/([^?/]+)", url, re.IGNORECASE)
        if scope_match and scope_match.group(1) != OA_SCOPE:
            notes.append(
                f"Wrong institution scope: \"{scope_match.group(1)}\" "
                f"(expected \"{OA_SCOPE}\")"
            )

        # Table lookup on the extracted vendor URL
        match = lookup_vendor(url_param)
        if match:
            name, oa_url = match
            notes.append(f"Vendor recognised: {name} — confirmed entry point substituted")
            return ("repaired", oa_url, notes)

        # Re-encode cleanly
        clean_rebuilt = to_openathens(url_param)
        if clean_rebuilt != url:
            notes.append("URL re-encoded cleanly")
            return ("repaired", clean_rebuilt, notes)

        notes.append("No obvious fault detected — URL returned as-is")
        return ("warn", url, notes)

    # Not an OA URL — treat as plain vendor URL needing conversion
    if re.match(r"^https?://", url, re.IGNORECASE):
        skip_match = lookup_skip_vendor(url)
        if skip_match:
            name, reason = skip_match
            notes.append(f"{name}: {reason}")
            return ("skip", "", notes)
        match = lookup_vendor(url)
        if match:
            name, oa_url = match
            notes.append(f"Not an OA URL — vendor recognised: {name} — confirmed entry point used")
            return ("repaired", oa_url, notes)
        notes.append("Not an OA URL — wrapped in standard redirector")
        return ("repaired", to_openathens(url), notes)

    return ("skip", "", ["Does not appear to be a valid URL"])


# ---------------------------------------------------------------------------
# Main conversion dispatcher
# ---------------------------------------------------------------------------

def convert_line(
    raw: str,
    plain_mode: bool = False,
    repair_mode: bool = False
) -> tuple[str, str, str, str]:
    """
    Convert a single URL.
    Returns (source, converted_url_or_empty, status, notes_string).
    Status: confirmed | ok | warn | repaired | skip
    """
    source = raw.strip()
    if not source:
        return ("", "", "", "")

    if repair_mode:
        status, converted, notes = repair_oa_url(source)
        return (source, converted, status, "; ".join(notes))

    if plain_mode:
        if not re.match(r"^https?://", source, re.IGNORECASE):
            return (source, "", "skip", "Does not start with http:// or https://")
        skip_match = lookup_skip_vendor(source)
        if skip_match:
            name, reason = skip_match
            return (source, "", "skip", f"{name}: {reason}")
        match = lookup_vendor(source)
        if match:
            name, oa_url = match
            return (source, oa_url, "confirmed", f"Confirmed entry point: {name}")
        return (source, to_openathens(source), "ok", "")

    # EZproxy mode
    try:
        cleaned, notes = clean_ezproxy_url(source)
        skip_match = lookup_skip_vendor(cleaned)
        if skip_match:
            name, reason = skip_match
            return (source, "", "skip", f"{name}: {reason}")
        match = lookup_vendor(cleaned)
        if match:
            name, oa_url = match
            unusual = [n for n in notes
                       if not n.startswith("Proxied hostname restored")
                       and n != "EZproxy login wrapper stripped"]
            all_notes = unusual + [f"Confirmed entry point: {name}"]
            return (source, oa_url, "confirmed", "; ".join(all_notes))
        unusual = [n for n in notes
                   if not n.startswith("Proxied hostname restored")
                   and n != "EZproxy login wrapper stripped"]
        status = "warn" if unusual else "ok"
        return (source, to_openathens(cleaned), status, "; ".join(unusual))
    except ValueError as e:
        return (source, "", "skip", str(e))


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def read_input(path: Path) -> list[str]:
    """
    Read URLs from a .txt or .csv file.
    For CSV, extracts the first column, skipping a header if the first
    cell does not look like a URL.
    """
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()

    if path.suffix.lower() == ".csv" or ("," in (lines[0] if lines else "")):
        reader = csv.reader(lines)
        rows = list(reader)
        if rows and not re.match(r"^https?://", rows[0][0].strip(), re.IGNORECASE):
            rows = rows[1:]
        return [row[0].strip() for row in rows if row and row[0].strip()]
    else:
        return [l.strip() for l in lines]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert EZproxy or OpenAthens URLs for University of Waikato Library."
    )
    parser.add_argument("input", help="Input file (.txt or .csv)")
    parser.add_argument("output", help="Output CSV file")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--plain",
        action="store_true",
        help="Plain URL mode — wrap vendor URLs in the OA redirector without EZproxy cleaning",
    )
    mode_group.add_argument(
        "--repair",
        action="store_true",
        help="Repair mode — diagnose and fix broken OpenAthens URLs",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    urls = read_input(input_path)
    if not urls:
        print("Error: no URLs found in input file.", file=sys.stderr)
        sys.exit(1)

    mode_label = "repair" if args.repair else ("plain" if args.plain else "EZproxy")
    print(f"Processing {len(urls):,} URLs in {mode_label} mode...", flush=True)

    results = [
        convert_line(u, plain_mode=args.plain, repair_mode=args.repair)
        for u in urls
    ]
    # Drop empty rows from blank lines
    results = [(s, c, st, n) for s, c, st, n in results if s]

    n_confirmed = sum(1 for _, _, st, _ in results if st == "confirmed")
    n_ok        = sum(1 for _, _, st, _ in results if st == "ok")
    n_warn      = sum(1 for _, _, st, _ in results if st == "warn")
    n_repair    = sum(1 for _, _, st, _ in results if st == "repaired")
    n_skip      = sum(1 for _, _, st, _ in results if st == "skip")
    n_total     = len(results)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source_url", "converted_url", "status", "notes"])
        for source, converted, status, notes in results:
            writer.writerow([source, converted, status, notes])

    def pct(n):
        return f"({n / n_total * 100:.1f}%)" if n_total else ""

    print(f"\nConversion report")
    print(f"-----------------")
    if n_confirmed:
        print(f"Confirmed entry point used  : {n_confirmed:>6,}  {pct(n_confirmed)}")
    print(f"Converted cleanly           : {n_ok:>6,}  {pct(n_ok)}")
    print(f"Converted with warnings     : {n_warn:>6,}  {pct(n_warn)}")
    if n_repair:
        print(f"Repaired                    : {n_repair:>6,}  {pct(n_repair)}")
    print(f"  Total converted           : {n_confirmed+n_ok+n_warn+n_repair:>6,}  "
          f"{pct(n_confirmed+n_ok+n_warn+n_repair)}")
    print(f"Not converted (skipped)     : {n_skip:>6,}  {pct(n_skip)}")
    print(f"  Total processed           : {n_total:>6,}")
    print(f"\nOutput written to: {output_path}")


if __name__ == "__main__":
    main()
