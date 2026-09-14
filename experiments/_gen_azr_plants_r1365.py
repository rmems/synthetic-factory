#!/usr/bin/env python3
"""Emit experiments/azr-plants-r1365.py — unique IDOR/BFLA for r1365+."""
from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).with_name("azr-plants-r1365.py")

PLANTS = [
    "abeam", "adrift", "aground", "alee", "aloft", "amidships", "apeak", "athwart",
    "awash", "ballast", "barnacle", "barque", "becket", "bilge", "bitthead",
    "boomvang", "bowse", "brigantine", "bulkhead", "bulwark", "camcleat", "carline",
    "catboat", "chock", "coaming", "coir", "counter", "cutwater", "deadeye",
    "deadwood", "dodger", "draught", "dutchman", "fishplate", "flotsam", "focsle",
    "forepeak", "galley", "gennaker", "girtline", "grabrail", "gripe", "gudgeon",
    "gunport", "gybe", "hance", "hatchcoam", "headstay", "helmstock", "hogframe",
    "jackline", "jibsheet", "kingplank", "knighthead", "lateen", "leeward",
    "limberhole", "logline", "mainsheet", "masthead", "oarlock", "partnerbeam",
    "pintle", "poopdeck", "portlight", "quarterbeam", "ridingbitt", "rudderhead",
    "runningback", "scupper", "sheetbend", "spinnaker", "stemson", "sternpost",
    "timberhead", "waterway", "weathercloth", "windward", "yawlboat", "yokeplate",
]

FIRST = ["authn", "mask", "any_member", "list_scope"]
RESIDUAL = ["pdf", "export", "search", "mget", "csv", "admin", "webhook", "comments"]
LEFTOVER = ["put", "patch", "update"]

# slug, surface, mod, model, lookup, sample, owner, product, bug
IDOR = [
    ("mgrs-grid-idor", "MGRS grid square object-id IDOR", "mgrs", "Mgrs", "mgrs", "18TWL850000", "map_id", "mgrs-nga", "MGRS unique from NGA grid"),
    ("maidenhead-grid-idor", "Maidenhead locator object-id IDOR", "maidenheads", "Maidenhead", "locator", "FN20xr", "club_id", "maidenhead-iaru", "Maidenhead unique from IARU"),
    ("unlocode-port-idor", "UN/LOCODE port object-id IDOR", "unlocodes", "Unlocode", "locode", "USNYC", "network_id", "unlocode-unece", "LOCODE unique from UNECE"),
    ("iata-airport-idor", "IATA airport code object-id IDOR", "iataapts", "IataApt", "iata", "JFK", "network_id", "iata-apt", "IATA unique from location table"),
    ("icao-airline-idor", "ICAO airline designator object-id IDOR", "airlines", "Airline", "icaoal", "UAL", "alliance_id", "icao-al", "ICAO airline unique from Doc 8585"),
    ("imo-ship-idor", "IMO ship number object-id IDOR", "imoships", "ImoShip", "imo", "IMO9074729", "fleet_id", "imo-gis", "IMO unique from GISIS"),
    ("eni-inland-idor", "ENI inland craft object-id IDOR", "enis", "Eni", "eni", "04012345", "fleet_id", "eni-cesni", "ENI unique from CESNI"),
    ("isrc-track-idor", "ISRC recording object-id IDOR", "isrcs", "Isrc", "isrc", "USRC17607839", "label_id", "isrc-ifpi", "ISRC unique from IFPI"),
    ("iswc-work-idor", "ISWC musical work object-id IDOR", "iswcs", "Iswc", "iswc", "T-034.524.680-1", "society_id", "iswc-cisac", "ISWC unique from CISAC"),
    ("isni-party-idor", "ISNI party object-id IDOR", "isnis", "Isni", "isni", "0000000121032683", "registry_id", "isni-iso", "ISNI unique from ISO 27729"),
    ("lccn-record-idor", "LCCN bibliographic object-id IDOR", "lccns", "Lccn", "lccn", "n79021164", "library_id", "lccn-loc", "LCCN unique from LoC"),
    ("oclc-number-idor", "OCLC number object-id IDOR", "oclcs", "Oclc", "oclc", "ocm00012345", "library_id", "oclc-worldcat", "OCLC unique from WorldCat"),
    ("dblp-pid-idor", "DBLP person object-id IDOR", "dblps", "Dblp", "pid", "homepages/h/BjarneStroustrup", "campus_id", "dblp-pid", "DBLP pid unique from Trier"),
    ("upc-a-sku-idor", "UPC-A SKU object-id IDOR", "upcs", "Upc", "upc", "036000291452", "catalog_id", "upc-gs1", "UPC unique from GS1 US"),
    ("jan-barcode-idor", "JAN barcode object-id IDOR", "jans", "Jan", "jan", "4901234567894", "catalog_id", "jan-dsri", "JAN unique from DSRI"),
    ("giai-asset-idor", "GS1 GIAI asset object-id IDOR", "giais", "Giai", "giai", "06141411234567890", "depot_id", "giai-gs1", "GIAI unique from asset registry"),
    ("cvx-vaccine-idor", "CVX vaccine object-id IDOR", "cvxs", "Cvx", "cvx", "141", "clinic_id", "cvx-cdc", "CVX unique from CDC IIS"),
    ("umls-cui-idor", "UMLS CUI object-id IDOR", "umls", "Umls", "cui", "C0011849", "clinic_id", "umls-nlm", "CUI unique from UMLS Metathesaurus"),
    ("meddra-pt-idor", "MedDRA PT object-id IDOR", "meddras", "Meddra", "ptcode", "10067569", "sponsor_id", "meddra-mss", "PT unique from MSSO"),
    ("icpc2-code-idor", "ICPC-2 encounter object-id IDOR", "icpcs", "Icpc", "icpc", "T90", "clinic_id", "icpc-wonca", "ICPC unique from WONCA"),
    ("ucum-unit-idor", "UCUM unit object-id IDOR", "ucums", "Ucum", "ucum", "mmol/L", "lab_id", "ucum-regenstrief", "UCUM unique from Regenstrief"),
    ("gnomad-vid-idor", "gnomAD variant object-id IDOR", "gnomads", "Gnomad", "vid", "1-55516888-G-GA", "lab_id", "gnomad-broad", "VID unique from gnomAD"),
    ("civic-eid-idor", "CIViC evidence object-id IDOR", "civics", "Civic", "eid", "EID:1998", "lab_id", "civic-wustl", "EID unique from CIViC"),
    ("oncotree-code-idor", "OncoTree code object-id IDOR", "oncotrees", "Oncotree", "oncotree", "LUAD", "lab_id", "oncotree-msk", "OncoTree unique from MSK"),
    ("doid-disease-idor", "Disease Ontology object-id IDOR", "doids", "Doid", "doid", "DOID:9351", "clinic_id", "doid-obo", "DOID unique from OBO"),
    ("efo-term-idor", "EFO trait object-id IDOR", "efos", "Efo", "efo", "EFO:0000400", "lab_id", "efo-ebi", "EFO unique from EMBL-EBI"),
    ("cl-cell-idor", "Cell Ontology object-id IDOR", "clcells", "Clcell", "clid", "CL:0000236", "lab_id", "cl-obo", "CL unique from Cell Ontology"),
    ("cellosaurus-cvcl-idor", "Cellosaurus CVCL object-id IDOR", "cvcls", "Cvcl", "cvcl", "CVCL_0030", "lab_id", "cellosaurus-sib", "CVCL unique from SIB"),
    ("rrid-resource-idor", "RRID resource object-id IDOR", "rrids", "Rrid", "rrid", "RRID:AB_217931", "lab_id", "rrid-scicrunch", "RRID unique from SciCrunch"),
    ("addgene-plasmid-idor", "Addgene plasmid object-id IDOR", "plasmids", "Plasmid", "addgene", "52920", "lab_id", "addgene-plasmid", "Addgene unique from catalog"),
    ("jax-strain-idor", "JAX strain object-id IDOR", "jaxs", "Jax", "jax", "000664", "lab_id", "jax-strain", "JAX unique from Mouse Genome"),
    ("flybase-fbid-idor", "FlyBase gene object-id IDOR", "flybases", "Flybase", "fbid", "FBgn0000490", "lab_id", "flybase-fbid", "FBid unique from FlyBase"),
    ("wormbase-wbid-idor", "WormBase gene object-id IDOR", "wormbases", "Wormbase", "wbid", "WBGene00000898", "lab_id", "wormbase-wbid", "WBID unique from WormBase"),
    ("sgd-orf-idor", "SGD ORF object-id IDOR", "sgds", "Sgd", "sgd", "S000000001", "lab_id", "sgd-orf", "SGD unique from yeast genome"),
    ("zfin-id-idor", "ZFIN gene object-id IDOR", "zfins", "Zfin", "zfin", "ZDB-GENE-980526-166", "lab_id", "zfin-id", "ZFIN unique from zebrafish"),
    ("mgi-marker-idor", "MGI marker object-id IDOR", "mgis", "Mgi", "mgi", "MGI:96677", "lab_id", "mgi-marker", "MGI unique from Jackson"),
    ("rgd-gene-idor", "RGD gene object-id IDOR", "rgds", "Rgd", "rgd", "RGD:620268", "lab_id", "rgd-gene", "RGD unique from rat genome"),
    ("drugbank-id-idor", "DrugBank compound object-id IDOR", "drugbanks", "Drugbank", "drugbank", "DB00945", "lab_id", "drugbank-id", "DrugBank unique from Wishart"),
    ("zinc15-id-idor", "ZINC15 molecule object-id IDOR", "zincs", "Zinc", "zinc", "ZINC000000000016", "lab_id", "zinc15-id", "ZINC unique from Irwin"),
    ("lipidmaps-idor", "LIPID MAPS object-id IDOR", "lipidmaps", "Lipidmap", "lm", "LMFA01010001", "lab_id", "lipidmaps-id", "LM unique from LIPID MAPS"),
    ("emdb-map-idor", "EMDB map object-id IDOR", "emdbs", "Emdb", "emdb", "EMD-0001", "lab_id", "emdb-map", "EMDB unique from EBI"),
    ("bmrb-entry-idor", "BMRB entry object-id IDOR", "bmrbs", "Bmrb", "bmrb", "bmr15000", "lab_id", "bmrb-entry", "BMRB unique from NMR"),
    ("afdb-model-idor", "AlphaFold DB model object-id IDOR", "afdbs", "Afdb", "afdb", "AF-P04637-F1", "lab_id", "afdb-model", "AFDB unique from EBI"),
    ("wikipathways-idor", "WikiPathways object-id IDOR", "wikipathways", "Wikipathway", "wpid", "WP554", "lab_id", "wikipathways-id", "WP unique from WikiPathways"),
    ("biogrid-int-idor", "BioGRID interaction object-id IDOR", "biogrids", "Biogrid", "biogrid", "113409", "lab_id", "biogrid-int", "BioGRID unique from interaction"),
    ("intact-ebi-idor", "IntAct interaction object-id IDOR", "intacts", "Intact", "intact", "EBI-464353", "lab_id", "intact-ebi", "IntAct unique from EBI"),
    ("string-protein-idor", "STRING protein object-id IDOR", "strings", "Stringp", "stringid", "9606.ENSP00000269305", "lab_id", "string-protein", "STRING unique from ELIXIR"),
    ("brenda-ligand-idor", "BRENDA ligand object-id IDOR", "brendas", "Brenda", "brenda", "CHEBI:15377", "lab_id", "brenda-ligand", "BRENDA unique from enzyme"),
    ("panther-family-idor", "PANTHER family object-id IDOR", "panthers", "Panther", "pthr", "PTHR23086", "lab_id", "panther-family", "PTHR unique from PANTHER"),
    ("prosite-ps-idor", "PROSITE pattern object-id IDOR", "prosites", "Prosite", "ps", "PS00107", "lab_id", "prosite-ps", "PS unique from SIB"),
    ("smart-domain-idor", "SMART domain object-id IDOR", "smarts", "Smart", "smart", "SM00220", "lab_id", "smart-domain", "SMART unique from EMBL"),
    ("cdd-domain-idor", "CDD domain object-id IDOR", "cdds", "Cdd", "cdd", "cd00180", "lab_id", "cdd-domain", "CDD unique from NCBI"),
    ("ncit-code-idor", "NCI Thesaurus object-id IDOR", "ncits", "Ncit", "ncit", "C4872", "clinic_id", "ncit-code", "NCIt unique from NCI"),
    ("icdo3-morph-idor", "ICD-O-3 morphology object-id IDOR", "icdos", "Icdo", "icdo", "8140/3", "clinic_id", "icdo3-morph", "ICD-O unique from IARC"),
    ("dsm5-code-idor", "DSM-5 disorder object-id IDOR", "dsm5s", "Dsm5", "dsm5", "F32.1", "clinic_id", "dsm5-code", "DSM-5 unique from APA"),
    ("naics-code-idor", "NAICS industry object-id IDOR", "naics", "Naics", "naics", "541511", "firm_id", "naics-census", "NAICS unique from Census"),
    ("sic-code-idor", "SIC industry object-id IDOR", "sics", "Sic", "sic", "7372", "firm_id", "sic-osha", "SIC unique from OSHA"),
    ("isic-code-idor", "ISIC industry object-id IDOR", "isics", "Isic", "isic", "J62", "firm_id", "isic-unsd", "ISIC unique from UNSD"),
    ("nace-code-idor", "NACE industry object-id IDOR", "naces", "Nace", "nace", "62.01", "firm_id", "nace-eurostat", "NACE unique from Eurostat"),
    ("cpc-patent-idor", "CPC patent class object-id IDOR", "cpcs", "Cpc", "cpc", "G06F21/31", "firm_id", "cpc-patent", "CPC unique from USPTO/EPO"),
    ("ipc-patent-idor", "IPC patent class object-id IDOR", "ipcs", "Ipc", "ipc", "G06F21/00", "firm_id", "ipc-wipo", "IPC unique from WIPO"),
    ("uspto-app-idor", "USPTO application object-id IDOR", "usptos", "Uspto", "appno", "16/123456", "firm_id", "uspto-app", "appno unique from PAIR"),
    ("epo-publ-idor", "EPO publication object-id IDOR", "epos", "Epo", "epodoc", "EP1234567A1", "firm_id", "epo-publ", "EPODOC unique from Espacenet"),
    ("wipo-pct-idor", "PCT application object-id IDOR", "pcts", "Pct", "pct", "PCT/US2024/012345", "firm_id", "wipo-pct", "PCT unique from Patentscope"),
    ("trademark-serial-idor", "USPTO trademark serial object-id IDOR", "tmarks", "Tmark", "serial", "88812345", "firm_id", "tm-serial", "serial unique from TESS"),
    ("ark-identifier-idor", "ARK identifier object-id IDOR", "arks", "Ark", "ark", "ark:/13030/tf5p30086k", "library_id", "ark-id", "ARK unique from NAAN"),
    ("purl-record-idor", "PURL record object-id IDOR", "purls", "Purl", "purl", "https://purl.org/dc/terms/title", "library_id", "purl-oclc", "PURL unique from OCLC"),
    ("urn-nbn-idor", "URN:NBN national bib object-id IDOR", "nbns", "Nbn", "nbn", "urn:nbn:de:bvb:12-bsb00000000-0", "library_id", "urn-nbn", "NBN unique from DNB"),
    ("sici-serial-idor", "SICI serial item object-id IDOR", "sicis", "Sici", "sici", "0095-4403(199502/03)21:3<12:WATIIB>2.0.TX;2-J", "library_id", "sici-niso", "SICI unique from NISO"),
    ("coden-serial-idor", "CODEN serial object-id IDOR", "codens", "Coden", "coden", "NATUAS", "library_id", "coden-cas", "CODEN unique from CASSI"),
    ("lcc-class-idor", "LCC class object-id IDOR", "lccs", "Lcc", "lcc", "QA76.9.A25", "library_id", "lcc-class", "LCC unique from LoC schedules"),
    ("ddc-class-idor", "DDC class object-id IDOR", "ddcs", "Ddc", "ddc", "005.8", "library_id", "ddc-class", "DDC unique from OCLC Dewey"),
    ("mesh-qualifier-idor", "MeSH qualifier object-id IDOR", "meshqs", "Meshq", "meshq", "Q000188", "campus_id", "mesh-qual", "MeSH qualifier unique from NLM"),
    ("icd10pcs-proc-idor", "ICD-10-PCS procedure object-id IDOR", "pcs", "Pcs", "pcs", "0SRC0J9", "clinic_id", "icd10-pcs", "PCS unique from CMS"),
    ("loinc-answer-idor", "LOINC answer list object-id IDOR", "loincans", "Loincans", "ll", "LL715-4", "clinic_id", "loinc-ans", "LL unique from Regenstrief"),
    ("rxnorm-in-idor", "RxNorm ingredient object-id IDOR", "rxins", "Rxin", "rxin", "161", "pharmacy_id", "rxnorm-in", "IN unique from RxNorm TTY"),
    ("atcvet-code-idor", "ATCvet code object-id IDOR", "atcvets", "Atcvet", "atcvet", "QJ01CA04", "clinic_id", "atcvet-who", "ATCvet unique from WHO"),
    ("icd11-mms-ext-idor", "ICD-11 MMS extension object-id IDOR", "icd11xs", "Icd11x", "icd11x", "XT3S", "clinic_id", "icd11-ext", "ICD-11 extension unique from WHO"),
    ("hgnc-alias-idor", "HGNC alias symbol object-id IDOR", "hgncalias", "Hgncalias", "alias", "p53", "lab_id", "hgnc-alias", "alias unique from HGNC"),
    ("refseq-nm-idor", "RefSeq NM transcript object-id IDOR", "nms", "Nm", "nm", "NM_000546.6", "lab_id", "refseq-nm", "NM unique from NCBI"),
]

assert len(IDOR) == 80
assert len(PLANTS) == 80
assert len({x[0] for x in IDOR}) == 80
assert len({x[2] for x in IDOR}) == 80
assert len({x[4] for x in IDOR}) == 80

# slug, surface, family, skip, auth  (leftover cycled)
BFLA = [
    ("loopback-remote-skip-delete", "LoopBack remoteMethod skip ACL on delete", "js_route",
     "Note.delete = {acl: [], http: {verb: 'del', path: '/:id'}}",
     "Note.findById = {acls: [{permission: 'ALLOW', principalType: 'ROLE', principalId: '$authenticated'}]}"),
    ("feathers-hook-skip-delete", "Feathers remove hook missing authenticate", "js_route",
     "app.service('notes').hooks({ before: { remove: [] } })",
     "app.service('notes').hooks({ before: { find: [authenticate('jwt')] } })"),
    ("moleculer-alias-skip-delete", "Moleculer alias DELETE missing auth", "js_route",
     "remove: { auth: false, rest: 'DELETE /notes/:id' }",
     "get: { auth: 'required', rest: 'GET /notes/:id' }"),
    ("meteor-method-unauthed-delete", "Meteor method delete missing this.userId", "js_route",
     "Meteor.methods({ 'notes.remove'(id) { Notes.remove(id) } })",
     "Meteor.publish('notes', function () { if (!this.userId) return []; return Notes.find({owner: this.userId}) })"),
    ("ember-adapter-skip-delete", "Ember Data adapter deleteRecord skips adapter auth", "js_route",
     "deleteRecord(store, type, snapshot) { return fetch(`/notes/${snapshot.id}`, {method:'DELETE'}) }",
     "findRecord(store, type, id) { return this.ajax(`/notes/${id}`, 'GET', {headers: this.headers}) }"),
    ("redwood-sdl-skip-delete", "Redwood SDL deleteNote missing @requireAuth", "js_route",
     "deleteNote(id: Int!): Note! @skipAuth",
     "note(id: Int!): Note @requireAuth"),
    ("blitz-resolver-skip-delete", "Blitz resolver delete missing authorize", "js_route",
     "export default resolver.pipe(async ({id}) => db.note.delete({where:{id}}))",
     "export default resolver.pipe(resolver.authorize(), async ({id}) => db.note.findFirst({where:{id}}))"),
    ("trpc-procedure-public-delete", "tRPC publicProcedure leftover on delete", "js_route",
     "delete: publicProcedure.input(z.number()).mutation(({input}) => db.note.delete({where:{id:input}}))",
     "get: protectedProcedure.input(z.number()).query(({input, ctx}) => db.note.findFirst({where:{id:input, ownerId: ctx.user.id}}))"),
    ("postgraphile-delete-grant", "PostGraphile GRANT DELETE leftover", "sql",
     "GRANT DELETE ON notes TO graphile_anon;",
     "GRANT SELECT ON notes TO graphile_user;"),
    ("graphql-yoga-plugin-skip", "GraphQL Yoga useGenericAuth skip on delete", "js_route",
     "deleteNote: (_e, {id}) => notes.del(id)",
     "note: (_e, {id}, ctx) => { if (!ctx.user) throw new Error('unauth'); return notes.get(id, ctx.user) }"),
    ("apollo-plugin-skip-delete", "Apollo Server field delete missing auth directive", "js_route",
     "type Mutation { deleteNote(id: ID!): Boolean }",
     "type Query { note(id: ID!): Note @auth }"),
    ("mercurius-preHandler-skip", "Mercurius preHandler skip leftover on delete", "js_route",
     "app.graphql.defineMutation('deleteNote', { preHandler: [] }, (_, {id}) => notes.del(id))",
     "app.graphql.defineQuery('note', { preHandler: [auth] }, (_, {id}, ctx) => notes.get(id, ctx.user))"),
    ("foal-hook-skip-delete", "FoalTS @Delete missing @UseGuard", "js_route",
     "@Delete('/:id')\nasync delete(ctx: Context) { await Note.delete(ctx.request.params.id) }",
     "@Get('/:id')\n@UseGuard(AuthGuard)\nasync get(ctx: Context) { return Note.get(ctx.request.params.id, ctx.user) }"),
    ("tsed-useauth-skip-delete", "Ts.ED delete missing @UseAuth", "js_route",
     "@Delete('/:id')\ndelete(@PathParams('id') id: string) { return Note.delete(id) }",
     "@Get('/:id')\n@UseAuth(AuthMiddleware)\nget(@PathParams('id') id: string, @User() u: User) { return Note.get(id, u) }"),
    ("routing-controllers-skip", "routing-controllers delete missing @Authorized", "js_route",
     "@Delete('/notes/:id')\ndelete(@Param('id') id: string) { return Note.delete(id) }",
     "@Get('/notes/:id')\n@Authorized()\nget(@Param('id') id: string, @CurrentUser() u: User) { return Note.get(id, u) }"),
    ("analog-endpoint-public-delete", "Analog endpoint DELETE missing auth", "js_route",
     "export const DELETE = defineEventHandler((e) => notes.del(getRouterParam(e, 'id')))",
     "export const GET = defineEventHandler(async (e) => { const u = await requireUser(e); return notes.get(getRouterParam(e, 'id'), u) })"),
    ("bun-serve-delete-bare", "Bun.serve DELETE missing auth", "js_route",
     "if (req.method === 'DELETE') return notes.del(new URL(req.url).pathname)",
     "if (req.method === 'GET') { const u = auth(req); return notes.get(path, u) }"),
    ("deno-serve-delete-bare", "Deno.serve DELETE missing auth", "js_route",
     "if (req.method === 'DELETE') return notes.del(url.pathname)",
     "if (req.method === 'GET') { const u = await auth(req); return notes.get(url.pathname, u) }"),
    ("oak-delete-no-mw", "Oak delete outside auth middleware", "js_route",
     "router.delete('/notes/:id', (ctx) => notes.del(ctx.params.id))",
     "router.use(auth); router.get('/notes/:id', (ctx) => notes.get(ctx.params.id, ctx.state.user))"),
    ("aleph-handler-public-delete", "Aleph DELETE handler missing auth", "js_route",
     "export function DELETE(req: Request, ctx: Context) { return notes.del(ctx.params.id) }",
     "export async function GET(req: Request, ctx: Context) { const u = await requireUser(req); return notes.get(ctx.params.id, u) }"),
    ("cloudflare-worker-delete-open", "Cloudflare Worker DELETE missing auth", "js_route",
     "if (request.method === 'DELETE') return notes.del(id)",
     "if (request.method === 'GET') { const u = await env.AUTH.verify(request); return notes.get(id, u) }"),
    ("azure-func-anon-delete", "Azure Function DELETE AuthorizationLevel.Anonymous leftover", "js_route",
     "[Function('DeleteNote')] HttpResponseData Run([HttpTrigger(AuthorizationLevel.Anonymous, 'delete')]",
     "[Function('GetNote')] HttpResponseData Run([HttpTrigger(AuthorizationLevel.Function, 'get')]"),
    ("firebase-fn-no-auth-delete", "Firebase Function delete missing context.auth", "js_route",
     "exports.deleteNote = functions.https.onRequest((req, res) => notes.del(req.query.id))",
     "exports.getNote = functions.https.onCall((data, ctx) => { if (!ctx.auth) throw new functions.https.HttpsError('unauthenticated','x'); return notes.get(data.id, ctx.auth.uid) })"),
    ("appwrite-function-open-delete", "Appwrite function delete missing JWT", "js_route",
     "export default async ({ req }) => notes.del(req.query.id)",
     "export default async ({ req }) => { const u = req.headers['x-appwrite-user-id']; return notes.get(req.query.id, u) }"),
    ("pocketbase-hook-skip-delete", "PocketBase OnRecordDelete skip auth", "js_route",
     "onRecordDelete((e) => { e.next() })",
     "onRecordViewRequest((e) => { if (!e.httpContext.auth) throw new ForbiddenError() })"),
    ("parse-clp-public-delete", "Parse CLP public delete leftover", "js_route",
     "Note._defaultACL.setPublicWriteAccess(true)",
     "Note._defaultACL.setReadAccess(user, true)"),
    ("ghost-content-delete-open", "Ghost Content API delete missing staff token", "js_route",
     "router.delete('/notes/:id', api.notes.destroy)",
     "router.get('/notes/:id', mw.authenticateStaff, api.notes.read)"),
    ("wordpress-rest-delete-cap", "WordPress REST delete missing capability", "php_mw",
     "register_rest_route('notes/v1', '/(?P<id>[\\d]+)', ['methods'=>'DELETE','callback'=>'notes_delete','permission_callback'=>'__return_true'])",
     "register_rest_route('notes/v1', '/(?P<id>[\\d]+)', ['methods'=>'GET','permission_callback'=>'is_user_logged_in'])"),
    ("drupal-rest-delete-anon", "Drupal REST delete anon leftover", "php_mw",
     "$config['notes.delete']['auth'] = ['cookie' => 'anon'];",
     "$config['notes.GET']['auth'] = ['cookie' => 'user'];"),
    ("joomla-api-delete-public", "Joomla Web Services delete public leftover", "php_mw",
     "<webservice><operation name=\"delete\" public=\"true\"/></webservice>",
     "<webservice><operation name=\"get\" public=\"false\"/></webservice>"),
    ("magento-webapi-acl-skip", "Magento webapi ACL skip leftover on delete", "php_mw",
     "<route url=\"/V1/notes/:id\" method=\"DELETE\"><service class=\"NoteRepository\" method=\"delete\"/><resources><resource ref=\"anonymous\"/></resources></route>",
     "<route url=\"/V1/notes/:id\" method=\"GET\"><resources><resource ref=\"self\"/></resources></route>"),
    ("prestashop-ws-delete-open", "PrestaShop WS delete missing authentication key scope", "php_mw",
     "$this->url['delete'] = ['url' => '/notes/{id}', 'auth' => false];",
     "$this->url['get'] = ['url' => '/notes/{id}', 'auth' => true];"),
    ("opencart-api-delete-bare", "OpenCart API delete missing api_token", "php_mw",
     "public function delete() { $this->model_note->delete($this->request->get['id']); }",
     "public function get() { $this->checkApiToken(); return $this->model_note->get($this->request->get['id']); }"),
    ("shopware-acl-skip-delete", "Shopware ACL skip leftover on delete", "php_mw",
     "#[Route(path: '/api/note/{id}', methods: ['DELETE'], defaults: ['_acl' => ['note:delete']])]",
     "#[Route(path: '/api/note/{id}', methods: ['GET'], defaults: ['_acl' => ['note:read'], '_auth' => true])]"),
    ("saleor-permission-skip", "Saleor GraphQL delete missing permission", "js_route",
     "class DeleteNote(BaseMutation):\n    permissions = []",
     "class Note(ModelObjectType):\n        permissions = [NotePermissions.MANAGE_NOTES]"),
    ("medusa-auth-skip-delete", "Medusa delete missing authenticate middleware", "js_route",
     "router.delete('/admin/notes/:id', (req, res) => noteService.delete(req.params.id))",
     "router.get('/admin/notes/:id', authenticate(), (req, res) => noteService.retrieve(req.params.id, req.user))"),
    ("spree-cancan-skip-delete", "Spree CanCan skip authorize! on destroy", "rb_filter",
     "def destroy; @note.destroy; end",
     "def show; authorize! :read, @note; end"),
    ("solidus-ability-skip-delete", "Solidus Ability skip leftover on destroy", "rb_filter",
     "can :destroy, Spree::Note",
     "can :read, Spree::Note, user_id: user.id"),
    ("sylius-voter-skip-delete", "Sylius voter skip leftover on delete", "php_mw",
     "#[Route('/notes/{id}', methods: ['DELETE'])]\npublic function delete(int $id): Response",
     "#[IsGranted('NOTE_VIEW')]\n#[Route('/notes/{id}', methods: ['GET'])]\npublic function show(int $id): Response"),
    ("vendure-guard-skip-delete", "Vendure resolver delete missing @Allow", "js_route",
     "@Mutation() async deleteNote(id: ID) { return this.noteService.delete(id) }",
     "@Query() @Allow(Permission.Authenticated) async note(id: ID, ctx: RequestContext) { return this.noteService.find(id, ctx) }"),
    ("umbraco-auth-skip-delete", "Umbraco API delete missing [Authorize]", "cs_attr",
     "[HttpDelete(\"{id}\")] public IActionResult Delete(int id) { _notes.Delete(id); return NoContent(); }",
     "[Authorize] [HttpGet(\"{id}\")] public IActionResult Get(int id) => Ok(_notes.Get(id, User));"),
    ("sitecore-authz-skip-delete", "Sitecore Services Client delete missing Authorize", "cs_attr",
     "[HttpDelete] public void Delete(string id) { repository.Delete(id); }",
     "[Authorize] [HttpGet] public Item Get(string id) => repository.Get(id, User);"),
    ("kentico-perm-skip-delete", "Kentico Xperience delete missing permission", "cs_attr",
     "public void Delete(int id) { noteInfoProvider.Delete(id); }",
     "[Authorize] public NoteInfo Get(int id) => noteInfoProvider.Get(id, User);"),
    ("optimizely-auth-skip-delete", "Optimizely CMS delete missing AuthorizeContent", "cs_attr",
     "[HttpDelete] public ActionResult Delete(int id) { _repo.Delete(id); return NoContent(); }",
     "[AuthorizeContent] [HttpGet] public ActionResult Get(int id) => Ok(_repo.Get(id));"),
    ("contentful-mgmt-skip-delete", "Contentful CMA delete missing space token scope", "js_route",
     "client.entry.delete({entryId})",
     "client.entry.get({entryId, headers: {Authorization}})"),
    ("sanity-groq-skip-delete", "Sanity listener delete missing token ACL", "js_route",
     "client.delete(id)",
     "client.fetch('*[_id==$id && _acl match $user]', {id, user})"),
    ("forest-smart-skip-delete", "Forest Admin smart action delete missing permission", "js_route",
     "collection('notes', { actions: [{ name: 'delete', endpoint: '/forest/notes/delete' }] })",
     "collection('notes', { fields: [{ field: 'id', isReadOnly: true }], segments: ['own'] })"),
    ("revel-filter-skip-delete", "Revel filter skip leftover on Delete", "go_mw",
     "func (c Notes) Delete(id int) revel.Result { c.Txn.Delete(&Note{Id: id}); return c.NoContent() }",
     "func (c Notes) Show(id int) revel.Result { c.CheckAuth(); return c.RenderJSON(c.Txn.Get(id, c.User)) }"),
    ("buffalo-mw-skip-delete", "Buffalo DELETE outside authorization middleware", "go_mw",
     "app.DELETE(\"/notes/{id}\", notes.Destroy)",
     "app.Use(Authorization); app.GET(\"/notes/{id}\", notes.Show)"),
    ("martini-delete-bare", "Martini DELETE missing MapAuth", "go_mw",
     "m.Delete(\"/notes/:id\", func(p martini.Params) { notes.Del(p[\"id\"]) })",
     "m.Get(\"/notes/:id\", MapAuth, func(u User, p martini.Params) { return notes.Get(p[\"id\"], u) })"),
    ("negroni-delete-no-mw", "Negroni DELETE mounted outside JWT middleware", "go_mw",
     "mux.HandleFunc(\"/notes/{id}\", h.Delete).Methods(\"DELETE\")",
     "n := negroni.New(negroni.HandlerFunc(jwt)); n.UseHandler(getMux)"),
    ("go-zero-jwt-skip-delete", "go-zero jwt:false leftover on delete", "go_mw",
     "delete:\n  handler: DeleteNoteHandler\n  jwt: false",
     "get:\n  handler: GetNoteHandler\n  jwt: true"),
    ("kratos-middleware-skip", "go-kratos HTTP delete missing middleware.JWT", "go_mw",
     "r.DELETE(\"/notes/{id}\", h.Delete)",
     "r.GET(\"/notes/{id}\", middleware.JWT(), h.Get)"),
    ("gokit-endpoint-open-delete", "Go kit delete endpoint missing AuthMiddleware", "go_mw",
     "r.Methods(\"DELETE\").Path(\"/notes/{id}\").Handler(httptransport.NewServer(deleteEp, dec, enc))",
     "r.Methods(\"GET\").Path(\"/notes/{id}\").Handler(httptransport.NewServer(authMw(getEp), dec, enc))"),
    ("goa-security-skip-delete", "Goa design delete missing Security", "go_mw",
     "Method(\"delete\", func() { HTTP(func() { DELETE(\"/notes/{id}\") }) })",
     "Method(\"show\", func() { Security(JWT); HTTP(func() { GET(\"/notes/{id}\") }) })"),
    ("go-restful-filter-skip", "go-restful delete missing Filter(auth)", "go_mw",
     "ws.Route(ws.DELETE(\"/notes/{id}\").To(h.Delete))",
     "ws.Route(ws.GET(\"/notes/{id}\").Filter(auth).To(h.Get))"),
    ("macaron-delete-bare", "Macaron DELETE missing reqAuth", "go_mw",
     "m.Delete(\"/notes/:id\", h.Delete)",
     "m.Get(\"/notes/:id\", reqAuth, h.Get)"),
    ("gotham-pipeline-skip-delete", "Gotham pipeline skip leftover on delete", "rust_ext",
     "fn delete(st: &State) -> (StatusCode, ()) { Note::delete(id(st)); (StatusCode::NO_CONTENT, ()) }",
     "fn get(st: &State) -> (StatusCode, String) { let u = AuthUser::borrow_from(st); Note::get(id(st), u.id) }"),
    ("nickel-delete-bare", "Nickel delete missing middleware", "rust_ext",
     "server.delete(\"/notes/:id\", middleware! { |req, res| notes::del(req.param(\"id\").unwrap()) })",
     "server.get(\"/notes/:id\", middleware! { |req, res| { let u = req.user(); notes::get(req.param(\"id\").unwrap(), u) } })"),
    ("iron-handler-open-delete", "Iron handler delete missing BeforeMiddleware", "rust_ext",
     "router.delete(\"/notes/:id\", delete_note, \"delete_note\");",
     "chain.link_before(Auth); router.get(\"/notes/:id\", get_note, \"get_note\");"),
    ("rouille-delete-bare", "rouille DELETE missing session login", "rust_ext",
     "(DELETE) (/notes/{id: i32}) => { notes::del(id); true }",
     "(GET) (/notes/{id: i32}) => { let u = session.user()?; notes::get(id, u) }"),
    ("thruster-mw-skip-delete", "Thruster delete missing auth middleware", "rust_ext",
     "app.delete(\"/notes/:id\", delete_note);",
     "app.use(auth); app.get(\"/notes/:id\", get_note);"),
    ("viz-guard-skip-delete", "Viz delete missing RequestExt user", "rust_ext",
     "async fn delete(Path(id): Path<i32>) { Note::delete(id).await }",
     "async fn get(Path(id): Path<i32>, user: User) { Note::get(id, user.id).await }"),
    ("salvo-hoop-skip-delete", "Salvo delete missing hoop auth", "rust_ext",
     "#[handler] async fn delete(req: &mut Request) { Note::delete(req.param(\"id\").unwrap()).await }",
     "router.push(Router::with_hoop(auth).get(get_note));"),
    ("ntex-guard-skip-delete", "ntex delete missing Identity extractor", "rust_ext",
     "async fn delete(path: web::Path<i32>) -> HttpResponse { Note::delete(*path).await; HttpResponse::NoContent().finish() }",
     "async fn get(path: web::Path<i32>, id: Identity) -> HttpResponse { Note::get(*path, id.id()).await }"),
    ("loco-auth-skip-delete", "Loco.rs delete missing auth extractor", "rust_ext",
     "async fn delete(Path(id): Path<i32>, State(ctx): State<AppContext>) { notes::delete(&ctx, id).await }",
     "async fn get(auth: auth::JWT, Path(id): Path<i32>, State(ctx): State<AppContext>) { notes::get(&ctx, id, auth.user_id).await }"),
    ("javalin-before-skip-delete", "Javalin delete outside before auth", "java_ann",
     "app.delete(\"/notes/{id}\", ctx -> notes.delete(ctx.pathParam(\"id\")));",
     "app.before(\"/notes/*\", ctx -> auth(ctx)); app.get(\"/notes/{id}\", ctx -> notes.get(ctx.pathParam(\"id\"), ctx.attribute(\"user\")));"),
    ("sparkjava-before-skip-delete", "SparkJava delete outside before filter", "java_ann",
     "delete(\"/notes/:id\", (req, res) -> { notes.delete(req.params(\":id\")); return \"\"; });",
     "before(\"/notes/*\", (req, res) -> auth(req)); get(\"/notes/:id\", (req, res) -> notes.get(req.params(\":id\"), req.attribute(\"user\")));"),
    ("ratpack-handler-open-delete", "Ratpack delete missing byAuth handler", "java_ann",
     "delete(\"notes/:id\", ctx -> notes.delete(ctx.getPathTokens().get(\"id\")));",
     "get(\"notes/:id\", ctx -> ctx.get(User.class); notes.get(id, user));"),
    ("helidon-roles-skip-delete", "Helidon delete missing RolesAllowed", "java_ann",
     "@DELETE @Path(\"{id}\") public void delete(@PathParam(\"id\") long id) { notes.delete(id); }",
     "@GET @Path(\"{id}\") @RolesAllowed(\"user\") public Note get(@PathParam(\"id\") long id) { return notes.get(id); }"),
    ("cxf-secure-skip-delete", "Apache CXF delete missing @RolesAllowed", "java_ann",
     "@DELETE @Path(\"{id}\") public void delete(@PathParam(\"id\") long id) { notes.delete(id); }",
     "@GET @Path(\"{id}\") @RolesAllowed(\"user\") public Note get(@PathParam(\"id\") long id) { return notes.get(id); }"),
    ("restlet-guard-skip-delete", "Restlet delete missing ChallengeAuthenticator", "java_ann",
     "router.attach(\"/notes/{id}\", DeleteNoteServerResource.class);",
     "guard.setNext(GetNoteServerResource.class); router.attach(\"/notes/{id}\", guard);"),
    ("grails-interceptor-skip", "Grails interceptor except destroy leftover", "rb_filter",
     "static except = ['destroy']\nboolean before() { true }",
     "def show() { respond noteService.get(params.id, request.user) }"),
    ("fatfree-route-open-delete", "Fat-Free Framework DELETE missing auth beacon", "php_mw",
     "$f3->route('DELETE /notes/@id', 'Note->delete');",
     "$f3->route('GET /notes/@id', 'Note->show'); $f3->set('AUTH', true);"),
    ("flightphp-delete-bare", "Flight PHP delete missing Flight::auth", "php_mw",
     "Flight::route('DELETE /notes/@id', function($id){ Note::delete($id); });",
     "Flight::route('GET /notes/@id', function($id){ Flight::auth(); return Note::get($id, Flight::get('user')); });"),
    ("swoole-http-delete-open", "Swoole HTTP delete missing session check", "php_mw",
     "$server->on('request', function ($req, $res) { if ($req->server['request_method']==='DELETE') notes_del($req); });",
     "if ($req->server['request_method']==='GET') { auth($req); notes_get($req); }"),
    ("workerman-delete-bare", "Workerman HTTP delete missing auth", "php_mw",
     "if ($request->method() === 'DELETE') return notes_del($request->id);",
     "if ($request->method() === 'GET') { $u = auth($request); return notes_get($request->id, $u); }"),
    ("spiral-guard-skip-delete", "Spiral Framework delete missing GuardNamespace", "php_mw",
     "#[Route('/notes/<id>', methods: 'DELETE')] public function delete(int $id): void",
     "#[Guarded] #[Route('/notes/<id>', methods: 'GET')] public function show(int $id): Note"),
    ("hyperf-middleware-skip-delete", "Hyperf delete outside auth middleware", "php_mw",
     "Router::delete('/notes/{id}', 'NoteController@destroy');",
     "Router::addGroup('/notes', function () { Router::get('/{id}', 'NoteController@show'); }, ['middleware' => [AuthMiddleware::class]]);"),
    ("webman-auth-skip-delete", "Webman delete missing Auth middleware", "php_mw",
     "Route::delete('/notes/{id}', [NoteController::class, 'destroy']);",
     "Route::group('/notes', function () { Route::get('/{id}', [NoteController::class, 'show']); })->middleware(Auth::class);"),
]

assert len(BFLA) == 80
assert len({x[0] for x in BFLA}) == 80


def pystr(s: str) -> str:
    return repr(s)


def emit_idor() -> str:
    lines = ["EXTRA_IDOR_ROWS = ["]
    for i, row in enumerate(IDOR):
        slug, surface, mod, model, lookup, sample, owner, product, bug = row
        plant = PLANTS[i]
        ticket = f"{plant[:3].upper()}-{1 + (i % 9)}"
        first = FIRST[i % 4]
        residual = RESIDUAL[i % 8]
        lines.append(
            "    dict("
            f"slug={pystr(slug)}, plant={pystr(plant)}, ticket={pystr(ticket)}, "
            f"surface={pystr(surface)}, mod={pystr(mod)}, model={pystr(model)}, "
            f"lookup={pystr(lookup)}, sample={pystr(sample)}, owner={pystr(owner)}, "
            f"first={pystr(first)}, residual={pystr(residual)}, "
            f"product={pystr(plant + '-' + product)}, bug={pystr(ticket + ' ' + bug)}"
            "),"
        )
    lines.append("]")
    return "\n".join(lines)


def emit_bfla() -> str:
    lines = ["BFLA_ROWS = ["]
    for i, row in enumerate(BFLA):
        slug, surface, family, skip, auth = row
        plant = PLANTS[i]
        ticket = f"{plant[:3].upper()}-{1 + (i % 9)}"
        leftover = LEFTOVER[i % 3]
        lines.append(
            "    dict("
            f"slug={pystr(slug)}, plant={pystr(plant)}, ticket={pystr(ticket)}, "
            f"surface={pystr(surface)}, family={pystr(family)}, "
            f"skip={pystr(skip)}, auth={pystr(auth)}, leftover={pystr(leftover)}"
            "),"
        )
    lines.append("]")
    return "\n".join(lines)


HEADER = '''"""Extra unique IDOR/BFLA plants for authz-regression-factory r1365+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1364 vesselNNNN-sys.
Not clones of r1364 geohash-cell-idor / channels-consumer-skip-delete.
"""
from __future__ import annotations


'''

FOOTER = '''

def extra_bflas(H):
    return [H(**_expand_bfla(row)) for row in BFLA_ROWS]


def _expand_bfla(row: dict) -> dict:
    plant = row["plant"]
    ticket = row["ticket"]
    slug = row["slug"]
    fw = row["surface"].split()[0]
    family = row["family"]
    skip = row["skip"]
    auth = row["auth"]
    leftover = row["leftover"]
    tag = ticket.split("-")[0].lower()
    src = f"src/{tag}_notes.py"
    handler = src
    test = f"tests/test_{tag}_delete.py"
    test_fn = "test_viewer_delete_403"
    src_fn = "delete"
    leftover_fn = leftover
    companion_path = f"src/{tag}_acl.py"
    src_obs = f"{skip}\\n    # {ticket} {fw} delete skip\\n"
    handler_obs = f"{auth}\\n"
    inspect_obs = f"{src}: {src_fn} skip\\n{test}: {test_fn}\\n"
    test_obs = (
        "def test_viewer_delete_403(client, viewer, note):\\n"
        "    client.login(viewer)\\n"
        '    assert client.delete(f"/notes/{note.id}").status_code == 403\\n'
    )
    first_apply = f"{fw} auth on list"
    first_path = src
    first_old = "def index():\\n    return Note.list()"
    first_new = f"def index():\\n    require_user()\\n    return Note.list()  # {tag} list"
    first_obs = f"list gated; {src_fn} leftover skip"
    reflection = (
        f"{fw} list auth does not wrap delete. Gate {src_fn} plus owner, leave {leftover} if still skipped."
    )
    plan_change = f"auth on {src_fn}; owner abort"
    grep_pat = f"{src_fn}|{leftover_fn}"
    grep_obs = f"{src}: {src_fn} skip\\n"
    legacy_path = src
    legacy_hint = f"{src_fn} skip"
    legacy_obs = src_obs
    legacy_new = (
        f"{auth}\\n"
        f"    n = Note.get(nid)\\n"
        f"    if n.owner_id != user.id: abort(403)\\n"
        f"    n.delete()  # {ticket} owner"
    )
    legacy_edit_obs = f"{src_fn} auth+owner"
    companion_old = "def owns(nid, uid): return True"
    companion_new = (
        "def owns(nid, uid):\\n"
        "    n = Note.get_raw(nid)\\n"
        "    return n is not None and n.owner_id == uid"
    )
    companion_obs = "owner"
    extra_fn = f"test_viewer_{leftover}_403"
    extra_old = "def test_viewer_delete_403(client, viewer, note):"
    extra_new = (
        f'@pytest.mark.xfail(reason="handoff: {leftover} still skipped", strict=False)\\n'
        f"def {extra_fn}(client, viewer, note):\\n"
        "    client.login(viewer)\\n"
        f'    assert client.{leftover if leftover != "update" else "put"}(f"/notes/{{note.id}}", json={{}}).status_code == 403\\n'
        "\\n"
        "def test_viewer_delete_403(client, viewer, note):"
    )
    extra_obs = f"xfails {leftover} leftover"
    handoff_path = src
    handoff_obs = f"{skip.replace('delete', leftover, 1) if 'delete' in skip.lower() else skip}\\n    # {leftover} still skipped\\n"
    if leftover not in handoff_obs.lower() and leftover not in skip.lower():
        handoff_obs = f"# {leftover} still skipped\\n{skip}\\n"
    handoff_hint = f"{leftover} still skipped"
    residual = handoff_hint
    residual_path = src
    residual_pat = leftover_fn
    residual_obs = handoff_obs
    residual_refl = f"{src_fn} gated. {leftover} still skipped."
    leave_cmd = f"echo {ticket} handoff {fw} {leftover} skipped"
    leave_obs = f"{ticket} handoff {fw} {leftover} skipped"
    goal = (
        f"{plant}-notes DELETE /notes/{{id}} is 200 for a viewer because {fw} {src_fn} skips auth. "
        f"Require auth without 403ing owners. Leave a handoff if {leftover} still skips."
    )
    plan = f"{first_apply} and rerun {test}."
    outcome = (
        f"List auth left {src_fn} skipped. Plan change: auth+owner on {src_fn}. "
        f"Partial: {leftover} leftover (xfail handoff)."
    )
    return dict(
        slug=slug,
        plant=plant,
        surface=row["surface"],
        src=src,
        src_fn=src_fn,
        handler=handler,
        test=test,
        test_fn=test_fn,
        bug_hint=f"{fw} {src_fn} skips auth; list/get uses auth",
        inspect_obs=inspect_obs,
        src_obs=src_obs,
        handler_obs=handler_obs,
        test_obs=test_obs,
        first_apply=first_apply,
        first_path=first_path,
        first_old=first_old,
        first_new=first_new,
        first_obs=first_obs,
        reflection=reflection,
        plan_change=plan_change,
        grep_pat=grep_pat,
        grep_obs=grep_obs,
        legacy_path=legacy_path,
        legacy_hint=legacy_hint,
        legacy_obs=legacy_obs,
        legacy_old=skip,
        legacy_new=legacy_new,
        legacy_edit_obs=legacy_edit_obs,
        companion_path=companion_path,
        companion_old=companion_old,
        companion_new=companion_new,
        companion_obs=companion_obs,
        extra_fn=extra_fn,
        extra_old=extra_old,
        extra_new=extra_new,
        extra_obs=extra_obs,
        handoff_path=handoff_path,
        handoff_obs=handoff_obs,
        handoff_hint=handoff_hint,
        residual=residual,
        residual_path=residual_path,
        residual_pat=residual_pat,
        residual_obs=residual_obs,
        residual_refl=residual_refl,
        leave_cmd=leave_cmd,
        leave_obs=leave_obs,
        ticket=ticket,
        goal=goal,
        plan=plan,
        outcome=outcome,
        family=family,
    )
'''

# FOOTER currently has escaped newlines that would write literal \\n into the
# generated plants file's Python source. Copy expand from r1285 instead.


def main() -> None:
    r1285 = Path(__file__).with_name("azr-plants-r1285.py").read_text()
    marker = "def extra_bflas(H):"
    expand = r1285[r1285.index(marker) :]
    text = HEADER + emit_idor() + "\n\n\n" + emit_bfla() + "\n\n\n" + expand
    OUT.write_text(text)
    print(f"wrote {OUT} bytes={OUT.stat().st_size} idor={len(IDOR)} bfla={len(BFLA)}")


if __name__ == "__main__":
    main()
