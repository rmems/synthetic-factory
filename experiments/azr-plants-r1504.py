"""Extra unique IDOR/BFLA plants for authz-regression-factory r1504+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1503 vesselNNNN-sys.
Not clones of r1364 geohash / r1445 casbin / r1464 DID-web / japronto.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
    dict(slug='iban-acct-idor', plant='heeling', ticket='HEE-1', surface='IBAN account object-id IDOR', mod='ibans', model='Iban', lookup='iban', sample='DE89370400440532013000', owner='bank_id', first='authn', residual='pdf', product='heeling-iban-iso', bug='HEE-1 IBAN unique from ISO 13616'),
    dict(slug='bban-acct-idor', plant='helmport', ticket='HEL-2', surface='BBAN account object-id IDOR', mod='bbans', model='Bban', lookup='bban', sample='370400440532013000', owner='bank_id', first='mask', residual='export', product='helmport-bban-iso', bug='HEL-2 BBAN unique from national'),
    dict(slug='sortcode-uk-idor', plant='hogging', ticket='HOG-3', surface='UK sort code object-id IDOR', mod='sorts', model='Sort', lookup='sortcode', sample='040004', owner='bank_id', first='any_member', residual='search', product='hogging-sort-uk', bug='HOG-3 sort unique from Vocalink'),
    dict(slug='tin-us-idor', plant='inboard', ticket='INB-4', surface='US TIN taxpayer object-id IDOR', mod='tins', model='Tin', lookup='tin', sample='12-3456789', owner='firm_id', first='list_scope', residual='mget', product='inboard-tin-us', bug='INB-4 TIN unique from IRS'),
    dict(slug='ein-us-idor', plant='jibhank', ticket='JIB-5', surface='EIN employer object-id IDOR', mod='eins', model='Ein', lookup='ein', sample='98-7654321', owner='firm_id', first='authn', residual='csv', product='jibhank-ein-us', bug='JIB-5 EIN unique from IRS'),
    dict(slug='itin-us-idor', plant='keelband', ticket='KEE-6', surface='ITIN taxpayer object-id IDOR', mod='itins', model='Itin', lookup='itin', sample='9XX-70-XXXX', owner='firm_id', first='mask', residual='admin', product='keelband-itin-us', bug='KEE-6 ITIN unique from IRS'),
    dict(slug='wkn-de-idor', plant='logchip', ticket='LOG-7', surface='WKN security object-id IDOR', mod='wkns', model='Wkn', lookup='wkn', sample='A1EWWW', owner='book_id', first='any_member', residual='webhook', product='logchip-wkn-de', bug='LOG-7 WKN unique from WM Daten'),
    dict(slug='valor-ch-idor', plant='lufftackle', ticket='LUF-8', surface='Valoren number object-id IDOR', mod='valors', model='Valor', lookup='valor', sample='1222171', owner='book_id', first='list_scope', residual='comments', product='lufftackle-valor-ch', bug='LUF-8 Valor unique from SIX'),
    dict(slug='permid-idor', plant='mastband', ticket='MAS-9', surface='PermID instrument object-id IDOR', mod='permids', model='Permid', lookup='permid', sample='4295904307', owner='book_id', first='authn', residual='pdf', product='mastband-permid-ref', bug='MAS-9 PermID unique from LSEG'),
    dict(slug='cfi-code-idor', plant='midship', ticket='MID-1', surface='CFI classification object-id IDOR', mod='cfis', model='Cfi', lookup='cfi', sample='ESVUFR', owner='book_id', first='mask', residual='export', product='midship-cfi-iso', bug='MID-1 CFI unique from ISO 10962'),
    dict(slug='dti-cftc-idor', plant='monkey', ticket='MON-2', surface='DTI swap object-id IDOR', mod='dtis', model='Dti', lookup='dti', sample='RDT1C3L9K8', owner='book_id', first='any_member', residual='search', product='monkey-dti-cftc', bug='MON-2 DTI unique from CFTC'),
    dict(slug='scfigi-idor', plant='mouse', ticket='MOU-3', surface='share-class FIGI object-id IDOR', mod='scfigis', model='Scfigi', lookup='scfigi', sample='BBG001S5N8V8', owner='book_id', first='list_scope', residual='mget', product='mouse-scfigi-omg', bug='MOU-3 share-class FIGI unique from OMG'),
    dict(slug='ticker-bbg-idor', plant='nipple', ticket='NIP-4', surface='Bloomberg ticker object-id IDOR', mod='bbgticks', model='Bbgtick', lookup='bbgtick', sample='AAPL US Equity', owner='book_id', first='authn', residual='csv', product='nipple-bbg-tick', bug='NIP-4 ticker unique from Bloomberg'),
    dict(slug='opmic-idor', plant='outboard', ticket='OUT-5', surface='operating MIC object-id IDOR', mod='opmics', model='Opmic', lookup='opmic', sample='XNAS', owner='venue_group', first='mask', residual='admin', product='outboard-opmic-iso', bug='OUT-5 operating MIC unique from ISO 10383'),
    dict(slug='segmic-idor', plant='pee', ticket='PEE-6', surface='segment MIC object-id IDOR', mod='segmics', model='Segmic', lookup='segmic', sample='XNGS', owner='venue_group', first='any_member', residual='webhook', product='pee-segmic-iso', bug='PEE-6 segment MIC unique from ISO 10383'),
    dict(slug='ruc-pe-idor', plant='reefear', ticket='REE-7', surface='Peru RUC object-id IDOR', mod='rucpes', model='Rucpe', lookup='rucpe', sample='20123456789', owner='firm_id', first='list_scope', residual='comments', product='reefear-ruc-pe', bug='REE-7 RUC unique from SUNAT'),
    dict(slug='ruc-ec-idor', plant='bunkers', ticket='BUN-8', surface='Ecuador RUC object-id IDOR', mod='rucecs', model='Rucec', lookup='rucec', sample='1790012345001', owner='firm_id', first='authn', residual='pdf', product='bunkers-ruc-ec', bug='BUN-8 RUC unique from SRI'),
    dict(slug='ruc-py-idor', plant='cablelaid', ticket='CAB-9', surface='Paraguay RUC object-id IDOR', mod='rucpys', model='Rucpy', lookup='rucpy', sample='80012345-6', owner='firm_id', first='mask', residual='export', product='cablelaid-ruc-py', bug='CAB-9 RUC unique from SET'),
    dict(slug='ruc-pa-idor', plant='camberstrake', ticket='CAM-1', surface='Panama RUC object-id IDOR', mod='rucpas', model='Rucpa', lookup='rucpa', sample='155588888-2-2015', owner='firm_id', first='any_member', residual='search', product='camberstrake-ruc-pa', bug='CAM-1 RUC unique from DGI'),
    dict(slug='rnc-do-idor', plant='cantline', ticket='CAN-2', surface='Dominican RNC object-id IDOR', mod='rncs', model='Rnc', lookup='rnc', sample='130123456', owner='firm_id', first='list_scope', residual='mget', product='cantline-rnc-do', bug='CAN-2 RNC unique from DGII'),
    dict(slug='rtn-hn-idor', plant='caprail', ticket='CAP-3', surface='Honduras RTN object-id IDOR', mod='rtns', model='Rtn', lookup='rtn', sample='08011999123456', owner='firm_id', first='authn', residual='csv', product='caprail-rtn-hn', bug='CAP-3 RTN unique from SAR'),
    dict(slug='nite-cr-idor', plant='catdavits', ticket='CAT-4', surface='Costa Rica NITE object-id IDOR', mod='nites', model='Nite', lookup='nite', sample='3-101-123456', owner='firm_id', first='mask', residual='admin', product='catdavits-nite-cr', bug='CAT-4 NITE unique from Hacienda'),
    dict(slug='nit-sv-idor', plant='cheekknee', ticket='CHE-5', surface='El Salvador NIT object-id IDOR', mod='nitsv', model='Nitsv', lookup='nitsv', sample='0614-290180-102-5', owner='firm_id', first='any_member', residual='webhook', product='cheekknee-nit-sv', bug='CHE-5 NIT unique from MH'),
    dict(slug='nit-gt-idor', plant='chockbeam', ticket='CHO-6', surface='Guatemala NIT object-id IDOR', mod='nitgt', model='Nitgt', lookup='nitgt', sample='1234567-8', owner='firm_id', first='list_scope', residual='comments', product='chockbeam-nit-gt', bug='CHO-6 NIT unique from SAT'),
    dict(slug='cpf-br-idor', plant='clewgarnet', ticket='CLE-7', surface='CPF taxpayer object-id IDOR', mod='cpfs', model='Cpf', lookup='cpf', sample='123.456.789-09', owner='firm_id', first='authn', residual='pdf', product='clewgarnet-cpf-br', bug='CLE-7 CPF unique from Receita'),
    dict(slug='rfc-pf-idor', plant='coamingbeam', ticket='COA-8', surface='RFC persona fisica object-id IDOR', mod='rfcpfs', model='Rfcpf', lookup='rfcpf', sample='XAXX010101HDFXXX01', owner='firm_id', first='mask', residual='export', product='coamingbeam-rfc-pf', bug='COA-8 RFC PF unique from SAT'),
    dict(slug='ico-sk-idor', plant='cockpitsole', ticket='COC-9', surface='Slovak ICO object-id IDOR', mod='icosk', model='Icosk', lookup='icosk', sample='35780154', owner='firm_id', first='any_member', residual='search', product='cockpitsole-ico-sk', bug='COC-9 ICO unique from ORSR'),
    dict(slug='oib-hr-idor', plant='countertimber', ticket='COU-1', surface='Croatian OIB object-id IDOR', mod='oibs', model='Oib', lookup='oib', sample='12345678901', owner='firm_id', first='list_scope', residual='mget', product='countertimber-oib-hr', bug='COU-1 OIB unique from Porezna'),
    dict(slug='pib-rs-idor', plant='cringlesplice', ticket='CRI-2', surface='Serbian PIB object-id IDOR', mod='pibs', model='Pib', lookup='pib', sample='100000003', owner='firm_id', first='authn', residual='csv', product='cringlesplice-pib-rs', bug='CRI-2 PIB unique from PURS'),
    dict(slug='edrpou-ua-idor', plant='daggerport', ticket='DAG-3', surface='EDRPOU entity object-id IDOR', mod='edrpous', model='Edrpou', lookup='edrpou', sample='00032139', owner='firm_id', first='mask', residual='admin', product='daggerport-edrpou-ua', bug='DAG-3 EDRPOU unique from USR'),
    dict(slug='bin-kz-idor', plant='davitspan', ticket='DAV-4', surface='Kazakh BIN object-id IDOR', mod='binkz', model='Binkz', lookup='binkz', sample='041140000111', owner='firm_id', first='any_member', residual='webhook', product='davitspan-bin-kz', bug='DAV-4 BIN unique from KGDC'),
    dict(slug='gst-my-idor', plant='fishdavit', ticket='FIS-5', surface='Malaysia GST ID object-id IDOR', mod='gstmys', model='Gstmy', lookup='gstmy', sample='001234567890', owner='firm_id', first='list_scope', residual='comments', product='fishdavit-gst-my', bug='FIS-5 GST unique from LHDN'),
    dict(slug='npwp-id-idor', plant='footblock', ticket='FOO-6', surface='Indonesia NPWP object-id IDOR', mod='npwps', model='Npwp', lookup='npwp', sample='10.123.456.7-012.000', owner='firm_id', first='authn', residual='pdf', product='footblock-npwp-id', bug='FOO-6 NPWP unique from DJP'),
    dict(slug='tin-ph-idor', plant='gaffthroat', ticket='GAF-7', surface='Philippines TIN object-id IDOR', mod='tinphs', model='Tinph', lookup='tinph', sample='123-456-789-000', owner='firm_id', first='mask', residual='export', product='gaffthroat-tin-ph', bug='GAF-7 TIN unique from BIR'),
    dict(slug='crn-kr-idor', plant='gammoniron', ticket='GAM-8', surface='Korea CRN object-id IDOR', mod='crnkrs', model='Crnkr', lookup='crnkr', sample='110111-1234567', owner='firm_id', first='any_member', residual='search', product='gammoniron-crn-kr', bug='GAM-8 CRN unique from NTS'),
    dict(slug='houjin-jp-idor', plant='guyplate', ticket='GUY-9', surface='Japan houjin bangou object-id IDOR', mod='houjins', model='Houjin', lookup='houjin', sample='1234567890123', owner='firm_id', first='list_scope', residual='mget', product='guyplate-houjin-jp', bug='GUY-9 houjin unique from NTA'),
    dict(slug='uscc-cn-idor', plant='hawsehole', ticket='HAW-1', surface='China USCC object-id IDOR', mod='usccs', model='Uscc', lookup='uscc', sample='91110000MA01234567', owner='firm_id', first='authn', residual='csv', product='hawsehole-uscc-cn', bug='HAW-1 USCC unique from SAMR'),
    dict(slug='brn-tw-idor', plant='headrail', ticket='HEA-2', surface='Taiwan BAN object-id IDOR', mod='brntws', model='Brntw', lookup='brntw', sample='12345678', owner='firm_id', first='mask', residual='admin', product='headrail-brn-tw', bug='HEA-2 BAN unique from MOF'),
    dict(slug='abn-branch-idor', plant='hogpiece', ticket='HOG-3', surface='ABN branch object-id IDOR', mod='abnbrs', model='Abnbr', lookup='abnbr', sample='51824753556-001', owner='firm_id', first='any_member', residual='webhook', product='hogpiece-abn-br', bug='HOG-3 ABN branch unique from ABR'),
    dict(slug='gstin-isd-idor', plant='limberboard', ticket='LIM-4', surface='GSTIN ISD object-id IDOR', mod='gstisds', model='Gstisd', lookup='gstisd', sample='27AAPFU0939F2Z1', owner='firm_id', first='list_scope', residual='comments', product='limberboard-gstin-isd', bug='LIM-4 ISD unique from GSTN'),
]


BFLA_ROWS = [
    dict(slug='hypercorn-delete-bare', plant='heeling', ticket='HEE-1', surface='Hypercorn ASGI delete missing auth', family='py_async', skip="@app.delete('/notes/{nid}')\nasync def delete(nid: str):", auth="@app.get('/notes/{nid}')\nasync def get(nid: str, user=Depends(auth)):", leftover='put'),
    dict(slug='daphne-delete-bare', plant='helmport', ticket='HEL-2', surface='Daphne ASGI delete missing auth', family='py_async', skip="async def delete(scope, receive, send):\n    await notes.del(scope['path'])", auth="async def get(scope, receive, send):\n    auth(scope)\n    await notes.get(scope['path'])", leftover='patch'),
    dict(slug='granian-delete-bare', plant='hogging', ticket='HOG-3', surface='Granian delete missing auth', family='py_async', skip="@app.delete('/notes/{nid}')\nasync def delete(nid: str):", auth="@app.get('/notes/{nid}')\nasync def get(nid: str, user=Depends(auth)):", leftover='update'),
    dict(slug='flask-restless-delete-bare', plant='inboard', ticket='INB-4', surface='Flask-Restless delete missing preprocessors', family='py_async', skip="manager.create_api(Note, methods=['DELETE'])", auth="manager.create_api(Note, methods=['GET'], preprocessors={'GET_SINGLE': [auth]})", leftover='put'),
    dict(slug='flask-admin-delete-bare', plant='jibhank', ticket='JIB-5', surface='Flask-Admin delete missing is_accessible', family='py_async', skip='class NoteAdmin(ModelView):\n    can_delete = True', auth='class NoteAdmin(ModelView):\n    def is_accessible(self):\n        return current_user.is_authenticated', leftover='patch'),
    dict(slug='django-oscar-delete-bare', plant='keelband', ticket='KEE-6', surface='django-Oscar delete missing dashboard perm', family='py_async', skip='def delete_order(request, pk):\n    Order.objects.get(pk=pk).delete()', auth="@permission_required('order.view_order')\ndef order_detail(request, pk):", leftover='update'),
    dict(slug='feincms-delete-bare', plant='logchip', ticket='LOG-7', surface='FeinCMS delete missing item_editor auth', family='py_async', skip='def delete_page(request, pk):\n    Page.objects.get(pk=pk).delete()', auth='@staff_member_required\ndef page_editor(request, pk):', leftover='put'),
    dict(slug='hobby-delete-bare', plant='lufftackle', ticket='LUF-8', surface='Hobby delete missing halt', family='rb_filter', skip='delete { |id| Note[id].destroy }', auth='get { |id| halt 401 unless env.user; Note[id] }', leftover='patch'),
    dict(slug='httprouter-delete-bare', plant='mastband', ticket='MAS-9', surface='httprouter DELETE missing auth', family='go_mw', skip="router.DELETE('/notes/:id', h.Delete)", auth="router.GET('/notes/:id', auth, h.Get)", leftover='update'),
    dict(slug='httptreemux-delete-bare', plant='midship', ticket='MID-1', surface='httptreemux DELETE missing auth', family='go_mw', skip="router.DELETE('/notes/:id', h.Delete)", auth="router.GET('/notes/:id', authGet)", leftover='put'),
    dict(slug='atreugo-delete-bare', plant='monkey', ticket='MON-2', surface='Atreugo DELETE missing middlewares', family='go_mw', skip="server.DELETE('/notes/:id', h.Delete)", auth="server.UseBefore(auth)\nserver.GET('/notes/:id', h.Get)", leftover='patch'),
    dict(slug='alice-mw-delete-bare', plant='mouse', ticket='MOU-3', surface='justinas/alice DELETE outside chain', family='go_mw', skip="r.Handle('/notes/{id}', delNote).Methods('DELETE')", auth="chain := alice.New(auth)\nr.Handle('/notes/{id}', chain.Then(getNote)).Methods('GET')", leftover='update'),
    dict(slug='pat-go-delete-bare', plant='nipple', ticket='NIP-4', surface='bmizerany/pat DELETE missing auth', family='go_mw', skip="m.Del('/notes/:id', h.Delete)", auth="m.Get('/notes/:id', auth, h.Get)", leftover='put'),
    dict(slug='gocraft-web-delete-bare', plant='outboard', ticket='OUT-5', surface='gocraft/web DELETE missing middleware', family='go_mw', skip="router.Delete('/notes/:id', (*Context).Delete)", auth="router.Middleware(Auth)\nrouter.Get('/notes/:id', (*Context).Get)", leftover='patch'),
    dict(slug='traffic-delete-bare', plant='pee', ticket='PEE-6', surface='Traffic DELETE missing filter', family='go_mw', skip="t.Delete('/notes/:id', h.Delete)", auth="t.Get('/notes/:id', auth, h.Get)", leftover='update'),
    dict(slug='go-json-rest-delete-bare', plant='reefear', ticket='REE-7', surface='go-json-rest DELETE missing auth', family='go_mw', skip="&rest.Route{'DELETE', '/notes/:id', h.Delete}", auth="&rest.Route{'GET', '/notes/:id', authGet}", leftover='put'),
    dict(slug='leptos-delete-bare', plant='bunkers', ticket='BUN-8', surface='Leptos server fn delete missing user', family='rust_ext', skip='#[server]\nasync fn delete_note(id: i32) { Note::delete(id).await }', auth='#[server]\nasync fn get_note(id: i32) { let u = use_user()?; Note::get(id, u.id).await }', leftover='patch'),
    dict(slug='dioxus-delete-bare', plant='cablelaid', ticket='CAB-9', surface='Dioxus server delete missing session', family='rust_ext', skip='#[server]\nasync fn delete_note(id: i32) { Note::delete(id).await }', auth='#[server]\nasync fn get_note(id: i32) { extract_user()?; Note::get(id).await }', leftover='update'),
    dict(slug='sycamore-delete-bare', plant='camberstrake', ticket='CAM-1', surface='Sycamore server delete missing auth', family='rust_ext', skip='async fn delete(id: i32) { Note::delete(id).await }', auth='async fn get(id: i32, user: User) { Note::get(id, user.id).await }', leftover='put'),
    dict(slug='http4k-delete-bare', plant='cantline', ticket='CAN-2', surface='http4k delete outside Filter', family='java_ann', skip='"/notes/{id}" bindContract DELETE to { notes.del(it) }', auth='"/notes/{id}" bindContract GET to { req -> auth(req); notes.get(id) }', leftover='patch'),
    dict(slug='finatra-delete-bare', plant='caprail', ticket='CAP-3', surface='Finatra delete missing filter', family='scala_mw', skip="delete('/notes/:id') { notes.del(params('id')) }", auth="filter[AuthFilter].get('/notes/:id') { notes.get(params('id'), user) }", leftover='update'),
    dict(slug='pretender-delete-bare', plant='catdavits', ticket='CAT-4', surface='Pretender delete missing guard', family='rust_ext', skip='async fn delete(Path(id): Path<i32>) { Note::delete(id).await }', auth='async fn get(Path(id): Path<i32>, user: User) { Note::get(id, user.id).await }', leftover='put'),
    dict(slug='yew-ssr-delete-bare', plant='cheekknee', ticket='CHE-5', surface='Yew SSR delete missing auth', family='rust_ext', skip='#[function_component]\nfn Delete(id: i32) { Note::delete(id); }', auth='#[function_component]\nfn Show(id: i32, user: User) { Note::get(id, user.id); }', leftover='patch'),
    dict(slug='fiber-group-skip-delete', plant='chockbeam', ticket='CHO-6', surface='Fiber group DELETE skipping jwtware', family='go_mw', skip="app.Delete('/notes/:id', h.Delete)", auth="g := app.Group('/notes', jwtware.New()); g.Get('/:id', h.Get)", leftover='update'),
    dict(slug='gin-engine-skip-delete', plant='clewgarnet', ticket='CLE-7', surface='Gin engine DELETE outside group auth', family='go_mw', skip="r.DELETE('/notes/:id', h.Delete)", auth="g := r.Group('/notes', Auth()); g.GET('/:id', h.Get)", leftover='put'),
    dict(slug='echo-group-skip-delete', plant='coamingbeam', ticket='COA-8', surface='Echo group DELETE skipping JWT', family='go_mw', skip="e.DELETE('/notes/:id', h.Delete)", auth="g := e.Group('/notes', mw.JWT()); g.GET('/:id', h.Get)", leftover='patch'),
    dict(slug='chi-except-skip-delete', plant='cockpitsole', ticket='COC-9', surface='chi Except DELETE leftover', family='go_mw', skip="r.With(chimw.Except(auth, 'DELETE')).Delete('/notes/{id}', h.Delete)", auth="r.With(auth).Get('/notes/{id}', h.Get)", leftover='update'),
    dict(slug='iris-party-skip-delete', plant='countertimber', ticket='COU-1', surface='Iris party DELETE outside auth', family='go_mw', skip="app.Delete('/notes/{id}', h.Delete)", auth="p := app.Party('/notes', auth); p.Get('/{id}', h.Get)", leftover='put'),
    dict(slug='beego-ns-skip-delete', plant='cringlesplice', ticket='CRI-2', surface='Beego namespace DELETE missing Filter', family='go_mw', skip="beego.NSRouter('/notes/:id', &C{}, 'delete:Delete')", auth="ns := beego.NewNamespace('/notes', beego.NSBefore(auth), beego.NSRouter('/:id', &C{}, 'get:Get'))", leftover='patch'),
    dict(slug='macaron-group-skip-delete', plant='daggerport', ticket='DAG-3', surface='Macaron group DELETE missing reqAuth', family='go_mw', skip="m.Delete('/notes/:id', h.Delete)", auth="m.Group('/notes', func() { m.Get('/:id', h.Get) }, reqAuth)", leftover='update'),
    dict(slug='buffalo-skip-delete', plant='davitspan', ticket='DAV-4', surface='Buffalo DELETE outside authorization', family='go_mw', skip="app.DELETE('/notes/{id}', notes.Destroy)", auth="app.Use(Authorization); app.GET('/notes/{id}', notes.Show)", leftover='put'),
    dict(slug='revel-skip-delete', plant='fishdavit', ticket='FIS-5', surface='Revel Delete missing CheckAuth', family='go_mw', skip='func (c Notes) Delete(id int) revel.Result { c.Txn.Delete(&Note{Id: id}); return c.NoContent() }', auth='func (c Notes) Show(id int) revel.Result { c.CheckAuth(); return c.RenderJSON(c.Txn.Get(id, c.User)) }', leftover='patch'),
    dict(slug='goa-skip-delete', plant='footblock', ticket='FOO-6', surface='Goa delete missing Security', family='go_mw', skip="Method('delete', func() { HTTP(func() { DELETE('/notes/{id}') }) })", auth="Method('show', func() { Security(JWT); HTTP(func() { GET('/notes/{id}') }) })", leftover='update'),
    dict(slug='gokit-skip-delete', plant='gaffthroat', ticket='GAF-7', surface='Go kit delete missing AuthMiddleware', family='go_mw', skip="r.Methods('DELETE').Path('/notes/{id}').Handler(kithttp.NewServer(deleteEp, dec, enc))", auth="r.Methods('GET').Path('/notes/{id}').Handler(kithttp.NewServer(authMw(getEp), dec, enc))", leftover='put'),
    dict(slug='kratos-skip-delete', plant='gammoniron', ticket='GAM-8', surface='go-kratos HTTP delete missing JWT', family='go_mw', skip="r.DELETE('/notes/{id}', h.Delete)", auth="r.GET('/notes/{id}', middleware.JWT(), h.Get)", leftover='patch'),
    dict(slug='gozero-skip-delete', plant='guyplate', ticket='GUY-9', surface='go-zero jwt:false leftover on delete', family='go_mw', skip='delete:\n  handler: DeleteNoteHandler\n  jwt: false', auth='get:\n  handler: GetNoteHandler\n  jwt: true', leftover='update'),
    dict(slug='restful-skip-delete', plant='hawsehole', ticket='HAW-1', surface='go-restful delete missing Filter', family='go_mw', skip="ws.Route(ws.DELETE('/notes/{id}').To(h.Delete))", auth="ws.Route(ws.GET('/notes/{id}').Filter(auth).To(h.Get))", leftover='put'),
    dict(slug='martini-skip-delete', plant='headrail', ticket='HEA-2', surface='Martini DELETE missing MapAuth', family='go_mw', skip="m.Delete('/notes/:id', func(p martini.Params) { notes.Del(p['id']) })", auth="m.Get('/notes/:id', MapAuth, func(u User, p martini.Params) { return notes.Get(p['id'], u) })", leftover='patch'),
    dict(slug='negroni-skip-delete', plant='hogpiece', ticket='HOG-3', surface='Negroni DELETE mounted outside JWT', family='go_mw', skip="mux.HandleFunc('/notes/{id}', h.Delete).Methods('DELETE')", auth='n := negroni.New(negroni.HandlerFunc(jwt)); n.UseHandler(getMux)', leftover='update'),
    dict(slug='chi-mount-skip-delete', plant='limberboard', ticket='LIM-4', surface='chi Mount DELETE skipping authorize', family='go_mw', skip="r.Delete('/notes/{id}', h.Delete)", auth="r.Route('/notes', func(r chi.Router) { r.Use(authorize); r.Get('/{id}', h.Get) })", leftover='put'),
]


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
    src_obs = f"{skip}\n    # {ticket} {fw} delete skip\n"
    handler_obs = f"{auth}\n"
    inspect_obs = f"{src}: {src_fn} skip\n{test}: {test_fn}\n"
    test_obs = (
        "def test_viewer_delete_403(client, viewer, note):\n"
        "    client.login(viewer)\n"
        '    assert client.delete(f"/notes/{note.id}").status_code == 403\n'
    )
    first_apply = f"{fw} auth on list"
    first_path = src
    first_old = "def index():\n    return Note.list()"
    first_new = f"def index():\n    require_user()\n    return Note.list()  # {tag} list"
    first_obs = f"list gated; {src_fn} leftover skip"
    reflection = (
        f"{fw} list auth does not wrap delete. Gate {src_fn} plus owner, leave {leftover} if still skipped."
    )
    plan_change = f"auth on {src_fn}; owner abort"
    grep_pat = f"{src_fn}|{leftover_fn}"
    grep_obs = f"{src}: {src_fn} skip\n"
    legacy_path = src
    legacy_hint = f"{src_fn} skip"
    legacy_obs = src_obs
    legacy_old = skip.split("\n")[0] if False else skip
    # keep skip unique as old; new is auth+owner
    legacy_new = (
        f"{auth}\n"
        f"    n = Note.get(nid)\n"
        f"    if n.owner_id != user.id: abort(403)\n"
        f"    n.delete()  # {ticket} owner"
    )
    legacy_edit_obs = f"{src_fn} auth+owner"
    companion_old = "def owns(nid, uid): return True"
    companion_new = (
        "def owns(nid, uid):\n"
        "    n = Note.get_raw(nid)\n"
        "    return n is not None and n.owner_id == uid"
    )
    companion_obs = "owner"
    extra_fn = f"test_viewer_{leftover}_403"
    extra_old = "def test_viewer_delete_403(client, viewer, note):"
    extra_new = (
        f'@pytest.mark.xfail(reason="handoff: {leftover} still skipped", strict=False)\n'
        f"def {extra_fn}(client, viewer, note):\n"
        "    client.login(viewer)\n"
        f'    assert client.{leftover if leftover != "update" else "put"}(f"/notes/{{note.id}}", json={{}}).status_code == 403\n'
        "\n"
        "def test_viewer_delete_403(client, viewer, note):"
    )
    extra_obs = f"xfails {leftover} leftover"
    handoff_path = src
    handoff_obs = f"{skip.replace('delete', leftover, 1) if 'delete' in skip.lower() else skip}\n    # {leftover} still skipped\n"
    if leftover not in handoff_obs.lower() and leftover not in skip.lower():
        handoff_obs = f"# {leftover} still skipped\n{skip}\n"
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
    )
