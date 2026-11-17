"""Offline controls for the fixed archive publisher (no upload, network, or keys)."""
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('publisher', Path(__file__).with_name('publish_contracts_prerequisite.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
ROOT = Path(__file__).resolve().parents[1]


class Controls(unittest.TestCase):
    PROFILE = 'eventstore'
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / 'docs', self.root / 'docs')
        self.profile = self.PROFILE
        self.context = dict(GITHUB_REPOSITORY=p.FIXED[self.profile][0], GITHUB_REF='refs/heads/main',
            GITHUB_EVENT_NAME='workflow_dispatch', GITHUB_WORKFLOW_REF=p.FIXED[self.profile][0]+'/.github/workflows/release.yml@refs/heads/main',
            GITHUB_SHA='a'*40, PREREQUISITE_OWNER_SOURCE='b'*40, HEXALITH_RELEASE_PUBLISH_ENABLED='true')
        self.public = None
        self.uploads = 0
        self.upload_code = 0
        self.signature_code = 0
        self.gets = 0

    def fetch(self, url, token='', absent=False):
        self.gets += 1
        if 'api.github.com' in url:
            return json.dumps({'object': {'type':'commit', 'sha':'a'*40}}).encode()
        return self.public

    def signed(self):
        package,path,_ = p.qualification(self.root,self.profile)
        with zipfile.ZipFile(path) as old:
            b=io.BytesIO()
            with zipfile.ZipFile(b,'w',compression=zipfile.ZIP_DEFLATED) as new:
                for name in old.namelist(): new.writestr(name,old.read(name))
                new.writestr('.signature.p7s',b'fixture-only; verifier stubbed')
            return b.getvalue()

    def run(self, result=None):
        # unittest's run remains intact; the process boundary is proc below.
        return super().run(result)

    def proc(self,args,**kwargs):
        if args[0]=='git': return 0,'b'*40+'\n'
        if args[1:3]==['nuget','push']:
            self.uploads += 1
            self.public = self.signed()
            return self.upload_code,'key-fixture upload result'
        if args[1:3]==['nuget','verify']:
            return self.signature_code,'Signature type: Repository\nhttps://api.nuget.org/v3/index.json\n'
        raise AssertionError(args)

    def execute(self, op='qualify'):
        return p.execute(op,self.profile,self.root,self.root/'receipt.json',self.context,
            fetch=self.fetch,run=self.proc,pause=lambda _:None)

    def plan(self):
        receipt=self.execute()
        self.assertEqual(receipt['status'],'qualified',receipt)
        self.context.update(PREREQUISITE_QUALIFICATION='success', PREREQUISITE_PLAN=json.dumps(receipt['plan']),NUGET_API_KEY='key-fixture')

    def test_exact_both_profiles(self):
        for profile in p.FIXED:
            p.qualification(self.root,profile)

    def test_single_upload_signed_payload_verified(self):
        self.plan(); r=self.execute('publish')
        self.assertEqual(r['status'],'published-verified',r)
        self.assertEqual(self.uploads,1);self.assertNotIn('key-fixture',json.dumps(r))
        self.assertEqual(r['upload_count'],1)

    def test_ambiguous_upload_never_retried(self):
        self.upload_code=1;self.plan();r=self.execute('publish')
        self.assertEqual(r['status'],'published-verified',r);self.assertEqual(self.uploads,1)
        self.assertEqual(r['upload_exit_code'],1)

    def test_occupied_payload_no_upload(self):
        self.public=self.signed();self.plan();r=self.execute('publish')
        self.assertEqual(r['status'],'published-verified',r);self.assertEqual(self.uploads,0)

    def test_bad_signature_fails(self):
        self.public=self.signed();self.signature_code=1;self.plan();r=self.execute('publish')
        self.assertEqual(r['status'],'failed');self.assertEqual(self.uploads,0)

    def test_wrong_dispatch_variants(self):
        for key,bad in [('GITHUB_REF','refs/heads/other'),('GITHUB_EVENT_NAME','push'),('GITHUB_SHA','short'),
                ('GITHUB_WORKFLOW_REF','wrong'),('GITHUB_REPOSITORY',p.FIXED['projects' if self.profile=='eventstore' else 'eventstore'][0]),
                ('HEXALITH_RELEASE_PUBLISH_ENABLED','TRUE')]:
            original=self.context[key];self.context[key]=bad
            self.assertEqual(self.execute()['status'],'failed',(key,bad))
            self.context[key]=original

    def test_qualification_must_pass_and_match(self):
        self.plan()
        for key,bad in [('PREREQUISITE_QUALIFICATION','skipped'),('PREREQUISITE_PLAN','{}'),('NUGET_API_KEY','')]:
            original=self.context[key];self.context[key]=bad
            self.assertEqual(self.execute('publish')['status'],'failed',key)
            self.context[key]=original
        self.assertEqual(self.uploads,0)

    def test_approved_archive_tamper_rejected(self):
        _,path,_=p.qualification(self.root,self.profile);path.write_bytes(path.read_bytes()+b'tamper')
        self.assertEqual(self.execute()['status'],'failed');self.assertEqual(self.gets,0)

    def test_required_proof_tamper_rejected(self):
        path=self.root/'docs/contracts-prerequisites/projects-tests.json';path.write_text('{}')
        self.assertEqual(self.execute()['status'],'failed');self.assertEqual(self.gets,0)

    def test_zip_changed_extra_duplicate_and_missing_signature(self):
        package,path,_=p.qualification(self.root,self.profile)
        with self.assertRaises(ValueError): p.payload(path.read_bytes(),package['entries'],signed=True)
        with zipfile.ZipFile(path) as old:
            for mode in ['changed','extra','duplicate']:
                b=io.BytesIO()
                with zipfile.ZipFile(b,'w',compression=zipfile.ZIP_DEFLATED) as z:
                    for name in old.namelist(): z.writestr(name,b'changed' if mode=='changed' else old.read(name))
                    z.writestr('.signature.p7s',b'sig')
                    if mode=='extra': z.writestr('extra',b'bad')
                    if mode=='duplicate': z.writestr('README.md',b'bad')
                with self.assertRaises(ValueError):p.payload(b.getvalue(),package['entries'],signed=True)

    def test_source_advance_rejected_before_upload(self):
        self.plan()
        original=self.fetch
        def fetch(url,*args,**kwargs):
            if 'api.github.com' in url:return json.dumps({'object':{'type':'commit','sha':'c'*40}}).encode()
            return original(url,*args,**kwargs)
        r=p.execute('publish',self.profile,self.root,self.root/'receipt.json',self.context,fetch=fetch,run=self.proc)
        self.assertEqual(r['status'],'failed');self.assertEqual(self.uploads,0)

    def test_verification_only_never_uploads(self):
        r=self.execute('verify');self.assertEqual(r['status'],'failed');self.assertEqual(self.uploads,0)
        self.public=self.signed();r=self.execute('verify');self.assertEqual(r['status'],'published-verified');self.assertEqual(self.uploads,0)

    def test_delayed_visibility_and_transient_observation(self):
        self.plan()
        original=self.fetch
        polls=[]
        def fetch(url,*args,**kwargs):
            if self.uploads and 'api.nuget.org' in url:
                polls.append(1)
                if len(polls)==1: raise OSError('transient public observation')
                if len(polls)==2:return None
            return original(url,*args,**kwargs)
        r=p.execute('publish',self.profile,self.root,self.root/'receipt.json',self.context,
            fetch=fetch,run=self.proc,pause=lambda _:None)
        self.assertEqual(r['status'],'published-verified',r)
        self.assertEqual(self.uploads,1);self.assertEqual(len(polls),3)
        self.assertEqual(len(r['observation_errors']),1)

    def test_never_visible_retains_attempt(self):
        self.plan()
        original=self.fetch
        polls=[]
        def fetch(url,*args,**kwargs):
            if self.uploads and 'api.nuget.org' in url:polls.append(1);return None
            return original(url,*args,**kwargs)
        r=p.execute('publish',self.profile,self.root,self.root/'receipt.json',self.context,
            fetch=fetch,run=self.proc,pause=lambda _:None)
        self.assertEqual(r['status'],'failed');self.assertEqual(self.uploads,1)
        self.assertTrue(r['push_attempted']);self.assertEqual(r['upload_count'],1)
        self.assertEqual(len(polls),12)
        self.assertEqual(json.loads((self.root/'receipt.json').read_text())['upload_count'],1)

    def test_interrupted_upload_has_durable_attempt(self):
        self.plan()
        original=self.proc
        def proc(args,**kwargs):
            if args[1:3]==['nuget','push']:raise KeyboardInterrupt('fixture interruption')
            return original(args,**kwargs)
        with self.assertRaises(KeyboardInterrupt):
            p.execute('publish',self.profile,self.root,self.root/'receipt.json',self.context,
                fetch=self.fetch,run=proc,pause=lambda _:None)
        receipt=json.loads((self.root/'receipt.json').read_text())
        self.assertTrue(receipt['push_attempted']);self.assertEqual(receipt['upload_count'],1)
        self.assertEqual(receipt['failed_operation'],'upload exact archive once')

    def test_frozen_publication_allows_readonly_verification(self):
        self.public=self.signed();self.context['HEXALITH_RELEASE_PUBLISH_ENABLED']='false'
        self.assertEqual(self.execute('verify')['status'],'published-verified')
        self.assertEqual(self.execute('qualify')['status'],'failed');self.assertEqual(self.uploads,0)

    def test_timeout_process_output_retained(self):
        import sys
        code,output=p.command([sys.executable,'-c',"print('retained before timeout',flush=True);import time;time.sleep(1)"],timeout=0.05)
        self.assertEqual(code,124);self.assertIn('retained before timeout',output)


    def test_sigterm_upload_checkpoint_survives_without_finally(self):
        import subprocess,sys
        self.plan()
        script = """
import importlib.util,json,os,signal,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('publisher',sys.argv[1]);p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
root=Path(sys.argv[2]);profile=sys.argv[3];context=json.loads(sys.argv[4])
def fetch(url,*args,**kwargs):
    if 'api.github.com' in url:return json.dumps({'object':{'type':'commit','sha':'a'*40}}).encode()
    return None
def run(args,**kwargs):
    if args[0]=='git':return 0,'b'*40
    if args[1:3]==['nuget','push']:os.kill(os.getpid(),signal.SIGTERM)
    raise AssertionError(args)
p.execute('publish',profile,root,root/'terminated-receipt.json',context,fetch=fetch,run=run)
"""
        result=subprocess.run([sys.executable,'-B','-c',script,str(ROOT/'tools/publish_contracts_prerequisite.py'),
            str(self.root),self.profile,json.dumps(self.context)],capture_output=True,timeout=10)
        self.assertEqual(result.returncode,-15,result.stderr)
        receipt=json.loads((self.root/'terminated-receipt.json').read_text())
        self.assertTrue(receipt['push_attempted']);self.assertEqual(receipt['upload_count'],1)
        self.assertEqual(receipt['failed_operation'],'upload exact archive once')



class ProjectsControls(Controls):
    PROFILE = 'projects'


if __name__=='__main__': unittest.main(verbosity=2)
