"""Extra unique IDOR/BFLA plants for authz-regression-factory r1464+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1463 vesselNNNN-sys.
Not clones of r1364 geohash-cell-idor / channels-consumer-skip-delete.
Not clones of r1445–r1458 casbin/oso/keycloak/ory/auth0 plants.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
    dict(slug='did-web-idor', plant='abaft', ticket='ABA-1', surface='DID web identifier object-id IDOR', mod='dids', model='Did', lookup='did', sample='did:web:issuer.example', owner='issuer_id', first='authn', residual='pdf', product='abaft-did-web', bug='ABA-1 DID unique from W3C DID'),
    dict(slug='cid-ipfs-idor', plant='ahull', ticket='AHU-2', surface='IPFS CID object-id IDOR', mod='cids', model='Cid', lookup='cid', sample='bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi', owner='node_id', first='mask', residual='export', product='ahull-ipfs-cid', bug='AHU-2 CID unique from IPFS'),
    dict(slug='arweave-tx-idor', plant='aweather', ticket='AWE-3', surface='Arweave tx object-id IDOR', mod='arweave', model='Arweave', lookup='arx', sample='sHqUBKFeS42-CMCvNqPR31yM0SfugqhtXgdl_eEXAM1', owner='wallet_id', first='any_member', residual='search', product='aweather-arweave-tx', bug='AWE-3 tx unique from Arweave'),
    dict(slug='ens-name-idor', plant='backwash', ticket='BAC-4', surface='ENS name object-id IDOR', mod='ens', model='Ens', lookup='ens', sample='vitalik.eth', owner='wallet_id', first='list_scope', residual='mget', product='backwash-ens-name', bug='BAC-4 ENS unique from registry'),
    dict(slug='sns-sol-idor', plant='belaying', ticket='BEL-5', surface='SNS Solana name object-id IDOR', mod='sns', model='Sns', lookup='sns', sample='bonfida.sol', owner='wallet_id', first='authn', residual='csv', product='belaying-sns-sol', bug='BEL-5 SNS unique from Bonfida'),
    dict(slug='lnurl-pay-idor', plant='bight', ticket='BIG-6', surface='LNURL-pay object-id IDOR', mod='lnurls', model='Lnurl', lookup='lnurl', sample='LNURL1DP68GURN8GHJ7MRWW4EXCTNXD9SHG6NPV3JXSCTQDSKHX', owner='node_id', first='mask', residual='admin', product='bight-lnurl-pay', bug='BIG-6 LNURL unique from LUD-06'),
    dict(slug='bolt11-inv-idor', plant='bitt', ticket='BIT-7', surface='BOLT11 invoice object-id IDOR', mod='bolt11s', model='Bolt11', lookup='bolt11', sample='lnbc20m1pvjluezpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypq', owner='node_id', first='any_member', residual='webhook', product='bitt-bolt11-inv', bug='BIT-7 BOLT11 unique from invoice'),
    dict(slug='upi-vpa-idor', plant='boomend', ticket='BOO-8', surface='UPI VPA object-id IDOR', mod='vpasa', model='Vpa', lookup='vpa', sample='merchant@upi', owner='bank_id', first='list_scope', residual='comments', product='boomend-upi-vpa', bug='BOO-8 VPA unique from NPCI'),
    dict(slug='paynow-uen-idor', plant='breast', ticket='BRE-9', surface='PayNow UEN object-id IDOR', mod='paynows', model='Paynow', lookup='uen', sample='201234567A', owner='firm_id', first='authn', residual='pdf', product='breast-paynow-uen', bug='BRE-9 UEN unique from PayNow'),
    dict(slug='duitnow-idor', plant='brightwork', ticket='BRI-1', surface='DuitNow proxy object-id IDOR', mod='duitnows', model='Duitnow', lookup='duitnow', sample='+60123456789', owner='bank_id', first='mask', residual='export', product='brightwork-duitnow-my', bug='BRI-1 DuitNow unique from PayNet'),
    dict(slug='promptpay-idor', plant='bunkboard', ticket='BUN-2', surface='PromptPay proxy object-id IDOR', mod='promptpays', model='Promptpay', lookup='ppid', sample='0105542000000', owner='bank_id', first='any_member', residual='search', product='bunkboard-promptpay-th', bug='BUN-2 PromptPay unique from BOT'),
    dict(slug='alias-cbu-idor', plant='cantframe', ticket='CAN-3', surface='CBU alias object-id IDOR', mod='cbus', model='Cbu', lookup='cbu', sample='0000003100000000000001', owner='bank_id', first='list_scope', residual='mget', product='cantframe-cbu-ar', bug='CAN-3 CBU unique from BCRA'),
    dict(slug='occ-osi-idor', plant='carlings', ticket='CAR-4', surface='OCC OSI option object-id IDOR', mod='osis', model='Osi', lookup='osi', sample='AAPL  240119C00150000', owner='book_id', first='authn', residual='csv', product='carlings-occ-osi', bug='CAR-4 OSI unique from OCC'),
    dict(slug='fisn-idor', plant='catspaw', ticket='CAT-5', surface='FISN instrument object-id IDOR', mod='fisns', model='Fisn', lookup='fisn', sample='US0378331005/APPLE INC', owner='book_id', first='mask', residual='admin', product='catspaw-fisn-iso', bug='CAT-5 FISN unique from ISO 18774'),
    dict(slug='vlei-idor', plant='chainhook', ticket='CHA-6', surface='vLEI legal entity object-id IDOR', mod='vleis', model='Vlei', lookup='vlei', sample='ENqP3owN7XPR4owkQ', owner='firm_id', first='any_member', residual='webhook', product='chainhook-vlei-gleif', bug='CHA-6 vLEI unique from GLEIF'),
    dict(slug='gstin-idor', plant='cheekblock', ticket='CHE-7', surface='GSTIN taxpayer object-id IDOR', mod='gstins', model='Gstin', lookup='gstin', sample='27AAPFU0939F1ZV', owner='firm_id', first='list_scope', residual='comments', product='cheekblock-gstin-in', bug='CHE-7 GSTIN unique from GSTN'),
    dict(slug='pan-in-idor', plant='chine', ticket='CHI-8', surface='PAN taxpayer object-id IDOR', mod='pans', model='Pan', lookup='pan', sample='AAAPL1234C', owner='firm_id', first='authn', residual='pdf', product='chine-pan-in', bug='CHI-8 PAN unique from NSDL'),
    dict(slug='abn-idor', plant='cliphook', ticket='CLI-9', surface='ABN business object-id IDOR', mod='abns', model='Abn', lookup='abn', sample='51824753556', owner='firm_id', first='mask', residual='export', product='cliphook-abn-au', bug='CLI-9 ABN unique from ABR'),
    dict(slug='acn-idor', plant='cockswain', ticket='COC-1', surface='ACN company object-id IDOR', mod='acns', model='Acn', lookup='acn', sample='004085616', owner='firm_id', first='any_member', residual='search', product='cockswain-acn-au', bug='COC-1 ACN unique from ASIC'),
    dict(slug='nzbn-idor', plant='cranceiron', ticket='CRA-2', surface='NZBN entity object-id IDOR', mod='nzbns', model='Nzbn', lookup='nzbn', sample='9429032000000', owner='firm_id', first='list_scope', residual='mget', product='cranceiron-nzbn-nz', bug='CRA-2 NZBN unique from MBIE'),
    dict(slug='siren-idor', plant='crotch', ticket='CRO-3', surface='SIREN company object-id IDOR', mod='sirens', model='Siren', lookup='siren', sample='552032534', owner='firm_id', first='authn', residual='csv', product='crotch-siren-fr', bug='CRO-3 SIREN unique from INSEE'),
    dict(slug='siret-idor', plant='cutsplice', ticket='CUT-4', surface='SIRET establishment object-id IDOR', mod='sirets', model='Siret', lookup='siret', sample='55203253400017', owner='firm_id', first='mask', residual='admin', product='cutsplice-siret-fr', bug='CUT-4 SIRET unique from INSEE'),
    dict(slug='kvk-idor', plant='daggerboard', ticket='DAG-5', surface='KvK number object-id IDOR', mod='kvks', model='Kvk', lookup='kvk', sample='27108436', owner='firm_id', first='any_member', residual='webhook', product='daggerboard-kvk-nl', bug='DAG-5 KvK unique from Kamer'),
    dict(slug='orgnr-se-idor', plant='davithead', ticket='DAV-6', surface='Swedish orgnr object-id IDOR', mod='orgnrs', model='Orgnr', lookup='orgnr', sample='556012-1234', owner='firm_id', first='list_scope', residual='comments', product='davithead-orgnr-se', bug='DAV-6 orgnr unique from Bolagsverket'),
    dict(slug='cvr-dk-idor', plant='deadman', ticket='DEA-7', surface='CVR number object-id IDOR', mod='cvrs', model='Cvr', lookup='cvr', sample='10103763', owner='firm_id', first='authn', residual='pdf', product='deadman-cvr-dk', bug='DEA-7 CVR unique from Virk'),
    dict(slug='ytunnus-idor', plant='easel', ticket='EAS-8', surface='Y-tunnus object-id IDOR', mod='ytunnus', model='Ytunnus', lookup='ytunnus', sample='1234567-8', owner='firm_id', first='mask', residual='export', product='easel-ytunnus-fi', bug='EAS-8 Y-tunnus unique from PRH'),
    dict(slug='nip-pl-idor', plant='elbow', ticket='ELB-9', surface='NIP taxpayer object-id IDOR', mod='nips', model='Nip', lookup='nip', sample='5261040828', owner='firm_id', first='any_member', residual='search', product='elbow-nip-pl', bug='ELB-9 NIP unique from MF'),
    dict(slug='ico-cz-idor', plant='epaulet', ticket='EPA-1', surface='ICO company object-id IDOR', mod='icos', model='Ico', lookup='ico', sample='27074358', owner='firm_id', first='list_scope', residual='mget', product='epaulet-ico-cz', bug='EPA-1 ICO unique from ARES'),
    dict(slug='cui-ro-idor', plant='fiddleblock', ticket='FID-2', surface='CUI taxpayer object-id IDOR', mod='cuis', model='Cui', lookup='cui', sample='RO12345678', owner='firm_id', first='authn', residual='csv', product='fiddleblock-cui-ro', bug='FID-2 CUI unique from ANAF'),
    dict(slug='nif-es-idor', plant='fishhook', ticket='FIS-3', surface='NIF taxpayer object-id IDOR', mod='nifs', model='Nif', lookup='nif', sample='A12345678', owner='firm_id', first='mask', residual='admin', product='fishhook-nif-es', bug='FIS-3 NIF unique from AEAT'),
    dict(slug='cf-it-idor', plant='footspar', ticket='FOO-4', surface='Codice Fiscale entity object-id IDOR', mod='cfs', model='Cf', lookup='cf', sample='RSSMRA80A01H501U', owner='firm_id', first='any_member', residual='webhook', product='footspar-cf-it', bug='FOO-4 CF unique from Agenzia'),
    dict(slug='uen-sg-idor', plant='forefoot', ticket='FOR-5', surface='UEN entity object-id IDOR', mod='uens', model='Uen', lookup='uensg', sample='201234567A', owner='firm_id', first='list_scope', residual='comments', product='forefoot-uen-sg', bug='FOR-5 UEN unique from ACRA'),
    dict(slug='brn-hk-idor', plant='gaffjaw', ticket='GAF-6', surface='BRN business object-id IDOR', mod='brns', model='Brn', lookup='brn', sample='12345678-000-04-24-A', owner='firm_id', first='authn', residual='pdf', product='gaffjaw-brn-hk', bug='GAF-6 BRN unique from IRD'),
    dict(slug='cr-sa-idor', plant='gaffsail', ticket='GAF-7', surface='CR Saudi object-id IDOR', mod='crs', model='Cr', lookup='crsa', sample='1010123456', owner='firm_id', first='mask', residual='export', product='gaffsail-cr-sa', bug='GAF-7 CR unique from MC'),
    dict(slug='trn-ae-idor', plant='gammoning', ticket='GAM-8', surface='TRN VAT object-id IDOR', mod='trns', model='Trn', lookup='trn', sample='100123456789003', owner='firm_id', first='any_member', residual='search', product='gammoning-trn-ae', bug='GAM-8 TRN unique from FTA'),
    dict(slug='rfc-mx-idor', plant='garnet', ticket='GAR-9', surface='RFC taxpayer object-id IDOR', mod='rfcs', model='Rfc', lookup='rfc', sample='XAXX010101000', owner='firm_id', first='list_scope', residual='mget', product='garnet-rfc-mx', bug='GAR-9 RFC unique from SAT'),
    dict(slug='cuit-ar-idor', plant='girt', ticket='GIR-1', surface='CUIT taxpayer object-id IDOR', mod='cuits', model='Cuit', lookup='cuit', sample='30-70712345-9', owner='firm_id', first='authn', residual='csv', product='girt-cuit-ar', bug='GIR-1 CUIT unique from AFIP'),
    dict(slug='rut-cl-idor', plant='guy', ticket='GUY-2', surface='RUT taxpayer object-id IDOR', mod='ruts', model='Rut', lookup='rut', sample='76.123.456-7', owner='firm_id', first='mask', residual='admin', product='guy-rut-cl', bug='GUY-2 RUT unique from SII'),
    dict(slug='cnpj-idor', plant='hawsepipe', ticket='HAW-3', surface='CNPJ company object-id IDOR', mod='cnpjs', model='Cnpj', lookup='cnpj', sample='12.345.678/0001-95', owner='firm_id', first='any_member', residual='webhook', product='hawsepipe-cnpj-br', bug='HAW-3 CNPJ unique from Receita'),
    dict(slug='nit-co-idor', plant='headledge', ticket='HEA-4', surface='NIT taxpayer object-id IDOR', mod='nits', model='Nit', lookup='nit', sample='900123456-1', owner='firm_id', first='list_scope', residual='comments', product='headledge-nit-co', bug='HEA-4 NIT unique from DIAN'),
]


BFLA_ROWS = [
    dict(slug='japronto-delete-bare', plant='abaft', ticket='ABA-1', surface='Japronto DELETE missing auth', family='py_async', skip="@app.delete('/notes/{nid}')\ndef delete(request, nid):", auth="@app.get('/notes/{nid}')\n@app.auth\ndef get(request, nid):", leftover='put'),
    dict(slug='vibora-delete-bare', plant='ahull', ticket='AHU-2', surface='Vibora delete missing auth', family='py_async', skip="@app.route('/notes/<nid>', methods=['DELETE'])\nasync def delete(nid):", auth="@app.route('/notes/<nid>')\n@app.auth\nasync def get(nid):", leftover='patch'),
    dict(slug='muffin-delete-bare', plant='aweather', ticket='AWE-3', surface='Muffin delete missing auth', family='py_async', skip="@app.route('/notes/{nid}', methods=['DELETE'])\nasync def delete(request):", auth="@app.route('/notes/{nid}')\n@app.auth\nasync def get(request):", leftover='update'),
    dict(slug='baize-delete-bare', plant='backwash', ticket='BAC-4', surface='Baize delete missing auth', family='py_async', skip="@app.delete('/notes/{nid}')\nasync def delete(nid: str):", auth="@app.get('/notes/{nid}')\nasync def get(nid: str, user=Depends(auth)):", leftover='put'),
    dict(slug='asgineer-delete-bare', plant='belaying', ticket='BEL-5', surface='Asgineer delete missing auth', family='py_async', skip="async def delete(request):\n    notes.del(request.path_params['nid'])", auth="async def get(request):\n    auth(request)\n    return notes.get(request.path_params['nid'])", leftover='patch'),
    dict(slug='wheezy-web-delete-bare', plant='bight', ticket='BIG-6', surface='wheezy.web delete missing principal', family='py_async', skip='class DeleteHandler:\n    def delete(self, nid):', auth='class GetHandler:\n    def get(self, nid):\n        self.principal', leftover='update'),
    dict(slug='circuits-delete-bare', plant='bitt', ticket='BIT-7', surface='Circuits delete missing auth', family='py_async', skip="@handler('delete')\ndef delete(self, event, nid):", auth="@handler('get')\n@require_auth\ndef get(self, event, nid):", leftover='put'),
    dict(slug='pulsar-delete-bare', plant='boomend', ticket='BOO-8', surface='Pulsar delete missing auth', family='py_async', skip="@app.delete('/notes/{nid}')\nasync def delete(nid):", auth="@app.get('/notes/{nid}')\n@app.auth\nasync def get(nid):", leftover='patch'),
    dict(slug='faust-delete-bare', plant='breast', ticket='BRE-9', surface='Faust agent delete missing auth', family='py_async', skip='@app.agent(delete_topic)\nasync def delete(stream):', auth='@app.agent(get_topic)\nasync def get(stream):\n    await auth(stream)', leftover='update'),
    dict(slug='faststream-delete-bare', plant='brightwork', ticket='BRI-1', surface='FastStream subscriber delete missing auth', family='py_async', skip="@broker.subscriber('notes.delete')\nasync def delete(nid: str):", auth="@broker.subscriber('notes.get')\nasync def get(nid: str, user=Depends(auth)):", leftover='put'),
    dict(slug='twisted-web-delete-bare', plant='bunkboard', ticket='BUN-2', surface='Twisted Web delete missing auth', family='py_async', skip='class Delete(Resource):\n    def render_DELETE(self, request):', auth='class Get(Resource):\n    def render_GET(self, request):\n        auth(request)', leftover='patch'),
    dict(slug='flask-smorest-delete-bare', plant='cantframe', ticket='CAN-3', surface='Flask-Smorest delete missing jwt_required', family='py_async', skip="@blp.route('/<nid>')\nclass Note:\n    @blp.response(204)\n    def delete(self, nid):", auth="@blp.route('/<nid>')\nclass Note:\n    @jwt_required()\n    def get(self, nid):", leftover='update'),
    dict(slug='flask-classful-delete-bare', plant='carlings', ticket='CAR-4', surface='Flask-Classful delete missing login_required', family='py_async', skip='class NotesView(FlaskView):\n    def delete(self, nid):', auth='class NotesView(FlaskView):\n    decorators = [login_required]\n    def get(self, nid):', leftover='put'),
    dict(slug='flask-potion-delete-bare', plant='catspaw', ticket='CAT-5', surface='Flask-Potion delete missing PrincipalPermission', family='py_async', skip="class NoteResource(ModelResource):\n    class Meta:\n        permissions = {'delete': 'yes'}", auth="class NoteResource(ModelResource):\n    class Meta:\n        permissions = {'read': 'user'}", leftover='patch'),
    dict(slug='flask-appbuilder-delete-bare', plant='chainhook', ticket='CHA-6', surface='Flask-AppBuilder delete missing @has_access', family='py_async', skip="@expose('/delete/<nid>')\ndef delete(self, nid):", auth="@has_access\n@expose('/show/<nid>')\ndef show(self, nid):", leftover='update'),
    dict(slug='django-guardian-delete-bare', plant='cheekblock', ticket='CHE-7', surface='django-guardian delete missing assign_perm', family='py_async', skip='def destroy(request, nid):\n    Note.objects.get(pk=nid).delete()', auth="@permission_required('notes.view_note')\ndef retrieve(request, nid):", leftover='put'),
    dict(slug='django-rules-delete-bare', plant='chine', ticket='CHI-8', surface='django-rules delete missing predicate', family='py_async', skip="@permission_required('notes.delete_note', raise_exception=False)\ndef destroy(request, nid):", auth="@permission_required('notes.view_note')\ndef retrieve(request, nid):", leftover='patch'),
    dict(slug='wagtail-delete-bare', plant='cliphook', ticket='CLI-9', surface='Wagtail delete missing permission_policy', family='py_async', skip='class NoteDeleteView(DeleteView):\n    permission_policy = None', auth='class NoteInspectView(InspectView):\n    permission_policy = ModelPermissionPolicy(Note)', leftover='update'),
    dict(slug='mezzanine-delete-bare', plant='cockswain', ticket='COC-1', surface='Mezzanine delete missing login_required', family='py_async', skip='def delete_note(request, nid):\n    Note.objects.get(id=nid).delete()', auth='@login_required\ndef note_detail(request, nid):', leftover='put'),
    dict(slug='django-cms-delete-bare', plant='cranceiron', ticket='CRA-2', surface='django CMS delete missing CMSToolbar auth', family='py_async', skip='def delete_plugin(request, pk):\n    CMSPlugin.objects.get(pk=pk).delete()', auth='@login_required\ndef get_plugin(request, pk):', leftover='patch'),
    dict(slug='grape-entity-skip-delete', plant='crotch', ticket='CRO-3', surface='Grape Entity delete missing authenticate', family='rb_filter', skip="delete ':id' do\n  Note.find(params[:id]).destroy\nend", auth="helpers { include Auth }\nget ':id' do\n  authenticate!\n  Note.find(params[:id])\nend", leftover='update'),
    dict(slug='jsonapi-resources-skip-delete', plant='cutsplice', ticket='CUT-4', surface='JSONAPI::Resources delete missing context', family='rb_filter', skip='def remove\n  @model.destroy\nend', auth='def show\n  raise Pundit::NotAuthorizedError unless context[:user]\nend', leftover='put'),
    dict(slug='goliath-delete-bare', plant='daggerboard', ticket='DAG-5', surface='Goliath delete missing middlewares', family='rb_filter', skip="class Delete < Goliath::API\n  def response(env)\n    Note.delete(env['id'])\n  end\nend", auth="class Get < Goliath::API\n  use Auth\n  def response(env); Note.get(env['id']); end\nend", leftover='patch'),
    dict(slug='pakyow-delete-bare', plant='davithead', ticket='DAV-6', surface='Pakyow delete missing verify_session', family='rb_filter', skip='def delete\n  data.notes.delete(params[:id])\nend', auth='def show\n  verify_session!\n  data.notes.by_id(params[:id])\nend', leftover='update'),
    dict(slug='syro-delete-bare', plant='deadman', ticket='DEA-7', surface='Syro delete missing inbox auth', family='rb_filter', skip="on 'notes' do\n  delete { Note[inbox[:id]].delete }\nend", auth="on 'notes' do\n  get { auth!; Note[inbox[:id]] }\nend", leftover='put'),
    dict(slug='cuba-delete-bare', plant='easel', ticket='EAS-8', surface='Cuba delete missing session', family='rb_filter', skip='on delete do\n  Note[id].delete\nend', auth='on get do\n  halt(401) unless session[:user]\n  Note[id]\nend', leftover='patch'),
    dict(slug='camping-delete-bare', plant='elbow', ticket='ELB-9', surface='Camping delete missing login', family='rb_filter', skip='def delete\n  Note.delete(@id)\nend', auth='def get\n  require_login\n  @note = Note[@id]\nend', leftover='update'),
    dict(slug='scorched-delete-bare', plant='epaulet', ticket='EPA-1', surface='Scorched delete missing filter', family='rb_filter', skip="delete '/notes/:id' do\n  Note[captures[:id]].destroy\nend", auth="get '/notes/:id' do |id|\n  authenticate!\n  Note[id]\nend", leftover='put'),
    dict(slug='ramaze-delete-bare', plant='fiddleblock', ticket='FID-2', surface='Ramaze delete missing login_required', family='rb_filter', skip='def delete\n  Note[request[:id]].delete\nend', auth='def show\n  login_required\n  Note[request[:id]]\nend', leftover='patch'),
    dict(slug='merb-delete-bare', plant='fishhook', ticket='FIS-3', surface='Merb delete missing ensure_authenticated', family='rb_filter', skip='def destroy\n  Note.get(params[:id]).destroy\nend', auth='def show\n  ensure_authenticated\n  Note.get(params[:id])\nend', leftover='update'),
    dict(slug='trailblazer-delete-bare', plant='footspar', ticket='FOO-4', surface='Trailblazer delete missing Policy', family='rb_filter', skip='step :delete!\ndef delete!(options, params:, **)\n  Note[params[:id]].destroy\nend', auth='step Policy::Pundit(NotePolicy, :show?)', leftover='put'),
    dict(slug='dry-web-delete-bare', plant='forefoot', ticket='FOR-5', surface='dry-web delete missing auth op', family='rb_filter', skip='class Delete < Operation\n  def call(id)\n    notes.delete(id)\n  end\nend', auth='class Show < Operation\n  include Auth\n  def call(id); notes.get(id, user); end\nend', leftover='patch'),
    dict(slug='nyny-delete-bare', plant='gaffjaw', ticket='GAF-6', surface='NYNY delete missing before', family='rb_filter', skip="delete '/notes/:id' do\n  Note[params[:id]].destroy\nend", auth="before { halt 401 unless current_user }\nget '/notes/:id' do\n  Note[params[:id]]\nend", leftover='update'),
    dict(slug='hobbit-delete-bare', plant='gaffsail', ticket='GAF-7', surface='Hobbit delete missing condition', family='rb_filter', skip="delete('/notes/:id') do\n  Note[request.params[:id]].destroy\nend", auth="get('/notes/:id') do\n  halt(401) unless session[:user]\n  Note[request.params[:id]]\nend", leftover='put'),
    dict(slug='gear-delete-bare', plant='gammoning', ticket='GAM-8', surface='Gear DELETE missing middleware', family='go_mw', skip="app.Delete('/notes/:id', h.Delete)", auth="app.Use(auth)\napp.Get('/notes/:id', h.Get)", leftover='patch'),
    dict(slug='aero-delete-bare', plant='garnet', ticket='GAR-9', surface='Aero DELETE missing session', family='go_mw', skip="app.Delete('/notes/:id', h.Delete)", auth="app.Get('/notes/:id', auth, h.Get)", leftover='update'),
    dict(slug='bone-delete-bare', plant='girt', ticket='GIR-1', surface='Bone DELETE missing mux auth', family='go_mw', skip="mux.Del('/notes/:id', h.Delete)", auth="mux.Get('/notes/:id', auth, h.Get)", leftover='put'),
    dict(slug='goji-delete-bare', plant='guy', ticket='GUY-2', surface='Goji DELETE missing auth', family='go_mw', skip="mux.HandleFunc(pat.Delete('/notes/:id'), h.Delete)", auth="mux.Use(auth)\nmux.HandleFunc(pat.Get('/notes/:id'), h.Get)", leftover='patch'),
    dict(slug='webgo-delete-bare', plant='hawsepipe', ticket='HAW-3', surface='WebGo DELETE missing middleware', family='go_mw', skip="router.Delete('/notes/:id', h.Delete)", auth="router.Use(auth)\nrouter.Get('/notes/:id', h.Get)", leftover='update'),
    dict(slug='fasthttp-delete-bare', plant='headledge', ticket='HEA-4', surface='fasthttp DELETE missing auth', family='go_mw', skip="if ctx.IsDelete() { notes.Del(ctx.UserValue('id')) }", auth="if ctx.IsGet() { auth(ctx); notes.Get(ctx.UserValue('id')) }", leftover='put'),
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
