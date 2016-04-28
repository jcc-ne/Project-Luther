import ftplib
from ftplib import FTP
import glob

ftp = FTP('ftp.fu-berlin.de')
ftp.login()
ftp.retrlines('LIST')

ftp.cwd('misc/movies/database')
datalist = ftp.nlst()

for d in datalist:
    if not glob.glob(d):
        print "downloading", d, "..."
        try:
            ftp.retrbinary('RETR {}'.format(d), open(d, 'wb').write)
        except ftplib.error_perm:
            print d, 'not working'
    else:
        print d, 'already exists'

# build database
# !imdbpy2sql.py -d ./ -u 'sqlite:///Users/janine/Documents/Projects/Metis/Project-Luther/data/data.db' --sqlite-transactions

