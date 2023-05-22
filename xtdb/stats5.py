from xtdb.dbclient import xtdb, log, edn_dumps
import os
URL = os.getenv( 'XTDB') or 'http://localhost:3001'
M =  int( os.getenv( 'MXTDB') or 1)
N =  int( os.getenv( 'NXTDB') or 3)
for i in range( M,1+N):
    URX= URL[:-1]+str(i)
    db = xtdb( URX)
    infos = dict(
        numKeys= lambda: db.status()['xtdb.kv/estimateNumKeys'],
        #print( i, '-', dict( (k,v) for k,v in db.stats().items() if k[0]=='a'))
        tx_subm= lambda: db.latest_submitted_tx()['txId'],
        tx_done= lambda: db.latest_completed_tx()['txId'],
        )
    print( i, end=': ')
    for k,f in infos.items():
        try: r = f()
        except Exception as e: r = str(e)
        print( k,r, end='; ')
        if isinstance(r,str) and ('NewConnectionError' in r or 'ConnectionResetError' in r or 'RemoteDisconnected' in r):
            break
    print()

# vim:ts=4:sw=4:expandtab
