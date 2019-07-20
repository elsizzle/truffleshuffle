#!/usr/bin/python

# tomsom
# Derived from Sara Edwards' SANS FOR518

# Truffleshuffle is a simple script that parses the Mac OS
# ChunkStoreDatabase and ChunkStorage to carve versioned files.

import os
import sqlite3
from optparse import OptionParser
import struct

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
    # Extracting chunk lists
    for [clt_rowid, clt_inode, clt_count, clt_chunkRowIDs] in db.execute('SELECT clt_rowid,clt_inode,clt_count,clt_chunkRowIDs FROM CSStorageChunkListTable'):
        print "CSStorageChunkListTable RowID: %d" % (int(clt_rowid))
        print "Inode: %d" % (int(clt_inode))
        print "Number of chunks: %d" % (int(clt_count))
        filename = "%s/%s-%s"     % (options.outdir, clt_inode, clt_rowid)
        print "Output file: %s" % (filename)
        print "Length clt_chunkRowIDs: %d" % (len(clt_chunkRowIDs))
        number_of_chunks = int(len(clt_chunkRowIDs)/8)
        print "Number of chunks based on length clt_chunkRowIDs: %d" % (number_of_chunks)

        # Sanity check
        if number_of_chunks != clt_count:
            print "WARNING: number of chnuks inconsistent!"

        # Open output file
        try:
            output = open(filename, 'wb')
        except IOError as e:
            print "IO ERROR - Opening output file failed: %s" % (str(e))
            sys.exit(-1)

        # Extracting chunks IDs
        for i in range(0,len(str(clt_chunkRowIDs))/8):
            (chunk_id,) = struct.unpack("<Q",str(clt_chunkRowIDs)[i*8:i*8+8])

            # Extracting chunks
            for [offset, dataLen, cid] in db.execute("SELECT offset,dataLen,cid from CSChunkTable where ct_rowid = '%s'" % chunk_id):

                filenameraw = "%s/%s-%s-%d-raw" % (options.outdir, clt_inode, clt_rowid, chunk_id)

                # Appen the actual chunk data to the output file
                cs.seek(offset + 25)
                chunkData = cs.read(dataLen - 25)
                output.write(chunkData)

                # Write the chunk data with header to the RAW output file
                cs.seek(offset)
                chunkDataRaw = cs.read(dataLen)

                # Sanity checks
                if struct.unpack(">l",chunkDataRaw[0:4])[0] != dataLen:
                    print "WARNING: Chunk size inconsistent!"
                    print "Chunk size in chunk: %d" % (struct.unpack(">l",chunkDataRaw[0:4])[0])
                    print "Chunk size in DB: %d" % (dataLen)

                if str(chunkDataRaw[4:25]).encode('hex') != str(cid).encode('hex'):
                    print "WARNING: Chunk ID inconsistent!"
                    print "Chunk ID in chunk: %s" % (str(chunkDataRaw[4:25]).encode('hex'))
                    print "Chunk ID in DB: %s" % (str(cid).encode('hex'))

                try:
                    outputraw = open(filenameraw,'wb')
                except IOError as e:
                    print "IO ERROR - Opening raw output file failed: %s" % (str(e))
                    sys.exit(-1)

                outputraw.write(chunkDataRaw)
                outputraw.close()

        output.close()

except sqlite3.Error as err:
   print("SQLite error - %s" % str(err))
   exit()

db.close()
