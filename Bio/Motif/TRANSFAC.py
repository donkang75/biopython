# Copyright 2003 by Bartek Wilczynski.  All rights reserved.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.

"""Parsing TRANSFAC files
"""

import string
from Bio.Motif import Motif as BaseMotif

class Motif(BaseMotif, dict):
    """A Bio.Motif.TRANSFAC.Motif stores the information in one TRANSFAC
motif. This class inherits from the Bio.Motif.Motif base class, as well
as from a Python dictionary. All motif information found by the parser
is stored as attributes of the base class when possible; see the
Bio.Motif.Motif base class for a description of these attributes. All
other information associated with the motif is stored as (key, value)
pairs in the dictionary, where the key is the two-letter fields as found
in the TRANSFAC file. References are an exception: These are stored in
the .references attribute.

These fields are commonly found in TRANSFAC files:
    AC:    Accession number
    AS:    Accession numbers, secondary
    BA:    Statistical basis
    BF:    Binding factors
    BS:    Factor binding sites underlying the matrix
           [SITE accession number; start position for matrix sequence;
            length of sequence used; number of gaps inserted; strand
            orientation]
    CC:    Comments
    CO:    Copyright notice
    DE:    Short factor description
    DR:    External databases
           [EMBL/GEnBank accession number; EMBL identifier (1st: last
            position of the TRANSFAC sequence element)]
    DT:    Date created/updated
    HC:    Subfamilies
    HP:    Superfamilies
    ID:    Identifier
    NA:    Name of the binding factor
    OC:    Taxonomic classification
    OS:    Species/Taxon
    OV:    Older version
    PV:    Preferred version
    TY:    Type
    XX:    Empty line; these are not stored in the Record.

References are stored in an .references attribute, which is a list of
dictionaries with the following keys:
    RN:    Reference number
    RA:    Reference authors
    RL:    Reference data
    RT:    Reference title
    RX:    PubMed ID

For more information, see the TRANSFAC documentation.
"""
    _multiple_value_keys = set(['BF', 'OV', 'HP', 'BS', 'HC', 'DT', 'DR'])
    # These keys can occur multiple times for one motif

    _reference_keys = set(['RX', 'RA', 'RT', 'RL'])
    # These keys occur for references

    def __init__(self):
        BaseMotif.__init__(self)
        self.references = []

    def __getitem__(self,index):
        # This can be removed if we remove the __getitem__ method from BaseMotif
        return dict.__getitem__(self, index)

    def __str__(self):
        keys = ('AC', 'AS', 'ID', 'DT', 'CO', 'NA', 'DE',
                'TY', 'OS', 'OC', 'HP', 'HC', 'BF', 'P0',
                'BA', 'BS', 'CC', 'DR', 'OV', 'PV')
        lines = []
        for key in keys:
            if key=='P0':
                length = self.length
                line = "P0      A      C      G      T"
                lines.append(line)
                for i in range(length):
                    position = string.zfill(i+1, 2)
                    line = "%s\t%f\t%f\t%f\t%f" % (position,
                                             self.counts['A'][i],
                                             self.counts['C'][i],
                                             self.counts['G'][i],
                                             self.counts['T'][i])
                    lines.append(line)
                continue
            value = self.get(key)
            if value==None:
                continue
            if key in Motif._multiple_value_keys:
                for v in value:
                    line = "%s  %s" % (key, v)
                    lines.append(line)
            else:
                line = "%s  %s" % (key, value)
                lines.append(line)
        keys = ("RN", "RX", "RA", "RT", "RL")
        for reference in self.references:
            for key in keys:
                value = reference.get(key)
                if value==None:
                    continue
                line = "%s  %s" % (key, value)
                lines.append(line)
        line = "//"
        lines.append(line)
        text = "\n".join(lines) + "\n"
        return text


class Record(object):
    """A Bio.Motif.TRANSFAC.Record stores the information in a TRANSFAC
matrix table.

Attributes:
    o version:   The version number, corresponding to the 'VV' field
                 in the TRANSFAC file;
    o motifs:    The list of motifs.
"""
    def __init__(self):
        self.motifs = []

    def __str__(self):
        lines = []
        line = "VV  %s" % self.version
        lines.append(line)
        line = "//"
        lines.append(line)
        block = "\n".join(lines) + "\n"
        blocks = [block]
        for motif in self.motifs:
            block = str(motif)
            blocks.append(block)
        text = "".join(blocks)
        return text

def read(handle):
    """record = read(handle)"""
    motif = None
    status = None
    record = Record()
    for line in handle:
        line = line.strip()
        if line=='//':
            if motif!=None:
                record.motifs.append(motif)
            motif = None
            status = None
        elif line=='XX':
            pass
        else:
            key, value = line.split(None, 1)
            if key=='VV':
                record.version = value
                continue
            if motif==None:
                motif = Motif()
            if status=="freq":
               try:
                   i = int(key)
               except ValueError:
                   status = None
               else:
                   motif.length+=1
                   assert i==motif.length
                   values = value.split()
                   for c, v in zip("ACGT", values):
                       motif.counts[c].append(float(v))
                   continue
            if key=='P0':
                assert status!="freq"
                assert motif.counts==None
                motif.counts = {}
                assert value.split()[:4]==['A','C','G','T']
                motif.length = 0
                for c in "ACGT":
                    motif.counts[c] = []
                status = "freq"
            elif key=='RN':
                index, accession = value.split(";")
                assert index[0]=='['
                assert index[-1]==']'
                index = int(index[1:-1])
                assert len(motif.references)==index-1
                reference = {key: value}
                motif.references.append(reference)
            elif key in Motif._reference_keys:
                reference[key] = value
            elif key in Motif._multiple_value_keys:
                if not key in motif:
                    motif[key] = []
                motif[key].append(value)
            else:
                motif[key] = value
    return record