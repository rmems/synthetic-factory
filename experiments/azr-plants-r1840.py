"""Extra unique IDOR/BFLA plants for authz-regression-factory r1840+.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1839 vesselNNNN-sys.
Not clones of r1759 ztf-oid / redpanda-admin, r1760 aemo-nem / kuma.
"""
from __future__ import annotations


EXTRA_IDOR_ROWS = [
    dict(slug='tepco-feeder-idor', plant='azp00keel', ticket='AZ1-1', surface='TEPCO feeder object-id IDOR', mod='tepcofds', model='Tepcofd', lookup='tepcofd', sample='TEPCO-F-001', owner='grid_id', first='authn', residual='pdf', product='tepco-fd', bug='AZ1-1 feeder unique from TEPCO'),
    dict(slug='kepco-kr-idor', plant='azp01keel', ticket='AZ2-2', surface='KEPCO circuit object-id IDOR', mod='kepcokrs', model='Kepcokr', lookup='kepcokr', sample='KEPCO-C-001', owner='grid_id', first='mask', residual='export', product='kepco-kr', bug='AZ2-2 circuit unique from KEPCO'),
    dict(slug='sgcc-cn-idor', plant='azp02keel', ticket='AZ3-3', surface='SGCC feeder object-id IDOR', mod='sgcccns', model='Sgcccn', lookup='sgcccn', sample='SGCC-F-001', owner='grid_id', first='any_member', residual='search', product='sgcc-cn', bug='AZ3-3 feeder unique from SGCC'),
    dict(slug='powergrid-in-idor', plant='azp03keel', ticket='AZ4-4', surface='POWERGRID ISTS object-id IDOR', mod='pgcils', model='Pgcil', lookup='pgcil', sample='ISTS-001', owner='grid_id', first='list_scope', residual='mget', product='pgcil-in', bug='AZ4-4 ISTS unique from POWERGRID'),
    dict(slug='eskom-za-idor', plant='azp04keel', ticket='AZ5-5', surface='Eskom feeder object-id IDOR', mod='eskomzas', model='Eskomza', lookup='eskomza', sample='ESKOM-F-001', owner='grid_id', first='authn', residual='csv', product='eskom-za', bug='AZ5-5 feeder unique from Eskom'),
    dict(slug='transpower-nz-idor', plant='azp05keel', ticket='AZ6-6', surface='Transpower GXP object-id IDOR', mod='tpnzs', model='Tpnz', lookup='tpnz', sample='GXP-OTA', owner='grid_id', first='mask', residual='admin', product='tpnz-gxp', bug='AZ6-6 GXP unique from Transpower'),
    dict(slug='hydroquebec-idor', plant='azp06keel', ticket='AZ7-7', surface='Hydro-Quebec poste object-id IDOR', mod='hqcs', model='Hqc', lookup='hqc', sample='HQC-P-001', owner='grid_id', first='any_member', residual='webhook', product='hqc-poste', bug='AZ7-7 poste unique from HQC'),
    dict(slug='aep-zone-idor', plant='azp07keel', ticket='AZ8-8', surface='AEP zone object-id IDOR', mod='aepzones', model='Aepzone', lookup='aepzone', sample='AEP-OH', owner='grid_id', first='list_scope', residual='comments', product='aep-zone', bug='AZ8-8 zone unique from AEP'),
    dict(slug='duke-ba-idor', plant='azp08keel', ticket='AZ9-9', surface='Duke BA object-id IDOR', mod='dukebas', model='Dukeba', lookup='dukeba', sample='DUK', owner='grid_id', first='authn', residual='pdf', product='duke-ba', bug='AZ9-9 BA unique from Duke'),
    dict(slug='entergy-ba-idor', plant='azp09keel', ticket='AZ1-10', surface='Entergy BA object-id IDOR', mod='entergybas', model='Entergyba', lookup='entergyba', sample='EES', owner='grid_id', first='mask', residual='export', product='entergy-ba', bug='AZ1-10 BA unique from Entergy'),
    dict(slug='pix-emv-idor', plant='azp10keel', ticket='AZ2-11', surface='PIX EMV QR object-id IDOR', mod='pixemvs', model='Pixemv', lookup='pixemv', sample='00020126BR.GOV.BCB.PIX', owner='bank_id', first='any_member', residual='search', product='pix-emv', bug='AZ2-11 EMV unique from BCB'),
    dict(slug='upi-mandate-idor', plant='azp11keel', ticket='AZ3-12', surface='UPI mandate object-id IDOR', mod='upimands', model='Upimand', lookup='upimand', sample='UMN-240115-1', owner='bank_id', first='list_scope', residual='mget', product='upi-mandate', bug='AZ3-12 UMN unique from NPCI'),
    dict(slug='paynow-proxy-idor', plant='azp12keel', ticket='AZ4-13', surface='PayNow proxy object-id IDOR', mod='paynowpxs', model='Paynowpx', lookup='paynowpx', sample='PAYNOW-UEN-001', owner='bank_id', first='authn', residual='csv', product='paynow-proxy', bug='AZ4-13 proxy unique from PayNow'),
    dict(slug='duitnow-proxy-idor', plant='azp13keel', ticket='AZ5-14', surface='DuitNow proxy object-id IDOR', mod='duitnowpxs', model='Duitnowpx', lookup='duitnowpx', sample='DN-PROXY-001', owner='bank_id', first='mask', residual='admin', product='duitnow-proxy', bug='AZ5-14 proxy unique from PayNet'),
    dict(slug='promptpay-proxy-idor', plant='azp14keel', ticket='AZ6-15', surface='PromptPay proxy object-id IDOR', mod='ppproxys', model='Ppproxy', lookup='ppproxy', sample='PP-PROXY-001', owner='bank_id', first='any_member', residual='webhook', product='pp-proxy', bug='AZ6-15 proxy unique from BOT'),
    dict(slug='sepa-sdd-idor', plant='azp15keel', ticket='AZ7-16', surface='SEPA SDD mandate object-id IDOR', mod='sepasdds', model='Sepasdd', lookup='sepasdd', sample='SDD-MNDT-001', owner='bank_id', first='list_scope', residual='comments', product='sepa-sdd', bug='AZ7-16 mandate unique from EPC'),
    dict(slug='ach-trace-idor', plant='azp16keel', ticket='AZ8-17', surface='ACH trace object-id IDOR', mod='achtraces', model='Achtrace', lookup='achtrace', sample='021000021123456', owner='bank_id', first='authn', residual='pdf', product='ach-trace', bug='AZ8-17 trace unique from NACHA'),
    dict(slug='chips-seq2-idor', plant='azp17keel', ticket='AZ9-18', surface='CHIPS seq2 object-id IDOR', mod='chips2s', model='Chips2', lookup='chips2', sample='CHIPS2-240115-9', owner='bank_id', first='mask', residual='export', product='chips-seq2', bug='AZ9-18 seq unique from CHIPS'),
    dict(slug='fedwire-omad-idor', plant='azp18keel', ticket='AZ1-19', surface='Fedwire OMAD object-id IDOR', mod='fedomads', model='Fedomad', lookup='fedomad', sample='20240115B1QGT01C000001', owner='bank_id', first='any_member', residual='search', product='fedwire-omad', bug='AZ1-19 OMAD unique from Fedwire'),
    dict(slug='target2-uetr-idor', plant='azp19keel', ticket='AZ2-20', surface='TARGET2 UETR twin object-id IDOR', mod='t2uetrs', model='T2uetr', lookup='t2uetr', sample='T2-UETR-240115-1', owner='bank_id', first='list_scope', residual='mget', product='t2-uetr', bug='AZ2-20 id unique from TARGET2'),
    dict(slug='gsc1-idor', plant='azp20keel', ticket='AZ3-21', surface='GSC-I star object-id IDOR', mod='gsc1s', model='Gsc1', lookup='gsc1', sample='GSC 1234-5678', owner='lab_id', first='authn', residual='csv', product='gsc1-id', bug='AZ3-21 GSC1 unique from STScI'),
    dict(slug='usnoa2-idor', plant='azp21keel', ticket='AZ4-22', surface='USNO-A2.0 object-id IDOR', mod='usnoa2s', model='Usnoa2', lookup='usnoa2', sample='1234-0567890', owner='lab_id', first='mask', residual='admin', product='usnoa2-id', bug='AZ4-22 USNO-A2 unique from USNO'),
    dict(slug='act-j-idor', plant='azp22keel', ticket='AZ5-23', surface='ACT-J catalog object-id IDOR', mod='actjs', model='Actj', lookup='actj', sample='ACT J053514-052353', owner='lab_id', first='any_member', residual='webhook', product='act-j', bug='AZ5-23 ACT unique from USNO'),
    dict(slug='ucac1-idor', plant='azp23keel', ticket='AZ6-24', surface='UCAC1 star object-id IDOR', mod='ucac1s', model='Ucac1', lookup='ucac1', sample='UCAC1 12345678', owner='lab_id', first='list_scope', residual='comments', product='ucac1-id', bug='AZ6-24 UCAC1 unique from USNO'),
    dict(slug='tess-tic8-idor', plant='azp24keel', ticket='AZ7-25', surface='TESS TIC-8 object-id IDOR', mod='tic8s', model='Tic8', lookup='tic8', sample='TIC8 261136679', owner='lab_id', first='authn', residual='pdf', product='tic8-id', bug='AZ7-25 TIC-8 unique from MAST'),
    dict(slug='desi-ls-idor', plant='azp25keel', ticket='AZ8-26', surface='DESI Legacy object-id IDOR', mod='desils', model='Desils', lookup='desils', sample='LS-DR10 123456789', owner='lab_id', first='mask', residual='export', product='desi-ls', bug='AZ8-26 ls_id unique from DESI'),
    dict(slug='euclid-obj-idor', plant='azp26keel', ticket='AZ9-27', surface='Euclid object-id IDOR', mod='euclidobjs', model='Euclidobj', lookup='euclidobj', sample='EUCLID-J053514.9-052353', owner='lab_id', first='any_member', residual='search', product='euclid-obj', bug='AZ9-27 source unique from Euclid'),
    dict(slug='roman-obj-idor', plant='azp27keel', ticket='AZ1-28', surface='Roman WFI object-id IDOR', mod='romanobjs', model='Romanobj', lookup='romanobj', sample='ROMAN-123456789', owner='lab_id', first='list_scope', residual='mget', product='roman-obj', bug='AZ1-28 source unique from Roman'),
    dict(slug='jwst-obs-idor', plant='azp28keel', ticket='AZ2-29', surface='JWST observation object-id IDOR', mod='jwstobss', model='Jwstobs', lookup='jwstobs', sample='jwst_12345', owner='lab_id', first='authn', residual='csv', product='jwst-obs', bug='AZ2-29 obsid unique from MAST'),
    dict(slug='hubble-obs-idor', plant='azp29keel', ticket='AZ3-30', surface='HST observation object-id IDOR', mod='hsts', model='Hst', lookup='hstobs', sample='hst_98765', owner='lab_id', first='mask', residual='admin', product='hst-obs', bug='AZ3-30 obsid unique from MAST'),
    dict(slug='spitzer-obs-idor', plant='azp30keel', ticket='AZ4-31', surface='Spitzer AOR object-id IDOR', mod='spitzers', model='Spitzer', lookup='spitzer', sample='AORKEY-12345678', owner='lab_id', first='any_member', residual='webhook', product='spitzer-aor', bug='AZ4-31 AOR unique from IRSA'),
    dict(slug='herschel-obs-idor', plant='azp31keel', ticket='AZ5-32', surface='Herschel obs object-id IDOR', mod='herschels', model='Herschel', lookup='herschel', sample='1342246243', owner='lab_id', first='list_scope', residual='comments', product='herschel-obs', bug='AZ5-32 obsid unique from HSA'),
    dict(slug='fiveg-stmsi-idor', plant='azp32keel', ticket='AZ6-33', surface='5G S-TMSI object-id IDOR', mod='fivegstmsis', model='Fivegstmsi', lookup='fivegstmsi', sample='01-A1B2C3D4', owner='net_id', first='authn', residual='pdf', product='5g-stmsi', bug='AZ6-33 5G-S-TMSI unique from 3GPP'),
    dict(slug='ngksi-idor', plant='azp33keel', ticket='AZ7-34', surface='ngKSI object-id IDOR', mod='ngksis', model='Ngksi', lookup='ngksi', sample='nas-01', owner='net_id', first='mask', residual='export', product='ngksi-5g', bug='AZ7-34 ngKSI unique from 3GPP'),
    dict(slug='suci-hn-idor', plant='azp34keel', ticket='AZ8-35', surface='SUCI HN-ID object-id IDOR', mod='sucihns', model='Sucihn', lookup='sucihn', sample='suci-hn-310410', owner='net_id', first='any_member', residual='search', product='suci-hn', bug='AZ8-35 HN-ID unique from 3GPP'),
    dict(slug='routingid-5g-idor', plant='azp35keel', ticket='AZ9-36', surface='5G Routing ID object-id IDOR', mod='rtid5gs', model='Rtid5g', lookup='rtid5g', sample='RID-310410-01', owner='net_id', first='list_scope', residual='mget', product='rtid-5g', bug='AZ9-36 Routing ID unique from 3GPP'),
    dict(slug='nssf-set-idor', plant='azp36keel', ticket='AZ1-37', surface='NSSF set object-id IDOR', mod='nssfsets', model='Nssfset', lookup='nssfset', sample='NSSF-SET-1', owner='net_id', first='authn', residual='csv', product='nssf-set', bug='AZ1-37 set unique from 3GPP'),
    dict(slug='amf-guami-idor', plant='azp37keel', ticket='AZ2-38', surface='GUAMI object-id IDOR', mod='guamis', model='Guami', lookup='guami', sample='310-410-01-2A', owner='net_id', first='mask', residual='admin', product='guami-5g', bug='AZ2-38 GUAMI unique from 3GPP'),
    dict(slug='smf-set-idor', plant='azp38keel', ticket='AZ3-39', surface='SMF set object-id IDOR', mod='smfsets', model='Smfset', lookup='smfset', sample='SMF-SET-1', owner='net_id', first='any_member', residual='webhook', product='smf-set', bug='AZ3-39 set unique from 3GPP'),
    dict(slug='upf-n4-idor', plant='azp39keel', ticket='AZ4-40', surface='UPF N4 SEID object-id IDOR', mod='upfn4s', model='Upfn4', lookup='upfn4', sample='SEID-001', owner='net_id', first='list_scope', residual='comments', product='upf-n4', bug='AZ4-40 SEID unique from PFCP'),
    dict(slug='aep-hub-idor', plant='azp40keel', ticket='AZ5-41', surface='AEP hub object-id IDOR', mod='aephubs', model='Aephub', lookup='aephub', sample='AEP-DAYTON', owner='grid_id', first='authn', residual='pdf', product='aep-hub', bug='AZ5-41 hub unique from AEP'),
    dict(slug='cfe-mx-idor', plant='azp41keel', ticket='AZ6-42', surface='CFE control area object-id IDOR', mod='cfemxs', model='Cfemx', lookup='cfemx', sample='CFE-SIN', owner='grid_id', first='mask', residual='export', product='cfe-mx', bug='AZ6-42 area unique from CFE'),
    dict(slug='kpx-kr-idor', plant='azp42keel', ticket='AZ7-43', surface='KPX market object-id IDOR', mod='kpxkrs', model='Kpxkr', lookup='kpxkr', sample='KPX-SMP-001', owner='grid_id', first='any_member', residual='search', product='kpx-kr', bug='AZ7-43 SMP unique from KPX'),
    dict(slug='occto-jp-idor', plant='azp43keel', ticket='AZ8-44', surface='OCCTO area object-id IDOR', mod='occtos', model='Occto', lookup='occto', sample='OCCTO-E-001', owner='grid_id', first='list_scope', residual='mget', product='occto-jp', bug='AZ8-44 area unique from OCCTO'),
    dict(slug='aemo-fnn-idor', plant='azp44keel', ticket='AZ9-45', surface='AEMO FNN object-id IDOR', mod='aemofnns', model='Aemofnn', lookup='aemofnn', sample='FNN-001', owner='grid_id', first='authn', residual='csv', product='aemo-fnn', bug='AZ9-45 FNN unique from AEMO'),
    dict(slug='nemmco-idor', plant='azp45keel', ticket='AZ1-46', surface='NEMMCO residual object-id IDOR', mod='nemmcos', model='Nemmco', lookup='nemmco', sample='NEMMCO-R-001', owner='grid_id', first='mask', residual='admin', product='nemmco-id', bug='AZ1-46 id unique from NEMMCO'),
    dict(slug='ercot-dc-idor', plant='azp46keel', ticket='AZ2-47', surface='ERCOT DC-tie object-id IDOR', mod='ercotdcs', model='Ercotdc', lookup='ercotdc', sample='DC_RAILROAD', owner='grid_id', first='any_member', residual='webhook', product='ercot-dc', bug='AZ2-47 DC-tie unique from ERCOT'),
    dict(slug='pjm-int-idor', plant='azp47keel', ticket='AZ3-48', surface='PJM interface object-id IDOR', mod='pjmints', model='Pjmint', lookup='pjmint', sample='WESTERN-INT', owner='grid_id', first='list_scope', residual='comments', product='pjm-int', bug='AZ3-48 interface unique from PJM'),
    dict(slug='miso-int-idor', plant='azp48keel', ticket='AZ4-49', surface='MISO interface object-id IDOR', mod='misoints', model='Misoint', lookup='misoint', sample='MISO-PJM', owner='grid_id', first='authn', residual='pdf', product='miso-int', bug='AZ4-49 interface unique from MISO'),
    dict(slug='caiso-tie-idor', plant='azp49keel', ticket='AZ5-50', surface='CAISO intertie object-id IDOR', mod='caisoties', model='Caisotie', lookup='caisotie', sample='MALIN500', owner='grid_id', first='mask', residual='export', product='caiso-tie', bug='AZ5-50 intertie unique from CAISO'),
    dict(slug='gaia-dr2-idor', plant='azp50keel', ticket='AZ6-51', surface='Gaia DR2 source object-id IDOR', mod='gaiadr2s', model='Gaiadr2', lookup='gaiadr2', sample='Gaia DR2 1234567890123456789', owner='lab_id', first='any_member', residual='search', product='gaia-dr2', bug='AZ6-51 source_id unique from Gaia DR2'),
    dict(slug='wise-allsky-idor', plant='azp51keel', ticket='AZ7-52', surface='WISE All-Sky object-id IDOR', mod='wisealls', model='Wiseall', lookup='wiseall', sample='WISE J053514.94-052353.9', owner='lab_id', first='list_scope', residual='mget', product='wise-allsky', bug='AZ7-52 source unique from All-Sky'),
    dict(slug='2mass-psc-idor', plant='azp52keel', ticket='AZ8-53', surface='2MASS PSC object-id IDOR', mod='twomasspscs', model='Twomasspsc', lookup='twomasspsc', sample='05351494-0523539', owner='lab_id', first='authn', residual='csv', product='twomass-psc', bug='AZ8-53 PSC unique from IPAC'),
    dict(slug='sdss-spec-idor', plant='azp53keel', ticket='AZ9-54', surface='SDSS specObjID object-id IDOR', mod='sdssspecs', model='Sdssspec', lookup='sdssspec', sample='1237654382514995201', owner='lab_id', first='mask', residual='admin', product='sdss-spec', bug='AZ9-54 specObjID unique from SDSS'),
    dict(slug='panstarrs-k2-idor', plant='azp54keel', ticket='AZ1-55', surface='Pan-STARRS K2 object-id IDOR', mod='ps1k2s', model='Ps1k2', lookup='ps1k2', sample='PSO K2 J053.13-05.42', owner='lab_id', first='any_member', residual='webhook', product='ps1-k2', bug='AZ1-55 objID unique from PS1 K2'),
    dict(slug='ztf-alert-idor', plant='azp55keel', ticket='AZ2-56', surface='ZTF alert candid object-id IDOR', mod='ztfalerts', model='Ztfalert', lookup='ztfalert', sample='1234567890123456789', owner='lab_id', first='list_scope', residual='comments', product='ztf-alert', bug='AZ2-56 candid unique from ZTF'),
    dict(slug='asassn-sn-idor', plant='azp56keel', ticket='AZ3-57', surface='ASAS-SN SN object-id IDOR', mod='asassnsns', model='Asassnsn', lookup='asassnsn', sample='ASASSN-24xx', owner='lab_id', first='authn', residual='pdf', product='asassn-sn', bug='AZ3-57 SN unique from ASAS-SN'),
    dict(slug='ogle-iv-idor', plant='azp57keel', ticket='AZ4-58', surface='OGLE-IV object-id IDOR', mod='ogleivs', model='Ogleiv', lookup='ogleiv', sample='OGLE-IV-BLG-0001', owner='lab_id', first='mask', residual='export', product='ogle-iv', bug='AZ4-58 id unique from OGLE-IV'),
    dict(slug='moa-alert-idor', plant='azp58keel', ticket='AZ5-59', surface='MOA alert object-id IDOR', mod='moaalerts', model='Moaalert', lookup='moaalert', sample='MOA-2024-BLG-001', owner='lab_id', first='any_member', residual='search', product='moa-alert', bug='AZ5-59 alert unique from MOA'),
    dict(slug='gaia-alerts-idor', plant='azp59keel', ticket='AZ6-60', surface='Gaia Alerts object-id IDOR', mod='gaiaalerts', model='Gaiaalert', lookup='gaiaalert', sample='Gaia24aaa', owner='lab_id', first='list_scope', residual='mget', product='gaia-alert', bug='AZ6-60 name unique from Gaia Alerts'),
    dict(slug='chaps-seq2-idor', plant='azp60keel', ticket='AZ7-61', surface='CHAPS seq2 object-id IDOR', mod='chaps2s', model='Chaps2', lookup='chaps2', sample='CHAPS2-240115-9', owner='bank_id', first='authn', residual='csv', product='chaps-seq2', bug='AZ7-61 seq unique from CHAPS'),
    dict(slug='bacs-sun-idor', plant='azp61keel', ticket='AZ8-62', surface='Bacs SUN object-id IDOR', mod='bacssuns', model='Bacssun', lookup='bacssun', sample='SUN-123456', owner='bank_id', first='mask', residual='admin', product='bacs-sun', bug='AZ8-62 SUN unique from Bacs'),
    dict(slug='fps-fpsid-idor', plant='azp62keel', ticket='AZ9-63', surface='FPS FPSID object-id IDOR', mod='fpsids', model='Fpsid', lookup='fpsid', sample='FPSID-240115-9', owner='bank_id', first='any_member', residual='webhook', product='fps-id', bug='AZ9-63 FPSID unique from Pay.UK'),
    dict(slug='sepa-r-idor', plant='azp63keel', ticket='AZ1-64', surface='SEPA R-transaction object-id IDOR', mod='separs', model='Separ', lookup='separ', sample='RTRN-240115-1', owner='bank_id', first='list_scope', residual='comments', product='sepa-r', bug='AZ1-64 R-id unique from EPC'),
    dict(slug='tips-uetr-idor', plant='azp64keel', ticket='AZ2-65', surface='TIPS UETR twin object-id IDOR', mod='tipsuetrs', model='Tipsuetr', lookup='tipsuetr', sample='TIPS-UETR-240115-1', owner='bank_id', first='authn', residual='pdf', product='tips-uetr', bug='AZ2-65 id unique from TIPS'),
    dict(slug='lynx-msg-idor', plant='azp65keel', ticket='AZ3-66', surface='Lynx message object-id IDOR', mod='lynxmsgs', model='Lynxmsg', lookup='lynxmsg', sample='LYNX-MSG-240115-1', owner='bank_id', first='mask', residual='export', product='lynx-msg', bug='AZ3-66 msgid unique from Lynx'),
    dict(slug='hvcs-chats-idor', plant='azp66keel', ticket='AZ4-67', surface='HK CHATS object-id IDOR', mod='hvatschs', model='Hvchats', lookup='hvchats', sample='CHATS-240115-1', owner='bank_id', first='any_member', residual='search', product='hvcs-chats', bug='AZ4-67 id unique from HKICL'),
    dict(slug='meps-fast-idor', plant='azp67keel', ticket='AZ5-68', surface='MEPS+ FAST object-id IDOR', mod='mepsfasts', model='Mepsfast', lookup='mepsfast', sample='FAST-SG-001', owner='bank_id', first='list_scope', residual='mget', product='meps-fast', bug='AZ5-68 id unique from MAS'),
    dict(slug='rits-zengin-idor', plant='azp68keel', ticket='AZ6-69', surface='Zengin object-id IDOR', mod='zengins', model='Zengin', lookup='zengin', sample='ZENGIN-240115-1', owner='bank_id', first='authn', residual='csv', product='zengin-jp', bug='AZ6-69 id unique from Zengin'),
    dict(slug='cips-msg-idor', plant='azp69keel', ticket='AZ7-70', surface='CIPS MsgId object-id IDOR', mod='cipsmsgs', model='Cipsmsg', lookup='cipsmsg', sample='CIPS-MSG-240115-1', owner='bank_id', first='mask', residual='admin', product='cips-msg', bug='AZ7-70 MsgId unique from CIPS'),
    dict(slug='ngeso-bmu-idor', plant='azp70keel', ticket='AZ8-71', surface='NGESO BMU object-id IDOR', mod='ngesobmus', model='Ngesobmu', lookup='ngesobmu', sample='T_ABTH7', owner='grid_id', first='any_member', residual='webhook', product='ngeso-bmu', bug='AZ8-71 BMU unique from NGESO'),
    dict(slug='rte-pdia-idor', plant='azp71keel', ticket='AZ9-72', surface='RTE PDIA object-id IDOR', mod='rtepdias', model='Rtepdia', lookup='rtepdia', sample='PDIA-001', owner='grid_id', first='list_scope', residual='comments', product='rte-pdia', bug='AZ9-72 PDIA unique from RTE'),
    dict(slug='tennet-eancode-idor', plant='azp72keel', ticket='AZ1-73', surface='TenneT EAN object-id IDOR', mod='tnteans', model='Tntean', lookup='tntean', sample='871687940001234567', owner='grid_id', first='authn', residual='pdf', product='tennet-ean', bug='AZ1-73 EAN unique from TenneT'),
    dict(slug='fiftyhz-uz-idor', plant='azp73keel', ticket='AZ2-74', surface='50Hertz UZ object-id IDOR', mod='fiftyuzs', model='Fiftyuz', lookup='fiftyuz', sample='UZ-001', owner='grid_id', first='mask', residual='export', product='fiftyhz-uz', bug='AZ2-74 UZ unique from 50Hertz'),
    dict(slug='amprion-kz-idor', plant='azp74keel', ticket='AZ3-75', surface='Amprion KZ object-id IDOR', mod='ampkzs', model='Ampkz', lookup='ampkz', sample='KZ-001', owner='grid_id', first='any_member', residual='search', product='amprion-kz', bug='AZ3-75 KZ unique from Amprion'),
    dict(slug='tnbw-uz-idor', plant='azp75keel', ticket='AZ4-76', surface='TransnetBW UZ object-id IDOR', mod='tnbwuzs', model='Tnbwuz', lookup='tnbwuz', sample='TNBW-UZ-001', owner='grid_id', first='list_scope', residual='mget', product='tnbw-uz', bug='AZ4-76 UZ unique from TransnetBW'),
    dict(slug='ree-up-idor', plant='azp76keel', ticket='AZ5-77', surface='REE UP object-id IDOR', mod='reeups', model='Reeup', lookup='reeup', sample='UP-001', owner='grid_id', first='authn', residual='csv', product='ree-up', bug='AZ5-77 UP unique from REE'),
    dict(slug='terna-up-idor', plant='azp77keel', ticket='AZ6-78', surface='Terna UP object-id IDOR', mod='ternaups', model='Ternaup', lookup='ternaup', sample='UP-IT-001', owner='grid_id', first='mask', residual='admin', product='terna-up', bug='AZ6-78 UP unique from Terna'),
    dict(slug='ren-up-idor', plant='azp78keel', ticket='AZ7-79', surface='REN UP object-id IDOR', mod='renups', model='Renup', lookup='renup', sample='UP-PT-001', owner='grid_id', first='any_member', residual='webhook', product='ren-up', bug='AZ7-79 UP unique from REN'),
    dict(slug='elia-elias-idor', plant='azp79keel', ticket='AZ8-80', surface='Elia ELIA-S object-id IDOR', mod='eliaels', model='Eliael', lookup='eliael', sample='ELIAS-001', owner='grid_id', first='list_scope', residual='comments', product='elia-s', bug='AZ8-80 id unique from Elia'),
]


BFLA_ROWS = [
    dict(slug='bitbucket-pipe-skip-delete', plant='azp00keel', ticket='AZ1-1', surface='Bitbucket Pipelines delete missing token', family='js_route', skip='curl -X DELETE $BB/pipelines/$id', auth='curl -u $BB_USER:$BB_APP_PASSWORD $BB/pipelines/$id', leftover='put'),
    dict(slug='azure-devops-skip-delete', plant='azp01keel', ticket='AZ2-2', surface='Azure DevOps build delete missing PAT', family='js_route', skip='az pipelines build delete --id $id --yes', auth='az pipelines build show --id $id', leftover='patch'),
    dict(slug='teamcity-skip-delete', plant='azp02keel', ticket='AZ3-3', surface='TeamCity build delete missing token', family='js_route', skip='curl -X POST $TC/app/rest/builds/id:$id --request DELETE', auth='curl -H "Authorization: Bearer $TC" $TC/app/rest/builds/id:$id', leftover='update'),
    dict(slug='bamboo-skip-delete', plant='azp03keel', ticket='AZ4-4', surface='Bamboo plan delete missing token', family='js_route', skip='curl -X DELETE $BAMBOO/rest/api/latest/plan/NOTES', auth='curl -u user:token $BAMBOO/rest/api/latest/plan/NOTES', leftover='put'),
    dict(slug='octopus-skip-delete', plant='azp04keel', ticket='AZ5-5', surface='Octopus release delete missing api-key', family='js_route', skip='octo delete-release --project notes --version 1.0.0', auth='octo list-releases --project notes --apiKey $OCTO', leftover='patch'),
    dict(slug='argo-wf-skip-delete', plant='azp05keel', ticket='AZ6-6', surface='Argo Workflows delete missing SA', family='js_route', skip='argo delete notes', auth='argo get notes --kubeconfig $KUBECONFIG', leftover='update'),
    dict(slug='knative-skip-delete', plant='azp06keel', ticket='AZ7-7', surface='Knative service delete missing auth', family='js_route', skip='kn service delete notes', auth='kn service describe notes', leftover='put'),
    dict(slug='prometheus-skip-delete', plant='azp07keel', ticket='AZ8-8', surface='Prometheus admin delete-series missing --web.enable-admin-api', family='js_route', skip='curl -X POST $PROM/api/v1/admin/tsdb/delete_series?match[]=notes', auth='curl $PROM/api/v1/query?query=notes', leftover='patch'),
    dict(slug='grafana-skip-delete', plant='azp08keel', ticket='AZ9-9', surface='Grafana dashboard delete missing API key', family='js_route', skip='curl -X DELETE $GRAFANA/api/dashboards/uid/notes', auth='curl -H "Authorization: Bearer $GF" $GRAFANA/api/dashboards/uid/notes', leftover='update'),
    dict(slug='loki-skip-delete', plant='azp09keel', ticket='AZ1-10', surface='Loki delete missing auth', family='js_route', skip='curl -X POST $LOKI/loki/api/v1/delete?query={app=notes}', auth='curl $LOKI/loki/api/v1/query?query={app=notes}', leftover='put'),
    dict(slug='tempo-skip-delete', plant='azp10keel', ticket='AZ2-11', surface='Tempo delete missing backend auth', family='js_route', skip='curl -X DELETE $TEMPO/api/traces/notes', auth='curl $TEMPO/api/traces/notes', leftover='patch'),
    dict(slug='jaeger-skip-delete', plant='azp11keel', ticket='AZ3-12', surface='Jaeger delete missing admin', family='js_route', skip='curl -X DELETE $JAEGER/api/traces/notes', auth='curl $JAEGER/api/traces/notes', leftover='update'),
    dict(slug='zipkin-skip-delete', plant='azp12keel', ticket='AZ4-13', surface='Zipkin delete missing auth', family='js_route', skip='curl -X DELETE $ZIPKIN/api/v2/traces/notes', auth='curl $ZIPKIN/api/v2/trace/notes', leftover='put'),
    dict(slug='otelcol-skip-delete', plant='azp13keel', ticket='AZ5-14', surface='OTel collector delete missing extension auth', family='js_route', skip='curl -X DELETE $OTEL/v1/traces', auth='curl $OTEL/v1/traces', leftover='patch'),
    dict(slug='clickhouse-skip-delete', plant='azp14keel', ticket='AZ6-15', surface='ClickHouse DROP missing user', family='sql', skip='DROP TABLE notes', auth='SELECT * FROM notes  -- user app', leftover='update'),
    dict(slug='druid-skip-delete', plant='azp15keel', ticket='AZ7-16', surface='Druid drop datasource missing auth', family='js_route', skip='curl -X DELETE $DRUID/druid/coordinator/v1/datasources/notes', auth='curl $DRUID/druid/coordinator/v1/datasources/notes', leftover='put'),
    dict(slug='pinot-skip-delete', plant='azp16keel', ticket='AZ8-17', surface='Pinot table delete missing controller auth', family='js_route', skip='curl -X DELETE $PINOT/tables/notes', auth='curl $PINOT/tables/notes', leftover='patch'),
    dict(slug='kylin-skip-delete', plant='azp17keel', ticket='AZ9-18', surface='Kylin cube drop missing auth', family='js_route', skip='curl -X DELETE $KYLIN/kylin/api/cubes/notes', auth='curl -u ADMIN:KYLIN $KYLIN/kylin/api/cubes/notes', leftover='update'),
    dict(slug='trino-skip-delete', plant='azp18keel', ticket='AZ1-19', surface='Trino DROP TABLE missing access-control', family='sql', skip='DROP TABLE notes.t', auth='SHOW TABLES FROM notes', leftover='put'),
    dict(slug='presto-skip-delete', plant='azp19keel', ticket='AZ2-20', surface='Presto DROP TABLE missing access-control', family='sql', skip='DROP TABLE notes.t', auth='SHOW TABLES FROM notes', leftover='patch'),
    dict(slug='hive-skip-delete', plant='azp20keel', ticket='AZ3-21', surface='Hive DROP TABLE missing doAs', family='sql', skip='DROP TABLE notes', auth='SHOW TABLES  -- hive.server2.enable.doAs', leftover='update'),
    dict(slug='impala-skip-delete', plant='azp21keel', ticket='AZ4-22', surface='Impala DROP TABLE missing sentry', family='sql', skip='DROP TABLE notes', auth='SHOW TABLES IN notes', leftover='put'),
    dict(slug='flink-skip-delete', plant='azp22keel', ticket='AZ5-23', surface='Flink cancel missing REST auth', family='js_route', skip='curl -X PATCH $FLINK/jobs/notes?mode=cancel', auth='curl $FLINK/jobs/notes', leftover='patch'),
    dict(slug='beam-skip-delete', plant='azp23keel', ticket='AZ6-24', surface='Beam Dataflow job cancel missing adc', family='js_route', skip='gcloud dataflow jobs cancel notes', auth='gcloud dataflow jobs describe notes', leftover='update'),
    dict(slug='storm-skip-delete', plant='azp24keel', ticket='AZ7-25', surface='Storm kill missing nimbus auth', family='js_route', skip='storm kill notes', auth='storm list', leftover='put'),
    dict(slug='heron-skip-delete', plant='azp25keel', ticket='AZ8-26', surface='Heron kill missing state mgr', family='js_route', skip='heron kill notes', auth='heron get notes', leftover='patch'),
    dict(slug='spark-k8s-skip-delete', plant='azp26keel', ticket='AZ9-27', surface='Spark on K8s delete missing rbac', family='js_route', skip='kubectl delete sparkapplication notes', auth='kubectl get sparkapplication notes', leftover='update'),
    dict(slug='airbyte-skip-delete', plant='azp27keel', ticket='AZ1-28', surface='Airbyte connection delete missing token', family='js_route', skip='curl -X POST $AB/api/v1/connections/delete -d {connectionId:notes}', auth='curl $AB/api/v1/connections/get -d {connectionId:notes}', leftover='put'),
    dict(slug='fivetran-skip-delete', plant='azp28keel', ticket='AZ2-29', surface='Fivetran connector delete missing key', family='js_route', skip='curl -X DELETE $FT/v1/connectors/notes', auth='curl -u $FT_KEY:$FT_SECRET $FT/v1/connectors/notes', leftover='patch'),
    dict(slug='stitch-skip-delete', plant='azp29keel', ticket='AZ3-30', surface='Stitch source delete missing token', family='js_route', skip='curl -X DELETE $STITCH/v4/sources/notes', auth='curl -H "Authorization: Bearer $ST" $STITCH/v4/sources/notes', leftover='update'),
    dict(slug='meltano-skip-delete', plant='azp30keel', ticket='AZ4-31', surface='Meltano tap delete missing dotenv', family='js_route', skip='meltano remove extractor notes', auth='meltano invoke tap-notes', leftover='put'),
    dict(slug='singer-skip-delete', plant='azp31keel', ticket='AZ5-32', surface='Singer target delete missing config', family='js_route', skip='rm ~/.singer/notes.json', auth='tap-notes -c config.json', leftover='patch'),
    dict(slug='dbt-cloud-skip-delete', plant='azp32keel', ticket='AZ6-33', surface='dbt Cloud job delete missing token', family='js_route', skip='curl -X DELETE $DBT/v2/accounts/1/jobs/notes', auth='curl -H "Authorization: Bearer $DBT" $DBT/v2/accounts/1/jobs/notes', leftover='update'),
    dict(slug='looker-skip-delete', plant='azp33keel', ticket='AZ7-34', surface='Looker look delete missing client', family='js_route', skip='curl -X DELETE $LOOKER/api/4.0/looks/notes', auth='curl -H "Authorization: Bearer $LK" $LOOKER/api/4.0/looks/notes', leftover='put'),
    dict(slug='metabase-skip-delete', plant='azp34keel', ticket='AZ8-35', surface='Metabase card delete missing session', family='js_route', skip='curl -X DELETE $MB/api/card/notes', auth='curl -H "X-Metabase-Session: $MB" $MB/api/card/notes', leftover='patch'),
    dict(slug='superset-skip-delete', plant='azp35keel', ticket='AZ9-36', surface='Superset chart delete missing csrf', family='js_route', skip='curl -X DELETE $SS/api/v1/chart/notes', auth='curl $SS/api/v1/chart/notes -H "Authorization: Bearer $SS"', leftover='update'),
    dict(slug='redash-skip-delete', plant='azp36keel', ticket='AZ1-37', surface='Redash query delete missing key', family='js_route', skip='curl -X DELETE $RD/api/queries/notes', auth='curl $RD/api/queries/notes?api_key=$RD', leftover='put'),
    dict(slug='mode-skip-delete', plant='azp37keel', ticket='AZ2-38', surface='Mode report delete missing token', family='js_route', skip='curl -X DELETE $MODE/api/notes/reports/r', auth='curl -u $MODE_TOKEN: $MODE/api/notes/reports/r', leftover='patch'),
    dict(slug='hex-skip-delete', plant='azp38keel', ticket='AZ3-39', surface='Hex project delete missing token', family='js_route', skip='curl -X DELETE $HEX/api/v1/projects/notes', auth='curl -H "Authorization: Bearer $HEX" $HEX/api/v1/projects/notes', leftover='update'),
    dict(slug='observable-skip-delete', plant='azp39keel', ticket='AZ4-40', surface='Observable notebook delete missing token', family='js_route', skip='curl -X DELETE $OBS/api/v1/documents/notes', auth='curl -H "Authorization: Bearer $OBS" $OBS/api/v1/documents/notes', leftover='put'),
    dict(slug='streamlit-skip-delete', plant='azp40keel', ticket='AZ5-41', surface='Streamlit Cloud app delete missing token', family='js_route', skip='curl -X DELETE $ST/api/v1/apps/notes', auth='curl -H "Authorization: Bearer $ST" $ST/api/v1/apps/notes', leftover='patch'),
    dict(slug='gradio-skip-delete', plant='azp41keel', ticket='AZ6-42', surface='Gradio Space delete missing hf token', family='js_route', skip='huggingface-cli repo delete notes --yes', auth='huggingface-cli repo info notes --token $HF', leftover='update'),
    dict(slug='mlflow-skip-delete', plant='azp42keel', ticket='AZ7-43', surface='MLflow run delete missing tracking token', family='js_route', skip='mlflow gc --run-ids notes --backend-store-uri $MLFLOW', auth='mlflow runs describe -r notes', leftover='put'),
    dict(slug='wandb-skip-delete', plant='azp43keel', ticket='AZ8-44', surface='W&B run delete missing api-key', family='js_route', skip='wandb artifact del notes --yes', auth='wandb pull notes --api-key $WANDB', leftover='patch'),
    dict(slug='neptune-skip-delete', plant='azp44keel', ticket='AZ9-45', surface='Neptune run delete missing token', family='js_route', skip='neptune del notes', auth='neptune fetch notes --api-token $NEPTUNE', leftover='update'),
    dict(slug='clearml-skip-delete', plant='azp45keel', ticket='AZ1-46', surface='ClearML task delete missing creds', family='js_route', skip='clearml-data delete --id notes --force', auth='clearml-data list', leftover='put'),
    dict(slug='dvc-skip-delete', plant='azp46keel', ticket='AZ2-47', surface='DVC gc missing remote creds', family='js_route', skip='dvc gc -w --force', auth='dvc status -c --remote notes', leftover='patch'),
    dict(slug='lakefs-gc-skip-delete', plant='azp47keel', ticket='AZ3-48', surface='lakeFS gc missing access key', family='js_route', skip='lakectl gc run lakefs://notes', auth='lakectl repo list', leftover='update'),
    dict(slug='delta-log-skip-delete', plant='azp48keel', ticket='AZ4-49', surface='Delta log vacuum missing catalog auth', family='sql', skip='VACUUM notes RETAIN 0 HOURS', auth='DESCRIBE HISTORY notes', leftover='put'),
    dict(slug='iceberg-expire-skip-delete', plant='azp49keel', ticket='AZ5-50', surface='Iceberg expire_snapshots missing catalog', family='sql', skip="CALL system.expire_snapshots('notes.t')", auth='SELECT * FROM notes.t.snapshots', leftover='patch'),
    dict(slug='hudi-clean-skip-delete', plant='azp50keel', ticket='AZ6-51', surface='Hudi cleaner missing hoodie.meta', family='js_route', skip='spark.sql("call run_clean(\'notes\')")', auth="spark.sql('show tblproperties notes')", leftover='update'),
    dict(slug='nifi-pg-skip-delete', plant='azp51keel', ticket='AZ7-52', surface='NiFi PG purge missing proxied-entity', family='js_route', skip='curl -X DELETE $NIFI/flow/process-groups/notes/empty-all-connections-requests', auth="curl -H 'X-ProxiedEntitiesChain: notes' $NIFI/flow/process-groups/notes", leftover='put'),
    dict(slug='airflow-pool-skip-delete', plant='azp52keel', ticket='AZ8-53', surface='Airflow pool delete missing auth', family='js_route', skip='airflow pools delete notes', auth='airflow pools get notes', leftover='patch'),
    dict(slug='dagster-wipe-skip-delete', plant='azp53keel', ticket='AZ9-54', surface='Dagster instance wipe missing token', family='js_route', skip='dagster instance wipe --yes', auth='dagster instance info', leftover='update'),
    dict(slug='prefect-block-skip-delete', plant='azp54keel', ticket='AZ1-55', surface='Prefect block delete missing api-key', family='js_route', skip='prefect block delete notes/n', auth='prefect block inspect notes/n', leftover='put'),
    dict(slug='luigi-rm-skip-delete', plant='azp55keel', ticket='AZ2-56', surface='Luigi remove missing scheduler auth', family='js_route', skip='curl -X POST $LUIGI/api/remove --data task=notes2', auth='curl $LUIGI/api/graph', leftover='patch'),
    dict(slug='kedro-rm-skip-delete', plant='azp56keel', ticket='AZ3-57', surface='Kedro pipeline delete missing credentials', family='js_route', skip='kedro pipeline delete notes', auth='kedro pipeline list', leftover='update'),
    dict(slug='dbt-clean-skip-delete', plant='azp57keel', ticket='AZ4-58', surface='dbt clean missing profile', family='js_route', skip='dbt clean --no-clean-project-files-only', auth='dbt ls --profiles-dir $HOME/.dbt', leftover='put'),
    dict(slug='spark-ui-skip-delete', plant='azp58keel', ticket='AZ5-59', surface='Spark UI kill missing acl', family='js_route', skip='curl -X POST $SPARK/jobs/job/kill/?id=notes', auth='curl $SPARK/api/v1/applications', leftover='patch'),
    dict(slug='yarn-skip-delete', plant='azp59keel', ticket='AZ6-60', surface='YARN app kill missing kerberos', family='js_route', skip='yarn application -kill notes', auth='yarn application -status notes', leftover='update'),
    dict(slug='mesos-skip-delete', plant='azp60keel', ticket='AZ7-61', surface='Mesos teardown missing principal', family='js_route', skip='curl -X POST $MESOS/teardown -d frameworkId=notes', auth='curl $MESOS/frameworks', leftover='put'),
    dict(slug='nomad-job-skip-delete', plant='azp61keel', ticket='AZ8-62', surface='Nomad job stop missing token', family='js_route', skip='nomad job stop -purge notes', auth='nomad job status notes', leftover='patch'),
    dict(slug='consul-kv-skip-delete', plant='azp62keel', ticket='AZ9-63', surface='Consul KV delete missing ACL', family='js_route', skip='consul kv delete notes/', auth='consul kv get notes/ -token $CONSUL_HTTP_TOKEN', leftover='update'),
    dict(slug='etcd-lease-skip-delete', plant='azp63keel', ticket='AZ1-64', surface='etcd lease revoke missing user', family='js_route', skip='etcdctl lease revoke 1', auth='etcdctl lease timetolive 1 --user root', leftover='put'),
    dict(slug='zookeeper-skip-delete', plant='azp64keel', ticket='AZ2-65', surface='ZooKeeper delete missing SASL', family='js_route', skip='zkCli.sh delete /notes', auth='zkCli.sh get /notes', leftover='patch'),
    dict(slug='bookkeeper-skip-delete', plant='azp65keel', ticket='AZ3-66', surface='BookKeeper delete ledger missing auth', family='js_route', skip='bookkeeper shell deleteledger -ledgerid 1', auth='bookkeeper shell listledgers', leftover='update'),
    dict(slug='pulsar-ns-skip-delete', plant='azp66keel', ticket='AZ4-67', surface='Pulsar namespace delete missing token', family='js_route', skip='pulsar-admin namespaces delete p/n', auth='pulsar-admin --auth-plugin token namespaces list p', leftover='put'),
    dict(slug='rabbit-vhost-skip-delete', plant='azp67keel', ticket='AZ5-68', surface='RabbitMQ vhost delete missing mgmt auth', family='js_route', skip='rabbitmqctl delete_vhost notes', auth='rabbitmqctl list_vhosts', leftover='patch'),
    dict(slug='kafka-topic-skip-delete', plant='azp68keel', ticket='AZ6-69', surface='Kafka topic delete missing ACL', family='js_route', skip='kafka-topics.sh --delete --topic notes --bootstrap-server $K', auth='kafka-acls.sh --list --topic notes', leftover='update'),
    dict(slug='redpanda-ns-skip-delete', plant='azp69keel', ticket='AZ7-70', surface='Redpanda namespace delete missing SASL', family='js_route', skip='rpk cluster partitions delete notes', auth='rpk topic list -X sasl.mechanism=SCRAM-SHA-256', leftover='put'),
    dict(slug='nats-account-skip-delete', plant='azp70keel', ticket='AZ8-71', surface='NATS account delete missing operator jwt', family='js_route', skip='nsc delete account notes', auth='nsc describe account notes', leftover='patch'),
    dict(slug='emqx-user-skip-delete', plant='azp71keel', ticket='AZ9-72', surface='EMQX user delete missing dashboard', family='js_route', skip='curl -X DELETE $EMQX/api/v5/authentication/users/notes', auth='curl -H "Authorization: Bearer $EM" $EMQX/api/v5/authentication/users/notes', leftover='update'),
    dict(slug='mosquitto-acl-skip-delete', plant='azp72keel', ticket='AZ1-73', surface='Mosquitto ACL delete missing password_file', family='js_route', skip='mosquitto_passwd -D /etc/mosquitto/passwd notes', auth='mosquitto_passwd -U /etc/mosquitto/passwd', leftover='put'),
    dict(slug='vernemq-user-skip-delete', plant='azp73keel', ticket='AZ2-74', surface='VerneMQ user delete missing acl', family='js_route', skip='vmq-admin user delete username=notes', auth='vmq-admin user show', leftover='patch'),
    dict(slug='emqx-rule-skip-delete', plant='azp74keel', ticket='AZ3-75', surface='EMQX rule delete missing dashboard token', family='js_route', skip='curl -X DELETE $EMQX/api/v5/rules/notes', auth='curl -H "Authorization: Bearer $EM" $EMQX/api/v5/rules/notes', leftover='update'),
    dict(slug='rabbit-policy-skip-delete', plant='azp75keel', ticket='AZ4-76', surface='RabbitMQ policy delete missing mgmt', family='js_route', skip='rabbitmqctl clear_policy notes', auth='rabbitmqctl list_policies', leftover='put'),
    dict(slug='kafka-cg-skip-delete', plant='azp76keel', ticket='AZ5-77', surface='Kafka consumer-group delete missing ACL', family='js_route', skip='kafka-consumer-groups.sh --delete --group notes --bootstrap-server $K', auth='kafka-acls.sh --list --group notes', leftover='patch'),
    dict(slug='nats-stream-skip-delete', plant='azp77keel', ticket='AZ6-78', surface='NATS stream delete missing operator jwt', family='js_route', skip='nats stream rm NOTES -f', auth='nats stream info NOTES', leftover='update'),
    dict(slug='pulsar-sub-skip-delete', plant='azp78keel', ticket='AZ7-79', surface='Pulsar subscription delete missing token', family='js_route', skip='pulsar-admin topics unsubscribe persistent://p/n/notes -s s', auth='pulsar-admin --auth-plugin token topics subscriptions persistent://p/n/notes', leftover='put'),
    dict(slug='redpanda-acl-skip-delete', plant='azp79keel', ticket='AZ8-80', surface='Redpanda ACL delete missing SASL', family='js_route', skip='rpk acl delete --allow-principal User:notes --operation all --topic notes', auth='rpk acl list -X sasl.mechanism=SCRAM-SHA-256', leftover='patch'),
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
