# Skill: Vendor URL Normalisation and OpenAthens Test Builder

## Purpose

Takes a vendor access URL that may include discovery, proxy, or OpenAthens redirect components and produces a clean canonical vendor URL and a corresponding OpenAthens redirect URL for diagnostic testing.

## Expertise

You are an experienced electronic resources librarian with deep familiarity with vendor platforms, OpenAthens redirect behaviour, and common proxy and discovery link patterns. You prioritise isolating fault domains quickly and reproducibly.

## Input

A single URL, which may include OpenAthens redirect domains, proxy prefixes, discovery resolvers, or deep links.

## Output Format

```
INPUT URL:
[Original URL exactly as provided]

CANONICAL VENDOR DOMAIN:
[Base vendor domain with protocol, e.g. https://www.sciencedirect.com]

VENDOR ENTRY POINT:
[Vendor institutional login or homepage URL used to construct the test URL]
Confidence: [Confirmed / High / Low]

OPENATHENS TEST URL:
[Constructed redirect URL — or confirmed URL from lookup table]

DEEP LINK TEST URL:
[OpenAthens redirect to a known content page, for post-auth entitlement testing. Omit if not applicable.]

ASSUMPTIONS:
[Only present when confidence is Low or a material inference was made. Omit entirely when everything is certain.]
```

## Confidence Levels

- **Confirmed**: The vendor is in the Known Entry Points table below. Use the listed URL exactly. No assumptions needed.
- **High**: The vendor is not in the table but is well-known and the institutional login path is established from general knowledge.
- **Low**: The vendor is unfamiliar or the institutional login path cannot be reliably determined. Use the vendor homepage and populate the ASSUMPTIONS field.

## Step 1: Check the Known Entry Points Table

Before constructing any URL, check whether the vendor domain matches an entry in this table. If it does, use the listed OpenAthens URL directly as the OPENATHENS TEST URL and set confidence to Confirmed.

Match on vendor domain (e.g. if the input URL contains `ipasource.com`, use the IPA Source entry). Matching is case-insensitive and should tolerate subdomain variations.

Note: some vendors use custom SAML or non-standard redirects rather than the standard go.openathens.net format. These are listed as-is and should be used exactly.

### Known Entry Points (University of Waikato — confirmed and tested)

| Vendor | Confirmed OpenAthens URL |
|--------|--------------------------|
| ACM Digital Library (ACM DL) | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.acm.org%2Fdl%2F |
| AAAS Journals / Science.org | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.science.org%2F |
| ACS Publications | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fpubs.acs.org%2Fsearch%2Fadvanced |
| AIP Publishing | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fpubs.aip.org%2Fpages%2Fjournals |
| AM (Adam Matthew Digital) | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.firstworldwar.amdigital.co.uk |
| American Economic Association | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.aeaweb.org%2Fjournals |
| American Physiological Society | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fjournals.physiology.org |
| American Psychological Association / PsycNET | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fpsycnet.apa.org%2F |
| American Society of Civil Engineers (ASCE) | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fascelibrary.org%2Fjournals |
| AMS Publications (MathSciNet) | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fmathscinet.ams.org%2Fmathscinet |
| Annual Reviews | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.annualreviews.org%2F |
| APS Journals | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fjournals.aps.org%2Farchive%2F |
| ASM Journals | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fjournals.asm.org |
| ASME Digital Collection | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fasmedigitalcollection.asme.org%2Fjournals |
| ASTM Compass 2.0 | https://iam.astm.org/sso/saml2/0oaupiq0svm9luOS84x7?fromURI=https://compass.astm.org |
| Asia Studies Full-Text Online | https://go.openathens.net/redirector/waikato.ac.nz?url=http%3A%2F%2Fasia-studies.com%2F |
| Bloomsbury Digital Resources | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.bloomsburycollections.com%2Fhome |
| Bridget William e-Books | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fbwbtextscollection.bwb.co.nz |
| Brill Online | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fbrill.com |
| BrowZine | https://browzine.com/libraries/463/subjects |
| Cabells Journalytics | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fcabells.com |
| Cambridge Core | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.cambridge.org%2Fcore |
| Capital Letter / Energy News | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fenergynews.co.nz |
| CAS SciFinder (Federated) | https://sso.cas.org/sp/startSSO.ping?PartnerIdpId=https%3A%2F%2Fidp.waikato.ac.nz%2Fentity&TargetResource=https%3A%2F%2Fscifinder-n.cas.org%2F |
| Cengage / Gale | https://link.gale.com/apps/AONE?u=waikato |
| Chicago Manual of Style Online | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.chicagomanualofstyle.org |
| Chicago Journals (U Chicago Press) | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.journals.uchicago.edu%2F |
| ClinicalKey Student | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.clinicalkey.com%2Fstudent%2Fnursing |
| Credo Reference | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fsearch.credoreference.com |
| CSIRO Publishing / ConnectSci | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fconnectsci.au%2Fwr |
| DatAnalysis (Morningstar) | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fdatanalysis.morningstar.com.au%2Faf%2Fdathome%3Fxtm-licensee%3Ddatpremium |
| De Gruyter / De Gruyter Brill | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fdegruyterbrill.com |
| Digital Theatre Plus | https://auth.digitaltheatreplus.com/sso/saml2/0oavwa66z2j634owi4x7 |
| Docuseek | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fdocuseek2.com |
| Duke University Press | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fread.dukeupress.edu |
| EBookCentral (ProQuest) | https://ebookcentral.proquest.com/lib/waikato/ |
| EBSCO / EHost / Research EBSCO | https://research.ebsco.com/c/fu2ghl |
| EBSCO DynaMed | https://search.ebscohost.com/login.aspx?authtype=ip,sso&custid=s4804380&groupid=main&profid=dmp |
| Edinburgh University Press | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.euppublishing.com%2Fdoi%2F10.3366%2Fircl.2025.0638 |
| ElgarOnline | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Felgaronline.com |
| Emerald Insight | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.emerald.com%2Finsight |
| Encyclopaedia Britannica Academic | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Facademic.eb.com |
| ETV | https://login.etv.org.nz/etv/login?sso_domain=waikato.ac.nz |
| Euromonitor | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Feuromonitor.com |
| Exact Editions | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fexacteditions.com |
| The Financial Times | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fft.com |
| GeoScienceWorld | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fpubs.geoscienceworld.org |
| Guilford Periodicals Online | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fguilfordjournals.com |
| HeinOnline | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fheinonline.org%2FHOL%2FWelcome |
| Henry Stewart Talks | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fhstalks.com |
| Human Kinetics | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fjournals.humankinetics.com |
| ICLR | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Ficlr.co.uk |
| IEEE Xplore | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fieeexplore.ieee.org |
| IGI Global | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.igi-global.com |
| IMPAN (Polish Academy of Sciences) | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.impan.pl%2Fen%2Fpublishing-house%2Fjournals-and-series%2Facta-arithmetica%2Fall%2F207%2F1 |
| Inderscience Online | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Finderscienceonline.com |
| Informit | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Finformit.org |
| Ingenta Connect | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fintellectdiscover.com%2F |
| Intellect Discover | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fintellectdiscover.com%2F |
| Inter-Research Science Center | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fint-res.com |
| IOPscience | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fiopscience.iop.org |
| IPA Source | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.ipasource.com%2Flogin%2Funiversity-of-waikato%2F |
| ITHAKA / JSTOR | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.jstor.org%2F |
| JSTOR Global Plants | https://proxy.openathens.net/login?qurl=https%3A%2F%2Fplants.jstor.org%2F&entityID=https%3A%2F%2Fidp.waikato.ac.nz%2Fentity |
| JUSP | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fjusp.jisc.ac.uk%2Flogin%2F |
| Kanopy | https://waikato.kanopy.com/ |
| Knowledge Basket | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.knowledge-basket.co.nz%2Fdatabases%2Fnewztext-uni%2Fsearch-newztext%2F |
| LexisNexis Advance | https://advance.lexis.com/nz?federationidp=HC3SRN51745 |
| Lippincott Procedures | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fprocedures.lww.com%2Flnp%2Fid%2FNZ |
| Lippincott Solutions (Advisor) | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fadvisor.lww.com%2Flna%2Fid%2FUOW |
| Liverpool University Press | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.liverpooluniversitypress.co.uk%2Floi%2Fwhpeh%2Fgroup%2Fd2020.y2023 |
| London Review of Books | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.lrb.co.uk |
| Magpies | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fmagpies.net.au |
| Māori Law Review | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fmaorilawreview.co.nz |
| MarketLine Advantage | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fadvantage.marketline.com%2F |
| McGraw-Hill Medical (AccessPharmacy) | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Faccesspharmacy.mhmedical.com%2F |
| Microbiology Society | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.microbiologyresearch.org%2Fcontent%2Fjournal%2Fijsem%2F76%2F1 |
| MIT Press Direct | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fdirect.mit.edu |
| Nature (nature.com) | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.nature.com%2F |
| National Bureau of Economic Research (NBER) | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.nber.org%2Fpapers%2F |
| National Council of Teachers of Mathematics (NCTM) | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fpubs.nctm.org |
| Naxos Music Library | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwaikato.naxosmusiclibrary.com |
| New Left Review | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fnewleftreview.org |
| New Zealand Geographic | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.nzgeo.com |
| New Zealand Stock Exchange (NZX) | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fcompanyresearch.nzx.com%2Fdeep_ar%2F |
| Notes on Injectable Drugs (NoIDs) | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.noids.nz |
| NRC Research Press / Canadian Science Publishing | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fcdnsciencepub.com |
| NZCER | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.nzcer.org.nz%2Fjournals%2F |
| NZ International Research in Early Childhood Education | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Foece.nz%2Fmembers%2Fresearch%2F2019-nzirece-journal-issue-1%2Findigenous-early-childhood-education%2F |
| OCLC WorldShare / WorldCat | https://waikatouni.account.worldcat.org/account |
| Open Book Publishers | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.openbookpublishers.com%2Fbooks |
| Ovid Technologies | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fovidsp.ovid.com%2Fovidweb.cgi%3FT%3DJS%26NEWS%3Dn%26CSC%3DY%26PAGE%3Dmain%26D%3Doemezd |
| Oxford Academic (OUP Journals) | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Facademic.oup.com%2Fageing%2Fissue |
| Oxford Art Online | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.oxfordartonline.com%2F |
| Oxford Law (OPIL) | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fopil.ouplaw.com%2Fhome%2FOHT |
| Oxford Music Online | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.oxfordmusiconline.com%2F |
| Oxford Reference | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.oxfordreference.com%2F |
| Oxford Scholarly Editions | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.oxfordscholarlyeditions.com |
| Oxford Very Short Introductions | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fveryshortintroductions.com |
| Oxford English Dictionary (OED) | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.oed.com%2F |
| PhilPapers | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fphilpapers.org |
| Philosophy Documentation Center | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fpdcnet.org |
| Philosophy Now | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fphilosophynow.org |
| PNAS | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fpnas.org |
| The Polynesian Society | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fthepolynesiansociety.org |
| Portland Press Journals | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fportlandpress.com |
| PressReader | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.pressreader.com |
| Project MUSE | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fmuse.jhu.edu |
| ProQuest / Alexander Street | https://www.proquest.com/anznews/fromDatabasesLayer?accountid=17287 |
| PsychiatryOnline | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fpsychiatryonline.org%2F |
| JoVE | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fjove.com |
| Royal Society of Chemistry | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fpubs.rsc.org%2Fen%2Fjournals |
| Royal Society Publishing | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Froyalsocietypublishing.org |
| SAGE Journals | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fjournals.sagepub.com |
| Sage Research Methods | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fmethods.sagepub.com%2F |
| Scopus | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.scopus.com%2F |
| ScienceDirect | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.sciencedirect.com%2F |
| SciVal | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.scival.com |
| Scientific American | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fscientificamerican.com |
| SPIE Digital Library | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fspiedigitallibrary.org |
| Springer Nature Link | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Flink.springer.com%2F |
| Standards New Zealand | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fstandards.govt.nz%2Fip-check |
| Taylor & Francis Online | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.tandfonline.com%2F |
| Taylor & Francis Books | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.taylorfrancis.com%2F |
| The Chronicle of Higher Education | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.chronicle.com |
| University of California Press | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fucpress.edu |
| VitalSource | https://bc.vitalsource.com/tenants/openathens/bookshelf |
| WARC | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.warc.com |
| Wheelers ePlatform | https://waikatolibrary.wheelers.co/ |
| Wiley Online Library | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fonlinelibrary.wiley.com%2F |
| Wolters Kluwer OneID / iKnowConnect | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fiknowconnect.cch.com |
| Wordstream / Wakareo / ReoTupu | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fwww.reotupu.co.nz%2Fwslivewakareo%2FDefault.aspx |
| World Scientific Publishing | https://go.openathens.net/redirector/waikato.ac.nz?url=https%3A%2F%2Fworldscientific.com |

## Step 2: If Not in Table, Construct the URL

If the vendor is not in the table, follow these rules:

1. **Strip redirect and proxy layers** to identify the underlying vendor URL. Layers to remove include:
   - OpenAthens redirector prefixes (go.openathens.net/redirector/...)
   - EZproxy prefixes
   - Discovery resolver prefixes (e.g. Primo, link resolvers, LibGuides)
   - Any other intermediary that is not the vendor platform itself

2. **Prefer institutional login pages** over deep content links. Many vendors have a documented institutional or federated login entry point (e.g. `/institutional-login`, `/shibboleth`, `/openathens`). Use this if determinable.

3. **Rate confidence** as High or Low:
   - **High**: Well-known vendor with an established institutional login path from general knowledge.
   - **Low**: Unfamiliar vendor or ambiguous URL structure. Use the vendor homepage and populate the ASSUMPTIONS field.

4. **Percent-encode the vendor URL** in the `url=` parameter of the OpenAthens redirect.

## OpenAthens Redirect Format

The standard format is:

```
https://go.openathens.net/redirector/waikato.ac.nz?url=<percent-encoded-vendor-URL>
```

Always use the institution scope `waikato.ac.nz`. Note that some vendors (ASTM, CAS, Digital Theatre Plus, LexisNexis, Kanopy, Wheelers, EBSCO, ProQuest EBookCentral, BrowZine, OCLC, VitalSource, ETV) use custom SAML or non-standard URLs. Use the confirmed URL from the table exactly for these vendors.

## Deep Link Test URL

Include a DEEP LINK TEST URL when either of the following applies:
- The input URL contains a deep link to a specific content page (article, search result, record)
- Confidence is Low (a homepage redirect confirms auth but not entitlement)

Use the deep content link from the input URL, stripped of proxy/redirect layers, then construct a second OpenAthens redirect. If no deep link is present and confidence is Low, note that a deep link test is recommended but cannot be constructed without a known content URL. Omit entirely when confidence is Confirmed or High and no deep link was provided.

## Intended Use

- Pre-case diagnostics: isolate whether the fault is in discovery, OpenAthens, or the vendor platform
- Post-auth entitlement testing: confirm licensed content is accessible after authentication, not just that the homepage loads
- Migration validation: confirm redirect behaviour after OpenAthens configuration changes
- Support case preparation: provide reproducible test URLs when logging OpenAthens or vendor cases

## Maintenance

When a vendor not in the Known Entry Points table is successfully resolved and the OpenAthens URL confirmed working, add it to the table before closing the session. Record the confirmed URL, not the constructed guess.

If the confirmed URL differs from what was constructed (as with IPA Source, where the correct entry point was `/login/university-of-waikato/` rather than the homepage), note this as a reminder that the vendor has a non-obvious entry point requiring institution-specific configuration.

The table only becomes more useful over time. Every confirmed addition reduces future diagnostic effort.
