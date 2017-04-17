#!/usr/bin/python

# tomsom
# Derived from Sara Edwards' SANS FOR518

# truffleshuffle parses the Mac OS ChunkStoreDatabase 
# and ChunkStorage file to carve versioned files.  

import os
import sqlite3
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-c", dest="csfile", help="ChunkStorage file")
parser.add_option("-d", dest="csdb",   help="ChunkStoreDatabase SQLite file")
parser.add_option("-o", dest="outdir", help="Output folder", default="output")
(options, args) = parser.parse_args()

try:
   if not os.path.exists(options.outdir):
      os.makedirs(options.outdir)
except OSError as err:
   print("OS error - %s" % str(err))
   exit()

# open ChunkStoreDatabase and ChunkStorage file
db = sqlite3.connect(str(options.csdb))  
cs = open(str(options.csfile), 'r')

try: 
   for [clt_rowid, clt_inode] in db.execute('SELECT clt_rowid,clt_inode FROM CSStorageChunkListTable'):
      for [offset, dataLen] in db.execute("SELECT offset,dataLen from CSChunkTable where ct_rowid = '%s'" % clt_rowid):

         filenameraw = "%s/%s-%s-raw" % (options.outdir, clt_inode, clt_rowid)
         filename    = "%s/%s-%s"     % (options.outdir, clt_inode, clt_rowid)

         outputraw = open(filenameraw, 'w') 
         output    = open(filename, 'w') 

         cs.seek(offset)  
         file = cs.read(dataLen)
         outputraw.write(file)
         outputraw.close()

         cs.seek(offset + 25)
         file = cs.read(dataLen - 25)
         output.write(file)
         output.close()

except sqlite3.Error as err:
   print("SQLite error - %s" % str(err))
   exit()

db.close()
